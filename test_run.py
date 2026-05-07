import os
import matplotlib.pyplot as plt
from line_profiler import LineProfiler
import networkx as nx
from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain

def plot_graph(graph):
    G = nx.Graph()

    # ⚠️ à adapter selon ta structure interne
    # ici on suppose graph.edges = liste de tuples (u, v)
    for u, v in graph.unique_edges:
        G.add_edge(u, v)

    plt.figure(figsize=(6,6))
    pos = nx.fruchterman_reingold_layout(G, seed=42)  # layout force-directed
    nx.draw_networkx_nodes(G, pos, node_size=20)
    nx.draw_networkx_edges(G, pos, alpha=0.1)

    plt.tight_layout()
    plt.title("Sampled graph")

    plt.tight_layout()

def test_run():

    file = os.path.join(
        os.path.dirname(__file__),
        'data',
        'ucidata-zachary',
        'out.ucidata-zachary'
    )

    graph = Graph(directed=False)
    graph.read_ssv(file)
    N_swap = graph.M * 1000

    def run_mc():
        return mc.run()

    mc = MarkovChain(
        graph,
        N_swap=N_swap,
        gamma=3.0,
        use_assortativity=True,
        use_fixed_tclosedpath=True,
        #use_fixed_triangle_range=1,
        verbose=True,
        old_count=False
    )
    lp = LineProfiler()
    lp.add_function(mc.find_swap_opti)
    lp.add_function(mc.check_swap)
    window = []
    print("N_swap :",N_swap)
    print("Starting run...")
    window.extend(lp.runcall(run_mc))
    #lp.print_stats()
    print("Run finished")

    print("Accept rate :", mc.accept_rate)
    print("Refusal rate :", mc.refusal_rate)

    plot_graph(mc.graph)

    # plot
    plt.figure()
    plt.plot(window)
    plt.xlabel("Swap step")
    plt.ylabel("Assortativity")
    plt.title("Evolution of assortativity during edge swaps")
    plt.show()




if __name__ == "__main__":
    test_run()