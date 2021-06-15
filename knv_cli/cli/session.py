from os.path import join

from ..utils import load_json


class Session:
    # PROPS

    providers = [
        'invoices',
        'paypal',
        'volksbank',
    ]


    def __init__(self, session_files: dict = {}) -> None:
        # Build session from previously saved session data
        data = {k: load_json(v) for k, v in session_files.items() if session_files}

        # Initialize blank session if previous data is (at least partially) unavailable
        for provider in self.providers:
            if provider not in data: data[provider] = {}

        self.session = data


    # CORE methods

    def has(self, data: dict, identifier: str) -> bool:
        return data.identifier() in self.session[identifier]
