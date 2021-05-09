# ~*~ coding=utf-8 ~*~


from configparser import SafeConfigParser
from os.path import isfile, join, realpath

from xdg import xdg_config_home


class Config(object):
    def __init__(self):
        # Provide sensible defaults
        config = SafeConfigParser()
        config['DEFAULT'] = {
            'data_dir': './src',
            'verbose': 'off'
        }

        config['import'] = {
            'import_dir': './imports',
            'payment_regex': 'Download*.CSV',
            'order_regex': 'Orders_*.csv',
            'info_regex': 'OrdersInfo_*.csv',
        }

        config['export'] = {
            'export_dir': './dist',
            'invoice_file': 'invoices.pdf',
        }

        # Load config provided by user
        config_file = realpath(join(xdg_config_home(), 'knv-cli' 'config.ini'))

        if isfile(config_file):
            config.read(config_file)

        # Apply resulting config
        for section in config.sections():
            for option in config[section]:
                setattr(self, option, config.get(section, option))

        # Expose useful directories ..
        # (1) .. when establishing the database
        self.payment_dir = join(self.data_dir, 'payments')
        self.order_dir = join(self.data_dir, 'orders')
        self.info_dir = join(self.data_dir, 'infos')
        self.invoice_dir = join(self.data_dir, 'invoices')

        # (2) .. when generating data
        self.matches_dir = join(self.export_dir, 'matches')
        self.rankings_dir = join(self.export_dir, 'rankings')
        self.contacts_dir = join(self.export_dir, 'contacts')

    def get(self, section: str, option: str):
        booleans = ['verbose']

        if self.config.has_option(section, option):
            if option in booleans:
                return self.config.getboolean(section, option)

            return self.config.get(section, option)

        if option in self.config['DEFAULT']:
            return self.config.get('DEFAULT', option)

        raise Exception
