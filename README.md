# K-Edge-Swap

Python package to generate randomly uniformly picked graph by swapping edges from an existing graph.

## Installation

* To install package avec requirement: 

    pip install ./

* To check if everything works well:

    pytest tests/test.py

* Requirements : 
    - pip and setuptools : pip install --upgrade pip setuptools wheel
	- numpy
	- argparse
	- progressbar # TODO pas utile juste joli..
    - python3 
    - arch : pip install arch

## Input format

* The input graph should be in "edge-list" format:

  1 2  
  1 3   
  4 5  
  5 6  

* The package only stores simple graphs. If the input contains multiple edges, they will be merged into one single edge. Loops are ignored.


## Usage
* Notation: We call V the node set, E the edge set. 

* Usage example: 
	python main.py -f ./data/ucidata-zachary/out.ucidata-zachary -o ./karateclub.out -v

* Get a list of the main.py arguments:

    python main.py --help


## Documentation
* A documentation is available at [readthedocs]()

[comment]: # ## Datasets
[comment]: # 
[comment]: #    | name | directed | bipartite | number of nodes | number of edges | density | assortativity | number of triangles | number of mutual dyads |
[comment]: #    | ---- | -------- | --------- | --------------- | --------------- | ------- | ------------- | ------------------- | ---------------------- |
[comment]: #    | lesmiserables | no | no | 77 | 254 | 0.08681 | -0.16523 | 467 | - |
[comment]: #    | powergrid | no | no | 4941 | 6594 | 0.00054 | 0.00346| 651 | - |
[comment]: #    | karateclub | no | no | 34 | 78 | 0.13904 | -0.476| 45 | - |
[comment]: #    | celegans | no | no | 453 | 2025 |  0.01978 | -0.226 | 3284 | - |
[comment]: #    | maayan | yes | no | 1226 | 2613 | 0.00174 | 0.0447 | 326 | 205 |
[comment]: #    | health | yes | no | 2539 | 12969 | 0.00201 | 0.288 | 4694 | 2514 |
[comment]: #    | macaques | yes | no | 62 | 1187 | 0.31386 | -0.0645 | 9781 | 20 |
[comment]: #    | gotelli finches | no | yes | 36 (17 + 19) | 55 | 0.17027 | -0.44 | - | - |
[comment]: #    | krackhardt | yes | no | 21 | 100 | 0.23810 | -0.184 | 100 | 44 |
[comment]: #    | chiloe_polinators | no | yes | 155 (129 + 26) | 312 | 0.09302 | -0.57958 | - | - |
[comment]: #    | wikiquotes_jp | no | yes | 4847 (901 + 3946) | 10205 |  0.00574 | -0.20421 | - | - | 
[comment]: #    | crime | no | yes | 1380 | 1476 | 
[comment]: # 
[comment]: # 
[comment]: # ## Comparaison temps execution des méthodes d'estimation de eta
[comment]: # 
[comment]: #     * linear eta estimation: burn-in de 1000M pas, initialisation de eta à 0, puis incrément de eta += 0.05M jusqu'à atteindre une valeur validant 9/10 des tests d'autocorrelation avec un lag1
[comment]: # 
[comment]: #     * dichotomic eta estimation: burn-in de 1000M pas, estimation du taux d'acceptation A de la chaîne de Markov, initialisation de eta = M/A, puis eta = 2eta si les tests ne sont pas validés, eta = eta/2 sinon, et on stop lorsqu'il y a changement de comportement du test. (#TODO mal décrit)
[comment]: # 
[comment]: #     * turbo eta estimation: burn in de 10M, estimation du taux d'acceptation A de la chaîne de Markov, eta = 10M/A
[comment]: # 
[comment]: #    | dataset | linear (time in s) | dichotomic (time in s) | turbo (time in s) | linear eta value | dichotomic eta value | turbo eta value |
[comment]: #    | ------- | ------------------ | ---------------------- | ----------------- | ---------------- | -------------------- | --------------- |
[comment]: #    | karateclub | 9145 | 407 | 0.14 | 452 | 741 | 8222 |
[comment]: #    | gotelli finches | 24214 | 541 | 0.07 | 611 | 1146 | 15778 |
[comment]: #    | lesmis | 40629 | 1267 | 0.51 | 1562 | 1788 | 18021|
[comment]: # 
[comment]: # 
[comment]: # ## Benchmark
[comment]: # 
[comment]: #    | dataset | directed | constraint | using eta estimation | eta value | acceptation rate | eta estimation runtime (in seconds) | convergence runtime (in seconds) | total runtime (in seconds) |
[comment]: #    | ------- | -------- | ---------- | -------------------- | --------- | ---------------- | ----------------------------------- | -------------------------------- | ------------------------ |
[comment]: #    | powergrid | no | fixed degree sequence | yes | 8064 | 40.88% | 65285s | 73.86s |  79261s |
[comment]: #    | karateclub |  no | fixed degree sequence | yes | 751 | 10.38% | 392s | 6.71s | 647s |
[comment]: #    | celegans | no | fixed degree sequence | yes | 5847 | 17.31% | 19414 s | 20s | 24670s | 
[comment]: #    | lesmiserables | no | fixed degree sequence | yes | 3576 | 14.20% | 3043s | 64s | 4573s |
[comment]: #    | health |  yes |   fixed degree sequence |  yes |  32 457 |  39.48% |   174238s |  1 754s | 259364s |
[comment]: #    | maayan | yes | fixed degree sequence | yes |  6730 | 38.82% | 8804s | 57s | 13175s |
[comment]: #    | krackhardt | yes | fixed degree sequence | yes |  430 | 5.80% | 484s | 12s | 563s |
[comment]: #    | crime | bip | fixed degree sequence | yes | 957 | 38.53% | 3979s | 17s | 3999s (no sample generation) | 
[comment]: #    | wikiquotes_jp | bip | fixed degree sequence | yes | 62869 | 16.23% | 264401s | 150s | 412792s | 
[comment]: #    | gotelli finches | bip |  fixed degree sequence | yes | 116 | 5.92% | 260s | 5s | 284s |
[comment]: #    | lesmiserables | no | fixed joint degree matrix | yes | 24643 |  1.03% | 15987s | 43s | 26398s |
[comment]: #    | karateclub | no | fixed joint degree matrix | yes | 5053 |  1.54% | 2567s | 8s | 4184s |
[comment]: #    | powergrid | no | fixed joint degree matrix | yes | 197 180 | 1.54% | 1644229s | 6023s | 2001551s |
[comment]: #    | maayan | yes | fixed joint degree matrix | yes | 163494 | 3.2% | 516290s | 330s | 668480s |
[comment]: #    | celegans | no | fixed joint degree matrix | yes | - | 1.11% | - | - | en cours | 
[comment]: #    | crime (gamma 8) | bip | fixed joint degree matrix | yes | 45941 | 12.85% | 11485s | 69s | 147480s | 
[comment]: #    | maayan | yes  | fixed number of dyads | yes | 6727 | 38.84% | 8564s | 8s | 13041s |  
[comment]: #    | health | yes | fixed number of dyads | yes | 32468 | 39.94% | 172813s | 431s | 255743s |
[comment]: #    | krackhardt | yes | fixed number of dyads | yes |  444 | 5.62% | 508s | 0.15s | 575s |
[comment]: # 
[comment]: # ## Comparaison Gamma
[comment]: # 
[comment]: #    - Séquence de degré fixé
[comment]: # 
[comment]: #    | dataset | directed | gamma | eta value | acceptation rate | eta estimation runtime | convergence runtime | total runtime |
[comment]: #    | ---- | -------- | --------- | --------------- | --------------- | ------- | ------------- | ------------------- |
[comment]: #    | lesmiserables | no | 2 | 3576 | 14.20% | 3043s | 64s | 4573s |
[comment]: #    | lesmiserables | no | 4 | 2268 | 22.39% | 1342s | 0.66s | 1966s |
[comment]: #    | lesmiserables | no | 8 | 1972 | 48.21% | 1086s | 3s | 1578 |
[comment]: #    | powergrid | no | 2 |  8064 | 40.88% | 65285s | 73s |  79261s |
[comment]: #    | powergrid | no | 3 | 14914 | 44.21% | 125539s | 302s| 148479s |
[comment]: #    | powergrid | no | 4 | 28541 | 46.20% | 102955s | 1466s| 221700s |
[comment]: #    | powergrid | no | 8 | 53576 | 49.23% | - | | en cours |
[comment]: #    | celegans | no | 2 | 5847 | 17.31% | 19414s | 20s | 24670 | 
[comment]: #    | celegans | no | 3 | 8608 | 23.52% | 9844s | 10s | 15253s | 
[comment]: #    | celegans | no | 4 | 7664 | 26.41% | 8470s | 18s | 13187s | 
[comment]: #    | celegans | no | 8 | 6780 | 29.86% | 7867s | 29s | 12021s | 
[comment]: #    | maayan | yes | 2 |  6730 | 38.82% | 8804s | 57s | 13175s |
[comment]: #    | maayan | yes | 4 | 6286 | 38.30% | 12023s | 212s | 18319s |
[comment]: #    | maayan | yes | 8 | 9988 | 48.21% | 15678s | 34s | 14489s |
[comment]: #    | krackhardt | yes | 2 | 444 | 5.602% | 508s | 0.15s | 575s |
[comment]: #    | krackhardt | yes | 4 | 251 | 9.945% | 302s | 5s | 547s |
[comment]: #    | krackhardt | yes | 8 | 209 | 11.95% | 295s | 3s | 333s |
[comment]: # 
[comment]: #    - Séquence de degré fixé
[comment]: # 
[comment]: #    | dataset | directed | gamma | eta value | acceptation rate | eta estimation runtime | convergence runtime | total runtime |
[comment]: #    | ---- | -------- | --------- | --------------- | --------------- | ------- | ------------- | ------------------- |
[comment]: #    | lesmiserables | no | 2 | 24643 | 1.03% | 15987s | 43s | 26398s |
[comment]: #    | lesmiserables | no | 2 | 13223 | 1.92% | 5552s | 36s | 5597s (pas de generation après convergence) |
[comment]: # 
