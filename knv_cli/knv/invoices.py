# This module contains a class for processing & working with
# invoices (PDF), as exported from FitBis & Shopkonfigurator


from datetime import datetime
from os.path import basename

import PyPDF2

from ..command import Command


class Invoices():
    # PROPS

    regex = '*_Invoices_TimeFrom*_TimeTo*.zip'


    def __init__(self, invoice_files: list = None):
        if invoice_files:
            self.invoices = {self.invoice2number(invoice): invoice for invoice in invoice_files}


    # DATA methods

    def load(self, invoice_files: list) -> None:
        self.invoices = {self.invoice2number(invoice): invoice for invoice in invoice_files}


    def has(self, invoice: str) -> bool:
        return self.invoice2number(invoice) in self.invoices.keys()


    def get(self, invoice_number: str) -> str:
        return self.invoices[invoice_number]


    def add(self, invoice: str) -> None:
        self.invoices[self.invoice2number(invoice)] = invoice


    def remove(self, invoice_number: str) -> None:
        del self.invoices[invoice_number]


    # PARSING methods

    def parse(self, invoice_file) -> list:
        # Make sure given invoice is available for parsing
        if self.invoice2number(invoice_file) not in self.invoices:
            raise Exception

        # Normalize input
        invoice_file = self.invoices[self.invoice2number(invoice_file)]

        # Extract general information from file name
        invoice_date = self.invoice2date(invoice_file)
        invoice_number = self.invoice2number(invoice_file)

        # Prepare data
        invoice = {
            'Rechnungsnummer': invoice_number,
            'Datum': invoice_date,
            'Steuern': {},
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
            # (1) .. coupons
            coupons = []

            if 'Gutschein' in content:
                coupon_indices = [count for count, line in enumerate(content) if line == 'Gutschein']

                for index in coupon_indices:
                    coupons.append({
                        'Anzahl': content[index - 1],
                        'Wert': content[index + 2],
                    })

            # (2) .. taxes
            for tax_rate in ['5', '7', '16', '19']:
                if 'MwSt. ' + tax_rate + ',00 %' in content:
                    invoice['Steuern'][tax_rate + '%'] = content[content.index('MwSt. ' + tax_rate + ',00 %') + 2]

        else:
            data = {}

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

            # Determine available tax rates
            tax_rates = [self.format_tax_rate(tax_rate) for tax_rate in costs[:2]]

            if len(costs) < 6:
                data[tax_rates[0]] = costs[4].replace('MwSt. gesamt:', '').split(' ')[0]
                data[tax_rates[1]] = costs[2].split('EUR')[1]

            else:
                # Fetch tax rates, either 5% / 16% or 7% / 19%
                tax_rates = [self.format_tax_rate(tax_rate) for tax_rate in costs[:2]]

                # Distinguish (another) two kinds of invoices ..
                if costs[2][-3:] == 'EUR':
                    # .. and another two
                    if len(costs[2].split(':')[-1].split(' ')) > 2:
                        data[tax_rates[0]] = costs[2].split(':')[-1].split(' ')[0]
                        data[tax_rates[1]] = costs[6].split(' ')[0]

                    else:
                        # .. aaaaand another two
                        i = 5

                        if 'MwSt.' in costs[6]:
                            i = 6
                        #     data[tax_rates[0]] = costs[6].split(':')[-1].split(' ')[0]
                        #     data[tax_rates[1]] = costs[7].split(' ')[0]

                        # else:
                        data[tax_rates[0]] = costs[i].split(':')[-1].split(' ')[0]
                        data[tax_rates[1]] = costs[i + 1].split(' ')[0]

                else:
                    # .. well, what do you know
                    if 'Zwischensumme' in costs[4]:
                        data[tax_rates[0]] = costs[4].replace('MwSt. gesamt:', '').split(' ')[0]
                        data[tax_rates[1]] = costs[4].split('EUR')[1]

                    else:
                        data[tax_rates[0]] = costs[4].split(':')[-1].split(' ')[0]
                        data[tax_rates[1]] = costs[5].split(' ')[0]

            for index, line in enumerate(content):
                if 'Versandkosten:' in line:
                    data['Versandkosten'] = line.replace('Versandkosten:', '')

                if 'Zwischensumme:' in line:
                    data['Zwischensumme'] = line.split('Zwischensumme:')[-1]

                if 'Gesamtbetrag' in line:
                    data['Gesamtbetrag'] = line.replace('Gesamtbetrag', '')

            invoice['Steuern'] = data

        return invoice


    # PARSING HELPER methods

    def format_tax_rate(self, string: str) -> str:
        return (string[:-1].replace('Nettobetrag', '')).strip()


    def get_index(self, haystack: list, needle: str, last: bool = False) -> int:
        position = 0

        if last:
            position = -1

        return [i for i, string in enumerate(haystack) if needle in string][position]


    def convert_number(self, string) -> str:
        # Clear whitespaces & convert to string (suck it, `int` + `float`)
        string = str(string).strip()

        # Take care of thousands separator, as in '1.234,56'
        if '.' in string and ',' in string:
            string = string.replace('.', '')

        string = float(string.replace(',', '.'))
        integer = f'{string:.2f}'

        return str(integer)


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
