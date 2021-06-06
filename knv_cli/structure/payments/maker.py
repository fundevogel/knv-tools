from ..maker import Maker
from ..shared.invoice import Invoice
from .payments import Payments
from .payment import Payment


class PaymentsMaker(Maker):
    def __init__(self, payments: dict, invoices: dict) -> None:
        # Add data
        self.payments = payments
        self.invoices = invoices


    # CORE methods

    def build(self) -> Payments:
        payments = Payments()

        for data in self.payments.values():
            order = Payment(data)

            if isinstance(data['Rechnungen'], dict):
                # Ensure validity & availability of each invoice
                for invoice in [self.invoices[invoice] for invoice in data['Rechnungen'].keys() if invoice in self.invoices]:
                    order.add(Invoice(invoice))

            payments.add(order)

        return payments
