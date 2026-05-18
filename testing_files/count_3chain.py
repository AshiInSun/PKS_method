from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx

from kedgeswap.Graph import Graph

def count_f3cc(graph):
    """
    Compte les f3cc (chemins fermés de longueur 3) de la même façon que
    delta_local_3closedpath dans MarkovChain :
    pour chaque arête (u,v) : (deg(u) - 1) * (deg(v) - 1)
    """
    edges2tchains = defaultdict(set)
    tchains2edges = defaultdict(set)

    for u in graph.neighbors:
        nu = graph.neighbors[u]

        for v in nu:
            nv = graph.neighbors[v]
            for w in nv:
                if w == u:
                    continue #avoid loops
                nw = graph.neighbors[w]
                for x in nw:
                    if x == v or u > x:
                        continue
                    else:
                        if x > w and x == u:
                            continue
                        else:
                            chain = (u, v, w, x)

                            pairs = [(u, v), (v, w), (w, x)]

                            for a, b in pairs:
                                if a != b:
                                    e1 = (a, b)
                                    e2 = (b, a)

                                    edges2tchains[e1].add(chain)
                                    edges2tchains[e2].add(chain)

                                    tchains2edges[chain].add(e1)
                                    tchains2edges[chain].add(e2)

    return tchains2edges

def draw_graph(graph):
    G = nx.Graph()

    # ajouter les arêtes
    for u, v in graph.unique_edges:
        G.add_edge(u, v)

    plt.figure()
    pos = nx.spring_layout(G)  # layout automatique

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=700,
        font_size=10
    )

    plt.title("Visualisation du graphe")
    plt.show()


def main():

    g = Graph(directed=False)

    input_file = "data/ego_dataset/a7d9793a763083b3473ca0ad027e35e7.gml"
    other = "out/out_a7d9/gen_f3ccr1/g_15"
    g.read_ssv(other)

    print("Nombre de sommets :", g.N)
    print("Nombre d'arêtes   :", g.M)

    paths = count_f3cc(g)

    f3cc = len(count_f3cc(g))
    #print("Nombre de f3cc :", f3cc)
    chains = list(paths)
    chains.sort()

    #draw_graph(g)
    print("Nombre de chaînes de taille 3 :", f3cc)


if __name__ == "__main__":
    main()