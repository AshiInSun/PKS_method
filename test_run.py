import os
import matplotlib.pyplot as plt

from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain


def test_run():

    toy_file = os.path.join(
        os.path.dirname(__file__),
        'data',
        'ego_dataset',
        'a939a651c53a358ca918c69445c8db22.gml'
    )

    graph = Graph(directed=False)
    graph.read_gml(toy_file)

    mc = MarkovChain(
        graph,
        N_swap=10000,
        gamma=2.0,
        use_assortativity=True,
        use_fixed_triangle=True,
        verbose=True
    )

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