from abc import abstractmethod
from typing import List

from ..waypoint import Waypoint
from .payment import Payment


class Payments(Waypoint):
    def __init__(self, payments: dict, orders: dict, invoices: dict) -> None:
        # Initialize 'Waypoint' props
        super().__init__()

        # Process ingredients
        self.process(payments, orders, invoices)


    # CORE methods

    @abstractmethod
    def process(self, payments: dict, orders: dict, invoices: dict) -> None:
        pass
