from operator import itemgetter

from ..invoices.invoice import Invoice
from ..orders.order import Order
from .payments import Payments
from .payment import Payment


class PaypalPayments(Payments):
    def __init__(self, payments: dict, orders: dict, invoices: dict) -> None:
        # Initialize 'Molecule' props
        super().__init__()

        # Build composite structure
        for data in payments.values():
            # Ground zero
            payment = None

            # Search for matching order
            matching_order = {}

            # (1) Distinguish between online shop payments ..
            if data['Zahlungsart'] == 'Shopbestellung':
                # Find matching order for current payment
                for order in orders.values():
                    # .. whose transaction codes will match ..
                    if data['Transaktion'] == order['Abwicklung']['Transaktionscode']:
                        # .. which represents a one-to-one match
                        data['Treffer'] = 'sicher'

                        # Save result
                        matching_order = order

                        # Abort iterations
                        break

            # (2) .. and regular payments
            else:
                # Find matching order, but this will almost always fail
                matching_order = self.match_orders(data, orders)

            # Search for matching invoice(s)
            matching_invoices = []

            if matching_order and isinstance(matching_order, dict):
                # Add order number
                data['ID'] = matching_order['ID']

                # (2) Add invoice numbers
                # TODO: Check
                # - matching total costs for all invoices
                # - individual costs
                # that way we could increase accuracy to at least 'fast sicher'
                if isinstance(matching_order['Rechnungen'], dict):
                    matching_invoices = list(matching_order['Rechnungen'].keys())

                # Create payment & add matching order
                payment = Payment(data)
                payment.add(Order(matching_order))

            # .. without matching order, this can only be achieved by going through invoices
            else:
                matching_invoice = self.match_invoices(data, invoices)

                if matching_invoice:
                    matching_invoices = [matching_invoice['Vorgang']]

            # Initialize payment (if necessary)
            if payment is None:
                payment = Payment(data)

            # Skip if no matching invoice numbers
            if matching_invoices:
                # Ensure validity & availability of each invoice
                for invoice in [invoices[invoice] for invoice in matching_invoices if invoice in invoices]:
                    # Add invoices to payment
                    payment.add(Invoice(invoice))

            self.add(payment)


    # CORE methods

    def export(self) -> list:
        data = []

        for child in self._children:
            data.append(child.export())

        return data


    # MATCHING methods

    def match_orders(self, payment: dict, orders: dict) -> dict:
        for order in orders.values():
            candidates = []

            # Check if payment amount matches order costs, and only then ..
            if payment['Brutto'] == order['Gesamtbetrag']:
                # .. for last two weeks ..
                for days in range(1, 14):
                    # .. determine matching orders by highest probability, but only those ..
                    candidate = ()

                    # .. matching
                    if self.match_dates(payment['Datum'], order['Datum'], days, True):
                        # Let them fight ..
                        hits = 0

                        # Determine chance of match for given payment & order ..
                        # (1) .. by comparing their names
                        payment_names = payment['Name'].split(' ')
                        payment_first, payment_last = payment_names[0], payment_names[-1]
                        order_first, order_last = (order['Vorname'], order['Nachname'])

                        # Add one point for matching first name, since that's more likely, but ..
                        if payment_first.lower() == order_first.lower():
                            hits += 1

                        # .. may be overridden by matching last name
                        if payment_last.lower() == order_last.lower():
                            hits += 2

                        # (2) .. by comparing their contact details
                        if payment['Telefon'].lower() == order['Telefon'].lower():
                            hits += 5

                        if payment['Email'].lower() == order['Email'].lower():
                            hits += 5

                        # (3) .. by comparing their home / shipping address
                        if order['Straße'].lower() in order['Anschrift'].lower():
                            hits += 2

                        if payment['PLZ'] == order['PLZ']:
                            hits += 1

                        candidate = (order, hits)

                    if candidate:
                        candidates.append(candidate)

            if candidates:
                # Sort candidates by hits ..
                candidates.sort(key=itemgetter(1), reverse=True)

                # .. and select most promising one
                return candidates[0][0]

        return {}


    def match_invoices(self, payment: dict, invoices: dict) -> dict:
        for invoice in invoices.values():
            # Check if payment amount matches invoice costs, and only then ..
            if payment['Brutto'] == invoice['Gesamtbetrag']:
                # .. within next two months ..
                for days in range(1, 60):
                    # check if payment date matches invoices within two months, and only then ..
                    if self.match_dates(payment['Datum'], invoice['Datum'], days):
                        # .. return matching invoice
                        return invoice

        return {}


    # # MATCHING OUTPUT methods

    # def matched_payments(self, csv_compatible: bool = False) -> list:
    #     if csv_compatible:
    #         # Output 'flat' data, also removing irrelevant information ..
    #         csv_data = []

    #         for item in self._matched_payments:
    #             # .. like unique transaction identifiers
    #             del item['Transaktion']

    #             # Convert invoice numbers to string
    #             if isinstance(item['Rechnungen'], list):
    #                 item['Rechnungen'] = ';'.join(item['Rechnungen'])

    #             # Extract tax rates & their respective amount
    #             if isinstance(item['Steuern'], dict):
    #                 # Add taxe rates
    #                 taxes = {}

    #                 # for invoice_number,
    #                 for tax_rate, tax_amount in item['Steuern'].items():
    #                     item[tax_rate + ' MwSt'] = tax_amount

    #                 # Add share of payment fees for each tax rate
    #                 # (1) Calculate total amount of taxes
    #                 total_taxes = [taxes for invoice_number, taxes in item['Steuern'].items() if invoice_number in item['Rechnungen']]


    #                 # (2) Calculate share for each tax rate
    #                 # for tax_rate, tax_amount in item['Steuern'].items():
    #                 #     ratio = total_taxes / tax_amount
    #                 #     share = float(item['Gebühr'].replace('-', '')) / ratio

    #                 #     item['Gebührenanteil ' + tax_rate] = self.number2string(share)

    #             csv_data.append(item)

    #         return sorted(csv_data, key=itemgetter('Datum'))

    #     return sorted(self._matched_payments, key=itemgetter('Datum'))
