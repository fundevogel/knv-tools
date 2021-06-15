from ..waypoint import Waypoint


class Order(Waypoint):
    def __init__(self, data: dict) -> None:
        # Initialize 'Waypoint' props
        super().__init__()

        self.data = data


    # CORE methods

    def export(self) -> list:
        return self.data


    def identifier(self) -> str:
        return self.data['ID']


    def contact(self) -> dict:
        return {
            'Letzte Bestellung': self.data['Datum'],
            'Anrede': self.data['Anrede'],
            'Vorname': self.data['Vorname'],
            'Nachname': self.data['Nachname'],
            'Email': self.data['Email'],
            'Straße': self.data['Straße'],
            'Hausnummer': self.data['Hausnummer'],
            'PLZ': self.data['PLZ'],
            'Ort': self.data['Ort'],
            'Land': self.data['Land'],
            'Telefon': self.data['Telefon'],
        }


    # ACCOUNTING methods

    def amount(self) -> str:
        return self.data['Gesamtbetrag']


    def taxes(self) -> dict:
        return self.data['Steuern']
