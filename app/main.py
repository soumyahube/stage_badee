"""
Point d'entrée Streamlit — Assistant de rédaction LinkedIn BADEE.
V1 : Proof of concept, sans connexion aux données réelles ni publication automatique.

Lancer avec : streamlit run app/main.py
"""

import streamlit as st
import sys
import os
import base64
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODELES_A_COMPARER, MODELE_ACTIF
from app.conversation import generer_reponse


# ============================================================
# CHEMINS
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "images", "logo_badee.png")
CSS_PATH = os.path.join(BASE_DIR, "assets", "styles", "badee_theme.css")


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
# EN-TÊTE AVEC LOGO (bandeau vert foncé assorti au fond du logo)
# ============================================================
def logo_base64():
    if not os.path.exists(LOGO_PATH):
        return None
    with open(LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()

_logo_b64 = logo_base64()
_logo_html = (
    f'<img src="data:image/png;base64,{_logo_b64}" width="90" alt="Logo BADEE">'
    if _logo_b64 else
    '<div style="width:90px;height:35px;display:flex;align-items:center;'
    'justify-content:center;color:white;font-weight:700;">BADEE</div>'
)

st.markdown(f"""
<div class="badee-header">
    {_logo_html}
    <div>
        <p class="badee-header-title">Assistant de rédaction LinkedIn</p>
        <p class="badee-header-subtitle">BADEE — Social &amp; Inclusive Business Builder, INNOVX</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# BANDEAU DE VALIDATION HUMAINE
# ============================================================
st.markdown("""
<div class="validation-banner">
    <span>⚠</span> Validation humaine obligatoire avant toute publication
</div>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR — PARAMÈTRES
# ============================================================
with st.sidebar:
    if logo:
        st.image(logo, width=100)

    st.markdown("### Paramètres")

    modele_choisi = st.selectbox(
        "Modèle de langage",
        options=list(MODELES_A_COMPARER.keys()),
        index=list(MODELES_A_COMPARER.keys()).index(MODELE_ACTIF),
    )
    st.caption(f"Fournisseur : {MODELES_A_COMPARER[modele_choisi]['provider']}")

    st.divider()

    if st.button("Réinitialiser la conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.markdown("### Version")
    st.caption("""
    **V1 — Proof of Concept**

    - Génération de brouillons
    - Assistance conversationnelle
    - Modèles : Gemma, Llama 3.3

    **Limites :**
    - Pas de connexion aux données réelles
    - Pas de publication automatique
    """)

    st.divider()

    st.markdown("### Identité visuelle")
    st.color_picker("Jaune", "#FFE144", disabled=True)
    st.color_picker("Vert clair", "#209138", disabled=True)
    st.color_picker("Violet", "#67569D", disabled=True)
    st.color_picker("Vert foncé", "#125D21", disabled=True)


# ============================================================
# HISTORIQUE DE CONVERSATION
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# ZONE DE SAISIE
# ============================================================
prompt_utilisateur = st.chat_input("Décrivez le post que vous souhaitez rédiger...")

if prompt_utilisateur:
    st.session_state.messages.append({"role": "user", "content": prompt_utilisateur})
    with st.chat_message("user"):
        st.markdown(prompt_utilisateur)

    with st.chat_message("assistant"):
        with st.spinner("Rédaction en cours..."):
            try:
                reponse = generer_reponse(modele_choisi, st.session_state.messages)
                st.markdown(reponse)
                st.session_state.messages.append({"role": "assistant", "content": reponse})

                st.markdown("""
                <div class="validation-banner">
                    <span>⚠</span> Brouillon à valider par un responsable avant publication
                </div>
                """, unsafe_allow_html=True)

            except ValueError as e:
                st.error(str(e))


# ============================================================
# PIED DE PAGE
# ============================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #67569D; font-size: 0.8rem;">
    BADEE — Assistant de rédaction LinkedIn &bull; V1 Proof of Concept
</div>
""", unsafe_allow_html=True)