from ..components import Molecule
from ..invoices.invoice import Invoice
from .payment import Payment


class Payments(Molecule):
    def __init__(self, payments: dict, orders: dict, invoices: dict) -> None:
        # Initialize 'Molecule' props
        super().__init__()

        # Build composite structure
        # TODO: Move 'matching' logic here
        for data in payments.values():
            order = Payment(data)

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
