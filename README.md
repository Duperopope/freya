# Freya 2.1

[![English](https://img.shields.io/badge/Language-English-blue.svg)](README.md) [![Français](https://img.shields.io/badge/Langue-Français-red.svg)](README.fr.md)

[![Built with AI](https://img.shields.io/badge/Built%20with-AI-FF6B6B.svg)](https://github.com/features/copilot) [![AI-Powered](https://img.shields.io/badge/AI--Powered-Yes-9C88FF.svg)](https://ollama.ai) [![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-00ADD8.svg)](https://ollama.ai) [![Llama.cpp](https://img.shields.io/badge/Supports-Llama.cpp-FF6B35.svg)](https://github.com/ggerganov/llama.cpp)

[![Version](https://img.shields.io/badge/Version-2.1.0-green.svg)](#) [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org) [![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev) [![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com) [![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://typescriptlang.org) [![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-38BDF8.svg)](https://tailwindcss.com)

---

<p align="center">
  <img src="web/public/freya-icon.svg" alt="Freya Logo" width="120" />
</p>

<h3 align="center">BMAD-aligned Multi-Agent Orchestrator for Local LLMs</h3>

<p align="center">
  <strong>Modern • Real-time • Privacy-First</strong>
</p>

---

## What's New in 2.1

**Freya 2.1** elevates the modern web interface with enhanced features and improved user experience:

### Core Enhancements

- **Free Web Search Integration** - DuckDuckGo and SearXNG support, no API keys required
- **Enhanced Cyber Watch** - 8+ security sources including NVD, Exploit-DB, GitHub Security Advisories
- **Live Theme System** - Real-time theme switching with Dark, Light, and Midnight modes
- **Editable Settings** - Full configuration management including custom paths and API integrations
- **Real-time Auto-refresh** - Configurable auto-refresh with visible timestamps across all dashboards

### New Features

| Feature | Description |
|---------|-------------|
| **Multi-provider Search** | DuckDuckGo, SearXNG, Wikipedia, Brave integration |
| **Repository Integration** | GitHub/GitLab API support for BMAD repo access |
| **Advanced Cyber Dashboard** | Real-time global attack visualization |
| **Expandable Benchmark Results** | Detailed per-model metrics with export |
| **JSON Error Export** | Normalized error export for debugging |
| **Custom Font Support** | Cascadia Code, Fira Code, JetBrains Mono |

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FREYA 2.1                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      FRONTEND (React 18 + TypeScript)                │   │
│  │                                                                      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │  Chat   │ │  Bench  │ │  BMAD   │ │  Watch  │ │Settings │       │   │
│  │  │  Page   │ │  Page   │ │ Studio  │ │  Page   │ │  Page   │       │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │   │
│  │       │           │           │           │           │             │   │
│  │  ┌────┴───────────┴───────────┴───────────┴───────────┴────┐       │   │
│  │  │              Zustand Store (State Management)            │       │   │
│  │  │   • AppStore • BenchProgress • SystemStatus • Theme      │       │   │
│  │  └────────────────────────────┬─────────────────────────────┘       │   │
│  │                               │                                      │   │
│  │  ┌────────────────────────────┴─────────────────────────────┐       │   │
│  │  │          TanStack Query (Data Fetching + Cache)          │       │   │
│  │  └────────────────────────────┬─────────────────────────────┘       │   │
│  │                               │                                      │   │
│  │  ┌────────────────────────────┴─────────────────────────────┐       │   │
│  │  │                  API Client (api.ts)                      │       │   │
│  │  │  • Type-safe • Error handling • WebSocket support         │       │   │
│  │  └────────────────────────────┬─────────────────────────────┘       │   │
│  └───────────────────────────────│──────────────────────────────────────┘   │
│                                  │                                          │
│                         HTTP/REST & WebSocket                               │
│                                  │                                          │
│  ┌───────────────────────────────┴──────────────────────────────────────┐   │
│  │                      BACKEND (FastAPI + Python)                       │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │                    API Layer (/api/*)                        │     │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │     │   │
│  │  │  │ /chat  │ │ /bench │ │ /bmad  │ │ /watch │ │/settings│    │     │   │
│  │  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘    │     │   │
│  │  │      └──────────┴──────────┴──────────┴──────────┘          │     │   │
│  │  │                         │                                    │     │   │
│  │  │  ┌──────────────────────┴────────────────────────────┐      │     │   │
│  │  │  │              WebSocket Manager                     │      │     │   │
│  │  │  │   Channels: BENCH | CHAT | BMAD | SYSTEM | LOGS   │      │     │   │
│  │  │  └───────────────────────────────────────────────────┘      │     │   │
│  │  └──────────────────────────────────────────────────────────────┘     │   │
│  │                                  │                                    │   │
│  │  ┌───────────────────────────────┴────────────────────────────┐      │   │
│  │  │                     Core Services                           │      │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │      │   │
│  │  │  │ Orchestrator│  │  LLM Router │  │   Monitor   │         │      │   │
│  │  │  │  (Agents)   │  │ (Benchmark) │  │  (System)   │         │      │   │
│  │  │  └──────┬──────┘  └──────┬──────┘  └─────────────┘         │      │   │
│  │  │         │                │                                  │      │   │
│  │  │  ┌──────┴────────────────┴──────────────────────────┐      │      │   │
│  │  │  │              Ollama Client (HTTP)                 │      │      │   │
│  │  │  │     Base URL: http://localhost:11434             │      │      │   │
│  │  │  └──────────────────────────────────────────────────┘      │      │   │
│  │  └────────────────────────────────────────────────────────────┘      │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────┐      │   │
│  │  │                     Integrated Tools                        │      │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │      │   │
│  │  │  │WebSearch │  │WebWatch  │  │  Shell   │  │ Clipboard│   │      │   │
│  │  │  │DuckDuckGo│  │CISA/NVD  │  │ Secure   │  │  System  │   │      │   │
│  │  │  │Wikipedia │  │CERT-FR   │  │ Sandbox  │  │ Access   │   │      │   │
│  │  │  │SearXNG   │  │Exploit-DB│  │          │  │          │   │      │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │      │   │
│  │  └────────────────────────────────────────────────────────────┘      │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BMAD Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BMAD WORKFLOW PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌───────────┐                                                           │
│    │   GOAL    │  User provides project goal                               │
│    └─────┬─────┘                                                           │
│          │                                                                  │
│          ▼                                                                  │
│    ╔═══════════════╗                                                       │
│    ║   ANALYST     ║ ─────────────────────▶ project-brief.md               │
│    ║  Requirements ║     Requirements analysis, stakeholder                │
│    ╚═══════╤═══════╝     identification, scope definition                  │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║      PM       ║ ─────────────────────▶ PRD.md                         │
│    ║   Product     ║     Product requirements document,                    │
│    ╚═══════╤═══════╝     features, user stories overview                   │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║  ARCHITECT    ║ ─────────────────────▶ architecture.md                │
│    ║   Technical   ║     System design, tech stack,                        │
│    ╚═══════╤═══════╝     component architecture, APIs                      │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║      PO       ║ ─────────────────────▶ epics/*.md                     │
│    ║ Product Owner ║     Epic breakdown, feature                           │
│    ╚═══════╤═══════╝     prioritization, roadmap                           │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║      SM       ║ ─────────────────────▶ stories/*.md                   │
│    ║ Scrum Master  ║     User stories, acceptance                          │
│    ╚═══════╤═══════╝     criteria, sprint planning                         │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║  DEVELOPER    ║ ─────────────────────▶ code/                          │
│    ║     Code      ║     Implementation, tests,                            │
│    ╚═══════╤═══════╝     documentation, quality gate                       │
│            │                                                                │
│            ▼                                                                │
│    ╔═══════════════╗                                                       │
│    ║      QA       ║ ─────────────────────▶ QA.md                          │
│    ║   Quality     ║     Test report, coverage,                            │
│    ╚═══════╧═══════╝     validation results                                │
│                                                                             │
│    ┌───────────────────────────────────────────────────────────────────┐   │
│    │                    REAL-TIME WEBSOCKET UPDATES                    │   │
│    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│    │  │ Progress │  │ Artifacts│  │  Errors  │  │  Status  │          │   │
│    │  │  Events  │  │ Generated│  │ Detected │  │  Changes │          │   │
│    │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │   │
│    └───────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Benchmark System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BENCHMARK SYSTEM ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        BENCHMARK PROGRAMS                            │   │
│  │                                                                      │   │
│  │   ⚡ Fast Scan        🎯 Standard          🏆 Advanced               │   │
│  │   ─────────────      ─────────────        ─────────────              │   │
│  │   • ~5 minutes       • ~20 minutes        • ~60 minutes              │   │
│  │   • 1 trial/model    • 5 trials/model     • 5 trials/model           │   │
│  │   • Quick eval       • Balanced           • Comprehensive            │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         EVALUATION PHASES                            │   │
│  │                                                                      │   │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                │   │
│  │  │  PROMPTING  │──▶│  REASONING  │──▶│   CODING    │                │   │
│  │  │   Tests     │   │   Tests     │   │   Tests     │                │   │
│  │  │             │   │             │   │             │                │   │
│  │  │ • Clarity   │   │ • Logic     │   │ • Syntax    │                │   │
│  │  │ • Structure │   │ • Analysis  │   │ • Quality   │                │   │
│  │  │ • Context   │   │ • Planning  │   │ • Patterns  │                │   │
│  │  └─────────────┘   └─────────────┘   └─────────────┘                │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ROLE-BASED SCORING                              │   │
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
│  │   │   Best model per role → Automatic routing configuration     │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cyber Watch Security Feed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CYBER WATCH FEED ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       SECURITY DATA SOURCES                          │   │
│  │                                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │  CISA KEV   │  │  CERT-FR    │  │     NVD     │  │ Exploit-DB │ │   │
│  │  │  Known      │  │  French     │  │  National   │  │  Exploits  │ │   │
│  │  │  Exploited  │  │  Security   │  │  Vuln       │  │  Database  │ │   │
│  │  │  Vulns      │  │  Alerts     │  │  Database   │  │            │ │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │   │
│  │         │                │                │               │         │   │
│  │  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐  ┌─────┴──────┐ │   │
│  │  │   GitHub    │  │PacketStorm  │  │  VulnDB     │  │  OpenCVE   │ │   │
│  │  │  Security   │  │  Security   │  │   Feed      │  │   Feed     │ │   │
│  │  │  Advisories │  │   News      │  │             │  │            │ │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │   │
│  │         │                │                │               │         │   │
│  │         └────────────────┴────────────────┴───────────────┘         │   │
│  │                                   │                                  │   │
│  └───────────────────────────────────┼──────────────────────────────────┘   │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       AGGREGATION ENGINE                             │   │
│  │                                                                      │   │
│  │   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐         │   │
│  │   │    Caching    │   │  Deduplication│   │   Severity    │         │   │
│  │   │   (30 min)    │   │    Engine     │   │   Scoring     │         │   │
│  │   └───────────────┘   └───────────────┘   └───────────────┘         │   │
│  │                                                                      │   │
│  │   • TTL-based cache refresh       • CVSS v3.1/v3.0/v2.0 parsing    │   │
│  │   • Parallel feed fetching        • Source prioritization          │   │
│  │   • Error resilience              • Real-time updates              │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        FRONTEND DASHBOARD                            │   │
│  │                                                                      │   │
│  │   ┌──────────────────────────────────────────────────────────────┐  │   │
│  │   │  🔴 Critical  │  🟠 High  │  🟡 Medium  │  🟢 Low  │ ⚪ Info │  │   │
│  │   └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  │   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │   │
│  │   │  Filter    │  │  Search    │  │Auto-Refresh│  │  Export    │   │   │
│  │   │  by Source │  │  CVE/Text  │  │ Toggle     │  │  JSON      │   │   │
│  │   └────────────┘  └────────────┘  └────────────┘  └────────────┘   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Features

Freya is an advanced multi-agent orchestrator aligned with the **BMAD workflow** (Business Model - Architecture - Development), designed to work with local LLMs via Ollama and Llama.cpp.

### Core Features

| Feature | Description |
|---------|-------------|
| **Complete BMAD Workflow** | From business analysis to code delivery with 7 specialized agents |
| **Multi-backend LLM Support** | Ollama and Llama.cpp with automatic model discovery |
| **Intelligent Benchmarking** | Automatic model routing based on role-specific performance |
| **Modern Web Interface** | Professional React-based UI with dark/light themes |
| **Real-time Updates** | WebSocket-powered live progress for all operations |
| **Free Web Search** | DuckDuckGo, SearXNG, Wikipedia integration |
| **Cyber Security Watch** | 8+ vulnerability feed sources with CVE lookup |

### Specialized Agents

| Agent | Role | Output | Key Skills |
|-------|------|--------|------------|
| **Analyst** | Requirements analysis | `project-brief.md` | Stakeholder interviews, scope definition |
| **PM** | Product requirements | `PRD.md` | Feature planning, user stories |
| **Architect** | Technical design | `architecture.md` | System design, tech stack |
| **PO** | Epic breakdown | `epics/*.md` | Feature prioritization |
| **SM** | User stories | `stories/*.md` | Sprint planning, acceptance criteria |
| **Developer** | Code implementation | Source code | Clean code, tests, documentation |
| **QA** | Quality assurance | `QA.md` | Test coverage, validation |

### Integrated Tools

| Tool | Capabilities | Data Sources |
|------|--------------|--------------|
| **WebSearch** | Free web search | DuckDuckGo, SearXNG, Wikipedia, Brave |
| **WebWatch** | Security monitoring | CISA KEV, CERT-FR, NVD, Exploit-DB, GitHub Security |
| **Shell** | Secure execution | Sandboxed command environment |
| **Clipboard** | System integration | System clipboard operations |
| **Redact** | Content protection | Sensitive data masking |

---

## Technology Stack

### Frontend (web/)

| Technology | Purpose | Version |
|------------|---------|---------|
| **React** | UI Framework | 18.x |
| **TypeScript** | Type Safety | 5.x |
| **Vite** | Build Tool | 5.x |
| **Tailwind CSS** | Styling | 3.4.x |
| **Zustand** | State Management | 4.x |
| **TanStack Query** | Data Fetching | 5.x |
| **Lucide React** | Icons | Latest |
| **React Router** | Navigation | 6.x |
| **react-markdown** | Markdown Rendering | Latest |

### Backend (src/freya/)

| Technology | Purpose | Version |
|------------|---------|---------|
| **FastAPI** | Web Framework | 0.109+ |
| **Uvicorn** | ASGI Server | Latest |
| **Pydantic** | Data Validation | 2.x |
| **httpx** | HTTP Client | Latest |
| **WebSockets** | Real-time Communication | Native |

### LLM Integration

| Backend | Description |
|---------|-------------|
| **Ollama** | Primary LLM runtime (local) |
| **Llama.cpp** | Alternative runtime support |

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for building the web UI)
- **Ollama** running locally at `http://localhost:11434`

### Installation

```powershell
# Clone the repository
git clone https://github.com/Duperopope/Freya.git
cd Freya

# Install Python package
pip install -e .

# Build the web UI
cd web
npm install
npm run build
cd ..
```

### Running Freya

```powershell
# Start the web server
freya serve

# With debug mode (auto-reload)
freya serve --debug

# Custom host/port
freya serve --host 0.0.0.0 --port 8080
```

Then open **http://localhost:8765** in your browser.

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `freya serve` | Start web server |
| `freya serve --debug` | Start with auto-reload + API docs |
| `freya discover-models` | List installed Ollama models |
| `freya bench-fast` | Quick benchmark (~5 min) |
| `freya bench-standard` | Standard benchmark (~20 min) |
| `freya bench-advanced` | Full benchmark (~60 min) |
| `freya autopilot --goal "..."` | Generate project from goal |
| `freya tui` | Legacy TUI (requires `pip install freya[tui]`) |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FREYA_MANAGED_ROOT` | `~/.freya` | Main data directory |
| `FREYA_OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `FREYA_OLLAMA_TIMEOUT_SEC` | `120` | Request timeout |
| `FREYA_WORKSPACE_ROOT` | Current directory | Working directory |

### Settings Panel (Web UI)

The Settings page provides comprehensive configuration:

| Tab | Features |
|-----|----------|
| **Paths** | Edit managed_root, cache_root, artifacts_root, output_root, prompts_root |
| **Ollama** | View connection status, base URL, installed models |
| **Model Routing** | Assign best model per role (manual or from benchmark) |
| **APIs** | Configure GitHub/GitLab tokens, NVD API key, SearXNG instance |
| **Appearance** | Theme (Dark/Light/Midnight), Font family, Font size |
| **About** | Version info, system resources, quick links |

---

## Web Interface

### Pages

| Page | Description | Key Features |
|------|-------------|--------------|
| **Chat** | AI conversation | Hat/persona selection, web search, code highlighting |
| **Bench** | LLM benchmarking | Real-time progress, billboard, detailed results |
| **BMAD** | Agent pipeline | Visual pipeline, artifact preview, goal-to-code |
| **Settings** | Configuration | Paths, routing, APIs, appearance |
| **Files** | File browser | Syntax highlighting, tree view, editor |
| **Watch** | Security feed | 8+ sources, CVE lookup, export JSON |

### Real-time Features

| Feature | Technology | Update Interval |
|---------|------------|-----------------|
| **Benchmark Progress** | WebSocket | 1 second |
| **BMAD Pipeline** | WebSocket | Real-time |
| **System Monitor** | REST Polling | 5 seconds |
| **Cyber Watch** | REST Polling | 5 minutes (configurable) |
| **Ollama Status** | REST Polling | 30 seconds |

---

## API Endpoints

### Health & System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check + Ollama status |
| `/api/system` | GET | CPU, RAM, disk usage |

### Chat

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/hats` | GET | List persona presets |
| `/api/chat/generate` | POST | Generate AI response |
| `/api/chat/search` | POST | Free web search (DuckDuckGo/SearXNG) |

### Benchmark

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/bench/status` | GET | Current benchmark status |
| `/api/bench/start` | POST | Start benchmark program |
| `/api/bench/stop` | POST | Stop running benchmark |
| `/api/bench/billboard` | GET | Best scores per role |
| `/api/bench/history` | GET | Historical results |
| `/api/bench/apply-routing` | POST | Apply billboard as routing |

### BMAD

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/bmad/status` | GET | Pipeline status |
| `/api/bmad/run` | POST | Start BMAD cycle |
| `/api/bmad/agent` | POST | Run single agent |
| `/api/bmad/artifacts` | GET | List generated artifacts |
| `/api/bmad/artifact` | GET | Get artifact content |
| `/api/bmad/autopilot` | POST | Full autopilot mode |

### Models

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models/` | GET | List installed models |
| `/api/models/pull` | POST | Pull new model |
| `/api/models/routing` | GET/POST | Get/set routing config |

### Files

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/files/browse` | GET | Directory listing |
| `/api/files/read` | GET | Read file content |
| `/api/files/write` | POST | Write file |
| `/api/files/tree` | GET | Full file tree |

### Watch (Cyber Security)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/watch/` | GET | Combined security feed |
| `/api/watch/cisa-kev` | GET | CISA Known Exploited Vulnerabilities |
| `/api/watch/cert-fr` | GET | CERT-FR alerts |
| `/api/watch/nvd` | GET | NVD recent CVEs |
| `/api/watch/exploitdb` | GET | Exploit-DB entries |
| `/api/watch/github-advisories` | GET | GitHub Security Advisories |
| `/api/watch/cve/{id}` | GET | CVE detail lookup |
| `/api/watch/stats` | GET | Cache statistics |

### Settings

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/settings/paths` | GET/POST | Directory paths |
| `/api/settings/prompts` | GET | List prompts |
| `/api/settings/prompts/{name}` | GET/POST | Get/save prompt |
| `/api/settings/version` | GET | Version info |

---

## Project Structure

```
freya/
├── pyproject.toml               # Python project configuration
├── README.md                    # This documentation (English)
├── README.fr.md                 # Documentation (French)
│
├── src/freya/                   # Python backend
│   ├── cli.py                   # CLI (freya serve, bench-*, etc.)
│   ├── config.py                # Pydantic configuration
│   ├── orchestrator.py          # Agent coordination
│   ├── router.py                # LLM routing & benchmarking
│   ├── ollama_client.py         # Ollama API client
│   │
│   ├── api/                     # FastAPI REST API
│   │   ├── main.py              # App factory & lifespan
│   │   ├── websocket.py         # WebSocket manager (channels)
│   │   └── routes/              # API endpoints
│   │       ├── chat.py          # Chat + web search
│   │       ├── bench.py         # Benchmarking
│   │       ├── bmad.py          # BMAD workflow
│   │       ├── models.py        # Model management
│   │       ├── files.py         # File browser
│   │       ├── watch.py         # Cyber watch
│   │       └── settings.py      # Configuration
│   │
│   ├── agents/                  # BMAD agents
│   │   ├── analyst.py           # Requirements analysis
│   │   ├── pm.py                # Product management
│   │   ├── architect.py         # Technical architecture
│   │   ├── po.py                # Product owner
│   │   ├── sm.py                # Scrum master
│   │   ├── dev.py               # Developer
│   │   └── qa.py                # Quality assurance
│   │
│   └── tools/                   # Integrated tools
│       ├── shell.py             # Secure shell execution
│       ├── webwatch.py          # Security feed aggregation
│       ├── websearch.py         # Free web search
│       └── ...
│
└── web/                         # React frontend
    ├── package.json             # npm configuration
    ├── vite.config.ts           # Vite build config
    ├── tailwind.config.js       # Tailwind theme (Freya colors)
    ├── postcss.config.js        # PostCSS config
    └── src/
        ├── App.tsx              # Root component + routing
        ├── index.css            # Global styles + Freya theme
        │
        ├── components/
        │   ├── layout/          # Sidebar, Header, StatusBar
        │   ├── chat/            # ChatPage (conversation + search)
        │   ├── bench/           # BenchPage (benchmarking dashboard)
        │   ├── bmad/            # BMADPage (agent pipeline studio)
        │   ├── settings/        # SettingsPage (full config UI)
        │   ├── files/           # FilesPage (file browser + editor)
        │   └── watch/           # WatchPage (cyber security feed)
        │
        ├── stores/              # Zustand state management
        │   └── appStore.ts      # Global app state
        │
        ├── hooks/               # Custom React hooks
        │   └── useWebSocket.ts  # WebSocket connection
        │
        └── lib/                 # Utilities
            └── api.ts           # Type-safe API client
```

---

## Development

### Frontend Development

```bash
cd web
npm install
npm run dev   # Dev server at http://localhost:5173
```

The dev server proxies `/api` requests to the backend at port 8765.

### Backend Development

```bash
pip install -e ".[dev]"
freya serve --debug
```

### Running Tests

```bash
pytest tests/
```

---

## Changelog

### v2.1.0 (2026-01-26)

#### New Features
- **Free Web Search** : DuckDuckGo and SearXNG integration (no API key required)
- **Enhanced Cyber Watch** : 8+ security sources (NVD, Exploit-DB, GitHub Security, PacketStorm)
- **Repository Integration** : GitHub/GitLab API configuration for BMAD repo access
- **Live Theme System** : Real-time theme switching (Dark, Light, Midnight)
- **Editable Paths** : Full path configuration in Settings
- **Auto-refresh Toggle** : Visible timestamps and configurable refresh for Watch
- **JSON Export** : Export filtered vulnerabilities as JSON

#### Improvements
- **Settings Overhaul** : Complete redesign with 6 tabs (Paths, Ollama, Routing, APIs, Appearance, About)
- **BMAD Studio** : Enhanced agent visualization with real-time artifact preview
- **Benchmark Dashboard** : Expandable detailed results per model
- **API Client** : Full TypeScript type coverage
- **WebSocket Stability** : Improved channel management and reconnection

#### Bug Fixes
- Fixed CERT-FR RSS parsing (XML namespace handling)
- Fixed static file serving in production mode
- Fixed WebSocket endpoint registration order
- Fixed TypeScript compilation errors in frontend

### v2.0.0 (2026-01-26)

- **NEW**: Modern React web interface
- **NEW**: FastAPI REST API with WebSocket
- **NEW**: Cyber Watch security feed
- **NEW**: File browser with editor
- **NEW**: Real-time progress tracking
- **IMPROVED**: Complete UI/UX overhaul
- **IMPROVED**: Configuration management
- **DEPRECATED**: TUI (available via `pip install freya[tui]`)

### v1.1.6.1 (2026-01-26)

- Architecture diagrams
- TUI improvements
- Better routing and autopilot

---

## License

MIT License - See LICENSE file for details.

---

## Credits

Built with:
- [Ollama](https://ollama.ai) - Local LLM runtime
- [FastAPI](https://fastapi.tiangolo.com) - Python web framework
- [React](https://react.dev) - UI library
- [Tailwind CSS](https://tailwindcss.com) - Styling
- [Zustand](https://zustand-demo.pmnd.rs) - State management
- [TanStack Query](https://tanstack.com/query) - Data fetching
- [Lucide](https://lucide.dev) - Icons
- [Vite](https://vitejs.dev) - Build tool

---

<p align="center">
  <strong>Freya</strong> - <em>BMAD-aligned multi-agent orchestrator for local LLMs</em>
</p>

<p align="center">
  <a href="https://github.com/Duperopope/Freya">GitHub</a> •
  <a href="https://github.com/Duperopope/Freya/issues">Issues</a> •
  <a href="https://github.com/Duperopope/Freya/discussions">Discussions</a>
</p>
