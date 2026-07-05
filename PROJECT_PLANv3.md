# 🧠 Second Brain — PROJECT_PLAN v3

**Status:** ACTIVE — Phase 0 only. Phases 1+ gated behind contact-center POC Day 5.
**Created:** 2026-07-04 · Supersedes PROJECT_PLANv2.md (draft, never locked)
**Companion tracker:** STATUS.md

---

## The One-Line Summary

A git-versioned markdown vault that every project reads from and writes notes into —
**a dependency, not a sibling.** Projects never merge with it. The agent-maintained
loops (compile / lint / synthesis / research) are built *after* the contact-center POC
ships, from that POC's proven scaffolding.

---

## Relationship to the Contact-Center POC (read this first)

The two projects stay **separate**: two repos, two plans. The POC is a client-facing
deliverable with locked scope; the vault is personal infrastructure underneath all
projects. The only connection this week:

1. The vault exists as a folder the POC repo points at (three lines in POC CLAUDE.md)
2. POC scribe notes / What Broke rows / daily decisions land as dated files in `raw/`
   — work already committed in POC plan Part 4, now captured permanently
3. Nothing else. No loops, no LangGraph, no second build competing with POC week

**What flows back after POC Day 5:**
- Battle-tested scaffolding (FastAPI service, SqliteSaver, config-first loader,
  event-table pattern) → cloned into the Phase 1 loop service
- A week of real captured material → the vault's first compile workload
- Empirical grounding for the deferred **memory/storage design session** (STATUS.md
  open item on the POC side) — the raw/-vs-compiled split, provenance links, and
  human-gated promotion are the crawl rung of that design

---

## Architecture: Two Planes

```
┌──────────────────────────────────────────────────────────────┐
│  KNOWLEDGE PLANE  (Phase 0 — build now, zero code)           │
│                                                              │
│   ~/vault/            git repo, Obsidian-compatible          │
│   ├── raw/            immutable captures — agent never edits │
│   ├── entities/       one page per client/tool/person/co.    │
│   ├── concepts/       one page per idea/pattern/lesson       │
│   ├── INDEX.md        every page + one-line description      │
│   └── CLAUDE.md       <200 lines: rules + pointers, never    │
│                       content                                │
│                                                              │
│   Interactive runtime: Claude Code / Claude Desktop          │
│   Read discipline: INDEX first → walk links → open only what │
│   the trail points at. Subagents for >10-page reads.         │
│   Sync rule: git ONLY. No iCloud/OneDrive on this folder.    │
└──────────────────────────┬───────────────────────────────────┘
                           │ reads / writes via git branches
┌──────────────────────────▼───────────────────────────────────┐
│  CONTROL PLANE  (Phases 1–3 — build after POC Day 5)         │
│                                                              │
│   LangGraph loop service (FastAPI, containerized) — cloned   │
│   from contact-center POC scaffolding                        │
│   ├── compile node    nightly · Haiku · raw/ → wiki pages    │
│   ├── lint node       weekly · Haiku · contradictions,       │
│   │                   duplicates, dead links, expired facts  │
│   ├── synthesis node  weekly · Fable · "what changed /       │
│   │                   what's drifting" note                  │
│   └── research graph  weekly · fan-out subagents + skeptic   │
│                       gate → dated, sourced, expiring pages  │
│                                                              │
│   Every run: LangSmith traced · SqliteSaver checkpointed ·   │
│   output = git branch + diff · human merge = approval        │
└──────────────────────────────────────────────────────────────┘
```

**HITL model (resolves the June open question):** the agent self-routes memory;
**git is the approval gate.** Every loop run lands as a branch + diff; human merge =
promotion approval. Same checkpoint motif as the POC's Slack Approve/Deny, at the
personal price point. Slack surface has a Phase 3 reinstatement trigger.

---

## Core Rules (written into vault CLAUDE.md, verbatim)

1. One lesson per file, one-line summary at top
2. Update the existing page — never create a duplicate
3. Delete notes that turn out to be wrong
4. **Never touch raw/** — it is read-only ground truth
5. Every compiled page links back to its raw/ source; unsourced pages get flagged,
   not trusted
6. Time-sensitive pages carry an expiry date

---

## Enterprise Capability Mapping

Every component doubles as a working demo of the foundational-capabilities framework —
the consulting artifact hiding inside the personal build.

| POC Component | Framework Capability | Enterprise Analogue |
|---|---|---|
| Vault (raw/entities/concepts) | 5. Data Foundations | Knowledge Store; raw/ = bronze, wiki = gold |
| INDEX.md + link-walking | 5a. Knowledge Store | Data catalog / metadata-driven retrieval |
| Git branch + human merge | 3. HITL approval workflow | Agent proposes, human approves |
| Nightly compile (cheap tier) | 5c. Data Ingestion | Scheduled ETL; routine work → routine tier |
| Weekly lint | 2 / 5c. Control Plane | Data quality jobs |
| Model tiering (Haiku loops, Fable synthesis) | 2b. Cost Analytics | FinOps / model routing |
| LangSmith on every run | 2. Observability | 100% execution tracing |
| Research graph + skeptic agent | 3. Multi-Agent Coordination | Fan-out/aggregate + fresh-context verification |
| Receipts (source + date + expiry) | 2. Risk | Data lineage + freshness SLAs |
| Container Apps deploy (Phase 3) | 4e. Agent Ops | Serverless agent hosting |

---

## Phases

### Phase 0 — The Vault (NOW: before/alongside POC Day 1 · ~2 hrs · zero code)

1. Create vault repo: `raw/`, `entities/`, `concepts/`, `INDEX.md`, `CLAUDE.md`
   (rules above); `git init`; confirm folder excluded from all cloud sync
2. Seed `raw/` — **POC-first, minimal:** PROJECT_PLANv3 (contact center),
   ARCHITECTURE.md, STATUS.md, this plan
3. Add three knowledge lines to the **POC repo's** CLAUDE.md:
   ```markdown
   ## knowledge
   - before starting, read relevant pages from ~/vault/entities/ and ~/vault/concepts/
   - ground claims about prior decisions in vault pages
   - at session end, write decisions/breakages as dated notes to ~/vault/raw/
   ```
4. **During POC week (passive):** scribe notes, What Broke rows, S1–S5 observations,
   daily decisions → dated files in `raw/`. No other vault work this week.

**Exit criteria:** vault exists · POC repo points at it · ≥5 dated notes accumulate
across the build week without dedicated effort.

### Phase 0.5 — Backfill + First Compile (weekend after POC Day 5 · ~3 hrs)

1. Dump the wider corpus into `raw/`: Terminus docs, blog posts, skill files, client
   notes, newsletter analyses, key chat exports
2. Run the `/goal` backfill in Claude Code: compile raw/ → entity/concept pages, every
   change as a diff, every page source-linked; review + merge
3. Run one manual synthesis pass over POC week's dated notes: draft the What Broke
   consolidation + S1–S5 entries *from the vault* (POC Day 5 task, executed here)
4. Open Obsidian graph view; sanity-check the web

**Exit criteria:** ≥30 compiled pages · 0 unsourced pages · INDEX complete · the vault
answers one real work question that vanilla Claude gets wrong or generic.

### Phase 1 — The Loops (weeks 1–2 post-POC)

- LangGraph service cloned from POC scaffolding: compile / lint / synthesis nodes,
  SqliteSaver, LangSmith traced
- `loops.config.yaml` — config-first, node → model tier mapping (same pattern as
  `department.config.yaml`)
- Session hook: end-of-session mining → dated notes in raw/
- Runs local (Mac mini, cron); outputs to git branches; human merges

**Exit criteria:** 7 consecutive unattended nightly compiles · lint catches ≥1 real
contradiction · cost per nightly run < $0.10 · every run in LangSmith.

### Phase 2 — The Research Machine (weeks 3–4 post-POC)

- Research graph: question → 3–5 sub-questions → parallel search agents → skeptic gate
  (fresh context, never shares researcher's context) → survivors land as dated, sourced,
  expiring pages
- **Convergence:** ai-newsletter-agent output redirects into raw/ as a feed — the two
  projects merge intake, not codebases
- One standing weekly sweep: agentic-AI practitioner layer

**Exit criteria:** one sweep produces ≥5 verified pages with receipts · skeptic kills
≥20% of raw claims (kill-rate of zero = broken skeptic).

### Phase 3 — Scale on Triggers, Not Calendar

| Item | Reinstatement trigger |
|---|---|
| Qdrant hybrid retrieval | Vault >500 pages OR retrieval-miss log >10% of queries |
| Azure Container Apps deploy | Loops stable 4+ weeks AND Mac mini uptime is the bottleneck |
| Slack Approve/Deny surface | Git-merge review exceeds ~15 min/week |
| Databricks pipeline | Vault feeds a client-facing or multi-user use case |
| Multi-user / RBAC | A second human touches the vault |

---

## NFRs

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Cost per nightly compile | < $0.10 |
| NFR-02 | Cost per weekly synthesis | < $1.50 |
| NFR-03 | CLAUDE.md size | < 200 lines, pointers only |
| NFR-04 | Trace coverage | 100% of loop runs in LangSmith |
| NFR-05 | Provenance | 0 compiled pages without raw/ source link (lint-enforced) |
| NFR-06 | Freshness | Time-sensitive pages carry expiry; lint flags expired |
| NFR-07 | Human review load | < 15 min/week merging diffs |

---

## Cut / Deferred (from v1 README)

| Item | Disposition |
|---|---|
| Qdrant vector RAG | Deferred — Phase 3 trigger |
| PostgreSQL | Cut — SQLite for loop state; vault holds knowledge |
| Chainlit UI | Deferred indefinitely — Claude Code/Desktop is the UI |
| Voice (Whisper/ElevenLabs) | Cut — Claude apps provide it |
| DSPy RL module | Cut — speculative, demos nothing |
| `user_profile` merged table | Replaced by raw/-vs-compiled split |
| Databricks | Trigger-gated, Phase 3 |

## Risks

| Risk | Mitigation |
|---|---|
| Vault work bleeds into POC week | Phase 0 is capped at setup + passive capture; hard gate on all other phases until POC Day 5 |
| Plumbing before content | No LangGraph code until Phase 0.5 exit criterion passes |
| Compile pass degrades pages | raw/ immutability + provenance lint + human merge gate |
| Sync corruption | Git only; folder excluded from all cloud sync |
| Loop cost creep | Tiering in `loops.config.yaml`; NFRs checked weekly from LangSmith |
| Skeptic rubber-stamps | Fresh-context isolation; kill-rate tracked |
