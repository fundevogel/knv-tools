# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from os.path import splitext

from ..receiver import Receiver

from .paypal import Paypal
from .volksbank import Volksbank


class Payments(Receiver):
    # PROPS

    paypal = None
    volksbank = None

    # Available payment gateways
    gateways = {
        'paypal': Paypal,
        'volksbank': Volksbank,
    }


    # DATA methods

    def load(self, identifier: str, payment_files: list = None):
        if not payment_files:
            return self.gateways[identifier]()

        # Depending on filetype, proceed with ..
        extension = splitext(payment_files[0])[1]

        # .. processing unformatted CSV data
        if extension == '.csv':
            return self.gateways[identifier](payment_files)

        # .. loading formatted JsON data
        if extension == '.json':
            return self.gateways[identifier]().load(self.load_json(payment_files))

        # .. otherwise, raise a formal complaint, fine Sir!
        raise Exception


    def init(self, force: bool = False) -> Payments:
        # Initialize payment handlers
        for identifier in self.gateways.keys():
            setattr(self, identifier, self.load(identifier))

        return self
