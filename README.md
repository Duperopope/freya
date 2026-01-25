# Freya

[![English](https://img.shields.io/badge/Language-English-blue.svg)](README.md) [![Français](https://img.shields.io/badge/Langue-Français-red.svg)](README.fr.md)

[![Built with AI](https://img.shields.io/badge/Built%20with-AI-FF6B6B.svg)](https://github.com/features/copilot) [![AI-Powered](https://img.shields.io/badge/AI--Powered-Yes-9C88FF.svg)](https://ollama.ai) [![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-00ADD8.svg)](https://ollama.ai) [![Llama.cpp](https://img.shields.io/badge/Supports-Llama.cpp-FF6B35.svg)](https://github.com/ggerganov/llama.cpp)

[![Llama 3.1](https://img.shields.io/badge/Model-Llama%203.1-FF6B35.svg)](https://ollama.ai/library/llama3.1) [![Mistral](https://img.shields.io/badge/Model-Mistral-9C88FF.svg)](https://ollama.ai/library/mistral) [![Qwen](https://img.shields.io/badge/Model-Qwen-00ADD8.svg)](https://ollama.ai/library/qwen) [![CodeLlama](https://img.shields.io/badge/Model-CodeLlama-FF6B6B.svg)](https://ollama.ai/library/codellama) [![Dolphin](https://img.shields.io/badge/Model-Dolphin-9C88FF.svg)](https://ollama.ai/library/dolphin-llama3)

Freya is an advanced multi-agent orchestrator aligned with the BMAD workflow (Business Model - Architecture - Development), designed to work with local LLMs via Ollama and Llama.cpp. It automates software development by coordinating specialized agents to transform a project brief into quality code.

## Main Features

- **Complete BMAD Workflow** : From business analysis to code delivery through specialized agents
- **Multi-backend LLM Support** : Ollama and Llama.cpp for maximum flexibility
- **Intelligent Benchmarking** : Automatic model routing by role based on performance benchmarks
- **Modern TUI Interface** : Interactive text-based user interface with Textual
- **Specialized Agents** :
  - Analyst : Requirements analysis
  - Product Owner : Business priorities management
  - Architect : Technical design
  - Scrum Master : Team coordination
  - Developer : Code development
  - QA : Quality assurance
- **Integrated Tools** :
  - Shell : System command execution
  - WebWatch : Web monitoring and scraping
- **Model Management** : Automatic downloading, tracking and optimization
- **Enhanced Security** : Operations isolation in managed directories

## Architecture

Freya follows a modular architecture organized around specialized components :

```
freya2/
├── freya.ps1                    # PowerShell installation script
├── pyproject.toml               # Python project configuration
├── README.md                    # Documentation
├── bench_raw/                   # Raw benchmark data
└── src/
    └── freya/
        ├── __init__.py          # Package entry point
        ├── cli.py               # Command line interface
        ├── config.py            # Centralized configuration
        ├── orchestrator.py      # Agent coordination
        ├── router.py            # Intelligent LLM routing
        ├── tui.py               # Text user interface
        ├── benchmarkq.py        # Benchmarking suite
        ├── bmad_sync.py         # BMAD synchronization
        ├── console.py           # Console utilities
        ├── fsx.py               # File system extensions
        ├── ide.py               # IDE controller
        ├── llamacpp_server.py  # Llama.cpp client
        ├── loggingx.py          # Logging extensions
        ├── model_manager.py     # Model manager
        ├── monitoring.py        # System monitoring
        ├── ollama_client.py     # Ollama client
        ├── openai_compat_client.py # OpenAI compatibility
        ├── powershell.py        # PowerShell integration
        ├── quality.py           # Quality gates
        ├── agents/              # Specialized agents
        │   ├── __init__.py
        │   ├── analyst.py       # Analysis agent
        │   ├── architect.py     # Architecture agent
        │   ├── base.py          # Base agent class
        │   ├── dev.py           # Developer agent
        │   ├── pm.py            # Product Manager agent
        │   ├── po.py            # Product Owner agent
        │   ├── qa.py            # QA agent
        │   └── sm.py            # Scrum Master agent
        └── tools/               # Integrated tools
            ├── __init__.py
            ├── shell.py         # Shell tool
            └── webwatch.py      # Web monitoring tool
```

### Main Components

- **Orchestrator** : System core, coordinates agents according to BMAD workflow
- **Router** : Manages request routing to appropriate LLMs based on benchmarks
- **Agents** : Specialized classes for each development workflow role
- **Tools** : Utilities to interact with system and web
- **LLM Clients** : Interfaces for Ollama and Llama.cpp
- **TUI** : Modern user interface with Textual

### Logical Architecture

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

#### Main Data Flow

1. **Interface** → **Orchestrator** : User command transmission
2. **Orchestrator** → **Router** : Intelligent LLM selection
3. **Router** → **LLM Clients** : AI request execution
4. **Orchestrator** → **Agents** : Business workflow coordination
5. **Agents** → **Tools** : Concrete actions (shell, web, IDE)
6. **System Management** : Cross-cutting support (config, monitoring, quality)

#### Functional Relationships

- **Orchestrator ↔ BMAD Sync** : Development workflow management
- **Router ↔ BenchmarkQ** : LLM performance optimization
- **Agents ↔ Tools** : Operational task execution
- **TUI ↔ All components** : Unified interface and visualization
- **System Management** : Shared infrastructure and monitoring

#### Layered Architecture

```
┌─────────────────────────────────────┐
│         User Interface              │
│               (TUI)                 │
├─────────────────────────────────────┤
│         Coordination                │
│        (Orchestrator)               │
├─────────────────────────────────────┤
│         Intelligence                │
│   (Router + BenchmarkQ + Agents)    │
├─────────────────────────────────────┤
│         Execution                   │
│   (LLM Clients + Tools)             │
├─────────────────────────────────────┤
│         Infrastructure              │
│   (Config + Monitoring + System)    │
└─────────────────────────────────────┘
```

## Installation

```bash
pip install -e .
```

## Configuration

Freya uses a flexible configuration system via environment variables :

- `FREYA_MANAGED_ROOT` : Management directory (.freya by default)
- `FREYA_OLLAMA_URL` : Ollama server URL (http://localhost:11434)
- `FREYA_LLAMACPP_EXE` : Path to llama-server.exe
- `FREYA_GGUF_DIR` : Directory for GGUF models
- `FREYA_DISK_FREE_MIN_GB` : Minimum required disk space (40GB)

## Commands

### Discovery and benchmarking

- `freya discover-models` : List installed Ollama models
- `freya bench-fast` : Fast benchmark (1 trial, quick mode)
- `freya bench-standard` : Standard benchmark (5 trials, tune mode)
- `freya bench-advanced` : Advanced benchmark (5 trials, tune mode)

### User interface

- `freya tui` : Launch the interactive text user interface

## TUI Interface

The TUI interface offers several tabs :

- **Chat** : Direct interaction with agents
- **Bench** : Benchmark management and visualization
- **Dev** : Integrated development tools
- **Settings** : Advanced configuration
- **Files** : Project file management
- **Watch** : Real-time web monitoring

## BMAD Workflow

1. **Business Model** : Project analysis and briefing
2. **Architecture** : Technical design and specifications
3. **Development** : Iterative implementation with agents
4. **Delivery** : Finalized and tested code

## Security

Freya never deletes files outside its `.freya` directory. All operations are isolated and caches/logs are automatically managed.

## Supported LLM Servers

### Ollama

- Default server : http://localhost:11434
- Automatic routing by role based on benchmarks

### Llama.cpp

- Configurable server via `FREYA_LLAMACPP_*`
- Support for local GGUF models

## Development

Freya is developed in Python 3.11+ with the following dependencies :

- pydantic : Data validation
- requests : HTTP communications
- rich : Enhanced console interface
- textual : TUI framework
- psutil : System monitoring
