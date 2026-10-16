# 27b — Final rubric walk before shipping (2026-10-16, late night)

One reviewer, no sub-agents, read-only on code. This walk checks the three architectures, `UI-HANDOFF.md` and `33-state-of-play.md` against rulings 1-84 (file 26, where the latest ruling wins), against each other, and against the harness code on branch `qma/hp17` (commit `584a7f41`).

Paths are relative to `tracker/qma-v2/` unless they start with `qmx-agents/`. The `qmx-agents/` paths are files on `qma/hp17`, read with `git show qma/hp17:<path>`. Abbreviations: `ENG` = `architecture/workflow-engine/`, `LIB` = `architecture/library-and-data/`, `LAB` = `architecture/lab-and-pods/`, `SD` = `ENG/SOLUTION-DESIGN.md`, `SP` = `ARCHITECTURE-SPINE.md`. `QH` = `qmx-agents/packages/qma-harness/src/qma/harness/`.

**Track E.** The brief asks what "the build plan's Track E" needs. No build plan exists yet. I searched for "Track E" in this worktree, in every worktree under `D:\QMX-worktrees`, and on branch `plan/agent-system`, and found nothing. File 33 §5 is the only packet list: (1) format and validator; (2) ledger, memo and replay; (3) core node kinds; (4) test mode with real cheap models; (5) agent and llm nodes through the harness; (6) scheduler and inbox. This walk treats those six engine packets as Track E. Section 4 maps the open gaps onto them.

## Verdict

**6 blockers, 26 should-fix findings, 9 notes.** The architectures agree on the big shape: one engine, one Library, the Lab as kinds plus a pack plus templates, and the harness outside the sandbox. The blockers sit where the three meet. They concern what "draft", "tested" and "test run" mean, which harness names the engine may touch, ruling 78 (absent from all three), and the 12 GB Contabo box (ruling 76), which the defaults ignore. Each blocker has a concrete fix in section 6, and none needs a redesign.

---

## 1. Findings

### Blockers (fix before the first packet that touches them)

**B1. Ruling 78 is not designed: no chunking, no compaction policy, no caching discipline, no hooks and no tool-call tracing in engine agent nodes.**
- *Location:* `ENG/SP.md:91` (AD-5 edge mapping `one | zip | broadcast | keyed-join | cartesian`), `ENG/SP.md:211` (AD-25: "Wider fan-out … is an engine `broadcast` edge, which gets more containers"), `SD:82` (example: `broadcast` into the agent node "Read each paper", one agent per paper), `SD:123` (agent kind row), `SD:845-860` (defaults). The engine sources stop at rulings 60-72 (`ENG/SP.md:12`).
- *Problem:* ruling 78 says fan-out is per CHUNK of items, never one agent per item, and that compaction near 40%, caching, tool calls and hooks are critical in the engine. Searching `ENG/*.md` for "chunk", "compact" or "hook" finds nothing. "Cache" appears only as account affinity (`SD:451`, `SD:808`) and as span token fields (`SD:541`).
- *Evidence from code:*
  - Compaction is only observed. `QH/project.py:284` defines `Compacted`, `:608` parses `compact_boundary`, and `QH/chat.py:1187` writes a `changed` block. No public method compacts a chat or sets a threshold.
  - `CLAUDE_CODE_AUTO_COMPACT_WINDOW` is allowed only as a per-provider quirk on key-provider rows (`QH/profiles.py:141`). `ClaudePlan` has no quirks (`QH/profiles.py:75`), so plan chats can't get a 40% rule today.
  - The only hook is the money gate on PreToolUse (`QH/launch.py:383-391`). `setting_sources=[]` (`QH/launch.py:407`), and `NewChat` has no hook field (`QH/harness.py:150-159`).
  - `[claude] hooks` in `settings.toml` is operator-editable and global, covering every chat (`QH/home.py:244-251`).
- *Impact:* packets 3 and 5 would build per-item fan-out and agent nodes with no context discipline. That is the exact design the operator ruled out.
- *Fix:* add engine AD-34 "Agent-node context discipline", a `chunk` edge mapping, harness requests H15/H16 and checks E29-E31 (section 6, `ENG/SP.md` and `SD`).

**B2. "Test runs use real models" (ruling 51) is contradicted in five places.**
- *Location:*
  - `ENG/SP.md:193` (AD-22: the builder "calls validate and a fake-provider test");
  - `ENG/DOC-CHANGES.md:9` (row 2: "a test run on a draft uses pinned data and the fake provider");
  - `SD:811` (§16 row "Test step … Chosen: pinned + fake");
  - `SD:981` (E7: "`tests.run` on it → runs with the fake provider");
  - `SD:533` (last sentence: "The fake provider is an engine executor selected by `mode: test`").
- *Against:* `ENG/SP.md:127` (AD-11), `SD:367` (§6.2), `SD:387` (§6.4), `SD:818` (§16 row "real by default") and `SD:995` (E21).
- *Problem:* packet 4 is "test mode with real cheap models". A builder who codes E7 or AD-22 ships the fake provider as the default.
- *Fix:* five one-line edits (section 6).

**B3. Under the Library's rules a workflow can never become "tested".**
- *Location:* `LIB/SP.md:145` (AD-15: "tested" = a `tested-by` edge to a `workflow-run` whose status is `passed`; a run with status `test` is a real run that never fast-forwards), `LIB/HLD.md:172` (the engine "refuses to schedule otherwise"), `LIB/ENGINE-REQUESTS-ANSWERED.md:15` (L9: `test` is a status) and `ENG/LIBRARY-REQUESTS.md:15` (L9).
- *Problem:* test runs carry status `test`, and "tested" needs status `passed`. Engine AD-11 makes enabling depend on a passing test report from a test run. One field holds both the run's mode and its outcome. On top of that, the status sets differ:
  - engine runs are `queued | running | waiting | parked | finished | cancelled` (`SD:148-163`);
  - Library runs are `running | waiting | passed | failed | stopped | interrupted | test`.
- *Impact:* packets 2 and 4 have no run vocabulary to code against.
- *Fix:* split `mode: live|test` from `status`, publish one mapping table, and make the fast-forward key on `mode` (section 6).

**B4. "Draft", "version" and `main` mean three different things.**
- *Engine:* kind `workflow` is the draft head and kind `workflow_version` is immutable (`ENG/SP.md:145`). Triggers bind to `(workflow_id, version)` (`ENG/SP.md:121`).
- *Library:* `workflow_version` is not a kind (`LIB/ENGINE-REQUESTS-ANSWERED.md:20`). A draft is "`fields.stage = draft` on an object on `main` or an agent ref" (`LIB/LLD.md:116`). A scheduled run "resolves `refs/champions/<item>` first and falls back to `main`" (`LIB/SP.md:145`). `main` is "the version you trust" (`LIB/PLAIN-WORDS.md:48`).
- *Lab:* "the operator's `main` draft" (`LAB/SP.md:94`) and "the operator edits `main`" (`LAB/SP.md:194`).
- *Problem:* if the operator's draft sits on `main`, a scheduled run that falls back to `main` runs a draft. Engine AD-11 forbids that ("live runs refuse drafts"). The Library's run-output fast-forward (`LIB/SP.md:163`) also lands workflow-made `workflow`, `mini-app` and `unit` objects on `main` as if published. That bypasses ruling 80 (creation is human-driven first) and engine AD-22 (publish needs his yes once).
- *Impact:* the LibraryPort fake that packets 1-4 code against would encode one of three answers.
- *Fix:* add a `refs/drafts/<item>` namespace and pin triggers to object ids. Lifecycle kinds produced by runs land as drafts (section 6).

**B5. Harness touch points that rulings 24 and 39 don't cover.**
- *(a) The engine can't start a Background chat using only public names.* `Background`, `Child` and `Interactive` live in `QH/launch.py:61-84` and are not exported from `QH/__init__.py:7-24`. Engine AD-3 makes "an import of a harness submodule … a CI failure" (`ENG/SP.md:79`, check E15 `SD:989`). Yet `SD:457` builds `NewChat(..., kind=Background())`, and so does DESIGN.md call site 3 (`research/one-engine/architect/DESIGN.md:83`). Packet 5 can't be built without breaking AD-3 or editing the harness.
- *(b) `AGENT_OPERATIONS` rows.* New agent tools need rows in `QH/tools.py:121`, a harness file. The Library says its rows are added and "nothing else in the harness changes (ruling 24; ruling 39's exception is for the load balancer, not needed here)" (`LIB/LLD.md:226`). The Lab says the same (`LAB/LLD.md:342`, `LAB/DOC-CHANGES.md:21` "table rows only, ruling 24"). Editing that table is still a harness change, and no ruling grants it.
- *(c) The engine needs effect changes too.* `workflows_put` and `workflows_run` are MANAGE (`QH/tools.py:142,144`), so every copilot draft save and every test run would ask him. That contradicts AD-22 ("the operator's yes once"). None of this is listed in `ENG/HARNESS-REQUESTS.md`.
- *Fix:* one explicit operator grant: "export-only and table-row edits to the harness are allowed", plus requests H0 and H17 (section 6).

**B6. The Contabo defaults ignore ruling 76 (12 GB of RAM, about 4-6 concurrent Claude sessions).**
- *Location:*
  - `ENG/SP.md:133` (AD-12: "feeds the twenty server runners");
  - `ENG/SP.md:211` (AD-25: "a semaphore of 20");
  - `SD:337` (sizing "about 32-48 GiB RAM and 8+ cores for 20 concurrent agent nodes; under 32 GiB cap the semaphore at 10");
  - `SD:453` ("The server's twenty runners");
  - `SD:852` (`placement.server.semaphore` 20, or 10 under 32 GiB);
  - `SD:982` (E8 "20 Background chats");
  - `ENG/OPEN-DECISIONS.md:7` ("the server's twenty runners");
  - `ENG/OPEN-DECISIONS.md:8` (asks for server specs that ruling 76 already gave).
- *Problem:* even the derived formula is wrong for this box. With `overhead_mb` 4,096 (`SD:860`), 12 GiB gives 5 sessions. But Contabo also runs `qmx-hub`, `qmx-vault`, market data, monitoring, the server engine and 2 warm workers (`ENG/SP.md:241`, `SD:864`). None of these count against the budget. Defaults live once in `qmx_engine.settings.DEFAULTS` (`ENG/SP.md:270`), so packet 1 or 6 would code 20 in.
- *Fix:* set `max_sessions` for the server by derivation only, with a services overhead of about 6 GiB, which gives 4 on today's box. Rewrite the four "twenty" sentences (section 6).

### Should-fix

| # | Location | Problem | Evidence | Fix |
|---|---|---|---|---|
| S1 | `LAB/SP.md:112` (AD-5), `:130` (AD-8), `LAB/LLD.md:134`; vs `ENG/SP.md:247` (AD-31) | Ruling 68: backtests run on ONE dedicated QMB machine that agents call. The Lab runs `qmb.doors.api` **in-process on the controlled host**, and tags anything off that host `exploration_only`. That makes two backtest doors, and every QMB-machine result would be "exploration only". | Engine: `app_op qmb_backtest` on placement kind `qmb`. Lab: `qmb.*` are `script` nodes over `QmbPort`. | Lab AD-5: `QmbPort`'s default adapter is the engine `app_op qmb_backtest` on the `qmb` placement. Lab AD-8: "controlled host" = the PC **or** the registered `qmb` placement (both may produce evidence). The `qmb.*` types become `typeVersion`s of `app_op`, not `script`. |
| S2 | `LAB/SP.md:156` (AD-13 "spend above `settings.lab.ask_above_usd`"), `LAB/LLD.md:325,330,335,442` (`ask_above_usd` 5) | Violates ruling 27: no spending caps and no asking about usage. | Quoted lines. | Delete `ask_above_usd` and every "MANAGE above spend threshold" note; keep MANAGE only for publish, governed merge, paper start, promotion and labeler promotion. |
| S3 | `ENG/SP.md:157,121` (AD-16 "Any budget breach parks the run"), `SD:567` (budget → `run_paused` + inbox `urgent`), `SD:766`, `SD:845` (default "$2 estimate"), `SD:139` (lint requires a budget) | A per-run cost budget that parks the run and raises an urgent item is a spending cap with an ask attached. That contradicts rulings 27 and 77. | Quoted lines. | Rename it the **runaway guard**: default limits on tokens, agents and wall time (no USD figure), set high. A breach pauses the run as `waiting(runaway)`, writes an `info` digest line and resumes on the next trigger. Keep USD only as an estimate on spans. |
| S4 | Harness `Budgets` (`QH/launch.py:182-188`: `max_live_chats` 4, `background_cap` 0.5, `max_budget_usd` 5.0 per Background chat) | Every engine agent node is a Background chat. Without notice it stops at $5 (estimated), and on the plan it is refused at 50% of the window with a `needs_you` block (`QH/harness.py:353-361`). The PC's "about three at a time" (`ENG/PLAIN-WORDS.md:7`, `SD:284`) can't hold with `max_live_chats` 4 minus `interactive_reserve` (fan-out width `max_live_chats − 2` = 2, `SD:849`). | Code lines. | Engine §7.4 names these three settings, maps `error_max_budget_usd` to the ladder as `waiting(runaway)`, and gives UI-editable defaults for engine hosts in Settings (`[budgets] max_live_chats` ≥ 6 on the PC). Ask whether the 50% background cap still stands for workflows, given ruling 27. Settings only; no harness change. |
| S5 | `LIB/SP.md:127` (AD-12 "Provider keys are injected at start by the submitter (`credentials_scope` over stdin or sandbox env)"), `LIB/HLD.md:125,191`, `LIB/LLD.md:260`; vs `ENG/SP.md:229` (AD-28) | The Library still ships keys to workers. The engine says no worker ever holds a key. Engine L11-L14 (`ENG/LIBRARY-REQUESTS.md:17-20`) are **unanswered**: `LIB/ENGINE-REQUESTS-ANSWERED.md` covers L1-L10 only. | `qmx_remote` `ComputeProvider.start(handle, secrets)` passes secrets as `--env` (`qmx-agents/packages/qmx-remote/src/qmx_remote/providers.py:20,119`). | Apply engine `DOC-CHANGES.md:25` (row 19) to Library AD-12, HLD §5b and §7, and LLD 8d. Add L11-L14 rows to ENGINE-REQUESTS-ANSWERED. State that every `ComputeProvider.start` call passes only `{QMX_RUN_PASS}` in `secrets`. |
| S6 | `SD:300` ("What the gateway must provide … `placement_status`, `cancel(attempt)` … The Library agent's Hub is that gateway"); vs `LIB/SP.md:121`, `LIB/ENGINE-REQUESTS-ANSWERED.md:14` | The Library put `placement_status` and `cancel` on `qmx-node`, not on the Hub. The engine text still says the Hub provides them. | Quoted lines. | SD §5.3: `GatewayPort` fronts two services: the Hub (bundle, artifacts, events, Library proxies) and `qmx-node` (placement status, cancel, lease renewal). |
| S7 | `SD:611` (challenger on `refs/agents/<engine>/<workflow_item>`); vs `LIB/SP.md:97` (`refs/agents/<session_id>/<item>` owned by `agent:<session_id>`) | The engine's challenger ref is not an owned namespace, so the `engine:<store>` principal can't write it. | Owner table. | Library AD-7: add `refs/challengers/<workflow_item>`, owned by `engine:<store>` on the schedule's store. Engine SD §11.3 uses it. |
| S8 | `ENG/SP.md:145` (kinds `workflow_version`, `workflow_run`, `test_report`; edges `consumed_by`, `supersedes`), `SD:151`, `SD:472-479` | The engine still uses underscore kind names and the `workflow_version` kind that the Library refused (`LIB/ENGINE-REQUESTS-ANSWERED.md:20`). `supersedes` is not in Library AD-4 (`LIB/SP.md:79`), although `LIB/LLD.md:310` uses it too. | Quoted lines. | Engine AD-14 adopts the Library's names (`workflow-run`, `test-report`, version = object of the `workflow` item). Library AD-4 adds `supersedes` (or both sides switch to `replaces`). |
| S9 | `LAB/SP.md:100` (AD-3: types `lab.data`, `qmb.run` … "each a `typeVersion` of an engine kind"), `LAB/LLD.md:62-96`; vs `ENG/SP.md:91` ("v1 kinds, closed and extended only by `typeVersion`"), `SD:101` ("an unknown type … fails validation") | Nothing says how a node with `"type": "qmb.run"` validates. The engine registry has no pack sub-type. Also `lab.note` (`LAB/LLD.md:70`) vs `note` (`SD:140`). | Quoted lines. | Engine AD-5: a pack registers `<pack>.<name>` with a `base_kind`; JSON `type` is the pack type; the validator checks it against its base kind's contract. One note type: `note`. |
| S10 | `LAB/LLD.md:245` (`paper` = `loop(until stopped)` { `paper.step` per bar } in ONE run; pause and resume write `gate_resolved`), `LAB/SP.md:152` | A week-long soak (`paper.min_days` 7) inside one engine run breaks engine AD-25's claim that a workflow "is a finite run … ledger bounded" (`ENG/SP.md:211`). It also trips the 2 h wall-time guard (`SD:845`), has no typed loop stop (`SD:218`), and misuses `gate_resolved`, which is reserved for human gates. | Quoted lines. | Paper = an `interval` trigger (per bar or per N minutes) on the `paper` version with `continuity` (`ENG/SP.md:121`), `max_concurrent 1` and a daily `paper.check` trigger. Pause and resume = disable and enable the trigger. Each step is a short run. |
| S11 | `LAB/SP.md:136` (AD-9: KernelPort day-one adapter = `python -I` subprocess under engine AD-24), `LAB/LLD.md:484`; vs `ENG/SP.md:205` (AD-24: host tier only for trusted scripts "never model-written"), `ENG/SP.md:91` (`rlm` kernel in the sandbox) | Board cells written by the copilot or an agent would run bare on the PC. That gives two Python kernels: the Lab's `KernelPort` and the engine's `rlm`/`sandbox_python`. | Quoted lines. | `KernelPort`'s day-one adapter = the engine `sandbox_python` kernel in the `qmx-worker` container. The `host` subprocess is allowed only for cells whose content hash matches an operator-saved version. |
| S12 | `LAB/LLD.md:72-80` (`qmb.run`, `qmb.sweep`, … effect `irreversible`, "CPU time") | Engine AD-8 says an `irreversible` attempt with an `unknown` outcome is never retried and parks with an inbox item (`SD:213`). A worker dying during a backtest would wait for him (rulings 57, 77). | Engine effect rules. | Mark `qmb.*` compute nodes `none` (memoised by intent key, AD-27); only `qmb.holdout_touch` stays `irreversible`. |
| S13 | `SD:105` (`runs_on: local`), `ENG/SP.md:79` (`home_engine pc | server`), `SD:533` (role lists `pc`, `server`), `SD:742` (`server-1`), `LAB/LLD.md:117` (`"placement": "local"`), `LAB/SP.md:130` ("controlled host") | Placement names drift: `local`, `pc`, `server`, `server-1` and "controlled host". | Quoted lines. | One registry vocabulary: `pc`, `contabo`, `qmb`, plus provider rows. Drop `local`; define "controlled host" as `pc | qmb`. |
| S14 | `LIB/HLD.md:171` (template = `template` object with `instantiates`; "use this template" = new `workflow` with `derived-from → template`); vs `SD:399` (template = a published workflow version in the Templates shelf; variant = overlay with `variant_of`) | Two template models. | Quoted lines. | Pick the engine's: a template is a published `workflow` version tagged `template`. Library `template` kind is retired or kept for non-workflow templates only; "use" = `derived-from`, "variant" = `variant-of`. |
| S15 | `LIB/HLD.md:174` (`ran-on → machine` descriptor stored as a `setup` object); vs `LAB/LLD.md:101-121` (`setup` = CT-47 backtest spec) | The `setup` kind means two things. | Quoted lines. | The machine descriptor becomes a placement snapshot field on `workflow-run` (engine L14), or a new kind `placement`. `setup` stays the CT-47 spec. |
| S16 | `SD:650-655` (§13: `workflows_put` "(publish flag)", `workflows_run` "(mode test)", `triggers.*` → `jobs_list`/`jobs_cancel`, `runs.*` → `run_job`, `runs_*`) | The hp17 signatures have no publish flag or mode (`qmx-agents/packages/qmx-control/src/qmx_control/service.py:916-930`). `runs_*` and `run_job` already mean remote compute runs (`service.py:518-617`). No trigger-create tool exists, and no app archive operation exists (`service.py:685-912`). | Code lines. | SD §13: new tools `workflow_drafts_*`, `workflow_tests_run`, `workflow_versions_*`, `workflow_runs_*`, `workflow_triggers_*` and `apps_archive`, with explicit Effects (B5 grant). Keep `runs_*` for remote compute. |
| S17 | `ENG/SP.md:278` (`caller_kind user | agent | workflow`); vs `LIB/SP.md:97`, `LIB/LLD.md:200` (Principal `operator | agent:<sid> | run:<rid> | engine:<store> | hub | migrator`) | Two principal vocabularies. It's unclear which principal a run's Library write carries (the engine holds `LibraryPort` as `engine:<store>`, `LIB/LLD.md:224`, but run branches are owned by `run:<run_id>`). | Quoted lines. | Engine conventions: map `user→operator`, `agent→agent:<sid>`, `workflow→run:<run_id>`. A run's writes carry `run:<run_id>` (minted pass); only fast-forward, memory and champion moves carry `engine:<store>`. |
| S18 | `ENG/SP.md:157,163` (park → inbox item; preflight `blocked_config` → inbox; 401 → inbox), `SD:757-793` | Ruling 77: "Human attention is needed only for provider failures and harness-level errors". A parked logic or bad-output failure is neither. | Failure table. | Inbox severities: `normal` and above only for provider failures (401, all accounts closed > `alert_after`), harness or ledger errors, unknown outcomes on irreversible external effects, and stolen passes. A park from logic, bad input or bad output = `info` (digest) plus a challenger for AD-26. |
| S19 | `ENG/OPEN-DECISIONS.md:5,8,10`; `33-state-of-play.md:3,27,39-46` | Stale after rulings 73-84. Open decision 1 is answered by 74 (Contabo first), 4 by 76 (6 cores, 12 GB, 200 GB SSD; only the KVM check remains), and 6 by 79 (ship a default). File 33 still says "rulings 1-72" and lists these as open. | Quoted lines. | Mark them answered with ruling numbers; update 33's table row and §3. |
| S20 | Ruling 74 ("the copilot should be able to set a provider up from those instructions (built in, no hand-wiring)") | Not designed anywhere. AD-30 only says adapters map `provision/start/…` (`ENG/SP.md:241`). | grep of `ENG`, `LIB`, `LAB`. | Engine AD-30 adds a **provider onboarding** path. The copilot reads the provider's published skill or instructions and writes a placement row (`[placements]`) plus a `KeyProvider` row through `ControlService` (MANAGE once). Adapters are generic (SSH, HTTP API, `host_harness`); a provider-specific adapter is code only when the generic ones fail. |
| S21 | Rulings 58, 81 ("Data is among the first things built … tick backup and import are early work") | No architecture owns the market-data service, tick backup or the import of the orphaned ~10 GB history. Engine `ENG/SP.md:241` and Library `LIB/SP.md:245` both defer to study 30, which is a study, not a spine (`30-data-and-devops.md:18,176`). | Quoted lines. | Before build planning, make study 30 §4-§5 the binding design for a **Data track** (backup the 10 GB now; one ingest path; `qmx-marketdata` on Contabo; `dataset` cards) or run a short spine pass. The build plan must schedule it first, as ruling 81 requires. |
| S22 | `SD:74-75,86-87` (example `human_gate` "Promote to a Lab test?" in front of a `library` write) | It fails its own validation: a `human_gate` is allowed only in front of an irreversible external effect (`ENG/SP.md:91`, `SD:560`). Builders copy examples. | Quoted lines. | Replace n6 with a `rule` node (`score >= threshold`) or an `app_op` "send message" marked `irreversible_external`. |
| S23 | `LIB/LLD.md:265` ("OPEN-6 policy fast-forwards or queues the run's objects for review"), `LIB/HLD.md:181` ("OPEN-6 decides auto fast-forward per kind"), `ENG/DOC-CHANGES.md:22` (row 16 "No change to OPEN-6 (manual merge …)") | Stale: OPEN-6 is closed and replaced by Library AD-18. | `LIB/OPEN-DECISIONS.md:3`. | Point all three at AD-18. |
| S24 | `LAB/SP.md:148` ("This reads the Library roster's rows `book-definition → pod` … the conflict is surfaced … not resolved here") | Stale: Library AD-3 resolved it (`LIB/SP.md:73`, `book`/`bms` kinds). | Quoted lines. | Replace with "resolved by Library AD-3". |
| S25 | `LIB/SP.md:50,109`, `LIB/HLD.md:61`, `LIB/SP.md` source tree "the eleven verbs"; `LAB/SP.md:54` | AD-9 lists 15 verbs plus `adopt`. | `LIB/LLD.md:174-195`. | Say "fifteen verbs plus operator-only `adopt`". |
| S26 | `UI-HANDOFF.md:21` ("**four** answers in code (`allow_once | allow_always | reject_once | reject_always`)") | False. The code has `allow_once | allow_always | reject | answers`, plus statuses `resolved, already_answered, expired, invalid, unknown`. | `QH/routes.py:180-205`, `QH/chat.py:230-253`. | Correct the row (see section 5). |

### Notes

| # | Location | Note |
|---|---|---|
| N1 | `ENG/SP.md:229` (one relay per host) vs ruling 75 (one machine runs the relay, others route through it over Tailscale) | Compatible in practice: burst VMs and containers already use the Contabo relay. Record in AD-28 that ruling 75's central relay is the Contabo relay for every non-owned placement, and that the PC keeps its own relay only for plan-free key calls. |
| N2 | `SD:300`, `ENG/SP.md:211`, study 29 ("Docker+runsc is 80 % coded in `SSHProvider`", `SD:816`) | `SSHProvider.start` has the hardened `runc` flags (`providers.py:81-100`) but no `--runtime=runsc`, and it passes secrets as env. Also, `SSHProvider` works over SSH; a **local Docker Desktop** provider doesn't exist yet. The claim is optimistic; packet sizing should count a new local provider. |
| N3 | Ruling 26 (ChatGPT among the pooled providers) | GPT capacity stays 1 (`ENG/SP.md:133`) because `siwc` holds one sign-in. That is honest, and a harness limit, not a ruling bend. |
| N4 | `ENG/SP.md:211` E23, `ENG/SP.md:235` E24 | Two probes gate the agent-node packet (runner-outside tool quality; non-Claude sub-agent model ids). The build plan must put them first, as `WORKFLOW-SHIP-PREP.md` step 11 says. |
| N5 | Ruling 83 ("each template must actually run on the engine") | Only the Lab names its templates (`LAB/SP.md:36`). The engine and hub templates (brief, paper scout, playlist idea run, Firecrawl scrape and sort) have no list and no check. Add E32 "every shipped template passes a real-model test run" to the engine checks. |
| N6 | Ruling 12 (the hub is just a place; sessions keep their home) | The backend home field is "still owed" (`UI-HANDOFF.md:19`) and no architecture owns it. It is harness territory (session origin is fixed to `"qma"`, `QH/harness.py:317`), so it needs a harness request when the UI wires homes. |
| N7 | Ruling 80 vs Library AD-18 | After the B4 fix, run-made lifecycle kinds land as drafts. Results, artifacts, notes and memory rows still fast-forward freely (ruling 57). |
| N8 | `LIB/SP.md:121` (the Hub listens on the tailnet; Amp orbs join via OIDC) | Fine for Contabo-first (ruling 74). The public listener stays OPEN-5, off. |
| N9 | `ENG/SP.md:259` (Cua: a login wall or CAPTCHA ends the attempt, inbox item) | Consistent with ruling 77 (a harness-level wall) and with the no-CAPTCHA safety rule. No change. |

---

## 2. Ruling compliance (1-84)

Status: **OK** honoured; **BENT** honoured in spirit with a silent deviation; **VIOLATED** contradicted; **GAP** not designed although binding; **OUT** owned by another session or tomorrow's work (rulings 82, 84); **HIST** superseded or process-only.

| # | Status | Where / why |
|---|---|---|
| 1 | OK | Engine = the workflow system; the methodology comes tomorrow (82) |
| 2 | OK | Agent nodes are Claude Agent SDK harness chats (`ENG/SP.md:139`) |
| 3 | OK | Roles, not models (`ENG/SP.md:135-139`); any Anthropic-compatible provider (`:235`) |
| 4 | OUT | Methodology tomorrow; the builder references BMad phases (`ENG/SP.md:193`) |
| 5 | OUT | Organogram; the hub loads the Lab pack (`LAB/SP.md:164`) |
| 6 | OK | Lab spine |
| 7 | OUT | Output renderer deferred (`ENG/SP.md:437`) |
| 8 | OK | Engine AD-18 |
| 9 | OK / S16 | Archive everywhere (`LIB/SP.md:87-91`); no `apps_archive` operation exists on hp17 |
| 10 | OK | Pack = Claude plugin (`ENG/SP.md:175`) |
| 11 | OK | Single-agent, mixed and script workflows (`ENG/SP.md:73`) |
| 12 | BENT (N6) | Home field unowned |
| 13 | OUT | Portfolio session |
| 14 | OK | `NodePort` only (`LAB/SP.md:148`) |
| 15 | OK | Roles in Settings |
| 16 | OK | Reference only |
| 17 | OUT | Methodology |
| 18 | OK | Variants (`SD:397-399`), procedure-to-skill (`ENG/SP.md:217`) |
| 19 | OK | Workflow = folder (`ENG/SP.md:73`) |
| 20 | OK | Cua pack (`ENG/SP.md:255-259`) |
| 21 | OK | Ladder, doctor, memo, inbox |
| 22 | OK, with S9/S11 | One engine; Lab pack typing and a second kernel to fix |
| 23 | OK | Test gate (`ENG/SP.md:127`) |
| 24 | VIOLATED (B5) | Non-exported `Background`; `AGENT_OPERATIONS` rows added "without changing the harness" |
| 25 | OK | Server or local, Hermes cron (`ENG/SP.md:121`) |
| 26 | OK | Pool (`ENG/SP.md:133`) |
| 27 | VIOLATED (S2, S3, S4) | Lab `ask_above_usd`; run budget parks with an urgent ask; harness $5 cap unaddressed |
| 28 | OK | One Library (`LIB/SP.md:57-61`) |
| 29 | OK | Paper ends the line (`LAB/SP.md:150-154`) |
| 30 | OUT | Browser journeys owed (`UI-HANDOFF.md:90`) |
| 31 | OK, with B4 | Board = draft; draft storage contradictory |
| 32 | OK | Desktop only |
| 33 | HIST | No waves |
| 34 | OK | Phone later (`ENG/SP.md:163`) |
| 35 | OK | Example names are plain (`SD:41`); the template list comes tomorrow |
| 36 | HIST | Done |
| 37 | HIST | This walk |
| 38 | OK | No risk re-raised |
| 39 | OK | Pool and relay extensions inside the exception (`ENG/HARNESS-REQUESTS.md:61`) |
| 40 | OK | Desktop |
| 41 | OK | Library design |
| 42 | OK | Storage tiers (`LIB/SP.md:111-115`) |
| 43 | OK, with S5/S6 | Hub and sidecar; key path and gateway split stale |
| 44 | OK | |
| 45 | HIST | |
| 46 | OK | Lab from the screens |
| 47 | BENT (section 5) | UI-HANDOFF misses rows |
| 48 | OK, with N5 | Templates on one engine; engine template list missing |
| 49 | OK | Memory port |
| 50 | OK | Engine seat beside the harness |
| 51 | VIOLATED (B2) | Five fake-provider statements |
| 52 | OK | Sub-agents, agent tools, `rlm` |
| 53 | OK, with S11 | Sandbox contract; Lab host kernel bends it |
| 54 | OK | Hermes scheduling, one catch-up |
| 55 | OK | Plain servers first; the "20" figure superseded by 76 (B6) |
| 56 | OK | Primary switch (`LIB/SP.md:165-169`) |
| 57 | BENT (S12, S18) | Inbox volume; backtests marked irreversible |
| 58 | GAP (S21) | Data study, no spine |
| 59 | HIST | |
| 60 | OK | Cua pack on scope only |
| 61 | OK, with S5 | Vault, relay, run pass; the Library side is stale |
| 62 | OK | Relay routes by model id; probe E24 |
| 63 | OK | `KeyProvider` rows; OpenCode via H12 |
| 64 | BENT (B1) | Fan-out designed per item, not per chunk |
| 65 | OK | Live view on demand (`ENG/SP.md:253`) |
| 66 | OK, with B6 | Contabo home; RAM ignored |
| 67 | OK | Provider dashboards first |
| 68 | VIOLATED in the Lab (S1) | Engine AD-31 OK |
| 69 | OK | Provider-neutral burst |
| 70 | HIST | Done |
| 71 | HIST | Replaced by 84 |
| 72 | OK, with S19 | 33 exists; stale after 72 |
| 73 | HIST | |
| 74 | BENT (S20, S19) | Contabo first OK; self-setup from published instructions missing |
| 75 | BENT (N1) | Per-host relays rather than one central relay |
| 76 | VIOLATED (B6) | 20-session defaults |
| 77 | BENT (S18) | Notifications UI-side OK; inbox too chatty |
| 78 | GAP (B1) | Chunking, compaction, caching, hooks, tool calls |
| 79 | OK, with S19 | Default `auto` shipped; still listed as open |
| 80 | OK, with B4 | Operator publishes; run-made lifecycle kinds must land as drafts |
| 81 | GAP (S21) | No data design to build first |
| 82 | OUT | Tomorrow |
| 83 | BENT (N5) | No "every template runs" check |
| 84 | HIST | Process |

Count: VIOLATED 5 (24, 27, 51, 68 in the Lab, 76); GAP 3 (58, 78, 81); BENT 8 (12, 47, 57, 64, 74, 75, 77, 83). Everything else is OK, OK with a cited caveat, OUT or HIST.

---

## 3. Facts about the existing code (`qma/hp17` at 584a7f41)

| # | Claim in the architectures | Verdict | Evidence |
|---|---|---|---|
| F1 | The engine uses only names exported by `qma/harness/__init__.py` (`ENG/HARNESS-REQUESTS.md:3`) and builds `NewChat(kind=Background())` (`SD:457`) | **False as a pair** | Exports: `QH/__init__.py:7-24` (no `Background`, `Child`, `Interactive`); kinds in `QH/launch.py:61-84` (B5a) |
| F2 | `NewChat` has no `output_format`, `tools` or `max_turns`; `max_turns` is one global `[budgets]` value (H2) | True | `QH/harness.py:150-159`; `QH/launch.py:177-188,424-425` |
| F3 | `live()` yields deltas only; the turn end is internal `Chat.next_end()` (H1) | True | `QH/chat.py:815-819,889-897` |
| F4 | `CLAUDE_CODE_DISABLE_WORKFLOWS=1` for every chat (H4) | True | `QH/launch.py:239` |
| F5 | ControlService `workflows_*` are 501 stubs | True ("requires P10") | `qmx-control/.../service.py:916-930`, `_unavailable` at `:679-683` |
| F6 | `qmx` tools `workflows_get/put/validate/run`, `run_job`, `runs_*`, `jobs_*`, `sessions_list` exist (`SD:650-655`) | True, but the signatures lack the "publish flag" and "mode test" the SD assumes, and the Effects are MANAGE | `QH/tools.py:121-168` (`workflows_put` MANAGE `:142`, `workflows_run` MANAGE `:144`) |
| F7 | `qmx_ledger.RunJournal` is append-only, fingerprint-chained JSONL; `fingerprint` uses sort_keys, compact separators, `allow_nan=False` | True | `qmx-ledger/.../journal.py:17-36,69` |
| F8 | `qmx_remote.ComputeProvider` = `provision / start / status / logs / stop / teardown`; `E2BProvider`, `ModalProvider` exist | True; also `AmpProvider(SSHProvider)`. `start` takes `secrets` and passes them as `--env` | `qmx-remote/.../providers.py:18-24,119,156,169,250` |
| F9 | `RunBundle` = `kind, definition_hash, inputs, credentials_scope, resources, files` | True (plus `model_profile`, `command`, `app_id`, `code`) | `qmx-remote/.../models.py:67-78` |
| F10 | "Docker+runsc is 80 % coded in `SSHProvider`" (`SD:816`) | **Overstated** | Hardened runc flags only (`providers.py:81-100`); no `runsc`; remote over SSH, no local Docker provider |
| F11 | Approval answers (UI-HANDOFF: "four … `reject_once | reject_always`") | **False** | `allow_once | allow_always | reject | answers` (`QH/routes.py:180-205`; `QH/chat.py:230-251`) |
| F12 | Background chats have no REST door, so the engine sits in-process (`SD:802`) | True | `NewChatIn` has no `kind` (`QH/routes.py:130-137`); routes `QH/routes.py:263-427` |
| F13 | Relay on loopback; the relay is the only key reader | True today | `QH/harness.py:238,270-277`; `keyring_secret` |
| F14 | Compaction is supported by the harness | **Observed only** | `QH/project.py:284,608`; `QH/chat.py:1187`; threshold env only as a provider quirk (`QH/profiles.py:141`); no plan quirk (`:75`) |
| F15 | Prompt caching is preserved by session affinity; spans carry cache tokens | True | `QH/relay.py:960-961`; `QH/usage.py:40`; `Quote` uncached resend `QH/chat.py:358-362`; `resets_cache` `QH/launch.py:168-175` |
| F16 | Hooks available to engine agent nodes | **Not per chat** | Money-gate PreToolUse only (`QH/launch.py:383-391`); `setting_sources=[]` (`:407`); global `[claude] hooks` allowed (`QH/home.py:244-251`) |
| F17 | Global sub-agent concurrency knob exists | True (H7 fallback is partly there) | `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` in `CLAUDE_ENV_NAMES` (`QH/home.py:232-241`) |
| F18 | Harness Background limits | `max_live_chats` 4, `background_cap` 0.5, `max_turns` 50, `max_budget_usd` 5.0 | `QH/launch.py:182-188` (S4) |
| F19 | Session origin is hard-coded `"qma"` | True | `QH/harness.py:317` |
| F20 | `AGENT_OPERATIONS` is a harness table | True | `QH/tools.py:121` (B5b) |

Twenty claims checked. Four are false or overstated (F1, F10, F11, F14 as phrased in UI-HANDOFF §1.6 "compact now"), and two are true but incomplete in a way that matters (F6, F8).

---

## 4. Gaps a builder would hit tomorrow (engine packets, the "Track E" stand-in)

| Packet (file 33 §5) | Open item | Finding |
|---|---|---|
| 1 Format and validator | Pack type registration (`<pack>.<name>` → base kind); `note` name; placement vocabulary; the §2.1 example fails validation; `chunk` edge mapping | S9, S13, S22, B1 |
| 2 Ledger, memo, replay | Run status vs mode; engine-to-Library status map; LibraryPort fake semantics for draft, version and `main` | B3, B4, S8 |
| 3 Core node kinds | `broadcast` per item → `chunk`; runaway guard instead of USD budget | B1, S3 |
| 4 Test mode, real models | Five fake-provider statements; "tested" unreachable | B2, B3 |
| 5 Agent and llm nodes | `Background` not exported; compaction threshold, hooks and tool-call spans; harness `max_budget_usd` 5 and `background_cap`; `max_live_chats` 4; E23 and E24 probes first | B5a, B1, S4, N4 |
| 6 Scheduler and inbox | Inbox only for provider and harness failures; tool Effects (`workflows_put`/`run` are MANAGE); trigger tools don't exist; server defaults | S18, S16, B5c, B6 |
| (outside Track E, early per ruling 81) | Data track: tick backup, import, `qmx-marketdata` | S21 |

**Context compaction, caching, hooks and tool calls (ruling 78) in detail.** The minimum a builder needs, and the source of the AD-34 text in section 6:
1. **Chunking.** An edge into an `agent` or `llm` node that carries a list must use `map: chunk` with `chunk: {by: items | tokens, size?, fill: 0.3}`. With `by: tokens` the size is `fill × context window of the resolved model` (a 1M model takes about 300k tokens of items per chunk). The validator refuses `broadcast` of a list into an `agent` node. The memo and partition rules of AD-7 apply per chunk.
2. **Compaction.** Agent nodes compact at `settings.agent.compact_at` (default 0.40 of context). Mechanism: H15 (a per-chat compaction env on `NewChat` for Background and Child chats). Fallback: the existing per-provider quirk `CLAUDE_CODE_AUTO_COMPACT_WINDOW` on key-provider rows; plan rows stay on the CLI default until H15 lands. Every `Compacted` fact becomes a span event `compacted{trigger}`, and before compaction the agent is told to `memory_note` its working state (a PreCompact hook, item 4).
3. **Caching.** The prompt is built in fixed order: harness system preset → skills → the frozen memory snapshot (AD-18, already frozen per run) → node brief → chunk payload last. All chunks of one node in one run prefer one account lease (affinity key `run:node`), so chunk 2 onward reads the cache. Spans already carry `cache_read`/`cache_write` (`SD:541`). Check E30 asserts `cache_read > 0` on chunk 2.
4. **Hooks.** The engine needs PreToolUse (observe only; the money gate stays first), PostToolUse, PreCompact, Stop and SubagentStop on its own chats. Mechanism: H16 (per-chat SDK hook callbacks on `NewChat` for Background chats, appended after the money gate). Fallback: none acceptable. The global `[claude] hooks` (`QH/home.py:244-251`) would fire in copilot chats too.
5. **Tool calls.** Each tool call is a child span (`kind: tool`, name, Effect, sandbox placement, duration, error) from PostToolUse, or from the `tool` blocks the harness already writes to the session until H16. Each node gets a `max_tool_calls` runaway guard.

---

## 5. UI-HANDOFF completeness

**Wrong today:**
- §1.4 approvals (F11): the decisions are `allow_once`, `allow_always`, `reject` and `answers`. The statuses are `resolved`, `already_answered`, `expired`, `invalid` and `unknown`.
- §1.6 "compact now" has no backend (F14). Mark it "needs harness request H15".
- §4 "29 object kinds": the roster has 33 (`LIB/SP.md:73`).
- §4 "CT-07's 14 relations plus 17 Library ones": the Library set has 24 (`LIB/SP.md:79`).
- §3 "Where it ran … (PC, server, Amp runner or orb, E2B/Modal)" leaves out managed agent hosts (Cloudroom, Amp threads) and the `mode` field (`ENG/SP.md:253`).
- §5 is silent on `ask_above_usd`. It must say there is no spend ask (S2).

**Missing rows (the source of each is in brackets):**
1. **Machines list in Settings** = the placement registry with live preflight states, sessions in use / `max_sessions`, RAM, vault sync age and last error; run card, span and inbox fields `placement`, `mode`, `health`, `cost so far`, `link_out`; live view only on `watch: true` and when opened; provider dashboards reached by the copilot [`ENG/SP.md:249-253`, `SD:941-949`, `ENG/DOC-CHANGES.md:28`; file 33 line 32 flags it as still to add].
2. **Keys once:** per key `replicable`, `vault_version` and last sync; "key rotated, N relays updated"; re-pair placements; `qmx node login <placement>` [`SD:889-897`].
3. **Providers and roles:** a provider row = base URL + key ref + four tiers + quirks (+ `wire: openai_chat`); role candidate lists **per placement** (`pc`, `contabo`); OpenRouter marked test-only [`SD:527-533`, `ENG/SP.md:235`].
4. **Provider onboarding from published instructions** (once S20 is designed) [ruling 74].
5. **Cua scope and manifest editor** on an agent node (apps, origins, profile, expiry); screenshots in the trace; the always-on broker deny-list shown read-only [`SD:953-966`].
6. **Self-improvement:** per-workflow `self_improve auto | propose_only | off`; champion vs `main` badge; automatic rollback line [`ENG/SP.md:217`].
7. **Agent-made tools:** `unreviewed` / `reviewed` with a review action [`LIB/SP.md:73`].
8. **Run vocabulary:** one status set plus `mode: test` badge (after B3) [`SD:148-163`, `LIB/SP.md:145`].
9. **Inbox severities** `info` (digest), `normal`, `urgent`, `black` (repeats until acknowledged); actions `retry | stronger model | skip node | open trace | stop | resume` [`ENG/SP.md:163`, `SD:575`].
10. **Chunk progress** on fan-out nodes (chunk n of m, cache hits) and a **tool-call sub-timeline** per agent span (after B1).
11. **Draft vs published** on every workflow, mini-app and pod card (after B4); triggers show the pinned version.
12. **QMB machine** as a placement with its own queue depth [`ENG/SP.md:247`].
13. **Lab paper** as an interval schedule with pause = disable (after S10).
14. **Library home indicator** off: the UI never shows which store answered, but shows `primary_moving` during cut-over [`LIB/LLD.md:200`].
15. **Harness budgets** in Settings: `max_live_chats`, `max_budget_usd`, `background_cap` with their effect on workflows (S4).

---

## 6. Fixes to apply before shipping (exact edits, by file)

### `architecture/workflow-engine/ARCHITECTURE-SPINE.md`
1. Line 12 `sources`: append `'methodology/26 section J (rulings 73-84)'`.
2. Line 79 (AD-3): after "an import of a harness submodule is a CI failure" add "(the chat-kind names `Background` and `Child` arrive with HARNESS-REQUESTS H0)".
3. Line 91 (AD-5): edge mapping becomes `one | zip | broadcast | chunk | keyed-join | cartesian`. Add the sentence "An edge that carries a list into an `llm` or `agent` node must be `chunk` (ruling 78); `broadcast` of a list into those kinds is refused at validation." Add the pack rule: "A capability pack registers types `<pack>.<name>` with a `base_kind`; the validator checks them against the base kind's contract; `note` is the one draft-only type."
4. Line 133 (AD-12): "feeds the twenty server runners, since one plan cannot feed twenty agents" → "feeds the server's runners (`max_sessions` derived from RAM: about 4 on today's 12 GB box, ruling 76)".
5. Line 145 (AD-14): kinds → "`workflow` (items whose versions are objects; drafts on `refs/drafts/<item>`), `workflow-run`, `artifact`, `test-report`". Edges → the Library's hyphenated names, plus `supersedes`. The sentence about test runs: "a run carries `mode: live | test` and a status from the shared table in SOLUTION-DESIGN §3.1".
6. Line 157 (AD-16): "Any budget breach parks the run" → "A runaway-guard breach (tokens, agents, tool calls, wall time) sets the run `waiting(runaway)` with an `info` digest line; no USD cap exists (ruling 27)".
7. Line 163 (AD-17): severities rule: "`normal` and above only for provider failures, harness or ledger errors, unknown outcomes on irreversible external effects and pass theft (ruling 77); a park from logic, bad input or bad output is `info`".
8. Line 193 (AD-22): "calls validate and a fake-provider test" → "calls validate and a real-model test run on cheap candidates (ruling 51)".
9. Line 211 (AD-25): "a semaphore of 20" → "`max_sessions` derived from RAM (AD-30)".
10. Line 241 (AD-30): add "`overhead_mb` on Contabo counts every colocated service (hub, vault, market data, monitoring, server engine, warm workers); Claude's default 6,144, which derives 4 sessions on 12 GiB (ruling 76)", and add the provider-onboarding path of S20.
11. New **AD-34 "Agent-node context discipline (ruling 78)"**: the five items of section 4 above (chunking, compaction at 0.40, cache-stable prompt order with per-node lease affinity, per-chat hooks, tool-call spans), binding `nodes.agent`, `nodes.llm`, `definition`, `ledger`.

### `architecture/workflow-engine/SOLUTION-DESIGN.md`
1. Lines 74-75, 84-87: replace node n6 with `{"type":"rule", "parameters":{"expr":"items.score >= 0.7"}}` and ports `true`/`false`.
2. Line 82: `"map": "broadcast"` → `"map": "chunk", "chunk": {"by": "tokens", "fill": 0.3}`.
3. Line 105: `runs_on` → "`pc` (default) or a registered placement name".
4. §3.1 (after line 163): add the status table. Engine `queued|running|waiting|parked|finished|cancelled|unknown` → Library `running|waiting|failed|passed|stopped|interrupted`, plus `mode live|test`.
5. Line 300: "The Library agent's Hub is that gateway" → "`GatewayPort` fronts the Hub (bundles, artifacts, events, Library proxies) and `qmx-node` (`placement_status`, `cancel`, lease renewal); Library AD-11".
6. Lines 337 and 453: delete "semaphore 20", "sizing about 32-48 GiB … cap the semaphore at 10" and "The server's twenty runners"; point to AD-30's derivation.
7. Line 457 (§7.4): add a paragraph on the harness `[budgets]` interaction (S4).
8. Line 533: delete "The fake provider is an engine executor selected by `mode: test`." and write "The fake provider is an explicit per-run switch (`fake: true`) for a no-spend dry run".
9. Line 611: `refs/agents/<engine>/<workflow_item>` → `refs/challengers/<workflow_item>`.
10. §13 lines 650-655: new tool names (S16) with Effects: drafts and tests DOMAIN_WRITE; publish, enable and triggers MANAGE.
11. Line 811 (§16): "Chosen: pinned + fake" → "pinned + real cheap models; fake as a switch".
12. §17 lines 845, 849, 852, 860: budget → runaway guard (no USD); fan-out width note "bounded by `[budgets] max_live_chats` − `interactive_reserve`, raise `max_live_chats` on engine hosts"; `placement.server.semaphore` row deleted; `overhead_mb` "4,096 PC / 6,144 Contabo"; add `agent.compact_at 0.40`, `chunk.fill 0.3`, `agent.max_tool_calls 200`.
13. Line 981 (E7): "runs with the fake provider" → "runs on a real cheap candidate".
14. Line 982 (E8): "20 Background chats" → "8 Background chats across two accounts".
15. New checks: **E29** chunking (a list of 50 items becomes ⌈tokens / chunk size⌉ attempts, not 50); **E30** cache (chunk 2's span shows `cache_read > 0`); **E31** compaction (an agent node over 40% context emits `compacted` and a pre-compaction `memory_note`); **E32** every shipped template passes a real-model test run.

### `architecture/workflow-engine/HARNESS-REQUESTS.md`
Add rows:
- **H0**: export `Background` and `Child` (and `Interactive`) from `qma/harness/__init__.py`. Two names, no behaviour change; DESIGN.md call site 3 already uses them.
- **H15**: per-chat compaction threshold (env or option) on `NewChat` for Background and Child chats.
- **H16**: per-chat SDK hook callbacks (PreToolUse observe, PostToolUse, PreCompact, Stop, SubagentStop), appended after the money gate.
- **H17**: `AGENT_OPERATIONS` rows for the new engine, Library and Lab tools, and `apps_archive`, with the Effects of SD §13 and LLD tables (table rows only).

Fallbacks: H0, none (packet 5 blocks); H15, the provider quirk; H16, `tool` blocks from sessions with no PreCompact note; H17, none (the tools don't exist). Line 61: add "H0, H15-H17 need the operator's explicit grant: they are outside ruling 39's load-balancer exception (ruling 24)".

### `architecture/workflow-engine/OPEN-DECISIONS.md`
- Line 5 (1): "Answered by ruling 74: Contabo first; others addable."
- Line 7 (3): "the server's twenty runners" → "the server's runners".
- Line 8 (4): "Answered by ruling 76 (6 cores, 12 GB, 200 GB SSD; upgrade possible in December); only `ls /dev/kvm` remains."
- Line 10 (6): "Answered by ruling 79: ship `auto` as the default."
- Add one new decision: "Does the 50% plan background cap still apply to workflow agent nodes, given ruling 27?"

### `architecture/workflow-engine/DOC-CHANGES.md`
- Line 8 (row 2): "uses pinned data and the fake provider" → "uses pinned data and real cheap models (ruling 51)".
- Line 22 (row 16): "No change to OPEN-6" → "OPEN-6 is closed by Library AD-18".

### `architecture/workflow-engine/PLAIN-WORDS.md`
- Line 7: "Your PC runs about three at a time" → "Your PC runs about three at a time and your server about four today (12 GB of memory); more goes to rented machines".
- Add one sentence: "Big jobs are cut into chunks, not one agent per item, and long conversations are compacted early so the AI stays sharp."

### `architecture/library-and-data/ARCHITECTURE-SPINE.md`
1. Line 73 (AD-3): mark `template` "for non-workflow templates only; a workflow template is a published `workflow` version tagged `template`".
2. Line 79 (AD-4): add `supersedes`.
3. Line 97 (AD-7): add `refs/drafts/<item>` (operator on the primary store; the editor's draft) and `refs/challengers/<workflow_item>` (`engine:<store>` on the schedule's store). Add the sentence "`main` holds published versions only."
4. Line 109 (AD-9): "eleven verbs" → "fifteen verbs plus operator-only `adopt`" (also lines 50, 177, `HLD.md:61`).
5. Line 127 (AD-12): replace "Provider keys are injected at start by the submitter (…stdin or sandbox env)" with "Provider keys never reach a worker; the relay on the runner host injects them; the worker holds a run pass (engine AD-28). The token is the pass: add `attempt, placement, model_scope, relay_url, nonce`; revocation is per pass".
6. Line 145 (AD-15):
   - "a scheduled run resolves `refs/champions/<item>` first and falls back to `main`" → "a scheduled run resolves the object its trigger pinned, or `refs/champions/<item>` when that champion descends from the pinned object; never a draft";
   - status set → `running | waiting | passed | failed | stopped | interrupted` plus field `mode: live | test`;
   - "tested" = `tested-by` to a `workflow-run` with status `passed` (either mode) for that object id.
7. Line 163 (AD-18): "Runs with status `test`" → "Runs with `mode: test`, or with status `failed`, `stopped` or `interrupted`". Add: "objects of lifecycle kinds (`workflow`, `mini-app`, `pod`, `skill`, `methodology`) a run produces land on `refs/drafts/<item>`, never as a published version on `main` (ruling 80, engine AD-22)".

### `architecture/library-and-data/LLD.md`, `HLD.md`, `ENGINE-REQUESTS-ANSWERED.md`
- `LLD.md:116`: "on an object on `main` or an agent ref" → "on `refs/drafts/<item>` or an agent ref, never on `main`".
- `LLD.md:226`: "nothing else in the harness changes (ruling 24 …)" → "these rows are engine HARNESS-REQUESTS H17 and need the operator's grant".
- `LLD.md:260`: "keys over stdin" → "a run pass, no keys".
- `LLD.md:265`: "OPEN-6 policy fast-forwards or queues …" → "AD-18 fast-forwards".
- `LLD.md:310`: keep `supersedes` (now in AD-4).
- `HLD.md:125`, `HLD.md:191`: the same key change. `HLD.md:174`: "stored as a `setup` object" → "a placement snapshot on the `workflow-run` (engine L14)". `HLD.md:181`: "OPEN-6 decides …" → "AD-18 decides". `HLD.md:172`: "status=passed" (status passed, any mode).
- `ENGINE-REQUESTS-ANSWERED.md`: add rows L11 (vault separate: granted, matches AD-12), L12 (run pass: granted, AD-12 amended), L13 (imported traces: `trace` blob slot with `provenance: imported`), L14 (placement fields on `workflow-run`); and L9 reworded to `mode: test`.

### `architecture/lab-and-pods/ARCHITECTURE-SPINE.md`
1. Line 94 (AD-2): "the operator's `main` draft" → "the operator's draft on `refs/drafts/<item>`". Line 194: "the operator edits `main`" → "the operator edits `refs/drafts/<item>`; Save publishes a version to `main`".
2. Line 100 (AD-3): "each a `typeVersion` of an engine kind" → "each a pack type with a `base_kind` (engine AD-5)"; `qmb.*` compute types have `base_kind: app_op`.
3. Line 112 (AD-5): `QmbPort` default adapter = engine `app_op qmb_backtest` on the `qmb` placement (ruling 68); in-process `qmb.doors.api` only when the `qmb` placement is the PC.
4. Line 130 (AD-8): "controlled host" = the `pc` or `qmb` placement; both may produce evidence.
5. Line 136 (AD-9): day-one `KernelPort` adapter = the engine's `sandbox_python` kernel in `qmx-worker`; host subprocess only for operator-saved cell versions; the same kernel serves `rlm`.
6. Line 148 (AD-11): drop "the conflict is surfaced … not resolved here"; cite Library AD-3.
7. Line 152 (AD-12): paper = an `interval` trigger with `continuity` and a daily `paper.check` trigger; pause/resume = disable/enable.
8. Line 156 (AD-13): delete "and for spend above `settings.lab.ask_above_usd`" and "bounded by the engine's budgets" → "bounded by the engine's runaway guard".

### `architecture/lab-and-pods/LLD.md`, `DOC-CHANGES.md`, `UI-TO-BACKEND-MAP.md`
- `LLD.md:62-96`: column "Engine kind" → "base kind"; `qmb.run`, `qmb.sweep`, `qmb.walk_forward`, `qmb.robustness`, `qmb.optimize` → base `app_op`, effect `none`; `lab.note` → `note`.
- `LLD.md:117`: `"placement": "local"` → `"placement": "qmb"`.
- `LLD.md:245`: the paper template per item 7 above.
- `LLD.md:325,330,335`: delete the MANAGE-above-spend notes.
- `LLD.md:342`: "nothing else in the harness changes (ruling 24)" → "engine HARNESS-REQUESTS H17".
- `LLD.md:442`: delete the `lab.ask_above_usd` row.
- `LLD.md:484`: `KernelPort` adapter per spine item 5.
- `DOC-CHANGES.md:21`: "(table rows only, ruling 24)" → "(table rows, engine H17, operator grant)".
- `UI-TO-BACKEND-MAP.md:14`: "this laptop / VPS / Colab" → registry names `pc`, `contabo`, `qmb`, provider rows.

### `UI-HANDOFF.md`
- Line 21: replace with "The backend has four **decisions**: `allow_once`, `allow_always` (not for asking QMX tools), `reject` (with a message) and `answers` (AskUserQuestion). An answer returns `resolved | already_answered | expired | invalid | unknown`. There is no `reject_always`. 'For this errand' doesn't exist. Add 'expired, re-run from here'."
- Line 23: mark "compact now" as "needs harness request H15".
- Line 53: "29 object kinds" → "33 object kinds".
- Line 55: "plus 17 Library ones" → "plus 24 Library ones".
- Add a new **§9 "Machines, keys, providers, context"** with the 15 missing rows of section 5.
- §5: add "No spend asks anywhere in the Lab (ruling 27)."

### `research/methodology/33-state-of-play.md`
- Line 3 and line 27: "rulings 1-72" → "rulings 1-84".
- §3: mark items 1 (ruling 74), 4 (ruling 67), 6 self-improvement (ruling 79) as answered.
- Add a line: "Final rubric walk: `27b-final-rubric-walk.md` (6 blockers)".

### Operator decisions this walk surfaces (for the lead to ask, recommendation first)
1. **Grant H0 and H17** as export-only and table-row harness edits (recommended: yes; without them the engine's agent nodes and every new agent tool can't ship). Grant **H15 and H16** inside the engine build (recommended: yes; ruling 78 calls them critical).
2. **Does the 50% plan background cap still bind workflow agent nodes** under ruling 27 (recommended: keep it for the plan only; key providers are uncapped)?
3. **Data track first** (ruling 81): accept study 30 §4-§5 as the design for the first data packets, or run a short spine pass first (recommended: accept 30 and build tick backup plus import first).
