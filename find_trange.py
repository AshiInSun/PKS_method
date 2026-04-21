import os
import numpy as np
import matplotlib.pyplot as plt

from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain


def run_experiment():

    file = os.path.join(
        os.path.dirname(__file__),
        'data',
        'ucidata-zachary',
        'egograph_edges.txt'
    )

    graph = Graph(directed=False)
    graph.read_ssv(file)

    ranges = range(0, 10)
    repetitions = 5  # nombre de runs pour faire une moyenne

    mean_acceptances = []
    burn_in = MarkovChain(
                graph,
                N_swap=1000000,
                gamma=3.0,
                use_triangles=True,
                use_fixed_triangle=True,
                use_fixed_triangle_range=1,
                verbose=False,
                old_count=False
            )
    burn_in.run()

    for r in ranges:
        acceptances = []

        print(f"\nTesting range = {r}")

        for i in range(repetitions):

            mc = MarkovChain(
                graph,
                N_swap=100000,
                gamma=3.0,
                use_triangles=True,
                use_fixed_triangle=True,
                use_fixed_triangle_range=r,
                verbose=False,
                old_count=False
            )

            mc.run()
            acceptances.append(mc.accept_rate)
            print(f"Run {i+1}/{repetitions}, acceptance rate: {mc.accept_rate}")

        mean_acc = np.mean(acceptances)
        mean_acceptances.append(mean_acc)

        print(f"Mean acceptance: {mean_acc}")

    # plot
    plt.figure()
    plt.plot(list(ranges), mean_acceptances, marker='o')
    plt.xlabel("use_fixed_triangle_range")
    plt.ylabel("Mean acceptance rate")
    plt.title("Acceptance rate vs triangle range")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    run_experiment()