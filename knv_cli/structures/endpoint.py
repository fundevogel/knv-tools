from .framework import Framework


class Endpoint(Framework):
    def __init__(self, data: dict) -> None:
        self.data = data


    # CORE methods

    def export(self) -> dict:
        return self.data
