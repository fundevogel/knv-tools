from abc import abstractmethod

from .framework import Framework


class Endpoint(Framework):
    # PROPS

    data = {}


    def __init__(self, data: dict) -> None:
        self.data = data


    # CORE methods

    def export(self) -> dict:
        return self.data


    # ACCOUNTING methods

    # @abstractmethod
    # def revenues(self) -> None:
    #     pass
