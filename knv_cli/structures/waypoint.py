from operator import itemgetter
from typing import List

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


    def __init__(self) -> None:
        self._children: List[Framework] = []


    # ADMINISTRATION methods

    def add(self, component: Framework):
        self._children.append(component)
        component.parent = self


    def remove(self, component: Framework):
        self._children.remove(component)
        component.parent = None


    def has_children(self) -> bool:
        return len(self._children) > 0


    def filter(self, year: str, quarter: str = None) -> list:
        # Determine appropriate month range
        month_range = self.month_range(quarter)

        # Filter out children not matching given year and quarter
        return [child for child in self._children if child.year() == year and int(child.month()) in month_range]


    def has(self, number: str) -> bool:
        return number in self.identifiers()


    def get(self, number: str) -> dict:
        for child in self._children:
            if number == child.identifier(): return child

        return {}


    # CORE methods

    def export(self) -> list:
        data = []

        for child in self._children:
            data.append(child.export())

        # Sort by date
        data.sort(key=itemgetter('Datum'))

        return data


    # ACCOUNTING methods

    def amount(self, year: str, quarter: str = None) -> dict:
        data = {}

        # Select orders matching given time period
        for item in self.filter(year, quarter):
            if item.month() not in data:
                data[item.month()] = []

            data[item.month()].append(float(item.amount()))

        # Assign data to respective month
        data = {int(month): sum(amount) for month, amount in data.items()}

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


    # HELPER methods

    def identifiers(self) -> list:
        return [child.identifier() for child in self._children]
