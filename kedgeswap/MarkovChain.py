# This file is part of K-edge-swap.
#
#    K-edge-swap is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    K-edge-swap is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with K-edge-swap. If not, see <https://www.gnu.org/licenses/>. 

""" MarkovChain class, used to perform k-edge on a Graph object.
"""

import os
import gzip
import copy
import argparse
import numpy as np
from numpy.f2py.auxfuncs import throw_error

from kedgeswap.Graph import Graph
from progressbar import ProgressBar
from collections import defaultdict

class MarkovChain:
    """ make swaps """

    def __init__(self, graph, N_swap = 0, gamma=0, use_jd=False, use_fixed_triangle=False, use_triangles=False, use_assortativity=False, use_mutualdiades=False, verbose=False, keep_record=False, log_dir = None, debug=False):
        """
            Class to handle k-edge random swap

            Attributes:
            -----------
            graph: Graph object
                graph stored as an adjacency list, can be directed or not.
            N_swap: int
                the number of swaps to perform on the graph
            gamma: int
                parameter used for zipf distribution to pick k value at each round
            force_k: bool
                if true, force edge swap to be exactly of k edges (cyclic 
                permutation)
            assortativity: float
                store assortativity value
            D: float
                constant denominator used to compute assortativity (compute once)
            edges2triangles: dict(list)
                map an edge to its triangles
            triangles2edges: dict(list)
                map a triangle to its edges
            possible_ks: list(int)
                list of possible values of k
            k_distrib: list(float)
                probabilities of picking each k (not normalized yet)
            use_jd: bool
                if True, edge swaps will keep the joint degree matrix fixed
            use_triangles: bool
                if True, follow convergence by following the number of triangles
            use_assortativity: bool
                if True, follow convergence by following the assortativity
            use_mutualdiades: bool
                if True, the swap keep the number of mutual dyads constant
            joint_degree: np.array
                the joint degree matrix
            accept_rate: int
                number of accepted swaps in current batch of swaps
            refusal_rate: int
                number of refused swaps in current batch of swaps
            accept_rate_byk: dict(int)
                number of accepted swaps per k value
            refusal_rate_byk: dict(int)
                number of refused swaps per k value
            verbose: bool
                if enabled, output logs are more detailed
            keep_record: bool
                if enabled, write graphs at each step of the markov chain, and the edge swap
            log_dir: str
                if keep_record is enabled, log_dir specifies a folder in which to write the graphs
            debug: bool
                if enabled, adds check and log output. Used for debugging purposes only.
        """
        print(use_mutualdiades)
        self.graph = graph
        self.N_swap = N_swap

        # parameters to choose number of edges to swap
        self.gamma = gamma
        self.possible_ks = range(2, graph.M)
        self.k_distrib = np.array([1/(k**self.gamma) for k in self.possible_ks])
        self.force_k = False

        # assortativity
        self.assortativity = 0
        self.D = 0 # assortativity denominator - does not depend on links
        
        # triangles
        self.edges2triangles = defaultdict(list)
        self.triangles2edges = defaultdict(list)
        self.initial_trianglenumber = 0

        # constraints
        self.use_jd = use_jd
        self.use_fixed_triangle = use_fixed_triangle # use_triangle and use_fixed_triangle are mutually exclusive,
                                                     # as fixed one is a generation constraint while the other is a convergence constraint.
        self.use_triangles = use_triangles
        self.use_assortativity = use_assortativity # use_assortativity and use_triangles are mutually exclusive
        self.use_mutualdiades = use_mutualdiades
        self.joint_degree = np.zeros(0)

        # debug
        self.verbose = verbose
        self.keep_record = keep_record
        self.output_file = 0 # number of graph dumped
        self.log_dir = log_dir # directory to dump graph and swap when asked
        self.debug = debug

        # acceptation rate 
        self.accept_rate = 0
        self.refusal_rate = 0
        self.accept_rate_byk = defaultdict(int)
        self.refusal_rate_byk = defaultdict(int)

    def __dump__(self, edge_to_swap, permutation, n_cycle, n_swapped, output_file):
        """Write graph and permutation, useful for debugging"""
        with gzip.open(output_file, 'wb') as fout:
            fout.write('neighbors\n'.encode())
            for node in self.graph.neighbors:
                fout.write(f'{node}: {self.graph.neighbors[node]}\n'.encode())
            fout.write('edges\n'.encode())
            for edge in self.graph.edges:
                fout.write(f'{edge}: {self.graph.edges[edge]}\n'.encode())
            fout.write('edges2triangles\n'.encode())
            for edge in self.edges2triangles:
                fout.write(f'{edge}: {self.edges2triangles[edge]}\n'.encode())
            fout.write('triangles2edges\n'.encode())
            for triangle in self.triangles2edges:
                fout.write(f'{triangle}: {self.triangles2edges[triangle]}\n'.encode())
            fout.write('edge_to_swap and permutation\n'.encode())
            for ((u,v), (x,y)) in zip(edge_to_swap, permutation):
                fout.write(f'{(u,v)}, {(x,y)}\n'.encode())
            fout.write(f'number of cycle {n_cycle}, number of edges swapped {n_swapped}\n'.encode())

    def pick_k(self):
        """
            Pick k value using powerlaw distribution. The exponent of the powerlaw can be fixed by the
            gamma argument.

            Return
            ------
            k: int
                number of edges to swap
        """
        # minimum k is 2
        k = np.random.choice(a=self.possible_ks ,p=1/sum(self.k_distrib) * self.k_distrib)

        return k

    def find_swap(self, k):
        """ 
            Randomly pick k edges to swap, and randomly pick a permutation
            When self.force_k == True, permutation is a cyclic permutation,
            else it is a random permutation, with possible identity for some edges.


            Parameters
            ----------
            k: int
                number of edges to swap

            Return
            ------
            edge_to_swap: list(tuples)
                list of the edges to swap
            permutation: list(tuples)
                list of the edges with which we should swap the\
                edges in edge_to_swap
            _edge_to_swap: list(int)
                indexes in unique_edges of the edges in edge_to_swap

        """
        #valid_permutation = False
        # pick edge indexes
        _edge_to_swap = np.random.choice(len(self.graph.unique_edges), k, replace=False)

        if self.graph.directed:
            edge_to_swap = [self.graph.unique_edges[e_idx] for e_idx in _edge_to_swap]
        else:
            # for undirected graphs, pick edges directions
            edge_to_swap = [(self.graph.unique_edges[e_idx][1], self.graph.unique_edges[e_idx][0]) 
                                if np.random.choice([True, False]) 
                       else (self.graph.unique_edges[e_idx][0], self.graph.unique_edges[e_idx][1]) for e_idx in _edge_to_swap]

        permutation = edge_to_swap.copy() # find permutation by shuffling list of edges to swap

        if self.force_k:
            # if force_k, permutation is cyclic, to force the swap to be of exactly k edges
            cycle = np.random.randint(1,k)
            permutation = [edge_to_swap[idx - cycle] for idx in range(len(edge_to_swap))]
        else:
            # if !force_k, permutation is of k edges or less, can "swap" an edge with itself.
            np.random.shuffle(permutation) 

        return edge_to_swap, permutation, _edge_to_swap

    def create_partial_local_graph(self, edges):
        """
        Crée un sous-graphe local pour un ensemble d'arêtes,
        en gardant les voisins originaux des nœuds impliqués.

        Parameters
        ----------
        edges : list of tuple
            Liste des arêtes impliquées dans le swap

        Returns
        -------
        local_graph : Graph
            Copie locale contenant :
            - Tous les voisins des nœuds impliqués
            - TOUTES les arêtes entre nœuds impliqués
            - Les arêtes "actives" du swap pour la modification
        """

        graph = self.graph

        nodes = set()
        for u, v in edges:
            nodes.add(u)
            nodes.add(v)

        for node in list(nodes):
            nodes.update(graph.neighbors[node])

        local_graph = Graph(directed=graph.directed)

        unique_edges = set()

        for u in nodes:
            for v in graph.neighbors[u]:
                if v not in nodes:
                    continue

                if graph.directed:
                    local_graph.neighbors[u].append(v)
                    local_graph.edges[(u, v)] = len(local_graph.neighbors[u]) - 1
                    unique_edges.add((u, v))

                else:
                    if (u, v) not in local_graph.edges:
                        local_graph.neighbors[u].append(v)
                        local_graph.edges[(u, v)] = len(local_graph.neighbors[u]) - 1

                        local_graph.neighbors[v].append(u)
                        local_graph.edges[(v, u)] = len(local_graph.neighbors[v]) - 1

                        unique_edges.add((min(u, v), max(u, v)))

        local_graph.unique_edges = list(unique_edges)
        local_graph.N = len(nodes)
        local_graph.M = len(unique_edges)

        global_index_map = {e: i for i, e in enumerate(self.graph.unique_edges)}
        local_to_global = {i: global_index_map[e] for i, e in enumerate(local_graph.unique_edges)}
        global_to_local = {global_idx: local_idx for local_idx, global_idx in local_to_global.items()}

        return local_graph, global_to_local

    def perform_local_swap(self, local_graph, edge_to_swap, permutation, edge_to_swap_idx, dico):
        """
        Effectue un swap local sur un sous-graphe, en mettant à jour les voisins impliqués et les autres voisins.

        Parameters
        ----------
        local_graph : Graph
            Le sous-graphe local à modifier
        edge_to_swap : list of tuple
            Liste des arêtes à échanger
        permutation : list of tuple
            Liste des arêtes cibles pour le swap
        edge_to_swap_idx : list of int
        dico : list of index global -> local
        """
        for (u, v), (x, y), e_idx in zip(edge_to_swap, permutation, edge_to_swap_idx):

            if local_graph.directed:
                goal_edge = (u, y)
            else:
                goal_edge = (u, y) if u < y else (y, u)
            local_index = dico[e_idx]
            local_graph.unique_edges[local_index] = goal_edge

            if local_graph.directed:
                v_idx, u_idx, v_out_idx, u_in_idx = local_graph.edges[(u, v)]
                y_idx, x_idx, y_out_idx, x_in_idx = local_graph.edges[(x, y)]
                local_graph.out_neighbors[u][v_out_idx] = y
                local_graph.in_neighbors[y][x_in_idx] = u

                local_graph.edges[(u, y)] = (v_idx, x_idx, v_out_idx, x_in_idx)
            else:
                v_idx = local_graph.edges[(u, v)]
                u_idx = local_graph.edges[(v, u)]
                y_idx = local_graph.edges[(x, y)]
                x_idx = local_graph.edges[(y, x)]

                local_graph.edges[(u, y)] = v_idx
                local_graph.edges[(y, u)] = x_idx

            local_graph.neighbors[u][v_idx] = y # on change v dans neighbors (u)
            local_graph.neighbors[y][x_idx] = u
        for (u, v), (x,y) in zip(edge_to_swap, permutation):
            del local_graph.edges[(u,v)]
            if not local_graph.directed:
                del local_graph.edges[(v,u)]

    def delta_local_triangle(self, local_graph, edge_to_swap, permutation):
        """
        Calcule le delta du nombre de triangles dans un sous-graphe local après un swap.

        Cette fonction calcule le changement net du nombre de triangles sans modifier les structures
        de données globales (edges2triangles, triangles2edges). Elle utilise la même logique que
        update_triangles mais retourne seulement le delta.

        Parameters
        ----------
        local_graph : Graph
            Le sous-graphe local après le swap local (local_graph a déjà été modifié par perform_local_swap)
        edge_to_swap : list of tuple
            Liste des arêtes à échanger (arêtes avant le swap)
        permutation : list of tuple
            Liste des arêtes cibles pour le swap (arêtes après le swap)

        Returns
        -------
        delta_triangle : int
            Le changement net du nombre de triangles après le swap
        """
        delta = 0
        destroyed_triangles_set = set()
        created = set()
        created_triangles_set = set()

        for (u, v), (x,y) in zip(edge_to_swap, permutation):
            if local_graph.directed:
                goal_edge = (u, y)
            else:
                goal_edge = (u, y) if u < y else (y ,u)

            if (u, v) in self.edges2triangles:
                destroyed_triangle = self.edges2triangles[(u, v)].copy()
                for triangle in destroyed_triangle:
                    destroyed_triangles_set.add(triangle)

            if (not self.graph.directed) and (v, u) in self.edges2triangles:
                destroyed_triangles = self.edges2triangles[(v,u)].copy()
                for triangle in destroyed_triangles:
                    destroyed_triangles_set.add(triangle)

            for neigh in local_graph.neighbors[u]:
                if neigh == y:
                    continue
                if (neigh, y) in local_graph.edges or (y, neigh) in local_graph.edges:
                    current_triangle = tuple(sorted((u, y, neigh)))
                    created.add(current_triangle)
        delta += len(created)
        delta -= len(destroyed_triangles_set)
        return delta
    def check_swap(self, edge_to_swap, permutation, edge_to_swap_idx):
        """
            Verify constraints to see if swap can be accepted or not

            Parameters
            ----------
            edge_to_swap: list(tuples)
                list of the edges to swap
            permutation: list(tuples)
                list of the edges with which we should swap the\
                edges in edge_to_swap
            edge_to_swap_idx: list(int)
                index of the edges in graph.unique_edges (useful when undirected)

            Returns
            -------
            swap_accepted: bool
                true if swap can be accepted

        """

        # list of the edges after permutation
        goal_edges = []

        # sets of broken and created dyads, to check if the
        # swap keeps the number of dyads fixed. (only if -md option is enabled)
        broken_diades = set()
        created_diades = set()
        for ((u,v), (x,y)) in zip(edge_to_swap, permutation):
            # goal edge is the result of permutation between (u,v) and (x,y)
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

        # check that we don't create multi-edges
        if not len(set(goal_edges)) == len(goal_edges):
            return False

        # check if joint degree matrix changes
        if self.use_jd:
            # check if joint degree matrix changed

            updated_jd = self.update_joint_degree(edge_to_swap, permutation)
            jd_changed = False
            for _, val in updated_jd.items():
                if val != 0:
                    jd_changed = True
                    break

            if jd_changed:
                return False
            #if not (updated_jd1 == self.joint_degree).all():
            #    return False, None
            #else:
            #    for key in updated_jd2:
            #        assert updated_jd2[key] == 0
        else:
            updated_jd1 = None

        # using the number of triangles as a constraint on generation,
        # check if the number of triangles change
        if self.use_fixed_triangle:
            #we do a copy of the sub-graph changed by the swap, i.e. the nodes implied in the swap and their neighboors.

            #we check the delta of the number of triangle which need to be equal to zero

            local_graph, dico_globaltolocal = self.create_partial_local_graph(edge_to_swap)
            temp_mc = MarkovChain(local_graph)
            temp_mc.count_triangles()
            init_number_triangle = len(temp_mc.triangles2edges)

            self.perform_local_swap(local_graph, edge_to_swap, permutation, edge_to_swap_idx, dico_globaltolocal)

            temp_mc.update_triangles(edge_to_swap, permutation)
            new_number_of_triangles = len(temp_mc.triangles2edges)

            delta_triangle = new_number_of_triangles - init_number_triangle
            if delta_triangle != 0:
                return False

        # check if total number of mutual diades changes
        #if self.graph.directed and self.use_mutualdiades:
        #    if len(broken_diades) != len(created_diades):
        #        return False
        
        #if len(broken_diades) != 0 or len(created_diades) != 0 :
        if self.graph.directed and self.use_mutualdiades:
            old_dyads, new_dyads = self.check_dyads(edge_to_swap, permutation)
            if len(old_dyads) != len(new_dyads):
                return False


        return True

    def check_dyads(self,edge_to_swap, permutation):
        # sets of dyads before and after swap
        old_dyad = set()
        new_dyad = set()
        graph_outneigh = copy.deepcopy(self.graph.out_neighbors)
        
        swapped_nodes = set()
        for (u, v), (x,y) in zip(edge_to_swap, permutation):

            #add nodes to set of changing nodes
            swapped_nodes.add(u)
            swapped_nodes.add(v)
            swapped_nodes.add(x)
            swapped_nodes.add(y)

            if self.graph.directed:
                goal_edge = (u, y)
            else:
                goal_edge = (u, y) if u < y else (y ,u)

            v_idx, u_idx, v_out_idx, u_in_idx = self.graph.edges[(u,v)]
            y_idx, x_idx, y_out_idx, x_in_idx = self.graph.edges[(x,y)]

            # simulate the swap 
            graph_outneigh[u][v_out_idx] = y

        # measure the dyads sets involving the swapped nodes
        swapped_nodes_l = list(swapped_nodes)
        for u in swapped_nodes: #graph_outneigh: 
            for v in graph_outneigh[u]:
                if v not in swapped_nodes:
                    continue
                if u in graph_outneigh[v] and v in graph_outneigh[u]:
                    new_dyad.add((min(u,v), max(u,v)))
        
        for u in swapped_nodes: #self.graph.out_neighbors: 
            for v in self.graph.out_neighbors[u]:
                if v not in swapped_nodes:
                    continue
                if u in self.graph.out_neighbors[v] and v in self.graph.out_neighbors[u]:
                    old_dyad.add((min(u,v), max(u,v)))
        
        return old_dyad, new_dyad

    def perform_swap(self, edge_to_swap, permutation, edge_to_swap_idx):
        """
            When permutation is accepted, swap the edges in the graph data structure.

            Parameters
            ----------
            edge_to_swap: list(tuples)
                list of the edges to swap
            permutation: list(tuples)
                list of the edges with which we should swap the\
                edges in edge_to_swap
            edge_to_swap_idx: list(int)
                index of the edges in graph.unique_edges (useful when undirected)
        """
        for (u, v), (x,y), e_idx in zip(edge_to_swap, permutation, edge_to_swap_idx):

            # naming departure edge = (u,v) and arrival edge = (x,y) , goal edge = (u, y)
            if self.graph.directed:
                goal_edge = (u, y)
            else:
                goal_edge = (u, y) if u < y else (y ,u)
            #old_edge = self.graph.unique_edges[e_idx] # TODO comment - not used
            self.graph.unique_edges[e_idx] = goal_edge

            #old_edge = (u, v) if u < v else (v, u)

            if self.graph.directed:
                # directed graphs
                v_idx, u_idx, v_out_idx, u_in_idx = self.graph.edges[(u,v)]
                y_idx, x_idx, y_out_idx, x_in_idx = self.graph.edges[(x,y)]
                self.graph.out_neighbors[u][v_out_idx] = y
                self.graph.in_neighbors[y][x_in_idx] = u

                self.graph.edges[(u,y)] = (v_idx, x_idx, v_out_idx, x_in_idx)
            else:
                # undirected graphs
                v_idx = self.graph.edges[(u,v)]
                u_idx = self.graph.edges[(v,u)]
                y_idx = self.graph.edges[(x,y)]
                x_idx = self.graph.edges[(y,x)]

                self.graph.edges[(u,y)] = v_idx
                self.graph.edges[(y,u)] = x_idx

            # perform swap
            self.graph.neighbors[u][v_idx] = y # on change v dans neighbors (u)
            self.graph.neighbors[y][x_idx] = u

        # remove old edges from graph.edges
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

        # loop to compute S2 and S3
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
        self.D = S1 * S3 - S2 * S2 # denominator does not change when edges are swapped
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

            #if self.graph.directed:
            #    deg_u += len(self.graph.in_neighbors[u])
            #    deg_v += len(self.graph.in_neighbors[v])
            #    deg_x += len(self.graph.in_neighbors[x])
            #    deg_y += len(self.graph.in_neighbors[y])

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

               | we store each triangle in a set of tuplet ((u,v,w)) where \
               | u, v and w are the node, with u < v < w, and we store each link\
               | involved in the triangle in edges_in_triangles (pointing to the triangle tuplet)\
            For directed graphs:
            
               | we store each triangle thrice in a set of tuplet, with each node as a starting point,\
               | e.g. for triangle (u,v,w) we store {(u,v,w), (v,w,u), (w,u,v)}. We store each link\
               | involved in the triangle in edges_in_triangles (pointing to the triangle tuplet)\
        """
        for node_1 in self.graph.neighbors.keys():
            
            # skip nodes of degree < 2, they can't have triangles...
            if len(self.graph.neighbors[node_1]) < 2:
                continue
            
            # check neighborhoods or neighbors of node_1
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

                # for each triangle in destroyed, remove it and remove its edges 
                for current_triangle in destroyed_triangles:
                    for edge in self.triangles2edges[current_triangle]:
                        self.edges2triangles[edge].remove(current_triangle)
                        if len(self.edges2triangles[edge]) == 0:
                            del self.edges2triangles[edge]
                    del self.triangles2edges[current_triangle]

            # destroyed triangles for undirected graphs, check other directions of each edge
            if (not self.graph.directed) and (v, u) in self.edges2triangles:
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
            for neigh in self.graph.neighbors[u]: # graph.neighbors has already been updated
                if neigh == y:
                    continue
                if (neigh, y) in self.graph.edges or (y, neigh) in self.graph.edges:

                    current_triangle = tuple(sorted((u, y, neigh)))
                    created.append(current_triangle)

                    # add triangle to edges2triangles and triangles2edges
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


    def init_joint_degree(self):
        """ Initialize the joint degree matrix.

            joint_degree[i - 1, j - 1] gives the number of links from nodes of
            degree i to nodes of the degree j.
            Initialise the joint degree matrix by looping over each node n, 
            then each neighbor nn of n, and incrementing joint_degree[deg(n), deg(nn)] by 1/2.
            (increment by 1/2 to take into account that each edge is added twice)
        """
        max_degree = 0
        for node in self.graph.neighbors:
            if len(self.graph.neighbors[node]) > max_degree:
                max_degree = len(self.graph.neighbors[node])

        # initialize matrix
        self.joint_degree = np.zeros((max_degree, max_degree))

        # compute matrix // BEWARE : index for degree i is (i-1) 
        for node in self.graph.neighbors:
            for neighbor in self.graph.neighbors[node]:
                deg_1 = len(self.graph.neighbors[node]) - 1
                deg_2 = len(self.graph.neighbors[neighbor]) - 1

                # each edge is added twice
                self.joint_degree[min(deg_1, deg_2), max(deg_1, deg_2)] += 1/2
                self.joint_degree[max(deg_1, deg_2), min(deg_1, deg_2)] += 1/2

    def update_joint_degree_old(self, edge_to_swap, permutation):
        """ 
            DEPRECATED - Only used for unit testing !
            Given a permutation, compute the changed in the joint degree matrix.
            Compute the update by copying the joint degree matrix, looping over
            each edge swap, decrementing the joint degree value for the 'old' edges
            and incrementing the joint degree value for the 'new' edges.


            Parameters:
            edge_to_swap : list of the edges to swap
            permutation  : list of the edges with which we should swap the\
                           edges in edge_to_swap

            Return :
            updated_joint_degree : np.array, the updated version of the joint degree matrix\
                                   if the permutation given in input is performed.

        """
        # get copy of joint degree matrix
        updated_joint_degree = self.joint_degree.copy()

        # loop over each edge swap
        for (u, v), (x,y) in zip(edge_to_swap, permutation):

            if self.graph.directed:
                goal_edge = (u, y)
            else:
                goal_edge = (u, y) if u < y else (y ,u)

            # copy the neighborhood of u and y and alter them as if the swap was performed
            #_neighbors = dict()
            #_neighbors[u] = self.graph.neighbors[u].copy()
            #_neighbors[y] = self.graph.neighbors[y].copy()
            #if self.graph.directed:
            #    v_idx, u_idx, v_out_idx, u_in_idx = self.graph.edges[(u,v)]
            #    y_idx, x_idx, y_out_idx, x_in_idx = self.graph.edges[(x,y)]
            #else:
            #    v_idx = self.graph.edges[(u,v)]
            #    u_idx = self.graph.edges[(v,u)]
            #    y_idx = self.graph.edges[(x,y)]
            #    x_idx = self.graph.edges[(y,x)]
            #
            #_neighbors[u][v_idx] = y
            #_neighbors[y][x_idx] = u


            # get degree of each node involved
            deg_u = len(self.graph.neighbors[u]) - 1
            deg_v = len(self.graph.neighbors[v]) -1
            deg_x = len(self.graph.neighbors[x]) -1
            deg_y = len(self.graph.neighbors[y]) -1


            # update the joint degree values for the previous degrees
            updated_joint_degree[min(deg_u, deg_v), max(deg_u, deg_v)] -= 1/2
            updated_joint_degree[max(deg_u, deg_v), min(deg_u, deg_v)] -= 1/2

            updated_joint_degree[min(deg_x, deg_y), max(deg_x, deg_y)] -= 1/2
            updated_joint_degree[max(deg_x, deg_y), min(deg_x, deg_y)] -= 1/2

            updated_joint_degree[min(deg_u, deg_y), max(deg_u, deg_y)] += 1#/2
            updated_joint_degree[max(deg_u, deg_y), min(deg_u, deg_y)] += 1#/2

        return updated_joint_degree

    def update_joint_degree(self, edge_to_swap, permutation):
        """ Given a permutation, compute the changed in the joint degree matrix.
            Compute the update by copying the joint degree matrix, looping over
            each edge swap, decrementing the joint degree value for the 'old' edges
            and incrementing the joint degree value for the 'new' edges.


            Parameters:
            edge_to_swap : list of the edges to swap
            permutation  : list of the edges with which we should swap the\
                           edges in edge_to_swap

            Return :
            updated_joint_degree : np.array, the updated version of the joint degree matrix\
                                   if the permutation given in input is performed.

        """
        # get copy of joint degree matrix
        #updated_joint_degree = self.joint_degree.copy()
        updated_joint_degree = defaultdict(int)

        # loop over each edge swap
        for (u, v), (x,y) in zip(edge_to_swap, permutation):

            if self.graph.directed:
                goal_edge = (u, y)
            else:
                goal_edge = (u, y) if u < y else (y ,u)

            # get degree of each node involved
            deg_u = len(self.graph.neighbors[u]) - 1
            deg_v = len(self.graph.neighbors[v]) -1
            deg_x = len(self.graph.neighbors[x]) - 1
            deg_y = len(self.graph.neighbors[y]) - 1


            # update the joint degree values for the previous degrees
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
        def write_swap(ets, p):
            """ for debug only - write all the swaps """
            with  open('swap', 'a') as fout:
                fout.write(f'{len(ets)}\n')
                for e1, e2 in zip(ets, p):
                    fout.write(f'{e1[0]} {e1[1]} : {e2[0]} {e2[1]}\n')
                fout.write(f'\n\n')

        def detect_cycles(ets, p):
            """ for debug - count number of cycles in current swap"""
            all_tagged = []
            flat_all_tagged = []
            for e1, e2 in zip(ets, p):
                if e1==e2:
                    continue
                if e1 in flat_all_tagged:
                    continue
                tagged = []
                tagged.append(e2)
                flat_all_tagged.append(e2)
                __e2 = e2
                while __e2 != e1:
                    e2_idx = ets.index(__e2)
                    __e2 = p[e2_idx]
                    tagged.append(__e2)
                    flat_all_tagged.append(__e2)
                all_tagged.append(tagged)
            return len(all_tagged), len(flat_all_tagged)

        # populate assortativity values in window
        window = []

        if N_swap == None:
            N_swap = self.N_swap

        accept_rate = 0
        refusal_rate = 0

        # initialize values
        if self.use_jd:
            self.init_joint_degree()
        if self.use_fixed_triangle:
            self.count_triangles()
            self.initial_trianglenumber = len(self.triangles2edges)

        if self.use_triangles:
            self.count_triangles()
        elif self.use_assortativity:
            self.init_assortativity()

        # run N_swap swaps
        for swap_idx in range(N_swap):

            # print a dot every 1000 swap to show progress
            #if self.verbose and (swap_idx % 50000 == 0):
            #    #print(f'swap {swap_idx}/{N_swap}')
            #    print('.', end='')

            # pick k, permutation, and check if swap can be accepted
            k = self.pick_k()
            edge_to_swap, permutation, edge_to_swap_idx = self.find_swap(k)
            accept_permutation = self.check_swap(edge_to_swap, permutation, edge_to_swap_idx)



            # if swap is accepted, perform swap and update graph metrics values
            if accept_permutation:

                # if debug is enabled, check that degree sequence is constant
                if self.debug:
                    debug_deg_seq = []
                    previous_debug_deg_seq = []

                    for node in range(self.graph.N):
                        previous_debug_deg_seq.append(len(self.graph.neighbors[node]))

                # add swap to list of accepted
                accept_rate += 1 
                self.accept_rate_byk[k] += 1

                # realise the swap
                self.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)


                # debug - check if degree sequence changed
                if self.debug:
                     for node in range(self.graph.N):
                        debug_deg_seq.append(len(self.graph.neighbors[node]))
                     assert debug_deg_seq == previous_debug_deg_seq, 'ERROR : degree sequence changed!' 

                # compute value of interest (assortativity/triangles) to follow convergence
                if self.use_assortativity:
                    self.update_assortativity(edge_to_swap, permutation)
                # we need to keep triangles also when it's a generative constraint
                elif self.use_triangles or self.use_fixed_triangle:
                    self.update_triangles(edge_to_swap, permutation)

                #if self.use_jd:
                #    self.joint_degree = updated_jd
                #write_swap(edge_to_swap, permutation) 

                # for debugging mostly - if keep_record is enabled, write graph and swap (as gzip)
                if self.keep_record:
                    n_cycle, n_edge_swap = detect_cycles(edge_to_swap, permutation)
                    self.output_file += 1
                    output_file = self.graph.dataset_name + f'_{self.output_file}.log.gz'
                    if self.log_dir is not None:
                        output_file = os.path.join(self.log_dir, output_file)
                    self.__dump__(edge_to_swap, permutation, n_cycle, n_edge_swap, output_file)
            else:
                # add swap to list of refused
                refusal_rate += 1
                self.refusal_rate_byk[k] += 1

            # populate assortativity values
            if self.use_assortativity:
                window.append(self.assortativity)
            elif self.use_triangles:
                window.append(len(self.triangles2edges))

        # store accept rate and refusal rate
        self.accept_rate = accept_rate
        self.refusal_rate = refusal_rate
        return window


