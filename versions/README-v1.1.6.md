# Freya v1.1.6

[![English](https://img.shields.io/badge/Language-English-blue.svg)](README.md) [![Fran├ºais](https://img.shields.io/badge/Langue-Fran├ºais-red.svg)](README.fr.md)

[![Built with AI](https://img.shields.io/badge/Built%20with-AI-FF6B6B.svg)](https://github.com/features/copilot) [![AI-Powered](https://img.shields.io/badge/AI--Powered-Yes-9C88FF.svg)](https://ollama.ai) [![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-00ADD8.svg)](https://ollama.ai) [![Llama.cpp](https://img.shields.io/badge/Supports-Llama.cpp-FF6B35.svg)](https://github.com/ggerganov/llama.cpp)

[![Llama 3.1](https://img.shields.io/badge/Model-Llama%203.1-FF6B35.svg)](https://ollama.ai/library/llama3.1) [![Mistral](https://img.shields.io/badge/Model-Mistral-9C88FF.svg)](https://ollama.ai/library/mistral) [![Qwen](https://img.shields.io/badge/Model-Qwen-00ADD8.svg)](https://ollama.ai/library/qwen) [![CodeLlama](https://img.shields.io/badge/Model-CodeLlama-FF6B6B.svg)](https://ollama.ai/library/codellama) [![Dolphin](https://img.shields.io/badge/Model-Dolphin-9C88FF.svg)](https://ollama.ai/library/dolphin-llama3)

Freya is an advanced multi-agent orchestrator aligned with the BMAD workflow (Business Model - Architecture - Development), designed to work with local LLMs via Ollama and Llama.cpp. It automates software development by coordinating specialized agents to transform a project brief into quality code.

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

Freya follows a modular architecture organized around specialized components:

```
freya2/
Ôö£ÔöÇÔöÇ freya.ps1                    # PowerShell installation script
Ôö£ÔöÇÔöÇ pyproject.toml               # Python project configuration
Ôö£ÔöÇÔöÇ README.md                    # Documentation
Ôö£ÔöÇÔöÇ bench_raw/                   # Raw benchmark data
ÔööÔöÇÔöÇ src/
    ÔööÔöÇÔöÇ freya/
        Ôö£ÔöÇÔöÇ __init__.py          # Package entry point
        Ôö£ÔöÇÔöÇ cli.py               # Command line interface
        Ôö£ÔöÇÔöÇ config.py            # Centralized configuration
        Ôö£ÔöÇÔöÇ orchestrator.py      # Agent coordination
        Ôö£ÔöÇÔöÇ router.py            # Intelligent LLM routing
        Ôö£ÔöÇÔöÇ tui.py               # Text user interface
        Ôö£ÔöÇÔöÇ benchmarkq.py        # Benchmarking suite
        Ôö£ÔöÇÔöÇ bmad_sync.py         # BMAD synchronization
        Ôö£ÔöÇÔöÇ console.py           # Console utilities
        Ôö£ÔöÇÔöÇ fsx.py               # File system extensions
        Ôö£ÔöÇÔöÇ ide.py               # IDE controller
        Ôö£ÔöÇÔöÇ llamacpp_server.py  # Llama.cpp client
        Ôö£ÔöÇÔöÇ loggingx.py          # Logging extensions
        Ôö£ÔöÇÔöÇ model_manager.py     # Model manager
        Ôö£ÔöÇÔöÇ monitoring.py        # System monitoring
        Ôö£ÔöÇÔöÇ ollama_client.py     # Ollama client
        Ôö£ÔöÇÔöÇ openai_compat_client.py # OpenAI compatibility
        Ôö£ÔöÇÔöÇ powershell.py        # PowerShell integration
        Ôö£ÔöÇÔöÇ quality.py           # Quality gates
        Ôö£ÔöÇÔöÇ agents/              # Specialized agents
        Ôöé   Ôö£ÔöÇÔöÇ __init__.py
        Ôöé   Ôö£ÔöÇÔöÇ analyst.py       # Analysis agent
        Ôöé   Ôö£ÔöÇÔöÇ architect.py     # Architecture agent
        Ôöé   Ôö£ÔöÇÔöÇ base.py          # Base agent class
        Ôöé   Ôö£ÔöÇÔöÇ dev.py           # Developer agent
        Ôöé   Ôö£ÔöÇÔöÇ pm.py            # Product Manager agent
        Ôöé   Ôö£ÔöÇÔöÇ po.py            # Product Owner agent
        Ôöé   Ôö£ÔöÇÔöÇ qa.py            # QA agent
        Ôöé   ÔööÔöÇÔöÇ sm.py            # Scrum Master agent
        ÔööÔöÇÔöÇ tools/               # Integrated tools
            Ôö£ÔöÇÔöÇ __init__.py
            Ôö£ÔöÇÔöÇ shell.py         # Shell tool
            ÔööÔöÇÔöÇ webwatch.py      # Web monitoring tool
```

- **Orchestrator** : System core, coordinates agents according to BMAD workflow
- **Router** : Manages request routing to appropriate LLMs based on benchmarks
- **Agents** : Specialized classes for each development workflow role
- **Tools** : Utilities to interact with system and web
- **LLM Clients** : Interfaces for Ollama and Llama.cpp
- **TUI** : Modern user interface with Textual

### Logical Architecture

#### Overview of interactions

```
                    ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
                    Ôöé   User          Ôöé
                    Ôöé   Interface     Ôöé
                    Ôöé     (TUI)       Ôöé
                    ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ
                              Ôöé
                              Ôû╝
                    ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
                    Ôöé  Orchestrator   Ôöé
                    Ôöé                 Ôöé
                    ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ
                              Ôöé
                              Ôû╝
                    ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
                    Ôöé     Router      Ôöé
                    Ôöé  (LLM Routing)  Ôöé
                    ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ
                              Ôöé
                    ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö╝ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
                    Ôöé         Ôöé         Ôöé
                    Ôû╝         Ôû╝         Ôû╝
          ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
          Ôöé    Ollama       Ôöé ÔöéLlama. Ôöé ÔöéOpenAI Ôöé
          Ôöé    Client       Ôöé Ôöécpp    Ôöé ÔöéCompat Ôöé
          ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ

                    ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
                    Ôöé   Specialized   Ôöé
                    Ôöé     Agents      Ôöé
                    Ôöé                 Ôöé
                    Ôöé ÔÇó Analyst       Ôöé
                    Ôöé ÔÇó Architect     Ôöé
                    Ôöé ÔÇó Dev           Ôöé
                    Ôöé ÔÇó PM/PO/SM/QA   Ôöé
                    ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö¼ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ
                              Ôöé
                              Ôû╝
                    ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔö╝ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
                    Ôöé         Ôöé         Ôöé
                    Ôû╝         Ôû╝         Ôû╝
          ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
          Ôöé     Tools       Ôöé ÔöéWeb-   Ôöé Ôöé IDE   Ôöé
          Ôöé    (Shell)      Ôöé ÔöéWatch  Ôöé ÔöéCtrl   Ôöé
          ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ

                    ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
                    Ôöé System          Ôöé
                    Ôöé Management      Ôöé
                    Ôöé                 Ôöé
                    Ôöé ÔÇó Config        Ôöé
                    Ôöé ÔÇó Monitoring    Ôöé
                    Ôöé ÔÇó Quality       Ôöé
                    Ôöé ÔÇó Model Manager Ôöé
                    Ôöé ÔÇó Logger        Ôöé
                    Ôöé ÔÇó FSX           Ôöé
                    ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ
```

1. **Interface** ÔåÆ **Orchestrator** : User command transmission
2. **Orchestrator** ÔåÆ **Router** : Intelligent LLM selection
3. **Router** ÔåÆ **LLM Clients** : AI request execution
4. **Orchestrator** ÔåÆ **Agents** : Business workflow coordination
5. **Agents** ÔåÆ **Tools** : Concrete actions (shell, web, IDE)
6. **System Management** : Cross-cutting support (config, monitoring, quality)

- **Orchestrator Ôåö BMAD Sync** : Development workflow management
- **Router Ôåö BenchmarkQ** : LLM performance optimization
- **Agents Ôåö Tools** : Operational task execution
- **TUI Ôåö All components** : Unified interface and visualization
- **System Management** : Shared infrastructure and monitoring

#### Layered Architecture

```
ÔöîÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÉ
Ôöé         User Interface              Ôöé
Ôöé               (TUI)                 Ôöé
Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ
Ôöé         Coordination                Ôöé
Ôöé        (Orchestrator)               Ôöé
Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ
Ôöé         Intelligence                Ôöé
Ôöé   (Router + BenchmarkQ + Agents)    Ôöé
Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ
Ôöé         Execution                   Ôöé
Ôöé   (LLM Clients + Tools)             Ôöé
Ôö£ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöñ
Ôöé         Infrastructure              Ôöé
Ôöé   (Config + Monitoring + System)    Ôöé
ÔööÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÿ
```

## Quickstart (Windows)

### 1) Install (editable)

```powershell
cd H:\Code\Freya2
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e .
```

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

The TUI interface offers several tabs :

- **Chat** : Direct interaction with agents
- **Bench** : Benchmark management and visualization
- **Dev** : Integrated development tools
- **Settings** : Advanced configuration
- **Files** : Project file management
- **Watch** : Real-time web monitoring

1. **Business Model** : Project analysis and briefing
2. **Architecture** : Technical design and specifications
3. **Development** : Iterative implementation with agents
4. **Delivery** : Finalized and tested code

Freya never deletes files outside its `.freya` directory. All operations are isolated and caches/logs are automatically managed.

## Supported LLM Servers

- Default server : http://localhost:11434
- Automatic routing by role based on benchmarks

- Configurable server via `FREYA_LLAMACPP_*`
- Support for local GGUF models

Freya is developed in Python 3.11+ with the following dependencies :

- pydantic : Data validation
- requests : HTTP communications
- rich : Enhanced console interface
- textual : TUI framework
- psutil : System monitoring

## Version

Current version: **1.1.5**

## Patch Notes

### v1.1.5 (January 25, 2026)

- Consolidated README into a single bilingual file (English & French)
- Added comprehensive Commands (CLI) section with autopilot command
- Added high-level Architecture overview with simplified diagram
- Added Security guidelines and recommendations
- Added Fonts & icons recommendations for terminal display
- Added Status & roadmap with current features and upcoming developments
- Added References / Sources section with relevant links
- Updated Quickstart with detailed Windows installation steps
- Removed redundant separate French README file
- Updated language badges to reflect unified bilingual documentation

### v1.1 (January 25, 2026)

- Added CaskaydiaCove Nerd Font support for enhanced terminal display
- Enhanced TUI with clipboard integration (copy last answer)
- Added benchmark live progress bars and controls
- Improved artifact management with hover and selection
- Added new tools: clipboard.py and redact.py for security
- Updated UI layout with better proportions (60/40 split)
- Added VS Code workspace opening functionality
- Improved chat logging with Markdown rendering and panels
- Added PowerShell status integration in TUI
- Enhanced Cyber Watch with better formatting and prioritization
- Added progress tracking for benchmark phases and models
- Fixed async handling in TUI artifacts tree reload for improved stability

## Commands (CLI)

### Model management

- `freya discover-models` ÔÇö list installed Ollama models

### Benchmarking

- `freya bench-fast` ÔÇö fast (1 trial)
- `freya bench-standard` ÔÇö standard (5 trials)
- `freya bench-advanced` ÔÇö advanced (5 trials)

### UI

- `freya tui` ÔÇö launch the Textual interface

### Delivery automation

- `freya autopilot --goal ... --name ... --output ...` ÔÇö generate a project + tests + open VS Code

## Architecture (high-level)

Freya is designed as a modular system:

- **CLI (freya)** : commands (discover/bench/tui/autopilot)
- **Router (LLMRouter)** : bench + routing requests to the best model
- **LLM Clients** : Ollama (and optionally llama.cpp server)
- **TUI (Textual)** : terminal UI
- **Autopilot** : reproducible pipeline "project ÔåÆ code ÔåÆ tests ÔåÆ validation ÔåÆ VS Code"
- **Artifacts & logs** : JSONL events and resume-friendly state

### Logical diagram (simplified)

```
User (TUI/CLI)
   |
   v
Orchestrator / Autopilot
   |
   +--> Router (bench + pick best model)
   |         |
   |         +--> Ollama / llama.cpp
   |
   +--> Tools (shell / web watch / fs / ide)
   |
   +--> Artifacts + Logs (JSONL) + State (resume)
```

## Security

- **Local-first** : local execution, local models.
- **Traceability** : event logs (JSONL) for diagnosis/replay.
- **Strong recommendation** : never paste tokens/keys in plain text in the UI, prompts or logs.

## Fonts & icons (recommended)

For clean rendering (terminal icons), use a Nerd Font in Windows Terminal (ex: CaskaydiaCove Nerd Font) then configure the profile.

## Status & roadmap

### Ô£à Already operational:

- CLI (discover, bench, tui)
- Bench + routing (selection by role)
- Autopilot V1 (project + tests + VS Code opening)

### ­ƒö£ Coming iteratively:

- Complete BMAD Orchestrator (artifacts + run/resume)
- Dev/QA loop "tests failing ÔåÆ patch ÔåÆ retest" via LLMRouter
- Dedicated Bench Chat / Summary / Web-research
- Filled and editable Settings (prompts/presets/hats)
- Cyber Watch (watch) via public sources (API/RSS), formatted FR

## References / Sources

- **BMAD Method** (workflow & artefacts): https://github.com/bmad-code-org/BMAD-METHOD
- **Ollama API** (tags/generate): https://github.com/ollama/ollama/blob/main/docs/api.md
- **llama.cpp** (server): https://github.com/ggerganov/llama.cpp
- **Textual** (TUI framework): https://textual.textualize.io/
- **VS Code CLI** (code): https://code.visualstudio.com/docs/editor/command-line
- **Python venv**: https://docs.python.org/3/library/venv.html
- **Pytest**: https://docs.pytest.org/en/stable/
- **Windows Terminal settings** (fonts, profiles): https://learn.microsoft.com/windows/terminal/customize-settings/profile-settings
- **Nerd Fonts**: https://www.nerdfonts.com/
