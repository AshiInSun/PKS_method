#!/usr/bin/env python
"""
Test local graph creation with toyexample.out
"""

import os
import sys
import networkx as nx
import matplotlib.pyplot as plt
from numpy.random import permutation

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain

# Load toyexample.out
toy_file = os.path.join(os.path.dirname(__file__), 'data', 'ucidata-zachary', 'toyexample.out')
print(f"Loading graph from: {toy_file}")

# Create undirected graph
mygraph = Graph(directed=False)
mygraph.read_ssv(toy_file)

print(f"\n=== Original Graph ===")
print(f"Nodes: {mygraph.N}")
print(f"Edges: {mygraph.M}")
print(f"\nAdjacency List:")
for node in sorted(mygraph.neighbors.keys()):
    print(f"  {node}: {sorted(mygraph.neighbors[node])}")

print(f"\nUnique Edges:")
for edge in sorted(mygraph.unique_edges):
    print(f"  {edge}")

# Create MarkovChain to access local graph methods
mc = MarkovChain(mygraph, 10, 2, False)
edge_to_swap, permutation, e_idx = mc.find_swap(2)
goal_edges = []
checks_passed = False
mc.count_triangles()

def check_swap_validity(edges, permutations):
    for ((u, v), (x, y)) in zip(edges, permutations):
        # goal edge is the result of permutation between (u,v) and (x,y)
        if mygraph.directed:
            goal_edge = (u, y)
        else:
            goal_edge = (u, y) if u < y else (y, u)
        goal_edges.append(goal_edge)

        # avoid loops
        if u == y:
            return False

        # avoid multiple edges
        if goal_edge in mygraph.edges:
            return False
    return True

while not checks_passed:
    edge_to_swap, permutation, e_idx = mc.find_swap(2)
    checks_passed = check_swap_validity(edge_to_swap, permutation)


# Define edges to use for local graph
edges_to_include = edge_to_swap
print(f"\n=== Creating Local Graph with edges: {edges_to_include} ===")

# Create partial local graph
local_graph, dico = mc.create_partial_local_graph(edges_to_include)

tempmc = MarkovChain(local_graph)
tempmc.count_triangles()
initial_count_triangles = len(tempmc.triangles2edges)

print(f"\nLocal Graph Stats:")
print(f"Nodes: {local_graph.N}")
print(f"Edges: {local_graph.M}")
print(f"\nLocal Graph Adjacency List:")
for node in sorted(local_graph.neighbors.keys()):
    print(f"  {node}: {sorted(local_graph.neighbors[node])}")

print(f"\nLocal Graph Unique Edges:")
for edge in sorted(local_graph.unique_edges):
    print(f"  {edge}")

print(f"\nLocal Graph Unique Edges:")
for edge in sorted(local_graph.edges):
    print(f"  {edge}")

print(f"\nLocal Graph Triangles:")
for triangle in tempmc.triangles2edges:
    print(f"  {triangle} : {tempmc.triangles2edges[triangle]}")

print(f"\n=== Performing one edge swap in local graph ===")

before_swap_graph = local_graph.copy()
mc.perform_local_swap(local_graph, edge_to_swap, permutation, e_idx, dico)

print(f"\nAfter Swap Graph Stats:")
print(f"Nodes: {local_graph.N}")
print(f"Edges: {local_graph.M}")
print(f"\nAfter Swap Graph Adjacency List:")
for node in sorted(local_graph.neighbors.keys()):
    print(f"  {node}: {sorted(local_graph.neighbors[node])}")

print(f"\nLocal Graph Unique Edges:")
for edge in sorted(local_graph.unique_edges):
    print(f"  {edge}")

print(f"\nLocal Graph Edges:")
for edge in sorted(local_graph.edges):
    print(f"  {edge}")

tempmc.update_triangles(edge_to_swap, permutation)
new_count_triangles = len(tempmc.triangles2edges)

delta_plus, delta_moins =  mc.delta_local_triangle(local_graph, edge_to_swap, permutation)
delta = delta_plus - delta_moins
print(f"\nDelta plus (triangles created): {delta_plus}")
print(f"\nDelta moins (triangles destroyed): {delta_moins}")
# print(f"\nLocal Graph Triangles:")
# for triangle in tempmc.triangles2edges:
#     print(f"  {triangle} : {tempmc.triangles2edges[triangle]}")
#
# print(f"\nchecks passed for swap: {checks_passed}")
#
# print(f"\nnumber of triangles before swap: {initial_count_triangles}")
# print(f"\nnumber of triangles after swap: {new_count_triangles}")
# print(f"\nDELTA in number of triangles after swap: {delta}")

# ===== VISUALIZATION =====
fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# Original graph
ax1 = axes[0]
G_original = nx.Graph()
G_original.add_nodes_from(range(mygraph.N))
for edge in mygraph.unique_edges:
    G_original.add_edge(edge[0], edge[1])

pos_original = nx.spring_layout(G_original, seed=42)
nx.draw_networkx_nodes(G_original, pos_original, node_color='lightblue', node_size=500, ax=ax1)
nx.draw_networkx_labels(G_original, pos_original, font_size=10, ax=ax1)
nx.draw_networkx_edges(G_original, pos_original, ax=ax1)

# Highlight the edges used for local graph
edge_list_to_include = edges_to_include
for edge in edge_list_to_include:
    if G_original.has_edge(edge[0], edge[1]):
        nx.draw_networkx_edges(G_original, pos_original, [(edge[0], edge[1])],
                              edge_color='red', width=2, ax=ax1)

ax1.set_title("Original Graph (red edges are in local graph)")
ax1.axis('off')

# Local graph
ax2 = axes[1]
G_local = nx.Graph()
G_local.add_nodes_from(sorted(before_swap_graph.neighbors.keys()))
for edge in before_swap_graph.unique_edges:
    G_local.add_edge(edge[0], edge[1])

# After swap graph
ax3 = axes[2]
G_after = nx.Graph()
G_after.add_nodes_from(sorted(local_graph.neighbors.keys()))

for edge in local_graph.unique_edges:
    G_after.add_edge(edge[0], edge[1])

if G_after.number_of_nodes() > 0:
    pos_after = nx.spring_layout(G_after, seed=42)
    nx.draw_networkx_nodes(G_after, pos_after, node_color='lightcoral', node_size=500, ax=ax3)
    nx.draw_networkx_labels(G_after, pos_after, font_size=10, ax=ax3)
    nx.draw_networkx_edges(G_after, pos_after, ax=ax3)

    ax3.set_title("Local Graph After Swap")
    ax3.axis('off')

# Use a better layout for visualization
if G_local.number_of_nodes() > 0:
    pos_local = nx.spring_layout(G_local, seed=42)
    nx.draw_networkx_nodes(G_local, pos_local, node_color='lightgreen', node_size=500, ax=ax2)
    nx.draw_networkx_labels(G_local, pos_local, font_size=10, ax=ax2)
    nx.draw_networkx_edges(G_local, pos_local, ax=ax2)
    ax2.set_title(f"Local Graph (nodes in neighborhood of {edges_to_include} and {permutation})")
    ax2.axis('off')

plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), 'local_graph_visualization.png'), dpi=100)
print(f"\n✓ Graph saved to local_graph_visualization.png")
plt.show()

print("\n=== Test Complete ===")

