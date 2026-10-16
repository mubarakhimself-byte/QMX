# Rubric walk — the good-spine checklist

Reviewer: this run, inline.

| Check | Result | Note |
| --- | --- | --- |
| Fixes the real divergence points for the level below and misses none | **mostly** | adds needed: principal model, run-ref ownership, item-state storage (see adversarial 3-5) |
| Every AD's Rule is enforceable and prevents its stated divergence | **mostly** | AD-2 is not enforceable as written for governed kinds (adversarial 1) |
| Nothing under Deferred could let two units diverge | pass | the embedding model, CSR cadence and GC policy cannot change any interface |
| Named tech verified-current | pass | see review-currency |
| Ratifies rather than contradicts the brownfield codebase | pass | keeps Library B's blob store discipline, FTS5, memo, lock + BEGIN IMMEDIATE, `ResultsStore` layout as degraded mode, `ComputeProvider`, `credentials_scope`, CT-07 verbatim, CT-09 identity law, DEC-0188 bucket push by the server |
| Covers the driving spec's capabilities | pass | every item in the task brief (kinds, relationships, versions, previews, search, agent access, concurrent edits, backups, migration; gateway, auth, transfer, caching, conflicts, offline, secrets, money, DevOps; engine interface) maps to an AD in the Capability map |
| No new AD weakens an inherited one | n/a | no parent spine; the harness DESIGN.md is treated as read-only and untouched |
| Every dimension the altitude owns is decided, deferred or open | **one gap** | hub self-monitoring is silent (adversarial 7); performance budget is silent: add a Deferred row stating the expected scale (thousands of objects, not millions) and that CSR/FTS are sized for it |
| Operational envelope (deployment, environments, operations) | pass after fix | PC + server + bucket topology, timers, drills, restore path; worlds under OPEN-2 |
| Candidate designs listed before choosing | pass | HLD §2 lists four Library candidates and three intermediary candidates with reasons |
| Claims labelled retrieved / remembered / inferred | pass | spine, HLD, LLD carry labels; memlog entries carry them |

**Verdict: close the five adversarial holes and the two silent dimensions, then final.**
