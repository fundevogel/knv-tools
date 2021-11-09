# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from re import compile, VERBOSE

from ..invoices import InvoiceProcessor


class ShopkonfiguratorInvoiceProcessor(InvoiceProcessor):
    # PROPS

    regex = 'SK_*_Invoices_TimeFrom*_TimeTo*.zip'


    # CORE methods

    def process(self) -> ShopkonfiguratorInvoiceProcessor:
        '''
        Processes '{VKN}-{Ymd}-*.pdf' files
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
                'Kontierung': 'H',
                'Status': 'offen',
                'Zahlung': 'nicht zugeordnet',
                'Versandkosten': self.number2string(0),
                'Gesamtbetrag': 'keine Angabe',
                'Steuern': 'keine Angabe',
                'Gutscheine': 'keine Angabe',
                'Rechnungsart': 'Kundenrechnung',
            }

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

            # In this case, fetch last occurence of 'EUR' (= terminal point)
            if reverse_order: terminal_point = self.get_index(content, 'EUR', True)

            costs = content[starting_point:terminal_point + 1]

            # (2) .. taxes
            # Compile regular expression
            regex = compile(
                r"""
                ^Nettobetrag
                (?P<min_rate>\d).*                              # reduced tax rate, either 5% or 7%
                (?P<max_rate>\d{2}).*                           # full tax rate, either 16% or 19%
                (?P<min_net>\d+,\d{2})EUR                       # reduced tax net
                (?P<max_net>\d+,\d{2})EUR                       # full tax net
                \d+,\d{2}EUR.*gesamt:                           # net subtotal
                (?P<min_share>\d+,\d{2})EUR(?:Zwischensumme:)?  # reduced tax amount
                (?P<max_share>\d+,\d{2})EUR                     # full tax amount
                """, VERBOSE
            )

            # Match named capturing groups
            match = regex.search(''.join(costs).replace(' ', ''))

            # Determine tax rates
            reduced_rate = match.group('min_rate') + '%'
            full_rate = match.group('max_rate') + '%'

            # Add taxes
            # (1) Reduced tax
            reduced_tax = self.number2string(match.group('min_share'))
            reduced_net = self.number2string(match.group('min_net'))

            # (2) Full tax
            full_tax = self.number2string(match.group('max_share'))
            full_net = self.number2string(match.group('max_net'))

            # (3) Bring everything together
            taxes = {
                'Brutto': {
                    reduced_rate: self.number2string(float(reduced_tax) + float(reduced_net)),
                    full_rate: self.number2string(float(full_tax) + float(full_net)),
                },
                'Anteil': {
                    reduced_rate: reduced_tax,
                    full_rate: full_tax,
                },
            }

            # Apply (only successfully) extracted taxes
            if {k: v for k, v in taxes.items() if v}: invoice['Steuern'] = taxes

            invoices[invoice_number] = invoice

        self.data = invoices

        return self
