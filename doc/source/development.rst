.. _development:

Development guide
=================

- The aim of this guide is to give a quick understanding of the package's structure. If you want to modify or add content to the package, this page should help you !

Package Structure
-----------------

- This package is made of three classes that interact with each other:

  * Graph: The Graph object reads the input graph and store it in a data structure described below. The graph is *simple*, *without loops*, can be *undirected* or *directed*, and can be *bipartite*. To add new input format, or to modify the data structure, this is the class to check.

  * MarkovChain: The MarkovChain object selects the edges to swap, check the constraints, performs the swaps and measures some metrics on the graph (e.g. the assortativity value, the number of triangles etc..). To add new constraints on the MarkovChain (e.g. fixed number of triangles) or to measure other values (number of a certain pattern), this is the class to check.

  * Stat: The Stat object estimates the sampling gap of the Markov Chain, and check if the Markov Chain has converged. To adapt the sampling gap estimation, or to implement other methods to check for the Markov Chain convergence, this is the class to check.

- You will find below some insights on the implementations of each class.

Graph
-----

- The Graph object stores a *simple* graph. The data structure used for the graph is, 

  - for undirected, directed and bipartite graphs:

      * M and N: int
                   respectively store the number of edges and the number of nodes of the graph. Both remain constant during the swapping process.

      * neighbors: dict(list)
                   Stores the adjacency list for each node of the graph. Given that the structure is a dict (hash map), getting the adjacency list of a node is in O(1), amortized time.
                   *neighbors* is used to store the neighbors of each node, and is updated at each swap.

      * unique_edges: list
                   Stores one exemplar of each edge of the graph. *unique_edges* is used to uniformly pick random edges of the graph, and is updated at each swap.
      
      * directed: bool
                   Indicates if the graph is directed or not.  
               
               
  - for undirected graphs:

      * edges: dict(int)
                   For each edge **(u,v)**, it stores the position of **v** in the adjacency list of **u**. 
                   E.g. 
                   ..code-block:: python

                        v_idx = edges[(u,v)]
                        u_idx = edges[(v,u)]
                        neighbors[u][v_idx] == v # True
                        neighbors[v][u_idx] == u # True


  - for directed graphs:

      * in_neighbors and out_neighbors: dict(list)
                   For each node **u** of the graph, respectively store the incoming neighbors and outgoing neighbors of **u**. This structure is used for example to check on mutual dyads and is updated during each swap.

      * edges: dict(tuple)
                   For each edge **(u,v)**, it stores the position of **v** in **neighbors[u]**, in **out_neighbors[u]**, and the position of **u** in **neighbors[v]** and in **in_neighbors[v]**.

MarkovChain
-----------

- The main function of the MarkovChain object is the **run** methods, that calls all the others depending on the input constraints. To add new constraints, update the **check_swap** methods, that accepts or rejects a swap depending on the constraints.

    * pick_k : choose a **k** value following a powerlaw distribution with exponent **gamma**

    * find_swap : uniformly choose **k** edges to swap, and a permutation.

    * check_swap : check that the chosen swap respects each constraint. The complexity depends on the constraints.
               For undirected graph, with fixed degree sequence constraint (the basic case), for each swap between **(u,v)** and **(x,y)**: 

               * check that it doesn't create a loop (**u != y**) in **O(1)**

               * check that swapped edge doesn't exist (**(u,y) not in graph.edges**) in **O(1)**

               * if **k>2**, check that several permutations don't result in the same edge in **O(k)** (**len(goal_edges) == len(set(goal_edges))**, where **goal_edges** is the list of all the resulting edge if swap is accepted)

    * perform_swap : update the Graph data structure depending on the swap. 
               Each swap between two edges **(u,v)** and **(x,y)** is in amortized **O(1)** time (for undirected graphs - easily generalized to directed graphs): 

               * getting the possition **v_idx = edges[(u,v)]** of **v** in **neighbors[u]** is in amortized O(1) (edges is a hash map), and **x_idx = edges[(y,x)]**

               * updating the value **neighbors[u][v_idx] = y** is in amortized **O(1)**

               * deleting **edges[(u,v)]** and **edges[(v,u)]** is in amortized **O(1)**

               * adding **edges[(u,y)] = y** and **edges[(y,u)]=x_idx** is in amortized **O(1)**



- Other methods are implemented to measure some metrics on the graph. Each metric has an "init" and an "update" function, the "init" computes the value for the input graph, then the "update" methods updates it after each swap without having to compute it again for edges that haven't changed.


Stat
----

- The Stat class implements methods to estimate the sampling gap of the MarkovChain object, and follows its convergence. 

- The sampling gap is the number of required steps of the *converged* Markov Chain between two samples to ensure that both samples are uncorrelated.

- Two methods are implemented to choose a sampling gap:

  * estimate_sampling_gap: 
    
    * First run a *burn-in* step to obtain a fully converged Markov Chain

    * Estimate the acceptation rate **A** of the Markov Chain on the burn-in

    * initialize the sample gap value at **eta = M/A ** where **M** is the number of edges in the graph and **A** the acceptation rate of the chain.

    * Starting from the same final step of the *burn-in*, run **10** different chains for **500eta** steps, measuring **1** assortativity (or number of triangles) each **eta** step.

    * If the autocorellation with lag 1 of each timeserie of assortativities (or number of triangles) returns that at least **9** out of the **10** chains are not correlated, the sampling gap is considered valid.

        * If the sampling gap **eta** is valid, try **eta=eta/2**

        * If not, try **eta=2eta**

        * start as soon as the comportment changes and return the last valid eta value.



  * run_dfgls:

        * if no **eta** value is given in input, estimate an **eta** value

        * while the MarkovChain is not converged:

            * run the MarkovChain object for **eta** step and collect the assortativity (or number of triangles) at each step.

            * after **eta** steps, check if the timeserie of assortativity values (or number of triangles) has converged using a DFGLS test.

Contribution
------------

- To contribute to the package, you can put issues on the gitlab repository to either report a bug or a problem, or to ask a question.

- Any pull request will be reviewed and integrated if the contribution is within the scope of the project.

