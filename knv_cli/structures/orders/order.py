from ..waypoint import Waypoint


class Order(Waypoint):
    def __init__(self, data: dict) -> None:
        # Initialize 'Waypoint' props
        super().__init__()

        self.data = data


    # CORE methods

    def export(self) -> list:
        return self.data


    def contact(self) -> dict:
        return {
            'Anrede': self.form_of_address(),
            'Vorname': self.first_name(),
            'Nachname': self.last_name(),
            'Email': self.mail(),
            'Letzte Bestellung': self.date(),
        }


    # ACCOUNTING methods

    def amount(self) -> str:
        return self.data['Gesamtbetrag']


    def taxes(self) -> dict:
        return self.data['Steuern']


    # HELPER methods

    def identifier(self) -> str:
        return self.data['ID']


    def form_of_address(self) -> str:
        return self.data['Anrede']


    def first_name(self) -> str:
        return self.data['Vorname']


    def last_name(self) -> str:
        return self.data['Nachname']

    def mail(self) -> str:
        return self.data['Email']