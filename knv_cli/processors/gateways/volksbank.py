# This module contains a class for processing & working with
# 'Umsätze', as exported from Volksbank

# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from re import findall, fullmatch, split
from string import punctuation

from ...utils import dedupe
from .gateway import Gateway


class Volksbank(Gateway):
    # PROPS

    regex = 'Umsaetze_*_*.csv'

    # CSV options
    csv_skiprows=12

    # Class only
    VKN = None
    blocklist = []


    # CORE methods

    def process_payments(self) -> Volksbank:
        '''
        Processes 'Umsaetze_{IBAN}_{Y.m.d}.csv' files
        '''

        payments = {}

        for code, item in enumerate(self.data):
            # Skip all payments not related to customers
            # (1) Skip withdrawals
            if item[' '] == 'S' and item['Empfänger/Zahlungspflichtiger'] not in ['Raiffeisen Factor Bank AG']:
                continue

            # (2) Skip opening & closing balance
            if item['Kundenreferenz'] in ['Anfangssaldo', 'Endsaldo']:
                continue

            reference = split('\n', item['Vorgang/Verwendungszweck'])

            # (3) Skip balancing debits
            if reference[0].lower() == 'abschluss':
                continue

            # Prepare reference string
            reference = ''.join(reference[1:])

            payment = {}

            payment['Datum'] = self.date2string(item['Valuta'])
            payment['Kontierung'] = 'H'
            payment['Treffer'] = 'unsicher'
            payment['Auftragsnummer'] = 'nicht zugeordnet'
            payment['Rechnungsnummer'] = 'nicht zugeordnet'
            payment['Name'] = item['Empfänger/Zahlungspflichtiger']
            payment['Betrag'] = self.number2string(item['Umsatz'])
            payment['Währung'] = item['Währung']
            payment['Dienstleister'] = 'Volksbank'
            payment['Zahlungsart'] = 'Überweisung'
            payment['Verwendungszweck'] = reference
            payment['Rohdaten'] = item['Vorgang/Verwendungszweck']

            # As KNV transfers all its claims against stores to a certain Raiffeisen subsidiary ..
            if payment['Name'] == 'Raiffeisen Factor Bank AG':
                # .. coming across it, look for invoice numbers & collect them
                payment['Kontierung'] = 'S'
                pattern = r"(Rg\s\d{10})"
                expenses = [invoice.replace('Rg 00', '') for invoice in findall(pattern, reference)]

                # Apply matched fitbis invoices
                if expenses: payment['Rechnungsnummer'] = dedupe(expenses)

                payments[code] = payment

                # Proceed to next payment
                continue

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

            for line in reference.split():
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

            # Apply matched order(s)
            if order_candidates: payment['Auftragsnummer'] = order_candidates

            # Prepare reference string for further investigation by removing ..
            # (1) .. punctuation
            # (2) .. whitespaces
            # (3) .. tabs
            reference = reference.translate(str.maketrans('', '', punctuation)).replace(' ', '').replace("\t", '')

            # Extract invoice numbers, matching ..
            # (1) .. '20' + 9 random digits
            # (2) .. '9' + 11 random digits
            pattern = r"([2][0]\d{9}|[9]\d{11})"
            invoice_candidates = findall(pattern, reference)

            if invoice_candidates:
                payment['Rechnungsnummer'] = []

                for invoice in invoice_candidates:
                    # Normalize matched invoices
                    if invoice[:1] == '2': invoice = 'R' + invoice

                    payment['Rechnungsnummer'].append(invoice)

                # Remove duplicates AFTER normalization
                payment['Rechnungsnummer'] = dedupe(payment['Rechnungsnummer'])

            payments[code] = payment

        self.data = payments

        return self
