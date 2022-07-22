import os
import ipdb
import numpy as np
import argparse


from Graph import Graph
from progressbar import ProgressBar
from collections import defaultdict

class Swap:
    """ make swaps """

    def __init__(self, graph, N_swap=0, gamma=0):
        self.graph = graph
        self.N_swap = 0
        self.gamma = gamma
        self.force_k = True

    def pick_k(self):
        # minimum k is 2
        # use modulo to avoid having k greater than the size of the graph #TODO ya peut etre plus propre
        k = 1 + np.random.zipf(self.gamma) % self.graph.M
        
        return k

    def find_switch(self, k):
        """ TODO : 2 strategies, force k to be exact, or allow <=k

            edge_to_switch donne list des liens à changer
            switch donne avec quel lien changer chaque lien de edge_to_switch
            ex:  
        """
        #k = np.random.randint(10) # TODO lois ...
    
        # check if no self loop
        permut_idx = 0
        valid_permutation = False
        #while (not valid_permutation): # TODO juste pour tester, enlever le while
        #permut_idx += 1
        edge_to_switch = np.random.choice(self.graph.N, k, replace=False)
        #edge_to_switch = np.random.choice( len(self.edges), k, replace=False)

        permutation = edge_to_switch.copy() # find permutation by shuffling list of edges to switch

        if self.force_k:
            # if force_k, permutation is cyclic, to force the swap to be of exactly k edges
            cycle = np.random.randint(1,k)
            permutation = [edge_to_switch[idx - cycle] for idx in range(len(edge_to_switch))]
        else:
            # if !force_k, permutation is of k edges or less
            np.random.shuffle(permutation) 

             
        return edge_to_switch, permutation

    def check_swap(self, edge_to_switch, permutation):

        for before_edge_idx, after_edge_idx in zip(edge_to_switch, permutation):
            departure_edge = self.graph.edges[before_edge_idx]
            arrival_edge = self.graph.edges[after_edge_idx]

            # avoid loops
            if departure_edge[0] == arrival_edge[1]:
                accept_permutation = False
                break

            # avoid multiple edges
            if (departure_edge[0], arrival_edge[1]) in self.edge_set:
                accept_permutation = False
                break
        else:
            valid_permutation = True
            # TODO vérifier autres contraintes
        return accept_permutation

    def perform_switch(self, edge_to_switch, permutation):
        for before_edge_idx, after_edge_idx in zip(edge_to_switch, permutation):

            # get edge name
            departure_edge = self.edges[before_edge_idx]
            arrival_edge = self.edges[after_edge_idx]
            
            # switch in edge set
            print(departure_edge)
            print((departure_edge[0], arrival_edge[1]))

            self.edge_set.remove(departure_edge)
            self.edge_set.add((departure_edge[0], arrival_edge[1]))

            # switch in list
            #print(self.edges[before_edge_idx])
            self.edges[before_edge_idx] = (departure_edge[0], arrival_edge[1])
            #print(departure_edge in self.edges)
            # just for debug
            assert set(self.edges) == self.edge_set, "mismatch"

    def metric(self):
        pass

    def run(self):
        pb = ProgressBar()
        for swap_idx in pb(range(self.N_swap)):
            k = self.pick_k()
            edge_to_switch, permutation = self.find_switch(k)
            accept_permutation = self.check_swap(edge_to_switch, permutation)
            if (accept_permutation):
                self.perform_switch(edge_to_switch, permutation)
                # measure convergence
                self.metric()


def main():
    file_in = "./gp_references.txt"
    print('reading graph')
    mygraph = Graph()
    print('from ael')
    mygraph.read_ael(file_in)
    print('performing swaps')
    swaps = Swap(mygraph, 10000, 12)
    swaps.run()
    #for j in pb(range(1000000)):
    #    edge_to_switch, permutation = mygraph.find_switch(4)
    #    mygraph.perform_switch(edge_to_switch, permutation)
    #mygraph.to_ael()

if __name__ == "__main__": 
    main()


