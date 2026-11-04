#!/usr/bin/env python3
"""Réduit les PNG de `icones-prusaslicer/rendu/` à une palette de 32 couleurs (demande Pillow).

Jusqu'à l'application 1.18.7, les images partent aussi dans le message de
configuration, que le boîtier limite à 256 Ko. Les icônes sont en aplats : la
palette ne se voit pas.
"""
import os

from PIL import Image

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icones-prusaslicer", "rendu")

for nom in sorted(os.listdir(DOSSIER)):
    chemin = os.path.join(DOSSIER, nom)
    image = Image.open(chemin).convert("RGBA").quantize(colors=32, method=Image.Quantize.FASTOCTREE)
    image.save(chemin, optimize=True)
