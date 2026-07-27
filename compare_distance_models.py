"""
Comparaison des modèles sur la distribution des distances (équivalent de
compare_models.py mais pour distance_distribution.json au lieu de
graphlet_counts.json) :
- Z-scores par bin de distance (original vs randoms) pour chaque graphe
- Agrégation mean/median (+ std / IQR) par bin, par modèle, par cluster et globale
- Indice de proximité (|z| moyen/médian) par cluster + global, comme pour les graphlets
- Bonus : écart original-vs-randoms sur diameter et disconnected_fraction,
  vu que ces deux scalaires ne sont pas capturés par les z-scores de distribution
  (cf. distance_analysis.py — la distribution est normalisée sur les paires
  connectées uniquement)

Usage:
    python compare_distance_models.py results_dir [out_dir]
"""

import json
import os
import sys
import warnings
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams["figure.facecolor"] = "white"
mpl.rcParams["axes.facecolor"] = "white"
mpl.rcParams["savefig.facecolor"] = "white"

MODELS = ["gen_no_constraint", "gen_ftr1", "gen_jdm"]
COLORS = {"gen_no_constraint": "#51ff3d", "gen_ftr1": "#E230E8", "gen_jdm": "#2587f7"}
LABELS = {"gen_ftr1": "Triangles +- 1", "gen_no_constraint": "Configuration Model", "gen_jdm": "Joint Degree Matrix"}

YMAX_ABS = 20
DIST_CUTOFF = 10  # n'affiche que les 10 premiers bins de distance sur les courbes de z-score


# -----------------------------
# DATA LOADING
# -----------------------------
def load_json(path):
    with open(path) as f:
        return json.load(f)


def split_distributions(data):
    """original: vecteur distribution ; randoms: matrice (N, n_bins)"""
    original = np.array(data["__original__"]["distribution"])
    randoms = np.array([v["distribution"] for k, v in data.items() if k != "__original__"])
    return original, randoms


def split_scalars(data):
    """diameter / disconnected_fraction pour l'original et pour chaque random"""
    orig = data["__original__"]
    orig_scalars = {
        "diameter": orig["diameter"],
        "disconnected_fraction": orig["disconnected_fraction"],
    }
    rand_scalars = {
        "diameter": np.array([v["diameter"] for k, v in data.items() if k != "__original__"]),
        "disconnected_fraction": np.array(
            [v["disconnected_fraction"] for k, v in data.items() if k != "__original__"]
        ),
    }
    return orig_scalars, rand_scalars


def compute_zscores(original, randoms):
    mean = randoms.mean(axis=0)
    std = randoms.std(axis=0) + 1e-9
    z = (original - mean) / std
    z[original == 0] = np.nan
    return z


# -----------------------------
# COLLECT Z-SCORES + SCALAIRES PAR CLUSTER + GLOBAL
# -----------------------------
def collect_zscores(results_dir):
    """
    Retourne :
      collected_global : { model: [z_vec, ...] }
      collected_cluster: { cluster: { model: [z_vec, ...] } }
      scalars_global    : { model: {"diameter_diff": [...], "disc_diff": [...]} }
      scalars_cluster   : { cluster: { model: {"diameter_diff": [...], "disc_diff": [...]} } }
    diameter_diff / disc_diff = original - moyenne(randoms), par graphe
    """
    collected_global = {m: [] for m in MODELS}
    collected_cluster = {}
    scalars_global = {m: {"diameter_diff": [], "disc_diff": []} for m in MODELS}
    scalars_cluster = {}

    for cluster in sorted(os.listdir(results_dir)):
        cluster_path = os.path.join(results_dir, cluster)
        if not os.path.isdir(cluster_path):
            continue

        collected_cluster[cluster] = {m: [] for m in MODELS}
        scalars_cluster[cluster] = {m: {"diameter_diff": [], "disc_diff": []} for m in MODELS}

        for graph_id in sorted(os.listdir(cluster_path)):
            graph_path = os.path.join(cluster_path, graph_id)
            if not os.path.isdir(graph_path):
                continue

            paths = {}
            for model in MODELS:
                p = os.path.join(graph_path, model, "distance_distribution.json")
                if os.path.exists(p):
                    paths[model] = p

            if len(paths) < len(MODELS):
                continue

            for model, p in paths.items():
                data = load_json(p)
                if "__original__" not in data:
                    continue
                original, randoms = split_distributions(data)
                if randoms.shape[0] == 0:
                    continue

                z = compute_zscores(original, randoms)
                collected_global[model].append(z)
                collected_cluster[cluster][model].append(z)

                orig_scalars, rand_scalars = split_scalars(data)
                diam_diff = orig_scalars["diameter"] - rand_scalars["diameter"].mean()
                disc_diff = orig_scalars["disconnected_fraction"] - rand_scalars["disconnected_fraction"].mean()
                scalars_global[model]["diameter_diff"].append(diam_diff)
                scalars_global[model]["disc_diff"].append(disc_diff)
                scalars_cluster[cluster][model]["diameter_diff"].append(diam_diff)
                scalars_cluster[cluster][model]["disc_diff"].append(disc_diff)

    return collected_global, collected_cluster, scalars_global, scalars_cluster


# -----------------------------
# AGGREGATE : mean ± std / median ± IQR par bin de distance
# -----------------------------
def aggregate(collected):
    agg = {}
    for model in MODELS:
        vecs = np.array(collected[model], dtype=float)
        if vecs.shape[0] == 0:
            agg[model] = {"mean": None, "std": None, "median": None, "q25": None, "q75": None, "n": 0}
        else:
            abs_vecs = np.abs(vecs)
            # Un bin jamais atteint par l'original (typiquement ">MAX_DIST") vaut 0
            # partout -> z-score mis à NaN pour ce bin sur tous les graphes ->
            # colonne 100% NaN. C'est attendu (le bin sera simplement absent des
            # courbes), donc on masque les warnings NumPy correspondants plutôt
            # que de les laisser polluer la sortie.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                agg[model] = {
                    "mean": np.nanmean(vecs, axis=0),
                    "std": np.nanstd(vecs, axis=0),
                    "median": np.nanmedian(abs_vecs, axis=0),
                    "q25": np.nanpercentile(abs_vecs, 25, axis=0),
                    "q75": np.nanpercentile(abs_vecs, 75, axis=0),
                    "n": vecs.shape[0],
                }
    return agg


def aggregate_scalar(scalars, key):
    """mean ± std de `key` (diameter_diff ou disc_diff), par graphe, par modèle"""
    agg = {}
    for model in MODELS:
        vals = np.array(scalars[model][key], dtype=float)
        if vals.size == 0:
            agg[model] = {"mean": np.nan, "std": np.nan, "n": 0}
        else:
            agg[model] = {"mean": np.nanmean(vals), "std": np.nanstd(vals), "n": vals.size}
    return agg


# -----------------------------
# PROXIMITY INDEX (mean / median de |z| sur tous les bins et tous les graphes)
# -----------------------------
def compute_proximity_index(collected):
    result = {}
    for model in MODELS:
        vecs = np.array(collected[model], dtype=float)
        if vecs.shape[0] == 0:
            result[model] = {"index": np.nan, "std": np.nan, "n": 0}
        else:
            abs_z = np.abs(vecs)
            per_graph = np.nanmean(abs_z, axis=1)
            result[model] = {"index": np.nanmean(per_graph), "std": np.nanstd(per_graph), "n": vecs.shape[0]}
    return result


def compute_median_proximity_index(collected):
    result = {}
    for model in MODELS:
        vecs = np.array(collected[model], dtype=float)
        if vecs.shape[0] == 0:
            result[model] = {"index": np.nan, "q25": np.nan, "q75": np.nan, "n": 0}
        else:
            abs_z = np.abs(vecs)
            per_graph = np.nanmedian(abs_z, axis=1)
            result[model] = {
                "index": np.nanmedian(per_graph),
                "q25": np.nanpercentile(per_graph, 25),
                "q75": np.nanpercentile(per_graph, 75),
                "n": vecs.shape[0],
            }
    return result


# -----------------------------
# PLOT HELPERS
# -----------------------------
def _distance_labels(n_bins):
    return [str(d) for d in range(1, n_bins)] + [f">{n_bins - 1}"]


def _annotate_overflow(ax, x_pos, raw, ymin, ymax, color, rank=0, step=0.9):
    """rank : position du modèle parmi ceux qui dépassent sur ce bin, pour empiler
    les valeurs verticalement au lieu de les superposer."""
    if np.isnan(raw):
        return
    if raw > ymax:
        ax.text(x_pos, ymax + 0.4 + rank * step, f"{raw:.1f}", ha="center",
                va="bottom", fontsize=9, color=color, fontweight="bold", clip_on=False)
    elif raw < ymin:
        ax.text(x_pos, ymin - 0.4 - rank * step, f"{raw:.1f}", ha="center",
                va="top", fontsize=9, color=color, fontweight="bold", clip_on=False)


def _annotate_overflow_stacked(ax, per_model_values, ymin, ymax, colors):
    """
    per_model_values : { model: array de valeurs (une par bin affiché) }
    Pour chaque bin, empile les annotations des modèles qui dépassent
    ymax (ou passent sous ymin), triées par valeur croissante, pour
    qu'elles ne se superposent jamais.
    """
    n_bins = len(next(iter(per_model_values.values())))
    for j in range(n_bins):
        over = [(model, v[j]) for model, v in per_model_values.items()
                if not np.isnan(v[j]) and v[j] > ymax]
        over.sort(key=lambda t: t[1])
        for rank, (model, raw) in enumerate(over):
            _annotate_overflow(ax, j, raw, ymin, ymax, colors[model], rank=rank)

        under = [(model, v[j]) for model, v in per_model_values.items()
                 if not np.isnan(v[j]) and v[j] < ymin]
        under.sort(key=lambda t: -t[1])
        for rank, (model, raw) in enumerate(under):
            _annotate_overflow(ax, j, raw, ymin, ymax, colors[model], rank=rank)


# -----------------------------
# PLOT : |z| moyen / médian par bin de distance
# -----------------------------
def plot_mean_abszscore_line(agg, n_bins):
    n_show = min(DIST_CUTOFF, n_bins)
    x = np.arange(n_show)
    labels = _distance_labels(n_bins)[:n_show]

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.subplots_adjust(bottom=0.15, top=0.78)

    per_model_abs_mean = {}

    for model in MODELS:
        d = agg[model]
        if d["mean"] is None:
            continue
        color = COLORS[model]
        lbl = f"{LABELS[model]} (n={d['n']})"

        abs_mean = np.abs(d["mean"])[:n_show]
        std = d["std"][:n_show]
        abs_mean_clamped = np.clip(abs_mean, 0, YMAX_ABS)

        valid = ~np.isnan(abs_mean)
        ax.plot(x[valid], abs_mean_clamped[valid], marker="o", linewidth=1.8,
                markersize=5, color=color, label=lbl)
        ax.fill_between(x[valid],
                         np.clip(abs_mean[valid] - std[valid], 0, YMAX_ABS),
                         np.clip(abs_mean[valid] + std[valid], 0, YMAX_ABS),
                         alpha=0.15, color=color)

        per_model_abs_mean[model] = abs_mean

    _annotate_overflow_stacked(ax, per_model_abs_mean, 0, YMAX_ABS, COLORS)

    ax.axhline(2, linestyle="--", color="gray", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Distance")
    ax.set_ylim(0, YMAX_ABS)
    ax.set_xlim(-0.5, n_show - 0.5)
    ax.set_ylabel("Mean |Z-score| (± std over graphs)")
    ax.set_title("Mean |Z-score| per distance bin", y=1.18)
    ax.legend(fontsize=9)

    return fig


def plot_median_abszscore_line(agg, n_bins):
    n_show = min(DIST_CUTOFF, n_bins)
    x = np.arange(n_show)
    labels = _distance_labels(n_bins)[:n_show]

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.subplots_adjust(bottom=0.15, top=0.78)

    per_model_abs_median = {}

    for model in MODELS:
        d = agg[model]
        if d["median"] is None:
            continue
        color = COLORS[model]
        lbl = f"{LABELS[model]} (n={d['n']})"

        abs_median = np.abs(d["median"])[:n_show]
        q25 = d["q25"][:n_show]
        q75 = d["q75"][:n_show]
        abs_median_clamped = np.clip(abs_median, 0, YMAX_ABS)

        valid = ~np.isnan(abs_median)
        ax.plot(x[valid], abs_median_clamped[valid], marker="o", linewidth=1.8,
                markersize=5, color=color, label=lbl)
        ax.fill_between(x[valid],
                         np.clip(q25[valid], 0, YMAX_ABS),
                         np.clip(q75[valid], 0, YMAX_ABS),
                         alpha=0.15, color=color)

        per_model_abs_median[model] = abs_median

    _annotate_overflow_stacked(ax, per_model_abs_median, 0, YMAX_ABS, COLORS)

    ax.axhline(2, linestyle="--", color="gray", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Distance")
    ax.set_ylim(0, YMAX_ABS)
    ax.set_xlim(-0.5, n_show - 0.5)
    ax.set_ylabel("Median |Z-score| (IQR over graphs)")
    ax.set_title("Median |Z-score| per distance bin", y=1.18)
    ax.legend(fontsize=9)

    return fig


# -----------------------------
# PLOT : indice de proximité par cluster + global
# -----------------------------
def plot_proximity_index(proximity_per_cluster, proximity_global):
    cluster_names = sorted(proximity_per_cluster.keys())
    x_labels = cluster_names + ["GLOBAL"]
    x = np.arange(len(x_labels))

    n_models = len(MODELS)
    group_width = 0.8
    bar_width = group_width / n_models

    fig, ax = plt.subplots(figsize=(max(8, len(x_labels) * 1.2 + 2), 5))
    fig.subplots_adjust(bottom=0.15)

    for i, model in enumerate(MODELS):
        offset = (i - (n_models - 1) / 2) * bar_width
        color = COLORS[model]

        indices, stds = [], []
        for cluster in cluster_names:
            d = proximity_per_cluster[cluster][model]
            indices.append(d["index"])
            stds.append(d["std"])
        d_global = proximity_global[model]
        indices.append(d_global["index"])
        stds.append(d_global["std"])

        indices = np.array(indices)
        stds = np.array(stds)
        displayed = np.minimum(indices, YMAX_ABS)

        bars = ax.bar(x + offset, displayed, width=bar_width * 0.95, color=color, alpha=0.6, label=LABELS[model])

        for bar, true_val in zip(bars, indices):
            if true_val > YMAX_ABS:
                txt = f"{true_val:.1e}" if true_val >= 1000 else f"{true_val:.1f}"
                ax.text(bar.get_x() + bar.get_width() / 2, YMAX_ABS + 0.3, txt,
                        ha="center", va="bottom", fontsize=8, rotation=90, clip_on=False)

        ax.errorbar(x + offset, indices, yerr=stds, fmt="none", color="black", capsize=4, linewidth=1)

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Mean |Z-score| (proximity index)")
    ax.set_title("Proximity index per cluster (and global) — distances", y=1.02)
    ax.axhline(2, linestyle="--", color="gray", linewidth=0.8)
    ax.set_ylim(0, YMAX_ABS)
    ax.legend(fontsize=9)

    return fig


def plot_median_proximity_index(proximity_per_cluster, proximity_global):
    cluster_names = sorted(proximity_per_cluster.keys())
    x_labels = cluster_names + ["GLOBAL"]
    x = np.arange(len(x_labels))

    n_models = len(MODELS)
    group_width = 0.8
    bar_width = group_width / n_models

    fig, ax = plt.subplots(figsize=(max(8, len(x_labels) * 1.2 + 2), 5))
    fig.subplots_adjust(bottom=0.15)

    for i, model in enumerate(MODELS):
        offset = (i - (n_models - 1) / 2) * bar_width
        color = COLORS[model]

        indices, q25s, q75s = [], [], []
        for cluster in cluster_names:
            d = proximity_per_cluster[cluster][model]
            indices.append(d["index"])
            q25s.append(d["q25"])
            q75s.append(d["q75"])
        d_global = proximity_global[model]
        indices.append(d_global["index"])
        q25s.append(d_global["q25"])
        q75s.append(d_global["q75"])

        indices = np.array(indices)
        q25s = np.array(q25s)
        q75s = np.array(q75s)
        displayed = np.minimum(indices, YMAX_ABS)

        bars = ax.bar(x + offset, displayed, width=bar_width * 0.95, color=color, alpha=0.6, label=LABELS[model])

        for bar, true_val in zip(bars, indices):
            if true_val > YMAX_ABS:
                txt = f"{true_val:.1e}" if true_val >= 1000 else f"{true_val:.1f}"
                ax.text(bar.get_x() + bar.get_width() / 2, YMAX_ABS + 0.3, txt,
                        ha="center", va="bottom", fontsize=8, rotation=90, clip_on=False)

        ax.errorbar(x + offset, indices, yerr=[indices - q25s, q75s - indices],
                    fmt="none", color="black", capsize=4, linewidth=1)

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Median |Z-score| (proximity index)")
    ax.set_title("Median proximity index per cluster (and global) — distances", y=1.02)
    ax.axhline(2, linestyle="--", color="gray", linewidth=0.8)
    ax.set_ylim(0, 7)
    ax.legend(fontsize=9)

    return fig


# -----------------------------
# PLOT : écart original-randoms sur un scalaire (diameter ou disconnected_fraction)
# -----------------------------
def plot_scalar_diff(scalars_per_cluster, scalars_global, key, ylabel, title, out_ylim=None):
    cluster_names = sorted(scalars_per_cluster.keys())
    x_labels = cluster_names + ["GLOBAL"]
    x = np.arange(len(x_labels))

    cluster_aggs = {c: aggregate_scalar(scalars_per_cluster[c], key) for c in cluster_names}
    global_agg = aggregate_scalar(scalars_global, key)

    n_models = len(MODELS)
    group_width = 0.8
    bar_width = group_width / n_models

    fig, ax = plt.subplots(figsize=(max(8, len(x_labels) * 1.2 + 2), 5))
    fig.subplots_adjust(bottom=0.15)

    for i, model in enumerate(MODELS):
        offset = (i - (n_models - 1) / 2) * bar_width
        color = COLORS[model]

        means = [cluster_aggs[c][model]["mean"] for c in cluster_names] + [global_agg[model]["mean"]]
        stds = [cluster_aggs[c][model]["std"] for c in cluster_names] + [global_agg[model]["std"]]

        ax.bar(x + offset, means, width=bar_width * 0.95, color=color, alpha=0.6, label=LABELS[model])
        ax.errorbar(x + offset, means, yerr=stds, fmt="none", color="black", capsize=4, linewidth=1)

    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title, y=1.02)
    if out_ylim:
        ax.set_ylim(*out_ylim)
    ax.legend(fontsize=9)

    return fig


# -----------------------------
# MAIN
# -----------------------------
def main(results_dir, out_dir=None):
    if out_dir is None:
        out_dir = results_dir
    os.makedirs(out_dir, exist_ok=True)

    print("Collecting distance z-scores...")
    collected_global, collected_cluster, scalars_global, scalars_cluster = collect_zscores(results_dir)

    for model in MODELS:
        n = len(collected_global[model])
        print(f"  {model} : {n} graphes (global)")

    n_bins = None
    for model in MODELS:
        if collected_global[model]:
            n_bins = len(collected_global[model][0])
            break
    if n_bins is None:
        print("Aucune donnée trouvée (vérifiez results_dir et les noms de modèles dans MODELS).")
        return

    print("Aggregating...")
    agg_global = aggregate(collected_global)

    out = os.path.join(out_dir, "mean_abszscore_line_distance.png")
    fig = plot_mean_abszscore_line(agg_global, n_bins)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    out = os.path.join(out_dir, "median_abszscore_line_distance.png")
    fig = plot_median_abszscore_line(agg_global, n_bins)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    print("Computing proximity indices (mean)...")
    proximity_global = compute_proximity_index(collected_global)
    proximity_per_cluster = {c: compute_proximity_index(collected_cluster[c]) for c in collected_cluster}
    for model in MODELS:
        d = proximity_global[model]
        print(f"  GLOBAL / {model} : index={d['index']:.3f} ± {d['std']:.3f} (n={d['n']})")

    out = os.path.join(out_dir, "proximity_index_per_cluster_distance.png")
    fig = plot_proximity_index(proximity_per_cluster, proximity_global)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    print("Computing proximity indices (median)...")
    med_global = compute_median_proximity_index(collected_global)
    med_per_cluster = {c: compute_median_proximity_index(collected_cluster[c]) for c in collected_cluster}
    for model in MODELS:
        d = med_global[model]
        print(f"  GLOBAL / {model} : index={d['index']:.3f} [{d['q25']:.3f}, {d['q75']:.3f}] (n={d['n']})")

    out = os.path.join(out_dir, "proximity_median_index_per_cluster_distance.png")
    fig = plot_median_proximity_index(med_per_cluster, med_global)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    print("Comparing diameter / disconnected_fraction (original - randoms)...")
    out = os.path.join(out_dir, "diameter_diff_per_cluster.png")
    fig = plot_scalar_diff(scalars_cluster, scalars_global, "diameter_diff",
                            "Original − moyenne(randoms)  [diameter]",
                            "Écart de diameter (original vs randoms)")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    out = os.path.join(out_dir, "disconnected_fraction_diff_per_cluster.png")
    fig = plot_scalar_diff(scalars_cluster, scalars_global, "disc_diff",
                            "Original − moyenne(randoms)  [disconnected_fraction]",
                            "Écart de disconnected_fraction (original vs randoms)",
                            out_ylim=(-1, 1))
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compare_distance_models.py results_dir [out_dir]")
        sys.exit(1)
    results_dir = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else None
    main(results_dir, out_dir)