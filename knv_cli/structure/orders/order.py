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


    def get_taxes(self) -> dict:
        pass


    # HELPER methods

    def taxes(self) -> dict:
        return self.data['Steuern']
