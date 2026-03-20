import os
import matplotlib.pyplot as plt
import networkx as nx

from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain

toy_file = os.path.join(
    os.path.dirname(__file__),
    'data',
    'ego_dataset',
    '4a614391ef27b94d336a410bec2aa934.gml'
)

graph = Graph(directed=False)
graph.read_gml(toy_file)

fig, axes = plt.subplots(1, 1, figsize=(20, 6))

G_original = nx.Graph()
G_original.add_nodes_from(range(graph.N))
for edge in graph.unique_edges:
    G_original.add_edge(edge[0], edge[1])

pos_original = nx.fruchterman_reingold_layout(G_original)
nx.draw_networkx_nodes(G_original, pos_original, node_size=20)
nx.draw_networkx_edges(G_original, pos_original, alpha=0.1)

plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), 'local_graph_visualization.png'), dpi=100)
print(f"\n✓ Graph saved to local_graph_visualization.png")
plt.show()
