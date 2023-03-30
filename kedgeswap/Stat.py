# This file is part of K-edge-swap.
#
#    K-edge-swap is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    K-edge-swap is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with K-edge-swap. If not, see <https://www.gnu.org/licenses/>. 

import os
import time
import scipy
import argparse
import numpy as np

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
    def __init__(self, mc, eta=None, turbo=False, verbose=False):
        #self.use_ks = use_ks
        self.mc = mc # markov chain
        self.eta = eta
        self.turbo = turbo
        self.verbose = verbose

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
            return 1
        else:
            return 0

    def guesstimate_sampling_gap(self, graph, gamma):
        """
            Sampling gap estimation is long, this function gives an empirical estimation of the sampling gap.
            Measure the acceptation rate A of the Markov Chain, and fix the sampling gap as 10*(1/A) * M, 
            where M is the number of edges of the network. This estimation was fixed empirically to overestimate
            the sampling gap we measure using the estimation from Dutta, U. (2022).
        """
        # run a short burn in
        N_swap = 5 * self.mc.graph.M # burn in 
        burn_in = MarkovChain(graph, N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles, 
                              use_assortativity=self.mc.use_assortativity, 
                              verbose=self.mc.verbose, keep_record=False, log_dir=None)
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
                else:
                    S_T.append(len(mc[c].triangles2edges))
            return S_T

        N_swap = 1000 * self.mc.graph.M # burn in 
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
        burn_in = MarkovChain(graph, N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles,
                              use_assortativity=self.mc.use_assortativity,
                              verbose=self.mc.verbose, keep_record=False, log_dir=None)
        burn_in.run()

        # estimate the acceptation rate of the markov chain
        burn_in_rate = burn_in.accept_rate / (burn_in.accept_rate + burn_in.refusal_rate)

        if self.verbose:
            print('acceptation/refusals by k')
            print(burn_in.accept_rate_byk)
            print(burn_in.refusal_rate_byk)

        # Measure sampling gap
        if self.verbose:
            print(f'measuring sampling gap...')

        # first eta is estimated from the accept/refuse rate of the burn in
        # then dichotomic search to get better eta
        #eta = 10 * self.mc.graph.M
        eta = 1/burn_in_rate * self.mc.graph.M
        d_eta = C
        prev_d_eta = C
        prev_eta = eta
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
                    mc.append(MarkovChain(burn_in.graph.copy(), N_swap, gamma, use_jd=self.mc.use_jd,
                            use_triangles=self.mc.use_triangles, use_assortativity=self.mc.use_assortativity,
                            verbose=self.mc.verbose, keep_record=False, log_dir=None))
                else:
                    mc[c] = MarkovChain(burn_in.graph.copy(), N_swap, gamma, use_jd=self.mc.use_jd,
                                use_triangles=self.mc.use_triangles, use_assortativity=self.mc.use_assortativity,
                                verbose=self.mc.verbose, keep_record=False, log_dir=None)


                #mc[c].run()

            S_Ts = Parallel(n_jobs=5)(delayed(run_chain)(c) for c in range(C))
            for c in range(C):
                d_c = self.CheckAutocorrLag1(S_Ts[c], alpha)
                d_eta += d_c
                #if self.verbose:
                #    print(f'for eta={eta}: d_eta={d_eta}, u={u}')

            # check if eta value is accepted - if a most u chains show no correlation 
            # on the S_T timeserie with lag 1, the value of eta is considered valid.
            if d_eta <= u:
                if self.verbose:
                    print('eta {eta} accepted (d_eta={d_eta} <= u={u})')
                prev_eta = eta
                prev_d_eta = d_eta
                if prev_eta == eta/2:
                    # don't check eta/2 again
                    tuned = True
                else:
                    print('trying eta=eta/2...')
                    eta = eta/2
                #tuned = True
            elif d_eta > u and prev_d_eta <= u:
                prev_d_eta = d_eta
                tuned = True
                if self.verbose:
                    print('eta {eta} refused (d_eta={d_eta} <= u={u}), using eta={prev_eta}.')
                eta = prev_eta

            elif d_eta > u and prev_d_eta > u:
                prev_d_eta = d_eta
                prev_eta = eta
                eta = 2 * eta
                if self.verbose:
                    print('eta {prev_eta} refused (d_eta={d_eta} <= u={u}), trying eta={eta}.')

        return eta


    def run_dfgls(self, output):
        """
            If no sampling gap eta specified, run estimation of eta.
            Run Markov Chain for eta steps, retrieve list of assortativity values (or number of triangles)
            and estimate the convergence of this time serie, to decide if the Markov Chain is
            converged.
        """

        # Get sampling gap value
        if self.eta is None:
            t0 = time.time()
            if self.turbo:
                # turbo estimation
                eta = self.guesstimate_sampling_gap(self.mc.graph, self.mc.gamma)
            else:
                # dichotomic estimation
                eta = self.estimate_sampling_gap(self.mc.graph, self.mc.gamma)
            self.eta = eta
            t1 = time.time()
            eta_time = t1 - t0
            #print(f'eta estimation {t1 - t0} seconds')
        else:
            # use eta given in input
            eta = self.eta

        # Run the markov chain, and check its convergence using the DFGLS test
        has_converged = False
        if self.verbose:
            print('running markov chain and checking convergence...')
        t0 = time.time()

        while (not has_converged):
            window = self.mc.run(int(np.round(eta)))
            test = DFGLS(window)

            try: 
                # in some very rare cases, usually when very few swaps are accepted, the DFGLS
                # doesn't have enough different values to run, so it raises an error. Catch that error and
                # run the markov chain some more.
                if self.verbose:
                    print(f'test statistic : {test.stat},\n Markov chain is stationnary if test statistic < {test.critical_values["1%"]}')
                    #print(test.summary)

                if test.stat < test.critical_values["1%"]:
                    has_converged = True
                    self.mc.graph.to_ssv(output)
            except:
                print("Warning, dfgls doesn't have enough unique observations to compute.")
                continue

        # some verbose output
        if self.verbose:
            print('acceptation by k')
            for k in self.mc.accept_rate_byk:
                print(f'({k}: {self.mc.accept_rate_byk[k]})', end=', ')

            print('\nrefusal by k')
            for k in self.mc.refusal_rate_byk:
                print(f'({k}: {self.mc.refusal_rate_byk[k]})', end=', ')
            print('')
        t1 = time.time()
        conv_time = t1 - t0
        print(f'eta estimation took {eta_time} seconds')
        print(f'convergence took {conv_time} seconds')

