# This module contains a class for processing & working with
# 'Aktivitäten', as exported from PayPal™
# See https://www.paypal.com/de/smarthelp/article/FAQ1007


from operator import itemgetter
from os.path import join

from .gateway import Gateway


class Paypal(Gateway):
    # PROPS

    identifier = 'Transaktion'
    regex = 'Download*.CSV'

    # CSV options
    csv_encoding='utf-8'
    csv_delimiter=','


    # DATA methods

    def process_payments(self, data: list) -> list:
        '''
        Processes 'Download*.CSV' files
        '''

        codes = set()
        payments = []

        for item in data:
            # Skip withdrawals
            if item['Brutto'][:1] == '-':
                self._blocked_payments.append(payment)
                continue

            # Assign identifier
            code = item['Transaktionscode']

            payment = {}

            payment['ID'] = 'nicht zugeordnet'
            payment['Datum'] = self.convert_date(item['Datum'])
            payment['Vorgang'] = 'nicht zugeordnet'
            payment['Name'] = item['Name']
            payment['Email'] = item['Absender E-Mail-Adresse']
            payment['Bestellung'] = 'keine Angabe'
            payment['Bestellsumme'] = 'keine Angabe'
            payment['Versand'] = 'keine Angabe'
            payment['Brutto'] = self.convert_number(item['Brutto'])
            payment['Gebühr'] = self.convert_number(item['Gebühr'])
            payment['Netto'] = self.convert_number(item['Netto'])
            payment['Währung'] = item['Währung']
            payment['Steuern'] = 'keine Angabe'
            payment['Transaktion'] = code
            payment['Dienstleister'] = 'PayPal'

            if item['Typ'] == 'Allgemeine Zahlung':
                payment['Zahlungsart'] = 'Überweisung'

            if code not in codes:
                codes.add(code)
                payments.append(payment)

        return payments


    def get(self, transaction: str) -> dict:
        for payment in self.data:
            if payment['Transaktion'] == transaction:
                return payment

        return {}


    # MATCHING methods

    def match_payments(self, data: list) -> None:
        results = []

        for payment in self.data:
            # Assign invoice number(s) to each payment
            # (1) Find matching order for current payment
            matching_order = self.match_orders(payment, data)

            if not matching_order:
                results.append(payment)
                continue

            # (2) Check invoice number(s) for matching order
            matching_invoices = []

            if isinstance(matching_order['Bestellung'], dict):
                matching_invoices = list(matching_order['Bestellung'].keys())

            # Skip if no matching invoice numbers
            if not matching_invoices:
                results.append(payment)
                continue

            # Store data
            # (1) Apply matching order number
            payment['ID'] = matching_order['ID']

            # (2) Add invoice number(s) to payment data
            payment['Vorgang'] = matching_invoices

            # (3) Add total order & shipping cost
            payment['Bestellung'] = matching_order['Bestellung']
            payment['Bestellsumme'] = matching_order['Bestellsumme']
            payment['Versand'] = matching_order['Versand']
            payment['Steuern'] = matching_order['Steuern']

            # (4) Save matched payment
            results.append(payment)

        self._matched_payments = results


    def match_orders(self, payment, orders) -> dict:
        # Determine matching orders by highest probability
        candidates = []

        for order in orders:
            # (1) Check if transaction code matches ..
            if payment['Transaktion'] == order['Abwicklung']['Transaktionscode']:
                # .. in which case there's a one-to-one match
                return order

            # (2) Check for common properties of payment and orders within one day
            for days in range(1, 7):
                candidate = self.approximate_order(payment, order, days)

                if candidate:
                    break

            if candidate:
                candidates.append(candidate)

        matches = sorted(candidates, key=itemgetter(1), reverse=True)

        if matches:
            return matches[0][0]

        return {}


    def approximate_order(self, payment: dict, order: dict, days: int) -> tuple:
        candidate = ()

        costs_match = payment['Brutto'] == order['Gesamtbetrag']
        dates_match = self.match_dates(payment['Datum'], order['Datum'], days)

        if costs_match and dates_match:
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

            # (2) .. by comparing their mail addresses
            if str(payment['Email']).lower() == str(order['Email']).lower():
                hits += 5

            # (3) .. by comparing their home / shipping address
            # TODO: Use address details for comparison
            # Orders:
            # rechnungaddressstreet	rechnungaddresshousenumber	rechnungaddresszipcode	rechnungaddresscity
            # Paypal:
            # Adresszeile 1 (= street, number) Ort PLZ

            # TODO: If that doesn't cut it, use data from available invoice files
            # See 'R20210031789'

            candidate = (order, hits)

        return candidate


    # MATCHING OUTPUT methods

    def matched_payments(self, csv_compatible: bool = False) -> list:
        if csv_compatible:
            # Output 'flat' data, also removing irrelevant information ..
            csv_data = []

            for item in self._matched_payments:
                # .. like unique transaction identifiers
                del item['Transaktion']

                # Convert invoice numbers to string
                if item['Vorgang'] != 'nicht zugeordnet':
                    item['Vorgang'] = ';'.join(item['Vorgang'])

                # Extract tax rates & their respective amount
                if isinstance(item['Steuern'], dict):
                    # Add taxe rates
                    for tax_rate, tax_amount in item['Steuern'].items():
                        item[tax_rate + ' MwSt'] = tax_amount

                    # Add share of payment fees for each tax rate
                    # (1) Calculate total amount of taxes
                    total_taxes = [taxes for invoice_number, taxes in item['Steuern'].items() if invoice_number in item['Vorgang']]

                    # (2) Calculate share for each tax rate
                    # for tax_rate, tax_amount in item['Steuern'].items():
                    #     ratio = total_taxes / tax_amount
                    #     share = float(item['Gebühr'].replace('-', '')) / ratio

                    #     item['Gebührenanteil ' + tax_rate] = self.convert_number(share)

                csv_data.append(item)

            return sorted(csv_data, key=itemgetter('Datum'))

        return sorted(self._matched_payments, key=itemgetter('Datum'))


    # MATCHING OUTPUT HELPER methods

    def get_total_taxes(self, taxes) -> str:
        return sum([float(tax_amount) for tax_amount in taxes.values()])
