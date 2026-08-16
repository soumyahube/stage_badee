"""
Données simulées pour le dashboard de reporting.
Basées sur les chiffres réels de l'état des lieux (audit du 5 juillet 2026,
31 posts LinkedIn / 6 posts Instagram analysés manuellement).

À REMPLACER par une vraie requête à l'API LinkedIn + Supabase dès que l'accès
API est obtenu (voir data/Ressource_API_LinkedIn.docx). En attendant, ces
données permettent de démontrer les fonctionnalités du dashboard.
"""

import pandas as pd

# ============================================================
# INDICATEURS GLOBAUX (chiffres réels de l'audit)
# ============================================================
KPI_GLOBAUX = {
    "linkedin": {
        "abonnes": 1155,
        "posts_analyses": 31,
        "likes_moyen": 48,
        "commentaires_moyen": 2,
        "frequence_mensuelle": 2.3,
    },
    "instagram": {
        "abonnes": 34,
        "posts_analyses": 6,
        "likes_moyen": 7,
        "commentaires_moyen": 0,
        "frequence_mensuelle": 0.42,
    },
}

# ============================================================
# RÉPARTITION PAR CATÉGORIE DE CONTENU (LinkedIn, 31 posts)
# ============================================================
REPARTITION_CATEGORIES = pd.DataFrame([
    {"categorie": "Vœux et commémorations", "volume": 12, "likes_moyen": 22},
    {"categorie": "Événements internationaux", "volume": 12, "likes_moyen": 41},
    {"categorie": "Impact terrain / storytelling", "volume": 3, "likes_moyen": 126},
    {"categorie": "Annonce institutionnelle", "volume": 1, "likes_moyen": 53},
    {"categorie": "Contenu de marque / vision", "volume": 1, "likes_moyen": 37},
    {"categorie": "Republication tiers", "volume": 1, "likes_moyen": 15},
])

# ============================================================
# TOP / FLOP POSTS (issus de l'audit réel)
# ============================================================
TOP_POSTS = pd.DataFrame([
    {"post": "Remerciement OCP Africa", "categorie": "Storytelling / remerciement", "likes": 196, "commentaires": 12},
    {"post": "Ouverture Semaine ESS Addis-Abeba", "categorie": "Bilan événement", "likes": 176, "commentaires": 7},
    {"post": "Coopérative de laine El Jadida", "categorie": "Storytelling terrain", "likes": 87, "commentaires": 4},
])

FLOP_POSTS = pd.DataFrame([
    {"post": "Vœux Nouvel An Hégire 1448", "categorie": "Vœux religieux", "likes": 5, "commentaires": 0},
    {"post": "Vœux Nouvel An grégorien", "categorie": "Vœux calendaire", "likes": 9, "commentaires": 0},
    {"post": "Republication INNOVX (simple)", "categorie": "Republication", "likes": 15, "commentaires": 1},
])

# ============================================================
# ÉVOLUTION MENSUELLE SIMULÉE (pas de vraie série temporelle
# disponible sans API — extrapolation illustrative uniquement)
# ============================================================
EVOLUTION_MENSUELLE = pd.DataFrame([
    {"mois": "Mars 2026", "posts": 2, "likes_total": 78},
    {"mois": "Avril 2026", "posts": 3, "likes_total": 145},
    {"mois": "Mai 2026", "posts": 2, "likes_total": 91},
    {"mois": "Juin 2026", "posts": 4, "likes_total": 210},
    {"mois": "Juillet 2026", "posts": 3, "likes_total": 168},
])
