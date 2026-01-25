# Freya

Freya est une orchestratrice multi-agents avancée alignée sur le workflow BMAD (Business Model - Architecture - Development), conçue pour travailler avec des LLMs locaux via Ollama et Llama.cpp. Elle automatise le développement logiciel en coordonnant des agents spécialisés pour transformer un brief de projet en code de qualité.

## Fonctionnalités principales

- **Workflow BMAD complet** : De l'analyse métier à la livraison de code via des agents spécialisés
- **Support multi-backend LLM** : Ollama et Llama.cpp pour une flexibilité maximale
- **Benchmarking intelligent** : Routage automatique des modèles par rôle basé sur des benchmarks de performance
- **Interface TUI moderne** : Interface utilisateur textuelle interactive avec Textual
- **Agents spécialisés** :
  - Analyst : Analyse des exigences
  - Product Owner : Gestion des priorités métier
  - Architect : Conception technique
  - Scrum Master : Coordination d'équipe
  - Developer : Développement de code
  - QA : Assurance qualité
- **Outils intégrés** :
  - Shell : Exécution de commandes système
  - WebWatch : Surveillance web et scraping
- **Gestion de modèles** : Téléchargement, suivi et optimisation automatique
- **Sécurité renforcée** : Isolation des opérations dans des répertoires gérés

## Installation

```bash
pip install -e .
```

## Configuration

Freya utilise un système de configuration flexible via variables d'environnement :

- `FREYA_MANAGED_ROOT` : Répertoire de gestion (.freya par défaut)
- `FREYA_OLLAMA_URL` : URL du serveur Ollama (http://localhost:11434)
- `FREYA_LLAMACPP_EXE` : Chemin vers llama-server.exe
- `FREYA_GGUF_DIR` : Répertoire des modèles GGUF
- `FREYA_DISK_FREE_MIN_GB` : Espace disque minimum requis (40GB)

## Commandes

### Découverte et benchmarking

- `freya discover-models` : Liste les modèles Ollama installés
- `freya bench-fast` : Benchmark rapide (1 essai, mode quick)
- `freya bench-standard` : Benchmark standard (5 essais, mode tune)
- `freya bench-advanced` : Benchmark avancé (5 essais, mode tune)

### Interface utilisateur

- `freya tui` : Lance l'interface utilisateur textuelle interactive

## Interface TUI

L'interface TUI offre plusieurs onglets :

- **Chat** : Interaction directe avec les agents
- **Bench** : Gestion et visualisation des benchmarks
- **Dev** : Outils de développement intégrés
- **Settings** : Configuration avancée
- **Files** : Gestion des fichiers du projet
- **Watch** : Surveillance web en temps réel

## Workflow BMAD

1. **Business Model** : Analyse et brief du projet
2. **Architecture** : Conception technique et spécifications
3. **Development** : Implémentation itérative avec agents
4. **Delivery** : Code finalisé et testé

## Sécurité

Freya ne supprime jamais de fichiers en dehors de son répertoire `.freya`. Toutes les opérations sont isolées et les caches/logs sont gérés automatiquement.

## Serveurs LLM supportés

### Ollama

- Serveur par défaut : http://localhost:11434
- Routage automatique par rôle basé sur les benchmarks

### Llama.cpp

- Serveur configurable via `FREYA_LLAMACPP_*`
- Support des modèles GGUF locaux

## Développement

Freya est développée en Python 3.11+ avec les dépendances suivantes :

- pydantic : Validation de données
- requests : Communications HTTP
- rich : Interface console enrichie
- textual : Interface TUI
- psutil : Monitoring système
