.. _benchmark:

Benchmark
=========

- On this page, you will find a benchmark of *kedgeswap* on different datasets with various constraints, 
  to give an idea of what to expect in terms of execution time and a better grasp of how to choose the sampling gap.

Datasets
--------

- For this benchmark, we used the following datasets (we note n the number of nodes and m the number of edges):
  
  * karateclub: undirected simple graph: n=34, m=78, `available here <http://konect.cc/networks/ucidata-zachary/>`_

  * lesmiserables:  undirected simple graph: n=77, m=254, `available here <http://konect.cc/networks/moreno_lesmis/>`_

  * powergrid: undirected simple graph, n=4941, m=6594, `available here <http://konect.cc/networks/opsahl-powergrid/>`_ 

  * airtraffic: directed simple graph: n=1226, m=2615, `available here <http://konect.cc/networks/maayan-faa/>`_

  * adohealth: directed simple graph, n=2539, m=12969, `available here <http://konect.cc/networks/moreno_health/>`_

  * crime: bipartite graph, n=829+551, m=1476, `available here <http://konect.cc/networks/moreno_crime/>`_

Protocol
--------

- We generate samples of 1000 graphs.

- The parameter g is set to 2.

- We follow the convergence using the number of triangles of the graph except for the case of bipartite graphs, where we use the assortativity of the graph.
    
- An algorithm adapted from [1] estimates the sampling gap.

- The datasets are tested with different constraints:

  * Fixed degree sequence : the k-swaps do not affect the degree sequence of the graph. 

  * Fixed joint degree matrix : the k-swaps do not affect the joint degree matrix of the graph. Note that it implies that the degree sequence is also fixed.

  * Fixed degree sequence and number of mutual dyads : the k-swaps do not affect the degree sequence of the graph and the number of reciprocal links of the graph (directed graphs only).



Results
-------

.. list-table:: Title
   :widths: 30 30 30 30 30 30 30
   :header-rows: 1

   * - dataset
     - constraint
     - eta value
     - success rate
     - eta estimation runtime (in seconds)
     - convergence runtime (in seconds)
     - total runtime (in seconds)
   * - karateclub
     - degree sequence
     - 751
     - 10.39%
     - 377
     - 2 
     - 1575
   * - lesmiserables
     - degree sequence
     - 1781
     - 14.26%
     - 1203
     - 5
     - 4955
   * - powergrid
     - degree sequence
     - 16137
     - 40.86%
     - 50995
     - 52
     - 233528
   * - airtraffic
     - degree sequence
     - 6719
     - 38.89%
     - 9063
     - 19
     - 37817 
   * - adohealth
     - degree sequence
     - 32463
     - 39.95%
     - 179200
     - 152
     - 762030
   * - crime
     - degree sequence
     - 3869
     - 38.45%
     - 3026
     - 38
     - 13885
   * - karateclub
     - joint degree matrix
     - 5053
     - 1.54%
     - 2 567
     - 8s
     - 4184
   * - lesmiserables
     - joint degree matrix
     - 24643
     - 1.03%
     - 15987
     - 43
     - 26398
   * - powergrid
     - joint degree matrix
     - 197180
     - 1.54%
     - 1644229
     - 6023
     - 2001551
   * - airtraffic
     - degree sequence + dyads
     - 6707
     - 38.96%
     - 8922
     - 17
     - 37876 
   * - adohealth
     - degree sequence + dyads
     - 32449
     - 39.97%
     - 191847
     - 1006
     - 800532



References
----------

[1] Dutta, U., Fosdick, B.K., & Clauset, A. (2021). Sampling random graphs with specified degree sequences. arXiv preprint arXiv:2105.12120.
