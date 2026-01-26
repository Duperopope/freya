# Freya 2.1

[![English](https://img.shields.io/badge/Language-English-blue.svg)](README.md) [![Français](https://img.shields.io/badge/Langue-Français-red.svg)](README.fr.md)

[![Built with AI](https://img.shields.io/badge/Built%20with-AI-FF6B6B.svg)](https://github.com/features/copilot) [![AI-Powered](https://img.shields.io/badge/AI--Powered-Yes-9C88FF.svg)](https://ollama.ai) [![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-00ADD8.svg)](https://ollama.ai) [![Llama.cpp](https://img.shields.io/badge/Supports-Llama.cpp-FF6B35.svg)](https://github.com/ggerganov/llama.cpp)

[![Version](https://img.shields.io/badge/Version-2.1.0-green.svg)](#) [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org) [![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev) [![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com) [![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://typescriptlang.org) [![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-38BDF8.svg)](https://tailwindcss.com)

---

<p align="center">
  <img src="web/public/freya-icon.svg" alt="Freya Logo" width="120" />
</p>

<h3 align="center">Orchestrateur Multi-Agents aligné BMAD pour LLMs Locaux</h3>

<p align="center">
  <strong>Moderne • Temps Réel • Respect de la Vie Privée</strong>
</p>

---

## Nouveautés v2.1

**Freya 2.1** enrichit l'interface web moderne avec des fonctionnalités avancées et une expérience utilisateur améliorée :

### Améliorations Principales

- **Recherche Web Gratuite** - Support DuckDuckGo et SearXNG, sans clés API requises
- **Cyber Watch Amélioré** - 8+ sources de sécurité incluant NVD, Exploit-DB, GitHub Security Advisories
- **Système de Thèmes Live** - Changement de thème en temps réel (Dark, Light, Midnight)
- **Paramètres Éditables** - Gestion complète de la configuration incluant chemins personnalisés et intégrations API
- **Auto-refresh Configurable** - Timestamps visibles et rafraîchissement configurable sur tous les dashboards

### Nouvelles Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| **Recherche Multi-providers** | DuckDuckGo, SearXNG, Wikipedia, Brave |
| **Intégration Dépôts** | Support API GitHub/GitLab pour accès repos BMAD |
| **Dashboard Cyber Avancé** | Visualisation temps réel des attaques globales |
| **Résultats Benchmark Extensibles** | Métriques détaillées par modèle avec export |
| **Export Erreurs JSON** | Export normalisé des erreurs pour debugging |
| **Support Polices Personnalisées** | Cascadia Code, Fira Code, JetBrains Mono |

---

## Architecture Système

### Architecture Haut Niveau

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FREYA 2.1                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND (React 18 + TypeScript)                  │   │
│  │                                                                      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │  Chat   │ │  Bench  │ │  BMAD   │ │  Watch  │ │Settings │       │   │
│  │  │  Page   │ │  Page   │ │ Studio  │ │  Page   │ │  Page   │       │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │   │
│  │       │           │           │           │           │             │   │
│  │  ┌────┴───────────┴───────────┴───────────┴───────────┴────┐       │   │
│  │  │              Zustand Store (Gestion d'État)              │       │   │
│  │  │   • AppStore • BenchProgress • SystemStatus • Theme      │       │   │
│  │  └────────────────────────────┬─────────────────────────────┘       │   │
│  │                               │                                      │   │
│  │  ┌────────────────────────────┴─────────────────────────────┐       │   │
│  │  │          TanStack Query (Récupération + Cache)           │       │   │
│  │  └────────────────────────────┬─────────────────────────────┘       │   │
│  │                               │                                      │   │
│  │  ┌────────────────────────────┴─────────────────────────────┐       │   │
│  │  │                  Client API (api.ts)                      │       │   │
│  │  │  • Type-safe • Gestion erreurs • Support WebSocket        │       │   │
│  │  └────────────────────────────┬─────────────────────────────┘       │   │
│  └───────────────────────────────│──────────────────────────────────────┘   │
│                                  │                                          │
│                         HTTP/REST & WebSocket                               │
│                                  │                                          │
│  ┌───────────────────────────────┴──────────────────────────────────────┐   │
│  │                      BACKEND (FastAPI + Python)                       │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │                    Couche API (/api/*)                       │     │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │     │   │
│  │  │  │ /chat  │ │ /bench │ │ /bmad  │ │ /watch │ │/settings│    │     │   │
│  │  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘    │     │   │
│  │  │      └──────────┴──────────┴──────────┴──────────┘          │     │   │
│  │  │                         │                                    │     │   │
│  │  │  ┌──────────────────────┴────────────────────────────┐      │     │   │
│  │  │  │              Gestionnaire WebSocket                │      │     │   │
│  │  │  │   Canaux: BENCH | CHAT | BMAD | SYSTEM | LOGS     │      │     │   │
│  │  │  └───────────────────────────────────────────────────┘      │     │   │
│  │  └──────────────────────────────────────────────────────────────┘     │   │
│  │                                  │                                    │   │
│  │  ┌───────────────────────────────┴────────────────────────────┐      │   │
│  │  │                     Services Principaux                     │      │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │      │   │
│  │  │  │Orchestrateur│  │  LLM Router │  │  Moniteur   │         │      │   │
│  │  │  │  (Agents)   │  │ (Benchmark) │  │  (Système)  │         │      │   │
│  │  │  └──────┬──────┘  └──────┬──────┘  └─────────────┘         │      │   │
│  │  │         │                │                                  │      │   │
│  │  │  ┌──────┴────────────────┴──────────────────────────┐      │      │   │
│  │  │  │              Client Ollama (HTTP)                 │      │      │   │
│  │  │  │     URL Base: http://localhost:11434             │      │      │   │
│  │  │  └──────────────────────────────────────────────────┘      │      │   │
│  │  └────────────────────────────────────────────────────────────┘      │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────┐      │   │
│  │  │                     Outils Intégrés                         │      │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │      │   │
│  │  │  │WebSearch │  │WebWatch  │  │  Shell   │  │ Clipboard│   │      │   │
│  │  │  │DuckDuckGo│  │CISA/NVD  │  │  Secure  │  │  Système │   │      │   │
│  │  │  │Wikipedia │  │CERT-FR   │  │  Sandbox │  │  Accès   │   │      │   │
│  │  │  │SearXNG   │  │Exploit-DB│  │          │  │          │   │      │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │      │   │
│  │  └────────────────────────────────────────────────────────────┘      │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pipeline d'Agents BMAD

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PIPELINE WORKFLOW BMAD                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌───────────┐                                                           │
│    │  OBJECTIF │  L'utilisateur fournit l'objectif du projet               │
│    └─────┬─────┘                                                           │
│          │                                                                  │
│          ▼                                                                  │
│    ╔═══════════════╗                                                       │
│    ║   ANALYSTE    ║ ─────────────────────▶ project-brief.md               │
│    ║  Besoins      ║     Analyse des besoins, identification               │
│    ╚═══════╤═══════╝     des parties prenantes, définition du scope        │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║      PM       ║ ─────────────────────▶ PRD.md                         │
│    ║   Produit     ║     Document d'exigences produit,                     │
│    ╚═══════╤═══════╝     fonctionnalités, vue d'ensemble user stories      │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║  ARCHITECTE   ║ ─────────────────────▶ architecture.md                │
│    ║   Technique   ║     Conception système, stack technique,              │
│    ╚═══════╤═══════╝     architecture composants, APIs                     │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║      PO       ║ ─────────────────────▶ epics/*.md                     │
│    ║ Product Owner ║     Découpage en epics, priorisation                  │
│    ╚═══════╤═══════╝     fonctionnalités, roadmap                          │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║      SM       ║ ─────────────────────▶ stories/*.md                   │
│    ║ Scrum Master  ║     User stories, critères d'acceptation,             │
│    ╚═══════╤═══════╝     planification sprints                             │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║  DÉVELOPPEUR  ║ ─────────────────────▶ code/                          │
│    ║     Code      ║     Implémentation, tests,                            │
│    ╚═══════╤═══════╝     documentation, quality gate                       │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║      QA       ║ ─────────────────────▶ QA.md                          │
│    ║   Qualité     ║     Rapport de tests, couverture,                     │
│    ╚═══════╧═══════╝     résultats de validation                           │
│                                                                             │
│    ┌───────────────────────────────────────────────────────────────────┐   │
│    │                 MISES À JOUR WEBSOCKET TEMPS RÉEL                 │   │
│    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│    │  │Progression│  │Artifacts │  │ Erreurs  │  │  Statut  │          │   │
│    │  │  Events   │  │ Générés  │  │ Détectées│  │ Changés  │          │   │
│    │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │   │
│    └───────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Architecture du Système de Benchmark

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   ARCHITECTURE DU SYSTÈME DE BENCHMARK                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     PROGRAMMES DE BENCHMARK                          │   │
│  │                                                                      │   │
│  │   ⚡ Fast Scan        🎯 Standard          🏆 Advanced               │   │
│  │   ─────────────      ─────────────        ─────────────              │   │
│  │   • ~5 minutes       • ~20 minutes        • ~60 minutes              │   │
│  │   • 1 essai/modèle   • 5 essais/modèle    • 5 essais/modèle          │   │
│  │   • Éval rapide      • Équilibré          • Complet                  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       PHASES D'ÉVALUATION                            │   │
│  │                                                                      │   │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                │   │
│  │  │  PROMPTING  │──▶│ RAISONNEMENT│──▶│   CODAGE    │                │   │
│  │  │   Tests     │   │   Tests     │   │   Tests     │                │   │
│  │  │             │   │             │   │             │                │   │
│  │  │ • Clarté    │   │ • Logique   │   │ • Syntaxe   │                │   │
│  │  │ • Structure │   │ • Analyse   │   │ • Qualité   │                │   │
│  │  │ • Contexte  │   │ • Planning  │   │ • Patterns  │                │   │
│  │  └─────────────┘   └─────────────┘   └─────────────┘                │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SCORING PAR RÔLE                                │   │
│  │                                                                      │   │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐               │   │
│  │   │ Analyst │  │   PM    │  │Architect│  │   PO    │               │   │
│  │   │  Score  │  │  Score  │  │  Score  │  │  Score  │               │   │
│  │   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘               │   │
│  │        │            │            │            │                     │   │
│  │   ┌────┴────┐  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐               │   │
│  │   │   SM    │  │   Dev   │  │   QA    │  │ Routing │               │   │
│  │   │  Score  │  │  Score  │  │  Score  │  │ Config  │               │   │
│  │   └─────────┘  └─────────┘  └─────────┘  └────┬────┘               │   │
│  │                                               │                     │   │
│  │   ┌───────────────────────────────────────────┴─────────────────┐  │   │
│  │   │                    BILLBOARD                                 │  │   │
│  │   │   Meilleur modèle par rôle → Configuration routage auto     │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fonctionnalités

Freya est un orchestrateur multi-agents avancé aligné sur le **workflow BMAD** (Business Model - Architecture - Development), conçu pour fonctionner avec des LLMs locaux via Ollama et Llama.cpp.

### Fonctionnalités Principales

| Fonctionnalité | Description |
|----------------|-------------|
| **Workflow BMAD Complet** | De l'analyse métier à la livraison de code avec 7 agents spécialisés |
| **Support Multi-backend LLM** | Ollama et Llama.cpp avec découverte automatique des modèles |
| **Benchmarking Intelligent** | Routage automatique basé sur les performances par rôle |
| **Interface Web Moderne** | UI React professionnelle avec thèmes sombre/clair |
| **Mises à Jour Temps Réel** | Progression en direct via WebSocket pour toutes les opérations |
| **Recherche Web Gratuite** | Intégration DuckDuckGo, SearXNG, Wikipedia |
| **Veille Cyber Sécurité** | 8+ sources de flux de vulnérabilités avec lookup CVE |

### Agents Spécialisés

| Agent | Rôle | Sortie | Compétences Clés |
|-------|------|--------|------------------|
| **Analyst** | Analyse des besoins | `project-brief.md` | Interviews parties prenantes, définition scope |
| **PM** | Exigences produit | `PRD.md` | Planning fonctionnalités, user stories |
| **Architect** | Conception technique | `architecture.md` | Design système, stack technique |
| **PO** | Découpage epics | `epics/*.md` | Priorisation fonctionnalités |
| **SM** | User stories | `stories/*.md` | Planning sprints, critères acceptation |
| **Developer** | Implémentation | Code source | Code propre, tests, documentation |
| **QA** | Assurance qualité | `QA.md` | Couverture tests, validation |

### Outils Intégrés

| Outil | Capacités | Sources de Données |
|-------|-----------|-------------------|
| **WebSearch** | Recherche web gratuite | DuckDuckGo, SearXNG, Wikipedia, Brave |
| **WebWatch** | Surveillance sécurité | CISA KEV, CERT-FR, NVD, Exploit-DB, GitHub Security |
| **Shell** | Exécution sécurisée | Environnement sandbox |
| **Clipboard** | Intégration système | Presse-papiers système |
| **Redact** | Protection contenu | Masquage données sensibles |

---

## Stack Technologique

### Frontend (web/)

| Technologie | Usage | Version |
|-------------|-------|---------|
| **React** | Framework UI | 18.x |
| **TypeScript** | Typage Fort | 5.x |
| **Vite** | Outil de Build | 5.x |
| **Tailwind CSS** | Styling | 3.4.x |
| **Zustand** | Gestion d'État | 4.x |
| **TanStack Query** | Récupération Données | 5.x |
| **Lucide React** | Icônes | Dernier |
| **React Router** | Navigation | 6.x |
| **react-markdown** | Rendu Markdown | Dernier |

### Backend (src/freya/)

| Technologie | Usage | Version |
|-------------|-------|---------|
| **FastAPI** | Framework Web | 0.109+ |
| **Uvicorn** | Serveur ASGI | Dernier |
| **Pydantic** | Validation Données | 2.x |
| **httpx** | Client HTTP | Dernier |
| **WebSockets** | Communication Temps Réel | Natif |

---

## Démarrage Rapide

### Prérequis

- **Python 3.11+**
- **Node.js 18+** (pour construire l'UI web)
- **Ollama** en local sur `http://localhost:11434`

### Installation (Windows PowerShell)

```powershell
# Cloner le dépôt
git clone https://github.com/Duperopope/Freya.git
cd Freya

# Installation automatique
.\install.ps1

# OU installation manuelle :

# 1. Créer et activer l'environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Installer le package Python
pip install -e .

# 3. Construire l'interface web
cd web
npm install
npm run build
cd ..
```

### Lancement de Freya

```powershell
# Activer l'environnement (si pas déjà fait)
.\.venv\Scripts\Activate.ps1

# Démarrer le serveur web
freya serve

# Avec mode debug (rechargement auto)
freya serve --debug

# Host/port personnalisés
freya serve --host 0.0.0.0 --port 8080
```

Puis ouvrez **http://localhost:8765** dans votre navigateur.

---

## Commandes CLI

| Commande | Description |
|----------|-------------|
| `freya serve` | Démarrer le serveur web |
| `freya serve --debug` | Démarrer avec rechargement auto + docs API |
| `freya discover-models` | Lister les modèles Ollama installés |
| `freya bench-fast` | Benchmark rapide (~5 min) |
| `freya bench-standard` | Benchmark standard (~20 min) |
| `freya bench-advanced` | Benchmark complet (~60 min) |
| `freya autopilot --goal "..."` | Générer un projet à partir d'un objectif |
| `freya tui` | TUI legacy (requiert `pip install freya[tui]`) |

---

## Configuration

### Variables d'Environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `FREYA_MANAGED_ROOT` | `~/.freya` | Répertoire principal des données |
| `FREYA_OLLAMA_URL` | `http://localhost:11434` | URL du serveur Ollama |
| `FREYA_OLLAMA_TIMEOUT_SEC` | `120` | Timeout des requêtes |
| `FREYA_WORKSPACE_ROOT` | Répertoire courant | Répertoire de travail |

### Panneau Paramètres (UI Web)

La page Settings propose une configuration complète :

| Onglet | Fonctionnalités |
|--------|-----------------|
| **Paths** | Éditer managed_root, cache_root, artifacts_root, output_root, prompts_root |
| **Ollama** | Voir statut connexion, URL base, modèles installés |
| **Model Routing** | Assigner meilleur modèle par rôle (manuel ou depuis benchmark) |
| **APIs** | Configurer tokens GitHub/GitLab, clé API NVD, instance SearXNG |
| **Appearance** | Thème (Dark/Light/Midnight), Famille police, Taille police |
| **About** | Info version, ressources système, liens rapides |

---

## Interface Web

### Pages

| Page | Description | Fonctionnalités Clés |
|------|-------------|---------------------|
| **Chat** | Conversation IA | Sélection persona/hat, recherche web, coloration code |
| **Bench** | Benchmarking LLM | Progression temps réel, billboard, résultats détaillés |
| **BMAD** | Pipeline agents | Pipeline visuel, preview artifacts, goal-to-code |
| **Settings** | Configuration | Chemins, routage, APIs, apparence |
| **Files** | Explorateur fichiers | Coloration syntaxique, vue arbre, éditeur |
| **Watch** | Flux sécurité | 8+ sources, lookup CVE, export JSON |

### Fonctionnalités Temps Réel

| Fonctionnalité | Technologie | Intervalle Mise à Jour |
|----------------|-------------|------------------------|
| **Progression Benchmark** | WebSocket | 1 seconde |
| **Pipeline BMAD** | WebSocket | Temps réel |
| **Moniteur Système** | Polling REST | 5 secondes |
| **Cyber Watch** | Polling REST | 5 minutes (configurable) |
| **Statut Ollama** | Polling REST | 30 secondes |

---

## Endpoints API

### Santé & Système

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/health` | GET | Health check + statut Ollama |
| `/api/system` | GET | CPU, RAM, usage disque |

### Chat

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/chat/hats` | GET | Liste presets persona |
| `/api/chat/generate` | POST | Générer réponse IA |
| `/api/chat/search` | POST | Recherche web gratuite (DuckDuckGo/SearXNG) |

### Benchmark

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/bench/status` | GET | Statut benchmark actuel |
| `/api/bench/start` | POST | Démarrer programme benchmark |
| `/api/bench/stop` | POST | Arrêter benchmark en cours |
| `/api/bench/billboard` | GET | Meilleurs scores par rôle |
| `/api/bench/history` | GET | Résultats historiques |
| `/api/bench/apply-routing` | POST | Appliquer billboard comme routage |

### BMAD

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/bmad/status` | GET | Statut pipeline |
| `/api/bmad/run` | POST | Démarrer cycle BMAD |
| `/api/bmad/agent` | POST | Exécuter agent unique |
| `/api/bmad/artifacts` | GET | Lister artifacts générés |
| `/api/bmad/artifact` | GET | Obtenir contenu artifact |
| `/api/bmad/autopilot` | POST | Mode autopilot complet |

### Models

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/models/` | GET | Lister modèles installés |
| `/api/models/pull` | POST | Télécharger nouveau modèle |
| `/api/models/routing` | GET/POST | Get/set config routage |

### Files

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/files/browse` | GET | Listing répertoire |
| `/api/files/read` | GET | Lire contenu fichier |
| `/api/files/write` | POST | Écrire fichier |
| `/api/files/tree` | GET | Arbre complet fichiers |

### Watch (Cyber Sécurité)

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/watch/` | GET | Flux sécurité combiné |
| `/api/watch/cisa-kev` | GET | CISA Known Exploited Vulnerabilities |
| `/api/watch/cert-fr` | GET | Alertes CERT-FR |
| `/api/watch/nvd` | GET | CVEs récentes NVD |
| `/api/watch/exploitdb` | GET | Entrées Exploit-DB |
| `/api/watch/github-advisories` | GET | GitHub Security Advisories |
| `/api/watch/cve/{id}` | GET | Lookup détail CVE |
| `/api/watch/stats` | GET | Statistiques cache |

### Settings

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/settings/paths` | GET/POST | Chemins répertoires |
| `/api/settings/prompts` | GET | Lister prompts |
| `/api/settings/prompts/{name}` | GET/POST | Get/save prompt |
| `/api/settings/version` | GET | Info version |

---

## Structure du Projet

```
freya/
├── pyproject.toml               # Configuration projet Python
├── README.md                    # Documentation (English)
├── README.fr.md                 # Cette documentation (Français)
│
├── src/freya/                   # Backend Python
│   ├── cli.py                   # CLI (freya serve, bench-*, etc.)
│   ├── config.py                # Configuration Pydantic
│   ├── orchestrator.py          # Coordination des agents
│   ├── router.py                # Routage LLM & benchmarking
│   ├── ollama_client.py         # Client API Ollama
│   │
│   ├── api/                     # API REST FastAPI
│   │   ├── main.py              # Factory d'app & lifespan
│   │   ├── websocket.py         # Gestionnaire WebSocket (canaux)
│   │   └── routes/              # Endpoints API
│   │       ├── chat.py          # Chat + recherche web
│   │       ├── bench.py         # Benchmarking
│   │       ├── bmad.py          # Workflow BMAD
│   │       ├── models.py        # Gestion modèles
│   │       ├── files.py         # Explorateur fichiers
│   │       ├── watch.py         # Veille cyber
│   │       └── settings.py      # Configuration
│   │
│   ├── agents/                  # Agents BMAD
│   │   ├── analyst.py           # Analyse besoins
│   │   ├── pm.py                # Product management
│   │   ├── architect.py         # Architecture technique
│   │   ├── po.py                # Product owner
│   │   ├── sm.py                # Scrum master
│   │   ├── dev.py               # Développeur
│   │   └── qa.py                # Assurance qualité
│   │
│   └── tools/                   # Outils intégrés
│       ├── shell.py             # Exécution shell sécurisée
│       ├── webwatch.py          # Agrégation flux sécurité
│       ├── websearch.py         # Recherche web gratuite
│       └── ...
│
└── web/                         # Frontend React
    ├── package.json             # Configuration npm
    ├── vite.config.ts           # Config build Vite
    ├── tailwind.config.js       # Thème Tailwind (couleurs Freya)
    ├── postcss.config.js        # Config PostCSS
    └── src/
        ├── App.tsx              # Composant racine + routing
        ├── index.css            # Styles globaux + thème Freya
        │
        ├── components/
        │   ├── layout/          # Sidebar, Header, StatusBar
        │   ├── chat/            # ChatPage (conversation + recherche)
        │   ├── bench/           # BenchPage (dashboard benchmarking)
        │   ├── bmad/            # BMADPage (studio pipeline agents)
        │   ├── settings/        # SettingsPage (UI config complète)
        │   ├── files/           # FilesPage (explorateur + éditeur)
        │   └── watch/           # WatchPage (flux sécurité cyber)
        │
        ├── stores/              # Gestion état Zustand
        │   └── appStore.ts      # État global app
        │
        ├── hooks/               # Hooks React personnalisés
        │   └── useWebSocket.ts  # Connexion WebSocket
        │
        └── lib/                 # Utilitaires
            └── api.ts           # Client API type-safe
```

---

## Développement

### Développement Frontend

```bash
cd web
npm install
npm run dev   # Serveur dev sur http://localhost:5173
```

Le serveur de dev proxy les requêtes `/api` vers le backend sur le port 8765.

### Développement Backend

```bash
pip install -e ".[dev]"
freya serve --debug
```

### Exécuter les Tests

```bash
pytest tests/
```

---

## Changelog

### v2.1.0 (2026-01-26)

#### Nouvelles Fonctionnalités
- **Recherche Web Gratuite** : Intégration DuckDuckGo et SearXNG (pas de clé API requise)
- **Cyber Watch Amélioré** : 8+ sources sécurité (NVD, Exploit-DB, GitHub Security, PacketStorm)
- **Intégration Dépôts** : Configuration API GitHub/GitLab pour accès repos BMAD
- **Système Thèmes Live** : Changement thème temps réel (Dark, Light, Midnight)
- **Chemins Éditables** : Configuration complète des chemins dans Settings
- **Toggle Auto-refresh** : Timestamps visibles et rafraîchissement configurable pour Watch
- **Export JSON** : Export des vulnérabilités filtrées en JSON

#### Améliorations
- **Refonte Settings** : Redesign complet avec 6 onglets (Paths, Ollama, Routing, APIs, Appearance, About)
- **BMAD Studio** : Visualisation agents améliorée avec preview artifacts temps réel
- **Dashboard Benchmark** : Résultats détaillés extensibles par modèle
- **Client API** : Couverture TypeScript complète des types
- **Stabilité WebSocket** : Gestion améliorée des canaux et reconnexion

#### Corrections
- Correction parsing RSS CERT-FR (gestion namespace XML)
- Correction service fichiers statiques en mode production
- Correction ordre d'enregistrement endpoint WebSocket
- Correction erreurs compilation TypeScript frontend

### v2.0.0 (2026-01-26)

- **NOUVEAU** : Interface web React moderne
- **NOUVEAU** : API REST FastAPI avec WebSocket
- **NOUVEAU** : Flux sécurité Cyber Watch
- **NOUVEAU** : Explorateur de fichiers avec éditeur
- **NOUVEAU** : Suivi de progression temps réel
- **AMÉLIORÉ** : Refonte complète UI/UX
- **AMÉLIORÉ** : Gestion de la configuration
- **DÉPRÉCIÉ** : TUI (disponible via `pip install freya[tui]`)

### v1.1.6.1 (2026-01-26)

- Diagrammes d'architecture
- Améliorations TUI
- Meilleur routage et autopilot

---

## Licence

Licence MIT - Voir le fichier LICENSE pour les détails.

---

## Crédits

Construit avec :
- [Ollama](https://ollama.ai) - Runtime LLM local
- [FastAPI](https://fastapi.tiangolo.com) - Framework web Python
- [React](https://react.dev) - Bibliothèque UI
- [Tailwind CSS](https://tailwindcss.com) - Styling
- [Zustand](https://zustand-demo.pmnd.rs) - Gestion d'état
- [TanStack Query](https://tanstack.com/query) - Récupération données
- [Lucide](https://lucide.dev) - Icônes
- [Vite](https://vitejs.dev) - Outil de build

---

<p align="center">
  <strong>Freya</strong> - <em>Orchestrateur multi-agents aligné BMAD pour LLMs locaux</em>
</p>

<p align="center">
  <a href="https://github.com/Duperopope/Freya">GitHub</a> •
  <a href="https://github.com/Duperopope/Freya/issues">Issues</a> •
  <a href="https://github.com/Duperopope/Freya/discussions">Discussions</a>
</p>
