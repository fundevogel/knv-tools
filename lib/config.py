# ~*~ coding=utf-8 ~*~


from configparser import SafeConfigParser
from os.path import abspath, dirname, exists, join, realpath

class Config(object):
    def __init__(self):
        # Set defaults for ..
        self.config = SafeConfigParser({
            # .. database tasks
            'import_dir'    : './imports',
            'data_dir'      : './data',
            'payment_regex' : 'Download*.CSV',
            'order_regex'   : 'Orders_*.csv',
            'info_regex'    : 'OrdersInfo_*.csv',
            'invoice_file'  : 'invoices.pdf',

            # .. inspector tasks
            'match_dir'    : 'build/matches',
            'rank_dir'     : 'build/rankings',
            'contacts_dir' : 'build/contacts',
        })


    def get(self, section: str, option: str):
        if self.config.has_option(section, option):
            return self.config.get(section, option)

        if option in self.config['DEFAULT']:
            return self.config.get('DEFAULT', option)

        raise Exception
