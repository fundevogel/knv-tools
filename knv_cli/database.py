# ~*~ coding=utf-8 ~*~


from os import getcwd, remove
from os.path import basename, isfile, join
from operator import itemgetter
from shutil import move
from zipfile import ZipFile

from .processors.paypal import Paypal
from .processors.volksbank import Volksbank
from .processors.shopkonfigurator import Orders, Infos
from .processors.invoices import Invoices
from .utils import load_json, dump_json
from .utils import build_path, dedupe, group_data


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

        # Import config
        self.config = config


    # GENERAL methods

    def init(self) -> None:
        self.orders = self.get_orders()
        self.infos = self.get_infos()
        self.invoices = self.get_invoices()


    def flush(self) -> None:
        files = self.payment_files['paypal'] + self.payment_files['volksbank']
        files += self.order_files + self.info_files + self.invoice_files

        for file in files:
            remove(file)


    # IMPORT methods

    def import_payments(self) -> None:
        for identifier, gateway in self.gateways.items():
            # Initialize payment gateway handler
            handler = gateway()

            # Apply VKN & blocklist CLI options
            handler.VKN = self.config.vkn
            handler.blocklist = self.config.blocklist

            # Select payment files to be imported
            import_files = build_path(self.config.import_dir, handler.regex)

            # Generate payment data by ..
            # (1) .. extracting information from import files
            handler.load_csv(import_files)

            # (2) .. merging with existing data
            handler.load_json(self.payment_files[identifier])

            # Split payments per-month & export them
            for code, data in group_data(handler.data).items():
                dump_json(data, join(self.config.payment_dir, identifier, code + '.json'))


    def import_orders(self) -> None:
        # Initialize handler
        handler = Orders()

        # Select order files to be imported
        import_files = build_path(self.config.import_dir, handler.regex)

        # Generate order data by ..
        # (1) .. extracting information from import files
        handler.load_csv(import_files)

        # (2) .. merging with existing data
        handler.load_json(self.order_files)

        # Split orders per-month & export them
        for code, data in group_data(handler.data).items():
            dump_json(data, join(self.config.order_dir, code + '.json'))


    def import_infos(self) -> None:
        # Initialize handler
        handler = Infos()

        # Select info files to be imported
        import_files = build_path(self.config.import_dir, handler.regex)

        # Generate order data by ..
        # (1) .. extracting information from import files
        handler.load_csv(import_files)

        # (2) .. merging with existing data
        handler.load_json(self.info_files)

        # Split infos per-month & export them
        for code, data in group_data(handler.data).items():
            dump_json(data, join(self.config.info_dir, code + '.json'))


    def import_invoices(self) -> None:
        # Select invoice files to be imported
        import_files = build_path(self.config.import_dir, self.config.invoice_regex)

        # Check invoices currently in database
        handler = Invoices(self.invoice_files)

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


    def get_orders(self, order_files: list = None) -> Orders:
        if order_files is not None:
            return Orders(order_files)

        return Orders(self.order_files)


    def get_infos(self, info_files: list = None) -> Infos:
        if info_files is not None:
            return Infos(info_files)

        return Infos(self.info_files)


    def get_invoices(self, invoice_files: list = None) -> Infos:
        if invoice_files is not None:
            return Invoices(invoice_files)

        return Invoices(self.invoice_files)
