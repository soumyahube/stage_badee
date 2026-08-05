"""
Configuration centralisée du projet.
Modifier MODELE_ACTIF pour changer de modèle sans toucher au reste du code.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Providers disponibles ---
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": os.getenv("GROQ_API_KEY"),
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
    },
}

# --- Modèles à comparer (phase de test) ---
# Ajouter/retirer des entrées ici pour élargir ou réduire la comparaison
MODELES_A_COMPARER = {
    "llama3.3-70b": {
        "provider": "groq",
        "model_id": "llama-3.3-70b-versatile",
    },
    "gemma4-26b": {
        "provider": "openrouter",
        "model_id": "google/gemma-4-26b-a4b-it:free",
    },
    "gpt-oss-20b": {
        "provider": "openrouter",
        "model_id": "openai/gpt-oss-20b:free",
    },
}

# --- Modèle actif par défaut (utilisé par l'app Streamlit) ---
# Changer cette valeur une fois la comparaison terminée et le modèle choisi
MODELE_ACTIF = "gemma4-26b"

# --- Paramètres de génération ---
TEMPERATURE = 0.7
MAX_TOKENS = 800

# --- Langue par défaut (règle métier) ---
# Anglais par défaut ; bilingue EN/FR pour événements ; arabe ajouté pour vœux/commémorations
LANGUE_PAR_DEFAUT = "anglais"
