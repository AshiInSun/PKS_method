import os
import matplotlib.pyplot as plt

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

    mc = MarkovChain(
        graph,
        N_swap=100000,
        gamma=2.0,
        use_assortativity=True,
        use_fixed_threechains=True,
        verbose=True
    )
    print("N_swap :",N_swap)
    print("Starting run...")
    window = mc.run()
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