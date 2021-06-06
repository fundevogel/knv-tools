from ..components import Molecule


class Order(Molecule):
    def __init__(self, data: dict) -> None:
        self.data = data

        # Initialize 'Molecule' props
        super().__init__()


    # CORE methods

    def export(self) -> list:
        return list(self.data.values())


    def get_revenue(self) -> float:
        return float(self.data['Gesamtbetrag'])


    def get_taxes(self) -> dict:
        pass


    def get_contact(self) -> dict:
        return {
            'Anrede': self.form_of_address(),
            'Vorname': self.first_name(),
            'Nachname': self.last_name(),
            'Email': self.mail(),
            'Letzte Bestellung': self.date(),
        }


    # HELPER methods

    def first_name(self) -> str:
        return self.data['Vorname']


    def last_name(self) -> str:
        return self.data['Nachname']

    def mail(self) -> str:
        return self.data['Email']


    def form_of_address(self) -> str:
        return self.data['Anrede']


    def taxes(self) -> dict:
        return self.data['Steuern']
