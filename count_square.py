import matplotlib.pyplot as plt
import networkx as nx
from itertools import combinations

from kedgeswap.Graph import Graph

def canonical_square(u, v, x, w):
    # cycle u-v-x-w-u
    nodes = [u, v, x, w]
    start = min(nodes)
    idx = nodes.index(start)
    # deux sens possibles depuis start
    forward = (nodes[idx], nodes[(idx+1)%4], nodes[(idx+2)%4], nodes[(idx+3)%4])
    backward = (nodes[idx], nodes[(idx-1)%4], nodes[(idx-2)%4], nodes[(idx-3)%4])
    return min(forward, backward)

def count_4cycle(graph):
    count = 0
    set_square = set()

    for u in graph.neighbors:
        nu = graph.neighbors[u]
        paires = list(combinations(nu, 2))
        for v, w in paires:
            inter = set(graph.neighbors[v]) & set(graph.neighbors[w])
            for x in inter:
                if x <= u:
                    continue
                else:
                    sq = canonical_square(u, v, x, w)
                    if sq in set_square:
                        continue
                    set_square.add(sq)
                    count += 1
                # les arêtes du cycle sont sq[0]-sq[1], sq[1]-sq[2], sq[2]-sq[3], sq[3]-sq[0]

    return count, set_square



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

    input_file = "data/ucidata-zachary/out.ucidata-zachary"
    g.read_ssv(input_file)

    print("Nombre de sommets :", g.N)
    print("Nombre d'arêtes   :", g.M)

    paths, chains = count_4cycle(g)
    print("Nombre de chaînes de taille 3 :", paths)
    print("Nombre de chaînes de taille 3 :", len(chains))
    chains = list(chains)
    chains.sort()

    for chain in chains:
        print(chain)

    draw_graph(g)
    print("Nombre de chaînes de taille 3 :", len(chains))


if __name__ == "__main__":
    main()