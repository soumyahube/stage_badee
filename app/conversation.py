"""
Gère l'appel au LLM (Groq ou OpenRouter selon le modèle configuré)
et l'historique de conversation.
"""

from openai import OpenAI
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROVIDERS, MODELES_A_COMPARER, TEMPERATURE, MAX_TOKENS
from app.system_prompt import SYSTEM_PROMPT


def get_client(provider: str) -> OpenAI:
    """Construit un client OpenAI compatible pour le provider demandé (groq ou openrouter)."""
    config_provider = PROVIDERS[provider]
    if not config_provider["api_key"]:
        raise ValueError(
            f"Clé API manquante pour '{provider}'. "
            f"Vérifie ton fichier .env (voir .env.example)."
        )
    return OpenAI(
        base_url=config_provider["base_url"],
        api_key=config_provider["api_key"],
    )


def generer_reponse(nom_modele: str, historique: list[dict]) -> str:
    """
    Envoie l'historique de conversation au modèle choisi et retourne la réponse texte.

    nom_modele : clé de config.MODELES_A_COMPARER (ex. "gemma4-26b")
    historique : liste de messages [{"role": "user"/"assistant", "content": "..."}]
    """
    if nom_modele not in MODELES_A_COMPARER:
        raise ValueError(f"Modèle inconnu : {nom_modele}. Voir config.MODELES_A_COMPARER.")

    infos_modele = MODELES_A_COMPARER[nom_modele]
    client = get_client(infos_modele["provider"])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + historique

    reponse = client.chat.completions.create(
        model=infos_modele["model_id"],
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    return reponse.choices[0].message.content
