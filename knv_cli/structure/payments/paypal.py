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
            payment = Payment(data)

            # Search for matching order
            matched_order = {}

            # (1) Distinguish between online shop payments ..
            if data['Zahlungsart'] == 'Shopbestellung':
                # Find matching order for current payment
                for order in orders.values():
                    # .. whose transaction codes will match ..
                    if payment.identifier() == order['Abwicklung']['Transaktionscode']:
                        # .. which represents a one-to-one match
                        payment.mark('sicher')

                        # Save result
                        matched_order = order

                        # Abort iterations
                        break

            # (2) .. and regular payments
            else:
                # Find matching order, but this will almost always fail
                matched_order = self.match_order(data, orders)

            # Determine matching invoices & orders
            # (1) Consider only valid (= currently available) orders
            matched_order = matched_order if matched_order and matched_order['ID'] in orders else {}

            # (2) Search for matching invoice(s)
            matched_invoices = []

            if matched_order:
                # Add matching order
                payment.add(Order(matched_order))
                payment.add_order_numbers(matched_order['ID'])

                if isinstance(matched_order['Rechnungen'], dict):
                    matched_invoices = list(matched_order['Rechnungen'].keys())

            # .. without matching order, this can only be achieved by going through invoices ..
            else:
                matched_invoice = self.match_invoice(data, invoices)

                # .. but never say never
                if matched_invoice: matched_invoices = [matched_invoice['Vorgang']]

            # Apply matching invoices, but ..
            if matched_invoices:
                # .. only considering valid (= currently available) invoices
                matched_invoices = matched_invoices = [Invoice(invoices[invoice]) for invoice in matched_invoices if invoice in invoices]

                # Add invoice number(s) to payment data
                payment.add_invoice_numbers(invoice.identifier() for invoice in matched_invoices)

                for invoice in matched_invoices:
                    # Add invoices to payment
                    payment.add(invoice)

            self.add(payment)


    # MATCHING methods

    def match_order(self, payment: dict, orders: dict) -> dict:
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


    def match_invoice(self, payment: dict, invoices: dict) -> dict:
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
