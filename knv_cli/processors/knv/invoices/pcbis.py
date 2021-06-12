# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from .invoices import InvoiceProcessor


class PcBisInvoiceProcessor(InvoiceProcessor):
    # PROPS

    regex = 'PCBIS_Invoices_TimeFrom*_TimeTo*.zip'


    # CORE methods

    def process(self) -> PcBisInvoiceProcessor:
        '''
        Processes 'RE_{Ymd}_{VKN}_*.pdf' files
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

            taxes = {
                'Brutto': {},
                'Anteil': {},
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
                # Determine tax rates where ..
                # .. 'reduced' equals either 5% or 7%
                # .. 'full' equals either 16% or 19%
                for tax_rate in ['0', '5', '7', '16', '19']:
                    tax_string = 'MwSt. ' + tax_rate + ',00 %'

                    if tax_string in content:
                        taxes['Anteil'][tax_rate + '%'] = self.number2string(content[content.index(tax_string) + 2])

                    # Calculate gross values from net values
                    tax_string = 'Rechnungsbetrag netto ' + tax_string

                    if tax_string in content:
                        # Use only net costs when invoices are paid with coupons
                        if tax_rate + '%' not in taxes['Anteil']:
                            taxes['Brutto'][tax_rate + '%'] = self.number2string(content[content.index(tax_string) + 2])

                            # Proceed to next tax rate
                            continue

                        taxes['Brutto'][tax_rate + '%'] = self.number2string(float(self.number2string(content[content.index(tax_string) + 2])) + float(taxes['Anteil'][tax_rate + '%']))

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
                        # TODO: NEEDS TESTING
                        # print(reduced_net, full_net)
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
                    index = 5

                    if 'MwSt.' in costs[6]:
                        index = 6

                        reduced_net = costs[index - 4].split(':')[-1]
                        full_net = costs[index - 3]

                    reduced_tax = costs[index].split(':')[-1].split()[0]
                    full_tax = costs[index + 1].split()[0]

                else:
                    reduced_tax = costs[5].split()[0]
                    full_tax = costs[2].split()[2]

                    if reduced_tax == 'MwSt.':
                        reduced_tax = costs[5].split(':')[-1]
                        full_tax = costs[6]

                # Extract gross values
                costs_list = costs[2].split(':')[1].split('EUR')
                reduced_net = costs_list[0]
                full_net = costs_list[1]

                if costs[2].count('EUR') == 1:
                    reduced_net = costs[2].split(':')[-1]
                    full_net = costs[3]

                    if 'MwSt.' in costs[3]:
                        full_net = costs[3].split()[0]

                # Add taxes
                reduced_tax, full_tax = self.number2string(reduced_tax), self.number2string(full_tax)
                reduced_net, full_net = self.number2string(reduced_net), self.number2string(full_net)

                taxes['Anteil'][tax_rates[0]] = reduced_tax
                taxes['Anteil'][tax_rates[1]] = full_tax

                taxes['Brutto'][tax_rates[0]] = self.number2string(float(reduced_net) + float(reduced_tax))
                taxes['Brutto'][tax_rates[1]] = self.number2string(float(full_net) + float(full_tax))

            # Apply (only successfully) extracted taxes
            if {k: v for k, v in taxes.items() if v}: invoice['Steuern'] = taxes

            invoices[invoice_number] = invoice

        self.data = invoices

        return self
