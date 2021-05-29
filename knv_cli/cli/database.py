# ~*~ coding=utf-8 ~*~


import json

from os import remove
from os.path import join
from zipfile import ZipFile

from ..gateways.paypal import Paypal
from ..gateways.volksbank import Volksbank
from ..knv.invoices import Invoices
from ..knv.orders import Orders
from ..knv.infos import Infos
from ..knv.shopkonfigurator import Shopkonfigurator
from ..utils import build_path, create_path, dump_json, group_data


class Database:
    # PROPS

    payments = None
    orders = None
    infos = None
    invoices = None

    # Available payment gateways
    gateways = {
        'paypal': Paypal,
        'volksbank': Volksbank,
    }


    def __init__(self, config: dict) -> None:
        # Establish database files
        self.order_files = build_path(config.order_dir)
        self.info_files = build_path(config.info_dir)
        self.invoice_files = {
            'pdf': build_path(join(config.invoice_dir, 'pdf'), '*.pdf'),
            'data': build_path(join(config.invoice_dir, 'data')),
        }
        self.payment_files = {
            'paypal': build_path(join(config.payment_dir, 'paypal')),
            'volksbank': build_path(join(config.payment_dir, 'volksbank')),
        }

        # Load merged data sources
        self.data_files = build_path(config.database_dir)

        # Import config
        self.config = config


    # GENERAL methods

    def flush(self) -> None:
        files = self.payment_files['paypal'] + self.payment_files['volksbank']
        files = self.invoice_files['pdf'] + self.invoice_files['data']
        files += self.order_files + self.info_files + self.invoice_files

        for file in files:
            remove(file)


    # REBUILD methods

    def rebuild_payments(self) -> None:
        for identifier, gateway in self.gateways.items():
            # Initialize payment gateway handler
            handler = gateway()

            # Apply VKN & blocklist CLI options
            handler.VKN = self.config.vkn
            handler.blocklist = self.config.blocklist

            # Select payment files to be imported
            import_files = build_path(self.config.import_dir, handler.regex)

            # Extract information from import files
            handler.load(import_files)

            # Split payments per-month & export them
            for code, data in group_data(handler.payments()).items():
                dump_json(data, join(self.config.payment_dir, identifier, code + '.json'))


    def rebuild_invoices(self) -> None:
        # Initialize handler
        handler = Invoices()

        # Select invoice files to be imported
        import_files = build_path(self.config.import_dir, handler.regex)

        # Extract invoices from archives
        for file in import_files:
            with ZipFile(file) as archive:
                for zipped_invoice in archive.namelist():
                    archive.extract(zipped_invoice, join(self.config.invoice_dir, 'pdf'))

        # Select imported invoice files ..
        invoice_files = build_path(join(self.config.invoice_dir, 'pdf'), '*.pdf')

        # .. and extract information from them
        handler.load(invoice_files)

        # Split invoice data per-month & export it
        for code, data in group_data(handler.invoices()).items():
            dump_json(data, join(self.config.invoice_dir, 'data', code + '.json'))


    def rebuild_orders(self) -> None:
        # Initialize handler
        handler = Orders()

        # Select order files to be imported
        import_files = build_path(self.config.import_dir, handler.regex)

        # Extract information from import files
        handler.load(import_files)

        # Split orders per-month & export them
        for code, data in group_data(handler.orders()).items():
            dump_json(data, join(self.config.order_dir, code + '.json'))


    def rebuild_infos(self) -> None:
        # Initialize handler
        handler = Infos()

        # Select info files to be imported
        import_files = build_path(self.config.import_dir, handler.regex)

        # Extract information from import files
        handler.load(import_files)

        # Split infos per-month & export them
        for code, data in group_data(handler.infos()).items():
            dump_json(data, join(self.config.info_dir, code + '.json'))


    def rebuild_data(self):
        handler = Shopkonfigurator()

        order_files = build_path(self.config.order_dir)
        info_files = build_path(self.config.info_dir)

        # Load import files & merge their data
        handler.load('orders', order_files).load('infos', info_files).init()

        for code, data in group_data(handler.data).items():
            dump_json(data, join(self.config.database_dir, code + '.json'))


    # GET methods

    def get_payments(self,
        identifier: str,
        year: int = None,
        quarter: int = None,
        months: list = None
    ):
        # Load respective database entries
        payment_files = build_path(
            join(self.config.payment_dir, identifier),
            year=year,
            quarter=quarter,
            months=months
        )

        return self.gateways[identifier](payment_files)


    def get_invoices(self, invoice_files: list = None) -> Invoices:
        if invoice_files:
            return Invoices(invoice_files)

        return Invoices(self.invoice_files['data'])


    def get_shopkonfigurator(self, data_files: list = None) -> Shopkonfigurator:
        if data_files:
            return Shopkonfigurator(data_files)

        return Shopkonfigurator(self.data_files)
