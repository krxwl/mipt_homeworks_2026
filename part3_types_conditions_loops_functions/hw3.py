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
    "Other": ("Cat",),
}

financial_transactions_storage: list[dict[str, Any]] = []

FEBRUARY = 2
MONTHS_IN_YEAR = 12

DATE_LENGTH = 3
CATEGORY_LENGTH = 2
COMMAND_LENGTH = 3
COST_COMMAND_LENGTH = 2
COST_COMMAND_LENGTH2 = 4
STATS_COMMAND_LENGTH = 2

days_to_months = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31
}


def is_leap_year(year: int) -> bool:
    return ((year % 4 == 0 and year % 100 != 0) or
            (year % 100 == 0 and year % 400 == 0))


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_LENGTH:
        return None

    for part in parts:
        if not part.isdigit():
            return None

    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])

    max_days = days_to_months.get(month, 0)
    if month == FEBRUARY and is_leap_year(year):
        max_days = 29

    if not (1 <= day <= max_days and 1 <= month <= MONTHS_IN_YEAR):
        return None
    return (day, month, year)


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

    financial_transactions_storage.append({
        "amount": amount,
        "date": date_tuple,
        "income": True
    })
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

    financial_transactions_storage.append({
        "category": category_name,
        "amount": amount,
        "date": date_tuple,
        "income": False
    })
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


def compare_dates(date1: tuple[int, int, int], date2: tuple[int, int, int]) -> bool:
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

    return "\n" + "\n".join(lines) + "\n" if lines else ""


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
    total_capital = calculate_capital_until_date(report_date)
    profit_loss = month_incomes - month_costs

    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {total_capital:.2f} rubles",
        get_str_profit_or_loss(profit_loss),
        f"Income: {month_incomes:.2f} rubles",
        f"Expenses: {month_costs:.2f} rubles",
        "Details (category: amount):" + format_stats_details(category_costs),
    ]

    return "\n".join(lines)


def recognize_command(command: list[str]) -> str:
    if len(command) != COMMAND_LENGTH:
        return UNKNOWN_COMMAND_MSG

    amount = get_correct_float(command[1])
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    if extract_date(command[2]) is None:
        return INCORRECT_DATE_MSG
    return income_handler(amount, command[2])


def validate_cost_command(command: list[str]) -> str:
    result: str = UNKNOWN_COMMAND_MSG

    if len(command) == COST_COMMAND_LENGTH and command[1] == "categories":
        result = cost_categories_handler()
    elif len(command) == COST_COMMAND_LENGTH2:
        category_name = command[1]
        if not is_valid_category(category_name):
            result = NOT_EXISTS_CATEGORY
        else:
            amount = get_correct_float(command[2])
            if amount is None or amount <= 0:
                result = NONPOSITIVE_VALUE_MSG
            elif extract_date(command[3]) is None:
                result = INCORRECT_DATE_MSG
            else:
                result = cost_handler(category_name, amount, command[3])

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
