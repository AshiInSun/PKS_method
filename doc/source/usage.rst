.. _usage:

Usage
=====

- The **kedgeswap** package builds tools to generate random graphs picked uniformly given certain 
  constraints (simple graph with fixed degree sequence, directed simple graph with fixed degree sequence, simple graph with fixed joint degree matrix ...).

Input Format
------------

- This package takes as input a simple graph as an edge list (one line corresponds to an edge, two nodes are seperated by a space or tabulation):

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

- This package generates graphs picked uniformely randomly from the set of graphs with the same degree sequence as the input graph. You can put additional constraints on the set.

Constraints
-----------

- This package generates uniformly randomly picked **simple** graphs **without loops**.

- Several constraints can be used to generate the graphs:

    * fixed degree sequence: the first constraint (defined by default). Can be applied on several "flavours" of simple graphs: undirected, directed, biparatite. The model convergence can be evaluated either by following the assortativity (-a option) or the number of triangles (-t option).

    * fixed joint degree matrix: a more complex constraint. Can also be aplied to undirected, directed and bipartite graphs. The model convergence can only be evaluated by following the number of triangles (-t), as the assortativity will remain constant.

    * fixed number of dyads: can only be applied to directed graphs. A mutual dyad occurs when the graph contain links in two directions between two nodes, this constraint fixes the total number of mutual dyads in the graph.

.. note::
    Additional constraints can be defined by adding them to the
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

    * -f : path to the edge list input file.

    * -o : path to the output files. Will write *N* output graphs with this prefix as filename, where *N* is fixed by the *--output_number* parameter (see Optional arguments, defaults to 1000).

    * -d : enable if the input graph is directed or bipartite.


  - Constraint definition:

    * -jd : enable if you want to generate samples with a fixed joint degree matrix. Warning: only works with *-t* option to follow convergence (assortativity is constant when joint degree matrix is fixed).

    * -md : enable to generate samples with a fixed number of mutual dyads. Warning: only works on directed graphs (*-d*).

    * -t : enable to follow the convergence of the Markov chain using the number of triangles in the graph. Warning, option is not compatible with *-a*.

    * -a : enable to follow the convergence of the Markov chain using the assortativity of the graph. Warning, option is not compatible with *-t* or *-jd*.

  - Optional arguments:

    * -v : optional: enable to be more verbose. Adds the Markov Chains status to the logs, number of accepted/rejected swaps, DFGLS output to follow convergence...

    * -g : exponent of the 1/(n^g) law used to pick the number of edges to swap.

    * -e : sampling gap between each generated graph. If not specified, will use a (very slow) estimation method.

    * --output_number: number *N* of uncorrelated graphs to generate once the Markov Chain has reached its convergence. Default to 1000.

    * --debug: makes some additional checks, like checking that the degree sequences hasn't changed after each swap. Slows down everything, only used for debuggin purposes.

    * --keep_record : optional: enable to store every step (as gzip file) of the Markov chain, as well as every permutation (warning: produces a very large number of files, mostly useful for debug purposes) 

    * --log_dir : optional: only useful if keep_record is enabled. Specify a path to store each step of the Markov Chain



