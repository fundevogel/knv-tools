# This module contains a class for processing & working with
# 'Umsätze', as exported from Volksbank
# TODO: Add link about CSV export in Volksbank online banking


from re import findall, fullmatch, split
from string import punctuation

from ..knv.invoices import Invoices
from ..utils import dedupe

from .gateway import Gateway


class Volksbank(Gateway):
    # PROPS

    regex = 'Umsaetze_*_*.csv'

    # CSV options
    csv_skiprows=12


    # DATA methods

    def process_payments(self, data) -> list:
        payments = []

        for item in data:
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
    def match_payments(self, data: list, invoice_handler: Invoices = None) -> None:
        results = []

        for payment in self.data:
            # Assign payment to order number(s) & invoices
            # (1) Find matching order(s) for current payment
            matching_orders = self.match_orders(payment, data)

            # (2) Find matching invoices for each identified order
            matching_invoices = []

            if isinstance(payment['Vorgang'], list):
                # Extracted invoices most likely sum up to total order cost
                matching_invoices = payment['Vorgang']

            # if notmatching_orders:
            #     for matching_order in matching_orders:
            #         if isinstance(matching_order['Rechnungen'], dict):
            #             matching_invoices += list(matching_order['Rechnungen'].keys())

            # Store data
            # (1) Add invoice number(s)
            if matching_invoices:
                payment['Vorgang'] = matching_invoices

                # There are two ways extracting information about invoices ..
                if invoice_handler:
                    # .. via parsing invoice files
                    matching_invoices = self.parse_invoices(matching_invoices, invoice_handler)

                    payment['Vorgang'] = [invoice['Vorgang'] for invoice in matching_invoices]
                    payment['Rechnungssumme'] = '0.00'
                    payment['Bestellung'] = []

                    taxes = {}

                    for invoice in matching_invoices:
                        payment['Rechnungssumme'] = self.convert_number(float(payment['Rechnungssumme']) + float(invoice['Gesamtbetrag']))
                        payment['Bestellung'].append(invoice['Steuern'])

                        for  tax_rate, tax_amount in invoice['Steuern'].items():
                            if not tax_rate in taxes:
                                taxes[tax_rate] = tax_amount

                            else:
                                taxes[tax_rate] = self.convert_number(float(taxes[tax_rate]) + float(tax_amount))

                    for tax_rate, tax_amount in taxes.items():
                        payment[tax_rate + ' MwSt'] = tax_amount

                else:
                    if matching_orders:
                        # .. via fetching order data
                        taxes = self.match_invoices(matching_invoices, matching_orders)

                        if taxes:
                            payment['Bestellung'] = taxes

                # Reverse-lookup orders if no matching order number(s) yet
                # if not matching_orders:
                #     matching_orders = self.lookup_orders(matching_invoices, infos)

            # (2) Apply matching order number(s)
            if matching_orders:
                payment['ID'] = [matching_order['ID'] for matching_order in matching_orders]

            # (3) Save matched payment
            results.append(payment)

        self._matched_payments = results


    def match_orders(self, payment: dict, orders: list) -> list:
        matches = []

        for order in orders:
            if order['ID'] in payment['ID']:
                matches.append(order)

        return dedupe(matches)


    # def lookup_orders(self, invoices: list, infos: list) -> list:
    #     matches = []

    #     for invoice in invoices:
    #         for info in infos:
    #             if invoice in info['Rechnungen']:
    #                 matches.append(info['ID'])
    #                 break

    #     return dedupe(matches)


    def match_invoices(self, invoices: list, orders: list) -> dict:
        matches = {}

        for invoice in invoices:
            for order in orders:
                if invoice in order['Abrechnungen']:
                    matches[invoice] = order['Abrechnungen'][invoice]

        return matches


    def parse_invoices(self, invoices: list, handler: Invoices) -> list:
        results = []

        for invoice in invoices:
            if handler.has(invoice):
                results.append(handler.parse(invoice))

        return results
