from abc import abstractmethod

from ...utils import number2string
from ..invoices.invoice import Invoice
from ..orders.order import Order
from ..waypoint import Waypoint


class Payment(Waypoint):
    def __init__(self, data: dict) -> None:
        # Initialize 'Waypoint' props
        super().__init__()

        self.data = data


    # CORE methods

    @abstractmethod
    def identifier(self) -> str:
        pass


    def export(self) -> list:
        return self.data


    def assign(self, identifier: str) -> None:
        if identifier not in ['sicher', 'fast sicher', 'unsicher', 'manuell']:
            raise Exception

        self.data['Treffer'] = identifier


    def assigned(self) -> bool:
        return self.data['Treffer'] in ['sicher', 'manuell']


    def amount(self) -> str:
        return self.data['Betrag']


    def invoice_numbers(self) -> list:
        return [child.identifier() for child in self._children]


    def order_numbers(self) -> list:
        return self.data['Auftragsnummer'] if isinstance(self.data['Auftragsnummer'], list) else []


    # INVOICE methods

    def invoices_amount(self) -> str:
        return self.number2string(sum([float(child.amount()) for child in self._children]))
