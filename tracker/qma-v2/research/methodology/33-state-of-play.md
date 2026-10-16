# 33 — State of play, 2026-10-16 late night (re-walk before the usage reset)

The lead re-walked the whole session, from the morning backlog through the resets, at the operator's request (ruling 72). Read this file first next time, then `26` (the rulings, which outrank everything else).

**Updated 2026-10-16, night (after 27d).** Current truth, in short:
- Rulings run **1-88** (file 26, sections A-J). Ruling 88: gaps go back into the architectures first.
- The HP stack is **merged into `rebuild/base`** at `ed704c92`. The old blocker "the HP stack is unmerged" is gone.
- The three architectures were amended through **27c** (gap fixes from the final rubric walk `27b-final-rubric-walk.md`) and **27d** (the independent fix-check `27d-fix-check.md`). The applied record is `27c-gap-fixes-applied.md`, including its §"27d applied".
- `ENGINE-PLAN.md` (the engine build plan, packets EP0-EP14, TP1-TP4, DP1) and `PROMPT-ENGINE.md` (its start prompt) exist at the root of `tracker/qma-v2/`.
- The superseded drafts 06, 07, 12, 19, 20a, 20b, 21 and 22 are archived in `archive/2026-10-16-methodology-drafts/`.
- The Wayfinder map was rewritten (`wayfinder/REWRITE-NOTES.md`), and the tickets resolved by 27c and 27d are closed.

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

## 2. What exists now (all on `D:\QMX-worktrees\agent-system`, branch `plan/agent-system`)

| Item | Path | Status |
|---|---|---|
| Binding rulings 1-88 | `research/methodology/26-operator-rulings-and-alignment.md` | Current; outranks all (ruling 73: architecture approved as solid) |
| Rubric walks | `27-rubric-walk.md`, `27b-final-rubric-walk.md` (6 blockers, 26 should-fix), `27d-fix-check.md` (1 critical, 13 should-fix) | All findings applied; see `27c-gap-fixes-applied.md` |
| **Workflow engine architecture** | `architecture/workflow-engine/` (35 ADs) | Approved; amended three times plus the 27c and 27d fixes: chunking and context discipline (AD-34), session homes (AD-35), drafts off `main`, run `mode` plus one shared status table, "tested" keyed on the definition `content_hash`, runaway guard (no spend caps), capacity derived from RAM, central relay, provider onboarding |
| **Library + remote data architecture** | `architecture/library-and-data/` (19 ADs) | Approved; L1-L17 answered; run passes (no key on any worker), `refs/drafts`, `refs/challengers` |
| **Lab + Pods architecture** | `architecture/lab-and-pods/` (17 ADs, UI-TO-BACKEND-MAP) | Approved with the rest (ruling 73); backtests on the QMB machine, paper as daily runs, no spend asks |
| UI handoff (running) | `UI-HANDOFF.md` | Sections 0-9; §9 adds machines, keys, providers and context |
| Engine build plan | `ENGINE-PLAN.md`, `PROMPT-ENGINE.md` | Written; check it against 27d (see `27c` §"27d applied" for what changed under it) |
| Studies still valid as sources | 01-03, 08, 09, 11, 13, 14, 18, 23-25, 28-32 | — |
| Archived drafts | `archive/2026-10-16-methodology-drafts/` (06, 07, 12, 19, 20a, 20b, 21, 22) | Reference only |
| Wayfinder map | `wayfinder/` | Rewritten against the architectures; resolved tickets closed |
| Explainer pages | artifact "QMX Agent System" (stale), "QMX Design Day" (pre-amendment) | Need one refreshed page |

## 3. Open decisions, merged (his calls only; everything else is a labelled default)

**His calls first** (engine OPEN-DECISIONS A-C):
- A. Grant harness requests H0, H15, H16, H17. Recommended: yes. Each has a fallback that needs no harness edit.
- B. Does the 50% plan background cap still apply to workflows (ruling 27)? Recommended: keep it for plan accounts only.
- C. Accept study 30 §4-§5 as the design for the first data packets (rulings 58, 81)? Recommended: yes, tick backup first.

**Still open, with recommendations:** the burst provider to try first; whether `host_harness` is acceptable at all; plan logins on Contabo and an owned Amp runner; what counts as an irreversible external effect; Library OPEN-2 to 5 (mirror the registry, encrypt the bucket, dense retrieval, public Hub listener); Lab OPEN-1, 2, 4, 6 (pod to node, paper money, mix, pairs).

**Answered since this file was first written:**
- Hosting: Contabo first, others addable (ruling 74); capacity is about 4 sessions on its 12 GB (ruling 76).
- Central relay (ruling 75): the PC and Contabo keep relays; Contabo's is central.
- Credentials (61), mixed providers (62), machines view (65, 67) and the QMB machine (68): all designed (engine AD-28 to AD-32).
- Self-improvement default (79), inbox volume (77), creation and publishing (80).
- Paper start needs his yes (80). Lab schedules ask once at publish (80).
- Chat merges into `main` ask once: lifecycle kinds by ruling 80, governed kinds on the earlier recommendation.

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
- **Blockers, as of the 27d update:**
  - ~~The HP stack (#81-#90) is unmerged.~~ Merged into `rebuild/base` at `ed704c92`.
  - D1-D4 have not run.
  - The B1 SQLite fix is not in.
  - ~~No build plan or packets.~~ `ENGINE-PLAN.md` and `PROMPT-ENGINE.md` exist; shipping starts in the morning (ruling 84).
- Superseded: "ship tonight" (ruling 71) became "ship early tomorrow morning" (ruling 84).

## 6. Cloudroom facts (read in the browser, 2026-10-16)

- **What it is:** open-source cloud agents. Each agent gets its own isolated sandbox VM with full admin rights and its own git branch. The site shows 100 agents on 100 VMs. There's a desktop app; macOS and Linux only.
- **Harnesses:** cloud threads run Claude Code, Codex, Pi Agent, OpenCode, fx and **Hermes**.
- **Models:** sub-agents can mix models across harnesses and models, including OpenRouter. This is the exact "main on one model, sub-agents on others" pattern from ruling 62.
- **Subscriptions:** you bring your own, and harnesses call the providers directly.
- **Pricing:** the free plan includes 100 cloud agents per 30 days. Pro is $50/month, Ultra $500/month.
- **Self-hosting:** the Rust core runs on a Linux VM with PostgreSQL. Packaging is still in progress.
- **Fit:** it is an agent host plus a dashboard, like Amp. Under the Rivet principle it runs the harness *inside* the sandbox, so treat it as a compute and placement option behind the engine's WorkerPort, not as QMX's engine.
