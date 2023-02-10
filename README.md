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
   | ---- | -------- | --------------- | --------------- | ------- | ------------- | ------------------- | ---------------------- |
   | powergrid | no | no | 4939 | 6594 | 0.00054 | 0.00346| 651 | - |
   | karateclub | no | no | 33 | 78 | 0.148 | -0.476| 45 | - |
   | celegans | no | no | 57 | 2025 | 0.0000278 | -0.226 | 3284 | - |
   | maayan | yes | no | 628 | 2613 | 0.0000993 | 0.0447 | 326 | 205 |
   | health | yes | no | 2539 | 12969 | 0.0020 | 0.288 | 4694 | 2514 |
   | macaques | yes | no | 57 | 1187 | 0.372 | -0.0645 | 9781 | 20 |
   | gotelli finches | no | yes | 36 | 55 | 0.17 | -0.44 | - | - |
 

    

## Benchmark

   | dataset | directed | constraint | using eta estimation | eta value | acceptation rate | eta estimation runtime (in seconds) | convergence runtime (in seconds) | total runtime (in seconds) |
   | ------- | -------- | ---------- | -------------------- | --------- | ---------------- | ----------------------------------- | -------------------------------- | ------------------------ |
   | powergrid | no | fixed degree sequence | yes | 8064 | 40.88% | 65 285s | 73.86s |  79261s |
   | karateclub |  no | fixed degree sequence | yes | 751 | 10.38% | 392.90s | 6.71s | 647s |
   | celegans | no | fixed degree sequence | yes | 5847 | 17.31% | 19 414 s | 91.89s | ? | 
   | health |  yes |   fixed degree sequence |  yes |  32 457 |  39.48% |   174 238s |  1 754s | 259364s |
   | maayan | yes | fixed degree sequence | yes |  6730 | 38.82% | 8804.56s | 57.13s | 13175s |
   | gotelli finches | no |  fixed degree sequence | yes | 1141 | 4.1% | 510.14s | 4.30s | 937.94s 
   | karateclub | no | fixed joint degree matrix | yes | 5053 |  1.54% | 2 567s | 8.32s | 4184s |
   | powergrid | no | fixed joint degree matrix | yes | 197 180 | 1.54% | 1 644 229s | 1 399.76s | ? |
   | maayan | yes | fixed joint degree matrix | yes | 163494 | 3.2% | 516 290s | 427.52s | ? |
   | celegans | no | fixed joint degree matrix | yes | - | 1.11% | - | - | ? | 
   | maayan | yes  | fixed number of diades | yes | 6727 | 38.84% | 8564.87s | 8.98s | 13041s |  
   | health | yes | fixed number of diades | yes | 32468 | 39.94% | 172813.34s | 431.45s | 255743s |



