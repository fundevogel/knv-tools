from operator import itemgetter

from ..command import Command


class Infos(Command):
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
                info['Rechnungen'] = {}

                infos[code] = info

            if invoice_number not in infos[code]['Rechnungen'].keys():
                infos[code]['Rechnungen'][invoice_number] = [item_number]

            else:
                infos[code]['Rechnungen'][invoice_number].append(item_number)

        return infos


    def infos(self):
        # Sort infos by date & order number, output as list
        return sorted(list(self.data.values()), key=itemgetter('Datum', 'ID'))
