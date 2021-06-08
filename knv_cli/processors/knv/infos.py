# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from ..processor import Processor


class InfoProcessor(Processor):
    # PROPS

    regex = 'OrdersInfo_*.csv'


    # CORE methods

    def process(self) -> InfoProcessor:
        '''
        Processes 'OrdersInfo_*.csv' files
        '''

        infos = {}

        for item in self.data:
            # Skip availability information
            if str(item['Invoice Number']) == 'nan':
                continue

            # Standardize invoice number & costs
            invoice_number = self.normalize(item['Invoice Number'])
            item_number = str(item['Order Item Id'])

            # Assign identifier
            code = item['OrmNumber']

            if code not in infos:
                info = {}

                info['ID'] = code
                info['Datum'] = item['Creation Date'][:10]
                info['Bestellung'] = {}

                infos[code] = info

            if invoice_number not in infos[code]['Bestellung']:
                infos[code]['Bestellung'][invoice_number] = {}

            infos[code]['Bestellung'][invoice_number][item_number] = {
                'Nummer': item_number,
                'Anzahl': int(item['Quantity']),
                'Einzelpreis': self.number2string(item['Total Cost']),
            }

        self.data = infos

        return self
