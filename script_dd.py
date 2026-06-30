from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain

import matplotlib.pyplot as plt
import networkx as nx

def main():
    out_dir = './out/stars_cluster/out_0305fa001039c87957e4b40382da1af8/0305fa001039c87957e4b40382da1af8.gml'
    dd = set()

    graph = Graph(directed=False)
    graph.read_gml(out_dir)
    for node in graph.neighbors:
        dd.add(len(graph.neighbors[node]))

    print("Distribution :", len(dd))


if __name__ == "__main__":
    main()