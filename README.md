# auto_click

Petit script Python qui capture l’écran et demande à GPT-4o Vision où se trouve un élément désigné. Il déplace ensuite la souris au-dessus de la position renvoyée et peut saisir du texte.

## Utilisation


 ```bash
 python auto_click.py -t "bouton Télécharger"                 # capture auto via $OPENAI_API_KEY
 python auto_click.py -s screenshot.png -t "champ de recherche"  # utilise une image existante
 python auto_click.py -k sk-... -t "bouton OK"                   # clé OpenAI explicite
 python auto_click.py --no-hover -t "Zone de texte"             # debug : ne pas bouger la souris
 python auto_click.py --test-firefox                           # teste l'ic\u00f4ne Firefox
 ```

## Exemple rapide

Pour demander un clic sur l'icône *Firefox* affichée sur le bureau :

1. Ouvrez la session graphique avec l'icône visible.
2. Lancez :

   ```bash
   python auto_click.py -t "icône Firefox"
   ```

Le programme capture l'écran, interroge GPT‑4o pour localiser l'icône,
déplace la souris puis affiche brièvement un cercle rouge autour de la
position visée afin d'indiquer où il tente de cliquer.

## Mode test Firefox

Pour vérifier rapidement le fonctionnement du script, on peut lancer :

```bash
python auto_click.py --test-firefox
```

Le programme cherche l'icône Firefox, effectue un double clic et laisse le
marqueur rouge affiché pendant dix secondes pour montrer la position visée.

Le script fonctionne plutôt bien mais il clique souvent juste à côté de la bonne cible. Je n’ai pas trouvé comment améliorer cela, sauf attendre un meilleur modèle.
Le code complet se trouve dans [auto_click.py](auto_click.py).
