"""
Point d'entrée Streamlit — Assistant de rédaction LinkedIn BADEE + Dashboard.
V1 : Proof of concept, sans connexion aux données réelles ni publication automatique.

Lancer avec : streamlit run app/main.py
"""

import streamlit as st
import sys
import os
import json
import base64
from datetime import datetime
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODELES_A_COMPARER, MODELE_ACTIF
from app.conversation import generer_reponse
from app.dashboard import afficher_dashboard


# ============================================================
# CHEMINS
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "images", "logo_badee.png")
CSS_PATH = os.path.join(BASE_DIR, "assets", "styles", "badee_theme.css")
HISTORIQUE_PATH = os.path.join(BASE_DIR, "data", "conversation_history.json")


def charger_historique():
    """Recharge la conversation sauvegardée (survit au rechargement de page)."""
    if os.path.exists(HISTORIQUE_PATH):
        try:
            with open(HISTORIQUE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def sauvegarder_historique(messages):
    """Sauvegarde la conversation sur disque après chaque échange."""
    os.makedirs(os.path.dirname(HISTORIQUE_PATH), exist_ok=True)
    with open(HISTORIQUE_PATH, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def effacer_historique():
    if os.path.exists(HISTORIQUE_PATH):
        os.remove(HISTORIQUE_PATH)


def formater_conversation_txt(messages):
    """Formate la conversation en texte lisible pour le téléchargement."""
    lignes = [
        "BADEE — Assistant de rédaction LinkedIn",
        f"Conversation exportée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        "=" * 50,
        "",
    ]
    for message in messages:
        auteur = "Vous" if message["role"] == "user" else "Assistant"
        lignes.append(f"[{auteur}]")
        lignes.append(message["content"])
        lignes.append("")
    return "\n".join(lignes)


def load_logo():
    if os.path.exists(LOGO_PATH):
        return Image.open(LOGO_PATH)
    return None

logo = load_logo()


# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================
st.set_page_config(
    page_title="BADEE — Assistant rédaction LinkedIn",
    page_icon=logo if logo else "⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CHARGEMENT DU CSS
# ============================================================
def load_css():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()


# ============================================================
# EN-TÊTE — logo + titre (statique, les onglets gèrent le contexte)
# ============================================================
def logo_base64():
    if not os.path.exists(LOGO_PATH):
        return None
    with open(LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()

_logo_b64 = logo_base64()
_logo_html = (
    f'<img src="data:image/png;base64,{_logo_b64}" width="72" alt="Logo BADEE">'
    if _logo_b64 else ""
)

st.markdown(f"""
<div class="badee-header">
    {_logo_html}
    <div>
        <p class="badee-header-title">Agent IA de communication BADEE</p>
        <p class="badee-header-subtitle">BADEE — Social &amp; Inclusive Business Builder, INNOVX</p>
    </div>
</div>
""", unsafe_allow_html=True)

tab_chatbot, tab_dashboard, tab_calendrier = st.tabs(["💬  Chatbot", "📊  Dashboard", "🗓️  Calendrier"])


# ============================================================
# SIDEBAR — paramètres, sobre (commun aux deux vues)
# ============================================================
with st.sidebar:
    st.markdown('<span class="badee-badge">V1 — Proof of Concept</span>', unsafe_allow_html=True)

    st.markdown("### Paramètres")
    st.caption(f"Modèle : {MODELE_ACTIF} ({MODELES_A_COMPARER[MODELE_ACTIF]['provider']})")

    if st.button("Réinitialiser la conversation", use_container_width=True):
        st.session_state.messages = []
        effacer_historique()
        st.rerun()

    if st.session_state.get("messages"):
        st.download_button(
            "Télécharger la conversation",
            data=formater_conversation_txt(st.session_state.messages),
            file_name=f"conversation_badee_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )


with tab_chatbot:

    st.markdown("""
    <div class="validation-banner">
        <span>⚠</span> Validation humaine obligatoire avant toute publication
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = charger_historique()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt_utilisateur = st.chat_input("Décrivez le post que vous souhaitez rédiger...")

    if prompt_utilisateur:
        st.session_state.messages.append({"role": "user", "content": prompt_utilisateur})
        sauvegarder_historique(st.session_state.messages)
        with st.chat_message("user"):
            st.markdown(prompt_utilisateur)

        with st.chat_message("assistant"):
            with st.spinner("Rédaction en cours..."):
                try:
                    reponse = generer_reponse(MODELE_ACTIF, st.session_state.messages)
                    st.markdown(reponse)
                    st.session_state.messages.append({"role": "assistant", "content": reponse})
                    sauvegarder_historique(st.session_state.messages)

                    st.markdown("""
                    <div class="validation-banner">
                        <span>⚠</span> Brouillon à valider par un responsable avant publication
                    </div>
                    """, unsafe_allow_html=True)

                except ValueError as e:
                    st.error(str(e))


with tab_dashboard:
    afficher_dashboard()


with tab_calendrier:
    from datetime import date as _date
    from data.evenements_personnalises import (
        ajouter_evenement, lister_evenements, supprimer_evenement, supabase_actif
    )

    if supabase_actif():
        st.markdown("""
        <div class="validation-banner" style="background-color:#EAF6EC; border-left-color:#209138;">
            <span style="color:#209138;">✓</span> Stockage persistant actif (Supabase) — les événements sont partagés avec le système d'alerte.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="validation-banner">
            <span>⚠</span> Mode démonstration — Supabase non configuré. Les événements ajoutés ici ne persistent que le temps de la session (voir README pour activer le stockage permanent).
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### Ajouter un événement")
    st.caption("Salon, partenariat, lancement — tout événement pertinent pour la communication BADEE, en plus des fêtes déjà intégrées automatiquement.")

    with st.form("form_ajout_evenement", clear_on_submit=True):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            nom_evt = st.text_input("Nom de l'événement")
        with col_b:
            date_evt = st.date_input("Date", value=_date.today())
        message_evt = st.text_input("Message suggéré (optionnel)", placeholder="Ex : Teaser participation salon X")
        submitted = st.form_submit_button("Ajouter", type="primary")

        if submitted:
            if nom_evt.strip():
                ajouter_evenement(nom_evt.strip(), date_evt, message_evt.strip())
                st.success(f"« {nom_evt} » ajouté au calendrier.")
                st.rerun()
            else:
                st.warning("Le nom de l'événement est obligatoire.")

    st.markdown("#### Événements à venir")
    evenements = lister_evenements()

    if not evenements:
        st.caption("Aucun événement personnalisé pour l'instant.")
    else:
        for evt in evenements:
            col_info, col_del = st.columns([5, 1])
            with col_info:
                date_affichee = evt["date_evenement"]
                message = evt.get("message_suggere") or "—"
                st.markdown(f"**{evt['nom']}** — {date_affichee}  \n*{message}*")
            with col_del:
                if st.button("🗑️", key=f"del_{evt['id']}"):
                    supprimer_evenement(evt["id"])
                    st.rerun()
            st.markdown("<hr style='margin:0.3rem 0;'>", unsafe_allow_html=True)


# ============================================================
# PIED DE PAGE
# ============================================================
st.markdown("""
<hr>
<div class="badee-footer">
    BADEE — Agent IA Communication &bull; V1 Proof of Concept
</div>
""", unsafe_allow_html=True)