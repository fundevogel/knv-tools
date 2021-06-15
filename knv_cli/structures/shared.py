from operator import itemgetter

import pendulum


# CONTACTS methods

def get_contacts(data: list, cutoff_date: str = None, blocklist = []) -> list:
    # Set default date
    if cutoff_date is None:
        today = pendulum.today()
        cutoff_date = today.subtract(years=2).to_datetime_string()[:10]

    codes = set()
    contacts  = []

    for item in data:
        contact_details = item.contact()

        # Normalize input
        mail_address = contact_details['Email'].lower()

        # Avoid blocklist bypass for empty mail addresses (edge case) ..
        if not mail_address:
            # .. by proceeding to next entry
            continue

        # Check for blocklisted mail addresses
        if mail_address in blocklist:
            continue

        # Grab date & name keys, which are different for orders & payments
        date_key = list(contact_details.keys())[0]
        name_key = 'Nachname' if 'Nachname' in contact_details else 'Name'

        # Throw out everything before cutoff date (if provided)
        if contact_details[date_key] < cutoff_date:
            continue

        if mail_address not in codes:
            codes.add(mail_address)
            contacts.append(contact_details)

    # Sort by date & lastname, in descending order
    contacts.sort(key=itemgetter(date_key, name_key), reverse=True)

    return contacts
