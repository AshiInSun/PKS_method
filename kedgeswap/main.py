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

from arch.unitroot import DFGLS
from kedgeswap.Stat import Stat
from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain


def run(dataset, directed, gamma, use_jd, use_triangles, use_dfgls, use_ks, eta, output, verbose):

    # read graph
    graph = Graph(directed)
    graph.read_ssv(dataset)

    # initialize MCMC
    mc = MarkovChain(graph, N_swap=0, gamma=gamma, use_jd=use_jd, use_triangles=use_triangles, verbose=verbose)

    # initialize metrics
    stat = Stat(mc, use_dfgls, use_ks, eta, verbose)

    # start run
    stat.run_dfgls(output)
    ## start run
    ## estimate sampling gap
    #print('estimating sampling gap...')
    #eta = stat.estimate_sampling_gap(mc.graph, mc.gamma)

    #if verbose:
    #    print(f'sampling gap is {eta}')

    ## run markov chain and follow convergence
    #print(f'running Markov Chain...')
    #has_converged = False
    #while (not has_converged):

    #    # run eta swaps and populate degree assortativity window
    #    window = mc.run(eta)

    #    # test convergence on degree assortativity window

    #    test = DFGLS(window)
    #    if verbose:
    #        # write summary of statistics test
    #        print(test.summary)

    #    if np.abs(test.stat) > np.abs(test.critical_values["1%"]):
    #        has_converged = True
    #        mc.graph.to_ssv(output)


def main():
    #  parse arguments
    parser = argparse.ArgumentParser(description='k edge swap')
    parser.add_argument('-f', '--dataset', type=str, 
            help='path to the dataset')

    parser.add_argument('-o', '--output', type=str, default=None, 
            help='path to the output')

    parser.add_argument('-n', '--N_swap', type=int, default=1000000,
            help='number of swap')

    parser.add_argument('-g', '--gamma', type=int, default=2,
	    help='exponent of zipf law, for pick K value')

    parser.add_argument('-d', '--directed', action='store_true', default=False,
            help='enable if input graph is directed')

    parser.add_argument('-e', '--eta', type=float, default=None,
            help='value of eta. If not specified, will run estimation.')

    parser.add_argument('-jd', '--jointdegree', action='store_true', default=False,
            help='enable to use the joint degree matrix as a measure to accept or refuse a swap')

    parser.add_argument('-t', '--triangles', action='store_true', default=False,
            help='enable to search the triangles in the graph at each step of the markov chain')

    parser.add_argument('-dfgls', '--dfgls', action='store_true', default=True,
            help='estimate convergence of the markov chain using the Dickey-Fuller Generalised Least Square method on the degree assortativity')

    parser.add_argument('-ks', '--kolmogorovsmirnov', action='store_true', default=False,
            help='compare degree assortativity distribution to another generation method.') # TODO to define...

    parser.add_argument('-v', '--verbose', action='store_true', default=False,
            help='increase verbosity')

    args = parser.parse_args()

    run(args.dataset, args.directed, args.gamma, args.jointdegree, args.triangles, args.dfgls, args.kolmogorovsmirnov, args.eta, args.output, args.verbose)

if __name__ == "__main__":
    main()
