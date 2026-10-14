"""MCP tool server for the expenses agent.

Exposes all 7 expense tools over the Streamable HTTP transport.

Run standalone (from expenses-mcp/):
    uv run python main.py

The agent (main.py) does NOT start this process — they run as separate processes.
"""

import logging
from datetime import datetime
from os import environ

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth import JWTVerifier, RemoteAuthProvider
from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import JSONResponse

from .auth import resolve_acting_user
from .token_client import svc_token_client
from .tools import (
    create_expense as _create_expense,
)
from .tools import (
    create_expense_category as _create_expense_category,
)
from .tools import (
    get_all_categories as _get_all_categories,
)
from .tools import (
    get_all_expenses as _get_all_expenses,
)
from .tools import (
    get_category_by_name as _get_category_by_name,
)
from .tools import (
    get_expenses_by_category as _get_expenses_by_category,
)
from .tools import (
    get_expenses_since as _get_expenses_since,
)
from .types import (
    Category,
    CategoryWithTotal,
    Expense,
    ExpenseTotalResponse,
    ExpenseWithCategory,
)

load_dotenv()

logger = logging.getLogger(__name__)

_AUTH_REQUIRED = environ.get("AUTH_REQUIRED", "true").lower() not in ("false", "0", "no")
_AUTH_URL = environ.get("AUTH_URL", "http://localhost:8001")
_AUTH_JWKS_URI = environ.get("AUTH_JWKS_URI", "")
_AUTH_ISSUER = environ.get("AUTH_ISSUER", "")
_MCP_BASE_URL = environ.get("MCP_BASE_URL", "")

if _AUTH_REQUIRED:
    _jwt_verifier: JWTVerifier = JWTVerifier(  # type: ignore[assignment]
        jwks_uri=_AUTH_JWKS_URI,
        issuer=_AUTH_ISSUER,
        audience="expenses-mcp",
    )
    _auth_provider: RemoteAuthProvider = RemoteAuthProvider(  # type: ignore[assignment]
        token_verifier=_jwt_verifier,
        authorization_servers=[AnyHttpUrl(_AUTH_URL)],
        base_url=AnyHttpUrl(_MCP_BASE_URL),
    )
    mcp: FastMCP = FastMCP("expenses-tools", auth=_auth_provider)  # type: ignore[call-arg]
else:
    logger.warning(
        "AUTH_REQUIRED=false — MCP server running WITHOUT bearer authentication. "
        "Do NOT use this setting in production."
    )
    mcp = FastMCP("expenses-tools")  # type: ignore[call-arg]


@mcp.custom_route("/health", methods=["GET"])  # type: ignore[misc]
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@mcp.tool  # type: ignore[misc]
async def get_all_expenses() -> list[ExpenseWithCategory]:
    """It retrieves all expenses a user has recorded.
    The number retrieved is just the first 100 entries.
    """
    acting_user = resolve_acting_user()
    auth_headers = await svc_token_client.build_headers(acting_user)
    return _get_all_expenses(auth_headers)


@mcp.tool  # type: ignore[misc]
async def create_expense_category(name: str, description: str) -> Category:
    """It creates an new expense category, if it doesn't already exist.
    All expenses are recorded under a specific category.
    This helps to retrieve and record an expense category.

    Parameters:
      name (str) - The category name
      description (str) - The category description. It is optional.
    """
    acting_user = resolve_acting_user()
    auth_headers = await svc_token_client.build_headers(acting_user)
    return _create_expense_category(name, description, auth_headers)


@mcp.tool  # type: ignore[misc]
async def get_all_categories() -> list[Category]:
    """It retrieves all categories. It retrieves the first 100 entries."""
    acting_user = resolve_acting_user()
    auth_headers = await svc_token_client.build_headers(acting_user)
    return _get_all_categories(auth_headers)


@mcp.tool  # type: ignore[misc]
async def get_category_by_name(name: str) -> Category:
    """It retrieves a category by name.

    Parameters:
      name (str) - the category name
    """
    acting_user = resolve_acting_user()
    auth_headers = await svc_token_client.build_headers(acting_user)
    return _get_category_by_name(name, auth_headers)


@mcp.tool  # type: ignore[misc]
async def create_expense(
    amount: float, description: str, date: datetime, category_name: str
) -> Expense:
    """It records a new expense.

    Parameters:
      amount (float) - the amount of money a user just spent
      description (string) - description of what the expense is about. It's optional.
      date (datetime) - Time and date at which the money was spent.
        If not specified, please use today's date.
      category_name (string) - The name of the category this expense falls into.
        It could be an existing or a new category. Please guess the category
        based on existing ones, if not, propose one.
    """
    acting_user = resolve_acting_user()
    auth_headers = await svc_token_client.build_headers(acting_user)
    return _create_expense(amount, description, date, category_name, auth_headers)


@mcp.tool  # type: ignore[misc]
async def get_expenses_by_category() -> list[CategoryWithTotal]:
    """
    Retrieves the total amount of expenses recorded by a user, grouped by category.

    Note: If the user specifies a specific time period, use the get_expenses_since
    tool internally instead. Do not mention this tool to the user.
    """
    acting_user = resolve_acting_user()
    auth_headers = await svc_token_client.build_headers(acting_user)
    return _get_expenses_by_category(auth_headers)


@mcp.tool  # type: ignore[misc]
async def get_expenses_since(
    days: int | None,
    start_date: datetime | None,
    category_name: str | None,
) -> ExpenseTotalResponse:
    """
    Retrieves the total amount of expenses since a specified time period.
    You can define the period either by providing a specific start date or by
    specifying the number of past days. Optionally, expenses can be filtered
    by category.

    Parameters:
      days (int, optional): Number of past days from today to include in the total.
      start_date (datetime, optional): Specific date from which to start calculating
        expenses. If not provided, defaults to 30 days ago.
      category_name (str, optional): If provided, filters expenses by this category.
        This is optional.

    Returns:
      Object containing total expense amount plus the query parameters used
      (start_date, days, category_name).
    """
    acting_user = resolve_acting_user()
    auth_headers = await svc_token_client.build_headers(acting_user)
    return _get_expenses_since(days, start_date, category_name, auth_headers)
