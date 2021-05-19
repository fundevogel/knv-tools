# ~*~ coding=utf-8 ~*~

# PROCESSORS HELPER functions


from datetime import datetime


def convert_date(string: str) -> str:
    return datetime.strptime(string, '%d.%m.%Y').strftime('%Y-%m-%d')


def convert_number(string) -> str:
    # Convert integers & floats
    string = str(string)

    # Check if there's a dot AND a comma, eg '1.234,56'
    if '.' in string.split(',')[0]:
        string = string.replace('.', '')

    string = float(string.replace(',', '.'))
    integer = f'{string:.2f}'

    return str(integer)
