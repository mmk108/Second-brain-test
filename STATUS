# Second Brain — STATUS.md

**Last updated:** 2026-07-04
**Current phase:** Phase 0 — The Vault
**Plan of record:** PROJECT_PLANv3.md
**Hard gate:** Phases 0.5+ blocked until contact-center POC Day 5 ships

---

## Where We Are

Plan v3 locked in principle 2026-07-04. Key decisions resolved this session:

- **Separation decision:** vault is a **dependency, not a sibling** of the contact-center
  POC. Two repos, two plans, never merged. POC reads from the vault via three CLAUDE.md
  lines and writes dated notes into raw/ — nothing more this week.
- **Architecture pivot from v1 README:** navigation-first vault (INDEX + wikilinks)
  replaces chunk/embed/Qdrant RAG at personal scale. Qdrant deferred behind a measured
  trigger (>500 pages or >10% retrieval misses).
- **HITL model:** agent self-routes memory; git branch + human merge is the approval
  gate. Resolves the June memory-router open question at the crawl rung.
- **Sequencing:** knowledge plane now (zero code); control plane (LangGraph loops)
  built post-POC from the POC's proven scaffolding.

---

## Step Tracker

### Phase 0 — The Vault (target: 2026-07-04/05, ~2 hrs)

| # | Step | Status |
|---|---|---|
| 0.1 | Create vault repo (raw/, entities/, concepts/, INDEX.md, CLAUDE.md w/ 6 rules) | ☐ Not started |
| 0.2 | `git init`; verify folder excluded from iCloud/OneDrive sync | ☐ Not started |
| 0.3 | Seed raw/ with POC docs (PROJECT_PLANv3-CC, ARCHITECTURE.md, STATUS.md) + this plan | ☐ Not started |
| 0.4 | Add three knowledge lines to POC repo CLAUDE.md | ☐ Not started |
| 0.5 | Passive capture during POC week: scribe notes, What Broke rows, decisions → dated files in raw/ | ☐ Ongoing (POC Day 1–5) |

**Exit check:** vault exists · POC repo points at it · ≥5 dated notes by POC Day 5.

### Phase 0.5 — Backfill + First Compile (target: weekend after POC Day 5)

| # | Step | Status |
|---|---|---|
| 0.6 | Dump wider corpus into raw/ (Terminus, blog posts, skills, client notes, newsletter output) | ☐ Blocked (gate) |
| 0.7 | `/goal` backfill in Claude Code — compile w/ diffs + source links; review + merge | ☐ Blocked (gate) |
| 0.8 | Manual synthesis pass over POC week notes → What Broke consolidation + S1–S5 draft | ☐ Blocked (gate) |
| 0.9 | Graph-view sanity check; INDEX complete | ☐ Blocked (gate) |
| 0.10 | **Vault proof test:** one real work question answered better than vanilla Claude | ☐ Blocked (gate) |

### Phase 1 — The Loops (weeks 1–2 post-POC)

Not started. First step will be cloning POC scaffolding (FastAPI, SqliteSaver,
config loader) into the loop service + drafting `loops.config.yaml` schema.

---

## Open Questions

| # | Question | Owner | Needed by |
|---|---|---|---|
| Q1 | Vault location + git remote: local-only, or private GitHub repo under mmk108? (Remote recommended — offsite backup; contents include client-adjacent notes, so private + review before any push) | Max | Phase 0.1 |
| Q2 | Obsidian installed on Mac mini, MacBook, or both? (Affects nothing agent-side; vault must live on ONE machine, others read via git) | Max | Phase 0.1 |
| Q3 | What client material is allowed into raw/? Define a redline (e.g., no client-confidential docs; sanitized lessons only) before backfill | Max | Phase 0.6 |
| Q4 | Session-hook mechanism: Claude Code hooks vs manual end-of-session prompt for POC week (manual is fine for Phase 0) | Max | Phase 1 |
| Q5 | Does the enterprise memory/storage design session (POC-side open item) consume vault learnings formally? Schedule after 2+ weeks of vault operation | Max | Post-Phase 1 |

## Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-04 | Keep second brain separate from contact-center POC | Locked POC scope; vault is cross-project infrastructure |
| 2026-07-04 | Navigation-first vault; Qdrant trigger-gated | Personal scale favors agentic file navigation; measure before adding infra |
| 2026-07-04 | Git merge as HITL promotion gate | Self-routing + post-hoc diff approval; cheapest rung of checkpoint motif |
| 2026-07-04 | Cut Chainlit, voice, DSPy from MVP | Fail the dual test: no daily-use value AND no capability-framework demo |
| 2026-07-04 | ai-newsletter-agent output becomes a raw/ feed (Phase 2) | Merge intake, not codebases |

## What Broke / What Was Missing

*(Fill a row every time something breaks or a capability is missing — same discipline
as the POC log.)*

| Date | What I tried | What broke / was missing | Implication | Priority |
|---|---|---|---|---|
| | | | | |

---

## Next Action

**→ Step 0.1: create the vault repo.** Two hours, zero code, then back to the
contact-center build.
