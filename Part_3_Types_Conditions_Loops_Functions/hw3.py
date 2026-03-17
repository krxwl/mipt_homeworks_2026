#!/usr/bin/env python3

UNKNOWN_COMMAND_MSG = "Неизвестная команда!"
NONPOSITIVE_VALUE_MSG = "Значение должно быть больше нуля!"
INCORRECT_DATE_MSG = "Неправильная дата!"
OP_SUCCESS_MSG = "Добавлено"
LOSS = "убыток составил"
PROFIT = "прибыль составила"

incomes: dict[str, float] = {}
costs: dict[str, dict[str, float]] = {}

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

args_for_commands = {
    "income": 3,
    "cost": 4,
    "stats": 2
}

FEBRUARY = 2
MONTHS_IN_YEAR = 12


def is_leap_year(year: int) -> bool:
    return ((year % 4 == 0 and year % 100 != 0) or
            (year % 100 == 0 and year % 400 == 0))


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    day, month, year = [int(i) for i in maybe_dt.split("-")]
    max_days = 29 if (month == FEBRUARY and is_leap_year(year)) else days_to_months[month]

    if 1 <= day <= max_days and 1 <= month <= MONTHS_IN_YEAR:
        return (day, month, year)
    return None


def get_correct_float(my_float: str) -> float:
    return float(my_float.replace(",", "."))


def get_capital() -> float:
    capital = sum(incomes.values())
    for categories in costs.values():
        for cost_value in categories.values():
            capital -= cost_value
    return capital


def income(command: list[str]) -> None:
    amount = get_correct_float(command[1])
    if amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return

    data = extract_date(command[2])
    if data is None:
        print(INCORRECT_DATE_MSG)
        return

    date_str = command[2]
    incomes[date_str] = incomes.get(date_str, 0) + amount
    print(OP_SUCCESS_MSG)


def cost(command: list[str]) -> None:
    category_name = command[1]

    amount = get_correct_float(command[2])
    if amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return

    data = extract_date(command[3])
    if data is None:
        print(INCORRECT_DATE_MSG)
        return

    date_str = command[3]
    if date_str not in costs:
        costs[date_str] = {}
    costs[date_str] = costs.get(date_str, {})
    costs[date_str][category_name] = (costs[date_str]
                                      .get(category_name, 0) + amount)
    print(OP_SUCCESS_MSG)


def calculate_month_incomes(target_month: int, target_year: int) -> float:
    month_incomes: float = 0
    for data, income_value in incomes.items():
        extracted_date = extract_date(data)
        if extracted_date is None:
            continue
        if (extracted_date[2] == target_year and extracted_date[1] == target_month):
            month_incomes += income_value
    return month_incomes


def recalculate_categories(categories: dict[str, float]) -> None:
    for cats in costs.values():
        for cat, val in cats.items():
            categories[cat] = categories.get(cat, 0) + val


def calculate_month_costs(
        target_month: int, target_year: int) -> tuple[float, dict[str, float]]:
    total: float = 0
    categories: dict[str, float] = {}

    for date, cats in costs.items():
        data = extract_date(date)
        if data and data[2] == target_year and data[1] == target_month:
            total += sum(cats.values())
    recalculate_categories(categories)

    return total, categories


def get_string(summa: float) -> str:
    return PROFIT if (summa >= 0) else LOSS

def stats(command: list[str]) -> None:
    date_tuple = extract_date(command[1])
    if date_tuple is None:
        print(INCORRECT_DATE_MSG)
        return

    month_incomes = calculate_month_incomes(
        date_tuple[1], date_tuple[2])

    month_costs, category_costs = calculate_month_costs(
        date_tuple[1], date_tuple[2])

    print(f"Ваша статистика по состоянию на {command[1]}:")
    print(f"Суммарный капитал: {get_capital():.2f} рублей")
    print(f"B этом месяце {get_string(month_incomes - month_costs)} {abs(month_incomes - month_costs):.2f} рублей")
    print(f"Доходы: {month_incomes:.2f} рублей")
    print(f"Расходы: {month_costs:.2f} рублей\n")
    print("Детализация (категория: сумма):")

    if not category_costs:
        return

    sorted_categories = sorted(category_costs.items(), key=lambda x: x[0])
    for i, (category, cost) in enumerate(sorted_categories, 1):
        if cost == int(cost):
            print(f"{i}. {category}: {int(cost)}")
        else:
            print(f"{i}. {category}: {cost:.2f}")


def check_is_income(txt_cmd: str, command: list[str]) -> bool:
    return txt_cmd == "income" and len(command) == args_for_commands[command[0]]


def check_is_cost(txt_cmd: str, command: list[str]) -> bool:
    return txt_cmd == "cost" and len(command) == args_for_commands[command[0]]


def check_is_stats(txt_cmd: str, command: list[str]) -> bool:
    return txt_cmd == "stats" and len(command) == args_for_commands[command[0]]


def match_the_command(command: list[str]) -> bool:
    if not command:
        return False
    txt_cmd = command[0]
    if check_is_income(txt_cmd, command):
        income(command)
    elif check_is_cost(txt_cmd, command):
        cost(command)
    elif check_is_stats(txt_cmd, command):
        stats(command)
    elif txt_cmd == "exit":
        return True
    else:
        print(UNKNOWN_COMMAND_MSG)
    return False


def main() -> None:
    while True:
        command = input().strip().split()
        if (not match_the_command(command)):
            break


if __name__ == "__main__":
    main()
