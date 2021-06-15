from ..endpoint import Endpoint


class Invoice(Endpoint):
    # CORE methods

    def identifier(self) -> str:
        return self.data['Vorgang']


    def file(self) -> str:
        return self.data['Datei']


    def is_revenue(self) -> str:
        return self.data['Kontierung'] == 'H'


    def is_expense(self) -> str:
        return self.data['Kontierung'] == 'S'


    def assign(self, identifier: str) -> None:
        if identifier not in ['offen', 'abgeschlossen']:
            raise Exception

        self.data['Status'] = identifier


    def assigned(self) -> bool:
        return self.data['Status'] == 'abgeschlossen'


    def taxes(self) -> dict:
        return self.data['Steuern']['Brutto'] if isinstance(self.data['Steuern'], dict) else {}


    def has_cashback(self) -> bool:
        return self.data['Rechnungsart'] == 'Sammelrechnung'
