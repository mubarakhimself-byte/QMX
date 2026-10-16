---
title: Memory candidates facts
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Memory for autonomous workflows (ruling 8)."
closed: 2026-10-16
---

## Question

Finish backlog B51: the MemoryProvider interface, the scopes, and the facts on Hindsight, Mem0, plain files and LangChain-style stores, so the memory-scopes ticket can decide with sources.

## Why it matters

The memory ticket is HITL and waits on these facts. The research note exists at `rebuild/research/2026-10-12-agent-system/memory.md` but was never finished, and Deep Agents' memory (namespaces, episodic search, background consolidation) is the behaviour QMX lost (`03` §4, §8 item 11).

## What the session does

AFK research in the browser. For each candidate: scopes it supports, size limits, write conflicts, consolidation, cost, licence, whether it runs locally. Add Hermes' bounded `MEMORY.md` rules and BMad's sanctum layout. Write the comparison into `research/methodology/` with the provider interface sketch.

## Unblocks

Memory scopes and lessons.

## Sources

`BACKLOG.md` B40, B51; `03-workflow-engines.md` §4, §6 Hermes memory, §9.3; `01-bmad.md` memory agents.

## Resolution

Resolved. Study 28 and engine AD-18 (memory is a port; evidence lives in the Library as `memory-row`, Library L1 granted). (Map rewrite 2026-10-16.)
