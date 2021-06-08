from ..components import Atom


class Invoice(Atom):
    def __init__(self, data: dict) -> None:
        self.data = data


    # ACCOUNTING methods

    def revenues(self) -> float:
        return float(self.data['Gesamtbetrag'])


    def taxes(self) -> float:
        return self.data['Steuern']


    # HELPER methods

    def identifier(self) -> str:
        return self.data['Vorgang']


    def file(self) -> str:
        return self.data['Datei']
