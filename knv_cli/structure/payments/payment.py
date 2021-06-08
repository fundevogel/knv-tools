from hashlib import md5

from ...utils import number2string
from ..components import Molecule
from ..invoices.invoice import Invoice
from ..orders.order import Order


class Payment(Molecule):
    accuracies = [
        'sicher',
        'fast sicher',
        'unsicher',
        'manuell',
    ]


    def __init__(self, data: dict) -> None:
        # Initialize 'Molecule' props
        super().__init__()

        self.data = data


    # CORE methods

    def export(self) -> list:
        return self.data


    # ACCOUNTING methods

    def revenues(self) -> float:
        amount = '0.00'

        # Paypal payments
        if 'Brutto' in self.data: amount = self.data['Brutto']

        # Volksbank payments
        if 'Betrag' in self.data: amount = self.data['Betrag']

        return float(amount)


    def invoice_revenues(self) -> float:
        amount = 0

        for invoice in self.invoices():
            amount += invoice.revenues()

        return float(number2string(amount))


    def order_revenues(self) -> float:
        amount = 0

        for invoice in self.orders():
            amount += invoice.revenues()

        return float(number2string(amount))


    def taxes(self) -> None:
        pass


    def mark(self, identifier: str) -> None:
        if identifier not in self.accuracies:
            raise Exception

        self.data['Treffer'] = identifier


    def is_paid(self) -> bool:
        return self.data['Treffer'] in ['sicher', 'manuell']


    def add_invoice_numbers(self, data) -> None:
        if not isinstance(self.data['Rechnungen'], list):
            self.data['Rechnungen'] = []

        for invoice_number in list(data):
            if invoice_number not in self.data['Rechnungen']:
                self.data['Rechnungen'].append(invoice_number)


    def add_order_numbers(self, data) -> None:
        if not isinstance(self.data['Auftrag'], list):
            self.data['Auftrag'] = []

        for order_number in list(data):
            if order_number not in self.data['Auftrag']:
                self.data['Auftrag'].append(order_number)


    # HELPER methods

    def identifier(self) -> str:
        # Use transaction number for PayPal payments
        if 'Transaktion' in self.data:
            return self.data['Transaktion']

        # Build unique string based on various properties
        return md5(str([
            self.data['Datum'],
            self.data['Name'],
            self.data['Betrag'],
            self.data['Rohdaten'],
        ]).encode('utf-8')).hexdigest()


    def invoice_numbers(self) -> list:
        return [child.identifier() for child in self._children if isinstance(child, Invoice)]


    def invoices(self) -> list:
        return [child for child in self._children if isinstance(child, Invoice)]


    def order_numbers(self) -> list:
        return [child.identifier() for child in self._children if isinstance(child, Order)]


    def orders(self) -> list:
        return [child for child in self._children if isinstance(child, Order)]
