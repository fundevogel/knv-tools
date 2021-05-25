# This module contains a class for processing & working with
# invoices (PDF), as exported from FitBis & Shopkonfigurator


from datetime import datetime
from os.path import basename


class Invoices:
    # PROPS

    regex = '*_Invoices_TimeFrom*_TimeTo*.zip'


    def __init__(self, invoice_files: list = None):
        if invoice_files:
            self.invoices = {self.invoice2number(invoice): invoice for invoice in invoice_files}


    # DATA methods

    def load(self, invoice_files: list) -> None:
        self.invoices = {self.invoice2number(invoice): invoice for invoice in invoice_files}


    def has(self, invoice: str) -> bool:
        return self.invoice2number(invoice) in self.invoices.keys()


    def get(self, invoice_number: str) -> str:
        return self.invoices[invoice_number]


    def add(self, invoice: str) -> None:
        self.invoices[self.invoice2number(invoice)] = invoice


    def remove(self, invoice_number: str) -> None:
        del self.invoices[invoice_number]


    # HELPER methods

    @staticmethod
    def invoice2date(string: str) -> str:
        # Distinguish between delimiters ..
        # (1) .. hyphen ('Shopkonfigurator')
        delimiter = '-'

        # (2) .. underscore ('Barsortiment')
        if delimiter not in string:
            delimiter = '_'

        date_string = basename(string).split(delimiter)[1].replace('.pdf', '')

        return datetime.strptime(date_string, '%Y%m%d').strftime('%Y-%m-%d')


    @staticmethod
    def invoice2number(string: str) -> str:
        # Strip path information
        string = basename(string)

        # Distinguish between delimiters ..
        # (1) .. hyphen ('Shopkonfigurator')
        delimiter = '-'

        # (2) .. underscore ('Barsortiment')
        if delimiter not in string:
            delimiter = '_'

        # (3) .. as well as invoice numbers
        if delimiter not in string:
            return string

        return string.split(delimiter)[-1].replace('.pdf', '')
