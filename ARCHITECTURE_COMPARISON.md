# Second Brain — Architecture Comparison

**Purpose:** Reference document comparing the three architectures evaluated for this
project, why the final design was chosen, and what it borrows from each.
**Related docs:** PROJECT_PLANv3.md (plan of record) · STATUS.md (tracker)
**Date:** 2026-07-04

---

## The Three Architectures at a Glance

| | **A. Retrieval-First (RAG)** | **B. Navigation-First (Vault/Wiki)** | **C. Two-Plane Hybrid (chosen)** |
|---|---|---|---|
| Origin | Original v1 README | Karpathy LLM-Wiki pattern; Machina article; claude-obsidian / claude-second-brain repos | This project — PROJECT_PLANv3 |
| Knowledge lives in | Vector DB (chunked embeddings) + SQL profile table | Plain markdown files in a git folder | Markdown vault (knowledge) + thin service layer (maintenance) |
| Retrieval | Semantic search over chunks | Agent walks INDEX.md + wikilinks, opens only what the trail points at | Navigation-first; hybrid index added only on measured trigger |
| Memory update | Agent extracts facts → merges into profile table | Agent compiles raw captures into wiki pages | Compile loops with git diff + human merge as approval gate |
| Ground truth | None (agent rewrites its own memory) | Immutable `raw/` folder | Immutable `raw/` folder + provenance links (lint-enforced) |
| UI | Custom (Chainlit) | Claude Code / Obsidian | Claude Code / Obsidian |
| Infra required day 1 | Vector DB, Postgres, blob storage, app hosting | A folder and git | A folder and git; loop service post-POC |
| Best at | Large corpora, fuzzy recall, multi-user scale | Personal scale, auditability, zero cost, compounding links | Both goals: daily-use tool + enterprise-pattern lab |
| Fails when | Personal scale (cost/complexity unjustified); stale facts embed as close as current ones and quietly rot | Corpus outgrows link-walking; link hygiene slips | Complexity creep if triggers are ignored |

---

## Architecture A — Retrieval-First (RAG Pipeline)

**Shape:** Ingest → chunk → embed → vector store (Qdrant) → semantic search →
stuff context window. Conversations and an agent-maintained `user_profile` table
in PostgreSQL. Chainlit UI, LangGraph orchestration on the chat path.

```
Upload → Chunk → Embed → Qdrant ─┐
                                  ├→ Context builder → Claude → UI
History + Profile (Postgres) ────┘
        ▲
        └── post-session fact extraction (agent merges into profile)
```

**Strengths**
- Scales to large corpora and fuzzy semantic recall
- Standard enterprise pattern — maps directly to Knowledge Store reference architectures
- Multi-user ready (row-level scoping in the DB)

**Weaknesses (why it lost at personal scale)**
- Chunking destroys document structure; embeddings miss exact-match lookups
  (names, order numbers, decisions, dates)
- **No ground truth:** the agent extracts, merges, and dedups its own memory —
  errors compound with no audit trail and no way to re-derive a fact
- **Invalidation rot:** a stale fact often embeds just as close as the current one;
  flat vector memory returns the most recent-looking match, not the true one
- Heavy standing infrastructure (vector DB + SQL + hosting + custom UI) for a
  single-user corpus of a few hundred documents
- Every query pays retrieval cost whether or not retrieval was needed

**Where it remains right:** enterprise scale, millions of chunks, many users,
compliance-scoped access. This is a deployment-scale architecture, not a
personal-scale one.

---

## Architecture B — Navigation-First (Vault / LLM-Wiki)

**Shape:** A git-versioned folder of plain markdown. The agent treats the knowledge
base like a codebase: reads an index, walks wikilinks, compiles raw captures into
entity and concept pages. Obsidian is the human window; Claude Code is the agent
runtime. No database, no embeddings, no server.

```
raw/        immutable captures (articles, transcripts, notes) — never edited
entities/   one page per concrete thing (client, tool, person, company)
concepts/   one page per idea (strategy, pattern, lesson)
INDEX.md    every page + one-line description — the front door
CLAUDE.md   <200 lines of rules + pointers, never content
```

**Operating loops (the part most implementations skip)**
- Session hook: end-of-session decisions/mistakes → dated notes in raw/
- Nightly compile (cheap model): new raw material → updated wiki pages
- Weekly lint: contradictions, duplicates, dead links, expired claims
- Weekly synthesis (premium model): cross-vault "what changed / what's drifting"
- Weekly research: fan-out sub-agents → skeptic gate → dated, sourced, expiring pages

**Strengths**
- **Compounding, not degrading:** search-based stores get noisier as they grow;
  a linked wiki gets stronger — every new page connects into the web
- Full auditability: raw/ is ground truth; every compiled claim links to its source
- Zero infrastructure cost; survives model swaps (the vault outlives the driver)
- Read discipline is cheap: index first, walk links, sub-agents for big reads
- Human and agent share the same artifact — no translation layer

**Weaknesses**
- Link-walking degrades past a corpus threshold (~500+ pages) or if lint slips
- No built-in observability, cost tracking, or governance — maintenance runs on
  trust and diffs
- Loops require scheduling infrastructure the pattern itself doesn't provide
- Single-user by construction

**Community reference implementations (studied, not adopted)**
- *claude-obsidian* (Karpathy LLM-Wiki lineage) — entity/concept compilation,
  lint pass, **hot cache** (session-end recent-context file → warm cold-starts)
- *claude-second-brain* — same raw/wiki split; local hybrid vector+BM25 SQLite
  index (qmd) as a lighter alternative to a vector DB; GitHub as source of truth
- *obsidian-second-brain* — scheduled maintenance agents; **vault-first research**
  (scan what's known, research only the gaps, produce a delta report)
- *second-brain-starter* (Agent SDK) — heartbeat pattern for proactive surfacing

---

## Architecture C — Two-Plane Hybrid (Chosen)

**Shape:** Architecture B is the product; a thin, containerized service layer from
Architecture A's toolchain runs B's maintenance loops with enterprise-grade
observability and human-in-the-loop control. Knowledge and machinery are kept on
separate planes so either can evolve independently.

```
┌──────────────────────────────────────────────────────────────┐
│  KNOWLEDGE PLANE (Architecture B, verbatim)                  │
│  git-versioned vault: raw/ · entities/ · concepts/ · INDEX   │
│  Runtime: Claude Code / Obsidian · Sync: git ONLY            │
└──────────────────────────┬───────────────────────────────────┘
                           │  reads / writes via git branches
┌──────────────────────────▼───────────────────────────────────┐
│  CONTROL PLANE (Architecture A's toolchain, relocated)       │
│  LangGraph loop service (FastAPI, containerized)             │
│  compile (nightly·cheap) · lint (weekly) · synthesis         │
│  (weekly·premium) · research graph (fan-out + skeptic)       │
│  Every run: LangSmith traced · SqliteSaver checkpointed ·    │
│  output = git branch + diff · human merge = approval         │
└──────────────────────────────────────────────────────────────┘
```

**The synthesis — what C takes from each**

| From A (RAG design) | From B (vault design) |
|---|---|
| LangGraph orchestration — moved from the chat path to the loops | Markdown vault as sole knowledge store |
| Observability from day one (LangSmith, 100% loop-run tracing) | raw/-vs-compiled split; immutable ground truth |
| Config-first discipline (`loops.config.yaml`, node → model tier) | INDEX-first cheap reading; link-walking |
| NFRs and phase gates with acceptance criteria | Maintenance loops + expiry-dated claims |
| Containerized service, Azure deploy path (trigger-gated) | Git as sync and version layer |
| HITL governance instinct | — realized as **git diff + human merge** (agent proposes, human approves) |

**Key design decisions**
1. **Vault is a dependency, not a sibling.** Every project reads from it via three
   CLAUDE.md lines and writes dated notes into raw/. Projects never merge with it.
2. **HITL promotion:** the agent self-routes memory; git is the approval gate.
   Every loop run lands as a branch + diff; human merge = promotion. Same
   checkpoint motif as an enterprise Slack/Teams Approve-Deny, at the personal
   price point.
3. **Scale on triggers, not calendar.** Vector retrieval returns only when the
   vault exceeds ~500 pages or a retrieval-miss log shows >10% link-walk failures
   — and as a local hybrid index (vector+BM25 SQLite) before any hosted vector DB.
4. **Model tiering as FinOps:** routine compile/lint on the cheap tier; the premium
   model earns its seat only on the weekly synthesis pass.
5. **Provenance is lint-enforced:** zero compiled pages without a raw/ source link;
   time-sensitive pages carry expiry dates (the invalidation problem, solved at
   file level).

**Enterprise mapping (why this doubles as a reference miniature)**

| Component | Enterprise analogue |
|---|---|
| raw/ → compiled wiki | Bronze → gold knowledge layers |
| INDEX.md + link-walking | Metadata-driven retrieval / data catalog |
| Git branch + human merge | HITL approval workflow (agent proposes, human approves) |
| Nightly compile / weekly lint | Scheduled ingestion + data-quality jobs |
| Model tiering in config | FinOps / model routing |
| LangSmith on every run | Control-plane observability |
| Skeptic-gated research + receipts | Multi-agent verification + data lineage / freshness SLAs |

---

## Landscape Note — Dedicated Memory Frameworks (evaluated, not adopted)

Mem0 (managed personalization memory), Zep/Graphiti (temporal knowledge graph with
fact validity windows), Letta/MemGPT (OS-style tiered memory runtime), and Cognee
(graph construction from unstructured docs) solve the *transient agent-session
memory* problem at multi-user scale. Industry consensus as of mid-2026: three memory
scopes are standard (episodic / semantic / procedural), and the hardest sub-problem
is **invalidation** — knowing when a stored fact stopped being true. Common
production pattern: a markdown vault holds canonical, human-owned knowledge; a
framework layer holds transient session memory. This project implements the vault
half; the framework half is an enterprise-phase decision (input to the deferred
memory/storage design session).

---

## Decision Summary

**A** is the right architecture at enterprise scale and the wrong one at personal
scale. **B** is the right knowledge model but ships with no observability,
governance, or scheduling. **C** keeps B's knowledge model intact and applies A's
engineering discipline only where it earns its keep — the maintenance loops —
with humans approving every promotion via git. It is simultaneously a daily-use
tool and a working miniature of an enterprise agent-knowledge platform.
