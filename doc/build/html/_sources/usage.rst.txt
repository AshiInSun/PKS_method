.. _usage:

Usage
=====

- The *kedgeswap* package builds tools to generate random graphs picked uniformly given certain 
  constraints (simple graph with fixed degree sequence, directed simple graph with fixed degree sequence, simple graph with fixed joint degree matrix ...).

Input Format
------------

- This package takes as input a simple graph as a space separated edge list: 

   1 2
   3 5
   6 5
   .
   .
   .

.. note::
   This package does not handle loops and multiple edges.
   If the input graph contains either, they will be automatically removed when the graph is read.

Command Line Interface
----------------------

- usage example: 
    python main.py -f ./data/ucidata-zachary/out.ucidata-zachary -o ./karateclub.out
    

- list of main.py parameters:
    * -f : path to the edge list input file.

    * -o : path to the output files. Will write N output graphs with this prefix as filename.

    * -n : optional: number of requested swaps.

    * -g : exponent of the 1/(n^g) law used to pick the number of edges to swap.

    * -d : enable if the input graph is directed.

    * -e : optional: sampling gap between each generated graph. If not specified, will use a (very slow) estimation method.

    * -jd : enable if you want to generate samples with a fixed joint degree matrix. Warning: only works with "-t" option to follow convergence (assortativity is constant when joint degree matrix is fixed).

    * -t : enable to follow the convergence of the Markov chain using the number of triangles in the graph. Warning, option is not compatible with "-a".

    * -a : enable to follow the convergence of the Markov chain using the assortativity of the graph. Warning, option is not compatible with "-t" or "-jd".

    * -v : optional: enable to be more verbose.

    * --keep_record : optional: enable to store every step (as gzip file) of the Markov chain, as well as every permutation (warning: produces a very large number of files, mostly useful for debug purposes) 

    * --log_dir : optional: only useful if keep_record is enabled. Specify a path to store each step of the Markov Chain


