"""MCP tool server for the expenses agent.

Exposes all 7 expense tools over the Streamable HTTP transport.

Run standalone (from expenses-mcp/):
    uv run python main.py

The agent (main.py) does NOT start this process — they run as separate processes.
"""

from datetime import datetime

from dotenv import load_dotenv
from fastmcp import FastMCP

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

mcp: FastMCP = FastMCP("expenses-tools")  # type: ignore[call-arg]


@mcp.tool  # type: ignore[misc]
async def get_all_expenses() -> list[ExpenseWithCategory]:
    """It retrieves all expenses a user has recorded.
    The number retrieved is just the first 100 entries.
    """
    return _get_all_expenses()


@mcp.tool  # type: ignore[misc]
async def create_expense_category(name: str, description: str) -> Category:
    """It creates an new expense category, if it doesn't already exist.
    All expenses are recorded under a specific category.
    This helps to retrieve and record an expense category.

    Parameters:
      name (str) - The category name
      description (str) - The category description. It is optional.
    """
    return _create_expense_category(name, description)


@mcp.tool  # type: ignore[misc]
async def get_all_categories() -> list[Category]:
    """It retrieves all categories. It retrieves the first 100 entries."""
    return _get_all_categories()


@mcp.tool  # type: ignore[misc]
async def get_category_by_name(name: str) -> Category:
    """It retrieves a category by name.

    Parameters:
      name (str) - the category name
    """
    return _get_category_by_name(name)


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
    return _create_expense(amount, description, date, category_name)


@mcp.tool  # type: ignore[misc]
async def get_expenses_by_category() -> list[CategoryWithTotal]:
    """
    Retrieves the total amount of expenses recorded by a user, grouped by category.

    Note: If the user specifies a specific time period, use the get_expenses_since
    tool internally instead. Do not mention this tool to the user.
    """
    return _get_expenses_by_category()


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
    return _get_expenses_since(days, start_date, category_name)
