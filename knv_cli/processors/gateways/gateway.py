# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import abstractmethod
from datetime import datetime, timedelta

from ..processor import Processor


class Gateway(Processor):
    # PROPS

    _matched_payments = []
    _blocked_payments = []


    # CORE methods

    def process(self) -> Gateway:
        self.process_payments()

        return self


    @abstractmethod
    def process_payments(self) -> Gateway:
        pass


    # # MATCHING HELPER methods

    # def match_dates(self, test_date, start_date, days=1, before: bool = False) -> bool:
    #     end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=days)).strftime('%Y-%m-%d')

    #     return start_date >= test_date >= end_date if before else start_date <= test_date <= end_date


    # # OUTPUT methods

    # def blocked_payments(self) -> list:
    #     return self._blocked_payments


    # def matched_payments(self, csv_compatible: bool = False) -> list:
    #     return self._matched_payments
