from ..endpoint import Endpoint


class Invoice(Endpoint):
    # CORE methods

    # def export(self) -> None:
    #     pass


    # ACCOUNTING methods

    # def revenues(self) -> float:
    #     return float(self.data['Gesamtbetrag'])


    # def taxes(self) -> float:
    #     return self.data['Steuern']


    # HELPER methods

    def identifier(self) -> str:
        return self.data['Vorgang']


    def file(self) -> str:
        return self.data['Datei']


    def is_revenue(self) -> str:
        return self.data['Art'] == 'H'


    def is_expense(self) -> str:
        return self.data['Art'] == 'S'
