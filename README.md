# auto_click

Petit script Python qui capture l’écran et demande à GPT-4o Vision où se trouve un élément désigné. Il déplace ensuite la souris au-dessus de la position renvoyée et peut saisir du texte.

## Utilisation

```bash
python auto_click.py -t "bouton Télécharger"                 # capture auto via $OPENAI_API_KEY
python auto_click.py -s screenshot.png -t "champ de recherche"  # utilise une image existante
python auto_click.py -k sk-... -t "bouton OK"                   # clé OpenAI explicite
python auto_click.py --no-hover -t "Zone de texte"             # debug : ne pas bouger la souris
```

Le script fonctionne plutôt bien mais il clique souvent juste à côté de la bonne cible. Je n’ai pas trouvé comment améliorer cela, sauf attendre un meilleur modèle.

Le code complet se trouve dans [auto_click.py](auto_click.py).
