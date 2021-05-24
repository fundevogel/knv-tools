from abc import ABC, abstractmethod
from datetime import datetime
from hashlib import md5
from operator import itemgetter

from pandas import concat, read_csv


class BaseClass(ABC):
    # PROPS

    data = None

    # CSV options
    encoding = 'iso-8859-1'
    delimiter = ';'
    skiprows = None


    def __init__(self, csv_files: list = None):
        if csv_files:
            self.load_csv(csv_files)


    # DATA methods

    def load_csv(self, csv_files: list) -> list:
        try:
            df = concat(map(lambda file: read_csv(
                file,
                sep=self.delimiter,
                encoding=self.encoding,
                low_memory=False,
                skiprows=self.skiprows
            ), csv_files))

        except ValueError:
            return []

        self.data = self.process_data(df.to_dict('records'))


    @abstractmethod
    def process_data(self, data: list):
        pass


    # HELPER methods

    def convert_date(self, string: str) -> str:
        return datetime.strptime(string, '%d.%m.%Y').strftime('%Y-%m-%d')


    def convert_number(self, string) -> str:
        # Convert integers & floats
        string = str(string)

        # Take care of thousands separator, as in '1.234,56'
        if '.' in string and ',' in string:
            string = string.replace('.', '')

        string = float(string.replace(',', '.'))
        integer = f'{string:.2f}'

        return str(integer)


    def convert_tax_rate(self, string: str) -> str:
        return str(string).replace(',00', '') + '%'
