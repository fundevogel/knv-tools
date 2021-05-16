# ~*~ coding=utf-8 ~*~


from operator import itemgetter

from matplotlib import pyplot, rcParams
from pandas import DataFrame


# RANKING functions

def get_ranking(orders: list) -> list:
    data = {}

    # Sum up number of sales
    for order in orders:
        for isbn, product in order['Bestellung'].items():
            # Skip total order cost
            if isbn == 'Summe':
                continue

            if isbn not in data:
                data[isbn] = product['Anzahl']

            else:
                data[isbn] = data[isbn] + product['Anzahl']

    ranking = []

    for isbn, quantity in data.items():
        item = {}

        item['ISBN'] = isbn
        item['Anzahl'] = quantity

        ranking.append(item)

    # Sort sales by quantity & in descending order
    ranking.sort(key=itemgetter('Anzahl'), reverse=True)

    return ranking


def get_ranking_chart(ranking, limit=1, kind='barh'):
    # Update ranking to only include entries above set limit
    ranking = [{'Anzahl': item['Anzahl'], 'ISBN': item['ISBN']} for item in ranking if item['Anzahl'] >= int(limit)]
    df = DataFrame(ranking, index=[item['ISBN'] for item in ranking])

    # Rotate & center x-axis labels
    pyplot.xticks(rotation=45, horizontalalignment='center')

    # Make graph 'just fit' image dimensions
    rcParams.update({'figure.autolayout': True})

    return df.plot(kind=kind).get_figure()
