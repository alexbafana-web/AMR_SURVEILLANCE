import pandas as pd


def calculer_resistance_par_antibiotique(df):
    """Calcule le nombre de tests, le nombre de résultats résistants et le taux par antibiotique."""
    resume = (
        df.groupby("antibiotic")["phenotype"]
        .agg(
            echantillons_tests="count",
            echantillons_resistants=lambda x: (x == "Resistant").sum(),
        )
        .reset_index()
    )

    resume["taux_resistance_pct"] = (
        resume["echantillons_resistants"]
        / resume["echantillons_tests"]
        * 100
    ).round(1)

    return resume

def comparer_sites(df):
    comparaison = (
        df.groupby(["site", "antibiotic"])["phenotype"]
        .agg(
            echantillons_tests="count",
            echantillons_resistants=lambda x: (x == "Resistant").sum()
        )
        .reset_index()
    )

    comparaison["echantillons_resistants"] = pd.to_numeric(
        comparaison["echantillons_resistants"], errors="coerce"
    )
    comparaison["echantillons_tests"] = pd.to_numeric(
        comparaison["echantillons_tests"], errors="coerce"
    )

    comparaison["taux_resistance_pct"] = (
        comparaison["echantillons_resistants"]
        .div(comparaison["echantillons_tests"].replace(0, pd.NA))
        .mul(100)
        .round(1)
    )

    return comparaison
