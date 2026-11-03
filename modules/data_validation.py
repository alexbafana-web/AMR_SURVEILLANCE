import pandas as pd

COLONNES_REQUISES = [
    "sample_id",
    "site",
    "gene",
    "antibiotic",
    "bacterium",
    "phenotype",
]


def verifier_donnees(df):
    """Vérifie que le tableau contient les colonnes nécessaires."""
    erreurs = []

    colonnes_manquantes = [
        colonne
        for colonne in COLONNES_REQUISES
        if colonne not in df.columns
    ]

    if colonnes_manquantes:
        erreurs.append(
            "Colonnes manquantes : " + ", ".join(colonnes_manquantes)
        )

    if df.empty:
        erreurs.append("Le fichier ne contient aucune ligne de données.")

    return erreurs
