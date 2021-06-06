from operator import itemgetter

import pendulum

from matplotlib import pyplot, rcParams
from pandas import DataFrame

from ..components import Molecule


class Orders(Molecule):
    # CORE methods

    def export(self) -> list:
        data = []

        for child in self._children:
            data.append(child.export())

        return data


    # RANKING methods

    def get_ranking(self, limit: int = 1) -> list:
        data = {}

        # Sum up number of sales
        for item in [item[0] for item in [order.data['Bestellung'] for order in self._children]]:
            if item['Titel'] not in data:
                data[item['Titel']] = 0

            data[item['Titel']] = data[item['Titel']] + item['Anzahl']

        # Sort by quantity, only including items if above given limit
        return sorted([(isbn, quantity) for isbn, quantity in data.items() if quantity >= int(limit)], key=itemgetter(1), reverse=True)


    def get_ranking_chart(self, ranking, kind: str = 'barh'):
        # Load ranking into dataframe
        df = DataFrame([{'Anzahl': item[-1], 'Titel': item[0]} for item in ranking], index=[item[0] for item in ranking])

        # Rotate & center x-axis labels
        pyplot.xticks(rotation=45, horizontalalignment='center')

        # Make graph 'just fit' image dimensions
        rcParams.update({'figure.autolayout': True})

        return df.plot(kind=kind).get_figure()
