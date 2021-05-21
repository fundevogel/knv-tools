# This module contains a class for processing & working with
# 'Aktivitäten', as exported from PayPal™
# See https://www.paypal.com/de/smarthelp/article/FAQ1007

from .helpers import convert_number, convert_date
from .payments import Payments


class Paypal(Payments):
    # Props
    identifier = 'Transaktion'
    regex = 'Download*.CSV'

    # CSV options
    encoding='utf-8'
    delimiter=','


    def process_payments(self, data) -> list:
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
            payment['Transaktion'] = code
            payment['Datum'] = convert_date(item['Datum'])
            payment['Vorgang'] = 'nicht zugeordnet'
            payment['Name'] = item['Name']
            payment['Email'] = item['Absender E-Mail-Adresse']
            payment['Brutto'] = convert_number(item['Brutto'])
            payment['Gebühr'] = convert_number(item['Gebühr'])
            payment['Netto'] = convert_number(item['Netto'])
            payment['Währung'] = item['Währung']

            if code not in codes:
                codes.add(code)

                # Sort out regular payments
                if item['Typ'] == 'Allgemeine Zahlung':
                    self._blocked_payments.append(payment)
                    continue

                payments.append(payment)

        return payments
