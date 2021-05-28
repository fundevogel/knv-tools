# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import abstractmethod
from datetime import datetime, timedelta
from operator import itemgetter

from ..command import Command
from ..knv.invoices import Invoices


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
    def match_payments(self, data: list, invoice_handler: Invoices = None) -> None:
        pass


    # MATCHING HELPER methods

    def match_dates(self, start_date, test_date, days=1) -> bool:
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=days)).strftime('%Y-%m-%d')

        return start_date <= test_date <= end_date


    # OUTPUT methods

    def payments(self):
        # Sort payments by date
        return sorted(self.data, key=itemgetter('Datum', 'ID', 'Name'))


    def blocked_payments(self):
        return sorted(self._blocked_payments, key=itemgetter('Datum', 'ID', 'Name'))


    def matched_payments(self):
        # Sort payments by date
        try:
            # TODO: Workaround for Volksbank
            return sorted(self._matched_payments, key=itemgetter('Datum', 'ID', 'Name'))
        except TypeError:
            return sorted(self._matched_payments, key=itemgetter('Datum', 'Name'))
