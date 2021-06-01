from operator import itemgetter

from ..command import Command


class Infos(Command):
    # PROPS

    regex = 'OrdersInfo_*.csv'


    # DATA methods

    def process_data(self, info_data: list) -> dict:
        '''
        Processes 'OrdersInfo_*.csv' files
        '''

        infos = {}

        for item in info_data:
            # Skip availability information
            if str(item['Invoice Number']) == 'nan':
                continue

            # Standardize invoice number & costs
            invoice_number = str(item['Invoice Number']).replace('.0', '')
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
                'Einzelpreis': self.convert_number(item['Total Cost']),
            }

        return infos
