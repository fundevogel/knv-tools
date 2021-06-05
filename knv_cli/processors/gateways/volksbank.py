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

        for code, item in enumerate(self._data):
            # Skip all payments not related to customers
            # (1) Skip withdrawals
            if item[' '] == 'S':
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

            payment['ID'] = 'nicht zugeordnet'
            payment['Datum'] = self.convert_date(item['Valuta'])
            payment['Rechnungen'] = 'nicht zugeordnet'
            payment['Name'] = item['Empfänger/Zahlungspflichtiger']
            payment['Betrag'] = self.convert_number(item['Umsatz'])
            payment['Steuern'] = 'keine Angabe'
            payment['Währung'] = item['Währung']
            payment['Treffer'] = 'unsicher'
            payment['Dienstleister'] = 'Volksbank'
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
                payment['Rechnungen'] = []

                for invoice in invoice_candidates:
                    if invoice[:1] == '2':
                        invoice = 'R' + invoice

                    payment['Rechnungen'].append(invoice)

                # Remove duplicates AFTER normalization
                payment['Rechnungen'] = dedupe(payment['Rechnungen'])

            payments[code] = payment

        self.data = payments

        return self


    # # MATCHING methods

    # def match_payments(self, orders: dict, invoices: dict) -> None:
    #     results = []

    #     for payment in self.data.values():
    #         # Find matching invoices for each invoice candidate
    #         if isinstance(payment['Rechnungen'], list):
    #             # Consider only valid (= currently available) invoices
    #             payment['Rechnungen'] = [invoice for invoice in payment['Rechnungen'] if invoice in invoices]

    #             if not payment['Rechnungen']:
    #                 # Use other criteria since all detected invoice numbers were invalid
    #                 payment['Rechnungen'] = 'nicht zugeordnet'

    #             else:
    #                 # Check if extracted invoices sum up to total order cost ..
    #                 if self.compare_invoice_total(payment, invoices):
    #                     # .. which is a one-to-one hit
    #                     payment['Treffer'] = 'sicher'

    #                     # Add taxes
    #                     payment['Steuern'] = self.extract_taxes(payment['Rechnungen'], invoices)

    #                     results.append(payment)

    #                     # Move on to next payment
    #                     continue

    #                 # TODO: Yeah, what if not?
    #                 else:
    #                     pass

    #         # Find matching order(s) for each order candidate
    #         matching_orders = []

    #         if isinstance(payment['ID'], list):
    #             matching_orders = [orders[order_number] for order_number in payment['ID'] if order_number in orders]

    #         # Apply matching order number(s)
    #         if matching_orders:
    #             # Consider only valid (= currently available) orders
    #             payment['ID'] = [order['ID'] for order in matching_orders if order['ID'] in orders]

    #             payment['Rechnungen'] = []

    #             # Fill up on potential invoices ..
    #             for order_number in payment['ID']:
    #                 payment['Rechnungen'] += [invoice_number for invoice_number in orders[order_number]['Rechnungen'].keys() if isinstance(orders[order_number]['Rechnungen'], dict)]

    #             if not payment['Rechnungen']:
    #                 # Use other criteria since all detected invoice numbers were invalid
    #                 payment['Rechnungen'] = 'nicht zugeordnet'

    #             else:
    #                 # .. and here we go again, checking if extracted invoices sum up to total order cost ..
    #                 if self.compare_invoice_total(payment, invoices):
    #                     # .. which is (probably) a one-to-one hit
    #                     payment['Treffer'] = 'fast sicher'

    #                     # Add taxes
    #                     payment['Steuern'] = self.extract_taxes(payment['Rechnungen'], invoices)

    #                     results.append(payment)

    #                     # Move on to next payment
    #                     continue

    #                 # TODO: Yeah, what if not?
    #                 else:
    #                     pass

    #         results.append(payment)

    #     self._matched_payments = results


    # # MATCHING HELPER methods

    # def compare_invoice_total(self, payment: dict, invoices: dict) -> bool:
    #     return payment['Betrag'] == self.convert_number(sum([float(invoices[invoice]['Gesamtbetrag']) for invoice in payment['Rechnungen']]))


    # def extract_taxes(self, invoice_candidates: list, invoices: dict) -> dict:
    #     taxes = {}

    #     for invoice_number, invoice in invoices.items():
    #         if invoice_number in invoice_candidates and isinstance(invoice['Steuern'], dict):
    #             for tax_rate, tax_amount in invoice['Steuern'].items():
    #                 if tax_rate not in taxes:
    #                     taxes[tax_rate] = '0'

    #                 taxes[tax_rate] = self.convert_number(float(taxes[tax_rate]) + float(tax_amount))

    #     return taxes
