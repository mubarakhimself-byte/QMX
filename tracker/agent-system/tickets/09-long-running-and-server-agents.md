---
id: 09
title: Long-running and server agents
label: wayfinder:grilling
status: open
assignee:
blocked-by: [02]
who-decides: Claude decides and reports back (AFK)
---

## Question

How do background and server agents run? Cover:
- a Hermes-style scheduler (cron, no-agent jobs, goals, loops);
- budgets that pause rather than fail;
- automatic export of transcripts and logs;
- "where jobs run";
- resume after a crash.

## Added 2026-10-12

- **Load target:** about 40 agents at once on the operator's PC (browser use, research, compiling, tests, mini apps feeding each other). QMX-engine agents are light (mostly waiting on the network); Claude Code workers are ~1 GB RAM each, so they need a cap.
- **No Docker by default.** A light QMX sandbox (own work folder, hooks, process limits); Docker only where a remote server needs it.
- **SQLite at that load:** checkpoints and `control.db` take one writer at a time. Measure before 40 agents, and decide on per-thread files or Postgres.
- **The DevOps lens for agents:** logs, traces, and proof that a write really landed.
- **Runs lasting days** must survive restarts and usage-limit pauses.
