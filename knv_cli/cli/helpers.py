from getpass import getpass
from io import BytesIO

import click

from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


# CLI HELPER functions

def add_watermark(pdf_file, string: str, x: int = 60, y: int = 800) -> PdfFileReader:
    # Merge file object & watermark
    # (1) Generate PDF byte stream
    byte_stream = BytesIO()
    can = canvas.Canvas(byte_stream, pagesize=letter)

    # (2) Add text string
    can.drawString(x, y, string)

    # (3) Create file object from result
    can.save()
    byte_stream.seek(0)
    pdf_watermark = PdfFileReader(byte_stream)

    # Load vanilla PDF invoice file
    with open(pdf_file, 'rb') as file:
        pdf_invoice = PdfFileReader(file)

        # Merge invoice & watermark
        # (1) Extract & merge (first) pages
        page_existing = pdf_invoice.getPage(0)
        page_watermark = pdf_watermark.getPage(0)
        page_existing.mergePage(page_watermark)

        # (2) Create new file object with page
        pdf_merged = PdfFileWriter()
        pdf_merged.addPage(page_existing)

        # (3) Add remaining pages from vanilla PDF invoice
        # TODO: This needs testing
        for index in range(1, pdf_invoice.getNumPages()):
            pdf_merged.addPage(pdf_invoice.getPage(index))

        # (4) Append result to PDF data
        pdf_result = BytesIO()
        pdf_result.seek(0)
        pdf_merged.write(pdf_result)

    return PdfFileReader(pdf_result)


def ask_credentials() -> dict:
    return {
        'VKN': getpass('VKN: '),
        'Benutzer': getpass('Benutzer: '),
        'Passwort': getpass('Passwort: '),
    }


def pretty_print(data: dict) -> None:
    for key, value in data.items():
        click.echo('{key}: "{value}"'.format(key=key, value=value))


def print_get_result(data: dict, number: str) -> None:
    if data:
        click.echo(' done.')

        # Print result & exit ..
        pretty_print(data)
        click.Context.exit(0)

    # .. otherwise, end with error message
    click.echo(' failed: No entry found for "{}"'.format(number))
