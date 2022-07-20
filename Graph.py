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

    def __init__(self):
        self.N = 0 # number of node
        self.M = 0 # number of edges
        self.neighbors = defaultdict(list) # np.array() # TODO pas besoin ?
        #self.edges = set() #dict() ?
        self.edges = list()
        self.edge_set = set() # pour enlever les doublons TODO overkill ?
        self.directed = False # directed graph flag
        #self.metric = False # fonction de métrique à vérifier de temps à autres

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
                self.neighbors[node_in] = neighbor_list
                #self.edges += [(node_in, node_out) for node_out in neighbor_list]
                if self.directed :
                    for node_out in neighbor_list: # TODO surement une façon plus rapide et propre de faire ça
                        #if (not (node_in, node_out) in self.edge_set) and (not (node_in, node_out) in self.edge_set):
                            #self.edges.append((node_in, node_out))
                        self.edge_set.add((node_in, node_out))
                else:
                    for node_out in neighbor_list:
                        # probablement pas utile et overkill..?
                        if node_in < node_out:
                            #self.edges.append((node_in, node_out))
                            self.edge_set.add((node_in, node_out))
                            self.neighbors[node_in].append(node_out)
                        else:
                            #self.edges.append((node_out, node_in))
                            self.edge_set.add((node_out, node_in))
                            self.neighbors[node_out].append(node_in)
        print(node_in)
        self.edges = list(self.edge_set)
        assert set(self.edges) == self.edge_set
        self.N = node_in




    def find_switch(self, k):
        """ edge_to_switch donne list des liens à changer
            switch donne avec quel lien changer chaque lien de edge_to_switch
            ex:  
        """
        #k = np.random.randint(10) # TODO lois ...
    
        # check if no self loop
        permut_idx = 0
        valid_permutation = False
        while (not valid_permutation): # TODO juste pour tester, enlever le while
            permut_idx += 1
            edge_to_switch = np.random.choice( self.N, k, replace=False)
            #edge_to_switch = np.random.choice( len(self.edges), k, replace=False)

            permutation = edge_to_switch.copy() # find permutation by shuffling list of edges to switch
            np.random.shuffle(permutation)

            for before_edge_idx, after_edge_idx in zip(edge_to_switch, permutation):
                departure_edge = self.edges[before_edge_idx]
                arrival_edge = self.edges[after_edge_idx]
                 
                # TODO séparer vérifications
                # no loop
                if departure_edge[0] == arrival_edge[1]:
                    valid_permutation = False
                    break

                # no multiple edges
                if (departure_edge[0], arrival_edge[1]) in self.edge_set:
                    valid_permutation = False
                    break
            else:
                valid_permutation = True
                # TODO vérifier autres contraintes
        return edge_to_switch, permutation

    def check_swap(self, edge_to_switch, permutation):
        pass

    def perform_switch(self, edge_to_switch, permutation):
        print('=====')
        for before_edge_idx, after_edge_idx in zip(edge_to_switch, permutation):
            # get edge name
            departure_edge = self.edges[before_edge_idx]
            arrival_edge = self.edges[after_edge_idx]
            
            # switch in set
            print(departure_edge)
            print((departure_edge[0], arrival_edge[1]))

            self.edge_set.remove(departure_edge)
            self.edge_set.add((departure_edge[0], arrival_edge[1]))

            # switch in list
            print(self.edges[before_edge_idx])
            self.edges[before_edge_idx] = (departure_edge[0], arrival_edge[1])
            print(departure_edge in self.edges)
            assert set(self.edges) == self.edge_set, "mismatch"


    def to_ael(self):
        to_write = dict()
        for node_in, node_out in self.edges:
            if node_in not in to_write:
                to_write[node_in] = []
            if node_out not in to_write:
                to_write[node_out] = []
            to_write[node_in].append(str(node_out))
            to_write[node_out].append(str(node_in))

        with open('output', 'w') as fout:
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


