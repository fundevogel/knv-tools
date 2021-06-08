# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import abstractmethod
from datetime import datetime, timedelta

from ..processor import Processor


class Gateway(Processor):
    # PROPS

    _blocked_payments = []


    # CORE methods

    def process(self) -> Gateway:
        self.process_payments()

        return self


    @abstractmethod
    def process_payments(self) -> Gateway:
        pass
