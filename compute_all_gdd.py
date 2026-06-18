"""
compute_all_gdd.py
Calcule les orbites par nœud (via orca) pour tous les clusters trouvés dans out/,
et sauvegarde le résultat dans out/{nom}_cluster/out_{id}/{id}_gdd.json.

Usage : python compute_all_gdd.py [--force]
  --force : recalcule même si le JSON existe déjà
"""

import argparse
import json
import os
import sys

import networkx as nx
import numpy as np
from orca import orca_nodes

MODELS = {"gen_jdm", "gen_ftr1", "gen_no_constraint"}
BASE_OUT = "out"


def compute_node_orbits(G: nx.Graph) -> list:
    edges = np.array(list(G.edges()), dtype=np.int32)
    return orca_nodes(edges, graphlet_size=5).tolist()


def process_cluster(cluster_dir: str, cluster_id: str, force: bool) -> None:
    out_path = os.path.join(cluster_dir, f"{cluster_id}_gdd.json")
    if os.path.exists(out_path) and not force:
        print(f"  [skip] {out_path} existe déjà")
        return

    result = {}

    # Graphe original
    gml_path = os.path.join(cluster_dir, f"{cluster_id}.gml")
    if not os.path.exists(gml_path):
        print(f"  [warn] GML introuvable : {gml_path}", file=sys.stderr)
        return
    G_orig = nx.read_gml(gml_path, label="id")
    result["original"] = compute_node_orbits(G_orig)

    # Modèles sélectionnés
    for gen_name in sorted(os.listdir(cluster_dir)):
        if gen_name not in MODELS:
            continue
        gen_path = os.path.join(cluster_dir, gen_name)
        if not os.path.isdir(gen_path):
            continue
        for fname in sorted(os.listdir(gen_path)):
            if not fname.startswith("g"):
                continue
            fpath = os.path.join(gen_path, fname)
            try:
                G = nx.read_edgelist(fpath)
                key = f"{gen_name}/{fname}"
                result[key] = compute_node_orbits(G)
            except Exception as e:
                print(f"  [warn] {fpath} : {e}", file=sys.stderr)

    with open(out_path, "w") as f:
        json.dump(result, f)
    print(f"  [done] {out_path}  ({len(result)} entrées)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="Recalcule même si le JSON existe déjà")
    args = parser.parse_args()

    if not os.path.isdir(BASE_OUT):
        print(f"Dossier '{BASE_OUT}' introuvable.", file=sys.stderr)
        sys.exit(1)

    for cluster_type in sorted(os.listdir(BASE_OUT)):           # stars_cluster, ...
        cluster_type_path = os.path.join(BASE_OUT, cluster_type)
        if not os.path.isdir(cluster_type_path) or not cluster_type.endswith("_cluster"):
            continue
        for entry in sorted(os.listdir(cluster_type_path)):     # out_{id}
            if not entry.startswith("out_"):
                continue
            cluster_id = entry[len("out_"):]
            cluster_dir = os.path.join(cluster_type_path, entry)
            print(f"{cluster_type}/{entry}")
            process_cluster(cluster_dir, cluster_id, args.force)


if __name__ == "__main__":
    main()