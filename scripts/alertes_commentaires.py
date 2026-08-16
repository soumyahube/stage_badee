"""
Système d'alerte BADEE — Commentaires non répondus (48h)
Vérifie les commentaires en attente de réponse et alerte en priorisant
les profils à forte valeur, grâce à un scoring IA (poste + contenu du
commentaire), avec repli automatique sur un scoring par mots-clés si le
LLM est indisponible (voir scripts/scoring_commentaires.py).

Premier test avec données simulées (à remplacer par l'API LinkedIn
+ Supabase une fois le module Collecte connecté).

Lancer : python scripts/alertes_commentaires.py
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.scoring_commentaires import scorer_commentaires, SEUIL_PRIORITAIRE

# ============================================================
# CONFIGURATION
# ============================================================
SEUIL_HEURES = 48  # Alerter si commentaire sans réponse depuis plus de 48h

# Commentaires simulés (à remplacer par l'API plus tard)
COMMENTAIRES_SIMULES = [
    {
        "post_titre": "Participation de BADEE à INDEX Saudi Arabia",
        "auteur": "Amine K.",
        "poste_auteur": "Investment Director chez XYZ Capital",
        "commentaire": "Félicitations pour cette belle participation !",
        "date_commentaire": "2026-08-03 10:15",
        "repondu": False,
        "lien": "https://linkedin.com/company/badee/posts/12345"
    },
    {
        "post_titre": "Coopérative de laine El Jadida",
        "auteur": "Fatima Z.",
        "poste_auteur": "Membre coopérative",
        "commentaire": "Magnifique initiative, bravo à toute l'équipe.",
        "date_commentaire": "2026-08-04 14:30",
        "repondu": False,
        "lien": "https://linkedin.com/company/badee/posts/12346"
    },
    {
        "post_titre": "Adhésion au GIIN",
        "auteur": "John D.",
        "poste_auteur": "Researcher, Social Impact Lab",
        "commentaire": "Great step forward for impact investing in the region.",
        "date_commentaire": "2026-08-05 09:00",
        "repondu": False,
        "lien": "https://linkedin.com/company/badee/posts/12347"
    },
]

EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender": "sosoumya995@gmail.com",       # À remplacer par l'adresse BADEE confirmée
    "password": os.getenv("EMAIL_PASSWORD"),
    "recipient": "soumya.laaouina1@gmail.com"  # À remplacer par contact@badee.ma + M. El Ksis
}

# ============================================================
# FONCTIONS
# ============================================================
def heures_ecoulees(date_str):
    date_commentaire = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    delta = datetime.now() - date_commentaire
    return delta.total_seconds() / 3600


def detecter_commentaires_en_attente():
    """Filtre les commentaires non répondus depuis plus de SEUIL_HEURES,
    puis les envoie au scoring IA (score 0-100 + catégorie) avant de trier
    par priorité décroissante."""
    candidats = []
    for c in COMMENTAIRES_SIMULES:
        if c["repondu"]:
            continue
        h = heures_ecoulees(c["date_commentaire"])
        if h >= SEUIL_HEURES:
            c["heures_ecoulees"] = round(h, 1)
            candidats.append(c)

    if not candidats:
        return []

    # Scoring IA en un seul appel batch (fallback mots-clés géré en interne)
    candidats_scores = scorer_commentaires(candidats)

    # Tri par score décroissant, puis par ancienneté pour départager
    candidats_scores.sort(key=lambda c: (-c["score"], -c["heures_ecoulees"]))
    return candidats_scores


def construire_corps_email(commentaires):
    lignes = []
    for c in commentaires:
        if c["score"] >= SEUIL_PRIORITAIRE:
            priorite = "🔴 PRIORITAIRE"
        elif c["sentiment"] == "negatif":
            priorite = "⚠️ TON NÉGATIF"  # à surveiller même si peu urgent côté business
        else:
            priorite = "🟡 Standard"
        emoji_sentiment = {"positif": "🙂", "neutre": "😐", "negatif": "🙁"}[c["sentiment"]]
        lignes.append(f"""
{priorite} — score {c['score']}/100 ({c['categorie']}) — ton {emoji_sentiment} {c['sentiment']}
Post : {c['post_titre']}
Auteur : {c['auteur']} — {c['poste_auteur']}
Commentaire : "{c['commentaire']}"
Pourquoi ce score : {c['justification']}
Sans réponse depuis : {c['heures_ecoulees']} h
Lien : {c['lien']}
{'-'*50}""")
    return "\n".join(lignes)


def envoyer_alerte_email(commentaires):
    if not commentaires:
        print("✅ Aucun commentaire en attente au-delà du seuil.")
        return False

    if not EMAIL_CONFIG["password"] or EMAIL_CONFIG["password"] == "votre_mot_de_passe_applicatif":
        print("⚠️ Mot de passe email non configuré.")
        print("📧 Alerte simulée (email non envoyé):")
        afficher_alerte_console(commentaires)
        return False

    nb_prioritaires = sum(1 for c in commentaires if c["score"] >= SEUIL_PRIORITAIRE)
    sujet = f"⚠️ ALERTE - {len(commentaires)} commentaire(s) sans réponse ({nb_prioritaires} prioritaire(s))"

    corps = f"""
Bonjour l'équipe,

Ce message est une alerte automatique concernant des commentaires LinkedIn
sans réponse depuis plus de {SEUIL_HEURES}h. Les commentaires sont triés par
priorité (score IA basé sur le poste de l'auteur et le contenu du commentaire).

{construire_corps_email(commentaires)}

---
Ce message a été généré automatiquement par le système d'alerte BADEE.
Aucune réponse n'est envoyée automatiquement — validation humaine requise.
    """

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_CONFIG["sender"]
        msg["To"] = EMAIL_CONFIG["recipient"]
        msg["Subject"] = sujet
        msg.attach(MIMEText(corps, "plain"))

        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
        server.send_message(msg)
        server.quit()

        print("✅ Alerte envoyée par email.")
        return True

    except Exception as e:
        print(f"❌ Erreur d'envoi : {e}")
        return False


def afficher_alerte_console(commentaires):
    print("=" * 60)
    print("⚠️  ALERTE COMMENTAIRES NON RÉPONDUS - BADEE")
    print("=" * 60)
    print(construire_corps_email(commentaires))
    print("=" * 60)


def main():
    print("🔍 Vérification des commentaires en attente de réponse...")
    en_attente = detecter_commentaires_en_attente()
    print(f"📝 {len(en_attente)} commentaire(s) au-delà du seuil de {SEUIL_HEURES}h")

    if en_attente:
        afficher_alerte_console(en_attente)
        envoyer_alerte_email(en_attente)
    else:
        print("✅ Tout est à jour.")


if __name__ == "__main__":
    main()