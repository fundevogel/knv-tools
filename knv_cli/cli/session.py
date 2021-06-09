from os.path import join

from ..utils import dump_json


class Session:
    def __init__(self, session: dict) -> None:
        self.session = session


    # CORE methods

    def has(self, data) -> bool:
        return data.identifier() in self.session
