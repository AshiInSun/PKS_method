.. _usage:

Usage
=====

- The **kedgeswap** package provides a program to generate random simple graphs uniformly with a given set of target constraints:
	
	* undirected graphs with a fixed degree sequence

	* directed graphs with a fixed degree sequence

	* bipartite graphs with a fixed degree sequence

	* directed graphs with a fixed degree sequence and a fixed number of mutual dyads

	* undirected graphs with a fixed joint degree matrix

Input Format
------------

- The program takes as input a simple graph described as an edge list (one line corresponds to an edge, two nodes are seperated by a space or tabulation):

   | 1 2
   | 3 5
   | 6 5
   | .
   | .
   | .

.. note::
   This package does not handle loops and multiple edges.
   If the input graph contains either, they will be automatically removed when the graph is read.

Output
------

- The program generates a sample of graphs selected uniformly at random from the set of graphs with the same target constraints as the input graph.

Target Constraints
------------------

- The program generates uniformly at random **simple** graphs (no loops, no multiedges).

- Several target constraints are available:

    * fixed degree sequence (default): Can be applied on several "flavours" of simple graphs: undirected, directed, bipartite. The model convergence can be evaluated either by following the assortativity (-a option) or the number of triangles (-t option).

    * fixed joint degree matrix: Can be aplied to undirected, directed and bipartite graphs. The model convergence can only be evaluated by following the number of triangles (-t), as the assortativity is constant.

    * fixed number of mutual dyads: Can only be applied to directed graphs. A mutual dyad occurs when the graph contain links in two directions between two nodes, this constraint fixes the total number of mutual dyads in the graph. The model convergence can be evaluated either by following the assortativity (-a option) or the number of triangles (-t option).

.. note::
    A user can add to the code additional constraints by adding them to the
    MarkovChain class. The constraints should be added in the 
    **check_swap** method, used to verify if an edge swap is valid or not.
    An argument to select this constraint can then be added to the list 
    of arguments in the main.py file.

Command Line Interface
----------------------

- Usage example, in the root folder of the package: 

    python kedgeswap/main.py -f ./data/ucidata-zachary/out.ucidata-zachary -o ./karateclub.out


- list of main.py parameters:

  - Required arguments: 

    * -f <path> : path to the input file.

    * -o <path> : path to the output files. Will write *N* output graphs with this prefix as filename, where *N* is fixed by the *\-\-output_number* parameter (see Optional arguments).

    * -d : enable if the input graph is directed or bipartite.

    * -a : enable to follow the convergence of the Markov chain using the assortativity of the graph. Warning, option is not compatible with *-t* or *-jd*.

    * -t : enable to follow the convergence of the Markov chain using the number of triangles in the graph. Warning, option is not compatible with *-a*. 

    * -jd : (target constraint argument) enable to generate sample of graphs with a fixed joint degree matrix. Warning: only works with *-t* option to follow convergence (assortativity is constant when joint degree matrix is fixed).

    * -md : (target constraint argument) enable to generate sample of graphs with a fixed number of mutual dyads. Warning: only works on directed graphs (*-d* option).

  - Optional arguments:

    * -v : enable to be more verbose. Adds the Markov Chain status to the logs, number of accepted/rejected swaps, DFGLS output to follow convergence.

    * -g <positive integer>: exponent of the probability law used to pick the number of edges to swap.

    * -e <positive integer>: sampling gap between each generated graph. If not specified, will use a (slow) estimation method.

    * \-\-output_number <positive integer>: number *N* of uncorrelated graphs to generate once the Markov Chain has reached its convergence. Default to 1000.

    * \-\-debug : makes some additional checks, like checking that the degree sequences hasn't changed after each swap. Slows down everything, only used for debuggin purposes.

    * \-\-keep_record : enable to store every step (as gzip file) of the Markov chain, as well as every permutation (warning: produces a very large number of files, mostly useful for debug purposes) 

    * \-\-log_dir : only useful if keep_record is enabled. Specify a path to store each step of the Markov Chain



