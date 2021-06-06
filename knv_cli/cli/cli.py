from os.path import basename, join

import click
import pendulum

from matplotlib import pyplot, rcParams
from pandas import DataFrame
from PyPDF2 import PdfFileReader, PdfFileMerger

from .config import Config
from .database import Database
from ..api.exceptions import InvalidLoginException
from ..api.webservice import Webservice
from ..processors.knv.invoices import InvoiceProcessor
from ..utils import load_json, dump_json, dump_csv
from ..utils import ask_credentials, build_path, create_path, group_data, pretty_print


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
@click.option('-c', '--enable-chart', is_flag=True, help='Create bar chart alongside results.')
@click.option('-l', '--limit', default=1, help='Minimum limit to be included in bar chart.')
def rank(config, year, quarter, enable_chart, limit):
    """Rank sales"""

    # Initialize database
    db = Database(config)

    # Exit if database is empty
    data_files = build_path(config.database_dir, year=year, quarter=quarter)

    if not data_files:
        click.echo('Error: No orders found in database.')
        click.Context.exit(1)

    # Initialize handler
    handler = db.get_orders(data_files)

    click.echo('Ranking data ..', nl=False)

    # Extract & rank sales
    ranking = handler.get_ranking(limit)

    if config.verbose:
        # Write ranking to stdout
        click.echo(ranking)

    else:
        # Count total
        count = sum([item[-1] for item in ranking])

        # Write ranking to CSV file
        file_name = basename(data_files[0])[:-5] + '_' + basename(data_files[-1])[:-5]
        ranking_file = join(config.rankings_dir, file_name + '_' + str(count) + '.csv')

        dump_csv(ranking, ranking_file)

    click.echo(' done!')

    # Create graph if enabled
    if enable_chart and not config.verbose:
        click.echo('Creating graph from data ..', nl=False)

        # Plot graph into PNG file
        # (1) Load ranking into dataframe
        # (2) Rotate & center x-axis labels
        # (3) Make graph 'just fit' image dimensions
        df = DataFrame([{'Anzahl': item[-1], 'Titel': item[0]} for item in ranking], index=[item[0] for item in ranking])
        pyplot.xticks(rotation=45, horizontalalignment='center')
        rcParams.update({'figure.autolayout': True})

        # (4) Output graph
        df.plot(kind='barh').get_figure().savefig(join(config.rankings_dir, file_name + '_' + str(limit) + '.png'))

        click.echo(' done!')


@cli.command()
@pass_config
@click.option('-d', '--date', default=None, help='Cutoff date in ISO date format, eg \'YYYY-MM-DD\'. Default: today two years ago')
@click.option('-b', '--blocklist', type=click.File('r'), help='Path to file containing mail addresses that should be ignored.')
def contacts(config, date, blocklist):
    """Generate customer contact list"""

    # Initialize database
    db = Database(config)

    # Initialize handler
    handler = db.get_knv()

    # Exit if database is empty
    if not handler.data:
        click.echo('Error: No orders found in database.')
        click.Context.exit(1)

    click.echo('Generating contact list ..', nl=config.verbose)

    # Generate contact list
    # (1) Set default date
    today = pendulum.today()

    if date is None:
        date = today.subtract(years=2).to_datetime_string()[:10]

    # (2) Apply 'blocklist' CLI option
    if blocklist is not None:
        config.blocklist = blocklist.read().splitlines()

    # (3) Extract & export contacts
    contacts = handler.get_contacts(date, config.blocklist)

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
def stats():
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


# DATABASE REBUILD subtasks

@db.group()
@pass_config
def rebuild(config):
    pass


@rebuild.command()
@pass_config
def all(config):
    """Rebuild database"""

    # Initialize database
    db = Database(config)

    # Import info files
    click.echo('Rebuilding infos ..', nl=False)
    db.rebuild_infos()
    click.echo(' done.')

    # Import order files
    click.echo('Rebuilding orders ..', nl=False)
    db.rebuild_orders()
    click.echo(' done.')

    # Merge data sources
    click.echo('Merging data sources ..', nl=False)
    db.rebuild_data()
    click.echo(' done.')

    # Import payment files
    click.echo('Rebuilding payments ..', nl=False)
    db.rebuild_payments()
    click.echo(' done.')

    # Import invoice files
    click.echo('Rebuilding invoices ..', nl=False)
    db.rebuild_invoices()
    click.echo(' done.')

    click.echo('Update complete!')


@rebuild.command()
@pass_config
def payments(config):
    """Rebuild payments"""

    # Initialize database
    db = Database(config)

    # Import payment files
    click.echo('Rebuilding payments ..', nl=False)
    db.rebuild_payments()
    click.echo(' done.')


@rebuild.command()
@pass_config
def infos(config):
    """Rebuild infos"""

    # Initialize database
    db = Database(config)

    # Import info files
    click.echo('Rebuilding infos ..', nl=False)
    db.rebuild_infos()
    click.echo(' done.')


@rebuild.command()
@pass_config
def invoices(config):
    """Rebuild invoices"""

    # Initialize database
    db = Database(config)

    # Import invoice files
    click.echo('Rebuilding invoices ..', nl=False)
    db.rebuild_invoices()
    click.echo(' done.')


@rebuild.command()
@pass_config
def orders(config):
    """Rebuild orders"""

    # Initialize database
    db = Database(config)

    # Import order files
    click.echo('Rebuilding orders ..', nl=False)
    db.rebuild_orders()
    click.echo(' done.')


@rebuild.command()
@pass_config
def merge(config):
    """Rebuild merged data"""

    # Initialize database
    db = Database(config)

    # Merge data sources
    click.echo('Merging data sources ..', nl=False)
    db.rebuild_data()
    click.echo(' done.')


# DATABASE GET subtasks

@db.group()
@pass_config
def get(config):
    pass


@get.command()
@pass_config
@click.argument('number')
def payment(config, number):
    click.echo('Searching database ..', nl=False)

    # Initialize database
    db = Database(config)

    # Match payments for all available gateways
    for identifier in db.gateways.keys():
        # Initialize payment handler
        handler = db.get_payments(identifier)

        # Extract payment for given (transaction or order) number
        payment = handler.get(number)

        if payment:
            click.echo(' done.')
            pretty_print(payment)
            click.Context.exit(0)

    click.echo(' failed: No entry found for "{}"'.format(number))


@get.command()
@pass_config
@click.argument('invoice_number')
def invoice(config, invoice_number):
    click.echo('Searching database ..', nl=False)

    # Initialize database
    db = Database(config)

    # Initialize info handler
    handler = db.get_invoices()

    if invoice_number in handler.data:
        click.echo(' done.')
        pretty_print(handler.get(invoice_number))
        click.Context.exit(0)

    click.echo(' failed: No entry found for "{}"'.format(invoice_number))


@get.command()
@pass_config
@click.argument('order_number')
def order(config, order_number):
    click.echo('Searching database ..', nl=False)

    # Initialize database
    db = Database(config)

    # Initialize order handler
    handler = db.get_orders()

    # Extract order for given order number
    order = handler.get(order_number)

    if order:
        click.echo(' done.')
        pretty_print(order)
        click.Context.exit(0)

    click.echo(' failed: No entry found for "{}"'.format(order_number))


@get.command()
@pass_config
@click.argument('order_number')
def info(config, order_number):
    click.echo('Searching database ..', nl=False)

    # Initialize database
    db = Database(config)

    # Initialize info handler
    handler = db.get_infos()

    # Extract info for given order number
    info = handler.get(order_number)

    if info:
        click.echo(' done.')
        pretty_print(info)
        click.Context.exit(0)

    click.echo(' failed: No entry found for "{}"'.format(order_number))


@get.command()
@pass_config
@click.argument('order_number')
def data(config, order_number):
    click.echo('Searching database ..', nl=False)

    # Initialize database
    db = Database(config)

    # Initialize info handler
    handler = db.get_knv()

    # Extract combined data record for given order number
    data = handler.get(order_number)

    if data:
        click.echo(' done.')
        pretty_print(data)
        click.Context.exit(0)

    click.echo(' failed: No entry found for "{}"'.format(order_number))


# ACCOUNTING tasks

@cli.group()
@pass_config
def acc(config):
    pass


@acc.command()
@pass_config
def run(config):
    """Start accounting mode"""
    pass


@acc.command()
@pass_config
@click.option('-y', '--year', default=None, help='Year.')
@click.option('-q', '--quarter', default=None, help='Quarter.')
@click.option('-b', '--years_back', default=2, help='Years back.')
@click.option('-c', '--enable-chart', is_flag=True, help='Create bar chart alongside results.')
def report(config, year, quarter, years_back, enable_chart):
    '''
    Generate revenue report
    '''

    # Initialize database
    db = Database(config)

    handler = db.get_orders()

    if year is None:
        year = pendulum.today().year

    click.echo('Generating revenue report ..', nl=config.verbose)

    revenues = {}

    for i in range(0, 1 + int(years_back)):
        this_year = str(int(year) - i)
        revenues[this_year] = handler.get_revenues(this_year, quarter)

    df = DataFrame(revenues, index=list(revenues.values())[0].keys())

    click.echo(' done!')

    if config.verbose:
        # Write revenues to stdout
        print(revenues)

    else:
        # Print well-formatted revenue report
        click.echo(df)

    # Create graph if enabled
    if enable_chart and not config.verbose:
        click.echo('Creating graph from data ..', nl=False)

        # Build filename indicating year range
        file_name = 'revenues-' + year + '-' + str(int(year) + '-' + years_back) + '.png'
        df.plot(kind='bar').get_figure().savefig(join(config.rankings_dir, file_name))


@acc.command()
@pass_config
@click.option('-y', '--year', default=None, help='Year.')
@click.option('-q', '--quarter', default=None, help='Quarter.')
def match(config, year, quarter):
    """Match payments & invoices"""

    # Initialize database
    db = Database(config)

    # Match payments for all available gateways
    for identifier in db.gateways.keys():
        # Initialize payment handler
        handler = db.get_payments(identifier, year, quarter)

        # Exit if database has no payments
        if not handler.data:
            click.echo('No "{}" payments found in database, skipping.'.format(identifier))
            continue

        click.echo('Matching ' + identifier + ' data ..', nl=False)

        # Get combined order data
        data = db.get_knv().data

        # Load invoices from database
        invoices = db.get_invoices()

        # Match payments with orders & infos
        handler.match_payments(data, invoices.data)

        if config.verbose:
            # Write matches to stdout
            click.echo(handler.matched_payments())

        else:
            # Filter & merge matched invoices
            for code, data in group_data(handler.data).items():
                # Extract matching invoice numbers
                invoice_numbers = set()

                for item in data.values():
                    if isinstance(item['Rechnungen'], list):
                        for invoice_number in item['Rechnungen']:
                            invoice_numbers.add(invoice_number)

                # Init merger object
                merger = PdfFileMerger()

                # Merge corresponding invoices
                for invoice_number in sorted(invoice_numbers):
                    if invoice_number in invoices.data:
                        pdf_file = invoices.get(invoice_number)['Datei']

                        with open(pdf_file, 'rb') as file:
                            merger.append(PdfFileReader(file))

                    else:
                        click.echo("\n" + 'Missing invoice: ' + str(invoice_number))

                # Write merged PDF to disk
                invoice_file = join(config.matches_dir, identifier, code, code + '.pdf')
                create_path(invoice_file)
                merger.write(invoice_file)

            # Write results to CSV files
            for code, data in group_data(handler.matched_payments(True)).items():
                csv_file = join(config.matches_dir, identifier, code, code + '.csv')
                dump_csv(data, csv_file)

        click.echo(' done!')

    click.echo('Process complete!')


# API tasks

@cli.group()
@pass_config
@click.option('--credentials', type=clickpath, help='Path to JSON file containing credentials.')
def api(config, credentials):
    """KNV Webservice API tasks"""

    if credentials is not None:
        config.credentials = credentials


@api.command()
@pass_config
def version(config):
    """Check current API version"""

    # Initialize webservice
    ws = Webservice()

    try:
        click.echo('Current API version: ' + ws.version())

    except Exception as error:
        click.echo('Error: ' + str(error))


@api.command()
@pass_config
@click.argument('isbn')
@click.option('-o', '--output-file', type=click.Path(), help='Path to output JSON file.')
@click.option('-c', '--cache-only', is_flag=True, help='Only return cached database records.')
@click.option('-f', '--force-refresh', is_flag=True, help='Force database record being updated.')
def lookup(config, isbn, output_file, cache_only, force_refresh):
    """Lookup information about ISBN"""

    if cache_only is False:
        if config.credentials:
            credentials = load_json(config.credentials)

        else:
            click.echo('Please enter your account information first:')
            credentials = ask_credentials()

    click.echo('Loading data ..', nl=False)

    data = {}

    try:
        # Initialize webservice
        ws = Webservice(credentials, config.cache_dir)

    except InvalidLoginException as error:
        click.echo(' failed!')

        click.echo('Authentication error: ' + str(error))
        click.Context.exit(1)

    # Retrieve data (either from cache or via API call)
    data = ws.fetch(isbn, force_refresh)

    click.echo(' done!')

    if config.verbose:
        click.echo(data)

    else:
        if 'AutorSachtitel' in data:
            click.echo('Match: ' + data['AutorSachtitel'])

    if output_file:
        dump_json(data, output_file)
        click.echo('Data saved: ' + output_file)


@api.command()
@pass_config
@click.argument('isbn')
@click.option('-q', '--quantity', default=1, help='Number of items to be checked.')
def ola(config, isbn, quantity):
    if config.credentials:
        credentials = load_json(config.credentials)

    else:
        click.echo('Please enter your account information first:')
        credentials = ask_credentials()

    click.echo('Calling OLA ..', nl=False)

    try:
        # Initialize webservice
        ws = Webservice(credentials, config.cache_dir)

    except InvalidLoginException as error:
        click.echo(' failed!')

        click.echo('Authentication error: ' + str(error))
        click.Context.exit(1)

    # Retrieve data (either from cache or via API call)
    ola = ws.ola(isbn, int(quantity))

    click.echo(' done!')

    if config.verbose:
        click.echo(ola.data)

    else:
        click.echo(str(ola))
