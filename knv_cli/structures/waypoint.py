from abc import abstractmethod
from operator import itemgetter
from typing import List

import pendulum

from .framework import Framework
from .invoices.expense import Expense
from .invoices.revenue import Revenue


class Waypoint(Framework):
    # PROPS

    invoice_types = {
        # Expenses
        'BWD': Expense,
        'EDV': Expense,
        'Sammelrechnung': Expense,
        # Revenues
        'Kundenrechnung': Revenue,
    }


    def __init__(self, *data) -> None:
        # Initialize child list
        self._children: List[Framework] = []

        # Load data (if provided)
        if data: self.load(data)


    # ADMINISTRATION methods

    def add(self, component: Framework):
        self._children.append(component)
        component.parent = self


    def remove(self, component: Framework):
        self._children.remove(component)
        component.parent = None


    def has_children(self) -> bool:
        return len(self._children) > 0


    def filterBy(self, identifier: str, year: str = None, period: str = None) -> list:
        # Ensure validity of provided time period
        if identifier not in ['year', 'quarter', 'month']: raise Exception

        # Fallback to current year
        if year is None: year = pendulum.today().year

        handler = type(self)()

        for child in self._children:
            # Sort out if year not matching
            if child.year() != str(year): continue

            # Add children as specified by ..
            # (1) .. year
            if identifier == 'year':
                handler.add(child)

            # (2) .. quarter
            if identifier == 'quarter' and int(child.month()) in [month + 3 * (int(period) - 1) for month in [1, 2, 3]]:
                handler.add(child)

            # (3) .. month
            if identifier == 'month' and child.month() == str(period).zfill(2):
                handler.add(child)

        return handler


    def has(self, number: str) -> bool:
        return number in self.identifiers()


    def get(self, number: str) -> dict:
        for child in self._children:
            if number == child.identifier(): return child

        return {}


    # CORE methods

    @abstractmethod
    def load(self, data) -> None:
        pass


    def export(self) -> list:
        data = []

        for child in self._children:
            data.append(child.export())

        # Sort by date
        data.sort(key=itemgetter('Datum'))

        return data


    def identifiers(self) -> list:
        return [child.identifier() for child in self._children]
