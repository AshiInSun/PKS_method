"""
Graphlet analysis pipeline:
- Reads SSV files (edge lists)
- Counts the 30 graphlets using Charbey's enumeration
- Outputs a JSON with counts per file
"""

import sys
import json
import glob
import os
from igraph import Graph as IGraph
from collections import defaultdict


class Enumerate(object):
    def __init__(self, graph, k):
        self._k = k
        self.dict_patterns = {
            '[1, 1]': 1,
            '[1, 1, 2]': 2,
            '[2, 2, 2]': 3,
            '[1, 1, 2, 2]': 4,
            '[1, 1, 1, 3]': 5,
            '[1, 2, 2, 3]': 6,
            '[2, 2, 2, 2]': 7,
            '[2, 2, 3, 3]': 8,
            '[3, 3, 3, 3]': 9,
            '[1, 1, 2, 2, 2]': 10,
            '[1, 1, 1, 1, 4]': 11,
            '[1, 1, 1, 2, 3]': 12,
            '[1, 2, 2, 2, 3]': (1, 2, (13, 17)),
            '[1, 1, 2, 3, 3]': 14,
            '[1, 1, 2, 2, 4]': 15,
            '[2, 2, 2, 2, 2]': 16,
            '[1, 2, 3, 3, 3]': 18,
            '[1, 2, 2, 3, 4]': 19,
            '[2, 2, 2, 2, 4]': 20,
            '[2, 2, 2, 3, 3]': (3, 3, (21, 22)),
            '[1, 3, 3, 3, 4]': 23,
            '[2, 2, 3, 3, 4]': 24,
            '[2, 2, 2, 4, 4]': 25,
            '[2, 3, 3, 3, 3]': 26,
            '[3, 3, 3, 3, 4]': 27,
            '[2, 3, 3, 4, 4]': 28,
            '[3, 3, 4, 4, 4]': 29,
            '[4, 4, 4, 4, 4]': 30
        }
        self.patterns_tab = []
        self._graph = graph

    def create_list_neighbors(self):
        for v in self._graph.vs:
            v['list_neighbors'] = []
        for e in self._graph.es:
            if e.source not in self._graph.vs[e.target]['list_neighbors']:
                self._graph.vs[e.target]['list_neighbors'].append(e.source)
            if e.target not in self._graph.vs[e.source]['list_neighbors']:
                self._graph.vs[e.source]['list_neighbors'].append(e.target)
        for v in self._graph.vs:
            v['list_neighbors'].sort(reverse=True)

    def degree_distribution(self, graph_sub):
        result = []
        for v in graph_sub.vs:
            result.append(v.degree())
            v['d'] = result[v.index]
        result.sort()
        return result

    def disambiguate_pattern(self, graph_sub, new_pattern):
        for v in graph_sub.vs:
            if v['d'] == new_pattern[0]:
                for n in v.neighbors():
                    if n['d'] == new_pattern[1]:
                        return new_pattern[2][0]
                return new_pattern[2][1]

    def index_pattern(self, graph_sub):
        dd = self.degree_distribution(graph_sub)
        key = str(dd)
        if key not in self.dict_patterns:
            return
        new_pattern = self.dict_patterns[key]
        if type(new_pattern) != int:
            new_pattern = self.disambiguate_pattern(graph_sub, new_pattern)
        self.patterns_tab[new_pattern - 1] += 1

    def in_neighborhood_vsub(self, list_neighbors, length_vsub):
        for n in list_neighbors:
            if self._graph.vs[n]['id_sub'] != -1 and self._graph.vs[n]['id_sub'] != length_vsub - 1:
                return True
        return False

    def add_vertex(self, graph_sub, vertex):
        vertex['id_sub'] = len(graph_sub.vs)
        graph_sub.add_vertex(name=vertex['name'], **{'id_principal': vertex.index})

    def extend_subgraph(self, graph_sub, v, vext):
        if len(graph_sub.es) > 0:
            self.index_pattern(graph_sub)
        if len(graph_sub.vs) == self._k:
            return
        while vext:
            w = vext.pop()
            vext2 = list(vext)
            self.add_vertex(graph_sub, w)
            for nei in w['list_neighbors']:
                u = self._graph.vs[nei]
                if u.index >= v.index:
                    if u['id_sub'] == -1:
                        if not self.in_neighborhood_vsub(u['list_neighbors'], len(graph_sub.vs)):
                            vext2.append(u)
                    else:
                        graph_sub.add_edge(len(graph_sub.vs) - 1, u['id_sub'])
                else:
                    break
            self.extend_subgraph(graph_sub, v, vext2)
            graph_sub.delete_vertices(w['id_sub'])
            w['id_sub'] = -1

    def characterize_with_patterns(self):
        self.create_list_neighbors()
        self.patterns_tab = 30 * [0]
        for v in self._graph.vs:
            v['id_sub'] = -1
            if 'name' not in v.attributes() or v['name'] is None:
                v['name'] = str(v.index)

        for v in self._graph.vs:
            graph_sub = IGraph.Formula()
            v['id_sub'] = 0
            graph_sub.add_vertex(name=v['name'], **{'id_principal': v.index})
            vext = []
            for nei in v['list_neighbors']:
                if nei > v.index:
                    vext.append(self._graph.vs[nei])
            if len(vext) > 0:
                self.extend_subgraph(graph_sub, v, vext)
            v['id_sub'] = -1

        return self.patterns_tab


def ssv_to_igraph(filepath):
    """Read SSV edge list and return igraph Graph"""
    edges = []
    nodes = set()
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                u, v = int(parts[0]), int(parts[1])
                if u != v:
                    edges.append((u, v))
                    nodes.add(u)
                    nodes.add(v)

    node_list = sorted(nodes)
    node_map = {n: i for i, n in enumerate(node_list)}
    remapped = [(node_map[u], node_map[v]) for u, v in edges]

    g = IGraph(n=len(node_list), edges=remapped)
    g.simplify()
    for i, v in enumerate(g.vs):
        v['name'] = str(node_list[i])
    return g


def gml_to_igraph(filepath):
    g = IGraph.Read_GML(filepath)
    g = g.as_undirected()
    g.simplify()

    for v in g.vs:
        if 'name' not in v.attributes() or v['name'] is None:
            v['name'] = str(v.index)
        else:
            v['name'] = str(v['name'])

    return g


def count_graphlets(filepath, k=5):
    if filepath.endswith('.gml'):
        g = gml_to_igraph(filepath)
    else:
        g = ssv_to_igraph(filepath)
    enum = Enumerate(g, k)
    counts = enum.characterize_with_patterns()
    return counts


def main():
    """
    Usage:
      python graphlet_analysis.py <generated_folder> [original_file.gml|.ssv]

    original_file can be .gml or .ssv
    generated_folder should contain SSV files (one per generated graph)
    """
    folder = sys.argv[1] if len(sys.argv) > 1 else '.'
    original_file = sys.argv[2] if len(sys.argv) > 2 else None
    out = sys.argv[3] if len(sys.argv) > 3 else "graphlet_count.json"

    results = {}

    # Count graphlets for original if provided
    if original_file and os.path.exists(original_file):
        print(f"Processing original: {original_file}")
        results['__original__'] = count_graphlets(original_file)
        print(f"  -> {results['__original__']}")
    elif original_file:
        print(f"Warning: original file not found: {original_file}")

    # Count for all generated graphs
    files = sorted(glob.glob(os.path.join(folder, '*')))
    files = [f for f in files if os.path.isfile(f)]

    for i, fpath in enumerate(files):
        name = os.path.basename(fpath)
        print(f"[{i+1}/{len(files)}] {name}")
        try:
            results[name] = count_graphlets(fpath)
        except Exception as e:
            print(f"  ERROR: {e}")

    with open(out, 'w') as f:
        json.dump(results, f)

    print(f"\nDone. Results saved to {out}")
    return results


if __name__ == '__main__':
    main()