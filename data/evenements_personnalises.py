"""
Gestion des événements personnalisés ajoutés par l'équipe BADEE.
Ces événements enrichissent le calendrier éditorial (scripts/calendrier_editorial.py)
utilisé par le système d'alerte de rappel de publication.

Fonctionne en deux modes :
- Supabase configuré (SUPABASE_URL + SUPABASE_KEY dans .env / secrets) : stockage
  persistant, partagé entre l'app Streamlit ET les scripts GitHub Actions.
- Sinon : repli en mémoire (liste Python au niveau du module) — permet de démontrer
  la fonctionnalité sans configuration préalable, utilisable aussi bien dans l'app
  Streamlit que dans les scripts autonomes. Les événements ne survivent pas à un
  redémarrage du processus (redéploiement, nouveau run GitHub Actions).
"""

import os
from datetime import date

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase_client = None
_supabase_disponible = False

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        _supabase_disponible = True
    except Exception:
        _supabase_disponible = False

# Repli mémoire — simple liste Python, partagée au sein du même processus,
# fonctionne aussi bien depuis l'app Streamlit que depuis un script autonome
_evenements_memoire = []
_prochain_id_memoire = [1]  # liste pour permettre la mutation dans une fonction


def supabase_actif() -> bool:
    """Indique si le stockage persistant Supabase est actif (sinon : mémoire seule)."""
    return _supabase_disponible


def ajouter_evenement(nom: str, date_evenement: date, message_suggere: str = "", ajoute_par: str = ""):
    """Ajoute un événement — vers Supabase si configuré, sinon en mémoire du processus."""
    if _supabase_disponible:
        _supabase_client.table("evenements_personnalises").insert({
            "nom": nom,
            "date_evenement": date_evenement.isoformat(),
            "message_suggere": message_suggere,
            "ajoute_par": ajoute_par,
        }).execute()
    else:
        _evenements_memoire.append({
            "id": _prochain_id_memoire[0],
            "nom": nom,
            "date_evenement": date_evenement.isoformat(),
            "message_suggere": message_suggere,
            "ajoute_par": ajoute_par,
        })
        _prochain_id_memoire[0] += 1


def lister_evenements():
    """Retourne tous les événements personnalisés, triés par date."""
    if _supabase_disponible:
        result = _supabase_client.table("evenements_personnalises") \
            .select("*").order("date_evenement").execute()
        return result.data
    else:
        return sorted(_evenements_memoire, key=lambda e: e["date_evenement"])


def supprimer_evenement(evenement_id):
    """Supprime un événement par son id."""
    global _evenements_memoire
    if _supabase_disponible:
        _supabase_client.table("evenements_personnalises").delete().eq("id", evenement_id).execute()
    else:
        _evenements_memoire = [e for e in _evenements_memoire if e["id"] != evenement_id]
