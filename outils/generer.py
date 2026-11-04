#!/usr/bin/env python3
"""
Fabrique les modèles et plugins à partir des fiches de sources/.

    outils/generer.py                       # sources/ vers modeles/ et plugins/
    outils/generer.py --sources X --sortie Y

Une fiche décrit une application (raccourcis Windows, Mac et Linux, avec leurs
sources). Elle donne un modèle à deux variantes, Essentiel et Complet, et un
plugin avec les mêmes touches rangées par catégorie.
"""
import argparse
import colorsys
import hashlib
import json
import os
import re
import urllib.parse

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
APP_MINIMALE = "1.18.5"
DATE = "2026-11-04"
GAUCHE, DROITE = 18, 23
PAR_PAGE = 22
MAX_PAGES = 10
MINIMUM_TOUCHES = 6
CASES = [case for case in range(24) if case not in (GAUCHE, DROITE)]
CATEGORIES = {
    "Vidéo": "streaming", "Audio": "music", "Émulation": "gaming",
}

MODIFICATEURS = {"control": "ctrl", "option": "alt", "opt": "alt", "command": "cmd", "maj": "shift"}
SYNONYMES = {
    "/": "slash", ".": "period", ",": "comma", ";": "semicolon", "'": "quote", "`": "backquote",
    "=": "equal", "-": "minus", "+": "plus", "[": "bracketleft", "]": "bracketright", "\\": "backslash",
    "return": "enter", "esc": "escape", "del": "delete", "asterisk": "numstar",
    "arrowup": "up", "arrowdown": "down", "arrowleft": "left", "arrowright": "right",
    "pgup": "pageup", "pgdn": "pagedown",
}
TOUCHES = re.compile(
    r"[a-z0-9]|f([1-9]|1[0-2])|up|down|left|right|home|end|pageup|pagedown|enter|tab|space|escape|backspace|delete"
    r"|plus|minus|equal|comma|period|slash|backslash|semicolon|quote|bracketleft|bracketright|backquote"
    r"|num[0-9]|numplus|numminus|numstar|numslash|numperiod|numenter"
)
RESERVES = {"alt+tab", "cmd+tab", "cmd+space", "ctrl+alt+delete", "cmd+h", "cmd+m"}

with open(os.path.join(ICI, "pictos-lucide.json"), encoding="utf-8") as fichier:
    PICTOS = json.load(fichier)
with open(os.path.join(ICI, "logos-simple-icons.json"), encoding="utf-8") as fichier:
    LOGOS = json.load(fichier)


def data_uri(svg):
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg, safe="-_.!~*'()")


def picto(nom):
    interieur = PICTOS.get(nom) or PICTOS["keyboard"]
    return data_uri(
        '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 24 24" fill="none" '
        'stroke="#0f172a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + interieur + "</svg>"
    )


def couleur(texte):
    teinte = int(hashlib.sha256(texte.encode()).hexdigest()[:4], 16) / 65535
    rouge, vert, bleu = colorsys.hls_to_rgb(teinte, 0.42, 0.6)
    return f"#{int(rouge * 255):02X}{int(vert * 255):02X}{int(bleu * 255):02X}"


def logo(fiche):
    """Logo Simple Icons (CC0) s'il existe, sinon une tuile aux initiales."""
    for nom in (fiche.get("logo"), fiche["nom"]):
        trouve = LOGOS.get(str(nom).lower())
        if trouve:
            return data_uri(
                '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 24 24">'
                f'<path fill="#{trouve["hex"]}" d="{trouve["path"]}"/></svg>'
            )
    mots = [mot for mot in re.split(r"[\s\-_/]+", fiche["nom"]) if mot and mot[0].isalnum()]
    initiales = "".join(mot[0] for mot in mots[:2]).upper() or "?"
    return data_uri(
        '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">'
        f'<rect width="96" height="96" rx="20" fill="{couleur(fiche["nom"])}"/>'
        '<text x="48" y="62" font-family="Arial,sans-serif" font-size="40" font-weight="700" '
        f'text-anchor="middle" fill="#fff">{initiales}</text></svg>'
    )


def normaliser(raccourci, systeme):
    """Raccourci dans la grammaire de keyChord.ts, ou None s'il ne peut pas y entrer."""
    texte = str(raccourci).strip().lower()
    final = "+" if texte.endswith("+") else None
    parties = [partie.strip() for partie in texte.split("+") if partie.strip()]
    if final:
        parties.append(final)
    if not parties:
        return None
    *mods, touche_finale = parties
    mods = [MODIFICATEURS.get(mod, mod) for mod in mods]
    touche_finale = SYNONYMES.get(touche_finale, touche_finale)
    if systeme == "mac" and touche_finale == "delete":
        touche_finale = "backspace"  # Sur Mac, la touche marquée « delete » est le retour arrière.
    if systeme == "win" and mods and touche_finale in ("numplus", "numminus"):
        touche_finale = touche_finale[3:]  # Windows n'envoie pas le pavé avec un modificateur.
    resultat = "+".join(mods + [touche_finale])
    valide = (
        TOUCHES.fullmatch(touche_finale)
        and len(set(mods)) == len(mods)
        and all(mod in ("ctrl", "shift", "alt", "cmd") for mod in mods)
        and (systeme == "mac" or "cmd" not in mods)
        and not (systeme == "win" and mods and touche_finale.startswith("num") and touche_finale != "numenter")
        and resultat not in RESERVES
    )
    return resultat if valide else None


def charge_utile(fiche, action):
    parties = []
    windows = normaliser(action["win"], "win") if action.get("win") else None
    if windows:
        parties.append("win=" + windows)
    macos = normaliser(action["mac"], "mac") if action.get("mac") else None
    if macos:
        parties.append("mac=" + macos)
    linux = action.get("linux") or (action.get("win") if "linux" in fiche.get("systemes", []) else None)
    linux = normaliser(linux, "lin") if linux else None
    if linux:
        parties.append("lin=" + linux)
    return "touche:" + ";".join(parties) if parties else None


def touche(fiche, action):
    charge = charge_utile(fiche, action)
    if not charge:
        return None
    return {
        "id": f'{fiche["id"]}-{action["id"]}'[:64],
        "type": "keyboard",
        "name": action["nom"],
        "icon": picto(action.get("picto")),
        "color": couleur(action.get("groupe", "")),
        "payload": charge,
    }


def navigation(identifiant, nom, picto_nom):
    return {"id": identifiant, "type": "system", "payload": identifiant, "name": nom,
            "icon": picto(picto_nom), "color": "#3B82F6"}


def page(index, nom, touches, total):
    boutons = [{"id": case, "active": False, "action": None} for case in range(24)]
    for case, action in zip(CASES, touches):
        boutons[case] = {"id": case, "active": True, "action": action}
    if index > 0:
        boutons[GAUCHE] = {"id": GAUCHE, "active": True, "action": navigation("page-prev", "Page précédente", "chevron-left")}
    if index < total - 1:
        boutons[DROITE] = {"id": DROITE, "active": True, "action": navigation("page-next", "Page suivante", "chevron-right")}
    return {"page": index, "name": nom, "buttons": boutons}


def essentiel(fiche, actions):
    choix = sorted(actions, key=lambda action: action.get("priorite", 3))[:PAR_PAGE]
    ordre = {action["id"]: rang for rang, action in enumerate(actions)}
    choix.sort(key=lambda action: ordre[action["id"]])
    touches = [touche(fiche, action) for action in choix]
    return {"totalPages": 1, "pages": [page(0, "Essentiel", touches, 1)]}


def groupes(actions):
    rangees = {}
    for action in actions:
        rangees.setdefault(action.get("groupe") or "Divers", []).append(action)
    return rangees


def complet(fiche, actions):
    morceaux = []
    for nom, liste in groupes(actions).items():
        for debut in range(0, len(liste), PAR_PAGE):
            morceaux.append((nom, liste[debut:debut + PAR_PAGE]))
    # Les petits groupes voisins partagent une page plutôt que d'en gaspiller une.
    pages = []
    for nom, liste in morceaux:
        if pages and len(pages[-1][1]) + len(liste) <= PAR_PAGE:
            pages[-1] = (f"{pages[-1][0]} · {nom}"[:40], pages[-1][1] + liste)
        else:
            pages.append((nom, liste))
    pages = pages[:MAX_PAGES]
    return {
        "totalPages": len(pages),
        "pages": [page(index, nom, [touche(fiche, a) for a in liste], len(pages))
                  for index, (nom, liste) in enumerate(pages)],
    }


def modele(fiche, actions):
    base = essentiel(fiche, actions)
    avertissement = fiche.get("avertissement") or (
        "Ces raccourcis sont à définir d'abord dans l'application." if not fiche.get("raccourcis_par_defaut", True) else ""
    )
    return {
        "id": fiche["id"],
        "name": fiche["nom"][:80],
        "description": f'Les raccourcis de {fiche["nom"]} sur vos touches. {avertissement}'.strip()[:1000],
        "icon": logo(fiche),
        "author": "ClickDeck",
        "version": fiche.get("version", "1.0.1"),
        "createdAt": DATE,
        "updatedAt": DATE,
        "category": fiche.get("categorie") or CATEGORIES.get(re.split(r"[ ,]", fiche.get("section", ""))[0], "productivity"),
        "section": fiche.get("section", "Divers"),
        "tags": [fiche.get("editeur", "")] if fiche.get("editeur") else [],
        "minAppVersion": APP_MINIMALE,
        "config": base,
        "variants": [{"name": "Essentiel", "description": "Une page, le quotidien"},
                     {"name": "Complet", "description": "Toutes les fonctions, par thème"}],
        "variantConfigs": [base, complet(fiche, actions)],
    }


def plugin(fiche, actions):
    categories = []
    for index, (nom, liste) in enumerate(groupes(actions).items()):
        categories.append({
            "id": f'{fiche["id"]}-{index}'[:64],
            "name": nom,
            "icon": picto(liste[0].get("picto")),
            "expanded": False,
            "actions": [touche(fiche, action) for action in liste],
        })
    return {
        "id": fiche["id"],
        "name": fiche["nom"][:80],
        "icon": logo(fiche),
        "description": f'Toutes les touches de {fiche["nom"]} dans l\'éditeur.',
        "version": fiche.get("version", "1.0.1"),
        "author": "ClickDeck",
        "section": fiche.get("section", "Divers"),
        "minAppVersion": APP_MINIMALE,
        "categories": categories,
    }


def nom_de_lancement(fiche):
    lancement = fiche.get("lancement") or {}
    nom = lancement.get("windows") or lancement.get("mac") or fiche["nom"]
    return re.sub(r"[^\w ._+-]", "", re.sub(r"\(.*?\)", "", nom)).strip() or fiche["id"]


def pack(section, fiches):
    """Applications sans raccourcis utiles : une touche de lancement chacune."""
    identifiant = "pack-" + re.sub(r"[^a-z0-9]+", "-", section.lower().encode("ascii", "ignore").decode()).strip("-")
    touches = [{
        "id": f'lancer-{fiche["id"]}'[:64],
        "type": "app",
        "name": fiche["nom"][:18],
        "icon": logo(fiche),
        "color": "#64748B",
        "payload": nom_de_lancement(fiche),
    } for fiche in sorted(fiches, key=lambda fiche: fiche["nom"].lower())]
    morceaux = [touches[debut:debut + PAR_PAGE] for debut in range(0, len(touches), PAR_PAGE)][:MAX_PAGES]
    return {
        "id": identifiant[:64],
        "name": f"Lanceur : {section}"[:80],
        "description": "Une touche pour ouvrir chacune de ces applications, qui n'ont pas de raccourcis utiles.",
        "icon": picto("rocket"),
        "author": "ClickDeck",
        "version": "1.0.1",
        "createdAt": DATE,
        "updatedAt": DATE,
        "category": "productivity",
        "section": section,
        "tags": ["lanceur"],
        "minAppVersion": APP_MINIMALE,
        "config": {
            "totalPages": len(morceaux),
            "pages": [page(index, f"Page {index + 1}", liste, len(morceaux)) for index, liste in enumerate(morceaux)],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources", default=os.path.join(RACINE, "sources"))
    parser.add_argument("--sortie", default=RACINE)
    options = parser.parse_args()

    os.makedirs(os.path.join(options.sortie, "modeles"), exist_ok=True)
    os.makedirs(os.path.join(options.sortie, "plugins"), exist_ok=True)
    produits, vides = 0, []
    packs = {}
    for nom in sorted(os.listdir(options.sources)):
        if not nom.endswith(".json"):
            continue
        with open(os.path.join(options.sources, nom), encoding="utf-8") as fichier:
            fiche = json.load(fichier)
        actions = [action for action in fiche.get("actions", []) if charge_utile(fiche, action)]
        if len(actions) < MINIMUM_TOUCHES or (fiche.get("sans_raccourcis") and len(actions) < 2 * MINIMUM_TOUCHES):
            packs.setdefault(fiche.get("section", "Divers"), []).append(fiche)
            vides.append(fiche["id"])
            continue
        for dossier, contenu in (("modeles", modele(fiche, actions)), ("plugins", plugin(fiche, actions))):
            with open(os.path.join(options.sortie, dossier, f'{fiche["id"]}.json'), "w", encoding="utf-8") as fichier:
                json.dump(contenu, fichier, ensure_ascii=False, separators=(",", ":"))
        produits += 1
    for section, fiches in packs.items():
        contenu = pack(section, fiches)
        with open(os.path.join(options.sortie, "modeles", f'{contenu["id"]}.json'), "w", encoding="utf-8") as fichier:
            json.dump(contenu, fichier, ensure_ascii=False, separators=(",", ":"))
    print(f"{produits} applications générées, {len(vides)} en {len(packs)} packs de lancement")


if __name__ == "__main__":
    main()
