"""
Scoring IA des commentaires LinkedIn — BADEE.

Remplace/complète le scoring par mots-clés (est_profil_forte_valeur) par une
évaluation LLM qui prend en compte à la fois le poste de l'auteur ET le contenu
réel du commentaire, et renvoie une priorité nuancée (0-100) plutôt qu'un simple
booléen.

Réutilise la même infrastructure que le chatbot de rédaction (config.py,
PROVIDERS, MODELES_A_COMPARER) — pas de nouvelle dépendance, pas de nouveau coût.

Principe de robustesse : si l'appel LLM échoue (clé manquante, quota dépassé,
réponse mal formée...), on retombe automatiquement sur le scoring par mots-clés
existant, pour que le système d'alerte ne tombe jamais en panne à cause du scoring.

Lancer un test isolé : python scripts/scoring_commentaires.py
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODELES_A_COMPARER, MODELE_ACTIF
from app.conversation import get_client

# ============================================================
# CONFIGURATION
# ============================================================
SEUIL_PRIORITAIRE = 70  # score >= ce seuil => 🔴 PRIORITAIRE

# Mots-clés simples utilisés UNIQUEMENT en secours si le LLM échoue
MOTS_CLES_PROFIL_FORTE_VALEUR = [
    "director", "directeur", "ceo", "founder", "fondateur",
    "chercheur", "researcher", "investisseur", "investor",
    "partner", "partenaire"
]

CATEGORIES_VALIDES = {
    "opportunite_business",
    "partenaire_potentiel",
    "presse_media",
    "soutien_communaute",
    "question",
    "negatif",
}

SENTIMENTS_VALIDES = {"positif", "neutre", "negatif"}

SYSTEM_PROMPT_SCORING = """Tu es un assistant qui aide l'équipe communication de BADEE \
(social & inclusive business builder, filiale d'INNOVX) à prioriser les commentaires \
LinkedIn en attente de réponse.

Pour CHAQUE commentaire fourni, évalue :
- "score" : un entier de 0 à 100 représentant la priorité de réponse pour BADEE \
(100 = très urgent/à haute valeur, ex. opportunité business concrète, journaliste, \
partenaire institutionnel qui pose une vraie question ; 0 = aucune urgence, ex. simple \
émoji ou compliment générique)
- "categorie" : une seule valeur parmi "opportunite_business", "partenaire_potentiel", \
"presse_media", "soutien_communaute", "question", "negatif"
- "sentiment" : le ton du commentaire — une seule valeur parmi "positif", "neutre", "negatif" \
(indépendant de la catégorie : une question peut être posée sur un ton neutre ou négatif ; \
un commentaire négatif sur le fond n'est pas forcément insultant, ex. une critique polie compte \
comme "negatif")
- "justification" : une phrase courte expliquant le score

Base-toi sur le POSTE de l'auteur ET sur le CONTENU du commentaire, pas seulement le poste : \
un profil senior qui laisse un simple compliment n'est pas forcément plus urgent qu'un \
commentaire anonyme qui pose une vraie question business.

Ne jamais inventer d'information sur l'auteur ou l'entreprise au-delà de ce qui est fourni.

Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant ni après, sans balises \
markdown. Format attendu :
[
  {"id": 0, "score": 85, "categorie": "opportunite_business", "sentiment": "positif", "justification": "..."},
  {"id": 1, "score": 20, "categorie": "soutien_communaute", "sentiment": "positif", "justification": "..."}
]
L'ordre et le nombre d'éléments doivent correspondre exactement aux commentaires fournis, \
identifiés par leur "id"."""


# ============================================================
# SCORING PAR MOTS-CLÉS (fallback)
# ============================================================
def _score_fallback_mots_cles(commentaire: dict) -> dict:
    """Scoring de secours si le LLM est indisponible. Reproduit l'ancienne logique
    binaire, convertie en score pour rester compatible avec le tri par score."""
    poste = commentaire.get("poste_auteur", "").lower()
    forte_valeur = any(mot in poste for mot in MOTS_CLES_PROFIL_FORTE_VALEUR)
    return {
        "score": 75 if forte_valeur else 30,
        "categorie": "partenaire_potentiel" if forte_valeur else "soutien_communaute",
        "sentiment": "neutre",  # non détectable de façon fiable par mots-clés seuls
        "justification": "Scoring de secours (mots-clés du poste) — LLM indisponible.",
    }


# ============================================================
# SCORING LLM (batch)
# ============================================================
def _construire_prompt_batch(commentaires: list[dict]) -> str:
    lignes = ["Voici les commentaires à évaluer :\n"]
    for i, c in enumerate(commentaires):
        lignes.append(
            f'{{"id": {i}, "poste_auteur": {json.dumps(c.get("poste_auteur", ""), ensure_ascii=False)}, '
            f'"commentaire": {json.dumps(c.get("commentaire", ""), ensure_ascii=False)}}}'
        )
    return "\n".join(lignes)


JUSTIFICATION_PAR_DEFAUT = {
    "opportunite_business": "Contient une demande ou une piste business concrète.",
    "partenaire_potentiel": "Profil ou message en lien avec un partenariat possible.",
    "presse_media": "Sollicitation presse/média identifiée.",
    "soutien_communaute": "Message de soutien sans action requise.",
    "question": "Question posée nécessitant une réponse.",
    "negatif": "Commentaire à traiter avec attention (ton négatif détecté).",
}


def _justification_suspecte(texte: str) -> bool:
    """Détecte grossièrement un texte corrompu/artefact produit par le modèle
    (mots hors vocabulaire courant, séquences improbables). Volontairement simple :
    l'objectif est d'attraper les cas flagrants, pas de faire de la correction
    linguistique fine."""
    if not texte or len(texte) < 5:
        return True
    mots = texte.split()
    if len(mots) < 2:
        return True
    # Ratio de mots très courts/tout-majuscules suspects (ex. "PVP", "älj")
    mots_suspects = sum(
        1 for m in mots
        if (m.isupper() and len(m) <= 4 and m.isalpha())
        or any(ch in m for ch in "äöüßØ")  # caractères hors FR/EN typiques d'un artefact
    )
    return mots_suspects >= 1 and mots_suspects / len(mots) > 0.05


def _parser_reponse_json(texte: str, nb_attendu: int) -> list[dict] | None:
    """Extrait le tableau JSON de la réponse, même si le modèle a ajouté du texte
    ou des balises markdown autour (fréquent malgré la consigne)."""
    texte = texte.strip()
    # Retire d'éventuelles balises ```json ... ```
    if texte.startswith("```"):
        texte = texte.strip("`")
        texte = texte.replace("json\n", "", 1).replace("json", "", 1)
    # Isole le premier tableau JSON trouvé dans la réponse
    debut = texte.find("[")
    fin = texte.rfind("]")
    if debut == -1 or fin == -1 or fin < debut:
        return None
    try:
        resultats = json.loads(texte[debut:fin + 1])
    except json.JSONDecodeError:
        return None

    if not isinstance(resultats, list) or len(resultats) != nb_attendu:
        return None

    for r in resultats:
        if not isinstance(r, dict):
            return None
        if not isinstance(r.get("score"), (int, float)):
            return None
        if r.get("categorie") not in CATEGORIES_VALIDES:
            r["categorie"] = "question"  # valeur neutre si catégorie hors liste
        if r.get("sentiment") not in SENTIMENTS_VALIDES:
            r["sentiment"] = "neutre"  # valeur neutre si sentiment hors liste/manquant
        r["score"] = max(0, min(100, int(r["score"])))
        if _justification_suspecte(r.get("justification", "")):
            r["justification"] = JUSTIFICATION_PAR_DEFAUT[r["categorie"]]

    return resultats


def _sauvegarder_reponse_brute(texte: str) -> None:
    """Écrit la réponse brute du LLM dans un fichier UTF-8, horodaté, pour
    inspection manuelle — utile pour vérifier si un problème d'affichage vient
    du modèle ou du terminal local. Activé via la variable d'environnement
    BADEE_DEBUG_SCORING=1."""
    dossier = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(dossier, exist_ok=True)
    horodatage = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = os.path.join(dossier, f"debug_scoring_brut_{horodatage}.json")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)
    print(f"🔍 [DEBUG] Réponse brute du LLM sauvegardée dans : {chemin}")


def scorer_commentaires(commentaires: list[dict], nom_modele: str = MODELE_ACTIF) -> list[dict]:
    """
    Évalue une liste de commentaires et renvoie, pour chacun, un dict enrichi avec
    'score' (0-100), 'categorie', 'sentiment' (positif/neutre/negatif) et 'justification'.

    commentaires : liste de dicts contenant au minimum 'poste_auteur' et 'commentaire'
    nom_modele   : clé de config.MODELES_A_COMPARER (par défaut le modèle actif)

    Ne modifie pas la liste d'entrée ; renvoie une nouvelle liste de dicts fusionnés.
    En cas d'échec LLM (clé API manquante, erreur réseau, réponse mal formée),
    bascule automatiquement sur le scoring par mots-clés pour CHAQUE commentaire.
    """
    if not commentaires:
        return []

    resultats_llm = None
    try:
        infos_modele = MODELES_A_COMPARER[nom_modele]
        client = get_client(infos_modele["provider"])

        reponse = client.chat.completions.create(
            model=infos_modele["model_id"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_SCORING},
                {"role": "user", "content": _construire_prompt_batch(commentaires)},
            ],
            temperature=0.2,  # scoring = besoin de constance, pas de créativité
            max_tokens=1500,
        )
        texte = reponse.choices[0].message.content

        if os.getenv("BADEE_DEBUG_SCORING"):
            _sauvegarder_reponse_brute(texte)

        resultats_llm = _parser_reponse_json(texte, len(commentaires))

    except Exception as e:
        print(f"⚠️ Scoring LLM indisponible ({e}) — bascule sur le scoring par mots-clés.")

    commentaires_scores = []
    for i, c in enumerate(commentaires):
        c_enrichi = dict(c)
        if resultats_llm is not None:
            c_enrichi.update({
                "score": resultats_llm[i]["score"],
                "categorie": resultats_llm[i]["categorie"],
                "sentiment": resultats_llm[i]["sentiment"],
                "justification": resultats_llm[i]["justification"],
            })
        else:
            c_enrichi.update(_score_fallback_mots_cles(c))
        commentaires_scores.append(c_enrichi)

    if resultats_llm is None:
        print("⚠️ ATTENTION : tous les commentaires ont été scorés en mode secours (mots-clés).")

    return commentaires_scores


if __name__ == "__main__":
    # Test rapide avec des exemples simulés
    exemples = [
        {
            "poste_auteur": "Investment Director chez XYZ Capital",
            "commentaire": "Félicitations pour cette belle participation !",
        },
        {
            "poste_auteur": "Membre coopérative",
            "commentaire": "Comment puis-je proposer notre coopérative pour un futur partenariat ?",
        },
        {
            "poste_auteur": "Journaliste, Le Desk",
            "commentaire": "Je prépare un article sur l'ESS au Maroc, possible d'échanger avec votre CEO ?",
        },
    ]
    for r in scorer_commentaires(exemples):
        print(f"[{r['score']:3d}] {r['categorie']:22s} ({r['sentiment']:8s}) — {r['commentaire'][:50]}")
        print(f"      → {r['justification']}")