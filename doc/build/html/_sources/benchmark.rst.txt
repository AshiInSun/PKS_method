.. _benchmark:

Benchmark
=========

- On this page you'll find a benchmark of *kedgeswap* on different datasets and with different constraints, 
  to give you an idea of what to expect in term of execution time, and to give a better grasp of how to 
  choose the sampling gap.

Datasets
--------

- For this benchmark we used the following datasets (we note n the number of nodes and m the number of edges) #TODO choose with Lionel ?:
  
  * powergrid: undirected simple graph, n=4 941,  m=6 594, `available here <http://konect.cc/networks/opsahl-powergrid/>`_ 

  * karateclub: undirected simple graph: n=34, m=78, `available here <http://konect.cc/networks/ucidata-zachary/>`_

  * health: directed simple graph, n=2539, m=12969, `available here <http://konect.cc/networks/moreno_health/>`_

  * wordnet: undirected simple graph: n=146005, m=656999, `available here <http://konect.cc/networks/wordnet-words/>`_

  * maayan: directed simple graph: n=1226, m=2615, `available here <http://konect.cc/networks/maayan-faa/>`_

  * ...?

Protocol
--------

- The datasets are tested in differents setups:

  * With or without sampling gap estimation: The sampling gap is the number of steps of the Markov chain required to produce uncorrelated samples.
    An algorithm adapted from [1] estimates the sampling gap, but is very slow, especially for large networks, as the first step (the "burn in" step)
    runs 1000*m steps of the Markov Chain to ensure its convergence. #TODO ? When not possible to run the estimation, it is possible to (over)estimate it
    empirically by ... ? (taking coeff inversely proportional to acceptation rate ?)

  * Fixed degree sequence : the first constraint we can put on the swap is to accept swap only if they conserve the degree sequence. We can follow the convergence
    either by following the degree assortativity of the graph, or the number of triangles of the graph.

  * Fixed joint degree matrix : another more constraining condition is to accept an edge swap only if the conserve the joint degree matrix. We can follow the convergence
    using the number of triangles of the graph (when the joint degree matrix is fixed, the degree assortativity is also constant).

Results
-------

.. list-table:: Title
   :widths: 30 30 30 30 30 30 30 30 30
   :header-rows: 1

   * - dataset
     - directed
     - constraint
     - using eta estimation
     - eta value
     - acceptation rate
     - eta estimation runtime (in seconds)
     - convergence runtime (in seconds)
     - total runtime (hh:mm:ss)
   * - powergrid
     - no
     - fixed degree sequence
     - yes
     - 8064
     - 40.88%
     - 65 285s
     - 73.86s
     - 22:16:45
   * - karateclub
     - no
     - fixed degree sequence
     - yes
     - 751
     - 10.38%
     - 392.90s
     - 6.71s 
     - 00:10:47
   * - health
     - yes
     - fixed degree sequence
     - yes
     - 32 457
     - 39.48%
     - 174 238s
     - 1 754s
     - 72:02:44
   * - maayan
     - yes
     - fixed degree sequence
     - yes
     - 6730
     - 38.82%
     - 8804.56s
     - 57.13s
     - 3:39:25
   * - karateclub
     - no
     - fixed joint degree matrix
     - yes
     - 5053
     - 1.54%
     - 2 567s
     - 8.32s
     - 1:09:44
   * - powergrid
     - no
     - fixed joint degree matrix
     - yes
     - 197 180
     - 1.54%
     - 1 644 229s
     - 1 399.76s
     - ?
   * - maayan
     - yes
     - fixed joint degree matrix
     - yes
     - 163494
     - 3.2%
     - 516 290s
     - 427.52s
     - ?



References
----------

[1] Dutta, U., & Clauset, A. (2021). Convergence criteria for sampling random graphs with specified degree sequences. arXiv preprint arXiv:2105.12120.
