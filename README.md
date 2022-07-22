# code Swap Proba Partage

Code python pour les expériences de génération de graphes aléatoires

## Installation

* Requirements : 
	- numpy
	- argparse
	- progressbar # TODO pas utile juste joli..

## Utilisation

* Graph.py lit et stock la structure du graphe

* Swap.py trouve les échanges de liens et les réalise # TODO inclure métriques + vérification validité de l'échange dans swap.py

* example: 
	python Swap.py -f ./gp_references.txt -o ./gp_references.out -n 10000 -g 2


## TODO
- ajouter autres contraintes validité de l'échange :
	- 1) cas de base: distribution de degré fixée
	- 2) graphe simple dirigé de Rao et al.
	- 3) joint degree matrix
	- 4) graphe simple dirigé avec liens mutuels
	- 5) graphe simple dirigé avec motifs triangulaires
- ajouter métriques suivi convergence

	* proposition de quantités d'intérêt à suivre:
	- assortativité (définition trouvable dans Dutta et al.)
	- nombre de triangles
	
	* tests statistiques de vérification de l'uniformité, littérature:
	- Stanton et Pinar, 2012: Constructing and Sampling Graphs with a Prescribed Joint Degree Distribution
	- Dutta, Fosdick et Clauset, 2022: Sampling random graphs with specified degree sequences

- ajouter quelques "assert" (tester les fonctions de swap et de checking...)
- plusieurs formats de graphes en entrée

