from operator import itemgetter

import pendulum

from ..components import Molecule
from ..shared.invoice import Invoice
from .order import Order


class Orders(Molecule):
    def __init__(self, orders: dict, invoices: dict) -> None:
        # Initialize 'Molecule' props
        super().__init__()

        # Build composite structure
        for data in orders.values():
            order = Order(data)

            if isinstance(data['Rechnungen'], dict):
                # Ensure validity & availability of each invoice
                for invoice in [invoices[invoice] for invoice in data['Rechnungen'].keys() if invoice in invoices]:
                    order.add(Invoice(invoice))

            self.add(order)


    # CORE methods

    def export(self) -> list:
        data = []

        for child in self._children:
            data.append(child.export())

        return data


    # ACCOUNTING methods

    def get_revenues(self, year: str, quarter: str = None) -> dict:
        data = {}

        # Select orders matching given time period
        for order in self.filter(year, quarter)._children:
            if order.month() not in data:
                data[order.month()] = []

            data[order.month()].append(order.get_revenues())

        # Assign data to respective month
        data = {int(month): sum(revenues) for month, revenues in data.items()}

        # Fill missing months with zeroes
        # (1) .. generally including all months
        month_range = range(1, 13)

        # (2) .. or only those for given quarter
        if quarter is not None:
            month_range = range(self.qm(quarter), self.qm(quarter, True) + 1)

        # (3) .. execute!
        for i in month_range:
            if i not in data:
                data[i] = 0

        # Sort results
        return {k: data[k] for k in sorted(data)}


    def get_taxes(self):
        pass


    # ACCOUNTING HELPER methods

    def qm(self, quarter: str, last: bool = False) -> int:
        # Determine if first or last q(uarter) m(onth)
        start = 1 if not last else 3

        return start + 3 * (int(quarter) - 1)


    # RANKING methods

    def get_ranking(self, limit: int = 1) -> list:
        data = {}

        # Sum up number of sales
        for item in [item[0] for item in [order.data['Bestellung'] for order in self._children]]:
            if item['Titel'] not in data:
                data[item['Titel']] = 0

            data[item['Titel']] = data[item['Titel']] + item['Anzahl']

        # Sort by quantity, only including items if above given limit
        return sorted([(isbn, quantity) for isbn, quantity in data.items() if quantity >= int(limit)], key=itemgetter(1), reverse=True)


    # CONTACTS methods

    # def get_contacts(self, cutoff_date: str = None, blocklist = []) -> list:
    #     # Check if order entries are present
    #     if not self.data:
    #         raise Exception


    #     # Set default date
    #     if cutoff_date is None:
    #         today = pendulum.today()
    #         cutoff_date = today.subtract(years=2).to_datetime_string()[:10]

    #     codes = set()
    #     contacts  = []

    #     for order in self.data.values():
    #         mail_address = order['Email']

    #         # Check for blocklisted mail addresses
    #         if mail_address in blocklist:
    #             continue

    #         # Throw out everything before cutoff date (if provided)
    #         if order['Datum'] < cutoff_date:
    #             continue

    #         # Prepare dictionary
    #         contact = {}

    #         contact['Anrede'] = order['Anrede']
    #         contact['Vorname'] = order['Vorname']
    #         contact['Nachname'] = order['Nachname']
    #         contact['Email'] = order['Email']
    #         contact['Letzte Bestellung'] = order['Datum']

    #         if mail_address not in codes:
    #             codes.add(mail_address)
    #             contacts.append(contact)

    #     # Sort by date & lastname, in descending order
    #     contacts.sort(key=itemgetter('Letzte Bestellung', 'Nachname'), reverse=True)

    #     return contacts
