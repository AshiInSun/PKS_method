import matplotlib.pyplot as plt
import networkx as nx

from kedgeswap.Graph import Graph


def count_paths_length_3(graph):
    count = 0
    set_chains = set()

    for u in graph.neighbors:
        nu = graph.neighbors[u]

        for v in nu:
            nv = graph.neighbors[v]
            for w in nv:
                if w == u:
                    continue  # éviter les boucles
                nw = graph.neighbors[w]
                for x in nw:
                    if x == v or u >= x:
                        continue  # éviter les boucles et les chaines symétriques
                    chain = (u, v, w, x)
                    set_chains.add(chain)
                    count += 1
    return count, set_chains



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

    input_file = "data/ucidata-zachary/toyexample.out"
    g.read_ssv(input_file)

    print("Nombre de sommets :", g.N)
    print("Nombre d'arêtes   :", g.M)

    paths, chains = count_paths_length_3(g)

    print("Nombre de chaînes de taille 3 :", len(chains))
    chains = list(chains)
    chains.sort()

    for chain in chains:
        print(chain)

    draw_graph(g)


if __name__ == "__main__":
    main()