import json
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# LOAD
# -----------------------------
def load(path):
    with open(path, "r") as f:
        return json.load(f)


# -----------------------------
# SPLIT ORIGINAL / RANDOM
# -----------------------------
def split_data(data):
    original = np.array(data["__original__"])

    random_keys = [k for k in data.keys() if k != "__original__"]
    randoms = np.array([data[k] for k in random_keys])

    return original, randoms, random_keys


# -----------------------------
# Z-SCORE vs RANDOM DISTRIBUTION
# -----------------------------
def zscore_vs_random(original, randoms):
    mean = randoms.mean(axis=0)
    std = randoms.std(axis=0) + 1e-9  # éviter division par 0
    return (original - mean) / std, mean, std


# -----------------------------
# PLOT 1 : ORIGINAL vs MEAN RANDOM
# -----------------------------
def plot_mean_comparison(original, mean, path):
    x = np.arange(len(original))

    plt.figure(figsize=(10, 5))
    plt.plot(x, original, label="Original", linewidth=2)
    plt.plot(x, mean, label="Mean random", linestyle="--")

    plt.title("Original vs Random mean")
    plt.xlabel("Feature index")
    plt.ylabel("Value")
    plt.legend()
    plt.tight_layout()

    out = path.replace(".json", "_meandistrib.png")
    plt.savefig(out, dpi=300)

    plt.close()


# -----------------------------
# PLOT 2 : Z-SCORE
# -----------------------------
def plot_zscore(z, path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Vue complète
    ax1.plot(z, marker="o")
    ax1.axhline(0, color="black", linewidth=1)
    ax1.axhline(2, color="red", linestyle="--")
    ax1.axhline(-2, color="red", linestyle="--")
    ax1.set_title("Z-score — vue complète")
    ax1.set_ylabel("Z-score")

    # Vue symlog
    ax2.plot(z, marker="o")
    ax2.axhline(0, color="black", linewidth=1)
    ax2.axhline(2, color="red", linestyle="--")
    ax2.axhline(-2, color="red", linestyle="--")
    ax2.set_yscale("symlog", linthresh=2)  # linéaire entre -2 et 2 (zone seuil), log au-delà
    ax2.set_title("Z-score — échelle symlog")
    ax2.set_xlabel("Feature index")
    ax2.set_ylabel("Z-score (symlog)")

    plt.tight_layout()
    out = path.replace(".json", "_zscore.png")
    plt.savefig(out, dpi=300)
    plt.close()


# -----------------------------
# PLOT 3 : DISTRIBUTION RANDOM vs ORIGINAL
# -----------------------------
def plot_distributions(original, randoms, idx=0):
    plt.figure(figsize=(8, 4))

    plt.hist(randoms[:, idx], bins=20, alpha=0.6, label="Random")
    plt.axvline(original[idx], color="red", linewidth=2, label="Original")

    plt.title(f"Feature {idx} distribution")
    plt.legend()
    plt.tight_layout()
    plt.close()


# -----------------------------
# MAIN
# -----------------------------
def main(path):
    data = load(path)

    original, randoms, keys = split_data(data)

    z, mean, std = zscore_vs_random(original, randoms)

    print("Random graphs:", len(randoms))
    print("Features:", len(original))

    # 1. comparaison moyenne
    plot_mean_comparison(original, mean, path)

    # 2. z-score global
    plot_zscore(z, path)

    # 3. distribution sur quelques features importantes
    #for i in [1, 2, 27, 28, 29]:
    #    plot_distributions(original, randoms, idx=i)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compare_graphs.py file.json")
        sys.exit(1)

    main(sys.argv[1])