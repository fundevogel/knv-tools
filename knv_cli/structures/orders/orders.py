from operator import itemgetter

from ..invoices.invoice import Invoice
from ..shared import get_contacts
from ..waypoint import Waypoint
from .order import Order


class Orders(Waypoint):
    # CORE methods

    def load(self, data: tuple) -> None:
        orders, invoices = data

        for item in orders.values():
            order = Order(item)

            if isinstance(item['Rechnungen'], dict):
                # Ensure validity & availability of each invoice
                for invoice in [invoices[invoice] for invoice in item['Rechnungen'].keys() if invoice in invoices]:
                    order.add(self.invoice_types[invoice['Rechnungsart']](invoice))

            self.add(order)


    # ACCOUNTING methods

    def profit_report(self) -> dict:
        data = {}

        # Select orders matching given time period
        for child in self._children:
            if child.month() not in data:
                data[child.month()] = []

            data[child.month()].append(float(child.amount()))

        # Assign data to respective month
        data = {int(month): sum(amount) for month, amount in data.items()}

        # Sort results
        return {k: data[k] for k in sorted(data)}


    # CONTACTS methods

    def contacts(self, cutoff_date: str = None, blocklist = []) -> list:
        return get_contacts(self._children, cutoff_date, blocklist)


    # RANKING methods

    def ranking(self, limit: int = 1) -> list:
        data = {}

        # Sum up number of sales
        for item in [item[0] for item in [order.data['Bestellung'] for order in self._children]]:
            if item['Titel'] not in data:
                data[item['Titel']] = 0

            data[item['Titel']] = data[item['Titel']] + item['Anzahl']

        # Sort by quantity, only including items if above given limit
        return sorted([(isbn, quantity) for isbn, quantity in data.items() if quantity >= int(limit)], key=itemgetter(1), reverse=True)
