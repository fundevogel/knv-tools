# This module contains classes for processing & working with
# 'Auftragsdaten' & 'Ausführungen, as exported from Shopkonfigurator
# See http://www.knv-info.de/wp-content/uploads/2020/04/Auftragsdatenexport2.pdf


from operator import itemgetter
from os.path import splitext

import pendulum

from matplotlib import pyplot, rcParams
from pandas import DataFrame

from ..receiver import Receiver

from .infos import Infos
from .orders import Orders


class Shopkonfigurator(Receiver):
    # PROPS

    orders = None
    infos = None

    orders_regex = 'Orders_*.csv'
    infos_regex = 'OrdersInfo_*.csv'


    # DATA methods

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


    def init(self, force: bool = False) -> None:
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
