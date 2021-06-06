# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from ..processor import Processor


class OrderProcessor(Processor):
    # PROPS

    regex = 'Orders_*.csv'


    # CORE methods

    def process(self) -> OrderProcessor:
        '''
        Processes 'Orders_*.csv' files
        '''

        orders = {}

        for item in self.data:
            # Create reliable article number ..
            isbn = item['knvnumber']

            # .. since ISBNs are not always ISBNs
            if str(item['isbn']) != 'nan':
                isbn = item['isbn']

            # .. and - more often than not - formatted as floats with a trailing zero
            isbn = str(isbn).replace('.0', '')

            # Assign identifier
            code = item['ormorderid']

            if code not in orders:
                order = {}

                order['ID'] = code
                order['Datum'] = item['timeplaced'][:10]
                order['Anrede'] = item['rechnungaddresstitle']
                order['Vorname'] = item['rechnungaddressfirstname']
                order['Nachname'] = item['rechnungaddresslastname']
                order['Straße'] = self.convert_nan(item['rechnungaddressstreet'])
                order['Hausnummer'] = self.convert_nan(item['rechnungaddresshousenumber'])
                order['PLZ'] = self.convert_nan(item['rechnungaddresszipcode']).replace('.0', '')
                order['Ort'] = self.convert_nan(item['rechnungaddresscity'])
                order['Land'] = self.convert_nan(item['rechnungaddresscountry'])
                order['Telefon'] = str(item['rechnungaddressphonenumber'])
                order['Email'] = item['rechnungaddressemail']
                order['Bestellung'] = []
                order['Rechnungen'] = 'nicht zugeordnet'
                order['Gutscheine'] = 'keine Angabe'
                order['Bestellsumme'] = self.convert_number(item['totalproductcost'])
                order['Versand'] = self.convert_number(item['totalshipping'])
                order['Gesamtbetrag'] = self.convert_number(item['totalordercost'])
                order['Währung'] = item['currency']
                order['Steuern'] = 'keine Angabe'
                order['Abwicklung'] = {
                    'Zahlungsart': 'keine Angabe',
                    'Transaktionscode': 'keine Angabe'
                }

                orders[code] = order

            # Add information about ..
            # (1) .. each purchased article
            item_number = str(item['orderitemid'])

            orders[code]['Bestellung'].append({
                'Nummer': item_number,
                'ISBN': isbn,
                'Titel': item['producttitle'],
                'Anzahl': int(item['quantity']),
                'Einzelpreis': self.convert_number(item['orderitemunitprice']),
                'Steuersatz': self.convert_tax_rate(item['vatpercent']),
                'Steueranteil': self.convert_number(item['vatprice']),
            })

            # (2) .. method of payment
            if str(item['paymenttype']) != 'nan':
                orders[code]['Abwicklung']['Zahlungsart'] = item['paymenttype']

            # (3) .. transaction number (Paypal™ only)
            if str(item['transactionid']) != 'nan':
                orders[code]['Abwicklung']['Transaktionscode'] = str(item['transactionid'])

        self.data = orders

        return self


    # HELPER methods

    def convert_tax_rate(self, string: str) -> str:
        return str(string).replace(',00', '') + '%'
