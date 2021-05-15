# ~*~ coding=utf-8 ~*~


from os import remove
from os.path import join
from operator import itemgetter
from shutil import move

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
        import_data = process_payments(dedupe(import_data))

        # Load database files
        db_files = build_path(self.config.payment_dir)
        payments = load_json(db_files)

        # Compare existing & imported data if database was built before ..
        if payments:
            # Populate set with identifiers
            codes = {payment['ID'] for payment in payments}

            # Merge only data not already in database
            for item in import_data:
                if item['ID'] not in codes:
                    payments.append(item)

        # .. otherwise, start from scratch
        else:
            payments = import_data

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
        if orders:
            # Populate set with identifiers
            codes = {order['ID'] for order in orders}

            # Merge only data not already in database
            for item in import_data:
                if item['ID'] not in codes:
                    orders.append(item)

        # .. otherwise, start from scratch
        else:
            orders = import_data

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
        if infos:
            # Populate set with identifiers
            codes = {info['ID'] for info in infos}

            # Merge only data not already in database
            for item in import_data:
                if item['ID'] not in codes:
                    infos.append(item)

        # .. otherwise, start from scratch
        else:
            infos = import_data

        # Sort infos by date
        infos.sort(key=itemgetter('Datum'))

        # Split infos per-month & export them
        for code, data in group_data(infos).items():
            dump_json(data, join(self.config.info_dir, code + '.json'))


    def import_invoices(self) -> None:
        # Select invoice files to be imported
        invoice_files = build_path(self.config.import_dir, '*.pdf')

        # Move them
        for invoice_file in invoice_files:
            move(invoice_file, self.config.invoice_dir)
