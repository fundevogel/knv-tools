# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from os.path import splitext

from pandas import concat, read_csv

from ..utils import dump_json, load_csv
from ..utils import date2string, number2string


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

    def date2string(self, string: str, reverse: bool = False) -> str:
        return date2string(string, reverse)


    def number2string(self, string: str) -> str:
        return number2string(string)


    def normalize(self, string: str) -> str:
        return str(string).replace('.0', '') if str(string) != 'nan' else ''
