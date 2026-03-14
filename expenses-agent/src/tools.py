# Types in this file have been ignored, because for some reason, it affects the calling of tools. To be investigated later
import requests
from os import environ
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry
import logging
from shared.types import (
    Expense,
    Category,
    ExpenseWithCategory,
    CategoryWithTotal,
    ExpenseTotalResponse,
)
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXPENSES_API_URL = environ.get("EXPENSES_API_URL")
print(EXPENSES_API_URL)

# Create a session with connection pooling and retry logic
session = requests.Session()
adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
    ),
)
session.mount("http://", adapter)
session.mount("https://", adapter)


def get_all_expenses() -> list[ExpenseWithCategory] | RequestException:
    """It retrieves all expenses a user has recorded.
    The number retrieved is just the first 100 entries.
    """
    print("we're getting all expenses")
    url = EXPENSES_API_URL + "/expenses/"
    print(url)
    try:
        response = session.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching expenses: {e}")
        return e


def create_expense_category(name: str, description: str) -> Category | RequestException:
    """It creates an new expense category, if it doesn't alread exist. All expenses are recorded under a specific category
    This helps to retrieve and record an expense category.

    Parameters:
      name (str) - The category name
      description (str) - The category description. It is optional.
    """

    url = EXPENSES_API_URL + "/categories/"
    payload = {"name": name, "description": description}
    try:
        response = session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating expense category: {e}")
        return e


def get_all_categories() -> list[Category] | RequestException:
    """It retrieves all categories. It retrieves the first 100 entries."""

    url = EXPENSES_API_URL + "/categories/"
    try:
        response = session.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching categories: {e}")
        return e


def get_category_by_name(name: str) -> Category | RequestException:
    """It retrieves a category by name.

    parameters:
      name (str) - the category name
    """

    url = EXPENSES_API_URL + "/categories/name/" + name
    try:
        response = session.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching category by name: {e}")
        return e


def create_expense(
    amount: float, description: str, date: datetime, category_name: str
) -> Expense | RequestException:
    """It records a new expense.

    parameters:
      amount (float) - the amount of money a user just spent
      description (string) - description of what the expense is about. It's optional.
      date (datetime) - Time and date at which the money was spent. If not specified, please use today's date.
      category_name (string) - The name of the category this expense falls into. It could be an existing or a new category. Please guess the category based on existing ones, if not, propose one.
    """

    url = EXPENSES_API_URL + "/expenses/"
    payload = {
        "amount": amount,
        "description": description,
        "date": date,
        "category_name": category_name,
    }
    try:
        response = session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating expense: {e}")
        return e


def get_expenses_by_category() -> list[CategoryWithTotal] | RequestException:
    """
    Retrieves the total amount of expenses recorded by a user, grouped by category.

    Note: If the user specifies a specific time period, use the get_expenses_since tool internally instead. Do not mention this tool to the user.
    """
    url = EXPENSES_API_URL + "/expenses/totals/by-category/"
    try:
        response = session.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching expenses by category: {e}")
        return e


def get_expenses_since(
    days: int | None, start_date: datetime | None, category_name: str
) -> ExpenseTotalResponse | RequestException:
    """
    Retrieves the total amount of expenses since a specified time period. You can define the period either by providing a specific start date or by specifying the number of past days. Optionally, expenses can be filtered by category.

    Parameters:
      days (int, optional): Number of past days from today to include in the total.
      start_date (datetime, optional): Specific date from which to start calculating expenses. If not provided, defaults to 30 days ago.
      category_name (str, optional): If provided, filters expenses by this category. This is optional.

    Returns:
      Object containing total expense amount plus the query parameters used (start_date, days, category_name).
    """

    url = EXPENSES_API_URL + "/expenses/totals/since"
    params = {}
    if days is not None:
        params["days"] = days
    if start_date is not None:
        params["start_date"] = start_date
    if category_name is not None:
        params["category_name"] = category_name

    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching expenses since: {e}")
        return e


tools = [
    get_all_expenses,
    create_expense_category,
    get_all_categories,
    get_category_by_name,
    create_expense,
    get_expenses_by_category,
    get_expenses_since,
]
