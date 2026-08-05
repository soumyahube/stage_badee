# Limites connues — V1 (Proof of Concept)

Ce document doit être présenté explicitement lors de la démo. V1 est un **proof of concept**
de l'interface conversationnelle uniquement — pas une version connectée aux données réelles.

## Ce que V1 fait
- Dialogue avec l'utilisateur pour clarifier le type de post, le sujet, la langue
- Génération d'un brouillon de post LinkedIn respectant la typologie et les règles
  linguistiques identifiées dans l'état des lieux
- Comparaison possible entre plusieurs modèles LLM (Groq / OpenRouter)

## Ce que V1 ne fait PAS
- Aucune connexion à une base de données ou à l'historique réel des posts BADEE
- Aucune connexion à l'API LinkedIn — pas de récupération automatique de contexte
- Aucune publication automatique, sous aucune condition
- Aucune mémoire persistante entre les sessions (l'historique se perd à la fermeture)
- Aucune vérification factuelle automatique — l'utilisateur doit fournir des informations
  exactes (dates, chiffres, noms de partenaires) ; le modèle ne doit rien inventer,
  mais reste sous la responsabilité de relecture humaine

## Dépendances externes (hors contrôle du projet)
- Les modèles gratuits utilisés (Groq, OpenRouter) sont soumis aux conditions de leurs
  fournisseurs respectifs — disponibilité et limites de requêtes peuvent changer
- Aucun engagement de disponibilité garanti sur les tiers gratuits

## Prochaine étape (V2)
Connexion aux données réelles (Supabase), accès aux posts existants comme référence
de ton, et éventuellement suggestions basées sur les performances passées.
