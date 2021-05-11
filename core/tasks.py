# ~*~ coding=utf-8 ~*~


from datetime import datetime, timedelta
from operator import itemgetter
from os.path import basename, join

import click
import pendulum
from PyPDF2 import PdfFileReader, PdfFileMerger

from core.utils import dump_csv, load_json
from core.utils import build_path, create_path, dedupe, group_data


class Tasks:
    def __init__(self, config: dict) -> None:
        # Import config
        self.config = config


    def task_match_payments(self, year, quarter) -> None:
        # Generate data from ..
        # (1) .. payment sources
        payment_files = build_path(self.config.payment_dir, year=year, quarter=quarter)
        payments = load_json(payment_files)

        # (2) .. order sources
        order_files = build_path(self.config.order_dir)
        orders = load_json(order_files)

        # (3) .. info sources
        info_files = build_path(self.config.info_dir)
        infos = load_json(info_files)

        # Match payments with orders & infos
        matches = self.match_payments(payments, orders, infos)

        if self.config.verbose:
            # Write m<tches to stdout
            click.echo(matches)

        else:
            # Filter & merge matched invoices
            invoices = build_path(self.config.invoice_dir, '*.pdf')
            self.export_invoices(matches, invoices)

            # Write results to CSV files
            for code, data in group_data(matches).items():
                csv_file = join(self.config.matches_dir, code, code + '.csv')
                dump_csv(data, csv_file)


    def match_payments(self, payments, orders, infos) -> list:
        results = []

        for payment in payments:
            # Assign payment to invoice number(s)
            # (1) Find matching order for current payment
            # (2) Find matching invoice number for this order
            matching_order = self.match_orders(payment, orders)

            if not matching_order:
                results.append(payment)
                continue

            matching_infos = self.match_infos(matching_order, infos)

            # Skip if no matching invoice numbers
            if not matching_infos:
                results.append(payment)
                continue

            # Store data
            # (1) Apply matching order number
            # (2) Add invoice number(s) to payment data
            # (3) Save matched payment
            payment['ID'] = matching_order['ID']
            payment['Vorgang'] = ';'.join(matching_infos)
            results.append(payment)

        return results


    def match_dates(self, base_date, test_date, days=1) -> bool:
        date_objects = [datetime.strptime(date, '%Y-%m-%d') for date in [base_date, test_date]]
        date_range = timedelta(days=days)

        if date_objects[0] <= date_objects[1] <= date_objects[0] + date_range:
            return True

        return False


    def match_orders(self, payment, orders) -> dict:
        candidates = []

        for item in orders:
            costs_match = payment['Brutto'] == item['Betrag']
            dates_match = self.match_dates(payment['Datum'], item['Datum'])

            if costs_match and dates_match:
                # Let them fight ..
                hits = 0

                # Determine chance of match for given payment & order
                # (1) Split by whitespace
                payment_name = payment['Name'].split(' ')
                order_name = item['Name'].split(' ')
                # (2) Take first list item as first name, last list item as last name
                payment_first, payment_last = payment_name[0], payment_name[-1]
                order_first, order_last = order_name[0], order_name[-1]

                # Add one point for matching first name, since that's more likely, but ..
                if payment_first.lower() == order_first.lower():
                    hits += 1

                # .. may be overridden by matching last name
                if payment_last.lower() == order_last.lower():
                    hits += 2

                candidates.append((hits, item))

        matches = sorted(candidates, key=itemgetter(0), reverse=True)

        if matches:
            return matches[0][1]

        return {}


    def match_infos(self, order, infos) -> list:
        info = []

        for info in infos:
            if info['ID'] == order['ID']:
                return info['Rechnungen']

        return []


    def export_invoices(self, matches, invoice_list) -> None:
        # Prepare invoice data
        invoices = {basename(invoice).split('-')[2][:-4]: invoice for invoice in invoice_list}

        for code, data in group_data(matches).items():
            # Extract matching invoice numbers
            invoice_numbers = []

            for item in data:
                if item['Vorgang'] != 'nicht zugeordnet':
                    if ';' in item['Vorgang']:
                        invoice_numbers += [number for number in item['Vorgang'].split(';')]
                    else:
                        invoice_numbers.append(item['Vorgang'])

            # Init merger object
            merger = PdfFileMerger()

            # Merge corresponding invoices
            for number in dedupe(invoice_numbers):
                if number in invoices:
                    pdf_file = invoices[number]

                    with open(pdf_file, 'rb') as file:
                        merger.append(PdfFileReader(file))

            # Write merged PDF to disk
            invoice_file = join(self.config.matches_dir, code, self.config.invoice_file)
            create_path(invoice_file)
            merger.write(invoice_file)


    def task_rank_sales(self, year, quarter) -> None:
        # Select order files to be analyzed
        order_files = build_path(self.config.order_dir, year=year, quarter=quarter)

        # Fetch their content
        orders = load_json(order_files)

        # Rank sales for given period
        ranking = self.rank_sales(orders)

        if self.config.verbose:
            # Write ranking to stdout
            click.echo(ranking)

        else:
            # Count total
            count = sum([item['Anzahl'] for item in ranking])

            # Write ranking to CSV file
            file_name = basename(order_files[0])[:-5] + '_' + basename(order_files[-1])[:-5] + '_' + str(count)
            ranking_file = join(self.config.rankings_dir, file_name + '.csv')

            dump_csv(ranking, ranking_file)


    def rank_sales(self, orders: list) -> list:
        data = {}

        # Sum up number of sales
        for order in orders:
            for isbn, quantity in order['Bestellung'].items():
                if isbn not in data:
                    data[isbn] = quantity

                else:
                    data[isbn] = data[isbn] + quantity

        ranking = []

        for isbn, quantity in data.items():
            item = {}

            item['ISBN'] = isbn
            item['Anzahl'] = quantity

            ranking.append(item)

        # Sort sales by quantity & in descending order
        ranking.sort(key=itemgetter('Anzahl'), reverse=True)

        return ranking


    def task_create_contacts(self, cutoff_date: str):
        # Set default date
        today = pendulum.today()

        if cutoff_date is None:
            cutoff_date = today.subtract(years=2).to_datetime_string()[:10]

        # Select order files to be analyzed
        order_files = build_path(self.config.order_dir)

        # Fetch their content
        orders = load_json(order_files)

        contacts = self.create_contacts(orders, cutoff_date, self.config.blocklist)

        if self.config.verbose:
            # Write contacts to stdout
            click.echo(contacts)

        else:
            # Write contacts to CSV file
            file_name = cutoff_date + '_' + today.to_datetime_string()[:10]
            contacts_file = join(self.config.contacts_dir, file_name + '.csv')

            dump_csv(contacts, contacts_file)


    def create_contacts(self, orders: list, cutoff_date: str = None, blocklist = []) -> list:
        # Set default date
        if cutoff_date is None:
            today = pendulum.today()
            cutoff_date = today.subtract(years=2).to_datetime_string()[:10]

        # Sort orders by date & in descending order
        orders.sort(key=itemgetter('Datum'), reverse=True)

        codes = set()
        contacts  = []

        for order in orders:
            mail_address = order['Email']

            # Check for blocklisted mail addresses
            if mail_address in blocklist:
                continue

            # Throw out everything before cutoff date (if provided)
            if order['Datum'] < cutoff_date:
                continue

            # Prepare dictionary
            contact = {}

            contact['Anrede'] = order['Anrede']
            contact['Vorname'] = order['Vorname']
            contact['Nachname'] = order['Nachname']
            contact['Name'] = order['Name']
            contact['Email'] = order['Email']
            contact['Letzte Bestelltung'] = self.convert_date(order['Datum'])

            if mail_address not in codes:
                codes.add(mail_address)
                contacts.append(contact)

        return contacts


    def convert_date(self, string: str) -> str:
        return datetime.strptime(string, '%Y-%m-%d').strftime('%d.%m.%Y')
