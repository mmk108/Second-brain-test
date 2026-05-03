# Second Brain AI Agent

A personal AI intelligence system that ingests your documents, remembers your conversations, learns your thinking style, and answers questions grounded in your actual knowledge. Built on Claude (Anthropic), LangGraph, Qdrant, and Chainlit.

## Quick Start

```bash
# 1. Copy and fill in your API keys
cp .env.example .env
# Required: ANTHROPIC_API_KEY, OPENAI_API_KEY, LANGCHAIN_API_KEY,
#           BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD

# 2. Start local services (Qdrant + PostgreSQL)
docker compose up -d

# 3. Install dependencies
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4. Run the app
chainlit run interface/app.py
```

Open [http://localhost:8000](http://localhost:8000) — log in with your `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD`.

## Documentation

| Document | Purpose |
|---|---|
| [PRODUCT_SPEC.md](./PRODUCT_SPEC.md) | Full requirements, use cases, user stories, and architecture — **source of truth** |
| [CLAUDE.md](./CLAUDE.md) | Claude Code session guide — setup, known bugs, conventions, implementation order |

## Project Structure

```
├── agents/          # LangGraph agent, retrieval tool, memory tool
├── config/          # Environment variable loading
├── db/              # PostgreSQL schema and connection helpers
├── ingestion/       # Document loaders, chunker, embedder → Qdrant
├── interface/       # Chainlit web UI
├── memory/          # Conversation history and user profile (PostgreSQL)
├── models/          # Claude (Anthropic) LLM wrapper
├── observability/   # LangSmith tracing config
├── tests/           # Pytest test suite
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Claude `claude-sonnet-4-6` (Anthropic API) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Orchestration | LangGraph |
| UI | Chainlit |
| Vector Store | Qdrant |
| Database | PostgreSQL |
| Observability | LangSmith |

## Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```
