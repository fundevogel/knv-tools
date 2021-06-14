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

            payment['Datum'] = self.date2string(item['Datum'])
            payment['Art'] = 'H'
            payment['Treffer'] = 'unsicher'
            payment['Auftragsnummer'] = 'nicht zugeordnet'
            payment['Rechnungsnummer'] = 'nicht zugeordnet'
            payment['Name'] = item['Name']
            payment['Betrag'] = self.number2string(item['Brutto'])
            payment['Gebühr'] = self.number2string(item['Gebühr'][1:])
            payment['Netto'] = self.number2string(item['Netto'])
            payment['Währung'] = item['Währung']
            payment['Anschrift'] = item['Adresszeile 1']
            payment['PLZ'] = self.normalize(item['PLZ'])
            payment['Ort'] = item['Ort']
            payment['Land'] = item['Land']
            payment['Telefon'] = self.normalize(item['Telefon'])
            payment['Email'] = item['Absender E-Mail-Adresse']
            payment['Dienstleister'] = 'PayPal'
            payment['Zahlungsart'] = 'Sofortzahlung'
            payment['Transaktion'] = code

            if payment['Telefon'] != '':
                payment['Telefon'] = '0' + payment['Telefon'].replace('+49', '')

            if item['Typ'] == 'Allgemeine Zahlung':
                payment['Zahlungsart'] = 'Überweisung'

            payments[code] = payment

        self.data = payments

        return self
