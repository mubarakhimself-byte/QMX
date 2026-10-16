---
title: Library read contract for agents
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Rewrite against ruling 28 and study 24 (one Library replacing two); drop Strats and the Strats-session hand-off."
closed: 2026-10-16
---

## Question

Which nodes and edges can be parsed for free today across the five strategy stores, and what read interface agents need from Strats so the methodology's workflows can search prior work, dead ends and lineage.

## Why it matters

Strats v2 is its own session (B8), but the methodology cannot wait for it: the hub routes by scanning artifacts, the hill-climb reads negative results, the validator reads lineage. The 40-million-documents clipping shows that when a corpus already ships its edges the graph is a parse, not an extraction (929M edges, zero model calls), and that its LangGraph agent loop was worse than the plain pipeline with a refusal ladder. `05` §4 already lists the parseable nodes and the 14 typed CT-07 edges.

## What the session does

AFK research. Inventory the five stores (control Library, QMF registry, CT-33 bots, QMB ledger, app artifacts and journals): node kinds, edge kinds, keys, where the join fails today (free-text Library relations, no agent path into the registry or ledger). Write the read contract: `library.search(kind, tags, text)`, `library.lineage(id, relation, depth)`, `library.negative_results(tags)`, `library.memo(key)`, with a refusal when nothing grounds the query. Save the note in `research/methodology/` and hand the inventory to the Strats session.

## Unblocks

Nothing on the map directly. Feeds the Lab tools, memory scopes, first templates and the Strats session.

## Sources

`05-qmx-today.md` §4; clipping "Structuring 40 Million Documents into an Agentic Knowledge Graph"; `BACKLOG.md` B8, B18.

## Resolution

Resolved. Library AD-9 (one port, eleven verbs) and AD-15 (the engine uses the port only). One Library replaces both hp17 Libraries (`MIGRATION.md`). (Map rewrite 2026-10-16.)
