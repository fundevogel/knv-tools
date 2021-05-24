# ~*~ coding=utf-8 ~*~


import json

from os import remove
from os.path import join
from zipfile import ZipFile

from ..gateways.paypal import Paypal
from ..gateways.volksbank import Volksbank
from ..knv.shopkonfigurator import Shopkonfigurator
from ..knv.invoices import Invoices
from ..utils import build_path, create_path, group_data


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
        self.invoice_files = build_path(config.invoice_dir, '*.pdf')
        self.payment_files = {
            'paypal': build_path(join(config.payment_dir, 'paypal')),
            'volksbank': build_path(join(config.payment_dir, 'volksbank')),
        }

        # Load merged data sources
        self.data_files = build_path(config.database_dir)

        # Import config
        self.config = config


    # GENERAL methods

    def init(self) -> None:
        pass
        # self.orders = self.get_orders()
        # self.infos = self.get_infos()
        # self.invoices = self.get_invoices()


    def flush(self) -> None:
        files = self.payment_files['paypal'] + self.payment_files['volksbank']
        files += self.order_files + self.info_files + self.invoice_files

        for file in files:
            remove(file)


    # REBUILD methods

    def rebuild_orders(self) -> None:
        # Initialize handler
        handler = Shopkonfigurator()

        # Select order files to be imported
        import_files = build_path(self.config.import_dir, handler.orders_regex)

        # Extract information from import files
        handler.load_orders(import_files)

        # Split orders per-month & export them
        for code, data in group_data(handler.orders).items():
            self.dump_json(data, join(self.config.order_dir, code + '.json'))


    def rebuild_infos(self) -> None:
        # Initialize handler
        handler = Shopkonfigurator()

        # Select info files to be imported
        import_files = build_path(self.config.import_dir, handler.infos_regex)

        # Extract information from import files
        handler.load_infos(import_files)

        # Split infos per-month & export them
        for code, data in group_data(handler.infos).items():
            self.dump_json(data, join(self.config.info_dir, code + '.json'))


    def rebuild_invoices(self) -> None:
        # Initialize handler
        handler = Invoices()

        # Select invoice files to be imported
        import_files = build_path(self.config.import_dir, handler.regex)

        # Check invoices currently in database
        handler.load(self.invoice_files)

        for file in import_files:
            try:
                with ZipFile(file) as archive:
                    for zipped_invoice in archive.namelist():
                        # Import only invoices not already in database
                        if not handler.has(zipped_invoice):
                            archive.extract(zipped_invoice, self.config.invoice_dir)
                            handler.add(join(self.config.invoice_dir, zipped_invoice))

            except:
                raise Exception


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
            handler.load_csv(import_files)

            # Split payments per-month & export them
            for code, data in group_data(handler.data).items():
                self.dump_json(data, join(self.config.payment_dir, identifier, code + '.json'))


    def rebuild_data(self):
        order_files = build_path(self.config.order_dir)
        info_files = build_path(self.config.info_dir)
        handler = Shopkonfigurator(order_files, info_files)

        handler.init()

        for code, data in group_data(handler.data).items():
            self.dump_json(data, join(self.config.database_dir, code + '.json'))


    def rebuild(self):
        self.rebuild_orders()
        self.rebuild_infos()
        self.rebuild_invoices()
        self.rebuild_data()


    # GET methods

    def get_payments(self,
        identifier: str,
        year: int = None,
        quarter: int = None,
        months: list = None
    ):
        # Choose payment handler ..
        if identifier in ['paypal', 'volksbank']:
            # Load respective database entries
            payment_files = build_path(
                join(self.config.payment_dir, identifier),
                year=year,
                quarter=quarter,
                months=months
            )

            return self.gateways[identifier](payment_files)

        # .. otherwise, raise a formal complaint, fine Sir!
        raise Exception


    def get_invoices(self, invoice_files: list = None) -> Invoices:
        if invoice_files is not None:
            return Invoices(invoice_files)

        return Invoices(self.invoice_files)


    def get_data(self) -> Shopkonfigurator:
        handler = Shopkonfigurator()
        handler.load_data(self.data_files)

        return handler


    # HELPER methods

    def dump_json(self, data, json_file) -> None:
        create_path(json_file)

        with open(json_file, 'w') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
