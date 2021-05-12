# ~*~ coding=utf-8 ~*~


from configparser import SafeConfigParser
from os.path import basename, join

import click
import pendulum
from PyPDF2 import PdfFileReader, PdfFileMerger

from .config import Config
from .database import Database
from .operations import match_payments, get_contacts, get_ranking
from .utils import dump_csv, load_json
from .utils import build_path, create_path, group_data

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@pass_config
@click.option('-v', '--verbose', is_flag=True, default = None, help='Activate verbose mode.')
def cli(config, verbose):
    """Tools for handling KNV data"""

    # Apply CLI options
    if verbose is not None:
        config.verbose = verbose


# GENERAL tasks

@cli.command()
@pass_config
@click.option('-y', '--year', help='Year.')
@click.option('-q', '--quarter', help='Quarter.')
def match(config, year = None, quarter = None):
    """Match payments & invoices"""

    click.echo('Matching data ..', nl=False)

    # Generate data from ..
    # (1) .. payment sources
    payment_files = build_path(config.payment_dir, year=year, quarter=quarter)
    payments = load_json(payment_files)

    # (2) .. order sources
    order_files = build_path(config.order_dir)
    orders = load_json(order_files)

    # (3) .. info sources
    info_files = build_path(config.info_dir)
    infos = load_json(info_files)

    # Match payments with orders & infos
    matches = match_payments(payments, orders, infos)

    if config.verbose:
        # Write m<tches to stdout
        click.echo(matches)

    else:
        # Filter & merge matched invoices
        invoices = build_path(config.invoice_dir, '*.pdf')
        invoices = {basename(invoice).split('-')[2][:-4]: invoice for invoice in invoices}

        for code, data in group_data(matches).items():
            # Extract matching invoice numbers
            invoice_numbers = set()

            for item in data:
                if item['Vorgang'] != 'nicht zugeordnet':
                    for invoice_number in item['Vorgang'].split(';'):
                        invoice_numbers.add(invoice_number)

            # Init merger object
            merger = PdfFileMerger()

            # Merge corresponding invoices
            for invoice_number in invoice_numbers:
                if invoice_number in invoices:
                    pdf_file = invoices[invoice_number]

                    with open(pdf_file, 'rb') as file:
                        merger.append(PdfFileReader(file))

                else:
                    click.echo('Missing invoice: ' + str(invoice_number))

            # Write merged PDF to disk
            invoice_file = join(config.matches_dir, code, config.invoice_file)
            create_path(invoice_file)
            merger.write(invoice_file)

        # Write results to CSV files
        for code, data in group_data(matches).items():
            csv_file = join(config.matches_dir, code, code + '.csv')
            dump_csv(data, csv_file)

    click.echo(' done!')


@cli.command()
@pass_config
@click.option('-y', '--year', help='Year.')
@click.option('-q', '--quarter', help='Quarter.')
def rank(config, year = None, quarter = None):
    """Rank sales"""

    click.echo('Ranking data ..', nl=False)

    # Fetch orders
    order_files = build_path(config.order_dir, year=year, quarter=quarter)
    orders = load_json(order_files)

    # Extract & rank sales
    ranking = get_ranking(orders)

    if config.verbose:
        # Write ranking to stdout
        click.echo(ranking)

    else:
        # Count total
        count = sum([item['Anzahl'] for item in ranking])

        # Write ranking to CSV file
        file_name = basename(order_files[0])[:-5] + '_' + basename(order_files[-1])[:-5] + '_' + str(count)
        ranking_file = join(config.rankings_dir, file_name + '.csv')

        dump_csv(ranking, ranking_file)

    click.echo(' done!')


@cli.command()
@pass_config
@click.option('-d', '--date', help='Cutoff date in ISO date format, eg \'YYYY-MM-DD\'. Default: today two years ago')
@click.option('-b', '--blocklist', type=click.File('r'), help='Path to file containing mail addresses that should be ignored.')
def contacts(config, date = None, blocklist = None):
    """Generate customer contact list"""

    click.echo('Generating contact list ..', nl=config.verbose)

    # Apply 'blocklist' CLI option
    if blocklist is not None:
        config.blocklist = blocklist.read().splitlines()

    # Set default date
    today = pendulum.today()

    if date is None:
        date = today.subtract(years=2).to_datetime_string()[:10]

    # Fetch orders
    order_files = build_path(config.order_dir)
    orders = load_json(order_files)

    # Extract & export contacts
    contacts = get_contacts(orders, date, config.blocklist)

    if config.verbose:
        # Write contacts to stdout
        click.echo(contacts)

    else:
        # Write contacts to CSV file
        file_name = date + '_' + today.to_datetime_string()[:10]
        contacts_file = join(config.contacts_dir, file_name + '.csv')

        dump_csv(contacts, contacts_file)

    click.echo(' done!')


# DATABASE tasks

@cli.group()
def db():
    """Database tasks"""


@db.command()
@pass_config
def update(config):
    """Update database"""

    # Initialize database
    db = Database(config)

    # Import payment files
    click.echo('Importing payments ..', nl=False)
    db.import_payments()
    click.echo(' done.')

    # Import order files
    click.echo('Importing orders ..', nl=False)
    db.import_orders()
    click.echo(' done.')

    # Import info files
    click.echo('Importing infos ..', nl=False)
    db.import_infos()
    click.echo(' done.')

    # Import PDF files
    click.echo('Importing invoices ..', nl=False)
    db.import_invoices()
    click.echo(' done.')

    click.echo('Update complete!')


@db.command()
@pass_config
def stats():
    """Show statistics"""
    pass


@db.command()
@pass_config
def flush(config):
    """Flush database"""

    # Initialize database
    db = Database(config)

    # Import payment files
    click.echo('Flushing database ..', nl=False)
    db.flush()
    click.echo(' done.')
