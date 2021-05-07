#! /usr/bin/python
# ~*~ coding=utf-8 ~*~


import json
from os.path import join
# from io import StringIO, BytesIO

from pandas import concat, read_csv

from lib.utilities import create_path, dedupe, group_data


# CSV tasks

# TODO: Merge with CSV stream loader
def load_csv(csv_files, encoding='iso-8859-1', delimiter=';') -> list:
    try:
        df = concat(map(lambda file: read_csv(file, sep=delimiter, encoding=encoding, low_memory=False), csv_files))

    except ValueError:
        return []

    return df.to_dict('records')


# def load_csv_from_stream(csv_files, encoding='iso-8859-1', delimiter=';') -> list:
#     data = []

#     for csv_file in csv_files:
#         try:
#             text_stream = StringIO((csv_file.stream.read()).decode(encoding))
#             data += read_csv(text_stream, sep=delimiter).to_dict('records')

#         except FileNotFoundError:
#             continue

#     return data


# JSON handlers

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
    with open(json_file, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
