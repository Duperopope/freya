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
- [🔀 Hybrid LLM Routing](#-hybrid-llm-routing)
- [📊 Enhanced Benchmarking](#-enhanced-benchmarking)
- [🛡️ Cyber Security Features](#-cyber-security-features)
- [🌐 Web Interface Improvements](#-web-interface-improvements)
- [📦 Technical Architecture](#-technical-architecture)
- [🛠️ Installation & Setup](#-installation--setup)

---

# Freya v2.1 - Hybrid Routing System

**Commit:** a52a866
**Date:** Local/Remote LLM routing with multi-provider support
**Description:** Advanced hybrid routing and comprehensive benchmarking enhancements

## Overview

### 🔀 Hybrid Routing Revolution

**Problem Solved**: Implemented intelligent routing between local and remote LLM providers, enabling seamless switching based on task requirements, cost optimization, and performance needs.

**Context**: Users needed the flexibility to leverage both local models (privacy, cost-effective) and remote APIs (advanced capabilities, specialized models) without manual intervention.

**The Solution**: Multi-provider routing system with intelligent decision-making based on model capabilities, cost, and user preferences.

### 🎯 Key Achievements

**🚀 Multi-Provider Support**

- **Local Models**: Ollama integration with Llama, Mistral, and other open-source models
- **Remote APIs**: OpenAI GPT integration with automatic API key management
- **Smart Routing**: Automatic model selection based on task complexity and requirements
- **Fallback System**: Graceful degradation when preferred models are unavailable

**📊 Enhanced Benchmarking Suite**

- **External Benchmarks**: Integration with industry-standard performance tests
- **Comparative Analysis**: Side-by-side model performance evaluation
- **Automated Testing**: Continuous benchmarking with historical tracking
- **Custom Metrics**: User-defined performance indicators

**🛡️ Cyber Security Integration**

- **AI-Powered Analysis**: Automated threat detection in code and communications
- **Real-time Monitoring**: Continuous security assessment during operations
- **Compliance Checking**: Security best practice validation
- **Incident Response**: Automated security incident handling and reporting

### 🔧 Technical Implementation

The hybrid routing system includes:

1. **Router Engine**: Intelligent decision-making algorithm for model selection
2. **Provider Abstraction**: Unified interface for different LLM providers
3. **Cost Optimization**: Automatic selection of most cost-effective options
4. **Quality Assurance**: Performance validation before routing decisions
5. **Monitoring Integration**: Real-time metrics and routing analytics

```bash
# Configure hybrid routing
freya config routing --hybrid --providers ollama,openai
```

## Usage

```bash
# Use hybrid routing for optimal performance
freya chat --hybrid

# Run comprehensive benchmarks
freya bench --external --compare-all

# Enable cyber security monitoring
freya watch --security --real-time
```

---

## 🤖 Core Features

- **Hybrid Routing**: Intelligent local/remote LLM selection
- **Multi-Provider Support**: Ollama + OpenAI + future providers
- **Enhanced Benchmarking**: External benchmark integration
- **Cyber Security**: AI-powered threat analysis
- **Web Interface**: Improved React-based UI
- **Real-time Updates**: WebSocket-powered live updates

---

## 🔀 Hybrid LLM Routing

### Routing Strategies

- **Cost-Optimized**: Automatic selection of most economical options
- **Performance-Based**: Choose fastest/most capable models for complex tasks
- **Privacy-First**: Prefer local models for sensitive content
- **Fallback Chains**: Multiple backup options when primary models fail

### Supported Providers

- **Ollama**: Local models (Llama 2/3, Mistral, CodeLlama, etc.)
- **OpenAI**: GPT-4, GPT-3.5-turbo, specialized models
- **Future**: Anthropic Claude, Google Gemini, and other providers

---

## 📊 Enhanced Benchmarking

### Benchmark Categories

- **Performance Tests**: Speed, throughput, and latency measurements
- **Quality Assessment**: Output accuracy and relevance scoring
- **Resource Usage**: CPU, memory, and power consumption analysis
- **External Benchmarks**: Integration with GLUE, MMLU, and other standards

### Automated Testing

- **Continuous Monitoring**: Regular performance validation
- **Historical Tracking**: Performance trends over time
- **Comparative Analysis**: Model-to-model performance comparisons
- **Custom Scenarios**: User-defined test cases and workloads

---

## 🛡️ Cyber Security Features

### Security Capabilities

- **Code Analysis**: Automated vulnerability detection in generated code
- **Communication Monitoring**: Security assessment of chat interactions
- **Threat Detection**: AI-powered identification of malicious patterns
- **Compliance Validation**: Security best practice enforcement

### Real-time Protection

- **Live Scanning**: Continuous monitoring during operations
- **Automated Response**: Immediate actions for detected threats
- **Audit Logging**: Comprehensive security event tracking
- **User Alerts**: Real-time notifications for security events

---

## 🌐 Web Interface Improvements

### Enhanced Pages

- **Chat Page**: Improved multi-agent conversation interface
- **Bench Page**: Advanced benchmarking visualization and controls
- **BMAD Studio**: Enhanced pipeline development tools
- **Settings Page**: Comprehensive routing and provider configuration
- **Security Dashboard**: Real-time threat monitoring and alerts

### User Experience

- **Responsive Design**: Optimized for all screen sizes
- **Dark/Light Themes**: User preference-based theming
- **Accessibility**: WCAG compliance and screen reader support
- **Performance**: Optimized loading and interaction speeds

---

## 📦 Technical Architecture

- **Routing Engine**: Intelligent provider selection and load balancing
- **Provider SDKs**: Unified interfaces for different LLM services
- **Benchmark Framework**: Extensible testing and measurement system
- **Security Module**: AI-powered threat detection and response
- **WebSocket Infrastructure**: Real-time communication and updates

---

## 🛠️ Installation & Setup

```bash
# Install with all providers
pip install freya[all]

# Configure providers
freya config providers --ollama-url http://localhost:11434
freya config providers --openai-key your-api-key

# Start with hybrid routing
freya serve --routing hybrid
```

### Configuration

```json
{
  "routing": {
    "strategy": "hybrid",
    "providers": {
      "ollama": {
        "enabled": true,
        "models": ["llama2", "mistral"]
      },
      "openai": {
        "enabled": true,
        "models": ["gpt-4", "gpt-3.5-turbo"]
      }
    },
    "rules": {
      "cost_optimization": true,
      "privacy_first": false,
      "performance_priority": "balanced"
    }
  }
}
```

---

## 📚 Documentation

- [Routing Configuration Guide](../docs/routing.md)
- [Benchmarking Manual](../docs/benchmarking.md)
- [Security Features](../docs/security.md)
- [API Reference](../docs/api.md)

---

## 🤝 Contributing

Contributions welcome! Focus areas for v2.1+:

- Additional LLM provider integrations
- Enhanced routing algorithms
- New benchmark categories
- Security feature expansions

---

## 📄 License

MIT License - See [LICENSE](../LICENSE) file for details.</content>
<parameter name="filePath">h:\Code\Freya2\versions\61-README-v2.1.md