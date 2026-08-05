"""
Script de comparaison manuelle des modèles configurés dans config.MODELES_A_COMPARER.
Lance les 3 mêmes scénarios sur chaque modèle et affiche les résultats côte à côte.

Ce n'est PAS une suite de tests unitaires classique — c'est un outil d'aide
à la décision pour choisir le modèle le plus adapté avant de figer MODELE_ACTIF.

Lancer avec : python tests/test_prompts_manuel.py
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODELES_A_COMPARER
from app.conversation import generer_reponse

# Scénarios de test, calibrés sur les 3 cas linguistiques les plus exigeants
SCENARIOS = {
    "post_anglais_standard": (
        "Rédige un post teaser pour notre participation au salon Maison&Objet Paris, "
        "du 5 au 9 septembre, stand 4B12. Post en anglais."
    ),
    "post_bilingue_evenement": (
        "Rédige un post de bilan pour notre participation au GSEF Bordeaux, "
        "avec de bons échanges avec des partenaires francophones. "
        "Post bilingue anglais/français."
    ),
    "voeu_arabe": (
        "Rédige un post de vœux pour l'Aïd al-Fitr, dans le registre solennel habituel, "
        "avec de l'arabe natif comme il se doit pour ce type de contenu."
    ),
}


def lancer_comparaison():
    resultats = []

    for nom_modele in MODELES_A_COMPARER:
        print(f"\n{'=' * 60}")
        print(f"MODÈLE : {nom_modele} ({MODELES_A_COMPARER[nom_modele]['provider']})")
        print(f"{'=' * 60}")

        for nom_scenario, prompt in SCENARIOS.items():
            print(f"\n--- Scénario : {nom_scenario} ---")
            try:
                historique = [{"role": "user", "content": prompt}]
                reponse = generer_reponse(nom_modele, historique)
                print(reponse)
                resultats.append(
                    {
                        "modele": nom_modele,
                        "scenario": nom_scenario,
                        "reponse": reponse,
                        "erreur": None,
                    }
                )
            except Exception as e:
                print(f"❌ ERREUR : {e}")
                resultats.append(
                    {
                        "modele": nom_modele,
                        "scenario": nom_scenario,
                        "reponse": None,
                        "erreur": str(e),
                    }
                )

    # Sauvegarde des résultats bruts pour analyse ultérieure
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin_sortie = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs",
        f"comparaison_modeles_{horodatage}.md",
    )

    with open(chemin_sortie, "w", encoding="utf-8") as f:
        f.write(f"# Comparaison des modèles — {horodatage}\n\n")
        for r in resultats:
            f.write(f"## {r['modele']} — {r['scenario']}\n\n")
            if r["erreur"]:
                f.write(f"❌ Erreur : {r['erreur']}\n\n")
            else:
                f.write(f"{r['reponse']}\n\n")

    print(f"\n\n✅ Résultats sauvegardés dans : {chemin_sortie}")


if __name__ == "__main__":
    lancer_comparaison()
