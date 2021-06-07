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

        for item in self.data:
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
