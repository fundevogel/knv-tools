from .algorithms.contacts import get_contacts
from .algorithms.matching import Matching
from .algorithms.ranking import get_ranking
from .processors.paypal import process_payments
from .processors.shopkonfigurator import process_orders, process_infos
from .utils import dedupe, group_data

__all__ = [
    # Operations
    'Matching',
    'get_ranking',
    'get_contacts',

    # Processors
    'process_payments',
    'process_orders',
    'process_infos',

    # Utilities
    'dedupe',
    'group_data'
]
