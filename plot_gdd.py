"""
plot_gdd.py
Charge tous les {id}_gdd.json, calcule la GDD brute pour l'orbite demandée,
et produit une figure moyenne ± std par modèle + original, avec inset zoomé sur k=0..3.

Usage : python plot_gdd.py <orbit_idx> [--out figure.png] [--zoom N]
"""

import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
import numpy as np



MODELS = ["gen_jdm", "gen_ftr1", "gen_no_constraint"]
BASE_OUT = "out"

COLORS = {
    "gen_jdm":           ("blue",    "jdm"),
    "gen_no_constraint": ("#51ff3d", "no_constraint"),
    "gen_ftr1":          ("#E230E8", "ftr1"),
}


def raw_gdd(orbit_counts: np.ndarray, bins: np.ndarray) -> np.ndarray:
    hist, _ = np.histogram(orbit_counts, bins=bins)
    s = hist.sum()
    return hist / s if s > 0 else hist.astype(float)


def collect_json_paths(cluster_filter=None) -> list[str]:
    paths = []
    for cluster_type in sorted(os.listdir(BASE_OUT)):
        ct_path = os.path.join(BASE_OUT, cluster_type)
        if not os.path.isdir(ct_path) or not cluster_type.endswith("_cluster"):
            continue
        if cluster_filter is not None and cluster_type != cluster_filter:
            continue
        for entry in sorted(os.listdir(ct_path)):
            if not entry.startswith("out_"):
                continue
            cluster_id = entry[len("out_"):]
            json_path = os.path.join(ct_path, entry, f"{cluster_id}_gdd.json")
            if os.path.exists(json_path):
                paths.append(json_path)
    return paths


def load_orbit(json_path: str, orbit_idx: int) -> dict[str, np.ndarray]:
    """Retourne {clé: array 1-D des counts orbit_idx pour tous les nœuds}."""
    with open(json_path) as f:
        data = json.load(f)
    out = {}
    for key, orbits in data.items():
        arr = np.array(orbits)          # shape (n_nodes, 73)
        out[key] = arr[:, orbit_idx]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("orbit_idx", type=int)
    parser.add_argument("--out", default=None,
                        help="Chemin du fichier de sortie (défaut : orbit{N}_gdd_all.png)")
    parser.add_argument("--zoom", type=int, nargs=2, default=[0, 3],
                        metavar=("MIN", "MAX"),
                        help="Plage de k pour l'inset (défaut : 0 3)")
    parser.add_argument(
        "--cluster",
        default=None,
        help="Filtrer sur un cluster (ex: stars_cluster)"
    )
    args = parser.parse_args()
    orbit_idx = args.orbit_idx
    zoom_min, zoom_max = args.zoom
    out_file  = args.out or f"orbit{orbit_idx}_gdd_all.png"

    json_paths = collect_json_paths(args.cluster)
    if not json_paths:
        print("Aucun *_gdd.json trouvé.", file=sys.stderr)
        sys.exit(1)
    print(f"{len(json_paths)} clusters chargés")

    # --- Passe 1 : global_max pour des bins communs ---
    global_max = 0
    for p in json_paths:
        for arr in load_orbit(p, orbit_idx).values():
            if arr.size:
                global_max = max(global_max, int(arr.max()))
    bins = np.arange(0, global_max + 2)
    x = bins[:-1]

    # --- Passe 2 : accumuler les GDD par modèle ---
    orig_gdds: list[np.ndarray] = []
    model_gdds: dict[str, list[np.ndarray]] = {m: [] for m in MODELS}
    k0_diffs: dict[str, list[float]] = {m: [] for m in MODELS}

    for p in json_paths:
        orbit_data = load_orbit(p, orbit_idx)

        if "original" in orbit_data:
            gdd_orig = raw_gdd(orbit_data["original"], bins)
            orig_gdds.append(gdd_orig)

        for key, arr in orbit_data.items():
            if key == "original":
                continue

            gen = key.split("/")[0]

            if gen in model_gdds:
                gdd = raw_gdd(arr, bins)
                model_gdds[gen].append(gdd)

                # distance sur k=0
                k0_diffs[gen].append(abs(gdd[0] - gdd_orig[0]))

    # --- Figure ---
    fig, ax = plt.subplots(figsize=(9, 5))

    # plot_data : (mean, std, color, is_orig) pour réutilisation dans l'inset
    plot_data = []

    for gen in MODELS:
        gdds = model_gdds[gen]
        if not gdds:
            continue
        color, label = COLORS.get(gen, ("gray", gen))
        mat  = np.array(gdds)
        mean = mat.mean(axis=0)
        std  = mat.std(axis=0)
        ax.plot(x, mean, color=color, lw=2, label=label)
        ax.fill_between(x, mean - std, mean + std, color=color, alpha=0.2)
        plot_data.append((mean, std, color, False))

    if orig_gdds:
        mat_orig  = np.array(orig_gdds)
        mean_orig = mat_orig.mean(axis=0)
        std_orig  = mat_orig.std(axis=0)
        ax.plot(x, mean_orig, color="red", lw=2, zorder=5, label="original")
        ax.fill_between(x, mean_orig - std_orig, mean_orig + std_orig,
                        color="red", alpha=0.15, zorder=4)
        plot_data.append((mean_orig, std_orig, "red", True))

    ax.set_xlabel(f"Orbit {orbit_idx} count (k)")
    ax.set_ylabel("Fréquence relative")
    ax.set_title(f"GDD — orbite {orbit_idx}  ({len(json_paths)} clusters)")
    ax.legend()

    # --- Inset zoomé sur k = 0..zoom_max ---
    mask = (x >= zoom_min) & (x <= zoom_max)
    ax_ins = inset_axes(ax, width="50%", height="60%",
                    loc="center left",
                    bbox_to_anchor=(0.17, 0.14, 1, 1),
                    bbox_transform=ax.transAxes)
    for mean, std, color, is_orig in plot_data:
        zorder = 5 if is_orig else 2
        alpha  = 0.15 if is_orig else 0.2
        ax_ins.plot(x[mask], mean[mask], color=color, lw=1.5, zorder=zorder)
        ax_ins.fill_between(x[mask], (mean - std)[mask], (mean + std)[mask],
                            color=color, alpha=alpha, zorder=zorder - 1)
    ax_ins.set_xlim(zoom_min - 0.5, zoom_max + 0.5)
    ax_ins.set_xticks(range(zoom_min, zoom_max + 1))
    ax_ins.tick_params(labelsize=7)
    ax_ins.set_title(f"k = {zoom_min}..{zoom_max}", fontsize=8)
    mark_inset(ax, ax_ins, loc1=3, loc2=4, fc="none", ec="0.5", lw=0.8)

    plt.tight_layout()
    fig.savefig(out_file, dpi=150)
    print(f"Figure sauvegardée : {out_file}")

    fig2, ax2 = plt.subplots(figsize=(6, 4))

    labels = []
    means = []
    stds = []
    colors = []

    for gen in MODELS:
        if not k0_diffs[gen]:
            continue

        labels.append(COLORS[gen][1])
        means.append(np.mean(k0_diffs[gen]))
        stds.append(np.std(k0_diffs[gen]))
        colors.append(COLORS[gen][0])

    ax2.bar(
        labels,
        means,
        yerr=stds,
        capsize=5,
        color=colors,
        edgecolor="black"
    )

    ax2.set_ylabel(r"$|GDD(0)-GDD_{orig}(0)|$")
    ax2.set_title(f"Distance moyenne sur k=0 — orbite {orbit_idx}")

    fig2.tight_layout()
    fig2.savefig(out_file.replace(".png", "_k0_distance.png"), dpi=150)


if __name__ == "__main__":
    main()