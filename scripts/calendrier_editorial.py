"""
Calendrier éditorial BADEE — génère une suggestion de sujet de post
en fonction des événements à venir (fêtes nationales, jours internationaux,
fêtes religieuses) plutôt que d'un simple mapping mois → sujet.

À importer dans alertes.py à la place de generer_suggestion_sujet().
"""

from datetime import datetime, timedelta

FENETRE_JOURS_PAR_DEFAUT = 10  # regarde X jours en avant pour trouver un événement pertinent

# ============================================================
# ÉVÉNEMENTS FIXES (calendrier grégorien — même date chaque année)
# Format : (mois, jour, nom, message suggéré)
# ============================================================
EVENEMENTS_FIXES = [
    (1, 1,   "Nouvel An",                          "Vœux Nouvel An"),
    (1, 11,  "Manifeste de l'Indépendance",        "Commémoration du Manifeste de l'Indépendance"),
    (1, 14,  "Nouvel An Amazigh (Yennayer)",        "Vœux Nouvel An Amazigh"),
    (5, 1,   "Fête du Travail",                     "Vœux Fête du Travail"),
    (7, 30,  "Fête du Trône",                       "Vœux Fête du Trône"),
    (8, 14,  "Allégeance Oued Eddahab",              "Commémoration Oued Eddahab"),
    (8, 20,  "Révolution du Roi et du Peuple",       "Commémoration Révolution du Roi et du Peuple"),
    (8, 21,  "Fête de la Jeunesse",                  "Vœux Fête de la Jeunesse"),
    (11, 6,  "Marche Verte",                         "Commémoration Marche Verte"),
    (11, 18, "Fête de l'Indépendance",                "Vœux Fête de l'Indépendance"),
    # Jour international pertinent pour la mission BADEE (coopératives/impact social)
    # Date exacte = 1er samedi de juillet, gérée à part (voir fonction dédiée)
]

# ============================================================
# ÉVÉNEMENTS MOBILES (calendrier hégirien — À METTRE À JOUR CHAQUE ANNÉE)
# Ces dates sont des estimations astronomiques ; la date officielle n'est
# confirmée par le ministère des Habous qu'après observation du croissant
# lunaire, parfois seulement 1-2 jours avant. Prévoir une marge.
# ============================================================
EVENEMENTS_MOBILES_PAR_ANNEE = {
    2026: [
        (datetime(2026, 3, 20), "Aïd al-Fitr",       "Vœux Aïd al-Fitr"),
        (datetime(2026, 5, 27), "Aïd al-Adha",        "Vœux Aïd al-Adha"),
        (datetime(2026, 6, 17), "Nouvel An Hégire",    "Vœux Nouvel An Hégire 1448"),
        (datetime(2026, 8, 25), "Aïd Al Mawlid",       "Vœux Aïd Al Mawlid Annabaoui"),
    ],
    # 2027 : à compléter en fin d'année 2026 dès les premières estimations
}

# ============================================================
# ROTATION DE FOND — si aucun événement proche, on propose un pilier de
# contenu (au lieu d'un texte générique fixe), pour varier les axes déjà
# identifiés comme sous-exploités dans l'état des lieux (impact terrain,
# storytelling, formats vidéo)
# ============================================================
PILIERS_CONTENU = [
    "Contenu d'impact terrain (coopérative, artisan, bénéficiaire)",
    "Storytelling / témoignage",
    "Actualité partenariat ou collaboration",
    "Contenu de fond sur la mission BADEE (hors événement)",
]


def _jour_international_cooperatives(annee):
    """1er samedi de juillet — Journée internationale des coopératives (ONU)."""
    d = datetime(annee, 7, 1)
    while d.weekday() != 5:  # 5 = samedi
        d += timedelta(days=1)
    return d


def _prochains_evenements(date_reference, fenetre_jours):
    """Retourne tous les événements (fixes + mobiles + jour coopératives)
    tombant entre date_reference et date_reference + fenetre_jours."""
    limite = date_reference + timedelta(days=fenetre_jours)
    annee = date_reference.year
    candidats = []

    # Événements fixes de l'année courante ET, si la fenêtre chevauche
    # le nouvel an, de l'année suivante
    for annee_test in (annee, annee + 1):
        for mois, jour, nom, message in EVENEMENTS_FIXES:
            try:
                d = datetime(annee_test, mois, jour)
            except ValueError:
                continue
            if date_reference <= d <= limite:
                candidats.append((d, nom, message))

        d_coop = _jour_international_cooperatives(annee_test)
        if date_reference <= d_coop <= limite:
            candidats.append((d_coop, "Journée internationale des coopératives",
                               "Post Journée internationale des coopératives"))

    # Événements mobiles (hégiriens)
    for annee_test in (annee, annee + 1):
        for d, nom, message in EVENEMENTS_MOBILES_PAR_ANNEE.get(annee_test, []):
            if date_reference <= d <= limite:
                candidats.append((d, nom, message))

    candidats.sort(key=lambda c: c[0])
    return candidats


def generer_suggestion_sujet(date_reference=None, fenetre_jours=FENETRE_JOURS_PAR_DEFAUT):
    """
    Retourne une suggestion de sujet de post.
    - S'il y a un événement (fixe ou mobile) dans les `fenetre_jours` prochains
      jours, le propose avec le nombre de jours restants.
    - Sinon, propose un pilier de contenu en rotation (pas de texte générique figé).
    """
    if date_reference is None:
        date_reference = datetime.now()

    evenements = _prochains_evenements(date_reference, fenetre_jours)

    if evenements:
        date_evt, nom, message = evenements[0]
        jours_restants = (date_evt - date_reference).days
        if jours_restants == 0:
            delai = "aujourd'hui"
        elif jours_restants == 1:
            delai = "demain"
        else:
            delai = f"dans {jours_restants} jours"
        return f"{message} — {nom} ({delai}, le {date_evt.strftime('%d/%m/%Y')})"

    # Pas d'événement proche : rotation sur les piliers de contenu,
    # basée sur le jour de l'année pour varier d'un appel à l'autre
    index = date_reference.timetuple().tm_yday % len(PILIERS_CONTENU)
    return PILIERS_CONTENU[index]


if __name__ == "__main__":
    # Test rapide
    print(generer_suggestion_sujet())