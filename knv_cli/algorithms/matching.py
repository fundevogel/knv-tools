# ~*~ coding=utf-8 ~*~


from datetime import datetime, timedelta
from operator import itemgetter
from os.path import join

from ..processors.helpers import convert_number


# MATCHING functions

class Matching:
    def __init__(self, payments, orders, infos) -> None:
        # Match data
        self.data = self.match_payments(payments, orders, infos)


    # ESSENTIAL functions

    def match_payments(self, payments: list, orders: list, infos: list) -> list:
        results = []

        for payment in payments:
            # Assign payment to invoice number(s)
            # (1) Find matching order for current payment
            # (2) Find matching invoice number for this order
            matching_order = self.match_orders(payment, orders)

            if not matching_order:
                results.append(payment)
                continue

            matching_infos = self.match_infos(matching_order, infos)

            # Skip if no matching invoice numbers
            if not matching_infos:
                results.append(payment)
                continue

            # Store data
            # (1) Apply matching order number
            # (2) Add invoice number(s) to payment data
            payment['ID'] = matching_order['ID']
            payment['Vorgang'] = matching_infos
            payment['Versand'] = matching_order['Versand']
            # (3) Add total order cost & purchased items
            payment['Summe'] = matching_order['Bestellung']['Summe']
            del matching_order['Bestellung']['Summe']
            payment['Bestellung'] = matching_order['Bestellung']

            # (4) Save matched payment
            results.append(payment)

        return results


    def match_orders(self, payment, orders) -> dict:
        candidates = []

        for order in orders:
            # Skip payments other than PayPal™
            if order['Abwicklung']['Zahlungsart'].lower() != 'paypal':
                continue

            # Determine matching transaction code ..
            if order['Abwicklung']['Transaktionscode'] != 'keine Angabe':
                if order['Abwicklung']['Transaktionscode'] == payment['Transaktion']:
                    # .. in which case there's a one-to-one match
                    return order

                # .. otherwise, why bother
                # TODO: In the future, this might be the way to go,
                # simply because PayPal always includes a transaction code ..
                #
                # .. BUT the algorithm could be used for other payments
                #
                # else:
                #     continue

            costs_match = payment['Brutto'] == order['Betrag']
            dates_match = self.match_dates(payment['Datum'], order['Datum'])

            if costs_match and dates_match:
                # Let them fight ..
                hits = 0

                # Determine chance of match for given payment & order
                # (1) Split by whitespace
                payment_name = payment['Name'].split(' ')
                order_name = order['Name'].split(' ')

                # (2) Take first list item as first name, last list item as last name
                payment_first, payment_last = payment_name[0], payment_name[-1]
                order_first, order_last = order_name[0], order_name[-1]

                # Add one point for matching first name, since that's more likely, but ..
                if payment_first.lower() == order_first.lower():
                    hits += 1

                # .. may be overridden by matching last name
                if payment_last.lower() == order_last.lower():
                    hits += 2

                candidates.append((hits, order))

        matches = sorted(candidates, key=itemgetter(0), reverse=True)

        if matches:
            return matches[0][1]

        return {}


    def match_infos(self, order, infos) -> list:
        info = []

        for info in infos:
            if info['ID'] == order['ID']:
                return info['Rechnungen']

        return []


    # HELPER functions

    def match_dates(self, base_date, test_date, days=1) -> bool:
        date_objects = [datetime.strptime(date, '%Y-%m-%d') for date in [base_date, test_date]]
        date_range = timedelta(days=days)

        if date_objects[0] <= date_objects[1] <= date_objects[0] + date_range:
            return True

        return False


    # OUTPUT functions

    def to_json(self) -> list:
        return self.data


    def to_csv(self) -> list:
        csv_data = []

        for item in self.data:
            del item['Transaktion']

            # Convert invoice numbers to string
            if item['Vorgang'] != 'nicht zugeordnet':
                item['Vorgang'] = ';'.join(item['Vorgang'])

            # Extract tax rates & their respective amount
            # TODO: Maybe this should go into __init__ function as default
            if 'Bestellung' in item:
                # Determine taxes from purchase information
                taxes = self.get_taxes(item['Bestellung'])
                del item['Bestellung']

                # Add taxe rates
                for tax_rate, tax_amount in taxes.items():
                    item[self.get_tax_label(tax_rate) + ' MwSt'] = convert_number(tax_amount)

                # Add share of payment fees for each tax rate
                # (1) Calculate total amount of taxes
                total_taxes = self.get_total_taxes(taxes)

                # (2) Calculate share for each tax rate
                for tax_rate, tax_amount in taxes.items():
                    ratio = total_taxes / tax_amount
                    share = float(item['Gebühr'][1:]) / ratio

                    item['Gebührenanteil ' + self.get_tax_label(tax_rate) + ' MwSt'] = convert_number(share)

            csv_data.append(item)

        return csv_data


    # OUTPUT HELPER functions

    def get_taxes(self, purchase):
        taxes = {}

        for item in purchase.values():
            if item['Steuersatz'] not in taxes:
                taxes[item['Steuersatz']] = float(item['Steueranteil'])

            else:
                taxes[item['Steuersatz']] += float(item['Steueranteil'])

        return taxes


    def get_total_taxes(self, taxes) -> str:
        return sum([tax_amount for tax_amount in taxes.values()])


    def get_tax_label(self, tax_rate) -> str:
        return str(tax_rate).split('.')[0] + '%'
