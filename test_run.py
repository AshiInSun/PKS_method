import os
import matplotlib.pyplot as plt
from line_profiler import LineProfiler

from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain

def test_run():

    file = os.path.join(
        os.path.dirname(__file__),
        'data',
        'ego_dataset',
        '4a614391ef27b94d336a410bec2aa934.gml'
    )

    graph = Graph(directed=False)
    graph.read_gml(file)
    N_swap = graph.M * 1000

    def run_mc():
        return mc.run()

    mc = MarkovChain(
        graph,
        N_swap=100000,
        gamma=2.0,
        use_triangles=True,
        use_fixed_triangle=True,
        use_fixed_triangle_range=75,
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