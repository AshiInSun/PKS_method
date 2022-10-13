# code Swap Proba Partage

Code python pour les expériences de génération de graphes aléatoires

## Installation

* To install package avec requirement: 

    pip install -e ./

* To check if everything works well:

    pytest tests/test.py

* Requirements : 
	- numpy
	- argparse
	- progressbar # TODO pas utile juste joli..
    - python3 
    - arch : pip install arch

## Utilisation
* Notation: V est l'ensemble des noeuds du graph, E est l'ensemble des liens du graph. 

* Graph.py lit et stock la structure du graphe. La structure utilisée est: 
	- neighbors, defaultdict(list) :  une table de hachage stockant les liste d'adjacence pour chaque noeud, i.e. neighbors[u] = [ node v / (u,v) in E ]
	- edges, dict : une table de hachage stockant pour chaque lien la position du second noeud dansl a liste d'adjacence du premier noeud, e.g. si neighbors[u] = [n,m], edges[(u, m)] = 1
	- unique_edges : liste stockant un exemplaire unique de chaque noeud, nécessaire uniquement pour les graphes non dirigés (permet de piocher un lien sans remplacement, sans risque de le piocher une seconde fois)

* MarkovChain.py trouve les échanges de liens et les réalise

* Stat.py estime le sampling gap et mesure la convergence

* example d'utilisation: 
	python main.py -f ./gp_references.txt -o ./gp_references.out 


## TODO
- ajouter autres contraintes validité de l'échange TODO a implémenter + tester:
	- 4) graphe simple dirigé avec liens mutuels
	- 5) graphe simple dirigé avec motifs triangulaires
- ajouter métriques suivi convergence

