from operator import itemgetter

from ..waypoint import Waypoint
from .expense import Expense
from .invoice import Invoice
from .revenue import Revenue


class Invoices(Waypoint):
    def load(self, data: tuple) -> None:
        invoices = data

        # Build composite structure
        for item in invoices.values():
            self.add(self.invoice_types[item['Rechnungsart']](item))
