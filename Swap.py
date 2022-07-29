import os
import ipdb
import numpy as np
import argparse


from Graph import Graph
from progressbar import ProgressBar
from collections import defaultdict

class Swap:
    """ make swaps """

    def __init__(self, graph, N_swap = 0, gamma=0):
        """
            Class to handle k-edge random swap

            Attributes:
            graph (Graph object) : graph stored as an adjacency list, can be directed or not.
            N_swap (int) : the number of swaps to perform on the graph
            gamma (int) : parameter used for zipf distribution to pick k value at each round
            force_k (bool) : if true, force edge swap to be exactly of k edges (cyclic 
                             permutation)
            assortativity (float) : store assortativity value
            D (float) : constant denominator used to compute assortativity (compute once)
            triangles (set) : set used to store all the triangles in the graph
            edges_in_triangles (dict) : set used to store all the edges involved in a triangle,
                                        pointing to the triangle they are involved in 

        """

        self.graph = graph
        self.N_swap = N_swap
        self.gamma = gamma
        self.force_k = True
        self.assortativity = 0
        self.D = 0 # assortativity denominator - does not depend on links
        self.triangles = set() # set of all triangles in graph
        self.edges_in_triangles = set()

    def pick_k(self):
        """
            Pick k value using zipf distribution.
            Use modulo to force k to be equal to the number of edges in the graph at max.

            Return:
            k (int) : number of edges to swap
        """
        # minimum k is 2
        # use modulo to avoid having k greater than the size of the graph #TODO ya peut etre plus propre
        k = 2 + (np.random.zipf(self.gamma) % self.graph.M  )

        return k

    def find_swap(self, k):
        """ TODO : 2 strategies, force k to be exact, or allow <=k

            edge_to_swap donne list des liens à changer
            swap donne avec quel lien changer chaque lien de edge_to_swap
            ex:  

            Randomly pick k edges to swap, and randomly pick a permutation

            Parameters:
            k (int) : number of edges to swap

            Return:
            edge_to_swap : list of the edges to swap
            permutation  : list of the edges with which we should swap the
                           edges in edge_to_swap

        """
    
        # check if no self loop
        permut_idx = 0
        valid_permutation = False
        _edge_to_swap = np.random.choice(len(self.graph.unique_edges), k, replace=False)
        if self.graph.directed:
            edge_to_swap = [self.graph.unique_edges[e_idx] for e_idx in edge_to_swap]
        else:
            # for undirected graphs, pick if edges are reversed or not
            edge_to_swap = [(self.graph.unique_edges[e_idx][0], self.graph.unique_edges[e_idx][1]) 
                                if np.random.choice([True, False]) 
                       else (self.graph.unique_edges[e_idx][0], self.graph.unique_edges[e_idx][1]) for e_idx in _edge_to_swap]

        permutation = edge_to_swap.copy() # find permutation by shuffling list of edges to swap

        if self.force_k:
            # if force_k, permutation is cyclic, to force the swap to be of exactly k edges
            cycle = np.random.randint(1,k)
            permutation = [edge_to_swap[idx - cycle] for idx in range(len(edge_to_swap))]
        else:
            # if !force_k, permutation is of k edges or less
            np.random.shuffle(permutation) 

        return edge_to_swap, permutation, _edge_to_swap

    def check_swap(self, edge_to_swap, permutation):
        """
            Verify constraints to see if swap can be accepted or not

            Parameters:
            edge_to_swap : list of the edges to swap
            permutation  : list of the edges with which we should swap the
                           edges in edge_to_swap

            Return :
            accept_permutation : bool, true if swap can be accepted

        """
        accept_permutation = False
        goal_edges = []
        for ((u,v), (x,y)) in zip(edge_to_swap, permutation):
            goal_edge = (u, y) if u < y else (y ,u)
            goal_edges.append(goal_edge)

            # avoid loops
            if u == y:
                accept_permutation = False
                break

            # avoid multiple edges
            if goal_edge in self.graph.edges:
                accept_permutation = False
                break

        else:
            if len(set(goal_edges)) == len(goal_edges): # NOTE : VERIFIER QU'ON A PAS DEUX SWAP QUI VISENT LE MEME LIEN !!
                accept_permutation = True
            else:
                accept_permutation = False
            # TODO vérifier autres contraintes
        return accept_permutation

    def perform_swap(self, edge_to_swap, permutation, edge_to_swap_idx):
        """
            When permutation is accepted, swap the edges in the graph data structure.

            Parameters:
            edge_to_swap : list of the edges to swap
            permutation  : list of the edges with which we should swap the
                           edges in edge_to_swap
            edge_to_swap_idx : index of the edges in graph.unique_edges (useful when undirected)
        """

        # TODO put unit test only as debug
        for (u, v), (x,y), e_idx in zip(edge_to_swap, permutation, edge_to_swap_idx):
            departure = (u,v) if u < v else (v,u)
            arrival = (x, y) if x < y else (y,x)
            assert (u,v) in self.graph.edges
            assert (v,u) in self.graph.edges
            assert (x,y) in self.graph.edges
            assert (y,x) in self.graph.edges
            assert departure in self.graph.unique_edges
            assert arrival in self.graph.unique_edges

        for (u, v), (x,y), e_idx in zip(edge_to_swap, permutation, edge_to_swap_idx):

            # naming departure edge = (u,v) and arrival edge = (x,y)
            # , goal edge = (u, y)
            goal_edge = (u, y) if u < y else (y ,u)
            old_edge = self.graph.unique_edges[e_idx]
            assert len(set(self.graph.unique_edges)) == self.graph.M

            self.graph.unique_edges[e_idx] = goal_edge
            try:
               assert len(set(self.graph.unique_edges)) == self.graph.M
            except:
                ipdb.set_trace()

            old_edge = (u, v) if u < v else (v, u)
            assert old_edge not in self.graph.unique_edges
            v_idx = self.graph.edges[(u,v)]
            u_idx =  self.graph.edges[(v,u)]
            y_idx = self.graph.edges[(x,y)]
            x_idx =  self.graph.edges[(y,x)]

            # perform swap
            self.graph.neighbors[u][v_idx] = y # on change v dans neighbors (u)
            # j'ai envie de faire self.graph.neighbors[y][x_idx] = u : x y va disparaitre pour etre remplacé par x y' => x sera plus voisin de y donc pas de pb 
            self.graph.neighbors[y][x_idx] = u

            self.graph.edges[(u,y)] = v_idx
            self.graph.edges[(y,u)] = x_idx
        for (u, v), (x,y) in zip(edge_to_swap, permutation):


            del self.graph.edges[(u,v)]
            del self.graph.edges[(v,u)]
        for u, v in self.graph.unique_edges:
            assert (u, v) in self.graph.edges
        for (u, v), (x,y), e_idx in zip(edge_to_swap, permutation, edge_to_swap_idx):
            departure = (u,v) if u < v else (v,u)
            arrival = (x, y) if x < y else (y,x)
            goal_edge = (u, y) if u < y else (y ,u)

            assert (u,v) not in self.graph.edges
            assert (v,u) not in self.graph.edges
            assert (x,y) not in self.graph.edges
            assert (y,x) not in self.graph.edges
            assert (u,y) in self.graph.edges
            assert (y,u) in self.graph.edges

            assert goal_edge in self.graph.unique_edges
            assert departure not in self.graph.unique_edges
            assert arrival not in self.graph.unique_edges

    def init_assortativity(self):
        """
            Compute Assortativity initial value, using the formula found in 
            "Dutta, Fosdick et Clauset, 2022: Sampling random graphs with specified degree sequences".
            
             Using the notation deg(u) for the degree of u, and Axy for the adjancency matrix value for
             nodes x and y, and Sk = sum_x (deg(x) ^ k), we compute the following values:
                -S1, S2 and S3, 
                -Sl= sum_xy (Axy * deg(x) * deg(y))

            Using these values, the assortativity is computed as :

            r = ( S1 * Sl - S2 * S2 ) / ( S1 * S3 - S2 * S2 )

            Since Sl is the only value to depend on the presence of each link, we store the denominator
            to update the assortativity value in O(1) after each swap.
        """
        S1 = 2 * self.graph.M

        # loop to comput S2 and S3
        S2 = 0
        S3 = 0
        Sl = 0
        for u in self.graph.neighbors.keys():
            deg_u = len(self.graph.neighbors[u])
            S2 += deg_u ** 2
            S3 += deg_u ** 3
            for v in self.graph.neighbors[u]:
                deg_v = len(self.graph.neighbors[v])
                Sl += deg_u * deg_v
        N = S1 * Sl - S2*S2
        self.D = S1 * S3 - S2 * S2
        self.assortativity = N/self.D


    def update_assortativity(self, edge_to_swap, permutation):
        """ 
            Given a K-edge swap, update assortativy value using generalised formual from
            "Dutta, Fosdick et Clauset, 2022: Sampling random graphs with specified degree sequences"
        """

        # TODO CHECK IF THAT WORKS (math + practice)
        N = 0 

        for (u, v), (x,y) in zip(edge_to_swap, permutation):

            # new edge is (u,y), disappearing edge is (u,v)
            deg_u = len(self.graph.neighbors[u])
            deg_v = len(self.graph.neighbors[v])
            deg_x = len(self.graph.neighbors[x])
            deg_y = len(self.graph.neighbors[y])
            N += deg_u * deg_y - deg_u * deg_v
        N = N * 4 * self.graph.M
        delta_r = N / self.D # difference in assortativity
        self.assortativity += delta_r

    def count_triangles(self):
        """ 
            Enumerate and store all triangles found in the graph.
            For undirected graphs:
                we store each triangle in a set of tuplet ((u,v,w)) where 
                u, v and w are the node, with u < v < w, and we store each link
                involved in the triangle in edges_in_triangles (pointing to the triangle tuplet)
            For directed graphs:
                we store each triangle thrice in a set of tuplet, with each node as a starting point,
                e.g. for triangle (u,v,w) we store {(u,v,w), (v,w,u), (w,u,v)}. We store each link
                involved in the triangle in edges_in_triangles (pointing to the triangle tuplet)


        """
        nb_triangles = 0
        #self.triangles =
        for node_1 in self.graph.neighbors.keys():
            
            # skip nodes of degree < 2
            if len(self.graph.neighbors[node_1]) < 2:
                continue
            
            # check neighborhood or neighbors of node_1
            for node_2 in self.graph.neighbors[node_1]:
                for node_3 in self.graph.neighbors[node_2]:
                    
                    # count triangle if not already counted
                    if (node_3, node_1) in self.graph.edges:
                        if not self.graph.directed:
                            current_triangle = tuple(sorted((node_1, node_2, node_3)))
                            self.triangles.add(current_triangle)

                            self.edges_in_triangles[(node_1, node_2)]
                            self.edges_in_triangles[(node_2, node_3)]
                            self.edges_in_triangles[(node_3, node_1)]

                            self.edges_in_triangles[(node_2, node_1)] = current_triangle
                            self.edges_in_triangles[(node_3, node_2)] = current_triangle
                            self.edges_in_triangles[(node_1, node_3)] = current_triangle

                        # if graph is directed, add three version of triangle
                        elif self.graph.directed :
                            self.triangles.add((node_1, node_2, node_3))
                            self.triangles.add((node_2, node_3, node_1))
                            self.triangles.add((node_3, node_1, node_2))

                            # store arbitrary version of triangle
                            self.edges_in_triangles[(node_1, node_2)] = (node_1, node_2, node_3)
                            self.edges_in_triangles[(node_2, node_3)] = (node_1, node_2, node_3)
                            self.edges_in_triangles[(node_3, node_1)] = (node_1, node_2, node_3)

                        
    def update_triangles(self, edge_to_swap, permutation):
        
        """
            Update the sets of triangles by looking at each edge swap:

            - if the initial edge was involved in a triangle, remove triangle from sets
            - if the goal edge creates a triangle, add it to the sets
        """
        # TODO version graphe dirigé
        for (u, v), (x,y), e_idx in zip(edge_to_swap, permutation, edge_to_swap_idx):

           goal_edge = (u, y) if u < y else (y ,u)

           # destroyed triangles
           if (u, v) in self.edges_in_triangles:
               destroyed_triangle = self.edges_in_triangles[(u,v)] 
               self.triangles.remove(destroyed_triangle)

           # created triangles
           for neigh in self.graph.neighbors[u]:
               if (neigh, y) in self.graph.edges:
                   current_triangle = tuple(sorted((u, v, neigh)))
                   self.triangles.add(current_triangle)
       

    def metric(self):
        pass

    def run(self):
        """
            K-edge swap algorithm.
            Start by computing assortativity initial value, then 
            perform N_swap, each time checking the constraints and computing
            metrics.
        """
        #pb = ProgressBar()
        #for swap_idx in pb(range(self.N_swap)):
        self.init_assortativity()
        print(f"starting assortativity {self.assortativity}")
        for swap_idx in range(self.N_swap):

            k = self.pick_k()
            edge_to_swap, permutation, edge_to_swap_idx = self.find_swap(k)
            accept_permutation = self.check_swap(edge_to_swap, permutation)
            #for (e_idx , (v_idx, u_idx)) in enumerate(self.graph.neighbors_index):
            #    (u, v) = self.graph.edges[e_idx]
            #    assert self.graph.neighbors[u][v_idx] == v
            #    assert self.graph.neighbors[v][u_idx] == u


            if (accept_permutation):
                self.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)
                assert len(self.graph.unique_edges) == self.graph.M

                assert len(self.graph.unique_edges) == len(set(self.graph.unique_edges))

                # measure convergence

                self.update_assortativity(edge_to_swap, permutation)
                updated_assortativity = self.assortativity

                # compare with complete assortativity
                self.init_assortativity()
                if not np.isclose(updated_assortativity, self.assortativity):
                    print(f" updated {updated_assortativity} whole {self.assortativity}")
                #print(self.assortativity)

                self.metric()





def main():
    parser = argparse.ArgumentParser(description='k edge swap')
    parser.add_argument('-f', '--dataset', type=str, default="./gp_references.txt",
            help='path to the dataset')
    parser.add_argument('-o', '--output', type=str, default="./gp_references.out",
            help='path to the output')
    parser.add_argument('-n', '--N_swap', type=int, default=10000,
            help='number of swap')
    parser.add_argument('-g', '--gamma', type=int, default=2,
	    help='exponent of zipf law, for pick K value')
    parser.add_argument('-d', '--directed', action='store_true', default=False,
            help='enable if input graph is directed')
    args = parser.parse_args()

    #file_in = "./gp_references.txt"

    mygraph = Graph(args.directed)
    print('reading graph')
    mygraph.read_ael(args.dataset)
    print('performing swaps')
    swaps = Swap(mygraph, args.N_swap, args.gamma)
    print(swaps.assortativity)
    swaps.run()
    print('writing graph')
    swaps.graph.to_ael(args.output)
    #for j in pb(range(1000000)):
    #    edge_to_swap, permutation = mygraph.find_swap(4)
    #    mygraph.perform_swap(edge_to_swap, permutation)
    #mygraph.to_ael()

if __name__ == "__main__": 
    main()


