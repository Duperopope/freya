# Freya

[![English](https://img.shields.io/badge/Language-English-blue.svg)](README.md) [![Français](https://img.shields.io/badge/Langue-Français-red.svg)](README.fr.md)

[![Built with AI](https://img.shields.io/badge/Built%20with-AI-FF6B6B.svg)](https://github.com/features/copilot) [![AI-Powered](https://img.shields.io/badge/AI--Powered-Yes-9C88FF.svg)](https://ollama.ai) [![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-00ADD8.svg)](https://ollama.ai) [![Llama.cpp](https://img.shields.io/badge/Supports-Llama.cpp-FF6B35.svg)](https://github.com/ggerganov/llama.cpp)

[![Llama 3.1](https://img.shields.io/badge/Model-Llama%203.1-FF6B35.svg)](https://ollama.ai/library/llama3.1) [![Mistral](https://img.shields.io/badge/Model-Mistral-9C88FF.svg)](https://ollama.ai/library/mistral) [![Qwen](https://img.shields.io/badge/Model-Qwen-00ADD8.svg)](https://ollama.ai/library/qwen) [![CodeLlama](https://img.shields.io/badge/Model-CodeLlama-FF6B6B.svg)](https://ollama.ai/library/codellama) [![Dolphin](https://img.shields.io/badge/Model-Dolphin-9C88FF.svg)](https://ollama.ai/library/dolphin-llama3)

Freya est un orchestrateur multi-agent avancé aligné sur le workflow BMAD (Business Model - Architecture - Development), conçu pour fonctionner avec des LLMs locaux via Ollama et Llama.cpp. Il automatise le développement logiciel en coordonnant des agents spécialisés pour transformer un brief de projet en code de qualité.

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
  - WebWatch : Surveillance et scraping web
- **Gestion des modèles** : Téléchargement automatique, suivi et optimisation
- **Sécurité renforcée** : Isolation des opérations dans des répertoires gérés

## Architecture

Freya suit une architecture modulaire organisée autour de composants spécialisés :

```
freya2/
├── freya.ps1                    # Script d'installation PowerShell
├── pyproject.toml               # Configuration du projet Python
├── README.md                    # Documentation
├── bench_raw/                   # Données brutes de benchmark
└── src/
    └── freya/
        ├── __init__.py          # Point d'entrée du package
        ├── cli.py               # Interface ligne de commande
        ├── config.py            # Configuration centralisée
        ├── orchestrator.py      # Coordination des agents
        ├── router.py            # Routage intelligent LLM
        ├── tui.py               # Interface utilisateur textuelle
        ├── benchmarkq.py        # Suite de benchmarking
        ├── bmad_sync.py         # Synchronisation BMAD
        ├── console.py           # Utilitaires console
        ├── fsx.py               # Extensions système de fichiers
        ├── ide.py               # Contrôleur IDE
        ├── llamacpp_server.py  # Client Llama.cpp
        ├── loggingx.py          # Extensions de logging
        ├── model_manager.py     # Gestionnaire de modèles
        ├── monitoring.py        # Surveillance système
        ├── ollama_client.py     # Client Ollama
        ├── openai_compat_client.py # Compatibilité OpenAI
        ├── powershell.py        # Intégration PowerShell
        ├── quality.py           # Portes de qualité
        ├── agents/              # Agents spécialisés
        │   ├── __init__.py
        │   ├── analyst.py       # Agent d'analyse
        │   ├── architect.py     # Agent d'architecture
        │   ├── base.py          # Classe d'agent de base
        │   ├── dev.py           # Agent développeur
        │   ├── pm.py            # Agent Product Manager
        │   ├── po.py            # Agent Product Owner
        │   ├── qa.py            # Agent QA
        │   └── sm.py            # Agent Scrum Master
        └── tools/               # Outils intégrés
            ├── __init__.py
            ├── shell.py         # Outil Shell
            └── webwatch.py      # Outil de surveillance web
```

- **Orchestrator** : Noyau du système, coordonne les agents selon le workflow BMAD
- **Router** : Gère le routage des requêtes vers les LLMs appropriés basés sur les benchmarks
- **Agents** : Classes spécialisées pour chaque rôle du workflow de développement
- **Tools** : Utilitaires pour interagir avec le système et le web
- **LLM Clients** : Interfaces pour Ollama et Llama.cpp
- **TUI** : Interface utilisateur moderne avec Textual
- **CLI** : Interface ligne de commande pour l'automatisation et les scripts

### Architecture logique

#### Aperçu des interactions

```
                    ┌─────────────────┐
                    │   Utilisateur   │
                    │   Interface     │
                    │   (TUI/CLI)     │
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
                    │  (Routage LLM)  │
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
                    │   spécialisés   │
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
          │     Outils      │ │Web-   │ │ IDE   │
          │    (Shell)      │ │Watch  │ │Ctrl   │
          └─────────────────┘ └───────┘ └───────┘

                    ┌─────────────────┐
                    │ Gestion         │
                    │ système         │
                    │                 │
                    │ • Config        │
                    │ • Monitoring    │
                    │ • Quality       │
                    │ • Model Manager │
                    │ • Logger        │
                    │ • FSX           │
                    └─────────────────┘
```

1. **Interface** → **Orchestrator** : Transmission des commandes utilisateur
2. **Orchestrator** → **Router** : Sélection intelligente de LLM
3. **Router** → **Clients LLM** : Exécution des requêtes IA
4. **Orchestrator** → **Agents** : Coordination du workflow métier
5. **Agents** → **Outils** : Actions concrètes (shell, web, IDE)
6. **Gestion système** : Support transversal (config, monitoring, qualité)

- **Orchestrator ↔ BMAD Sync** : Gestion du workflow de développement
- **Router ↔ BenchmarkQ** : Optimisation des performances LLM
- **Agents ↔ Outils** : Exécution des tâches opérationnelles
- **Interface (TUI/CLI) ↔ Tous les composants** : Interface et visualisation unifiées
- **Gestion système** : Infrastructure et monitoring partagés

#### Architecture en couches

```
┌─────────────────────────────────────┐
│         Interface utilisateur       │
│             (TUI/CLI)               │
├─────────────────────────────────────┤
│         Coordination                │
│        (Orchestrator)               │
├─────────────────────────────────────┤
│         Intelligence                │
│   (Router + BenchmarkQ + Agents)    │
├─────────────────────────────────────┤
│         Exécution                   │
│   (Clients LLM + Outils)            │
├─────────────────────────────────────┤
│         Infrastructure              │
│   (Config + Monitoring + Système)   │
└─────────────────────────────────────┘
```

## Démarrage rapide (Windows)

### 1) Installation (éditable)

```powershell
cd H:\Code\Freya2
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e .
```

Freya utilise un système de configuration flexible via des variables d'environnement :

- `FREYA_MANAGED_ROOT` : Répertoire de gestion (.freya par défaut)
- `FREYA_OLLAMA_URL` : URL du serveur Ollama (http://localhost:11434)
- `FREYA_LLAMACPP_EXE` : Chemin vers llama-server.exe
- `FREYA_GGUF_DIR` : Répertoire pour les modèles GGUF
- `FREYA_DISK_FREE_MIN_GB` : Espace disque minimum requis (40GB)

## Commandes

### Découverte et benchmarking

- `freya discover-models` : Lister les modèles Ollama installés
- `freya bench-fast` : Benchmark rapide (1 essai, mode rapide)
- `freya bench-standard` : Benchmark standard (5 essais, mode réglage)
- `freya bench-advanced` : Benchmark avancé (5 essais, mode réglage)

### Interface utilisateur

- `freya tui` : Lancer l'interface utilisateur textuelle interactive

L'interface TUI offre plusieurs onglets :

- **Chat** : Interaction directe avec les agents
- **Bench** : Gestion et visualisation des benchmarks
- **Dev** : Outils de développement intégrés
- **Settings** : Configuration avancée
- **Files** : Gestion des fichiers de projet
- **Watch** : Surveillance web en temps réel

1. **Business Model** : Analyse et briefing de projet
2. **Architecture** : Conception technique et spécifications
3. **Development** : Implémentation itérative avec agents
4. **Delivery** : Code finalisé et testé

Freya ne supprime jamais de fichiers en dehors de son répertoire `.freya`. Toutes les opérations sont isolées et les caches/logs sont automatiquement gérés.

## Serveurs LLM supportés

- Serveur par défaut : http://localhost:11434
- Routage automatique par rôle basé sur les benchmarks

- Serveur configurable via `FREYA_LLAMACPP_*`
- Support pour les modèles GGUF locaux

Freya est développé en Python 3.11+ avec les dépendances suivantes :

- pydantic : Validation des données
- requests : Communications HTTP
- rich : Interface console améliorée
- textual : Framework TUI
- psutil : Surveillance système

## Version

Version actuelle : **1.1.6**

## Notes de patch

### v1.1.6 (26 janvier 2026)

- Améliorations majeures de l'interface TUI avec fonctionnalités étendues
- Mises à jour significatives du système de configuration avec de nouvelles options
- Routage LLM amélioré et optimisations de performance
- Commandes CLI supplémentaires et gestion améliorée des commandes

### v1.1.5 (25 janvier 2026)

- Consolidation du README en un seul fichier bilingue (Anglais & Français)
- Ajout d'une section Commandes (CLI) complète avec commande autopilot
- Ajout d'un aperçu Architecture de haut niveau avec diagramme simplifié
- Ajout de directives de sécurité et recommandations
- Ajout de recommandations pour polices et icônes pour l'affichage terminal
- Ajout de statut et roadmap avec fonctionnalités actuelles et développements à venir
- Ajout de section Références / Sources avec liens pertinents
- Mise à jour du Démarrage rapide avec étapes d'installation Windows détaillées
- Suppression du fichier README français séparé redondant
- Mise à jour des badges de langue pour refléter la documentation bilingue unifiée

### v1.1 (25 janvier 2026)

- Ajout du support CaskaydiaCove Nerd Font pour un affichage terminal amélioré
- Amélioration du TUI avec intégration presse-papiers (copier la dernière réponse)
- Ajout de barres de progression en direct pour les benchmarks et contrôles
- Amélioration de la gestion des artefacts avec survol et sélection
- Ajout de nouveaux outils : clipboard.py et redact.py pour la sécurité
- Mise à jour de la disposition UI avec de meilleures proportions (60/40)
- Ajout de fonctionnalité d'ouverture d'espace de travail VS Code
- Amélioration du logging de chat avec rendu Markdown et panneaux
- Ajout d'intégration du statut PowerShell dans le TUI
- Amélioration de Cyber Watch avec un meilleur formatage et priorisation
- Ajout de suivi de progression pour les phases de benchmark et modèles
- Correction de la gestion asynchrone dans le rechargement de l'arbre des artefacts TUI pour une meilleure stabilité

## Commandes (CLI)

### Gestion des modèles

- `freya discover-models` — lister les modèles Ollama installés

### Benchmarking

- `freya bench-fast` — rapide (1 essai)
- `freya bench-standard` — standard (5 essais)
- `freya bench-advanced` — avancé (5 essais)

### UI

- `freya tui` — lancer l'interface Textual

### Automatisation de livraison

- `freya autopilot --goal ... --name ... --output ...` — générer un projet + tests + ouvrir VS Code

## Architecture (haut niveau)

Freya est conçu comme un système modulaire :

- **CLI (freya)** : commandes (discover/bench/tui/autopilot)
- **Router (LLMRouter)** : bench + routage des requêtes vers le meilleur modèle
- **Clients LLM** : Ollama (et optionnellement serveur llama.cpp)
- **TUI (Textual)** : UI terminal
- **Autopilot** : pipeline reproductible "projet → code → tests → validation → VS Code"
- **Artefacts & logs** : événements JSONL et état reprenable

### Diagramme logique (simplifié)

```
Utilisateur (TUI/CLI)
   |
   v
Orchestrator / Autopilot
   |
   +--> Router (bench + choisir le meilleur modèle)
   |         |
   |         +--> Ollama / llama.cpp
   |
   +--> Outils (shell / surveillance web / fs / ide)
   |
   +--> Artefacts + Logs (JSONL) + État (reprendre)
```

## Sécurité

- **Local-first** : exécution locale, modèles locaux.
- **Traçabilité** : logs d'événements (JSONL) pour diagnostic/replay.
- **Recommandation forte** : ne jamais coller de tokens/clés en texte clair dans l'UI, les prompts ou les logs.

## Polices & icônes (recommandées)

Pour un rendu propre (icônes terminal), utilisez une Nerd Font dans Windows Terminal (ex: CaskaydiaCove Nerd Font) puis configurez le profil.

## Statut & roadmap

### ✅ Déjà opérationnel :

- CLI (discover, bench, tui)
- Bench + routage (sélection par rôle)
- Autopilot V1 (projet + tests + ouverture VS Code)

### 🔜 À venir de manière itérative :

- Orchestrateur BMAD complet (artefacts + run/resume)
- Boucle Dev/QA "tests échouant → patch → retest" via LLMRouter
- Chat Bench dédié / Résumé / Recherche web
- Paramètres remplis et éditables (prompts/préréglages/chapeaux)
- Cyber Watch (watch) via sources publiques (API/RSS), formaté FR

## Références / Sources

- **Méthode BMAD** (workflow & artefacts) : https://github.com/bmad-code-org/BMAD-METHOD
- **API Ollama** (tags/generate) : https://github.com/ollama/ollama/blob/main/docs/api.md
- **llama.cpp** (server) : https://github.com/ggerganov/llama.cpp
- **Textual** (framework TUI) : https://textual.textualize.io/
- **VS Code CLI** (code) : https://code.visualstudio.com/docs/editor/command-line
- **Python venv** : https://docs.python.org/3/library/venv.html
- **Pytest** : https://docs.pytest.org/en/stable/
- **Paramètres Windows Terminal** (polices, profils) : https://learn.microsoft.com/windows/terminal/customize-settings/profile-settings
- **Nerd Fonts** : https://www.nerdfonts.com/
