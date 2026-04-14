import os
import matplotlib.pyplot as plt
from line_profiler import LineProfiler

from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain

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
        N_swap=10000000,
        gamma=3.0,
        use_triangles=True,
        use_fixed_tclosedpath=True,
        verbose=True,
        old_count=False
    )
    lp = LineProfiler()
    lp.add_function(mc.find_swap_opti)
    lp.add_function(mc.check_swap)

    print("N_swap :",N_swap)
    print("Starting run...")
    window = lp.runcall(run_mc)
    lp.print_stats()
    print("Run finished")

    print("Accept rate :", mc.accept_rate)
    print("Refusal rate :", mc.refusal_rate)

    # plot
    plt.figure()
    plt.plot(window)
    plt.xlabel("Swap step")
    plt.ylabel("Assortativity")
    plt.title("Evolution of assortativity during edge swaps")
    plt.show()

if __name__ == "__main__":
    test_run()