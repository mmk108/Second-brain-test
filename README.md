# Second Brain AI Agent

A personal Jarvis-style AI agent that ingests your documents, remembers your conversations, learns your thinking style, and proactively surfaces relevant knowledge. Built on Claude (Anthropic), LangGraph, and Qdrant.

## Quick Start

```bash
# 1. Copy and fill in your API keys
cp .env.example .env
nano .env

# 2. Start local services (Qdrant + PostgreSQL)
docker compose up -d

# 3. Install dependencies
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4. Run the app
chainlit run interface/app.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Project Structure

```
second-brain/
├── ingestion/          # Document loaders, chunker, embedder → Qdrant
├── memory/             # Conversation history and user profile (PostgreSQL)
├── agents/             # LangGraph agent, retrieval tool, memory tool
├── models/             # Claude (Anthropic) LLM wrapper
├── interface/          # Chainlit web UI
├── observability/      # LangSmith tracing config
├── db/                 # PostgreSQL schema and connection helpers
├── config/             # Settings loaded from environment variables
├── tests/              # Pytest test suite
├── docker-compose.yml  # Local Qdrant + PostgreSQL
├── Dockerfile          # App container
├── requirements.txt
└── .env.example
```

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Claude (Anthropic API) — `claude-sonnet-4-6` |
| Orchestration | LangGraph |
| UI | Chainlit |
| Vector Store | Qdrant |
| Database | PostgreSQL |
| Observability | LangSmith |

See [`instructions`](./instructions) for the full product spec, architecture, and roadmap.
