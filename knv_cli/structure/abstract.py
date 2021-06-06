# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import ABCMeta, abstractmethod


class Component(metaclass=ABCMeta):
    # PROPS

    data = None

    @property
    def parent(self) -> Component:
        return self._parent


    @parent.setter
    def parent(self, parent: Component):
        self._parent = parent


    # CORE methods

    @abstractmethod
    def export(self) -> None:
        pass


    # HELPER methods

    def date(self) -> str:
        return self.data['Datum']


    def year(self) -> str:
        return self.data['Datum'].split('-')[0]


    def month(self) -> str:
        return self.data['Datum'].split('-')[1]


    def day(self) -> str:
        return self.data['Datum'].split('-')[-1]