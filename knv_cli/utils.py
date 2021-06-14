import json

from datetime import datetime
from fnmatch import translate
from glob import glob
from hashlib import md5
from operator import itemgetter
from os import listdir, makedirs
from os.path import exists, dirname, join, splitext
from re import compile, match, IGNORECASE
from pandas import DataFrame, concat, read_csv


# CSV functions

def load_csv(
    csv_files: list,
    delimiter: str = None,
    encoding: str = None,
    skiprows: int = None
) -> list:
    try:
        return concat(map(lambda file: read_csv(
            file,
            sep=delimiter,
            encoding=encoding,
            skiprows=skiprows,
            low_memory=False,
        ), csv_files)).to_dict('records')

    except ValueError:
        pass

    return []


def dump_csv(data: dict, csv_file: str) -> None:
    # Create directory if necessary
    create_path(csv_file)

    # Write CSV file
    DataFrame(data).to_csv(csv_file, index=False)


# JSON functions

def load_json(json_files: list) -> dict:
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


def dump_json(data: dict, json_file: str) -> None:
    create_path(json_file)

    with open(json_file, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# DATA HELPER functions

def date2string(string: str, reverse: bool = False) -> str:
    # Convert little-endian + dot separator to big-endian + hyphen separator
    formats = ['%d.%m.%Y', '%Y-%m-%d']

    # .. unless told otherwise
    if reverse: formats.reverse()

    try:
        return datetime.strptime(string, formats[0]).strftime(formats[-1])

    except ValueError:
        # Give back unprocessed string if things go south
        return string


def number2string(string: str) -> str:
    # Convert to string & clear whitespaces
    string = str(string).strip()

    # Take care of thousands separator, as in '1.234,56'
    if '.' in string and ',' in string:
        string = string.replace('.', '')

    string = float(string.replace(',', '.'))

    return str(f'{string:.2f}')


# UTILITY functions

def file_glob(path: str, regex: list) -> list:
    return [join(path, file) for file in listdir(path) if compile(translate(regex), IGNORECASE).match(file)]


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
    if year is None: return sorted(file_glob(base_path, regex))

    # Valid quarter => generate months
    if quarter is not None and 1 <= int(quarter) <= 4:
        months = [month + 3 * (int(quarter) - 1) for month in [1, 2, 3]]

    # Year & months => given months for given year
    if months is not None: return sorted([join(base_path, '-'.join([str(year), str(month).zfill(2) + '.json'])) for month in months])

    # No year, no quarter, invalid quarter, no months =>
    return sorted(file_glob(base_path, str(year) + regex))


def create_path(path) -> None:
    # Determine if (future) target is appropriate data file
    if splitext(path)[1].lower() in ['.csv', '.json', '.pdf', 'png']:
        path = dirname(path)

    if not exists(path):
        try:
            makedirs(path)

        # Guard against race condition
        except OSError:
            pass


def dedupe(duped_data, encoding='utf-8') -> list:
    codes = set()
    deduped_data = []

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
