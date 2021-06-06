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


    # CORE methods

    def export(self) -> list:
        data = []

        for child in self._children:
            data.append(child.export())

        return data


    # ACCOUNTING methods

    def get_taxes(self):
        pass
