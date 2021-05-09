# ~*~ coding=utf-8 ~*~


from configparser import SafeConfigParser
from os.path import abspath, dirname, exists, join, realpath

import click

from lib.config import Config
from lib.database import Database
from lib.inspector import Inspector

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@pass_config
@click.option('-v', '--verbose', is_flag=True, help='Activates verbose mode.')
def cli(config, verbose):
    """Provides tools for handling KNV data"""

    # Apply CLI options
    config.verbose = verbose


# DATABASE tasks

@cli.group()
def db():
    """Database tasks"""


@db.command()
@pass_config
def update(config):
    """Updates database"""

    # Initialize object
    handler = Database(config)

    # Import payment files
    click.echo('Importing payments ..', nl=False)
    handler.import_payments()
    click.echo(' done.')

    # Import order files
    click.echo('Importing orders ..', nl=False)
    handler.import_orders()
    click.echo(' done.')

    # Import info files
    click.echo('Importing infos ..', nl=False)
    handler.import_infos()
    click.echo(' done.')

    # Import PDF files
    click.echo('Importing invoices ..', nl=False)
    handler.import_invoices()
    click.echo(' done.')

    click.echo('Update complete!')


@db.command()
@pass_config
def flush(config):
    """Flushes database"""

    # Initialize object
    handler = Database(config)

    # Import payment files
    click.echo('Flushing database ..', nl=False)
    handler.flush()
    click.echo(' done.')


# EXTRACTION tasks

@cli.group()
def ex():
    """Extraction tasks"""


@ex.command()
@pass_config
@click.option('-y', '--year', help='Year.')
@click.option('-q', '--quarter', help='Quarter.')
def match(config, year = None, quarter = None):
    """Matches payments & invoices"""

    # Initialize object
    handler = Inspector(config)

    # Load & match data sources
    click.echo('Matching data ..')
    handler.match(year, quarter)
    click.echo(' done!')


@ex.command()
@pass_config
@click.option('-y', '--year', help='Year.')
@click.option('-q', '--quarter', help='Quarter.')
def rank(config, year = None, quarter = None):
    """Ranks sold books"""

    # Initialize object
    handler = Inspector(config)

    # Load & match data sources
    click.echo('Ranking data ..', nl=False)
    handler.rank(year, quarter)
    click.echo(' done!')


@ex.command()
@pass_config
@click.option('-d', '--date', help='Cutoff date in ISO date format, eg \'YYYY-MM-DD\'. Default: today two years ago')
def contacts(config, date = None):
    """Generates mailmerge-ready contact list"""

    # Initialize object
    handler = Inspector(config)

    # Load & match data sources
    click.echo('Generating contact list ..', nl=False)
    handler.contacts(date)
    click.echo(' done!')
