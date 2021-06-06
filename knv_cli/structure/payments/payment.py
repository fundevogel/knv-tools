from ..components import Molecule


class Payment(Molecule):
    def __init__(self, data: dict) -> None:
        self.data = data

        # Initialize 'Molecule' props
        super().__init__()


    # CORE methods

    def export(self) -> list:
        return list(self.data.values())


    # ACCOUNTING methods

    def get_revenues(self) -> float:
        if 'Brutto' in self.data:
            return float(self.data['Brutto'])

        if 'Betrag' in self.data:
            return float(self.data['Betrag'])

        return float(0)
