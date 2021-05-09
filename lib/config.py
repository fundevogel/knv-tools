# ~*~ coding=utf-8 ~*~


from configparser import SafeConfigParser
from os.path import isfile, join, realpath

from xdg import xdg_config_home


class Config(object):
    def __init__(self):
        # Initialize config & provide sensible defaults
        # TODO: This should be handled waaay more nicely ..
        config = SafeConfigParser()
        config['DEFAULT'] = {
            'data_dir': './data',
            'debug': 'off'
        }

        # .. database tasks
        config['database'] = {
            'import_dir': './imports',
            'payment_regex': 'Download*.CSV',
            'order_regex': 'Orders_*.csv',
            'info_regex': 'OrdersInfo_*.csv',
        }

        # .. inspector tasks
        config['extraction'] = {
            'invoice_file': 'invoices.pdf',
            'matches_dir': './build/matches',
            'rankings_dir': './build/rankings',
            'contacts_dir': './build/contacts',
        }

        # Load config provided by user
        config_file = realpath(join(xdg_config_home(), 'knv-cli' 'config.ini'))

        if isfile(config_file):
            config.read(config_file)

        self.config = config


    def get(self, section: str, option: str):
        booleans = ['debug']

        if self.config.has_option(section, option):
            if option in booleans:
                return self.config.getboolean(section, option)

            return self.config.get(section, option)

        if option in self.config['DEFAULT']:
            return self.config.get('DEFAULT', option)

        raise Exception
