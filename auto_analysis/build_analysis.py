import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib as mpl
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

mpl.rcParams["figure.facecolor"] = "white"
mpl.rcParams["axes.facecolor"] = "white"
mpl.rcParams["savefig.facecolor"] = "white"

# -----------------------------
# SLICES  (indices dans le vecteur complet)
# -----------------------------
SLICE_4 = slice(3, 9)    # graphlets 4-9   → 6 motifs taille 4
SLICE_5 = slice(9, 30)   # graphlets 10-30 → 21 motifs taille 5

# Dossier contenant les tuiles g04.png … g30.png
TILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graphlet_files")

# -----------------------------
# LOAD
# -----------------------------
def load(path):
    with open(path, "r") as f:
        return json.load(f)

IMAGE_CACHE = {}

def load_tile(graphlet_1indexed, zoom=0.01):
    if graphlet_1indexed not in IMAGE_CACHE:
        path = os.path.join(TILES_DIR, f"graphlet_{graphlet_1indexed:02d}.png")
        IMAGE_CACHE[graphlet_1indexed] = mpimg.imread(path)
    return OffsetImage(IMAGE_CACHE[graphlet_1indexed], zoom=zoom)

def split_data(data):
    original   = np.array(data["__original__"])
    random_keys = [k for k in data if k != "__original__"]
    randoms    = np.array([data[k] for k in random_keys])
    return original, randoms

def zscore_vs_random(original, randoms, sl):
    orig = original[sl]
    rand = randoms[:, sl]
    mean = rand.mean(axis=0)
    std  = rand.std(axis=0) + 1e-9
    z    = (orig - mean) / std
    return z, mean, std

def significance_profile(z, zero_mask):
    z_f = z.copy()
    z_f[zero_mask] = 0.0
    norm = np.linalg.norm(z_f)
    if norm < 1e-12:
        return np.zeros_like(z)
    return z_f / norm

EPSILON = 4

def subgraph_ratio_profile(delta):
    norm = np.linalg.norm(delta)
    if norm < 1e-12:
        return np.zeros_like(delta)
    return delta / norm

def compute_delta(original, randoms, sl):
    orig = original[sl]
    mean_rand = randoms[:, sl].mean(axis=0)
    delta = (orig - mean_rand) / (orig + mean_rand + EPSILON)
    return delta, mean_rand


def set_graphlet_xticks(ax, graphlet_indices_1based, y_offset_axes=-0.18, zoom=0.01):
    """
    Remplace les x-ticks d'un axe par les images des graphlets.
    graphlet_indices_1based : liste des numéros 1-based dans l'ordre des x positions.
    """
    ax.set_xticks([])          # supprime les ticks numériques
    ax.set_xticklabels([])

    # Coordonnées data → on place les images juste sous l'axe
    for x_pos, g_idx in enumerate(graphlet_indices_1based):
        img_box = load_tile(g_idx, zoom=zoom)
        ab = AnnotationBbox(
            img_box,
            xy=(x_pos, 0),
            xycoords=("data", "axes fraction"),
            xybox=(0, -25),          # décalage en points sous l'axe
            boxcoords="offset points",
            box_alignment=(0.5, 1.0),
            frameon=False,
            annotation_clip=False,
        )
        ax.add_artist(ab)

# -----------------------------
# PLOT : ORIGINAL vs MEAN RANDOM
# -----------------------------
def plot_mean_comparison(original, mean, sl, label, path):
    orig = original[sl]
    x    = np.arange(len(orig))

    plt.figure(figsize=(10, 5))
    plt.plot(x, orig, label="Original", linewidth=2)
    plt.plot(x, mean, label="Mean random", linestyle="--")
    plt.title(f"Original vs Random mean — size-{label} graphlets")
    plt.xlabel("Graphlet")
    plt.ylabel("Count")
    plt.legend()
    plt.tight_layout()

    out = path.replace(".json", f"_size{label}_meandistrib.png")
    plt.savefig(out, dpi=150)
    plt.close()

# -----------------------------
# PLOT : Z-SCORE
# -----------------------------
def plot_zscore(z, zero_mask, graphlet_ids, label, path):
    n = len(z)
    x = np.arange(n)
    valid_mask = ~zero_mask
    x_zero     = x[zero_mask]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.subplots_adjust(bottom=0.18, hspace=0.55)

    for ax, scale in zip([ax1, ax2], [None, "symlog"]):
        # Points valides
        ax.plot(x[valid_mask], z[valid_mask], marker="o",
                linestyle="-", linewidth=1.5, label="Z-score")
        # Barres verticales pour les zéros
        for xi in x_zero:
            ax.axvline(xi, color="orange", linestyle=":", linewidth=1.5,
                       label="Original = 0" if xi == x_zero[0] else "")
        ax.axhline(0,  color="black", linewidth=1)
        ax.axhline( 2, linestyle="--", color="gray")
        ax.axhline(-2, linestyle="--", color="gray")
        ax.set_ylabel("Z-score")
        ax.set_xlim(-0.5, n - 0.5)
        ax.legend(fontsize=8)

        title = f"Z-score — size-{label} graphlets"
        if scale == "symlog":
            ax.set_yscale("symlog", linthresh=2)
            title += " (symlog)"
        ax.set_title(title)

        if label=="4":
            set_graphlet_xticks(ax, graphlet_ids, zoom=0.1)
        else:
            set_graphlet_xticks(ax, graphlet_ids, zoom=0.032)

    out = path.replace(".json", f"_size{label}_zscore.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()

def plot_zscore_trimed(z, zero_mask, graphlet_ids, label, path):
    n = len(z)
    x = np.arange(n)
    valid_mask = ~zero_mask
    x_zero = x[zero_mask]

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.subplots_adjust(bottom=0.25)

    # courbe principale
    ax.plot(
        x[valid_mask],
        z[valid_mask],
        marker="o",
        linestyle="-",
        linewidth=1.5,
        label="Z-score"
    )

    # lignes verticales pour les zéros
    for xi in x_zero:
        ax.axvline(
            xi,
            color="orange",
            linestyle=":",
            linewidth=1.5,
            label="Original = 0" if xi == x_zero[0] else ""
        )

    # lignes de référence
    ax.axhline(0, color="black", linewidth=1)
    ax.axhline(2, linestyle="--", color="gray")
    ax.axhline(-2, linestyle="--", color="gray")

    ax.set_ylim(-20, 20)

    ax.set_ylabel("Z-score")
    ax.set_xlim(-0.5, n - 0.5)
    ax.legend(fontsize=8)

    ax.set_title(f"Z-score — size-{label} graphlets (trimmed)")

    if label == "4":
        set_graphlet_xticks(ax, graphlet_ids, zoom=0.1)
    else:
        set_graphlet_xticks(ax, graphlet_ids, zoom=0.032)

    out = path.replace(".json", f"_size{label}_zscore_trimed.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
# -----------------------------
# PLOT : SIGNIFICANCE PROFILE
# -----------------------------
def plot_significance_profile(sp, zero_mask, graphlet_ids, label, path):
    n = len(sp)
    x = np.arange(n)
    x_zero = x[zero_mask]

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.subplots_adjust(bottom=0.22)

    ax.bar(x, sp, width=0.8)

    for xi in x_zero:
        ax.axvline(xi, color="orange", linestyle=":", linewidth=1.5,
                   label="Original = 0" if xi == x_zero[0] else "")
    ax.axhline(0, linewidth=1)
    ax.set_title(f"Significance Profile — size-{label} graphlets (zero-count excluded)")
    ax.set_ylabel("SP")
    ax.set_ylim(-1, 1)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_yticks(np.linspace(-1, 1, 5))
    if len(x_zero):
        ax.legend(fontsize=8)

    if label== "4" :
        set_graphlet_xticks(ax, graphlet_ids, zoom=0.1)
    else:
        set_graphlet_xticks(ax, graphlet_ids, zoom=0.032)

    out = path.replace(".json", f"_size{label}_significance_profile.png")

    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()

def plot_significance_profile_radar(sp, zero_mask, graphlet_ids, label, path):
    n = len(sp)

    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    values = sp.tolist()
    angles += angles[:1]
    values += values[:1]

    fig = plt.figure(figsize=(7, 7), facecolor="white")
    ax = plt.subplot(111, polar=True)

    ax.plot(angles, values, linewidth=2, color="steelblue", label="SP")
    ax.fill(angles, values, alpha=0.25, color="steelblue")
    ax.plot(angles, [0] * len(angles), linewidth=1.2, color="black",
            linestyle="--", zorder=3)

    for i, z in enumerate(zero_mask):
        if z:
            ax.plot([angles[i]], [values[i]], marker="o", color="orange")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([])
    ax.set_rgrids([-1, -0.3, -0.6, 0, 0.5, 1.0])
    ax.set_ylim(-1, 1)
    ax.set_title(f"Significance Profile (Radar) — size-{label}", pad=60)
    ax.grid(True)
    ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1.15))

    zoom = 0.05 if label == "4" else 0.04

    fig.canvas.draw()

    # Centre exact via coordonnées axes (0.5, 0.5) = centre de l'axe
    axes_to_display = ax.transAxes
    display_to_figure = fig.transFigure.inverted()

    center_display = axes_to_display.transform((0.5, 0.5))
    cx, cy = display_to_figure.transform(center_display)

    # Rayon : bord droit de l'axe (1.0, 0.5) en coordonnées axes
    edge_display = axes_to_display.transform((1.0, 0.5))
    ex, ey = display_to_figure.transform(edge_display)
    r_fig = abs(ex - cx)  # rayon horizontal en coordonnées figure

    image_radius = 1.18
    vertical_offset = 0.01
    if label=="4":
        orizontal_offset = 0
        vertical_offset = -0.014
    else:
        orizontal_offset = 0

    for angle, g_idx in zip(angles[:-1], graphlet_ids):
        img_box = load_tile(g_idx, zoom=zoom)

        x_fig = cx + image_radius * r_fig * np.cos(angle) - orizontal_offset
        y_fig = cy + image_radius * r_fig * np.sin(angle) + vertical_offset
         # +1 ou -1 ?

        ab = AnnotationBbox(
            img_box,
            (x_fig, y_fig),
            xycoords="figure fraction",
            frameon=False,
            annotation_clip=False,
            box_alignment=(0.5, 0.5),
        )
        ax.add_artist(ab)


    out = path.replace(".json", f"_size{label}_significance_profile_radar.png")
    plt.savefig(out, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close()

def plot_srp_radar(srp, zero_mask, graphlet_ids, label, path, normalized=True):
    n = len(srp)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    values = srp.tolist()
    angles += angles[:1]
    values += values[:1]

    fig = plt.figure(figsize=(7, 7), facecolor="white")
    ax = plt.subplot(111, polar=True)

    ax.plot(angles, values, linewidth=2, color="steelblue", label="SRP")
    ax.fill(angles, values, alpha=0.25, color="steelblue")
    ax.plot(angles, [0] * len(angles), linewidth=1.2, color="black",
            linestyle="--", zorder=3)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([])
    ax.yaxis.set_visible(False)
    ax.set_ylim(-1, 1)
    ax.set_title(f"SRP Radar — size-{label}", pad=60)
    ax.grid(True)
    ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1.15))

    zoom = 0.05 if label == "4" else 0.04
    fig.canvas.draw()

    axes_to_display = ax.transAxes
    display_to_figure = fig.transFigure.inverted()
    center_display = axes_to_display.transform((0.5, 0.5))
    cx, cy = display_to_figure.transform(center_display)
    edge_display = axes_to_display.transform((1.0, 0.5))
    ex, _ = display_to_figure.transform(edge_display)
    r_fig = abs(ex - cx)

    image_radius = 1.18
    vertical_offset = 0.01
    if label == "4":
        orizontal_offset = 0
        vertical_offset = -0.014
    else:
        orizontal_offset = 0

    for angle, g_idx in zip(angles[:-1], graphlet_ids):
        img_box = load_tile(g_idx, zoom=zoom)
        x_fig = cx + image_radius * r_fig * np.cos(angle) - orizontal_offset
        y_fig = cy + image_radius * r_fig * np.sin(angle) + vertical_offset
        ab = AnnotationBbox(
            img_box,
            (x_fig, y_fig),
            xycoords="figure fraction",
            frameon=False,
            annotation_clip=False,
            box_alignment=(0.5, 0.5),
        )
        ax.add_artist(ab)

    if normalized:
        out = path.replace(".json", f"_size{label}_srp_radar_norm.png")
    else:
        out = path.replace(".json", f"_size{label}_srp_radar.png")
    plt.savefig(out, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")

def plot_srp(srp, delta, zero_mask, graphlet_ids, label, path, normalized=True):
    n = len(srp)
    x = np.arange(n)

    colors = ["steelblue" if d >= 0 else "tomato" for d in delta]

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.subplots_adjust(bottom=0.22)

    ax.bar(x, srp, width=0.8, color=colors)

    ax.axhline(0, linewidth=1, color="black")
    ax.set_title(f"Subgraph Ratio Profile (SRP) — size-{label} graphlets")
    ax.set_ylabel("SRP")
    ax.set_ylim(-1, 1)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_yticks(np.linspace(-1, 1, 5))

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="steelblue", label="Over-represented"),
        Patch(facecolor="tomato",    label="Under-represented"),
    ]
    ax.legend(handles=legend_elements, fontsize=8, loc="upper right")

    zoom = 0.1 if label == "4" else 0.032
    set_graphlet_xticks(ax, graphlet_ids, zoom=zoom)
    if normalized:
        out = path.replace(".json", f"_size{label}_srp_norm.png")
    else:
        out = path.replace(".json", f"_size{label}_srp.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved: {out}")

# -----------------------------
# MAIN
# -----------------------------
def main(path, path2):
    data = load(path)
    data_includ = load(path2)
    original_includ, randoms_includ = split_data(data_includ)
    original, randoms = split_data(data)

    # Numéros 1-based des graphlets pour chaque taille
    ids_4 = list(range(4, 10))   # [4,5,6,7,8,9]
    ids_5 = list(range(10, 31))  # [10..30]

    for sl, label, gids in [
        (SLICE_4, "4", ids_4),
        (SLICE_5, "5", ids_5),
    ]:
        z, mean, std = zscore_vs_random(original, randoms, sl)
        zero_mask    = (original[sl] == 0)
        sp           = significance_profile(z, zero_mask)
        delta, _     = compute_delta(original, randoms, sl)
        srp = subgraph_ratio_profile(delta)

        z_i, mean_i, std_i = zscore_vs_random(original_includ, randoms_includ, sl)
        zero_mask_i = (original_includ[sl] == 0)
        sp_i = significance_profile(z_i, zero_mask_i)
        delta_i, _ = compute_delta(original_includ, randoms_includ, sl)
        srp_i = subgraph_ratio_profile(delta_i)

        plot_mean_comparison(original, mean, sl, label, path)
        plot_zscore(z, zero_mask, gids, label, path)
        plot_significance_profile(sp, zero_mask, gids, label, path)
        plot_zscore_trimed(z, zero_mask, gids, label, path)
        plot_significance_profile_radar(sp, zero_mask, gids, label, path)
        plot_srp(srp, delta, zero_mask, gids, label, path)
        plot_srp_radar(srp, zero_mask, gids, label, path)
        plot_srp(delta, delta, zero_mask, gids, label, path, normalized=False)
        plot_srp_radar(delta, zero_mask, gids, label, path, normalized=False)

        plot_mean_comparison(original_includ, mean_i, sl, label, path2)
        plot_zscore(z_i, zero_mask_i, gids, label, path2)
        plot_significance_profile(sp_i, zero_mask_i, gids, label, path2)
        plot_zscore_trimed(z_i, zero_mask_i, gids, label, path2)
        plot_significance_profile_radar(sp_i, zero_mask_i, gids, label, path2)
        plot_srp(srp_i, delta_i, zero_mask_i, gids, label, path2)
        plot_srp(delta_i, delta_i, zero_mask_i, gids, label, path2, normalized=False)
        plot_srp_radar(srp_i, zero_mask_i, gids, label, path2)
        plot_srp_radar(delta_i, zero_mask_i, gids, label, path2, normalized=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_graphs.py file.json file2.json")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])