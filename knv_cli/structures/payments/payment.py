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


    # ACCOUNTING methods

    @abstractmethod
    def tax_report(self) -> None:
        pass


    def taxes(self) -> dict:
        data = {}

        for child in self._children:
            for rate, amount in child.taxes().items():
                if rate not in data:
                    data[rate] = 0

                data[rate] = data[rate] + float(amount)

        return {k: self.number2string(v) for k, v in data.items()}


    # INVOICE methods

    def invoices_amount(self) -> str:
        return self.number2string(sum([float(child.amount()) for child in self._children]))
