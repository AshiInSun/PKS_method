import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull

# positions des noeuds (à la main ou layout)
pos = {
    1: (0, 0),
    2: (1, 0),
    3: (2, 0),
    4: (0.5, 1),
    5: (1.5, 1),
    6: (3, 1),
    7: (3, 2),
    8: (2, 2),
    9: (4, 2),
    10: (4, 1)
}

# hyperedges
hyperedges = [
    [1, 2],
    [1, 2, 3, 4, 5],
    [4, 6, 7, 8],
    [6, 7, 8, 9, 10]
]

fig, ax = plt.subplots()

# dessiner les "patates"
for hedge in hyperedges:
    points = np.array([pos[n] for n in hedge])

    if len(points) >= 3:
        hull = ConvexHull(points)
        polygon = points[hull.vertices]
        ax.fill(*polygon.T, alpha=0.2)
    else:
        # petit cercle pour les hyperedges à 2 noeuds
        x, y = points.T
        ax.plot(x, y, linewidth=5, alpha=0.3)

# dessiner les noeuds
for node, (x, y) in pos.items():
    ax.scatter(x, y, color='black')
    ax.text(x, y, str(node), ha='center', va='center', color='white')

ax.set_aspect('equal')
plt.show()