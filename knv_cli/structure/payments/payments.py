from abc import abstractmethod
from datetime import datetime, timedelta
from typing import List

from ..components import Molecule
from .payment import Payment


class Payments(Molecule):
    # ACCOUNTING methods

    def taxes(self) -> None:
        pass


    # HELPER methods

    def match_dates(self, test_date, start_date, days=1, before: bool = False) -> bool:
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=days)).strftime('%Y-%m-%d')

        return start_date >= test_date >= end_date if before else start_date <= test_date <= end_date
