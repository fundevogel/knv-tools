from ..components import Atom


class Invoice(Atom):
    def __init__(self, data: dict) -> None:
        self.data = data


    def export(self) -> list:
        return list(self.data.values())
