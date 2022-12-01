# This file is part of K-edge-swap.
#
#    K-edge-swap is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    K-edge-swap is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with Foobar. If not, see <https://www.gnu.org/licenses/>. 
"""
TODO - plus de doc, 
     - faire classe séparée pour les swap plutôt qu'intégrer à la classe graphe"
     - ajouter contraintes
     - ajouter mesures
"""
import os
#import ipdb

import numpy as np
import argparse

from pathlib import Path
from collections import defaultdict


class Graph:
    """ Read input graph and store graph as
        adjacency list

        Attributes:
        N (int) : number of nodes
        M (int) : number of edges
        neighbors (dict(list)) : store adjacency list for each node
        in_neighbors (dict(list)) : used only in directed graph, for each node
                       store their neighbors from "in-edges"
        out_neighbors (dict(list)) : used only in directed graph, for each node
                        store their neighbors from "out-edges"
        edges (dict()) : in undirected graph: for each edge (u,v), store the position
                        of v in the adjacency list of u
                        in directed graph: for each edge (u,v), store a quartuplet
                        (v_idx, u_idx, v_out_idx, u_in_idx), where:
                          v_idx is the position of v in u's adjacency list
                          u_idx is the position of u in v's adjacency list
                          v_out_idx is the position of v in out_neighbors[u]
                          u_in_idx is the position of u in in_neighbors[v]
        unique_edges (list()): used mostly for undirected graph, to store one version
                               of each edge
        directed (bool) : enable if graph is directed
    """

    def __init__(self, directed = False):
        # TODO clarifier quels structures utiles / pas utiles
        self.N = 0 # number of node
        self.M = 0 # number of edges
        self.neighbors = defaultdict(list) # is used as out_neighbors when directed
        self.in_neighbors = defaultdict(list)
        self.out_neighbors = defaultdict(list)
        self.edges = dict()
        self.unique_edges = list()
        self.directed = directed # directed graph flag
        self.dataset_name = None

    def copy(self):
        graph_copy = Graph()
        graph_copy.N = self.N
        graph_copy.M = self.M
        graph_copy.neighbors = self.neighbors.copy()
        graph_copy.in_neighbors = self.in_neighbors.copy()
        graph_copy.out_neighbors = self.out_neighbors.copy()
        graph_copy.edges = self.edges.copy()
        graph_copy.unique_edges = self.unique_edges.copy()
        graph_copy.directed = self.directed
        return graph_copy

    def read_ssv(self, in_file):
        """ Read space separated values
            Input format is separated with spaces, e.g.:

            >>  0 1
            >>  3 2
            >>  2 4
            >>  .
            >>  .
            >>  .

            where the first columns is the source node and the second column is
            the destination node.
            When self.directed == True, the graph is considered directed and
            edges are stored as written in the file, 
            else they are stored as (src, dest) with src < dest.
            Self Loop and multi-graphs are not accepted.
        """
        self.dataset_name = Path(in_file).stem 
        with open(in_file, 'r') as fin:
            for line in fin:
                
                if line == '\n': # skip empty lines
                    continue
                _node_in, _node_out = line.strip().split(' ')
                node_in, node_out = int(_node_in), int(_node_out)

                if _node_in == _node_out:
                    raise ValueError("self loop detected")

                # add to graph
                if self.directed :

                    self.neighbors[node_in].append(node_out)
                    self.neighbors[node_out].append(node_in)
                    self.out_neighbors[(node_in)].append(node_out)
                    self.in_neighbors[(node_out)].append(node_in)
                    self.M += 1 
                    self.edges[(node_in, node_out)] = (len(self.neighbors[node_in]) -1,
                                                       len(self.neighbors[node_out]) -1,
                                                       len(self.out_neighbors[node_in]) - 1,
                                                       len(self.in_neighbors[node_out]) - 1) 
                    self.unique_edges.append((node_in, node_out))
                else:
                    if (node_in, node_out) in self.edges:
                        continue
                    else:
                        if node_in < node_out:
                            self.unique_edges.append((node_in, node_out))
                        else:
                            self.unique_edges.append((node_out, node_in))

                        self.neighbors[node_in].append(node_out)
                        self.edges[(node_in, node_out)] = len(self.neighbors[node_in]) -1
                        self.neighbors[node_out].append(node_in)
                        self.edges[(node_out, node_in)] = len(self.neighbors[node_out]) -1


        assert len(self.unique_edges) == len(set(self.unique_edges))
        self.M = len(self.unique_edges) #TODO for directed graph
        self.N = node_in


    def read_ael(self, in_file):
        """ Read ael format
            TODO example format
            TODO lecteurs pour d'autres formats
        """
        with open(in_file, 'r') as fin:
            for node_in, line in enumerate(fin):
                
                if line == '\n': # skip empty lines
                    continue

                _neighbor_list = line.strip().split(' ')
                neighbor_list = [int(node_out) for node_out in _neighbor_list]

                # check self loop
                if node_in in neighbor_list:
                    raise ValueError("self loop detected")

                # check no repetition
                if len(set(neighbor_list)) != len(neighbor_list):
                    print('warning : removing duplicate values')
                    neighbor_list = list(set(neighbor_list))
                    #raise ValueError("repetition detected")

                # add to graph
                if self.directed :
                    # TODO : adapt AEL to directed
                    for node_idx, node_out in enumerate(neighbor_list):
                        self.M += 1 
                        self.neighbors[node_in].append(node_out)
                        self.edges[(node_in, node_out)] = len(self.neighbors[node_in]) -1
                        self.unique_edges.append((node_in, node_out))
                else:
                    for node_idx, node_out in enumerate(neighbor_list):

                        # probablement pas utile et overkill..?
                        if (node_in, node_out) in self.edges:
                            continue
                        else:
                            if node_in < node_out:
                                self.unique_edges.append((node_in, node_out))
                            else:
                                self.unique_edges.append((node_out, node_in))

                            self.neighbors[node_in].append(node_out)
                            self.edges[(node_in, node_out)] = len(self.neighbors[node_in]) -1
                            self.neighbors[node_out].append(node_in)
                            self.edges[(node_out, node_in)] = len(self.neighbors[node_out]) -1

        assert len(self.unique_edges) == len(set(self.unique_edges))
        self.M = len(self.unique_edges) #TODO for directed graph
        self.N = node_in

    def to_ael(self, output):
        to_write = dict()
        for node_in, node_out in self.edges:
            if node_in not in to_write:
                to_write[node_in] = []
            if node_out not in to_write:
                to_write[node_out] = []
            to_write[node_in].append(str(node_out))
            to_write[node_out].append(str(node_in))

        with open(output, 'w') as fout:
            for node_in in range(self.N + 1):
                if node_in in to_write:
                    fout.write(f'{" ".join(to_write[node_in])}\n')
                else:
                    fout.write(f'\n')

    def to_ssv(self, output):
        with open(output, 'w') as fout:
            for node_in, node_out in self.unique_edges:
                fout.write(f'{node_in} {node_out}\n')
