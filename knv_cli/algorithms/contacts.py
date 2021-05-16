# ~*~ coding=utf-8 ~*~


from datetime import datetime
from operator import itemgetter

import pendulum


# CONTACTS functions

def get_contacts(orders: list, cutoff_date: str = None, blocklist = []) -> list:
    # Set default date
    if cutoff_date is None:
        today = pendulum.today()
        cutoff_date = today.subtract(years=2).to_datetime_string()[:10]

    # Sort orders by date & in descending order
    orders.sort(key=itemgetter('Datum'), reverse=True)

    codes = set()
    contacts  = []

    for order in orders:
        mail_address = order['Email']

        # Check for blocklisted mail addresses
        if mail_address in blocklist:
            continue

        # Throw out everything before cutoff date (if provided)
        if order['Datum'] < cutoff_date:
            continue

        # Prepare dictionary
        contact = {}

        contact['Anrede'] = order['Anrede']
        contact['Vorname'] = order['Vorname']
        contact['Nachname'] = order['Nachname']
        contact['Name'] = order['Name']
        contact['Email'] = order['Email']
        contact['Letzte Bestelltung'] = convert_date(order['Datum'])

        if mail_address not in codes:
            codes.add(mail_address)
            contacts.append(contact)

    return contacts


# CONTACTS HELPER functions

def convert_date(string: str) -> str:
    return datetime.strptime(string, '%Y-%m-%d').strftime('%d.%m.%Y')
