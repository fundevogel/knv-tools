# This module contains a class for processing & working with
# 'Umsätze', as exported from Volksbank
# TODO: Add link about CSV export in Volksbank online banking


from re import findall, fullmatch, split
from string import punctuation

from .payments import Payments
from ..utils import dedupe


class Volksbank(Payments):
    # PROPS

    regex = 'Umsaetze_*_*.csv'

    # CSV options
    skiprows=12


    # DATA methods

    def process_payments(self, data) -> list:
        payments = []

        for item in data:
            # Skip all payments not related to customers
            # (1) Skip withdrawals
            if item[' '] == 'S':
                continue

            # (2) Skip opening & closing balance
            if item['Kundenreferenz'] == 'Anfangssaldo' or item['Kundenreferenz'] == 'Endsaldo':
                continue

            reference = split('\n', item['Vorgang/Verwendungszweck'])

            # (3) Skip balancing debits
            if reference[0].lower() == 'abschluss':
                continue

            # Prepare reference string
            reference = ''.join(reference[1:])

            payment = {}

            payment['ID'] = 'nicht zugeordnet'
            payment['Datum'] = self.convert_date(item['Buchungstag'])
            payment['Vorgang'] = 'nicht zugeordnet'
            payment['Name'] = item['Empfänger/Zahlungspflichtiger']
            payment['Betrag'] = self.convert_number(item['Umsatz'])
            payment['Währung'] = item['Währung']
            payment['Rohdaten'] = item['Vorgang/Verwendungszweck']

            # Skip blocked payers by ..
            is_blocklisted = False

            # (1) .. iterating over them & blocklisting current payment based on ..
            for entity in self.blocklist:
                # (a) .. name of the payer
                if entity.lower() in payment['Name'].lower():
                    is_blocklisted = True
                    break

                # (b) .. payment reference
                if entity.lower() in reference.lower():
                    is_blocklisted = True
                    break

            # (3) .. skipping (but saving) blocklisted payments
            if is_blocklisted:
                self._blocked_payments.append(payment)
                continue

            # Extract order identifiers
            order_candidates = []

            for line in reference.split(' '):
                # Skip VKN
                if line == self.VKN:
                    continue

                # Match strings preceeded by VKN & hypen (definite hit)
                if self.VKN + '-' in line:
                    order_candidates.append(line)

                # Otherwise, try matching 6 random digits ..
                else:
                    order_candidate = fullmatch(r"\d{6}", line)

                    # .. and unless it's the VKN by itself ..
                    if order_candidate and order_candidate[0] != self.VKN:
                        # .. we got a hit
                        order_candidates.append(self.VKN + '-' + order_candidate[0])

            if order_candidates:
                payment['ID'] = order_candidates

            # Prepare reference string for further investigation
            reference = reference.replace('/', ' ').translate(str.maketrans('', '', punctuation))

            # Extract invoice numbers, matching ..
            # (1) .. '20' + 9 random digits
            # (2) .. '9' + 11 random digits
            pattern = r"([2][0]\d{9}|[9]\d{11})"
            invoice_candidates = findall(pattern, reference)

            # If this yields no invoices as result ..
            if not invoice_candidates:
                # .. remove whitespace & try again
                reference = reference.replace(' ', '')
                invoice_candidates = findall(pattern, reference)

            if invoice_candidates:
                payment['Vorgang'] = []

                for invoice in invoice_candidates:
                    if invoice[:1] == '2':
                        invoice = 'R' + invoice

                    payment['Vorgang'].append(invoice)

            payments.append(payment)

        return payments


    # MATCHING methods

    # TODO: Check if payment equals order total
    def match_payments(self, orders: list, infos: list) -> None:
        results = []

        for payment in self.data:
            # Assign payment to order number(s) & invoices
            # (1) Find matching order(s) for current payment
            matching_orders = self.match_orders(payment, orders)

            # (2) Find matching invoices for each identified order
            matching_invoices = self.match_invoices(matching_orders, infos)

            if isinstance(payment['Vorgang'], list):
                matching_invoices += payment['Vorgang']

            # Store data
            # (1) Add invoice number(s) to payment data
            if matching_invoices:
                payment['Vorgang'] = matching_invoices

                # Reverse-lookup orders if no matching order number(s) yet
                if not matching_orders:
                    matching_orders = self.lookup_orders(matching_invoices, infos)

            # (2) Apply matching order number(s)
            if matching_orders:
                payment['ID'] = matching_orders

            # (3) Save matched payment
            results.append(payment)

        self._matched_payments = results


    def match_orders(self, payment: dict, orders: list) -> list:
        matches = []

        for order in orders:
            if order['ID'] in payment['ID']:
                matches.append(order['ID'])

        return dedupe(matches)


    def match_invoices(self, orders: list, infos: list) -> list:
        matches = []

        for order in orders:
            for info in infos:
                if order == info['ID']:
                    matches += info['Rechnungen']
                    break

        return dedupe(matches)


    def lookup_orders(self, invoices: list, infos: list) -> list:
        matches = []

        for invoice in invoices:
            for info in infos:
                if invoice in info['Rechnungen']:
                    matches.append(info['ID'])
                    break

        return dedupe(matches)