from ..invoices.invoice import Invoice
from ..orders.order import Order
from .payments import Payments
from .payment import Payment


class VolksbankPayments(Payments):
    def __init__(self, payments: dict, orders: dict, invoices: dict) -> None:
        # Initialize 'Molecule' props
        super().__init__()

        for data in payments.values():
            payment = Payment(data)

            # Determine matching invoices & orders
            # (1) Find matching invoice(s) for payment, while ..
            matched_invoices = []

            # .. only considering valid (= currently available) invoices
            if isinstance(data['Rechnungen'], list):
                matched_invoices = [Invoice(invoices[invoice]) for invoice in data['Rechnungen'] if invoice in invoices]

            # (2) Find matching order(s) for payment, while ..
            matched_orders = []

            # .. only considering valid (= currently available) orders
            if isinstance(data['Auftrag'], list):
                matched_orders = [Order(orders[order_number]) for order_number in data['Auftrag'] if order_number in orders]

            # Apply matching invoices & orders
            # (1) Add invoices
            for invoice in matched_invoices:
                payment.add(invoice)

            # (2) Add orders
            for order in matched_orders:
                payment.add(order)

            # Determine level of accuracy
            # (1) Check if payment sum equals sum of orders ..
            if payment.revenues() == payment.order_revenues():
                # .. which is a one-to-one hit
                payment.mark('fast sicher')

            # (2) Check if payment sum equals sum of invoices ..
            if payment.revenues() == payment.invoice_revenues():
                # .. which is a one-to-one hit
                payment.mark('sicher')

            # Add payment
            self.add(payment)


    # MATCHING HELPER methods

    def extract_taxes(self, invoice_candidates: list, invoices: dict) -> dict:
        taxes = {}

        for invoice_number, invoice in invoices.items():
            if invoice_number in invoice_candidates and isinstance(invoice['Steuern'], dict):
                for tax_rate, tax_amount in invoice['Steuern'].items():
                    if tax_rate not in taxes:
                        taxes[tax_rate] = '0'

                    taxes[tax_rate] = self.number2string(float(taxes[tax_rate]) + float(tax_amount))

        return taxes
