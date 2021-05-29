# This module contains a class for processing & working with
# invoices (PDF), as exported from FitBis & Shopkonfigurator


from datetime import datetime
from operator import itemgetter
from os.path import basename, isfile, splitext

import PyPDF2

from ..command import Command
from ..utils import load_json


class Invoices(Command):
    # PROPS

    regex = '*_Invoices_TimeFrom*_TimeTo*.zip'


    # DATA methods

    def load_data(self, data_files: list) -> list:
        return self.process_data(data_files)


    def process_data(self, data_files: list) -> list:
        return [self.parse(data_file) for data_file in data_files]


    def has(self, invoice_file: str) -> bool:
        return self.invoice2number(invoice_file) in [invoice['Vorgang'] for invoice in self.data]


    def get(self, invoice_number: str) -> str:
        return [invoice['Datei'] for invoice in self.data if invoice['Vorgang'] == self.invoice2number(invoice_number)][0]


    # PARSING methods

    def parse(self, invoice_file: str) -> dict:
        # Make sure given invoice is real file
        if not isfile(invoice_file):
            return {}

        # Extract general information from file name
        invoice_date = self.invoice2date(invoice_file)
        invoice_number = self.invoice2number(invoice_file)

        # Prepare data storage
        invoice = {
            'Datei': invoice_file,
            'Vorgang': invoice_number,
            'Datum': invoice_date,
            'Versandkosten': '0.00',
            'Gesamtbetrag': 'keine Angabe',
            'Steuern': {},
            'Gutscheine': 'keine Angabe',
        }

        content = []

        # Fetch content from invoice file
        with open(invoice_file, 'rb') as file:
            pdf = PyPDF2.PdfFileReader(file)

            for page in pdf.pages:
                content += [text.strip() for text in page.extractText().splitlines() if text]

        # Determine invoice kind, as those starting with 'R' are formatted quite differently
        if invoice_number[:1] == 'R':
            # Parse content, looking for information about ..
            # (1) .. general information
            for line in content:
                if 'Rechnungsbetrag gesamt brutto' in line:
                    invoice['Gesamtbetrag'] = self.convert_number(content[content.index(line) + 1])

                if 'Versandpauschale' in line or 'Versandkosten' in line:
                    invoice['Versandkosten'] = self.convert_number(content[content.index(line) + 2])

                # Edge case with two lines preceeding shipping cost
                if 'versandt an' in line:
                    invoice['Versandkosten'] = self.convert_number(content[content.index(line) + 2])

            # (2) .. taxes
            for tax_rate in ['5', '7', '16', '19']:
                tax_string = 'MwSt. ' + tax_rate + ',00 %'

                if tax_string in content:
                    invoice['Steuern'][tax_rate + '%'] = self.convert_number(content[content.index(tax_string) + 2])

            # (3) .. coupons
            if 'Gutschein' in content:
                coupons = []

                # Check if coupon was purchased ..
                check_point = 0 if 'Gesamtbetrag' not in content else self.get_index(content, 'Gesamtbetrag')

                for index in self.build_indices(content, 'Gutschein'):
                    # .. or applied
                    if check_point < index:
                        continue

                    coupons.append({
                        'Anzahl': int(content[index - 1]),
                        'Wert': self.convert_number(content[index + 2]),
                    })

                invoice['Gutscheine'] = coupons

        else:
            # Gather general information
            for index, line in enumerate(content):
                # TODO: Get values via regexes
                if 'Versandkosten:' in line:
                    invoice['Versandkosten'] = self.convert_number(line.replace('Versandkosten:', ''))

                if 'Gesamtbetrag' in line:
                    invoice['Gesamtbetrag'] = self.convert_number(line.replace('Gesamtbetrag', ''))

            # Fetch first occurence of ..
            # (1) .. 'Nettobetrag' (= starting point)
            starting_point = self.get_index(content, 'Nettobetrag')

            # (2) .. 'Gesamtbetrag' (= terminal point)
            terminal_point = self.get_index(content, 'Gesamtbetrag')

            # Try different setup, since some invoices are the other way around
            reverse_order = starting_point > terminal_point

            if reverse_order:
                # In this case, fetch last occurence of 'EUR' (= terminal point)
                terminal_point = self.get_index(content, 'EUR', True)

            costs = content[starting_point:terminal_point + 1]

            # Determine tax rates:
            # reduced = 5% or 7%
            # full = 16% or 19%
            tax_rates = [self.format_tax_rate(tax_rate) for tax_rate in costs[:2]]

            reduced_tax = 0
            full_tax = 0

            if len(costs) < 8:
                costs_list = costs[4].replace('MwSt. gesamt:', '').split()

                reduced_tax = costs_list[0]
                full_tax = costs_list[1]

                if len(costs_list) < 3:
                    full_tax = costs[5]

            elif len(costs) == 9:
                reduced_tax = costs[4].split(':')[-1]
                full_tax = costs[5]

                if 'MwSt. gesamt' in costs[5]:
                    costs_list = costs[5].split(':')[-1].split()

                    reduced_tax = costs_list[0]
                    full_tax = costs_list[1]

                if 'MwSt. gesamt' in costs[6]:
                    reduced_tax = costs[6].split(':')[-1]
                    full_tax = costs[7]


            elif len(costs) in [10, 11]:
                index = 6 if 'MwSt.' in costs[6] else 5

                reduced_tax = costs[index].split(':')[-1].split()[0]
                full_tax = costs[index + 1].split()[0]

            else:
                reduced_tax = costs[5].split()[0]
                full_tax = costs[2].split()[2]

                if reduced_tax == 'MwSt.':
                    reduced_tax = costs[5].split(':')[-1]
                    full_tax = costs[6]

            invoice['Steuern'][tax_rates[0]] = self.convert_number(reduced_tax)
            invoice['Steuern'][tax_rates[1]] = self.convert_number(full_tax)

        return invoice


    # PARSING HELPER methods

    def format_tax_rate(self, string: str) -> str:
        return (string[:-1].replace('Nettobetrag', '')).strip()


    def get_index(self, haystack: list, needle: str, last: bool = False) -> int:
        position = 0

        if last:
            position = -1

        return [i for i, string in enumerate(haystack) if needle in string][position]


    def build_indices(self, haystack: list, needle: str) -> list:
        return [count for count, line in enumerate(haystack) if line == needle]


    def convert_number(self, string) -> str:
        # Strip 'EUR', apart from that as usual
        return super().convert_number(str(string).replace('EUR', ''))


    # HELPER methods

    def invoice2date(self, string: str) -> str:
        date_string = self.split_string(string)[1].replace('.pdf', '')

        return datetime.strptime(date_string, '%Y%m%d').strftime('%Y-%m-%d')


    def invoice2number(self, string: str) -> str:
        string_list = self.split_string(string)

        # Sort out invoice numbers
        if len(string_list) == 1:
            return string

        return string_list[-1].replace('.pdf', '')


    def split_string(self, string: str) -> str:
        # Strip path information
        string = basename(string)

        # Distinguish between delimiters ..
        # (1) .. hyphen ('Shopkonfigurator')
        delimiter = '-'

        # (2) .. underscore ('Barsortiment')
        if delimiter not in string:
            delimiter = '_'

        return string.split(delimiter)


    # OUTPUT methods

    def invoices(self):
        # Sort invoices by date & order number, output as list
        return sorted(list(self.data.values()), key=itemgetter('Datum', 'Vorgang'))
