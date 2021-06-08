from getpass import getpass

import click


# CLI HELPER functions

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
