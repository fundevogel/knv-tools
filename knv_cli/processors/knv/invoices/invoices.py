# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from io import BytesIO
from os.path import basename, splitext
from re import match
from zipfile import ZipFile

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError

from ...processor import Processor


class InvoiceProcessor(Processor):
    # I/O methods

    def load_files(self, files: list) -> InvoiceProcessor:
        invoices = {}

        for file in files:
            # Check filetype, depending on this either ..
            extension = splitext(file)[1].lower()

            # (1) .. extract PDF invoices to memory
            if extension == '.zip':
                # See https://stackoverflow.com/a/10909016
                archive = ZipFile(file)

                for file in archive.namelist():
                    invoices[file] = []

                    byte_stream = BytesIO(BytesIO(archive.read(file)).read())
                    byte_stream.seek(0)

                    try:
                        pdf = PdfFileReader(byte_stream)

                        for page in pdf.pages:
                            invoices[file] += [text.strip() for text in page.extractText().splitlines() if text]

                        byte_stream.close()

                    except PdfReadError:
                        pass

            # (2) .. parse PDF invoices directly
            if extension == '.pdf':
                invoices[file] = []

                # Fetch content from invoice file
                with open(file, 'rb') as pdf_file:
                    pdf = PdfFileReader(pdf_file)

                    for page in pdf.pages:
                        invoices[file] += [text.strip() for text in page.extractText().splitlines() if text]

        self.data = invoices

        return self


    # CORE methods

    @abstractmethod
    def process(self) -> InvoiceProcessor:
        pass


    # HELPER methods

    def split_string(self, string: str) -> str:
        # Strip path information
        string = splitext(basename(string))[0]

        # Distinguish between delimiters ..
        # (1) .. hyphen ('Shopkonfigurator')
        delimiter = '-'

        # (2) .. underscore ('Barsortiment')
        if delimiter not in string:
            delimiter = '_'

        return string.split(delimiter)


    def invoice2date(self, string: str) -> str:
        date_string = self.split_string(string)[1]

        return datetime.strptime(date_string, '%Y%m%d').strftime('%Y-%m-%d')


    def invoice2number(self, string: str) -> str:
        string_list = self.split_string(string)

        # Sort out invoice numbers
        if len(string_list) == 1:
            return string

        return string_list[-1]


    def number2string(self, string) -> str:
        # Strip all letters ..
        hit = match(r'^(.*?)[a-zA-Z]', str(string))

        # .. if there are any
        if hit is not None:
            string = hit[1]

        return super().number2string(string)


    def get_index(self, haystack: list, needle: str, last: bool = False) -> int:
        position = -1 if last else 0

        return [i for i, string in enumerate(haystack) if needle in string][position]


    def build_indices(self, haystack: list, needle: str) -> list:
        return [count for count, line in enumerate(haystack) if line == needle]


    def format_tax_rate(self, string: str) -> str:
        return (string[:-1].replace('Nettobetrag', '')).strip()
