import json

from abc import ABCMeta, abstractmethod
from hashlib import md5

from pandas import concat, read_csv


class BaseClass(metaclass=ABCMeta):
    # Props
    data = None
    identifier = None

    # CSV options
    encoding='iso-8859-1'
    delimiter=';'
    skiprows=None


    def load_csv(self, csv_files) -> None:
        try:
            df = concat(map(lambda file: read_csv(
                file,
                sep=self.delimiter,
                encoding=self.encoding,
                low_memory=False,
                skiprows=self.skiprows
            ), csv_files))

        except ValueError:
            return []

        self.load_data(self.process_data(df.to_dict('records')))


    def load_json(self, json_files) -> None:
        data = []

        for json_file in json_files:
            try:
                with open(json_file, 'r') as file:
                    data.extend(json.load(file))

            except json.decoder.JSONDecodeError:
                raise Exception

            except FileNotFoundError:
                pass

        self.load_data(data)


    def load_data(self, data: list) -> None:
        if self.data:
            # Permit only unique entries, either by ..
            if self.identifier is not None:
                # .. (1) using a unique identifier
                codes = {item[self.identifier] for item in self.data}

                # Merge only data not already in database
                for item in data:
                    if item[self.identifier] not in codes:
                        codes.add(item[self.identifier])
                        self.data.append(item)

            else:
                # (2) .. hashing the whole item
                codes = set()

                for item in data:
                    hash_digest = md5(str(item).encode('utf-8')).hexdigest()

                    if hash_digest not in codes:
                        codes.add(hash_digest)
                        self.data.append(item)

        # .. otherwise, start from scratch
        else:
            self.data = data


    @abstractmethod
    def process_data(self, data: list) -> list:
        pass
