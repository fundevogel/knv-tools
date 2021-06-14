from operator import itemgetter

import pendulum

from ..waypoint import Waypoint
from .expense import Expense
from .invoice import Invoice
from .revenue import Revenue


class Invoices(Waypoint):
    def __init__(self, invoices: dict) -> None:
        # Initialize 'Molecule' props
        super().__init__()

        # Build composite structure
        for data in invoices.values():
            self.add(self.invoice_types[data['Rechnungsart']](data))


    # ACCOUNTING methods

    # def taxes(self):
    #     pass
