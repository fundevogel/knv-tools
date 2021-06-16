# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import ABCMeta, abstractmethod

from ..utils import number2string


class Framework(metaclass=ABCMeta):
    # PROPS

    data = None


    # ADMINISTRATION methods

    @property
    def parent(self) -> Framework:
        return self._parent


    @parent.setter
    def parent(self, parent: Framework):
        self._parent = parent


    # CORE methods

    @abstractmethod
    def export(self) -> None:
        pass


    def date(self) -> str:
        return self.data['Datum']


    def year(self) -> str:
        return self.data['Datum'].split('-')[0]


    def month(self) -> str:
        return self.data['Datum'].split('-')[1]


    def day(self) -> str:
        return self.data['Datum'].split('-')[-1]


    # HELPER methods

    def number2string(self, string: str) -> str:
        return number2string(string)
