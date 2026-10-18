# 46. Domain expansion: the scenarios QMX must hold, and what they change

Written 2026-10-18 by one Opus 5.5 agent for the planning lead and the architect. Read-only except this file. Nothing committed. No sub-agents.

**Method.** A context collection first (operator addition: nothing may re-implement what exists), then a funnel.
- **Context collection** (§1): every merged tree (`origin/main`, `origin/integration`, `origin/rebuild/base`, `origin/engine/base`), the other remote branches (one line each), the legacy `docs/` and `_docwork/`, the three architectures, studies 26, 37d, 39, 44 and 45, the alignment files A, B and C, `UI-HANDOFF.md`, the Hermes mirror, the three clippings and Hindsight's own site. All read with `git ls-tree`, `git show`, `git grep` and `git log`; nothing checked out.
- **Diverge** (§3): BMad party mode run headless in `session` mode, one mind voicing every persona: Carson (brainstorming coach), Maya (design thinking), Dr. Quinn (problem solver), Victor (innovation strategist), Winston (architect), Sophia (storyteller) and Caravaggio (presentation). The operator's seat is answered from his rulings, never invented. Brainstorming ran in "ideate for me" headless mode with these techniques: Persona Journey, Jobs to be Done, What If Scenarios, Reverse Brainstorming, Chaos Engineering, Assumption Reversal, Time Shifting, Ecosystem Thinking, Predator and Prey, Five Whys, Failure Analysis, Starbursting, SCAMPER and Cross-Pollination (from the clippings and Hermes). Design thinking supplied the point-of-view statements, problem solving the root-cause pass, and innovation strategy the jobs and moat check.
- **Converge** (§4): Affinity Clustering, then a relevance filter against his purpose and rulings, then a ranking by value and by how much the design would change.
- **Deviation from the skills, on purpose:** the brief allows one file, so the brainstorming memlog and HTML keepsake were not written. The diverge log in §3 is the memlog.

**Labels.** Every idea and every kept scenario carries one tag:
- **EXISTS**: built in merged code or fully designed in an architecture; the citation says where. It stays in the log and produces no design change.
- **PARTIAL**: something exists; the tag says what is missing.
- **NEW**: nothing on the ground covers it.

"Built" means merged code on `origin/engine/base` (`132169c7`) or `origin/rebuild/base` (`4345eafa`). "Designed" means an architecture decision (engine `AD-n`, Library `L-AD-n`, Lab `Lab AD-n`) or a study design change (`45 DC-n`, `44 §n`).

**Not available when this was written.** Study 43 (`43-whole-app-unlocked.md`) is named in all three architecture memlogs as the record of the ruling-118 pass, but the file is not on disk. The engine spine already carries that pass (AD-52 to AD-60, unstaged). The Library spine does not yet carry its decision "sessions are Library items" (Library memlog, ruling-118 entry); this file calls it **L-AD-21 (memlog only)**.

---

## 0. In plain words (for the operator)

**What this study did.** It imagined QMX in use, the way you described it: a research partner with copilots, workflows that run on your PC or your server, mini apps that feed each other, one Library that keeps everything, the Lab, and memory. It first listed what already exists so nothing gets built twice. Then it produced 214 scenario ideas from your journeys, from the code, from Hermes and from your clippings. It kept the 34 that matter for trading research and set the rest aside with reasons.

**What already holds.** The workflow engine is built, with schedules, catch-up, replay, tests and pausing at provider limits. The backtester, the trading-framework packages, the trading node and the bot-authoring library are built, and so are the mini-app supervisor and remote-machine adapters. The Library, memory, the Lab, routing and the desktop host are designed but not built. Many scenarios you named already have an answer in the designs: two agents editing one thing, mini apps feeding each other, remote workflows reaching the Library, provider limits mid-run and mixed providers. Those are listed as covered, not redesigned.

**What the scenarios showed is missing.** Nearly every gap traces back to three missing ideas:

1. **Bad news does not travel.** The Library records what was used to make what, but nothing reads those links backwards. A bad data file, a wrong indicator or a poisoned lesson therefore leaves every result built on it looking healthy. A test result counts as passed even though its input was later corrected. The fix is one mechanism: a mark on an item ("corrected", "quarantined", "replaced") that QMX works out at read time for everything built from it, and that pauses schedules that depend on it. The same mechanism lets an idea show "supported", "refuted" or "open" from the tests linked to it. That gives you a ledger of hypotheses, which is the heart of a research assistant.
2. **Time is not first-class.** Lessons have no "true for which period". A mini app's output has no "fresh until". A schedule has no "must be ready by London open" and no market-calendar check. In trading, a lesson from a trending quarter applied blindly to a ranging one is a real loss.
3. **Work in flight is invisible across machines.** QMX can tell that something was already built. It cannot tell that something is being built right now on the server, so two agents can build the same thing at once. There is also no single switch to pause all autonomous work, and no check that your server runs the same QMX version as your PC.

All three can ride on things already designed: the links between Library items, the memory rows, and the heartbeats the server already sends. No new store and no new service are needed.

**Five more changes worth having:**
- turn a copilot "keep watching this" loop into a server workflow with one click, so it survives a closed laptop;
- let stable agent steps turn into plain scripts over time, falling back to the agent when the script meets something new;
- steer a running workflow without starting over;
- give one mini app several setups (one per currency pair) without copying it;
- ask several agents or models the same question and show where they disagree, instead of trusting one confident answer (your probabilistic-thinking clipping).

**Nothing here needs your decision.** Two items touch your words: whether a "hypothesis" is a thing you want to see in the Library, and whether "forget this" may truly remove a memory. Both have a recommended default in §6.

---

## 1. Already on the ground

### 1.1 The merged trees

| Tree | Date | What it holds |
|---|---|---|
| `origin/main` | 09-27 | Docs only (`docs/`, `_docwork/`, `_bmad-output/`, `tracker/`); no code. Moves only by his click. |
| `origin/integration` | 09-30 | The factory-era code: QMF packages (`packages/qmf-*`), `qmb`, `qml`, `qmn`, `extensions/qmf-calendar-forex`, and the QMA daemon generation (`qma-core`, `qma-daemon`, `qma-wire`, `qma-ui-contract`). 713 commits ahead of `main`. |
| `origin/rebuild/base` | 10-18 | `integration` + 857 commits: the rebuild P01-P23 (control, apps, remote, tools, ledger, broker, agents) and the QMA v2 harness HP0-HP17 (`qma-harness`). |
| `origin/engine/base` | 10-18 | `rebuild/base` minus 25 commits (HP2 and two test fixes) plus 60 commits: the workflow engine EP0-EP14, harness grants HG1-HG2, templates TP1-TP4. His merge click into `rebuild/base` is pending (alignment C M-19). |

**Other branches, one line each:**
- `plan/agent-system`: the planning tracker (this folder).
- `qma/hp0`-`hp17`, `engine/ep0`-`ep14`, `tp1`-`tp4`, `hg1`-`hg2`: merged packet branches.
- `rebuild/p01`-`p23`, `p16a`-`p16c-*`: merged rebuild packets and deletion steps (P16b and P16c retired daemon parts).
- `epic/070`-`073`, `ui-epic/066-shell`, `ui-integration`, `codex/factory-*`, `deployment/fmt-check`, `factory-recovery/007/*`: factory-era work, contained in `integration` or superseded.
- `qmx-*-checkpoint-2026-10-01`: frozen checkpoints.
- Local only (not pushed): `ui-review/repair` holds the rebuilt UI (Lab template cards, start-up motion; the UI session owns it), `ui`, `plan/risk-sizing` (the risk session) and `research/mql5-article-library`.

### 1.2 Capability inventory

| Capability | Where it lives | State |
|---|---|---|
| Money, time, instrument primitives, fp1 identity | `packages/qmf-core` | built |
| Data rooms, dataset splits, **12-month holdout seal enforced on reads**, journals, source adapters, backup primitives | `packages/qmf-data` (README: "reads still enforce the wired 12-month seal") | built |
| Indicator protocol and wrappers; causal structure families | `packages/qmf-indicators`, `qmf-structure` | built |
| Registry: per-kind records, typed append-only lineage edges, human-signed promotion skeleton | `packages/qmf-registry` | built |
| Book, BMS, exits, paper mode, risk arithmetic | `packages/qmf-risk` | built (an edge module; the risk session owns its future) |
| cTrader venue seam | `packages/qmf-venue` | built |
| Forex market-hours calendar | `extensions/qmf-calendar-forex` | built |
| Backtester: runloop, sweeps (sensitivity, splits, resume), optimise (admit, rank, batch), **robustness (walk-forward, carve-out, perturbation, trade-order shuffle, significance)**, paper, workbench, registry projection | `qmb/src/qmb/*` (325 files) | built |
| Bot authoring: protocol, declaration, generation, conformance, research | `qml/src/qml/*` | built |
| Trading node: MIS, promotion, protection, reconcile, replay, observability, bench, seats | `qmn/src/qmn/*` (338 files) | built (ruling 14: premature to deepen) |
| QMA daemon generation (Task Graph, mailbox, pairing, packs and grants) | `qma-daemon`, `qma-core`, `qma-wire` | built; on the deletion plan (engine AD-59) |
| QMA v2 harness: isolated chat homes, permissions, money gate, relay key and GPT lanes, blocking `delegate`, usage meter, doctor, per-chat compaction, hooks and tool rows (HG1) | `qma-harness/src/qma/harness/*` | built |
| Agent specs, a scoped memory with hooks (LangGraph `deepagents` backend), router v0, builder skills `build-workflow`, `build-mini-app`, `debug-app` | `qmx-agents/src/qmx_agents/*` | built (rebuild era); AD-59 ports its skills and deletes the runtime |
| Control service: sessions, Library v0 (`library.db`: immutable blobs, version chains, FTS), memoised backtest, remote runs and jobs, apps (create, test, publish, rollback, start, stop, logs, resource, call, backup, restore, evidence; archive is a stub), workflows doors, weekly git snapshot backup, Ubuntu node bootstrap with a Tailscale-only control service | `qmx-control/src/qmx_control/{service,library,backup,node,runs}.py` | built; runs and jobs retire under AD-57 |
| Mini-app runtime: immutable definitions, stdio MCP per app, volume lease, heartbeat with CPU seconds and RSS, schema-checked `feeds` and `provides` artifacts, road stages, Docker and Windows Job, backup schedule; app-owned schedule and usage budget (to retire) | `qmx-apps/src/qmx_apps/*` | built (45 §5.0 probe F1-F4) |
| Remote compute adapters SSH, Amp, Modal, E2B | `qmx-remote/src/qmx_remote/providers.py` | built; `worker.py` (LangGraph loop) to delete (AD-57) |
| Domain tools and MCP servers; broker reads and unsigned proposals; run journals | `qmx-tools`, `qmx-broker`, `qmx-ledger` | built |
| Workflow engine: one format `qmx.workflow/1`, nodes (script, rule, loop, join, wait, llm, agent, grader, monitor, subworkflow, trigger, doctor), memo and node replay, ledger, spans, drafts, versions, test runs with pinned data, publish needs tested, inbox, explain, failure ladder, idle watchdog, chunked agent fan-out, pause at provider limits, admission with interactive reserve | `qmx-engine/src/qmx_engine/*` | built |
| Triggers cron (IANA zone), interval, manual, after, catch-up, quota hold, fire claims under lease, preflight | `qmx_engine/triggers/*` | built; `event`, `webhook`, `session` designed only (`ledger/migrations.py:35` CHECK) |
| Intent key annotation and `find_by_intent` on the engine's Library port | `ports/library.py:224, :245` | built (port and fake); `check_built` real check owed (memory packet) |
| Memory port, eight verbs, stub | `ports/memory.py`, `memory/__init__.py` (one docstring) | built stub; AD-18 designed; Hindsight nowhere in code |
| 31 templates (research, trader, Lab, developer, mini-app pipeline and lifecycle) | `qmx_engine/templates/*` | built; 9 tested (44 §1.2), 22 drafts |
| Old UI shell (home, copilot, library, authoring, settings) | `apps/qmx-ui` | built, superseded by `ui-review/repair` |
| Library, Hub, run passes, sidecar, backups by replication | Library spine L-AD-1 to L-AD-20 | designed; three stand-ins answer today (`qmb/registryread`, control `library.db`, engine `library_fake`) |
| Lab (document kinds, node pack, QMB door, families, pods, kernel, board) | Lab spine AD-1 to AD-18 | designed; no Lab package |
| Router, pool, model registry, mixed providers, `delegate` v2, multimodal layer, permissions guard, browser and Cua, explainers, skills curator, copilot loops, desktop host, worktrees, one composition root, packs as plugins, one run system, capacity table | engine AD-12, 28-35, 38-60 | designed |
| Domain model: three classes, landing rule, operations as the contract, two channels, one app home, evidence door, board as draft | `45` DC-1 to DC-15 | study, not folded |
| Toolsets, one `Surface`, `RecallEngine` seam with Hindsight default, eval battery, revolution loop | `44` §2-§4 | study, not folded |
| 35 golden scenarios (holdout seal, QMB replay, three experiment lanes, projection vs rerun, pack lifecycle, nested mission, host retry, diagnosis) | legacy `docs/scenarios/SCN-0001`-`0035` | doc only; several now land in built QMF and QMB code |
| 71 features with dependency order | legacy `_docwork/feature_inventory.yaml` FEAT-0001-0071 | doc only; FEAT-0001-0039 broadly built in QMF, QMB, QML and QMN |

### 1.3 Facts this study relies on that are not in 45

- **The holdout seal is built** in `qmf-data`, and QMB's robustness ladder (walk-forward, carve-out, perturbation, trade-order shuffle, significance) is built. Several "honest judging" ideas below are EXISTS or PARTIAL because of this.
- **`attached` references have no home any more.** 45 §2.9 put them "beside `session_homes`" in `qmx_control`. The unlock pass dropped `session_homes` (engine AD-35: the home is a field of the harness chat record). Library memlog makes sessions Library items. This study's X-3 settles it.
- **AD-19 still says** `emits` and `accepts` "on the engine bus". 45 DC-3 (events are Library ref-log rows) is not folded yet. Scenarios below assume DC-3.
- **`check_built` covers finished work only** (engine AD-27). Nothing covers two runs building the same thing at the same moment.

---

## 2. The room (an excerpt)

Headless party, `session` mode. The operator's seat is answered from his rulings, with the ruling cited.

**Carson:** Whole app unlocked, nothing legacy! YES AND: what does he do on a Tuesday? Start there, and I want a hundred scenarios before anyone draws a box.

**Maya:** Point of view: *a solo trader-researcher needs every idea he touches to remember what became of it, because his edge is the failures he does not repeat.* How might we make "what happened to that idea" one click from anywhere?

**Mubarak (ruling 57):** Nothing waits for me. Workflows write to the Library freely, garbage or clean.

**Dr. Quinn:** Then garbage is a first-class citizen. AHA: the Library records `consumed` and `derived-from` edges, so it knows what was built from what. But who reads those edges *backwards* when an input turns out to be garbage? Nobody. Every downstream result stays green.

**Winston:** Trade-off first. Storing a "tainted" flag on every descendant means a write storm and a second source of truth. Compute it at read from the edges and the marks on the roots. At his scale (thousands to low hundreds of thousands of items, 45 DC-15) a recursive SQLite walk is fine.

**Victor:** Strategic silence... then: this is the moat. Every backtest tool shows you a Sharpe. None shows that this Sharpe was built on a feed corrected last Tuesday, inside a family of 212 trials, testing a hypothesis two other runs refuted. Jobs to be done: "keep me from fooling myself". Build *that* and QMX has no competitor.

**Sophia:** Then let me tell the story of one idea. A video on London breakouts becomes a hypothesis. It gets tested 40 times by three agents on two machines and refuted in Q2. Then a new regime arrives in Q4, and a fresh session proposes it again. Does QMX say "you tried this", or "you tried this, *in a different regime*"?

**Dr. Quinn:** Second root cause: time. Lessons have no validity window. Outputs have no freshness. Schedules have no "ready by".

**Mubarak (ruling 55, 117):** Don't rely on my laptop. Local by default, but work off my machine is very important.

**Carson:** Chaos round! The PC sleeps mid-loop. Contabo runs an older QMX than the PC. Two agents start the same scrape at 07:00. NFP lands during a fan-out. A key gets pasted into a note.

**Winston:** Third root cause: in-flight state across machines. Heartbeats already flow to the Hub (L-AD-13). Put three more facts on them: running intent keys, the host's version and kind digest, and a pause flag. No new channel.

**Caravaggio:** And please, no wall of red badges. One mark, three words: *built on corrected data*. One click shows the path.

**Maya:** And the copilot's answers? His clipping says every answer is one draw from a set.

**Victor:** He uses cheap Chinese models most (ruling 107) and has no caps (ruling 106). Asking three models and showing the spread costs almost nothing. That is a feature no single-vendor tool can offer.

**Winston:** Agreed, but as a template and a prompt rule, not a mechanism. Everything else here should also land on things that exist. Show me each idea tagged EXISTS, PARTIAL or NEW before I take any of it.

---

## 3. Diverge log (all ideas, grouped)

Tag key: **E** = EXISTS, **P** = PARTIAL, **N** = NEW. "→ K-n" marks ideas carried into a kept scenario, "→ park" ideas parked in §6.

### G1. Copilot sessions and places (journeys; Persona Journey)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-001 | A Lab session resumed in the hub keeps its home, tools and transcript | E | engine AD-35 (home on the chat record, resume on every surface) |
| D-002 | One session combines Lab, Portfolio, a workflow and a mini app by pack set | E | AD-35, AD-55 (toggle per session), probe P-TG |
| D-003 | The hub has every capability of the Lab and Portfolio copilots | E | AD-35, AD-55, ruling 12 |
| D-004 | Attached context references travel with the session | P | 45 §2.9 places them on a dropped table → K-02, X-3 |
| D-005 | A context reference pins an item version, or follows the latest | N | pins never resolve silently (legacy DEC-0443) apply only to apps → K-02 |
| D-006 | A video attached while being transcribed is a pending reference | N | AD-42 pre-processing is synchronous in the design → K-02 |
| D-007 | Session recap on resume in another place | E | Hermes H-111 → AD-35 |
| D-008 | Fork a session to try two directions in parallel | P | Library variant refs and AD-41 exist; no session fork → K-30 |
| D-009 | Merge a fork's drafts back into one direction | E | L-AD-7 merges, AD-49 reconcile |
| D-010 | Long errand survives compaction (errand notes) | E | 44 §2.2 errand.md skill |
| D-011 | Session started in an app's place; app's agents reachable | E | AD-19, AD-55 |
| D-012 | Several sessions at once editing related items | E | L-AD-7 one owner per ref |
| D-013 | Sessions themselves searchable as Library items | P | L-AD-21 (memlog only) → K-26 |
| D-014 | Copilot "keep watching X" loop must survive a closed laptop | N | AD-47 loops live in the PC harness → K-18 |
| D-015 | Copilot answers label claims retrieved, remembered or inferred | P | 44 §1.4 names the labels; no prompt slot rule yet (B29) → K-11 |
| D-016 | Copilot asks itself for candidates and ranges on open questions | N | probabilistic clipping → K-11 |
| D-017 | His dictated seeds become structured briefs with recommended answers | E | Lab AD-18 (board questions with recommended answers) |
| D-018 | Copilot explains with rendered explainers and widgets | E | AD-45 |
| D-019 | Voice chat in QMX | → park | ruling 85 |
| D-020 | Phone alerts | → park | ruling 34 |

### G2. Context gathering and intake (Jobs to be Done; Cross-Pollination from Hermes)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-021 | Pull a pod, an app's output, a folder, a website, a video into a session | P | 45 §2.9, 44 §2.6; no single context package → K-02 |
| D-022 | One size-capped, cited context package shared by copilot, workflow and helper | P | 44 §2.6.3 gap 5 → K-02 |
| D-023 | Hermes `@file`, `@folder`, `@url` references with soft and hard caps | E | 37d H-112 adopted |
| D-024 | Playlist or Instagram saves intake with chunked fan-out | E | templates A, RS1 and AD-34 |
| D-025 | Firecrawl 5,000 articles → sort → ideate → macro research | E | 39 §8, SOLUTION-DESIGN §26.13 |
| D-026 | Dedupe a video seen in two playlists | E | AD-27 intent key |
| D-027 | Every derived note keeps a locator back to the source (timestamp, page, paragraph) | N | edges have no locator → K-01, X-24 |
| D-028 | His Obsidian clippings folder as a watched research source | P | mechanisms exist (interval trigger + hashing script + intent key); no template → K-31 |
| D-029 | A deleted or private video mid-run | E | failure ladder AD-16; node fails, run continues |
| D-030 | YouTube needs his login | E | AD-44 browser with his profile snapshot |
| D-031 | Image or video to a text-only model | E | AD-42 description fallback |
| D-032 | Clipping text is data, never instructions | E | AD-43 injection hygiene |
| D-033 | Paper intake with figures and tables | E | `paper-read` shared block, AD-42 |
| D-034 | Podcast or audio intake | E | AD-42 audio by default (ruling 100) |
| D-035 | TradingView chart screenshots as inputs | E | AD-42 |
| D-036 | Intake grades usefulness and drops "useless" sources | E | `understand-extract` block (44 §1.2 J2) |
| D-037 | Source reliability score per channel or author over time | N | → park (nice, not core) |

### G3. Memory (Hindsight; Time Shifting)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-038 | Memory follows the subject (pod, workflow, app), not the folder | P | 44 §2.6.4 tags `item:<id>`; AD-18 not amended → K-03 |
| D-039 | Hindsight is the default recall engine (his choice) | P | 44 flags it as a ruling change; AD-18 says built-in default → K-03 |
| D-040 | Banks by writer trust (operator, copilot, workflows) | P | 44 §2.6.4 proposal → K-03 |
| D-041 | Lessons carry a validity window and regime tags | N | AD-18 row fields lack time and regime → K-03, X-4 |
| D-042 | "Forget that" removes a memory | N | archive-never-delete plus Hindsight index; no forget path → K-03 |
| D-043 | Contradicting lessons reconcile | E | Hindsight observation consolidation; AD-18 `correct` move |
| D-044 | Memory poisoning by garbage workflow output | P | banks by trust (44); no taint → K-07 |
| D-045 | Remote runs recall through the Hub | E | AD-18 port; L-AD-11 |
| D-046 | PC offline: FTS5 fallback adapter | E | 44 §2.6.4 two adapters |
| D-047 | Hindsight's retain and reflect calls route through QMX's router | P | 44 §2.6.3 gap 6; not designed → K-03 |
| D-048 | Dead end from a nightly workflow surfaces when he proposes the idea in the hub | P | `check_dead_end` designed; the copilot path is not → K-03 |
| D-049 | Standing questions (mental models) as Library items | E | 44 §2.6.4 |
| D-050 | Memory graph over time in the UI | E | 37d H-80 → UI-HANDOFF |
| D-051 | Self-improvement from memory | E | AD-26, ruling 79 |
| D-052 | A projection of the Library as markdown he can grep (like `hindsight fs mount`) | N | → park |

### G4. Library (Starbursting; clipping "40 million documents")

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-053 | The Lab reads a Library object a mini app is using | E | 45 DC-6, L-AD-2, L-AD-7 → K-08 |
| D-054 | A result shows "your input has a newer version" | N | computed from edges; nothing reads them → K-08, X-1 |
| D-055 | Concurrent agents branch and merge (git-like) | E | L-AD-7, L-AD-20, engine AD-49 → K-12 |
| D-056 | Workflow definitions merge per node id, not as text | P | L-AD-7 "per field and blob type"; no workflow merge driver named → K-12 |
| D-057 | Binary blobs (weights, parquet) never three-way merge; pick-one card | E | L-AD-7 |
| D-058 | Remote workflow reads and writes the Library through the Hub | E | L-AD-11 to L-AD-13, 45 DC-11 → K-14 |
| D-059 | Server becomes the primary when it exists | P | L-AD-19 setting; 45 DC-11 default flip not folded |
| D-060 | Big blobs fetched by hash from the bucket and cached on the worker | P | L-AD-10 tiers; no worker cache or locality → K-14, X-18 |
| D-061 | Library search answers carry the edge that admitted each item | P | 45 DC-15 → K-26 |
| D-062 | As-of queries: what the Library looked like on a date | P | ref log is history; no as-of read verb → K-26 |
| D-063 | Garbage-in: search noise and bloat from free workflow writes | N | → K-25, X-15 |
| D-064 | Test-run refs pile up forever | N | → K-25 |
| D-065 | A secret pasted into a note lands as an immutable object | N | → K-27, X-16 |
| D-066 | Previews and detail views from schema | E | L-AD-17 |
| D-067 | Kinds are data; a new kind is a schema file | P | 45 DC-1 not folded |
| D-068 | Collections as saved queries | E | 45 A16, legacy DEC-0282 |
| D-069 | Agent-made tools land unreviewed | E | L-AD-3, UI-HANDOFF §9 row 7 |
| D-070 | Library archive refuses while something enabled pins the item | E | 45 §2.3, 37b §17.7 |
| D-071 | Claim-level verification of explainer text against cited items (clipping "gate 6") | N | → K-05 |
| D-072 | Citation validation: an id cited must be in the admitted set | N | → K-05 |
| D-073 | Grounder precision measured, truncation constant tested | P | 45 DC-15 probe P-SRCH |

### G5. Workflows and the engine (Graph and loop engineering)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-074 | Fully agentic, mixed and script-only workflows on one engine | E | AD-2, `nodes/script.py`, ruling 52 |
| D-075 | Monitor before waking an agent (no tokens when nothing changed) | E | `nodes/monitor.py` |
| D-076 | Stable agent steps crystallise into scripts; fall back to the agent on new inputs | N | AD-22 traces-first goes one way only → K-19, X-10 |
| D-077 | Steer a running workflow: rerun from a node with new parameters, reusing finished work | P | node replay built (EP5); no fork-from-node door → K-20, X-11 |
| D-078 | Revolution loop: plateau → reframe the search space → continue | P | 44 §2.5, DC-11 of 44 |
| D-079 | Loop inside a loop via a subworkflow | P | 44 §2.4 gap 1 |
| D-080 | Selected-subgraph test run | E | AD-11 |
| D-081 | Pinned data tests (n8n style) | E | `service/tests.py` |
| D-082 | Unknown outcome of an irreversible external step waits on a gate | E | EP7, AD-8 |
| D-083 | A failed step does not redo everything | E | memo and replay AD-7 |
| D-084 | Provider limit mid fan-out pauses and resumes | E | EP11, AD-9, AD-40 |
| D-085 | Chunk model fallback re-plans unstarted chunks | E | 39 §8, AD-34 |
| D-086 | Two runs build the same thing at the same moment | N | AD-27 covers finished only → K-13, X-6 |
| D-087 | `[SILENT]` and declared-failure output contract | E | 37d H-62 adopted |
| D-088 | Create a trigger paused (canary) | E | 37d H-64 adopted |
| D-089 | Failure-streak nudge | P | `triggers/claims.py` built; inbox nudge owed (H-61) |
| D-090 | Deadline: "brief ready before London open" | N | → K-16, X-8 |
| D-091 | Market-calendar precheck (no runs when FX is shut) | P | `extensions/qmf-calendar-forex` built; `precheck` designed (AD-10); no shipped precheck → K-16 |
| D-092 | Priority among queued runs when slots are short | N | AD-58 queue has no priority → K-16 |
| D-093 | Global pause of all autonomous work | N | → K-28, X-17 |
| D-094 | Workflow writes a new workflow (QMX creates workflows) | E | AD-22 builder, ruling 22 |
| D-095 | Templates ship working | P | 22 of 31 drafts (alignment C M-5) |
| D-096 | Trajectory export from traces for fine-tuning his own models | N | 37d H-94 → park |
| D-097 | Mixture-of-agents as a virtual model | N | Hermes MoA → park (the panel template covers the need) |
| D-098 | Darwinian evolution of prompts, regex or indicator code | N | Hermes `darwinian-evolver` skill → park |
| D-099 | Long ML training resumes from its own checkpoint after preemption | P | sidecar flushes checkpoints (L-AD-13); node replay is node-level → K-23, X-20 |
| D-100 | GPU as a resource class | P | AD-58 names CPU, chat and container slots; GPU via `resources` only → K-23 |

### G6. Mini apps (Ecosystem Thinking; Predator and Prey)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-101 | Apps feed apps through landed outputs | E | 45 DC-3 (proven F1-F3) → K-09 |
| D-102 | An app feeds on its own output; the loop ends by intent key | E | 45 DC-12 |
| D-103 | Producer publishes a changed `provides` schema; consumers break | N | → K-09, X-5 |
| D-104 | Consumer sees how fresh the producer's output is | N | → K-09, K-22, X-5 |
| D-105 | Producer outruns the consumer (coalesce to latest) | N | `max_concurrent` exists; no coalesce → K-09 |
| D-106 | Fan-in from three producers fires once each | E | 45 DC-3 dedupe per trigger and object |
| D-107 | Garbage producer: consumer's schema check refuses, incident blames the producer | P | refusal built (F3); attribution not designed → K-22 |
| D-108 | One app, many setups (EURUSD, GBPUSD) without copying | N | 45 A15 says "variant pack" → K-10, X-12 |
| D-109 | App agent asks another app (no permission union) | E | 45 DC-7 |
| D-110 | A panel of app agents answers one question; disagreements shown | P | operations exist; no template → K-11 |
| D-111 | App on Contabo, consumer on the PC, PC asleep | E | 45 DC-6 (read last landed output) |
| D-112 | App crashes at 3 a.m.; diagnosis by closed failure classes | P | 45 DC-10; supervisor restart built → K-22 |
| D-113 | App wraps a workflow; the inner workflow gets v2; the app keeps v1 until republished | E | 45 §2.5a pins |
| D-114 | App render check of four widget states | P | `ma-mini-app-lifecycle` draft; `qmx app check` in 45 §2.5a |
| D-115 | App archived, never deleted | P | `apps_archive` stub (`service.py:1017`) |
| D-116 | App's external API key per app | E | AD-24 `qmx/tool/<name>` |
| D-117 | App calls the Lab (`lab.*` operations) | E | 45 A13, DC-2 |
| D-118 | App shared with a friend or a marketplace | → park | QMX is personal (ruling 32, 40) |
| D-119 | App with a live dashboard from live sources | E | Hermes live-dashboard skill → widgets AD-45 |
| D-120 | Webhook into an app (TradingView alert) | P | webhook trigger designed, not built → K-17 |

### G7. The Lab and honest judging (Assumption Reversal; clipping lessons)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-121 | Published procedure on a draft subject is a live run that lands | E | 45 DC-8 |
| D-122 | Notebook cell numbers are exploration, never evidence | E | 45 DC-8, Lab AD-9 |
| D-123 | Explainer numbers are bound to artifact fields, not typed by the model | P | AD-45 "model writes data and directives"; binding by reference not stated → K-05 |
| D-124 | Matched placebo control: the same procedure with one ingredient swapped for random | P | QMB robustness built (shuffle, perturbation, significance); no matched-control procedure → K-05 |
| D-125 | Family trial count includes every agent and machine | P | Lab AD-6 from edges; a missing `variant-of` edge undercounts → K-06 |
| D-126 | Detect an unlinked near-duplicate variant at publish | N | Lab AD-16 identity table → K-06 |
| D-127 | Holdout touches are counted, and each touch spends it | P | seal built in `qmf-data`; no touch ledger → K-06, X-19 |
| D-128 | Projection vs rerun (a filtered view is not new evidence) | E | 45 DC-8, legacy DEC-0273 |
| D-129 | Hypothesis as an item with status computed from its tests | N | → K-04, X-2 |
| D-130 | Rejected board ideas become dead-end memory | E | Lab AD-18 |
| D-131 | Hypotheses from dead ends | E | template `rs6-hypotheses-from-dead-ends` |
| D-132 | Notebook cell graduates into a workflow node | P | Lab AD-9 `lab.cell`; hidden kernel state not handled → K-29 |
| D-133 | Results comparable only with the same procedure, data release and cost model | P | → K-34, X-21 |
| D-134 | Rerun a months-old result; a provider changed the model behind an alias | N | → K-34 |
| D-135 | MIS variants per scalper type in the Lab | → park | Lab OPEN-7 (risk session) |
| D-136 | Neural net training in the Lab on a rented GPU | P | `d6-ml-training-run` draft, AD-57 → K-23 |
| D-137 | Paper run as a daily schedule | E | Lab AD-12 |
| D-138 | Promotion is two human clicks | E | Lab AD-12, `qmf-registry` promotion skeleton |
| D-139 | Bad data feed discovered after 40 results used it | N | → K-07, X-1 |
| D-140 | Source correction arrives for history already used | P | legacy SCN-0002 bitemporal shape in `qmf-data`; nothing propagates to results → K-07 |
| D-141 | Indicator bug fixed; every result using v3 of it is suspect | N | → K-07 |

### G8. Placements, machines and remote work (Chaos Engineering)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-142 | PC sleeps mid-run; server schedules keep firing | E | 39 RP.3 |
| D-143 | Worker drops mid-chunk; retried elsewhere | E | AD-8, AD-20 |
| D-144 | Hub down; sidecar buffers; relays keep cached keys | E | L-AD-13, 39 RP.3 |
| D-145 | Run pass renewed by heartbeat on a long run | E | Library memlog (credential expiry renewed by heartbeat) |
| D-146 | Contabo runs an older QMX than the PC | N | → K-24, X-7 |
| D-147 | QMX upgrade while runs are in flight | P | AD-48 desktop host; drain and migrate not stated → K-24 |
| D-148 | Contabo RAM pressure with five sessions | E | AD-58 capacity table, AD-30 |
| D-149 | Data gravity: run where the dataset already is | N | → K-14, X-18 |
| D-150 | Bring a remote run home: replay it locally from fetched memo and logs | P | memo, replay and logs-as-Library-data exist; no fetch door → K-15 |
| D-151 | Provider onboarding from the provider's own docs | E | AD-30 |
| D-152 | Credentials once everywhere | E | AD-28 |
| D-153 | A standing "employee" agent with its own machine and routines | P | AD-55 agent item, ruling 60, Hermes H-106 → K-21 |
| D-154 | VM desktops rendered live | E | AD-32 `watch: true`, AD-33 |
| D-155 | Keep the computer awake while a turn is in flight | E | 37d H-74 → AD-48 |
| D-156 | Version skew between `qmx-node` and the PC host | N | AD-52 `--role node` exists; no version check → K-24 |

### G9. Operations, DevOps and attention (Failure Analysis; Starbursting)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-157 | One span shape for runs, sessions and app calls | P | AD-15 runs built; sessions as traces and app spans designed (45 DC-10) → K-15 |
| D-158 | "What is running where and why is it slow" answered by the copilot | N | → K-15, X-14 |
| D-159 | Resource use per run and per machine on run cards | P | AD-32 L14 fields; app heartbeat meters built → K-15 |
| D-160 | Cost and tokens per idea family (visibility, never a cap) | N | usage meter built per chat; no roll-up by subject → K-15 |
| D-161 | Incidents per error signature with closed app failure classes | P | 45 DC-10; engine signatures built (`ledger/signature.py`) |
| D-162 | Morning digest of everything since he last looked | P | templates `rv`, `db` exist; no "since last look" cursor → K-32 |
| D-163 | Inbox only for provider and harness failures | E | AD-17, ruling 77 |
| D-164 | Log retention off the small PC disk | P | logs as Library data (L-AD-13); PC retention not stated → K-15 |
| D-165 | Doctor and health page | E | doctor node built, AD-48 |
| D-166 | Capacity planning: "can I run 20 agents?" | P | heartbeats designed; no projection → K-15 |

### G10. Scheduling and market time (Time Shifting; Constraint Mapping)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-167 | Two workflows at London open compete for four slots | P | AD-58 queues; no priority → K-16 |
| D-168 | QMB machine queue shared by Lab sessions and overnight loops | E | AD-31 |
| D-169 | An app instance serialises its stateful operations | E | 45 DC-6 volume lease |
| D-170 | DST shift moves a cron | E | AD-10 IANA zone |
| D-171 | NFP release triggers pre- and post-event research | P | `t3-news-calendar-watch` draft; `event` and `webhook` kinds not built → K-17 |
| D-172 | Webhook flood or duplicate alert | N | dedupe by delivery id not stated → K-17 |
| D-173 | Webhook endpoint must live on the server, not the PC | P | gateway designed; home not stated → K-17 |
| D-174 | Catch-up after downtime: one run | E | EP12, ruling 54 |
| D-175 | Session loop and workflow both watch the same thing | P | → K-18 |

### G11. Providers and answer quality (probabilistic clipping)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-176 | Mixed providers per sub-agent, copilot and workflows | E | AD-29, AD-38 |
| D-177 | The same question to three cheap models; show the spread | N | → K-11, X-13 |
| D-178 | Fresh-context reruns for answers he will act on | N | → K-11 |
| D-179 | Maker and checker on different model families for validation | P | 44 §2.5 recommends; AD-13 labels only |
| D-180 | Model behind an alias changes; results drift | N | → K-34 |
| D-181 | Eval battery for the copilot | P | 44 DC-10 |
| D-182 | Toolsets cut 150 tools to about 20 | P | 44 §3 |
| D-183 | Tool search off on Chinese key providers | P | probe in 44 §2.2 |

### G12. Safety, secrets and permissions (Reverse Brainstorming: "how would we leak a key?")

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-184 | Keys never printed into logs, inbox or ledger | E | AD-37, ruling 116 |
| D-185 | A key pasted into a chat lands in a Library note | P | redaction seam on serve; no scan at land and no purge → K-27 |
| D-186 | Purge a secret from the bucket and replicas | N | → K-27 |
| D-187 | Guard denies secret files and store writes | E | AD-54 |
| D-188 | Agents never touch money; demo accounts only | E | ruling 116, AD-33 |
| D-189 | Standing grants approved at publish | P | 44 §3 |

### G13. Backup and disaster (Zombie Apocalypse Planning)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-190 | PC disk dies | P | git snapshots built (`backup.py`); Library replication designed (L-AD-16); restore order owed (45 §4.3) → K-33 |
| D-191 | Contabo dies; restore from the bucket | P | L-AD-16; drill owed → K-33 |
| D-192 | Restore drill as a scheduled workflow | P | L-AD-16 "drills" → K-33 |
| D-193 | Tick data backup and import | → park | data held (rulings 81, 91) |

### G14. Wildcards (Crazy 8s; What-If-The-World-Changed)

| Id | Idea | Tag | Where / what is missing |
|---|---|---|---|
| D-194 | QMX agents refactor QMX's own code | → park | ruling 118 unlocks design, not self-modification |
| D-195 | A second human (a partner) uses QMX | → park | single operator by design |
| D-196 | Several PCs | → park | one desktop app (ruling 40) |
| D-197 | The fifth quant lens | → park | ruling 112 |
| D-198 | The unit inside the trading node | → park | ruling 14 |
| D-199 | Telegram as a remote copilot door | → park | ruling 34 (later), 37d M-13 |
| D-200 | An idea's "story page" assembled from its whole history | P | explainers AD-45 + edges → folded into K-04 |
| D-201 | The copilot argues against him (devil's advocate mode) | P | ruling 5 "consider different angles" → folded into K-11 |
| D-202 | Overnight "red team" workflow tries to break yesterday's best result | P | QMB robustness built; schedule template not → folded into K-05 |
| D-203 | Regime detector labels every result with the regime it ran in | P | MIS `regime` slot (Lab AD-7) → folded into K-03 |
| D-204 | Library "time machine": rewind his whole research state to a date | P | → folded into K-26 |
| D-205 | Agents leave notes for each other on items (sticky notes) | E | shared request and reply artifacts (45 §2.6) |
| D-206 | An agent with a pet or skin | → park | Hermes pets and skins; no research value |
| D-207 | Weekly "what QMX learned" explainer | P | template `rv-weekly-review` → K-32 |
| D-208 | Show the cost of one hypothesis end to end | P | → K-15 |
| D-209 | QMX suggests which provider to rent when Contabo overflows | P | 39 §10 call 6 (money: his) → park |
| D-210 | Agent cursor overlays per session in shared browsers | E | 37d H-100 |
| D-211 | Screenshot eviction for computer-use token hygiene | E | 37d H-99 |
| D-212 | Data-feed health watcher pauses dependants automatically | N | → K-07 |
| D-213 | A quarantined input auto-unquarantines when corrected; reruns offered | N | → K-07 |
| D-214 | "Why is this number different from last week?": diff two runs node by node | P | `explain` built; no run diff → K-34 |

Count: 214 ideas. EXISTS 85, PARTIAL 73, NEW 44, parked at once 12 (more parked at convergence, §6).

---

## 4. Converge

**Move 1, Affinity Clustering.** The 214 ideas fall into nine clusters:
- A. The research spine: idea → hypothesis → test → verdict (D-027, D-129 to D-141, D-200 to D-202).
- B. Honest judging and accounting (D-071, D-072, D-123 to D-128).
- C. Bad news travelling: taint, supersede, corrections (D-054, D-139 to D-141, D-212, D-213, D-044).
- D. Time: validity, freshness, deadlines, calendars (D-041, D-090 to D-092, D-104, D-170, D-171).
- E. In-flight state across machines: claims, version skew, pause, ops (D-086, D-093, D-146, D-147, D-156 to D-166).
- F. Sessions and context (G1, G2).
- G. Mini-app ecosystem (G6).
- H. Workflow evolution: crystallise, steer, loops that outlive the laptop (D-014, D-076, D-077, D-099).
- I. Hygiene and safety (D-063 to D-065, D-185, D-186, G13).

**Move 2, relevance filter** against his purpose (a research and development assistant for trading, ruling 116), "design for complexity, not a complex system" (115), local by default with remote fully covered (117), no caps (106), Chinese models most (107), and nothing waits for him (57, 77). Out: anything that is a UI shape (UI session), data design (held, 91), trading-node depth (14), money paths (116), and other people.

**Move 3, ranking.** Each candidate was scored on value to his research cycle (the jobs J1-J11 in 44 §1.2) and on how much the design changes. Ideas that only restate an EXISTS item were not promoted to scenarios. They appear in §5.0 as covered.

**Root-cause pass (Five Whys on "why do rich scenarios break the design?").** Three causes sit under most of the kept scenarios (K-03, K-04, K-06 to K-09, K-13 to K-17, K-22, K-24 to K-28, K-34):
1. **Derived status over edges is missing.** Edges say what was used. Nothing turns a mark on an input into a mark on its outputs, or test outcomes into a hypothesis status (C, A, part of G).
2. **Time is missing from rows.** Lessons, outputs and schedules have no validity window, freshness or deadline (D).
3. **Live facts do not cross machines.** In-flight builds, host versions and a pause flag are not on the heartbeat (E).

Each has one simple mechanism (§7, X-1, X-4, X-6) that rides on designed parts: Library edges (L-AD-4), memory rows (AD-18) and heartbeats through the Hub (L-AD-13).

---

## 5. Scenario catalogue

### 5.0 Covered already (EXISTS): no design change

| Scenario he named or the room raised | Answer on the ground |
|---|---|
| Library version control for concurrent agents | L-AD-7 (one owner per ref, compare-and-swap, three-way merge, conflict objects), L-AD-20, engine AD-49; 45 §5.16 |
| Remote workflows reach the Library | L-AD-11 to L-AD-13 (Hub, run passes, sidecar); 45 DC-11; 39 RP.3 |
| Agentic vs non-agentic workflows | AD-2 one format; `script`, `monitor`, `rule` nodes built; a run with no model node spends no tokens |
| Provider limit mid fan-out; mixed providers per sub-agent | AD-9, AD-29, AD-38, AD-40; EP11 built; 39 §8 and RP.3 |
| 300-video playlist; Firecrawl pipeline | AD-34 chunking (built); SOLUTION-DESIGN §26.13 |
| Credentials on a new machine; provider onboarding | AD-28, AD-30 |
| App asks app; no permission union | 45 DC-7 |
| App self-feed loop ends | 45 DC-12 |
| Workflow grows into a mini app | 45 §2.5a; builder skill `build-mini-app` built (rebuild era) |
| Shared browser with his logins; take-over | AD-44 |
| Demo-broker setup by agents | ruling 108, AD-33 |
| Two copilots edit one Lab draft | 45 A17, L-AD-7 S-11 |
| Archive refuses while pinned | 45 §2.3 |
| Catch-up after downtime | EP12 built |
| Capacity queues, interactive reserve | AD-58; `admission.py` built |

### 5.1 Kept scenarios

Each entry gives: **Tag**, **Domains crossed**, **Expected**, **Edges and failures**, **Simplest mechanism**, **Covered**, **Missed**, **Blast radius**.

#### K-01. One idea, end to end: video → hypothesis → tests → verdict → paper — PARTIAL
- **Domains crossed:** intake workflows, Library, memory, Lab, QMB, copilot (hub and Lab), explainers, paper.
- **Expected:** He drops a video in the hub. Intake writes notes with locators back to the video's minute marks. The copilot frames two hypotheses. A Lab session runs sweeps on a draft bot through the published procedure, so the results land as evidence. A nightly loop runs robustness. Each hypothesis then shows supported, refuted or open, with the path back to the minute of the video that started it. Survivors go to paper by his click.
- **Edges and failures:** the video is deleted after intake (the notes keep the blob hash, AD-42 stores first); two hypotheses share one test (a result `tests` both); a hypothesis is restated in other words a month later (recall by item and by text, K-03).
- **Simplest mechanism:** existing kinds and edges, plus a `hypothesis` record kind (X-2) and a locator attribute on `derived-from` (X-24).
- **Covered:** intake templates; 45 DC-8 (evidence); Lab AD-6 (families); Lab AD-12 (paper); AD-45 (explainers).
- **Missed:** hypothesis status (X-2); source locators (X-24).
- **Blast radius:** one kind schema; one edge attribute; Lab board text (AD-18).

#### K-02. A session moves between places and pulls context from anywhere — PARTIAL
- **Domains crossed:** harness chat record, Library, multimodal layer, browser, memory, apps.
- **Expected:** In the Lab he attaches pod v7, the macro app's latest `bias`, a folder and a video. He reopens the session in the hub next day. The same references are there, each shown as a short excerpt plus a link. The pod shows "v8 exists" because he pinned v7. The app output follows the latest because he chose "follow".
- **Edges and failures:** the video is still being transcribed (the reference shows "pending" and resolves on a later turn); a folder of 2,000 files (the Hermes caps: 200 entries, 25 % soft and 50 % hard of context, H-112); an attached item is archived (the reference stays readable, marked archived); the reference points at a remote-only blob while offline ("not cached" with a fetch on reconnect).
- **Simplest mechanism:** an `attached` list on the session item. Each entry is `{item_id, pin: version | follow, version_id?, status: ready | pending | archived}` (X-3). Reading resolves pins, and the excerpt is built at turn time by the context package of 44 §2.6.
- **Covered:** 45 §2.9 (references, never copies); 44 §2.6 (context references); AD-35 (home and resume); AD-42; H-112.
- **Missed:** where the list lives (the dropped `session_homes` table); the pin policy; pending references.
- **Blast radius:** L-AD-21 (memlog only, needs its spine edit); AD-35 wording; the harness `NewChat` field set (AD-53); the UI composer.

#### K-03. Memory follows the subject, respects regimes, and can forget — PARTIAL
- **Domains crossed:** memory (Hindsight plus the built-in fallback), Library memory rows, copilot, workflows, Lab, router.
- **Expected:** A nightly loop learns "London breakout on EURUSD fails when 20-day ATR is below its median, Q2 2026". In Q4 he proposes London breakouts in the hub. Recall by `item:` and by text surfaces the lesson with its window and regime. The copilot says "refuted in Q2 in a low-volatility regime; current regime differs" and offers a fresh test instead of a refusal.
- **Edges and failures:**
  - Two lessons conflict: consolidation keeps both with their windows (Hindsight observations keep history; AD-18 `correct`).
  - A lesson came from a run whose input was later tainted: it inherits the mark (K-07).
  - He says "forget that": the row is archived, Hindsight deletes it by id, and `rebuild` never re-adds archived rows.
  - Hindsight's retain and reflect need a model: they go through QMX's router with a role, never with their own key (AD-28).
  - PC offline: the FTS5 adapter answers from the same rows.
- **Simplest mechanism:** AD-18 rows gain `valid_from`, `valid_to` (nullable) and `regime` tags. Recall passes the session's "now" and the current regime label as filters or boosts. `forget(row_id)` = archive + `RecallEngine.delete(row_id)`. Banks by writer trust (44 §2.6.4).
- **Covered:** AD-18; 44 §2.6.4 (`RecallEngine`, two adapters, banks, tags); Hindsight's temporal recall arm [retrieved: hindsight.vectorize.io, "Temporal — time expressions parsed into a window"].
- **Missed:** validity and regime fields; the forget path; routing Hindsight's model calls; recording "Hindsight is the default" as a ruling change (44).
- **Blast radius:** AD-18 row schema; 44's `RecallEngine` gains `delete`; the router gains a `memory` role; UI memory view.
- **Probe:** P-MEM: on his real rows, does Hindsight delete by document id remove derived observations, and does temporal recall honour a window? (Hindsight docs say observations keep evidence links; whether deleting a source fact re-consolidates is unverified.)

#### K-04. The hypothesis ledger — NEW
- **Domains crossed:** Library, Lab, memory, workflows, explainers.
- **Expected:** Every hypothesis is an item. Results link to it with `tests`, and the result carries its own outcome (supports, refutes, inconclusive) as a field, because "an edge is about, not true" (45 §3.3 point 4). The hypothesis's status is computed at read time from its admitted evidence: evidence-door results only, not exploration (45 DC-8). It is never stored, so it cannot go stale. Status counts family trials (K-06) and taint (K-07). Dead ends (Lab AD-18, AD-18 tags) link to the hypothesis they killed.
- **Edges and failures:** a result is later tainted, so the status recomputes to "open"; conflicting evidence across regimes yields "mixed, by regime"; an agent writes "supported" in prose without a linked evidence result, so the status ignores it.
- **Simplest mechanism:** one `hypothesis` kind (class `record`; 45 DC-1 makes kinds data), one relation `tests` added to the closed set (L-AD-4), an `outcome` field on result kinds, and a status function shared by the Library read and the UI.
- **Covered:** templates `rs0-idea-grill` and `rs6-hypotheses-from-dead-ends`; Lab AD-18; `qmf-registry` typed edges.
- **Missed:** the kind, the relation and the status function.
- **Blast radius:** L-AD-3 roster (or a schema file after DC-1); L-AD-4 relations; Lab AD-18 wording; the UI shelf. **Word for him:** "hypothesis" (§6).

#### K-05. Honest numbers everywhere — PARTIAL
- **Domains crossed:** QMB, Lab, explainers, copilot, Library search.
- **Expected:**
  - An explainer's numbers are references to fields of result items, rendered by QMX, never typed by the model.
  - Every claim sentence that cites items is checked against them (the clipping's gate 6). A citation outside the admitted set is stripped (the clipping's citation bug).
  - A strategy's report includes a matched control: the same procedure with the entry signal replaced by random entries at the same frequency, so leakage shows as "the control also made money".
  - An overnight "red team" run tries to break yesterday's best result with the built QMB robustness ladder.
- **Edges and failures:** a model rounds 1.47 to 1.5 in prose, so the rendered value wins and the prose is flagged; a number exists in no artifact (rendered as "unverified"); the control beats the strategy, so the result is marked "no edge over random".
- **Simplest mechanism:** an AD-45 directive `::value{item, field}`; a deterministic citation filter; a grader mode `claims` (entailment check by a family-separate judge, 44 §2.5); one procedure option `control: random_entries` in QMB's sweep.
- **Covered:** QMB robustness (walk-forward, carve-out, perturbation, trade-order shuffle, significance), built; 45 DC-8; AD-45; graders (built, deterministic mode).
- **Missed:** value binding; citation filter; matched-control procedure; claim grader mode.
- **Blast radius:** AD-45; grader modes (AD-5); one QMB procedure option (QMB session); Lab procedure template.

#### K-06. Family and holdout accounting across every agent and machine — PARTIAL
- **Domains crossed:** Lab, Library edges, QMB, workflows on Contabo, mini apps, qmf-data.
- **Expected:** He, a nightly loop and a mini app each try variants of one idea on two machines. The family's trial count includes all of them, and the luck warning (Lab AD-6) uses that count. Any read of the sealed holdout goes through the QMB door and is recorded as a touch on the family. A second touch shows "holdout already used once".
- **Edges and failures:** an agent creates a variant as a new bot with no `variant-of` edge. The identity table (Lab AD-16) and a structural similarity check at publish propose the edge, and the trial is counted pending his confirmation. An agent reads holdout-period bars through a general data tool: refused by qmf-data's seal, which is built.
- **Simplest mechanism:** an edge `touched-holdout` from a run to the family's root; the family count is computed from edges; a similarity check at publish (logic hash plus parameter-space overlap).
- **Covered:** seal built (`qmf-data`); Lab AD-5, AD-6, AD-16; legacy SCN-0003, FEAT-0015.
- **Missed:** the touch ledger and the similarity check.
- **Blast radius:** L-AD-4 relation; Lab AD-6 text; one publish check.

#### K-07. Bad news travels: taint, supersede and recover — NEW
- **Domains crossed:** data, Library, Lab results, memory, workflows, triggers, mini apps, explainers.
- **Expected:** He finds that a feed had wrong prices for March. He marks dataset release r12 `quarantined`. At read time every result, lesson, hypothesis status and app output built on r12 shows "built on quarantined input" with the path. Enabled triggers whose pinned inputs descend from r12 pause with one card. When r13 corrects it, "rerun on r13" is offered per family, and memoised nodes that did not consume r12 are reused (AD-7).
- **Edges and failures:**
  - An indicator v3 bug: same flow, marked on the component version.
  - A garbage workflow poisoned memory: rows inherit the mark and recall down-weights them.
  - A secret leak is different (K-27).
  - A mark on a widely used item: the walk is bounded by an index and computed on demand per item shown, never as a batch over the whole Library.
  - Removing the mark clears every derived mark at once, because nothing was stored.
- **Simplest mechanism (X-1):** marks `quarantined | superseded | corrected` live on root items only. "Derived mark" is a read-time function: walk `consumed` and `derived-from` up to the roots and report the worst mark with its path. Preflight (AD-20) refuses to fire a trigger whose pinned inputs carry a derived `quarantined`.
- **Covered:** edges (L-AD-4, built in `qmf-registry`); legacy SCN-0002 bitemporal corrections (`qmf-data`); preflight (built).
- **Missed:** marks, the derived read and the preflight rule.
- **Blast radius:** L-AD-4 and L-AD-9 (one verb `marks(item)`); AD-20 preflight; Lab family views; memory recall weighting; UI badge.
- **Probe:** P-TAINT: walk cost on a synthetic 100k-item edge table in SQLite (45 DC-15's store).

#### K-08. The Lab and a mini app use one object; inputs move on — EXISTS + small
- **Expected:** As in 45 §5.16. In addition, a result built on dataset v3 shows "newer input v4 exists" (a derived `superseded` from X-1) and offers a rerun.
- **Missed:** only the superseded mark (X-1). Blast radius: none beyond X-1.

#### K-09. Mini apps feed mini apps across machines, and change over time — PARTIAL
- **Domains crossed:** apps, Library, triggers, Hub, app check.
- **Expected:** The macro app (Contabo) provides `bias`. Session filter (PC) and signal (Contabo) feed on it. When macro publishes v2 with a changed `bias` schema, `qmx app check` lists every consumer pinned to the old contract and fails until each is compatible, adapted, or explicitly left on v1. Consumers declare `coalesce: latest` when only the newest bias matters. Producers declare `stale_after`, and a consumer reading an older output gets `stale: true`.
- **Edges and failures:** a producer floods (coalesce); a producer dies (consumers read the last good output, marked stale); fan-in (dedupe per trigger and object, 45 DC-3); a consumer on a sleeping PC (the trigger's home decides, AD-10).
- **Simplest mechanism (X-5):** `provides.<name>.stale_after`; trigger field `coalesce: each | latest`; a consumer list from edges at app check.
- **Covered:** 45 DC-3, DC-6, DC-12; F1-F3 proven schema checks.
- **Missed:** the contract-break check, freshness and coalesce. AD-19 still says `emits` and `accepts` (fold DC-3 first).
- **Blast radius:** `app.toml` schema; trigger row (with the planned `event` migration); `qmx app check` steps; AD-19.

#### K-10. One app, many setups — NEW
- **Expected:** He wants "macro analysis for one pair" (ruling 18) for seven pairs. One `macro` pack declares a `[profiles]` schema (pair, session, sources). Each profile is a small config item. Operations take `profile`, instance state is partitioned by profile key, and triggers are per profile.
- **Edges and failures:** a profile edited mid-run (the run pins the profile version); one profile's state corrupt (only that partition restores from snapshot); a new profile needs a new skill (that is a variant pack, the 45 A15 path).
- **Simplest mechanism (X-12):** a profile is a `record` item (no publish gate); an operation descriptor gains an optional `profile` parameter; the supervisor keeps one process and partitions `data/` by profile.
- **Covered:** 45 A15 (one instance per home), DC-2, DC-6.
- **Missed:** profiles. **Blast radius:** operation descriptor; `qmx_apps` volume layout (built code, additive); UI app card.

#### K-11. Ask the panel; show the spread — PARTIAL
- **Domains crossed:** copilot, apps' agents, router (mixed providers), workflows, explainers.
- **Expected:** "Should EURUSD longs be on this week?" The panel template asks the macro, sentiment and positioning app agents through their `ask` operations, and two extra models on fresh contexts. A judge lists the points of agreement, the points of disagreement, and which disagreement matters most. The explainer shows the spread, not one confident answer. Every copilot answer on an open question follows the clipping's discipline: claims labelled retrieved, remembered or inferred; candidates before the pick; ranges stated with a coverage level.
- **Edges and failures:** one panel member times out (shown as absent, not silently dropped); all members agree on a checkable fact (agreement noted as weak evidence); a member is on the same family as the judge (labelled, AD-13).
- **Simplest mechanism (X-13):** a shipped template (parallel `ask` operations plus a judge node) and a prompt-slot rule in the methodology (B29). No engine change.
- **Covered:** 45 DC-7; AD-38 mixed providers; ruling 5.
- **Missed:** the template and the prompt rule. **Blast radius:** templates; prompt slots (44 §2.1). **Probe:** spread on 20 of his real questions across three providers.

#### K-12. Four writers on one workflow — EXISTS + one gap
- **Expected:** He edits workflow W. The copilot drafts a fix. Self-improvement replays a challenger (AD-26). A remote run reads the pinned version. Each writer has its own ref, and merges are explicit.
- **Missed:** a named merge driver for `qmx.workflow/1`: three-way per node id and per parameter, with a conflict per node. Without it, JSON text merges of graphs produce invalid definitions.
- **Blast radius:** L-AD-7 driver list; engine `definition/` (a merge function beside `validate`). **Probe:** none; property tests on random graph edits.

#### K-13. Two runs start the same build at once — PARTIAL
- **Expected:** At 07:00 the PC's intake and Contabo's watcher both start extracting the same paper. The second sees a live claim on the intent key and waits, then links to the first's output.
- **Edges and failures:** the claimant dies (claim TTL is renewed by its heartbeat, so a dead claim expires); the Hub is unreachable (claim locally and accept a rare duplicate, which is honest and the same rule as AD-8's accepted duplicate spend).
- **Simplest mechanism (X-6):** `claim(intent_key, run_id, ttl)` beside `check_built`, held on the Library primary, renewed by the sidecar heartbeat.
- **Covered:** AD-27 (finished work), trigger fire claims (built pattern).
- **Missed:** in-flight claims. **Blast radius:** AD-27; the engine's Library port (a verb); L-AD-9. **Probe:** latency through the Hub (fold into 45 P-EV).

#### K-14. Remote work and data gravity — PARTIAL
- **Expected:** A 40 GB tick dataset lives on Contabo. A sweep placed by preference picks Contabo because the blobs are local. A rented GPU fetches only what it needs and caches by hash.
- **Edges and failures:** cache eviction mid-run (refetch by hash); the bucket is slow (the preflight score includes the estimated fetch); the PC asks for a remote-only blob offline ("not cached").
- **Simplest mechanism (X-18):** placements report cached blob hashes and free disk on the heartbeat; preflight adds a locality score.
- **Covered:** L-AD-10 to L-AD-14; AD-20, AD-30; 45 DC-11.
- **Missed:** the locality score and the worker cache. Data design is held (ruling 91), so this names the seam only. **Probe:** P-APP from 45, plus fetch timing.

#### K-15. One ops picture across machines — PARTIAL
- **Domains crossed:** engine spans, harness journals, app heartbeats, Hub, router journal, capacity table.
- **Expected:** He asks "what is running and why is the morning brief slow?" The copilot's `ops` toolset reads spans, heartbeats, the capacity queue and the router journal, and answers: "brief waited 14 minutes for a chat slot on Contabo; 5 of 4 slots in use by the playlist fan-out". Spend per hypothesis family is visible as tokens and machine minutes (never a cap). A remote failure can be brought home: the copilot fetches its memo and logs and replays it locally.
- **Edges and failures:** heartbeat volume from 20 agents on 12 GB; logs filling the PC disk (logs stay on the server by default, and the PC keeps an index); the Hub lags (the doctor shows the lag).
- **Simplest mechanism (X-14):** a read-only `ops` toolset over existing stores; `runs.fetch_home(run_id)`.
- **Covered:** 45 DC-10; AD-15, AD-32, AD-58; usage meter (built); `ledger/spans.py` (built).
- **Missed:** the toolset, the roll-up by subject and the fetch door. **Blast radius:** tool catalog rows (44 §3.4); Hub heartbeat ingestion; run cards. **Probe:** P-OPS, heartbeat volume.

#### K-16. Scheduling in market time, under contention — PARTIAL
- **Expected:** The brief must be ready by 07:30 London. The trigger card shows "last 10 runs took up to 48 min; start by 06:42", and he sets the cron. No runs fire while FX is closed (the `market_open` precheck uses the built forex calendar). When slots are short, a `priority: high` trigger is served before background fan-out chunks.
- **Edges and failures:** DST (IANA zone, built); a holiday (calendar); two high-priority triggers (FIFO among equals); a long fan-out starving others (priority applies per chunk at admission, so a low-priority fan-out yields between chunks).
- **Simplest mechanism (X-8):** trigger fields `priority` and an advisory `ready_by`; a shipped precheck script calling `qmf-calendar-forex`; the admission queue orders by priority, then age.
- **Covered:** AD-10, AD-31, AD-58; calendar extension (built); precheck (built).
- **Missed:** priority, ready-by and the shipped precheck. **Blast radius:** trigger row migration (already planned); `admission.py` order (built code, small).

#### K-17. Market events drive work — PARTIAL
- **Expected:** A TradingView alert webhook and the NFP calendar both start workflows. The webhook endpoint lives on Contabo, so the PC can sleep. Duplicate deliveries dedupe by delivery id. A flood coalesces (K-09).
- **Simplest mechanism:** the designed `webhook` trigger with `home: contabo` by default and `delivery_id` dedupe; an `event` trigger on calendar items landed by a calendar workflow.
- **Covered:** AD-10 design; `t3-news-calendar-watch` draft; calendar built.
- **Missed:** the default home and dedupe rule. **Blast radius:** AD-10 text; gateway.

#### K-18. A copilot loop outlives the laptop — NEW
- **Expected:** In the hub he says "watch the ECB speakers and tell me if the bias flips". The copilot starts a session loop (AD-47). When he closes the laptop, or on his click, "Run on the server" turns the loop into a workflow: its prompt becomes an agent node, its cadence a trigger on Contabo, its output a landed artifact. The session gets a digest line on resume and links to the runs.
- **Edges and failures:** the loop used session context (the attached references move with it as inputs, K-02); the loop needs his logged-in browser (stays local, with a note why).
- **Simplest mechanism (X-9):** a builder-skill action plus one UI button; no engine change.
- **Covered:** AD-47, AD-22, AD-30. **Missed:** the conversion. **Blast radius:** builder skill; UI loop card.

#### K-19. Workflows crystallise — NEW
- **Expected:** After 30 runs of the paper-scout template, the curator sees that the "classify source" agent step always produces one of four labels from title patterns. It proposes a script challenger. AD-26 replays it against the fix and guard sets, and it becomes champion. When the script's own check fails on a new input shape, that item falls back to the agent step.
- **Edges and failures:** the script silently mislabels (the guard set catches it in replay; production disagreement sampling, one in N items also sent to the agent, keeps measuring).
- **Simplest mechanism (X-10):** a new self-improvement move "crystallise" (AD-26), with a `rule` node routing to the script and falling back to the agent.
- **Covered:** AD-22 traces-first, AD-26, `rule` and `script` nodes (built).
- **Missed:** the move and the fallback pattern. **Blast radius:** AD-26 move list; one template pattern. **Probe:** equivalence over 20 replays on one template.

#### K-20. Steer a running workflow — PARTIAL
- **Expected:** At 02:00 he sees the fan-out wasting time on podcast episodes. He says "skip audio-only items and use GLM for the rest". The run stops. A new run starts from that node with an overlay, reusing every finished node's memo.
- **Simplest mechanism (X-11):** `runs.fork(run_id, from_node, overlay)` over the built replay; the new run links `forked-from`.
- **Covered:** AD-7 (node replay built in EP5), drafts and overlays (built `definition/overlay.py`). **Missed:** the door. **Blast radius:** engine service API; run card.

#### K-21. A standing research employee — PARTIAL
- **Expected:** "Macro Analyst" is an agent pack with its persona, skills, memory bank, routines (triggers) and a home placement on Contabo. He chats with it in its own session. Apps and workflows reach it through its `ask` operation.
- **Edges and failures:** its machine is down (routines wait on placement; `ask` returns "home unreachable" plus the last landed brief); two employees disagree (K-11).
- **Simplest mechanism:** an `agent` item (AD-55) plus triggers with `home` plus an `ask` operation; nothing new except stating the composition.
- **Covered:** AD-55, AD-30, 45 DC-6, DC-7; ruling 60. **Missed:** the composition written down, and a session home `agent` (homes are `general | lab | portfolio | library | app`). **Blast radius:** AD-35 home kinds (one value); a template.

#### K-22. A mini app breaks at 3 a.m. — PARTIAL
- **Expected:** The sentiment app crash-loops on Contabo. The supervisor restarts it, then stops after the crash-loop counter. One incident is raised with class `dependency`. Consumers read the last good output marked stale (X-5). In the morning the copilot has a fix drafted for his publish.
- **Missed:** blame attribution when a consumer's schema check refuses a producer's output (the incident is filed on the producer); freshness (X-5).
- **Covered:** 45 DC-10; `qmx_apps` supervisor (built). **Blast radius:** incident fields; X-5.

#### K-23. Long training on a rented GPU — PARTIAL
- **Expected:** A neural net trains on Modal. The node declares `checkpoint: ckpt/`; the sidecar flushes it; preemption restarts the attempt from the latest checkpoint, not from zero. The model lands as a `model` item with its training run.
- **Simplest mechanism (X-20):** a node contract field `checkpoint` that retry honours (resume, not restart); `gpu` as a resource class in the AD-58 table.
- **Covered:** L-AD-13 (5-second checkpoints), AD-57, `d6-ml-training-run`, Modal and E2B adapters (built). **Missed:** the resume contract and the GPU class. **Blast radius:** AD-4, AD-58; template. **Probe:** a preemption drill once a GPU provider is paid for (money: his call).

#### K-24. Version skew and upgrades — NEW
- **Expected:** He updates QMX on the PC. Contabo's `qmx-node` is one version behind. A workflow using a new node kind is placed only where the kind exists, or waits with "node needs update". Runs in flight on the PC drain before the host restarts, and their attempts resume after (AD-7).
- **Simplest mechanism (X-7):** heartbeats carry `qmx_version` and a digest of the node-kind registry; preflight compares them. The desktop host drains before an update.
- **Covered:** AD-20 preflight, AD-48, AD-52 `--role node`. **Missed:** the version facts and drain. **Blast radius:** heartbeat schema; preflight; AD-48.

#### K-25. Library hygiene at scale — PARTIAL
- **Expected:** After six months, 200k items, half from noisy fan-outs. Search ranks results from passed live runs and his own items above test-run refs and low-grade outputs. Test-run refs older than 30 days and never cited are archived by the curator. Storage stays cheap (ruling 42), so nothing is deleted.
- **Simplest mechanism (X-15):** ranking features (producer status, grade, citations); a curator rule for records.
- **Covered:** 45 DC-15, AD-46 curator, L-AD-6. **Missed:** the ranking features and the record retention rule. **Probe:** extend 45 P-SRCH with noise.

#### K-26. Ask QMX about its own past — PARTIAL
- **Expected:** "What did we learn about London breakouts, and what did the Library look like when I promoted bot B?" The answer comes from Library search (pipeline, admission reason per item), memory recall and run traces, with as-of reads from the ref log.
- **Missed:** an `as_of` parameter on reads and search (the ref log already holds the history). **Blast radius:** L-AD-9 verbs.

#### K-27. A secret lands in the Library — NEW
- **Expected:** He pastes an API key into a chat, and the copilot's note lands. A scan at landing (the AD-37 seam) catches token shapes and refuses the land. If one slips through, "purge" (his click only) replaces the blob with a tombstone in the store, the replicas and the bucket, and logs the purge.
- **Simplest mechanism (X-16):** redaction at land, not only at serve, plus one operator-only purge. This is the only exception to archive-never-delete.
- **Covered:** AD-37, AD-54, AD-23 (token literals refused in definitions, built). **Missed:** scan at land and purge. **Blast radius:** L-AD-6 exception; L-AD-16 replication; backups. **Probe:** a purge drill to the bucket.

#### K-28. Pause all autonomy — NEW
- **Expected:** He sees something wrong and clicks "pause everything". All hosts stop claiming trigger fires within one tick. Running attempts finish their current node, and new nodes wait. Copilot chats are unaffected. "Resume" restores, with one catch-up per trigger (AD-10).
- **Simplest mechanism (X-17):** one setting flag synced through the Hub; the ticker checks it before claiming.
- **Covered:** per-trigger disable (built). **Blast radius:** AD-10 text; Hub fact sync.

#### K-29. A notebook cell graduates into a workflow — PARTIAL
- **Expected:** A cell that computes a regime label becomes a `script` node. Its inputs are the variables it reads from earlier cells (detected, then confirmed by him or the copilot). Its outputs are declared.
- **Covered:** Lab AD-9 (`lab.cell` nodes), 45 DC-9 (board as draft). **Missed:** dependency capture. **Probe:** graduate five real notebooks.

#### K-30. Fork a session for parallel what-ifs — PARTIAL
- **Expected:** "Try both: tighter stops, and a session filter." The copilot forks. Each fork is a session with the same home and attached references and its own agent ref. A compare explainer follows, and he keeps one.
- **Covered:** AD-41, L-AD-7. **Missed:** fork as a session operation. **Probe:** the SDK session fork (37d H-75 probe).

#### K-31. His clippings flow into research — PARTIAL
- **Expected:** New Obsidian clippings are picked up hourly, deduped by hash, summarised, linked to hypotheses, and shown in the morning digest.
- **Mechanism:** existing pieces only (interval trigger, hashing script, intent key, intake blocks). The missing piece is a template.

#### K-32. The morning digest — PARTIAL
- **Expected:** One explainer: what ran, what landed, which hypotheses moved, what failed and needs him (ranked), since his last look.
- **Mechanism:** a workflow over the Library ref log from an operator cursor; templates `rv` and `db` are close. No mechanism change beyond the cursor row.

#### K-33. Disaster recovery — PARTIAL
- **Expected:** The PC disk dies. He reinstalls, pairs with Contabo, the Library restores from the server primary or the bucket, the engine ledger restores from its backup, and apps restore from snapshots, in a stated order. A monthly drill workflow proves it.
- **Covered:** `backup.py` (built), apps backup (built), L-AD-16. **Missed:** the restore order across stores (45 §4.3, legacy DEC-0440). **Owner:** the data study (ruling 91); named here only.

#### K-34. Reproduce a months-old result — PARTIAL
- **Expected:** "Rerun last March's best bot." The rerun pins the procedure version, data release, cost model, engine version and the resolved model id. When the numbers differ, a node-by-node run diff shows where. "Provider model changed" is shown when the resolved model id differs under the same alias.
- **Simplest mechanism (X-21):** a comparability key on results; resolved model id and provider on every span (AD-15); a run diff over memos.
- **Covered:** AD-7, AD-15, `explain` (built), 44 surface digest. **Missed:** the key, the diff and the drift note.

---

## 6. Parked but interesting

| Idea | Why parked | When it could return |
|---|---|---|
| Source reliability score per channel (D-037) | Useful but not core; needs months of outcomes | After the hypothesis ledger (K-04) has data |
| Library as markdown he can grep (D-052) | Agents already read through tools | If he wants Obsidian sync |
| Trajectory export for fine-tuning his own models (D-096) | ML on his traces is speculative | Lab ML maturity |
| Mixture-of-agents virtual model (D-097) | The panel template (K-11) covers the need without a new provider type | If panel latency hurts |
| Darwinian evolution of indicators or prompts (D-098) | Fits generation; risks family explosion | After K-06 accounting exists |
| MIS variants in the Lab (D-135) | Lab OPEN-7, risk session | Risk session |
| App marketplace or sharing (D-118), second user (D-195), several PCs (D-196) | Personal desktop app | Never, unless he changes it |
| QMX refactoring itself (D-194) | Out of scope | — |
| Tick data backup and import (D-193) | Data held (rulings 81, 91) | Data study |
| Fifth lens (D-197), unit in node (D-198) | Rulings 112, 14 | His call |
| Telegram, phone, voice (D-019, D-020, D-199) | Rulings 34, 85 | Later |
| Burst provider advice (D-209) | Money is his call | When Contabo overflows |
| Pets and skins (D-206) | No research value | — |

**Two words for him, with defaults** (vocabulary only; nothing waits on them):
1. **"Hypothesis"** as a thing on a Library shelf. Default: yes, a shelf named "Ideas" whose items show supported, refuted or open.
2. **"Forget"** for a memory. Default: forget hides it from every recall and keeps an archived copy he can restore. Only secrets are truly purged (K-27).

---

## 7. Design changes for the architect, ranked

Ranking = value to the research cycle × how much the design changes, with shared mechanisms first. Every change extends something that exists. None adds a store, a service or a QMX cap. Prerequisites from 44 and 45 are named, not repeated.

| Rank | Change | Scenarios | Domains crossed | Extends (EXISTS) | Blast radius | Probe |
|---|---|---|---|---|---|---|
| 1 | **X-1. Marks on roots, derived at read.** `quarantined \| superseded \| corrected` on an item; `marks(item)` walks `consumed` and `derived-from` and returns the worst mark with its path; preflight refuses triggers on quarantined inputs; recall down-weights marked rows | K-07, K-08, K-04, K-03, K-25 | Library, Lab, memory, engine, apps, UI | L-AD-4 edges (`qmf-registry` built), AD-20 preflight (built) | L-AD-4, L-AD-9 (one verb), AD-20, Lab AD-6, AD-18; UI badge | P-TAINT (walk cost at 100k items) |
| 2 | **X-2. Hypothesis kind and computed status.** Kind `hypothesis` (record), relation `tests`, result field `outcome`, status function over evidence-door results | K-04, K-01 | Library, Lab, workflows, explainers | 45 DC-1 (kinds as data), DC-8 (evidence door), Lab AD-18 | one schema, L-AD-4 relation, Lab AD-18 text | none |
| 3 | **X-3. `attached` on the session item, with pin policy and pending status** | K-02, K-18, K-30 | harness, Library, multimodal | 45 §2.9, 44 §2.6, AD-35, L-AD-21 (memlog) | L-AD-21 spine edit, AD-35, AD-53 `NewChat` | none |
| 4 | **X-4. Memory rows gain validity window and regime; forget path; Hindsight default via the router** | K-03 | memory, router, Library | AD-18, 44 §2.6.4 `RecallEngine` | AD-18 schema, `RecallEngine.delete`, router role `memory`; record the Hindsight-default ruling change | P-MEM |
| 5 | **X-6. In-flight intent claims** `claim(intent_key, run_id, ttl)` beside `check_built`, renewed by heartbeat | K-13 | engine, Library, Hub | AD-27, trigger claim pattern (built) | AD-27, engine Library port, L-AD-9 | fold into 45 P-EV |
| 6 | **X-5. App contract evolution:** consumer contract check at producer publish; `stale_after` on `provides`; `coalesce` on feeds triggers | K-09, K-22 | apps, triggers, app check | 45 DC-3 (fold first), DC-12; F1-F3 (built) | `app.toml`, trigger row, `qmx app check`, AD-19 | none |
| 7 | **X-19. Holdout touch ledger and variant similarity check at publish** | K-06 | Lab, QMB, Library, qmf-data | seal (built), Lab AD-6, AD-16 | L-AD-4 relation, Lab AD-6, publish check | none |
| 8 | **X-14. `ops` toolset and "bring a run home"** | K-15 | engine, harness, apps, Hub, router | 45 DC-10, AD-15, AD-32, AD-58 | tool catalog rows (44 §3.4), Hub ingestion, run cards | P-OPS |
| 9 | **X-11. Fork a run from a node with an overlay** | K-20 | engine | AD-7 replay, `definition/overlay.py` (built) | engine service API, run card | none |
| 10 | **X-9. Promote a session loop to a server workflow** | K-18 | harness, engine, placements | AD-47, AD-22 | builder skill, UI loop card | none |
| 11 | **X-10. "Crystallise" as a self-improvement move, with agent fallback** | K-19 | engine, curator | AD-26, AD-22, `rule` and `script` nodes (built) | AD-26 move list, template pattern | equivalence on 20 replays |
| 12 | **X-8. Trigger `priority` and advisory `ready_by`; shipped `market_open` precheck** | K-16, K-17 | engine, QMF calendar | AD-10, AD-58, `admission.py`, calendar (built) | trigger migration (planned), admission order | none |
| 13 | **X-12. App profiles** | K-10 | apps, operations | 45 DC-2, DC-6, `qmx_apps` volumes (built) | operation descriptor, volume layout | none |
| 14 | **X-7. Host version and kind digest on heartbeats; drain before update** | K-24 | desktop host, placements, Hub | AD-20, AD-48, AD-52 | heartbeat schema, preflight, AD-48 | update drill |
| 15 | **X-13. Panel template and answer discipline (labels, candidates, ranges, spread)** | K-11 | copilot, apps, router, methodology | 45 DC-7, AD-38, prompt slots (44 §2.1) | template, B29 prompt slot | spread on 20 real questions |
| 16 | **X-21. Comparability key, resolved model id on spans, run diff** | K-34 | Lab, engine, router | AD-7, AD-15, `explain` (built) | result schema, span fields, explain | none |
| 17 | **X-24. Locator attribute on `derived-from`** | K-01, K-31 | intake, Library | L-AD-4 | edge schema | none |
| 18 | **X-15. Search ranking by producer status and citations; record retention rule** | K-25 | Library, curator | 45 DC-15, AD-46 | L-AD-8, curator | extend P-SRCH |
| 19 | **X-16. Redaction at land; operator-only purge** | K-27 | Library, backups, guard | AD-37, AD-54, AD-23 (built) | L-AD-6 exception, L-AD-16 | purge drill |
| 20 | **X-17. Global autonomy pause** | K-28 | engine, Hub | AD-10 ticker (built) | AD-10 text, fact sync | none |
| 21 | **X-18. Data locality in placement** | K-14 | placements, Library tiers | AD-20, AD-30, L-AD-10 | preflight score, heartbeat | with 45 P-APP |
| 22 | **X-20. Checkpoint resume contract; `gpu` resource class** | K-23 | engine, remote, Library | L-AD-13, AD-57, AD-58 | AD-4, AD-58 | preemption drill (paid provider) |
| 23 | **X-22. Session fork** | K-30 | harness, Library | AD-35, AD-41 | session operations | SDK fork (H-75) |
| 24 | **X-25. Cell dependency capture at graduation** | K-29 | Lab | Lab AD-9, 45 DC-9 | Lab LLD | five notebooks |
| 25 | **X-23. Operator "last look" cursor for the digest** | K-32 | Library, templates | ref log, `rv` and `db` templates | one row | none |

**Also for the architect, from the context collection (not new design):**
- Fold 45 DC-3 into AD-19 before X-5. AD-19 still says `emits` and `accepts` on the engine bus.
- Write L-AD-21 into the Library spine. Today it is a memlog decision only.
- Study 43 is referenced by three memlogs but is not on disk.
- AD-35's home kinds lack `agent` (K-21). Adding one value is enough.
- The rebuild-era `qmx_agents/memory.py` (scoped memory on a LangGraph `deepagents` backend) is deleted under AD-59. Port nothing from it except its scope names, which match AD-18's.
