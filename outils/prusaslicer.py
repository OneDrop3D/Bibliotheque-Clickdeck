#!/usr/bin/env python3
"""Modèle et plugin PrusaSlicer, faits à la main pour les versions 2.9.x et 3.0.

Ce modèle ne passe pas par generer.py : chaque page a sa disposition, et les deux
versions n'ont ni les mêmes raccourcis ni les mêmes icônes. Tout vient du code
source de PrusaSlicer (voir SOURCES) et les icônes de l'application elle-même,
copiées dans outils/icones-prusaslicer/ (licence AGPL-3.0, voir le LISEZMOI du
dossier).

Pourquoi le pavé numérique en 3.0 : la 3.0 compare les modificateurs exactement.
Sur un clavier AZERTY, « 1 » demande Maj, donc la touche « 1 » ne déclencherait
rien. Le pavé numérique y est déclaré en plus, et n'a pas ce problème.
La 2.9 lit le caractère reçu : les chiffres et « + » y fonctionnent normalement.

    python3 outils/prusaslicer.py            # écrit modeles/ et plugins/
    python3 outils/prusaslicer.py --copier   # recopie les icônes depuis les applications
"""

import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generer import APP_MINIMALE, DATE, DROITE, GAUCHE, RACINE, data_uri  # noqa: E402

VERSION = "1.1.0"
ID = "prusaslicer"
FOND = "#262626"       # fond sombre de PrusaSlicer : les icônes y sont lisibles
FOND_NAVIGATION = "#ED6B21"
DOSSIER_ICONES = os.path.join(RACINE, "outils", "icones-prusaslicer")
APPLICATIONS = {
    "2.9": "/Applications/Original Prusa Drivers/PrusaSlicer.app/Contents/Resources/icons",
    "3.0": "/Applications/PrusaSlicer-3.0.0-alpha12.app/Contents/Resources/icons",
}
SOURCES = [
    "https://github.com/prusa3d/PrusaSlicer/blob/version_2.9.7/src/slic3r/GUI/KBShortcutsDialog.cpp",
    "https://github.com/prusa3d/PrusaSlicer/blob/version_2.9.7/src/slic3r/GUI/GLCanvas3D.cpp",
    "https://github.com/prusa3d/PrusaSlicer/blob/version_3.0.0-alpha13/src/slic3r-shared/src/Slic3r/App/MenuCommandRegistrar.cpp",
    "https://github.com/prusa3d/PrusaSlicer/blob/version_3.0.0-alpha13/src/slic3r-shared/src/Slic3r/App/Plater/ToolGizmosUiInfo.cpp",
]


# --- Raccourcis ------------------------------------------------------------

def tous(touche):
    """Même touche partout, sans modificateur."""
    return {"win": touche, "mac": touche, "lin": touche}


def ctrl(touche):
    """Ctrl sous Windows et Linux, Cmd sur Mac."""
    return {"win": f"ctrl+{touche}", "mac": f"cmd+{touche}", "lin": f"ctrl+{touche}"}


SUPPRIMER = {"win": "delete", "mac": "backspace", "lin": "delete"}
TOUT_SUPPRIMER = {"win": "ctrl+delete", "mac": "cmd+backspace", "lin": "ctrl+delete"}
PREFERENCES = {"win": "ctrl+p", "mac": "cmd+comma", "lin": "ctrl+p"}
PLEIN_ECRAN_29 = {"win": "f11", "mac": "ctrl+cmd+f", "lin": "f11"}
PLEIN_ECRAN_30 = {"win": "f11", "lin": "f11"}   # la 3.0 ne déclare rien sur Mac


def couleur_30(numero):
    """Couleur de peinture : Maj + chiffre, ou Maj + pavé sur Mac (voir en-tête)."""
    return {"win": f"shift+{numero}", "mac": f"shift+num{numero}", "lin": f"shift+{numero}"}


# --- Touches ---------------------------------------------------------------
# (identifiant, nom affiché, raccourci, icône). L'icône est un fichier de
# l'application, ou « vue-… » pour les vues, que PrusaSlicer n'illustre pas.

T29 = {
    "nouveau": ("Nouveau", ctrl("n"), "add"),
    "ouvrir": ("Ouvrir", ctrl("o"), "open"),
    "sauver": ("Enregistrer", ctrl("s"), "save"),
    "sauver-sous": ("Enregistrer sous", {"win": "ctrl+alt+s", "mac": "cmd+shift+s", "lin": "ctrl+alt+s"}, "export_plater"),
    "importer": ("Importer modèle", ctrl("i"), "import_plater"),
    "importer-config": ("Importer réglages", ctrl("l"), "import_config"),
    "importer-projet": ("Réglages projet", {"win": "ctrl+alt+l", "mac": "cmd+alt+l", "lin": "ctrl+alt+l"}, "import_config_bundle"),
    "exporter-config": ("Exporter réglages", ctrl("e"), "export_config"),
    "decouper": ("Découper", ctrl("r"), "re_slice"),
    "gcode": ("Exporter G-code", ctrl("g"), "export_gcode"),
    "envoyer": ("Envoyer G-code", ctrl("shift+g"), "connect_gcode"),
    "carte": ("Vers carte SD", ctrl("u"), "export_to_sd"),
    "ejecter": ("Éjecter carte SD", ctrl("t"), "eject_sd"),
    "file": ("File d'envoi", ctrl("j"), "upload_queue"),
    "instance-appli": ("Nouvelle fenêtre", ctrl("shift+i"), "editor"),
    "recharger": ("Recharger", tous("f5"), "refresh"),
    "preferences": ("Préférences", PREFERENCES, "cog"),
    "chercher": ("Chercher", ctrl("f"), "search"),
    "annuler": ("Annuler", ctrl("z"), "undo"),
    "retablir": ("Rétablir", ctrl("y"), "redo"),
    "tout": ("Tout sélectionner", ctrl("a"), "check_on"),
    "aucun": ("Désélectionner", tous("escape"), "cross"),
    "supprimer": ("Supprimer", SUPPRIMER, "remove"),
    "tout-supprimer": ("Tout supprimer", TOUT_SUPPRIMER, "delete_all"),
    "copier": ("Copier", ctrl("c"), "copy"),
    "coller": ("Coller", ctrl("v"), "paste"),
    "organiser": ("Organiser", tous("a"), "arrange"),
    "organiser-sel": ("Organiser sél.", tous("shift+a"), "arrange"),
    "organiser-plateau": ("Organiser plateau", tous("d"), "arrange_current"),
    "organiser-plateau-sel": ("Sélection plateau", tous("shift+d"), "arrange_current"),
    "plus": ("Ajouter copie", tous("plus"), "instance_add"),
    "moins": ("Retirer copie", tous("minus"), "instance_remove"),
    "haut10": ("Y + 10 mm", tous("up"), "thumb_up"),
    "bas10": ("Y − 10 mm", tous("down"), "thumb_down"),
    "gauche10": ("X − 10 mm", tous("left"), "thumb_left"),
    "droite10": ("X + 10 mm", tous("right"), "thumb_right"),
    "haut1": ("Y + 1 mm", tous("shift+up"), "thumb_up"),
    "bas1": ("Y − 1 mm", tous("shift+down"), "thumb_down"),
    "gauche1": ("X − 1 mm", tous("shift+left"), "thumb_left"),
    "droite1": ("X + 1 mm", tous("shift+right"), "thumb_right"),
    "pivot-gauche": ("Pivoter à gauche", tous("pageup"), "undo_toolbar"),
    "pivot-droite": ("Pivoter à droite", tous("pagedown"), "redo_toolbar"),
    "o-deplacer": ("Déplacer", tous("m"), "move"),
    "o-echelle": ("Échelle", tous("s"), "scale"),
    "o-rotation": ("Rotation", tous("r"), "rotate"),
    "o-poser": ("Poser sur face", tous("f"), "place"),
    "o-couper": ("Couper", tous("c"), "cut"),
    "o-mesurer": ("Mesurer", tous("u"), "measure"),
    "o-supports": ("Peindre supports", tous("l"), "fdm_supports"),
    "o-couture": ("Peindre couture", tous("p"), "seam"),
    "o-rugueux": ("Peau rugueuse", tous("h"), "fuzzy_skin_painting"),
    "o-multi": ("Multimatériau", tous("n"), "mmu_segmentation"),
    "o-texte": ("Texte en relief", tous("t"), "add_text_part"),
    "o-sla": ("Supports SLA", tous("l"), "sla_supports"),
    "o-evider": ("Évider SLA", tous("h"), "hollow"),
    "o-quitter": ("Quitter l'outil", tous("escape"), "cross"),
    "o-ajuster": ("Ajuster au volume", tous("f"), "scale"),
    "v-iso": ("Iso", tous("0"), "vue-iso"),
    "v-dessus": ("Dessus", tous("1"), "vue-dessus"),
    "v-dessous": ("Dessous", tous("2"), "vue-dessous"),
    "v-avant": ("Avant", tous("3"), "vue-avant"),
    "v-arriere": ("Arrière", tous("4"), "vue-arriere"),
    "v-gauche": ("Gauche", tous("5"), "vue-gauche"),
    "v-droite": ("Droite", tous("6"), "vue-droite"),
    "zoom-plus": ("Zoom avant", tous("i"), "search"),
    "zoom-moins": ("Zoom arrière", tous("o"), "search_gray"),
    "zoom-plateau": ("Voir le plateau", tous("b"), "plater"),
    "zoom-selection": ("Voir la sélection", tous("z"), "search_"),
    "camera": ("Perspective", tous("k"), "vue-iso"),
    "etiquettes": ("Étiquettes", tous("e"), "number_of_copies"),
    "bascule": ("Plateau / aperçu", tous("tab"), "preview"),
    "barre": ("Barre latérale", tous("shift+tab"), "collapse"),
    "plein-ecran": ("Plein écran", PLEIN_ECRAN_29, "expand_btn"),
    "onglet-plateau": ("Plateau", ctrl("1"), "plater"),
    "onglet-impression": ("Réglages impr.", ctrl("2"), "cog"),
    "onglet-filament": ("Filament", ctrl("3"), "spool"),
    "onglet-imprimante": ("Imprimante", ctrl("4"), "printer"),
    "onglet-3d": ("Vue 3D", ctrl("5"), "editor"),
    "onglet-apercu": ("Aperçu", ctrl("6"), "preview"),
    "a-haut": ("Couche suivante", tous("up"), "thumb_up"),
    "a-bas": ("Couche précéd.", tous("down"), "thumb_down"),
    "a-haut5": ("5 couches +", tous("shift+up"), "thumb_up"),
    "a-bas5": ("5 couches −", tous("shift+down"), "thumb_down"),
    "a-gauche": ("Trajet −", tous("left"), "thumb_left"),
    "a-droite": ("Trajet +", tous("right"), "thumb_right"),
    "a-gauche5": ("Trajet − 5", tous("shift+left"), "thumb_left"),
    "a-droite5": ("Trajet + 5", tous("shift+right"), "thumb_right"),
    "a-couche": ("Aller à la couche", tous("shift+g"), "edit_layers_all"),
    "a-seule": ("Couche seule", tous("x"), "layers"),
    "a-legende": ("Légende", tous("l"), "legend_cog"),
    "a-fenetre": ("Fenêtre G-code", tous("c"), "custom-gcode_gcode"),
    "a-couleur": ("Changer couleur", tous("plus"), "colorchange_add"),
    "a-couleur-moins": ("Retirer couleur", tous("minus"), "colorchange_del"),
}

T30 = {
    "nouveau": ("Nouveau", ctrl("n"), "tb_new"),
    "ouvrir": ("Ouvrir", ctrl("o"), "open_folder"),
    "sauver": ("Enregistrer", ctrl("s"), "tb_save"),
    "sauver-sous": ("Enregistrer sous", ctrl("shift+s"), "tb_save"),
    "importer": ("Importer modèle", ctrl("i"), "cube_add"),
    "gcode": ("Exporter G-code", ctrl("g"), "save_print_to_local"),
    "envoyer": ("Envoyer G-code", ctrl("shift+g"), "connect_gcode"),
    "carte": ("Vers clé USB", ctrl("u"), "save_print_to_flash"),
    "preferences": ("Préférences", PREFERENCES, "cog_wx"),
    "chercher": ("Chercher", ctrl("f"), "search"),
    "annuler": ("Annuler", ctrl("z"), "tb_undo"),
    "retablir": ("Rétablir", ctrl("y"), "tb_redo"),
    "tout": ("Tout sélectionner", ctrl("a"), "check_on"),
    "aucun": ("Désélectionner", tous("escape"), "cross_new"),
    "supprimer": ("Supprimer", SUPPRIMER, "delete_button"),
    "copier": ("Copier", ctrl("c"), "copy"),
    "coller": ("Coller", ctrl("v"), "paste"),
    "organiser": ("Tout organiser", tous("a"), "layout"),
    "organiser-sel": ("Organiser sél.", tous("shift+a"), "layout"),
    "organiser-plateau": ("Organiser plateau", tous("d"), "bed"),
    "organiser-plateau-sel": ("Sélection plateau", tous("shift+d"), "bed"),
    "plus": ("Ajouter copie", tous("numplus"), "instance_add"),
    "moins": ("Retirer copie", tous("numminus"), "instance_remove"),
    "o-deplacer": ("Déplacer", tous("m"), "move"),
    "o-rotation": ("Rotation", tous("r"), "rotate"),
    "o-echelle": ("Échelle", tous("s"), "scale"),
    "o-poser": ("Poser sur face", tous("f"), "place"),
    "o-simplifier": ("Simplifier", tous("e"), "simplify"),
    "o-organiser": ("Outil Organiser", tous("q"), "layout"),
    "o-supports": ("Peindre supports", tous("l"), "paint_supports"),
    "o-couture": ("Peindre couture", tous("p"), "paint_seams"),
    "o-rugueux": ("Peau rugueuse", tous("h"), "paint_fuzzy_skin"),
    "o-multi": ("Multimatériau", tous("n"), "paint_multi_material"),
    "o-texte": ("Texte en relief", tous("t"), "text"),
    "o-svg": ("Image SVG", tous("g"), "toolbar_svg"),
    "o-mesurer": ("Mesurer", tous("u"), "ruler"),
    "o-couper": ("Couper", tous("c"), "cut"),
    "o-hauteur": ("Hauteur variable", tous("v"), "variable_layer_height"),
    "o-plages": ("Plages de hauteur", tous("w"), "height_range"),
    "o-sla": ("Supports SLA", tous("l"), "support"),
    "o-evider": ("Évider SLA", tous("h"), "hollowing"),
    "o-quitter": ("Quitter l'outil", tous("escape"), "close_gizmo"),
    "c-inverser": ("Inverser couleurs", tous("x"), "switch"),
    "c-plage": ("Ajouter plage", tous("h"), "plus_height_range"),
    "c-copier": ("Copier réglages", ctrl("c"), "copy_for_gizmo"),
    "c-coller": ("Coller réglages", ctrl("v"), "paste"),
    "c-mesure": ("Retirer mesure", tous("backspace"), "key_backspace"),
    "c-point-suppr": ("Retirer point", tous("delete"), "delete_button"),
    "c-point-tout": ("Tous les points", ctrl("a"), "check_on"),
    "c-valider": ("Valider", tous("enter"), "tick_mark"),
    "v-iso": ("Iso", tous("num0"), "vue-iso"),
    "v-dessus": ("Dessus", tous("num1"), "vue-dessus"),
    "v-dessous": ("Dessous", tous("num2"), "vue-dessous"),
    "v-avant": ("Avant", tous("num3"), "vue-avant"),
    "v-arriere": ("Arrière", tous("num4"), "vue-arriere"),
    "v-gauche": ("Gauche", tous("num5"), "vue-gauche"),
    "v-droite": ("Droite", tous("num6"), "vue-droite"),
    "zoom-plus": ("Zoom avant", tous("i"), "plus"),
    "zoom-moins": ("Zoom arrière", tous("o"), "minus"),
    "zoom-plateau": ("Voir le plateau", tous("b"), "bed"),
    "camera": ("Perspective", tous("k"), "vue-iso"),
    "bascule": ("Plateau / aperçu", tous("tab"), "preview"),
    "plein-ecran": ("Plein écran", PLEIN_ECRAN_30, "expand_btn"),
    "a-haut": ("Couche suivante", tous("up"), "thumb_up"),
    "a-bas": ("Couche précéd.", tous("down"), "thumb_down"),
    "a-haut-moyen": ("Couches + vite", tous("shift+up"), "thumb_up"),
    "a-bas-moyen": ("Couches − vite", tous("shift+down"), "thumb_down"),
    "a-haut-vite": ("Couches ++ vite", ctrl("up"), "thumb_up"),
    "a-bas-vite": ("Couches −− vite", ctrl("down"), "thumb_down"),
    "a-gauche": ("Trajet −", tous("left"), "thumb_left"),
    "a-droite": ("Trajet +", tous("right"), "thumb_right"),
    "a-gauche-moyen": ("Trajet − vite", tous("shift+left"), "thumb_left"),
    "a-droite-moyen": ("Trajet + vite", tous("shift+right"), "thumb_right"),
    "a-gauche-vite": ("Trajet −− vite", ctrl("left"), "thumb_left"),
    "a-droite-vite": ("Trajet ++ vite", ctrl("right"), "thumb_right"),
    "a-couche": ("Aller à la couche", tous("shift+g"), "layers_inspect"),
    "a-marque": ("Ajouter repère", tous("numplus"), "colorchange_add"),
    "a-marque-moins": ("Retirer repère", tous("numminus"), "colorchange_del"),
}
for numero in range(1, 9):
    T30[f"c-couleur{numero}"] = (f"Couleur {numero}", couleur_30(numero), "palette")


# --- Pages -----------------------------------------------------------------
# Quatre rangées de six cases. Les cases 18 et 23 servent à changer de page.

_ = None

PAGES_29 = [
    ("Projet", [
        "nouveau", "ouvrir", "sauver", "sauver-sous", "importer", "recharger",
        "decouper", "gcode", "envoyer", "carte", "ejecter", "file",
        "annuler", "retablir", "chercher", "importer-config", "importer-projet", "exporter-config",
        _, "preferences", "instance-appli", _, _, _,
    ]),
    ("Plateau", [
        "tout", "aucun", "supprimer", "tout-supprimer", "copier", "coller",
        "organiser", "organiser-sel", "organiser-plateau", "organiser-plateau-sel", "plus", "moins",
        "annuler", "retablir", "zoom-plateau", "zoom-selection", "etiquettes", "bascule",
        _, _, _, _, _, _,
    ]),
    ("Déplacer", [
        _, "haut10", _, _, "haut1", _,
        "gauche10", "aucun", "droite10", "gauche1", _, "droite1",
        _, "bas10", _, _, "bas1", _,
        _, "pivot-gauche", "pivot-droite", "annuler", "retablir", _,
    ]),
    ("Outils", [
        "o-deplacer", "o-echelle", "o-rotation", "o-poser", "o-couper", "o-mesurer",
        "o-supports", "o-couture", "o-rugueux", "o-multi", "o-texte", "o-quitter",
        "o-sla", "o-evider", "o-ajuster", _, "annuler", "retablir",
        _, _, _, _, _, _,
    ]),
    ("Vue", [
        "v-iso", "v-dessus", "v-dessous", "v-avant", "v-arriere", "v-gauche",
        "v-droite", "zoom-plus", "zoom-moins", "zoom-plateau", "zoom-selection", "camera",
        "onglet-plateau", "onglet-impression", "onglet-filament", "onglet-imprimante", "onglet-3d", "onglet-apercu",
        _, "etiquettes", "bascule", "barre", "plein-ecran", _,
    ]),
    ("Aperçu", [
        "a-haut", "a-bas", "a-haut5", "a-bas5", "a-couche", "a-seule",
        "a-gauche", "a-droite", "a-gauche5", "a-droite5", "a-legende", "a-fenetre",
        "a-couleur", "a-couleur-moins", "decouper", "gcode", "envoyer", "carte",
        _, "bascule", _, _, _, _,
    ]),
]

ESSENTIEL_29 = [
    "ouvrir", "sauver", "importer", "annuler", "retablir", "supprimer",
    "o-deplacer", "o-echelle", "o-rotation", "o-poser", "o-couper", "o-mesurer",
    "organiser", "plus", "moins", "o-supports", "o-couture", "o-multi",
    _, "decouper", "gcode", "envoyer", "bascule", _,
]

PAGES_30 = [
    ("Projet", [
        "nouveau", "ouvrir", "sauver", "sauver-sous", "importer", "preferences",
        "gcode", "envoyer", "carte", "chercher", "annuler", "retablir",
        _, _, _, _, _, _,
        _, _, _, _, _, _,
    ]),
    ("Plateau", [
        "tout", "aucun", "supprimer", "copier", "coller", "bascule",
        "organiser", "organiser-sel", "organiser-plateau", "organiser-plateau-sel", "plus", "moins",
        "annuler", "retablir", "zoom-plateau", _, _, _,
        _, _, _, _, _, _,
    ]),
    ("Outils", [
        "o-deplacer", "o-rotation", "o-echelle", "o-poser", "o-simplifier", "o-organiser",
        "o-supports", "o-couture", "o-rugueux", "o-multi", "o-texte", "o-svg",
        "o-mesurer", "o-couper", "o-hauteur", "o-plages", "o-sla", "o-evider",
        _, "annuler", "retablir", "o-quitter", _, _,
    ]),
    ("Dans les outils", [
        "c-couleur1", "c-couleur2", "c-couleur3", "c-couleur4", "c-inverser", "c-plage",
        "c-couleur5", "c-couleur6", "c-couleur7", "c-couleur8", "c-copier", "c-coller",
        "c-mesure", "c-point-suppr", "c-point-tout", "c-valider", _, "o-quitter",
        _, _, _, _, _, _,
    ]),
    ("Vue", [
        "v-iso", "v-dessus", "v-dessous", "v-avant", "v-arriere", "v-gauche",
        "v-droite", "zoom-plus", "zoom-moins", "zoom-plateau", "camera", "bascule",
        "plein-ecran", _, _, _, _, _,
        _, _, _, _, _, _,
    ]),
    ("Aperçu", [
        "a-haut", "a-bas", "a-haut-moyen", "a-bas-moyen", "a-haut-vite", "a-bas-vite",
        "a-gauche", "a-droite", "a-gauche-moyen", "a-droite-moyen", "a-gauche-vite", "a-droite-vite",
        "a-couche", "a-marque", "a-marque-moins", "gcode", "envoyer", "bascule",
        _, _, _, _, _, _,
    ]),
]

ESSENTIEL_30 = [
    "ouvrir", "sauver", "importer", "annuler", "retablir", "supprimer",
    "o-deplacer", "o-rotation", "o-echelle", "o-poser", "o-couper", "o-mesurer",
    "organiser", "plus", "moins", "o-supports", "o-couture", "o-multi",
    _, "gcode", "envoyer", "carte", "bascule", _,
]


# --- Icônes ----------------------------------------------------------------

def cube(face):
    """Cube isométrique, la face regardée en orange : PrusaSlicer n'a pas d'icône de vue."""
    p = {"a": (48, 12), "b": (84, 30), "c": (48, 48), "d": (12, 30),
         "e": (12, 68), "f": (48, 86), "g": (84, 68), "h": (48, 50)}
    faces = {"dessus": "abcd", "avant": "dcfe", "droite": "cbgf",
             "dessous": "ehgf", "arriere": "abgh", "gauche": "adeh"}
    points = lambda lettres: " ".join(f"{p[l][0]},{p[l][1]}" for l in lettres)
    cachees = ""
    if face in ("dessous", "arriere", "gauche"):
        cachees = '<path d="M48 50V12M48 50L12 68M48 50L84 68" fill="none" stroke="#fff" stroke-width="3" stroke-dasharray="5 5" opacity=".55"/>'
    contour = (f'<polygon points="{points("abgfed")}" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round"/>'
               '<path d="M12 30L48 48L84 30M48 48V86" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round"/>')
    if face == "iso":
        pleines = "".join(f'<polygon points="{points(faces[nom])}" fill="#ED6B21" opacity="{o}"/>'
                          for nom, o in (("dessus", 1), ("avant", .75), ("droite", .5)))
    else:
        cachee = face in ("dessous", "arriere", "gauche")
        pleines = f'<polygon points="{points(faces[face])}" fill="#ED6B21"{" opacity=\".8\"" if cachee else ""}/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">{pleines}{cachees}{contour}</svg>'


def nettoyer(svg):
    """Comme PrusaSlicer en thème sombre : le gris passe en blanc. Sans ce qui ne s'affiche pas."""
    svg = re.sub(r"<\?xml.*?\?>|<!--.*?-->|<!DOCTYPE.*?>|<metadata.*?</metadata>|<title.*?</title>", "", svg, flags=re.S | re.I)
    svg = re.sub(r"#808080", "#FFFFFF", svg, flags=re.I)
    svg = re.sub(r">\s+<", "><", svg).strip()
    entete = re.match(r"<svg\b[^>]*>", svg, flags=re.S).group(0)
    largeur = re.search(r'\bwidth="([\d.]+)', entete)
    hauteur = re.search(r'\bheight="([\d.]+)', entete)
    if "viewBox" not in entete and largeur and hauteur:
        svg = svg.replace("<svg", f'<svg viewBox="0 0 {largeur.group(1)} {hauteur.group(1)}"', 1)
    entete = re.match(r"<svg\b[^>]*>", svg, flags=re.S).group(0)
    propre = re.sub(r'\s(width|height|x|y|id|style|enable-background|xml:space|version|xmlns:xlink)="[^"]*"', "", entete)
    propre = propre.replace("<svg", '<svg width="96" height="96"', 1)
    if "xmlns=" not in propre:
        propre = propre.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return svg.replace(entete, propre, 1)


def icone(version, nom):
    if nom.startswith("vue-"):
        return data_uri(cube(nom[4:]))
    with open(os.path.join(DOSSIER_ICONES, version, f"{nom}.svg"), encoding="utf-8") as fichier:
        return data_uri(nettoyer(fichier.read()))


# --- Construction ----------------------------------------------------------

def charge(raccourci):
    return "touche:" + ";".join(f"{systeme}={raccourci[systeme]}" for systeme in ("win", "mac", "lin") if systeme in raccourci)


def action(version, touches, cle):
    nom, raccourci, image = touches[cle]
    return {"id": f"prusaslicer-{version.replace('.', '')}-{cle}"[:64], "type": "keyboard", "name": nom,
            "icon": icone(version, image), "color": FOND, "payload": charge(raccourci)}


def navigation(identifiant, nom, image):
    return {"id": identifiant, "type": "system", "payload": identifiant, "name": nom,
            "icon": icone("3.0", image), "color": FOND_NAVIGATION}


def page(version, touches, index, nom, grille, total):
    assert len(grille) == 24, nom
    assert grille[GAUCHE] is None and grille[DROITE] is None, nom
    boutons = [{"id": case, "active": False, "action": None} for case in range(24)]
    for case, cle in enumerate(grille):
        if cle:
            boutons[case] = {"id": case, "active": True, "action": action(version, touches, cle)}
    if index > 0:
        boutons[GAUCHE] = {"id": GAUCHE, "active": True, "action": navigation("page-prev", "Page précédente", "chevron_left")}
    if index < total - 1:
        boutons[DROITE] = {"id": DROITE, "active": True, "action": navigation("page-next", "Page suivante", "chevron_right")}
    return {"page": index, "name": nom, "buttons": boutons}


def configuration(version, touches, pages):
    return {"totalPages": len(pages),
            "pages": [page(version, touches, index, nom, grille, len(pages)) for index, (nom, grille) in enumerate(pages)]}


def modele():
    essentiel_29 = configuration("2.9", T29, [("Essentiel", ESSENTIEL_29)])
    # L'ordre des variantes ne bouge pas : une mise à jour retrouve la variante par son rang.
    return {
        "id": ID,
        "name": "PrusaSlicer",
        "description": ("Pages faites pour PrusaSlicer 2.9.x et 3.0, avec les icônes de l'application. Les deux versions "
                        "n'ont pas les mêmes raccourcis : choisissez la vôtre. Raccourcis relevés dans le code source "
                        "des versions 2.9.7 et 3.0.0-alpha13 ; la 3.0 finale pourra différer. "
                        "Icônes © Prusa Research, licence AGPL-3.0."),
        "icon": logo(),
        "author": "ClickDeck",
        "version": VERSION,
        "createdAt": DATE,
        "updatedAt": DATE,
        "category": "productivity",
        "section": "3D, CAO & impression 3D",
        "tags": ["Prusa Research", "Impression 3D", "2.9", "3.0"],
        "minAppVersion": APP_MINIMALE,
        "config": essentiel_29,
        "variants": [
            {"name": "2.9.x Essentiel", "description": "Une page, le quotidien"},
            {"name": "2.9.x Complet", "description": "Six pages : projet, plateau, déplacer, outils, vue, aperçu"},
            {"name": "3.0 Essentiel", "description": "Une page, le quotidien"},
            {"name": "3.0 Complet", "description": "Six pages, avec les nouveaux outils de la 3.0"},
        ],
        "variantConfigs": [
            essentiel_29,
            configuration("2.9", T29, PAGES_29),
            configuration("3.0", T30, [("Essentiel", ESSENTIEL_30)]),
            configuration("3.0", T30, PAGES_30),
        ],
    }


def logo():
    with open(os.path.join(DOSSIER_ICONES, "2.9", "PrusaSlicer.svg"), encoding="utf-8") as fichier:
        return data_uri(re.sub(r">\s+<", "><", fichier.read()).strip())


def categories(version, touches, pages):
    resultat, vues = [], set()
    for nom, grille in pages:
        cles = [cle for cle in grille if cle and cle not in vues]
        vues.update(cles)
        if cles:
            resultat.append({"id": f"prusaslicer-{version.replace('.', '')}-{len(resultat)}", "name": f"{version} · {nom}",
                             "icon": icone(version, touches[cles[0]][2]), "expanded": False,
                             "actions": [action(version, touches, cle) for cle in cles]})
    return resultat


def plugin():
    return {
        "id": ID,
        "name": "PrusaSlicer",
        "icon": logo(),
        "description": "Toutes les touches de PrusaSlicer 2.9.x et 3.0 dans l'éditeur, avec les icônes de l'application.",
        "version": VERSION,
        "author": "ClickDeck",
        "section": "3D, CAO & impression 3D",
        "minAppVersion": APP_MINIMALE,
        "categories": categories("2.9", T29, PAGES_29) + categories("3.0", T30, PAGES_30),
    }


def icones_utilisees():
    for version, touches in (("2.9", T29), ("3.0", T30)):
        for _nom, _raccourci, image in touches.values():
            if not image.startswith("vue-"):
                yield version, image
    yield "3.0", "chevron_left"
    yield "3.0", "chevron_right"
    yield "2.9", "PrusaSlicer"


def copier():
    for version, nom in sorted(set(icones_utilisees())):
        dossier = os.path.join(DOSSIER_ICONES, version)
        os.makedirs(dossier, exist_ok=True)
        shutil.copy(os.path.join(APPLICATIONS[version], f"{nom}.svg"), dossier)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--copier", action="store_true", help="recopie les icônes depuis les applications installées")
    parser.add_argument("--sortie", default=RACINE)
    options = parser.parse_args()
    if options.copier:
        copier()
    for dossier, contenu in (("modeles", modele()), ("plugins", plugin())):
        chemin = os.path.join(options.sortie, dossier, f"{ID}.json")
        with open(chemin, "w", encoding="utf-8") as fichier:
            json.dump(contenu, fichier, ensure_ascii=False, separators=(",", ":"))
        print(chemin, os.path.getsize(chemin))


if __name__ == "__main__":
    main()
