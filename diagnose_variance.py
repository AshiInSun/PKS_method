"""
Diagnostic script: analyse la variance de la statistique de convergence
(assortativity, triangles, carrés) en fonction de eta.

Usage:
    python diagnose_variance.py -f <dataset> -a [-ftr <range>] [-ft] [-f3cc] [-n 8] [-T 200] [-j 5]
"""

import argparse
import os
import numpy as np
import copy
import scipy.stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from joblib import Parallel, delayed

from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain


# ---------------------------------------------------------------------------
# Fonctions statistiques
# ---------------------------------------------------------------------------

def autocorr_lag1(series):
    series = np.array(series)
    T = len(series)
    mean = np.mean(series)
    if np.var(series) == 0:
        return 1.0
    R1 = np.sum((series[:-1] - mean) * (series[1:] - mean)) / T
    R0 = np.sum((series - mean) ** 2) / T
    return R1 / R0


def integrated_autocorr_time(series, max_lag=None):
    series = np.array(series, dtype=float)
    T = len(series)
    mean = np.mean(series)
    var = np.var(series)
    if var == 0:
        return float('inf')
    if max_lag is None:
        max_lag = T // 2
    rho = np.correlate(series - mean, series - mean, mode='full')
    rho = rho[T - 1:] / (var * T)
    iat = 1.0
    for k in range(1, max_lag):
        if rho[k] <= 0:
            break
        iat += 2 * rho[k]
        if k > 5 * iat:
            break
    return iat


def check_autocorr_lag1_significant(series, alpha=0.04):
    S_T = np.array(series)
    T = len(S_T)
    mean_st = np.mean(S_T)
    R_1 = 1/T * np.sum((S_T[:-1] - mean_st) * (S_T[1:] - mean_st))
    R_0 = 1/T * np.sum((S_T - mean_st) ** 2)
    if R_0 == 0:
        return 1
    a = R_1 / R_0
    mu = -1 / T
    sigma_2 = (T**4 - 4*T**3 + 4*T - 4) / ((T+1) * T**2 * (T-1)**2)
    z = scipy.stats.norm.ppf(1 - alpha)
    A = (a - mu) / np.sqrt(sigma_2)
    return 1 if A > z else 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mc(graph, gamma, use_triangles, use_assortativity, use_squares,
            use_fixed_triangle, use_fixed_triangle_range,
            use_fixed_tclosedpath, triangle_buffer=0):
    return MarkovChain(
        graph=graph,
        N_swap=0,
        gamma=gamma,
        use_triangles=use_triangles,
        use_assortativity=use_assortativity,
        use_squares=use_squares,
        use_fixed_triangle=use_fixed_triangle or (use_fixed_triangle_range > 0),
        use_fixed_triangle_range=use_fixed_triangle_range,
        use_fixed_tclosedpath=use_fixed_tclosedpath,
        triangle_buffer=triangle_buffer,
        verbose=False,
        keep_record=False,
    )


def run_chain(mc, eta, T_obs):
    """
    Fonction top-level (picklable par joblib).
    Retourne la série de la statistique observée sur T_obs observations.
    """
    series = []
    for _ in range(T_obs):
        mc.run(int(eta))
        if mc.use_assortativity:
            series.append(mc.assortativity)
        elif mc.use_squares:
            series.append(len(mc.squares2edges))
        else:
            series.append(len(mc.triangles2edges))
    return series


# ---------------------------------------------------------------------------
# Diagnostic principal
# ---------------------------------------------------------------------------

def run_diagnosis(dataset, directed, use_triangles, use_assortativity, use_squares,
                  use_fixed_triangle, use_fixed_triangle_range, use_fixed_tclosedpath,
                  eta_fixed, read_gml, n_steps, T_obs, gamma=2, njobs=5,
                  n_burnin=500000, n_burnin_blocks=10000):

    # --- lecture du graphe ---
    print(f"\n{'='*60}")
    print(f"Graphe : {dataset}")
    graph = Graph(directed)
    if read_gml:
        graph.read_gml(dataset)
    else:
        graph.read_ssv(dataset)
    print(f"N={graph.N} noeuds, M={graph.M} arêtes")
    n_burnin = graph.M * 1000

    stat_label = "assortativity" if use_assortativity else ("nb carrés" if use_squares else "nb triangles")
    print(f"Statistique de convergence : {stat_label}")

    print(f"Contrainte triangles : ", end="")
    if use_fixed_triangle_range > 0:
        print(f"ftr={use_fixed_triangle_range} (marge ±{use_fixed_triangle_range})")
    elif use_fixed_triangle:
        print("ft (exact)")
    else:
        print("aucune")
    print(f"Contrainte 3-closed-path : {'oui' if use_fixed_tclosedpath else 'non'}")

    # --- burn-in ---
    print(f"\nBurn-in ({n_burnin} swaps)...")
    mc_burnin = make_mc(
        graph, gamma, use_triangles, use_assortativity, use_squares,
        use_fixed_triangle, use_fixed_triangle_range, use_fixed_tclosedpath
    )
    burnin_window = mc_burnin.run(n_burnin)

    accept_rate = mc_burnin.accept_rate / (mc_burnin.accept_rate + mc_burnin.refusal_rate)
    buffer_after_burnin = mc_burnin.buffer_triangle
    print(f"Taux d'acceptation (burn-in) : {accept_rate:.4f}  ({accept_rate*100:.1f}%)")
    print(f"Eta empirique minimal (1/accept_rate * M) : {int(1/accept_rate * graph.M)}")
    if use_fixed_triangle_range > 0:
        print(f"Buffer triangle après burn-in : {buffer_after_burnin}")

    # --- grille de eta ---
    eta_min_empirical = max(1, int(1/accept_rate * graph.M))
    eta_min_empirical = 1
    if eta_fixed is not None:
        eta_values = [int(eta_fixed)]
    else:
        eta_values = [max(1, int(eta_min_empirical * (2**i) / 4)) for i in range(n_steps)]

    C = 10
    alpha = 0.04
    print(f"\nValeurs de eta testées : {eta_values}")
    print(f"T_obs={T_obs}, C={C} chaînes parallèles, njobs={njobs}\n")

    results = []

    for eta in eta_values:

        chains = [
            make_mc(
                copy.deepcopy(mc_burnin.graph), gamma,
                use_triangles, use_assortativity, use_squares,
                use_fixed_triangle, use_fixed_triangle_range, use_fixed_tclosedpath,
                triangle_buffer=buffer_after_burnin
            )
            for _ in range(C)
        ]

        series_list = Parallel(n_jobs=njobs)(
            delayed(run_chain)(chains[c], eta, T_obs) for c in range(C)
        )

        variances, autocorrs, iats = [], [], []
        d_eta_count = 0
        for series in series_list:
            variances.append(np.var(series))
            autocorrs.append(autocorr_lag1(series))
            iats.append(integrated_autocorr_time(series))
            d_eta_count += check_autocorr_lag1_significant(series, alpha)

        finite_iats = [x for x in iats if not np.isinf(x)]
        mean_iat = np.mean(finite_iats) if finite_iats else float('inf')

        results.append({
            'eta': eta,
            'mean_variance': np.mean(variances),
            'std_variance': np.std(variances),
            'mean_autocorr_lag1': np.mean(autocorrs),
            'std_autocorr_lag1': np.std(autocorrs),
            'mean_iat': mean_iat,
            'd_eta': d_eta_count,
        })

        flag = "✓" if d_eta_count <= 1 else "✗"
        print(f"eta={eta:>10} | var={np.mean(variances):.3e} ± {np.std(variances):.1e}"
              f" | autocorr={np.mean(autocorrs):.3f} ± {np.std(autocorrs):.3f}"
              f" | IAT={mean_iat:>7.1f}"
              f" | d_eta={d_eta_count:>2}/10 {flag}")

    # --- diagnostic de la variance ---
    print(f"\n{'='*60}")
    print("DIAGNOSTIC")
    variances_all = [r['mean_variance'] for r in results]
    if len(variances_all) > 1 and min(variances_all) > 0:
        variance_range = max(variances_all) / min(variances_all)
        print(f"Ratio variance(max)/variance(min) : {variance_range:.2f}")
        if variance_range < 3:
            print("→ Variance STABLE : faible variance intrinsèque à l'espace cible.")
        else:
            print("→ Variance croissante : la chaîne explore encore, mixing insuffisant.")

    # --- tableau récap ---
    print(f"\n{'eta':>12} | {'variance':>12} | {'autocorr_lag1':>14} | {'IAT':>8} | {'d_eta/10':>9}")
    print("-" * 65)
    for r in results:
        flag = " ✓" if r['d_eta'] <= 1 else " ✗"
        print(f"{r['eta']:>12} | {r['mean_variance']:>12.3e} | {r['mean_autocorr_lag1']:>14.3f}"
              f" | {r['mean_iat']:>8.1f} | {r['d_eta']:>4}/10{flag}")

    # --- figures ---
    constraint_str = f"ftr={use_fixed_triangle_range}" if use_fixed_triangle_range > 0 \
        else ("ft" if use_fixed_triangle else "no constraint")
    if use_fixed_tclosedpath:
        constraint_str += "+f3cc"
    title_base = f"{os.path.basename(dataset)} | N={graph.N}, M={graph.M}, " \
                 f"accept_rate={accept_rate:.3f} | {constraint_str}"

    etas = [r['eta'] for r in results]

    # Figure 1 : burn-in
    fig1, ax = plt.subplots(figsize=(10, 4))
    ax.plot(burnin_window, linewidth=0.6, color='steelblue')
    ax.set_xlabel("pas MCMC (swaps tentés)")
    ax.set_ylabel(stat_label)
    ax.set_title(f"Burn-in — {title_base}")
    plt.tight_layout()
    out_burnin = os.path.splitext(os.path.basename(dataset))[0] + '_burnin.png'
    fig1.savefig(out_burnin, dpi=150)
    print(f"\nFigure burn-in sauvegardée : {out_burnin}")

    # Figure 2 : diagnostic eta
    fig2, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig2.suptitle(title_base, fontsize=9)

    axes[0].semilogx(etas, [r['d_eta'] for r in results], 'o-', color='steelblue')
    axes[0].axhline(y=1, color='red', linestyle='--', label='seuil Dutta (u=1)')
    axes[0].set_xlabel('eta')
    axes[0].set_ylabel('d_eta (nb chaînes autocorrélées / 10)')
    axes[0].set_title("Critère Dutta et al.")
    axes[0].legend()
    axes[0].set_ylim(0, C + 1)

    axes[1].semilogx(etas, [r['mean_autocorr_lag1'] for r in results], 'o-', color='darkorange')
    axes[1].fill_between(
        etas,
        [r['mean_autocorr_lag1'] - r['std_autocorr_lag1'] for r in results],
        [r['mean_autocorr_lag1'] + r['std_autocorr_lag1'] for r in results],
        alpha=0.2, color='darkorange'
    )
    axes[1].axhline(y=0, color='gray', linestyle='--')
    axes[1].set_xlabel('eta')
    axes[1].set_ylabel('autocorr lag-1')
    axes[1].set_title("Autocorrélation lag-1 (moy ± std sur C=10)")

    axes[2].semilogx(etas, [r['mean_variance'] for r in results], 'o-', color='seagreen')
    axes[2].fill_between(
        etas,
        [r['mean_variance'] - r['std_variance'] for r in results],
        [r['mean_variance'] + r['std_variance'] for r in results],
        alpha=0.2, color='seagreen'
    )
    axes[2].set_xlabel('eta')
    axes[2].set_ylabel(f'variance ({stat_label})')
    axes[2].set_title("Variance de la statistique (moy ± std sur C=10)")

    plt.tight_layout()
    out_diag = os.path.splitext(os.path.basename(dataset))[0] + '_diagnosis.png'
    fig2.savefig(out_diag, dpi=150)
    print(f"Figure diagnostic sauvegardée : {out_diag}")

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Diagnostic variance/autocorrélation pour k-edge-swap')
    parser.add_argument('-f', '--dataset', type=str, required=True)
    parser.add_argument('-gml', '--read_gml', action='store_true', default=False)
    parser.add_argument('-d', '--directed', action='store_true', default=False)
    parser.add_argument('-g', '--gamma', type=int, default=2)

    # statistique de convergence
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-t', '--triangles', action='store_true', default=False)
    group.add_argument('-a', '--assortativity', action='store_true', default=False)
    group.add_argument('-s', '--squares', action='store_true', default=False)

    # contraintes de génération
    parser.add_argument('-ft', '--fixed_triangle', action='store_true', default=False)
    parser.add_argument('-ftr', '--fixed_triangle_range', type=int, default=0)
    parser.add_argument('-f3cc', '--fixed_three_closed_path', action='store_true', default=False,
                        help='Fixer le nombre de 3-closed-paths (comme dans main.py)')

    # paramètres du diagnostic
    parser.add_argument('-e', '--eta', type=float, default=None)
    parser.add_argument('-n', '--n_steps', type=int, default=8)
    parser.add_argument('-T', '--T_obs', type=int, default=200)
    parser.add_argument('-j', '--njobs', type=int, default=5)
    parser.add_argument('--burnin', type=int, default=500000,
                        help='Nombre total de swaps du burn-in (défaut: 500000).')
    parser.add_argument('--burnin_blocks', type=int, default=10000,
                        help='Nombre de points collectés pendant le burn-in (défaut: 10000).')

    args = parser.parse_args()

    use_fixed_triangle = args.fixed_triangle or (args.fixed_triangle_range > 0)

    run_diagnosis(
        dataset=args.dataset,
        directed=args.directed,
        use_triangles=args.triangles,
        use_assortativity=args.assortativity,
        use_squares=args.squares,
        use_fixed_triangle=use_fixed_triangle,
        use_fixed_triangle_range=args.fixed_triangle_range,
        use_fixed_tclosedpath=args.fixed_three_closed_path,
        eta_fixed=args.eta,
        read_gml=args.read_gml,
        n_steps=args.n_steps,
        T_obs=args.T_obs,
        gamma=args.gamma,
        njobs=args.njobs,
        n_burnin=args.burnin,
        n_burnin_blocks=args.burnin_blocks,
    )


if __name__ == '__main__':
    main()