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


class Shopkonfigurator(BaseClass):
    # PROPS

    data = None
    orders = None
    infos = None
    invoices = None


    def __init__(self, data_files: list = None) -> None:
        if data_files:
            self.data = load_json(data_files)


    # DATA methods

    def load(self, identifier: str, data_files: list = None) -> Shopkonfigurator:
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


    def get(self, order_number: str) -> dict:
        for item in self.data:
            if order_number in item['ID']:
                return item

        return {}


    def init(self, force: bool = False) -> Shopkonfigurator:
        # Merge orders & infos
        if not self.data or force:
            self.data = self.merge_data(self.orders, self.infos, self.invoices)

        return self


    def merge_data(self, order_data: list, info_data: list, invoice_data: list) -> list:
        data = {}

        for order_number, order in order_data.items():
            for info in info_data.values():
                # Match order & info one-to-one first
                if order_number == info['ID']:
                    # Prepare data storage for invoices & their items
                    purchase = {}

                    for invoice_number, invoice_items in info['Bestellung'].items():
                        purchase[invoice_number] = []

                        matching_order = [order for order in order['Bestellung'] if order['Nummer'] in invoice_items][0]

                        for invoice_item in invoice_items.values():
                            invoice_item['ISBN'] = matching_order['ISBN']
                            invoice_item['Titel'] = matching_order['Titel']
                            invoice_item['Steuersatz'] = matching_order['Steuersatz']
                            invoice_item['Steueranteil'] = matching_order['Steueranteil']
                            invoice_item['ISBN'] = matching_order['ISBN']

                            purchase[invoice_number].append(invoice_item)

                    order['Bestellung'] = purchase

                    # Extract taxes from invoice files if invoice handler is available
                    # TODO: Add missing invoices to global store
                    # parsed_invoices = self.invoice_handler.parse_invoices(list(purchase.keys()))
                    # order['Steuern'] = {invoice['Vorgang']: invoice['Steuern'] for invoice in parsed_invoices[0]}

                    # if parsed_invoices[-1]:
                    #     print(parsed_invoices[-1])

                    # Move on to next order
                    break

            data[order_number] = order

        return data


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


    def get_ranking_chart(self, ranking, limit: int = 1, kind: str = 'barh'):
        # Update ranking to only include entries above set limit
        ranking = [{'Anzahl': item['Anzahl'], 'ISBN': item['ISBN']} for item in ranking if item['Anzahl'] >= int(limit)]
        df = DataFrame(ranking, index=[item['ISBN'] for item in ranking])

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
