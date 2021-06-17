from os.path import basename, join

import click
import pendulum

from matplotlib import pyplot, rcParams
from pandas import DataFrame
from PyPDF2 import PdfFileMerger

from ..api.exceptions import InvalidLoginException
from ..api.webservice import Webservice
from ..utils import load_json, dump_csv
from ..utils import build_path, create_path, date2string, group_data
from .config import Config
from .database import Database
from .helpers import add_watermark, ask_credentials, pretty_print, print_get_result


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
    '''
    CLI utility for handling data exported from KNV & pcbis.de
    '''

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
@click.option('-s', '--source', default=None, help='Source of contact details.')
@click.option('-d', '--date', default=None, help='Cutoff date in ISO date format, eg \'YYYY-MM-DD\'. Default: today two years ago')
@click.option('-b', '--blocklist', type=click.File('r'), help='Path to file containing mail addresses that should be ignored.')
def contacts(config, source, date, blocklist):
    '''
    Generate customer contact list
    '''

    # Determine source of contact details
    source = source if source in ['orders', 'paypal'] else 'orders'

    # Initialize database
    db = Database(config)

    # Initialize handler
    handler = db.get_orders() if source == 'orders' else db.get_payments('paypal')

    click.echo('Generating contact list from {} ..'.format(source), nl=config.verbose)

    # Generate contact list
    # (1) Set default date
    today = pendulum.today()

    if date is None:
        date = today.subtract(years=2).to_datetime_string()[:10]

    # (2) Apply 'blocklist' CLI option
    if blocklist is not None:
        config.blocklist = blocklist.read().splitlines()

    # (3) Extract & export contacts
    contacts = handler.contacts(date, config.blocklist)

    if config.verbose:
        # Write contacts to stdout
        click.echo(contacts)

    else:
        # Write contacts to CSV file
        dump_csv(contacts, join(config.contacts_dir, '{date}_{today}.csv'.format(date=date, today=today.to_datetime_string()[:10])))

    click.echo(' done!')


@cli.command()
@pass_config
@click.argument('source')
@click.argument('identifier')
def get(config, source, identifier):
    '''
    Retrieve IDENTIFIER from SOURCE in database
    '''

    # Normalize input
    source = source.lower()

    if source not in ['data', 'info', 'invoice', 'order', 'payment']:
        click.echo('Unknown source "{}", exiting ..'.format(source))
        click.Context.exit(0)

    click.echo('Searching database ..', nl=False)

    # Initialize database
    db = Database(config)

    if source == 'data':
        # Extract data record for given order number
        data = db.get_data(identifier)

    if source == 'info':
        # Extract info for given order number
        data = db.get_info(identifier)

    if source == 'invoice':
        # Extract invoice for given invoice number
        data = db.get_invoice(identifier)

    if source == 'order':
        # Extract order for given order number
        data = db.get_order(identifier)

    if source == 'payment':
        # Extract payment for given transaction
        data = db.get_payment(identifier)

    # Print result
    print_get_result(data, identifier)


@cli.command()
@pass_config
@click.option('-y', '--year', default=None, help='Year.')
@click.option('-q', '--quarter', default=None, help='Quarter.')
@click.option('-m', '--months', default=None, multiple=True, help='Month(s)')
@click.option('-c', '--enable-chart', is_flag=True, help='Create bar chart alongside results.')
@click.option('-l', '--limit', default=1, help='Minimum limit to be included in bar chart.')
def rank(config, year, quarter, months, enable_chart, limit):
    '''
    Rank sales
    '''

    # Fall back to current year
    if year is None: year = pendulum.today().year

    # Make months into list if provided
    months = list(months) if months else None

    # Exit if database is empty
    data_files = build_path(config.database_dir, year=year, quarter=quarter, months=months)

    if not data_files:
        click.echo('Error: No orders found in database.')
        click.echo('Exiting ..')
        click.Context.exit(1)

    # Initialize database
    db = Database(config)

    # Initialize handler
    handler = db.get_orders(data_files)

    click.echo('Ranking data ..', nl=False)

    # Extract & rank sales
    ranking = handler.ranking(limit)

    if config.verbose:
        # Write ranking to stdout
        click.echo(ranking)

    else:
        # Count total
        count = sum([item[-1] for item in ranking])

        # Write ranking to CSV file
        file_name = '{first_year}_{last_year}'.format(first_year=basename(data_files[0])[:-5], last_year=basename(data_files[-1])[:-5])
        ranking_file = join(config.rankings_dir, '{year_range}_{count}.csv'.format(year_range=file_name, count=str(count)))

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
        file_name = '{year_range}_{limit}.png'.format(year_range=file_name, limit=str(limit))
        df.plot(kind='barh').get_figure().savefig(join(config.rankings_dir, file_name))

        click.echo(' done!')


@cli.command()
@pass_config
@click.argument('source')
@click.argument('query')
def search(config, source, query):
    '''
    Query SOURCE for QUERY
    '''

    # Normalize input
    source = source.lower()

    if source not in ['invoices', 'orders', 'payments']:
        click.echo('Unknown source "{}", exiting ..'.format(source))
        click.Context.exit(0)

    # Initialize database
    db = Database(config)

    # Set defaults
    blocked_keys = []
    data = []

    # Store items already negated
    negated = []

    if source == 'invoices':
        blocked_keys = ['Datei', 'Steuern', 'Gutscheine']
        data = db.get_invoices().export()

    if source == 'orders':
        blocked_keys = ['Bestellung', 'Rechnungen', 'Gutscheine', 'Abwicklung']
        data = db.get_orders().export()

    if source == 'payments':
        blocked_keys = ['Gebühr', 'Netto', 'Steuern']

        for identifier in db.payment_structures.keys():
            data += db.get_payments(identifier).export()

    # Start search
    for item in data:
        # Skip blocked keys
        for key in blocked_keys:
            if key in item: del item[key]

        for key, value in item.items():
            # Skip key-value pairs negated before
            if {key: value} in negated: continue

            # Search everything
            if query.lower() in str(value).lower():
                click.echo('{key}: "{value}"'.format(key=key, value=str(value)))

                # If obviously unsuccessful ..
                if not click.confirm('Show complete record?', default=False):
                    # .. add result to blocklist
                    negated.append({key: value})

                    # Proceed to next key-value pair
                    continue

                pretty_print(item)

                # Terminate if search was sufficient, otherwise ..
                if click.confirm('Quit search?', default=False):
                    click.echo('Exiting ..')
                    click.Context.exit(0)

                # .. move on
                break

    click.echo('No further results for search term "{}", exiting ..'.format(query))


# DATABASE tasks

@cli.group()
@pass_config
def db(config):
    '''
    Database tasks
    '''

    pass


@db.command()
@pass_config
def stats(config):
    pass


@db.command()
@pass_config
def flush(config):
    '''
    Flush database
    '''

    # Initialize database
    db = Database(config)

    # Delete database files
    click.echo('Flushing database ..', nl=False)
    db.flush()
    click.echo(' done.')


@db.command()
@pass_config
@click.argument('source')
def rebuild(config, source):
    '''
    Rebuild database
    '''

    # Normalize input
    source = source.lower()

    if source not in ['all', 'data', 'invoice', 'invoices', 'payment', 'payments']:
        click.echo('Unknown source "{}", exiting ..'.format(source))
        click.Context.exit(0)

    # Initialize database
    db = Database(config)

    # Rebuild data from ..
    # (1) .. exported KNV data files
    if source in ['all', 'data']:
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

    # (2) .. exported KNV invoice PDF files
    if source in ['all', 'invoice', 'invoices']:
        # Import invoice files
        click.echo('Rebuilding invoices ..', nl=False)
        db.rebuild_invoices()
        click.echo(' done.')

    # (3) .. exported third-party payment data files
    if source in ['all', 'payment', 'payments']:
        # Import payment files
        click.echo('Rebuilding payments ..', nl=False)
        db.rebuild_payments()
        click.echo(' done.')

    if source == 'all': click.echo('Update complete!')


# ACCOUNTING tasks

@cli.group()
@pass_config
def acc(config):
    '''
    Accounting tasks
    '''

    pass


@acc.command()
@pass_config
def reset(config):
    '''
    Clear current session data
    '''

    # Initialize database
    db = Database(config)

    # Delete session files
    click.echo('Clearing session ..', nl=False)
    db.reset_session()
    click.echo(' done.')


@acc.command()
@pass_config
@click.option('-y', '--year', default=None, help='Year.')
@click.option('-q', '--quarter', default=None, help='Quarter.')
@click.option('-m', '--months', default=None, multiple=True, help='Month(s)')
def prepare(config, year, quarter, months):
    '''
    Generate cheatsheet for accounting mode
    '''

    # Fall back to current year
    if year is None: year = pendulum.today().year

    # Make months into list if provided
    months = list(months) if months else None

    # Initialize database
    db = Database(config)

    # Match payments for all available gateways
    for identifier in db.payment_structures.keys():
        # Exit if database is empty
        data_files = build_path(join(config.payment_dir, identifier), year=year, quarter=quarter, months=months)

        if not data_files:
            click.echo('Error: No payments found in database.')
            click.echo('Exiting ..')
            click.Context.exit(1)

        click.echo('Preparing cheatsheet for {} data ..'.format(identifier))

        # Initialize payment handler
        handler = db.get_payments(identifier, data_files)
        payment_data = handler.tax_report()

        if config.verbose:
            # Write matches to stdout
            click.echo(payment_data)

        else:
            # Write results to CSV files
            for code, data in group_data(payment_data).items():
                csv_file = join(config.matches_dir, identifier, code, code + '.csv')
                dump_csv(data, csv_file)

    click.echo('Process complete!')


@acc.command()
@pass_config
@click.option('-y', '--year', default=None, help='Year.')
@click.option('-q', '--quarter', default=None, help='Quarter.')
@click.option('-m', '--months', default=None, multiple=True, help='Month(s)')
def run(config, year, quarter, months):
    '''
    Start accounting session
    '''

    click.echo('Accounting mode ON')

    # Fall back to current year
    if year is None: year = pendulum.today().year

    # Make months into list if provided
    months = list(months) if months else None

    # Initialize database
    db = Database(config)

    # Exit gracefully, save exit status
    exited = False

    # Match payments for all available gateways
    for identifier in db.payment_structures.keys():
        # Take a deep breath, relax ..
        if not click.confirm('Ready to proceed with {} data?'.format(identifier), default=True):
            continue

        # Exit if database is empty
        data_files = build_path(join(config.payment_dir, identifier), year=year, quarter=quarter, months=months)

        if not data_files:
            click.echo('No payments found in database, skipping ..')
            continue

        click.echo('Initializing {} data ..'.format(identifier), nl=False)

        # Load current session
        last_session = db.load_session()

        # Initialize invoice handler
        invoices = db.get_invoices()

        # Initialize payment handler
        handler = db.get_payments(identifier, data_files)

        click.echo(' done.')

        manual_payments = []

        # Go through all unmatched payments
        # TODO: Substitute '_children'
        for index, payment in enumerate(handler._children):
            # Skip payments already marked in previous session
            if payment.assigned() or last_session.has(payment, identifier):
                # Proceed to next payment
                continue

            # Wrap logic in case session gets cut short ..
            try:
                # Print current payment identifier
                click.echo('Payment No. {}:'.format(str(index + 1)))
                pretty_print(payment.export())

                # Declare payment hit accuracy as 'manually assigned'
                payment.assign('manuell')

                if payment.invoice_numbers():
                    for index, invoice in enumerate(payment._children):
                        click.echo('Invoice No. {}: '.format(str(index + 1)))
                        pretty_print(invoice.export())

                    if click.confirm('Does payment match the invoice(s)?', default=False):
                        # Add payment data
                        manual_payments.append(payment)

                        # Proceed to next payment
                        continue

                    if click.confirm('Skip payment?', default=False): continue

                else: click.echo('No matching invoices found, entering manual mode ..')

                manual_invoices = []

                while not manual_invoices:
                    while click.confirm('Enter invoice?', default=True):
                        manual_invoices.append(click.prompt('Type invoice number', type=str))

                    for manual_invoice in manual_invoices:
                        if not invoices.has(manual_invoice):
                            manual_invoices.remove(manual_invoice)
                            click.echo('Invoice "{}" was not found!'.format(manual_invoice))

                    if manual_invoices:
                        click.echo('You have entered the following invoice numbers:')
                        click.echo(manual_invoices)

                        # If selected ..
                        if not click.confirm('Confirm choice(s)?', default=True):
                            # .. start from scratch
                            manual_invoices = []

                    elif click.confirm('Skip payment?', default=False): break

                # Add matched invoice numbers to payment
                payment.data['Rechnungsnummer'] = manual_invoices

                # Make payment 'manually assigned'
                manual_payments.append(payment)

            # Take care of aborted sessions
            except click.Abort:
                # Make some space
                click.echo("\n")

                if click.confirm('Save results before exiting?', default=True):
                    exited = True

                    # Skip payments
                    break

        if manual_payments:
            # Save results
            # (1) Payments
            click.echo('Saving {} payment(s) ..'.format(str(len(manual_payments))), nl=False)
            db.save_session(manual_payments, identifier)
            click.echo(' done.')

            # (2) Invoices
            paid_invoices = []

            for payment in manual_payments:
                for invoice in payment._children:
                    # Declare invoice status as 'paid'
                    invoice.assign('abgeschlossen')

                    # Add invoice to paid invoices
                    paid_invoices.append(invoice)

            click.echo('Saving {} invoice(s) ..'.format(str(len(paid_invoices))), nl=False)
            db.save_session(paid_invoices, 'invoices')
            click.echo(' done.')

            # Shut down
            if exited:
                click.Context.exit(0)

        else:
            click.echo('Nothing to do, moving on ..')

            # Proceed to next payment
            continue

    click.echo('Goodbye!')
    click.echo("\n")
    click.echo('Accounting mode OFF')


@acc.command()
@pass_config
def save(config):
    '''
    Apply session results
    '''

    # Initialize database
    db = Database(config)

    if db.has_session():
        # Prompt about really saving session data
        if not click.confirm('Save current session?', default=True):
            click.echo('Exiting ..')
            click.Context.exit(0)

        # Import session files
        click.echo('Importing data for current session ..', nl=False)
        db.import_session()
        click.echo(' done.')

        if click.confirm('Remove imported session files?', default=True):
            # Delete session files
            click.echo('Clearing session ..', nl=False)
            db.reset_session()
            click.echo(' done.')

        else: click.echo('Exiting ..')

    else: click.echo('Nothing to save, exiting ..')


@acc.command()
@pass_config
@click.option('-y', '--year', default=None, help='Year.')
@click.option('-q', '--quarter', default=None, help='Quarter.')
@click.option('-m', '--months', default=None, multiple=True, help='Month(s)')
def pdf(config, year, quarter, months):
    '''
    Create merged PDF invoices
    '''

    # Fall back to current year
    if year is None: year = pendulum.today().year

    # Make months into list if provided
    months = list(months) if months else None

    # Initialize database
    db = Database(config)

    # Initialize invoice handler
    invoices = db.get_invoices()

    # Merge PDF invoices
    for identifier in db.payment_structures.keys():
        # Exit if database is empty
        data_files = build_path(join(config.payment_dir, identifier), year=year, quarter=quarter, months=months)

        if not data_files:
            click.echo('Error: No payments found in database.')
            click.echo('Exiting ..')
            click.Context.exit(1)

        click.echo('Creating merged {} invoices ..'.format(identifier))

        # Initialize payment handler
        handler = db.get_payments(identifier, data_files)
        payment_data = handler.export()

        # Filter & merge matched invoices
        for code, data in group_data(payment_data).items():
            click.echo('Writing {identifier} invoices for {month} to disk ..'.format(identifier=identifier, month=code), nl=False)

            # Extract matching invoice numbers
            invoice_numbers = set()

            # Initialize merger object
            merger = PdfFileMerger()

            for item in data:
                # If no invoices assigned to payment ..
                if not isinstance(item['Rechnungsnummer'], list):
                    click.echo('No invoices for {}'.format(str(item)))

                    # .. proceed to next payment
                    continue

                for invoice_number in item['Rechnungsnummer']:
                    # If invoice ..
                    # (1) .. not present in database ..
                    if not invoices.has(invoice_number):
                        click.echo('Missing invoice: "{}"'.format(str(invoice_number)))

                        # .. proceed to next invoice
                        continue

                    # (2) .. already processed
                    if invoice_number in invoice_numbers:
                        click.echo('Duplicate invoice: "{}"'.format(str(invoice_number)))

                        # .. proceed to next invoice
                        continue

                    # Merge invoice files
                    # (1) Load original PDF file
                    pdf_file = invoices.get(invoice_number).file()

                    # (2) Add watermark (= payment date & banking service)
                    pdf_file = add_watermark(pdf_file, 'Bezahlt am {date} per {service}'.format(date=date2string(item['Datum'], True), service=item['Dienstleister']))

                    # (3) Merge result with processed PDF invoices
                    merger.append(pdf_file)

                    # Mark invoice number as processed
                    invoice_numbers.add(invoice_number)

            # Write merged PDF invoices to disk
            invoice_file = join(config.matches_dir, identifier, code, code + '.pdf')
            create_path(invoice_file)
            merger.write(invoice_file)

            click.echo(' done.')


@acc.command()
@pass_config
@click.option('-y', '--year', default=None, help='Year.')
@click.option('-m', '--month', default=None, help='Month.')
def show(config, year, month):
    '''
    Show pending invoices
    '''

    # Fall back to current year
    if year is None: year = pendulum.today().year

    # Validate month
    # (1) Convert input to integer
    month = 0 if month is None else int(month)

    # (2) Ensure validity of provided value
    while not 1 <= month <= 12: month = click.prompt('Please enter month (1-12)', type=int)

    # Initialize database
    db = Database(config)

    # Initialize invoices
    invoices = db.get_invoices().filterBy('month', year, month).unassigned()._children

    # Print
    try:
        for index, invoice in enumerate(invoices):
            if invoice.is_revenue():
                click.echo('Invoice No. {}:'.format(str(index + 1)))
                pretty_print(invoice.export())

            if not click.confirm('Show next invoice? ({} left)'.format(len(invoices) - index + 1), default=True):
                break

    except click.Abort: pass

    click.echo('Exiting ..')


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

    # Fall back to current year
    if year is None: year = pendulum.today().year

    # Determine report period & time range
    period = 'year'
    months = range(1, 13)

    if quarter is not None:
        period = 'quarter'
        months = [month + 3 * (int(quarter) - 1) for month in [1, 2, 3]]

    # Initialize database
    db = Database(config)

    # Initialize handler
    handler = db.get_orders()

    click.echo('Generating revenue report ..', nl=config.verbose)

    data = {}

    for gap in range(0, 1 + int(years_back)):
        current_year = str(int(year) - gap)
        data[current_year] = handler.filterBy(period, current_year, quarter).profit_report()

        # Fill missing months with zeroes
        for month in months:
            if month not in data[current_year]: data[current_year][month] = float(0)

    df = DataFrame(data, index=list(data.values())[0].keys())

    click.echo(' done!')

    if config.verbose:
        # Write revenues to stdout
        click.echo(data)

    else:
        # Print well-formatted revenue report
        click.echo(df)

    # Create graph if enabled
    if enable_chart and not config.verbose:
        click.echo('Creating graph from data ..', nl=False)

        # Build filename indicating year range
        file_path = join(config.rankings_dir, 'revenues-{first_year}-{last_year}.png'.format(first_year=year, last_year=str(int(year) - int(years_back))))
        create_path(file_path)
        df.plot(kind='bar').get_figure().savefig(file_path)

    click.echo(' done!')


# API tasks

@cli.group()
@pass_config
@click.option('--credentials', type=clickpath, help='Path to JSON file containing credentials.')
def api(config, credentials):
    '''
    KNV Webservice API tasks
    '''

    if credentials is not None:
        config.credentials = credentials


@api.command()
@pass_config
def version(config):
    '''
    Check current API version
    '''

    # Initialize webservice
    ws = Webservice()

    try:
        click.echo('Current API version: {}'.format(ws.version()))

    except Exception as error:
        click.echo('Error: {}'.format(str(error)))


@api.command()
@pass_config
@click.argument('isbn')
@click.option('-c', '--cache-only', is_flag=True, help='Only return cached database records.')
@click.option('-f', '--force-refresh', is_flag=True, help='Force database record being updated.')
def lookup(config, isbn, cache_only, force_refresh):
    '''
    Lookup information about ISBN
    '''

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

        click.echo('Authentication error: {}'.format(str(error)))
        click.echo('Exiting ..')
        click.Context.exit(1)

    # Retrieve data (either from cache or via API call)
    data = ws.fetch(isbn, force_refresh)

    click.echo(' done!')

    pretty_print(data)


@api.command()
@pass_config
@click.argument('isbn')
@click.option('-q', '--quantity', default=1, help='Number of items to be checked.')
def ola(config, isbn, quantity):
    '''
    Check order availability (OLA)
    '''

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

        click.echo('Authentication error: {}'.format(str(error)))
        click.echo('Exiting ..')
        click.Context.exit(1)

    # Retrieve data (either from cache or via API call)
    ola = ws.ola(isbn, int(quantity))

    click.echo(' done!')

    if config.verbose:
        click.echo(ola.data)

    else:
        click.echo(str(ola))
