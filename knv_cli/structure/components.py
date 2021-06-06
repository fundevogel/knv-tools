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


    def filter(self, year: str, quarter: str = None) -> Molecule:
        if quarter is not None:
            months = [month + 3 * (int(quarter) - 1) for month in [1, 2, 3]]

        for child in self._children:
            # Remove children with unmatching ..
            # (1) .. year
            if child.year() != year:
                self.remove(child)

                # Move to next child
                continue

            # (2) .. month
            if quarter is not None:
                if int(child.month()) not in months:
                    self.remove(child)

        return self


    # CORE methods

    @abstractmethod
    def export(self) -> None:
        pass


    # ACCOUNTING methods

    def get_revenues(self, year: str, quarter: str = None) -> dict:
        data = {}

        # Select orders matching given time period
        for item in self.filter(year, quarter)._children:
            if item.month() not in data:
                data[item.month()] = []

            data[item.month()].append(item.get_revenues())

        # Assign data to respective month
        data = {int(month): sum(revenues) for month, revenues in data.items()}

        # Fill missing months with zeroes
        # (1) .. generally including all months
        month_range = range(1, 13)

        # (2) .. or only those for given quarter
        if quarter is not None:
            month_range = range(self.qm(quarter), self.qm(quarter, True) + 1)

        # (3) .. execute!
        for i in month_range:
            if i not in data:
                data[i] = 0

        # Sort results
        return {k: data[k] for k in sorted(data)}


    # ACCOUNTING HELPER methods

    def qm(self, quarter: str, last: bool = False) -> int:
        # Determine if first or last q(uarter) m(onth)
        start = 1 if not last else 3

        return start + 3 * (int(quarter) - 1)


class Atom(Component):
    # CORE methods

    @abstractmethod
    def export(self) -> None:
        pass


    # ACCOUNTING methods

    @abstractmethod
    def get_revenues(self) -> None:
        pass
