# ~*~ coding=utf-8 ~*~


from os.path import basename, join

import click
import pendulum
from PyPDF2 import PdfFileReader, PdfFileMerger

from .config import Config
from .database import Database
from ..utils import dump_csv, load_json
from ..utils import build_path, create_path, group_data


clickpath = click.Path(exists=True)
pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@pass_config
@click.option('-v', '--verbose', is_flag=True, default=None, help='Activate verbose mode.')
@click.option('--vkn', help='KNV "Verkehrsnummer".')
@click.option('--data-dir', type=clickpath, help='Custom database directory.')
@click.option('--import-dir', type=clickpath, help='Custom import directory.')
@click.option('--export-dir', type=clickpath, help='Custom export directory.')
def cli(config, verbose, vkn, data_dir, import_dir, export_dir):
    """CLI utility for handling data exported from KNV & pcbis.de"""

    # Apply CLI options
    if verbose is not None:
        config.verbose = verbose

    if vkn is not None:
        config.VKN = vkn

    if data_dir is not None:
        config.data_dir = data_dir

    if import_dir is not None:
        config.import_dir = import_dir

    if export_dir is not None:
        config.export_dir = export_dir


# GENERAL tasks

@cli.command()
@pass_config
@click.option('-y', '--year', default=None, help='Year.')
@click.option('-q', '--quarter', default=None, help='Quarter.')
def match(config, year, quarter):
    """Match payments & invoices"""

    # Initialize database
    db = Database(config)

    # Load data from ..
    # (1) .. payment sources
    payments = db.get_payments('paypal', year, quarter)

    # Exit if database has no payments
    if not payments:
        click.echo('Error: No payments found in database.')
        click.Context.exit(1)

    click.echo('Matching data ..', nl=False)

    # Load orders, infos & invoices
    db.init()

    # Match payments with orders & infos
    payments.match_payments(db.orders.data, db.infos.data)

    if config.verbose:
        # Write matches to stdout
        click.echo(payments.matched_payments())

    else:
        # Filter & merge matched invoices
        for code, data in group_data(payments.matched_payments()).items():
            # Extract matching invoice numbers
            invoice_numbers = set()

            for item in data:
                if item['Vorgang'] != 'nicht zugeordnet':
                    for invoice_number in item['Vorgang']:
                        invoice_numbers.add(invoice_number)

            # Init merger object
            merger = PdfFileMerger()

            # Merge corresponding invoices
            for invoice_number in sorted(invoice_numbers):
                if db.invoices.has(invoice_number, True):
                    pdf_file = db.invoices.get(invoice_number)

                    with open(pdf_file, 'rb') as file:
                        merger.append(PdfFileReader(file))

                else:
                    click.echo("\n" + 'Missing invoice: ' + str(invoice_number))

            # Write merged PDF to disk
            invoice_file = join(config.matches_dir, code, code + '.pdf')
            create_path(invoice_file)
            merger.write(invoice_file)

        # Write results to CSV files
        for code, data in group_data(payments.matched_payments(True)).items():
            csv_file = join(config.matches_dir, code, code + '.csv')
            dump_csv(data, csv_file)

    click.echo(' done!')


@cli.command()
@pass_config
@click.option('-y', '--year', default=None, help='Year.')
@click.option('-q', '--quarter', default=None, help='Quarter.')
@click.option('-c', '--enable-chart', is_flag=True, help='Create bar chart alongside results.')
@click.option('-l', '--limit', default=1, help='Minimum limit to be included in bar chart.')
def rank(config, year, quarter, enable_chart, limit):
    """Rank sales"""

    # Initialize database
    db = Database(config)

    # Exit if database is empty
    order_files = build_path(config.order_dir, year=year, quarter=quarter)

    if not order_files:
        click.echo('Error: No orders found in database.')
        click.Context.exit(1)

    click.echo('Ranking data ..', nl=False)

    # Initialize handler
    handler = db.get_orders(order_files)

    # Extract & rank sales
    ranking = handler.get_ranking()

    if config.verbose:
        # Write ranking to stdout
        click.echo(ranking)

    else:
        # Count total
        count = sum([item['Anzahl'] for item in ranking])

        # Write ranking to CSV file
        file_name = basename(order_files[0])[:-5] + '_' + basename(order_files[-1])[:-5]
        ranking_file = join(config.rankings_dir, file_name + '_' + str(count) + '.csv')

        dump_csv(ranking, ranking_file)

    click.echo(' done!')

    # Create graph if enabled
    if enable_chart and not config.verbose:
        click.echo('Creating graph from data ..', nl=False)

        # Plot graph into PNG file
        chart_file = join(config.rankings_dir, file_name + '_' + str(limit) + '.png')

        bar_chart = handler.get_ranking_chart(ranking, limit)
        bar_chart.savefig(chart_file)

        click.echo(' done!')


@cli.command()
@pass_config
@click.option('-d', '--date', default=None, help='Cutoff date in ISO date format, eg \'YYYY-MM-DD\'. Default: today two years ago')
@click.option('-b', '--blocklist', type=click.File('r'), help='Path to file containing mail addresses that should be ignored.')
def contacts(config, date, blocklist):
    """Generate customer contact list"""

    # Initialize database
    db = Database(config)

    # Exit if database is empty
    order_files = build_path(config.order_dir)

    if not order_files:
        click.echo('Error: No orders found in database.')
        click.Context.exit(1)

    click.echo('Generating contact list ..', nl=config.verbose)

    # Initialize handler
    handler = db.get_orders(order_files)

    # Apply 'blocklist' CLI option
    if blocklist is not None:
        config.blocklist = blocklist.read().splitlines()

    # Set default date
    today = pendulum.today()

    if date is None:
        date = today.subtract(years=2).to_datetime_string()[:10]

    # Extract & export contacts
    contacts = handler.get_contacts(handler.data, date, config.blocklist)

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
@pass_config
def db(config):
    """Database tasks"""
    pass


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