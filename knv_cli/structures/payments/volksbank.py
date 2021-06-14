from hashlib import md5

from ..invoices.expense import Expense
from ..invoices.revenue import Revenue
from .payments import Payments
from .payment import Payment


class VolksbankPayments(Payments):
    # CORE methods

    def process(self, payments: dict, orders: dict, invoices: dict) -> None:
        # Build composite structure
        for data in payments.values():
            # Determine matching invoices & orders
            matched_invoices = []
            matched_orders = []

            # (1) Find matching invoices
            if isinstance(data['Rechnungsnummer'], list):
                # Consider only valid (= currently available) invoices
                matched_invoices = [invoice_number for invoice_number in data['Rechnungsnummer'] if invoice_number in invoices]

            # (2) Find matching orders
            if isinstance(data['Auftragsnummer'], list):
                # Consider only valid (= currently available) orders
                matched_orders = [order_number for order_number in data['Auftragsnummer'] if order_number in orders]

            # Apply matching invoices & orders
            # (1) Add invoices
            if matched_invoices: data['Rechnungsnummer'] = matched_invoices

            # (2) Add orders
            if matched_orders: data['Auftragsnummer'] = matched_orders

            # Initialize payment
            payment = VolksbankPayment(data)

            # Add invoices to payment
            for invoice_number in matched_invoices:
                invoice = invoices[invoice_number]
                payment.add(self.invoice_types[invoice['Rechnungsart']](invoice))

            # Determine if invoice(s) amount to payment amount ..
            if payment.amount() == payment.invoices_amount():
                # .. which makes them a one-to-one hit
                payment.assign('sicher')

            # Add payment
            self.add(payment)


class VolksbankPayment(Payment):
    # CORE methods

    def identifier(self) -> str:
        # Build unique string based on various properties
        return md5(str([
            self.data['Datum'],
            self.data['Name'],
            self.data['Brutto'],
            self.data['Rohdaten'],
        ]).encode('utf-8')).hexdigest()


    # ACCOUNTING methods

    def tax_report(self) -> dict:
        # Prepare output data
        data = {
            'Datum': self.data['Datum'],
            'Art': self.data['Art'],
            'Treffer': self.data['Treffer'],
            'Auftragsnummer': 'nicht zugeordnet',
            'Rechnungsnummer': 'nicht zugeordnet',
            'Name': self.data['Name'],
            'Betrag': self.data['Betrag'],
            'Verwendungszweck': self.data['Verwendungszweck'],
        }

        # Add order & invoice numbers as strings
        for identifier in ['Auftragsnummer', 'Rechnungsnummer']:
            if isinstance(self.data[identifier], list):
                data[identifier] = ';'.join(self.data[identifier])

        # Add taxes
        for rate, amount in self.taxes().items():
            data[rate + ' MwSt'] = amount

        return data
