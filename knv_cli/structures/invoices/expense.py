from .invoice import Invoice


class Expense(Invoice):
    # CORE methods

    def amount(self) -> str:
        return self.data['Brutto']
