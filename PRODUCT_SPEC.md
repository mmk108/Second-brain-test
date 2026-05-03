# Second Brain — Product Specification

## 1. Project Objective

Second Brain is a personal AI intelligence system designed to act as an always-on knowledge companion. It ingests the user's documents, remembers every conversation, learns their thinking style and preferences, and answers questions grounded in their actual knowledge — not fabricated information.

The system is designed for a single user who works with large amounts of written material (research, reports, notes, reference documents) and wants to query, synthesise, and reason across that material through natural conversation. Over time it builds an accurate model of who the user is and how they think, making every session faster and more useful than the last.

The guiding principle is: **the system should feel like a second brain, not a search engine**. It does not just retrieve documents — it understands context, remembers history, and gets smarter about the user with every interaction.

---

## 2. What the System Needs to Do

### Core Capabilities

| # | Capability | Description |
|---|---|---|
| C-01 | Document ingestion | Accept PDF, DOCX, and TXT files; parse, chunk, embed, and index them for semantic search |
| C-02 | Conversational Q&A | Answer questions using retrieved document content, with full conversation context |
| C-03 | Persistent memory | Retain conversation history across sessions so the user never has to repeat themselves |
| C-04 | User profile learning | Extract and store facts about the user — preferences, goals, style — and apply them to every response |
| C-05 | Grounded responses | Cite source documents in answers; never invent information not present in the knowledge base |
| C-06 | Full observability | Trace every LLM call end-to-end in LangSmith for debugging, evaluation, and cost monitoring |
| C-07 | Secure local-first operation | All data stays on the user's own infrastructure during MVP; no third-party data storage beyond the LLM API |

### Planned Future Capabilities (Phase 2+)

| # | Capability | Phase |
|---|---|---|
| C-08 | URL and web page ingestion | 2 |
| C-09 | Voice input and output | 2 |
| C-10 | Active mid-conversation memory updates | 2 |
| C-11 | Communication style adaptation | 2 |
| C-12 | Video ingestion via transcription | 3 |
| C-13 | Proactive surfacing of relevant content | 3 |
| C-14 | Structured data ingestion (CSV, JSON) | 3 |

---

## 3. Use Cases

### UC-01 — Upload and Index a Document

**Actor:** User  
**Goal:** Make a document queryable by the system  
**Precondition:** User has a PDF, DOCX, or TXT file they want to reference in future conversations

**Flow:**
1. User uploads the file through the Chainlit chat interface
2. System stores the raw file to Azure Blob Storage (Phase 1: local disk)
3. System creates a `documents` record in PostgreSQL with status `processing`
4. System parses the file text using the appropriate loader
5. System splits the text into overlapping chunks
6. System generates embeddings for each chunk and stores them in Qdrant
7. System updates the `documents` record to `complete` with chunk count
8. User receives a confirmation message with the document ID

**Outcome:** The document is now part of the user's knowledge base and can be referenced in any future conversation.

---

### UC-02 — Ask a Question Grounded in Documents

**Actor:** User  
**Goal:** Get an accurate answer drawn from their uploaded documents  
**Precondition:** At least one document has been ingested

**Flow:**
1. User types a question in the chat interface
2. System retrieves the most recent conversation history from PostgreSQL
3. System performs a semantic search in Qdrant using the question as the query
4. System assembles a context window: system prompt + user profile + conversation history + retrieved chunks
5. Claude generates a response using the retrieved content as its grounding
6. Response is streamed back to the user in the Chainlit UI
7. Both the user message and assistant response are saved to PostgreSQL
8. The full LLM call is traced in LangSmith

**Outcome:** User receives an answer that draws directly from their documents, not from Claude's general training.

---

### UC-03 — Continue a Conversation Across Sessions

**Actor:** User  
**Goal:** Pick up where they left off without re-explaining context  
**Precondition:** User has had at least one previous conversation

**Flow:**
1. User opens the Chainlit UI in a new session
2. System creates a new `conversations` record in PostgreSQL
3. User references something from a previous session ("Like we discussed last time...")
4. System loads recent message history from PostgreSQL and injects it into context
5. Claude responds with awareness of the prior discussion
6. At session end, system runs a memory extraction pass over the full session

**Outcome:** Conversations feel continuous. The user does not need to re-establish context at the start of every session.

---

### UC-04 — System Learns the User's Profile

**Actor:** System (automated, post-session)  
**Goal:** Build and maintain an accurate model of the user's preferences and style  
**Precondition:** A conversation session has ended

**Flow:**
1. User ends a conversation (closes tab or session times out)
2. System runs Claude over the full session transcript with a fact-extraction prompt
3. Claude returns a structured list of facts: name, timezone, communication style, goals, etc.
4. System upserts each fact into the `user_profile` table (deduplicates by category + key)
5. On the next session, the extracted profile is injected into the system prompt

**Outcome:** The system becomes progressively more personalised. By the third or fourth session it knows the user's name, preferences, and how they like to be answered without being told.

---

### UC-05 — View Ingested Documents

**Actor:** User  
**Goal:** Know what is in their knowledge base  
**Precondition:** At least one document has been ingested

**Flow:**
1. User asks "What documents have you indexed?" or similar
2. The memory tool queries the `documents` table
3. System returns a list of filenames, types, chunk counts, and ingestion dates

**Outcome:** User has visibility into what the system knows about, and can identify gaps.

---

### UC-06 — Ingest a Web Page (Phase 2)

**Actor:** User  
**Goal:** Add online content to the knowledge base without downloading it manually  
**Precondition:** User has a URL they want to index

**Flow:**
1. User pastes a URL into the chat
2. System crawls the URL and extracts clean text (via Crawl4AI or Firecrawl)
3. Ingestion pipeline processes it identically to a file upload
4. Document record is created with `source_url` populated instead of `blob_path`

**Outcome:** Web content is queryable alongside uploaded documents without any manual file handling.

---

## 4. User Stories

### Document Ingestion

> **US-01** — As a knowledge worker, I want to upload PDF research papers so that I can ask questions across them without re-reading them every time I need a reference.

> **US-02** — As a user, I want to upload DOCX reports so that my work documents are part of my knowledge base alongside my research.

> **US-03** — As a user, I want to receive confirmation when a document has been successfully indexed so that I know I can start querying it.

> **US-04** — As a user, I want to see which documents are in my knowledge base so that I understand what the system knows and what is missing.

---

### Conversational Q&A

> **US-05** — As a user, I want to ask natural language questions about my documents so that I can get answers without manually searching through files.

> **US-06** — As a user, I want to ask follow-up questions that build on previous answers so that I can explore a topic in depth without losing thread.

> **US-07** — As a user, I want answers to cite the source document so that I can verify the information and find the original passage.

> **US-08** — As a user, I want the assistant to tell me when it does not have a relevant document rather than making up an answer so that I can trust what it says.

---

### Memory and Personalisation

> **US-09** — As a user, I want the system to remember my name and preferences so that I do not have to re-introduce myself at the start of every session.

> **US-10** — As a user, I want the system to remember decisions and conclusions from previous conversations so that I can reference them without re-explaining context.

> **US-11** — As a user, I want the system to adapt to my communication style so that responses feel natural and appropriately detailed for how I work.

> **US-12** — As a user, I want to be able to correct a stored fact about me so that the profile stays accurate as my circumstances change.

---

### Observability and Trust

> **US-13** — As a developer/owner, I want every LLM call traced in LangSmith so that I can see exactly what context was sent, what was retrieved, and what was returned.

> **US-14** — As a developer/owner, I want to see token counts per message so that I can monitor costs and optimise context window usage.

> **US-15** — As a developer/owner, I want ingestion errors surfaced clearly so that I know when a document failed to index and why.

---

### Future (Phase 2+)

> **US-16** — As a user, I want to paste a URL and have it indexed so that online content is available in my knowledge base without manual downloading.

> **US-17** — As a user, I want to speak my questions and hear the responses so that I can use the system hands-free while working.

> **US-18** — As a user, I want the system to surface a relevant document or insight unprompted when it detects I am working on a related topic.

---

## 5. Logical Architecture

### Conceptual Overview

The system is composed of five logical layers. Each layer has a single responsibility and communicates with adjacent layers through clean interfaces.

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERFACE LAYER                          │
│  Chainlit web UI — chat input, file upload, streamed responses  │
└────────────────────────────┬────────────────────────────────────┘
                             │  user messages + uploaded files
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                         │
│  LangGraph agent — decides what tools to call, in what order    │
│                                                                 │
│   ┌──────────────────┐  ┌───────────────┐  ┌────────────────┐  │
│   │  Retrieval Tool  │  │  Memory Tool  │  │ Ingestion Tool │  │
│   │  (search Qdrant) │  │ (read/write   │  │ (parse+embed   │  │
│   │                  │  │  user profile)│  │  new files)    │  │
│   └──────────────────┘  └───────────────┘  └────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │  structured prompts with context
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MODEL LAYER                             │
│          Claude (Anthropic API) — all reasoning and generation  │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────┐      ┌───────────────────────────────────┐
│   VECTOR STORE       │      │        RELATIONAL STORE           │
│   Qdrant             │      │        PostgreSQL                 │
│                      │      │                                   │
│   document chunks    │      │   conversations   messages        │
│   + embeddings       │      │   user_profile    documents       │
│   semantic search    │      │   ingestion_jobs                  │
└──────────────────────┘      └───────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INGESTION PIPELINE                         │
│   File / URL → loader → chunker → embedder → Qdrant + Postgres  │
└─────────────────────────────────────────────────────────────────┘

                    All LLM calls → LangSmith (traces)
```

---

### Data Flows

#### Flow 1 — Document Ingestion

```
User uploads file
       │
       ▼
Chainlit receives file element
       │
       ▼
ingestion/loaders.py
  → parse raw text (PyPDF / Docx2txt / TextLoader)
       │
       ▼
ingestion/chunker.py
  → RecursiveCharacterTextSplitter
  → 1000-token chunks with 200-token overlap
       │
       ▼
ingestion/embedder.py
  → generate vector embedding per chunk
  → write chunks to Qdrant collection
  → write document record to PostgreSQL (status: complete)
       │
       ▼
User sees confirmation message
```

---

#### Flow 2 — Chat (Question → Answer)

```
User sends message
       │
       ▼
interface/app.py (on_message)
  → save user message to PostgreSQL
  → load recent conversation history from PostgreSQL
       │
       ▼
agents/graph.py — LangGraph agent receives:
  [system prompt + user profile] + [history] + [user message]
       │
       ├──→ Claude decides to call retrieve_documents tool
       │         │
       │         ▼
       │    agents/retrieval_tool.py
       │      → semantic search Qdrant with user query
       │      → return top-k relevant chunks
       │
       ├──→ Claude decides to call read_user_profile tool
       │         │
       │         ▼
       │    memory/user_profile.py
       │      → fetch all facts from PostgreSQL user_profile table
       │
       ▼
Claude generates response grounded in retrieved chunks
       │
       ▼
interface/app.py
  → stream response to Chainlit UI
  → save assistant message to PostgreSQL
  → full call traced in LangSmith
```

---

#### Flow 3 — Post-Session Memory Extraction

```
User ends session (tab closed / session timeout)
       │
       ▼
interface/app.py (on_chat_end)
  → load full session transcript from PostgreSQL
       │
       ▼
memory/user_profile.py — extract_and_store()
  → send transcript to Claude with fact-extraction prompt
  → Claude returns JSON: [{category, key, value, confidence}]
       │
       ▼
PostgreSQL user_profile table
  → upsert each fact (ON CONFLICT category+key → update)
       │
       ▼
Next session: updated profile injected into system prompt
```

---

### State Held Per Session

| What | Where | Lifetime |
|---|---|---|
| Current conversation ID | Chainlit user session (in-memory) | Single browser session |
| Conversation history | PostgreSQL `messages` table | Permanent |
| User profile facts | PostgreSQL `user_profile` table | Permanent, updated each session |
| Document embeddings | Qdrant vector collection | Permanent |
| Document metadata | PostgreSQL `documents` table | Permanent |
| LLM traces | LangSmith | Permanent (per LangSmith retention policy) |

---

### Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| LLM | Claude (Anthropic API) throughout | Single model for all reasoning — simpler, more consistent |
| Orchestration | LangGraph | Stateful agent graph with explicit control flow; easy to extend with new tools |
| Vector store | Qdrant | Production-grade, runs locally in Docker with zero config |
| Relational store | PostgreSQL | Reliable, queryable, supports JSONB for flexible metadata |
| UI | Chainlit | Purpose-built for LLM chat; handles file upload and streaming out of the box |
| Observability | LangSmith | First-class LangChain integration; traces all LLM calls with zero instrumentation code |
| Deployment (MVP) | Local Docker on Mac mini | Zero cloud cost during development; identical code runs on Azure in Phase 3 |

---

### What the System Is Not

- It is not a general-purpose search engine — it only knows what the user has explicitly ingested
- It is not multi-user — the knowledge base, profile, and conversation history belong to one person
- It is not a real-time system — documents are indexed on upload, not continuously monitored
- It does not learn from Claude's general knowledge — all factual answers must be grounded in the user's own documents
