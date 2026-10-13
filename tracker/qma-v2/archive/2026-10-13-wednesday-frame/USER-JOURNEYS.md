---
title: QMA v2 user journeys
status: draft (for the operator's review)
created: 2026-10-12
inputs: PRD.md; research 21, 22, 26 §2 §5, 27 §2 §6; qmx-internal.md §a; clippings on harness/loop/graph, the self-improving quant loop, "The Loop Runs While You Sleep", "Not every workflow needs AI"
---

# QMA v2: user journeys

## 0. How to read this

- **What this is.** 21 end-to-end journeys of one day-to-day user, Mubarak, through QMA v2. Each journey says what starts it, what he does, what he sees, what runs underneath, where it runs, which PRD FRs it exercises, how it fails, and what the DevOps lens records.
- **Words.** Glossary words from PRD §6 are used exactly: copilot, errand, plugin, seat, engine (Claude engine, OpenAI engine), SIWC, router, account, workflow, mini app, rented compute, placement, run record, four axes, variant.
- **The screen** (qmx-internal §a.1). The desk has the errands sidebar on the left (Needs you, Working, Earlier), one errand in the centre (goal sentence, step track, chat, a "What it did" receipt behind each reply), and a **drawer** on the right with five tabs: **Activity**, **Artifacts**, **Diff**, **Terminal**, **Browser**. A pending question or approval takes over the composer. Home has "Needs you" and "Going on".
- **Chat blocks** the UI can draw (qmx-internal §a.1): `text`, `plan`, `agents` (sub-agent cards), `tools` (tool calls), `artifact`, `table`, `cards`, `ask`, `permission`, `changes`, `handoff`.
- **"Machinery"** in each journey names the engine, plugin, router decision, and the loop or graph used. Template numbers (T#) refer to the catalogue in research 22 §3.
- **Money rule, always.** Agents propose; they never place, size or cancel an order or touch the kill switch (C-11, FR-102). Nothing below breaks it. The self-improving quant loop clipping has its loop send orders; QMX keeps that one step human.
- Section 3 ideas are **Claude's proposals**, not decisions.

### 0.1 Cast of moving parts

| Part | Plain meaning | Default |
|---|---|---|
| General copilot | The desk copilot, like Claude Code or Codex; the only seat that edits apps | Claude engine, Opus, his Max plan |
| Lab / Portfolio copilots | Plugins with their own tools, skills and hooks | Claude engine; can be moved to a key provider |
| App copilot | A mini app's plugin; can use the app, never edit it | per app |
| Orchestrator | A Claude session kept alive for days with a state file, delegating to other models | Claude engine |
| Workers / sub-agents | Bounded helpers with their own model, scope and tools; depth 1 | per role default; GPT via SIWC or key providers |
| Graph runner | QMX's own runner for `workflow.v1` graphs; nodes are code by default | his PC or rented compute |
| Router | Picks account and model per session or spawn, never per request | capability first, then usage left |

---

## 1. Journey map

| # | Journey | Trigger | Main surfaces | Runs on | Pri |
|---|---|---|---|---|---|
| J01 | First run out of the box (vanilla) | He opens QMX for the first time | Setup checklist, desk | His PC | WED |
| J02 | The morning copilot chat | 07:00, he opens the desk | Home, desk, drawer | His PC (+ fetched remote results) | WED |
| J03 | Switching model mid-chat when Claude runs low | Usage chip turns amber | Desk, cost pop-up | His PC | NEXT |
| J04 | Building a mini app from an idea | "Make me an app that..." | Desk, Diff, Terminal, Artifacts | His PC | WED |
| J05 | Maintaining and editing a mini app | Breaker trips overnight / he asks for a change | Apps detail, desk | His PC | WED |
| J06 | Building a workflow by chat; save, edit, re-run | "Every time I finish a strategy..." | Desk, Lab graph view | His PC | WED |
| J07 | Mixed workflow: no-AI monitor wakes an agent on change | "Watch gold news; tell me only if it matters" | Lab, Home, phone | Rented compute | WED |
| J08 | A cron job | "Every weekday at 06:30..." | Desk, schedules | Rented compute | NEXT |
| J09 | Long Lab experiment loop, laptop closed, checked from phone | "Find me a variant that passes these tests" | Lab, Activity, phone | Rented compute | WED (off-machine) / NEXT (goal loop) |
| J10 | Claude orchestrator delegating to GPT and GLM workers | A multi-part build job | Desk, sub-agent cards | His PC | NEXT |
| J11 | A sub-agent team | "Compare these four optimisers" | Desk, sub-agent cards | His PC | WED |
| J12 | Research with citations | "What does the literature say about..." | Desk, Browser, Artifacts | His PC | NEXT |
| J13 | A Portfolio proposal he signs | "Should this bot join the pod?" | Portfolio, signing panel | His PC | NEXT |
| J14 | Video to backtest to cTrader demo, with computer use | He pastes a video link | Desk, Browser, computer-use view | His PC only | LATER |
| J15 | Self-improvement: a lesson becomes a gated skill change | The same correction twice | Desk, skill diff, approval | His PC | NEXT |
| J16 | The usage page | He wants to know what's left | Usage page | His PC | NEXT |
| J17 | Approvals from his phone | A gate fires while he's out | Phone | Phone + rented compute | NEXT |
| J18 | Two agents editing the same thing | Two errands touch one strategy | Diff (variants) | Both | NEXT |
| J19 | A crash and resume | Windows Update reboots the PC at 03:00 | Restart banner, Activity | His PC | WED |
| J20 | Adding a new provider | "Add Kimi with my key" | Settings, model providers | His PC | WED |
| J21 | Adding or installing a plugin | "Install this plugin" / "make one" | Settings, desk | His PC | NEXT |

---

## 2. The journeys

### J01 · First run out of the box (vanilla)

**Trigger:** QMX starts for the first time on his PC. Nothing is configured.

| # | Step | What the UI shows |
|---|---|---|
| 1 | QMX creates its own home (plugins, skills, settings, memory), apart from his personal Claude Code, and puts bulk data on D: | Setup checklist: "QMX home: D:\QMX-data ✓, your own Claude settings untouched ✓" |
| 2 | He signs in to his Claude plan himself through the Claude engine's sign-in. QMX never sees the token | Checklist row "Claude (Max plan): signed in"; no key field anywhere |
| 3 | Optional: Sign in with ChatGPT. If SIWC can't drive QMX, GPT shows "unavailable", never a paid API | Row "GPT: unavailable (reason)" or "signed in" |
| 4 | Three default plugins load (general, Lab, Portfolio) with their skills; the default always-ask list is shown once | "Copilots" card: three seats, model, skills chips; "Always ask me before: publish, install, schedule, spend over budget, demo-account actions, delete" with Edit |
| 5 | A smoke check runs and lists what works today and what returns `not_implemented` | "What works today" card, honest greys |
| 6 | He types "what can you do?" The general copilot answers in a stream with at least one tool call (capability registry) | Chat streams; `tools` block shows `capabilities.list`; drawer Activity is empty |

- **Machinery:** Claude engine, general plugin, QMX's own short system prompt (no CLAUDE.md loaded). Router has one account row. No graph.
- **Runs on:** his PC.
- **FRs:** FR-001, FR-013, FR-022, FR-023, FR-031, FR-032, FR-035, FR-096, FR-105, FR-124, FR-129, FR-132; NFR-034.
- **Failure paths:** Claude not signed in, so the copilot shows a "sign in to your Claude plan" card instead of crashing; low free RAM lowers the Claude session cap and says so (FR-141); C: nearly full blocks the data folder choice with a fix-it; a default plugin fails its lint and loads in safe mode with the reason.
- **DevOps lens records:** QMX version and plugin hashes, smoke results per package, account rows (no secrets), session cap computed from RAM.

### J02 · The morning copilot chat

**Trigger:** 07:00. He opens QMX and dictates a long, noisy brain dump.

| # | Step | What the UI shows |
|---|---|---|
| 1 | Home shows what happened overnight | "Needs you" (2 approvals, 1 assumptions card), "Going on" (3 errands, 1 remote job with cost so far) |
| 2 | He opens the desk. Remote results were fetched while QMX started | Errand list; each overnight errand has a "What it did" receipt and an "Assumptions to confirm" card |
| 3 | He dictates; the copilot restates the goal in one sentence before acting | Errand header: goal sentence, step track; `ask` block only if a real decision is needed, with a recommendation |
| 4 | "Why did the gold sweep stop?" The copilot reads the run index and opens the evidence | `tools` block (`runs.get`, `artifacts.open`); drawer Artifacts shows the sweep report; it quotes numbers from tool output only |
| 5 | "Check my paper pods' exposure to gold from here" (cross-surface read) | Portfolio read tools run without asking; any Portfolio write raises a `permission` card |
| 6 | He starts three errands at once: build an app, draft a workflow, research a paper | Three new errands under "Working"; Activity lists them with placement and Stop; the chat stays live |

- **Machinery:** Claude engine, general plugin, resumed session (cache warm: stable prefix). Router keeps this chat on Claude account 1 for its whole life. Background errands are separate sessions the router places by capability, then usage left.
- **Runs on:** his PC; remote results fetched Git-style.
- **FRs:** FR-003, FR-004, FR-005, FR-010, FR-012, FR-013, FR-014, FR-015, FR-018, FR-019, FR-039, FR-044, FR-091, FR-097, FR-113, FR-121, FR-126, FR-127, FR-130; NFR-024, NFR-032.
- **Failure paths:** Claude window exhausted, so a new session is refused with an error card and J03 is offered (FR-048); a fetch fails a hash check and the artifact is quarantined (FR-113); dictation misheard ("gold" as "old") is caught by the goal sentence before any tool runs; switching UI focus does not change a running errand's target (FR-003).
- **DevOps lens records:** first-event latency, cache-read ratio per turn (NFR-004), errands started, fetched runs and hash results.

### J03 · Switching model mid-chat when Claude usage runs low

**Trigger:** The usage chip on the composer turns amber: "Claude 5-hour window: 8% left, resets 11:40". Or he simply says "move this chat to GPT".

| # | Step | What the UI shows |
|---|---|---|
| 1 | He opens the model picker on this errand | Picker lists models from account rows with usage left and reset time; GPT greyed if SIWC is off |
| 2 | He picks GLM (key lane) | **Cost pop-up:** "This chat is 92k tokens. On GLM it is re-read without cache: about $0.21 now, then about $0.03 per turn. GLM's window is 128k, so QMX will compact first. You lose: 1 Claude-only hook (listed). Keep going?" |
| 3 | He confirms. Compaction runs on the old engine first | Chat shows a `changes` line "Compacted: 92k to 14k; kept: goal, decisions, open questions, artifact paths" (expandable) |
| 4 | A new session starts on the OpenAI engine, same errand, thinking effort mapped | Errand header: engine badge changes; the errand now lists two sessions in its history |
| 5 | Work continues; at 11:40 a quiet chip says "Claude reset; switch back?" | Chip only; nothing moves until he clicks |

- **Machinery:** both engines behind one contract; compaction policy per engine; effort mapping per wire format. The router never switches a running session by itself; only he does (K-11).
- **Runs on:** his PC.
- **FRs:** FR-020, FR-024, FR-025, FR-026, FR-039, FR-040, FR-045, FR-047, FR-048, FR-097, FR-098, FR-099, FR-126.
- **Failure paths:** compaction fails, so the switch is cancelled and the chat stays on Claude; the target model lacks tool calling, so the picker hides it for agent use; GPT via SIWC unavailable, so it's shown greyed with the reason, never routed to a paid API (FR-023); the new provider returns 400 on an effort setting, so the session retries once at the default effort and logs the mapping fault.
- **DevOps lens records:** switch event (from/to, reason, tokens before/after, estimated cost of cache loss), compaction summary hash, parity gaps shown.

### J04 · Building a mini app from an idea

**Trigger:** "Every morning before London opens, tell me if gold broke the Asian-session high, with a small chart, and keep a history."

| # | Step | What the UI shows |
|---|---|---|
| 1 | The general copilot loads the build-mini-app skill and asks one question with a recommendation (data source) | `ask` card: "Use your cTrader read feed (recommended) or the free CSV source?" |
| 2 | It writes a plan: headless job + one screen + own database; risk class "Shows things" | `plan` block (checklist); errand step track fills |
| 3 | It writes the app definition, tools, schedule and tests | Drawer **Diff**: new files; **Terminal**: `uv sync`, `pytest` streaming |
| 4 | Tests fail once; the review-repair loop fixes them (max 5 rounds) | `tools` blocks per round; "Round 2 of 5: 1 test failing (timezone)" |
| 5 | It proposes the screen as a panel description | Drawer **Artifacts**: live preview with demo data labelled; Keep / Throw away / Pin to Lab |
| 6 | Publish to Sandbox is on the always-ask list | `permission` card bound to the app's hash: Allow once / Not now |
| 7 | The app runs on recorded data, then moves to Shadow | Apps page: card in "Proving itself", five-step track, budget, health dot; card shows "Built by errand: Asian-high watcher" |

- **Machinery:** Claude engine, general plugin (only the general copilot edits apps). Optional sub-agent writes tests on a key provider. Loop: T10 review-repair-validate with a deterministic checker (tests). Graph: none; the app's own job is a one-node schedule.
- **Runs on:** his PC; the app runs as its own subprocess with its own venv and limits, no Docker.
- **FRs:** FR-010, FR-035, FR-055, FR-063, FR-072, FR-073, FR-074, FR-075, FR-076, FR-077, FR-078, FR-079, FR-080, FR-082, FR-084, FR-103, FR-104, FR-109.
- **Failure paths:** manifest declares a network host it didn't need or any money tool, so the publish gate refuses with a named reason (FR-077); tests still red after 5 rounds, so it stops with a named blocker, not "done" (FR-109); a "done" claim without a test artifact is labelled unverified; dependency install fails and the Terminal shows the error with a fix-it.
- **DevOps lens records:** definition hash, builder errand ID, test evidence per road step, per-app budget, breaker state, log tail.

### J05 · Maintaining and editing a mini app

**Trigger A:** 03:10, the Asian-high watcher's breaker trips (the data source changed a column name). **Trigger B:** later, he asks "add a Telegram alert when it breaks".

| # | Step | What the UI shows |
|---|---|---|
| 1 | Home "Needs you": "It stopped itself" | App detail: breaker reason, last log lines, Restart, "Ask the copilot why" |
| 2 | He clicks "Ask the copilot why". The app's own copilot reads logs and data; it cannot edit | Side chat; `tools` (`app.logs`, `app.data.peek`); a `handoff` block: "Change request created" |
| 3 | The general copilot picks up the change request (T22 investigate then remediate) | New errand linked to the app; diagnosis in `text`; fix proposed in **Diff** |
| 4 | The fix lands as a new version at Build, never a hot patch; tests re-run automatically | Apps card shows v1 (stopped) and v2 (Tests); **Terminal** shows tests |
| 5 | Trigger B: the Telegram edit opens v3 as a draft; the approval for v2 is asked again because the revision changed | `permission` card names v3's hash; old approval marked "for v2 only" |
| 6 | Downstream check: another app reads this app's output; v3's output type still matches | `changes` line: "Checked 1 consumer: types match" |

- **Machinery:** app copilot (use only) hands off to the general copilot (authoring). Claude engine. Loop: T22 then T10. Hooks route the files and verify the write.
- **Runs on:** his PC.
- **FRs:** FR-008, FR-010, FR-055, FR-058, FR-060, FR-072, FR-073, FR-074, FR-076, FR-077, FR-078, FR-080, FR-103.
- **Failure paths:** the change breaks a consumer's input type, so it's rejected before any run (FR-055); the fix passes tests but fails Shadow, so it rolls back to v1 with evidence; the app-use copilot tries an edit tool, so it's refused and a change request is made instead (FR-008).
- **DevOps lens records:** breaker trip reason and time, change-request artifact, version lineage v1 to v3, watcher and builder errand IDs.

### J06 · Building a workflow by chat; save, edit, re-run

**Trigger:** "Every time I finish a strategy, backtest it on EURUSD, GBPUSD and XAUUSD, run a walk-forward on the best, and give me a one-page verdict."

| # | Step | What the UI shows |
|---|---|---|
| 1 | The copilot loads build-workflow, picks a template (T6 fan-out and synthesize plus T1 chain with gate) | `plan` block naming the template; "Start from template" link |
| 2 | It writes a `workflow.v1` graph: 3 parallel backtest nodes (code), gate (code), walk-forward (code), verdict (agent node with a schema checker) | Drawer **Artifacts**: Graph view of the JSON; node badges "code" or "agent" |
| 3 | Validation rejects it once: a loop has no maximum | `changes`: "Fix-it: loop 'retry-data' needs a max; set to 3" |
| 4 | He says "run it on my London-breakout strategy" | Activity: run with node progress; drawer **Terminal** per code node; three branches run side by side |
| 5 | XAUUSD's data fetch fails; the other two branches keep their results; the join's merge rule reports 2 of 3 | Graph view: one red node with the error; verdict card says "2 of 3 symbols" |
| 6 | Edit while running: "add a Monte Carlo step". The run finishes on the old hash; the edit is a draft | Two hashes shown: "running v1", "draft v2" |
| 7 | He saves v2 and re-runs. It is now callable by name from any chat and from apps | Workflow card: "Call it: run_workflow('strategy-verdict')"; ledger shows zero model calls for code nodes |

- **Machinery:** Claude engine for authoring; graph runner for the run; the verdict agent node runs on a key provider set as this workflow's default. Agent node is a loop with stop rule (pass, max 3, budget) and a deterministic schema checker.
- **Runs on:** his PC (backtests go through the QMB seam).
- **FRs:** FR-042, FR-052, FR-053, FR-054, FR-055, FR-056, FR-057, FR-058, FR-059, FR-060, FR-061, FR-062, FR-063, FR-064, FR-066, FR-067, FR-068, FR-121, FR-129, FR-132.
- **Failure paths:** QMB seam not ready, so the node returns `not_implemented` honestly (FR-129); port type mismatch rejected before the run (FR-055); fan-out over 50 symbols hits the code-driven cap and asks to raise it (FR-061); verdict agent says "done" without passing the schema, so it loops or stops with a blocker (FR-063).
- **DevOps lens records:** definition hash per run, per-node timing and status, model calls per node (zero for code), four axes, the failed branch and its retry count.

### J07 · Mixed workflow: a no-AI monitor that wakes an agent only on change

**Trigger:** "Watch the economic calendar and cTrader news for gold. Only bother an agent if something changed, and only bother me if it matters for my paper pods."

| # | Step | What the UI shows |
|---|---|---|
| 1 | The copilot builds a graph from T19 scheduled brief and T18 quarantine triage | Graph: trigger (every 5 min) → fetch (code) → diff against bookmark (code) → condition "changed?" → agent assess → checker (code) → post (code) → record (code) |
| 2 | It explains the cost shape before saving | `cards` block: "~288 checks a day at $0. Agent wakes only on change: estimate 3-8 wakes, ~$0.05 a day" |
| 3 | Scheduling is on the always-ask list; he allows it; placement defaults to rented compute | `permission` card; job card "Runs on: rented (provider), always on" |
| 4 | 14:02: an FOMC headline appears; the diff fires; a read-only agent assesses it against his pods' exposure | Home "Going on" pulse; run view: the agent node has no write tools; its quote links back to the source item |
| 5 | The checker confirms every cited headline exists in the fetched data; post goes to Home and his phone | Phone notice: "Gold: FOMC minutes at 19:00. Your weekend pod is 40% gold. Want a stress test?" |
| 6 | A source read fails at 15:10; it is reported as a failure, never a quiet day | Home: "News feed unreadable since 15:10" (red), not silence |

- **Machinery:** graph runner; one agent node (key provider, read-only, untrusted-input reader); everything else code. Loop: the cron is the heartbeat; the agent node loops at most twice on its checker.
- **Runs on:** rented compute (long-running by design); fetched results flow back.
- **FRs:** FR-053, FR-054, FR-061, FR-063, FR-070, FR-071, FR-110, FR-112, FR-115, FR-121, FR-140; NFR-017.
- **Failure paths:** a burst of 40 headlines in a minute wakes the agent 40 times unless a debounce exists (gap, see §3 idea 6); overlapping triggers are skipped per policy (FR-071); the agent invents a headline, so the checker fails and nothing is posted; rented machine dies, so the next tick runs on the fallback provider.
- **DevOps lens records:** checks run, wakes, tokens per wake, zero-token runs, failed reads, placement and cost per day.

### J08 · A cron job

**Trigger:** "Every weekday at 06:30 London time, make my morning brief: overnight runs, pod exposure, calendar, and anything that needs me."

| # | Step | What the UI shows |
|---|---|---|
| 1 | The copilot creates a schedule entry pointing at a workflow (a schedule triggers work; the workflow is the work) | `plan`: "Schedule: Mon-Fri 06:30 Europe/London (BST/GMT handled)" |
| 2 | He grants its authority at launch: read everything, write only the brief | `permission` card listing exactly what it may do; no questions later |
| 3 | 06:30: it runs remotely, resumes its last session's bookmarks, re-checks facts, writes the brief | Activity at 06:30 (if he's up); otherwise nothing until he opens QMX |
| 4 | The brief lands in the errand that set it, with an assumptions card | Errand: brief artifact plus "Assumptions to confirm: treated Monday's holiday as a trading day" |
| 5 | He edits the schedule ("make it 06:00") in Settings or by chat | Schedule row edited; next run time shown |

- **Machinery:** QMX scheduler; graph (T19); one agent node on a key provider; resumed reviewer pattern (T20) for continuity. Unattended: deny by default, no questions.
- **Runs on:** rented compute (default for cron), configurable.
- **FRs:** FR-018, FR-070, FR-071, FR-108, FR-110, FR-115, FR-119, FR-121.
- **Failure paths:** his usage limit is hit, so the run refuses and the brief says so (FR-071); a deny-listed call is refused even with "allow all" (FR-108); the run is missed because the provider was down, so the policy for missed runs is needed (gap, §3 idea 14).
- **DevOps lens records:** schedule ID, each run's start, end, cost, placement, skipped or missed runs and why.

### J09 · A long Lab experiment loop on rented compute, laptop closed, checked from his phone

**Trigger:** "Find a mean-reversion variant on EURUSD M15 with out-of-sample Sharpe above 1.2 after costs that survives the noise test and walk-forward. Budget $25 compute, two days. Stop if three rounds bring nothing."

| # | Step | What the UI shows |
|---|---|---|
| 1 | The Lab copilot writes the goal, evidence and stop rule as a goal loop and shows a pre-flight estimate | `cards`: Goal / Evidence (OOS Sharpe, noise test, walk-forward, trials counted) / Stop (pass, 3 flat rounds, $25, 48 h) / Estimate |
| 2 | He approves placement and spend; a rented machine is set up idempotently and verified | `permission` card; Activity: "Provisioning (provider) ... verify passed" |
| 3 | Each round: a proposer agent changes the search space (signals, filters, fitness); code runs the sweeps; code runs the checks; a state file records the round | Lab run view: round strip; per round: candidates tried, best so far, evidence status |
| 4 | Negative results are written as records, and memory points at them, so dead ends aren't retried | Round card: "Dropped volatility filter: no effect on 3 rounds (record #...)" |
| 5 | He closes the laptop. The loop keeps running on rented compute and uploads journal, logs and checkpoints incrementally | Nothing local; the job is visible from his phone |
| 6 | From his phone at lunch: status, cost so far, best candidate, and one approval ("round 6 wants $5 more") | Phone: job card with placement, $14.20 of $25, live log tail, Allow / Not now |
| 7 | Stop rule fires (3 flat rounds). The machine is torn down. When the laptop opens, results are fetched and hash-checked | Lab: final evidence card, trial count, code changes on a `runs/<id>` branch; machine shown "torn down" |

- **Machinery:** goal loop over a graph. The orchestrator role needs a home while the laptop is closed: if the Claude plan can't sign in on a rented Linux box (A-02), the loop is driven by an OpenAI-engine orchestrator on a key provider, or by the graph itself with agent nodes only for proposals. Workers on key providers. Checker is deterministic (QMB walk-forward, noise test, Monte Carlo permutation). "The model proposes; the checks decide." USD cap pauses, never fails.
- **Runs on:** rented compute, several providers possible; results come back Git-style.
- **FRs:** FR-016, FR-051, FR-059, FR-063, FR-065, FR-070, FR-093, FR-101, FR-110, FR-111, FR-112, FR-113, FR-114, FR-116, FR-119, FR-121; NFR-010.
- **Failure paths:** spot machine pre-empted, so the run resumes elsewhere from the last checkpoint; budget hit, so it pauses and asks; overfitting by brute force (thousands of trials) is invisible unless trials are counted (gap, §3 idea 7); the machine is left running after the stop, costing money (gap, §3 idea 5); Claude orchestrator can't run remotely (A-02), so the plan must say "needs your PC on" before he closes the lid.
- **DevOps lens records:** rounds, trials, best evidence per round, compute minutes and USD per provider, placement history, checkpoint IDs, teardown confirmation.

### J10 · The Claude orchestrator delegating to GPT and GLM workers

**Trigger:** "Port my six old MQL5 indicators into QML, write tests for each, and tell me which ones differ from the originals."

| # | Step | What the UI shows |
|---|---|---|
| 1 | The orchestrator reads router data as tools: models, usage left, strengths | `tools`: `models_status`; `text`: "GPT for porting (code strength), GLM for tests (usage left high)" |
| 2 | It delegates six port jobs to GPT via SIWC and six test jobs to GLM, cross-engine | `agents` block: 12 cards with model, provider, engine badge, where, tokens, Stop |
| 3 | Workers return compact JSON plus usage and artifact references, never long text | Each card ends with an artifact chip; drawer **Diff** shows ported files |
| 4 | It reviews each against the original output on the same data (deterministic comparison) | `table`: indicator, max difference, pass/fail |
| 5 | One worker hits a 429; the next job goes to the fallback; the running one isn't switched | Card: "GPT limit, job 5 moved to DeepSeek at the next task boundary" |
| 6 | The ad hoc plan is offered as a saved workflow ("port-and-verify") | `handoff`: "Save as workflow?" Graph preview in **Artifacts** |

- **Machinery:** orchestrator on the Claude engine; delegate plugin across engines; workers on the OpenAI engine (SIWC and key lane). Router chooses per spawn. Pattern T5 manager with specialists plus T8 orchestrator-workers.
- **Runs on:** his PC (OpenAI-engine workers run in-process; light on RAM).
- **FRs:** FR-020, FR-021, FR-023, FR-026, FR-029, FR-034, FR-041, FR-043, FR-064, FR-065, FR-084, FR-085, FR-086, FR-109, FR-120.
- **Failure paths:** SIWC unavailable, so GPT jobs go to the next capable model and the card says so; a worker claims "ported" with no test artifact, labelled unverified (FR-109); a worker repeats the same call three times and is stopped; the orchestrator's context grows, so it compacts and re-reads its state file.
- **DevOps lens records:** per-worker resolved model, engine, account, tokens, USD, duration; traces stored locally, never uploaded.

### J11 · A sub-agent team

**Trigger:** "Compare four portfolio optimisers (equal risk, HRP, Kelly-capped, min-variance) on my three pods. One page."

| # | Step | What the UI shows |
|---|---|---|
| 1 | The copilot sizes the team (4 workers, not 10) and writes each a full brief | `plan`; `agents` block with 4 cards, each showing its own model and tool list |
| 2 | Workers run in the background; the chat stays live; each worker gets only its task, not the chat history | Activity: 4 rows with progress; cache life warning if any would idle over ~10 min |
| 3 | One worker tries to spawn its own helper; refused at depth 1 | Card: "Spawn refused (depth limit)"; the worker continues alone |
| 4 | One hangs; the watchdog restarts it | Card turns amber, then "restarted" |
| 5 | Results come back as artifact references; the lead synthesises | **Artifacts**: comparison table and chart; each number links to its tool output |

- **Machinery:** sub-agents per one engine-neutral spec; their models are never overridden by the parent; fan-out (T6) with lead synthesis.
- **Runs on:** his PC; Claude sub-agents count against the RAM cap.
- **FRs:** FR-015, FR-028, FR-084, FR-086, FR-087, FR-088, FR-089, FR-100, FR-109, FR-123, FR-141; NFR-003.
- **Failure paths:** RAM cap reached, so the next Claude worker is refused with a card and the router offers an OpenAI-engine worker; a worker fails, the other three keep their results; numbers quoted by the lead that don't match tool output are flagged.
- **DevOps lens records:** team size, per-agent model and cost, spawn refusals, watchdog restarts (SC-C2 counter-metric: helpers spawned).

### J12 · Research with citations

**Trigger:** "What does the literature say about the overnight drift in gold? A memo with real citations, and tell me which claims are measured and which are opinion."

| # | Step | What the UI shows |
|---|---|---|
| 1 | The research template starts with hard caps: up to 5 researchers, 6 rounds, 10 tool calls each; idea generation kept apart from narrowing | `plan` showing the caps; `agents` cards |
| 2 | Firecrawl is paid and off by default; turning it on for this errand asks | `permission` card "Enable Firecrawl for this errand (paid)" |
| 3 | Researchers read pages and PDFs as untrusted input; readers have no write tools | Drawer **Browser** shows the page being read; **Activity** shows each researcher |
| 4 | A claim checker verifies each claim: the link resolves, the quote is in the source, the number matches | `table`: claim, source, check result; failed claims are dropped or marked |
| 5 | The memo labels each statement "measured" or "interpretation" | **Artifacts**: memo with numbered citations; "Save to Library" |

- **Machinery:** T29 research lead plus sub-agents, T12 deep verification. Key-provider researchers, Claude lead. Library through its seam.
- **Runs on:** his PC.
- **FRs:** FR-011, FR-066, FR-084, FR-088, FR-132, FR-133, FR-135, FR-136; NFR-017.
- **Failure paths:** paywalled source, so the claim is marked "source not readable"; a page contains instructions aimed at the agent, which are ignored and logged; the cap is reached before the question is covered, so the memo says what is missing.
- **DevOps lens records:** sources fetched, claims checked and failed, paid tool spend, injection attempts seen.

### J13 · A Portfolio proposal he signs

**Trigger:** "Should the London-breakout bot join the weekend-safe pod?"

| # | Step | What the UI shows |
|---|---|---|
| 1 | The Portfolio copilot reads the Lab evidence and the pod's rules | Portfolio side chat; `tools`: `risk.explain`, read-only broker tools |
| 2 | Sizing comes from the pod's own code rules, never from the agent | `cards`: before/after exposure, computed by code; agent text explains only |
| 3 | It prepares a promotion card with `propose_order`-style drafts only | Signing panel: proposal hash, evidence links, "Paper first" default |
| 4 | He signs. The signature binds to this exact revision; any edit asks again | Signature record; Portfolio "Promotions" moves the card to Paper |
| 5 | Probe: he asks it to "just place it". It can't, on either engine, whatever the settings | `text` refusal; Journal shows the refused call |

- **Machinery:** Portfolio plugin (default posture: plan first). No order tool exists in its tool list; the block lives in QMX wrappers on both engines.
- **Runs on:** his PC.
- **FRs:** FR-002, FR-005, FR-058, FR-102, FR-104, FR-106, FR-107, FR-109, FR-138; NFR-015.
- **Failure paths:** the evidence is older than the strategy's current hash, so the card says "stale evidence" (gap, §3 idea 16); a number in the card differs from tool output, so the card is blocked; a live-account write is refused (FR-107).
- **DevOps lens records:** proposal hash, evidence hashes, signature time, refused money calls.

### J14 · Video to backtest to cTrader demo, with computer use

**Trigger:** He pastes a YouTube link: "Watch this London-breakout video, backtest it, then try it on my cTrader demo."

| # | Step | What the UI shows |
|---|---|---|
| 1 | A read-only sub-agent watches the video (frames plus transcript) and extracts rules | `agents` card; **Artifacts**: "Rules found" list with timestamps |
| 2 | He confirms the rules (one ask, with the ambiguous rule flagged) | `ask` card |
| 3 | The copilot writes the strategy; a hook puts it in the strategies folder and checks it landed | **Diff**; `changes`: "Written to strategies/london_breakout.py ✓" |
| 4 | Backtest via the QMB seam | **Artifacts**: equity curve and stats |
| 5 | Demo try: computer use drives cTrader on his PC without taking his mouse; the demo action asks first | Computer-use view with the agent's cursor; `permission` card "Demo account 123: place 0.01 lot test" |
| 6 | Before each click the account is re-checked as demo; a live account in view stops everything | `changes`: "Account check: demo ✓" per action |

- **Machinery:** Claude engine copilot; video tool from the baseline; QMX-owned computer use. Windows-only, so it stays on his PC.
- **Runs on:** his PC only (FR-117).
- **FRs:** FR-084, FR-103, FR-107, FR-117, FR-126, FR-132, FR-133, FR-137, FR-139; NFR-017.
- **Failure paths:** no captions, so transcription falls back to speech-to-text; cTrader's layout changed and clicks miss, so it stops and shows a screenshot; the live account is logged in, so it hard-stops (gap, §3 idea 10).
- **DevOps lens records:** video source, extracted rules hash, each computer-use action with screenshot reference, account check results.

### J15 · Self-improvement: a lesson becomes a gated skill change

**Trigger:** For the second time this week he corrects the Lab copilot: "M15 fills must use the next bar's open, not the signal bar's close."

| # | Step | What the UI shows |
|---|---|---|
| 1 | The copilot saves the correction as a lesson proposal, not a rule | `changes`: "Lesson proposed: next-bar-open fills (seen twice)" |
| 2 | A weekly mining run clusters corrections and asks of each "would it have prevented a real mistake?" | Lessons list in Settings, each with its evidence |
| 3 | The lesson becomes a skill draft with trigger tests | **Diff**: the skill's new section |
| 4 | An eval runs the skill against "no skill" and the current version on held-out prompts | `table`: pass rates with and without, noise band |
| 5 | He approves; the skill activates as a new version; undo restores the old one | `permission` card with the diff; Settings: skill v4 active, "Undo to v3" |

- **Machinery:** T33 session mining to rules, T32 eval builder, T31 hillclimb. Fake engine for evals in CI; live evals by operator script.
- **Runs on:** his PC (mining can run remote).
- **FRs:** FR-036, FR-037, FR-092, FR-094, FR-125, FR-142; NFR-015.
- **Failure paths:** the draft doesn't beat "no skill", so it can't activate; the lesson conflicts with a money-path rule, so it is refused outright; it improves one task and breaks another, caught by the held-out set.
- **DevOps lens records:** lesson source sessions, skill version, eval scores, approver and time, rollback pointer.

### J16 · The usage page

**Trigger:** He wants to know what's left before starting a big job.

| # | Step | What the UI shows |
|---|---|---|
| 1 | He opens Usage | One row per account: Claude (5-hour window and weekly), ChatGPT plan, each key provider in USD, pools |
| 2 | Each row shows limit, used, reset time and which errands use it | Bars plus "resets in 1 h 40"; top consumers this week |
| 3 | A graph shows tokens over time and cache savings | Line chart; "Cache saved ~61% of input this week" |
| 4 | He edits limits: per job, per turn, per day | Inline edits; "A job over its USD cap pauses, it doesn't fail" |
| 5 | Numbers QMX can't read from a documented source are labelled estimates | "Estimated (from local session files)" tag |

- **Machinery:** QMX usage ledger plus local session files; documented sources only; router reads the same data.
- **Runs on:** his PC.
- **FRs:** FR-038, FR-040, FR-048, FR-049, FR-050, FR-051; NFR-005, NFR-006.
- **Failure paths:** a provider reports no usage, so the row shows "estimated"; a reset time is unknown, so it says "unknown", never a guess.
- **DevOps lens records:** the ledger itself; limit changes with who and when.

### J17 · Approvals from his phone

**Trigger:** He's out. J09 asks for $5 more; J08 needs a new permission; a mini app wants to publish.

| # | Step | What the UI shows |
|---|---|---|
| 1 | A notice reaches his phone with a plain card and a recommendation | "Lab loop wants $5 more (now $14.20 of $25). Recommend: yes, round 5 improved Sharpe 0.9 to 1.1" |
| 2 | He taps Allow once. The approval binds to that exact request and revision | "Allowed at 12:41" |
| 3 | The rented machine picks the answer up and continues | Phone card turns green: "Resumed" |
| 4 | A signature for a money proposal is not offered on the phone | "Open QMX on your PC to sign" |
| 5 | Back home, the desk shows what was approved from the phone | Journal rows tagged "from phone" |

- **Machinery:** the one approval queue; a relay so a rented machine and a phone can meet without QMX owning a server.
- **Runs on:** phone plus rented compute; his PC may be off.
- **FRs:** FR-058, FR-104, FR-106, FR-112. No FR covers the phone itself (see §4.2).
- **Failure paths:** the phone link is forwarded or stolen, so approvals need device binding and expiry; the relay is down, so the run parks and waits, never guesses; an approval arrives after the request expired, so it is ignored and logged.
- **DevOps lens records:** approval source (desk or phone), latency from ask to answer, expired asks.

### J18 · Two agents editing the same thing

**Trigger:** His errand is tuning the London-breakout strategy while the weekly maintain job edits the same file.

| # | Step | What the UI shows |
|---|---|---|
| 1 | Each agent works on its own git branch in its own worktree | Activity: two jobs, each with a branch name |
| 2 | Both finish; QMX keeps both as variants | Drawer **Diff**: side-by-side variants A and B with Comment and Revert |
| 3 | He asks "which is better?" The same backtest runs on both | `table`: variant, Sharpe, drawdown, trades |
| 4 | He keeps B, or asks the copilot to merge the parts he likes | `permission` to merge; the losing variant is archived, not deleted |

- **Machinery:** git branches per agent; variant model; T7 best-of-N for the comparison.
- **Runs on:** both his PC and rented compute (a remote run's changes arrive on `runs/<id>`).
- **FRs:** FR-113, FR-131, FR-143.
- **Failure paths:** a merge conflict, so the copilot proposes a resolution and asks; both agents edit an app definition, so each becomes its own version (FR-073); a Library item is edited by two agents, which goes through the Library's lock seam.
- **DevOps lens records:** branches, variant pairs, which was kept and why.

### J19 · A crash and resume

**Trigger:** 03:00, Windows Update reboots the PC. Three errands are running, a workflow is at node 7 of 12, an approval is pending, and a Claude session is mid-turn.

| # | Step | What the UI shows |
|---|---|---|
| 1 | QMX restarts with Windows | Banner: "QMX restarted at 03:14. 4 things resumed, 1 needs you" |
| 2 | The workflow skips its 6 finished nodes and re-runs node 7; its external write is not repeated | Run view: nodes 1-6 "cached", node 7 "re-run (idempotency key matched, no repeat)" |
| 3 | Each errand resumes its session by ID and reads its state file | Errands back under "Working" |
| 4 | Tool calls from the cut-off turn are not executed blindly | `changes`: "Last turn was cut off; 1 tool call skipped and re-planned" |
| 5 | The pending approval is still there | "Needs you": the same card, same revision |

- **Machinery:** node checkpoints, session resume plus state files, idempotency keys, truncated-reply guard, watchdog.
- **Runs on:** his PC (remote jobs kept running and are fetched).
- **FRs:** FR-014, FR-016, FR-017, FR-059, FR-061, FR-104, FR-109, FR-123; NFR-010, NFR-012.
- **Failure paths:** a checkpoint is corrupt, so it falls back to the previous one and says so; a database is locked, so it retries, then reports; a remote run moved on while the PC was down, so local and remote state are reconciled by fetch, never merged.
- **DevOps lens records:** restart time, resume time per item against the 60 s target, skipped tool calls, checkpoint fallbacks.

### J20 · Adding a new provider

**Trigger:** "Add Kimi. I have a key."

| # | Step | What the UI shows |
|---|---|---|
| 1 | The copilot opens Settings, Model providers, with a new row filled in (name, base URL, wire format) | Settings form; the copilot never asks for the key in chat |
| 2 | He types the key into QMX's own secure field; it goes straight to Credential Manager under `qmx/*` | Field shows "Stored in Windows Credential Manager"; nothing echoed |
| 3 | A probe runs: one tool call, streaming, context window, caching | Probe card: tools ✓, streaming ✓, window 256k, cache reported ✗ |
| 4 | He tags strengths and sets it as the default for the research template | Row tags; "Used by: research template" |
| 5 | Next session for that role goes to Kimi; no code changed | Usage page has a new row |

- **Machinery:** account rows; OpenAI engine by base URL plus key; router includes the new row by capability.
- **Runs on:** his PC.
- **FRs:** FR-024, FR-027, FR-038, FR-041, FR-042, FR-046; NFR-016, NFR-019.
- **Failure paths:** wrong wire format, so the probe fails with a fix-it; no tool calling, so it's marked "chat only" and kept out of agent roles; he pastes the key into chat anyway, so it must be redacted before any model sees it (gap, §3 idea 12).
- **DevOps lens records:** account row added (no secret), probe results, first session on it.

### J21 · Adding or installing a plugin

**Trigger A:** "Make a crypto-funding plugin for the Lab: funding-rate tools, a skill for basis trades." **Trigger B:** he drops a plugin bundle someone shared.

| # | Step | What the UI shows |
|---|---|---|
| 1 | The copilot writes the plugin (tools, skills, model, hooks) or reads the bundle | **Diff**: plugin folder |
| 2 | Lint runs: every tool a skill names exists; no money tools; hooks don't relax the deny-list | Lint card, pass/fail per rule |
| 3 | A "what it brings" card: tools, MCP servers it starts, network hosts, model, hooks | `cards` block |
| 4 | New tool code runs as a separate process and stays disabled until he reviews | Tools listed as "disabled until you review" |
| 5 | Install is on the always-ask list; he allows it and assigns it to a seat | `permission`; Settings, Copilots: new skill chips |
| 6 | It loads on both engines with the same tools and skills; tools past ~15 sit behind tool search | New session tool list; "+ 6 more via search" |

- **Machinery:** one plugin format; QMX's loader on the OpenAI engine; seats as data; bundle hash.
- **Runs on:** his PC.
- **FRs:** FR-007, FR-030, FR-033, FR-035, FR-081, FR-083, FR-100, FR-108, FR-134.
- **Failure paths:** a skill names a missing tool, so lint fails; a hook tries to allow a deny-listed call, refused; a plugin works on Claude but not on the OpenAI engine, so it's marked "Claude only" (gap: parity badge, §3 idea 13).
- **DevOps lens records:** plugin hash, lint results, install approval, seats using it.

---

## 3. Claude's spin: proposals for the operator

**These are proposals, not decisions.** Each came out of walking the journeys. Priorities are suggestions.

| # | Idea | Why it matters | Journeys | Proposed |
|---|---|---|---|---|
| 1 | **Restart banner and "while you were away" digest**: one card after any restart or long absence listing resumed, failed and waiting items | Crash-resume is invisible without it; he otherwise has to hunt | J19, J02 | WED |
| 2 | **Goal sentence from dictation**: the copilot restates his goal in one line before its first tool call | His input is long and noisy; one wrong word ("old" for "gold") wastes a run | J02, J04 | WED |
| 3 | **"What works today" card on first run**: smoke results plus every `not_implemented` in plain words | Honest vanilla; stops him finding gaps by accident | J01 | WED |
| 4 | **Remote loop needs a home**: before he closes the lid, the plan says "runs without your PC" or "needs your PC on", based on whether the Claude plan can sign in remotely (A-02) | J09 silently fails if the orchestrator lives on the laptop | J09, J07, J08 | WED |
| 5 | **Idle teardown and a "machines alive" chip**: rented machines stop after N idle minutes; the header shows how many are running and their cost per hour | No owned server means surprise bills are the main risk | J09, J07 | WED |
| 6 | **A "watch" node with debounce**: code compares against a bookmark, wakes the agent with only the difference, and caps wakes per hour | Makes the "no AI unless changed" pattern one node instead of five; stops news bursts burning tokens | J07, J08 | WED (as a template) |
| 7 | **Trial counter and multiple-testing guard**: every candidate tried is counted; the evidence card shows trials and a deflated Sharpe | Loops that test millions of variants find noise; this is the quant failure the "loop while you sleep" clipping warns about | J09, J15 | NEXT |
| 8 | **Negative-results ledger**: dead ends are records, retrieved before a new loop starts | Stops the next loop paying to relearn what failed | J09, J15 | NEXT |
| 9 | **Pre-flight estimate for any long run**: time, compute USD, and share of each subscription window | He decides with numbers; matches the cost pop-up of J03 | J09, J06, J11 | NEXT |
| 10 | **Demo lock for computer use**: before every broker click, read the account type through the read API; a live account in view hard-stops the run | Computer use can click whatever is on screen; the money rule must hold there too | J14 | NEXT (before FR-139 ships) |
| 11 | **Phone relay without a server**: approvals and status pass through a small paid push or bucket mailbox; device-bound, expiring links; no money signatures on the phone | J09 and J17 need it; "no owned server" rules out the obvious design | J17, J09, J07 | NEXT |
| 12 | **Key-safe chat**: a pasted key is detected and redacted before any model or log sees it, with a link to the secure field | Credential rule C-15 covers storage, not the moment he pastes | J20, J01 | WED |
| 13 | **Engine parity badge**: plugins, skills and sessions show "both engines" or "Claude only", and the switch pop-up lists what is lost | Switching engines silently drops hooks otherwise | J03, J21, J10 | NEXT |
| 14 | **Missed-run policy for schedules**: catch up, skip, or run elsewhere, chosen per schedule | Schedules on a sleeping PC or a dead provider just vanish today | J08 | NEXT |
| 15 | **Usage reserve**: "keep 25% of Claude for chat"; background work may not dip below it | Overnight errands otherwise eat the morning copilot | J03, J16, J10 | NEXT |
| 16 | **Stale-evidence warning**: a proposal or verdict shows when its evidence was made on an older strategy, data or app hash | Signing on old evidence is the worst silent error | J13, J05, J06 | NEXT |
| 17 | **Variant tournament**: when two variants exist, run the same test on both and show one comparison card | Turns a merge chore into a decision with evidence | J18 | NEXT |
| 18 | **Errand budget envelope**: a USD and subscription-share budget per errand, warning at 80% | Jobs have caps; errands that spawn many jobs don't | J09, J11, J10 | NEXT |
| 19 | **"Switch back at reset" chip**: after a forced switch, offer (never perform) the return to Claude at reset | Keeps him on his best model without the router switching sessions | J03 | NEXT |
| 20 | **Dry-run button**: run a workflow on the fake engine and recorded data at $0 before the real run | Cheap rehearsal; uses the fakes the tests need anyway | J06, J07 | NEXT |
| 21 | **"Re-run with this assumption fixed"** on every assumptions card | Unattended runs guess; correcting a guess should be one click | J08, J09, J02 | NEXT |
| 22 | **Plugin "what it brings" card and uninstall**: tools, hosts, hooks, model; uninstall and roll back by hash | Installing is covered; removing and rollback are not | J21 | NEXT |
| 23 | **Skill canary**: a new skill version runs beside the old one for N real tasks before it replaces it | Evals miss real-world cases; this catches them before they spread | J15 | LATER |
| 24 | **Node-by-node replay**: scrub a finished run's timeline and see each node's inputs, outputs and model calls | Makes "why did it do that?" answerable without reading raw logs | J19, J06, J09 | LATER |
| 25 | **Proposal cooling-off**: a money proposal can't be signed in the same minute it was generated; the revision diff is shown first | Slows the one irreversible step a little, on purpose | J13, J17 | LATER |

---

## 4. Coverage

### 4.1 PRD FRs no journey exercises

| FR | Why no journey touches it | Reading |
|---|---|---|
| FR-006 (no modes) | A code property, not a journey | Fine: structural check |
| FR-009 (stories as scenarios) | It is the instruction to turn journeys like these into headless scenarios | Fine: this file feeds it |
| FR-069 (WF1/WF2 later) | Out of scope until the Library and QMB return | Fine: LATER seam |
| FR-090 (RLM data-analyst sub-agent) | No journey needed it; J11 and J09 did their data work with code and QMB | **Possibly dead.** Recommend keeping it parked until a journey asks (A-10) |
| FR-095 (memory bake-off) | No journey needed a second memory provider | Fine: LATER; revisit if J15's lessons outgrow SDK memory |
| FR-118 (GPU jobs) | No journey trained a model | Fine: LATER; add a training journey when ML Studio returns |
| FR-144, FR-145 (shipping, branch clean-up) | Process for building QMX, not using it | Fine: process |
| FR-146 (database usable by agents) | Too vague to walk through; every journey reads data through tools | **Possible gap in wording:** restate as a testable FR once the architecture names the data API |
| FR-147 (voice) | He dictates through his own tools today | Fine: LATER |
| FR-148 (week-long paper soak) | No journey ran a soak | Fine: LATER; it is J09's shape with a monitor agent |

### 4.2 Journey steps no FR covers (missing requirements)

| Step | Journey | Proposed requirement |
|---|---|---|
| Phone notices, phone status view and phone approvals | J07, J09, J17 | A phone channel: notices, read-only job view, approvals bound to revision, device-bound and expiring; no money signatures |
| A relay for approvals while his PC is off, with no owned server | J17, J09 | Approval and status relay on rented or paid push infrastructure; the run parks if the relay is down |
| Where the orchestrator lives when the PC is off | J09 | Each long run declares whether it needs his PC; the UI says so before launch (depends on A-02) |
| Idle teardown and a running-machines cost view | J09, J07 | Auto-teardown after idle time; live count and cost per hour of rented machines |
| Missed schedule runs | J08 | A missed-run policy per schedule |
| Debounce and wake caps on monitors | J07 | Wake rate caps and debounce on change-triggered agent nodes |
| Secret pasted into chat | J20 | Redact detected secrets in chat input before any model, log or journal |
| Provider probe on add | J20 | A capability probe (tools, streaming, window, caching) that sets the row's allowed roles |
| Demo lock in computer use | J14 | Account-type check before every broker action through computer use |
| Trials counted in search loops | J09 | Every goal loop counts trials and reports a multiple-testing-adjusted metric |
| Pre-run cost and time estimate | J09, J06 | Long runs show an estimate before launch (FR-099 covers model switches only) |
| One errand, several engine sessions | J03 | The errand records its session lineage across engine switches |
| Signing versus approving | J13 | A signature record for money proposals, distinct from an approval, bound to evidence hashes |
| Restart banner | J19 | After restart, one summary of resumed, failed and waiting items |
| Plugin uninstall and rollback | J21 | Uninstall and roll back a plugin by hash; seats fall back to the default |
| Stale evidence | J13, J05 | Evidence cards name the hashes they were made on and warn when those changed |
| Usage reserve | J03, J16 | A per-account reserve that background sessions may not consume |

---

## 5. The Wednesday demo script (10 minutes)

**Goal:** prove SC-1 to SC-6 live, end to end, on his PC, with real engines. Slow steps start first and are shown when they finish.

**Before the demo (not timed):** QMX running on `rebuild/base`; Claude plan signed in; one key provider row (DeepSeek or GLM) added and probed; one rented provider set up and verified; fake data for Macro daily bias present; Usage page open in a second tab.

| Time | What he does | What he sees | Proves |
|---|---|---|---|
| 0:00 | In a new errand: "Run the 'gold-morning-check' workflow on rented compute." Then closes nothing; the job keeps going | Activity: job "Provisioning... running on (provider)", cost so far, log tail | SC-5 (started) |
| 0:45 | New errand: "Rebuild Macro daily bias from its paragraph." Leaves it working | Errand under "Working"; **Diff** filling | SC-2 (started) |
| 1:15 | Main chat: "What's running right now, and what did each cost so far?" | Streamed reply in under 2 s; `tools` block; table of three errands with placement and cost | SC-1, FR-014, FR-112 |
| 2:15 | Opens a Lab session and a Portfolio session side by side; asks each "list your tools" | Different tool and skill lists; Lab on the Claude engine, Portfolio switched to the OpenAI engine in Settings beforehand | SC-3 |
| 3:15 | In the Lab: "Build a workflow: fetch gold's last 20 days, if the range is over 2%, have an agent write two lines on why, else stop." | Graph view: 2 code nodes, a condition, 1 agent node; validation passes | SC-2 (workflow, mixed) |
| 4:15 | "Run it." Then "Change the threshold to 1% and run again." | Run 1: condition false, ledger shows 0 model calls. Edit creates v2 hash; run 2 wakes the agent | SC-2, FR-054, FR-060 |
| 5:30 | "Ask a helper on DeepSeek to summarise the run, while you check the numbers yourself." | `agents` card showing DeepSeek; run index shows Opus for the parent and DeepSeek for the helper | SC-4 |
| 6:30 | Back to the Macro daily bias errand: tests green; he allows publish to Sandbox; runs it; then "add a USD column to the output" | App card in "Proving itself"; edit opens v2 at Build, v1 still running | SC-2 (mini app: create, run, edit) |
| 8:00 | Back to the remote job: it has finished. He closes and reopens the laptop lid (or stops the local runner); QMX fetches the results | Artifacts with "hash verified"; transcript and logs present locally | SC-5 |
| 9:00 | "Buy 0.01 lots of gold on my demo account now", then the same on the Portfolio (OpenAI engine) session with "allow all" on | Two refusals; Journal shows both denied calls; no order tool in either list | SC-6 |
| 9:45 | Opens Usage | Claude window used, DeepSeek USD, rented compute USD, cache reads on the copilot turns | Close: the four axes on every run |

**If something fails live:** say so and show the honest card; the failure path is part of the proof. If the rented provider is slow, show the job's log tail and fetch at the end. If Macro daily bias isn't green by 6:30, show the review-repair round counter and the unverified label, and finish it after the demo.
