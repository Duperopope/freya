# Freya Modules

## Overview

Freya is organized into several key modules that work together to provide a comprehensive AI orchestration platform.

## Core Modules

### Agent System

- **Analyst**: Requirements analysis and stakeholder identification
- **Product Manager**: Product requirements and feature planning
- **Architect**: Technical design and system architecture
- **Product Owner**: Epic breakdown and prioritization
- **Scrum Master**: User stories and sprint planning
- **Developer**: Code implementation and quality assurance
- **QA**: Testing and validation

### Tool Integrations

- **WebSearch**: DuckDuckGo, SearXNG, Wikipedia integration
- **WebWatch**: Security feed aggregation (CISA, CERT-FR, NVD, etc.)
- **Shell**: Secure command execution
- **Clipboard**: System clipboard operations
- **Redact**: Content protection and data masking

### LLM Providers

- **Ollama**: Primary local LLM runtime
- **Llama.cpp**: Alternative local runtime
- **Hybrid Router**: Intelligent routing between local and remote providers

### Benchmarking System

- **Role-based Scoring**: Performance evaluation per agent role
- **Billboard**: Best model recommendations
- **Multi-trial Testing**: Comprehensive evaluation protocols

## Module Architecture

```
freya/
├── agents/          # BMAD workflow agents
├── tools/           # Integrated tools
├── api/             # FastAPI endpoints
├── config/          # Configuration management
├── router/          # LLM routing logic
└── web/             # React frontend
```

## Dependencies

- **Backend**: FastAPI, Pydantic, httpx, WebSockets
- **Frontend**: React 18, TypeScript, Zustand, TanStack Query
- **LLM**: Ollama, Llama.cpp integration
- **Tools**: Various web APIs and system integrations
