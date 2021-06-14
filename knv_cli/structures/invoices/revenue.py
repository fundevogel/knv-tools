from .invoice import Invoice


class Revenue(Invoice):
    # CORE methods

    def amount(self) -> str:
        return self.data['Gesamtbetrag']
