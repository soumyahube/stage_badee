# BADEE — Assistant de rédaction LinkedIn (V1)

Chatbot conversationnel pour aider à la rédaction de brouillons de posts LinkedIn BADEE.
**V1 = proof of concept** : interface conversationnelle uniquement, sans connexion aux
données réelles. Voir `docs/limites_connues_v1.md` pour le détail des limites.

## Installation

```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
cp .env.example .env
```

Remplir `.env` avec tes clés :
- `OPENROUTER_API_KEY` — https://openrouter.ai/settings/keys
- `GROQ_API_KEY` — https://console.groq.com/keys

## Lancer l'application

```bash
streamlit run app/main.py
```

## Comparer les modèles

Avant de figer un modèle en production, lancer la comparaison sur les 3 scénarios
de référence (anglais, bilingue EN/FR, vœu en arabe) :

```bash
python tests/test_prompts_manuel.py
```

Résultats sauvegardés dans `docs/comparaison_modeles_<horodatage>.md`.

## Structure du projet

```
badee-agent-ia/
├── app/
│   ├── main.py            # interface Streamlit
│   ├── system_prompt.py   # règles de comportement et typologie
│   └── conversation.py    # appel LLM (Groq / OpenRouter)
├── config.py               # modèles comparés, modèle actif, paramètres
├── data/                   # contexte factuel BADEE
├── docs/                   # limites, scénarios de démo, comparaisons
├── outputs/                # brouillons générés
└── tests/                  # script de comparaison manuelle
```

## Modèles comparés (phase de test)
- Llama 3.3 70B — via Groq
- Gemma 4 26B — via OpenRouter
- gpt-oss-20b — via OpenRouter

Le modèle retenu est fixé dans `config.py` → `MODELE_ACTIF`.

## Contraintes du projet
- Validation humaine obligatoire à chaque étape — aucune publication automatique
- Infrastructure 100% gratuite (Groq, OpenRouter, Streamlit)
