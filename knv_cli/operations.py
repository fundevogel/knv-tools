# ~*~ coding=utf-8 ~*~


from operator import itemgetter
from os.path import join
from datetime import datetime, timedelta

from matplotlib import pyplot, rcParams
from pandas import DataFrame
import pendulum


# MATCHING functions

def match_payments(payments, orders, infos) -> list:
    results = []

    for payment in payments:
        # Assign payment to invoice number(s)
        # (1) Find matching order for current payment
        # (2) Find matching invoice number for this order
        matching_order = match_orders(payment, orders)

        if not matching_order:
            results.append(payment)
            continue

        matching_infos = match_infos(matching_order, infos)

        # Skip if no matching invoice numbers
        if not matching_infos:
            results.append(payment)
            continue

        # Store data
        # (1) Apply matching order number
        # (2) Add invoice number(s) to payment data
        # (3) Save matched payment
        payment['ID'] = matching_order['ID']
        payment['Vorgang'] = ';'.join(matching_infos)
        results.append(payment)

    return results


def match_dates(base_date, test_date, days=1) -> bool:
    date_objects = [datetime.strptime(date, '%Y-%m-%d') for date in [base_date, test_date]]
    date_range = timedelta(days=days)

    if date_objects[0] <= date_objects[1] <= date_objects[0] + date_range:
        return True

    return False


def match_orders(payment, orders) -> dict:
    candidates = []

    for order in orders:
        # Skip payments other than PayPal™
        if order['Abwicklung']['Zahlungsart'].lower() != 'paypal':
            continue

        # Determine matching transaction code ..
        if order['Abwicklung']['Transaktionscode'] != 'keine Angabe':
            if order['Abwicklung']['Transaktionscode'] == payment['Transaktion']:
                # .. in which case there's a one-to-one match
                return order

            # .. otherwise, why bother
            # TODO: In the future, this might be the way to go,
            # simply because PayPal always includes a transaction code ..
            #
            # .. BUT the algorithm could be used for other payments
            #
            # else:
            #     continue

        costs_match = payment['Brutto'] == order['Betrag']
        dates_match = match_dates(payment['Datum'], order['Datum'])

        if costs_match and dates_match:
            # Let them fight ..
            hits = 0

            # Determine chance of match for given payment & order
            # (1) Split by whitespace
            payment_name = payment['Name'].split(' ')
            order_name = order['Name'].split(' ')

            # (2) Take first list item as first name, last list item as last name
            payment_first, payment_last = payment_name[0], payment_name[-1]
            order_first, order_last = order_name[0], order_name[-1]

            # Add one point for matching first name, since that's more likely, but ..
            if payment_first.lower() == order_first.lower():
                hits += 1

            # .. may be overridden by matching last name
            if payment_last.lower() == order_last.lower():
                hits += 2

            candidates.append((hits, order))

    matches = sorted(candidates, key=itemgetter(0), reverse=True)

    if matches:
        return matches[0][1]

    return {}


def match_infos(order, infos) -> list:
    info = []

    for info in infos:
        if info['ID'] == order['ID']:
            return info['Rechnungen']

    return []


# EXTRACTION functions

def get_ranking(orders: list) -> list:
    data = {}

    # Sum up number of sales
    for order in orders:
        for isbn, quantity in order['Bestellung'].items():
            if isbn not in data:
                data[isbn] = quantity

            else:
                data[isbn] = data[isbn] + quantity

    ranking = []

    for isbn, quantity in data.items():
        item = {}

        item['ISBN'] = isbn
        item['Anzahl'] = quantity

        ranking.append(item)

    # Sort sales by quantity & in descending order
    ranking.sort(key=itemgetter('Anzahl'), reverse=True)

    return ranking


def get_ranking_chart(ranking, limit=1, kind='barh'):
    # Update ranking to only include entries above set limit
    ranking = [{'Anzahl': item['Anzahl'], 'ISBN': item['ISBN']} for item in ranking if item['Anzahl'] >= int(limit)]
    df = DataFrame(ranking, index=[item['ISBN'] for item in ranking])

    # Rotate & center x-axis labels
    pyplot.xticks(rotation=45, horizontalalignment='center')

    # Make graph 'just fit' image dimensions
    rcParams.update({'figure.autolayout': True})

    return df.plot(kind=kind).get_figure()


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


# EXTRACTION HELPER functions

def convert_date(string: str) -> str:
    return datetime.strptime(string, '%Y-%m-%d').strftime('%d.%m.%Y')
