# code Swap Proba Partage

Code python pour les expériences de génération de graphes aléatoires

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
   
## Format d'entrée

* Le paquet prend en entrée des graphes au format "edge-list" séparés par des espaces: 

  1 2

  1 3

  4 5

  5 6

* Si un lien apparait plusieurs fois, un seul exemplaire du lien sera conservé dans la structure stockée. Si le graphe est dirigé, le lecteur fera une différence entre un lien "u v" et le lien réciproque "v u", sinon il sera stocké sous la forme "u v" avec u < v.

* Les boucles ne sont pas conservées.

## Utilisation
* Notation: V est l'ensemble des noeuds du graph, E est l'ensemble des liens du graph. 

* Graph.py lit et stock la structure du graphe. La structure utilisée est: 
	- neighbors, defaultdict(list) :  une table de hachage stockant les liste d'adjacence pour chaque noeud, i.e. neighbors[u] = [ node v / (u,v) in E ]
	- edges, dict : une table de hachage stockant pour chaque lien la position du second noeud dansl a liste d'adjacence du premier noeud, e.g. si neighbors[u] = [n,m], edges[(u, m)] = 1
	- unique_edges : liste stockant un exemplaire unique de chaque noeud, nécessaire uniquement pour les graphes non dirigés (permet de piocher un lien sans remplacement, sans risque de le piocher une seconde fois)

* MarkovChain.py trouve les échanges de liens et les réalise

* Stat.py estime le sampling gap et mesure la convergence

* example d'utilisation: 
	python main.py -f ./data/ucidata-zachary/out.ucidata-zachary -o ./karateclub.out

* paramètrage de main.py:

    * -f : donner le chemin vers le fichier d'entrée (format edge list, noeuds séparés par des espaces)

    * -o : donner le chemin vers le fichier de sortie. Va écrire 10000 graphes post-convergence.

    * -n : optionnel: nombre de swaps demandés.

    * -g : exposant de la loi 1/n^g permettant de choisir k.

    * -d : activer si le graphe d'entrée est dirigé.

    * -e : optionnel: spécifier le "sampling gap". Si non spécifié, une methode d'estimation (assez lente) est utilisée.

    * -jd : optionnel: activer pour chercher des swaps qui conservent la "joint degree matrix" constante. Attention, option incompatible avec "-a" puisque l'assortativité reste aussi constante, et donc ne permet pas de verifier la convergence.

    * -t : optionnel: activer pour suivre la convergence en regardant le nombre de triangles dans le graphe. Option obligatoire si "-jd" est activé. Attention, option incompatible avec "-a", choisir l'un ou l'autre.

    * -a : optionnel (activé par défaut): activer pour suivre la convergence en regardant l'assortativité du graphe. Attention, option incompatible avec "-t" et "-jd".

    * -dfgls : optionnel (activé par défaut): méthode utilisé pour suivre la convergence (Dick Fulley Generalized Least Square utilisé sur la série temporelle de l'assortativité ou du nombre de triangles selon l'option -a ou -t).

    
    * -v : optionnel: augment la verbosité

    * --keep_record : optionnel: permet de sauvegarder tous les graphes et tout les swaps ayant permis de generer ces graphes.

    * --log_dir : optionnel: à utiliser si --keep_record est activé. Spécifie un dossier dans lequel les graphes et swaps sont sauvegardés.

## Datasets

   | name | directed | bipartite | number of nodes | number of edges | density | assortativity | number of triangles | number of mutual dyads |
   | ---- | -------- | --------- | --------------- | --------------- | ------- | ------------- | ------------------- | ---------------------- |
   | lesmiserables | no | no | 77 | 254 | 0.08681 | -0.16523 | 467 | - |
   | powergrid | no | no | 4941 | 6594 | 0.00054 | 0.00346| 651 | - |
   | karateclub | no | no | 34 | 78 | 0.13904 | -0.476| 45 | - |
   | celegans | no | no | 453 | 2025 |  0.01978 | -0.226 | 3284 | - |
   | maayan | yes | no | 1226 | 2613 | 0.00174 | 0.0447 | 326 | 205 |
   | health | yes | no | 2539 | 12969 | 0.00201 | 0.288 | 4694 | 2514 |
   | macaques | yes | no | 62 | 1187 | 0.31386 | -0.0645 | 9781 | 20 |
   | gotelli finches | no | yes | 36 (17 + 19) | 55 | 0.17027 | -0.44 | - | - |
   | krackhardt | yes | no | 21 | 100 | 0.23810 | -0.184 | 100 | 44 |
   | chiloe_polinators | no | yes | 155 (129 + 26) | 312 | 0.09302 | -0.57958 | - | - |

## Comparaison temps execution des méthodes d'estimation de eta

    * linear eta estimation: burn-in de 1000M pas, initialisation de eta à 0, puis incrément de eta += 0.05M jusqu'à atteindre une valeur validant 9/10 des tests d'autocorrelation avec un lag1

    * dichotomic eta estimation: burn-in de 1000M pas, estimation du taux d'acceptation A de la chaîne de Markov, initialisation de eta = M/A, puis eta = 2eta si les tests ne sont pas validés, eta = eta/2 sinon, et on stop lorsqu'il y a changement de comportement du test. (#TODO mal décrit)

    * turbo eta estimation: burn in de 10M, estimation du taux d'acceptation A de la chaîne de Markov, eta = 10M/A

   | dataset | linear (time in s) | dichotomic (time in s) | turbo (time in s) | linear eta value | dichotomic eta value | turbo eta value |
   | ------- | ------------------ | ---------------------- | ----------------- | ---------------- | -------------------- | --------------- |
   | karateclub | 9145 | 407 | 0.14 | 452 | 741 | 8222 |
   | gotelli finches | 24214 | 541 | 0.07 | 611 | 1146 | 15778 |
   | lesmis | 40629 | 1267 | 0.51 | 1562 | 1788 | 18021|


## Benchmark

   | dataset | directed | constraint | using eta estimation | eta value | acceptation rate | eta estimation runtime (in seconds) | convergence runtime (in seconds) | total runtime (in seconds) |
   | ------- | -------- | ---------- | -------------------- | --------- | ---------------- | ----------------------------------- | -------------------------------- | ------------------------ |
   | powergrid | no | fixed degree sequence | yes | 8064 | 40.88% | 65285s | 73.86s |  79261s |
   | karateclub |  no | fixed degree sequence | yes | 751 | 10.38% | 392s | 6.71s | 647s |
   | celegans | no | fixed degree sequence | yes | 5847 | 17.31% | 19414 s | 20s | 24670s | 
   | lesmiserables | no | fixed degree sequence | yes | 3576 | 14.20% | 3043s | 64s | 4573s |
   | health |  yes |   fixed degree sequence |  yes |  32 457 |  39.48% |   174238s |  1 754s | 259364s |
   | maayan | yes | fixed degree sequence | yes |  6730 | 38.82% | 8804s | 57s | 13175s |
   | krackhardt | yes | fixed degree sequence | yes |  430 | 5.80% | 484s | 12s | 563s |
   | gotelli finches | bip |  fixed degree sequence | yes | 116 | 5.92% | 260s | 5s | 284s |
   | lesmiserables | no | fixed joint degree matrix | yes | 24643 |  1.03% | 15987s | 43s | 26398s |
   | karateclub | no | fixed joint degree matrix | yes | 5053 |  1.54% | 2567s | 8s | 4184s |
   | powergrid | no | fixed joint degree matrix | yes | 197 180 | 1.54% | 1644229s | 6023s | 2001551s |
   | maayan | yes | fixed joint degree matrix | yes | 163494 | 3.2% | 516290s | 330s | 668480s |
   | celegans | no | fixed joint degree matrix | yes | - | 1.11% | - | - | en cours | 
   | maayan | yes  | fixed number of dyads | yes | 6727 | 38.84% | 8564s | 8s | 13041s |  
   | health | yes | fixed number of dyads | yes | 32468 | 39.94% | 172813s | 431s | 255743s |
   | krackhardt | yes | fixed number of dyads | yes |  444 | 5.62% | 508s | 0.15s | 575s |

## Comparaison Gamma

   | dataset | directed | gamma | eta value | acceptation rate | eta estimation runtime | convergence runtime | total runtime |
   | ---- | -------- | --------- | --------------- | --------------- | ------- | ------------- | ------------------- |
   | lesmiserables | no | 2 | 3576 | 14.20% | 3043s | 64s | 4573s |
   | lesmiserables | no | 4 | 2268 | 22.39% | 1342s | 0.66s | 1966s |
   | lesmiserables | no | 8 | 1972 | 48.21% | 1086s | 3s | 1578 |
   | powergrid | no | 2 |  8064 | 40.88% | 65285s | 73s |  79261s |
   | powergrid | no | 3 | 14914 | 44.21% | 125539s | 302s| 148479s |
   | powergrid | no | 4 | 28541 | 46.20% | 102955s | 1466s| 221700s |
   | powergrid | no | 8 | - | 49.23% | - | | en cours |
   | celegans | no | 2 | 5847 | 17.31% | 19414s | 20s | 24670 | 
   | celegans | no | 3 | 8608 | 23.52% | 9844s | 10s | 15253s | 
   | celegans | no | 4 | 7664 | 26.41% | 8470s | 18s | 13187s | 
   | celegans | no | 8 | 6780 | 29.86% | 7867s | 29s | 12021s | 
   | maayan | yes | 2 |  6730 | 38.82% | 8804s | 57s | 13175s |
   | maayan | yes | 4 |  | 38.30% |  | | en cours |
   | maayan | yes | 8 | 9988 | 48.21% | 15678s | 34s | en cours |
   | krackhardt | yes | 2 | 444 | 5.602% | 508s | 0.15s | 575s |
   | krackhardt | yes | 4 | 251 | 9.945% | 302s | 5s | 547s |
   | krackhardt | yes | 8 | 209 | 11.95% | 295s | 3s | 333s |


