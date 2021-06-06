# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import abstractmethod
from typing import List

from .abstract import Component


class Molecule(Component):
    def __init__(self) -> None:
        self._children: List[Component] = []


    # ADMINISTRATION methods

    def add(self, component):
        self._children.append(component)
        component.parent = self


    def remove(self, component):
        self._children.remove(component)
        component.parent = None


    def filter(self, year: str, quarter: str = None) -> list:
        # Determine appropriate month range
        month_range = self.month_range(quarter)

        # Filter out children not matching given year and quarter
        return [child for child in self._children if child.year() == year and int(child.month()) in month_range]


    # CORE methods

    @abstractmethod
    def export(self) -> None:
        pass


    # ACCOUNTING methods

    def get_revenues(self, year: str, quarter: str = None) -> dict:
        data = {}

        # Select orders matching given time period
        for item in self.filter(year, quarter):
            if item.month() not in data:
                data[item.month()] = []

            data[item.month()].append(item.get_revenues())

        # Assign data to respective month
        data = {int(month): sum(revenues) for month, revenues in data.items()}

        # Determine appropriate month range
        month_range = self.month_range(quarter)

        # Fill missing months with zeroes
        for i in month_range:
            if i not in data:
                data[i] = float(0)

        # Sort results
        return {k: data[k] for k in sorted(data)}


    # ACCOUNTING HELPER methods

    def month_range(self, quarter) -> list:
        return range(1, 13) if quarter is None else [month + 3 * (int(quarter) - 1) for month in [1, 2, 3]]


class Atom(Component):
    # CORE methods

    @abstractmethod
    def export(self) -> None:
        pass


    # ACCOUNTING methods

    @abstractmethod
    def get_revenues(self) -> None:
        pass
