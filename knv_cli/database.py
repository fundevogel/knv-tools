# ~*~ coding=utf-8 ~*~


from os import remove
from os.path import basename, join
from operator import itemgetter
from shutil import move
from zipfile import ZipFile

from .processors.paypal import Paypal
from .processors.shopkonfigurator import Orders, Infos
from .utils import load_csv, load_json, dump_json
from .utils import build_path, dedupe, group_data, invoice2id


class Database:
    def __init__(self, config: dict) -> None:
        # Import config
        self.config = config


    # GENERAL methods

    def flush(self) -> None:
        files = build_path(self.config.payment_dir) + build_path(self.config.order_dir) + build_path(self.config.info_dir)

        for file in files:
            remove(file)


    # IMPORT methods

    def import_payments(self) -> None:
        # Select payment files to be imported
        import_files = build_path(self.config.import_dir, self.config.payment_regex)

        # Generate payment data by ..
        # (1) .. extracting information from import files
        handler = Paypal()
        handler.load_csv(import_files, 'utf-8', ',')

        # (2) .. merging with existing data
        handler.load_json(build_path(self.config.payment_dir))

        # Split payments per-month & export them
        for code, data in group_data(handler.payments()).items():
            dump_json(data, join(self.config.payment_dir, code + '.json'))


    def import_orders(self) -> None:
        # Select order files to be imported
        import_files = build_path(self.config.import_dir, self.config.order_regex)

        # Generate order data by ..
        # (1) .. extracting information from import files
        handler = Orders()
        handler.load_csv(import_files)

        # (2) .. merging with existing data
        handler.load_json(build_path(self.config.order_dir))

        # Split orders per-month & export them
        for code, data in group_data(handler.orders()).items():
            dump_json(data, join(self.config.order_dir, code + '.json'))


    def import_infos(self) -> None:
        # Select info files to be imported
        import_files = build_path(self.config.import_dir, self.config.info_regex)

        # Generate order data by ..
        # (1) .. extracting information from import files
        handler = Infos()
        handler.load_csv(import_files)

        # (2) .. merging with existing data
        handler.load_json(build_path(self.config.info_dir))

        # Split infos per-month & export them
        for code, data in group_data(handler.infos()).items():
            dump_json(data, join(self.config.info_dir, code + '.json'))


    def import_invoices(self) -> None:
        # Select invoice files to be imported
        invoice_files = build_path(self.config.import_dir, self.config.invoice_regex)

        # Check invoices currently in database
        invoices = build_path(self.config.invoice_dir, '*.pdf')
        invoices = {invoice2id(invoice, '-'): invoice for invoice in invoices}

        for invoice_file in invoice_files:
            try:
                with ZipFile(invoice_file) as archive:
                    for zipped_invoice in archive.namelist():
                        # Import only invoices not already in database
                        if not invoice2id(zipped_invoice, '-') in invoices:
                            archive.extract(zipped_invoice, self.config.invoice_dir)

            except:
                raise Exception


    def merge_data(self, data, import_data: list, identifier: str) -> list:
        if data:
            # Populate set with identifiers
            codes = {item[identifier] for item in data}

            # Merge only data not already in database
            for item in import_data:
                if item[identifier] not in codes:
                    codes.add(item[identifier])
                    data.append(item)

        # .. otherwise, start from scratch
        else:
            data = import_data

        return data
