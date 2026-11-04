# Bibliothèque ClickDeck

Les modèles et les plugins proposés dans l'application ClickDeck. L'application lit ce dépôt
sans compte : il doit rester **public**.

| Chemin | Contenu |
|---|---|
| `modeles/<id>.json` | un modèle : pages et touches |
| `plugins/<id>.json` | un plugin : catégories d'actions ajoutées à l'éditeur |
| `sources/<id>.json` | la fiche d'une application : raccourcis par système et leurs sources |
| `outils/generer.py` | fabrique les modèles et plugins depuis `sources/` |
| `index.json` | applications jusqu'à la 1.18 : liste figée, générée par `publier.py` |
| `catalogue.json` | à partir de la 1.19.0 : fiches consultées en ligne, générées par `publier.py` |

## Publier un changement

Ne dépassez jamais 500 entrées dans `index.json` : les applications jusqu'à la 1.18 refuseraient
l'index entier. `publier.py` y garde seulement les éléments déjà présents ; tout le reste va dans
`catalogue.json`. Les maths n'y figurent pas : ils sont embarqués dans l'application.

1. Modifiez le fichier du modèle ou du plugin, ou sa fiche dans `sources/` puis lancez
   `outils/generer.py`.
2. Montez son champ `version` (`1.2.0` → `1.3.0`). Sans cela, `publier.py` refuse.
3. `./publier.py` montre ce qui partirait, `./publier.py --publier` publie.

Les applications vérifient le dépôt au démarrage puis toutes les six heures ; le bouton
**Vérifier** de la bibliothèque le fait à la demande. Une publication est visible au plus tard
cinq minutes après (cache de `raw.githubusercontent.com`).

Si un modèle a besoin d'une touche apparue dans une version précise de l'application, ajoutez
`"minAppVersion": "1.19.0"` : les applications plus anciennes garderont la version d'avant.

## Ce que reçoit l'utilisateur

- **Modèle non modifié** : mis à jour automatiquement, sauf celui affiché à l'écran, qui attend
  un clic. L'option se coupe dans la bibliothèque.
- **Modèle modifié par l'utilisateur** : jamais remplacé tout seul. Il peut le demander (« Remplacer
  par la vX »), et sa version est alors gardée dans un nouveau modèle.
- **Plugin** : mis à jour depuis l'onglet Plugins. Les touches déjà posées ne changent pas.

## Sécurité

Un fichier de ce dépôt ne peut pas exécuter de commande : l'application n'accepte qu'une liste
fermée de types de touches, une grammaire fermée pour les raccourcis (`touche:win=…;mac=…;lin=…`) (`desktop-app/src/library/libraryValidation.ts`) et refuse tout le
reste, dont le type `custom`. Un nouveau type de touche doit d'abord y être ajouté, dans une
nouvelle version de l'application, puis exigé ici avec `minAppVersion`.
