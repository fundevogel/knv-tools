# ~*~ coding=utf-8 ~*~


from os import remove
from os.path import basename, join
from operator import itemgetter
from shutil import move
from zipfile import ZipFile

from .processors.paypal import process_payments
from .processors.shopkonfigurator import process_orders, process_infos
from .utils import load_csv, load_json, dump_json
from .utils import build_path, dedupe, group_data


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
        # (1) .. fetching their content
        import_data = load_csv(import_files, 'utf-8', ',')

        # (2) .. removing duplicates
        # (3) .. extracting information
        import_data, _ = process_payments(dedupe(import_data))

        # Load database files
        db_files = build_path(self.config.payment_dir)
        payments = load_json(db_files)

        # Compare existing & imported data if database was built before ..
        payments = self.merge_data(payments, import_data, 'Transaktion')

        # Sort payments by date
        payments.sort(key=itemgetter('Datum'))

        # Split payments per-month & export them
        for code, data in group_data(payments).items():
            dump_json(data, join(self.config.payment_dir, code + '.json'))


    def import_orders(self) -> None:
        # Select order files to be imported
        import_files = build_path(self.config.import_dir, self.config.order_regex)

        # Generate order data by ..
        # (1) .. fetching their content
        import_data = load_csv(import_files)

        # (2) .. removing duplicates
        # (3) .. extracting information
        import_data = process_orders(dedupe(import_data))

        # Load database files
        db_files = build_path(self.config.order_dir)
        orders = load_json(db_files)

        # Compare existing & imported data if database was built before ..
        orders = self.merge_data(orders, import_data, 'ID')

        # Sort orders by date
        orders.sort(key=itemgetter('Datum'))

        # Split orders per-month & export them
        for code, data in group_data(orders).items():
            dump_json(data, join(self.config.order_dir, code + '.json'))


    def import_infos(self) -> None:
        # Select info files to be imported
        import_files = build_path(self.config.import_dir, self.config.info_regex)

        # Generate info data by ..
        # (1) .. fetching their content
        import_data = load_csv(import_files)

        # (2) .. removing duplicates
        # (3) .. extracting information
        import_data = process_infos(dedupe(import_data))

        # Load database files
        db_files = build_path(self.config.info_dir)
        infos = load_json(db_files)

        # Compare existing & imported data if database was built before ..
        infos = self.merge_data(infos, import_data, 'ID')

        # Sort infos by date
        infos.sort(key=itemgetter('Datum'))

        # Split infos per-month & export them
        for code, data in group_data(infos).items():
            dump_json(data, join(self.config.info_dir, code + '.json'))


    def import_invoices(self) -> None:
        # Select invoice files to be imported
        invoice_files = build_path(self.config.import_dir, self.config.invoice_regex)

        # Check invoices currently in database
        invoices = build_path(self.config.invoice_dir, '*.pdf')
        invoices = [basename(invoice) for invoice in invoices]

        for invoice_file in invoice_files:
            try:
                with ZipFile(invoice_file) as archive:
                    for zipped_invoice in archive.namelist():
                        # Import only invoices not already in database
                        if not zipped_invoice in invoices:
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
