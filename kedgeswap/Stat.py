# This file is part of K-edge-swap.
#
#    K-edge-swap is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    K-edge-swap is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with K-edge-swap. If not, see <https://www.gnu.org/licenses/>.
import math
import os
import time
import scipy
import argparse
import numpy as np
import copy

from scipy.stats import kstest
from arch.unitroot import DFGLS
from kedgeswap.Graph import Graph
from progressbar import ProgressBar
from joblib import Parallel, delayed
from kedgeswap.MarkovChain import MarkovChain





class Stat():
    """
        Class to compute statistics on a Markov Chain object. This class implements
        methods to estimate the Markov Chain's sampling gap, and to follow its convergence
        using the DFGLS test.

        Attributes:
        -----------
        mc: MarkovChain object
            The MarkovChain object on which we follow the convergence.
        eta: float
            The sampling gap used for the Markov Chain. The sampling gap
            gives a number of steps to make on the Markov Chain to obtain
            two uncorrelated graphs.
        turbo: bool
            Enable to make a fast but unverified estimation of the sampling gap.
        verbose: bool
            Enable to add information to the logs
        
    """
    def __init__(self, mc, eta=None, turbo=False, verbose=False, njobs=1, acf_stability=False, forced_burnin=0):
        #self.use_ks = use_ks
        self.mc = mc # markov chain
        self.eta = eta
        self.turbo = turbo
        self.verbose = verbose
        self.njobs = njobs
        self.acf_stability = acf_stability
        self.forced_burnin = forced_burnin

    def _make_markov_chain(self, graph, N_swap, gamma, triangle_buffer=0):
        """Instancie un MarkovChain avec tous les paramètres de self.mc."""
        return MarkovChain(
            graph, N_swap, gamma,
            use_jd=self.mc.use_jd,
            use_triangles=self.mc.use_triangles,
            use_fixed_triangle=self.mc.use_fixed_triangle,
            use_assortativity=self.mc.use_assortativity,
            use_mutualdiades=self.mc.use_mutualdiades,
            verbose=self.mc.verbose,
            keep_record=False,
            log_dir=None,
            use_fixed_threechains=self.mc.use_fixed_threechains,
            use_fixed_triangle_range=self.mc.use_fixed_triangle_range,
            triangle_buffer=triangle_buffer,
            old_count=self.mc.old_count,
            use_fixed_tclosedpath=self.mc.use_fixed_tclosedpath,
            use_squares=self.mc.use_squares,
        )

    @staticmethod
    def CheckAutocorrLag1(S_T, alpha):
        """ Check the autocorrelation with lag 1 of a time serie.

            Parameters
            ----------
            S_T: list(float)
                List of assortativity(/number of triangles) values
                to test autocorrelation
            alpha: float
                Significance level of the test (usually fixed to 0.04).
        """
        T = len(S_T)
        tau = 10 # lag at which the sample autocorr is calculated
        mean_st = np.mean(S_T)
        var_st = np.var(S_T)

        R_1 = 1/T * sum( np.multiply(S_T[:-1] -mean_st, S_T[1:] - mean_st))
        R_0 = 1/T * sum( np.multiply(S_T -mean_st, S_T - mean_st))
        #a_i = R_1/R_0
        a = R_1/R_0
        #a = np.correlate(S_T-mean_st, S_T-mean_st, mode='full')[T] # mode=full: convolution over each point of overlap - take value at T to get lag=1
        #a = a/ (var_st * len(S_T))

        mu = -1/T
        sigma_2 = (T**4 - 4 * T**3 + 4 * T - 4) / ((T+1)* T**2 * (T-1)**2)
        A = (a - mu)/np.sqrt(sigma_2)
        z = scipy.stats.norm.ppf(1-alpha)
        if A > z:
            return 1, A
        else:
            return 0, A

    def guesstimate_sampling_gap(self, graph, gamma):
        """
            Sampling gap estimation is long, this function gives an empirical estimation of the sampling gap.
            Measure the acceptation rate A of the Markov Chain, and fix the sampling gap as 10*(1/A) * M, 
            where M is the number of edges of the network. This estimation was fixed empirically to overestimate
            the sampling gap we measure using the estimation from Dutta, U. (2022).
        """
        # run a short burn in
        N_swap = 5 * self.mc.graph.M # burn in
        burn_in = MarkovChain(graph, N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles, use_fixed_triangle=self.mc.use_fixed_triangle,
                              use_assortativity=self.mc.use_assortativity, use_mutualdiades=self.mc.use_mutualdiades, 
                              verbose=self.mc.verbose, keep_record=False, log_dir=None, use_fixed_threechains=self.mc.use_fixed_threechains,
                              use_fixed_triangle_range=self.mc.use_fixed_triangle_range, old_count=self.mc.old_count,
                              use_fixed_tclosedpath=self.mc.use_fixed_tclosedpath, use_squares=self.mc.use_squares)
        burn_in.run()
        
        # estimate the acceptation rate of the Markov Chain
        burn_in_rate = burn_in.accept_rate / (burn_in.accept_rate + burn_in.refusal_rate)

        # take a large estimate to overestimate minimum sampling gap value
        eta = 10/burn_in_rate * graph.M
        #print(f'guesstimation: burn in rate {burn_in_rate}, using eta {eta}')
        return eta

    #def linear_estimate_sampling_gap(self, graph, gamma):
    #    """ Estimate the sampling gap for the MCMC, following algorithm 1 (and using the same values) of 
    #    Dutta, U. (2022). Sampling random graphs with specified degree sequences 

    #    """

    #    # run 1 Markov chain to get the S_T timeserie - used to parallelize.
    #    def run_chain(c):
    #        S_T = []
    #        n_swap = int(np.round(eta))
    #        for t in range(T):
    #            mc[c].run(n_swap)
    #            if mc[c].use_assortativity:
    #                S_T.append(mc[c].assortativity)
    #            else:
    #                S_T.append(len(mc[c].triangles2edges))
    #        return S_T

    #    N_swap = 1000 * self.mc.graph.M # burn in 
    #    C = 10
    #    T = 500
    #    #S_T = [] # list of degree assortativity of size T
    #    u = 1 # lower bound on number of mcmc chains that have significant lag-1 autocorrelation
    #    mc = [] # list of C MCMC
    #    alpha = 0.04 # significance level for each test

    #    if self.verbose:
    #        print(f'estimation parameters: N_swap {N_swap}, C {C}, T {T}, u {u}, alpha {alpha}')
    #        print(f'burn in...')
    #    #for c in range(C):
    #    #    if self.verbose:
    #    #        print(f'MCMC {c}/{C}')
    #    #    mc.append(MarkovChain(graph, N_swap, gamma))
    #    #    mc[c].run()
    #    burn_in = MarkovChain(graph, N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles,
    #                          use_assortativity=self.mc.use_assortativity,
    #                          verbose=self.mc.verbose, keep_record=False, log_dir=None)
    #    burn_in.run()
    #    #burn_in_rate = burn_in.accept_rate / (burn_in.accept_rate + burn_in.refusal_rate)

    #    # Measure sampling gap
    #    if self.verbose:
    #        print(f'measuring sampling gap...')

    #    # first eta is estimated from the accept/refuse rate of the burn in
    #    # then dichotomic search to get better eta
    #    #eta = 10 * self.mc.graph.M
    #    #eta = 1/burn_in_rate * self.mc.graph.M
    #    eta=0
    #    d_eta = C
    #    #prev_d_eta = C
    #    #prev_eta = eta
    #    #tuned = False
    #    while (d_eta > u): 
    #        eta += 0.05 * graph.M
    #        if self.verbose:
    #            print(f'considering eta {eta}...')

    #        d_eta = 0
    #        for c in range(C):
    #            S_T = []
    #            if d_eta > u:
    #                continue

    #            if len(mc) <= c:
    #                mc.append(MarkovChain(burn_in.graph.copy(), N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles, use_assortativity=self.mc.use_assortativity, verbose=self.mc.verbose, keep_record=False, log_dir=None))
    #            else:
    #                mc[c] = MarkovChain(burn_in.graph.copy(), N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles, use_assortativity=self.mc.use_assortativity, verbose=self.mc.verbose, keep_record=False, log_dir=None)


    #            #mc[c].run()

    #        S_Ts = Parallel(n_jobs=5)(delayed(run_chain)(c) for c in range(C))
    #        for c in range(C):
    #            d_c = self.CheckAutocorrLag1(S_Ts[c], alpha)
    #            d_eta += d_c
    #            if self.verbose:
    #                print(f'for eta={eta}: d_eta={d_eta}, u={u}')
    #        #if d_eta <= u:
    #        #    prev_eta = eta
    #        #    prev_d_eta = d_eta
    #        #    eta = eta/2
    #        #    #tuned = True
    #        #elif d_eta > u and prev_d_eta <= u:
    #        #    prev_d_eta = d_eta
    #        #    tuned = True
    #        #    eta = prev_eta
    #        #elif d_eta > u and prev_d_eta > u:
    #        #    prev_d_eta = d_eta
    #        #    prev_eta = eta
    #        #    eta = 2 * eta

    #    return eta



    def estimate_sampling_gap(self, graph, gamma):
        """ Estimate the sampling gap for the MCMC, following algorithm 1 (and using the same values) of 
        Dutta, U. (2022). Sampling random graphs with specified degree sequences 

        """
        # run 1 Markov chain to get the S_T timeserie - used to parallelize.
        def run_chain(c):
            S_T = []
            n_swap = int(np.round(eta))
            for t in range(T):
                mc[c].run(n_swap)
                if mc[c].use_assortativity:
                    S_T.append(mc[c].assortativity)
                elif mc[c].use_triangles:
                    S_T.append(len(mc[c].triangles2edges))
                else:
                    S_T.append(len(mc[c].squares2edges))
            return S_T
        if self.forced_burnin == 0:
            N_swap = 1000 * self.mc.graph.M # burn in
        else:
            N_swap = self.forced_burnin
        C = 10
        T = 500
        #S_T = [] # list of degree assortativity of size T
        u = 1 # lower bound on number of mcmc chains that have significant lag-1 autocorrelation
        mc = [] # list of C MCMC
        alpha = 0.04 # significance level for each test

        if self.verbose:
            print(f'eta estimation parameters: N_swap {N_swap}, C {C}, T {T}, u {u}, alpha {alpha}')
            print(f'burn in...')
        #for c in range(C):
        #    if self.verbose:
        #        print(f'MCMC {c}/{C}')
        #    mc.append(MarkovChain(graph, N_swap, gamma))
        #    mc[c].run()

        # run long burn in to reach convergence of the markov chain

        burn_in = MarkovChain(graph, N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles, use_fixed_triangle=self.mc.use_fixed_triangle,
                              use_assortativity=self.mc.use_assortativity,
                              use_mutualdiades=self.mc.use_mutualdiades,
                              verbose=self.mc.verbose, keep_record=False, log_dir=None, use_fixed_threechains=self.mc.use_fixed_threechains,
                              use_fixed_triangle_range=self.mc.use_fixed_triangle_range, old_count=self.mc.old_count,
                              use_fixed_tclosedpath=self.mc.use_fixed_tclosedpath, use_squares=self.mc.use_squares)
        burn_in.run()
        #we need to make the buffer of triangle consistant with the graph.
        self.mc.buffer_triangle = burn_in.buffer_triangle

        # estimate the acceptation rate of the markov chain
        burn_in_rate = burn_in.accept_rate / (burn_in.accept_rate + burn_in.refusal_rate)

        if self.verbose:
            print(burn_in.accept_rate_byk)
            print(burn_in.refusal_rate_byk)
            print(f'Burn In : acceptation/refusals by k : {burn_in_rate}')
            print(burn_in_rate)

        # Measure sampling gap
        if self.verbose:
            print(f'measuring sampling gap...')

        # first eta is estimated from the accept/refuse rate of the burn in
        # then dichotomic search to get better eta
        #eta = 10 * self.mc.graph.M
        eta = math.ceil(1/burn_in_rate * self.mc.graph.M)
        d_eta = C
        e = 0.05
        prev_d_eta = C
        prev_eta = eta
        prev_acfs = []
        first_round = True
        tuned = False
        while (not tuned): 

            if self.verbose:
                print(f'considering eta {eta}...')

            d_eta = 0
            for c in range(C):
                S_T = []
                if d_eta > u:
                    continue

                if len(mc) <= c:

                    mc.append(MarkovChain(copy.deepcopy(burn_in.graph), N_swap, gamma, use_jd=self.mc.use_jd,
                            use_triangles=self.mc.use_triangles, use_fixed_triangle=self.mc.use_fixed_triangle, use_assortativity=self.mc.use_assortativity,
                            use_mutualdiades=self.mc.use_mutualdiades,
                            verbose=self.mc.verbose, keep_record=False, log_dir=None, use_fixed_threechains=self.mc.use_fixed_threechains,
                            use_fixed_triangle_range=self.mc.use_fixed_triangle_range, triangle_buffer=burn_in.buffer_triangle, old_count=self.mc.old_count,
                            use_fixed_tclosedpath=self.mc.use_fixed_tclosedpath, use_squares=self.mc.use_squares))
                else:
                    mc[c] = MarkovChain(copy.deepcopy(burn_in.graph), N_swap, gamma, use_jd=self.mc.use_jd,
                            use_triangles=self.mc.use_triangles,use_fixed_triangle=self.mc.use_fixed_triangle, use_assortativity=self.mc.use_assortativity,
                            use_mutualdiades=self.mc.use_mutualdiades,
                            verbose=self.mc.verbose, keep_record=False, log_dir=None, use_fixed_threechains=self.mc.use_fixed_threechains,
                            use_fixed_triangle_range=self.mc.use_fixed_triangle_range, triangle_buffer=burn_in.buffer_triangle, old_count=self.mc.old_count,
                            use_fixed_tclosedpath=self.mc.use_fixed_tclosedpath, use_squares=self.mc.use_squares)


                #mc[c].run()

            S_Ts = Parallel(n_jobs=self.njobs)(delayed(run_chain)(c) for c in range(C))
            acfs = []
            for c in range(C):
                acfs.append(self.CheckAutocorrLag1(S_Ts[c], alpha))
                d_c, _ = acfs[-1]
                d_eta += d_c
                #if self.verbose:
                #    print(f'for eta={eta}: d_eta={d_eta}, u={u}')

            # check if eta value is accepted - if a most u chains show no correlation 
            # on the S_T timeserie with lag 1, the value of eta is considered valid.
            if self.acf_stability:
                if not first_round:
                    prev_acf_values = [a for _, a in prev_acfs]
                    acf_values = [a for _, a in acfs]
                    stable = abs(np.mean(acf_values) - np.mean(prev_acf_values)) / abs(np.mean(acf_values)) < e
                    print(f'ACF stability check: mean acf {np.mean(acf_values)}, previous mean acf {np.mean(prev_acf_values)}, stable={stable}')
                else:
                    if self.verbose:
                        print('using ACF STABILITY...')
                    stable = False
                    first_round = False
                prev_acfs = acfs
                tuned = stable
                if d_eta <= u:
                    tuned = True
                if not tuned:
                    prev_d_eta = d_eta
                    prev_eta = eta
                    eta = int(1.5 * eta)
                    if self.verbose:
                        print(f'eta {prev_eta} refused (d_eta={d_eta} <= u={u}), trying eta={eta}.')
            else:
                if d_eta <= u:
                    if self.verbose:
                        print(f'eta {eta} accepted (d_eta={d_eta} <= u={u})')
                    prev_d_eta = d_eta
                    if int(prev_eta) == int(eta/2):
                        # don't check eta/2 again
                        tuned = True
                    else:
                        print('trying eta=eta/2...')
                        eta = eta//2
                    prev_eta = eta
                    #tuned = True
                elif d_eta > u and prev_d_eta <= u:
                    prev_d_eta = d_eta
                    tuned = True
                    if self.verbose:
                        print(f'eta {eta} refused (d_eta={d_eta} <= u={u}), using eta={prev_eta}.')
                    eta = prev_eta

                elif d_eta > u and prev_d_eta > u:
                    prev_d_eta = d_eta
                    prev_eta = eta
                    eta = 2 * eta
                    if self.verbose:
                        print(f'eta {prev_eta} refused (d_eta={d_eta} <= u={u}), trying eta={eta}.')

        return eta

    def run_dfgls(self, output):
        """
            Si aucun sampling gap eta n'est spécifié, estime l'IAT via la méthode
            de Sokal. Lance ensuite la chaîne de Markov par blocs de eta pas et
            vérifie la convergence via le test DFGLS.
        """

        # Get sampling gap value
        if self.eta is None:
            t0 = time.time()
            if self.turbo:
                # turbo estimation (inchangé)
                eta = self.guesstimate_sampling_gap(self.mc.graph, self.mc.gamma)
            else:
                eta = self.estimate_sampling_gap(self.mc.graph, self.mc.gamma)
            self.eta = eta
            t1 = time.time()
            eta_time = t1 - t0
        else:
            eta = self.eta
            eta_time = 0

        # Run the markov chain, et vérification convergence via DFGLS (inchangé)
        has_converged = False
        if self.verbose:
            print('running markov chain and checking convergence...')
        t0 = time.time()

        while (not has_converged):
            window = self.mc.run(int(np.round(eta)))
            test = DFGLS(window)

            try:
                if self.verbose:
                    print(
                        f'test statistic : {test.stat},\n Markov chain is stationnary if test statistic < {test.critical_values["1%"]}')

                if test.stat < test.critical_values["1%"]:
                    has_converged = True
                    self.mc.graph.to_ssv(output)
            except:
                print("Warning, dfgls doesn't have enough unique observations to compute.")
                continue

        if self.verbose:
            print('Convergence : acceptation by k')
            for k in self.mc.accept_rate_byk:
                print(f'({k}: {self.mc.accept_rate_byk[k]})', end=', ')
            print('\nConvergence : refusal by k')
            for k in self.mc.refusal_rate_byk:
                print(f'({k}: {self.mc.refusal_rate_byk[k]})', end=', ')
            print('')

        t1 = time.time()
        conv_time = t1 - t0
        print(f'eta estimation took {eta_time} seconds')
        print(f'convergence took {conv_time} seconds')






    def estimate_iat_sokal(self, S_T, C=10):
        """
        Estime le temps d'autocorrélation intégré (IAT, τ) d'une série temporelle
        selon la méthode de fenêtrage de Sokal (1997) / Madras & Sokal (1988).

        La méthode :
        1. Calcule la fonction d'autocorrélation normalisée ρ(k)
        2. Somme ρ(k) jusqu'à la fenêtre M, définie comme
           le plus petit M tel que M >= C * τ_hat(M)
           (critère de Sokal, C ~ 5 recommandé)

        Paramètres
        ----------
        S_T : list ou np.array
            Série temporelle des valeurs (assortativity, nb triangles, etc.)
        C : float
            Constante de fenêtrage de Sokal (défaut : 5)

        Retourne
        --------
        tau : float
            Estimation du temps d'autocorrélation intégré.
            Si la série est trop courte pour satisfaire le critère,
            retourne None pour signaler qu'il faut plus de données.
        """
        S = np.array(S_T, dtype=float)
        N = len(S)

        # Centrage
        S -= np.mean(S)

        # Calcul de l'ACF via FFT (plus efficace que la sommation directe)
        # on zero-pad à 2N pour éviter les effets circulaires
        f = np.fft.rfft(S, n=2 * N)
        acf_raw = np.fft.irfft(f * np.conj(f))[:N]

        # Normalisation par rho(0) pour obtenir rho(k) in [-1, 1]
        acf = acf_raw / acf_raw[0]

        # Sommation avec fenêtrage de Sokal :
        # on accumule tau_hat(M) = 1 + 2*sum_{k=1}^{M} rho(k)
        # et on s'arrête au premier M où M >= C * tau_hat(M)
        tau_hat = 1.0
        for M in range(1, N):
            tau_hat += 2.0 * acf[M]

            # critère de Sokal
            if M >= C * tau_hat:
                return tau_hat  # bonne estimation

        # Si on arrive ici, la série est trop courte
        return None

    def estimate_iat(self, graph, gamma, C=10, max_batches=20):
        """
        Estime le temps d'autocorrélation intégré (IAT, τ) après le burn-in,
        en accumulant des batches de swaps jusqu'à ce que la série soit assez
        longue pour satisfaire le critère de fenêtrage de Sokal (M >= C * τ).

        La taille des batches est déterminée par le taux d'acceptation du
        burn-in : batch_size = ceil(1 / burn_in_rate * m)

        Paramètres
        ----------
        graph : Graph
            Le graphe sur lequel estimer l'IAT
        gamma : int
            Paramètre de la distribution de k
        C : float
            Constante de fenêtrage de Sokal. Défaut : 5
        max_batches : int
            Nombre maximum de batches avant d'abandonner. Défaut : 20

        Retourne
        --------
        tau : float
            Estimation de l'IAT.
        """
        m = graph.M
        S_T = []

        # Burn-in
        print('Burn-in...')
        N_burnin = 1000 * m
        burn_in = MarkovChain(
            graph, N_burnin, gamma,
            use_jd=self.mc.use_jd,
            use_triangles=self.mc.use_triangles,
            use_fixed_triangle=self.mc.use_fixed_triangle,
            use_assortativity=self.mc.use_assortativity,
            use_mutualdiades=self.mc.use_mutualdiades,
            verbose=self.mc.verbose,
            keep_record=False,
            log_dir=None,
            use_fixed_threechains=self.mc.use_fixed_threechains,
            use_fixed_triangle_range=self.mc.use_fixed_triangle_range,
            old_count=self.mc.old_count,
            use_fixed_tclosedpath=self.mc.use_fixed_tclosedpath
        )
        burn_in.run()
        self.mc.buffer_triangle = burn_in.buffer_triangle

        # taille de batch adaptative selon le taux d'acceptation du burn-in
        burn_in_rate = burn_in.accept_rate / (burn_in.accept_rate + burn_in.refusal_rate)
        batch_size = math.ceil(1 / burn_in_rate * m)
        print(f'Taux d\'acceptation burn-in : {burn_in_rate:.3f} → batch_size = {batch_size}')

        # chaîne unique qui continue depuis l'état post burn-in
        mc_iat = MarkovChain(
            burn_in.graph,
            0, gamma,
            use_jd=self.mc.use_jd,
            use_triangles=self.mc.use_triangles,
            use_fixed_triangle=self.mc.use_fixed_triangle,
            use_assortativity=self.mc.use_assortativity,
            use_mutualdiades=self.mc.use_mutualdiades,
            verbose=self.mc.verbose,
            keep_record=False,
            log_dir=None,
            use_fixed_threechains=self.mc.use_fixed_threechains,
            use_fixed_triangle_range=self.mc.use_fixed_triangle_range,
            triangle_buffer=burn_in.buffer_triangle,
            old_count=self.mc.old_count,
            use_fixed_tclosedpath=self.mc.use_fixed_tclosedpath
        )

        # boucle d'accumulation
        for batch_idx in range(max_batches):


            thin = max(1, math.ceil(1 / burn_in_rate)) * 2
            effective_batch = batch_size * thin
            print(f'Batch {batch_idx + 1}/{max_batches} ({effective_batch} swaps) with thinning {thin}...')

            window = mc_iat.run(effective_batch)

            # ton échantillonnage
            window_echantillone = window[::thin]
            S_T.extend(window_echantillone)

            print(f'  Série accumulée : {len(S_T)} valeurs')

            tau = self.estimate_iat_sokal(S_T, C=C)

            if tau is not None:
                print(f'  τ estimé : {tau:.1f} — critère satisfait après {batch_idx + 1} batch(es)')
                print(f'  τ pris : {tau*thin*10:.1f} — critère satisfait après {batch_idx + 1} batch(es)')
                self.mc.buffer_triangle = mc_iat.buffer_triangle
                return 10 * thin * tau
            else:
                print(f'  Série trop courte, batch supplémentaire nécessaire')

        # fallback si max_batches atteint
        tau_fallback = self.estimate_iat_sokal(S_T, C=1)
        if tau_fallback is None:
            # estimation brute sans fenêtrage
            tau_fallback = len(S_T) / 2
            print(f'Warning : estimation de secours τ = {tau_fallback:.1f}')
        else:
            print(f'Warning : max_batches atteint. Meilleure estimation de τ : {tau_fallback:.1f}')
        self.mc.buffer_triangle = mc_iat.buffer_triangle
        return 10 * tau_fallback
