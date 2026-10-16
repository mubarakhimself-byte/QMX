---
title: Model-agnostic audit
type: research
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Ruling 3."
closed: 2026-10-16
---

## Question

Which pieces of the designed system are Claude-only, and what the fallback is for each on another provider.

## Why it matters

The operator wants any capable LLM, not Claude-only, while the engine is the Claude Agent SDK. The tension holds only at the node level. Known Claude-only pieces: the `Workflow` tool, hooks that exist only in TypeScript, Claude auto memory, `.claude/agents` sub-agent files, `disable-model-invocation` frontmatter, the usage telemetry shape.

## What the session does

AFK research. For each piece: where it is used, the fallback on the relay (an `llm` node, a sequential run, a file-based memory, a sidecar), and what is lost. Verify in the browser which SDK hooks exist in Python versus TypeScript. Write the fallback table into `research/methodology/` and flag any piece with no fallback so the umbrella can say so.

## Unblocks

Feeds the methodology umbrella's "model-agnostic at the node" rule and the skill format.

## Sources

`03-workflow-engines.md` §1 limits, §2 SDK pieces, §8 item 15; `01-bmad.md` §Q4, §Q5; `02-pocock-pstack.md` §5.

## Resolution

Resolved. Engine AD-13 (roles, not models) and AD-29 (the relay routes by model id); ruling 3. (Map rewrite 2026-10-16.)
