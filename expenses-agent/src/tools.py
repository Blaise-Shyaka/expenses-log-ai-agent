# Types in this file have been ignored, because for some reason, it affects the calling of tools. To be investigated later
import requests
from os import environ

EXPENSES_API_URL = environ["EXPENSES_API_URL"]


def get_all_expenses():
    """It retrieves all expenses a user has recorded.
    The number retrieved is just the first 100 entries.
    """

    url = EXPENSES_API_URL + "/expenses/"
    try:
        response = requests.get(url)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(str(e))


def create_expense_category(name, description):
    """It creates an new expense category, if it doesn't alread exist. All expenses are recorded under a specific category
    This helps to retrieve and record an expense category.

    Parameters:
      name (str) - The category name
      description (str) - The category description. It is optional.
    """

    url = EXPENSES_API_URL + "/categories/"
    payload = {"name": name, "description": description}
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(str(e))


def get_all_categories():
    """It retrieves all categories. It retrieves the first 100 entries."""

    url = EXPENSES_API_URL + "/categories/"
    try:
        response = requests.get(url)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(str(e))


def get_category_by_name(name):
    """It retrieves a category by name.

    parameters:
      name (str) - the category name
    """

    url = EXPENSES_API_URL + "/categories/name/" + name
    try:
        response = requests.get(url)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(str(e))


def create_expense(amount, description, date, category_name):
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
        response = requests.post(url, json=payload)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(str(e))


def get_expenses():
    """It retrieves all the expenses a user has recorded. The limit is the first 100 items recorded."""

    url = EXPENSES_API_URL + "/expenses/"
    try:
        response = requests.get(url)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(str(e))


def get_expenses_by_category():
    """
    Retrieves the total amount of expenses recorded by a user, grouped by category.

    Note: If the user specifies a specific time period, use the get_expenses_since tool internally instead. Do not mention this tool to the user.
    """
    url = EXPENSES_API_URL + "/expenses/totals/by-category/"
    try:
        response = requests.get(url)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(str(e))


def get_expenses_since(days, start_date, category_name):
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
        response = requests.get(url, params=params)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(str(e))


tools = [
    get_all_expenses,
    create_expense_category,
    get_all_categories,
    get_category_by_name,
    create_expense,
    get_expenses,
    get_expenses_by_category,
    get_expenses_since,
]
