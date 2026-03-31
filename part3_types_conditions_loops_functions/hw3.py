#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

_INCOME_KEY = "income"
_AMOUNT_KEY = "amount"
_CATEGORY_KEY = "category"
_DATE_KEY = "date"

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

DateTuple = tuple[int, int, int]

financial_transactions_storage: list[dict[str, Any]] = []

FEBRUARY = 2
MONTHS_IN_YEAR = 12

DATE_LENGTH = 3
CATEGORY_LENGTH = 2
COMMAND_LENGTH = 3
COST_COMMAND_LENGTH = 2
COST_COMMAND_LENGTH2 = 4
STATS_COMMAND_LENGTH = 2

FIRST_HALF = [31, 28, 31, 30, 31, 30]
SECOND_HALF = [31, 31, 30, 31, 30, 31]
month_days = FIRST_HALF + SECOND_HALF
days_to_months = {i + 1: days for i, days in enumerate(month_days)}


def is_leap_year(year: int) -> bool:
    condition1 = year % 4 == 0 and year % 100 != 0
    condition2 = year % 100 == 0 and year % 400 == 0
    return condition1 or condition2


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_LENGTH:
        return None

    for part in parts:
        if not part.isdigit():
            return None

    day = int(parts[0])
    month = int(parts[1])

    max_days = days_to_months.get(month, 0)
    if month == FEBRUARY and is_leap_year(int(parts[2])):
        max_days = 29

    if 1 <= day <= max_days and 1 <= month <= MONTHS_IN_YEAR:
        return (day, month, int(parts[2]))
    return None


def get_correct_float(my_float: str) -> float | None:
    my_float = my_float.replace(",", ".")
    if my_float.count(".") > 1:
        return None
    parts = my_float.split(".")
    if not all(part.isdigit() for part in parts if part):
        return None
    return float(my_float)


def is_valid_category(category_name: str) -> bool:
    if "::" not in category_name:
        return False

    parts = category_name.split("::")
    if len(parts) != CATEGORY_LENGTH:
        return False

    if parts[0] not in EXPENSE_CATEGORIES:
        return False
    if parts[0] == "Other":
        return True
    return parts[1] in EXPENSE_CATEGORIES[parts[0]]


def get_all_categories() -> list[str]:
    categories: list[str] = []
    for common_cat, targets in EXPENSE_CATEGORIES.items():
        categories.extend(f"{common_cat}::{target_cat}" for target_cat in targets)
    return categories


def is_income_transaction(transaction: dict[str, Any]) -> bool:
    return bool(transaction.get(_INCOME_KEY, False))


def get_transaction_amount(transaction: dict[str, Any]) -> float:
    return float(transaction.get(_AMOUNT_KEY, 0))


def get_transaction_date(transaction: dict[str, Any]) -> tuple[int, int, int] | None:
    return transaction.get(_DATE_KEY)


def get_transaction_category(transaction: dict[str, Any]) -> str:
    return str(transaction.get(_CATEGORY_KEY, "Other"))


def change_capital(capital: float, operation: dict[str, Any]) -> float:
    amount = get_transaction_amount(operation)
    if is_income_transaction(operation):
        return capital + amount
    return capital - amount


def calculate_capital() -> float:
    capital: float = 0

    for operation in financial_transactions_storage:
        capital = change_capital(capital, operation)
    return capital


def income_handler(amount: float, income_date: str) -> str:
    date_tuple = extract_date(income_date)
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    if date_tuple is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({_AMOUNT_KEY: amount, _DATE_KEY: date_tuple, _INCOME_KEY: True})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    date_tuple = extract_date(income_date)
    is_cat_valid = is_valid_category(category_name)

    if not is_cat_valid:
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    if date_tuple is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {"category": category_name, "amount": amount, "date": date_tuple, "income": False}
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    return "\n".join(get_all_categories())


def is_transaction_in_month(transaction_date: tuple[int, int, int] | None, target_month: int, target_year: int) -> bool:
    if transaction_date is None:
        return False
    return transaction_date[1] == target_month and transaction_date[2] == target_year


def calculate_month_incomes(target_month: int, target_year: int) -> float:
    month_incomes: float = 0
    for transaction in financial_transactions_storage:
        if not is_income_transaction(transaction):
            continue
        if is_transaction_in_month(get_transaction_date(transaction), target_month, target_year):
            month_incomes += get_transaction_amount(transaction)
    return month_incomes


def proccess_transaction(
    total: float,
    categories: dict[str, float],
    transaction: dict[str, Any],
) -> float:
    amount = get_transaction_amount(transaction)
    total += amount
    cat = get_transaction_category(transaction)
    categories[cat] = categories.get(cat, 0) + amount
    return total


def calculate_month_costs(target_month: int, target_year: int) -> tuple[float, dict[str, float]]:
    total: float = 0
    categories: dict[str, float] = {}

    for transaction in financial_transactions_storage:
        if is_income_transaction(transaction):
            continue
        if not is_transaction_in_month(get_transaction_date(transaction), target_month, target_year):
            continue
        total = proccess_transaction(total, categories, transaction)
    return total, categories


def compare_dates(date1: DateTuple, date2: DateTuple) -> bool:
    if date1[2] != date2[2]:
        return date1[2] < date2[2]
    if date1[1] != date2[1]:
        return date1[1] < date2[1]
    return date1[0] <= date2[0]


def calculate_capital_until_date(target_date: str) -> float:
    data = extract_date(target_date)
    if data is None:
        return 0
    capital: float = 0

    for operation in financial_transactions_storage:
        t_data = get_transaction_date(operation)
        if t_data is None:
            continue
        if not compare_dates(t_data, data):
            continue
        capital = change_capital(capital, operation)
    return capital


def format_cost_value(cost: float) -> str:
    if cost == int(cost):
        return str(int(cost))
    return f"{cost:.2f}"


def format_stats_details(category_costs: dict[str, float]) -> str:
    if not category_costs:
        return ""

    lines: list[str] = []
    for number, (category, cost) in enumerate(sorted(category_costs.items()), 1):
        formatted_cost = format_cost_value(cost)
        lines.append(f"{number}. {category}: {formatted_cost}")

    return "".join(["\n", "\n".join(lines), "\n"])


def get_str_profit_or_loss(profit_loss: float) -> str:
    if profit_loss >= 0:
        return f"This month, the profit amounted to {profit_loss:.2f} rubles."
    return f"This month, the loss amounted to {abs(profit_loss):.2f} rubles."


def stats_handler(report_date: str) -> str:
    date_tuple = extract_date(report_date)
    if date_tuple is None:
        return INCORRECT_DATE_MSG

    month_incomes = calculate_month_incomes(date_tuple[1], date_tuple[2])
    month_costs, category_costs = calculate_month_costs(date_tuple[1], date_tuple[2])

    return "".join(
        [
            f"Your statistics as of {report_date}:\n",
            f"Total capital: {calculate_capital_until_date(report_date):.2f} rubles\n",
            f"{get_str_profit_or_loss(month_incomes - month_costs)}\n",
            f"Income: {month_incomes:.2f} rubles\n",
            f"Expenses: {month_costs:.2f} rubles\n",
            f"Details (category: amount):{format_stats_details(category_costs)}",
        ]
    )


def recognize_command(command: list[str]) -> str:
    if len(command) != COMMAND_LENGTH:
        return UNKNOWN_COMMAND_MSG

    amount = get_correct_float(command[1])
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    if extract_date(command[2]) is None:
        return INCORRECT_DATE_MSG
    return income_handler(amount, command[2])


def validate_cost_category(category_name: str) -> str | None:
    if not is_valid_category(category_name):
        return NOT_EXISTS_CATEGORY
    return None


def validate_cost_amount(amount_str: str) -> tuple[float | None, str | None]:
    amount = get_correct_float(amount_str)
    if amount is None or amount <= 0:
        return amount, NONPOSITIVE_VALUE_MSG
    return amount, None


def validate_cost_date(date_str: str) -> str | None:
    if extract_date(date_str) is None:
        return INCORRECT_DATE_MSG
    return None


def is_cost_categories_command(command: list[str]) -> bool:
    return len(command) == COST_COMMAND_LENGTH and command[1] == "categories"


def is_valid_cost_command_length(command: list[str]) -> bool:
    return len(command) == COST_COMMAND_LENGTH2


def get_cost_category_error(category_name: str) -> str | None:
    if is_valid_category(category_name):
        return None
    return NOT_EXISTS_CATEGORY


def get_cost_amount_error(amount_str: str) -> str | None:
    amount = get_correct_float(amount_str)
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    return None


def get_cost_date_error(date_str: str) -> str | None:
    if extract_date(date_str) is None:
        return INCORRECT_DATE_MSG
    return None


def get_cost_validation_error(command: list[str]) -> str | None:
    category_error = get_cost_category_error(command[1])
    if category_error is not None:
        return category_error

    amount_error = get_cost_amount_error(command[2])
    if amount_error is not None:
        return amount_error

    date_error = get_cost_date_error(command[3])
    if date_error is not None:
        return date_error

    return None


def validate_cost_command(command: list[str]) -> str:
    result: str = UNKNOWN_COMMAND_MSG

    if is_cost_categories_command(command):
        result = cost_categories_handler()
    elif is_valid_cost_command_length(command):
        error = get_cost_validation_error(command)
        category_name = command[1]
        date_str = command[3]
        amount = get_correct_float(command[2])
        if amount is not None:
            result = cost_handler(category_name, amount, date_str) if error is None else error

    return result


def validate_stats_command(command: list[str]) -> str:
    if len(command) != STATS_COMMAND_LENGTH:
        return UNKNOWN_COMMAND_MSG
    return stats_handler(command[1])


def parse_command(command: list[str]) -> str:
    if not command:
        return UNKNOWN_COMMAND_MSG

    cmd = command[0]
    result: str = UNKNOWN_COMMAND_MSG

    if cmd == "income":
        result = recognize_command(command)
    elif cmd == "cost":
        result = validate_cost_command(command)
    elif cmd == "stats":
        result = validate_stats_command(command)
    elif cmd == "exit":
        result = "exit"

    return result


def main() -> None:
    while True:
        command = input().strip().split()
        result = parse_command(command)
        if result == "exit":
            break
        print(result)


if __name__ == "__main__":
    main()
