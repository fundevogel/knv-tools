# ~*~ coding=utf-8 ~*~


from os import remove
from os.path import join
from datetime import datetime
from operator import itemgetter
from shutil import move

from lib.utils import load_csv, load_json, dump_json
from lib.utils import build_path, dedupe, group_data


class Database:
    def __init__(self, config: dict) -> None:
        # Import config
        self.config = config


    def flush(self) -> None:
        files = build_path(self.config.payment_dir) + build_path(self.config.order_dir) + build_path(self.config.info_dir)

        for file in files:
            remove(file)


    def process_payments(self, data) -> list:
        codes = set()
        payments = []

        for item in data:
            # Skip withdrawals
            if item['Brutto'][:1] == '-':
                continue

            # Assign identifier
            code = item['Transaktionscode']

            payment = {}

            payment['ID'] = code
            payment['Datum'] = self.convert_date(item['Datum'])
            payment['Vorgang'] = 'nicht zugeordnet'
            payment['Name'] = item['Name']
            payment['Email'] = item['Absender E-Mail-Adresse']
            payment['Brutto'] = self.convert_cost(item['Brutto'])
            payment['Gebühr'] = self.convert_cost(item['Gebühr'])
            payment['Netto'] = self.convert_cost(item['Netto'])
            payment['Währung'] = item['Währung']

            if code not in codes:
                codes.add(code)
                payments.append(payment)

        return payments


    def process_orders(self, order_data) -> list:
        orders = {}

        for item in order_data:
            # Create reliable article number ..
            clean_isbn = item['isbn']

            # .. since ISBNs are not always ISBNs
            if str(clean_isbn) == 'nan' or str(clean_isbn)[:3] != '978':
                clean_isbn = item['knvnumber']

            # .. and - more often than not - formatted as floats with a trailing zero
            clean_isbn = str(clean_isbn).replace('.0', '')

            # Assign identifier
            code = item['ormorderid']

            if code not in orders.keys():
                order = {}

                order['ID'] = code
                order['Datum'] = item['timeplaced'][:10]
                order['Anrede'] = item['rechnungaddresstitle']
                order['Vorname'] = item['rechnungaddressfirstname']
                order['Nachname'] = item['rechnungaddresslastname']
                order['Name'] = ' '.join([item['rechnungaddressfirstname'], item['rechnungaddresslastname']])
                order['Email'] = item['rechnungaddressemail']
                order['Bestellung'] = {clean_isbn: item['quantity']}
                order['Betrag'] = self.convert_cost(item['totalordercost'])
                order['Währung'] = item['currency']

                orders[code] = order

            else:
                if clean_isbn not in orders[code]['Bestellung'].keys():
                    orders[code]['Bestellung'][clean_isbn] = item['quantity']

                else:
                    orders[code]['Bestellung'][clean_isbn] = orders[code]['Bestellung'][clean_isbn] + item['quantity']

        return list(orders.values())


    def process_infos(self, info_data) -> list:
        infos = {}

        for item in info_data:
            # Create reliable invoice number ..
            clean_number = None

            if str(item['Invoice Number']) != 'nan':
                clean_number = str(item['Invoice Number']).replace('.0', '')

            # Assign identifier
            code = item['OrmNumber']

            if code not in infos.keys():
                info = {}

                info['ID'] = code
                info['Datum'] = item['Creation Date'][:10]
                info['Rechnungen'] = []

                if clean_number:
                    info['Rechnungen'].append(clean_number)

                infos[code] = info

            else:
                if clean_number and clean_number not in infos[code]['Rechnungen']:
                    infos[code]['Rechnungen'].append(clean_number)

        return list(infos.values())


    def import_payments(self) -> None:
        # Select payment files to be imported
        import_files = build_path(self.config.import_dir, self.config.payment_regex)

        # Generate payment data by ..
        # (1) .. fetching their content
        import_data = load_csv(import_files, 'utf-8', ',')

        # (2) .. removing duplicates
        # (3) .. extracting information
        import_data = self.process_payments(dedupe(import_data))

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
        import_data = self.process_orders(dedupe(import_data))

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
        import_data = self.process_infos(dedupe(import_data))

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


    # Helper tasks

    def convert_date(self, string) -> str:
        return datetime.strptime(string, '%d.%m.%Y').strftime('%Y-%m-%d')


    def convert_cost(self, string) -> str:
        if isinstance(string, float):
            string = str(string)

        string = float(string.replace(',', '.'))
        integer = f'{string:.2f}'

        return str(integer)
