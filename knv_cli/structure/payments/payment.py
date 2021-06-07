from ..components import Molecule


class Payment(Molecule):
    def __init__(self, data: dict) -> None:
        # Initialize 'Molecule' props
        super().__init__()

        self.data = data


    # CORE methods

    def export(self) -> list:
        return self.data


    # ACCOUNTING methods

    def revenues(self) -> float:
        if 'Brutto' in self.data:
            return float(self.data['Brutto'])

        if 'Betrag' in self.data:
            return float(self.data['Betrag'])

        return float(0)


    def taxes(self) -> None:
        pass


    # HELPER methods

    def identifier(self) -> str:
        return self.data['Transaktion'] if 'Transaktion' in self.data else ''
