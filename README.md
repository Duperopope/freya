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

## Architecture

Freya suit une architecture modulaire organisée autour de composants spécialisés :

```
freya2/
├── freya.ps1                    # Script PowerShell pour l'installation
├── pyproject.toml               # Configuration du projet Python
├── README.md                    # Documentation
├── bench_raw/                   # Données brutes des benchmarks
└── src/
    └── freya/
        ├── __init__.py          # Point d'entrée du package
        ├── cli.py               # Interface en ligne de commande
        ├── config.py            # Configuration centralisée
        ├── orchestrator.py      # Coordination des agents
        ├── router.py            # Routage intelligent des LLMs
        ├── tui.py               # Interface utilisateur textuelle
        ├── benchmarkq.py        # Suite de benchmarking
        ├── bmad_sync.py         # Synchronisation BMAD
        ├── console.py           # Utilitaires console
        ├── fsx.py               # Extensions système de fichiers
        ├── ide.py               # Contrôleur IDE
        ├── llamacpp_server.py  # Client Llama.cpp
        ├── loggingx.py          # Extensions de logging
        ├── model_manager.py     # Gestionnaire de modèles
        ├── monitoring.py        # Monitoring système
        ├── ollama_client.py     # Client Ollama
        ├── openai_compat_client.py # Compatibilité OpenAI
        ├── powershell.py        # Intégration PowerShell
        ├── quality.py           # Portes qualité
        ├── agents/              # Agents spécialisés
        │   ├── __init__.py
        │   ├── analyst.py       # Agent d'analyse
        │   ├── architect.py     # Agent architecte
        │   ├── base.py          # Classe de base des agents
        │   ├── dev.py           # Agent développeur
        │   ├── pm.py            # Agent Product Manager
        │   ├── po.py            # Agent Product Owner
        │   ├── qa.py            # Agent QA
        │   └── sm.py            # Agent Scrum Master
        └── tools/               # Outils intégrés
            ├── __init__.py
            ├── shell.py         # Outil shell
            └── webwatch.py      # Outil surveillance web
```

### Composants principaux

- **Orchestrator** : Cœur du système, coordonne les agents selon le workflow BMAD
- **Router** : Gère le routage des requêtes vers les LLMs appropriés basé sur les benchmarks
- **Agents** : Classes spécialisées pour chaque rôle du workflow de développement
- **Tools** : Utilitaires pour interagir avec le système et le web
- **Clients LLM** : Interfaces pour Ollama et Llama.cpp
- **TUI** : Interface utilisateur moderne avec Textual

### Architecture logique

### Architecture logique

#### Vue d'ensemble des interactions

```
                    ┌─────────────────┐
                    │   Interface     │
                    │   Utilisateur   │
                    │     (TUI)       │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Orchestrator   │
                    │                 │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │     Router      │
                    │  (LLM Routing)  │
                    └─────────┬───────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                    ▼         ▼         ▼
          ┌─────────────────┐ ┌───────┐ ┌───────┐
          │    Ollama       │ │Llama. │ │OpenAI │
          │    Client       │ │cpp    │ │Compat │
          └─────────────────┘ └───────┘ └───────┘

                    ┌─────────────────┐
                    │   Agents        │
                    │ Spécialisés     │
                    │                 │
                    │ • Analyst       │
                    │ • Architect     │
                    │ • Dev           │
                    │ • PM/PO/SM/QA   │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────┼─────────┐
                    │         │         │
                    ▼         ▼         ▼
          ┌─────────────────┐ ┌───────┐ ┌───────┐
          │     Tools       │ │Web-   │ │ IDE   │
          │    (Shell)      │ │Watch  │ │Ctrl   │
          └─────────────────┘ └───────┘ └───────┘

                    ┌─────────────────┐
                    │ Gestion         │
                    │ Système         │
                    │                 │
                    │ • Config        │
                    │ • Monitoring    │
                    │ • Quality       │
                    │ • Model Manager │
                    │ • Logger        │
                    │ • FSX           │
                    └─────────────────┘
```

#### Flux de données principal

1. **Interface** → **Orchestrator** : Transmission des commandes utilisateur
2. **Orchestrator** → **Router** : Sélection intelligente du LLM
3. **Router** → **Clients LLM** : Exécution des requêtes IA
4. **Orchestrator** → **Agents** : Coordination du workflow métier
5. **Agents** → **Tools** : Actions concrètes (shell, web, IDE)
6. **Gestion Système** : Support transversal (config, monitoring, qualité)

#### Relations fonctionnelles

- **Orchestrator ↔ BMAD Sync** : Gestion du workflow de développement
- **Router ↔ BenchmarkQ** : Optimisation des performances LLM
- **Agents ↔ Tools** : Exécution des tâches opérationnelles
- **TUI ↔ Tous composants** : Interface unifiée et visualisation
- **Gestion Système** : Infrastructure partagée et monitoring

#### Architecture en couches

```
┌─────────────────────────────────────┐
│         Interface Utilisateur       │
│               (TUI)                 │
├─────────────────────────────────────┤
│         Coordination                │
│        (Orchestrator)               │
├─────────────────────────────────────┤
│         Intelligence                │
│   (Router + BenchmarkQ + Agents)    │
├─────────────────────────────────────┤
│         Exécution                   │
│   (Clients LLM + Tools)             │
├─────────────────────────────────────┤
│         Infrastructure              │
│   (Config + Monitoring + Système)   │
└─────────────────────────────────────┘
```

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
