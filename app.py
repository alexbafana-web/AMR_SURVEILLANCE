import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
from reportlab.platypus import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from modules.data_validation import verifier_donnees
from modules.data_loader import charger_donnees
from modules.analysis import calculer_resistance_par_antibiotique, comparer_sites
st.set_page_config(
    page_title="AMR Surveillance Platform",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 AMR-SCOPE")
st.subheader("Antimicrobial Resistance Surveillance: Phenotypic and Genomic Monitoring")

st.write(
    "Cette plateforme permet d'explorer les données de surveillance "
    "de la résistance aux antimicrobiens."
)

# Chargement des données de démonstration
data_path = "data/demo_amr.csv"
df = charger_donnees(data_path)
erreurs = verifier_donnees(df)

if erreurs:
    st.error("Les données ne sont pas valides :")
    for erreur in erreurs:
        st.write(f"- {erreur}")
    st.stop()

st.info("Données fictives de démonstration — elles ne représentent pas des résultats réels.")

# Indicateurs principaux
col1, col2, col3 = st.columns(3)

col1.metric("Échantillons", df["sample_id"].nunique())
col2.metric("Sites", df["site"].nunique())
col3.metric("Gènes détectés", df.loc[df["gene"] != "", "gene"].nunique())

st.header("Filtrer les données")

sites = ["Tous"] + sorted(df["site"].dropna().unique().tolist())
site_choisi = st.selectbox("Choisir un site :", sites)

antibiotiques = ["Tous"] + sorted(df["antibiotic"].dropna().unique().tolist())
antibiotique_choisi = st.selectbox("Choisir un antibiotique :", antibiotiques)

bacteries = ["Toutes"] + sorted(df["bacterium"].dropna().unique().tolist())
bacterie_choisie = st.selectbox("Choisir une bactérie :", bacteries)
phenotypes = ["Tous"] + sorted(df["phenotype"].dropna().unique().tolist())
phenotype_choisi = st.selectbox("Choisir un phénotype :", phenotypes)

df_filtre = df.copy()

if site_choisi != "Tous":
    df_filtre = df_filtre[df_filtre["site"] == site_choisi]

if antibiotique_choisi != "Tous":
    df_filtre = df_filtre[df_filtre["antibiotic"] == antibiotique_choisi]

if bacterie_choisie != "Toutes":
    df_filtre = df_filtre[df_filtre["bacterium"] == bacterie_choisie]
if phenotype_choisi != "Tous":
    df_filtre = df_filtre[df_filtre["phenotype"] == phenotype_choisi]

st.metric("Échantillons correspondant aux filtres", len(df_filtre))
if len(df_filtre) > 0:
    taux_resistance = (
        (df_filtre["phenotype"] == "Resistant").sum()
        / len(df_filtre)
    ) * 100

    st.metric("Taux de résistance", f"{taux_resistance:.1f} %")
else:
    st.metric("Taux de résistance", "—")
st.download_button(
    label="Télécharger les données filtrées (CSV)",
    data=df_filtre.to_csv(index=False).encode("utf-8"),
    file_name="donnees_amr_filtrees.csv",
    mime="text/csv"
)
st.header("Aperçu des données")
st.dataframe(df_filtre, width="stretch")

st.header("Résistance par antibiotique")
resistant = df_filtre[df_filtre["phenotype"] == "Resistant"]

st.subheader("Taux de résistance par antibiotique")

st.subheader("Taux de résistance par antibiotique")

resume = calculer_resistance_par_antibiotique(df_filtre)

st.dataframe(resume, width="stretch")

if df_filtre.empty:
    st.warning("Aucun résultat pour cette combinaison de filtres.")
else:
    st.bar_chart(
        resume,
        x="antibiotic",
        y="taux_resistance_pct"
    )

st.caption("Résultats calculés uniquement à partir des données actuellement filtrées.")

st.header("Comparaison des sites")

comparaison = comparer_sites(df_filtre)

st.dataframe(comparaison, width="stretch")

st.subheader("Taux de résistance par site et antibiotique")
st.caption(
    "Pourcentage de résultats résistants parmi les tests disponibles, "
    "selon les filtres sélectionnés."
)
if comparaison.empty:
    st.warning("Aucun résultat à comparer pour les filtres sélectionnés.")
else:
    st.bar_chart(
        comparaison,
        x="site",
        y="taux_resistance_pct",
        color="antibiotic"
    )
def creer_rapport_pdf(df):
    tampon = BytesIO()

    document = SimpleDocTemplate(
        tampon,
        pagesize=A4,
        title="Rapport AMR-Scope"
    )

    styles = getSampleStyleSheet()
    contenu = []

    contenu.append(Paragraph("AMR-Scope — Rapport de surveillance", styles["Title"]))
    contenu.append(Spacer(1, 12))
    contenu.append(Paragraph(
        "Rapport généré à partir des données actuellement filtrées.",
        styles["BodyText"]
    ))
    contenu.append(Spacer(1, 12))
    contenu.append(Paragraph("Taux de résistance par antibiotique", styles["Heading2"]))

    resume_pdf = (
        df.groupby("antibiotic")["phenotype"]
        .agg(
            tests="count",
            resistants=lambda x: (x == "Resistant").sum()
        )
        .reset_index()
    )
    resume_pdf["etiquette"] = (
    resume_pdf["antibiotic"]
    + " ("
    + resume_pdf["tests"].astype(str)
    + " tests)"
    )

    resume_pdf["taux_pct"] = (
        resume_pdf["resistants"] / resume_pdf["tests"] * 100
    )

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(resume_pdf["etiquette"], resume_pdf["taux_pct"])
    ax.set_ylabel("Résistance (%)")
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    image_graphique = BytesIO()
    fig.savefig(image_graphique, format="png", dpi=150)
    plt.close(fig)
    image_graphique.seek(0)

    contenu.append(Image(image_graphique, width=450, height=225))
    contenu.append(Spacer(1, 12))

    donnees = [df.columns.tolist()]
    donnees.extend(df.astype(str).values.tolist())

    tableau = Table(donnees, repeatRows=1, colWidths=[55, 55, 105, 105, 90, 65, 55, 65])

    tableau.setStyle(TableStyle([
    ("FONTSIZE", (0, 0), (-1, -1), 6),
    ("LEADING", (0, 0), (-1, -1), 7),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
]))

    contenu.append(tableau)
    contenu.append(Spacer(1, 12))
    contenu.append(Paragraph("Résumé des données", styles["Heading2"]))
    nb_resultats = len(df)
    nb_resistants = (df["phenotype"] == "Resistant").sum()
    taux_global = nb_resistants / nb_resultats * 100 if nb_resultats > 0 else 0

    contenu.append(Paragraph(
        f"Nombre de résultats : {nb_resultats}<br/>"
        f"Résultats résistants : {nb_resistants}<br/>"
        f"Taux global de résistance : {taux_global:.1f} %",
        styles["BodyText"]
    ))

    document.build(contenu)
    tampon.seek(0)

    return tampon.getvalue()
if not df_filtre.empty:
    st.download_button(
        label="Télécharger le rapport PDF",
        data=creer_rapport_pdf(df_filtre),
        file_name="rapport_amr_scope.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Aucune donnée à exporter en PDF pour les filtres sélectionnés.")
