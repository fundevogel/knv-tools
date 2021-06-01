from abc import ABC
from datetime import datetime


class BaseClass(ABC):
    def __init__(self):
        pass

    # HELPER methods

    def convert_date(self, string: str) -> str:
        return datetime.strptime(string, '%d.%m.%Y').strftime('%Y-%m-%d')


    def convert_number(self, string: str) -> str:
        # Convert to string & clear whitespaces
        string = str(string).strip()

        # Take care of thousands separator, as in '1.234,56'
        if '.' in string and ',' in string:
            string = string.replace('.', '')

        string = float(string.replace(',', '.'))
        integer = f'{string:.2f}'

        return str(integer)
