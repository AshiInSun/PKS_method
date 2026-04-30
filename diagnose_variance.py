"""
Diagnostic script: analyse la variance de la statistique de convergence
(assortativity ou triangles) en fonction de eta, pour comparer des graphes
qui passent le critère de Dutta et al. (karate club) et ceux qui ne passent pas
(ego-graphes).

Usage:
    python diagnose_variance.py -f <dataset> -a [-ftr <range>] [-ft] [-n 8] [-T 200]

Options:
    -f / --dataset      : chemin vers le fichier graphe
    -t / --triangles    : utiliser le nombre de triangles comme statistique de convergence
    -a / --assortativity: utiliser l'assortativity comme statistique de convergence
    -ft                 : fixer exactement le nombre de triangles (contrainte de génération)
    -ftr / --fixed_triangle_range : marge autorisée sur le nombre de triangles (contrainte souple)
    -gml                : lire un fichier GML
    -d / --directed     : graphe dirigé
    -n / --n_steps      : nombre de valeurs de eta à tester (défaut: 8)
    -T / --T_obs        : nombre d'observations par valeur de eta (défaut: 200)
    -g / --gamma        : exposant de la loi de Zipf pour le choix de k (défaut: 2)
"""

import argparse
import sys
import numpy as np
import copy
import scipy.stats
import matplotlib.pyplot as plt

from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain


def autocorr_lag1(series):
    """Calcule l'autocorrélation au lag 1 d'une série."""
    series = np.array(series)
    T = len(series)
    mean = np.mean(series)
    if np.var(series) == 0:
        return 1.0
    R1 = np.sum((series[:-1] - mean) * (series[1:] - mean)) / T
    R0 = np.sum((series - mean) ** 2) / T
    return R1 / R0


def integrated_autocorr_time(series, max_lag=None):
    """
    Estime le temps d'autocorrélation intégré (IAT) de Sokal.
    IAT = 1 + 2 * sum_{k=1}^{inf} rho(k)
    Fenêtrage : on coupe quand rho(k) <= 0 ou k > 5 * IAT (règle de Sokal).
    """
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
    """
    Reproduit exactement le test CheckAutocorrLag1 de Stat.py.
    Retourne 1 si l'autocorrélation lag-1 est significativement > 0.
    """
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


def make_mc(graph, gamma, use_triangles, use_assortativity,
            use_fixed_triangle, use_fixed_triangle_range, triangle_buffer=0):
    """Instancie un MarkovChain avec les bonnes contraintes."""
    return MarkovChain(
        graph=graph,
        N_swap=0,
        gamma=gamma,
        use_triangles=use_triangles,
        use_assortativity=use_assortativity,
        use_fixed_triangle=use_fixed_triangle or (use_fixed_triangle_range > 0),
        use_fixed_triangle_range=use_fixed_triangle_range,
        triangle_buffer=triangle_buffer,
        verbose=False,
        keep_record=False,
    )


def run_diagnosis(dataset, directed, use_triangles, use_assortativity,
                  use_fixed_triangle, use_fixed_triangle_range,
                  eta_fixed, read_gml, n_steps, T_obs, gamma=2):

    # --- lecture du graphe ---
    print(f"\n{'='*60}")
    print(f"Graphe : {dataset}")
    graph = Graph(directed)
    if read_gml:
        graph.read_gml(dataset)
    else:
        graph.read_ssv(dataset)
    print(f"N={graph.N} noeuds, M={graph.M} arêtes")
    print(f"Statistique de convergence : {'triangles' if use_triangles else 'assortativity'}")
    print(f"Contrainte triangles : ", end="")
    if use_fixed_triangle_range > 0:
        print(f"ftr={use_fixed_triangle_range} (marge ±{use_fixed_triangle_range})")
    elif use_fixed_triangle:
        print("ft (exact)")
    else:
        print("aucune")

    # --- burn-in ---
    N_burnin = 1000 * graph.M
    print(f"\nBurn-in ({N_burnin} swaps)...")
    mc_burnin = make_mc(
        graph, gamma, use_triangles, use_assortativity,
        use_fixed_triangle, use_fixed_triangle_range
    )
    mc_burnin.run(N_burnin)

    accept_rate = mc_burnin.accept_rate / (mc_burnin.accept_rate + mc_burnin.refusal_rate)
    buffer_after_burnin = mc_burnin.buffer_triangle
    print(f"Taux d'acceptation (burn-in) : {accept_rate:.4f}  ({accept_rate*100:.1f}%)")
    print(f"Eta empirique minimal (1/accept_rate * M) : {int(1/accept_rate * graph.M)}")
    if use_fixed_triangle_range > 0:
        print(f"Buffer triangle après burn-in : {buffer_after_burnin}")

    # --- grille de eta ---
    eta_min_empirical = max(1, int(1 / accept_rate * graph.M))
    if eta_fixed is not None:
        eta_values = [int(eta_fixed)]
    else:
        # grille log centrée autour de eta_min_empirical
        eta_values = [max(1, int(eta_min_empirical * (2**i) / 4)) for i in range(n_steps)]

    print(f"\nValeurs de eta testées : {eta_values}")
    print(f"T_obs (observations par eta) : {T_obs}")
    print(f"C (chaînes parallèles) : 10\n")

    C = 10
    alpha = 0.04
    results = []

    for eta in eta_values:
        variances = []
        autocorrs = []
        iats = []
        d_eta_count = 0

        for c in range(C):
            mc = make_mc(
                copy.deepcopy(mc_burnin.graph), gamma,
                use_triangles, use_assortativity,
                use_fixed_triangle, use_fixed_triangle_range,
                triangle_buffer=buffer_after_burnin
            )

            series = []
            for _ in range(T_obs):
                mc.run(int(eta))
                if use_assortativity:
                    series.append(mc.assortativity)
                else:
                    series.append(len(mc.triangles2edges))

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
            print("→ Variance STABLE quelle que soit eta.")
            print("  La faible variance semble intrinsèque à l'espace cible,")
            print("  pas un artefact de mauvais mixing.")
            print("  Le critère d'autocorrélation lag-1 est inadapté pour ce graphe.")
        else:
            print("→ Variance croissante avec eta.")
            print("  La chaîne explore mieux avec des eta plus grands.")
            print("  Le problème est probablement le mixing, pas la statistique.")

    # --- tableau récap ---
    print(f"\n{'eta':>12} | {'variance':>12} | {'autocorr_lag1':>14} | {'IAT':>8} | {'d_eta/10':>9}")
    print("-" * 65)
    for r in results:
        flag = " ✓" if r['d_eta'] <= 1 else " ✗"
        print(f"{r['eta']:>12} | {r['mean_variance']:>12.3e} | {r['mean_autocorr_lag1']:>14.3f}"
              f" | {r['mean_iat']:>8.1f} | {r['d_eta']:>4}/10{flag}")

    # --- figure ---
    etas = [r['eta'] for r in results]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    constraint_str = f"ftr={use_fixed_triangle_range}" if use_fixed_triangle_range > 0 \
        else ("ft" if use_fixed_triangle else "no constraint")
    fig.suptitle(
        f"{dataset} | N={graph.N}, M={graph.M}, accept_rate={accept_rate:.3f} | {constraint_str}",
        fontsize=9
    )

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
    axes[2].set_ylabel('variance de la statistique')
    axes[2].set_title("Variance de la statistique (moy ± std sur C=10)")

    plt.tight_layout()
    import os
    out_name = os.path.splitext(os.path.basename(dataset))[0] + '_diagnosis.png'
    plt.savefig(out_name, dpi=150)
    print(f"\nFigure sauvegardée : {out_name}")
    plt.show()

    return results


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

    # contraintes sur les triangles
    parser.add_argument('-ft', '--fixed_triangle', action='store_true', default=False,
                        help='Fixer exactement le nombre de triangles')
    parser.add_argument('-ftr', '--fixed_triangle_range', type=int, default=0,
                        help='Marge autorisée sur le nombre de triangles (ex: -ftr 5)')

    # paramètres du diagnostic
    parser.add_argument('-e', '--eta', type=float, default=None,
                        help='Valeur fixe de eta (si non spécifié, teste une grille)')
    parser.add_argument('-n', '--n_steps', type=int, default=8,
                        help='Nombre de valeurs de eta à tester')
    parser.add_argument('-T', '--T_obs', type=int, default=200,
                        help='Nombre d\'observations par valeur de eta')

    args = parser.parse_args()

    use_fixed_triangle = args.fixed_triangle or (args.fixed_triangle_range > 0)

    run_diagnosis(
        dataset=args.dataset,
        directed=args.directed,
        use_triangles=args.triangles,
        use_assortativity=args.assortativity,
        use_fixed_triangle=use_fixed_triangle,
        use_fixed_triangle_range=args.fixed_triangle_range,
        eta_fixed=args.eta,
        read_gml=args.read_gml,
        n_steps=args.n_steps,
        T_obs=args.T_obs,
        gamma=args.gamma,
    )


if __name__ == '__main__':
    main()