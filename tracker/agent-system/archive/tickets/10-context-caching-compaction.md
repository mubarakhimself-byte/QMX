> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

---
id: 10
title: Context: caching and compaction
label: wayfinder:grilling
status: open
assignee:
blocked-by: [02]
who-decides: Claude decides and reports back (AFK)
---

## Question

What are the per-worker rules that keep the prompt cache and Opus 5.5's append-only history intact?
- Automatic compaction in the Anthropic style (server-side or Claude Code's own).
- Byte-stable prompt layout.
- Sticky account per thread.
- Effort changes.
- Background session memory, so the operator never waits on compaction.

Inputs: `langchain-stack.md` §a10-a11, `cookbooks.md` §1-5.
