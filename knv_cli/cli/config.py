
from configparser import SafeConfigParser
from os import getcwd
from os.path import isfile, join

from xdg import xdg_config_home, xdg_data_home


class Config(object):
    def __init__(self):
        # Provide sensible defaults
        config = SafeConfigParser()
        config['DEFAULT'] = {
            'vkn': '12345',
            'verbose': 'off',
        }

        config['directories'] = {
            'data_dir': join(xdg_data_home(), 'knv-cli'),
            'import_dir': './imports',
            'export_dir': './dist',
        }

        # Load config provided by user
        config_file = join(xdg_config_home(), 'knv-cli', 'config')

        if isfile(config_file):
            config.read(config_file)

        # Apply resulting config
        self.config = config

        for section in config.sections():
            for option in config[section]:
                setattr(self, option, self.get(section, option))

        # Expose useful directories ..
        # (1) .. when establishing the database
        self.info_dir = join(self.data_dir, 'src', 'infos')
        self.invoice_dir = join(self.data_dir, 'src', 'invoices')
        self.order_dir = join(self.data_dir, 'src', 'orders')
        self.payment_dir = join(self.data_dir, 'src', 'payments')
        self.cache_dir = join(self.data_dir, 'webservice')

        # (2) .. when merging data sources
        self.database_dir = join(self.data_dir, 'db')

        # (3) .. when in an accounting session
        self.session_dir = join(self.payment_dir, 'session')

        # (4) .. when generating data
        self.contacts_dir = join(self.export_dir, 'contacts')
        self.matches_dir = join(self.export_dir, 'matches')
        self.rankings_dir = join(self.export_dir, 'rankings')

        # Load blocklist if one exists
        self.blocklist = []

        block_file = join(getcwd(), 'blocklist.txt')

        if isfile(block_file):
            with open(block_file, 'r') as file:
                self.blocklist = file.read().splitlines()


    def get(self, section: str, option: str):
        booleans = ['verbose']

        if self.config.has_option(section, option):
            if option in booleans:
                return self.config.getboolean(section, option)

            return self.config.get(section, option)

        if option in self.config['DEFAULT']:
            return self.config.get('DEFAULT', option)

        raise Exception
