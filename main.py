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


if __name__ == '__main__':
    cli()
