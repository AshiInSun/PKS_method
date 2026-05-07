#!/usr/bin/env python
"""
Figure for abstract: before/after k-edge swap preserving triangles.
Trans flag colors: edges in #5BCEFA (blue), swapped edges highlighted in #F5A9B8 (pink).
"""

import os
import sys
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain

# Load graph
toy_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out', 'out_toy', 'gen')
# Create undirected graph
mygraph = Graph(directed=False)
mygraph.read_ssv(toy_file)

# Create MarkovChain and initialize triangles
mc = MarkovChain(mygraph, 10, 2, False)
mc.count_triangles()

edge_to_swap, permutation, e_idx = mc.find_swap(2)
goal_edges = []
checks_passed = False

def check_swap_validity(edges, perm):
    goal_edges.clear()
    for ((u, v), (x, y)) in zip(edges, perm):
        goal_edge = (u, y) if u < y else (y, u)
        goal_edges.append(goal_edge)
        if u == y:
            return False
        if goal_edge in mygraph.edges:
            return False

    # Check triangles are preserved
    local_n = mc.create_local_neighboorhood(edges, 1)
    delta = 0
    delta -= mc.nb_triangle_neighboor(local_n, edges)
    mc.perform_neighboor_swap(local_n, edges, perm)
    delta += mc.nb_triangle_neighboor(local_n, goal_edges)
    return delta == 0

while not checks_passed:
    edge_to_swap, permutation, e_idx = mc.find_swap(2)
    checks_passed = check_swap_validity(edge_to_swap, permutation)

# Build before graph
G_before = nx.Graph()
for node in mygraph.neighbors:
    G_before.add_node(node)
for edge in mygraph.unique_edges:
    G_before.add_edge(edge[0], edge[1])

# Build after graph (deep copy + perform swap)
import copy
mc2 = copy.deepcopy(mc)
mc2.perform_swap(edge_to_swap, permutation, e_idx)
G_after = nx.Graph()
for node in mc2.graph.neighbors:
    G_after.add_node(node)
for edge in mc2.graph.unique_edges:
    G_after.add_edge(edge[0], edge[1])

# Canonical swapped edges
swapped_before = set((min(u,v), max(u,v)) for (u,v) in edge_to_swap)
swapped_after  = set((min(u,y), max(u,y)) for (u,v),(x,y) in zip(edge_to_swap, permutation))

# Triangles
def get_triangles(G):
    tris = set()
    for n in G.nodes():
        nb = list(G.neighbors(n))
        for i in range(len(nb)):
            for j in range(i+1, len(nb)):
                if G.has_edge(nb[i], nb[j]):
                    tris.add(tuple(sorted([n, nb[i], nb[j]])))
    return tris

tris_before = get_triangles(G_before)
tris_after  = get_triangles(G_after)

# Shared layout
pos = nx.spring_layout(G_before, seed=42)

# ── Colors ────────────────────────────────────────────────────────────────────
TRANS_BLUE  = "#5BCEFA"
TRANS_PINK  = "#E8899B"
BG          = "#FFFFFF"
NODE_C      = "#FFFFFF"
NODE_EC     = "#5BCEFA"
TRI_FILL    = "#5BCEFA"

def draw(ax, G, pos, highlighted_edges, triangles):
    ax.set_facecolor(BG)

    # Triangle fills
    for tri in triangles:
        pts = np.array([pos[n] for n in tri])
        ax.add_patch(plt.Polygon(pts, closed=True,
                                 facecolor=TRI_FILL, alpha=0.13, zorder=1, lw=0))
        ax.add_patch(plt.Polygon(pts, closed=True, fill=False,
                                 edgecolor=TRI_FILL, alpha=0.35, lw=0.8,
                                 linestyle='--', zorder=2))

        # Normal edges
        normal = [(u, v) for u, v in G.edges()
                  if (min(u, v), max(u, v)) not in highlighted_edges]
        nx.draw_networkx_edges(G, pos, edgelist=normal,
                               edge_color=TRANS_BLUE, width=1.4, alpha=0.8, ax=ax)

        # Highlighted edges (rose, sous les noeuds mais au-dessus du reste)
        hl = [(u, v) for u, v in G.edges()
              if (min(u, v), max(u, v)) in highlighted_edges]
        for u, v in hl:
            ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                    color=TRANS_PINK, linewidth=2.5,
                    solid_capstyle='round', zorder=5)

        # Nodes (zorder=6, par-dessus tout)
        for node in G.nodes():
            x, y = pos[node]
            ax.scatter(x, y, s=150, color=NODE_C, edgecolors=NODE_EC,
                       linewidths=1.5, zorder=6)

        ax.axis('off')

    ax.axis('off')
# ── Figure ─────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6.5), facecolor=BG)
fig.patch.set_facecolor(BG)

draw(axes[0], G_before, pos, swapped_before, tris_before)
draw(axes[1], G_after,  pos, swapped_after,  tris_after)

plt.tight_layout(pad=1.0)
plt.savefig(os.path.join(os.path.dirname(__file__), 'figure_abstract.png'),
            dpi=260, bbox_inches='tight', facecolor=BG, edgecolor='none')
print("✓ Saved to figure_abstract.png")
plt.show()