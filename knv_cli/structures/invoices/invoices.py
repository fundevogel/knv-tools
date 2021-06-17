# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from operator import itemgetter

from ..waypoint import Waypoint
from .expense import Expense
from .invoice import Invoice
from .revenue import Revenue


class Invoices(Waypoint):
    def load(self, data: tuple) -> None:
        invoices, = data

        # Build composite structure
        for item in invoices.values():
            self.add(self.invoice_types[item['Rechnungsart']](item))


    def assigned(self) -> Invoices:
        handler = Invoices()

        for child in self._children:
            if child.assigned(): handler.add(child)

        return handler


    def unassigned(self) -> Invoices:
        handler = Invoices()

        for child in self._children:
            if not child.assigned(): handler.add(child)

        return handler
