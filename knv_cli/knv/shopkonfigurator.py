# This module contains classes for processing & working with
# 'Auftragsdaten' & 'Ausführungen, as exported from Shopkonfigurator
# See http://www.knv-info.de/wp-content/uploads/2020/04/Auftragsdatenexport2.pdf


import json

from operator import itemgetter
from os.path import splitext

import pendulum

from matplotlib import pyplot, rcParams
from pandas import DataFrame

from ..base import BaseClass


class Shopkonfigurator:
    # PROPS

    data = None
    orders = None
    infos = None

    orders_regex = 'Orders_*.csv'
    infos_regex = 'OrdersInfo_*.csv'


    def __init__(self, data_files: list = None) -> None:
        if data_files:
            self.load_data(data_files)


    # DATA methods

    def load_data(self, data_files: list = None) -> None:
        self.data = self.load_json(data_files)


    def load_orders(self, order_files: list) -> None:
        # Depending on filetype, proceed with ..
        extension = splitext(order_files[0])[1]

        if extension == '.csv':
            order_data = Orders(order_files).orders()

        if extension == '.json':
            order_data = self.load_json(order_files)

        self.orders = order_data


    def load_infos(self, info_files: list) -> None:
        # Depending on filetype, proceed with ..
        extension = splitext(info_files[0])[1]

        if extension == '.csv':
            info_data = Infos(info_files).infos()

        if extension == '.json':
            info_data = self.load_json(info_files)

        self.infos = info_data


    def init(self, force: bool = False):
        # Merge orders & infos
        if not self.data or force:
            self.data = self.merge_data(self.orders, self.infos)


    def merge_data(self, order_data: list, info_data: list) -> list:
        data = {}

        for order in order_data:
            code = order['ID']

            if code not in data:
                order['Rechnungen'] = 'nicht zugeordnet'
                order['Abrechnungen'] = 'nicht zugeordnet'

                for info in info_data:
                    # Match order & info one-to-one first
                    if code == info['ID']:
                        # Prepare data storage for invoices
                        invoice_data = {}

                        # Keep original data (as safety measure)
                        order['Rechnungen'] = info['Rechnungen']

                        for invoice_number, item_numbers in info['Rechnungen'].items():
                            # Add empty invoice placeholder
                            invoice_data[invoice_number] = []

                            for item_number in item_numbers:
                                # Add invoice data if item numbers match
                                if item_number in order['Bestellung'].keys():
                                    invoice_data[invoice_number].append(order['Bestellung'][item_number])

                        order['Abrechnungen'] = invoice_data

                        break

                data[code] = order

        return sorted(list(data.values()), key=itemgetter('Datum', 'ID', 'Nachname'))


    # # RANKING methods

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


    # def get_ranking_chart(self, ranking, limit=1, kind='barh'):
    #     # Update ranking to only include entries above set limit
    #     ranking = [{'Anzahl': item['Anzahl'], 'ISBN': item['ISBN']} for item in ranking if item['Anzahl'] >= int(limit)]
    #     df = DataFrame(ranking, index=[item['ISBN'] for item in ranking])

    #     # Rotate & center x-axis labels
    #     pyplot.xticks(rotation=45, horizontalalignment='center')

    #     # Make graph 'just fit' image dimensions
    #     rcParams.update({'figure.autolayout': True})

    #     return df.plot(kind=kind).get_figure()


    # CONTACTS methods

    def get_contacts(self, cutoff_date: str = None, blocklist = []) -> list:
        # Check if order entries are present
        if not self.data:
            raise Exception


        # Set default date
        if cutoff_date is None:
            today = pendulum.today()
            cutoff_date = today.subtract(years=2).to_datetime_string()[:10]

        codes = set()
        contacts  = []

        for order in self.data:
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
            contact['Email'] = order['Email']
            contact['Letzte Bestellung'] = order['Datum']

            if mail_address not in codes:
                codes.add(mail_address)
                contacts.append(contact)

        # Sort by date & lastname, in descending order
        contacts.sort(key=itemgetter('Letzte Bestellung', 'Nachname'), reverse=True)

        return contacts


    # HELPER methods

    def load_json(self, json_files: list):
        data = []

        for json_file in json_files:
            try:
                with open(json_file, 'r') as file:
                    data.extend(json.load(file))

            except json.decoder.JSONDecodeError:
                raise Exception

            except FileNotFoundError:
                pass

        return data


class Orders(BaseClass):
    # DATA methods

    def process_data(self, order_data: list) -> dict:
        '''
        Processes 'Orders_*.csv' files
        '''

        orders = {}

        for item in order_data:
            # Create reliable article number ..
            isbn = item['knvnumber']

            # .. since ISBNs are not always ISBNs
            if str(item['isbn']) != 'nan':
                isbn = item['isbn']

            # .. and - more often than not - formatted as floats with a trailing zero
            isbn = str(isbn).replace('.0', '')

            # Assign identifier
            code = item['ormorderid']

            if code not in orders:
                order = {}

                order['ID'] = code
                order['Datum'] = item['timeplaced'][:10]
                order['Anrede'] = item['rechnungaddresstitle']
                order['Vorname'] = item['rechnungaddressfirstname']
                order['Nachname'] = item['rechnungaddresslastname']
                order['Email'] = item['rechnungaddressemail']
                order['Bestellung'] = {}
                order['Bestellsumme'] = self.convert_number(item['totalproductcost'])
                order['Versand'] = self.convert_number(item['totalshipping'])
                order['Betrag'] = self.convert_number(item['totalordercost'])
                order['Währung'] = item['currency']
                order['Abwicklung'] = {
                    'Zahlungsart': 'keine Angabe',
                    'Transaktionscode': 'keine Angabe'
                }

                orders[code] = order

            # Add information about ..
            # (1) .. each purchased article
            item_number = str(item['orderitemid'])

            orders[code]['Bestellung'][item_number] = {
                'Nummer': item_number,
                'ISBN': isbn,
                'Titel': item['producttitle'],
                'Anzahl': int(item['quantity']),
                'Preis': self.convert_number(item['orderitemunitprice']),
                'Steuersatz': self.convert_tax_rate(item['vatpercent']),
                'Steueranteil': self.convert_number(item['vatprice']),
            }

            # (2) .. method of payment
            if str(item['paymenttype']) != 'nan':
                orders[code]['Abwicklung']['Zahlungsart'] = item['paymenttype']

            # (3) .. transaction number (Paypal™ only)
            if str(item['transactionid']) != 'nan':
                orders[code]['Abwicklung']['Transaktionscode'] = str(item['transactionid'])

        return orders


    def orders(self):
        # Sort orders by date & order number, output as list
        return sorted(list(self.data.values()), key=itemgetter('Datum', 'ID'))


class Infos(BaseClass):
    # DATA methods

    def process_data(self, info_data: list) -> dict:
        '''
        Processes 'OrdersInfo_*.csv' files
        '''

        infos = {}

        for item in info_data:
            # Skip availability information
            if str(item['Invoice Number']) == 'nan':
                continue

            # Standardize invoice number & costs
            invoice_number = str(item['Invoice Number']).replace('.0', '')
            item_number = str(item['Order Item Id'])

            # Assign identifier
            code = item['OrmNumber']

            if code not in infos:
                info = {}

                info['ID'] = code
                info['Datum'] = item['Creation Date'][:10]
                info['Rechnungen'] = {}

                infos[code] = info

            if invoice_number not in infos[code]['Rechnungen'].keys():
                infos[code]['Rechnungen'][invoice_number] = [item_number]

            else:
                infos[code]['Rechnungen'][invoice_number].append(item_number)

        return infos


    def infos(self):
        # Sort infos by date & order number, output as list
        return sorted(list(self.data.values()), key=itemgetter('Datum', 'ID'))
