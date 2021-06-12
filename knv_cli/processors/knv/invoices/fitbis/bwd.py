# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from re import findall

from .fitbis import FitBisInvoiceProcessor


class BwdInvoiceProcessor(FitBisInvoiceProcessor):
    # PROPS

    regex = 'BWD_*.zip'


    # CORE methods

    def process(self) -> BwdInvoiceProcessor:
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
                'Brutto': 'keine Angabe',
                'Netto': 'keine Angabe',
                'MwSt': 'keine Angabe',
            }

            # Extract accounting period from first page
            pattern = r"(\d{2}.\d{2}.[2][0]\d{2})"
            dates = findall(pattern, content[0])

            if dates:
                invoice['Zeitraum'] = {
                    'von': dates[0],
                    'bis': dates[1],
                }

            # Extract essential information from ..
            # (1) .. last page
            content = content[len(content) - 1].split()
            # (2) .. last three costs, indicated by 'EUR'
            invoice['Netto'], invoice['MwSt'], invoice['Brutto'] = [self.number2string(content[index + 1]) for index in self.build_indices(content, 'EUR')[-3:]]

            invoices[invoice_number] = invoice

        self.data = invoices

        return self
