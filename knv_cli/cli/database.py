from os import remove
from os.path import basename, join
from zipfile import ZipFile

from ..structure.payments.payments import Payments
from ..structure.payments.paypal import PaypalPayments
from ..structure.payments.volksbank import VolksbankPayments
from ..processors.gateways.paypal import Paypal
from ..processors.gateways.volksbank import Volksbank
from ..processors.knv.infos import InfoProcessor
from ..processors.knv.invoices import InvoiceProcessor
from ..processors.knv.orders import OrderProcessor
from ..processors.knv.shopkonfigurator import ShopkonfiguratorProcessor
from ..structure.invoices.invoices import Invoices
from ..structure.orders.orders import Orders
from ..structure.payments.payments import Payments
from ..utils import load_json, dump_json
from ..utils import build_path, dedupe, group_data, sort_data
from .session import Session


class Database:
    # PROPS

    gateways = {
        'paypal': Paypal,
        'volksbank': Volksbank,
    }

    structures = {
        'paypal': PaypalPayments,
        'volksbank': VolksbankPayments,
    }


    def __init__(self, config: dict) -> None:
        # Define database files
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

        # Define session files
        self.session_files = build_path(join(config.payment_dir, 'session'))

        # Define merged data files
        self.db_files = build_path(config.database_dir)

        # Import config
        self.config = config


    # GENERAL methods

    def flush(self) -> None:
        files = self.order_files + self.info_files
        files += self.invoice_files['pdf'] + self.invoice_files['data']
        files += self.payment_files['paypal'] + self.payment_files['volksbank']

        for file in files:
            remove(file)


    # REBUILD methods

    def rebuild_data(self):
        # Initialize handler
        handler = ShopkonfiguratorProcessor()

        # Load data files for infos & orders
        handler.load_files(self.info_files, 'infos', True)
        handler.load_files(self.order_files, 'orders', True)

        for code, data in group_data(handler.process().data).items():
            dump_json(sort_data(data), join(self.config.database_dir, code + '.json'))


    def rebuild_infos(self) -> None:
        # Initialize handler
        handler = InfoProcessor()

        # Select info files to be imported
        import_files = build_path(self.config.import_dir, handler.regex)

        # Extract information from import files
        handler.load_files(import_files).process()

        # Split infos per-month & export them
        for code, data in group_data(handler.data).items():
            dump_json(sort_data(data), join(self.config.info_dir, code + '.json'))


    def rebuild_invoices(self) -> None:
        # Initialize handler
        handler = InvoiceProcessor()

        # Select invoice files to be imported
        import_files = build_path(self.config.import_dir, handler.regex)

        # Set directory for extracted invoice files
        invoice_dir = join(self.config.invoice_dir, 'pdf')

        # Extract invoices from archives
        for file in import_files:
            with ZipFile(file) as archive:
                for zipped_invoice in archive.namelist():
                    archive.extract(zipped_invoice, invoice_dir)

        # .. and extract information from them
        handler.load_files(build_path(invoice_dir, '*.pdf')).process()

        # Split invoice data per-month & export it
        for code, data in group_data(handler.data).items():
            dump_json(sort_data(data), join(self.config.invoice_dir, 'data', code + '.json'))


    def rebuild_orders(self) -> None:
        # Initialize handler
        handler = OrderProcessor()

        # Select order files to be imported
        import_files = build_path(self.config.import_dir, handler.regex)

        # Extract information from import files
        handler.load_files(import_files).process()

        # Split orders per-month & export them
        for code, data in group_data(handler.data).items():
            dump_json(sort_data(data), join(self.config.order_dir, code + '.json'))


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
            handler.load_files(import_files).process()

            # Split payments per-month & export them
            for code, data in group_data(handler.data).items():
                dump_json(sort_data(data), join(self.config.payment_dir, identifier, code + '.json'))


    # GET methods

    def get_invoices(self, invoice_files: list = None) -> Invoices:
        # Select appropriate source files
        invoice_files = invoice_files if invoice_files else self.invoice_files['data']

        return Invoices(load_json(invoice_files))


    def get_orders(self, order_files: list = None):
        # Select appropriate source files
        order_files = order_files if order_files else self.db_files

        return Orders(load_json(order_files), load_json(self.invoice_files['data']))


    def get_payments(self, identifier: str, payment_files: list = None):
        # Select appropriate source files
        payment_files = payment_files if payment_files else self.payment_files[identifier]

        return self.structures[identifier](load_json(payment_files), load_json(self.db_files), load_json(self.invoice_files['data']))


    def get_data(self, identifier: str) -> dict:
        data = load_json(self.db_files)

        return {} if identifier not in data else data[identifier]


    def get_info(self, identifier: str) -> dict:
        infos = load_json(self.info_files)

        return {} if identifier not in infos else infos[identifier]


    def get_invoice(self, identifier: str) -> dict:
        invoices = load_json(self.invoice_files['data'])

        return {} if identifier not in invoices else invoices[identifier]


    def get_order(self, identifier: str) -> dict:
        orders = load_json(self.order_files)

        return {} if identifier not in orders else orders[identifier]


    def get_payment(self, identifier: str) -> dict:
        payments = load_json(self.payment_files['paypal'])

        return {} if identifier not in payments else payments[identifier]


    # ACCOUNTING methods

    def open_paid(self) -> dict:
        data = {}

        for text_file in build_path(self.config.payment_dir, '*-paid.txt'):
            # Assign year
            year = basename(text_file).split('-')[0]

            with open(text_file, 'r') as file:
                data[year] = file.read().splitlines()

        return data


    def save_paid(self, data: list) -> None:
        for year, lines in data.items():
            with open(join(self.config.payment_dir, year + '-paid.txt'), 'w') as file:
                file.writelines("%s\n" % i for i in dedupe(lines))


    # ACCOUNTING SESSION methods

    def save_session(self, data: dict) -> None:
        Session(data).save(self.config.session_dir)


    def load_session(self) -> Session:
        return Session(load_json(self.session_files))
