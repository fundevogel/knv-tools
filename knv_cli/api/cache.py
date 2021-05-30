
from glob import glob
from os import getcwd, remove
from os.path import basename, exists, join

from ..utils import _load_json, dump_json


class Cache:
    # Props
    cache_dir = cache_dir = join(getcwd(), '.cache')


    def __init__(self, cache_dir = None) -> None:
        if cache_dir is not None:
            self.cache_dir = cache_dir

        cache_files = glob(join(self.cache_dir, '*.json'))
        self.ids = [self.file2id(cache_file) for cache_file in cache_files]


    def contains(self, id: str) -> bool:
        return id in self.ids


    def fetch(self, id: str) -> dict:
        return _load_json(self.id2file(id))


    def save(self, id: str, data: dict) -> None:
        dump_json(data, self.id2file(id))
        self.ids.append(id)


    def delete(self, id: str) -> None:
        remove(self.id2file(id))
        self.ids.remove(id)


    # HELPER methods

    def file2id(self, string: str) -> str:
        return basename(string)[:-5]


    def id2file(self, string: str) -> str:
        return join(self.cache_dir, string + '.json')
