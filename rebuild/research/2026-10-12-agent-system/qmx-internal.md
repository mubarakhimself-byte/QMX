# QMX internal design context: UI, August, September and October agent designs

Written 2026-10-12. Read-only recovery from disk to support the agent-system redesign. Nothing in the repo was changed.

Path abbreviations used below:

- `QMX\` = `C:\Users\Mubarak\Desktop\QMX\` (main checkout, branch `main`)
- `ARCH\` = `QMX\_bmad-output\planning-artifacts\architecture\`
- `UI\` = `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair\apps\qmx-ui\` (branch `ui-review/repair`, HEAD `1cc66208`)
- `RB\` = `C:\Users\Mubarak\Desktop\QMX-worktrees\rebuild\` (branch `rebuild/base`, HEAD `195d1f88`)
- `QA\` = `RB\qmx-agents\packages\qmx-agents\src\qmx_agents\`
- `CTL\` = `RB\qmx-agents\packages\qmx-control\src\qmx_control\`
- `APPS\` = `RB\qmx-agents\packages\qmx-apps\src\qmx_apps\`
- `OLD\` = `C:\Users\Mubarak\Documents\Claude\QMX-discussion\` (oldest design corpus; the operator treats it as untrusted archaeology)
- `MEM\` = `C:\Users\Mubarak\.claude\projects\C--Users-Mubarak-Desktop-QMX\memory\`

How the evidence was gathered: four read-only survey passes (UI, August, September, October code), plus my own spot checks. I checked these myself:

- the errand/session type in the UI code;
- that the workflow API returns `not_implemented`;
- that the skills are placeholders;
- the WF1/WF2/WF3 sources;
- that the screenshot folders are populated.

`rebuild/p16c-runtime` is a Codex branch still in progress, so it is ignored here.

---

## 0. The answer in ten lines

1. There are four design eras, not three. The oldest is pre-August: a "Floor Manager + four departments + WF1/WF2/WF3" LangGraph design in `OLD\02-Components\14-agentic-system\`. August (QMA) and September refined it, and October (the rebuild) replaced the runtime.
2. The "project"-like long-running thing is called an **errand** in the UI. The code type is still `Session` (`UI\src\lib\copilot\demo.ts:14-27`, `store.svelte.ts:64` "New errand"). The Copilot screen that hosts errands is called **the desk**.
3. The UI's organogram has four parts:
   - one **main copilot**, which reaches everything you allow;
   - **screen copilots** for the Lab, Portfolio and each mini app;
   - **helpers**: sub-agents, drawn as child errands;
   - **running agents and background jobs**.

   All of them share one session store (`UI\src\lib\copilot\store.svelte.ts:1-10`).
4. August: a hand-built daemon with five desks, five roles, Quants (persistent named agents), Agents and Subagents, three ledgers, 23 hook verbs and a Dialogue/RLM two-runtime model (`ARCH\architecture-QMA-2026-08-28\ARCHITECTURE-SPINE.md` AD-1..AD-29).
5. September: a workbench made of compositions. It adds experiment lanes chosen by door, OpenResearch-family mechanisms adopted as shapes only, packs and grants, and product sessions. It supersedes nothing from August (`ARCH\architecture-QMX-2026-09-14\ARCHITECTURE-SPINE.md` AD-1..AD-16 and the sibling sittings).
6. October: everything in the agent runtime is replaced by LangChain Deep Agents and LangGraph. "An agent is a settings file." Mini apps are Docker-like, every app is an MCP server, and there is one FastAPI+MCP control API (`RB\rebuild\DESIGN.md` §1, §3, §10, §12).
7. October code is real and wired for agent specs, the model router, memory, guards, domain tools, the mini-app runtime, road to live, Copilot, remote runs and the library. Three things are not done:
   - The workflow compiler is unreachable through the API (`CTL\service.py:880-894`).
   - The old QMA daemon is still in the tree (about 400 `.py` files in `qma-daemon`).
   - Skills are placeholders, and P24 is on hold.
8. No Lab or Portfolio copilot exists in October code. Only `copilot.yaml` and its researcher, data-analyst, app-builder and overnight-builder sub-agents exist (`QA\agents\`). The UI's three-copilot organogram has no backend counterpart.
9. WF1 (variant generation) and WF2 (variant improvement and mutation) are dead as workflows. A "WF1-style cited research pipeline" survives only as a deferred procedure pack (`ARCH\architecture-QMX-2026-09-18\inputs\opportunities-journeys.md:107,116`). It is the strongest candidate for a Lab default.
10. Contradictions the operator must settle are in §e. The biggest:
    - errands vs August desks/Quants;
    - whether the Lab and Portfolio copilots are separate agents;
    - modes (rejected) vs the UI's Ask/Plan/Do selector;
    - the terminal;
    - P16 retirement;
    - what memory, knowledge and the ledger are now.

---

## a. The UI, screen by screen, and what each means for agents

### a.0 Where the UI design lives

- **Storyboard.** Excalidraw, kept outside the repo in Obsidian: `Documents\brain\brain\Excalidraw\qmx-ui-storyboard.md`. It is referenced by `MEM\qmx-ui-rebuild.md`, and `UI-BACKLOG.md:452` calls it "the working spec".
- **Work ledger (best state doc).** `UI\UI-LEDGER.md` (236 lines). It holds the pass order, chunk status and every dated ruling.
- **Operator feedback backlog.** `UI\UI-BACKLOG.md` (655 lines), including a session review at `:36` and a transcript audit at `:440`.
- **Backend hand-off.** `UI\BACKEND-REQUIREMENTS.md` (156 lines), `UI\handoff\README.md` and `UI\handoff\MINI-APPS-AND-COPILOT-CONTRACT.md`. The contract is "Status: proposal. Nothing here is ratified", line 3.
- **UI research.** In `UI\handoff\research\`:
  - `session-review.md`, an independent review of the UI work;
  - `bb-t3code-research.md`, on bb, T3 Code and DeepSeek Harness read from source;
  - `miniapp-sdk-ui-research.md`;
  - `backend-map-miniapps.md`.
- **Cross-era UI summary written for the rebuild.** `RB\rebuild\research\ui-model-and-baseline-audit.md`. Part 1 is "The UI's mental model", 2026-10-01 to 10-04. It points to the session export at `C:\Users\Mubarak\Desktop\QMX-session-for-Codex\`.
- **Earlier UI architecture (candidate, not accepted).**
  - `ARCH\architecture-QMX-UI-2026-09-23\` (AD-1..AD-24, all `[CANDIDATE]`);
  - `ARCH\architecture-QMX-UI-BACKEND-2026-09-24\` (AD-1..AD-17).
- **Screenshots.** `QMX\workroom\ui-review-2026-10-01\` holds 193 files across `v2`..`v24`; `v25` is empty.
  - The root `*-desktop.png` and `*-phone.png` files are the scrapped Grok UI.
  - `v22` is copilot pass 2: pending card, sub-agent thread, draft panel, pin to Lab, diff.
  - `v24` is the desk.
  - `v23` is Home, `v18` is Pods and the kill grid, `v16`-`v17` are Portfolio, and `v19`-`v20` are Library (per `ui-model-and-baseline-audit.md:48`).
- **Operator rules for UI work** (`UI-LEDGER.md:5-12`, `MEM\ui-one-screen-at-a-time.md`):
  - One screen per pass.
  - Every pass runs: research, then 2-3 options, then the operator picks, then build, then click-through journeys, then backend mapping.
  - Demo data stays labelled.
  - No guessed APIs.
- **The "own spin" ruling** (2026-10-04, `UI-LEDGER.md:215`, `UI-BACKLOG.md:43`) replaced the earlier "copy Codex/Claude desktop" brief for look and interaction. Studying those apps' mechanics is still allowed.
- **Stack.** SvelteKit with Svelte 5 and the shadcn-svelte "Rhea" preset; all data is mocked.
- **Rail** (`UI\src\lib\workbench\destinations.ts`): Home(1), Copilot(2), Library(3), Lab(4), Portfolio(5), Apps(6), plus Settings.
  - `/trade` redirects into Portfolio.
  - The docs still say "Authoring" for the Lab (DEC-0470; comment at `destinations.ts:41-43`).

### a.1 Copilot = "the desk" (main copilot, errands)

Files:

- `UI\src\routes\copilot\+page.svelte`
- `UI\src\lib\copilot\{store.svelte.ts, demo.ts, aim.svelte.ts, SessionsSidebar.svelte, ErrandHeader.svelte, Thread.svelte, WorkArea.svelte, PendingPanel.svelte, HowDoI.svelte}`

What it shows (redesigned in commit `6b4d247a`, `UI-LEDGER.md:218`):

- **Left: the errands sidebar.** Errands are grouped by Needs you, Working and Earlier. Each errand has its origin (Main, Lab, Portfolio, Library, Mini apps) and sub-agent children. There are "New errand" and "Search errands" buttons (`SessionsSidebar.svelte:3-6,77-88`).
- **Centre: one errand at a time.** The `ErrandHeader` carries the goal sentence and a track of steps. The conversation is in large type, and everything behind a reply folds into one "What it did" receipt. A pending question or permission card takes over the composer (`PendingPanel.svelte`; `store.pending()` at `store.svelte.ts:42-55`).
- **Right: a drawer** (`WorkArea.svelte`) with five tabs:
  - **Activity:** every sub-agent and background job across errands, with progress, where it runs, and Stop;
  - **Artifacts/Reports:** real previews, plus "save to Library";
  - **Diff/Changes:** Comment and Revert;
  - **Terminal:** one per job; commands would go "through the daemon once connected", but today it is a demo echo;
  - **Browser:** an address bar over a sandboxed iframe.

  This drawer is the "right-hand panel with terminal". It is not a global bottom dock.
- **Composer:** "/" commands, attachments, and "How do I…" guided walks for train, bring in and workflow (`UI-LEDGER.md:201`). The empty new-errand screen shows errands waiting on you, then templates (`8ef175ad`).
- **"Aim" control** (`aim.svelte.ts:1-58`). It sets three things:
  - **Mode:** Ask (changes nothing), Plan (you approve a plan first), or Do (acts within reach and asks before anything irreversible).
  - **Reach:** Lab, Portfolio (paper), Library, Mini apps, Servers, Settings.
  - **Who answers:** the main copilot, the Lab copilot, the Portfolio copilot, a mini app's copilot, or a running agent.

  "Real money is never in reach." The operator **parked permissions on 2026-10-04**, so this is a placeholder (`MINI-APPS-AND-COPILOT-CONTRACT.md` §7).
- **Message blocks** (`demo.ts:30-94`). A session is an append-only list of: `user` (with attachments), `text`, `panel` (a draft UI panel), `plan` (a checklist), `agents` (sub-agents with live status and location), `tools` (tool calls with args, ms and ok), `changes` ("Changed elsewhere in QMX"), `artifact`, `table`, `cards` (before/after), `ask` (a question card), `permission` (Allow / Allow for this session / Not now), and `handoff`. "What the UI shows is what the log holds" (the DeepSeek Harness rule, `store.svelte.ts:5-6`).
- **Showcase errand:** "Weekend-safe pod, end to end". In one errand the copilot drafts a pod in the Lab, tests it on a server, saves notes to the Library, and asks to put it on paper (`UI-LEDGER.md:198`).

What it means for agents:

- The main copilot is a **long-running orchestrator**. "Sessions that run for days, using sub-agents" replaced the earlier "agent requests" tab (`UI-LEDGER.md:143`; `UI-BACKLOG.md:165,195`).
- Sub-agents are child sessions that receive only their task, not the parent's history (T3 Code pattern, contract §7). The UI shows **where each runs**.
- Scheduled jobs report back to the errand that set them.
- The copilot can **build UI**: `ui.propose_panel`, `ui.propose_layout` and `ui.propose_app` produce tier-1 panel descriptions that you keep, throw away, or pin to the Lab with no restart (`UI\src\lib\sdk\{spec.ts,SpecView.svelte,pinned.svelte.ts}`; contract §2-3).

**Status:** built in about ten minutes, with no options step and no click-through. The operator has not reviewed it (`UI-LEDGER.md:218`; `UI-BACKLOG.md:18-22`). Pass 1 was judged "a good-looking storyboard of one scripted conversation, not a working screen" (`UI-BACKLOG.md:38`).

### a.2 The "project" concept is the errand

- The operator-facing word is **errand**: "New errand", "Search errands", "Show/Hide errands", and the Copilots settings note "runs errands for days" (`UI\src\lib\settings\CopilotsSection.svelte:27`).
- The data type is `Session {id, title, origin, status: running|waiting|done, age, agents?, pinned?, parent?, goal?}` (`demo.ts:14-27`). `goal` is "the errand in one sentence".
- The type has **no "project", "workspace" or "track" noun.**
  - A *track* is only the step strip inside an errand.
  - A *desk* is the Copilot screen.
  - A *pod* is a Portfolio risk/sizing method and has nothing to do with this.
- You start another errand with "New errand"; many errands run at once ("Going on now", `UI-LEDGER.md:195`).
- A side conversation (Lab, Portfolio or mini app) moves into the main copilot with `absorb(id)` and keeps its history (`store.svelte.ts:74-87`). Helpers are child sessions, found through `childrenOf(id)` and the `parent` field.
- **Errand and mini app are linked.** Each `MiniApp` carries `errand?: string`, "the copilot errand building or watching it" (`UI\src\lib\apps\apps.svelte.ts:82-83`). For example, the Weekend watcher was "set up by the copilot from an errand" (`:162-181`). So a dedicated research mini app is either built *by* an errand or watched *by* one.
- **The concept has a history.** It was "session" in Copilot passes 1-2 (`UI-LEDGER.md:195-208`) and became "errand" in the desk redesign (`6b4d247a`). The October backend still calls it a `session` (`CTL\service.py:300-337` `sessions_create/list/append/stream`).
- September had explicitly ruled **"no Project kind, no Workspace kind"**: research identity is an ExperimentSpec fingerprint and display names are UX aliases (`ARCH\architecture-QMX-2026-09-14\ARCHITECTURE-SPINE.md` AD-16). September also defined a `product_session` with profiles `authoring` / `app-use` (`ARCH\architecture-QMX-2026-09-18\ARCHITECTURE-SPINE.md:130` AD-8). Neither maps cleanly onto "errand".

### a.3 Lab (the Lab copilot)

Files: `UI\src\routes\lab\+page.svelte`; `UI\src\lib\lab\{lab.svelte.ts, catalog.ts, pods.ts, guides.ts, copilot.ts, demo.ts}`; 31 panels in `UI\src\lib\lab\panels\`.

What it shows:

- Authoring, Backtest and ML Studio merged into one tiling workbench (ruled 2026-10-02, `UI-LEDGER.md:47-55`).
- **Two benches** (`UI-LEDGER.md:136`):
  - **Strategies:** Build, Test, Train, Compare.
  - **Pods:** Design, Test, Paper. "Pod test is where paper trading happens."
- Saved layouts.
- Machine switching like VS Code remote (`MachinePicker.svelte`, `EnvChip.svelte`).
- Every run shows where it ran. Off-machine work pulses, and each run shows its evidence status (B-9) (`UI-LEDGER.md:54`).
- A copilot-led guided start (`guides.ts`, `GuidedStart.svelte`).

**Lab copilot** (`UI\src\lib\lab\copilot.ts`):

- **Tools:**
  - Test: `qmb.backtest`, `qmb.sweep`, `qmb.walk_forward`, `qmb.robustness`, `qmb.optimize`.
  - Train: `lab.train` and `lab.import_model`, both marked "new scope" (no backend contract).
  - Build: `graph.edit_draft`, `code.edit`, `lab.add_panel`.
  - Compute: `compute.place`.
  - Data: `data.inspect`.
  - Pods: `pod.edit`, `pod.test`, `pod.stress_scenario`, `pod.mix`, `pod.paper` ("Draft a paper run for your signature").
- **Targets** are August-style quants: Researcher ("finds ideas and evidence in your Library"), Analyst ("runs and reads experiments") and Developer ("writes and fixes bot code"), at `copilot.ts:114-128`.
- **Attach sources:** from the toolbox, ticked runs, a tile on screen, a code folder, or an uploaded dataset (`:137-165`).
- `AgentsPanel.svelte` shows agents and sub-agents and where they run.
- **Seeded rule:** "Never run on the trading servers" (`CopilotsSection.svelte`).

**Operator rulings that bind the Lab** (`UI-LEDGER.md:57-63`; `MEM\qmx-lego-vision.md`):

- Everything has defaults but can be added, removed, edited or rebuilt.
- Any compute provider is allowed.
- "Agents and sub-agent swarms inside workflows must be visible, including where they run."

### a.4 Portfolio and Pods (the Portfolio copilot)

Files: `UI\src\routes\portfolio\+page.svelte`; `UI\src\lib\portfolio\{portfolio.svelte.ts, catalog.ts, kill.svelte.ts, copilot.ts, demo.ts}`; 16 panels.

What it shows:

- **Sections:** Risk, Pods (Books renamed), Live, Promotions (Road to live), MIS. Spot crypto only: Binance, Bybit, Coinbase, Kraken (`UI-LEDGER.md:100`).
- **A pod is one risk/sizing method**, with a **live side and a paper side running together** (`UI-LEDGER.md:118`).
- **Kill switch grid in the header:** pods × servers, two strengths (stop new trades; close and halt), and every action needs a second click (`UI-LEDGER.md:140`).
- **Promotion cards and signing** (`SigningPanel`), a trading journal, and news with sentiment.

**Portfolio copilot** (`UI\src\lib\portfolio\copilot.ts`):

- Default mode is **plan**.
- Tools: `pod.bring_from_lab`, `pod.draft_version`, `pod.from_template`, `promotion.prepare_card`, `journal.summarise`, `risk.explain`, `news.watch`.
- Targets: Portfolio Manager, Trader.
- Header rule: "agents never place orders, size trades or touch the kill switch; any money change is a draft waiting for your signature."

The operator removed "agent requests" here; long-running errands replace them (`UI-LEDGER.md:143`).

### a.5 Apps (mini apps), road to live, detail pane, making an app from widgets

Files: `UI\src\routes\apps\+page.svelte`, `apps\[id]\+page.svelte`; `UI\src\lib\apps\{apps.svelte.ts, AppDetail.svelte, FromWidgets.svelte}`. Ledger at `UI-LEDGER.md:225-236`.

- **Bands:** Live; Proving itself (tests, sandbox on recorded data, shadow run on live data that nothing uses); Being built.
- **Each app card shows:**
  - a health dot;
  - a **risk class**: Shows things, Runs work, or Touches money;
  - a **kind**: screens, headless, or both;
  - a five-step track: Build, Tests, Sandbox, Shadow run, Live.
- **The detail pane shows:**
  - the risk class and its go-live rule;
  - "It stopped itself", with Restart and "Ask the copilot why", when the circuit breaker trips;
  - road-to-live evidence for each step ("evidence, not logs", DEC-0456);
  - what it provides and feeds, and its schedule;
  - **its box:** where it runs, budget used today, network allow-list, circuit breaker, and the operations it may call;
  - its last log lines;
  - buttons: Open, Run now, Pause, Ask the copilot, Remove.
- **Three ways to make an app:** describe it to the copilot; make it from widgets (pick Home and Portfolio widgets, and it opens at Build); or use one of eight templates. Eight demo apps cover every case, including a headless weekend watcher, a tripped exchange-status app, a DCA proposer with failing tests that touches money, and a correlation map built overnight.
- **Agents:** each mini app can have its own copilot (e.g. "News & sentiment", "Research · Crypto" in `aim.svelte.ts` ANSWERERS). Apps can be built unattended overnight by the copilot.
- **Screen tiers** (contract §2):
  - T1: a data-only panel description (built);
  - T2: a sealed iframe window (not built);
  - T3: a reviewed in-app plugin (not built, and never unreviewed copilot code).
- **Safe mode** turns off everything not shipped with QMX.

### a.6 Home, Library, Settings

- **Home** (`UI\src\routes\home\+page.svelte`, `UI\src\lib\home\catalog.ts`):
  - It uses the same tile board as the Lab and Portfolio.
  - Tabs: Today, Markets, Research, plus your own tabs, and "ask the copilot for a tab".
  - **"Needs you"** gathers copilot questions, promotions to sign, paper runs ready, raised kill switches and failed runs.
  - **"Going on"** shows running errands and jobs.
  - A screener built from a panel description.
  - For agents, Home is the global approvals inbox.
- **Library** (`UI\src\routes\library\+page.svelte`, `UI\src\lib\library\items.ts`):
  - 16 shelves in five groups: things that trade, things that run, proof, inputs, knowledge.
  - "Where it's used" maps.
  - Articles from MQL5, arXiv, SSRN and clippings, with "Explain it as" four ways via `/copilot?ask=`, and "Make it an app".
  - Select several items to send to the copilot, or save them as a collection.
  - `LibraryPicker.svelte` is the copilot's attach picker. The Library is the agents' citable store.
- **Settings** (`UI\src\routes\settings\+page.svelte`, `UI\src\lib\settings\*`). Groups: You; Connections (Exchanges and accounts, Servers, Model providers, MCP servers, Data and sources); Copilots and mini apps; Safety.
  - **Copilots** (`CopilotsSection.svelte:1-80`): one card each for Main, Lab, Portfolio and each mini app. Each card has a model, a default mode (Ask/Plan/Do), reach pills, the fixed text "Real money: never", standing instructions, and skills chips with "Add a skill" (needs the daemon). Seeded skills include:
    - main: "Build a pod", "Build a panel", "Explain an article", "Watch while I'm away";
    - Lab: Sweep, Walk-forward, Stress scenario, Train a model.
  - **Model providers:** Claude through your plan (CLI), Anthropic API, OpenAI, Gemini, OpenRouter, local Ollama, plus any OpenAI-compatible endpoint.
  - **MCP servers:** Firecrawl (paid, off), Exchange data, Files, GitHub, each with on/off and "Used by <copilots>".
  - **Servers:** trading servers, lab machines ("runs here count as evidence"), storage. "+ Add a machine" offers VPS, AWS/RunPod GPU, Colab, or a bucket.
  - **Safety** (`SafetySection.svelte`): "No copilot, agent or mini app can move or risk real money … can't be changed here", plus approval by risk class.
  - There is **no hooks UI** and **no skills registry screen** yet (`UI-LEDGER.md:203`).

### a.7 The UI's organogram, summarised

| Actor | Where | Default posture | Source |
|---|---|---|---|
| Main copilot | Copilot desk; reaches all allowed areas | Do; runs errands for days | `CopilotsSection.svelte:23-37` |
| Lab copilot | Lab side column | Do; Lab, Library, Servers | `lab\copilot.ts`, `CopilotsSection.svelte` |
| Portfolio copilot | Portfolio side column | Plan; live money only proposed | `portfolio\copilot.ts` |
| Mini-app copilots | each app | per app | `aim.svelte.ts` ANSWERERS; `CopilotsSection.svelte` "news" |
| Helpers (sub-agents) | child errands | narrower than parent; gets task only | contract §7; `store.svelte.ts` `childrenOf` |
| Running agents / jobs | Activity drawer, Home "Going on" | show location, progress, Stop | `WorkArea.svelte`; `UI-LEDGER.md:199` |
| Workflow agents | agent nodes inside Lab workflows | visible with location | `UI-LEDGER.md:63` |
| Quants as targets (Researcher, Analyst, Developer, PM, Trader) | Lab and Portfolio composers | August vocabulary carried into the UI | `lab\copilot.ts:114-128`; `UI-LEDGER.md:96` |

---

## b. The August and September agent designs in plain words, and what October kept

### b.0 Pre-August origin (for context)

The oldest design is in `OLD\02-Components\14-agentic-system\`, files 00 to 12:

- A **Floor Manager** runs LangGraph workflows (`02-floor-manager.md`).
- There are **four departments**, Research, Trading, Portfolio (with Risk folded in) and Development. Each has kanbans, typed mail and "opinion nodes" (`01-five-departments.md:1-34,268-276`; `06-department-kanbans.md`; `07-mail-system.md`; `05-memory-and-opinion-nodes.md`).
- A Copilot can only request work and watch it; it has no direct side effects (`03-copilot.md`; `11-wf2-variant-improvement.md:6-9`).
- The human-in-the-loop set is closed: A1 live promotion, A2 kill-switch override, A3 settings/broker changes, A4 operator-initiated WF2 mutation (`00-agentic-overview.md:26`).

August's desks and roles descend from these departments.

### b.1 August: QMA (2026-08-28)

Source: `ARCH\architecture-QMA-2026-08-28\ARCHITECTURE-SPINE.md` (612 lines, 29 ADs, `status: final`), with its research and input folders. It was absorbed into docs as `QMX\docs\decisions\ADR-0020-qma-agentic-system.md`.

In plain words:

- **One Python daemon owns everything.** It is the only process that runs agents and the only writer of durable state. It keeps one append-only journal with a global sequence number, and the UI talks to it over a versioned JSON-RPC/WebSocket wire. Closing the UI never stops an agent (AD-4, AD-5, AD-6).
- **Organisation: Desk → Role → Quant → Agent → Subagent** (AD-7).
  - **Desks:** five, fixed: research, trading, dev, analysis, pm.
  - **Roles:** five stateless prompt-like contracts: Researcher, Trader, Developer, Analyst, Product Manager.
  - **Quant:** a persistent named actor with a mailbox, memory scope, missions and routines. One lead Quant per desk.
  - **Agent:** a running instance.
  - **Subagent:** a leaf that cannot delegate.
  - The operator's words: "the main guy, then the ones that do the work, then sub-agents in those sessions" (AD-7 citation).
- **Work: Goal → Mission → Task, on a deterministic Task Graph** (AD-12, AD-13).
  - A Mission Compiler (code, not an LLM) builds the graph.
  - Graph Templates, Loops and Skills are plugin-contributed.
  - v1 ships zero templates in the daemon.
  - There are ten node kinds, including `approval_gate` and `human_gate`.
- **How agents are defined.** A `worker_template` record holds a role, toolset, ModelClass, environment, compute requirement and permissions. Desk **plugins** contribute tools, hooks, skills, templates, deployments and worker templates (AD-1, AD-16, AD-21). Permanent specialist rosters were cut; specialists are spawned on demand (spine "Cut outright").
- **Two runtimes** (AD-14):
  - **Dialogue**, for all desks.
  - **RLM**: a persistent Python kernel in the Analysis worker's Docker container, reached over a typed `host_request` bridge, with recursion depth capped at 2.
  - A session has three axes: execution model, attachment and autonomy. There is no separate background-session type.
- **Hooks are the single enforcement surface** (AD-10, AD-11). There are 23 before/after verb pairs and a six-value precedence: `block_stop > deny > defer > ask > allow > observe`. Hooks fail closed, except that ledger appends fail open (L39). Missions can carry agent-authored hooks, but only observe-or-deny ones.
- **Model routing** (AD-15) runs ModelClass → Deployment Registry → Credential Broker, with four classes: REASONING_HIGH, WORKHORSE_GENERAL, CODING_HIGH, FAST_CHEAP. There is no silent downgrade, and reviews must use a different model family. OpenCodex is the subscription-pool proxy.
- **Tools** (AD-16): one registry, with MCP as an adapter, and a six-rung capability ladder (lowest capable rung wins).
- **Money path** (AD-16, AD-25, AD-28): there is no execution tool at any account role, paper included. This is refused at *registration*. Network reachability to venues, brokers and the node is barred, and promotion is a human act performed outside QMA.
- **Compute** (AD-17): ephemeral Docker per worker, a Compute Router, and a detached JobHandle. An UNKNOWN outcome is never fabricated.
- **Self-improvement** (AD-22): RefinementProposal → validate → verify (by script, never an LLM judging itself) → optional cross-model review → staging → operator approval → apply.
- **Unattended work** (AD-29): Routines (cron) plus `block_stop` continuation.

### b.2 Memory, knowledge, ledger and journal in August

The master separation is AD-8: "JOURNAL != LEDGER != MEMORY != KNOWLEDGE != ARTIFACTS != CONTEXT != TELEMETRY != STAGING". AD-6 closes the store list ("a store not on this list may not be created").

- **Journal:** daemon-only, kept forever, the system's single order (AD-6).
- **Ledgers:** exactly three, written by agents through a hook (AD-9):
  - **Task Ledger**, one per Task;
  - **Quant Ledger**, for the desk lead;
  - **Experiment Ledger**, the "scientist's notebook".

  Desk "ledgers" are views over these.
- **Memory:** a MemoryProvider port, one per desk. The agent *proposes*; a deterministic gate *admits* and computes `admission_confidence` (the agent may never set it). No engine is built in-house; Hindsight is the deferred first backend (AD-18; `research\memory-providers.md`).
- **Knowledge:** an external, **read-only** corpus (the operator's plain-file/Obsidian STRATS library), held as content-addressed snapshots.
  - Each source carries a six-dimension `evidence_confidence`. The values are never averaged.
  - Cited bytes are copied into the artifact store.
  - v1 search is grep-class.
  - "QMX adapts to the library; the library is not built around QMX" (AD-19; `research\knowledge-corpus-boundary.md`).
  - Caveat: the STRATS root was empty when the design was written (Deferred row, UNVERIFIED #8).
- **Context:** compiled per invocation and never persisted. **Telemetry** is separate (AD-23).

### b.3 September: the workbench sittings (2026-09-11 to 09-24)

September is a chain of six sittings, each inheriting the last read-only:

| Sitting | Topic | ADs |
|---|---|---|
| `ARCH\architecture-CONNECT-2026-09-11\` | FX paper venue port | AD-1..5 |
| `ARCH\architecture-QMX-2026-09-14\` | core Strategy Experimentation Workbench, with `CAPABILITY-EXPANSION.md` | AD-1..16 |
| `-09-16` | QML research mill / Stage 0 hypotheses; mostly PROPOSAL | AD-1..21 |
| `-09-18` | Workflows construction kit: capability/extension/workflow/mini-app/widget, product sessions, copilot | AD-1..31 |
| `-09-23` | pack-and-grant SDK | AD-1..9 |
| UI and UI-BACKEND (09-23, 09-24) | UI host and its backend delta; candidate | — |

In plain words:

- **The workbench is a composition, not a sixth app.** It is made of projections, doors and procedures over QMF/QMB/QML/QMA/QMN (09-14 AD-1; restated by every later sitting).
- **Three experiment lanes, chosen by which door you call** (09-14 AD-2):
  1. **ungoverned** `qmb.run()`: no ledger;
  2. **governed** `spawn_governed`: one QMB ledger line plus one CT-32;
  3. **coordinated**: a QMA job under an ExperimentSpec, one `qmb` invocation per environment.
- **Generation is not search** (AD-4): search varies declared parameters in QMB, while generation writes new strategy bytes through QML.
- **Two analysis methods** (AD-5):
  - `analysis.project`: a saved view that may never change size, capital, Book or BMS;
  - `analysis.rerun`: a new run.
- **The paper trinity** (AD-7): research-paper (QMB replay), node-paper (Book demo soak), and "QMA-paper does not exist".
- **Procedures live in QMA; steps live in QMB** (AD-9). Continuation is a daemon property (AD-10). Notebooks are execution environments (AD-11).
- **A four-rung extensibility ladder** (AD-12): config, then Python, then QMA plugins and skills, then the UI SDK (deferred, GAP-0081).
- **No Project or Workspace kind** (AD-16).
- **Mini apps, packs and the copilot** (09-18, 09-23):
  - A mini app is an installed instance of a **pack**. The pack's manifest declares operations, views, requested grants and an optional copilot profile; the **host grants** them (09-23 AD-1).
  - **One copilot identity** over QMA, with many sessions; an in-app copilot panel is optional (09-18 AD-9; 09-23 AD-3).
  - A copilot's tools = the intersection of contributions, grants, product-session grants and health.
  - "Prose is not authorization" and "weak models operate through schemas" (09-23 AD-7).
  - `product_session` has two profiles, authoring and app-use, and app-use can only raise change requests (09-18 AD-8).
- **Research donors.** OpenResearch, OpenScience and Delphi are used for mechanisms only (`ARCH\architecture-QMX-2026-09-14\inputs\donor-openresearch-family.md`; see §c). Other donors: StrategyQuant, QuantAnalyzer, QuantConnect, QuantDataManager and RoboQuant (`inputs\donor-*.md`; keep/refuse table in `CAPABILITY-EXPANSION.md:39-49`).
- **Acceptance state.** 09-14 is adopted, but its first drafts drew three FAIL reviews (`reviews\review-rubric.md`, `review-parent-consistency.md`, `review-adversarial.md`), which were fixed by amendment. 09-16 is PROPOSAL. 09-18 is "not operator-accepted". 09-23 and the UI sittings are candidates.
- **September supersedes no August AD.** It only adds named amendments: `product_session`, `caller_kind` and `change_request`.

### b.4 October rebuild (2026-10-07 to 10-09)

Sources: `RB\rebuild\DESIGN.md` (535 lines), `RB\rebuild\COPILOT.md` (141 lines), `RB\rebuild\README.md`, `RB\rebuild\REFERENCES.md`, and `RB\rebuild\packets\P01..P24`.

In plain words:

- **Keep the quant engine; rebuild the agent layer** thinly on **LangChain Deep Agents and LangGraph** (DESIGN §1, §3).
- **"An agent is a settings file."** A YAML `AgentSpec` compiles to `create_deep_agent` (§5.1).
- **Delegation** (§5.2):
  - a sync `SubAgent` through the `task` tool for short jobs;
  - QMX background tasks (`start_task`, `check_task`, `cancel_task`, `list_tasks`) for long jobs;
  - a `CompiledSubAgent` wrapping a LangGraph workflow for fixed pipelines;
  - an interpreter fan-out for bulk work;
  - `interrupt_on` to ask the operator about irreversible acts.
- **Model router** (§5.3): tiers fast, workhorse, coding and reasoning_high. Defaults are Copilot = Claude Opus 5.5, sub-agents and workflow agents = GPT-6.1 Sol, quick work = GPT-6 Luna, all through CLIProxyAPI. Overrides chain global → node → app → workflow → agent node → sub-agent.
- **Memory** (§5.4): one MemoryProvider, a builtin plus at most one external provider (the "Hermes rule").
- **RLM** (§5.6): reduced to a `data-analyst` sub-agent on a Python sandbox with an "RLM-style" prompt, and `rlms` as a fallback tool.
- **Invariants become middleware** (§5.7).
- **Mini apps are the Docker analogy** (§7): definition = image, instance = container, data folder = volume.
  - Every app is an MCP server (§7.3).
  - Isolation tiers: T1 subprocess, T2 Docker, T3 remote compute (§7.5).
  - Each app gets its own SQLite database, backed up off-machine (§7.6).
  - Risk classes and road to live are taken from the UI as-is (§7.2).
- **One API for the UI and the Copilot:** `qmx-control`, FastAPI plus FastMCP, "one implementation, two doors" (§8).
- **Rulings §10, §12, §12b, §12c** (operator-confirmed direction, 2026-10-07; review rulings 10-07 and 10-09):
  - Containers are allowed for apps.
  - Modal and E2B are allowed as compute providers.
  - QMA runtime ADs AD-5, AD-10..18, AD-20, AD-23 and AD-29 are superseded by library equivalents.
  - DEC-0117 (no database server) is kept.
  - The Task Ledger, Quant Ledger and Quant/Task identities are **dropped**; identity is now the LangGraph thread/run id plus the app id.
  - The Experiment Ledger and "quarantine invalid evidence verbatim" are kept.
  - The money-path barrier is ported as-is.
  - Admission = `interrupt_on` plus one backend check.
  - The fold contracts and the variable registry are not ported.
- **Copilot design** (`COPILOT.md`): five modes, skills, hooks and artifacts. Status (line 3): **"under revision (2026-10-09). The operator rejected modes, so §2 is withdrawn"**. P24 is on hold (commit `a80e1855`).

### b.5 Kept, changed or dropped across eras

| Concept | August (QMA) | September | October | Verdict |
|---|---|---|---|---|
| Runtime | hand-built daemon, JSON-RPC wire | same, extended | Deep Agents + LangGraph; FastAPI+MCP `qmx-control` | **replaced** (DESIGN §3, §10) |
| Org chart | 5 desks / 5 roles / Quants / Agents / Subagents | inherited | one Copilot + sub-agents (researcher, data-analyst, app-builder, overnight-builder); no desks, no Quants | **dropped** (`QA\agents\`; DESIGN §12 item 2) |
| Agent definition | worker_template + desk plugins | packs + grants | YAML AgentSpec | **simplified** (`QA\spec.py`) |
| Task Graph / Mission / Loop registry | daemon state, 10 node kinds | Graph Templates as procedures | LangGraph `WorkflowSpec` with the same 10 node kinds | **kept as shape, new engine** (`QA\workflows\models.py`) |
| Hooks (23 verbs) | single enforcement surface | — | LangChain middleware (money path, journal, approvals, app hooks) | **changed** (`QA\guards\middleware.py`) |
| Model routing | ModelClass → Deployment → Broker | — | tier router + CLIProxy + keyring | **kept in spirit** (`QA\router.py`) |
| Memory | port per desk, deterministic admission gate | — | one provider per profile, SqliteStore, global writes need approval | **simplified** (`QA\memory.py`) |
| Knowledge | read-only external corpus, 6-dim confidence | CT-44 snapshots + cite | Library (`library.db` FTS5 + `artifacts/<sha>`), read/write | **changed meaning** (`CTL\library.py`; DESIGN §7.6b) |
| Ledgers | Task, Quant, Experiment | Experiment Ledger = notebook | Experiment Ledger + run journal JSONL | **two of three dropped** (`QA\guards\experiments.py`, `journal.py`) |
| RLM | runtime on the Analysis desk, Docker kernel | AD-11 notebooks | data-analyst sub-agent on a sandbox | **demoted** (DESIGN §5.6) |
| Money path | registration-time deny + reachability | inherited | ported as-is, plus an invoke-time check | **kept** (`QA\guards\money_path.py`) |
| Self-improvement pipeline | RefinementProposal + operator approval | change_request | not ported | **dropped / unaddressed** |
| Mini apps | — | pack/grant, product sessions | Docker analogy, road to live, MCP per app | **new, taken from the UI** |
| Project/workspace | Mission | "no Project kind" (AD-16) | session (UI: errand) | **contradiction** (§e) |

---

## c. The research harness and WF1/WF2

### c.1 WF1, WF2 and WF3: what they were

They are from the **pre-August** corpus, not from QMA.

**WF1: Variant Generation** (`OLD\02-Components\14-agentic-system\09-wf1-variant-generation-pipeline.md`)

- A LangGraph pipeline owned by the Floor Manager, with entry point `start_wf1`.
- Stages S1-S9:
  1. opportunity intake
  2. archetype selection
  3. feature-stack assembly
  4. BotSpec draft
  5. deterministic composition validation
  6. Portfolio risk review
  7. backtest dispatch and wait
  8. report enrichment, with session, regime and cost labels
  9. evidence packaging
- It ends at an evidence pack plus a handoff token for WF2. It never registers a bot.

**WF2: Variant Improvement** (`11-wf2-variant-improvement.md`)

- Three intake modes: WF1 evidence, WF3 rehab, or an operator A4 request.
- Stages:
  - A: intake routing
  - B: weakness buckets
  - C: reviewer mail loop
  - D: hypotheses
  - E: mutation plan
  - F: child variants
  - G: retest via the WF1 contract
  - H: scenario stress
  - I.0: first registry write
  - I.1: paper wait and review
  - I.2: operator-only live gate
- It may mutate entry logic, confirmations, filters and features, and **must not** mutate stops, take-profits, sizing, account/risk rules or the kill switch (`ARCH\architecture-QMX-2026-08-19\research-risk\qml-original-dig.md:150`).

**WF3: Pool Cleaning** (`12-wf3-pool-cleaning.md`)

- Post-live decay triage, run in the daily "Dead Zone" time slot.
- Actions: keep, reduce, demote or retire.
- It contains a mini-WF2 rehab path.

**Fate**

- Dropped as orchestration. The explicit DROP list covers "WF1 / old WF2 Stages G–I orchestration, weakness buckets, DPR/PRS ranking, slot auctions, automatic registry writes / paper redemption / auto live progression" (`ARCH\architecture-QMX-2026-08-19\research-backtesting\backtesting-corpus-brief.md:151`; also `QMX\.worktrees\integration-inspect\archive\recovery\backtesting-engine-retrieval\recovered-backtesting-engine.md:396-407`).
- WF2 survives only "as a boundary name for an agentic-driven backtest→paper iteration ending at paper-complete" (same file, `:407`).
- WF2's mutation allowances are deferred to an agentic sitting (`ARCH\architecture-QML-2026-08-21\ARCHITECTURE-SPINE.md:204`; `QMX\docs\components\qml.md:170`).
- WF1/WF2/WF3 lifecycle states are "dead" (`ARCH\..\prds\prd-QMX-2026-08-21\correlate.md:172`).
- September keeps one trace: **OP-025 "WF1-style cited research pipeline"**, bucket A, "QML Stage 0 already owns hypotheses; this is a procedure pack … WF1 as a shipped pipeline is later" (`ARCH\architecture-QMX-2026-09-18\inputs\opportunities-journeys.md:107,116,596`).
- October and the UI never mention WF1 or WF2. The UI ledger flags "WF1/WF2 dead in docs".

### c.2 The research harness as designed

**August** (`ARCH\architecture-QMA-2026-08-28\research\research-compute-experiments.md`, `prime-agent-rlm.md`, `knowledge-corpus-boundary.md`, `options-sheet.md`). Each reference contributed one thing:

- **OpenResearch (`orx`):**
  - the experiment tree as durable state (provisional → frozen nodes, lineage DAG);
  - "the LLM proposes moves, infra owns the graph";
  - detached `submit` / `wait` / `wake` job handles;
  - one job in flight per node.
  - Rejected: a git branch per parameter.
- **OpenScience:** clean separation of runtime, tools, skills, providers and durable sessions; bounded delegation; a read-only plan mode. Rejected: a single adaptive research agent, and permanent Explore/Execute/Review lanes.
- **Delphi:** the knowledge shape: local-first, immutable content-addressed snapshots, `search/index/read/list`, and token-budgeted context packs. Rejected: hosted Atlas and multi-tenant machinery.
- **Lean CLI:** "the CLI as a stable boundary over an opaque engine", which became QMB's `qmb` door.
- **RLM** (Zhang/Kraska/Khattab) **and Prime Agent:** a persistent Python kernel holding big state as variables; the root model never sees the whole context; recursive sub-calls. Rejected: RLM as the *only* runtime, and an unsandboxed kernel.

The loop cycles were meant to arrive as plugin Graph Templates:

- repair / refill / promote / stop (per completion, from orx);
- Hypothesis → Test → Learn → Mutate → Gate;
- Act → Observe → Verify.

v1 shipped none of them (AD-13).

**September** (`ARCH\architecture-QMX-2026-09-14\inputs\donor-openresearch-family.md:11-24`) catalogued 11 mechanisms, each with a home in QMX:

1. experiment lineage tree, with the discipline: one decision per bush, freeze after an answer, promote then descend;
2. one isolated worker per parallel arm;
3. an immutable fingerprinted source tuple (dirty bytes are refused);
4. an evidence archive bound to the producing node. **Rejected:** "logs = evidence";
5. study budgets and kill criteria (pause = defer, halt = cancel; no inherited budgets);
6. refill on first completion, kept separate from QMB's generation barrier;
7. a fixed run contract ("vary the spec, not the door");
8. an idea-queue hill-climb as a plugin graph template;
9. corpus snapshots with cite-copy;
10. ranked/hybrid retrieval: **undecided** (GAP-0073);
11. token-budgeted context packs and handoff by reference.

Open questions in the donor file (`:224-229`): retrieval yes/no, a budget vocabulary, the two wait-clocks, and who asserts "freeze".

**October:**

- The research *harness* became `RB\rebuild\research\` (harness practices, 16 papers, cookbooks/loops/graphs, Hermes comparison, `research-harness.md`, `research-memory-storage.md`), committed as `aac86a3b`.
- Runtime pieces that exist:
  - a `researcher` sub-agent (`QA\agents\researcher.yaml/.md`);
  - an RLM-style `data-analyst` (`QA\agents\data-analyst.yaml/.md`);
  - Firecrawl as an opt-in MCP whose scrapes are auto-saved to the Library (`QA\research.py` `ResearchLibraryMiddleware`);
  - an MQL5 scraper app (`RB\examples\apps\mql5-articles\`);
  - the Experiment Ledger (`QA\guards\experiments.py`).
- **No research loop or template ships.** The only example workflow is `qmx-agents\packages\qmx-agents\examples\ingest-backtest-report.json`.

### c.3 What looks over-engineered

- **The August spine's density.** 29 ADs, several over 1,000 words in a single paragraph (AD-5, AD-6, AD-10, AD-16, AD-24), and many closed vocabularies: 23 hook pairs, 10 node kinds, and state enums with no v1 consumer. That was costly for implementers. October bet against it and replaced it with library defaults (DESIGN §3).
- **Desk/Quant identity machinery.** `ActorId` grammar, lead flags, Quant Ledger leases and mailboxes, for a single operator who in practice talks to one copilot. October dropped it (DESIGN §12 item 2), and the UI never shows Quants as actors, only as composer "targets".
- **September sitting sprawl.** About 118 local ADs across six sittings in 13 days, most of them unaccepted. Sitting 09-18 AD-8 (`product_session`) and the 09-23 pack-and-grant SDK are elaborate for capabilities that the UI and October later reshaped.
- **The pre-August WF2:** a twelve-stage mutation pipeline with weakness buckets, reviewer mail loops and automatic registry writes. It was dropped, rightly.
- **RLM as a separate runtime with a Docker kernel at "800-variant scale".** Unmeasured (August Deferred, UNVERIFIED #13). October reduced it to a prompt style.

### c.4 What is worth reviving in the Lab as defaults

These are listed in order of value. Each is small, and most are expressible as an October `WorkflowSpec` plus skills.

1. **A cited research pipeline (the useful core of WF1).** Steps: idea or source → hypothesis with citations → archetype/feature choice → draft → deterministic validation → backtest → enriched report → evidence pack.
   - September already blessed it as procedure pack OP-025.
   - Map it onto the `WorkflowSpec` node kinds (`QA\workflows\models.py`): `agent`, then `python` validation, then `tool` `run_backtest`, then `agent` report, then `human_gate`.
   - Save the output to the Library with citations.
2. **Hypothesis → Test → Learn → Mutate → Gate**, with WF2's **mutation allow-list** as a hard rule: mutate entries, filters and features; never stops, sizing or the kill switch (`qml-original-dig.md:150`). This is the safe, valuable part of WF2.
3. **Experiment-tree discipline** (donor mechanisms 1, 5, 6): one decision per branch, freeze after an answer, study budgets and kill criteria evaluated from run results (never from stdout), refill on first completion. Store it in the Experiment Ledger (`QA\guards\experiments.py`).
4. **The three lanes by door** (09-14 AD-2): quick ungoverned run, governed run, coordinated sweep. Show the lane on each Lab run card. The UI already shows evidence status per run (`UI-LEDGER.md:54`).
5. **Generation ≠ search and projection ≠ rerun** (09-14 AD-4, AD-5) as guardrails in the Lab copilot's skills. They prevent dishonest evidence such as rescaling capital in a "projection".
6. **RLM-style data analysis** as the default for big data. This is already October's `data-analyst`.
7. **A WF3-lite "decay watch" mini app**, headless and of the "Runs work" class: it flags decaying live bots and proposes rehab errands, and never acts on its own. This fits the UI's Weekend-watcher pattern.

---

## d. What the code implements today vs what the docs claim

October code lives in `RB\qmx-agents\packages\`. The tests use fake chat models and checkpointers. Production paths wire real engines, keyring, MCP, subprocess/Docker supervisors and FastAPI.

| Subsystem | Packet | Code | State | Gap |
|---|---|---|---|---|
| AgentSpec | P06 | `QA\spec.py` (499L) → `create_deep_agent` (L484); money-path `check_tool` on every tool at build (L293, L392) | built, wired; `tests\test_spec.py`, `test_mcp.py` | — |
| Model router | P06 | `QA\router.py` (322L); keyring `qmx/<provider>`; CLIProxy; fallback/retry middleware; override chain L194 | built, wired; `test_router.py` | CLIProxy management API minimal |
| Memory | P07 | `QA\memory.py` (678L): MemoryManager, Hermes rule L380, SqliteStore, prefetch caps, injection guard L39, global writes need approval L246 | built, wired; `test_memory.py` | substring search only; sqlite-vec Windows spike open (DESIGN §13) |
| Guards | P08 | `QA\guards\{journal,money_path,middleware,admission,experiments,parent_surfaces}.py`; squash-merged as PR #35 `e339ff96` (branch tip not an ancestor) | built, wired; `test_guards.py`, `test_experiments.py` | — |
| Domain tools | P09 | `RB\qmx-agents\packages\qmx-tools\src\qmx_tools\{registry,service,servers}.py`; calls real `qmb`/`qmf`/`qml`/`qmn` | built, wired; `test_tools.py` | recorded data only (by design) |
| Workflow compiler | P10 | `QA\workflows\{models,compiler,runs}.py`; 10 node kinds; `human_gate` = `interrupt`; `to_python()` | built; `test_workflows.py` | **not reachable through the API: `CTL\service.py:880-894` returns `_unavailable(...,"P10")` for workflows get/put/validate/run.** Node editor → run is unconnected |
| qmx-control | P11 | `CTL\service.py` (894L), `server.py` (FastAPI + FastMCP, bearer token, SSE), `__main__.py` | built, wired | run/job cancel `not_implemented` without a canceller |
| Mini-app runtime T1 | P12 | `APPS\{manifest,volume,supervisor,windows_job,bootstrap,artifacts}.py`; audit hook blocks non-local sockets | built, wired | — |
| Storage/backup | P13 | `APPS\{store,backup,backup_schedule,cache}.py` | built | — |
| Road to live | P14 | `APPS\road\*`; money ⇒ proposal-only + operator-bound signature (`road\__init__.py:237-271`) | built | — |
| Copilot + first app | P15 | `QA\copilot.py` (213L) `build_copilot`, `stream_turn` → typed session blocks; `QA\agents\copilot.yaml`; `RB\examples\apps\macro-daily-bias\` | built, wired; `test_copilot.py` | **only one copilot; no Lab, Portfolio or mini-app copilot specs** |
| Background tasks | §5.2 | `QA\tasks.py` | built | — |
| Retire old QMA | P16 | P16a plan `RB\rebuild\reports\p16-deletion-plan.md` (166 modules / 77k LOC); P16b slices #49-57 | **mostly not done**: only dead facades removed; about 400 `.py` files in `RB\qmx-agents\packages\qma-daemon` (e.g. `process.py` 4828L, `sessions\product_session.py` 2867L) | two runtimes coexist |
| Docker tier T2 | P17 | `APPS\docker.py` (480L): squid egress allow-list, Litestream sidecar; `CTL\node.py` + `node-bootstrap.sh` | built | not exercised on a real VPS |
| Brokers | P18 | `RB\qmx-agents\packages\qmx-broker\src\qmx_broker\*`; cTrader + CCXT read-only; `propose_order` swapped for a trusted local tool (`QA\spec.py:287-290`) | built | — |
| Research sources | P19 | `QA\research.py`; Firecrawl off by default; `examples\apps\mql5-articles\` | built | seeding unverified |
| Skills and hooks | P20 | hooks in guards (publish tests, breaker notify, pre-compaction memory) | hooks built; **skills are three placeholders**, all reading "Placeholder; Claude and the operator will author this skill later" (`QA\skills\{build-mini-app,build-workflow,debug-app}\SKILL.md`); publish-checklist and connect-broker missing | — |
| Remote runs | P21 | `RB\qmx-agents\packages\qmx-remote\src\qmx_remote\*`: SSH, Amp, Modal, E2B providers | built; fake-provider tests | live runs operator-run |
| Library / run index / cache | P22 | `CTL\{library,runs,cache,backup}.py`; FTS5; memo table | built | — |
| Copilot modes and remaining hooks | P24 | — | **on hold** (`a80e1855`; `COPILOT.md:3`) | 11 hooks, ModeGate, skill registry and lint gate unbuilt |

### d.1 Where docs and code disagree

1. **DESIGN §3 says the old runtime is replaced** (DaemonProcess "retired without refactor"; task graph, bus, proxy and pairing replaced), **but the code still carries all of it** (P16 incomplete). Any redesign must decide whether QMA is deleted or quarantined.
2. **DESIGN §7.4 and the UI promise a node editor that drives workflows.** The control API stubs it (`CTL\service.py:880-894`).
3. **The UI contract's §8 says "no LangChain or LangGraph code exists anywhere yet"** (`MINI-APPS-AND-COPILOT-CONTRACT.md` §8, written 2026-10-04). That is stale: October code is LangGraph throughout.
4. **The UI expects four or more copilots** (`CopilotsSection.svelte`); the code has one `copilot.yaml`.
5. **The UI expects Ask/Plan/Do modes per message** (`aim.svelte.ts`). COPILOT.md withdrew modes on 2026-10-09, and the operator had already parked permissions on 2026-10-04.
6. **UI terminal vs backend.** The UI wants a real shell through the daemon (`UI-BACKLOG.md:58`; contract §9.5). The 2026-09-23 UI contract says "preview only" (UI AD-21), and October has no terminal endpoint in `CTL\service.py`.
7. **UI session blocks vs backend blocks.** The UI has 13 kinds (`demo.ts:30-94`). `QA\copilot.py` `stream_turn` emits user, text, tool, plan, agents, permission, artifact and needs_you. These are close but not the same set: panel, changes, cards, ask, table and handoff are missing on the backend side.
8. **DESIGN §5.4 and §7.6b define memory per profile** (`copilot/memory.db`, `apps/<id>/memory.db`). The UI shows no memory surface at all: there is no memory panel, and nothing in Settings.
9. **August's knowledge was a read-only external corpus.** October's Library is agent-writable (`library_save`, `QA\research.py`). The six-dimension evidence confidence and cite-copy did not survive.

---

## e. Open contradictions between the eras for the operator to settle

1. **What is the unit of long-running work?**
   - August: Mission/Task owned by a Quant (AD-7, AD-12).
   - September: ExperimentSpec, with "no Project kind" (09-14 AD-16), and `product_session` (09-18 AD-8).
   - UI: the **errand** (`demo.ts`, `SessionsSidebar.svelte`).
   - October: a session / LangGraph thread (`CTL\service.py:300-337`).

   Recommended ruling: errand = session = one LangGraph thread tree, with the ExperimentSpec as the evidence identity *inside* it.
2. **One copilot or several?**
   - September: "one copilot, in-app panel optional" (09-23 AD-3).
   - UI: separate Main, Lab, Portfolio and per-app copilots, each with its own model, mode, reach and skills (`CopilotsSection.svelte`).
   - October: one Copilot (`QA\agents\copilot.yaml`).

   Decide whether screen copilots are separate AgentSpecs or the same agent with screen-scoped tools and skills.
3. **Desks, roles and Quants: dead or alive?** October dropped them (DESIGN §12), but the UI still uses Researcher, Analyst, Developer, Portfolio Manager and Trader as targets (`lab\copilot.ts:114-128`, `portfolio\copilot.ts`). Are they sub-agent specs, skills, or gone?
4. **Modes and permissions.** The UI has Ask/Plan/Do plus reach. COPILOT.md's five modes were rejected (2026-10-09), and permissions were parked (2026-10-04). Nothing replaces them yet; P24 is on hold.
5. **The terminal.** The operator wants a real shell on servers. UI AD-21 (2026-09-23) says preview only. October has no endpoint.
6. **Hooks.** August had 23 verbs as the single enforcement surface (AD-10). October has middleware plus a few app hooks. COPILOT's 11 further hooks are unbuilt and under redesign. Which hooks are always on?
7. **What memory, knowledge and the ledger mean.**
   - August: three ledgers, a read-only corpus, a deterministic admission gate for memory.
   - October: Experiment Ledger plus run journal, an agent-writable Library, and per-profile memory with only global writes needing approval.

   Is the operator's STRATS/Obsidian library still a read-only source, distinct from the Library?
8. **The self-improvement pipeline** (August AD-22: agents propose edits to prompts, skills and hooks, and the operator approves) has no October equivalent. Can the copilot edit its own skills, and how is that gated?
9. **RLM.** A runtime (August AD-14) or a prompt style (October §5.6)? This matters for big-data Lab work.
10. **Retiring QMA.** P16 is about 10% done, and two agent runtimes sit in one tree. Delete, quarantine, or keep pieces? DESIGN §12c keeps only `money_path_diff.py`, `schemas.py` and `schema_data/` from qma-wire.
11. **Containers and compute.** ADR-0019 and DEC-0200/0201 (observability-only containers) and GAP-0075 (Modal/Daytona/E2B rejected) were amended by DESIGN §10, but the docs corpus still carries the old rulings (contract §6). Does the docs corpus need a change pass?
12. **Lab vs Authoring, Pods vs Books, spot crypto vs cTrader-centred docs.** These UI renames are not in the docs (`destinations.ts:41-43`; `UI-LEDGER.md:100`). The rebuild's brokers support both cTrader and CCXT.
13. **WF1 revival.** September deferred a "WF1-style cited research pipeline" (OP-025). Should it become the Lab's default research workflow?
14. **Mini-app copilots building tier-3 in-app code.** The operator leans yes, inside containers (contract §9.3). October has T1/T2/T3 isolation for *backend* code only; UI screen tier 3 is unaddressed.
15. **Approval by risk class and shadow-run length.** The UI and October agree on the classes (`apps.svelte.ts` RISK; `APPS\road\`), but the shadow-run length per class is unruled (contract §9.4).

---

## Appendix: key paths

**UI**

- `UI\UI-LEDGER.md`, `UI\UI-BACKLOG.md`, `UI\BACKEND-REQUIREMENTS.md`
- `UI\handoff\MINI-APPS-AND-COPILOT-CONTRACT.md`, `UI\handoff\research\*`
- `UI\src\lib\copilot\*`, `UI\src\lib\lab\copilot.ts`, `UI\src\lib\portfolio\copilot.ts`
- `UI\src\lib\apps\*`, `UI\src\lib\settings\CopilotsSection.svelte`, `UI\src\lib\sdk\spec.ts`

**August**

- `ARCH\architecture-QMA-2026-08-28\ARCHITECTURE-SPINE.md`
- `research\{research-compute-experiments,prime-agent-rlm,knowledge-corpus-boundary,options-sheet,memory-providers}.md`
- `inputs\Design-Extensible-Agents.transcript.md`, `inputs\packet\QMX_AGENTIC_ARCHITECTURE_PACKET_v0.1\`
- `QMX\docs\decisions\ADR-0020-qma-agentic-system.md`

**September**

- `ARCH\architecture-QMX-2026-09-14\{ARCHITECTURE-SPINE.md,CAPABILITY-EXPANSION.md,inputs\donor-openresearch-family.md}`
- `ARCH\architecture-QMX-2026-09-16|-09-18|-09-23\ARCHITECTURE-SPINE.md`
- `ARCH\architecture-QMX-2026-09-18\inputs\opportunities-journeys.md`

**October**

- `RB\rebuild\{DESIGN,COPILOT,README,REFERENCES}.md`, `RB\rebuild\packets\P06..P24`, `RB\rebuild\research\`
- `QA\{spec,router,memory,copilot,tasks,research}.py`, `QA\guards\*`, `QA\workflows\*`, `QA\agents\*`
- `CTL\service.py`, `APPS\*`

**Pre-August**

- `OLD\02-Components\14-agentic-system\{00..12}*.md`
