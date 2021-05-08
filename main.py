#! /usr/bin/python
# ~*~ coding=utf-8 ~*~


from os.path import abspath, dirname, exists, join, realpath

import click
from yaml import safe_load, YAMLError

from lib.database import Database
from lib.inspector import Inspector


def load_config(config_file: str = None):
    if config_file is None or not exists(realpath(config_file)):
        config_path = dirname(dirname(abspath(__file__)))
        config_file = join(config_path, 'config.yml')

    with open(config_file, 'r') as file:
        try:
            config = safe_load(file)
        except YAMLError:
            pass

    return config


@click.group()
def cli():
    """Useful tools for handling data exported from KNV / pcbis.de"""


@cli.group()
def db():
    """Database tasks"""
    pass

@click.option('-c', '--config', help='Path to configuration file.')
@db.command()
def update(config):
    """Updates database"""

    # Load config
    config = load_config(config)

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


@click.option('-c', '--config', help='Path to configuration file.')
@db.command()
def flush(config):
    """Flushes database"""

    # Load config
    config = load_config(config)

    # Initialize object
    handler = Database(config)

    # Import payment files
    click.echo('Flushing database ..', nl=False)
    handler.flush()
    click.echo(' done.')


@cli.group()
def ex():
    """Extraction tasks"""
    pass


@click.option('-c', '--config', help='Path to configuration file.')
@click.option('-y', '--year', help='Year.')
@click.option('-q', '--quarter', help='Quarter.')
@ex.command()
def match(
    config: str,
    year: int = None,
    quarter: int = None,
):
    """Matches payments & invoices"""

    # Load config
    config = load_config(config)

    # Initialize object
    handler = Inspector(config)

    # Load & match data sources
    click.echo('Matching data ..')
    handler.match(year, quarter)
    click.echo(' done!')


@click.option('-c', '--config', help='Path to configuration file.')
@click.option('-y', '--year', help='Year.')
@click.option('-q', '--quarter', help='Quarter.')
@ex.command()
def rank(
    config: str,
    year: int = None,
    quarter: int = None,
):
    """Ranks sold books"""

    # Load config
    config = load_config(config)

    # Initialize object
    handler = Inspector(config)

    # Load & match data sources
    click.echo('Ranking data ..', nl=False)
    handler.rank(year, quarter)
    click.echo(' done!')


@click.option('-c', '--config', help='Path to configuration file.')
@click.option('-d', '--date', help='Cutoff date in ISO date format, eg \'YYYY-MM-DD\'. Default: today two years ago')
@ex.command()
def contacts(config: str, date: str = None):
    """Generates mailmerge-ready contact list"""

    # Load config
    config = load_config(config)

    # Initialize object
    handler = Inspector(config)

    # Load & match data sources
    click.echo('Generating contact list ..', nl=False)
    handler.contacts(date)
    click.echo(' done!')


if __name__ == '__main__':
    cli()
