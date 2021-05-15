# ~*~ coding=utf-8 ~*~

# SHOPKONFIGURATOR
# This module contains functions for processing 'Auftragsdaten'
# See http://www.knv-info.de/wp-content/uploads/2020/04/Auftragsdatenexport2.pdf

from .helpers import convert_cost, convert_date


# Processes 'Orders_*.csv' files
def process_orders(order_data) -> list:
    orders = {}

    for item in order_data:
        # Create reliable article number ..
        clean_isbn = item['isbn']

        # .. since ISBNs are not always ISBNs
        if str(clean_isbn) == 'nan' or str(clean_isbn)[:3] != '978':
            clean_isbn = item['knvnumber']

        # .. and - more often than not - formatted as floats with a trailing zero
        clean_isbn = str(clean_isbn).replace('.0', '')

        # Assign identifier
        code = item['ormorderid']

        if code not in orders.keys():
            order = {}

            order['ID'] = code
            order['Datum'] = item['timeplaced'][:10]
            order['Anrede'] = item['rechnungaddresstitle']
            order['Vorname'] = item['rechnungaddressfirstname']
            order['Nachname'] = item['rechnungaddresslastname']
            order['Name'] = ' '.join([item['rechnungaddressfirstname'], item['rechnungaddresslastname']])
            order['Email'] = item['rechnungaddressemail']
            order['Bestellung'] = {clean_isbn: item['quantity']}
            order['Betrag'] = convert_cost(item['totalordercost'])
            order['Währung'] = item['currency']

            orders[code] = order

        else:
            if clean_isbn not in orders[code]['Bestellung'].keys():
                orders[code]['Bestellung'][clean_isbn] = item['quantity']

            else:
                orders[code]['Bestellung'][clean_isbn] = orders[code]['Bestellung'][clean_isbn] + item['quantity']

    return list(orders.values())


# Processes 'OrdersInfo_*.csv' files
def process_infos(info_data) -> list:
    infos = {}

    for item in info_data:
        # Create reliable invoice number ..
        clean_number = None

        if str(item['Invoice Number']) != 'nan':
            clean_number = str(item['Invoice Number']).replace('.0', '')

        # Assign identifier
        code = item['OrmNumber']

        if code not in infos.keys():
            info = {}

            info['ID'] = code
            info['Datum'] = item['Creation Date'][:10]
            info['Rechnungen'] = []

            if clean_number:
                info['Rechnungen'].append(clean_number)

            infos[code] = info

        else:
            if clean_number and clean_number not in infos[code]['Rechnungen']:
                infos[code]['Rechnungen'].append(clean_number)

    return list(infos.values())
