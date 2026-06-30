import networkx as nx
import numpy as np
from orca import orca_nodes
import json
import os

BASE = "out/stars_cluster/out_0305fa001039c87957e4b40382da1af8"
HASH = "0305fa001039c87957e4b40382da1af8"

def compute_node_orbits(G):
    edges = np.array(list(G.edges()), dtype=np.int32)
    return orca_nodes(edges, graphlet_size=5).tolist()

result = {}

# Graphe original
gml_path = os.path.join(BASE, f"{HASH}.gml")
G_orig = nx.read_gml(gml_path, label="id")
result["original"] = compute_node_orbits(G_orig)

# Tous les g_* de chaque gen_*
for gen_dir in sorted(os.listdir(BASE)):
    gen_path = os.path.join(BASE, gen_dir)
    if not os.path.isdir(gen_path) or not gen_dir.startswith("gen_"):
        continue
    for fname in sorted(os.listdir(gen_path)):
        if not fname.startswith("g"):
            continue
        fpath = os.path.join(gen_path, fname)
        G = nx.read_edgelist(fpath)
        key = f"{gen_dir}/{fname}"
        result[key] = compute_node_orbits(G)

with open("out_temp/stars_cluster/out_0305fa001039c87957e4b40382da1af8/node_orbits_0305.json", "w") as f:
    json.dump(result, f)

print("Done:", list(result.keys())[:5], "...")