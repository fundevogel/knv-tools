#! /usr/bin/python
# ~*~ coding=utf-8 ~*~


from datetime import datetime, timedelta
from operator import itemgetter
from os.path import basename, join

from pandas import DataFrame
from PyPDF2 import PdfFileReader, PdfFileMerger

from lib.handlers import load_json
from lib.utilities import build_path, create_path, dedupe, group_data


class Inspector:
    def __init__(self, config: dict) -> None:
        self.config = config


    def match(self, year, quarter) -> None:
        # Generate data from ..
        # (1) .. payment sources
        payment_files = build_path(self.config['payment_dir'], year=year, quarter=quarter)
        payments = load_json(payment_files)

        # (2) .. order sources
        order_files = build_path(self.config['order_dir'])
        orders = load_json(order_files)

        # (3) .. info sources
        info_files = build_path(self.config['info_dir'])
        infos = load_json(info_files)

        # Match payments with orders & infos
        matches = self.match_payments(payments, orders, infos)

        # Filter & merge matched invoices
        invoices = build_path(self.config['invoice_dir'], '*.pdf')
        self.export_pdf(matches, invoices)

        # Write results to CSV files
        self.export_csv(matches, self.config['match_dir'])


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


    # PDF tasks

    def export_pdf(self, matches, invoice_list) -> None:
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
            invoice_file = join(self.config['match_dir'], code, self.config['invoice_file'])
            create_path(invoice_file)
            merger.write(invoice_file)


    def export_csv(self, raw, base_dir):
        csv_data = dedupe(raw)

        for code, data in group_data(csv_data).items():
            csv_file = join(base_dir, code, code + '.csv')
            create_path(csv_file)

            DataFrame(data).to_csv(csv_file, index=False)
