from operator import itemgetter

import pendulum

from ..components import Molecule
from .invoice import Invoice


class Invoices(Molecule):
    def __init__(self, invoices: dict) -> None:
        # Initialize 'Molecule' props
        super().__init__()

        # Build composite structure
        for data in invoices.values():
            self.add(Invoice(data))


    # ACCOUNTING methods

    def taxes(self):
        pass
