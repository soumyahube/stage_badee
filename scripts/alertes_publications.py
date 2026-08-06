"""
Système d'alerte BADEE — Vérifie la dernière publication LinkedIn
et envoie une alerte si aucune publication depuis plus de X jours.

Lancer : python scripts/alertes.py
"""

import os
import json
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from calendrier_editorial import generer_suggestion_sujet
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================
SEUIL_JOURS = 7  # Alerter si pas de publication depuis 3 jours

# Données de la dernière publication (à remplacer par API plus tard)
DERNIERE_PUBLICATION = {
    "date": "2026-01-01",  # Dernière publication
    "titre": "Participation de BADEE à INDEX Saudi Arabia",
    "likes": 196,
    "comments": 12,
    "lien": "https://linkedin.com/company/badee/posts/12345"
}

# Configuration email (à remplacer par vos vraies données)
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender": "sosoumya995@gmail.com",  # À remplacer
    "password": os.getenv("EMAIL_PASSWORD"),  # À remplacer
    "recipient": "soumya.laaouina1@gmail.com"  # À remplacer
}

# ============================================================
# FONCTIONS
# ============================================================
def verifier_derniere_publication():
    """Vérifie la date de la dernière publication."""
    date_pub = datetime.strptime(DERNIERE_PUBLICATION["date"], "%Y-%m-%d")
    jours_ecoules = (datetime.now() - date_pub).days
    return jours_ecoules, DERNIERE_PUBLICATION


def envoyer_alerte_email(jours_ecoules, publication):
    """Envoie l'alerte par email."""
    if not EMAIL_CONFIG["password"] or EMAIL_CONFIG["password"] == "votre_mot_de_passe_applicatif":
        print("⚠️ Mot de passe email non configuré.")
        print("📧 Alerte simulée (email non envoyé):")
        afficher_alerte_console(jours_ecoules, publication)
        return False
    
    sujet = f"⚠️ ALERTE - {jours_ecoules} jours sans publication LinkedIn BADEE"
    
    corps = f"""
Bonjour l'équipe,

Ce message est une alerte automatique concernant la présence de BADEE sur LinkedIn.

📅 Dernière publication : {publication['date']}
📝 Titre : {publication['titre']}
⏰ Jours sans publication : {jours_ecoules} jours
❤️ Engagement : {publication['likes']} likes, {publication['comments']} commentaires

💡 Suggestion de sujet : {generer_suggestion_sujet()}

🔗 Lien : {publication.get('lien', 'Non disponible')}

---
Ce message a été généré automatiquement par le système d'alerte BADEE.
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

def afficher_alerte_console(jours_ecoules, publication):
    """Affiche l'alerte dans la console."""
    print("=" * 60)
    print("⚠️  ALERTE PUBLICATION LINKEDIN - BADEE")
    print("=" * 60)
    print(f"📅 Dernière publication : {publication['date']}")
    print(f"⏰ Jours écoulés : {jours_ecoules} jours")
    print(f"📝 Titre : {publication['titre']}")
    print(f"❤️ Engagement : {publication['likes']} likes, {publication['comments']} commentaires")
    print(f"\n💡 Suggestion : {generer_suggestion_sujet()}")
    print("=" * 60)

def main():
    print("🔍 Vérification de la dernière publication LinkedIn...")
    
    jours_ecoules, publication = verifier_derniere_publication()
    print(f"📅 Dernière publication : il y a {jours_ecoules} jours")
    
    if jours_ecoules > SEUIL_JOURS:
        print(f"⚠️ ALERTE ! Plus de {SEUIL_JOURS} jours sans publication.")
        afficher_alerte_console(jours_ecoules, publication)
        envoyer_alerte_email(jours_ecoules, publication)
    else:
        print("✅ Tout est bon ! Publication récente.")

if __name__ == "__main__":
    main()