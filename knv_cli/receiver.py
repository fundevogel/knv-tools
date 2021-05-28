import json

from abc import ABC, abstractmethod
from datetime import datetime
from hashlib import md5
from operator import itemgetter

from pandas import concat, read_csv

from .utils import load_json


class Receiver(ABC):
    # PROPS

    data = None


    def __init__(self, data_files: list = None) -> None:
        if data_files:
            self.load_data(data_files)


    # DATA methods

    def load_data(self, data_files: list = None) -> None:
        self.data = load_json(data_files)


    @abstractmethod
    def init(self, force: bool = False) -> None:
        pass
