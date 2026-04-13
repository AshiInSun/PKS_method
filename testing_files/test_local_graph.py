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
toy_file = os.path.join(os.path.dirname(__file__), 'data', 'ucidata-zachary', 'out.ucidata-zachary')
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
mc.init_tchain_undirected()
edge_to_swap, permutation, e_idx = mc.find_swap(2)
goal_edges = []
checks_passed = False
set_3chain = True

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

        if set_3chain:
            local_graph = mc.create_partial_local_graph(edges, 2)
            mc.perform_local_swap(local_graph, edge_to_swap, permutation)
            delta = mc.delta_local_3path(local_graph, edge_to_swap, permutation)
            if delta != 0:
                return False
    return True

while not checks_passed:
    edge_to_swap, permutation, e_idx = mc.find_swap(2)
    checks_passed = check_swap_validity(edge_to_swap, permutation)


# Define edges to use for local graph
edges_to_include = edge_to_swap
print(f"\n=== Creating Local Graph with edges: {edges_to_include} ===")

# Create partial local graph
local_g = mc.create_partial_local_graph(edges_to_include, 2)
init_count_3chain, set3chain = count_paths_length_3(local_g)


print(f"\nLocal Graph Stats:")
print(f"Nodes: {local_g.N}")
print(f"Edges: {local_g.M}")
print(f"\nLocal Graph Adjacency List:")
for node in sorted(local_g.neighbors.keys()):
    print(f"  {node}: {sorted(local_g.neighbors[node])}")

print(f"\nLocal Graph Unique Edges:")
for edge in sorted(local_g.unique_edges):
    print(f"  {edge}")

print(f"\nLocal Graph Unique Edges:")
for edge in sorted(local_g.edges):
    print(f"  {edge}")

print(f"\nLocal Graph 3chain:{init_count_3chain}")


print(f"\n=== Performing one edge swap in local graph ===")

before_swap_graph = local_g.copy()
mc.perform_local_swap(local_g, edge_to_swap, permutation)

print(f"\nAfter Swap Graph Stats:")
print(f"Nodes: {local_g.N}")
print(f"Edges: {local_g.M}")
print(f"\nAfter Swap Graph Adjacency List:")
for node in sorted(local_g.neighbors.keys()):
    print(f"  {node}: {sorted(local_g.neighbors[node])}")

print(f"\nLocal Graph Unique Edges:")
for edge in sorted(local_g.unique_edges):
    print(f"  {edge}")

print(f"\nLocal Graph Edges:")
for edge in sorted(local_g.edges):
    print(f"  {edge}")

new_count_3chain, set3chain = count_paths_length_3(local_g)
delta = mc.delta_local_3path(local_g, edge_to_swap, permutation)
print(f"\nOld 3 chain count: {init_count_3chain}")
print(f"\nNew 3 chain count: {new_count_3chain}")
print(f"\nestimated Delta in number of 3path after swap (computed): {delta}")
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
for edge in mygraph.edges:
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
for edge in before_swap_graph.edges:
    G_local.add_edge(edge[0], edge[1])

# After swap graph
ax3 = axes[2]
G_after = nx.Graph()
G_after.add_nodes_from(sorted(local_g.neighbors.keys()))

for edge in local_g.unique_edges:
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

