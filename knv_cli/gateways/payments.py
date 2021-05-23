from abc import abstractmethod
from datetime import datetime, timedelta
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
        return sorted(self._blocked_payments, key=itemgetter('Datum'))


    def matched_payments(self):
        # Sort payments by date
        return sorted(self._matched_payments, key=itemgetter('Datum'))


    # MATCHING HELPER methods

    def match_dates(self, base_date, test_date, days=1) -> bool:
        date_objects = [datetime.strptime(date, '%Y-%m-%d') for date in [base_date, test_date]]
        date_range = timedelta(days=days)

        if date_objects[0] <= date_objects[1] <= date_objects[0] + date_range:
            return True

        return False
