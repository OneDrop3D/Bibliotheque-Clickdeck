#!/usr/bin/env python3
"""
Recalcule index.json à partir de modeles/ et plugins/, puis publie.

    ./publier.py              # contrôle, et montre ce qui partirait
    ./publier.py --publier    # écrit index.json, commite et pousse

Un fichier modifié doit changer de version, sinon les applications ne verraient
pas la mise à jour : le script refuse de continuer. Les applications voient une
publication au plus tard cinq minutes après (cache de raw.githubusercontent.com).
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ICI, "index.json")
DOSSIERS = {"models": "modeles", "plugins": "plugins"}
IDENTIFIANT = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
TAILLE_MAX = 2 * 1024 * 1024
# Doit rester l'équivalent de desktop-app/src/library/libraryValidation.ts.
TYPES_INTERDITS = {"custom"}


def version_tuple(version):
    return tuple(int(partie) for partie in version.split("."))


def touches(element):
    configs = [element.get("config")] + list(element.get("variantConfigs") or [])
    for config in configs:
        for page in (config or {}).get("pages", []):
            for bouton in page.get("buttons", []):
                if bouton.get("action"):
                    yield bouton["action"]
    for categorie in element.get("categories", []):
        yield from categorie.get("actions", [])


def lire_entrees(cle):
    entrees = []
    dossier = os.path.join(ICI, DOSSIERS[cle])
    for nom in sorted(os.listdir(dossier)):
        if not nom.endswith(".json"):
            continue
        chemin = os.path.join(dossier, nom)
        with open(chemin, "rb") as fichier:
            contenu = fichier.read()
        element = json.loads(contenu)
        identifiant = nom[:-5]

        if element.get("id") != identifiant or not IDENTIFIANT.match(identifiant):
            sys.exit(f"{nom} : l'identifiant doit être le nom du fichier")
        if not VERSION.match(str(element.get("version"))):
            sys.exit(f"{nom} : version invalide (attendu 1.2.3)")
        if len(contenu) > TAILLE_MAX:
            sys.exit(f"{nom} : fichier trop volumineux")
        for action in touches(element):
            if str(action.get("type", "")).lower() in TYPES_INTERDITS:
                sys.exit(f"{nom} : type de touche interdit ({action.get('type')})")

        entree = {
            "id": identifiant,
            "version": element["version"],
            "sha256": hashlib.sha256(contenu).hexdigest(),
            "size": len(contenu),
        }
        if element.get("minAppVersion"):
            entree["minAppVersion"] = element["minAppVersion"]
        entrees.append(entree)
    return entrees


def comparer(cle, entrees, ancien):
    avant = {entree["id"]: entree for entree in ancien.get(cle, [])}
    changements = []
    for entree in entrees:
        precedente = avant.get(entree["id"])
        if not precedente:
            changements.append(f"nouveau   {DOSSIERS[cle]}/{entree['id']} {entree['version']}")
        elif precedente["sha256"] != entree["sha256"]:
            if version_tuple(entree["version"]) <= version_tuple(precedente["version"]):
                sys.exit(f"{entree['id']} a changé : passez sa version au-dessus de {precedente['version']}")
            changements.append(f"mis à jour {DOSSIERS[cle]}/{entree['id']} {precedente['version']} → {entree['version']}")
    for identifiant in avant.keys() - {entree["id"] for entree in entrees}:
        changements.append(f"retiré    {DOSSIERS[cle]}/{identifiant}")
    return changements


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--publier", action="store_true")
    options = parser.parse_args()

    ancien = {}
    if os.path.exists(INDEX):
        with open(INDEX, encoding="utf-8") as fichier:
            ancien = json.load(fichier)

    index = {"schema": 1}
    changements = []
    for cle in DOSSIERS:
        index[cle] = lire_entrees(cle)
        changements += comparer(cle, index[cle], ancien)

    print("\n".join(changements) or "Rien à publier.")
    if not options.publier or not changements:
        return

    with open(INDEX, "w", encoding="utf-8") as fichier:
        json.dump(index, fichier, indent=1, ensure_ascii=False)
        fichier.write("\n")
    subprocess.run(["git", "add", "-A"], cwd=ICI, check=True)
    subprocess.run(["git", "commit", "-m", f"Bibliothèque : {len(changements)} changement(s)"], cwd=ICI, check=True)
    subprocess.run(["git", "push"], cwd=ICI, check=True)


if __name__ == "__main__":
    main()
