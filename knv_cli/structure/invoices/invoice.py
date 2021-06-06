from ..components import Atom


class Invoice(Atom):
    def __init__(self, data: dict) -> None:
        self.data = data


    # CORE methods

    def export(self) -> list:
        return list(self.data.values())


    # ACCOUNTING methods

    def get_revenues(self) -> float:
        return float(self.data['Gesamtbetrag'])
