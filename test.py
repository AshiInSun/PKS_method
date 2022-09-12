
from Graph import Graph
From Swap import Swap

def test_directed_graph():
    mygraph = Graph(True)
    mygraph.read_ssv()#TODO
    for (u,v) in mygraph.edges:
        #assert (v,u) not in mygraph.edges
        
        v_idx, u_idx, v_out_idx, u_in_idx = edges[(u,v)]

        assert mygraph.neighbors[u][v_idx] == v
        assert mygraph.neighbors[v][u_idx] == u
        assert mygraph.out_neighbors[u][v_out_idx] == v
        assert mygraph.in_neighbors[v][u_in_idx] == u

def test_undirected_graph():
    mygraph = Graph(False)
    mygraph.read_ssv()#TODO
    for (u,v) in mygraph.edges:
        #assert (v,u) not in mygraph.edges
        
        v_idx = mygraph.edges[(u,v)]
        u_idx = mygraph.edges[(v,u)]

        assert mygraph.neighbors[u][v_idx] == v
        assert mygraph.neighbors[v][u_idx] == u

def test_directed_swaps():
    k = 10
    mygraph = Graph(False)
    mygraph.read_ssv()#TODO
    swaps = Swap(mygraph, args.N_swap, args.gamma, args.debug)

    edge_to_swap, permutation, edge_to_swap_idx = self.find_swap(k)
    accept_permutation = self.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True
    swaps.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)

    for (u,v) in mygraph.edges:
        #assert (v,u) not in mygraph.edges
        
        v_idx, u_idx, v_out_idx, u_in_idx = edges[(u,v)]

        assert mygraph.neighbors[u][v_idx] == v
        assert mygraph.neighbors[v][u_idx] == u
        assert mygraph.out_neighbors[u][v_out_idx] == v
        assert mygraph.in_neighbors[v][u_in_idx] == u

def test_undirected_swaps():
    k = 10
    mygraph = Graph(False)
    mygraph.read_ssv()#TODO
    swaps = Swap(mygraph, args.N_swap, args.gamma, args.debug)

    edge_to_swap, permutation, edge_to_swap_idx = self.find_swap(k)
    accept_permutation = self.check_swap(edge_to_swap, permutation)
    assert accept_permutation == True
    swaps.perform_swap(edge_to_swap, permutation, edge_to_swap_idx)

    for (u,v) in mygraph.edges:
        #assert (v,u) not in mygraph.edges
        
        v_idx = mygraph.edges[(u,v)]
        u_idx = mygraph.edges[(v,u)]

        assert mygraph.neighbors[u][v_idx] == v
        assert mygraph.neighbors[v][u_idx] == u

        v_idx, u_idx, v_out_idx, u_in_idx = edges[(u,v)]

def test_init_triangles():
    pass

def test_update_triangles():
    #TODO given graph, given swap, measure that destroyed triangles are the correct ones and created 
    pass

def test_init_assortativity():
    pass

def test_update_assortativity():
    # compare update & init 

