UNKNOWN_COMMAND_MSG = "Неизвестная команда!"
NONPOSITIVE_VALUE_MSG = "Значение должно быть больше нуля!"
INCORRECT_DATE_MSG = "Неправильная дата!"
OP_SUCCESS_MSG = "Добавлено"
LOSS = "убыток составил"
PROFIT = "прибыль составила"

incomes = {}
costs = {}

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
    return (year % 4 == 0 and year % 100 != 0) or (year % 100 == 0 and year % 400 == 0)


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    day, month, year = [int(i) for i in maybe_dt.split("-")]

    if month == FEBRUARY and is_leap_year(year):
        max_days = 29
    else:
        max_days = days_to_months[month]

    if 1 <= day <= max_days and 1 <= month <= MONTHS_IN_YEAR:
        return (day, month, year)
    return None


def get_correct_float(my_float: str) -> float:
    return float(my_float.replace(",", "."))


def get_capital() -> float:
    capital = 0.0
    for income_value in incomes.values():
        capital += income_value
    for categories in costs.values():
        for cost_value in categories.values():
            capital -= cost_value
    return capital


def main() -> None:
    while True:
        command = input().strip().split()
        if not command:
            continue

        if command[0] == "income" and len(command) == args_for_commands[command[0]]:
            amount = get_correct_float(command[1])
            if amount <= 0:
                print(NONPOSITIVE_VALUE_MSG)
                continue

            data = extract_date(command[2])
            if data is None:
                print(INCORRECT_DATE_MSG)
                continue

            date_str = command[2]
            if date_str in incomes:
                incomes[date_str] += amount
            else:
                incomes[date_str] = amount
            print(OP_SUCCESS_MSG)
            
        elif command[0] == "cost" and len(command) == args_for_commands[command[0]]:
            category_name = command[1]

            amount = get_correct_float(command[2])
            if amount <= 0:
                print(NONPOSITIVE_VALUE_MSG)
                continue

            data = extract_date(command[3])
            if data is None:
                print(INCORRECT_DATE_MSG)
                continue

            date_str = command[3]
            if date_str not in costs:
                costs[date_str] = {}

            if category_name in costs[date_str]:
                costs[date_str][category_name] += amount
            else:
                costs[date_str][category_name] = amount
            print(OP_SUCCESS_MSG)
            
        elif command[0] == "stats" and len(command) == args_for_commands[command[0]]:
            date_tuple = extract_date(command[1])
            if date_tuple is None:
                print(INCORRECT_DATE_MSG)
                continue

            _, target_month, target_year = date_tuple
            date_str = command[1]

            month_incomes = 0.0
            for date, income_value in incomes.items():
                extracted_date = extract_date(date)
                _, month, year = extracted_date
                if year == target_year and month == target_month:
                    month_incomes += income_value

            month_costs = 0.0
            category_costs = {}
            for cost_date, categories in costs.items():
                extracted_date = extract_date(cost_date)
                _, month, year = extracted_date
                if year == target_year and month == target_month:
                    for category, cost_value in categories.items():
                        month_costs += cost_value
                        category_costs[category] = category_costs.get(category, 0.0) + cost_value

            changes = month_incomes - month_costs
            loss_or_profit = PROFIT if changes >= 0 else LOSS
            abs_changes = abs(changes)
            capital = get_capital()

            print(f"Ваша статистика по состоянию на {date_str}:")
            print(f"Суммарный капитал: {capital:.2f} рублей")
            print(f"В этом месяце {loss_or_profit} {abs_changes:.2f} рублей")
            print(f"Доходы: {month_incomes:.2f} рублей")
            print(f"Расходы: {month_costs:.2f} рублей\n")
            print("Детализация (категория: сумма):")

            if not category_costs:
                continue

            sorted_categories = sorted(category_costs.items(), key=lambda x: x[0])
            for i, (category, cost) in enumerate(sorted_categories, 1):
                if cost == int(cost):
                    pass
                    print(f"{i}. {category}: {int(cost)}")
                else:
                    pass
                    print(f"{i}. {category}: {cost:.2f}")
        else:
            pass
            print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
