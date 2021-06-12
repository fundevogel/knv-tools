from ..invoices import InvoiceProcessor


class FitBisInvoiceProcessor(InvoiceProcessor):
    # HELPER methods

    def number2string(self, string) -> str:
        # As usual, apart from ..
        # (1) .. stripping 'KNV' / 'Zeitfracht'
        # (2) .. stripping 'Zahlbar'
        # (2) .. stripping hyphens (edge case)
        return super().number2string(str(string).replace('KNV', '').replace('Zeitfracht', '').replace('Zahlbar', '').replace('-', ''))
