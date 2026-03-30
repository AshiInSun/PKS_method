# This file is part of K-edge-swap.
#
#    K-edge-swap is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    K-edge-swap is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with K-edge-swap. If not, see <https://www.gnu.org/licenses/>. 

import os
import sys
import argparse
import numpy as np

from progressbar import ProgressBar
from arch.unitroot import DFGLS
from kedgeswap.Stat import Stat
from kedgeswap.Graph import Graph
from kedgeswap.MarkovChain import MarkovChain


def run(dataset, directed, gamma, use_jd, use_fixed_triangle, use_triangles, use_assortativity, mutualdiades, turbo, eta, output, verbose, keep_record, log_dir, output_number, debug, njobs, use_fixed_threechains, read_gml, use_fixed_triangle_range):

    # read graph
    print('Reading graph...')
    graph = Graph(directed)
    if read_gml:
        graph.read_gml(dataset)
    else:
        graph.read_ssv(dataset)

    # initialize MCMC
    print('Initializing markov chain')
    mc = MarkovChain(graph, N_swap=0, gamma=gamma, use_jd=use_jd, 
            use_fixed_triangle=use_fixed_triangle, use_triangles=use_triangles, use_assortativity=use_assortativity, use_mutualdiades=mutualdiades,
            verbose=verbose,
            keep_record=keep_record, log_dir=log_dir, debug=debug, use_fixed_threechains=use_fixed_threechains, use_fixed_triangle_range=use_fixed_triangle_range)

    # initialize metrics
    stat = Stat(mc, eta, turbo, verbose, njobs)

    # start run
    print('Starting Markov Chain convergence...')
    stat.run_dfgls(output)

    # when fully converged, run and save outputs
    print(f'Writing {output_number} graph samples...')
    pb = ProgressBar()
    for j in pb(range(output_number)):
        output_name = output + f'_{j}'
        stat.mc.run(int(np.round(stat.eta)))
        stat.mc.graph.to_ssv(output_name)


def main():
    #  parse arguments
    parser = argparse.ArgumentParser(description='k edge swap')

    # input output arguments
    parser.add_argument('-f', '--dataset', type=str, 
            help='path to the dataset')

    parser.add_argument('-gml', '--read_gml', action='store_true', default=False,
                        help='needed to read gml files.')

    parser.add_argument('-o', '--output', type=str, default=None, 
            help='path to the file output, will write sampled graph using this name.')

    # Markov Chain parameters
    parser.add_argument('-g', '--gamma', type=int, default=2,
	    help='exponent of zipf law, for pick K value')

    parser.add_argument('-d', '--directed', action='store_true', default=False,
            help='enable if input graph is directed or bipartite')

    parser.add_argument('-e', '--eta', type=float, default=None,
            help='value of eta. If not specified, will run estimation.')

    parser.add_argument('-jd', '--jointdegree', action='store_true', default=False,
            help='enable to use the joint degree matrix as a measure to accept or refuse a swap')

    parser.add_argument('-md', '--mutualdiades', action='store_true', default=False,
            help='enable to check if number of mutual diades (aka reciprocal links) stays constant to accept or refuse a swap. Only use with directed graphs.')

    parser.add_argument('-ft', '--fixed_triangle', action='store_true', default=False,
            help='enable to keep the number of triangles fixed during swaps')

    parser.add_argument('-ftr', '--fixed_triangle_range', type=int, default=0,
                        help='enable to keep the number of triangles fixed between a range during swaps')

    parser.add_argument('-f3c', '--fixed_three_chains', action='store_true', default=False,
                        help='enable to keep the number of 3 chains during swaps')
    parser.add_argument('--output_number', type=int, default=1000,
            help='set the number of graph to generate after Markov Chain convergence.'
            ' Default to 1000')

    parser.add_argument('--turbo', action='store_true', default=False,
            help='Optionnal, relevant only when running eta estimation.'
            'This method (over)estimates empirically a sampling ')

   
    # assortativity and triangles cannot be selected together
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--assortativity', action='store_true', default=False,
            help='enable to estimate the convergence using the assortativity. -a and -t are mutually exclusive.'
            'When no method is selected, this one is chosen by default. Warning: does not work with --jd')

    group.add_argument('-t', '--triangles', action='store_true', default=False,
            help='enable to count the triangles in the graph at each step of the markov chain.'
            'Use this count to estimate the convergence of the Markov Chain.'
            '-a and -t are mutually excluseive. If --jd is chosen, use -t.')

    # logging parameters
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
            help='increase verbosity')

    parser.add_argument('--debug', action='store_true', default=False,
            help='enable debug options (slows down process because it checks a lot of things)')

    parser.add_argument('--keep_record', action='store_true', default=False,
            help='save all the intermidiate graphs and the swaps')
    parser.add_argument('--log_dir', default=None,
            help='When keep_record enabled, can save all logs in a directory specified by log_dir.')
    parser.add_argument('--njobs', default=5, type=int,
            help='Parallelisation : Number of CPU to use during eta estimation step. By default <= 5, can be set to 1 if no parallelisation is wanted.')


    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    # some sanity checks
    ## check coherence of parameters
    if (args.assortativity and args.jointdegree):
        print("Error: assortivity is constant when using fixed joint degree constraint. Use -t to follow convergence. Exiting...")
        sys.exit()

    if (args.mutualdiades and not args.directed):
        print("Error: can't follow number of mutual diades when graph is not directed (reciprocal links can only exist in directed graphs)")
        sys.exit()

    if (not args.assortativity) and (not args.triangles):
        print('Error: no value selected to estimate convergence. Please select -a for assortativity, or -t for the number of triangles.\n We recommend -a for the fixed degree sequence condition, and -t for the fixed joint degree matrix condition')
        sys.exit()

    if (args.triangles and args.fixed_triangle):
        print("Error: cannot use triangle count for convergence when triangles are fixed as a constraint. Use -a for assortativity instead. Exiting...")
        sys.exit()


    run(args.dataset, args.directed, args.gamma, args.jointdegree, args.fixed_triangle, args.triangles,
            args.assortativity, args.mutualdiades, args.turbo,
            args.eta, args.output, args.verbose, args.keep_record, args.log_dir,
            args.output_number, args.debug, args.njobs, args.fixed_three_chains, args.read_gml, args.fixed_triangle_range)


if __name__ == "__main__":
    main()
