# This file is part of K-edge-swap.
#
#    K-edge-swap is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    K-edge-swap is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with Foobar. If not, see <https://www.gnu.org/licenses/>. 

import os
import argparse
import numpy as np

from scipy.stats import kstest
from arch.unitroot import DFGLS
from kedgeswap.Graph import Graph
from progressbar import ProgressBar
from kedgeswap.MarkovChain import MarkovChain

# bouger triangle + assortativité dans stats ? 
class Stat():

    def __init__(self, mc, use_dfgls=True, use_ks=False, verbose=False):
        self.use_dfgls = use_dfgls
        self.use_ks = use_ks
        self.mc = mc # markov chain
        self.verbose = verbose

    @staticmethod
    def CheckAutocorrLag1(S_T, alpha):
        T = len(S_T)
        tau = 10 # lag at which the sample autocorr is calculated
        a = np.correlate(S_T, S_T, mode='full')[T] # mode=full: convolution over each point of overlap - take value at T to get lag=1

        mu = -1/T
        sigma_2 = (T**4 - 4 * T**3 + 4 * T - 4) / ((T+1)* T**2 * (T-1)**2)
        A = (a - mu)/np.sqrt(sigma_2)
        z = scipy.stats.norm.ppf(alpha) #TODO Check if alpha or 1-alpha # (1-alpha) th quantile of N(O,1)
        if A > z:
            return 1
        else:
            0

    def estimate_sampling_gap(self, graph, gamma):
        """ Estimate the sampling gap for the MCMC, following algorithm 1 (and using the same values) of 
        Dutta, U. (2022). Sampling random graphs with specified degree sequences 

        """

        #N_swap = 1000 * self.mc.graph.M # burn in 
        N_swap = 10 * self.mc.graph.M # burn in 
        C = 10 # TODO CHECK NUMBER OF CHAINS
        T = 500
        S_T = [] # list of degree assortativity of size T
        u = 1 # lower bound on number of mcmc chains that have significant lag-1 autocorrelation
        mc = [] # list of C MCMC
        alpha = 0.04 # significance level for each test

        if self.verbose:
            print(f'estimation parameters: N_swap {N_swap}, C {C}, T {T}, u {u}, alpha {alpha}')
            print(f'burn in...')
        for c in range(C):
            if self.verbose:
                print(f'MCMC {c}/{C}')
            mc.append(MarkovChain(graph, N_swap, gamma))
            mc[c].run()

        # Measure sampling gap
        if self.verbose:
            print(f'measuring sampling gap...')
        eta = 0
        d_eta = C
        while d_eta > u:
            eta += 0.05 * self.mc.graph.M
            if self.verbose:
                print(f'considering eta {eta}...')

            d_eta = 0
            for c in range(C):
                if self.verbose:
                    print(f'MCMC {c}/{C}')
                n_swap = eta
                pb = ProgressBar()
                for t in pb(range(T)):

                    mc[c].run(n_swap)
                    S_T.append(mc[c].assortativity)
                d_c = CheckAutocorrLag1(S_T, alpha)
                d_eta += d_c

        return eta


    def run_dfgls(self):
        # measure density of graph and use Dutta et al. Fig5 decision tree for sampling gap
        #d = self.mc.graph.M/(self.mc.graph.N * (self.mc.graph.N -1))
        #if self.mc.graph.directed:
        #    d = d/2
        #if d < 0.134:
        #    print('using eta=2m')
        #    eta = 2 * self.mc.graph.M
        #else:
        #    print('estimating eta')
        #    eta = self.estimate_sampling_gap(self.mc.graph, self.mc.gamma)
        eta = self.estimate_sampling_gap(self.mc.graph, self.mc.gamma)

        has_converged = False
        if self.verbose:
            print('running markov chain and checking convergence...')
        while (not has_converged):
            window = self.mc.run(eta)
            test = DFGLS(window)
            if self.verbose:
                print(test.summary)
            if np.abs(test.stat) > np.abs(test.critical_values["1%"]): # TODO check real test ..
                has_converged = True


    def run_kolmogorov_smirnov(self, other):
        eta = self.estimate_sampling_gap(self.mc.graph, self.mc.gamma)

        has_converged = False
        print('testing convergence')
        C = 200 # TODO CHECK NUMBER OF CHAINS
        KS_samples = []
        for c in range(C):
            mc.append(MarkovChain(graph, N_swap, gamma))
            mc[c].run()
            KS_samples.append(mc.assortativity)

        
        test_stat, p_value = kstest(KS_samples, other)
        pass

