# Second Brain — Product Specification

---

## 1. Project Objective

Second Brain is a personal AI intelligence system designed to act as an always-on knowledge companion. It ingests the user's documents, remembers every conversation, learns their thinking style and preferences, and answers questions grounded in their actual knowledge — not fabricated information.

The system is designed for a single user who works with large amounts of written material (research, reports, notes, reference documents) and wants to query, synthesise, and reason across that material through natural conversation. Over time it builds an accurate model of who the user is and how they think, making every session faster and more useful than the last.

The guiding principle is: **the system should feel like a second brain, not a search engine**. It does not just retrieve documents — it understands context, remembers history, and gets smarter about the user with every interaction.

---

## 2. MVP Scope

This section defines exactly what is in and out of scope for the current build. Anything not listed under "In Scope" is deferred.

### In Scope — MVP

| # | Capability |
|---|---|
| S-01 | File upload and indexing — PDF, DOCX, TXT via the chat UI |
| S-02 | Conversational Q&A grounded in uploaded documents (RAG) |
| S-03 | Conversation history persisted within a session and carried forward via extracted profile |
| S-04 | Post-session memory extraction — key facts stored to user profile |
| S-05 | User profile injected into system prompt at session start |
| S-06 | User can correct a profile fact via chat |
| S-07 | User can ask what documents have been ingested |
| S-08 | Basic authentication on all UI routes (single user) |
| S-09 | Full LangSmith tracing on every LLM call |
| S-10 | Local Docker infrastructure — Qdrant + PostgreSQL on Mac mini |

### Out of Scope — MVP (Deferred to Phase 2+)

| # | Capability | Phase |
|---|---|---|
| D-01 | URL and web page ingestion | 2 |
| D-02 | Voice input and output | 2 |
| D-03 | Active mid-conversation memory updates by a background agent | 2 |
| D-04 | Communication style auto-adaptation without explicit user statement | 2 |
| D-05 | Video ingestion via transcription pipeline | 3 |
| D-06 | Proactive surfacing of content without user prompt | 3 |
| D-07 | Structured data ingestion (CSV, JSON) | 3 |
| D-08 | Azure cloud deployment | 3 |
| D-09 | Multi-user support | 3 |

---

## 3. What the System Needs to Do

### Core Capabilities

| # | Capability | Description |
|---|---|---|
| C-01 | Document ingestion | Accept PDF, DOCX, and TXT files; parse, chunk, embed, and index them for semantic search |
| C-02 | Conversational Q&A | Answer questions using retrieved document content, with full conversation context |
| C-03 | Persistent memory | Retain conversation history within a session; surface prior knowledge via user profile across sessions |
| C-04 | User profile learning | Extract and store facts about the user — preferences, goals, style — and apply them to every response |
| C-05 | Grounded responses | Cite source documents in answers; never invent information not present in the knowledge base |
| C-06 | Profile correction | Allow the user to correct inaccurate profile facts via natural language in chat |
| C-07 | Full observability | Trace every LLM call end-to-end in LangSmith for debugging, evaluation, and cost monitoring |
| C-08 | Secure access | Basic authentication required on all UI routes; credentials set via environment variables |

### Resolved Technical Decisions

| Decision | Resolution | Detail |
|---|---|---|
| Embedding model | OpenAI text-embedding-3-small | 1536-dimension vectors; requires `OPENAI_API_KEY`; ~$0.02 per million tokens |
| Vector dimensions | 1536 | Qdrant collection must be created with `vector_size=1536` and cosine distance |
| Retrieval chunk count | k = 5 | 5 chunks returned per semantic search query; no similarity score threshold applied for MVP |
| Similarity threshold | None (MVP) | All top-5 chunks returned regardless of score; scores logged to LangSmith for future tuning |
| Authentication | HTTP Basic Auth | Single username/password set via `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` env vars |
| LLM | claude-sonnet-4-6 | Anthropic API; used for all reasoning, Q&A, fact extraction, and profile correction |

---

## 4. Non-Functional Requirements

| ID | Requirement | Target | Notes |
|---|---|---|---|
| NFR-01 | Response latency (chat) | < 5 seconds p95 | Measured from user send to first token of response |
| NFR-02 | Ingestion throughput | 10+ documents concurrently | Requires async ingestion queue; not synchronous blocking |
| NFR-03 | Vector search relevance | > 85% on test set | Evaluated against a fixed set of known Q&A pairs |
| NFR-04 | System availability | > 99% uptime | Local Docker stack; Mac mini must not sleep |
| NFR-05 | Authentication | Required on all routes | Basic auth; no unauthenticated access to any UI route |
| NFR-06 | Data privacy | All data stays on-device | No document content sent to third parties except Anthropic API for inference and OpenAI API for embeddings |
| NFR-07 | Observability coverage | 100% of LLM calls traced | Every Anthropic API call must produce a LangSmith trace |
| NFR-08 | Cost per session | < $0.05 per session | Based on ~10 turns at claude-sonnet-4-6 pricing with 5 retrieved chunks per turn |
| NFR-09 | Maximum file size | 50 MB per file | Files exceeding this limit are rejected before processing |
| NFR-10 | Context window management | 20 most recent messages | Maximum history loaded per session to prevent context overflow |

---

## 5. Use Cases

### UC-01 — Upload and Index a Document

**Actor:** User
**Goal:** Make a document queryable by the system
**Precondition:** User is authenticated; file is PDF, DOCX, or TXT

**Happy Path:**
1. User uploads the file through the Chainlit chat interface
2. System creates a `documents` record in PostgreSQL with status `processing`
3. System parses the file text using the appropriate loader (PyPDF / Docx2txt / TextLoader)
4. System splits the text into overlapping chunks (1000 tokens, 200-token overlap)
5. System generates an embedding per chunk using OpenAI text-embedding-3-small
6. System writes all chunk vectors to Qdrant
7. System updates the `documents` record to status `complete` with chunk count
8. User sees: "Indexed **{filename}** — {n} chunks (ID: `{doc_id}`)"

**Outcome:** The document is searchable in any future conversation.

**Exception Flows:**

| Condition | System Behaviour |
|---|---|
| File exceeds 50MB | Reject before processing; respond: "File too large. Maximum size is 50MB." |
| Unsupported file type | Reject; respond: "Unsupported file type. Accepted: PDF, DOCX, TXT." |
| PDF has no extractable text (image-only / scanned) | Mark document `error`; respond: "Could not extract text from this PDF. It may be a scanned image without a text layer." |
| File is corrupt or unreadable | Mark document `error`; respond: "Failed to parse this file. Please check it opens correctly and try again." |
| Embedding fails mid-document | Remove any Qdrant entries already written for this document; mark status `error`; respond: "Indexing failed partway through. No partial data has been stored." |
| Qdrant is unreachable | Mark document `error` with message "Vector store unavailable"; respond with error; do not leave partial state |

---

### UC-02 — Ask a Question Grounded in Documents

**Actor:** User
**Goal:** Get an accurate answer drawn from their uploaded documents
**Precondition:** User is authenticated; at least one document has been ingested

**Happy Path:**
1. User types a question in the chat interface
2. System loads the current session's recent message history from PostgreSQL (up to 20 messages)
3. System performs a semantic search in Qdrant using the user's question (k=5 chunks)
4. System assembles the context window: system prompt + user profile + conversation history + retrieved chunks
5. Claude generates a response grounded in the retrieved content
6. Response is streamed back to the user in the Chainlit UI
7. Both the user message and assistant response are saved to PostgreSQL
8. The full LLM call — including retrieved chunks — is traced in LangSmith

**Outcome:** User receives an answer that draws directly from their documents, with source citations.

**Exception Flows:**

| Condition | System Behaviour |
|---|---|
| No documents ingested | Respond: "You haven't uploaded any documents yet. Upload a file to get started." Do not attempt retrieval. |
| No relevant chunks found (all scores below useful threshold) | Respond: "I don't have a document that covers this. Would you like to upload one?" Do not fabricate an answer. |
| Anthropic API timeout or error | Respond: "I couldn't reach the AI service. Please try again in a moment." Save the user message to DB regardless. |
| Qdrant unreachable | Respond: "I can't search your documents right now. Please check that services are running." |
| Context window would be exceeded | Truncate history to the most recent 10 messages; keep all retrieved chunks; never truncate the system prompt or user profile. |

---

### UC-03 — Continue a Conversation Across Sessions

**Actor:** User
**Goal:** Benefit from prior context without re-explaining themselves
**Precondition:** User is authenticated; at least one previous session has ended (triggering memory extraction)

**Clarification — how cross-session memory works:**
The system does NOT load raw message history from previous sessions. That would exhaust the context window. Instead, at the end of each session, Claude extracts key facts from the transcript and stores them as structured entries in the `user_profile` table. On the next session, this profile is injected into the system prompt. Cross-session awareness comes from this extracted profile — not from replaying old messages.

**Happy Path:**
1. User opens the Chainlit UI and authenticates
2. System creates a new `conversations` record and a fresh in-session history
3. System loads the `user_profile` table and injects all stored facts into the system prompt
4. User references something from a prior session ("Like we discussed last time...")
5. Claude responds with awareness of the extracted facts from that prior session
6. Current session messages accumulate in PostgreSQL under the new conversation ID
7. At session end, memory extraction runs over the current session's transcript

**Outcome:** The user experiences continuity without raw history replay. The profile grows richer after every session.

**Exception Flows:**

| Condition | System Behaviour |
|---|---|
| First-ever session — no profile exists | System prompt includes an empty profile section; Claude responds without personalisation; this is correct and expected |
| Previous session ended mid-way (browser crash) | Chainlit `on_chat_end` may not have fired; extraction is skipped for that session; session is recoverable from DB but not re-processed automatically; acceptable for MVP |
| User asks about something not captured in profile | Claude responds based on current context only; no attempt to retrieve old raw messages |

---

### UC-04 — System Learns the User's Profile

**Actor:** System (automated, triggered at session end)
**Goal:** Build and maintain an accurate model of the user's preferences, facts, and style
**Precondition:** A session has ended with at least one exchange

**Happy Path:**
1. Session ends (user closes tab, or Chainlit fires `on_chat_end`)
2. System loads the full session transcript from PostgreSQL
3. System sends the transcript to Claude with a structured extraction prompt
4. Claude returns a JSON array of facts: `[{category, key, value, confidence}]`
5. System upserts each fact into the `user_profile` table using `ON CONFLICT (category, key) DO UPDATE`
6. Extracted facts are available from the next session onward via system prompt injection

**Profile Fact Categories:**

| Category | Purpose | Example keys |
|---|---|---|
| `fact` | Objective facts about the user | `name`, `timezone`, `role`, `organisation` |
| `preference` | Stated preferences for how the system behaves | `response_length`, `format`, `language` |
| `style` | Communication and writing style observations | `communication_style`, `detail_level`, `tone` |
| `goal` | Current projects, objectives, or priorities | `current_project`, `deadline`, `learning_goal` |
| `relationship` | People, teams, or entities the user mentions | `manager`, `team`, `key_contact` |

**Exception Flows:**

| Condition | System Behaviour |
|---|---|
| Session had zero messages | Skip extraction silently; no LLM call made |
| Claude returns JSON wrapped in markdown fences | Strip fences before parsing; this is the expected Claude output format |
| Claude returns malformed or unparseable JSON | Log the failure; store zero facts; close the conversation normally; do not surface error to user |
| Extracted fact has confidence < 0.5 | Store it but flag it; low-confidence facts can be overridden by later explicit statements |
| Extraction LLM call fails (API error) | Log the error; close the conversation; skip extraction for this session |

---

### UC-05 — View Ingested Documents

**Actor:** User
**Goal:** Know what is in their knowledge base
**Precondition:** User is authenticated

**Happy Path:**
1. User asks "What documents have you indexed?" or similar
2. Agent queries the `documents` table in PostgreSQL
3. System returns a formatted list of all documents with: filename, file type, chunk count, ingestion date, status
4. Documents in `error` state are listed with their error reason

**Exception Flows:**

| Condition | System Behaviour |
|---|---|
| No documents ingested | Respond: "No documents have been indexed yet. Upload a PDF, DOCX, or TXT file to get started." |
| Mix of complete and errored documents | Show all; clearly mark errored ones with their reason |

---

### UC-06 — Ingest a Web Page *(Phase 2)*

**Actor:** User
**Goal:** Add online content to the knowledge base without downloading it manually
**Precondition:** User has a URL they want to index

**Happy Path:**
1. User pastes a URL into the chat
2. System crawls the URL and extracts clean text (via Crawl4AI or Firecrawl)
3. Ingestion pipeline processes the extracted text identically to a file upload
4. Document record is created with `source_url` populated instead of `blob_path`

**Outcome:** Web content is queryable alongside uploaded documents.

---

### UC-07 — Correct a Profile Fact

**Actor:** User
**Goal:** Fix an inaccurate fact the system has stored about them
**Precondition:** User is authenticated; at least one fact exists in `user_profile`

**Happy Path:**
1. User states a correction in natural language: "Actually my timezone is PST, not UTC" or "Forget that I prefer bullet points"
2. Agent recognises this as a profile correction intent
3. Agent calls the `update_user_profile` tool with the corrected `category`, `key`, and `value`
4. PostgreSQL `user_profile` row is upserted: same `category + key`, new `value`, `updated_at = NOW()`
5. Agent responds: "Got it — I've updated your [key] to [value]."
6. The corrected value takes effect for the remainder of the current session

**Outcome:** The user's profile stays accurate as their circumstances and preferences change.

**Exception Flows:**

| Condition | System Behaviour |
|---|---|
| The key being corrected does not exist yet | Agent creates it rather than returning an error; responds with the same confirmation |
| User says "forget everything about me" | Agent removes all rows from `user_profile`; responds: "Done — I've cleared your profile." |
| Correction is ambiguous (agent unsure of key) | Agent asks for clarification: "Which preference did you want to update — your response format, or something else?" |

---

## 6. User Stories

### Document Ingestion

> **US-01** — As a knowledge worker, I want to upload PDF research papers so that I can ask questions across them without re-reading them every time I need a reference.

**Acceptance Criteria:**
- Given a valid PDF ≤ 50MB, when uploaded, a "processing" acknowledgement appears immediately and completion confirmation arrives within 30 seconds
- Completion confirmation includes filename, document ID, and chunk count
- Given a password-protected or image-only PDF with no text layer, the system returns a plain-English error explaining why it failed
- Given a file exceeding 50MB, the system rejects it before processing begins and states the size limit
- After successful indexing, asking a question clearly related to the document's content returns an answer that cites that document

---

> **US-02** — As a user, I want to upload DOCX reports so that my work documents are part of my knowledge base alongside my research.

**Acceptance Criteria:**
- Given a valid DOCX ≤ 50MB, when uploaded, the full ingestion flow completes and produces the same confirmation format as a PDF upload
- Given a DOCX with minimal text content (mostly images or tables), the system extracts whatever text is available, confirms the chunk count, and does not fail silently
- Given a corrupt or unreadable DOCX, the system returns an error message and sets document status to `error`

---

> **US-03** — As a user, I want to receive confirmation when a document has been successfully indexed so that I know I can start querying it.

**Acceptance Criteria:**
- Confirmation message always includes: filename, document ID, chunk count, and file type
- Confirmation appears within 30 seconds for files under 10MB
- If indexing fails, the error message states a specific reason (not a generic "something went wrong")
- After confirmation, the document appears in the document list returned by UC-05
- No confirmation is sent until indexing is fully complete; a partial success is treated as a failure

---

> **US-04** — As a user, I want to see which documents are in my knowledge base so that I understand what the system knows and what is missing.

**Acceptance Criteria:**
- Asking "What documents do you have?" or equivalent natural language returns a formatted list
- Each entry shows: filename, file type, chunk count, ingestion date, and status
- Documents with `error` status appear in the list with their error reason
- If no documents have been ingested, the response is: "No documents have been indexed yet."
- The list reflects the current state of the `documents` table, not a cached or stale view

---

### Conversational Q&A

> **US-05** — As a user, I want to ask natural language questions about my documents so that I can get answers without manually searching through files.

**Acceptance Criteria:**
- Given at least one ingested document, when the user asks a question, the first token of the response arrives within 5 seconds (p95)
- Every answer that draws on document content includes at least one source citation identifying the filename
- Given a question with no relevant documents, the system states it has no relevant information rather than generating a general answer
- Answers are formatted appropriately for the question type (list vs. paragraph vs. step-by-step) based on the user's stored style preference if one exists
- The LangSmith trace for each response includes the full set of retrieved chunks used

---

> **US-06** — As a user, I want to ask follow-up questions that build on previous answers so that I can explore a topic in depth without losing thread.

**Acceptance Criteria:**
- Given a prior exchange in the current session, when the user asks a follow-up using pronouns ("it", "that", "those"), Claude correctly resolves the reference at least 9 times out of 10
- The system maintains context for at least the 20 most recent messages in the current session
- A follow-up question triggers a fresh Qdrant semantic search using the enriched context, not just the follow-up text in isolation
- Follow-up answers do not repeat the full context of the original answer; they build on it concisely

---

> **US-07** — As a user, I want answers to cite the source document so that I can verify the information and find the original passage.

**Acceptance Criteria:**
- Every response that uses document content includes "Source: [filename]" at the end of the relevant passage or at the end of the response
- If multiple documents contribute to a single response, all contributing documents are cited
- If a response is drawn entirely from Claude's general knowledge (not from documents), no source citation appears and the answer is prefaced with a note that no relevant document was found
- Source citations use the original filename as uploaded, not an internal document ID

---

> **US-08** — As a user, I want the assistant to tell me when it does not have a relevant document rather than making up an answer, so that I can trust what it says.

**Acceptance Criteria:**
- When retrieved chunks are not relevant to the question, the system responds: "I don't have a document that covers this. Would you like to upload one?"
- The system never presents information from Claude's training data as if it came from the user's documents
- When an answer is partially grounded in documents and partially inferred, the response clearly distinguishes what is from the document and what is the model's interpretation
- This honest-gap behaviour is consistent — it does not vary based on topic or question phrasing

---

### Memory and Personalisation

> **US-09** — As a user, I want the system to remember my name and preferences so that I do not have to re-introduce myself at the start of every session.

**Acceptance Criteria:**
- After a session in which the user states their name, all subsequent sessions address them by that name in the first response
- Stated preferences (e.g. "I prefer concise answers", "use bullet points") are extracted into `user_profile` and applied from the next session onward
- The user profile is injected into the system prompt at the start of every session before any user message is processed
- If the user has not stated a name, the system does not invent one or use a placeholder

---

> **US-10** — As a user, I want the system to remember decisions and conclusions from previous conversations so that I can reference them without re-explaining context.

**Acceptance Criteria:**
- Decisions and conclusions stated by the user during a session are extracted into `user_profile` with category `goal` or `fact` at session end
- In a subsequent session, when the user references a prior decision, Claude acknowledges it from the stored profile
- Each profile entry carries a `source_conv_id` linking it to the session it came from, making it auditable
- Profile entries are not deleted between sessions; they accumulate and are updated only when explicitly corrected or superseded

---

> **US-11** — As a user, I want the system to adapt to my communication style so that responses feel natural and appropriately detailed for how I work.

**Acceptance Criteria:**
- Communication style preferences (e.g. "bullet points", "detailed paragraphs", "step-by-step") are stored in `user_profile` under category `style`
- Once a style preference is stored, responses follow that style from the next session onward without the user having to re-state it
- Style is consistent across an entire response — the system does not switch format mid-answer
- If the user explicitly requests a different format for a specific response ("give me a summary this time"), the system honours that one-off request without overwriting the stored preference

---

> **US-12** — As a user, I want to be able to correct a stored fact about me so that the profile stays accurate as my circumstances change.

**Acceptance Criteria:**
- The user can correct a fact via natural language in chat without any special command syntax
- Corrections take effect within the same session — the updated profile is used for subsequent responses in that conversation
- The system confirms every correction with a specific acknowledgement: "Got it — I've updated your [key] to [value]."
- If the user asks to clear their entire profile ("forget everything about me"), all `user_profile` rows are deleted and the system confirms
- If the correction references a key that does not exist, the system creates it rather than returning an error

---

### Observability and Trust

> **US-13** — As a developer/owner, I want every LLM call traced in LangSmith so that I can see exactly what context was sent, what was retrieved, and what was returned.

**Acceptance Criteria:**
- Every call to the Anthropic API generates a trace in LangSmith with: model name, full input message list, full output, token counts (input + output), and latency
- Traces are tagged with the conversation ID so they can be filtered per session
- Retrieved chunks sent to the LLM are recorded in trace metadata (not just the final prompt)
- Zero LLM calls occur without a corresponding LangSmith trace — this is verified by setting `LANGCHAIN_TRACING_V2=true` before any call

---

> **US-14** — As a developer/owner, I want to see token counts per message so that I can monitor costs and optimise context window usage.

**Acceptance Criteria:**
- Each row in the `messages` table has a `token_count` column populated at write time
- LangSmith traces show input token count, output token count, and total per call
- A session-level query can be run to show total tokens consumed across all calls in that conversation: `SELECT SUM(token_count) FROM messages WHERE conversation_id = '...'`
- Token counts are recorded even when the LLM call returns an error

---

> **US-15** — As a developer/owner, I want ingestion errors surfaced clearly so that I know when a document failed to index and why.

**Acceptance Criteria:**
- Every ingestion failure sets `documents.status = 'error'` and populates `documents.error_message` with a specific reason
- The user sees a plain-English error message in the chat UI; no silent failures
- A developer can query all failed documents: `SELECT filename, error_message FROM documents WHERE status = 'error'`
- Partial ingestion failures (e.g. embedding fails after parsing succeeds) do not leave the system in an inconsistent state — either the document is fully indexed or fully rolled back

---

### Future Capabilities (Phase 2+)
*Acceptance criteria will be defined when these stories are scoped for implementation.*

> **US-16** — As a user, I want to paste a URL and have it indexed so that online content is available in my knowledge base without manual downloading.

> **US-17** — As a user, I want to speak my questions and hear the responses so that I can use the system hands-free while working.

> **US-18** — As a user, I want the system to surface a relevant document or insight unprompted when it detects I am working on a related topic.

---

## 7. Logical Architecture

### Conceptual Overview

The system is composed of five logical layers. Each layer has a single responsibility. **Ingestion is triggered directly from the Interface layer — it does not pass through the agent.**

```
┌──────────────────────────────────────────────────────────────────────┐
│                          INTERFACE LAYER                             │
│   Chainlit web UI — chat input, file upload, streamed responses      │
│   Basic auth required on all routes                                  │
│                                                                      │
│   ┌──────────────────────────┐   ┌──────────────────────────────┐    │
│   │  Chat handler            │   │  File upload handler         │    │
│   │  on_message()            │   │  on_message() with elements  │    │
│   │  → calls agent           │   │  → calls ingestion pipeline  │    │
│   │                          │   │    directly (not via agent)  │    │
│   └──────────────────────────┘   └──────────────────────────────┘    │
└───────────────────┬──────────────────────────────┬───────────────────┘
                    │ user message                  │ file path + metadata
                    ▼                               ▼
┌───────────────────────────────┐  ┌───────────────────────────────────┐
│      ORCHESTRATION LAYER      │  │       INGESTION PIPELINE          │
│      LangGraph Agent          │  │                                   │
│                               │  │  loaders.py → chunker.py          │
│  ┌──────────────────────────┐ │  │  → embedder.py                    │
│  │   Retrieval Tool         │ │  │                                   │
│  │   semantic search Qdrant │ │  │  File → parse → chunk             │
│  └──────────────────────────┘ │  │  → embed (OpenAI ada) → Qdrant    │
│  ┌──────────────────────────┐ │  │  → write metadata → PostgreSQL    │
│  │   Memory Tool            │ │  └──────────────┬────────────────────┘
│  │   read/write user facts  │ │                 │
│  └──────────────────────────┘ │                 │
└───────────────────┬───────────┘                 │
                    │ structured prompt            │
                    ▼                              │
┌──────────────────────────────────────────────────────────────────────┐
│                           MODEL LAYER                                │
│   Claude (claude-sonnet-4-6 via Anthropic API)                       │
│   All Q&A, fact extraction, profile correction, memory summarisation │
│                                                                      │
│   OpenAI (text-embedding-3-small) — embeddings only                  │
└──────────────┬───────────────────────────────┬───────────────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────┐     ┌─────────────────────────────────────┐
│   VECTOR STORE           │     │   RELATIONAL STORE                  │
│   Qdrant                 │     │   PostgreSQL                        │
│                          │     │                                     │
│   Collection:            │     │   conversations — session records   │
│   second_brain           │     │   messages     — every turn         │
│   1536-dim cosine        │     │   user_profile — extracted facts    │
│   document chunks        │     │   documents    — ingestion metadata │
│   + embeddings           │     │   ingestion_jobs — async queue      │
└──────────────────────────┘     └─────────────────────────────────────┘

                      All LLM calls → LangSmith (100% coverage)
```

---

### Data Flows

#### Flow 1 — Document Ingestion

```
User uploads file via Chainlit
       │
       ▼
Interface layer (on_message with file element)
  → validate: file type ∈ {pdf, docx, txt} AND size ≤ 50MB
  → if invalid: return error message, stop
       │
       ▼
ingestion/loaders.py
  → PDF:  PyPDFLoader
  → DOCX: Docx2txtLoader
  → TXT:  TextLoader
  → if parse fails: mark document error, return error message, stop
       │
       ▼
ingestion/chunker.py
  → RecursiveCharacterTextSplitter
  → chunk_size=1000 tokens, chunk_overlap=200 tokens
  → separators: ["\n\n", "\n", ". ", " ", ""]
       │
       ▼
ingestion/embedder.py
  → OpenAI text-embedding-3-small → 1536-dim vector per chunk
  → write all vectors to Qdrant collection "second_brain"
  → if Qdrant write fails: rollback all written vectors, mark document error, stop
  → write document record to PostgreSQL (status: complete, chunk_count: n)
       │
       ▼
User sees: "Indexed {filename} — {n} chunks (ID: {doc_id})"
```

---

#### Flow 2 — Chat (Question → Answer)

```
User sends message
       │
       ▼
Interface layer (on_message)
  → load current session history from PostgreSQL (last 20 messages, current conv_id only)
  → save user message to PostgreSQL
       │
       ▼
LangGraph agent receives:
  [system prompt + user profile from user_profile table]
  + [current session history]
  + [current user message]
       │
       ├──→ Agent calls retrieve_documents tool
       │         → embed query with OpenAI text-embedding-3-small
       │         → semantic search Qdrant, k=5 chunks
       │         → return formatted chunk text with source filenames
       │
       ├──→ Agent optionally calls read_user_profile tool
       │         → fetch all rows from user_profile table
       │         → return formatted profile string
       │
       ├──→ Agent optionally calls update_user_profile tool
       │         → upsert a fact to user_profile table
       │         → used for real-time profile corrections (UC-07)
       │
       ▼
Claude generates response grounded in retrieved chunks + session history
  → response streamed to Chainlit UI
  → assistant message saved to PostgreSQL
  → full LLM call traced in LangSmith (includes retrieved chunks in metadata)
```

---

#### Flow 3 — Post-Session Memory Extraction

```
Session ends (Chainlit fires on_chat_end)
       │
       ▼
Interface layer (on_chat_end)
  → if session has 0 messages: skip, close conversation
  → load full session transcript from PostgreSQL (current conv_id)
       │
       ▼
memory/user_profile.py — extract_and_store()
  → format transcript as "Human: ... / Assistant: ..."
  → send to Claude with extraction prompt:
      "Extract key facts as JSON: [{category, key, value, confidence}]"
  → strip markdown fences from response if present
  → parse JSON
  → if parse fails: log error, close conversation, return 0 facts
       │
       ▼
For each extracted fact:
  → INSERT INTO user_profile (category, key, value, confidence, source_conv_id)
     ON CONFLICT (category, key) DO UPDATE SET value, confidence, updated_at
       │
       ▼
conversations table updated: ended_at = NOW()
       │
       ▼
Next session: full user_profile injected into system prompt
  → cross-session "memory" is the accumulated profile, not raw message history
```

---

### State Held Per Session

| What | Where | Lifetime | Notes |
|---|---|---|---|
| Authenticated session | Chainlit + basic auth | Single browser session | Re-auth on new session |
| Current conversation ID | Chainlit user session (in-memory) | Single browser session | Lost on crash |
| Current session messages | PostgreSQL `messages` | Permanent | Queryable by conversation_id |
| User profile facts | PostgreSQL `user_profile` | Permanent, updated each session | Max one value per category+key |
| Document embeddings | Qdrant `second_brain` collection | Permanent | Persisted in Docker volume |
| Document metadata | PostgreSQL `documents` | Permanent | Includes status and error info |
| LLM traces | LangSmith | Per LangSmith retention policy | Includes retrieved chunks |

---

### Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| LLM | Claude (claude-sonnet-4-6) throughout | Single model for all reasoning — simpler, more consistent, easier to observe |
| Embedding model | OpenAI text-embedding-3-small | Best cost/quality ratio; 1536 dimensions; Qdrant collection must match |
| Orchestration | LangGraph | Stateful agent graph with explicit control flow; tool-call loop is simple and auditable |
| Vector store | Qdrant | Production-grade, runs locally in Docker with zero config; gRPC + REST |
| Relational store | PostgreSQL | Reliable, queryable, JSONB for flexible metadata; triggers for `updated_at` |
| UI | Chainlit | Purpose-built for LLM chat; handles file upload, streaming, and session management |
| Observability | LangSmith | First-class LangChain integration; traces all LLM calls with zero instrumentation code |
| Authentication | HTTP Basic Auth | Minimal complexity for a single-user MVP; credentials in env vars |
| Deployment (MVP) | Local Docker on Mac mini | Zero cloud cost during development; identical code paths move to Azure in Phase 3 |
| Cross-session memory | Extracted profile, not raw history | Raw message history from old sessions would exhaust the context window; structured facts scale indefinitely |

---

### What the System Is Not

- It is not a general-purpose search engine — it only knows what the user has explicitly ingested
- It is not multi-user — the knowledge base, profile, and conversation history belong to one person
- It is not a real-time system — documents are indexed on upload, not continuously monitored
- It does not answer from Claude's general training knowledge — all factual answers must be grounded in the user's own documents
- It does not replay raw conversation history across sessions — cross-session context comes from structured profile extraction only
