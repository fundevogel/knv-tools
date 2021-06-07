from ..invoices.invoice import Invoice
from ..orders.order import Order
from .payments import Payments
from .payment import Payment


class VolksbankPayments(Payments):
    def __init__(self, payments: dict, orders: dict, invoices: dict) -> None:
        # Initialize 'Molecule' props
        super().__init__()

        for data in payments.values():
            payment = None

            # Find matching invoices for each invoice candidate
            if isinstance(data['Rechnungen'], list):
                # Consider only valid (= currently available) invoices
                data['Rechnungen'] = [invoice for invoice in data['Rechnungen'] if invoice in invoices]

                if not data['Rechnungen']:
                    # Use other criteria since all detected invoice numbers were invalid
                    data['Rechnungen'] = 'nicht zugeordnet'

                else:
                    # Check if extracted invoices sum up to total order cost ..
                    if self.compare_invoice_total(data, invoices):
                        # .. which is a one-to-one hit
                        data['Treffer'] = 'sicher'

                        payment = Payment(data)

                        # Add invoices to payment & payment to payments
                        for invoice in [invoices[invoice] for invoice in data['Rechnungen']]:
                            payment.add(Invoice(invoice))

                        self.add(payment)

                        # Move on to next payment
                        continue

                    # TODO: Yeah, what if not?
                    else:
                        pass

            # Find matching order(s) for each order candidate
            matching_orders = []

            if isinstance(data['Auftrag'], list):
                # Consider only valid (= currently available) orders
                matching_orders = [orders[order_number] for order_number in data['Auftrag'] if order_number in orders]

            # Apply matching order number(s)
            if matching_orders:
                # Consider only valid (= currently available) orders
                data['Auftrag'] = [order['ID'] for order in matching_orders if order['ID'] in orders]

                data['Rechnungen'] = []

                # Fill up on potential invoices ..
                for order_number in data['Auftrag']:
                    data['Rechnungen'] += [invoice_number for invoice_number in orders[order_number]['Rechnungen'].keys() if isinstance(orders[order_number]['Rechnungen'], dict)]

                if not data['Rechnungen']:
                    # Use other criteria since all detected invoice numbers were invalid
                    data['Rechnungen'] = 'nicht zugeordnet'

                else:
                    # .. and here we go again, checking if extracted invoices sum up to total order cost ..
                    if self.compare_invoice_total(data, invoices):
                        # .. which is (probably) a one-to-one hit
                        data['Treffer'] = 'fast sicher'

                        # Ensure validity & availability of each invoice
                        payment = Payment(data)

                        # Add invoices to payment & payment to payments
                        for invoice in [invoices[invoice] for invoice in data['Rechnungen'] if invoice in invoices]:
                            payment.add(Invoice(invoice))

                        self.add(payment)

                        # Move on to next payment
                        continue

                    # TODO: Yeah, what if not?
                    else:
                        pass

            # Initialize payment (if necessary)
            if payment is None:
                payment = Payment(data)

            self.add(payment)


    # MATCHING HELPER methods

    def compare_invoice_total(self, payment: dict, invoices: dict) -> bool:
        return payment['Betrag'] == self.number2string(sum([float(invoices[invoice]['Gesamtbetrag']) for invoice in payment['Rechnungen']]))


    def extract_taxes(self, invoice_candidates: list, invoices: dict) -> dict:
        taxes = {}

        for invoice_number, invoice in invoices.items():
            if invoice_number in invoice_candidates and isinstance(invoice['Steuern'], dict):
                for tax_rate, tax_amount in invoice['Steuern'].items():
                    if tax_rate not in taxes:
                        taxes[tax_rate] = '0'

                    taxes[tax_rate] = self.number2string(float(taxes[tax_rate]) + float(tax_amount))

        return taxes
