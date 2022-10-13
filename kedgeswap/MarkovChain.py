# This file is part of K-edge-swap.
#
#    K-edge-swap is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    K-edge-swap is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with Foobar. If not, see <https://www.gnu.org/licenses/>. 

""" MarkovChain class, used to perform k-edge on a graph
"""

import os
#import ipdb
import numpy as np
import argparse

from kedgeswap.Graph import Graph
from progressbar import ProgressBar
from collections import defaultdict

class MarkovChain:
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
        #self.triangles = set() # set of all triangles in graph
        self.edges2triangles = defaultdict(list)
        self.triangles2edges = defaultdict(list)
        self.joint_degree = np.zeros(0)
        #self.debug = debug

    def __dump__(self, edge_to_swap, permutation):
        """Write graph and permutation, useful for debugging"""
        with open('dump.log', 'w') as fout:
            fout.write('neighbors\n')
            for node in self.graph.neighbors:
                fout.write(f'{node}: {self.graph.neighbors[node]}\n')
            fout.write('edges\n')
            for edge in self.graph.edges:
                fout.write(f'{edge}: {self.graph.edges[edge]}\n')
            fout.write('edges2triangles\n')
            for edge in self.edges2triangles:
                fout.write(f'{edge}: {self.edges2triangles[edge]}\n')
            fout.write('triangles2edges\n')
            for triangle in self.triangles2edges:
                fout.write(f'{triangle}: {self.triangles2edges[triangle]}\n')
            fout.write('edge_to_swap and permutation\n')
            for ((u,v), (x,y)) in zip(edge_to_swap, permutation):
                fout.write(f'{(u,v)}, {(x,y)}\n')

    def pick_k(self):
        """
            Pick k value using zipf distribution.
            Use modulo to force k to be equal to the number of edges in the graph at max.

            Return:
            k (int) : number of edges to swap
        """
        # minimum k is 2
        # use modulo to avoid having k greater than the size of the graph
        #TODO ya peut etre plus propre
        k = 2 + (np.random.zipf(self.gamma) % (self.graph.M-2))

        return k

    def find_swap(self, k):
        """ TODO : 2 strategies, force k to be exact, or allow <=k

            edge_to_swap donne list des liens à changer
            swap donne avec quel lien changer chaque lien de edge_to_swap
            ex:  

            Randomly pick k edges to swap, and randomly pick a permutation
            When self.force_k == True, permutation is a cyclic permutation,
            else it is a random permutation, with possible identity for some edges.

            Parameters:
            k (int) : number of edges to swap

            Return:
            edge_to_swap : list of the edges to swap
            permutation  : list of the edges with which we should swap the
                           edges in edge_to_swap

        """
        # TODO possibly same edges   
        # check if no self loop
        permut_idx = 0
        valid_permutation = False
        _edge_to_swap = np.random.choice(len(self.graph.unique_edges), k, replace=False)
        #_edge_to_swap = np.random.choice(len(self.graph.unique_edges), k, replace=True)

        if self.graph.directed:
            edge_to_swap = [self.graph.unique_edges[e_idx] for e_idx in _edge_to_swap]
        else:
            # for undirected graphs, pick if edges are reversed or not
            edge_to_swap = [(self.graph.unique_edges[e_idx][0], self.graph.unique_edges[e_idx][1]) 
                                if np.random.choice([True, False]) 
                       else (self.graph.unique_edges[e_idx][0], self.graph.unique_edges[e_idx][1]) for e_idx in _edge_to_swap]

        permutation = edge_to_swap.copy() # find permutation by shuffling list of edges to swap

        if self.force_k:
            # if force_k, permutation is cyclic, to force the swap to be of exactly k edges
            cycle = np.random.randint(1,k) #TODO pas nécessaire : lien tiré aléatoirement
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
            if self.graph.directed:
                goal_edge = (u, y)
            else:
                goal_edge = (u, y) if u < y else (y ,u)
            goal_edges.append(goal_edge)

            # avoid loops
            if u == y:
                return False

            # avoid multiple edges
            if goal_edge in self.graph.edges:
                return False

            # check joint degree matrix
            #updated_joint_degree = self.update_joint_degree(edge_to_swap, permutation)
            #if not (updated_joint_degree == self.joint_degree).all():
            #    return False
             
        if len(set(goal_edges)) == len(goal_edges): # NOTE : VERIFIER QU'ON A PAS DEUX SWAP QUI VISENT LE MEME LIEN !!
            accept_permutation = True
        else:
            return False
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

        for (u, v), (x,y), e_idx in zip(edge_to_swap, permutation, edge_to_swap_idx):

            # naming departure edge = (u,v) and arrival edge = (x,y) , goal edge = (u, y)
            if self.graph.directed:
                goal_edge = (u, y)
            else:
                goal_edge = (u, y) if u < y else (y ,u)
            old_edge = self.graph.unique_edges[e_idx]
            self.graph.unique_edges[e_idx] = goal_edge

            old_edge = (u, v) if u < v else (v, u)

            if self.graph.directed:
                v_idx, u_idx, v_out_idx, u_in_idx = self.graph.edges[(u,v)]
                y_idx, x_idx, y_out_idx, x_in_idx = self.graph.edges[(x,y)]

                self.graph.out_neighbors[u][v_out_idx] = y
                self.graph.in_neighbors[y][x_in_idx] = u

                self.graph.edges[(u,y)] = (v_idx, x_idx, v_out_idx, x_in_idx)
            else:
                v_idx = self.graph.edges[(u,v)]
                u_idx =  self.graph.edges[(v,u)]
                y_idx = self.graph.edges[(x,y)]
                x_idx =  self.graph.edges[(y,x)]

                self.graph.edges[(u,y)] = v_idx
                self.graph.edges[(y,u)] = x_idx

            # perform swap
            self.graph.neighbors[u][v_idx] = y # on change v dans neighbors (u)
            self.graph.neighbors[y][x_idx] = u

        for (u, v), (x,y) in zip(edge_to_swap, permutation):
            del self.graph.edges[(u,v)]
            if not self.graph.directed:
                del self.graph.edges[(v,u)]

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
            if self.graph.directed:
                deg_u += len(self.graph.in_neighbors[u])

            S2 += deg_u ** 2
            S3 += deg_u ** 3
            for v in self.graph.neighbors[u]:
                deg_v = len(self.graph.neighbors[v])
                if self.graph.directed:
                    deg_v += len(self.graph.in_neighbors[v])

                Sl += deg_u * deg_v
        N = S1 * Sl - S2*S2
        self.D = S1 * S3 - S2 * S2
        self.assortativity = N/self.D


    def update_assortativity(self, edge_to_swap, permutation):
        """ 
            Given a K-edge swap, update assortativy value using generalised formual from
            "Dutta, Fosdick et Clauset, 2022: Sampling random graphs with specified degree sequences"
        """
        N = 0 
        for (u, v), (x,y) in zip(edge_to_swap, permutation):

            # new edge is (u,y), disappearing edge is (u,v)
            deg_u = len(self.graph.neighbors[u])
            deg_v = len(self.graph.neighbors[v])
            deg_x = len(self.graph.neighbors[x])
            deg_y = len(self.graph.neighbors[y])

            if self.graph.directed:
                deg_u += len(self.graph.in_neighbors[u])
                deg_v += len(self.graph.in_neighbors[v])
                deg_x += len(self.graph.in_neighbors[x])
                deg_y += len(self.graph.in_neighbors[y])

            N += deg_u * deg_y - deg_u * deg_v
        N = N * 4 * self.graph.M
        delta_r = N / self.D # difference in assortativity
        self.assortativity += delta_r

    def _add_directed_triangle(self, u, v, triangle):
        if (u,v) in self.graph.edges:
            self.edges2triangles[(u, v)].append(triangle)
            self.triangles2edges[triangle].append((u,v))
        else:
            self.edges2triangles[(v, u)].append(triangle)
            self.triangles2edges[triangle].append((v,u))


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
        for node_1 in self.graph.neighbors.keys():
            
            # skip nodes of degree < 2
            if len(self.graph.neighbors[node_1]) < 2:
                continue
            
            # check neighborhood or neighbors of node_1
            for node_2 in self.graph.neighbors[node_1]:

                # skip nodes of degree < 2
                if len(self.graph.neighbors[node_2]) <2:
                    continue

                for node_3 in self.graph.neighbors[node_2]:

                    # skip nodes of degree < 2
                    if len(self.graph.neighbors[node_3]) < 2:
                        continue
                    
                    # count triangle if not already counted
                    if ((node_3, node_1) in self.graph.edges) or ((node_1, node_3) in self.graph.edges):
                        # store sorted version of triangle
                        current_triangle = tuple(sorted((node_1, node_2, node_3)))

                        # skip triangles when already counted
                        if current_triangle in self.triangles2edges:
                            continue

                        if self.graph.directed:
                            # add each directed edge
                            self._add_directed_triangle(node_1, node_2, current_triangle)
                            self._add_directed_triangle(node_2, node_3, current_triangle)
                            self._add_directed_triangle(node_1, node_3, current_triangle)
                        else:
                            # update edges2triangles -- add all possible pairs of nodes,
                            # in both directions
                            for (u,v) in ((a,b) for idx, a in enumerate(current_triangle) for b in current_triangle[idx+1:]):
                                self.edges2triangles[(u,v)].append(current_triangle)
                                self.triangles2edges[current_triangle].append((u,v))
                                
                                self.edges2triangles[(v,u)].append(current_triangle)
                                self.triangles2edges[current_triangle].append((v,u))

    def update_triangles(self, edge_to_swap, permutation):
        
        """
            Update the sets of triangles by looking at each edge swap:

            - if the initial edge was involved in a triangle, remove triangle from sets
            - if the goal edge creates a triangle, add it to the sets
        """
        for (u, v), (x,y) in zip(edge_to_swap, permutation):
            if self.graph.directed:
                goal_edge = (u, y)
            else:
                goal_edge = (u, y) if u < y else (y ,u)

            # destroyed triangles
            if (u, v) in self.edges2triangles:

                # get all destroyed triangles
                destroyed_triangles = self.edges2triangles[(u,v)].copy() 
                # for each triangle, remove them and remove edges 
                for current_triangle in destroyed_triangles:

                    for edge in self.triangles2edges[current_triangle]:
                        self.edges2triangles[edge].remove(current_triangle)
                        if len(self.edges2triangles[edge]) == 0:
                            del self.edges2triangles[edge]
                    del self.triangles2edges[current_triangle]


            if (not self.graph.directed) and (v, u) in self.edges2triangles: # replace by not directed TODO 
                destroyed_triangles = self.edges2triangles[(v,u)].copy() 

                for current_triangle in destroyed_triangles:
                    for edge in self.triangles2edges[current_triangle]:
                        #try:
                        self.edges2triangles[edge].remove(current_triangle)
                        if len(self.edges2triangles[edge]) == 0:
                            del self.edges2triangles[edge]
                    del self.triangles2edges[current_triangle]

            # created triangles
            created = []
            for neigh in self.graph.neighbors[u]: # neighbors has already been updated
                if neigh == y:
                    continue
                if (neigh, y) in self.graph.edges or (y, neigh) in self.graph.edges:

                    current_triangle = tuple(sorted((u, y, neigh)))
                    created.append(current_triangle)
                    #if (current_triangle not in self.triangles2edges):
                    #    # triangle has already been acounted for 
                    #    continue

                    if self.graph.directed:
                            self._add_directed_triangle(u, y, current_triangle)
                            self._add_directed_triangle(y, neigh, current_triangle)
                            self._add_directed_triangle(neigh, u, current_triangle)
                    else:
                        for (node_1, node_2) in ((a,b) for idx, a in enumerate(current_triangle) for b in current_triangle[idx+1:]):
                            self.edges2triangles[(node_1, node_2)].append(current_triangle)
                            self.triangles2edges[current_triangle].append((node_1, node_2))
                            
                            self.edges2triangles[(node_2, node_1)].append(current_triangle)
                            self.triangles2edges[current_triangle].append((node_2, node_1))

        updated_triangles2edges = self.triangles2edges.copy()
        updated_edges2triangles = self.edges2triangles.copy()

        self.count_triangles()

        #for triangle in updated_triangles2edges:
        #    try:
        #        assert triangle in self.triangles2edges
        #        assert len(updated_triangles2edges[triangle]) == len(self.triangles2edges[triangle])
        #    except:
        #        #ipdb.set_trace()
        #        assert triangle in self.triangles2edges
        #        assert len(updated_triangles2edges[triangle]) == len(self.triangles2edges[triangle])

        #for edge in updated_edges2triangles:
        #    assert edge in self.edges2triangles
        #    for triangle in updated_edges2triangles[edge]:
        #        assert triangle in self.edges2triangles[edge]

    def init_joint_degree(self):
        max_degree = 0
        for node in self.graph.neighbors:
            if len(self.graph.neighbors[node]) > max_degree:
                max_degree = len(self.graph.neighbors[node])

        # initialize matrix
        self.joint_degree = np.zeros((max_degree, max_degree))

        # compute matrix // TODO : ATTENTION indice - 1
        for node in self.graph.neighbors:
            for neighbor in self.graph.neighbors[node]:
                deg_1 = len(self.graph.neighbors[node]) - 1
                deg_2 = len(self.graph.neighbors[neighbor]) - 1

                # each edge is added twice
                self.joint_degree[min(deg_1, deg_2), max(deg_1, deg_2)] += 1/2
                self.joint_degree[max(deg_1, deg_2), min(deg_1, deg_2)] += 1/2

    def update_joint_degree(self, edge_to_swap, permutation):
        updated_joint_degree = self.joint_degree.copy()
        for (u, v), (x,y) in zip(edge_to_swap, permutation):

            if self.graph.directed:
                goal_edge = (u, y)
            else:
                goal_edge = (u, y) if u < y else (y ,u)
            _neighbors = dict()
            _neighbors[u] = self.graph.neighbors[u].copy()
            _neighbors[y] = self.graph.neighbors[y].copy()
            if self.graph.directed:
                v_idx, u_idx, v_out_idx, u_in_idx = self.graph.edges[(u,v)]
                y_idx, x_idx, y_out_idx, x_in_idx = self.graph.edges[(x,y)]
            else:
                v_idx = self.graph.edges[(u,v)]
                u_idx = self.graph.edges[(v,u)]
                y_idx = self.graph.edges[(x,y)]
                x_idx = self.graph.edges[(y,x)]
            
            # get updated neighborhoods
            _neighbors[u][v_idx] = y
            _neighbors[y][x_idx] = u

            deg_u = len(_neighbors[u]) - 1
            deg_v = len(self.graph.neighbors[v]) -1
            deg_x = len(self.graph.neighbors[x]) -1
            deg_y = len(_neighbors[y]) -1


            updated_joint_degree[min(deg_u, deg_v), max(deg_u, deg_v)] -= 1/2
            updated_joint_degree[max(deg_u, deg_v), min(deg_u, deg_v)] -= 1/2

            updated_joint_degree[min(deg_x, deg_y), max(deg_x, deg_y)] -= 1/2
            updated_joint_degree[max(deg_x, deg_y), min(deg_x, deg_y)] -= 1/2

            updated_joint_degree[min(deg_u, deg_y), max(deg_u, deg_y)] += 1#/2
            updated_joint_degree[max(deg_u, deg_y), min(deg_u, deg_y)] += 1#/2

        return updated_joint_degree

    def run(self, N_swap=None):
        """
            K-edge swap algorithm.
            Start by computing assortativity initial value, then 
            perform N_swap, each time checking the constraints and computing
            metrics.
        """
        # populate assortativity values
        window = []

        if N_swap == None:
            N_swap = self.N_swap

        accept_rate = 0
        refusal_rate = 0

        # initialize values
        self.init_assortativity()
        self.init_joint_degree()
        self.count_triangles()

        # run N_swap swap
        #pb = ProgressBar()
        for swap_idx in range(self.N_swap):
            
            # pick k, permutation, and check if swap can be accepted
            k = self.pick_k()
            edge_to_swap, permutation, edge_to_swap_idx = self.find_swap(k)
            accept_permutation = self.check_swap(edge_to_swap, permutation)
            accept_jd = self.update_joint_degree(edge_to_swap, permutation)

            # if swap is accepted, perform swap and update graph metrics values
            if (accept_permutation and accept_jd):
                accept_rate += 1 
                self.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)

                self.update_triangles(edge_to_swap, permutation)
                self.update_assortativity(edge_to_swap, permutation)
                
                #self.metric()
            else:
                refusal_rate += 1
            window.append(self.assortativity)
        print(f'accepted : {accept_rate} , refused : {refusal_rate}')
        return window

def main():
    parser = argparse.ArgumentParser(description='k edge swap')
    parser.add_argument('-f', '--dataset', type=str, default="./gp_references.txt",
            help='path to the dataset')
    parser.add_argument('-o', '--output', type=str, default="./gp_references.out",
            help='path to the output')
    parser.add_argument('-n', '--N_swap', type=int, default=1000000,
            help='number of swap')
    parser.add_argument('-g', '--gamma', type=int, default=2,
	    help='exponent of zipf law, for pick K value')
    parser.add_argument('-d', '--directed', action='store_true', default=False,
            help='enable if input graph is directed')
    parser.add_argument('--check', action='store_true', default=False,
            help='enable to make some unit test during run. Default to false, significantly slows run.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
            help='increase verbosity')
    #parser.add_argument('--debug', action='store_true', default=False,
    #        help='enable debugging, user assertions to check that all is working')

    args = parser.parse_args()

    #file_in = "./gp_references.txt"

    mygraph = Graph(args.directed)
    print('reading graph')
    mygraph.read_ssv(args.dataset)
    print('performing swaps')
    mc = MarkovChain(mygraph, args.N_swap, args.gamma)
    mc.run()
    print('writing graph')
    mc.graph.to_ael(args.output)

if __name__ == "__main__": 
    main()

