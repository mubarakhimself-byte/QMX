# 43. The whole app unlocked (ruling 118)

Written 2026-10-18 by the architect (Opus 5.5), headless, BMad architecture skill in amend mode, codebase-design vocabulary (deep modules, seams, adapters). No sub-agents; the reviewer gate ran inline. Nothing committed.

**Inputs read:** `26` (rulings 1-117, plus 118 as given), `39` (whole record: rerun, Review applied, Fix-check applied, Retirement pass), `37d` (142 rows) with `37a` to `37c`, `40`, `41`, `42`, `alignment/A`, `B`, `C` sections 2-3, `AUDIT-2026-10-18.md`, the three architectures (workflow-engine with SOLUTION-DESIGN, HARNESS-REQUESTS, OPEN-DECISIONS; library-and-data; lab-and-pods), `UI-HANDOFF.md`, `DELETION-PLAN.md`, the engine run record (`D:\QMX-worktrees\qma-ship\engine\BACKLOG.md`, `lows.md`). **Code truth:** `origin/engine/base` = `132169c7` read with `git show`, `git grep`, `git ls-tree` (packages `qma-harness`, `qmx-engine`, `qmx-control`, `qmx-apps`, `qmx-remote`, `qmx-agents`, `qma-core`, `qma-wire`, `qma-daemon`, `qmx-broker`, plus `qmb`, `qmn`, `qml`, `packages/qmf-*` at directory level); the installed `claude-agent-sdk` 0.2.166 (`types.py`, `client.py` in the engine run's venv). Every "[retrieved]" below was read in this pass.

**Files changed (all under `tracker/qma-v2/`):** engine `ARCHITECTURE-SPINE.md` (AD-52 to AD-60 added; AD-3, 4, 5, 8, 9, 12, 13, 16, 19, 22, 24, 25, 28, 34, 35, 38, 42, 43, 47, 48 amended in place; layer table, dependency diagram, seed, conventions, capability map, deferred rows), `HARNESS-REQUESTS.md` (rewritten as a plain change list), `OPEN-DECISIONS.md` (D and G closed), `SOLUTION-DESIGN.md` (§27 added; §8.4 and the §13 H17 fallback marked superseded), `PLAIN-WORDS.md`, `DOC-CHANGES.md` (rows 43-45), `.memlog.md`; Library `ARCHITECTURE-SPINE.md` (AD-21 added; AD-3, AD-5, AD-9 amended; one deferred row closed), `.memlog.md`; Lab `ARCHITECTURE-SPINE.md` (AD-14, two inherited rows, one deferred row, seed), `.memlog.md`; `UI-HANDOFF.md` (§14 added, eleven rows fixed); `26` (ruling 118 in section M); `README.md` (index). `lint_spine.py`: 0 findings on all three spines.

---

## 1. Summary

1. **One process, not three.** Today three hosts exist (`qma.serve` for chats, `qmx_engine.host` for the engine, `qmx_control` for neither) and each refuses a QMX home another holds, so **the copilot and the workflow engine cannot run at the same time on his PC** [retrieved: `qmx_engine/host.py`, ENGINE-NOTES "Never run the host on a home where `qma.serve` is running"]. That was the harness lock: the composition root lived inside the harness package. New `qmx_host` composes everything (engine AD-52).
2. **The harness gets a real interface for programs.** The engine waits for a turn by polling a chat file every 50 ms and re-reading all of the turn's events on every poll, and answers permission asks by polling too [retrieved: `ports/harness_adapter.py`]. The harness already has the turn-end signal inside (`Chat.next_end`). New `run_turn`, named permission policies and hook sinks, and chat options persisted on the chat record (AD-53). About 200 lines of polling and two fallbacks go.
3. **Engine agents can finally do work.** Every agent node today can only read and answer: "Every ask is rejected, so an agent node writes nothing on the host until the sandbox packet" [retrieved: `nodes/agent.py`]. With the policy, an agent writes inside its own attempt folder; only declared outputs are kept (AD-60).
4. **The money gate becomes a smaller guard.** `money.py` (1,198 lines) says of itself that each layer is a guard against accidents that Bash gets around; the run record says "the read-only broker token is the real guard". Its real protections (sign-ins, keys, QMX stores, his `~/.claude`, destructive commands) stay as the guard; the money-word matching, the broker-host refusals, the exposure probe and the scope proofs go (AD-54). Ruling 116 had kept the gate only as "existing harness behaviour" under the lock that ruling 118 lifts.
5. **Mini apps are real Claude plugins**, as ruling 10 said. The single plugin locked by a hash in code goes; each pack loads natively (skills, agents, commands), its tools are an in-process server switched per chat, so adding an app to a running chat needs no restart (AD-55).
6. **The router becomes its own package** (`qmx_router`) with a `complete` call, so one-shot AI steps on key and GPT providers stop starting a whole Claude Code program each (170-610 MB). The plan-lane probes stay exactly as they were: they rest on what the CLI does and how Anthropic bills a plan, not on any lock (AD-56).
7. **One run system.** The control plane's remote runs and jobs (a LangGraph worker) and the apps supervisor's own scheduler are folded into engine runs and triggers (AD-57).
8. **Capacity per resource class.** Every node kind shares one semaphore of 3 today, so a rule waits behind a backtest; the engine and harness count chat slots twice. Fixed (AD-58).
9. **About 122,600 lines of old runtime are deleted** (`qma-daemon`, `qma-core`, `qma-wire`, the LangChain `qmx_agents` runtime) with caller scans; QMB and QMN get small handoff edits (AD-59).
10. **Hermes:** no verdict had been REJECT or DEFER because of a lock; one ADAPT becomes ADOPT (an agent profile loads as a plugin); about thirty rows move from "harness request, his grant" to "direct change" (§4).
11. **His calls left:** one, money: which rented provider to pay for, and when (§11).

---

## 2. Inventory: where an old lock shaped the design

"Lock" means ruling 24 ("don't tamper with the harness"), its exceptions 39 and 89, ruling 109 ("the harness stays; the provider contracts change"), and any design that existed only to avoid changing another subsystem.

| # | Item (where) | Old workaround | New decision | Why |
| --- | --- | --- | --- | --- |
| 1 | Composition root inside `qma.harness.routes._serve`; engine host separate (`qmx_engine/host.py`, 101 lines) | the engine ran in its own process with no chat routes; L1 "seat the engine in `qma.serve`" deferred because H0 did not cover composing it | `qmx_host`, one composition root; old hosts forward one release, then go (AD-52) | chats and workflows on one home at once; one place that starts servers |
| 2 | Turn end (H1 refused): `harness_adapter.wait_turn` polls `chats/<sid>.json` every 50 ms and pages all of the turn's session events each poll | polling, racy on long turns, quadratic in blocks | `Harness.run_turn` with `events()` and `result()` over `Chat.next_end` (AD-53) | the harness already has the signal; deep module, small interface |
| 3 | Permission asks of engine chats | the adapter polls for `permission` blocks and answers `Reject("unattended run")` | named `engine` policy answered in-process from `can_use_tool` (AD-53, H39) | no poller, no late answers, policy survives restart |
| 4 | Agent nodes cannot write (`nodes/agent.py` docstring) | every ask rejected until a sandbox packet (L6, H8) | overlay as working folder, declared tools allowed there (AD-60) | ruling 52 (agents may make their own tools), ruling 117 (local like Claude Code) |
| 5 | H2 tool list | "use only these tools" in the brief; not enforced (B-51, B-70) | `NewChat.tools` | correctness |
| 6 | H15/H16 options and hooks lost on restart (H19 asked) | the engine watches context and restarts the attempt in a fresh chat at `compact_at` + 0.05; tool spans from session blocks after the turn | options persisted on the chat record; hook sinks and policies named, resolved on reload (H19) | one mechanism instead of a main path and a fallback |
| 7 | Node brief not cacheable (H21 deferred with an 8,000-character cap because settings, append text and deny rules ride the Windows command line) | brief in each chunk's first user message (~5,470 tokens per chunk, B-53) | `append_system_prompt`; Claude settings go to a per-chat file (the SDK `settings` takes a path [retrieved]); deny rules shrink with the guard | cheaper and faster chunks |
| 8 | Draft save and test run ask once (H20 deferred: "would change Interactive chats") | a first-run card asking him to add an allow rule | allow rules generated from the Effect table at launch; `DOMAIN_WRITE` never asks while his `domain_write = allow` (AD-22) | AD-22 already said they never ask |
| 9 | H17 fallback in `control_door.py` | a Library watcher that test-runs a draft when `meta.test_requested` changes | deleted; H17 was granted and built in HG1 | dead weight kept "as safety" |
| 10 | One-turn `llm` node (H3 not granted) | a whole Background chat, a CLI process per call | `router.complete` for key and GPT rows; plan rows keep the one-turn chat (AD-13, AD-56) | fan-out speed and RAM; same normaliser and journal |
| 11 | `delegate` blocking (H26 asked) | today's blocking `delegate(profile, prompt)` | `delegate` v2 as a plain change (AD-41) | ruling 92 |
| 12 | Native third-party sub-agents (H38 asked) | `delegate` only | H38 as a plain change; **plan mains still wait on probe P1** | P1 is a fact about the CLI under `/login`, not a lock |
| 13 | Router code in `qma.harness.relay` (1,147 lines), `qma.gpt.*`, `qma.harness.profiles`; pool planned in `qma.harness.pool`; vault in `qmx_engine.vault` (ruling 109: "routing lands in the router, profiles and pool, not the harness core") | "pool exception" rows; provider code spread over two packages | `qmx_router` package (AD-56) | locality: one place reads keys, routes, leases, journals |
| 14 | Plan lane framed as "what changes in the harness, plainly" (H27) | a grant | an ordinary change; ship gate P0, P1, P4, P2 unchanged | the gate protects against real CLI and billing behaviour |
| 15 | One SHA-locked plugin (`home.py:73` `PLUGIN_SHA256`) | mini-app tools as `app.<id>.<tool>` rows in the one `qmx` server; skills as Library objects read "through the skill tool"; agents only as delegate targets (AD-19, M-3) | packs are plugins materialised from published Library objects, each checked against its own hash (AD-55) | ruling 10 literally; no re-implementation of the CLI's plugin loader |
| 16 | Packs fixed at launch (M-15, P-PK) | `tools/list_changed` hope, else relaunch-by-resume | every pack's in-process server registered; `toggle_mcp_server` per session [retrieved: SDK 0.2.166] (AD-35) | no restart; no MCP process per pack per chat |
| 17 | Lab pack "not a second Claude plugin" (Lab AD-14) | tool rows in the one table | a real plugin (Lab AD-14) | same as 15 |
| 18 | Session home (AD-35): "an atomic `NewChat.home` would need a harness change" | a separate control table and a write-once `PUT` that could race the first turn | `NewChat.home` and `packs` on the chat record at birth (H40) | one record, atomic |
| 19 | Copilot loops (H34) | an idle-only `InjectedText` entry point asked of the harness, because an Interactive chat refuses injected text | the loop prompt is his own stored text, sent as `OperatorText`; loop rows on the chat record (AD-47) | keeps the injection rule; no special door |
| 20 | Background review fork (H37) | a scheduled `improve` workflow reading the session export | `fork_session` [retrieved] as a plain change; probe P-FK stays | — |
| 21 | Attachments (H30), copilot browser rows (H35), rules (H31) | UI uploads to the Library; workflows browse for the copilot; rules in code | plain changes | — |
| 22 | Money gate untouched (ruling 116 "Kept: the harness's existing behaviour (its money gate included)") | gate first on every call; floor "after the money gate" | the guard replaces it (AD-54) | rulings 116 and 118; its own docstring; the run record's "read-only broker token is the real guard" |
| 23 | `qma-core` kept for the money word list (DELETION-PLAN D3 "Keep `qma-core`… the money deny-list"); engine AD-3 allow-listed `qma.core.barriers.money_path` | 24,453 lines kept alive for one import; `qma-wire` kept for one QMN example | vendored word list in the engine lint; `qma-core`, `qma-wire`, `qma-daemon` deleted (AD-59) | the import was the only live tie |
| 24 | Harness budgets (H28 "his grant", "no fallback offered") | — | a plain change (already settled by AD-40) | — |
| 25 | Engine `admission.engine_cap` = `max_live_chats − reserve`, beside the harness's own `_take_slot` | the engine could not change how the harness admits sends | the harness slot table is the only chat-slot counter (AD-58) | two counters drift |
| 26 | `claude_workflow` node kind waiting on H4 | "off unless he enables it" | retired (AD-5) | never built; the engine's fan-out covers it (ruling 22) |
| 27 | His hooks for workflows ("we have hooks", alignment B chat item 4) | "hook scripts are script nodes on bus events, not a second hook system" (AD-43), because per-chat settings could not change | `NewChat.claude_hooks` per workflow, written into its agent chats' settings file (AD-53); bus scripts stay for run events | native Claude Code hooks where he expects them |
| 28 | Who acted (H24) | publish, enable and live start served only on the engine host's own REST routes | the principal is set at the one door in `qmx_host` | one REST door |
| 29 | `Harness.end_chat` (H18) | rely on the reaper | `close_chat` | RAM |
| 30 | `py.typed` (H22) | pyright `extraPaths` | ship it | — |
| 31 | Stuck detector: one design (AD-16) but no owner for copilot helpers | engine watchdog only | pure chat rules in `qma.harness.stuck`, used by the engine too (AD-16) | one judgement everywhere |
| 32 | Remote runs and jobs (`runs_*`, `run_job`, `jobs_*`) kept "brownfield" (SOLUTION-DESIGN §13: "keep their remote-compute meaning") because they were another subsystem | a LangGraph worker (`qmx_remote/worker.py` imports `langgraph`, `qmx_agents.router`) beside the engine | one run system (AD-57) | ruling 22 |
| 33 | Apps supervisor's own scheduler and run budget (`qmx_apps` README) | left alone | app schedules are engine triggers; the run budget retires (AD-57) | one scheduler; ruling 106 |
| 34 | Chat sessions not a Library kind ("transcripts stay harness state", DESIGN) | sessions only searchable inside the harness | kind `session` (Library AD-21) | ruling 28 |
| 35 | Deletion D1-D4 as a separate gated program with old premises | not run | executed under AD-59, and extended to `qma-core` and `qma-wire` | ruling 118 |
| 36 | Router "its own thread" inside `qma.serve` (41 H1) | — | same thread design inside `qmx_host` | — |

**Looked at and unchanged (the reason was never a lock):** the plan lane's probe gates and the rule that only the CLI holds the plan sign-in (CLI facts, Anthropic billing: 37d §6.5); the central relay and run passes (remote workflows need them, ruling 117); `runner_outside` for containers and remote placements (the Rivet principle); the model normaliser (AD-50: provider quirks); Interactive chats refusing injected text and verbatim Background prompts (prompt-injection hygiene); `setting_sources=[]` (QMX still writes the settings it wants, now into a file); the Library's paradigm (content-addressed objects with git-like refs); `PROPOSE_MONEY` always asking.

---

## 3. Rebuild designs

Each design: the module, its interface, what is deleted, what is kept, and the path from merged code. Interfaces are sketched in SOLUTION-DESIGN §27.

### 3.1 `qmx_host` (AD-52)

- **Module.** New package `qmx-agents/packages/qmx-host`. The only composition root and the only thing that starts servers.
- **Interface.** `python -m qmx_host serve --home --port [--role pc|node] [--ui-origin]`; programmatic `async with Host.open(home, role) as host`. Principal set at the door.
- **Deleted.** `qmx_engine/host.py` (101 lines); `qma.harness.routes._serve` composition; `qmx_control.__main__ serve`; `qma.serve`'s `serve` path (both become forwarders for one release); the engine host's duplicate `control-process.json` handling.
- **Kept.** `qma.boot` scrub-before-import order; `engine.lock`; the control app (`create_app`), chat routes, engine routes; `qma.serve start/status/stop` behaviour moves to `qmx_host`.
- **Migration.** (1) Add `qmx_host` composing what `routes._serve` and `qmx_engine.host.serve` compose today, plus the router thread; (2) point `qma.serve serve` and `qmx_control serve` at it; (3) QMB session edits its spawn string (DELETION-PLAN D2, retargeted from `qma.serve` to `qmx_host`); (4) delete the forwarders once no caller scan hit remains.
- **Survives.** Host crash mid-turn (chat reads `unknown`, run resumes from its ledger); a second host on the same home (refused by the lock); the router thread dying (restarted in-process, plan lane off until healthy, AD-38); the QMB host still spawning the old name during the overlap (forwarder answers).

### 3.2 The harness turn API (AD-53, AD-60)

- **Module.** `qma.harness` gains `turns.py` (TurnHandle, events), a policy and sink registry, and the persisted `NewChat` fields; `HarnessPort` in the engine is rebuilt on it.
- **Interface.** `start_chat`, `run_turn`, `interrupt`, `close_chat`, `set_packs`, `register_policy`, `register_sink` (SOLUTION-DESIGN §27.2). Order on a tool call: guard → CLI rules → `can_use_tool` → named policy.
- **Deleted.** In the engine: `wait_turn`'s loop, `_turn`, `_blocks`, `_last_event`, the poll-and-reject of asks (about 200 of `harness_adapter.py`'s 375 lines); the compaction-restart fallback, the ask-rejection rule text and the tool-call cap in `nodes/agent.py`. In the harness: the "options live only in this process" limitation in `ChatConfig`.
- **Kept.** The engine's `Turn` record shape (so nodes change little), the turn-end reconcile of tool spans against session blocks, the B-69 re-seed when a resumed chat never got its task, the JSON validation with one repair turn, verbatim prompts for Background and Child chats.
- **Migration.** Build `run_turn` on `Chat.next_end` and the block projection; persist options; add the registries; rebuild the adapter; then delete the polling. P-PERM and P-SET run first.
- **Survives.** A restart mid-turn (result `unknown`, policy and sink re-resolved by name); a turn waiting for a slot (`queued`, not stalled); a hook observer timing out (reconcile catches the span); a denied call repeated by the agent (AD-16 loop rule); a deferred irreversible tool never answered (the unattended window expires it, attempt continues without it).

### 3.3 The guard (AD-54)

- **Module.** `qma.harness.guard` replaces `qma.harness.money`.
- **Interface.** One PreToolUse callback (fail closed) plus `deny_rules()` for the command line (login and secret paths only); his lists are data in Settings (H31).
- **Deleted.** Money vocabulary on tool names and dispatch targets; broker hosts in shell and WebFetch; `MoneyPosture`, `money_posture`, `keyring_inventory`, scope proofs, the exposure probe and report, `/api/doctor/probe`; `check_tool_surface`'s runtime vocabulary; the `qma.core` imports in `money.py` and `tools.py`.
- **Kept.** Path normalisation (Windows forms, junctions, drive-relative words), shell-word scanning for protected paths and keyring names, login and secret files, QMX-home and store write protection, personal-home protection, the unattended external-MCP rule, the `delegate`-from-sub-agent rule, the fail-closed wrapper, injection hygiene (context-file scan, Unicode tag stripping). Outside the guard: the `Effect` enum without a money member, `AGENT_OPERATIONS` as an explicit list (now with a unit test that no row names an order act), `PROPOSE_MONEY` asks, redaction, the token canary.
- **Migration.** Write `guard.py` from `money.py`'s kept functions plus the floor rows; swap the hook; delete the rest; update live checks `s06_money.py` into a guard check (E56).
- **Survives.** A false positive the old gate produced (a WebFetch of a broker's public docs, refused by the broker-host rule) now passes; a key read through PowerShell's credential APIs is still refused (keyring reader rule); a write into `control.db` by any route is refused; his always-allow cannot lift a floor row.

### 3.4 Packs as plugins (AD-55, AD-35, Lab AD-14)

- **Module.** `qma.harness.packs`: materialise, verify, list, toggle.
- **Interface.** `materialise(object_id) -> Path`; launch passes `plugins=[core, *packs]` and registers one in-process server per pack; `Harness.set_packs(sid, packs)`.
- **Deleted.** `PLUGIN_SHA256` and `plugin_refusal`'s hash comparison against a constant (the install-tree check moves to the installer manifest); the planned `app.<id>.<tool>` rows and QMX skill-reading tool.
- **Kept.** qmx_apps's one supervised process per app (stdio MCP, volume lease, Job object); `qmx app check` as the publish gate, extended; archive, never delete.
- **Migration.** Build materialisation from Library objects (needs the Library packet; until it ships, from the qmx_apps definitions store under `<home>/definitions/<hash>`, which is already content-addressed [retrieved: qmx_apps README]); toggle; then retire the hash constant.
- **Survives.** A tampered materialised folder (not loaded, doctor line); an app installed mid-chat (joins at next turn by resume); P-TG failing (added packs join at next turn by resume); P-PL failing (one combined plugin view per pack set); an app whose own process crashes (its tools return the supervisor's error; the breaker restarts it).

### 3.5 `qmx_router` (AD-56)

- **Module.** New package `qmx-agents/packages/qmx-router`.
- **Interface.** `grant`, `complete`, `mint_pass`, `verify_pass`, `readings` (SOLUTION-DESIGN §27.5).
- **Deleted.** Nothing of behaviour; files move: `qma/harness/relay.py`, `qma/gpt/*`, `qma/harness/profiles.py`, the plan readings of `usage.py`.
- **Kept.** Every behaviour of the relay today (grants, egress stop, family rule, wire quirks, journal), and all of AD-38, AD-39, AD-50 as designed.
- **Migration.** First a pure move with import shims (H44), all harness relay tests green; then RTR1-RTR7 land in the new package; then `complete`.
- **Survives.** Router thread death (AD-38 supervision); a `complete` to a plan row (refused with a message naming the one-turn chat); a 429 on `complete` (the classifier and pool, same as a chat request).

### 3.6 One run system (AD-57)

- **Deleted.** Control operations `runs_*`, `run_job`, `job_*`, `jobs_*` and their tool rows; `work` table kinds `runs` and `jobs`; `qmx_remote/worker.py` (LangGraph), `runs.py`, `store.py`; `RunIndex` listing chat journals; the apps supervisor's interval scheduler and run budget.
- **Kept.** `qmx_remote/providers.py` (`E2BProvider`, `ModalProvider` and friends) as `ComputeProvider` adapters; `models.py`; the apps supervisor's crash, heartbeat and memory protections.
- **Migration.** Engine remote worker adapter on `providers.py`; one-node workflow template "run this on a machine" for placed jobs; app schedules converted to triggers at app install; then delete the old rows (caller scan).
- **Survives.** A remote machine lost mid-job (attempt `unknown`, retried by effect class, AD-8); an app whose schedule fires while the app is stopped (the `app_op` waits on the app's queue or fails with the supervisor's reason).

### 3.7 Capacity classes (AD-58)

- **Deleted.** `LocalWorker`'s single semaphore for every kind; `admission.engine_cap`; the background-share reading as a gate.
- **Kept.** Machine-derived numbers (RAM for chats, cores for scripts, containers per host), the interactive reserve, queue-or-spill.
- **Survives.** 40 rules and 12 chunks at once (rules never wait); his Interactive chat starting while workflows hold every other slot (the reserve); a parent blocked on its child (borrows the slot, 42 N5).

### 3.8 Old runtime deletion (AD-59)

Order and gates are in the AD. What each step must survive: a caller left in `qa/integration` (deleted with the daemon), QMN's two path-list tests (edited), the example apps pinned by commit (they keep their copy), docs naming the daemon (a documentation pass, DOC-CHANGES row 44).

### 3.9 The `llm` node on `complete` (AD-13)

- Two paths behind one executor: key and GPT rows call `router.complete` with the node's schema; plan rows keep the one-turn tool-less chat. Both validate the answer with one repair turn and write the same span fields. The doctor and the grader's `llm` mode use the same executor.

### 3.10 Engine agents that write (AD-60)

- Working folder = attempt overlay; read-only extra folders = the run's `code` and shared `work`; the `engine` policy with `policy_args {overlay, tools, irreversible}`; declared `outputs.files` commit at `ok`. Build templates (component builder, mini-app pipeline, build-and-prove) gain real tool declarations and outputs, and their agents stop saying "write nothing".

---

## 4. Hermes verdict changes (rows whose verdict or landing depended on a lock)

Re-validated against Hermes' own docs in `research/sources/hermes-docs/` where the row cited them. **No row of the 142 had been REJECT or DEFER because of a lock** (H-114's reject is "no outside metrics recipient"; the four DEFERs wait on real owners).

| Row | Was | Now | Why |
| --- | --- | --- | --- |
| H-105 agent profiles | ADAPT: an `agent` Library item; Hermes' separate profile homes not copied | **ADOPT**: an `agent` item loads as a plugin view (persona, skills, sub-agents) into the chats that use it, the Hermes profile idea, without a second home | packs are plugins now (AD-55) |
| H-41 smart approver | ADAPT: rejected "for money and MANAGE" | ADAPT: rejected for MANAGE and publishing only | money machinery retired; publishing stays his (ruling 80) |
| H-38 generic pass-through for apps | ADAPT: `llm_complete` instead, "once H3 is granted" | ADAPT unchanged (one door), served by `router.complete` now | not a lock; the landing is direct |
| H-42 destructive floor | ADOPT "after the money gate" (H31 his grant) | ADOPT: the floor **is** the guard, first on every call | AD-54 |
| H-118 re-seed for the compaction fallback | ADOPT for the fallback | ADOPT narrowed: only for a resumed chat that never got its task | the fallback is deleted (H19 persists `compact_at`) |
| H-131 activation split, lazy MCP | ADOPT via H32 | ADOPT via plugins plus `toggle_mcp_server`: activates now, not next session | AD-55 |
| H-85 one contribution registry | ADOPT | ADOPT; core and packs now load the same way in the CLI too | AD-55 |
| 37b "Directive `pre_tool_call` hooks for apps" | Skip ("only the harness gates tools (money gate)") | Skip: apps never approve; a pack's `hooks/` is never materialised | reason restated without the money gate |
| 37b skill hubs "scanned by AD-36" | Adapt later | Adapt later, scanned by the skill lint and `qmx app check` | AD-36 retired |

**Landing moves from "harness request, his grant" to "direct change" (verdict unchanged, ADOPT):** H-01, H-02, H-03, H-05, H-07, H-09, H-10 (`delegate` v2), H-13, H-16, H-24 to H-28, H-30 to H-34, H-36 (router package), H-39 (`complete`), H-43, H-44, H-46, H-47, H-49 (guard and rules), H-57 (import from `~/.claude`), H-67 to H-69 (loops: stored `OperatorText`), H-75 (fork), H-93 (sandbox tools, H8), H-112 (attachments), H-128, H-129 (tool caps, tag stripping in the harness).

---

## 5. Engine keep, rebuild, delete map (`qmx-engine` on `origin/engine/base`, about 13,000 non-template lines)

| Module (lines) | Verdict | What changes |
| --- | --- | --- |
| `definition/` (model 165, validate 249, registry 112, lint 207, overlay 81, folder 103, expr 188, schema 716) | **keep** | strip `runaway` from model, schema and lint (CAP-E); lint vendors its money word list; `claude_workflow` out of the vocabulary |
| `core/` fold 209, ready 528, joins 72, loops 77, partitions 71, replay 77, edges 134, state 151, waits 37, commands 134 | **keep** | strip the runaway guard and `Degrade`; nothing else |
| `core/ladder.py` (263) | **rebuild (small)** | runaway and degrade out; the account rung becomes real (pool); classifier hints |
| `core/simulate.py` (198) | **delete** | a second driver that writes the same events as the runner; move its tests (`test_fold`, `test_joins`, `test_loops`, `test_replay`, `test_rule`) and live checks (`e01`, `e02`, `e03`, `x06`) onto `Engine` with injected executors (the `executors=` seam exists); one event writer |
| `ledger/` (store 389, events 53, memo 128, spans 236, signature 31, migrations 98, inbox_table 172) | **keep** | migration for the new trigger kinds; redact seam (AD-37) |
| `triggers/` (rows 371, ticker 348, claims 370, cron 104, catchup 37, quota 46, preflight 100) | **keep** | `session` trigger kind for loops; app schedules land here |
| `nodes/script.py` (232) | **keep** | overlays (AD-51), CPU slot (AD-58) |
| `nodes/agent.py` (430) | **rebuild** (to about 250) | on `run_turn`, the `engine` policy and overlay (AD-60), hook sink; delete compaction fallback, ask-rejection rules, tool-call cap; warm-first gate moves to dispatch |
| `nodes/llm.py` (264) | **rebuild** | `router.complete` path for key and GPT rows beside the one-turn chat for plan rows |
| `nodes/` base 174, doctor 101, grader 36, join 12, loop 13, monitor 58, rule 28, subworkflow 96, trigger 11, wait 30, fake_provider 74 | **keep** | `base` loses runaway fields |
| `ports/harness_adapter.py` (375) | **rebuild** (to about 150) | on `run_turn`; polling gone |
| `ports/` library 267, memory 94, inbox 138, settings 72, clock 29 | **keep** | `RouterPort` added |
| `ports/library_fake.py` (453) | **keep as the test adapter only** | once `qmx_library` ships, its SQLite file in the home goes; it stays as the in-memory second adapter that makes the `LibraryPort` seam real |
| `admission.py` (122) | **rebuild** (to about 50) | pool lease plus the harness slot table; `engine_cap`, background share and the meter-as-gate go |
| `settings.py` (74) | **rewrite** | caps out; key-first role lists (HYG0), later generated from the registry; `cpu_slots`, `container_slots` |
| `roles.py` (111) | **rebuild** | candidates from the registry (RTR5); degrade out |
| `runner.py` (830) | **keep, trim** | runaway guard out; capacity classes; harness and memory construction moves to `qmx_host` |
| `control_door.py` (692) | **rebuild** (to about 350) | the Library-watcher fallback (`CURSOR`, `library-watch`, `nonce`) deleted; principal comes from the door |
| `host.py` (101) | **delete** | `qmx_host` |
| `__main__.py` (256) | **keep** | test mode only (`--mode live` removed, HYG0); dev tool |
| `prompts.py` 61, `trace_export.py` 130 | **keep** | brief and snapshot to `append_system_prompt` |
| `watchdog.py` (56) | **rebuild** | chat rules from `qma.harness.stuck`; run rules stay |
| `workers/local.py` 121, `workers/effects.py` 121 | **rebuild** | capacity classes; overlays replace zone snapshots (AD-51) |
| `service/` (api 98, context 90, drafts 81, explain 148, inbox 22, registry 22, rest 48, runs 279, tests 123, versions 104) | **keep** | — |
| `memory/` (docstring only) | **build** | memory packet (AD-18) |
| `templates/` (31 plus `_shared`) | **keep** | runaway blocks out, plain names, build templates declare tools and outputs (AD-60) |

**Net:** about 1,200 lines deleted (host, simulate, polling, watcher, fallbacks, runaway code across about 20 files), about 900 rebuilt, the rest kept. **Faster:** no CLI process for key and GPT `llm` nodes; no 50 ms polling with quadratic re-reads; rules and joins never wait for a slot; the node brief read from the prompt cache on every chunk after the first.

**The scenarios, after the unlock:**

| Scenario | What carries it | What the unlock changed |
| --- | --- | --- |
| Big fan-out with chunking (a 300-video playlist, a Firecrawl site) | chunk edges (AD-34), memo per chunk (AD-7), pool spread (AD-12), capacity spill (AD-30, AD-58) | cheaper chunks (cached brief), `complete` for one-shot sorting and classifying steps, no slot contention from pure nodes |
| Resume after limits | `waiting(resume_at)`, wake rows, drain (AD-9, AD-10) | a slot wait is `queued`, a recorded wait, never a stall |
| Resume after crashes | ledger plus memos (AD-7), `after_unknown` (AD-8), re-seed (AD-34) | options, policy and hooks survive the restart (H19); one host restarts as one |
| Remote placements | `WorkerPort`, passes, central router, sidecar (AD-20, AD-25, AD-28) | one run system; `qmx_remote` providers as the adapters; `qmx-node` is `qmx_host --role node` |
| Mixed providers | router lanes, registry, H38, `delegate` v2 (AD-38, AD-39, AD-41) | all plain changes; plan-main native helpers still gated by P1 |
| Templates | AD-46, E48 | build templates can write; runaway blocks gone |
| Copilot building workflows | builder skill, `workflow_*` rows (AD-22) | the skill ships in the core plugin; draft saves and tests never ask (H20); no watcher fallback |

---

## 6. QMA v2, Library, Lab and data changes

**QMA v2 (the harness and the copilot).** The turn API, persisted options, named policies and sinks (AD-53); the guard (AD-54); packs as plugins with per-chat switches (AD-55); `NewChat.home` and `packs` (AD-35); loops as stored operator text (AD-47); `delegate` v2, H38, attachments, browser rows, background review fork as plain changes; router code out to `qmx_router` (AD-56); one host (AD-52); the stuck detector's chat rules in the harness (AD-16); budgets unset (AD-40). The temporary console (`qma/console.py`, 921 lines, "deleted when the UI lands") stays until the UI is wired.

**Library.** New AD-21: sessions are Library items (a card annotated per turn, a redacted transcript export at close). AD-3 adds kind `session`; AD-5's PC writer is `qmx_host`; AD-9 tool rows need no grant. The Library is the first agentic store to build: today three stores answer "Library" calls (QMB's `registryread/library.py`, control's `library.db`, the engine's `library_fake.py` SQLite file), and the control-door watcher copies between two of them.

**Lab.** AD-14: the `qmx-lab` pack is a real plugin; its tools are one in-process server switched per session. Inherited rows name the guard and AD-55. The Agents panel's live state no longer waits on harness requests.

**Data (ruling 91 holds).** Nothing in the data design changes: `dataset` cards, `data_scope` on passes, the market-data service stay as designed. One agent-facing effect: scripts reading data get CPU slots of their own (AD-58), so a long data pull no longer blocks rule nodes. The tick-history backup risk is listed in §7.

---

## 7. Improvements noticed elsewhere (evidence only; not designed here)

| # | What | Evidence | Suggested owner |
| --- | --- | --- | --- |
| 1 | Two uv workspaces and two lockfiles: the root is still the "sssf-project" the retired factory stamped in (QMF, QML, QMB, QMN), and `qmx-agents/` is a second workspace that reaches the root packages by path | root `pyproject.toml` "A project the Super Simple Software Factory was stamped into"; `qmx-agents/pyproject.toml` `[tool.uv.workspace]`; every run recipe syncs twice | a repo-hygiene packet: one workspace, one lock |
| 2 | Factory leftovers on the main line: `adws/` (36 Python files: plan, build, test, review drivers) and `queue/` | `git ls-tree origin/engine/base adws/`; the global CLAUDE.md: the epic-factory plugin is retired, and the project CLAUDE.md: the factory and queue lanes are not used for QMA v2 (both 2026-10-13) | his go to archive them (deletion needs his go, branching-model rule) |
| 3 | "Paper" means three things: QMB's research-paper replay naming (`qmb/paper.py`), QMN's Book-level paper on a paired demo account (`qmn/paper/`), and the Lab's simulated paper ledger over live prices (Lab AD-12) | the three module docstrings | the risk and node session: one word per meaning before the Lab's paper packet |
| 4 | Every product has its own host CLI (QMB `host` 20 files, QMN `host` 33, QML `host` 3) beside the agent host; the desktop app supervises only the agent host (AD-48) | `git ls-tree` of the three `host` folders | the desktop packet: supervise every QMX process, or name which stay manual |
| 5 | QMB's host still spawns the dead daemon (`qmb/src/qmb/doors/cli/host.py:104` `DAEMON_SPAWN_MODULE = "qma.daemon"`, `:947`) | file lines | QMB session (DELETION-PLAN D2, retargeted to `qmx_host`) |
| 6 | 34 pages under `docs/` describe `qma-daemon` as the runtime | `git grep -l -E "qma[-.]daemon" -- docs` | documentation pass (DOC-CHANGES row 44) |
| 7 | The 10 GB tick history still has no copy | study 30 §1; alignment B mismatch 12; ticket `data-tick-backup` | the data study (ruling 91); a plain copy to his server is not a data design and could run now if he says so |
| 8 | Broker settings are read straight from `settings.toml`, bypassing `ControlService` | `qmx_broker/service.py:117-121` | the broker's owner, with AD-52's one reader |
| 9 | Example apps pin the old `qmx-agents` runtime by commit, so LangChain lives on in examples | DELETION-PLAN D1 "Leave `examples/apps/macro-daily-bias` and `examples/apps/weekend-watcher` alone" | rebuild them as packs when packs ship |
| 10 | QMN's integration example and two tests still name the old QMA packages | `qmn/examples/spot_paper_journey.py:15-17`, `qmn/tests/test_qmn_fx_paper.py:682-684` | QMN session (AD-59 step 3) |
| 11 | About 2.7 GB of throwaway test homes and a probe venv on `D:` | `AUDIT-2026-10-18.md` "qma-ship" | his go to delete |
| 12 | The `qa/` tree (219 Python files) includes integration tests for the daemon (`qa/integration/test_qma_*`) that will go with it | `git grep -l "qma.daemon" -- qa` | deleted with AD-59 step 2; the rest of `qa/` needs a check against the new stack in the QA phase |

---

## 8. Blast radius and scenarios per change

| Change | Code paths | Tests and live checks | Templates | UI rows (UI-HANDOFF) | Must survive | Probe first |
| --- | --- | --- | --- | --- | --- | --- |
| AD-52 one host | new `qmx_host`; `qma/serve.py`, `qma/harness/routes.py` `_serve`, `qmx_control/__main__.py`, `qmx_engine/host.py`, `qmx_engine/control_door.py` wiring; QMB `host.py` spawn (handoff) | `test_host`, `x13_doors`, `x14_hello`, HP live scripts that start `qma.serve`, every lane's boot recipe | none | §2, §14 row 1 | crash mid-turn; second host refused; router restart in-process | — |
| AD-53 turn API | `harness.py`, `chat.py`, `launch.py` (`ChatConfig`, `build_options`), `home.py` (chat record), new `turns.py`; engine `ports/harness_adapter.py`, `nodes/agent.py`, `nodes/llm.py` | `test_chat`, `test_launch`, `test_table`, `test_harness_port`, `test_agent`, `test_llm`; `x10_llm`, `x11_agent_chunks`, `e04b_agent_unknown` | none | §1 row 5, §14 row 8 | restart mid-turn; slot wait; observer timeout; deferred tool unanswered | P-SET |
| AD-54 guard | `money.py` → `guard.py`; `tools.py` (imports, surface check), `launch.py` (hook, deny rules), `home.py` (plugin refusal), `harness.py` (`doctor`, `probe_exposure`), `routes.py` (`/api/doctor/probe`, usage page posture); engine `definition/lint.py`; `qmx_apps/supervisor.py` | `test_money*`, `test_tools`, `test_launch`, `s06_money.py`, `s03_tools.py`, HP check 5 (order requests refused) rewritten as the guard check | `money-pack` lane in `t_templates.py` | §11 row 21, §12 row 9, §14 rows 3-4 | a key reader via PowerShell; a store write via any tool; a broker docs page fetch passes | — |
| AD-55 packs as plugins | `home.py` (`PLUGIN_SHA256`), `launch.py` (`plugins`, `mcp_servers`), `tools.py` (pack servers), new `packs.py`; `qmx_apps` (manifest view, check); Library `mini-app` and `agent` kinds | `test_plugin`, `test_tools`, apps tests; `qmx app check` cases | `ma-mini-app-lifecycle`, `d9-mini-app-pipeline` | §5, §6, §12 row 17, §14 row 5 | tampered view; install mid-chat; toggle unsupported | P-PL, P-TG |
| AD-56 router package | `relay.py`, `qma/gpt/*`, `profiles.py`, `usage.py` readings move; `launch.py` and `harness.py` import the new package; engine `nodes/llm.py`, `admission.py` | `test_relay`, `test_profiles`, `test_translate`, `test_usage`, `hp11_lanes.py`, P0-P4 lanes | none | §12 rows 2-5, 23 (unchanged), §14 row 11 | router death; `complete` on a plan row; 429 on `complete` | P0, P1, P1k, P3, P4, P2 (unchanged) |
| AD-57 one run system | `qmx_control/service.py` (runs, jobs), `qmx_control/runs.py`, `qma/harness/tools.py` rows, `qmx_remote/worker.py`, `runs.py`, `store.py`; `qmx_apps` scheduler | `qmx-control/tests/test_remote.py`, `qmx-remote` tests, apps scheduler tests | none (a "run on a machine" template added) | §14 row 6 | machine lost mid-job; app schedule fires while the app is stopped | — |
| AD-58 capacity | `workers/local.py`, `admission.py`, `harness.py` `_take_slot`, `settings.py` | `test_admission`, `test_drain`, `test_effects`, E58 | none | §14 row 7 | 40 rules + 12 chunks; reserve kept; parent blocked on child | — |
| AD-59 deletion | workspace members, both lockfiles, `tools/ci.py`, `tools/test_all.py`, `qa/integration`, `qmx-agents/examples/native_*`, QMB host spawn, QMN example and two tests | `just ci`, caller scans | none | none | QMB still spawning the old name during overlap (forwarder) | — |
| AD-60 agents write | `nodes/agent.py`, the `engine` policy, `workers/effects.py` overlays | `test_agent`, `x11_agent_chunks`, E50, E55 | build templates (`bc-build-a-component`, `d9-mini-app-pipeline`, `b-build-and-prove`, `d3-iterate-against-qmb`) declare tools and outputs | §14 row 2 | write outside denied and the attempt goes on; a resumed attempt keeps its policy; a sibling's files survive a retry | P-PERM |
| Library AD-21 sessions | host session recorder, kinds | Library tests | none | §14 row 9 | a key in a transcript (redacted export only); idle chat never closed (daily export) | — |
| Lab AD-14 | `plugins/qmx-lab` layout | Lab pack tests | Lab templates' skills | §5 | as AD-55 | P-PL, P-TG |

---

## 9. Probes to run before building

| Probe | Before | What it settles |
| --- | --- | --- |
| **P-PERM** | AD-60 and the `engine` policy | the order guard → CLI rules → `can_use_tool` → named policy in a Background chat in `default` mode; allow rules scoped to the overlay pass without the callback; undeclared tools reach the policy; a deferral holds the call until it resolves |
| **P-PL** | AD-55 | several local plugins load under `setting_sources=[]` and `strict_mcp_config=True`; their skills (`plugin:skill`), agents and commands work; nothing from a pack's hooks or MCP config runs |
| **P-TG** | AD-35 packs mid-session | `toggle_mcp_server` on an in-process server makes its tools answer on the next request with no relaunch |
| **P-SET** | H21 | the launcher passes `settings` as a file path on Windows; the command line shrinks |
| P-FK | the background review fork | unchanged |
| P0, P1, P1k, P2, P3, P4 | the plan lane, H38, the chat lane, the normaliser | unchanged (SOLUTION-DESIGN §26.14) |

Exact pass and fail lines: `HARNESS-REQUESTS.md` "Probes named above" and SOLUTION-DESIGN §26.14, §27.8.

---

## 10. Effect on the hardening plan (`HARDENING-PLAN.md` is not edited here; the planning lead edits it)

| Packet | Effect |
| --- | --- |
| HYG0 | keep; drop the "harness diff is empty" lane premise (the harness may change) |
| HG3 | **rename and widen** into the harness turn-API packet: H1 (`run_turn`), H2, H18, H19 (persisted options, named sinks and policies), H20, H21 (with the settings file), H22, H39, H40, H41, H45 and the five bug fixes; no call D, nothing blocked; probes P-SET and P-PERM first |
| L1 | **becomes the one-host packet** (AD-52); early, because most live checks want chats and workflows on one home |
| CAPE, CAPH | keep; H28 is no longer framed as a grant |
| SEC2A | keep; AD-60 builds on its overlays |
| HRMH | **widen into the guard packet** (AD-54): the floor and his rules replace `money.py`; the money posture, exposure probe and scope proofs go |
| RTR1-RTR7 | add **RTR0**, a pure move of the relay, `qma.gpt` and `profiles` into `qmx_router` before RTR1; `complete` joins RTR4 or its own packet; RTR6 (H38) and RTR7 (plan lane) keep their probe gates; RTR6 is no longer blocked on a call |
| DLG | keep; no longer blocked on a call |
| New: **PACK** | packs as plugins and per-session switches (AD-55, AD-35, Lab AD-14); probes P-PL and P-TG first |
| New: **AGW** | agents write in their overlay (AD-60), after SEC2A and the turn-API packet |
| New: **RUN1** | one run system (AD-57) |
| New: **CAPX** | capacity classes (AD-58); may ride with CAPE |
| New: **DEL1-DEL4** | the deletion (AD-59), after the guard, RUN1 and the one-host packet; DEL2 waits on the QMB session's spawn edit |
| New: **SES** | sessions in the Library (Library AD-21), after the Library packet |
| BLOCKED-ON list | shrinks to the probe gates only (RTR7 on P0, P1, P4, P2; RTR6's plan-main part on P1) |

---

## 11. His calls, in plain words

1. **Which rented computer service to pay for, and when.** Nothing is paid for yet. My recommendation: wait until your own server's four agent slots are full too often; adding a provider then takes no code.

That is the only call. Not calls, but worth knowing: the "fifth kind of quant" is still yours to name, and nothing waits on it; and the copilot on your Claude plan gets helpers from other providers inside the same chat only if one test with your real Claude sign-in passes. If it does not, those helpers still work as separate helper chats.

---

## 12. Reviewer gate (inline; no sub-agents were allowed)

- `lint_spine.py`: 0 findings on all three spines after the pass.
- **Rubric walk.** Every AD added has Binds, Prevents and an enforceable Rule; each new AD fixes a divergence two builders would otherwise create (who starts servers; how a program waits for a turn; where permissions are answered; how a pack loads; which package reads keys; where a run lives; who counts chat slots; what is deleted and in which order; where an agent may write). The operational envelope is covered (one process per machine, `--role node` on Contabo, the desktop host supervises it). One fix applied during the walk: an earlier draft of AD-52 claimed eleven harness modules read `settings.toml` directly; the code shows only `qma.boot` (by design) and `qmx_broker/service.py:117`; corrected and logged.
- **Currency lens.** No new library is bound. Every SDK fact used (`settings` as a path, `toggle_mcp_server`, `fork_session`, `AgentDefinition.model` and `effort`, `PermissionMode` including `dontAsk`) was read from claude-agent-sdk 0.2.166 as installed, the pinned version; behaviour not shown by the types (does a toggled server answer without relaunch; do several local plugins load under `setting_sources=[]`; the permission order) is a named probe, not a claim.
- **Adversary lens (two compliant units that still clash).** (a) A pack's tools served both by its plugin `.mcp.json` and by the in-process server: closed, AD-55 never materialises `.mcp.json`. (b) Two owners of the session home (control and harness): closed, AD-35 puts it on the chat record only. (c) Two chat-slot counters: closed, AD-58. (d) A policy allow rule lifting a floor row: closed, AD-53's order and AD-54. (e) The router and the engine both minting passes: closed, the engine mints through `qmx_router.passes`. (f) An app schedule in both the supervisor and the engine: closed, AD-57. (g) Hooks from a pack and from his settings both firing on engine chats: closed, AD-55 strips pack hooks, AD-34 keeps global hooks off engine chats and his per-workflow hooks ride `claude_hooks`.
- **Not done (owners named):** Library and Lab HLD and LLD companions were not re-projected (the spines win; owner: the next architecture or planning pass); `HARDENING-PLAN.md` and `DELETION-PLAN.md` were not edited (owner: the planning lead, from §10); no probe ran (P-PERM, P-PL, P-TG, P-SET are build-time gates).
