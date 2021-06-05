# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import abstractmethod
from os.path import splitext

from pandas import concat, read_csv

from ..base import BaseClass
from ..utils import load_csv, dump_json


class Processor(BaseClass):
    # PROPS

    _data = None

    # CSV options
    csv_delimiter = ';'
    csv_encoding = 'iso-8859-1'
    csv_skiprows = None


    # I/O methods

    def load_data(self, data: list) -> Processor:
        self._data = data

        return self


    def load_files(self, files: list) -> Processor:
        self._data = self._load_files(files)

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
