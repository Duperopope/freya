<p align="center">
  <img src="../web/public/freya-icon.svg" alt="Freya Logo" width="120" />
</p>

<h3 align="center">BMAD-aligned Multi-Agent Orchestrator for Local LLMs</h3>

<p align="center">
  <strong>Modern • Real-time • Privacy-First • Hybrid Routing</strong>
</p>

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

# Freya v2.0 - Modern Web Interface

**Commit:** 7f42d4b
**Date:** BREAKING: TUI → React Web App
**Description:** Complete architectural revolution from TUI to modern web application

## Overview

### 🌐 The Web Revolution

**Problem Solved**: Replaced the terminal-based TUI with a modern, responsive web interface that provides an intuitive user experience while maintaining all the power and functionality of the BMAD orchestrator.

**Context**: While the TUI provided excellent functionality for developers, it created barriers for non-technical users and limited the potential for rich, interactive experiences that modern web technologies could offer.

**The Solution**: Complete rewrite using React 18, TypeScript, and modern web technologies to create a comprehensive web application with six main pages.

### 🎯 Key Achievements

**🚀 Modern Technology Stack**

- React 18 with TypeScript for type safety and modern development
- Tailwind CSS for responsive, beautiful UI components
- FastAPI backend with WebSocket support for real-time communication
- Comprehensive REST API for all functionality

**📱 Six Complete Pages**

- **Chat**: Multi-agent conversations with real-time updates
- **Bench**: Performance benchmarking and testing suite
- **BMAD Studio**: Visual pipeline development and orchestration
- **Settings**: Global configuration and preferences
- **Files**: File management and document handling
- **Watch**: Real-time monitoring and system status

**⚡ Enhanced User Experience**

- Responsive design that works on all devices
- Real-time updates via WebSocket connections
- Intuitive navigation and user-friendly interfaces
- Rich visualizations and interactive components

### 🔧 Technical Implementation

The transition involved a complete architectural overhaul:

1. **Frontend Migration**: TUI components rewritten as React components
2. **Backend Enhancement**: FastAPI server with WebSocket endpoints
3. **API Development**: Comprehensive REST API for all operations
4. **Real-time Communication**: WebSocket integration for live updates
5. **State Management**: Modern React patterns for complex state handling

This version marks Freya's transition from a developer tool to a comprehensive platform accessible to all users while maintaining its technical excellence.

```bash
pip install freya[web]
freya serve
```

## Usage

```bash
# Start the web server
freya serve

# Access at http://localhost:8000
```

---

## 🤖 Core Features

- **BMAD Orchestration**: 7 specialized agents in coordinated pipelines
- **Hybrid Routing**: Intelligent local/remote LLM selection
- **Real-time Chat**: Multiple conversation modes
- **Web Interface**: Modern React-based UI
- **Benchmarking**: Comprehensive performance testing
- **Security**: AI-powered threat analysis

---

## 🧠 BMAD Multi-Agent Orchestration

The BMAD (Multi-Agent Decision) framework coordinates 7 specialized agents:

- **Project Manager**: Oversees project execution
- **Developer**: Handles code generation and implementation
- **QA Engineer**: Ensures quality and testing
- **DevOps**: Manages deployment and infrastructure
- **Security Analyst**: Performs security assessments
- **Researcher**: Conducts in-depth analysis
- **TestRunner**: Executes automated testing

---

## 🔀 Hybrid LLM Routing

Intelligent routing between:

- **Local Models**: Ollama-hosted models (Llama, Mistral, etc.)
- **Remote APIs**: OpenAI GPT models
- **Multi-provider**: Support for multiple LLM providers
- **Smart Selection**: Automatic model selection based on task requirements

---

## 💬 Real-Time Chat System

- **Multi-agent Conversations**: Simultaneous interactions with multiple agents
- **Autonomous Modes**: Self-executing research and development pipelines
- **Persistent Sessions**: Conversation history and context preservation
- **WebSocket Updates**: Real-time message delivery

---

## 🖥️ User Interfaces

- **Web Interface**: Primary interface with 6 comprehensive pages
- **TUI (Legacy)**: Still available via `freya[tui]` optional install
- **API Access**: REST and WebSocket APIs for integrations
- **CLI Tools**: Command-line utilities for automation

---

## 📊 Benchmarking Suite

- **Performance Testing**: External benchmark integration
- **Model Comparison**: Side-by-side LLM evaluation
- **Automated Testing**: Continuous performance monitoring
- **Custom Benchmarks**: User-defined test scenarios

---

## 🛡️ Cyber Security Monitoring

- **AI-Powered Analysis**: Automated threat detection
- **Real-time Monitoring**: Continuous security assessment
- **Compliance Checking**: Security best practice validation
- **Incident Response**: Automated security incident handling

---

## 🔬 Research & Autonomous Modes

- **Research Workflows**: Structured research methodologies
- **Autonomous Execution**: Self-running development pipelines
- **Collaborative Features**: Multi-user research capabilities
- **Advanced Analytics**: Research data visualization and insights

---

## 🌐 Web Interface

Six main application pages:

1. **Chat Page**: Multi-agent conversation interface
2. **Bench Page**: Benchmarking and performance testing
3. **BMAD Page**: Visual pipeline orchestration studio
4. **Settings Page**: Global configuration management
5. **Files Page**: Document and file management
6. **Watch Page**: Real-time system monitoring

---

## 📦 Technical Architecture

- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + WebSocket support
- **Database**: Efficient state management and persistence
- **APIs**: RESTful API with comprehensive endpoints
- **Real-time**: WebSocket communication infrastructure

---

## 🛠️ Installation & Setup

```bash
# Install with web interface
pip install freya[web]

# Start the web server
freya serve

# Access the application
# Open http://localhost:8000 in your browser
```

For detailed installation instructions, see the [installation guide](../docs/installation.md).

---

## 📚 Documentation

- [API Documentation](../docs/api.md)
- [Architecture Overview](../architecture/architecture_documentation.html)
- [Installation Guide](../docs/installation.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

---

## 🤝 Contributing

We welcome contributions! Please see our [contributing guidelines](../CONTRIBUTING.md) for details.

---

## 📄 License

MIT License - See [LICENSE](../LICENSE) file for details.</content>
<parameter name="filePath">h:\Code\Freya2\versions\60-README-v2.0.md