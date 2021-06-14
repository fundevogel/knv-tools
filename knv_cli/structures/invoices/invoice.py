from ..endpoint import Endpoint


class Invoice(Endpoint):
    # CORE methods

    def identifier(self) -> str:
        return self.data['Vorgang']


    def file(self) -> str:
        return self.data['Datei']


    def is_revenue(self) -> str:
        return self.data['Art'] == 'H'


    def is_expense(self) -> str:
        return self.data['Art'] == 'S'


    def taxes(self) -> dict:
        return self.data['Steuern']['Brutto'] if isinstance(self.data['Steuern'], dict) else {}
