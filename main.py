#! /usr/bin/python
# ~*~ coding=utf-8 ~*~


import click

from lib.database import Database
from lib.inspector import Inspector
from lib.utilities import load_config


@click.group()
def cli():
    """Useful tools for handling data exported from KNV / pcbis.de"""


@click.option('-c', '--config', help='Path to configuration file.')
@cli.command()
def update(config: str):
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
@click.option('-y', '--year', help='Year.')
@click.option('-q', '--quarter', help='Quarter.')
@cli.command()
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
@cli.command()
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


if __name__ == '__main__':
    cli()
