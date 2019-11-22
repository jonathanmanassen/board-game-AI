# phantom-at-the-opera

Ce projet est un projet python ou deux IAs (fantom et inspector) s'affrontent sur le jeu de plateau "phantom at the opera". Les deus IAs sont codés en python dans leurs fichiers respectifs.

## Implémentation

Les deux IAs ont été codés avec un minmax, une technique choisi de part le fait que nous n'avons pas accès à tous les moves possibles jusqu'à la fin de la partie.
En effet le serveur mélange les 8 cartes correspondant au personnages et l'on a à un instant présent que une à quatre cartes à disposition pour jouer, nous pourrions déduire les 4 autres cartes utilisées ensuite mais au dela de ça, il y a un mélange effectué par le serveur. De ce fait le minmax paraissait adapté car il était possible en un temps adapté (environ 1 seconde pour jouer une partie complète) de traverser un arbre contenant toutes les issues possibles à un moment donné en allant à une profondeur égale aux nombre de cartes activement donné par le serveur.
La taille de cet arbre était donc :
n * nbPotentielDéplacements * (nbPotentielPouvoirs + 1) + ... + 1 * nbPotentielDéplacements * (nbPotentielPouvoirs + 1) avec 1 <= n <= 4.

Ceci a été mis en place à l'aide d'une fonction minmax considérant qui peut jouer son coup, en itérant sur toutes les salles adjacentes accessibles, puis en itérant sur toutes les utilisations potentielles du pouvoir du personnage (+ 1 pour un déplacement sans pouvoir).

### Optimization

La vitesse des IAs est aussi considérablement améliorée de part l'utilisation de l'Élagage alpha-bêta qui permet d'optimiser grandement l'algorithme minimax sans en modifier le résultat.
Ceci est le cas car certains sous-arbres peuvent ne pas être considérés car nous pouvons savoir en avance qu'ils ne participeront pas au résultat final.

### Heuristique

Puisque l'algorithme ne joue pas au jeu jusqu'à ce qu'un vainqueur soit élu durant sa prise de décision, l'utilisation d'un heuristique est utilisé pour savoir si l'état du plateau est favorable au fantôme ou à l'inspecteur. Cet heuristique est d'ailleurs la seulle partie du code qui diffère entre les deux IAs.

Du côté du fantôme, la valeur de l'heuristique est simplement :
(nombre de suspects - nombres de personnes qui ne seront plus suspectes à la fin du tour) * 2 + 1 si le fantôme est révélé + 1.5 si le fantôme joue le personnage rouge.

Cet heuristique renvoie une valeur correspondant au nombre de cases que la carlotta avancerait à la fin du tour avec ce plateau, avec des valeurs plus hautes si un maximum de personnes restent suspectent. (le + 1.5 pour le personnage rouge est car il peut soit faire avancer d'une case comme le fait de révélé le fantôme, soit révéler un suspect).

Du côté de l'inspecteur nous ne connaissons pas le fantôme, nous appliquons donc la même formule que pour le fantôme (inversée puiqu'un plateau valant +10 pour le fantôme est le même que -10 pour l'inspecteur) autant de fois qu'il reste de suspects en imaginant le résultat pour chaque potentiel fantôme.

## Authors

**Jonathan Manassen**<br>
**Christophe Mei**
**Julien Meslin**
**Gabin Meyrieux-Drevet**