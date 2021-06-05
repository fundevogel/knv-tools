# This module contains a class for processing & working with
# 'Aktivitäten', as exported from PayPal™
# See https://www.paypal.com/de/smarthelp/article/FAQ1007

# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

# from operator import itemgetter
# from os.path import join

from .gateway import Gateway


class Paypal(Gateway):
    # PROPS

    regex = 'Download*.CSV'

    # CSV options
    csv_encoding='utf-8'
    csv_delimiter=','


    # CORE methods

    def process_payments(self) -> Paypal:
        '''
        Processes 'Download*.CSV' files
        '''

        payments = {}

        for item in self._data:
            # Skip withdrawals
            if item['Brutto'][:1] == '-':
                self._blocked_payments.append(payment)
                continue

            # Assign identifier
            code = item['Transaktionscode']

            payment = {}

            payment['ID'] = 'nicht zugeordnet'
            payment['Datum'] = self.convert_date(item['Datum'])
            payment['Rechnungen'] = 'nicht zugeordnet'
            payment['Name'] = item['Name']
            payment['Brutto'] = self.convert_number(item['Brutto'])
            payment['Gebühr'] = self.convert_number(item['Gebühr'])
            payment['Netto'] = self.convert_number(item['Netto'])
            payment['Währung'] = item['Währung']
            payment['Steuern'] = 'keine Angabe'
            payment['Anschrift'] = item['Adresszeile 1']
            payment['PLZ'] = item['PLZ']
            payment['Ort'] = item['Ort']
            payment['Land'] = item['Land']
            payment['Telefon'] = self.convert_nan(item['Telefon'])
            payment['Email'] = item['Absender E-Mail-Adresse']
            payment['Treffer'] = 'unsicher'
            payment['Dienstleister'] = 'PayPal'
            payment['Zahlungsart'] = 'Shopbestellung'
            payment['Transaktion'] = code

            if payment['Telefon']:
                payment['Telefon'] = '0' + payment['Telefon'].replace('.0', '')

            if item['Typ'] == 'Allgemeine Zahlung':
                payment['Zahlungsart'] = 'Überweisung'

            payments[code] = payment

        self.data = payments

        return self


    # # MATCHING methods

    # def match_payments(self, orders: dict, invoices: dict) -> None:
    #     results = []

    #     for payment in self.data.values():
    #         # Search for matching order
    #         matching_order = {}

    #         # (1) Distinguish between online shop payments ..
    #         if payment['Zahlungsart'] == 'Shopbestellung':
    #             # Find matching order for current payment
    #             for order in orders.values():
    #                 # .. whose transaction codes will match ..
    #                 if payment['Transaktion'] == order['Abwicklung']['Transaktionscode']:
    #                     # .. which represents a one-to-one match
    #                     payment['Treffer'] = 'sicher'
    #                     matching_order = order

    #                     # Abort iterations
    #                     break

    #         # (2) .. and regular payments
    #         else:
    #             # Find matching order, but this will almost always fail
    #             matching_order = self.match_orders(payment, orders)

    #         # Search for matching invoice(s)
    #         matching_invoices = []

    #         if matching_order and isinstance(matching_order, dict):
    #             # Apply order data
    #             # (1) Add matching order number
    #             payment['ID'] = matching_order['ID']

    #             # (2) Add taxes
    #             payment['Steuern'] = matching_order['Steuern']

    #             # (3) Add invoice numbers
    #             if isinstance(matching_order['Rechnungen'], dict):
    #                 matching_invoices = list(matching_order['Rechnungen'].keys())

    #         # .. without matching order, this can only be achieved by going through invoices
    #         else:
    #             matching_invoice = self.match_invoices(payment, invoices)

    #             if matching_invoice:
    #                 matching_invoices = [matching_invoice['Vorgang']]

    #                 # Add taxes
    #                 payment['Steuern'] = {
    #                     matching_invoice['Vorgang']: matching_invoice['Steuern']
    #                 }

    #         # Skip if no matching invoice numbers
    #         if matching_invoices:
    #             # Add invoice number(s) to payment data
    #             payment['Rechnungen'] = matching_invoices

    #         results.append(payment)

    #     self._matched_payments = results


    # def match_orders(self, payment: dict, orders: dict) -> dict:
    #     for order in orders.values():
    #         candidates = []

    #         # Check if payment amount matches order costs, and only then ..
    #         if payment['Brutto'] == order['Gesamtbetrag']:
    #             # .. for last two weeks ..
    #             for days in range(1, 14):
    #                 # .. determine matching orders by highest probability, but only those ..
    #                 candidate = ()

    #                 # .. matching
    #                 if self.match_dates(payment['Datum'], order['Datum'], days, True):
    #                     # Let them fight ..
    #                     hits = 0

    #                     # Determine chance of match for given payment & order ..
    #                     # (1) .. by comparing their names
    #                     payment_names = payment['Name'].split(' ')
    #                     payment_first, payment_last = payment_names[0], payment_names[-1]
    #                     order_first, order_last = (order['Vorname'], order['Nachname'])

    #                     # Add one point for matching first name, since that's more likely, but ..
    #                     if payment_first.lower() == order_first.lower():
    #                         hits += 1

    #                     # .. may be overridden by matching last name
    #                     if payment_last.lower() == order_last.lower():
    #                         hits += 2

    #                     # (2) .. by comparing their contact details
    #                     if payment['Telefon'].lower() == order['Telefon'].lower():
    #                         hits += 5

    #                     if payment['Email'].lower() == order['Email'].lower():
    #                         hits += 5

    #                     # (3) .. by comparing their home / shipping address
    #                     if order['Straße'].lower() in order['Anschrift'].lower():
    #                         hits += 2

    #                     if payment['PLZ'] == order['PLZ']:
    #                         hits += 1

    #                     candidate = (order, hits)

    #                 if candidate:
    #                     candidates.append(candidate)

    #         if candidates:
    #             # Sort candidates by hits ..
    #             candidates.sort(key=itemgetter(1), reverse=True)

    #             # .. and select most promising one
    #             return candidates[0][0]

    #     return {}


    # def match_invoices(self, payment: dict, invoices: dict) -> dict:
    #     for invoice in invoices.values():
    #         # Check if payment amount matches invoice costs, and only then ..
    #         if payment['Brutto'] == invoice['Gesamtbetrag']:
    #             # .. within next two months ..
    #             for days in range(1, 60):
    #                 # check if payment date matches invoices within two months, and only then ..
    #                 if self.match_dates(payment['Datum'], invoice['Datum'], days):
    #                     # .. return matching invoice
    #                     return invoice

    #     return {}


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

    #                 #     item['Gebührenanteil ' + tax_rate] = self.convert_number(share)

    #             csv_data.append(item)

    #         return sorted(csv_data, key=itemgetter('Datum'))

    #     return sorted(self._matched_payments, key=itemgetter('Datum'))
