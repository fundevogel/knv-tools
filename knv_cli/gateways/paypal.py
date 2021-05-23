# This module contains a class for processing & working with
# 'Aktivitäten', as exported from PayPal™
# See https://www.paypal.com/de/smarthelp/article/FAQ1007


from operator import itemgetter
from os.path import join

from .payments import Payments


class Paypal(Payments):
    # PROPS

    identifier = 'Transaktion'
    regex = 'Download*.CSV'

    # CSV options
    encoding='utf-8'
    delimiter=','


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
                continue

            # Assign identifier
            code = item['Transaktionscode']

            payment = {}

            payment['ID'] = 'nicht zugeordnet'
            payment['Datum'] = self.convert_date(item['Datum'])
            payment['Vorgang'] = 'nicht zugeordnet'
            payment['Name'] = item['Name']
            payment['Email'] = item['Absender E-Mail-Adresse']
            payment['Brutto'] = self.convert_number(item['Brutto'])
            payment['Gebühr'] = self.convert_number(item['Gebühr'])
            payment['Netto'] = self.convert_number(item['Netto'])
            payment['Währung'] = item['Währung']
            payment['Transaktion'] = code

            if code not in codes:
                codes.add(code)

                # Sort out regular payments
                if item['Typ'] == 'Allgemeine Zahlung':
                    self._blocked_payments.append(payment)
                    continue

                payments.append(payment)

        return payments


    # MATCHING methods

    def match_payments(self, orders: list, infos: list) -> None:
        results = []

        for payment in self.data:
            # Assign payment to invoice number(s)
            # (1) Find matching order for current payment
            # (2) Find matching invoice number for this order
            matching_order = self.match_orders(payment, orders)

            if not matching_order:
                results.append(payment)
                continue

            matching_invoices = self.match_invoices(matching_order, infos)

            # Skip if no matching invoice numbers
            if not matching_invoices:
                results.append(payment)
                continue

            # Store data
            # (1) Apply matching order number
            # (2) Add invoice number(s) to payment data
            payment['ID'] = matching_order['ID']
            payment['Vorgang'] = matching_invoices
            payment['Versand'] = matching_order['Versand']
            # (3) Add total order cost & purchased items
            payment['Summe'] = matching_order['Bestellung']['Summe']
            del matching_order['Bestellung']['Summe']
            payment['Bestellung'] = matching_order['Bestellung']

            # (4) Save matched payment
            results.append(payment)

        self._matched_payments = results


    def match_orders(self, payment, orders) -> dict:
        candidates = []

        for order in orders:
            # Skip payments other than PayPal™
            if order['Abwicklung']['Zahlungsart'].lower() != 'paypal':
                continue

            # Determine matching transaction code ..
            if order['Abwicklung']['Transaktionscode'] != 'keine Angabe':
                if order['Abwicklung']['Transaktionscode'] == payment['Transaktion']:
                    # .. in which case there's a one-to-one match
                    return order

                # .. otherwise, why bother
                # TODO: In the future, this might be the way to go,
                # simply because PayPal always includes a transaction code ..
                #
                # .. BUT the algorithm could be used for other payments
                #
                # else:
                #     continue

            costs_match = payment['Brutto'] == order['Betrag']
            dates_match = self.match_dates(payment['Datum'], order['Datum'])

            if costs_match and dates_match:
                # Let them fight ..
                hits = 0

                # Determine chance of match for given payment & order
                # (1) Split by whitespace
                payment_name = payment['Name'].split(' ')
                order_name = order['Name'].split(' ')

                # (2) Take first list item as first name, last list item as last name
                payment_first, payment_last = payment_name[0], payment_name[-1]
                order_first, order_last = order_name[0], order_name[-1]

                # Add one point for matching first name, since that's more likely, but ..
                if payment_first.lower() == order_first.lower():
                    hits += 1

                # .. may be overridden by matching last name
                if payment_last.lower() == order_last.lower():
                    hits += 2

                candidates.append((hits, order))

        matches = sorted(candidates, key=itemgetter(0), reverse=True)

        if matches:
            return matches[0][1]

        return {}


    def match_invoices(self, order, infos) -> list:
        for info in infos:
            if info['ID'] == order['ID']:
                return info['Rechnungen'].keys()

        return []


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
                if 'Bestellung' in item:
                    # Determine taxes from purchase information
                    taxes = self.get_taxes(item['Bestellung'])
                    del item['Bestellung']

                    # Add taxe rates
                    for tax_rate, tax_amount in taxes.items():
                        item[self.get_tax_label(tax_rate) + ' MwSt'] = tax_amount

                    # Add share of payment fees for each tax rate
                    # (1) Calculate total amount of taxes
                    total_taxes = self.get_total_taxes(taxes)

                    # (2) Calculate share for each tax rate
                    for tax_rate, tax_amount in taxes.items():
                        ratio = total_taxes / tax_amount
                        share = float(item['Gebühr'].replace('-', '')) / ratio

                        item['Gebührenanteil ' + self.get_tax_label(tax_rate) + ' MwSt'] = self.convert_number(share)

                csv_data.append(item)

            return sorted(csv_data, key=itemgetter('Datum'))

        return sorted(self._matched_payments, key=itemgetter('Datum'))


    # MATCHING OUTPUT HELPER methods

    def get_taxes(self, purchase):
        taxes = {}

        for item in purchase.values():
            tax_rate = str(item['Steuersatz']).split('.')[0]

            if tax_rate not in taxes:
                taxes[tax_rate] = float(item['Steueranteil'])

            else:
                taxes[tax_rate] += float(item['Steueranteil'])

        return taxes


    def get_total_taxes(self, taxes) -> str:
        return sum([tax_amount for tax_amount in taxes.values()])


    def get_tax_label(self, tax_rate) -> str:
        return str(tax_rate).split('.')[0] + '%'
