import json

from getpass import getpass
from glob import glob
from hashlib import md5
from operator import itemgetter
from os import makedirs
from os.path import exists, dirname, join

import click

from pandas import DataFrame


# CLI HELPER functions

def pretty_print(dictionary: dict) -> None:
    for key, value in dictionary.items():
        click.echo('{key}: "{value}"'.format(key=key, value=value))


# CSV functions

def dump_csv(data, csv_file) -> None:
    # Create directory if necessary
    create_path(csv_file)

    # Write CSV file
    DataFrame(data).to_csv(csv_file, index=False)


# JSON functions

def load_json(json_files) -> dict:
    # Normalize single files being passed as input
    if isinstance(json_files, str):
        json_files = glob(json_files)

    data = {}

    for json_file in list(json_files):
        try:
            with open(json_file, 'r') as file:
                data.update(json.load(file))

        except json.decoder.JSONDecodeError:
            raise Exception

        except FileNotFoundError:
            pass

    return data


def dump_json(data, json_file) -> None:
    create_path(json_file)

    with open(json_file, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# UTILITY functions

def ask_credentials() -> dict:
    return {
        'VKN': getpass('VKN: '),
        'Benutzer': getpass('Benutzer: '),
        'Passwort': getpass('Passwort: '),
    }


def build_path(
    base_path: str,
    regex: str = '*.json',
    year: int = None,
    quarter: int = None,
    months: list = None,
) -> list:
    # Create directory if necessary
    create_path(base_path)

    # No year => all files
    if year is None:
        return sorted(glob(join(base_path, regex)))

    # Generate months if quarter was given
    if quarter is not None and 1 <= int(quarter) <= 4:
        months = [month + 3 * (int(quarter) - 1) for month in [1, 2, 3]]

    # Year, but no months => given year
    if months is None:
        return sorted(glob(join(base_path, str(year) + '-' + regex)))

    # Year & months => given months for given year
    return sorted([join(base_path, '-'.join([str(year), str(month).zfill(2) + '.json'])) for month in months])


def create_path(file_path) -> None:
    if not exists(dirname(file_path)):
        try:
            makedirs(dirname(file_path))

        # Guard against race condition
        except OSError:
            pass


def dedupe(duped_data, encoding='utf-8') -> list:
    deduped_data = []
    codes = set()

    for item in duped_data:
        hash_digest = md5(str(item).encode(encoding)).hexdigest()

        if hash_digest not in codes:
            codes.add(hash_digest)
            deduped_data.append(item)

    return deduped_data


def group_data(data) -> dict:
    data = group_dict(data) if isinstance(data, dict) else group_list(data)

    return data


def group_list(ungrouped_data: list) -> dict:
    grouped_data = {}

    for item in ungrouped_data:
        try:
            year, month = str(item['Datum'])[:7].split('-')

        except ValueError:
            # EOF
            pass

        code = '-'.join([str(year), str(month)])

        if code not in grouped_data.keys():
            grouped_data[code] = []

        grouped_data[code].append(item)

    return grouped_data


def group_dict(ungrouped_data: dict) -> dict:
    grouped_data = {}

    for identifier, item in ungrouped_data.items():
        try:
            year, month = str(item['Datum'])[:7].split('-')

        except ValueError:
            # EOF
            pass

        code = '-'.join([str(year), str(month)])

        if code not in grouped_data.keys():
            grouped_data[code] = {}

        grouped_data[code][identifier] = item

    return grouped_data


def sort_data(data):
    data = sort_dict(data) if isinstance(data, dict) else sort_list(data)

    return data


def sort_list(data: list) -> list:
    return sorted(data, key=itemgetter('Datum'))


def sort_dict(data: dict) -> dict:
    return dict(sorted(data.items()))
