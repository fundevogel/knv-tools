# This module contains classes for processing & working with
# 'Auftragsdaten' & 'Ausführungen, as exported from Shopkonfigurator
# See http://www.knv-info.de/wp-content/uploads/2020/04/Auftragsdatenexport2.pdf

# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from os.path import splitext

from ...utils import load_csv, load_json
from ..processor import Processor
from .infos import InfoProcessor
from .orders import OrderProcessor


class ShopkonfiguratorProcessor(Processor):
    # PROPS

    infos = {}
    orders = {}


    # I/O methods

    def load_files(self, files: list, identifier: str, preprocessed: bool = False) -> ShopkonfiguratorProcessor:
        # Check identifier
        if identifier not in ['infos', 'orders']:
            raise Exception('Unsupported identifier: "{}"'.format(identifier))

        handlers = {
            'infos': InfoProcessor,
            'orders': OrderProcessor
        }

        # Load files for further processing, either ..
        # (1) .. converting its data through appropriate processor
        if not preprocessed:
            setattr(self, identifier, handlers[identifier]().load_files(files).process().data)

        # (2) .. using its data as-is ..
        else:
            # .. which is currently only supported when dealing with JSON
            if splitext(files[0])[1].lower() == '.json': setattr(self, identifier, load_json(files))

        return self


    def load_data(self, data: list, identifier: str, preprocessed: bool = False) -> ShopkonfiguratorProcessor:
        # Check identifier
        if identifier not in ['infos', 'orders']:
            raise Exception('Unsupported identifier: "{}"'.format(identifier))

        handlers = {
            'infos': InfoProcessor,
            'orders': OrderProcessor
        }

        # Load data for further processing, either ..
        # (1) .. converting it through appropriate processor
        if not preprocessed:
            setattr(self, identifier, handlers[identifier]().load_data(data).process().data)

        # (2) .. using it as-is
        else: setattr(self, identifier, data)

        return self


    # CORE methods

    def process(self) -> ShopkonfiguratorProcessor:
        for order_number, order in self.orders.items():
            # Check for matching info ..
            if order_number in self.infos:
                # .. which is a one-to-one most the time
                info = self.infos[order_number]

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

            self.data[order_number] = order

        return self
