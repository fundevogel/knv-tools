# ~*~ coding=utf-8 ~*~


from configparser import SafeConfigParser
from os.path import abspath, dirname, exists, join, realpath

import click

from core.config import Config
from core.database import Database
from core.tasks import Tasks

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

    # Initialize object
    handler = Tasks(config)

    # Load & match data sources
    click.echo('Matching data ..', nl=False)
    handler.task_match_payments(year, quarter)
    click.echo(' done!')


@cli.command()
@pass_config
@click.option('-y', '--year', help='Year.')
@click.option('-q', '--quarter', help='Quarter.')
def rank(config, year = None, quarter = None):
    """Rank sales"""

    # Initialize object
    handler = Tasks(config)

    # Load & match data sources
    click.echo('Ranking data ..', nl=False)
    handler.task_rank_sales(year, quarter)
    click.echo(' done!')


@cli.command()
@pass_config
@click.option('-d', '--date', help='Cutoff date in ISO date format, eg \'YYYY-MM-DD\'. Default: today two years ago')
@click.option('-b', '--blocklist', type=click.File('r'), help='Path to file containing mail addresses that should be ignored.')
def contacts(config, date = None, blocklist = None):
    """Generate customer contact list"""

    # Apply 'blocklist' CLI option
    if blocklist is not None:
        config.blocklist = blocklist.read().splitlines()

    # Initialize object
    handler = Tasks(config)

    # Load & match data sources
    click.echo('Generating contact list ..', nl=config.verbose)
    handler.task_create_contacts(date)
    click.echo(' done!')


# DATABASE tasks

@cli.group()
def db():
    """Database tasks"""


@db.command()
@pass_config
def update(config):
    """Update database"""

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
def stats():
    """Show statistics"""
    pass


@db.command()
@pass_config
def flush(config):
    """Flush database"""

    # Initialize object
    handler = Database(config)

    # Import payment files
    click.echo('Flushing database ..', nl=False)
    handler.flush()
    click.echo(' done.')
