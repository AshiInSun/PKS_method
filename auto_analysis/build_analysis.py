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

def filter_graphlets(arr):
    return np.array(arr[3:])

def significance_profile(z):
    norm = np.linalg.norm(z)

    if norm < 1e-12:
        return np.zeros_like(z)

    return z / norm
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

    original = original[3:]
    randoms = randoms[:, 3:]

    mean = randoms.mean(axis=0)
    std = randoms.std(axis=0) + 1e-9

    z = (original - mean) / std

    return z, mean, std

# -----------------------------
# PLOT 1 : ORIGINAL vs MEAN RANDOM
# -----------------------------
def plot_mean_comparison(original, mean, path):
    noriginal = original[3:]
    x = np.arange(len(noriginal))

    plt.figure(figsize=(10, 5))
    plt.plot(x, noriginal, label="Original", linewidth=2)
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

    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(10, 8)
    )

    # ------------------------
    # Full scale
    # ------------------------
    ax1.plot(z, marker="o")
    ax1.axhline(0, linewidth=1)

    ax1.axhline(2,
                linestyle="--")
    ax1.axhline(-2,
                linestyle="--")

    ax1.set_title("Z-score")
    ax1.set_ylabel("Z-score")

    # ------------------------
    # symlog
    # ------------------------
    ax2.plot(z, marker="o")
    ax2.axhline(0, linewidth=1)

    ax2.axhline(2,
                linestyle="--")
    ax2.axhline(-2,
                linestyle="--")

    ax2.set_yscale(
        "symlog",
        linthresh=2
    )

    ax2.set_title("Z-score (symlog)")
    ax2.set_xlabel("Graphlet index")
    ax2.set_ylabel("Z-score")

    plt.tight_layout()

    out = path.replace(
        ".json",
        "_zscore.png"
    )

    plt.savefig(out, dpi=300)
    plt.close()

def plot_significance_profile(sp, path):

    x = np.arange(3, 3 + len(sp))

    plt.figure(figsize=(10, 5))

    plt.plot(x, sp, marker="o", linewidth=1.5)

    plt.axhline(0, linewidth=1)

    plt.title("Significance Profile (normalized Z-score)")
    plt.xlabel("Graphlet index")
    plt.ylabel("SP")

    # FIXED AXES (important pour comparaison)
    plt.ylim(-1, 1)
    plt.xlim(2.5, 3 + len(sp) - 0.5)

    plt.xticks(np.arange(3, 3 + len(sp), 2))
    plt.yticks(np.linspace(-1, 1, 5))

    plt.tight_layout()

    out = path.replace(
        ".json",
        "_significance_profile.png"
    )

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

    z, mean, std = zscore_vs_random(
        original,
        randoms
    )

    sp = significance_profile(z)

    plot_mean_comparison(
        original,
        mean,
        path
    )

    plot_zscore(
        z,
        path
    )

    plot_significance_profile(
        sp,
        path
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compare_graphs.py file.json")
        sys.exit(1)

    main(sys.argv[1])