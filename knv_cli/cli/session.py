from os.path import join

import pendulum

from ..utils import dump_json


class Session:
    def __init__(self, session: dict) -> None:
        self.session = session


    # CORE methods

    def has(self, data) -> bool:
        return data.identifier() in self.session


    def save(self, path: str) -> None:
        dump_json(self.session, join(path, pendulum.now().strftime('%Y-%m-%d_%I-%M-%S') + '.json'))
