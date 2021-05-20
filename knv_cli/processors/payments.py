from abc import abstractmethod
from operator import itemgetter

from .base import BaseClass

class Payments(BaseClass):
    # Props
    _blocked_payments = []


    def process_data(self, data: list) -> list:
        return self.process_payments(data)


    @abstractmethod
    def process_payments(self, data: list) -> tuple:
        pass


    def payments(self):
        # Sort payments by date
        return sorted(self.data, key=itemgetter('Datum'))


    def blocked_payments(self):
        return sorted(self.blocked_payments, key=itemgetter('Datum'))
