#! /usr/bin/python
# ~*~ coding=utf-8 ~*~


import json
from glob import glob
from hashlib import md5
from os import makedirs
from os.path import abspath, exists, dirname, join, realpath

from pandas import DataFrame, concat, read_csv


# CSV tasks

def load_csv(csv_files, encoding='iso-8859-1', delimiter=';') -> list:
    try:
        df = concat(map(lambda file: read_csv(file, sep=delimiter, encoding=encoding, low_memory=False), csv_files))

    except ValueError:
        return []

    return df.to_dict('records')


def dump_csv(data, csv_file) -> None:
    # Create directory if necessary
    create_path(csv_file)

    # Write CSV file
    DataFrame(data).to_csv(csv_file, index=False)


# JSON tasks

def load_json(json_files) -> list:
    data = []

    for json_file in json_files:
        try:
            with open(json_file, 'r') as file:
                data.extend(json.load(file))

        except json.decoder.JSONDecodeError:
            raise Exception

        except FileNotFoundError:
            pass

    return data


def dump_json(data, json_file) -> None:
    create_path(json_file)

    with open(json_file, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# Helper functions

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
