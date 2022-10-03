import pytest
import numpy as np
from Graph import Graph
from progressbar import ProgressBar

from MarkovChain import MarkovChain

def test_directed_graph():
    mygraph = Graph(True)
    mygraph.read_ssv('data/japanese_macaques.tsv')#TODO
    for (u,v) in mygraph.edges:
        #assert (v,u) not in mygraph.edges
        
        v_idx, u_idx, v_out_idx, u_in_idx = mygraph.edges[(u,v)]

        assert mygraph.neighbors[u][v_idx] == v
        assert mygraph.neighbors[v][u_idx] == u
        assert mygraph.out_neighbors[u][v_out_idx] == v
        assert mygraph.in_neighbors[v][u_in_idx] == u

def test_undirected_graph():
    mygraph = Graph(False)
    mygraph.read_ssv('data/euroroad.tsv')#TODO
    for (u,v) in mygraph.edges:
        #assert (v,u) not in mygraph.edges
        
        v_idx = mygraph.edges[(u,v)]
        u_idx = mygraph.edges[(v,u)]

        assert mygraph.neighbors[u][v_idx] == v
        assert mygraph.neighbors[v][u_idx] == u

def test_directed_mc():
    # TODO : peut être ajouter test ou on enchaine un swap et son inverse + vérifier si on retourne bien au graphe de départ ?
    mygraph = Graph(True)
    mygraph.read_ssv('data/japanese_macaques.tsv')#TODO
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

def test_undirected_mc():
    mygraph = Graph(False)
    mygraph.read_ssv('data/euroroad.tsv')#TODO FIXTURES
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

def test_init_triangles():
    # undirected
    mygraph = Graph(False)
    mygraph.read_ssv('data/euroroad.tsv')#TODO FIXTURES
    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 
    mc.count_triangles()
    assert len(mc.triangles2edges) == 32

    # directed
    mygraph = Graph(True)
    mygraph.read_ssv('data/japanese_macaques.tsv')#TODO FIXTURES
    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 
    mc.count_triangles()
    assert len(mc.triangles2edges) == 9781


def test_update_triangles():
    # undirected
    mygraph = Graph(False)
    mygraph.read_ssv('data/euroroad.tsv')#TODO FIXTURES
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
    # directed
    mygraph = Graph(True)
    mygraph.read_ssv('data/japanese_macaques.tsv')#TODO FIXTURES
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

def test_update_triangles_random():
    # undirected
    mygraph = Graph(True)
    mygraph.read_ssv('data/japanese_macaques.tsv')#TODO FIXTURES

    mc = MarkovChain(mygraph, 10, 2, False) # TODO : debug ? 
    mc.count_triangles()
    k = 4
    for swap_idx in range(1000):
        edge_to_swap, permutation, edge_to_swap_idx = mc.find_swap(k)
        accept_permutation = mc.check_swap(edge_to_swap, permutation)

        if (accept_permutation):
            mc.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)
            mc.update_triangles(edge_to_swap, permutation)
            updated_triangles2edges = mc.triangles2edges.copy()
            updated_edges2triangles = mc.edges2triangles.copy()

            mc.count_triangles()

            for triangle in mc.triangles2edges:
                assert triangle in updated_triangles2edges
                for edge in mc.triangles2edges[triangle]:
                    assert edge in updated_triangles2edges[triangle]

            for triangle in updated_triangles2edges:
                assert triangle in mc.triangles2edges
                assert len(updated_triangles2edges[triangle]) == len(mc.triangles2edges[triangle])

            for edge in updated_edges2triangles:
                assert edge in mc.edges2triangles
                for triangle in updated_edges2triangles[edge]:
                    assert triangle in mc.edges2triangles[edge]

            for edge in mc.edges2triangles:
                assert edge in updated_edges2triangles
                for triangle in mc.edges2triangles[edge]:
                    assert triangle in updated_edges2triangles[edge]





def test_init_assortativity():
    pass

def test_update_assortativity():
    mygraph = Graph(False)
    mygraph.read_ssv('data/euroroad.tsv')#TODO FIXTURES
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

def test_edges2triangles():
    mygraph = Graph(True)
    mygraph.read_ssv('edge_list')
    mc = MarkovChain(mygraph, 10, 2, False)
    edge_to_swap = [(26, 31),(35, 59),(11, 9),(41, 58)]
    permutation = [ (41, 58),(26, 31),(35, 59),(11, 9)]
    mc.count_triangles()
    accept = mc.check_swap(edge_to_swap, permutation)

