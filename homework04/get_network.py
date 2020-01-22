import time
from typing import Optional
import config
import igraph
import requests
import numpy as np
from igraph import Graph, plot
from api import get_friends, get_names


def get_network(all_ids, as_edgelist=True):
    """ Building a friend graph for an arbitrary list of users """
    sort_ids = []
    for ids in all_ids:
        try:
            id_friends = get_friends(ids, 'first_name')['response']['items']
        except KeyError:
            continue
        for friend in id_friends:
            if friend['id'] in all_ids:
                sort_ids.append(ids)
                break
  
    vertices = list(range(len(sort_ids)))
    edges = set()
    for i in range(len(sort_ids)):
        try:
            id_friends = get_friends(sort_ids[i], 'first_name')['response']['items']
        except KeyError:
            continue
        for user in id_friends:
            if user['id'] in sort_ids:
                j = sort_ids.index(user['id'])
                edges.add((i, j))
    edges = list(edges)
    if as_edgelist:
        return vertices, edges
    else:
        matrix = [[0 for _ in vertices] for _ in vertices]
        for edge in edges:
            matrix[edge[0]][edge[1]] = 1
        return matrix


def plot_graph(vertices, edges):
    # Создание графа
    g = Graph(vertex_attrs={"label":vertices},
              edges=edges, directed=False)


    # Задаем стиль отображения графа
    N = len(vertices)
    visual_style = {}
    visual_style["layout"] = g.layout_fruchterman_reingold(
        maxiter=1000,
        area=N ** 3,
        repulserad=N ** 3)
    # Отрисовываем граф
    g.simplify(multiple=True, loops=True)
    plot(g, **visual_style)


if __name__ == '__main__':
    fr = get_friends(552537887, 'first_name')
    friends1 = [item['id'] for item in fr['response']['items']]
    vert, edg = get_network(friends1)
    plot_graph(vert, edg)
