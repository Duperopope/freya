# Freya 2.0

[![English](https://img.shields.io/badge/Language-English-blue.svg)](README.md) [![Français](https://img.shields.io/badge/Langue-Français-red.svg)](README.fr.md)

[![Built with AI](https://img.shields.io/badge/Built%20with-AI-FF6B6B.svg)](https://github.com/features/copilot) [![AI-Powered](https://img.shields.io/badge/AI--Powered-Yes-9C88FF.svg)](https://ollama.ai) [![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-00ADD8.svg)](https://ollama.ai) [![Llama.cpp](https://img.shields.io/badge/Supports-Llama.cpp-FF6B35.svg)](https://github.com/ggerganov/llama.cpp)

[![Version](https://img.shields.io/badge/Version-2.0.0-green.svg)](#) [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org) [![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev) [![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com)

---

## What's New in 2.0

**Freya 2.0** introduces a complete architectural overhaul with a **modern web interface** replacing the TUI:

- **Modern Web UI** : Professional React interface with real-time updates
- **REST API** : FastAPI backend with WebSocket support
- **Real-time Monitoring** : Live progress tracking for benchmarks and BMAD cycles
- **Cyber Watch** : Integrated security vulnerability monitoring (CISA KEV, CERT-FR)
- **File Browser** : Built-in file management with syntax highlighting
- **Settings Panel** : Complete configuration management in the UI

---

## Features

Freya is an advanced multi-agent orchestrator aligned with the **BMAD workflow** (Business Model - Architecture - Development), designed to work with local LLMs via Ollama and Llama.cpp.

### Core Features

- **Complete BMAD Workflow** : From business analysis to code delivery
- **Multi-backend LLM Support** : Ollama and Llama.cpp
- **Intelligent Benchmarking** : Automatic model routing based on performance
- **Modern Web Interface** : Professional React-based UI
- **REST API** : Full-featured FastAPI backend

### Specialized Agents

| Agent | Role | Output |
|-------|------|--------|
| **Analyst** | Requirements analysis | `project-brief.md` |
| **PM** | Product requirements | `PRD.md` |
| **Architect** | Technical design | `architecture.md` |
| **PO** | Epic breakdown | `epics/*.md` |
| **SM** | User stories | `stories/*.md` |
| **Developer** | Code implementation | Source code |
| **QA** | Quality assurance | `QA.md` |

### Integrated Tools

- **Shell** : Secure command execution
- **WebWatch** : Security feed aggregation (CISA KEV, CERT-FR)
- **WebSearch** : Wikipedia and Brave search integration
- **Clipboard** : System clipboard operations
- **Redact** : Sensitive content protection

---

## Architecture

```
freya/
├── pyproject.toml               # Python project configuration
├── README.md                    # This documentation
│
├── src/freya/                   # Python backend
│   ├── cli.py                   # CLI (freya serve, freya bench-*, etc.)
│   ├── config.py                # Pydantic configuration
│   ├── orchestrator.py          # Agent coordination
│   ├── router.py                # LLM routing & benchmarking
│   ├── ollama_client.py         # Ollama API client
│   │
│   ├── api/                     # FastAPI REST API
│   │   ├── main.py              # App factory & lifespan
│   │   ├── websocket.py         # WebSocket manager
│   │   └── routes/              # API endpoints
│   │       ├── chat.py          # Chat generation
│   │       ├── bench.py         # Benchmarking
│   │       ├── bmad.py          # BMAD workflow
│   │       ├── models.py        # Model management
│   │       ├── files.py         # File browser
│   │       ├── watch.py         # Cyber watch
│   │       └── settings.py      # Configuration
│   │
│   ├── agents/                  # BMAD agents
│   │   ├── analyst.py
│   │   ├── architect.py
│   │   ├── dev.py
│   │   ├── pm.py
│   │   ├── po.py
│   │   ├── qa.py
│   │   └── sm.py
│   │
│   └── tools/                   # Integrated tools
│       ├── shell.py
│       ├── webwatch.py
│       ├── websearch.py
│       └── ...
│
└── web/                         # React frontend
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    └── src/
        ├── App.tsx
        ├── components/
        │   ├── layout/          # Sidebar, Header, StatusBar
        │   ├── chat/            # Chat interface
        │   ├── bench/           # Benchmark dashboard
        │   ├── bmad/            # BMAD Studio
        │   ├── settings/        # Settings panel
        │   ├── files/           # File browser
        │   └── watch/           # Cyber Watch
        ├── stores/              # Zustand state
        ├── hooks/               # React hooks
        └── lib/                 # API client
```

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for building the web UI)
- **Ollama** running locally at `http://localhost:11434`

### Installation

```powershell
# Clone the repository
git clone https://github.com/YOUR_USERNAME/freya.git
cd freya

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
| `freya serve --debug` | Start with auto-reload |
| `freya discover-models` | List installed Ollama models |
| `freya bench-fast` | Quick benchmark (~5 min) |
| `freya bench-standard` | Standard benchmark (~20 min) |
| `freya bench-advanced` | Full benchmark (~60 min) |
| `freya autopilot --goal "..."` | Generate project from goal |
| `freya tui` | Legacy TUI (requires `pip install freya[tui]`) |

---

## Configuration

Freya uses environment variables for configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `FREYA_MANAGED_ROOT` | `~/.freya` | Main data directory |
| `FREYA_OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `FREYA_OLLAMA_TIMEOUT_SEC` | `120` | Request timeout |
| `FREYA_WORKSPACE_ROOT` | Current directory | Working directory |

### Example Setup (PowerShell)

```powershell
$env:FREYA_MANAGED_ROOT = "H:\Code\.freya"
$env:FREYA_OLLAMA_URL = "http://localhost:11434"
$env:FREYA_WORKSPACE_ROOT = "H:\Code\Projects"
```

---

## Web Interface

### Pages

| Page | Description |
|------|-------------|
| **Chat** | AI conversation with hat/persona selection |
| **Bench** | Run and monitor LLM benchmarks |
| **BMAD** | BMAD Studio - run the full agent pipeline |
| **Settings** | Configuration, routing, prompts |
| **Files** | Browse and edit project files |
| **Watch** | Security vulnerability feed |

### Real-time Features

- **WebSocket** : Live updates for bench/BMAD progress
- **System Monitor** : CPU, RAM, disk usage
- **Connection Status** : Ollama connectivity indicator

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

## API Endpoints

### Health & System

- `GET /api/health` - Health check
- `GET /api/system` - System resources

### Chat

- `GET /api/chat/hats` - List persona presets
- `POST /api/chat/generate` - Generate response
- `POST /api/chat/search` - Web search

### Benchmark

- `GET /api/bench/status` - Current status
- `POST /api/bench/start` - Start benchmark
- `POST /api/bench/stop` - Stop benchmark
- `GET /api/bench/billboard` - Best scores

### BMAD

- `GET /api/bmad/status` - Pipeline status
- `POST /api/bmad/run` - Start BMAD cycle
- `GET /api/bmad/artifacts` - List artifacts

### Models

- `GET /api/models/` - List models
- `POST /api/models/pull` - Pull model
- `GET /api/models/routing` - Get routing config

### Files

- `GET /api/files/browse` - Directory listing
- `GET /api/files/read` - Read file
- `POST /api/files/write` - Write file

### Watch

- `GET /api/watch/` - Combined feed
- `GET /api/watch/cisa-kev` - CISA KEV feed
- `GET /api/watch/cert-fr` - CERT-FR feed
- `GET /api/watch/cve/{id}` - CVE lookup

---

## Changelog

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
- [Lucide](https://lucide.dev) - Icons

---

**Freya** - *BMAD-aligned multi-agent orchestrator for local LLMs*
