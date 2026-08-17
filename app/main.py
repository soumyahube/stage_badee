"""
Point d'entrée Streamlit — Assistant de rédaction LinkedIn BADEE + Dashboard.
V1 : Proof of concept, sans connexion aux données réelles ni publication automatique.

Lancer avec : streamlit run app/main.py
"""

import streamlit as st
import sys
import os
import base64
from datetime import datetime
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODELES_A_COMPARER, MODELE_ACTIF
from app.conversation import generer_reponse
from app.dashboard import afficher_dashboard
from app.historique import (
    charger_conversations,
    obtenir_conversation_active,
    mettre_a_jour_conversation,
    creer_conversation,
    definir_conversation_active,
    supprimer_conversation,
    conversations_triees,
)


# ============================================================
# CHEMINS
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "images", "logo_badee.png")
CSS_PATH = os.path.join(BASE_DIR, "assets", "styles", "badee_theme.css")


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

tab_chatbot, tab_dashboard, tab_calendrier = st.tabs([" Chatbot", "  Dashboard", "  Calendrier"])


# ============================================================
# CHARGEMENT DES CONVERSATIONS — avant la sidebar, pour que la liste
# et le bouton d'export s'appuient sur la conversation active
# ============================================================
if "conversations_data" not in st.session_state:
    st.session_state.conversations_data = charger_conversations()

data = st.session_state.conversations_data
conversation_active = obtenir_conversation_active(data)
conversation_active_id = conversation_active["id"]


# ============================================================
# SIDEBAR — paramètres + conversations (commun aux trois onglets)
# ============================================================
with st.sidebar:
    st.markdown('<span class="badee-badge">V1 — Proof of Concept</span>', unsafe_allow_html=True)

    st.markdown("### Paramètres")
    st.caption(f"Modèle : {MODELE_ACTIF} ({MODELES_A_COMPARER[MODELE_ACTIF]['provider']})")

    if conversation_active["messages"]:
        st.markdown("### Export")
        st.download_button(
            "Télécharger cette conversation",
            data=formater_conversation_txt(conversation_active["messages"]),
            file_name=f"conversation_badee_{conversation_active_id}.txt",
            mime="text/plain",
            use_container_width=True,
        )


with tab_chatbot:

    conversations = conversations_triees(data)
    col_liste, col_nouvelle = st.columns([4, 1.3])

    with col_liste:
        options = {conv["id"]: conv["titre"] for conv in conversations}
        ids = list(options.keys())
        index_actif = ids.index(conversation_active_id) if conversation_active_id in ids else 0
        conv_choisie = st.selectbox(
            "Conversation",
            options=ids,
            index=index_actif,
            format_func=lambda cid: options[cid],
            label_visibility="collapsed",
        )
        if conv_choisie != conversation_active_id:
            definir_conversation_active(data, conv_choisie)
            st.rerun()

    with col_nouvelle:
        if st.button("＋ Nouvelle", use_container_width=True, type="primary"):
            creer_conversation(data)
            st.rerun()

    if conversations:
        with st.expander("Gérer les conversations"):
            for conv in conversations:
                col_titre, col_suppr = st.columns([5, 1])
                with col_titre:
                    st.caption(conv["titre"])
                with col_suppr:
                    if st.button("🗑", key=f"suppr_{conv['id']}", help="Supprimer cette conversation"):
                        supprimer_conversation(data, conv["id"])
                        st.rerun()

    st.markdown("""
    <div class="validation-banner">
        <span>⚠</span> Validation humaine obligatoire avant toute publication
    </div>
    """, unsafe_allow_html=True)

    for message in conversation_active["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt_utilisateur = st.chat_input("Décrivez le post que vous souhaitez rédiger...")

    if prompt_utilisateur:
        messages = conversation_active["messages"]
        messages.append({"role": "user", "content": prompt_utilisateur})
        mettre_a_jour_conversation(data, conversation_active_id, messages)

        with st.chat_message("user"):
            st.markdown(prompt_utilisateur)

        with st.chat_message("assistant"):
            with st.spinner("Rédaction en cours..."):
                try:
                    reponse = generer_reponse(MODELE_ACTIF, messages)
                    st.markdown(reponse)
                    messages.append({"role": "assistant", "content": reponse})
                    mettre_a_jour_conversation(data, conversation_active_id, messages)

                    st.markdown("""
                    <div class="validation-banner">
                        <span>⚠</span> Brouillon à valider par un responsable avant publication
                    </div>
                    """, unsafe_allow_html=True)

                    st.rerun()  # rafraîchit la sidebar (titre auto-généré, tri par date)

                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(
                        "Impossible de contacter le modèle pour le moment "
                        "(connexion réseau ou service indisponible). "
                        "Réessayez dans quelques instants."
                    )
                    st.caption(f"Détail technique : {type(e).__name__} — {e}")


with tab_dashboard:
    afficher_dashboard()


with tab_calendrier:
    from datetime import date as _date
    from data.evenements_personnalises import (
        ajouter_evenement, lister_evenements, supprimer_evenement, supabase_actif
    )

    try:
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

    except Exception as e:
        st.markdown(f"""
        <div class="validation-banner">
            <span>⚠</span> Calendrier indisponible pour le moment (connexion à Supabase impossible). Le Chatbot et le Dashboard restent utilisables normalement.
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"Détail technique : {type(e).__name__} — {e}")


# ============================================================
# PIED DE PAGE
# ============================================================
st.markdown("""
<hr>
<div class="badee-footer">
    BADEE — Agent IA Communication &bull; V1 Proof of Concept
</div>
""", unsafe_allow_html=True)