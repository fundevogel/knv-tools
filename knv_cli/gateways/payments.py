from os.path import splitext

from ..receiver import Receiver

from .paypal import Paypal
from .volksbank import Volksbank


class Payments(Receiver):
    # PROPS

    paypal = None
    Volksbank = None


    # DATA methods

    def load_paypal(self, payment_files: list) -> None:
        # Depending on filetype, proceed with ..
        extension = splitext(payment_files[0])[1]

        if extension == '.csv':
            payment_data = Paypal(payment_files).payments()

        if extension == '.json':
            payment_data = self.load_json(payment_files)

        self.paypal = payment_data


    def load_volksbank(self, payment_files: list) -> None:
        # Depending on filetype, proceed with ..
        extension = splitext(payment_files[0])[1]

        if extension == '.csv':
            payment_data = Volksbank(payment_files).payments()

        if extension == '.json':
            payment_data = self.load_json(payment_files)

        self.volksbank = payment_data


    def init(self, force: bool = False) -> None:
        pass
