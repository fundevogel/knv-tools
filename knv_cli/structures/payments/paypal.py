from datetime import datetime, timedelta
from operator import itemgetter

from ..invoices.invoice import Invoice
from ..orders.order import Order
from ..shared import get_contacts
from .payments import Payments
from .payment import Payment


class PaypalPayments(Payments):
    # CORE methods

    def process(self, payments: dict, orders: dict, invoices: dict) -> None:
        # Build composite structure
        for data in payments.values():
            # Search for matching order
            matched_order = {}

            # (1) Distinguish between online shop payments ..
            if data['Zahlungsart'] == 'Sofortzahlung':
                # Find matching order for current payment
                for order in orders.values():
                    # .. whose transaction codes will match ..
                    if data['Transaktion'] == order['Abwicklung']['Transaktionscode']:
                        # .. which represents a one-to-one match
                        data['Treffer'] = 'sicher'

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
                data['Auftragsnummer'] = matched_order['ID']

                if isinstance(matched_order['Rechnungen'], dict):
                    # Consider only valid (= currently available) invoices
                    matched_invoices = [invoice_number for invoice_number in list(matched_order['Rechnungen'].keys()) if invoice_number in invoices]

            # .. without matching order, this can only be achieved by going through invoices ..
            else:
                matched_invoice = self.match_invoice(data, invoices)

                # .. but never say never
                if matched_invoice: matched_invoices = [matched_invoice['Vorgang']]

            # Apply matching invoices
            if matched_invoices: data['Rechnungsnummer'] = matched_invoices

            # Initialize payment
            payment = PaypalPayment(data)

            # Add invoices to payment
            for invoice_number in matched_invoices:
                invoice = invoices[invoice_number]
                payment.add(self.invoice_types[invoice['Rechnungsart']](invoice))

            # Determine if invoice(s) amount to payment amount ..
            if not payment.assigned() and payment.amount() == payment.invoices_amount():
                # .. which makes them a one-to-one hit
                payment.assign('fast sicher')

            self.add(payment)


    # HELPER methods

    def match_order(self, payment: dict, orders: dict) -> dict:
        for order in orders.values():
            candidates = []

            # Check if payment amount matches order costs, and only then ..
            if payment['Betrag'] == order['Gesamtbetrag']:
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
        for invoice_data in invoices.values():
            invoice = self.invoice_types[invoice_data['Rechnungsart']](invoice_data)

            # Check if payment amount matches invoice costs, and only then ..
            if payment['Betrag'] == invoice.amount():
                # .. within next two months ..
                for days in range(1, 60):
                    # .. check if payment date matches invoices within two months, and only then ..
                    if self.match_dates(payment['Datum'], invoice.date(), days):
                        # .. return matching invoice
                        return invoice_data

        return {}


    def match_dates(self, test_date, start_date, days=1, before: bool = False) -> bool:
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=days)).strftime('%Y-%m-%d')

        return start_date >= test_date >= end_date if before else start_date <= test_date <= end_date


    # CONTACTS methods

    def contacts(self, cutoff_date: str = None, blocklist = []) -> list:
        return get_contacts(self._children, cutoff_date, blocklist)


class PaypalPayment(Payment):
    # CORE methods

    def identifier(self) -> str:
        # Use transaction number as identifier
        return self.data['Transaktion']


    def contact(self) -> dict:
        return {
            'Letzte Zahlung': self.data['Datum'],
            'Name': self.data['Name'],
            'Email': self.data['Email'],
            'Anschrift': self.data['Anschrift'],
            'PLZ': self.data['PLZ'],
            'Ort': self.data['Ort'],
            'Land': self.data['Land'],
            'Telefon': self.data['Telefon'],
        }


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
            'Gebühr': self.data['Gebühr'],
            'Netto': self.data['Netto'],
            'Transaktion': self.data['Transaktion'],
        }

        # Add order & invoice numbers as strings
        for identifier in ['Auftragsnummer', 'Rechnungsnummer']:
            if isinstance(self.data[identifier], list):
                data[identifier] = ';'.join(self.data[identifier])

        # Add taxes
        taxes = self.taxes()

        for rate, amount in taxes.items():
            data[rate + ' MwSt'] = amount

        # Add payment fee shares
        for rate, amount in taxes.items():
            # Calculate share for tax rates ..
            if float(amount) > 0:
                # .. if tax rate is available
                ratio = float(data['Betrag']) / float(amount)
                share = float(data['Gebühr']) / ratio

            # .. otherwise, add zero
            else: share = 0

            data['Gebührenanteil {} MwSt'.format(rate)] = self.number2string(share)

        return data
