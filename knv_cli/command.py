# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import abstractmethod
from hashlib import md5
from operator import itemgetter
from os.path import splitext

from pandas import concat, read_csv

from .base import BaseClass
from .utils import load_json


class Command(BaseClass):
    # CSV options
    csv_encoding = 'iso-8859-1'
    csv_delimiter = ';'
    csv_skiprows = None
    csv_low_memory = False


    def __init__(self, data_files: list = None):
        if data_files:
            self.load(data_files)


    # DATA methods

    def load(self, data_files: list) -> Command:
        self.data = {}

        # Assume filetype in order to either proceed with ..
        extension = splitext(data_files[0])[1]

        if extension == '.json':
            self.data = load_json(data_files)

        else:
            self.data = self.load_data(data_files)

        return self


    def load_data(self, data_files: list):
        return self.load_csv(data_files)


    def load_csv(self, csv_files: list):
        try:
            df = concat(map(lambda file: read_csv(
                file,
                sep=self.csv_delimiter,
                encoding=self.csv_encoding,
                skiprows=self.csv_skiprows,
                low_memory=self.csv_low_memory,
            ), csv_files))

        except ValueError:
            return []

        return self.process_data(df.to_dict('records'))


    @abstractmethod
    def process_data(self, data: list):
        pass


    # DATA HELPER methods

    def convert_nan(self, string: str) -> str:
        return str(string) if str(string) != 'nan' else ''
