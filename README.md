# code Swap Proba Partage

Code python pour les expériences de génération de graphes aléatoires

## Installation

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

* Swap.py trouve les échanges de liens et les réalise # TODO inclure métriques + vérification validité de l'échange dans swap.py

* example d'utilisation: 
	python Swap.py -f ./gp_references.txt -o ./gp_references.out -n 10000 -g 2


## TODO
- ajouter autres contraintes validité de l'échange TODO a implémenter + tester:
	- 1) cas de base: distribution de degré fixée 
	- 2) graphe simple dirigé de Rao et al.
	- 3) joint degree matrix
	- 4) graphe simple dirigé avec liens mutuels
	- 5) graphe simple dirigé avec motifs triangulaires
- ajouter métriques suivi convergence

	* proposition de quantités d'intérêt à suivre:
	- nombre de triangles TODO a tester
	
	* tests statistiques de vérification de l'uniformité, littérature: 
	- Stanton et Pinar, 2012: Constructing and Sampling Graphs with a Prescribed Joint Degree Distribution TODO a tester

- ajouter quelques "assert" (tester les fonctions de swap et de checking...)
- plusieurs formats de graphes en entrée

