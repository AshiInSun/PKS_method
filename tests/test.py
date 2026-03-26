# This file is part of K-edge-swap.
#
#    K-edge-swap is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    K-edge-swap is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with Foobar. If not, see <https://www.gnu.org/licenses/>.
import sys

import pytest
import numpy as np
import os

from kedgeswap.Graph import Graph
from progressbar import ProgressBar

from kedgeswap.MarkovChain import MarkovChain

@pytest.fixture
def japanese_macaques(request):
    mygraph = Graph(True)
    mygraph.read_ssv(os.path.join(request.fspath.dirname,'japanese_macaques.tsv'))
    return mygraph 

@pytest.fixture
def euroroad(request):
    mygraph = Graph(False)
    mygraph.read_ssv(os.path.join(request.fspath.dirname,'euroroad.tsv'))
    return mygraph 

@pytest.fixture
def handcrafted(request):
    mygraph = Graph(False)
    mygraph.read_ssv(os.path.join(request.fspath.dirname,'handcrafted.tsv'))
    return mygraph 

@pytest.fixture
def handcrafted_directed(request):
    mygraph = Graph(True)
    mygraph.read_ssv(os.path.join(request.fspath.dirname,'handcrafted_directed.tsv'))
    return mygraph 

@pytest.fixture
def egograph(request):
    mygraph = Graph(False)
    # Load from the egograph_edges.txt file in the data folder
    egograph_path = os.path.join(request.fspath.dirname, '..', 'data', 'ucidata-zachary', 'egograph_edges.txt')
    mygraph.read_ssv(egograph_path)
    return mygraph

def test_directed_graph(japanese_macaques):
    #mygraph = Graph(True)
    #mygraph.read_ssv('data/japanese_macaques.tsv')#TODO
    mygraph=japanese_macaques
    for (u,v) in mygraph.edges:
        #assert (v,u) not in mygraph.edges
        
        v_idx, u_idx, v_out_idx, u_in_idx = mygraph.edges[(u,v)]

        assert mygraph.neighbors[u][v_idx] == v
        assert mygraph.neighbors[v][u_idx] == u
        assert mygraph.out_neighbors[u][v_out_idx] == v
        assert mygraph.in_neighbors[v][u_in_idx] == u

def test_undirected_graph(euroroad):
    #mygraph = Graph(False)
    #mygraph.read_ssv('data/euroroad.tsv')#TODO
    mygraph=euroroad
    for (u,v) in mygraph.edges:
        #assert (v,u) not in mygraph.edges
        
        v_idx = mygraph.edges[(u,v)]
        u_idx = mygraph.edges[(v,u)]

        assert mygraph.neighbors[u][v_idx] == v
        assert mygraph.neighbors[v][u_idx] == u

def test_directed_mc(japanese_macaques):
    # TODO : peut être ajouter test ou on enchaine un swap et son inverse + vérifier si on retourne bien au graphe de départ ?
    #mygraph = Graph(True)
    #mygraph.read_ssv('data/japanese_macaques.tsv')#TODO
    mygraph = japanese_macaques
    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 

    edge_to_swap = [(43, 34), (57, 62), (36, 7), (12, 51), (27, 48), (49, 62), (11, 46), (8, 23), (56, 22), (59, 61)]
    permutation = [(59, 61), (43, 34), (57, 62), (36, 7), (12, 51), (27, 48), (49, 62), (11, 46), (8, 23), (56, 22)]
    edge_to_swap_idx = [1090, 1185, 100, 458, 1015, 1123, 436, 333, 734, 915]

    accept_permutation = mc.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True
    mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)

    for (u, v), (x,y), e_idx in zip(edge_to_swap, permutation, edge_to_swap_idx):

        goal_edge = (u, y)
        old_edge = (u, v)
        assert goal_edge in mygraph.edges
        assert old_edge not in mygraph.edges
        assert goal_edge in mygraph.unique_edges
        assert old_edge not in mygraph.unique_edges
        assert mygraph.unique_edges[e_idx] == goal_edge
        assert len(set(mygraph.unique_edges)) == mygraph.M

        y_idx, u_idx, y_out_idx, u_in_idx = mygraph.edges[(u,y)]

        assert mygraph.neighbors[u][y_idx] == y
        assert mygraph.neighbors[y][u_idx] == u
        assert mygraph.out_neighbors[u][y_out_idx] == y
        assert mygraph.in_neighbors[y][u_in_idx] == u

    for (u,v) in mygraph.edges:
        #assert (v,u) not in mygraph.edges
        
        v_idx, u_idx, v_out_idx, u_in_idx = mygraph.edges[(u,v)]

        assert mygraph.neighbors[u][v_idx] == v
        assert mygraph.neighbors[v][u_idx] == u
        assert mygraph.out_neighbors[u][v_out_idx] == v
        assert mygraph.in_neighbors[v][u_in_idx] == u

def test_undirected_mc(euroroad):
    #mygraph = Graph(False)
    #mygraph.read_ssv('data/euroroad.tsv')#TODO FIXTURES
    mygraph=euroroad
    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 

    edge_to_swap = [(578, 767), (1041, 1042), (935, 936), (254, 255), (284, 310), (346, 965), (473, 474), (962, 963), (381, 382), (28, 29)]
    permutation = [(28, 29), (578, 767), (1041, 1042), (935, 936), (254, 255), (284, 310), (346, 965), (473, 474), (962, 963), (381, 382)]
    edge_to_swap_idx = [972, 1343, 1281, 502, 566, 662, 837, 1300, 709, 59]

    accept_permutation = mc.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True
    mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)

    for (u, v), (x,y), e_idx in zip(edge_to_swap, permutation, edge_to_swap_idx):

        goal_edge = (u, y) if u < y else (y, u)
        old_edge = (u, v)
        assert goal_edge in mygraph.edges
        assert old_edge not in mygraph.edges
        assert goal_edge in mygraph.unique_edges
        assert old_edge not in mygraph.unique_edges
        assert mygraph.unique_edges[e_idx] == goal_edge
        assert len(set(mygraph.unique_edges)) == mygraph.M

        y_idx = mygraph.edges[(u,y)]
        u_idx = mygraph.edges[(y,u)]

        assert mygraph.neighbors[u][y_idx] == y
        assert mygraph.neighbors[y][u_idx] == u

    for (u,v) in mygraph.edges:
        
        v_idx = mygraph.edges[(u,v)]
        u_idx = mygraph.edges[(v,u)]

        assert mygraph.neighbors[u][v_idx] == v
        assert mygraph.neighbors[v][u_idx] == u

def test_init_triangles(euroroad, japanese_macaques):
    # undirected
    #mygraph = Graph(False)
    #mygraph.read_ssv('data/euroroad.tsv')#TODO FIXTURES
    mygraph=euroroad
    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 
    mc.count_triangles()
    assert len(mc.triangles2edges) == 32

    # directed
    #mygraph = Graph(True)
    #mygraph.read_ssv('data/japanese_macaques.tsv')#TODO FIXTURES
    mygraph = japanese_macaques
    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 
    mc.count_triangles()
    assert len(mc.triangles2edges) == 9781


def test_update_triangles(euroroad, japanese_macaques):
    # undirected
    mygraph=euroroad
    #mygraph = Graph(False)
    #mygraph.read_ssv('data/euroroad.tsv')#TODO FIXTURES
    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 
    mc.count_triangles()

    edge_to_swap = [(469, 470), (1085, 1086), (428, 732)]
    permutation = [(1085, 1086), (428, 732), (469, 470)]
    edge_to_swap_idx = [831, 1363, 768]
    destroyed_triangles = [(428, 429, 732)]

    assert destroyed_triangles[0] in mc.triangles2edges
    
    accept_permutation = mc.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True
    mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)

    # check that the following triangles are correctly removed by swap
    assert destroyed_triangles[0] in mc.triangles2edges

    mc.update_triangles(edge_to_swap, permutation)

    assert destroyed_triangles[0] not in mc.triangles2edges
    
    updated_triangles2edges = mc.triangles2edges.copy()
    mc.count_triangles()
    for triangle in mc.triangles2edges:
        assert triangle in updated_triangles2edges
        for edge in mc.triangles2edges[triangle]:
            assert edge in updated_triangles2edges[triangle]

    for triangle in updated_triangles2edges:
        assert triangle in mc.triangles2edges
        assert len(updated_triangles2edges[triangle]) == len(mc.triangles2edges[triangle])

        for edge in updated_triangles2edges[triangle]:
            assert edge in mc.triangles2edges[triangle]

    # directed # TODO Split in two tests ? 
    mygraph = japanese_macaques
    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 
    mc.count_triangles()

    assert len(mc.triangles2edges) == 9781
    edge_to_swap = [(18, 33), (48, 62)]
    permutation = [(48, 62), (18, 33)]
    edge_to_swap_idx = [647, 1112]
    destroyed_triangles = [(1, 18, 33), (3, 18, 33), (5, 18, 33), (7, 18, 33), 
            (8, 18, 33), (11, 18, 33), (12, 18, 33), (13, 18, 33), (15, 18, 33), 
            (16, 18, 33), (18, 33, 36), (18, 33, 37), (18, 33, 38), (18, 33, 56), 
            (18, 21, 33), (18, 22, 33), (18, 23, 33), (18, 24, 33), (18, 25, 33), 
            (18, 28, 33), (18, 29, 33), (18, 31, 33), (18, 33, 53), (18, 33, 47), 
            (18, 33, 34), (6, 48, 62), (19, 48, 62), (28, 48, 62), (34, 48, 62), 
            (35, 48, 62), (40, 48, 62), (48, 50, 62), (48, 59, 62), (48, 49, 62), 
            (48, 53, 62), (48, 54, 62), (48, 55, 62), (48, 57, 62) ]

    created_triangles = [(18, 37, 62), 
            (16, 18, 62), (18, 38, 62), (18, 19, 62), 
            (18, 50, 62), (18, 28, 62), (18, 53, 62), (18, 34, 62), (18, 38, 62), 
            (3, 33, 48), (6, 33, 48), (10, 33, 48), (14, 33, 48), (17, 33, 48), 
            (21, 33, 48), (22, 33, 48), (28, 33, 48), (31, 33, 48), (33, 48, 49), 
            (33, 48, 53), (33, 48, 54), (33, 34, 48), (33, 35, 48), (33, 48, 55), 
            (33, 48, 57)]

    accept_permutation = mc.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True
    mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)

    for triangle in destroyed_triangles:
        assert triangle in mc.triangles2edges

    for triangle in created_triangles:
        assert triangle not in mc.triangles2edges

    mc.update_triangles(edge_to_swap, permutation)

    for triangle in destroyed_triangles:
        assert triangle not in mc.triangles2edges

    updated_triangles2edges = mc.triangles2edges.copy()
    mc.count_triangles()
    for triangle in mc.triangles2edges:
        assert triangle in updated_triangles2edges
        for edge in mc.triangles2edges[triangle]:
            assert edge in updated_triangles2edges[triangle]

    for triangle in updated_triangles2edges:
        assert triangle in mc.triangles2edges
        assert len(updated_triangles2edges[triangle]) == len(mc.triangles2edges[triangle])

        for edge in updated_triangles2edges[triangle]:
            assert edge in mc.triangles2edges[triangle]

    for triangle in created_triangles:
        assert triangle in mc.triangles2edges

def test_update_triangles_random(japanese_macaques):
    #mygraph = Graph(True)
    #mygraph.read_ssv('data/japanese_macaques.tsv')#TODO FIXTURES
    mygraph=japanese_macaques
    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 
    mc.count_triangles()
    k = 4
    for swap_idx in range(10):
        edge_to_swap, permutation, edge_to_swap_idx = mc.find_swap(k)
        accept_permutation = mc.check_swap(edge_to_swap, permutation)

        if (accept_permutation):
            mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)
            mc.update_triangles(edge_to_swap, permutation)
            updated_triangles2edges = mc.triangles2edges.copy()
            updated_edges2triangles = mc.edges2triangles.copy()

            mc.count_triangles()

            for triangle in updated_triangles2edges:
                assert triangle in mc.triangles2edges
                assert len(updated_triangles2edges[triangle]) == len(mc.triangles2edges[triangle])
            for edge in updated_edges2triangles:
                assert edge in mc.edges2triangles
                for triangle in updated_edges2triangles[edge]:
                    assert triangle in mc.edges2triangles[edge]


            for triangle in mc.triangles2edges:
                assert triangle in updated_triangles2edges
                for edge in mc.triangles2edges[triangle]:
                    assert edge in updated_triangles2edges[triangle]



            for edge in mc.edges2triangles:
                assert edge in updated_edges2triangles
                for triangle in mc.edges2triangles[edge]:
                    assert triangle in updated_edges2triangles[edge]

def test_update_assortativity(euroroad):
    #mygraph = Graph(False)
    #mygraph.read_ssv('data/euroroad.tsv')#TODO FIXTURES
    mygraph=euroroad
    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 
    mc.init_assortativity()

    edge_to_swap = [(578, 767), (1041, 1042), (935, 936), (254, 255), (284, 310), (346, 965), (473, 474), (962, 963), (381, 382), (28, 29)]
    permutation = [(28, 29), (578, 767), (1041, 1042), (935, 936), (254, 255), (284, 310), (346, 965), (473, 474), (962, 963), (381, 382)]
    edge_to_swap_idx = [972, 1343, 1281, 502, 566, 662, 837, 1300, 709, 59]

    accept_permutation = mc.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True
    mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)
    mc.update_assortativity(edge_to_swap, permutation)
    updated_assortativity = mc.assortativity
    mc.init_assortativity()

    print(updated_assortativity, mc.assortativity)
    assert updated_assortativity == mc.assortativity

#def test_edges2triangles():
#    mygraph = Graph(True)
#    mygraph.read_ssv('edge_list')
#    mc = MarkovChain(mygraph, 10, 2, False)
#    edge_to_swap = [(26, 31),(35, 59),(11, 9),(41, 58)]
#    permutation = [ (41, 58),(26, 31),(35, 59),(11, 9)]
#    mc.count_triangles()
#    accept = mc.check_swap(edge_to_swap, permutation)
#

def test_init_joint_degree(handcrafted):
    #mygraph = Graph(True)
    #mygraph.read_ssv('unit_clean')
    mygraph=handcrafted
    mc = MarkovChain(mygraph, 10, 2, False)
    mc.init_joint_degree()

    deg_count = dict()
    for node in mygraph.neighbors:
        if len(mygraph.neighbors[node]) in deg_count:
            deg_count[len(mygraph.neighbors[node])] += 1
        else:
            deg_count[len(mygraph.neighbors[node])] = 1
           
    #for i in range(mc.joint_degree.shape[0]):
    #    for j in range(i+1):
    #        mc.joint_degree[i,j] = mc.joint_degree[j,i]
    # sum of ith line should be the total number of links by nodes of degree i
    for degree in deg_count:
        assert sum(mc.joint_degree[:,degree-1]) == deg_count[degree] * degree 

def test_init_joint_degree_small(handcrafted):
    #mygraph = Graph(False)
    #mygraph.read_ssv('unit_clean')#TODO
    mygraph=handcrafted

    mc = MarkovChain(mygraph, 10, 2, False)
    mc.init_joint_degree()

    # only computing upper right triangle
    gold_joint_degree = np.array([[0,0,1,1],[0,0,0,2],[1,0,2,3],[1,2,3,2]])

    assert (mc.joint_degree == gold_joint_degree).all()

def test_update_joint_degree(handcrafted):
    #mygraph = Graph(False)
    #mygraph.read_ssv('unit_clean')#TODO
    mygraph = handcrafted

    mc = MarkovChain(mygraph, 10, 2, False)
    mc.init_joint_degree()

    # edge swap
    edge_to_swap = [(1, 2), (5,6)]
    permutation = [(5, 6), (1, 2)]
    edge_to_swap_idx = [1, 8]

    updated_joint_degree = mc.update_joint_degree_old(edge_to_swap, permutation)
    mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)
    mc.init_joint_degree()
    assert (mc.joint_degree == updated_joint_degree).all()

def test_update_joint_degree_directed(japanese_macaques):
    #mygraph = Graph(True)
    #mygraph.read_ssv('data/japanese_macaques.tsv')#TODO
    mygraph=japanese_macaques

    mc = MarkovChain(mygraph, 10, 2, False)
    edge_to_swap = [(5, 38), (46, 57), (3, 28), (46, 62)]
    permutation = [(46, 57), (3, 28), (46, 62), (5, 38)]
    edge_to_swap_idx = [178, 1156, 87, 1157]
    accept_permutation = mc.check_swap(edge_to_swap, permutation)
    mc.init_joint_degree()

    updated_joint_degree = mc.update_joint_degree_old(edge_to_swap, permutation)
    mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)
    mc.init_joint_degree()
    assert (mc.joint_degree == updated_joint_degree).all()

def test_mutualdiades(japanese_macaques, handcrafted_directed):
    # TODO find more examples, maybe on health dataset ?
    # directed
    mygraph = japanese_macaques
    mc = MarkovChain(mygraph, 10, 2, False, use_mutualdiades=True)

    edge_to_swap =[(59, 35), (21, 20)]
    permutation = [(21, 20), (59, 35)]
    accept_permutation = mc.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True # same number of mutual diades

    edge_to_swap = [(28, 46), (41, 24)]
    permutation = [(41, 24), (28, 46)]
    accept_permutation = mc.check_swap(edge_to_swap, permutation)
    assert accept_permutation == False # create one mutual diades

    # TODO find more examples, maybe on health dataset ?
    # directed
    mygraph = handcrafted_directed
    mc = MarkovChain(mygraph, 10, 2, False , use_mutualdiades=True) 

    edge_to_swap =[(0,1), (2,6)]
    permutation = [(2,6), (0,1)]
    accept_permutation = mc.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True # same number of mutual diades

    edge_to_swap = [(4,1), (2,6)]
    permutation = [(2,6), (4,1)] # break two diades, create one
    
    accept_permutation = mc.check_swap(edge_to_swap, permutation)
    assert accept_permutation == False # create one mutual diades


def test_delta_local_triangle_calculation(euroroad):
    """
    Test if delta_local_triangle correctly counts the difference of triangles before/after swap
    Uses the same functions as check_swap: create_partial_local_graph, perform_local_swap, delta_local_triangle
    This test uses the same swap data as test_update_triangles from euroroad dataset.
    """
    mygraph = euroroad
    mc = MarkovChain(mygraph, 10, 2, False)
    mc.count_triangles()

    # Same swap data from test_update_triangles (euroroad)
    edge_to_swap = [(469, 470), (1085, 1086), (428, 732)]
    permutation = [(1085, 1086), (428, 732), (469, 470)]
    edge_to_swap_idx = [831, 1363, 768]
    # This swap destroys the triangle (428, 429, 732)

    # Count triangles before swap
    triangles_count_before = len(mc.triangles2edges)

    # Use the same approach as check_swap: create a local graph, perform swap on it, compute delta
    local_graph, dico = mc.create_partial_local_graph(edge_to_swap)
    mc.perform_local_swap(local_graph, edge_to_swap, permutation)
    delta_triangle = mc.delta_local_triangle(local_graph, edge_to_swap, permutation)

    print(f"Delta from delta_local_triangle: {delta_triangle}")

    # Now perform the actual swap on the main graph to verify
    mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)
    mc.update_triangles(edge_to_swap, permutation)
    triangles_count_after = len(mc.triangles2edges)

    observed_delta = triangles_count_after - triangles_count_before

    print(f"Observed delta from actual swap: {observed_delta}")
    print(f"Triangle count before: {triangles_count_before}, after: {triangles_count_after}")

    # The delta from delta_local_triangle should match the observed delta
    assert delta_triangle == observed_delta, f"Delta mismatch: {delta_triangle} != {observed_delta}"


def test_egograph_triangles(egograph):
    """
    Test delta_local_triangle calculation on egograph dataset
    This is a real-world network (Zachary's karate club)
    """
    mygraph = egograph
    mc = MarkovChain(mygraph, 10, 2, False)
    mc.count_triangles()

    print(f"\nEgograph basic stats:")
    print(f"Number of nodes: {mygraph.N}")
    print(f"Number of edges: {mygraph.M}")
    print(f"Number of triangles: {len(mc.triangles2edges)}")

    # Test multiple random swaps and verify delta calculation
    for swap_idx in range(5):
        # Find a swap
        edge_to_swap, permutation, edge_to_swap_idx = mc.find_swap(2)

        # Count triangles before swap
        triangles_count_before = len(mc.triangles2edges)

        # Use the same approach as check_swap
        local_graph, dico = mc.create_partial_local_graph(edge_to_swap)
        mc.perform_local_swap(local_graph, edge_to_swap, permutation)
        delta_triangle = mc.delta_local_triangle(local_graph, edge_to_swap, permutation)

        print(f"\nSwap {swap_idx + 1}:")
        print(f"  Edge to swap: {edge_to_swap}")
        print(f"  Permutation: {permutation}")
        print(f"  Delta from delta_local_triangle: {delta_triangle}")

        # Now perform the actual swap on the main graph to verify
        mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)
        mc.update_triangles(edge_to_swap, permutation)
        triangles_count_after = len(mc.triangles2edges)

        observed_delta = triangles_count_after - triangles_count_before

        print(f"  Observed delta from actual swap: {observed_delta}")
        print(f"  Triangle count before: {triangles_count_before}, after: {triangles_count_after}")

        # The delta from delta_local_triangle should match the observed delta
        assert delta_triangle == observed_delta, f"Delta mismatch for swap {swap_idx + 1}: {delta_triangle} != {observed_delta}"

    print(f"\n✓ All 5 swaps passed delta calculation verification on egograph!")
