# This file is part of K-edge-swap.
#
#    K-edge-swap is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    K-edge-swap is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with Foobar. If not, see <https://www.gnu.org/licenses/>. 

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

# bouger triangle + assortativité dans stats ? 
class Stat():

    def __init__(self, mc, use_dfgls=True, eta=None, verbose=False):
        #self.use_dfgls = use_dfgls
        #self.use_ks = use_ks
        self.mc = mc # markov chain
        self.eta = eta
        self.verbose = verbose

    @staticmethod
    def CheckAutocorrLag1(S_T, alpha):
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
        z = scipy.stats.norm.ppf(1-alpha) #TODO Check if alpha or 1-alpha # (1-alpha) th quantile of N(O,1)
        if A > z:
            return 1
        else:
            return 0

    def estimate_sampling_gap(self, graph, gamma):
        """ Estimate the sampling gap for the MCMC, following algorithm 1 (and using the same values) of 
        Dutta, U. (2022). Sampling random graphs with specified degree sequences 

        """
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
        C = 10 # TODO CHECK NUMBER OF CHAINS
        T = 500
        #S_T = [] # list of degree assortativity of size T
        u = 1 # lower bound on number of mcmc chains that have significant lag-1 autocorrelation
        mc = [] # list of C MCMC
        alpha = 0.04 # significance level for each test

        if self.verbose:
            print(f'estimation parameters: N_swap {N_swap}, C {C}, T {T}, u {u}, alpha {alpha}')
            print(f'burn in...')
        #for c in range(C):
        #    if self.verbose:
        #        print(f'MCMC {c}/{C}')
        #    mc.append(MarkovChain(graph, N_swap, gamma))
        #    mc[c].run()
        burn_in = MarkovChain(graph, N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles, use_assortativity=self.mc.use_assortativity, verbose=self.mc.verbose, keep_record=False, log_dir=None)
        burn_in.run()

        # Measure sampling gap
        if self.verbose:
            print(f'measuring sampling gap...')
        # Start with eta = 10 * M, then dichotomic search if successful, otherwise * 2
        eta = 10 * self.mc.graph.M
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
                    mc.append(MarkovChain(burn_in.graph.copy(), N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles, use_assortativity=self.mc.use_assortativity, verbose=self.mc.verbose, keep_record=False, log_dir=None))
                else:
                    mc[c] = MarkovChain(burn_in.graph.copy(), N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles, use_assortativity=self.mc.use_assortativity, verbose=self.mc.verbose, keep_record=False, log_dir=None)


                #mc[c].run()

            S_Ts = Parallel(n_jobs=5)(delayed(run_chain)(c) for c in range(C))
            for c in range(C):
                d_c = self.CheckAutocorrLag1(S_Ts[c], alpha)
                d_eta += d_c
                if self.verbose:
                    print(f'for eta={eta}: d_eta={d_eta}, u={u}')
            if d_eta <= u:
                prev_eta = eta
                #eta = eta/2
                tuned = True
            elif d_eta > u and prev_d_eta <= u:

                tuned = True
                eta = prev_eta
            elif d_eta > u and prev_d_eta > u:
                prev_eta = eta
                eta = 2 * eta

        return eta


    def run_dfgls(self, output):

        if self.eta is None:
            t0 = time.time()
            eta = self.estimate_sampling_gap(self.mc.graph, self.mc.gamma)
            self.eta = eta
            t1 = time.time()
            print(f'eta estimation {t1 - t0} seconds')
        else:
            eta = self.eta

        has_converged = False
        if self.verbose:
            print('running markov chain and checking convergence...')
        t0 = time.time()
        while (not has_converged):
            window = self.mc.run(int(np.round(eta)))
            test = DFGLS(window)

            try:
                if self.verbose:
                    print(f'test statistic : {test.stat},\n Markov chain is stationnary if test statistic < {test.critical_values["1%"]}')
                    #print(test.summary)

                if test.stat < test.critical_values["1%"]:
                    has_converged = True
                    self.mc.graph.to_ssv(output)
            except:
                print("Warning, dfgls doesn't have enough unique observations to compute.")
                continue

        t1 = time.time()
        print(f'convergence {t1 - t0} seconds')

    #def run_kolmogorov_smirnov(self, other):
    #    eta = self.estimate_sampling_gap(self.mc.graph, self.mc.gamma)
    #    has_converged = False
    #    print('testing convergence')
    #    C = 200 # TODO CHECK NUMBER OF CHAINS
    #    KS_samples = []
    #    for c in range(C):
    #        mc.append(MarkovChain(graph, N_swap, gamma, use_jd=self.mc.use_jd, use_triangles=self.mc.use_triangles, use_assortativity=self.mc.use_assortativity, verbose=self.mc.verbose))
    #        mc[c].run()
    #        KS_samples.append(mc.assortativity)

    #    
    #    test_stat, p_value = kstest(KS_samples, other)
    #    pass

