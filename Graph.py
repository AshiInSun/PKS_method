"""
TODO - plus de doc, 
     - faire classe séparée pour les swap plutôt qu'intégrer à la classe graphe"
     - ajouter contraintes
     - ajouter mesures
"""
import os
import ipdb

import numpy as np
import argparse

from collections import defaultdict


class Graph:
    """ Read ael (TODO: ... and other formats ?) and store graph as
    adjacency list
    """

    def __init__(self, directed = False):
        # TODO clarifier quels structures utiles / pas utiles
        self.N = 0 # number of node
        self.M = 0 # number of edges
        self.neighbors = defaultdict(list) # is used as out_neighbors when directed
        self.in_neighbors = defaultdict(list)
        self.out_neighbors = defaultdict(list)
        self.neighbors_index = [] # for edge (u,v) = self.edges[i], store index of v in self.neighbors[u]  and of u in self.neighbors[v]
        #self.edges = set() #dict() ?
        self.edges = dict()
        self.edge_set = set() # pour enlever les doublons TODO overkill ?
        self.unique_edges = list()
        self.directed = directed # directed graph flag
        #self.metric = False # fonction de métrique à vérifier de temps à autres


    def read_ssv(self, in_file):
        """ Read space separated values
            TODO example format
            TODO lecteurs pour d'autres formats
        """
        with open(in_file, 'r') as fin:
            for line in fin:
                #neighbor_array = []
                
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
                    self.edges[(node_in, node_out)] = (len(self.neighbors[node_in]) -1, len(self.neighbors[node_out]) -1, len(self.out_neighbors[node_in]) - 1, len(self.in_neighbors[node_out]) - 1) #.append((node_in, node_out))
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
                        self.edges[(node_in, node_out)] = len(self.neighbors[node_in]) -1 #.append((node_in, node_out))
                        self.neighbors[node_out].append(node_in)
                        self.edges[(node_out, node_in)] = len(self.neighbors[node_out]) -1 #.append((node_in, node_out))


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
                #neighbor_array = []
                
                if line == '\n': # skip empty lines
                    continue

                _neighbor_list = line.strip().split(' ')
                #if "" in _neighbor_list:
                #    continue
                neighbor_list = [int(node_out) for node_out in _neighbor_list]
                # check self loop
                if node_in in neighbor_list:
                    raise ValueError("self loop detected")

                # check no repetition
                if len(set(neighbor_list)) != len(neighbor_list):
                    print('removing duplicate values')
                    neighbor_list = list(set(neighbor_list))
                    #raise ValueError("repetition detected")
                #if self.directed:
                #self.neighbors[node_in] = neighbor_list
                #self.edges += [(node_in, node_out) for node_out in neighbor_list]

                # add to graph
                if self.directed :
                    #self.neighbors[node_in] = neighbor_list
                    for node_idx, node_out in enumerate(neighbor_list): # TODO surement une façon plus rapide et propre de faire ça
                        self.M += 1 
                        #self.neighbors_index.append(node_idx)
                        #print(node_out)
                        #if (not (node_in, node_out) in self.edge_set) and (not (node_in, node_out) in self.edge_set):
                        self.neighbors[node_in].append(node_out)
                        self.edges[(node_in, node_out)] = len(self.neighbors[node_in]) -1 #.append((node_in, node_out))
                        #self.edge_set.add((node_in, node_out))
                        self.unique_edges.append((node_in, node_out))
                else:
                    for node_idx, node_out in enumerate(neighbor_list):
                        #print(neighbor_list)

                        # probablement pas utile et overkill..?
                        if (node_in, node_out) in self.edges:
                            continue
                        else:
                            if node_in < node_out:
                                self.unique_edges.append((node_in, node_out))
                            else:
                                self.unique_edges.append((node_out, node_in))

                            self.neighbors[node_in].append(node_out)
                            self.edges[(node_in, node_out)] = len(self.neighbors[node_in]) -1 #.append((node_in, node_out))
                            self.neighbors[node_out].append(node_in)
                            self.edges[(node_out, node_in)] = len(self.neighbors[node_out]) -1 #.append((node_in, node_out))

                        #if node_in < node_out:
                        #    # only add edges once...
                        #    M_before = len(self.edge_set)
                        #    self.edge_set.add((node_in, node_out))
                        #    M_after = len(self.edge_set)
                        #    if M_before < M_after:
                        #        self.edges.append((node_in, node_out))
                        #        flag_new = True
                        #else:
                        #    # only add edges once...
                        #    M_before = len(self.edge_set)
                        #    self.edge_set.add((node_out, node_in))
                        #    M_after = len(self.edge_set)
                        #    if M_before < M_after:
                        #        self.edges.append((node_out, node_in))
                        #        flag_new = True


                        #    #self.edges.append((node_out, node_in))
                        #    #self.edge_set.add((node_out, node_in))
                        #    ##self.neighbors[node_out].append(node_in)

                        #if flag_new:
                        #    self.neighbors[node_in].append(node_out)
                        #    self.neighbors[node_out].append(node_in)
                        #    self.neighbors_index.append((len(self.neighbors[node_in])-1, len(self.neighbors[node_out])-1))

        #print(node_in)
        #self.edges = list(self.edge_set)
        #for edge_idx, (u,v) in enumerate(self.edges.keys()):
        #    v_idx, u_idx = self.neighbors_index[edge_idx]
        #    assert self.neighbors[u][v_idx] == v
        #    assert self.neighbors[v][u_idx] == u

        #self.M = len(self.edges.keys()) #TODO for directed graph
        assert len(self.unique_edges) == len(set(self.unique_edges))
        self.M = len(self.unique_edges) #TODO for directed graph
        #assert len(self.edges) == len(self.neighbors_index)
        #assert set(self.edges) == self.edge_set
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
        
def main():
    file_in = "./gp_references.txt"
    mygraph = Graph()
    mygraph.read_ael(file_in)
    from progressbar import ProgressBar
    pb = ProgressBar()
    for j in pb(range(1000000)):
        edge_to_switch, permutation = mygraph.find_switch(4)
        mygraph.perform_switch(edge_to_switch, permutation)
    mygraph.to_ael()

if __name__ == "__main__": 
    main()


