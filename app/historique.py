"""
Gestion de l'historique multi-conversations.

Chaque conversation est identifiée par un id (horodatage de création), possède
un titre généré automatiquement à partir du premier message utilisateur, et sa
propre liste de messages. Remplace l'ancien système à conversation unique
(data/conversation_history.json) qui écrasait tout à chaque réinitialisation.

Fichier de stockage : data/conversations.json
Structure :
{
    "conversation_active": "20260817_143000",
    "conversations": [
        {
            "id": "20260817_143000",
            "titre": "Teaser Maison&Objet Paris",
            "messages": [{"role": "user", "content": "..."}, ...],
            "derniere_maj": "2026-08-17T14:35:12"
        },
        ...
    ]
}
"""

import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVERSATIONS_PATH = os.path.join(BASE_DIR, "data", "conversations.json")

LONGUEUR_MAX_TITRE = 45
TITRE_PAR_DEFAUT = "Nouvelle conversation"


def _structure_vide():
    return {"conversation_active": None, "conversations": []}


def charger_conversations():
    """Charge toutes les conversations depuis le disque. Structure vide si absent
    ou corrompu (le chatbot reste fonctionnel, une nouvelle conversation sera créée)."""
    if not os.path.exists(CONVERSATIONS_PATH):
        return _structure_vide()
    try:
        with open(CONVERSATIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("conversations", [])
            data.setdefault("conversation_active", None)
            return data
    except (json.JSONDecodeError, OSError):
        return _structure_vide()


def sauvegarder_conversations(data):
    """Sauvegarde l'ensemble des conversations sur disque."""
    os.makedirs(os.path.dirname(CONVERSATIONS_PATH), exist_ok=True)
    with open(CONVERSATIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generer_titre(premier_message: str) -> str:
    """Génère un titre lisible à partir du premier message utilisateur."""
    titre = premier_message.strip().replace("\n", " ")
    if len(titre) > LONGUEUR_MAX_TITRE:
        titre = titre[:LONGUEUR_MAX_TITRE].rstrip() + "…"
    return titre or TITRE_PAR_DEFAUT


def creer_conversation(data):
    """Crée une conversation vide, la marque comme active, et la retourne.
    Insérée en tête de liste (les plus récentes en premier dans la sidebar)."""
    conv_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    conversation = {
        "id": conv_id,
        "titre": TITRE_PAR_DEFAUT,
        "messages": [],
        "derniere_maj": datetime.now().isoformat(),
    }
    data["conversations"].insert(0, conversation)
    data["conversation_active"] = conv_id
    sauvegarder_conversations(data)
    return conversation


def obtenir_conversation_active(data):
    """Retourne la conversation active. En crée une nouvelle si aucune n'existe
    ou si l'id actif ne correspond à rien (première utilisation, ou conversation
    supprimée entre-temps)."""
    conv_id = data.get("conversation_active")
    for conv in data["conversations"]:
        if conv["id"] == conv_id:
            return conv
    return creer_conversation(data)


def mettre_a_jour_conversation(data, conv_id, messages):
    """Met à jour les messages d'une conversation et déduit son titre si c'est
    encore le titre par défaut (premier message reçu)."""
    for conv in data["conversations"]:
        if conv["id"] == conv_id:
            conv["messages"] = messages
            conv["derniere_maj"] = datetime.now().isoformat()
            if conv["titre"] == TITRE_PAR_DEFAUT and messages:
                premier_message_utilisateur = next(
                    (m["content"] for m in messages if m["role"] == "user"), None
                )
                if premier_message_utilisateur:
                    conv["titre"] = generer_titre(premier_message_utilisateur)
            break
    sauvegarder_conversations(data)


def definir_conversation_active(data, conv_id):
    """Bascule vers une conversation existante (clic dans la sidebar)."""
    data["conversation_active"] = conv_id
    sauvegarder_conversations(data)


def supprimer_conversation(data, conv_id):
    """Supprime une conversation. Si c'était l'active, bascule sur la plus
    récente restante, ou en crée une nouvelle s'il n'en reste aucune."""
    data["conversations"] = [c for c in data["conversations"] if c["id"] != conv_id]
    if data.get("conversation_active") == conv_id:
        if data["conversations"]:
            data["conversation_active"] = data["conversations"][0]["id"]
            sauvegarder_conversations(data)
        else:
            creer_conversation(data)  # sauvegarde déjà à l'intérieur
    else:
        sauvegarder_conversations(data)


def conversations_triees(data):
    """Conversations triées par date de dernière modification, plus récente
    en premier — pour l'affichage dans la sidebar."""
    return sorted(
        data["conversations"], key=lambda c: c["derniere_maj"], reverse=True
    )
