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
        self.graph = graph
        self.N_swap = N_swap
        self.gamma = gamma
        self.force_k = True
        self.assortativity = 0
        self.D = 0 # assortativity denominator - does not depend on links
        self.triangles = set() # set of all triangles in graph
        self.edges_in_triangles = set()

    def pick_k(self):
        # minimum k is 2
        # use modulo to avoid having k greater than the size of the graph #TODO ya peut etre plus propre
        k = 1 + (np.random.zipf(self.gamma) % self.graph.M )
        #print(k)
        return k

    def find_swap(self, k):
        """ TODO : 2 strategies, force k to be exact, or allow <=k

            edge_to_swap donne list des liens à changer
            swap donne avec quel lien changer chaque lien de edge_to_swap
            ex:  
        """
        #k = np.random.randint(10) # TODO lois ...
    
        # check if no self loop
        permut_idx = 0
        valid_permutation = False
        #while (not valid_permutation): # TODO juste pour tester, enlever le while
        #permut_ixdx += 1
        #edge_to_swap = []
        #_edge_to_swap = np.random.choice(self.graph.M, k, replace=False)
        _edge_to_swap = np.random.choice(len(self.graph.unique_edges), k, replace=False)
        if self.graph.directed:
            edge_to_swap = [self.graph.unique_edges[e_idx] for e_idx in edge_to_swap]
        else:
            # for undirected graphs, pick if edges are reversed or not
            edge_to_swap = [(self.graph.unique_edges[e_idx][0], self.graph.unique_edges[e_idx][1]) 
                                if np.random.choice([True, False]) 
                       else (self.graph.unique_edges[e_idx][0], self.graph.unique_edges[e_idx][1]) for e_idx in _edge_to_swap]
        #    swap_dir = np.ones(k)
        #else:
        #    swap_dir = np.random.choice([True, False], (k, 2))

        #for (u,v) in _edge_to_swap:
        #    coin = np.random.choice([True, False]) if not self.graph.directed else True
        #    #(v_idx, u_idx) = self.graph.neighbors_index[e_idx]
        #    
        #    if coin:
        #        #(y_idx, x_idx) = self.graph.neighbors_index[after_edge_idx]
        #        edge_to_swap.append(
        #        edge_to_swap.append((e_idx, self.graph.edges[e_idx], self.graph.neighbors_index[e_idx]))
        #    else:
        #        edge_to_swap.append((e_idx, (self.graph.edges[e_idx][1], self.graph.edges[e_idx][0]), (u_idx, v_idx)))

        #edge_to_swap = np.random.choice( len(self.edges), k, replace=False)

        permutation = edge_to_swap.copy() # find permutation by shuffling list of edges to swap

        if self.force_k:
            # if force_k, permutation is cyclic, to force the swap to be of exactly k edges
            cycle = np.random.randint(1,k)
            permutation = [edge_to_swap[idx - cycle] for idx in range(len(edge_to_swap))]
        else:
            # if !force_k, permutation is of k edges or less
            np.random.shuffle(permutation) 

        ## si pas dirigé, choisir sens du swap...
        #if self.graph.directed:
        #    swap_dir = np.ones(k)
        #else:
        #    swap_dir = np.random.choice([True, False], (k, 2))


        #_edge_to_swap = [(e_idx, self.graph.edges[e_idx]) for e_idx in edge_to_swap]
        #_permutation = [(e_idx, self.graph.edges[e_idx]) for e_idx in permutation]
        return edge_to_swap, permutation, _edge_to_swap

    def check_swap(self, edge_to_swap, permutation):

        #for (before_edge_idx, (u,v), (v_idx, u_idx)), (after_edge_idx, (x,y), (y_idx, x_idx)) in zip(edge_to_swap, permutation):
        accept_permutation = False
        goal_edges = []
        for ((u,v), (x,y)) in zip(edge_to_swap, permutation):
            #u, v = self.graph.edges[before_edge_idx]
            #x, y = self.graph.edges[after_edge_idx]

            #goal_edge = (u, y) if u < y else (y ,u)
            #goal_edge = (u, y)
            goal_edge = (u, y) if u < y else (y ,u)
            goal_edges.append(goal_edge)
            #departure_edge = (u, v) if direction[0] else (v, u)
            #arrival_edge = (x, y) if direction[1] else (y, x)

            #goal_edge = (u, y) if direction else (u, x)
            # avoid loops
            #if departure_edge[0] == arrival_edge[1]:
            if u == y:
                accept_permutation = False
                break

            # avoid multiple edges
            #if ((departure_edge[0], arrival_edge[1]) in self.graph.edge_set) or ((arrival_edge[1], departure_edge[0]) in self.graph.edge_set):
            if goal_edge in self.graph.edges:
                accept_permutation = False
                break

            #_edge_to_swap.append((before_edge_idx, departure_edge))
            #_permutation.append((after_edge_idx, arrival_edge))
        else:
            if len(set(goal_edges)) == len(goal_edges): # NOTE : VERIFIER QU'ON A PAS DEUX SWAP QUI VISENT LE MEME LIEN !!
                accept_permutation = True
            else:
                accept_permutation = False
            # TODO vérifier autres contraintes
        return accept_permutation

    def perform_swap(self, edge_to_swap, permutation, edge_to_swap_idx):
        #for (before_edge_idx, (u,v)), (after_edge_idx, (x,y)) in zip(edge_to_swap, permutation):
        #for (before_edge_idx, (u,v), (v_idx, u_idx)), (after_edge_idx, (x,y), (y_idx, x_idx)) in zip(edge_to_swap, permutation):
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
            # get edge name
            #departure_edge = self.graph.edges[before_edge_idx]
            #arrival_edge = self.graph.edges[after_edge_idx]
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

            #assert self.graph.neighbors[u][v_idx] == v
            #assert self.graph.neighbors[v][u_idx] == u
            #assert self.graph.neighbors[x][y_idx] == y
            #assert self.graph.neighbors[y][x_idx] == x
            
            # perform swap
            self.graph.neighbors[u][v_idx] = y # on change v dans neighbors (u)
            # j'ai envie de faire self.graph.neighbors[y][x_idx] = u : x y va disparaitre pour etre remplacé par x y' => x sera plus voisin de y donc pas de pb 
            self.graph.neighbors[y][x_idx] = u

            self.graph.edges[(u,y)] = v_idx
            self.graph.edges[(y,u)] = x_idx
            #self.graph.neighbors[y].append(u) # on ajoute u dans neighbors (y)
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

            #self.graph.neighbors[y][
            #(u,v) = departure_edge
            #(x,y) = arrival_edge

            #print(departure_edge)
            #print(arrival_edge)
            #print(self.graph.neighbors[u])
            #print(self.graph.neighbors[v])
            #print(self.graph.neighbors[x])
            #print(self.graph.neighbors[y])


            # swap in edge set
            #print(departure_edge)
            #print((departure_edge[0], arrival_edge[1]))

            #self.graph.edge_set.remove(departure_edge)
            #self.graph.edge_set.add(goal_edge)
            #self.graph.edges[before_edge_idx] = goal_edge
            #if (u < y) or (self.graph.directed):
            #    self.graph.edge_set.add((u,y))
            #    self.graph.edges[before_edge_idx] = (u, y)

            #    #self.graph.edge_set.add((departure_edge[0], arrival_edge[1]))
            #elif (y < u and not self.graph.directed):
            #    self.graph.edge_set.add((y,u))
            #    self.graph.edges[before_edge_idx] = (y, u)

            # swap in list
            #print(self.edges[before_edge_idx])

            # change in adjacency lists 
            #if self.graph.directed:
            #    pass
            #else:
            #    pass
                ### NOTE : on change seulement neighbors[u] et neighbors[y] , neighbors[v] va être mis à jour plus tard
                #(v_idx, u_idx) = self.graph.neighbors_index[before_edge_idx]
                #(y_idx, x_idx) = self.graph.neighbors_index[after_edge_idx]

                #assert self.graph.neighbors[u][v_idx] == v
                #assert self.graph.neighbors[v][u_idx] == u
                #assert self.graph.neighbors[x][y_idx] == y 
                #assert self.graph.neighbors[y][x_idx] == x
                #self.graph.neighbors[u][v_idx] = y
                #try:
                #self.graph.neighbors[y][x_idx] = u
                #except:
                #    
                #    ipdb.set_trace()
                #    self.graph.neighbors[y][x_idx] = u

                #del self.graph 
                #del self.graph.edges
            #print(departure_edge in self.edges)
            # just for debug
            #assert set(self.graph.edges) == self.graph.edge_set, "mismatch after"
        #print('after swap')
        #for (before_edge_idx, (u,v)), (after_edge_idx, (x,y)) in zip(edge_to_swap, permutation):
        #    (v_idx, u_idx) = self.graph.neighbors_index[before_edge_idx]
        #    (y_idx, x_idx) = self.graph.neighbors_index[after_edge_idx]
        #    print(f'swapping ({u}, {v}) with ({x}, {y})')
        #    print(f'edges : {self.graph.edges[before_edge_idx]}')
        #    print(f'neighbors: {self.graph.neighbors[u][v_idx]}')

    def init_assortativity(self):
        # compute r0
        # r0 = N0 / D0
        # N0 = S1 * Sl - S2 * S2
        #
        # D0  = S1 * S3 - S2 * S2
        #
        # Sk = sum_x (deg(x) ^ k) 
        # Sl = sum_xy (Axy * kx * ky)
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
        # given a swap, update assortativity value given generalized equation from https://arxiv.org/pdf/2105.12120.pdf 
        # compute denominator
        # TODO CHECK IF THAT WORKS (math + practice)
        N = 0 
        #ipdb.set_trace()
        #for ((u,v), (x,y)) in zip(edge_to_swap, permutation):
        #for before_edge_idx, after_edge_idx in zip(edge_to_swap, permutation):
        for (u, v), (x,y) in zip(edge_to_swap, permutation):

            # naming departure edge = (u,v) and arrival edge = (x,y)
            # get edge name
            #departure_edge = self.graph.edges[before_edge_idx]
            #arrival_edge = self.graph.edges[after_edge_idx]
            #
            #(u,v) = departure_edge
            #(x,y) = arrival_edge

            # new edge is (u,y), disappearing edge is (u,v)
            deg_u = len(self.graph.neighbors[u])
            deg_v = len(self.graph.neighbors[v])
            deg_x = len(self.graph.neighbors[x])
            deg_y = len(self.graph.neighbors[y])
            N += deg_u * deg_y - deg_u * deg_v
        N = N * 4 * self.graph.M
        delta_r = N / self.D # difference in assortativity
        self.assortativity += delta_r

    #def _assortativity(self):
    def count_triangles(self):
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

         # TODO version graphe dirigé
         for (u, v), (x,y), e_idx in zip(edge_to_swap, permutation, edge_to_swap_idx):

            # naming departure edge = (u,v) and arrival edge = (x,y)
            # get edge name
            #departure_edge = self.graph.edges[before_edge_idx]
            #arrival_edge = self.graph.edges[after_edge_idx]
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
    args = parser.parse_args()

    #file_in = "./gp_references.txt"

    mygraph = Graph()
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


