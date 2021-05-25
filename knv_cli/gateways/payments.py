from abc import abstractmethod
from datetime import datetime, timedelta
from operator import itemgetter
from os.path import splitext

from ..command import Command
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


class Gateway(Command):
    # PROPS

    _blocked_payments = []
    _matched_payments = []

    # Class-specific
    VKN = None
    blocklist = []


    # DATA methods

    def process_data(self, data: list) -> list:
        return self.process_payments(data)


    @abstractmethod
    def process_payments(self, data: list) -> None:
        pass


    @abstractmethod
    def match_payments(self, data: list) -> None:
        pass


    def payments(self):
        # Sort payments by date
        return sorted(self.data, key=itemgetter('Datum', 'Name'))


    def blocked_payments(self):
        return sorted(self._blocked_payments, key=itemgetter('Datum', 'Name'))


    def matched_payments(self):
        # Sort payments by date
        return sorted(self._matched_payments, key=itemgetter('Datum', 'Name'))


    # MATCHING HELPER methods

    def match_dates(self, base_date, test_date, days=1) -> bool:
        date_objects = [datetime.strptime(date, '%Y-%m-%d') for date in [base_date, test_date]]
        date_range = timedelta(days=days)

        if date_objects[0] <= date_objects[1] <= date_objects[0] + date_range:
            return True

        return False
