# This module contains classes for processing & working with
# 'Auftragsdaten' & 'Ausführungen, as exported from Shopkonfigurator
# See http://www.knv-info.de/wp-content/uploads/2020/04/Auftragsdatenexport2.pdf

# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from operator import itemgetter
from os.path import splitext

import pendulum

from matplotlib import pyplot, rcParams
from pandas import DataFrame

from ..base import BaseClass
from ..utils import load_json


class KNV(BaseClass):
    # PROPS

    orders = None
    infos = None
    invoices = None


    def __init__(self, data_files: list = None) -> None:
        if data_files:
            self.data = load_json(data_files)


    # DATA methods

    def load(self, identifier: str, data_files: list = None) -> KNV:
        # Check identifier
        if identifier not in ['orders', 'infos', 'invoices']:
            raise Exception('Unsupported identifier: "{}"'.format(identifier))

        # Check filetype
        extension = splitext(data_files[0])[1]

        if extension != '.json':
            raise Exception('Unsupported filetype: "{}"'.format(extension))

        if identifier == 'orders':
            self.orders = load_json(data_files)

        if identifier == 'infos':
            self.infos = load_json(data_files)

        if identifier == 'invoices':
            self.invoices = load_json(data_files)

        return self


    def init(self, force: bool = False) -> KNV:
        # Merge orders, infos & invoices
        if not self.data or force:
            self.data = self.merge_sources(self.orders, self.infos, self.invoices)

        return self


    def merge_sources(self, orders: dict, infos: dict, invoices: dict) -> dict:
        main_data = {}

        for order_number, order in orders.items():
            # Check for matching info ..
            if order_number in infos:
                # .. which is a one-to-one most the time
                info = infos[order_number]

                # Prepare invoice data storage
                purchase = {}

                for invoice_number, invoice_items in info['Bestellung'].items():
                    purchase[invoice_number] = []

                    # Extract reference order item ..
                    match = [item for item in order['Bestellung'] if item['Nummer'] in invoice_items][0]

                    # .. and copy over its data, taking care of invoices with huge amounts of items being split into several invoices
                    # See '31776-001471'
                    for invoice_item in invoice_items.values():
                        invoice_item['ISBN'] = match['ISBN']
                        invoice_item['Titel'] = match['Titel']
                        invoice_item['Steuern'] = 'keine Angabe'
                        invoice_item['Steuersatz'] = match['Steuersatz']
                        invoice_item['Steueranteil'] = match['Steueranteil']

                        purchase[invoice_number].append(invoice_item)

                order['Rechnungen'] = purchase

                # Extract taxes for each invoice from parsed invoice files
                order['Steuern'] = {invoice_number: invoices[invoice_number]['Steuern'] for invoice_number in purchase.keys() if invoice_number in invoices}

            main_data[order_number] = order

        return main_data


    # RANKING methods

    def get_ranking(self, limit: int = 1) -> list:
        data = {}

        # Sum up number of sales
        for item in [item[0] for item in [order['Bestellung'] for order in self.data.values()]]:
            if item['ISBN'] not in data:
                data[item['ISBN']] = 0

            data[item['ISBN']] = data[item['ISBN']] + item['Anzahl']

        # Sort by quantity, only including items if above given limit
        return sorted([(isbn, quantity) for isbn, quantity in data.items() if quantity >= int(limit)], key=itemgetter(1), reverse=True)


    def get_ranking_chart(self, ranking, kind: str = 'barh'):
        # Load ranking into dataframe
        df = DataFrame([{'Anzahl': item[-1], 'ISBN': item[0]} for item in ranking], index=[item['ISBN'] for item in ranking])

        # Rotate & center x-axis labels
        pyplot.xticks(rotation=45, horizontalalignment='center')

        # Make graph 'just fit' image dimensions
        rcParams.update({'figure.autolayout': True})

        return df.plot(kind=kind).get_figure()


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

        for order in self.data.values():
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
