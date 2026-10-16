# 33 — State of play, 2026-10-16 late night (re-walk before the usage reset)

The lead re-walked the whole session, from the morning backlog through the resets, at the operator's request (ruling 72). Read this file first next time, then `26` (the rulings, which outrank everything else).

## 1. The day in one line each

1. **Morning.** The goal was set: design the workflow system and the methodology, and wire both into QMA v2 (BACKLOG B26-B36). Context collection covered BMad, Pocock, pstack, workflow engines and QMX today (files 01-05).
2. **Midday.** A Fable agent read the work through five quant lenses and drew a Wayfinder map (06, 07). The operator added seeds: the Lab is the core, plugins are the mini-app contract, the hub is just a place, and so on.
3. **Afternoon.** More studies came in: the funnel (08), the risk unit (09), UI depth (10), references (11), failure handling and RLM (13), folders, mini apps and browser (14), templates (15-17) and browser harnesses (18). They were centralised into 19, reviewed in 20a/20b, and a verdict was written (21). Explainer page v1 was produced.
4. **Evening turn.** The operator corrected course. Rulings 22-37:
   - One engine; the harness is untouched.
   - Desktop app only.
   - The Library stores everything.
   - A load balancer across multiple accounts.
   - No spending caps.
   - Strats is out of scope.
   - The build waves are dropped.

   Grounding followed: UI click-through (23), docs (24), Hermes, n8n and the load balancer (25). The rulings file (26) and a rubric walk (27) came next.
5. **18:30.** Two Fable + BMad architectures were delivered: the workflow engine and Library + remote data. The journey page was published. The operator approved both architectures.
6. **Night.** Rulings 45-59. Studies on memory (28), environments (29) and data/DevOps (30). The Lab and Pods architecture landed. Both architectures were amended. Other reading: Rivet (harness outside the sandbox), Cua (31), Amp (32), Cloudroom (below). Rulings 60-72.

## 2. What exists now (all on `D:\QMX-worktrees\agent-system`, branch `plan/agent-system`, **uncommitted**)

| Item | Path | Status |
|---|---|---|
| Binding rulings 1-72 | `research/methodology/26-operator-rulings-and-alignment.md` | Current; outranks all |
| Rubric walk | `27-rubric-walk.md` | Marks 01-22 as KEEP / PARTLY-STALE / SUPERSEDED |
| **Workflow engine architecture** | `architecture/workflow-engine/` (27 ADs) | Approved, amended once (rulings 45-59, Rivet, memory, environments) |
| **Library + remote data architecture** | `architecture/library-and-data/` (19 ADs) | Approved, amended once (server-primary switch, no asks, L1-L10 granted, dataset cards, book/bms) |
| **Lab + Pods architecture** | `architecture/lab-and-pods/` (17 ADs, UI-TO-BACKEND-MAP) | Delivered from screenshots; not yet reviewed by him |
| UI handoff (running) | `UI-HANDOFF.md` | Sections 0-7 filled; Machines view (ruling 65/67) still to add |
| Studies still valid as sources | 01-03, 08, 09, 11, 13, 14, 18, 23-25, 28-32 | — |
| Wayfinder map | `wayfinder/` (69 tickets, rubric field) | **Stale versus the three architectures**; needs a rewrite before build planning |
| Explainer pages | artifact "QMX Agent System" (stale), "QMX Design Day" (pre-amendment) | Need one refreshed page |

## 3. Open decisions, merged (his calls only; everything else is a labelled default)

1. **Agent hosting provider** (rulings 55, 69). Options:
   - Contabo for storage and always-on services, plus a managed agent host for burst. Candidates: Amp (runners free, orbs $0.08-1.32/h), Cloudroom (free 100 cloud agents per 30 days; Pro $50; open source, self-hostable Rust core, still being packaged), Cloudflare, others.
   - Or Contabo for everything.
2. **Credentials once, everywhere** (61): adopt the key vault in the Hub plus short-lived run passes. The Claude plan login stays per machine.
3. **Mixed providers inside one agent** (62): relay routing by model name, as a harness extension under the load-balancer exception.
4. **Machines view** (65, 67): lean on provider dashboards via MCP or computer use first; build a native view only if needed.
5. **Backtests on one dedicated QMB machine** (68): it shapes the Lab's QMB door and remote runs; detail comes later.
6. Engine leftovers: what counts as "irreversible external"; whether self-improvement defaults to auto.
7. Lab leftovers: paper start needs his yes; paper money lives on a server ledger in v1.
8. Library leftovers: copilot-chat merges of units and bots ask once.
9. Data (30): **back up the orphaned 10 GB tick history now**; the trading node gets its own small VPS.

## 4. Backlog coverage (BACKLOG.md)

- **Designed:**
  - B33 engine, with B34 cron, B35 load balancer and B13 templates as engine configurations;
  - B30/B31/B32 homes, packs, folders and plugins;
  - B23 mini apps (engine and Library);
  - B42, partly: Lab tools and the Library door;
  - B40/B41 memory and self-improvement;
  - B36 concurrent edits (Library branches);
  - B44-B46 server and long runs (environments, Hub);
  - B17/B38 browser and computer use (Cua, read-only first).
- **Researched, not designed:** B26-B28 methodology itself (planned "in chat"); B16 MCP apps.
- **Missed:** B29 system prompts.
- **Out:** B7-B10, Strats.

## 5. What could ship tonight (ruling 71)

- **Workflow:** poteto-mode **autopilot-stack** (`~/.claude/skills/poteto-mode/playbooks/autopilot-stack.md`): one owner per PR, verified, appended to one linear stack, and **never merged** by agents. Run it with the **light-verification** rule (memory `light-verification-per-pr`): one build and one check per PR, one fix round, low findings logged. The reference session is "Claude Agent SDK baseline and design".
- **Best candidate:** the **workflow engine core** as a new, separate package (`qmx-engine`), using only the harness's public API. Its first packets:
  1. format and validator;
  2. ledger, memo and replay;
  3. core node kinds (script, rule, loop, join, wait, subworkflow);
  4. test mode with real cheap models;
  5. agent/llm nodes via the harness;
  6. scheduler and inbox.

  It uses the LibraryPort with an in-memory fake until the Library ships.
- **Blockers to state honestly:**
  - The HP stack (#81-#90) is unmerged, so tonight's work stacks on `qma/hp17`.
  - D1-D4 have not run.
  - The B1 SQLite fix is not in.
  - No build plan or packets have been written yet (the Wayfinder map is stale).
- **Needed from him before 8 pm:** a go. The lead then writes the packet plan and the start prompt from the engine SOLUTION-DESIGN §18 live checks.

## 6. Cloudroom facts (read in the browser, 2026-10-16)

- **What it is:** open-source cloud agents. Each agent gets its own isolated sandbox VM with full admin rights and its own git branch. The site shows 100 agents on 100 VMs. There's a desktop app; macOS and Linux only.
- **Harnesses:** cloud threads run Claude Code, Codex, Pi Agent, OpenCode, fx and **Hermes**.
- **Models:** sub-agents can mix models across harnesses and models, including OpenRouter. This is the exact "main on one model, sub-agents on others" pattern from ruling 62.
- **Subscriptions:** you bring your own, and harnesses call the providers directly.
- **Pricing:** the free plan includes 100 cloud agents per 30 days. Pro is $50/month, Ultra $500/month.
- **Self-hosting:** the Rust core runs on a Linux VM with PostgreSQL. Packaging is still in progress.
- **Fit:** it is an agent host plus a dashboard, like Amp. Under the Rivet principle it runs the harness *inside* the sandbox, so treat it as a compute and placement option behind the engine's WorkerPort, not as QMX's engine.
