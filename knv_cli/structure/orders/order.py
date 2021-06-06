from ..components import Molecule


class Order(Molecule):
    def __init__(self, data: dict) -> None:
        self.data = data

        # Initialize 'Molecule' props
        super().__init__()


    # CORE methods

    def export(self) -> list:
        return list(self.data.values())


    def get_revenues(self) -> float:
        return float(self.data['Gesamtbetrag'])


    # HELPER methods

    def date(self) -> str:
        return self.data['Datum']


    def year(self) -> str:
        return self.data['Datum'].split('-')[0]


    def month(self) -> str:
        return self.data['Datum'].split('-')[1]


    def day(self) -> str:
        return self.data['Datum'].split('-')[-1]
