# diagnostic one-shot, hors pipeline
import os

import numpy as np

from kedgeswap.MarkovChain import MarkovChain
from kedgeswap.Graph import Graph
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf

file = os.path.join(
        os.path.dirname(__file__),
        'data',
        'ucidata-zachary',
        'egograph_edges.txt'
    )

graph = Graph(directed=False)
graph.read_ssv(file)
N_swap = 10000 * graph.M

print("N_swap :", N_swap)
series = []
mc = MarkovChain(
        graph,
        N_swap=N_swap,
        gamma=3.0,
        use_assortativity=True,
        use_fixed_triangle=True,
        use_fixed_triangle_range=9,
        verbose=True,
        old_count=False
    )
print("Starting burn-in...")
mc.run(10000000)
print("Burn-in ended, starting sampling...")
for _ in range(500):
    mc.run(30000)  # eta fixé à 1000
    series.append(mc.assortativity)

plot_acf(series, lags=30)
plt.title("ACF de l'assortativité, eta=1000")
plt.show()

print("Variance de la série :", np.var(series))
print("Min/Max :", min(series), max(series))