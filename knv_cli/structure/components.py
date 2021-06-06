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


class Atom(Component):
    # CORE methods

    @abstractmethod
    def export(self) -> None:
        pass
