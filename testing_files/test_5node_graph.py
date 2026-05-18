import os
import networkx as nx
from networkx.generators.atlas import graph_atlas_g
import matplotlib.pyplot as plt

def has_disjoint_edge_pair(G):
    edges = list(G.edges())

    for i in range(len(edges)):
        u1, v1 = edges[i]

        for j in range(i + 1, len(edges)):
            u2, v2 = edges[j]

            if len({u1, v1, u2, v2}) == 4:
                return True

    return False
# ----------------------------
# génération + filtre
# ----------------------------
def generate_unlabeled_graphs(n=5, min_edges=2):
    atlas = graph_atlas_g()

    graphs = []

    for G in atlas:
        if G.number_of_nodes() == n and has_disjoint_edge_pair(G):
            graphs.append(G)

    return graphs


# ----------------------------
# export SSV
# ----------------------------
def export_ssv(graphs, folder="fivenode_graphs"):
    os.makedirs(folder, exist_ok=True)

    for i, G in enumerate(graphs):
        path = os.path.join(folder, f"fg{i}.ssv")

        with open(path, "w") as f:
            for u, v in G.edges():
                f.write(f"{u} {v}\n")


# ----------------------------
# plot
# ----------------------------
def plot_graphs(graph_list, n=10):
    n = min(n, len(graph_list))
    cols = 5
    rows = (n + cols - 1) // cols

    plt.figure(figsize=(3 * cols, 3 * rows))

    for i in range(n):
        ax = plt.subplot(rows, cols, i + 1)
        nx.draw(graph_list[i], with_labels=True, node_size=400)
        ax.set_title(f"G{i}")
        ax.axis("off")

    plt.tight_layout()
    plt.show()


# ----------------------------
# RUN
# ----------------------------
graphs = generate_unlabeled_graphs(n=5, min_edges=2)

print("Number of graphs (n=5, |E|≥2):", len(graphs))

export_ssv(graphs)

plot_graphs(graphs, n=10)