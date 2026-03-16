import os
import matplotlib.pyplot as plt
import networkx as nx

from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain

toy_file = os.path.join(
    os.path.dirname(__file__),
    'out',
    'karateclub'
)

graph = Graph(directed=False)
graph.read_ssv(toy_file)

fig, axes = plt.subplots(1, 1, figsize=(20, 6))

G_original = nx.Graph()
G_original.add_nodes_from(range(graph.N))
for edge in graph.unique_edges:
    G_original.add_edge(edge[0], edge[1])

pos_original = nx.spring_layout(G_original, seed=42)
nx.draw_networkx_nodes(G_original, pos_original, node_color='lightblue', node_size=500)
nx.draw_networkx_labels(G_original, pos_original, font_size=10)
nx.draw_networkx_edges(G_original, pos_original)

plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), 'local_graph_visualization.png'), dpi=100)
print(f"\n✓ Graph saved to local_graph_visualization.png")
plt.show()
