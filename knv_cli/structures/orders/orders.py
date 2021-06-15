from operator import itemgetter

from ..invoices.invoice import Invoice
from ..shared import get_contacts
from ..waypoint import Waypoint
from .order import Order


class Orders(Waypoint):
    def __init__(self, orders: dict, invoices: dict) -> None:
        # Initialize 'Waypoint' props
        super().__init__()

        # Build composite structure
        for data in orders.values():
            order = Order(data)

            if isinstance(data['Rechnungen'], dict):
                # Ensure validity & availability of each invoice
                for invoice in [invoices[invoice] for invoice in data['Rechnungen'].keys() if invoice in invoices]:
                    order.add(self.invoice_types[invoice['Rechnungsart']](invoice))

            self.add(order)


    # ACCOUNTING methods

    def profit_report(self, year: str, quarter: str = None) -> dict:
        data = {}

        # Select orders matching given time period
        for item in self.filter(year, quarter):
            if item.month() not in data:
                data[item.month()] = []

            data[item.month()].append(float(item.amount()))

        # Assign data to respective month
        data = {int(month): sum(amount) for month, amount in data.items()}

        # Determine appropriate month range
        month_range = self.month_range(quarter)

        # Fill missing months with zeroes
        for i in month_range:
            if i not in data:
                data[i] = float(0)

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
