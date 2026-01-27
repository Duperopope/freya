# Freya 2.5.5

[![Built with AI](https://img.shields.io/badge/Built%20with-AI-FF6B6B.svg)](https://github.com/features/copilot) [![AI-Powered](https://img.shields.io/badge/AI--Powered-Yes-9C88FF.svg)](https://ollama.ai) [![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-00ADD8.svg)](https://ollama.ai) [![Llama.cpp](https://img.shields.io/badge/Supports-Llama.cpp-FF6B35.svg)](https://github.com/ggerganov/llama.cpp)

<details>
<summary>🛠️ Tech Stack / Pile Technologique</summary>

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org) [![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev) [![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com) [![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://typescriptlang.org) [![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-38BDF8.svg)](https://tailwindcss.com)

</details>

<details>
<summary>📦 Version / Version</summary>

[![Version](https://img.shields.io/badge/Version-2.5.5-green.svg)](#)

</details>

<details>
<summary>🌐 Languages / Langues</summary>

[![English](https://img.shields.io/badge/Language-English-blue.svg)](README.md) [![Français](https://img.shields.io/badge/Langue-Français-red.svg)](localization/README.fr.md) [![Español](https://img.shields.io/badge/Idioma-Español-green.svg)](localization/README.es.md) [![Deutsch](https://img.shields.io/badge/Sprache-Deutsch-yellow.svg)](localization/README.de.md) [![中文](https://img.shields.io/badge/语言-中文-purple.svg)](localization/README.zh.md) [![Italiano](https://img.shields.io/badge/Lingua-Italiano-orange.svg)](localization/README.it.md) [![Português](https://img.shields.io/badge/Idioma-Português-pink.svg)](localization/README.pt.md) [![Русский](https://img.shields.io/badge/Язык-Русский-cyan.svg)](localization/README.ru.md) [![日本語](https://img.shields.io/badge/言語-日本語-red.svg)](localization/README.ja.md) [![한국어](https://img.shields.io/badge/언어-한국어-teal.svg)](localization/README.ko.md) [![العربية](https://img.shields.io/badge/اللغة-العربية-brown.svg)](localization/README.ar.md) [![हिन्दी](https://img.shields.io/badge/भाषा-हिन्दी-maroon.svg)](localization/README.hi.md)

</details>

---

## Table of Contents

- [🚀 Quick Start](#-quick-start)
- [🤖 Core Features](#-core-features)
- [🧠 BMAD Multi-Agent Orchestration](#-bmad-multi-agent-orchestration)
- [🔀 Hybrid LLM Routing](#-hybrid-llm-routing)
- [💬 Real-Time Chat System](#-real-time-chat-system)
- [🖥️ User Interfaces](#-user-interfaces)
- [📊 Benchmarking Suite](#-benchmarking-suite)
- [🛡️ Cyber Security Monitoring](#-cyber-security-monitoring)
- [🔬 Research & Autonomous Modes](#-research--autonomous-modes)
- [🌐 Web Interface](#-web-interface)
- [📦 Technical Architecture](#-technical-architecture)
- [🛠️ Installation & Setup](#-installation--setup)
- [📚 Documentation](#-documentation)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

<p align="center">
  <img src="web/public/freya-icon.svg" alt="Freya Logo" width="120" />
</p>

<h3 align="center">BMAD-aligned Multi-Agent Orchestrator for Local LLMs</h3>

<p align="center">
  <strong>Modern • Real-time • Privacy-First • Hybrid Routing</strong>
</p>

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm (for web interface)
- **Ollama** (optional, for local LLM support)
- **Git** for cloning the repository

### One-Click Installation (Windows)

```powershell
# Download and run the installer
irm https://raw.githubusercontent.com/your-repo/freya/main/install.ps1 | iex
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/freya.git
cd freya

# Install Python dependencies
pip install -r requirements.txt

# Install web interface dependencies
cd web && npm install && cd ..

# Start the application
python -m freya
```

### First Run

1. **Configure Providers**: Set up Ollama and/or OpenAI API keys
2. **Run Benchmarks**: Execute the benchmarking suite to optimize model selection
3. **Start Chatting**: Use the TUI, CLI, or web interface for interactions

---

## 🤖 Core Features

### 🎯 Multi-Agent Orchestration

- **BMAD Framework**: 7 specialized agents working in coordinated pipelines
- **Role-Based Agents**: Analyst, Project Manager, Architect, Product Owner, Scrum Master, Developer, QA
- **Autonomous Operation**: Full project lifecycle from concept to delivery
- **Real-Time Collaboration**: Agents communicate and iterate in real-time

### 🔄 Hybrid Routing System

- **Intelligent Provider Selection**: Automatic choice between local (Ollama) and remote (OpenAI) models
- **Performance-Based Routing**: Benchmark-driven model selection for optimal results
- **Fallback Mechanisms**: Seamless switching when providers are unavailable
- **Cost Optimization**: Balance between speed, quality, and cost

### 💬 Advanced Chat Modes

- **Research Mode**: Internet research → market analysis → BMAD brief generation
- **Exchange Mode**: Two AI models discuss topics autonomously with synthesis
- **Autonomous Mode**: Full pipeline execution from research to code generation
- **Best Agent Mode**: Automatic model selection based on benchmark performance

### 📊 Comprehensive Benchmarking

- **Multi-Phase Testing**: Fast → Coarse → Advanced benchmark progression
- **External Benchmarks**: Pre-integrated MMLU, HellaSwag, TruthfulQA, GSM8K, HumanEval, and more
- **Real-Time Visualization**: Live performance tracking and comparison
- **Automated Optimization**: Continuous model performance monitoring

### 🛡️ Cyber Security Integration

- **CyberAgent**: AI-powered security analyst for threat analysis
- **Daily Threat Briefings**: Automated CVE summaries and risk assessments
- **Batch Analysis**: Multi-CVE evaluation with remediation suggestions
- **Security Monitoring**: Real-time cyber threat intelligence

### 🌐 Modern Web Interface

- **React 18 + TypeScript**: Modern frontend with type safety
- **Tailwind CSS**: Beautiful, responsive design
- **WebSocket Communication**: Real-time updates and persistent connections
- **Multi-Language Support**: 11 languages with full localization

### 🖥️ Multiple UI Options

- **Textual TUI**: Rich terminal interface with real-time updates
- **Command Line Interface**: Full CLI with argument parsing and rich formatting
- **Web Dashboard**: Modern browser-based interface
- **API Endpoints**: REST and WebSocket APIs for integration

---

## 🧠 BMAD Multi-Agent Orchestration

Freya implements the **BMAD (Multi-Agent Decision)** framework, orchestrating 7 specialized agents in a coordinated pipeline:

### Agent Pipeline

```
Analyst → Project Manager → Architect → Product Owner → Scrum Master → Developer → QA
```

### Agent Roles & Capabilities

| Agent               | Role                    | Key Responsibilities                                          |
| ------------------- | ----------------------- | ------------------------------------------------------------- |
| **Analyst**         | Research & Analysis     | Market research, requirement gathering, feasibility analysis  |
| **Project Manager** | Planning & Coordination | Timeline management, resource allocation, risk assessment     |
| **Architect**       | System Design           | Technical architecture, design patterns, scalability planning |
| **Product Owner**   | Requirements            | User story creation, prioritization, acceptance criteria      |
| **Scrum Master**    | Process Management      | Agile methodology, team coordination, impediment removal      |
| **Developer**       | Implementation          | Code writing, debugging, technical documentation              |
| **QA**              | Quality Assurance       | Testing, validation, quality metrics, bug tracking            |

### Pipeline Features

- **Real-Time Communication**: Agents collaborate with live updates
- **Iterative Refinement**: Continuous improvement through feedback loops
- **Validation Cycles**: Automated testing and validation at each stage
- **Resume Functionality**: Continue interrupted pipelines from any point
- **TestRunner Integration**: Automated testing throughout the development cycle

---

## 🔀 Hybrid LLM Routing

Freya's intelligent routing system provides optimal LLM selection and utilization:

### Provider Support

- **Local Models**: Ollama integration with Llama.cpp backend
- **Remote Models**: OpenAI API with GPT models
- **Hybrid Routing**: Automatic provider selection based on context and performance

### Routing Intelligence

- **Benchmark-Driven Selection**: Uses performance data to choose optimal models
- **Context-Aware Routing**: Different models for different task types
- **Fallback Mechanisms**: Seamless switching when primary providers fail
- **Cost Optimization**: Balance between local (free) and remote (paid) usage

### Configuration Options

```python
# Hybrid routing configuration
routing_config = {
    "providers": {
        "ollama": {"enabled": True, "models": ["llama2", "codellama"]},
        "openai": {"enabled": True, "api_key": "your-key", "models": ["gpt-4", "gpt-3.5-turbo"]}
    },
    "routing": {
        "strategy": "performance",  # performance, cost, or manual
        "thresholds": {"min_score": 0.7, "max_cost": 0.02}
    }
}
```

---

## 💬 Real-Time Chat System

### Chat Modes

#### 🤖 Research Mode

- **Internet Research**: Automated web research with source validation
- **Market Analysis**: Competitive analysis and trend identification
- **BMAD Brief Generation**: Structured briefs for multi-agent processing
- **Source Citations**: Verified sources with credibility scoring

#### 🔄 Exchange Mode

- **Multi-Model Discussion**: Two AI models debate topics autonomously
- **Synthesis Agent**: Cross-validation and consensus building
- **Perspective Diversity**: Multiple viewpoints for comprehensive analysis
- **Structured Output**: Organized discussion summaries

#### 🎯 Autonomous Mode

- **Full Pipeline Execution**: Research → Analysis → Planning → Implementation
- **Real-Time Progress**: Live updates throughout the process
- **Quality Validation**: Automated testing and refinement cycles
- **Resume Capability**: Continue interrupted autonomous operations

#### 🧠 Best Agent Mode

- **Automatic Model Selection**: Benchmark-based optimal model choice
- **Performance Thresholds**: Configurable quality requirements (50-95%)
- **Style Preferences**: Fast, Balanced, or Quality modes
- **Per-Role Overrides**: Manual control when needed

### Chat Features

- **Conversation Persistence**: Reliable chat history preservation
- **Export Functionality**: JSON export with full metadata
- **Share Links**: Base64-encoded shareable conversation URLs
- **Real-Time Logging**: Live progress updates and status monitoring

---

## 🖥️ User Interfaces

### Textual TUI (Terminal User Interface)

- **Rich Formatting**: Colors, styles, and interactive elements
- **Real-Time Updates**: Live data visualization and progress tracking
- **Keyboard Navigation**: Full keyboard control with shortcuts
- **Multi-Panel Layout**: Organized information display

### Command Line Interface (CLI)

- **Rich Argument Parsing**: Comprehensive command-line options
- **Progress Indicators**: Visual progress bars and status updates
- **Error Handling**: Clear error messages and recovery suggestions
- **Scripting Support**: Automation-friendly command structure

### Web Interface

- **React 18 Frontend**: Modern, responsive user interface
- **TypeScript**: Type-safe development and better IDE support
- **Tailwind CSS**: Utility-first styling for consistent design
- **WebSocket Integration**: Real-time bidirectional communication

### API Endpoints

- **REST API**: Full RESTful API for all functionality
- **WebSocket Support**: Real-time event streaming
- **OpenAPI Documentation**: Auto-generated API documentation
- **Integration Ready**: Easy integration with other systems

---

## 📊 Benchmarking Suite

### Benchmark Categories

#### 🚀 Performance Benchmarks

- **Response Time**: Latency measurement across different model sizes
- **Throughput**: Requests per second under various loads
- **Memory Usage**: RAM and VRAM consumption tracking
- **CPU Utilization**: Processing efficiency metrics

#### 🎯 Capability Benchmarks

- **MMLU**: Multi-task language understanding (57 subjects)
- **HellaSwag**: Commonsense reasoning and reading comprehension
- **TruthfulQA**: Factual accuracy and truthfulness
- **GSM8K**: Mathematical reasoning and problem-solving
- **HumanEval**: Code generation and programming tasks
- **MBPP**: Basic programming problems
- **ARC-Challenge**: Scientific reasoning and knowledge
- **MT-Bench**: Multi-turn conversational abilities
- **WinoGrande**: Commonsense reasoning at scale

### Benchmarking Features

- **Multi-Phase Execution**: Fast → Coarse → Advanced progression
- **Real-Time Visualization**: Live performance graphs and comparisons
- **Automated Scheduling**: Regular benchmark execution
- **Historical Tracking**: Performance trends over time
- **Model Comparison**: Side-by-side performance analysis

### External Benchmarks Integration

Pre-integrated benchmarks with automated execution and result analysis:

| Benchmark     | Category    | Metrics   | Status        |
| ------------- | ----------- | --------- | ------------- |
| MMLU          | Knowledge   | Accuracy  | ✅ Integrated |
| HellaSwag     | Reasoning   | Accuracy  | ✅ Integrated |
| TruthfulQA    | Factuality  | MC1, MC2  | ✅ Integrated |
| GSM8K         | Math        | Accuracy  | ✅ Integrated |
| HumanEval     | Coding      | Pass@1    | ✅ Integrated |
| MBPP          | Programming | Pass@1    | ✅ Integrated |
| ARC-Challenge | Science     | Accuracy  | ✅ Integrated |
| MT-Bench      | Chat        | Avg Score | ✅ Integrated |
| WinoGrande    | Commonsense | Accuracy  | ✅ Integrated |

---

## 🛡️ Cyber Security Monitoring

### CyberAgent Features

- **AI-Powered Analysis**: Intelligent threat assessment and recommendations
- **CVE Processing**: Automated vulnerability analysis and prioritization
- **Daily Briefings**: Executive summaries with actionable insights
- **Batch Analysis**: Multi-CVE evaluation with risk scoring
- **Remediation Guidance**: AI-generated patching and mitigation strategies

### Security Monitoring

- **Real-Time Alerts**: Live cyber threat intelligence
- **Threat Intelligence**: Integration with security databases
- **Risk Assessment**: Automated risk scoring and prioritization
- **Compliance Monitoring**: Regulatory compliance tracking

### Security Queries

- **Pre-built Prompts**: Common security questions and scenarios
- **Custom Analysis**: Flexible threat modeling and assessment
- **Historical Tracking**: Security incident timeline and trends
- **Report Generation**: Comprehensive security reports and briefings

---

## 🔬 Research & Autonomous Modes

### Research Mode

- **Internet Research**: Automated web scraping and analysis
- **Source Validation**: Credibility checking and fact verification
- **Market Intelligence**: Competitive analysis and trend identification
- **Structured Briefs**: BMAD-ready research summaries

### Autonomous Mode

- **Full Pipeline Automation**: End-to-end project execution
- **Quality Gates**: Automated validation at each pipeline stage
- **Iterative Refinement**: Continuous improvement through feedback
- **Progress Tracking**: Real-time status updates and logging

### Advanced Features

- **Multi-Agent Cross-Check**: Validation through multiple AI perspectives
- **Error Recovery**: Automatic error detection and correction
- **Resource Management**: Intelligent resource allocation and optimization
- **Scalability**: Horizontal scaling for large projects

---

## 🌐 Web Interface

### Frontend Architecture

- **React 18**: Latest React features with concurrent rendering
- **TypeScript**: Type-safe development and enhanced developer experience
- **Tailwind CSS**: Utility-first CSS framework for rapid styling
- **Vite**: Fast build tool with hot module replacement

### Real-Time Features

- **WebSocket Communication**: Bidirectional real-time updates
- **Live Progress Tracking**: Real-time pipeline execution monitoring
- **Interactive Chat**: Web-based chat interface with all modes
- **Dynamic Dashboards**: Live data visualization and analytics

### User Experience

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark/Light Themes**: User preference-based theming
- **Accessibility**: WCAG compliant interface design
- **Multi-Language**: Full internationalization support

---

## 📦 Technical Architecture

### Backend (Python/FastAPI)

- **FastAPI Framework**: High-performance async web framework
- **Pydantic Models**: Data validation and serialization
- **Async/Await**: Concurrent processing with asyncio
- **WebSocket Support**: Real-time bidirectional communication

### Agent System

- **Modular Architecture**: Pluggable agent system
- **Message Passing**: Inter-agent communication protocols
- **State Management**: Persistent state across sessions
- **Error Handling**: Comprehensive error recovery and logging

### LLM Integration

- **Provider Abstraction**: Unified interface for different LLM providers
- **Caching Layer**: Response caching for improved performance
- **Rate Limiting**: Intelligent rate limiting and quota management
- **Fallback System**: Automatic provider switching on failures

### Data Management

- **SQLite Database**: Local data storage with migration support
- **Configuration Management**: Hierarchical configuration system
- **Session Persistence**: Chat history and state preservation
- **Export/Import**: Data portability and backup features

---

## 🛠️ Installation & Setup

### System Requirements

- **Operating System**: Windows 10+, macOS 11+, Linux (Ubuntu 20.04+)
- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher (for web interface)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space

### Installation Methods

#### One-Click Installer (Windows)

```powershell
# Download and execute installer
irm https://raw.githubusercontent.com/your-repo/freya/main/install.ps1 | iex
```

#### Manual Installation

```bash
# Clone repository
git clone https://github.com/your-repo/freya.git
cd freya

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install web dependencies
cd web
npm install
cd ..

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings
```

### Configuration

```bash
# Environment variables
OPENAI_API_KEY=your_openai_key
OLLAMA_BASE_URL=http://localhost:11434
FREYA_WEB_PORT=8000
FREYA_LOG_LEVEL=INFO
```

### First-Time Setup

1. **Install Ollama** (optional): `https://ollama.ai/download`
2. **Pull Models**: `ollama pull llama2` and `ollama pull codellama`
3. **Configure API Keys**: Set up OpenAI API key in environment
4. **Run Benchmarks**: Execute initial benchmarking suite
5. **Start Application**: Launch with `python -m freya`

---

## 📚 Documentation

### 📖 User Guides

- **[Quick Start Guide](docs/quick-start.md)**: Get up and running in minutes
- **[User Manual](docs/user-manual.md)**: Comprehensive usage instructions
- **[API Reference](docs/api-reference.md)**: Complete API documentation
- **[Troubleshooting](docs/troubleshooting.md)**: Common issues and solutions

### 🏗️ Technical Documentation

- **[Architecture Overview](architecture/Architecture.md)**: System design and components
- **[Module Documentation](documentation/modules/modules.md)**: Detailed module breakdown
- **[Development Guide](docs/development.md)**: Contributing and development setup
- **[Security Guide](docs/security.md)**: Security features and best practices

### 🎯 Interactive Resources

- **[Version History Mindmap](architecture/architecture_documentation.html)**: Interactive evolution timeline
- **[Live Demo](https://demo.freya.ai)**: Try Freya in your browser
- **[Video Tutorials](https://youtube.com/freya-ai)**: Step-by-step video guides
- **[Community Forum](https://forum.freya.ai)**: User discussions and support

### 🌐 Internationalization

Complete documentation in 11 languages:

- English, Français, Español, Deutsch, 中文, Italiano, Português, Русский, 日本語, 한국어, العربية, हिन्दी

---

## 🤝 Contributing

### Development Setup

```bash
# Fork and clone
git clone https://github.com/your-username/freya.git
cd freya

# Set up development environment
pip install -r requirements-dev.txt
pre-commit install

# Run tests
pytest

# Start development server
python -m freya --dev
```

### Code Quality

- **Type Hints**: Full Python type hinting
- **Linting**: Ruff for fast, comprehensive linting
- **Testing**: pytest with comprehensive test coverage
- **Documentation**: Auto-generated API docs with FastAPI

### Contribution Guidelines

- **Issues**: Use issue templates for bug reports and feature requests
- **Pull Requests**: Follow the PR template and include tests
- **Code Style**: Follow PEP 8 with Ruff formatting
- **Documentation**: Update docs for any user-facing changes

### Community

- **Discord**: Real-time chat and support
- **GitHub Discussions**: Feature discussions and Q&A
- **Newsletter**: Monthly updates and roadmap
- **Events**: Virtual meetups and workshops

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

- **Ollama**: Apache 2.0
- **Llama.cpp**: MIT
- **FastAPI**: MIT
- **React**: MIT
- **Tailwind CSS**: MIT

### Acknowledgments

- **BMAD Framework**: Multi-agent orchestration methodology
- **Ollama**: Local LLM inference
- **OpenAI**: Remote LLM API
- **Textual**: Python TUI framework
- **Community Contributors**: Open source community support

---

## 📞 Support & Contact

### Getting Help

- **Documentation**: Comprehensive docs at [docs.freya.ai](https://docs.freya.ai)
- **Community Forum**: [forum.freya.ai](https://forum.freya.ai)
- **Discord**: [discord.gg/freya](https://discord.gg/freya)
- **GitHub Issues**: Bug reports and feature requests

### Professional Support

- **Enterprise Support**: Custom deployments and integrations
- **Training**: Team training and workshops
- **Consulting**: Architecture review and optimization
- **Custom Development**: Tailored features and modifications

### Stay Updated

- **Newsletter**: Monthly updates and roadmap
- **Blog**: Technical articles and tutorials
- **YouTube**: Video tutorials and demos
- **Twitter**: News and announcements

---

---

_Freya is an open-source project built with ❤️ by the AI community. Your contributions and feedback help make it better for everyone._

- Symptoms: 401/403 errors when using remote providers
- Solutions: Set API keys in environment (GROQ_API_KEY, HF_API_KEY, TOGETHER_API_KEY)

**4. High Memory Usage**

- Symptoms: System slowdown during benchmarks, OOM errors
- Solutions: Limit concurrent models, use smaller variants, edit routing.json

**5. BMAD Pipeline Stuck**

- Symptoms: Pipeline hangs on an agent
- Solutions: Check debug logs, use Stop button, verify Ollama responsiveness

**6. Frontend Build Errors**

- Symptoms: TypeScript errors, build failures
- Solutions: Clean node_modules, reinstall, rebuild

**7. WebSocket Disconnection**

- Symptoms: Real-time updates stop, "Disconnected" status
- Solutions: Refresh page, check backend, verify CORS

**Debug & Logs**:

- Platform-specific log paths (Windows: %USERPROFILE%\.freya\logs\, Linux/macOS: ~/.freya/logs/)
- Debug mode: `freya serve --debug`
- API health check: `curl http://localhost:8765/api/health`
</details>

### 2.2.0

- feat: Enhanced BenchPage and BMAD with v2.1 features

### 2.1.2

- docs: Update to version 2.1 with comprehensive architecture documentation

### 2.1.1

- feat: Major improvements - Web search, Cyber Watch, Settings

### 2.1.0

- fix: ensure static files are served in both debug and production modes

### 2.0.3

- fix: add WebSocket endpoint route before static files mount

### 2.0.2

- fix: add missing api.ts client library

### 2.0.1

- feat: Freya 2.0 - Modern Web Interface

### 2.0.0

- Update to version 1.1.6.1

### 0.3.6

- Add maintenance TODO comments to all main README sections

### 0.3.5

- Update interaction overview diagrams and add maintenance comments

### 0.3.4

- Update architecture to include all current components and tools

### 0.3.3

- Update architecture diagrams to include CLI interface

### 0.3.2

- Update README files to version 1.1.6

### 0.3.1

- Update to version 1.1.6

### 0.3.0

- Recreate French README.fr.md

### 0.2.6

- Consolidate README, add autopilot command

### 0.2.5

- 1.1.1, Hud Fix

### 0.2.4

- Fix async handling in TUI artifacts tree reload and update documentation

### 0.2.3

- 1.1 old Ui

### 0.2.2

- Add versioning and patch notes to French README

### 0.2.1

- Bump version to 1.1.0 and add patch notes section

### 0.2.0

- Add CaskaydiaCove Nerd Font and enhance TUI with clipboard, bench, and artifact management

### 0.1.2

- Ajout de badges pour les modèles LLM supportés

### 0.1.1

- Ajout de la version anglaise du README avec boutons de langue

### 0.1.0

- Refonte du schéma d'architecture avec un ASCII propre et bien aligné

### 0.0.3

- Ajout de la section Architecture avec arborescence du projet

### 0.0.2

- Mise à jour du README et améliorations générales

### 0.0.1

- Initial release: BMAD multi-agent orchestrator, TUI, CLI, agents, benchmarks

### 0.0.0 (Initial Release)

## Development Updates (Post-v2.5.5)

📋 **Development updates are now integrated in the interactive mindmap**

👉 **[View Development Updates in Mindmap](architecture/architecture_documentation.html)**

Post-v2.5.5 development updates and features are now available in the interactive mindmap within the HTML documentation file.

---

#### Major Features

- **CyberAgent AI Security Analyst** - Transform Cyber Watch into an intelligent security operations center with AI-powered threat analysis, daily briefings, and remediation suggestions
- **Best Agent Mode** - Automatic model selection based on benchmark performance with configurable thresholds and style preferences
- **External Benchmarks Integration** - Pre-integrated support for MMLU, HellaSwag, TruthfulQA, GSM8K, HumanEval, MBPP, ARC-Challenge, MT-Bench, WinoGrande
- **New Agent Roles** - Security Expert, DevOps Engineer, UX Designer, Data Scientist added to the BMAD pipeline

#### v2.5.0 - v2.5.4 Changes (since v2.2)

- **Research Mode (v2.5.0)** - Assisted & Autonomous internet research with market analysis and BMAD brief generation
- **Exchange Mode (v2.5.1)** - Two AI models autonomous discussion with configurable iterations
- **Conversation Management (v2.5.2)** - Export to JSON, shareable links, conversation history sidebar
- **Header Notifications (v2.5.3)** - Bell icon with real-time alerts, search palette (Ctrl+K)
- **File Browser Folder Import (v2.5.4)** - Import entire directories for BMAD with progress tracking
- **Settings Fusion (v2.5.4)** - Providers & API Keys merged into single tab, removed duplicate routing section

#### Architecture Improvements

- **Agent Intelligence Profiles** - Configurable temperature, max tokens, and capabilities per agent
- **Batch CVE Analysis** - Select and analyze multiple vulnerabilities simultaneously
- **Enhanced Multi-Agent Mode** - Thinking state indicators, collapsible responses, improved synthesis
- **Conversational Benchmarks** - MT-Bench and Chatbot Arena support for dialogue evaluation

#### UI/UX Enhancements

- **CyberAgent Panel** - Slide-in panel with chat interface, quick prompts, and analysis modes
- **Best Agent Settings** - Visual configuration with style preference cards
- **Agent Role Cards** - Emoji icons and descriptions for all 11 agent roles
- **External Benchmark Browser** - Visual list with integration status and metrics

#### Bug Fixes

- Fixed Multi-Agent mode not displaying individual agent responses
- Fixed conversation persistence across tab switches
- Fixed benchmark progress exceeding 100%
- Removed unused imports causing TypeScript errors

---

### v2.5.0 (2026-01-27)

#### Features

- Research modes with assisted and autonomous internet research
- Chat Exchange mode for AI model discussions
- UX improvements across the interface

---

### v2.4.2 (2026-01-27)

#### Features

- Research mode implementation
- UX improvements and data persistence enhancements

---

### v2.4.1 (2026-01-27)

#### Features

- UX improvements and persistence fixes

---

### v2.4.0 (2026-01-27)

#### Features

- Multi-Agent Chat improvements
- Autonomy Mode
- File deletion fixes

---

### v2.3.5 (2026-01-27)

#### Features

- Major UX Improvements
- Enhanced header and status bar
- Improved file navigation

---

### v2.3.2 (2026-01-27)

#### Features

- Bug fixes and code-splitting improvements
- UX enhancements

---

### v2.3.1 (2026-01-27)

#### Features

- Global Settings enhancements
- Hybrid Routing UI improvements
- Provider fixes

---

### v2.3.0 (2026-01-27)

#### Features

- Major UX improvements across all components

---

### v2.2.0 (2026-01-26)

#### Features

- Hybrid Routing System with multi-provider support
- Providers Dashboard in Settings
- Local Runtime Detection (Ollama, LM Studio, KoboldCpp)
- Continuous Mode for benchmarks (Fast → Standard → Advanced)

---

### v2.1.0 (2026-01-26)

#### New Features

- **Hybrid Routing** : Intelligent local/remote LLM routing with multi-provider support
- **Multi-Provider Support** : HuggingFace, Together AI, Groq integration with fallback chain
- **Local Runtime Detection** : Auto-detect Ollama, LM Studio, KoboldCpp, oobabooga
- **Consumption Prediction** : ML-based token and cost estimation
- **Health Monitoring** : Real-time provider health tracking with automatic failover
- **Free Web Search** : DuckDuckGo and SearXNG integration (no API key required)
- **Enhanced Cyber Watch** : 8+ security sources (NVD, Exploit-DB, GitHub Security, PacketStorm)
- **Repository Integration** : GitHub/GitLab API configuration for BMAD repo access
- **Live Theme System** : Real-time theme switching (Dark, Light, Midnight)
- **Editable Paths** : Full path configuration in Settings
- **Auto-refresh Toggle** : Visible timestamps and configurable refresh for Watch
- **JSON Export** : Export filtered vulnerabilities as JSON

<details>
<summary>🏗️ Hybrid Routing Architecture</summary>

```
┌─────────────────────────────────────────────────────────────────────┐
│                     HYBRID ROUTING v2.1                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      ROUTING DECISION                          │  │
│  │                                                                 │  │
│  │  1. Check local availability (Ollama/Llama.cpp)               │  │
│  │  2. If local_score >= MIN_THRESHOLD → Use local               │  │
│  │  3. Else evaluate remote providers:                            │  │
│  │     - Check health status                                      │  │
│  │     - Check quota availability                                 │  │
│  │     - Compare scores: remote > local * PERCENT_THRESHOLD?      │  │
│  │  4. Fallback chain: Groq → HF → Together → Local              │  │
│  │                                                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │   LOCAL        │  │   REMOTE       │  │   FALLBACK     │       │
│  │                │  │                │  │                │       │
│  │  • Ollama      │  │  • Groq (1)    │  │  Automatic     │       │
│  │  • LM Studio   │  │  • HF (2)      │  │  failover      │       │
│  │  • KoboldCpp   │  │  • Together(3) │  │  with health   │       │
│  │  • oobabooga   │  │                │  │  monitoring    │       │
│  │  • llama.cpp   │  │  Priority →    │  │                │       │
│  │                │  │                │  │                │       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

</details>

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

### v2.5.5 (2026-01-27)

- **feat(autonomous)**: Full automation from Research to BMAD pipeline
- **fix(chat)**: Use useRef for reliable autonomous mode stop detection
- **fix(chat)**: Real-time logging for Research & Autonomous modes + conversation persistence
- **feat(v2.5.5)**: Enhanced benchmarking with new roles + External Benchmarks UI
- **fix(launcher)**: Windows npm compatibility + Update Only option
- **fix(chat)**: Corrections majeures Chat, Research et Exchange modes
- **feat(v2.5.5)**: Add One-Click Launcher for update and launch
- **fix(v2.5.5)**: Corrections bugs critiques - Chat, Exchange, Research, Settings
- **feat(bmad)**: Major pipeline improvements with real-time logging and code generation
- **feat(bmad)**: Add Resume functionality, TestRunner agent, and real-time logging
- **fix(bmad)**: Critical pipeline fixes for code generation and validation
- **fix(bmad)**: Fix story generation and Dev agent fallbacks
- **feat(bmad)**: Infinite validation loop until app works
- **feat(bmad)**: Visual feedback for validation cycles
- **fix(bench+bmad)**: Multiple critical fixes

---

## Previous Updates Log

📋 **Previous updates log is now integrated in the interactive mindmap**

👉 **[View Previous Updates Log in Mindmap](architecture/architecture_documentation.html)**

The git commit history and previous updates are now available in the interactive mindmap within the HTML documentation file.

---

### 2026-01-27

- 572e172 feat(bmad): Visual feedback for validation cycles
- 826d304 feat(bmad): Infinite validation loop until app works
- a27804f fix(bmad): Fix story generation and Dev agent fallbacks
- a291ef9 fix(bmad): Critical pipeline fixes for code generation and validation
- 5d60987 feat(bmad): Add Resume functionality, TestRunner agent, and real-time logging
- a7f8605 feat(bmad): Major pipeline improvements with real-time logging and code generation
- 8222412 fix(bench+bmad): Multiple critical fixes
- c77a556 feat(autonomous): Full automation from Research to BMAD pipeline
- 17384a8 fix(chat): Use useRef for reliable autonomous mode stop detection
- 2f3ef08 fix(chat): Real-time logging for Research & Autonomous modes + conversation persistence
- 92167ec feat(v2.5.5): Enhanced benchmarking with new roles + External Benchmarks UI
- beddd64 fix(launcher): Windows npm compatibility + Update Only option
- 094bb6c fix(chat): Corrections majeures Chat, Research et Exchange modes
- 6fa8603 feat(v2.5.5): Add One-Click Launcher for update and launch
- d7056c4 fix(v2.5.5): Corrections bugs critiques - Chat, Exchange, Research, Settings
- aa449c9 feat: Freya v2.5.5 - CyberAgent, Best Agent, External Benchmarks
- 59e299b feat: Freya v2.5 - Research modes, Chat Exchange, UX improvements
- 1b3b0a7 feat: Freya v2.4.2 - Research mode, UX improvements, data persistence
- dda4e14 feat: Freya v2.4.1 - UX improvements and persistence
- 32d6519 feat: Freya v2.4 - Multi-Agent Chat improvements, Autonomy Mode, File deletion fixes
- faf9c24 fix: Files navigation back arrow reset file selection
- d50f460 feat: Freya 2.3.5 - Major UX Improvements
- 06da6c2 fix: Freya 2.3.2 - Bug fixes, code-splitting, UX improvements
- 820d776 feat: Freya 2.3.1 - Global Settings, Hybrid Routing UI, Provider Fixes
- 1af49c9 feat: Freya 2.3.0 - Major UX improvements
- f918fb1 fix: SPA routing - serve index.html for all non-API routes
- a219c15 fix: Remove unused TypeScript imports causing build errors
- 28ca562 feat: Freya 2.2 - Hybrid Routing, Providers Dashboard, UI Fixes
- 4077c58 fix: BenchPage continuous mode auto-advance, time estimation, and ChatPage web search/file attachments
- 1ef7d43 feat: Hybrid Routing System v2.1 - Local/Remote LLM routing with multi-provider support
- 815486f feat: Enhanced BenchPage and BMAD with v2.1 features
- df3c916 docs: Update to version 2.1 with comprehensive architecture documentation
- 5ac9155 feat: Major improvements - Web search, Cyber Watch, Settings
- 81b341e fix: ensure static files are served in both debug and production modes
- 31a489d fix: add WebSocket endpoint route before static files mount
- a968cf0 fix: add missing api.ts client library

### 2026-01-26

- c7cda19 feat: Freya 2.0 - Modern Web Interface

---

### 2026-01-27 Updates

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
