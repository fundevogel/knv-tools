# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from re import findall

from .fitbis import FitBisInvoiceProcessor


class SammelInvoiceProcessor(FitBisInvoiceProcessor):
    # PROPS

    regex = 'Sammelrechnungen_*.zip'


    # CORE methods

    def process(self) -> SammelInvoiceProcessor:
        '''
        Processes 'RE_{Ymd}_{VKN}_*.PDF' files
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
                'Zeitraum': 'keine Angabe',
                'Betrag': 'keine Angabe',
                'Skonto': 'keine Angabe',
                'MwSt': 'keine Angabe',
            }

            # Remove 'Korrekturaufstellung' pages from content
            content = [page for page in content if not 'Korrekturaufstellung' in page]

            # Extract accounting period from first page
            pattern = r"(\d{2}.\d{2}.[2][0]\d{2})"
            dates = findall(pattern, content[0])

            if dates:
                invoice['Zeitraum'] = {
                    'von': dates[0],
                    'bis': dates[1],
                }

            # Extract essential information from last page
            last_page = content[len(content) - 1].split()

            # (1) Determine invoice total
            invoice['Brutto'] = self.number2string(last_page[self.get_index(last_page, 'EUR') + 1])

            # (2) Determine tax rates
            reduced_tax, full_tax = [tax_rate for tax_rate in ['5%', '7%', '16%', '19%'] if tax_rate in ''.join(last_page)]

            # Fetch relevant data range
            starting_point = 0
            terminal_point = 0

            for index, line in enumerate(last_page):
                if 'Gesamt' in line:
                    starting_point = index + 1

                if 'Zahlbar' in line:
                    terminal_point = index + 1

            # Combine results
            if sum([starting_point, terminal_point]) > 0:
                invoice['Skonto'] = {}
                invoice['MwSt'] = {}

                try:
                    reduced_amount, _, reduced_share, full_amount, _, full_share = last_page[starting_point:terminal_point]

                    invoice['Skonto'][full_tax] = self.number2string(float(self.number2string(full_amount)) / 100 * 2)
                    invoice['MwSt'][full_tax] = {
                        'Brutto': self.number2string(full_amount),
                        'Anteil': self.number2string(full_share.split('Zahlbar')[0]),
                    }

                except ValueError:
                    # Only reduced items (= books) present, opposite case practically never happens ..
                    # TODO: .. or does it?
                    reduced_amount, _, reduced_share = last_page[starting_point:terminal_point]

                invoice['Skonto'][reduced_tax] = self.number2string(float(self.number2string(reduced_amount)) / 100 * 2)
                invoice['MwSt'][reduced_tax] = {
                    'Brutto': self.number2string(reduced_amount),
                    'Anteil': self.number2string(reduced_share.split('Zahlbar')[0]),
                }

            invoices[invoice_number] = invoice

        self.data = invoices

        return self
