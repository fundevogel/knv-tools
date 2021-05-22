# This module contains classes for processing & working with
# 'Auftragsdaten' & 'Ausführungen, as exported from Shopkonfigurator
# See http://www.knv-info.de/wp-content/uploads/2020/04/Auftragsdatenexport2.pdf


from abc import abstractmethod
from operator import itemgetter

import pendulum

from matplotlib import pyplot, rcParams
from pandas import DataFrame

from .base import BaseClass


class Orders(BaseClass):
    # PROPS

    identifier = 'ID'
    regex = 'Orders_*.csv'


    # DATA methods

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
                order['Bestellung'] = {'Summe': self.convert_number(item['totalproductcost'])}
                order['Versand'] = self.convert_number(item['totalshipping'])
                order['Betrag'] = self.convert_number(item['totalordercost'])
                order['Währung'] = item['currency']
                order['Abwicklung'] = {'Zahlungsart': 'keine Angabe', 'Transaktionscode': 'keine Angabe'}

                orders[code] = order
                codes.add(code)

            # Add information about each purchased article
            orders[code]['Bestellung'][clean_isbn] = {
                'Anzahl': int(item['quantity']),
                'Preis': self.convert_number(item['orderitemunitprice']),
                'Steuersatz': self.convert_number(item['vatpercent']),
                'Steueranteil': self.convert_number(item['vatprice']),
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


    # RANKING methods

    def get_ranking(self) -> list:
        data = {}

        # Sum up number of sales
        for order in self.data:
            for isbn, product in order['Bestellung'].items():
                # Skip total order cost
                if isbn == 'Summe':
                    continue

                if isbn not in data:
                    data[isbn] = product['Anzahl']

                else:
                    data[isbn] = data[isbn] + product['Anzahl']

        ranking = []

        for isbn, quantity in data.items():
            item = {}

            item['ISBN'] = isbn
            item['Anzahl'] = quantity

            ranking.append(item)

        # Sort sales by quantity & in descending order
        ranking.sort(key=itemgetter('Anzahl'), reverse=True)

        return ranking


    def get_ranking_chart(self, ranking, limit=1, kind='barh'):
        # Update ranking to only include entries above set limit
        ranking = [{'Anzahl': item['Anzahl'], 'ISBN': item['ISBN']} for item in ranking if item['Anzahl'] >= int(limit)]
        df = DataFrame(ranking, index=[item['ISBN'] for item in ranking])

        # Rotate & center x-axis labels
        pyplot.xticks(rotation=45, horizontalalignment='center')

        # Make graph 'just fit' image dimensions
        rcParams.update({'figure.autolayout': True})

        return df.plot(kind=kind).get_figure()


    # CONTACTS methods

    def get_contacts(self, orders: list, cutoff_date: str = None, blocklist = []) -> list:
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
            contact['Letzte Bestellung'] = order['Datum']

            if mail_address not in codes:
                codes.add(mail_address)
                contacts.append(contact)

        return contacts


class Infos(BaseClass):
    # Props
    identifier = 'ID'
    regex = 'OrdersInfo_*.csv'


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
