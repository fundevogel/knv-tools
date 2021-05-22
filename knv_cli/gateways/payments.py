from abc import abstractmethod
from operator import itemgetter

from ..base import BaseClass


class Payments(BaseClass):
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
    def match_payments(self, orders: list, infos: list) -> None:
        pass


    def payments(self):
        # Sort payments by date
        return sorted(self.data, key=itemgetter('Datum'))


    def blocked_payments(self):
        return sorted(self.blocked_payments, key=itemgetter('Datum'))
