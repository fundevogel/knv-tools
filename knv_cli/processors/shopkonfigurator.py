# SHOPKONFIGURATOR
# This module contains classes for processing & working with
# 'Auftragsdaten' & 'Ausführungen, as exported from Shopkonfigurator
# See http://www.knv-info.de/wp-content/uploads/2020/04/Auftragsdatenexport2.pdf


from abc import abstractmethod
from operator import itemgetter

from .base import BaseClass
from .helpers import convert_number


class Orders(BaseClass):
    # Props
    identifier = 'ID'


    def process_data(self, order_data: list) -> list:
        '''
        Processes 'Orders_*.csv' files
        '''
        orders = {}

        for item in order_data:
            # Create reliable article number ..
            clean_isbn = item['isbn']

            # .. since ISBNs are not always ISBNs
            if str(clean_isbn) == 'nan' or str(clean_isbn)[:3] != '978':
                clean_isbn = item['knvnumber']

            # .. and - more often than not - formatted as floats with a trailing zero
            clean_isbn = str(clean_isbn).replace('.0', '')

            # Populate set with identifiers
            codes = {order for order in orders.keys()}

            # Assign identifier
            code = item['ormorderid']

            if code not in codes:
                order = {}

                order['ID'] = code
                order['Datum'] = item['timeplaced'][:10]
                order['Anrede'] = item['rechnungaddresstitle']
                order['Vorname'] = item['rechnungaddressfirstname']
                order['Nachname'] = item['rechnungaddresslastname']
                order['Name'] = ' '.join([item['rechnungaddressfirstname'], item['rechnungaddresslastname']])
                order['Email'] = item['rechnungaddressemail']
                order['Bestellung'] = {'Summe': convert_number(item['totalproductcost'])}
                order['Versand'] = convert_number(item['totalshipping'])
                order['Betrag'] = convert_number(item['totalordercost'])
                order['Währung'] = item['currency']
                order['Abwicklung'] = {'Zahlungsart': 'keine Angabe', 'Transaktionscode': 'keine Angabe'}

                orders[code] = order
                codes.add(code)

            # Add information about each purchased article
            orders[code]['Bestellung'][clean_isbn] = {
                'Anzahl': int(item['quantity']),
                'Preis': convert_number(item['orderitemunitprice']),
                'Steuersatz': convert_number(item['vatpercent']),
                'Steueranteil': convert_number(item['vatprice']),
            }

            # Add information about ..
            # (1) .. method of payment
            if str(item['paymenttype']) != 'nan':
                orders[code]['Abwicklung']['Zahlungsart'] = item['paymenttype']

            # (2) .. transaction number (Paypal™ only)
            if str(item['transactionid']) != 'nan':
                orders[code]['Abwicklung']['Transaktionscode'] = str(item['transactionid'])

        return list(orders.values())


    def orders(self):
        # Sort orders by date
        return sorted(self.data, key=itemgetter('Datum'))


class Infos(BaseClass):
    # Props
    identifier = 'ID'

    def process_data(self, info_data: list) -> list:
        '''
        Processes 'OrdersInfo_*.csv' files
        '''
        infos = {}

        for item in info_data:
            # Create reliable invoice number ..
            clean_number = None

            if str(item['Invoice Number']) != 'nan':
                clean_number = str(item['Invoice Number']).replace('.0', '')

            # Populate set with identifiers
            codes = {info for info in infos.keys()}

            # Assign identifier
            code = item['OrmNumber']

            if code not in codes:
                info = {}

                info['ID'] = code
                info['Datum'] = item['Creation Date'][:10]
                info['Rechnungen'] = []

                if clean_number:
                    info['Rechnungen'].append(clean_number)

                codes.add(code)
                infos[code] = info

            else:
                if clean_number and clean_number not in infos[code]['Rechnungen']:
                    infos[code]['Rechnungen'].append(clean_number)

        return list(infos.values())


    def infos(self):
        # Sort infos by date
        return sorted(self.data, key=itemgetter('Datum'))
