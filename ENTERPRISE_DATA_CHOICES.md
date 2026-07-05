# Second Brain at Enterprise Scale — Data & Storage Choices

**Purpose:** Capture the design discussion on how the vault architecture translates
to Azure / GCP at enterprise scale, the two candidate spine patterns, and the open
questions to resolve before any client build.
**Status:** Working notes — input to the deferred memory/storage design session.
**Related docs:** PROJECT_PLANv3.md · ARCHITECTURE_COMPARISON.md
**Date:** 2026-07-04

---

## The Core Insight

The personal vault is secretly a **medallion architecture**:

| Vault | Medallion | Role |
|---|---|---|
| raw/ | Bronze | Immutable captures, never rewritten |
| (compile pass) | Silver | Extraction, dedup, linking |
| entities/ + concepts/ | Gold | Curated, compiled, trusted knowledge |

Every personal-scale component has a direct enterprise analogue — except identity,
which has no personal analogue at all (see Open Questions).

---

## Component Translation Map

| Vault component | Azure | GCP |
|---|---|---|
| **raw/** (immutable ground truth) | Blob Storage w/ immutability policy (WORM) + versioning | Cloud Storage w/ object versioning + retention lock |
| **Compiled wiki** (entities/concepts) | Delta Lake on ADLS Gen2 via Databricks, governed by Unity Catalog; or Blob + Cosmos DB metadata | BigQuery / Delta on GCS via Databricks; Firestore for page metadata |
| **INDEX.md** (front door) | Azure AI Search — hybrid keyword + vector, w/ security trimming | Vertex AI Search |
| **Wikilink graph** | Cosmos DB (Gremlin) — or Graphiti/Neo4j on AKS if temporal edges matter | Neo4j on GKE, or Spanner Graph |
| **journal/ + brain_events** | Postgres Flexible Server (guardrail_events schema, verbatim) + App Insights / LangFuse traces | Cloud SQL Postgres + BigQuery analytics (newsletter-agent runs/items pattern, generalized) |
| **Compile / lint / synthesis loops** | Container Apps Jobs + LangGraph, scheduled | Cloud Run Jobs + Cloud Scheduler |
| **Git-merge approval gate** | Azure DevOps / GitHub Enterprise PR review; or checkpoint → Teams/Slack Approve-Deny | Same; or Cloud Workflows + approval step |

---

## The Real Decision: Which Spine

Not Azure vs GCP — the architectural fork is **where canonical knowledge lives**.

### Pattern A — Docs-as-Code Spine (git-centric)

```
Authors/Agents → Git repo (markdown) → PR review = HITL promotion gate
                        │  (CODEOWNERS routes approval to domain owners)
                        ▼  CI on merge
                 Blob/GCS mirror → AI Search / Vertex Search indexer → Agents
```

- **Governance:** PR review IS the approval workflow — auditable, familiar,
  role-routable via CODEOWNERS. Better than most memory platforms offer natively.
- **Humans are first-class authors** — they edit knowledge with normal tools.
- **Portability:** knowledge is plain files; survives every platform swap.
- **Personal build ports almost unchanged** — swap "owner merges" for
  "department knowledge owner merges."
- Weakness: git is not an ACL system; document-level security must be enforced
  downstream at the index/retrieval layer.

**Best when:** knowledge is curated, human-owned, moderate volume; auditability
and authorship matter more than ingestion throughput.

### Pattern B — Lakehouse Spine (Databricks-centric)

```
Sources → Blob/GCS (bronze) → Databricks jobs (compile/lint = silver→gold)
              → Unity Catalog (ACL spine, lineage, audit)
              → Vector Search / AI Search → Agents
```

- **Unity Catalog replaces two vault rules automatically:** lineage = rule 5
  (provenance), and rule 6 (expiry) becomes a column + scheduled invalidation job.
- **ACL spine:** Entra ID groups mirrored into UC (the employee-support-assistant
  pattern) — row/document-level security enforced at query time.
- **Scales to many agents, many departments, high ingestion volume.**
- Weakness: humans are no longer first-class authors; knowledge editing goes
  through pipelines, and the approval gate must be custom-built.

**Best when:** the knowledge base serves many consumers, ingestion is high-volume
/ machine-generated, and per-document security is mandatory.

### Recommended Hybrid — A for Knowledge, B for Telemetry

Canonical knowledge lives in git (approval-by-PR as governance humans already
understand); events, traces, cost, and usage roll into the lakehouse (dashboards,
FinOps, chargeback). This mirrors the two-plane personal architecture exactly —
which makes the personal build a legitimate demo artifact for this client
conversation. Industry note: most mid-market deployments converge on markdown
vault for canonical knowledge + a managed layer for transient session memory.

---

## What Changes Fundamentally at Enterprise Scale

1. **Identity & access.** The vault has one reader; the enterprise version needs
   document-level ACLs enforced *at retrieval* (AI Search security trimming / UC
   row filters). A knowledge base that leaks across departments is a worse failure
   than one that forgets. No personal-scale analogue — must be designed fresh.
2. **Invalidation becomes a service.** Expiry dates on files become validity
   windows on facts (the Zep/Graphiti pattern: valid_at / invalid_at). Stale
   knowledge at scale is a liability, not an inconvenience.
3. **The skeptic gate becomes policy.** Personal: one skeptic agent. Enterprise:
   verification tiers by knowledge criticality (e.g., financial facts require
   two-source receipts; style guidance requires none).
4. **Session memory splits from canonical knowledge.** Transient agent-session
   memory (who said what, mid-task state) belongs in a dedicated layer
   (Mem0 / Zep / Letta class, or checkpointer store) — never compiled into the
   canonical vault without passing the promotion gate.
5. **Cost tracking becomes chargeback.** Personal NFR ("<$0.10/compile") becomes
   per-department attribution — the FinOps rows in the POC backlog.

---

## Open Questions to Think Through

### Spine & storage
- Q1. Does the client's knowledge change more by **human curation** (→ Pattern A)
  or **machine ingestion** (→ Pattern B)? What's the ratio?
- Q2. If Pattern A: what's the mirror latency tolerance (merge → searchable)?
  Minutes (event-driven indexer) vs hours (nightly)?
- Q3. If Pattern B: who owns the approval gate build, and what surface
  (Teams/Power Automate per the POC ladder)?
- Q4. Is a graph DB justified day 1, or does the wikilink-in-markdown +
  link-table-in-SQL rung hold until multi-hop queries are a proven need?
  (Same trigger discipline as personal Phase 3.)
- Q5. Blob/GCS vs Delta for the compiled layer: do downstream consumers need
  SQL access to knowledge pages, or only search/agent access?

### Governance & identity
- Q6. What is the promotion taxonomy — which knowledge classes need which
  approval tier (auto-merge / single owner / dual review)?
- Q7. How do ACLs propagate from source systems into the index (Entra → UC →
  security trimming)? Who owns group hygiene? (This killed timelines in the
  M365 Copilot rollout — permissions hygiene was the long pole.)
- Q8. Retention & residency: does raw/ (bronze) contain PII, and does WORM
  immutability conflict with right-to-erasure obligations? (It does — needs
  a redaction-on-write or crypto-shredding design.)
- Q9. Who owns the golden set for knowledge quality — same "managers own the
  golden set" operating model as the agent POC?

### Memory layer
- Q10. Build vs buy for transient session memory: checkpointer store (own) vs
  Mem0/Zep class (managed)? What data can leave the tenant?
- Q11. Where is the promotion boundary between session memory and canonical
  knowledge — what evidence threshold moves a fact from "the agent noticed"
  to "the organization knows"?
- Q12. Temporal correctness: do any use cases need "what was true as of date X"
  (→ validity windows / Graphiti pattern) or is current-state enough?

### Operations & economics
- Q13. What does the lint pass cost at N pages/day, and which tier runs it?
  (Model-tiering config from day 1.)
- Q14. What is the retrieval-miss metric at enterprise scale, and who reviews it?
  (The trigger discipline: measure before adding vector/graph infrastructure.)
- Q15. Chargeback unit: per department, per agent, per query? Aligns with POC
  Backlog #12.

### Strategy
- Q16. Does the client conversation start from the personal build as demo
  ("this is the pattern at $0/month — here is what each enterprise property
  costs you") — and if so, which vault contents are shareable?
- Q17. Where does this intersect the Microsoft estate story (Agent 365 /
  Copilot connectors indexing the same knowledge)? Complement or conflict?

---

## Next Step

These questions are the agenda skeleton for the **memory/storage design session**
(deferred item, contact-center POC STATUS.md). Recommended timing: after 2+ weeks
of personal vault operation, so answers are grounded in observed behavior —
compile quality, lint catch-rate, review load — rather than whiteboard reasoning.
