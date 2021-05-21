# This module contains a class for processing & working with
# 'Umsätze', as exported from Volksbank
# TODO: Add link about CSV export in Volksbank online banking


from re import findall, fullmatch, split
from string import punctuation

from .helpers import convert_number, convert_date
from .payments import Payments


class Volksbank(Payments):
    # Props
    regex = 'Umsaetze_*_*.csv'

    # CSV options
    skiprows=12


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
            payment['Datum'] = convert_date(item['Buchungstag'])
            payment['Vorgang'] = 'nicht zugeordnet'
            payment['Name'] = item['Empfänger/Zahlungspflichtiger']
            payment['Betrag'] = convert_number(item['Umsatz'])
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
                if line.split('-')[0] == self.VKN:
                    order_candidates.append(line)

                # Otherwise, try matching 6 random digits ..
                else:
                    order_candidate = fullmatch(r"\d{6}", line)

                    # .. so unless it's the VKN by itself ..
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
            pattern = r"(R?[2][0]\d{9}|[9]\d{11})"
            invoice_candidates = findall(pattern, reference)

            if not invoice_candidates:
                # Remove whitespace & try again
                reference = reference.replace(' ', '')
                invoice_candidates = findall(pattern, reference)

            if invoice_candidates:
                payment['Vorgang'] = invoice_candidates

            if payment['ID'] == 'nicht zugeordnet' and payment['Vorgang'] == 'nicht zugeordnet':
                self._blocked_payments.append(payment)
                continue

            payments.append(payment)

        return payments
