# ~*~ coding=utf-8 ~*~

# PROCESSORS HELPER functions


from datetime import datetime


def convert_date(string: str) -> str:
    return datetime.strptime(string, '%d.%m.%Y').strftime('%Y-%m-%d')


def convert_cost(string) -> str:
    # Convert integers & floats
    string = str(string)

    string = float(string.replace(',', '.'))
    integer = f'{string:.2f}'

    return str(integer)
