#! /usr/bin/python
# ~*~ coding=utf-8 ~*~


from glob import glob
from hashlib import md5
from os import makedirs
from os.path import abspath, exists, dirname, join, realpath

from yaml import safe_load, YAMLError


def build_path(
    base_path: str,
    regex: str = '*.json',
    year: int = None,
    quarter: int = None,
    months: list = None,
) -> list:
    # Check if directory exists
    if not exists(base_path):
        raise Exception

    # No year => all files
    if year is None:
        return glob(join(base_path, regex))

    # Generate months if quarter was given
    if quarter is not None and 1 <= int(quarter) <= 4:
        months = [month + 3 * (int(quarter) - 1) for month in [1, 2, 3]]

    # Year, but no months => given year
    if months is None:
        return glob(join(base_path, str(year) + '-' + regex))

    # Year & months => given months for given year
    return [join(base_path, '-'.join([str(year), str(month).zfill(2) + '.json'])) for month in months]


def create_path(file_path) -> None:
    if not exists(dirname(file_path)):
        try:
            makedirs(dirname(file_path))

        # Guard against race condition
        except OSError as e:
            # pylint: disable=undefined-variable
            if e.errno != errno.EEXIST:
                raise


def dedupe(duped_data, encoding='utf-8') -> list:
    deduped_data = []
    codes = set()

    for item in duped_data:
        hash_digest = md5(str(item).encode(encoding)).hexdigest()

        if hash_digest not in codes:
            codes.add(hash_digest)
            deduped_data.append(item)

    return deduped_data


def group_data(ungrouped_data) -> dict:
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
