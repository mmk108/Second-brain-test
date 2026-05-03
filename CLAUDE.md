# CLAUDE.md — Second Brain AI Agent

This file is read by Claude Code at the start of every session. **Read it fully before writing any code.**

---

## What This Project Is

Second Brain is a personal AI intelligence system that ingests the user's documents (PDF, DOCX, TXT), answers questions grounded in them via RAG, and builds a persistent memory of who the user is across sessions. It is a single-user system built on Claude (Anthropic), LangGraph, Qdrant, PostgreSQL, and Chainlit.

Full product requirements, use cases, user stories, and architecture: **[PRODUCT_SPEC.md](./PRODUCT_SPEC.md)** — this is the source of truth. Read it before implementing any feature.

---

## Current Build State

### What Is Built

| Module | File | Status |
|---|---|---|
| Config | `config/settings.py` | Built — has known bugs (see below) |
| LLM wrapper | `models/claude.py` | Built — clean |
| DB schema | `db/schema.sql` | Built — clean |
| DB client | `db/client.py` | Built — has known bug (see below) |
| Ingestion | `ingestion/loaders.py` | Built — clean |
| Ingestion | `ingestion/chunker.py` | Built — clean |
| Ingestion | `ingestion/embedder.py` | Built — has known bugs (see below) |
| Memory | `memory/conversation.py` | Built — has known bug (see below) |
| Memory | `memory/user_profile.py` | Built — has known bug (see below) |
| Agent | `agents/retrieval_tool.py` | Built — clean |
| Agent | `agents/memory_tool.py` | Built — clean |
| Agent | `agents/graph.py` | Built — clean |
| UI | `interface/app.py` | Built — has known bugs (see below) |
| Observability | `observability/langsmith.py` | Built — clean |
| Tests | `tests/` | Stubs only — no fixtures |

### What Is Not Yet Built

- Chainlit basic authentication wired up (spec: `BASIC_AUTH_USERNAME` / `BASIC_AUTH_PASSWORD`)
- Async-safe DB layer (current `db/client.py` is synchronous psycopg2)
- Document deletion
- Full test coverage (unit + integration)

---

## Known Bugs — Fix These First

**Do not add new features until these are resolved.** Each bug is a blocker.

### BUG-01 — `config/settings.py` crashes at import if env vars are missing
`os.environ["ANTHROPIC_API_KEY"]` and `os.environ["DATABASE_URL"]` raise `KeyError` at import time.
This means every test and every module that imports from `config` crashes without a populated `.env`.
**Fix:** Change to `os.getenv("KEY", "")` and add a `validate_required()` function called at app startup instead.

### BUG-02 — `ingestion/embedder.py` requires `OPENAI_API_KEY` but it is nowhere defined
`OpenAIEmbeddings` reads `OPENAI_API_KEY` from the environment, but this key is not in `config/settings.py` or `.env.example`.
**Fix:** Add `OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")` to `settings.py`; pass it explicitly to `OpenAIEmbeddings(api_key=OPENAI_API_KEY)`.

### BUG-03 — `memory/user_profile.py` JSON parsing fails silently
`json.loads(raw)` raises `JSONDecodeError` when Claude wraps its output in markdown fences (` ```json ... ``` `), which it does by default. The bare `except` swallows the error and returns 0 facts — memory extraction silently does nothing every session.
**Fix:** Strip markdown fences before parsing:
```python
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
raw = raw.strip()
```

### BUG-04 — `interface/app.py` history handling is wrong
The code saves the user message to DB, loads history (which now includes it), then strips `history[:-1]` before passing to the agent (which re-adds it as a HumanMessage). Any change to message ordering breaks this silently.
**Fix:** Load history BEFORE saving the new user message:
```python
history = load_history(conv_id, limit=20)   # load first
save_message(conv_id, "user", message.content)  # then save
answer = await run_agent(message.content, history)  # pass history directly
```

### BUG-05 — `db/client.py` synchronous DB calls block the async event loop
All DB calls in `memory/` use synchronous psycopg2. Chainlit is async. Blocking sync DB calls inside `async def` handlers stall the event loop under any concurrent usage.
**Fix (MVP approach):** Wrap sync calls with `asyncio.get_event_loop().run_in_executor(None, func, *args)` in the Chainlit handlers. Full fix is migrating `db/client.py` to `asyncpg`.

### BUG-06 — `memory/conversation.py` uses inline `__import__`
`__import__("json").dumps(...)` is an antipattern. It works but is unreadable.
**Fix:** Add `import json` at the top of the file and use `json.dumps(...)`.

### BUG-07 — Unused imports
- `interface/app.py` imports `tempfile` but never uses it
- `ingestion/embedder.py` imports `datetime` but never uses it

---

## Setup

### Prerequisites
- Python 3.11
- Docker Desktop running
- API keys: Anthropic (required), OpenAI (required for embeddings), LangSmith (free tier, required for tracing)

### First-time setup
```bash
# 1. Copy env template and fill in your keys
cp .env.example .env
# Open .env — set ANTHROPIC_API_KEY, OPENAI_API_KEY, LANGCHAIN_API_KEY,
#              BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD

# 2. Start local services (Qdrant + PostgreSQL)
docker compose up -d

# 3. Verify services are healthy
curl http://localhost:6333/healthz
docker exec second_brain_postgres pg_isready -U brain_user -d second_brain

# 4. Create Python virtual environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the app
```bash
source .venv/bin/activate
chainlit run interface/app.py
# UI available at http://localhost:8000
# Login with BASIC_AUTH_USERNAME / BASIC_AUTH_PASSWORD from .env
```

### Run tests
```bash
source .venv/bin/activate
pytest tests/ -v
```

### Docker operations
```bash
docker compose up -d          # start Qdrant + PostgreSQL
docker compose down           # stop services
docker compose logs -f        # stream logs
docker compose down -v        # wipe all data (destructive)
```

---

## Required Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Claude LLM calls |
| `OPENAI_API_KEY` | Yes | — | text-embedding-3-small embeddings |
| `LANGCHAIN_API_KEY` | Yes | — | LangSmith tracing |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `BASIC_AUTH_USERNAME` | Yes | `admin` | Chainlit login username |
| `BASIC_AUTH_PASSWORD` | Yes | — | Chainlit login password |
| `QDRANT_URL` | No | `http://localhost:6333` | Qdrant REST endpoint |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-6` | Override Claude model |
| `QDRANT_COLLECTION` | No | `second_brain` | Qdrant collection name |
| `CHUNK_SIZE` | No | `1000` | Tokens per ingestion chunk |
| `CHUNK_OVERLAP` | No | `200` | Overlap between adjacent chunks |

---

## Architecture Summary

```
Browser
  └── Chainlit UI (http://localhost:8000) — basic auth required
        │
        ├── on file upload
        │     └── ingestion pipeline (bypasses agent)
        │           loaders.py → chunker.py → embedder.py
        │           → Qdrant (vectors) + PostgreSQL (metadata)
        │
        ├── on chat message
        │     └── LangGraph agent (agents/graph.py)
        │           → retrieve_documents tool → Qdrant semantic search (k=5)
        │           → read_user_profile tool  → PostgreSQL user_profile table
        │           → update_user_profile tool → PostgreSQL upsert
        │           → Claude generates grounded response
        │           → save turn to PostgreSQL messages table
        │
        └── on session end
              └── memory extraction
                    → load session transcript from PostgreSQL
                    → Claude extracts facts as JSON
                    → upsert to user_profile table
                    → injected into system prompt on next session

All LLM calls → LangSmith (100% trace coverage required)
```

**Cross-session memory = extracted profile facts, not raw history replay.**
History from old sessions is never reloaded. At session end, Claude extracts structured facts
(name, preferences, goals, style) into `user_profile`. These are injected into the system
prompt at the start of every new session.

---

## Project Structure

```
├── agents/
│   ├── graph.py              # LangGraph agent — main chat entry point
│   ├── retrieval_tool.py     # @tool: semantic search in Qdrant (k=5)
│   └── memory_tool.py        # @tool: read/write user_profile table
├── config/
│   └── settings.py           # All env vars — always import from here, never os.environ directly
├── db/
│   ├── schema.sql            # PostgreSQL DDL — auto-applied on docker compose up
│   └── client.py             # Sync connection pool + query helpers
├── ingestion/
│   ├── loaders.py            # PyPDF / Docx2txt / TextLoader
│   ├── chunker.py            # RecursiveCharacterTextSplitter (1000 tokens, 200 overlap)
│   └── embedder.py           # OpenAI text-embedding-3-small → Qdrant; updates documents table
├── interface/
│   └── app.py                # Chainlit: on_chat_start, on_message, on_chat_end
├── memory/
│   ├── conversation.py       # save_message / load_history — PostgreSQL messages table
│   └── user_profile.py       # Post-session extraction + profile read/write
├── models/
│   └── claude.py             # get_llm() factory — use this everywhere; never instantiate directly
├── observability/
│   └── langsmith.py          # configure_tracing() — call once at app startup
├── tests/
│   ├── conftest.py           # Pytest fixtures — patches env vars, provides test files
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   └── test_memory.py
├── docker-compose.yml        # Qdrant + PostgreSQL local services
├── Dockerfile                # App container (python:3.11-slim, exposes 8000)
├── requirements.txt          # All Python dependencies with minimum versions
├── .env.example              # Template — copy to .env and fill in keys
└── PRODUCT_SPEC.md           # Full product requirements — source of truth
```

---

## Tech Stack

| Layer | Technology | Key detail |
|---|---|---|
| LLM | Claude via Anthropic API | `claude-sonnet-4-6` — used for Q&A, extraction, correction |
| Embeddings | OpenAI `text-embedding-3-small` | 1536 dimensions; Qdrant collection must match |
| Orchestration | LangGraph `>=0.2` | Stateful agent graph: agent → tools → agent loop |
| UI | Chainlit `>=2.0` | Handles streaming, file upload, session lifecycle |
| Vector store | Qdrant (Docker) | Collection: `second_brain`; cosine distance |
| Database | PostgreSQL 16 (Docker) | 5 tables: documents, conversations, messages, user_profile, ingestion_jobs |
| Observability | LangSmith | `LANGCHAIN_TRACING_V2=true` — all LLM calls traced |
| Python | 3.11 | f-strings, `|` union types, `match` supported |

---

## Coding Conventions

- **No comments unless the WHY is non-obvious** — good names are documentation
- **Never use `os.environ` directly** outside `config/settings.py`
- **Never instantiate `ChatAnthropic` directly** — always use `get_llm()` from `models/claude.py`
- **All Chainlit handlers are async** — never make synchronous blocking calls inside them
- **Errors are user-visible** — surface failures as Chainlit messages, not silent swallows
- **LangSmith tracing always on** — `configure_tracing()` must be called before any LLM call
- **Ingestion bypasses the agent** — file uploads go directly to the ingestion pipeline
- **DB writes use `db/client.py` helpers** — `execute()`, `fetchone()`, `fetchall()`

---

## Implementation Order for New Features

1. **Fix all bugs listed above first** — verify with `pytest tests/ -v`
2. `docker compose up -d` → verify Qdrant and PostgreSQL are healthy
3. `chainlit run interface/app.py` → test the golden path:
   - Upload a small PDF → confirm chunk count in response
   - Ask a question about it → confirm answer cites the document
   - End session (close tab) → query `SELECT * FROM user_profile;` to verify extraction ran
4. Only then add new functionality

---

## PostgreSQL Tables Reference

| Table | Purpose | Key columns |
|---|---|---|
| `documents` | Every ingested file | `id`, `filename`, `file_type`, `status`, `chunk_count`, `error_message` |
| `conversations` | Each chat session | `id`, `started_at`, `ended_at`, `message_count` |
| `messages` | Every message turn | `conversation_id`, `role`, `content`, `token_count`, `langsmith_run_id` |
| `user_profile` | Extracted user facts | `category`, `key`, `value`, `confidence`, `source_conv_id` |
| `ingestion_jobs` | Async job queue (Phase 2) | `document_id`, `job_type`, `status`, `attempts` |

Useful queries:
```sql
SELECT * FROM user_profile;                           -- view all known facts
SELECT filename, status, error_message FROM documents; -- check ingestion state
SELECT count(*) FROM messages;                         -- conversation volume
SELECT SUM(token_count) FROM messages WHERE conversation_id = '<id>'; -- session cost
```
