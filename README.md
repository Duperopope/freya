# Freya (V0.1)

Freya est une orchestratrice multi-agents alignée sur le workflow BMAD:
project-brief.md -> PRD.md -> architecture.md -> epic-_.md -> _.story.md -> code -> QA

## Commandes

- freya init
- freya sync-bmad
- freya bench
- freya run --goal "..."
- freya status

## Notes sécurité

Freya ne supprime jamais en dehors de son dossier .freya.
Le nettoyage s'applique uniquement aux caches/logs/runs gérés par Freya.

## Ollama

- Serveur: http://localhost:11434
- Les modèles sont routés par rôle (Analyst/PM/etc.) avec un micro-benchmark.
