# ~*~ coding=utf-8 ~*~

# PAYPAL™
# This module contains functions for processing 'Aktivitäten'
# See https://www.paypal.com/de/smarthelp/article/FAQ1007

from .helpers import convert_cost, convert_date


# Processes 'Download*.CSV' files
def process_payments(data) -> list:
    codes = set()
    payments = []

    for item in data:
        # Skip withdrawals
        if item['Brutto'][:1] == '-':
            continue

        # Assign identifier
        code = item['Transaktionscode']

        payment = {}

        payment['ID'] = code
        payment['Datum'] = convert_date(item['Datum'])
        payment['Vorgang'] = 'nicht zugeordnet'
        payment['Name'] = item['Name']
        payment['Email'] = item['Absender E-Mail-Adresse']
        payment['Brutto'] = convert_cost(item['Brutto'])
        payment['Gebühr'] = convert_cost(item['Gebühr'])
        payment['Netto'] = convert_cost(item['Netto'])
        payment['Währung'] = item['Währung']

        if code not in codes:
            codes.add(code)
            payments.append(payment)

    return payments
