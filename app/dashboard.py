"""
Dashboard de reporting — vue statistiques d'engagement.
V1 : Proof of concept sur données simulées (basées sur l'audit réel du
5 juillet 2026). À connecter à l'API LinkedIn + Supabase quand l'accès
sera obtenu (voir data/Ressource_API_LinkedIn.docx pour la procédure).

Appelé depuis main.py — ne pas lancer ce fichier directement.
"""

import streamlit as st
import plotly.express as px
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.data_simulee import (
    KPI_GLOBAUX, REPARTITION_CATEGORIES, TOP_POSTS, FLOP_POSTS, EVOLUTION_MENSUELLE
)

# Couleurs BADEE pour cohérence visuelle avec le reste de l'app
COULEUR_PRIMAIRE = "#209138"
COULEUR_SECONDAIRE = "#67569D"
COULEUR_ACCENT = "#125D21"
PALETTE = ["#209138", "#67569D", "#FFE144", "#125D21", "#8B7BC0", "#5CB876"]


def afficher_dashboard():
    st.markdown("""
    <div class="validation-banner">
        <span>⚠</span> Données simulées — basées sur l'audit manuel du 5 juillet 2026.
        Connexion à l'API LinkedIn requise pour des données en temps réel.
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # INDICATEURS CLÉS
    # ============================================================
    st.markdown("### Indicateurs clés")
    col1, col2, col3, col4 = st.columns(4)
    li = KPI_GLOBAUX["linkedin"]
    with col1:
        st.metric("Abonnés LinkedIn", f"{li['abonnes']:,}".replace(",", " "))
    with col2:
        st.metric("Likes moyen / post", li["likes_moyen"])
    with col3:
        st.metric("Commentaires moyen / post", li["commentaires_moyen"])
    with col4:
        st.metric("Fréquence de publication", f"{li['frequence_mensuelle']} /mois")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # RÉPARTITION PAR CATÉGORIE
    # ============================================================
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### Répartition des posts par catégorie")
        fig_cat = px.bar(
            REPARTITION_CATEGORIES.sort_values("volume", ascending=True),
            x="volume", y="categorie", orientation="h",
            color="categorie", color_discrete_sequence=PALETTE,
            text="volume",
        )
        fig_cat.update_layout(
            showlegend=False, height=320,
            margin=dict(l=0, r=10, t=10, b=10),
            xaxis_title="Nombre de posts", yaxis_title="",
            plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_right:
        st.markdown("#### Engagement moyen par catégorie")
        fig_eng = px.bar(
            REPARTITION_CATEGORIES.sort_values("likes_moyen", ascending=True),
            x="likes_moyen", y="categorie", orientation="h",
            color="categorie", color_discrete_sequence=PALETTE,
            text="likes_moyen",
        )
        fig_eng.update_layout(
            showlegend=False, height=320,
            margin=dict(l=0, r=10, t=10, b=10),
            xaxis_title="Likes moyen", yaxis_title="",
            plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig_eng, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # ÉVOLUTION MENSUELLE
    # ============================================================
    st.markdown("#### Évolution de l'engagement (illustratif)")
    fig_evol = px.line(
        EVOLUTION_MENSUELLE, x="mois", y="likes_total", markers=True,
    )
    fig_evol.update_traces(line_color=COULEUR_PRIMAIRE, line_width=3, marker_size=8)
    fig_evol.update_layout(
        height=280, margin=dict(l=0, r=10, t=10, b=10),
        xaxis_title="", yaxis_title="Total likes",
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig_evol, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # TOP / FLOP POSTS
    # ============================================================
    col_top, col_flop = st.columns(2)
    with col_top:
        st.markdown("#### 🟢 Top posts")
        st.dataframe(
            TOP_POSTS, hide_index=True, use_container_width=True,
            column_config={
                "post": "Post",
                "categorie": "Catégorie",
                "likes": st.column_config.NumberColumn("Likes", format="%d ❤️"),
                "commentaires": st.column_config.NumberColumn("Comm.", format="%d 💬"),
            },
        )
    with col_flop:
        st.markdown("#### 🔴 Posts les moins engageants")
        st.dataframe(
            FLOP_POSTS, hide_index=True, use_container_width=True,
            column_config={
                "post": "Post",
                "categorie": "Catégorie",
                "likes": st.column_config.NumberColumn("Likes", format="%d ❤️"),
                "commentaires": st.column_config.NumberColumn("Comm.", format="%d 💬"),
            },
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # LINKEDIN VS INSTAGRAM
    # ============================================================
    st.markdown("#### LinkedIn vs Instagram")
    ig = KPI_GLOBAUX["instagram"]
    comparaison = {
        "Plateforme": ["LinkedIn", "Instagram"],
        "Abonnés": [li["abonnes"], ig["abonnes"]],
        "Posts analysés": [li["posts_analyses"], ig["posts_analyses"]],
        "Likes moyen": [li["likes_moyen"], ig["likes_moyen"]],
        "Fréquence /mois": [li["frequence_mensuelle"], ig["frequence_mensuelle"]],
    }
    st.dataframe(comparaison, hide_index=True, use_container_width=True)

    st.caption(
        "Sources : audit manuel du 5 juillet 2026 (31 posts LinkedIn, 6 posts Instagram). "
        "Pour des données actualisées en continu, une connexion à l'API LinkedIn est nécessaire."
    )
