# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import datetime
from os.path import splitext

from pandas import concat, read_csv

from ..utils import dump_json, load_csv, number2string


class Processor(metaclass=ABCMeta):
    # PROPS

    data = {}

    # CSV options
    csv_delimiter = ';'
    csv_encoding = 'iso-8859-1'
    csv_skiprows = None


    # I/O methods

    def load_data(self, data: list) -> Processor:
        self.data = data

        return self


    def load_files(self, files: list) -> Processor:
        self.data = self._load_files(files)

        return self


    def _load_files(self, files: list) -> list:
        # Check filetype
        extension = splitext(files[0])[1].lower()

        if extension != '.csv':
            raise Exception('Unsupported filetype: "{}"'.format(extension))

        return load_csv(files, self.csv_delimiter, self.csv_encoding, self.csv_skiprows)


    def dump_data(self) -> dict:
        return self.data


    def export_data(self, file: str) -> None:
        dump_json(self.data, file)


    # CORE methods

    @abstractmethod
    def process(self) -> Processor:
        pass


    # HELPER methods

    def convert_date(self, string: str, reverse: bool = False) -> str:
        # Convert little-endian + dot separator to big-endian + hyphen separator
        formats = ['%d.%m.%Y', '%Y-%m-%d']

        # .. unless told otherwise
        if reverse: formats.reverse()

        try:
            return datetime.strptime(string, formats[0]).strftime(formats[-1])

        except ValueError:
            # Give back unprocessed string if things go south
            return string


    def number2string(self, string: str) -> str:
        return number2string(string)


    def normalize(self, string: str) -> str:
        return str(string).replace('.0', '') if str(string) != 'nan' else ''
