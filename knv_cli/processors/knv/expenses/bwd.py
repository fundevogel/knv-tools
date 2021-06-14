# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from re import findall

from ..invoices import InvoiceProcessor


class BwdInvoiceProcessor(InvoiceProcessor):
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
                'Status': 'S',
                'Zeitraum': 'keine Angabe',
                'Skonto': 'keine Angabe',
                'Brutto': 'keine Angabe',
                'Netto': 'keine Angabe',
                'Steuern': {
                    'Brutto': {},
                    'Anteil': {},
                },
                'Rechnungsart': 'BWD',
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
            # TODO: Act on hyphens (= credit notes)
            invoice['Netto'], tax_amount, invoice['Brutto'] = [self.number2string(content[index + 1].replace('-', '')) for index in self.build_indices(content, 'EUR')[-3:]]

            # Add taxes
            # (1) Determine relevant position
            index = self.get_index(content, 'MWSt')

            # (2) Extract tax amount, which is either one or two strings in front of index
            tax_rate = ''.join([content[index - 2], content[index - 1]]) if content[index - 1] == '%' else content[index - 1]

            # (3) Apply extracted values
            invoice['Steuern']['Brutto'][tax_rate.replace('+', '')] = invoice['Brutto']
            invoice['Steuern']['Anteil'][tax_rate.replace('+', '')] = tax_amount

            invoices[invoice_number] = invoice

        self.data = invoices

        return self
