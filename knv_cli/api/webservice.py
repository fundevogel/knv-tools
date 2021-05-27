# ~*~ coding=utf-8 ~*~


import xml.etree.ElementTree as etree

from isbnlib import clean as clean_isbn

import zeep

from .cache import Cache
from .ola import Ola


BASE_URL = 'http://ws.pcbis.de/knv-2.0/services/KNVWebService?wsdl'


class Webservice:
    # Props
    session = None
    offline = False


    def __init__(self, credentials: dict = None, cache_dir = None) -> None:
        # Fire up SOAP client
        self.client = zeep.Client(wsdl=BASE_URL).service

        # Determine offline mode
        if credentials is None:
            self.offline = True

        else:
            # Start new session
            self.login(credentials)

        # Initialize cache
        self.cache = Cache(cache_dir)


    def __del__(self) -> None:
        if self.session is not None:
            self.logout()


    # AUTHENTICATION methods

    def login(self, credentials: dict) -> str:
        try:
            self.session = self.client.WSCall(LoginInfo=credentials)['SessionID']

        except zeep.exceptions.Fault as error:
            self.offline = True


    def logout(self) -> None:
        self.client.WSCall(self.session, Logout=True)


    # API methods

    def version(self, version: str = '') -> str:
        return self.client.CheckVersion(version)


    def fetch(self, isbn: str, force_refresh: bool = False) -> dict:
        # Clean ISBN input
        isbn = clean_isbn(isbn)

        # Cater for offline mode where ..
        # (1) .. cache cannot be refreshed
        # (2) .. query cannot be sent
        if self.offline:
            data = {}

            if self.cache.contains(isbn):
                data = self.cache.fetch(isbn)

            # (3) .. resulting in cached data or none at all
            return data

        # Cater for online mode where cache ..
        # (1) .. has to be refreshed if requested
        # (2) .. has to be created if absent
        if not self.cache.contains(isbn) or force_refresh:
            self.cache.save(isbn, self.query(isbn))

        return self.cache.fetch(isbn)


    def query(self, isbn: str) -> dict:
        # Start new database query
        Suchen = {
            # Search across all databases
            'Datenbank': [
                'KNV',
                'KNVBG',
                'BakerTaylor',
                'Gardners',
            ],
            'Suche': {
                # Simple search suffices for querying single ISBN
                'SimpleTerm': {
                    'Suchfeld': 'ISBN',
                    'Suchwert': isbn,
                    'Suchart': 'Genau'
                }
            }
        }

        # Read query response & return first data point
        Lesen = {
            'SatzVon': 1,
            'SatzBis': 1,
            'Format': 'KNVXMLLangText',
        }

        # For getting started with KNV's (surprisingly well documented) german API,
        # see http://www.knv-zeitfracht.de/wp-content/uploads/2020/07/Webservice_2.0.pdf
        response = self.client.WSCall(self.session, Suchen=Suchen, Lesen=Lesen)

        # Process query response by ..
        if response.Daten is not None:
            # (1) .. fetching database record
            result = response.Daten.Datensaetze.Record[0].ArtikelDaten

            # (2) .. converting XML to dictionary
            return self.xml2data(result)

        return {}


    def ola(self, isbn: str, quantity: int = 1):
        isbn = clean_isbn(isbn)

        # TODO: Check cache for OLA request
        request = {
            'Art': 'Abfrage',
            'OLAItem': {
                'Bestellnummer': {
                    'ISBN': isbn,
                },
                'Menge': quantity,
            },
        }

        response = self.client.WSCall(self.session, OLA=request)

        return Ola(response)


    # HELPER methods

    def xml2data(self, xml_string: str):
        # Prepare raw XML response
        xml_root = etree.fromstring(xml_string.replace('&', '&amp;'))

        data = {}

        # Convert XML to dictionary
        for node in xml_root[0]:
            # All elements with same tag name ..
            if len(xml_root[0].findall(node.tag)) > 1:
                # .. are combined into lists holding their content
                if node.tag not in data:
                    data[node.tag] = []

                data[node.tag].append(node.text.strip())

            else:
                # .. otherwise proceed as usual
                data[node.tag] = node.text.strip()

        return data
