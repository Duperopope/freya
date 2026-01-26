# Freya 2.0

[![English](https://img.shields.io/badge/Language-English-blue.svg)](README.md) [![Français](https://img.shields.io/badge/Langue-Français-red.svg)](README.fr.md)

[![Built with AI](https://img.shields.io/badge/Built%20with-AI-FF6B6B.svg)](https://github.com/features/copilot) [![AI-Powered](https://img.shields.io/badge/AI--Powered-Yes-9C88FF.svg)](https://ollama.ai) [![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-00ADD8.svg)](https://ollama.ai) [![Llama.cpp](https://img.shields.io/badge/Supports-Llama.cpp-FF6B35.svg)](https://github.com/ggerganov/llama.cpp)

[![Version](https://img.shields.io/badge/Version-2.0.0-green.svg)](#) [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org) [![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev) [![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com)

---

## Nouveautés v2.0

**Freya 2.0** apporte une refonte architecturale complète avec une **interface web moderne** remplaçant la TUI :

- **Interface Web Moderne** : Interface React professionnelle avec mises à jour temps réel
- **API REST** : Backend FastAPI avec support WebSocket
- **Monitoring Temps Réel** : Suivi en direct des benchmarks et cycles BMAD
- **Cyber Watch** : Surveillance des vulnérabilités intégrée (CISA KEV, CERT-FR)
- **Explorateur de Fichiers** : Gestion de fichiers avec coloration syntaxique
- **Panneau Paramètres** : Configuration complète dans l'interface

---

## Fonctionnalités

Freya est un orchestrateur multi-agents avancé aligné sur le **workflow BMAD** (Business Model - Architecture - Development), conçu pour fonctionner avec des LLMs locaux via Ollama et Llama.cpp.

### Fonctionnalités Principales

- **Workflow BMAD Complet** : De l'analyse métier à la livraison de code
- **Support Multi-backend LLM** : Ollama et Llama.cpp
- **Benchmarking Intelligent** : Routage automatique des modèles basé sur les performances
- **Interface Web Moderne** : UI React professionnelle
- **API REST** : Backend FastAPI complet

### Agents Spécialisés

| Agent | Rôle | Sortie |
|-------|------|--------|
| **Analyst** | Analyse des besoins | `project-brief.md` |
| **PM** | Exigences produit | `PRD.md` |
| **Architect** | Conception technique | `architecture.md` |
| **PO** | Découpage en epics | `epics/*.md` |
| **SM** | User stories | `stories/*.md` |
| **Developer** | Implémentation | Code source |
| **QA** | Assurance qualité | `QA.md` |

### Outils Intégrés

- **Shell** : Exécution sécurisée de commandes
- **WebWatch** : Agrégation de flux sécurité (CISA KEV, CERT-FR)
- **WebSearch** : Recherche Wikipedia et Brave
- **Clipboard** : Opérations presse-papiers
- **Redact** : Protection des contenus sensibles

---

## Démarrage Rapide

### Prérequis

- **Python 3.11+**
- **Node.js 18+** (pour construire l'interface web)
- **Ollama** en local sur `http://localhost:11434`

### Installation (Windows PowerShell)

```powershell
# Cloner le dépôt
git clone https://github.com/VOTRE_USERNAME/freya.git
cd freya

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
| `freya serve --debug` | Démarrer avec rechargement auto |
| `freya discover-models` | Lister les modèles Ollama installés |
| `freya bench-fast` | Benchmark rapide (~5 min) |
| `freya bench-standard` | Benchmark standard (~20 min) |
| `freya bench-advanced` | Benchmark complet (~60 min) |
| `freya autopilot --goal "..."` | Générer un projet à partir d'un objectif |
| `freya tui` | TUI legacy (requiert `pip install freya[tui]`) |

---

## Configuration

Freya utilise des variables d'environnement :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `FREYA_MANAGED_ROOT` | `~/.freya` | Répertoire principal des données |
| `FREYA_OLLAMA_URL` | `http://localhost:11434` | URL du serveur Ollama |
| `FREYA_OLLAMA_TIMEOUT_SEC` | `120` | Timeout des requêtes |
| `FREYA_WORKSPACE_ROOT` | Répertoire courant | Répertoire de travail |

### Configuration Recommandée (PowerShell)

```powershell
# Ajouter à votre profil PowerShell ($PROFILE)
$env:FREYA_MANAGED_ROOT = "H:\Code\.freya"
$env:FREYA_OLLAMA_URL = "http://localhost:11434"
$env:FREYA_WORKSPACE_ROOT = "H:\Code\Projects"
```

---

## Interface Web

### Pages

| Page | Description |
|------|-------------|
| **Chat** | Conversation IA avec sélection de persona/hat |
| **Bench** | Lancer et surveiller les benchmarks LLM |
| **BMAD** | BMAD Studio - pipeline complet des agents |
| **Settings** | Configuration, routage, prompts |
| **Files** | Parcourir et éditer les fichiers projet |
| **Watch** | Flux de vulnérabilités sécurité |

### Fonctionnalités Temps Réel

- **WebSocket** : Mises à jour en direct pour bench/BMAD
- **Monitoring Système** : CPU, RAM, disque
- **Statut Connexion** : Indicateur de connectivité Ollama

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

## Architecture

```
freya/
├── pyproject.toml               # Configuration projet Python
├── README.md / README.fr.md     # Documentation
│
├── src/freya/                   # Backend Python
│   ├── cli.py                   # CLI (freya serve, bench-*, etc.)
│   ├── config.py                # Configuration Pydantic
│   ├── orchestrator.py          # Coordination des agents
│   ├── router.py                # Routage LLM & benchmarking
│   │
│   ├── api/                     # API REST FastAPI
│   │   ├── main.py              # Factory d'app & lifespan
│   │   ├── websocket.py         # Gestionnaire WebSocket
│   │   └── routes/              # Endpoints API
│   │
│   ├── agents/                  # Agents BMAD
│   └── tools/                   # Outils intégrés
│
└── web/                         # Frontend React
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx
        └── components/          # Composants UI
```

---

## Changelog

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
- [Lucide](https://lucide.dev) - Icônes

---

**Freya** - *Orchestrateur multi-agents aligné BMAD pour LLMs locaux*
