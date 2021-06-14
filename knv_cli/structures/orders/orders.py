from operator import itemgetter

import pendulum

from ..waypoint import Waypoint
from ..invoices.invoice import Invoice
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

    def taxes(self):
        pass


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


    # CONTACTS methods

    def contacts(self, cutoff_date: str = None, blocklist = []) -> list:
        # Set default date
        if cutoff_date is None:
            today = pendulum.today()
            cutoff_date = today.subtract(years=2).to_datetime_string()[:10]

        codes = set()
        contacts  = []

        for order in self._children:
            mail_address = order.mail()

            # Check for blocklisted mail addresses
            if mail_address in blocklist:
                continue

            # Throw out everything before cutoff date (if provided)
            if order.date() < cutoff_date:
                continue

            if mail_address not in codes:
                codes.add(mail_address)
                contacts.append(order.contact())

        # Sort by date & lastname, in descending order
        contacts.sort(key=itemgetter('Letzte Bestellung', 'Nachname'), reverse=True)

        return contacts
