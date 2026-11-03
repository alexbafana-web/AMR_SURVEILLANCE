import pandas as pd


def charger_donnees(chemin):
    """Charge un fichier CSV et retourne son contenu sous forme de tableau."""
    return pd.read_csv(chemin)
