# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from os.path import basename, splitext
from zipfile import ZipFile

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError

from ..processor import Processor


class InvoiceProcessor(Processor):
    # PROPS

    regex = '*_Invoices_TimeFrom*_TimeTo*.zip'


    # I/O methods

    def load_files(self, files: list) -> InvoiceProcessor:
        invoices = {}

        for file in files:
            # Check filetype, depending on this either ..
            extension = splitext(file)[1].lower()

            # (1) .. extract PDF invoices to memory
            if extension == '.zip':
                # See https://stackoverflow.com/a/10909016
                archive = ZipFile(file)

                for file in archive.namelist():
                    invoices[file] = []

                    byte_stream = BytesIO(BytesIO(archive.read(file)).read())
                    byte_stream.seek(0)

                    try:
                        pdf = PdfFileReader(byte_stream)

                        for page in pdf.pages:
                            invoices[file] += [text.strip() for text in page.extractText().splitlines() if text]

                        byte_stream.close()

                    except PdfReadError:
                        pass

            # (2) .. parse PDF invoices directly
            if extension == '.pdf':
                invoices[file] = []

                # Fetch content from invoice file
                with open(file, 'rb') as pdf_file:
                    pdf = PdfFileReader(pdf_file)

                    for page in pdf.pages:
                        invoices[file] += [text.strip() for text in page.extractText().splitlines() if text]

        self.data = invoices

        return self


    # CORE methods

    def process(self) -> InvoiceProcessor:
        '''
        Processes '{VKN}-{Ymd}-*.pdf' & 'RE_{Ymd}_{VKN}_*.pdf' files
        '''

        invoices = {}

        for invoice, content in self.data.items():
            # Extract general information from file name
            invoice_number = self.invoice2number(invoice)
            invoice_date = self.invoice2date(invoice)

            # Prepare data storage
            invoice = {
                'Datum': invoice_date,
                'Vorgang': invoice_number,
                'Datei': invoice,
                'Versandkosten': self.number2string(0),
                'Gesamtbetrag': 'keine Angabe',
                'Steuern': 'keine Angabe',
                'Gutscheine': 'keine Angabe',
            }

            # Determine invoice kind, as those starting with 'R' are formatted quite differently
            if invoice_number[:1] == 'R':
                # Parse content, looking for ..
                # (1) .. general information
                for line in content:
                    if 'Rechnungsbetrag gesamt brutto' in line:
                        invoice['Gesamtbetrag'] = self.number2string(content[content.index(line) + 1])

                    if 'Versandpauschale' in line or 'Versandkosten' in line:
                        invoice['Versandkosten'] = self.number2string(content[content.index(line) + 2])

                    # Edge case with two lines preceeding shipping cost
                    if 'versandt an' in line:
                        invoice['Versandkosten'] = self.number2string(content[content.index(line) + 2])

                # (2) .. taxes
                taxes = {}

                # Determine tax rates where ..
                # .. 'reduced' equals either 5% or 7%
                # .. 'full' equals either 16% or 19%
                for tax_rate in ['0', '5', '7', '16', '19']:
                    tax_string = 'MwSt. ' + tax_rate + ',00 %'

                    if tax_string in content:
                        taxes[tax_rate + '%'] = self.number2string(content[content.index(tax_string) + 2])

                if taxes:
                    invoice['Steuern'] = taxes

                # (3) .. coupons
                if 'Gutschein' in content:
                    coupons = []

                    # Check if coupon was purchased ..
                    check_point = 0

                    if 'Gesamt:' in content:
                        check_point = self.get_index(content, 'Gesamt:')

                    if 'Gesamtbetrag' in content:
                        check_point = self.get_index(content, 'Gesamtbetrag')

                    for index in self.build_indices(content, 'Gutschein'):
                        # .. or applied
                        if check_point < index:
                            continue

                        coupons.append({
                            'Anzahl': int(content[index - 1]),
                            'Wert': self.number2string(content[index + 2]),
                        })

                    invoice['Gutscheine'] = coupons

            else:
                # Parse content, looking for ..
                # (1) .. general information
                for index, line in enumerate(content):
                    # TODO: Get values via regexes
                    if 'Versandkosten:' in line:
                        invoice['Versandkosten'] = self.number2string(line.replace('Versandkosten:', ''))

                    if 'Gesamtbetrag' in line:
                        invoice['Gesamtbetrag'] = self.number2string(line.replace('Gesamtbetrag', ''))

                # Fetch first occurence of ..
                # .. 'Nettobetrag' (= starting point)
                starting_point = self.get_index(content, 'Nettobetrag')

                # .. 'Gesamtbetrag' (= terminal point)
                terminal_point = self.get_index(content, 'Gesamtbetrag')

                # Try different setup, since some invoices are the other way around
                reverse_order = starting_point > terminal_point

                if reverse_order:
                    # In this case, fetch last occurence of 'EUR' (= terminal point)
                    terminal_point = self.get_index(content, 'EUR', True)

                costs = content[starting_point:terminal_point + 1]

                # (2) .. taxes
                invoice['Steuern'] = {}

                # Determine tax rates where ..
                tax_rates = [self.format_tax_rate(tax_rate) for tax_rate in costs[:2]]

                # .. 'reduced' equals either 5% or 7%
                reduced_tax = 0

                # .. 'full' equals either 16% or 19%
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

                invoice['Steuern'][tax_rates[0]] = self.number2string(reduced_tax)
                invoice['Steuern'][tax_rates[1]] = self.number2string(full_tax)

            invoices[invoice_number] = invoice

        self.data = invoices

        return self


    # HELPER methods

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


    def invoice2date(self, string: str) -> str:
        date_string = self.split_string(string)[1].replace('.pdf', '')

        return datetime.strptime(date_string, '%Y%m%d').strftime('%Y-%m-%d')


    def invoice2number(self, string: str) -> str:
        string_list = self.split_string(string)

        # Sort out invoice numbers
        if len(string_list) == 1:
            return string

        return string_list[-1].replace('.pdf', '')


    def number2string(self, string) -> str:
        # Strip 'EUR', apart from that as usual
        return super().number2string(str(string).replace('EUR', ''))


    def get_index(self, haystack: list, needle: str, last: bool = False) -> int:
        position = -1 if last else 0

        return [i for i, string in enumerate(haystack) if needle in string][position]


    def build_indices(self, haystack: list, needle: str) -> list:
        return [count for count, line in enumerate(haystack) if line == needle]


    def format_tax_rate(self, string: str) -> str:
        return (string[:-1].replace('Nettobetrag', '')).strip()
