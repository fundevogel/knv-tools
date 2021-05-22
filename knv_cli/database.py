# ~*~ coding=utf-8 ~*~


from os import getcwd, remove
from os.path import basename, isfile, join
from operator import itemgetter
from shutil import move
from zipfile import ZipFile

from .processors.paypal import Paypal
from .processors.volksbank import Volksbank
from .processors.shopkonfigurator import Orders, Infos
from .utils import load_json, dump_json
from .utils import build_path, dedupe, group_data, invoice2number


class Database:
    # PROPS

    gateways = {
        'paypal': Paypal,
        'volksbank': Volksbank,
    }


    def __init__(self, config: dict) -> None:
        # Import config
        self.config = config


    # GENERAL methods

    def flush(self) -> None:
        files = build_path(join(self.config.payment_dir, 'paypal'))
        files += build_path(join(self.config.payment_dir, 'volksbank'))
        files += build_path(self.config.payment_dir)
        files += build_path(self.config.order_dir)
        files += build_path(self.config.info_dir)

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
            handler.load_json(build_path(join(self.config.payment_dir, identifier)))

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
        handler.load_json(build_path(self.config.order_dir))

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
        handler.load_json(build_path(self.config.info_dir))

        # Split infos per-month & export them
        for code, data in group_data(handler.data).items():
            dump_json(data, join(self.config.info_dir, code + '.json'))


    def import_invoices(self) -> None:
        # Select invoice files to be imported
        invoice_files = build_path(self.config.import_dir, self.config.invoice_regex)

        # Check invoices currently in database
        invoices = build_path(self.config.invoice_dir, '*.pdf')
        invoices = {invoice2number(invoice): invoice for invoice in invoices}

        for invoice_file in invoice_files:
            try:
                with ZipFile(invoice_file) as archive:
                    for zipped_invoice in archive.namelist():
                        # Import only invoices not already in database
                        if not invoice2number(zipped_invoice) in invoices:
                            archive.extract(zipped_invoice, self.config.invoice_dir)

            except:
                raise Exception


    def load_payments(self,
        identifier: str,
        year: int = None,
        quarter: int = None,
        months: list = None
    ):
        # Choose payment handler ..
        if identifier in ['paypal', 'volksbank']:
            # Initialize handler
            handler = self.gateways[identifier]()

            # Load respective database entries
            handler.load_json(build_path(join(self.config.payment_dir, identifier)))

            return handler

        # .. otherwise, raise a formal complaint, fine Sir!
        raise Exception


    def load_orders(self) -> Orders:
        # Load orders from database
        handler = Orders()
        handler.load_json(build_path(self.config.order_dir))

        return handler


    def load_infos(self) -> Infos:
        # Load infos from database
        handler = Infos()
        handler.load_json(build_path(self.config.info_dir))

        return handler
