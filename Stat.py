import os
import numpy as np
import argparse

from Graph import Graph
from arch.unitroot import DFGLS
from MarkovChain import MarkovChain
from scipy.stats import kstest

# bouger triangle + assortativité dans stats ? 
class Stat():

    def __init__(self, mc):
        self.use_dfgls = True
        self.use_ks = False
        self.mc = mc # markov chain

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

        N_swap = 1000 * self.mc.graph.M # burn in 
        C = 10 # TODO CHECK NUMBER OF CHAINS
        T = 500
        S_T = [] # list of degree assortativity of size T
        u = 1 # lower bound on number of mcmc chains that have significant lag-1 autocorrelation
        mc = [] # list of C MCMC
        alpha = 0.04 # significance level for each test
        print('burn in')
        for c in range(C):
            mc.append(MarkovChain(graph, N_swap, gamma))
            mc[c].run()

        # Measure sampling gap
        eta = 0
        d_eta = C
        print('estimating eta')
        while d_eta > u:
            eta += 0.05 * self.mc.graph.M
            print(f'considering eta {eta}')
            d_eta = 0
            for c in range(C):
                print(f'running {c}th MC')
                n_swap = eta
                for t in range(T):
                    mc[c].run(n_swap)
                    S_T.append(mc[c].assortativity)
                d_c = CheckAutocorrLag1(S_T, alpha)
                d_eta += d_c

        print(f'eta is {eta}')
        return eta


    def run_dfgls(self):
        # measure density of graph and use Dutta et al. Fig5 decision tree for sampling gap
        print('measuring density')
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
        print('testing convergence')
        while (not has_converged):
            window = self.mc.run(eta)
            test = DFGLS(window)
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

def main():
    parser = argparse.ArgumentParser(description='k edge swap')
    parser.add_argument('-f', '--dataset', type=str, default="./gp_references.txt",
            help='path to the dataset')
    parser.add_argument('-o', '--output', type=str, default="./gp_references.out",
            help='path to the output')
    parser.add_argument('-n', '--N_swap', type=int, default=1000000,
            help='number of swap')
    parser.add_argument('-g', '--gamma', type=int, default=2,
	    help='exponent of zipf law, for pick K value')
    parser.add_argument('-d', '--directed', action='store_true', default=False,
            help='enable if input graph is directed')
    parser.add_argument('--check', action='store_true', default=False,
            help='enable to make some unit test during run. Default to false, significantly slows run.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
            help='increase verbosity')
    parser.add_argument('--debug', action='store_true', default=False,
            help='enable debugging, user assertions to check that all is working')

    args = parser.parse_args()

    #file_in = "./gp_references.txt"

    mygraph = Graph(args.directed)
    print('reading graph')
    mygraph.read_ssv(args.dataset)
    print('init markov chain')
    mc = MarkovChain(mygraph, args.N_swap, args.gamma, args.debug)
    #mc.run()
    print('init Stat')
    stat = Stat(mc)
    print('run MCMC')
    stat.run_dfgls()
    #mc.graph.to_ael(args.output)


if __name__ == "__main__":
    main()

