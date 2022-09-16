import pytest

from Graph import Graph
from Swap import Swap

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

def test_directed_swaps():
    # TODO : peut être ajouter test ou on enchaine un swap et son inverse + vérifier si on retourne bien au graphe de départ ?
    mygraph = Graph(True)
    mygraph.read_ssv('data/japanese_macaques.tsv')#TODO
    swaps = Swap(mygraph, 10, 2, False) # TODO : debug ? 

    edge_to_swap = [(43, 34), (57, 62), (36, 7), (12, 51), (27, 48), (49, 62), (11, 46), (8, 23), (56, 22), (59, 61)]
    permutation = [(59, 61), (43, 34), (57, 62), (36, 7), (12, 51), (27, 48), (49, 62), (11, 46), (8, 23), (56, 22)]
    edge_to_swap_idx = [1090, 1185, 100, 458, 1015, 1123, 436, 333, 734, 915]

    accept_permutation = swaps.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True
    swaps.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)

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

def test_undirected_swaps():
    mygraph = Graph(False)
    mygraph.read_ssv('data/euroroad.tsv')#TODO FIXTURES
    swaps = Swap(mygraph, 10, 2, False) # TODO : debug ? 

    edge_to_swap = [(578, 767), (1041, 1042), (935, 936), (254, 255), (284, 310), (346, 965), (473, 474), (962, 963), (381, 382), (28, 29)]
    permutation = [(28, 29), (578, 767), (1041, 1042), (935, 936), (254, 255), (284, 310), (346, 965), (473, 474), (962, 963), (381, 382)]
    edge_to_swap_idx = [972, 1343, 1281, 502, 566, 662, 837, 1300, 709, 59]

    accept_permutation = swaps.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True
    swaps.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)

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
    swaps = Swap(mygraph, 10, 2, False) # TODO : debug ? 
    swaps.count_triangles()
    assert len(swaps.triangles2edges) == 32

    # directed
    mygraph = Graph(True)
    mygraph.read_ssv('data/japanese_macaques.tsv')#TODO FIXTURES
    swaps = Swap(mygraph, 10, 2, False) # TODO : debug ? 
    swaps.count_triangles()
    assert len(swaps.triangles2edges) == 9781


def test_update_triangles():
    mygraph = Graph(False)
    mygraph.read_ssv('data/euroroad.tsv')#TODO FIXTURES
    swaps = Swap(mygraph, 10, 2, False) # TODO : debug ? 
    swaps.count_triangles()

    edge_to_swap = [(469, 470), (1085, 1086), (428, 732)]
    permutation = [(1085, 1086), (428, 732), (469, 470)]
    edge_to_swap_idx = [831, 1363, 768]
    destroyed_triangles = [(428, 429, 732)]

    assert destroyed_triangles[0] in swaps.triangles2edges
    

    accept_permutation = swaps.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True
    swaps.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)

    # check that the following triangles are correctly removed by swap
    assert destroyed_triangles[0] in swaps.triangles2edges

    swaps.update_triangles(edge_to_swap, permutation)

    assert destroyed_triangles[0] not in swaps.triangles2edges


    #TODO given graph, given swap, measure that destroyed triangles are the correct ones and created 
    pass

def test_init_assortativity():
    pass

def test_update_assortativity():
    # compare update & init 
    pass

