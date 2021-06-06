from ..maker import Maker
from ..shared.invoice import Invoice
from .orders import Orders
from .order import Order


class OrdersMaker(Maker):
    def __init__(self, orders: dict, invoices: dict) -> None:
        # Add data
        self.orders = orders
        self.invoices = invoices


    # CORE methods

    def build(self) -> Orders:
        orders = Orders()

        for data in self.orders.values():
            order = Order(data)

            if isinstance(data['Rechnungen'], dict):
                # Ensure validity & availability of each invoice
                for invoice in [self.invoices[invoice] for invoice in data['Rechnungen'].keys() if invoice in self.invoices]:
                    order.add(Invoice(invoice))

            orders.add(order)

        return orders
