from os import remove
from os.path import join
from zipfile import ZipFile

from ..processors.gateways.paypal import Paypal
from ..processors.gateways.volksbank import Volksbank
from ..processors.knv.infos import InfoProcessor
from ..processors.knv.invoices import InvoiceProcessor
from ..processors.knv.orders import OrderProcessor
from ..processors.knv.shopkonfigurator import ShopkonfiguratorProcessor
from ..utils import load_json, dump_json
from ..utils import build_path, create_path, group_data, sort_data


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

        # Load merged data sources
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

        return self.gateways[identifier]().load_files(payment_files)


    # def get_invoices(self, invoice_files: list = None) -> Invoices:
    #     invoice_files = invoice_files if invoice_files else self.invoice_files['data']

    #     return Invoices(invoice_files)


    # def get_orders(self, order_files: list = None) -> Orders:
    #     order_files = order_files if order_files else self.order_files

    #     return Orders(order_files)


    # def get_infos(self, info_files: list = None) -> Infos:
    #     info_files = info_files if info_files else self.info_files

    #     return Infos(info_files)


    # def get_knv(self, data_files: list = None) -> KNV:
    #     data_files = data_files if data_files else self.db_files

    #     return KNV(data_files)
