# 34 — Engine run triage

Date: 2026-10-18. Scope: every item the workflow-engine run logged but did not build. That means `D:\QMX-worktrees\qma-ship\engine\BACKLOG.md` (lines 5-96) and every low in `lows.md` (lines 3-90). The checker reports in `engine\review\` were skimmed for blockers and money findings. `ledger.tsv` and the tail of `decisions.tsv` give the state of the run. Nothing here is built. This file is input for the next plan (operator rule: no unplanned work in a planned run).

How to read the IDs:

- **B-n** is line n of `BACKLOG.md`. **L-n** is line n of `lows.md`.
- Later packets are written as **Appendix G L1 ... L19** (ENGINE-PLAN), so they do not clash with low IDs. Harness requests are **H0 ... H17** (HARNESS-REQUESTS.md).
- "Found by" gives the PR id and its GitHub number.
- Every row sits in exactly one class. Duplicates keep their own row and are listed at the end.

IDs follow the BACKLOG.md snapshot read at the start of this triage (96 lines, 92 items). The coordinator edited the file while this was written: B-96 (test costs not recorded) has since been removed, and a new heading "Added after the morning of 2026-10-18" now sits at line 97 with no items under it yet. TP4 is still running, so read everything under that heading before planning.

## State of the run

- 20 PRs are CLEAN and stacked: EP0-EP14 with HG1 and HG2 (#91-#107), and TP1-TP3 (#108-#110). TP4 is still building. Nothing is merged; he lands the stacks.
- The EP14 and TP4 review gate waits for him. Evidence for EP14 is in `review/EP14-review-*`. He has asked for a Fable review of the stacked PRs after TP4.
- Twelve checkers reported a blocker or a promoted medium (HG2, EP3, EP4, EP6, EP7, EP10, EP11, EP12, EP13, TP1, TP2, TP3). Each was fixed in its one fix round **except TP3 B1**: the money lint does not scan script text or prompts. By his ruling that one went to BACKLOG (B-89, B-93), not to a new PR.
- Money and keys incidents during the run: EP10's lane script wrote the OpenRouter key row into the ship home `settings.toml` (restored byte-exact, fixed). EP14's early builder runs read his control token from the vault through the old x13 host (never printed, fixed in EP13's round). No key was printed and no money moved.
- OpenRouter spend across the program was about $3.7 (upper bound). The spend freeze is lifted (rule b). TP2 and TP3 real-model lanes are still owed.

## Urgent for the run that is still finishing

1. **B-95: the default test model is Kimi on OpenRouter.** Rule (b) says tests run on haiku through his plan login, and OpenRouter only proves other providers work. TP4's real-model lane, and the owed TP2/TP3 lanes, will try Kimi first unless the coordinator pins haiku for them. This is a lane setting, not a code change.
2. **B-75 / B-94: full `just ci` is red** on a one-line qma-core test that EP2 broke. It does not block the run. It blocks landing the stack green. He has to choose: a one-line test PR outside the engine boundary, or land with CI red.
3. **B-89 / B-93 and B-30: the two critical security gaps are in the stack he will land.** A Library script can read the plan login and the `qmx/*` keyring, and the money lint does not read script text. No broker is wired today, so nothing is exposed yet. Do not enable a live trigger on any script that did not ship with the templates until these are fixed.
4. **B-44: the `--mode live` CLI bypass** also ships in the stack. It runs any folder live with no Library object.
5. **L-23: the default strong-role ladder includes `claude/fable`.** Ruling 87 and his standing rule say no Fable unless he asks. A run whose opus candidate is unavailable could fall through to Fable. Check the ship home's `[roles]` before the Fable review and before the real-model lanes.

## Counts

| Class | critical | high | medium | low | Total |
|---|---|---|---|---|---|
| SECURITY | 3 | 7 | 6 | 2 | 18 |
| BUG | 0 | 2 | 29 | 25 | 56 |
| HARNESS | 0 | 2 | 8 | 3 | 13 |
| SPEC-GAP | 0 | 0 | 17 | 9 | 26 |
| LATER-PACKET | 0 | 0 | 11 | 4 | 15 |
| HYGIENE | 0 | 3 | 4 | 45 | 52 |
| **Total** | 3 | 14 | 75 | 88 | **180** |

Rows: 92 BACKLOG items (B-5 to B-96) and 88 lows (L-3 to L-90).

The 180 rows hold 164 distinct issues once the 16 duplicate pairs below are folded. Critical is 3 rows but 2 issues (B-89 and B-93 are one item).

## 1. SECURITY

Logins, keys, broker access or the money rule are at risk because an architecture assumption broke.

| ID | Summary | Sev | Touches | Owner | Found by | Note |
|---|---|---|---|---|---|---|
| B-30 | A host script runs as his user with cwd under the QMX home, so the plan login (../../../../claude) and qmx/* keyring entries are readable | critical | AD-24, AD-25, home layout | engine | EP7 (#100) |  |
| B-89 | The money lint scans only node types and parameters, not script text or prompts; host scripts can import keyring and qmn | critical | AD-24, definition/lint.py, nodes/script.py | engine | TP3 (#110) | dup B-93; related L-25 |
| B-93 | (coordinator) Money lint does not scan script text or prompts; host scripts can import keyring and qmn | critical | AD-24 | engine | TP3 (#110) | dup B-89 |
| B-17 | A node's credentials may name any qmx/* ref, including a broker ref such as qmx/ctrader-*; nothing refuses it | high | AD-24, AD-28, definition/lint.py | engine | EP3 (#96) |  |
| B-31 | A script process outlives an engine crash (no Job object, no parent-death signal) and can race a rerun in the same zone | high | AD-24, workers/local.py | engine | EP7 (#100) |  |
| B-39 | Provider failure messages must be redacted before the ledger and inbox, or a key echoed by a provider lands in inbox.sqlite | high | AD-17, AD-28, definition/lint.redact | engine | EP8 (#101) | dup L-50; related L-58 |
| B-44 | python -m qmx_engine run FOLDER --mode live runs any folder live with no Library object, outside AD-11 | high | AD-11, CLI | engine | EP9 (#102) |  |
| L-25 | The money lint reads node type and parameter values only; names, notes, settings, pinData and ref file contents are unread | high | AD-24, definition/lint.py | engine | EP3 (#96) | same gap as B-89 |
| L-50 | Inbox title and cause copy node_failed messages unredacted | high | AD-17 | engine | EP8 (#101) | dup B-39 |
| L-58 | redact needs a non-word char before a key, so key_sk-or-v1-... passes unredacted | high | definition/lint.py TOKEN_SHAPES | engine | EP10 (#103) | related B-39 |
| B-13 | The money lint uses only money_path (a smaller matcher); the fuller descriptors.name_money_act is barred by the import rule | medium | AD-24, AD-1 import rule, definition/lint.py | engine | EP3 (#96) | related L-24 |
| B-45 | The service lets an agent or workflow caller publish and enable; must be MANAGE (one ask) per AD-22 | medium | AD-22, AD-11, ruling 80 | engine | EP9 (#102) | dup L-53 |
| L-24 | money_path deny-list spelling gaps reach the lint: flatten, set_leverage, placeorder | medium | money_path, AD-24 | engine | EP3 (#96) | related B-13 |
| L-51 | Runs.version_state reads any workflow object not on a draft ref as published | medium | AD-11, service/runs.py | engine | EP9 (#102) |  |
| L-52 | explain prints node failure messages verbatim; a script echoing input to stderr shows raw values | medium | service/explain.py | engine | EP9 (#102) | EP13 fix redacted keys; verify explain path |
| L-53 | versions.publish and enable accept Caller("workflow"), against AD-11 and ruling 80 | medium | service/versions.py | engine | EP9 (#102) | dup B-45 |
| L-39 | effects.restore() joins snapshot paths onto the zone with no containment check | low | workers/effects.py, AD-24 | engine | EP7 (#100) |  |
| L-71 | x13 lane clients read the operator's real control token from the OS vault | low | scripts/live/engine | engine | EP13 (#106) | fixed in the EP13 fix round (decisions.tsv) |

## 2. BUG

Built behaviour that is wrong.

| ID | Summary | Sev | Touches | Owner | Found by | Note |
|---|---|---|---|---|---|---|
| B-63 | A time wait node never resumes on its own; a run held on wait seconds stays waiting forever | high | AD-5, AD-10 | engine | EP13 (#106) |  |
| B-69 | An agent chunk killed before its task reached the chat resumes with only RESUMED and no task; it wanders and parks the run | high | AD-34, nodes/agent.py | engine | EP14 (#107) |  |
| B-25 | The ledger writer accepts a second run_created for one run | medium | AD-23, ledger | engine | EP6 (#99) | dup L-36 |
| B-26 | Host script idle_seconds is not enforced, large stdout is not spilled, declared credentials are refused (resolution unbuilt) | medium | AD-24, nodes/script.py | engine | EP7 (#100) | credential half -> L4 |
| B-29 | A reversible retry undoes files another attempt wrote into the same zone at the same time | medium | AD-8, workers/effects.py | engine | EP7 (#100) |  |
| B-42 | EngineService reads settings once at open; a [engine] or [roles] edit reaches runs only after reopen | medium | AD-13, standing rule: configurable = editable | engine | EP9 (#102) |  |
| B-54 | The limit timer keeps Engine.start awaiting until reset, so a service test run holds its caller for hours | medium | AD-9, runner | engine | EP11 (#104) | verify after EP12 scheduler wake |
| B-55 | The watchdog counts the worker's own 10 s heartbeats as activity, so stalled never fires | medium | AD-16, watchdog | engine | EP11 (#104) | dup L-44 |
| B-57 | after_unknown retries a model-bearing node once even when it declares an irreversible effect | medium | AD-8, workers/effects.py | engine | EP11 (#104) | must be fixed before L6 |
| B-60 | A trigger's role_pins and effort_pin are stored but not applied; after-triggers fire only on scheduler runs | medium | AD-10, AD-13 | engine | EP12 (#105) |  |
| B-61 | A test run resumed by a wake gets no fresh test report, so its draft still reads waiting | medium | AD-11 | engine | EP12 (#105) |  |
| B-66 | Cancelling a run does not stop the child runs of a running subworkflow node | medium | SD 13, subworkflow | engine | EP13 (#106) |  |
| B-72 | run-now on a trigger whose last run parked returns an id and silently starts nothing | medium | AD-10, triggers | engine | EP14 (#107) |  |
| B-73 | A run held on a wait node and then resumed reads running from status_of, though nothing runs | medium | AD-15, status_of | engine | EP13 (#106) |  |
| B-77 | The fake switch answers llm nodes only; an agent node on a fake run calls the harness or is Unavailable | medium | SD 6.2, Run.agent_executor | engine | TP1 (#108) |  |
| B-92 | The host's draft view lists problems without needs_unmet, so a waiting draft reads as plain validated | medium | drafts.problems | engine | TP4 |  |
| L-16 | meter() has no cooldown; a turn with no rate-limit event returns None and every later call spends another haiku turn | medium | usage.py meter | harness | HG2 (#94) |  |
| L-32 | fold does not compare data.attempt with the scheduled attempt, so a late ending can settle the current attempt | medium | core/fold.py | engine | EP5 (#98) |  |
| L-36 | fold takes the last run_created's settings, so a second run_created moves chunk boundaries on resume | medium | core/fold.py | engine | EP6 (#99) | dup B-25 |
| L-37 | wait resume_at reads naive now as local time and compares instants as text, so a wait can fire early | medium | nodes/wait.py, core/waits.py | engine | EP6 (#99) |  |
| L-38 | Idempotency keys join with ':' and node ids may contain ':', so two keys can collide | medium | core/replay.py, AD-8 | engine | EP6 (#99) |  |
| L-40 | A directory junction in the write zone raises PermissionError outside the worker's try; the engine dies mid-attempt | medium | workers/effects.py | engine | EP7 (#100) |  |
| L-44 | The watchdog stall rule keys on the worker's own heartbeat, so a hung local executor never goes idle | medium | AD-16, watchdog | engine | EP8 (#101) | dup B-55 |
| L-45 | The runaway guard is checked only before rungs and new attempts; in-flight attempts run past a breach | medium | SD 10.3, AD-16 | engine | EP8 (#101) |  |
| L-60 | The warm-first gate holds chunks with no event; an idle_seconds under 10 s stall-cancels them and parks the run | medium | nodes/agent.py | engine | EP11 (#104) |  |
| L-63 | The anti-spin guard leaves a run waiting if admission keeps reporting the same past reset | medium | Run.wake | engine | EP11 (#104) |  |
| L-68 | workflow_runs_list drops in-flight runs; run views read null item while running | medium | control_door.py | engine | EP13 (#106) |  |
| L-69 | Cancelling a trigger-fired run leaves its fire running until the lease lapses, holding the max_concurrent slot | medium | ticker.py | engine | EP13 (#106) |  |
| L-80 | trace_export.run_files reads each artifact unguarded; a moved file makes the export raise after the run ended | medium | trace_export | engine | TP2 (#109) |  |
| L-81 | RS4's number check counts LLM free text as evidence; gaps is not in x-prose | medium | RS4 template | engine | TP2 (#109) |  |
| L-86 | DB gather.py skips only mode == "test" (fail-open), and a --mode live --fake run counts as live | medium | DB template | engine | TP3 (#110) | related B-78 |
| B-37 | A reversible attempt cancelled through LocalWorker.cancel is retried by the ladder; operator stop must go through run_cancelled | low | AD-16, workers | engine | EP8 (#101) |  |
| B-43 | A draft edited after its variant resolved loses variant_of; fake Library does not enforce refs/drafts ownership | low | AD-11, AD-14 | engine | EP9 (#102) | ownership -> L11 |
| B-67 | GET /api/runs lists harness chat journals as agent runs | low | runs listing | harness | EP13 (#106) |  |
| L-8 | Harness._options is never pruned; a long-lived host keeps every attempt's hook closures | low | harness.py | harness | HG1 (#92) |  |
| L-9 | _observer catches Exception only; a CancelledError from an observer escapes to the SDK handler | low | launch.py | harness | HG1 (#92) |  |
| L-17 | meter() awaits chat.close() before cleanup; if close raised, the record would stay listed | low | usage.py meter | harness | HG2 (#94) |  |
| L-28 | A BaseException in an operation kills the writer thread and later write() calls wait forever | low | ledger writer | engine | EP4 (#97) |  |
| L-29 | An ending event without node_id and attempt is stored but closes no span; partition vs partition_id naming | low | spans.py | engine | EP4 (#97) |  |
| L-31 | append() with non-dict data fails with AttributeError instead of ValueError | low | ledger append | engine | EP4 (#97) |  |
| L-33 | step() does not catch an executor exception, so a raising executor crashes the driver | low | nodes/base.py | engine | EP5 (#98) | verify runner owns it |
| L-34 | node_scheduled carries no input hash, which SD 3.2 lists | low | core/simulate.py, SD 3.2 | engine | EP5 (#98) |  |
| L-47 | An inbox item's tried list is taken before the ladder walks, so a first failure reads tried [] | low | AD-17 | engine | EP8 (#101) |  |
| L-54 | An overlay draft whose resolved hash was tested reads tested, yet publish refuses it | low | AD-11 | engine | EP9 (#102) |  |
| L-55 | tests.run rewrites a variant draft's head before the run, even when the test fails | low | service/tests.py | engine | EP9 (#102) |  |
| L-56 | A passed live run never adds a tested-by edge, though AD-11 counts it | low | AD-11 | engine | EP9 (#102) |  |
| L-57 | HarnessAdapter.marks is never pruned; grows in a long-lived host | low | ports/harness_adapter.py | engine | EP10 (#103) |  |
| L-61 | limit_wait lets a plan attempt start when the reading is over the share but has no resets_at (harness cap still refuses) | low | admission.py | engine | EP11 (#104) |  |
| L-64 | Two Scheduler instances on one Engine double-drive a run when a lease lapses | low | triggers/claims.py | engine | EP12 (#105) | host must keep one scheduler |
| L-65 | A wake can resume a run while its fire still settles, and the fire is later written waiting over a finished run | low | ticker.py, claims.py | engine | EP12 (#105) |  |
| L-70 | Host refusal is check-then-write; two hosts started together on one home can both pass | low | host.py | engine | EP13 (#106) |  |
| L-75 | meta.needs is outside the content hash, so a needs draft can reach tested and publish | low | AD-11 | engine | TP1 (#108) |  |
| L-82 | RS0's writer can launder a number as an assumption | low | RS0 template | engine | TP2 (#109) |  |
| L-83 | The shared citation_check lets a claim with id equal to its source_id cite itself | low | citation_check block | engine | TP2 (#109) |  |
| L-87 | render_and_grade matches a prose number against timestamps in the evidence | low | render_and_grade block | engine | TP3 (#110) |  |
| L-88 | links_check, lines_check and assembles tell inputs apart by shape, order-dependent | low | templates blocks | engine | TP3 (#110) |  |

## 3. HARNESS

Something QMA v2's harness (or qmx-control) must provide.

| ID | Summary | Sev | Touches | Owner | Found by | Note |
|---|---|---|---|---|---|---|
| B-51 | NewChat has no tools option, so an llm chat still carries the Claude Code tools; read-only tool calls can run | high | H2, AD-4 | harness | EP10 (#103) | related B-70 |
| B-70 | An agent node's tools: [] is only stated in the brief; a resumed chat still called Glob, Bash and TaskList | high | H2 | harness | EP14 (#107) | same request as B-51 |
| B-5 | Saving a draft or running a test still asks once in default mode unless an allow rule exists; the effect table only sets the mandatory ask | medium | AD-22, H17, tools.py | harness | HG1 (#92) |  |
| B-6 | compact_at and hooks are held in memory only; a Background chat reloaded after a host restart launches without them | medium | AD-34, H15, H16, home.py | harness | HG1 (#92) | dup L-7 |
| B-11 | No public way to build the ControlService; scripts import qma.harness.routes.control_service | medium | AD-3, Appendix G L1 | harness | EP2 (#95) |  |
| B-50 | No public way to close or delete a chat; each llm attempt's chat stays listed and its CLI stays live | medium | AD-3 | harness | EP10 (#103) |  |
| B-53 | The node brief cannot be cached across chunks; needs a per-chat appended system prompt | medium | AD-34, H2 | harness | EP11 (#104) |  |
| B-56 | The engine records each agent chat's session id but not its home (AD-35 per-chat home) | medium | AD-35 | harness | EP11 (#104) | Appendix G L17 |
| B-65 | qmx-control cannot tell a REST call from an agent tool call, so his UI saves are recorded as agent:qmx-control | medium | AD-22, server.py | harness | EP13 (#106) |  |
| L-7 | compact_at and hooks live only in Harness._options; a resumed chat after restart launches without them | medium | AD-34, harness.py | harness | HG1 (#92) | dup B-6 |
| B-8 | Each meter turn leaves a "Plan usage meter" session row in qmx-control and briefly lists its chat | low | qmx-control sessions, usage.py | harness | HG2 (#94) | dup L-18 |
| B-10 | qma-harness ships no py.typed; the engine works around it with pyright extraPaths | low | qma-harness packaging | harness | EP2 (#95) |  |
| L-18 | The "Plan usage meter" session row stays in control.db and the chat shows in GET /api/chats for ~5 s | low | qmx-control | harness | HG2 (#94) | dup B-8 |

## 4. SPEC-GAP

The architecture is silent, inconsistent or wrong, so builders guessed.

| ID | Summary | Sev | Touches | Owner | Found by | Note |
|---|---|---|---|---|---|---|
| B-15 | rule ports (true/false) and loop ports (in/next, body/main) were invented; the spine does not name them | medium | AD-4, AD-5 | engine | EP3 (#96) |  |
| B-18 | Node events carry no node id, iteration or partition in SD 3.2; span statuses gate and cancelled have no deriving event | medium | SD 3.2, AD-15, spans.py | engine | EP4 (#97) |  |
| B-24 | A loop-body node fed by a skipped body node and an outside node still runs on the outside value alone | medium | AD-5, core.ready | engine | EP6 (#99) | related B-87 |
| B-27 | subworkflow names a child folder inside the parent; caller_policy checked only at dispatch; a waiting child fails the parent | medium | AD-14, AD-5 subworkflow | engine | EP7 (#100) |  |
| B-38 | SD 17 says 2M tokens, 16 agents, 1,000 tool calls, 4 h; settings.py says 400k, 12, 2 h, no tool-call default | medium | SD 17, Appendix H, AD-16 | engine | EP8 (#101) | dup L-49 |
| B-49 | The runaway guard counts cache reads, so the 400k default trips after about 20 to 25 model turns | medium | AD-16, Appendix H | engine | EP10 (#103) |  |
| B-68 | triggers_enable also enables the version, but triggers_disable leaves it enabled, so another trigger can still fire | medium | AD-10, AD-22 | engine | EP13 (#106) |  |
| B-76 | A Library Bundle drops a subworkflow's child folder, so templates carry copies of shared blocks | medium | AD-14, Library bundle | Library | TP1 (#108) |  |
| B-78 | A script cannot tell a test run from a live run; templates pin fixtures through a run input | medium | AD-11, AD-24 env | engine | TP1 (#108) | related B-80, L-86 |
| B-80 | A script's env carries no run id, home or mode; RV's week.py derives them from its cwd | medium | AD-24 | engine | TP2 (#109) | dup L-84 |
| B-82 | No engine call replays a past run on an edited folder (R9 step 4), so every RV edit stays untested | medium | AD-7, AD-26 | Lab | TP2 (#109) |  |
| B-87 | A node fed by two branches runs as soon as one carries output; no "wait for all live inputs" edge option | medium | AD-5, core.ready | engine | TP3 (#110) | related B-24 |
| B-88 | Human points (sign a promotion, accept a lesson) end as result cards; decision cards in the inbox are missing | medium | AD-17, L15 human_gate | UI | TP3 (#110) |  |
| L-23 | The strong-role ladder is claude/opus -> claude/fable -> gpt; ruling 87 says no more Fable | medium | SD 9, Appendix H, ruling 87 | engine | EP2 (#95) |  |
| L-48 | The wall-time deadline counts from run_created, so a run asleep in a wait node is paused as runaway on wake | medium | AD-16, AD-9 | engine | EP8 (#101) |  |
| L-49 | Guard defaults follow settings.py; SD 17's row is stale; no runaway.tool_calls default exists | medium | SD 17, Appendix H | engine | EP8 (#101) | dup B-38 |
| L-84 | RV's week.py opens InboxTable from a script and derives its home from cwd parents | medium | AD-24 | engine | TP2 (#109) | dup B-80 |
| B-12 | The spine's layer diagram draws core -> ledger/ports/nodes, but AD-1 and the plan forbid those imports | low | ARCHITECTURE-SPINE structural seed, AD-1 | engine | EP2 (#95) |  |
| B-14 | AD-4 port kinds (reference, data, event, control) are not typed; edges are checked by name only | low | AD-4 | engine | EP3 (#96) |  |
| B-16 | agent.max_turns has a default in Appendix H but the lint refuses an agent without one; max_tool_calls is also split | low | SD 2.4, Appendix H, definition/lint.py | engine | EP3 (#96) |  |
| B-23 | Late partition failure after a join leaves no inbox line; no_progress_rounds has no direction; join timeout uses reason wait | low | SD 3.2, AD-16 | engine | EP6 (#99) |  |
| B-83 | Run artifacts are typed only run-file; typed artifacts (card, source) need a type per file | low | AD-14, Library artifact types | Library | TP2 (#109) |  |
| L-20 | The AD-6 rule allows time.monotonic and perf_counter in core, which is not replayable | low | AD-6 | engine | EP2 (#95) |  |
| L-26 | pinData is outside the content hash, so a pinData change keeps the tested mark | low | SD 2.2, AD-11 | engine | EP3 (#96) |  |
| L-42 | LocalWorker.run(job, executor, emit) differs from WorkerPort.run(NodeJob) with streamed events | low | AD-20, AD-25 | engine | EP7 (#100) | reconcile before L8 |
| L-46 | on_runaway degrade lets the whole held batch through | low | AD-16 | engine | EP8 (#101) |  |

## 5. LATER-PACKET

Planned work not yet built, mapped to Appendix G or a new packet.

| ID | Summary | Sev | Touches | Owner | Found by | Note |
|---|---|---|---|---|---|---|
| B-20 | Nested fan-out, a loop over fanned input, and a loop inside a loop body do not run; the core parks | medium | AD-5, core | engine | EP6 (#99) | new packet: nested fan-out |
| B-28 | Nothing folds a gate answer; an irreversible step with an unknown outcome waits forever; pinData ignored in test mode | medium | AD-8, AD-17 | engine | EP7 (#100) | new packet: gate folding (with L15) |
| B-32 | InboxPort.resolve records the answer, but nothing folds it into the run (gate_resolved, retry, skip_node, stop) | medium | AD-17, service | engine | EP8 (#101) | new packet: gate folding |
| B-33 | Raising the runaway guard and resuming from the run card, and ending waiting(runaway) runs, are not built | medium | AD-16, AD-9 | engine | EP8 (#101) | L18 run cards + new engine packet |
| B-35 | A failed fan-out partition read only by joins does not walk the ladder; chunk retry before the join closes is unbuilt | medium | AD-16, AD-34 | engine | EP8 (#101) | new packet: chunk retry |
| B-41 | A subworkflow's child run is not exported to the Library (no trace, summary or edges) | medium | AD-14, AD-15 | Library | EP9 (#102) | L11 |
| B-46 | The grader node's llm judge mode is unbuilt and fails grader_mode_unavailable | medium | AD-5, grader.py | engine | EP10 (#103) | new packet: grader llm mode; dup B-81 |
| B-47 | SD 6.2 pinData (pinned outputs replace execution in test mode) is unbuilt for every kind | medium | SD 6.2, AD-11 | engine | EP10 (#103) | new packet: pinData |
| B-52 | Agent prompts carry no frozen memory snapshot (AD-18 order); nothing takes one per run | medium | AD-18 | engine | EP11 (#104) | L12 |
| B-64 | The engine host serves no harness chat routes and builds ControlService without the claude/environment parsers | medium | AD-3, AD-21 | harness | EP13 (#106) | L1 |
| B-81 | The grader llm judge still refuses, so RS4's rubric judge cannot route a weak review to revision | medium | AD-5 | engine | TP2 (#109) | dup B-46 |
| B-34 | Doctor bad_input should rerun the upstream step once; logic verdict should write a challenger ref | low | AD-16, AD-26 | engine | EP8 (#101) | doctor verdicts -> L13 |
| B-36 | Doctor repair hint reaches the attempt only as resolved_model; degrade does not know the cheapest candidate | low | AD-13, AD-16 | engine | EP8 (#101) | L2 (pool knows cost) |
| B-40 | runs.cancel/resume missing from EP9; interrupted is derived only from a drive's outcome, never from the ledger | low | SD 13, AD-21 | engine | EP9 (#102) | cancel/resume landed in EP13; ledger-derived interrupted -> new packet |
| B-58 | Nothing ran Scheduler.serve until the EP13 host; paused runs and triggers need a ticking process | low | AD-10 | engine | EP12 (#105) | EP13 (verify closed) |

New packets that Appendix G does not name: **gate folding** (B-28, B-32), **nested fan-out** (B-20), **chunk retry under the ladder** (B-35), **grader llm mode** (B-46, B-81), **pinData** (B-47), and a **ledger-derived run state** reader (B-40).

## 6. HYGIENE

Small fixes: tests, scripts, docs text, dead code, defaults.

| ID | Summary | Sev | Touches | Owner | Found by | Note |
|---|---|---|---|---|---|---|
| B-75 | qma-core test_qma_ui_contract_placeholder_is_not_shipped pins the workspace list and is red since EP2 added qmx-engine | high | qma-core tests | engine | EP14 (#107) | dup B-94; blocks landing |
| B-94 | (coordinator) Full just ci is red on the qma-core placeholder test; one-line update outside the engine boundary | high | qma-core tests | engine | EP2 (#95) | dup B-75 |
| B-95 | (coordinator) Default test model is OpenRouter kimi-k2.5 and test mode tries it first; rule (b) says haiku via the plan | high | settings.py roles.test_only, Appendix H | engine | EP2 (#95) |  |
| B-22 | validate does not check loop, join or wait parameters, or that a join has exactly one inbound one-edge | medium | definition/validate | engine | EP6 (#99) |  |
| B-84 | The render-and-grade number check accepts any number in another input, so LLM intermediates make it circular | medium | templates shared blocks | engine | TP2 (#109) | pack-wide rule + test |
| B-90 | validate never runs expr.check on rule and loop predicates, so items.ok == true fails only at run time | medium | definition/expr.py | engine | TP4 |  |
| L-22 | Import and AD-6 rules miss aliases, attribute chains, importlib and uuid4/os.urandom/secrets | medium | AD-1, AD-6 lint rules | engine | EP2 (#95) |  |
| B-7 | Harness refusal text points at POST /api/usage/meter, which cannot help on today's CLI | low | usage.py | harness | EP0 (#91) | dup L-6 |
| B-9 | usage.py docstrings are stale and project.py's METER pattern matches nothing on CLI 2.1.299 | low | usage.py, project.py | harness | HG2 (#94) |  |
| B-19 | rule/trigger were marked unavailable until the runner; memo validity comes from events, so invalidate_by_definition has no reader | low | registry, ledger.memo | engine | EP5 (#98) | dup L-35 |
| B-21 | Chunk window is the context_window setting, not the model's own window; tokens estimated as JSON bytes / 4 | low | AD-34, chunk plan | engine | EP6 (#99) |  |
| B-48 | Default role rows gpt name no model, so roles.parse never resolves them | low | settings.py, Appendix H | engine | EP10 (#103) | dup L-19 |
| B-59 | The scheduler checks refs and skills only when given an inventory; the host should pass preflight lists | low | AD-10, preflight | engine | EP12 (#105) | verify in EP13 host |
| B-62 | Fire endings are written one by one; 500 fires on one tick take about 1.9 s to settle | low | ticker | engine | EP12 (#105) |  |
| B-71 | explain text lists attempts but not spans; chunk partitions show only in --json and REST | low | service/explain.py | engine | EP14 (#107) |  |
| B-74 | x10_llm doctor lane cannot pass on Kimi; it needs a deterministic bad answer (fake recording) | low | scripts/live/engine | engine | EP14 (#107) |  |
| B-79 | A template's needs live twice (catalogue row and meta.needs); nothing checks they agree | low | templates catalogue | engine | TP1 (#108) |  |
| B-85 | The fake switch answers every chunk with the whole recorded file, so claims repeat per chunk | low | fake provider | engine | TP3 (#110) |  |
| B-86 | Card roles analyst, coordinator, validator and explainer are not in the [roles] defaults | low | settings.py roles | engine | TP3 (#110) |  |
| B-91 | Template.folder could be required; install.py's "not yet built" branch is dead code | low | install.py | engine | TP4 |  |
| B-96 | (coordinator) Real-model test costs and wall times for RS2, A, DB and T4 are not recorded in the catalogue | low | templates catalogue | engine | TP4 | removed from BACKLOG.md after the snapshot; check it was recorded |
| L-3 | plan_harness log says "five-hour reading from meter()" but the value is the ledger's last reading | low | scripts/probes/engine/common.py | engine | EP0 (#91) |  |
| L-4 | p_cache plan check cannot fail; the 15k cache read is the CLI preamble, not the brief | low | p_cache.py | engine | EP0 (#91) |  |
| L-5 | plan_harness leaves a seed chat record and workspace in the ship home | low | scripts/probes/engine | engine | EP0 (#91) |  |
| L-6 | BackgroundCap refusal text advises POST /api/usage/meter, which gives no reading on CLI 2.1.299 | low | usage.py | harness | EP0 (#91) | dup B-7 |
| L-10 | Compaction at 40% is not proven live; HG1 lane 2 proves only that the env var reaches the CLI | low | AD-34 | harness | HG1 (#92) |  |
| L-11 | p_runner_outside.py writes results without a log prefix, so reruns overwrite the owner's evidence | low | scripts/probes/engine | engine | EP1 (#93) |  |
| L-12 | The scratch-folder fallback isolates env only, not files; Git Bash reaches every host path including the plan folder | low | p_runner_outside.py, feeds L6 | engine | EP1 (#93) | FINDINGS wording; matters for L6 design |
| L-13 | raw_client.py repeats EP0's lane lock and env scrub | low | scripts/probes/engine | engine | EP1 (#93) |  |
| L-14 | EP1 perf note calls task 01's slowdown noise; reruns disagree | low | FINDINGS.md | engine | EP1 (#93) |  |
| L-15 | p_model_ids.py prints ConnectionResetError tracebacks on shutdown | low | p_model_ids.py | engine | EP1 (#93) |  |
| L-19 | settings.py role rows use gpt with no model, against the profile/model spelling | low | settings.py | engine | EP2 (#95) | dup B-48 |
| L-21 | A settings test reads settings.py as text (source-shape test) | low | tests | engine | EP2 (#95) |  |
| L-27 | Racing writers are refused with "an unknown pid" because the lock is taken before the pid is written | low | ledger writer | engine | EP4 (#97) |  |
| L-30 | The write-error lane makes the connection read-only, not the file as the plan said | low | EP4 lane | engine | EP4 (#97) |  |
| L-35 | After an edit A->B->A the core reuses A's memo while ledger.memo says invalid; two sources of truth | low | AD-7, ledger.memo | engine | EP5 (#98) | dup B-19 |
| L-41 | x07 monitor lane's act script prints non-JSON, and the lane still passes | low | scripts/live/engine | engine | EP7 (#100) |  |
| L-43 | .snap folders under the zone are never pruned; each reversible attempt copies the whole zone | low | workers/effects.py | engine | EP7 (#100) |  |
| L-59 | x10_llm.py and e21 overwrite the owner's throwaway homes on rerun | low | scripts/live/engine | engine | EP10 (#103) |  |
| L-62 | EP11 lane 1 overwrote the EP10 checker's log | low | scripts | engine | EP11 (#104) |  |
| L-66 | scheduler.heartbeat is a dead setting; a tick at or over the lease is not warned | low | settings | engine | EP12 (#105) |  |
| L-67 | x12_scheduler.py loses its log prefix after the regression lane | low | scripts | engine | EP12 (#105) |  |
| L-72 | run_all's guard compares only the settings hash, so an edit-and-restore passes | low | run_all.py | engine | EP14 (#107) |  |
| L-73 | run_all attributes evidence by mtime, so a row lists the previous check's log | low | run_all.py | engine | EP14 (#107) |  |
| L-74 | Lane 4 waits 4 s before the kill, so it never covers a kill in a chunk's first seconds | low | EP14 lane 4 | engine | EP14 (#107) | covers B-69 |
| L-76 | RS1 and T3 carry fixture_ref parameters the engine never reads | low | templates | engine | TP1 (#108) |  |
| L-77 | T3 live never finds a surprise (free feed has no actuals); not in the README's Left out list | low | templates T3 | engine | TP1 (#108) |  |
| L-78 | t_templates.py loses its log prefix after the first lane | low | scripts | engine | TP1 (#108) |  |
| L-79 | x10_llm schema and ask lanes depend on Kimi misbehaving and will flake | low | scripts | engine | TP1 (#108) |  |
| L-85 | No unit case plants an invented number in any TP2 template | low | tests | engine | TP2 (#109) |  |
| L-89 | A live start of a force-published draft is refused needs_unmet without the need line | low | service | engine | TP3 (#110) |  |
| L-90 | Template tests overlap mildly on needs_unmet | low | tests | engine | TP3 (#110) |  |

## Architecture amendment list

Every SECURITY and SPEC-GAP item, written as a decision the architecture must make. Grouped by the AD it amends. Duplicates are named together.

### AD-24 — Host-tier envelope (the biggest gap)

- **Plan login and keyring reach (B-30, critical).** Decide how a host script is kept from the plan login and the `qmx/*` keyring. Options: move the plan folder outside the QMX home and deny it by ACL, or run host scripts as a separate low-rights user, or drop the host tier for Library scripts and require the Docker tier (AD-25). The env allow-list alone cannot meet AD-24.
- **Money lint scope (B-89, B-93, L-25, critical).** Decide that the money deny-list covers script text, prompt text, node names, notes, settings, pinData and ref file contents. It should match call-shaped verb phrases, because a plain identifier scan flags `open_positions` and `promotion`. Also decide that host scripts may not import `keyring` or `qmn` (an import deny-list, or a separate interpreter without them).
- **Matcher reuse (B-13, L-24).** Decide whether the engine lint may import `qma.core.barriers.descriptors.name_money_act` (an AD-1 import exception), so the lint and the harness gate share one fuller matcher. Decide whether spelling variants (`placeorder`, `set_leverage`, `flatten`) are in scope or left to the read-only broker token as the real guard.
- **Broker credential refs (B-17).** Decide that the definition lint refuses any `credentials` binding to a broker ref (`qmx/ctrader-*` and any future broker label), whatever the node kind.
- **Orphan scripts (B-31).** Decide the mechanism for "a script that outlives its run": a Windows Job object with KILL_ON_JOB_CLOSE and a POSIX parent-death signal, plus a sweep of orphans at engine start before any resume.
- **Snapshot containment (L-39).** Decide that restore paths must stay inside the write zone (an `is_relative_to` check), even for trusted scripts.
- **Run context in the script env (B-78, B-80, L-84).** Decide whether host scripts get `QMX_RUN_ID`, `QMX_HOME` and `QMX_MODE` (test or live), and whether a script may open engine stores (RV's `week.py` opens InboxTable). This also settles whether a test run may fetch from the network.
- **Probe scripts and the vault (L-71).** Decide that lane scripts never read his real control token; throwaway homes use their own. (Fixed for x13 in the EP13 round; the rule should be written down.)

### AD-28 / AD-17 — Secrets in messages

- **Redaction everywhere (B-39, L-50, L-52, L-58).** Decide one redaction pass that every provider message, node failure message, inbox title and cause, and explain output goes through before the ledger, inbox or REST. Decide the token shapes: a key glued to a word (`key_sk-or-v1-...`, `apikeysk-...`) must be caught.

### AD-11 / AD-22 — Lifecycle, test gate and who may publish

- **CLI live bypass (B-44).** Decide that live runs go only through the service with a published Library version: drop `--mode live` from the CLI, or gate it the same way.
- **Who may publish and enable (B-45, L-53).** Decide that only a user principal may publish or enable, and that agent or workflow callers are refused in the service, not only by the MANAGE ask.
- **Published means on main (L-51).** Decide that a version is "published" only when it is on `main`, as `Versions.get` already checks.
- **What the tested mark covers (L-26).** Decide whether pinData (and `meta.needs`, see L-75) are part of the content hash, so a change to them drops "tested".

### AD-1 / AD-6 — Core purity and determinism

- **Layer diagram (B-12).** Redraw the spine's layer diagram so core does not import ledger, ports or nodes, matching AD-1 and the plan.
- **Monotonic clocks in core (L-20).** Decide whether `time.monotonic` and `perf_counter` are allowed in core and definition. AD-6 names wall clock only, but a monotonic read is not replayable either.

### AD-4 / AD-5 — Node contract, kinds and edges

- **Port names (B-15).** Name `rule` ports (fixed true/false, or one port per branch) and `loop` ports (in/next, body/main, done) in the spine.
- **Port kinds (B-14).** Decide whether port kinds (reference, data, event, control) are typed in the registry and checked on edges, or dropped from AD-4.
- **Agent caps (B-16).** Decide one rule: `agent.max_turns` has a default (Appendix H says 12), or the lint requires it. Same for `max_tool_calls` (SD 2.4).
- **Readiness of multi-input nodes (B-24, B-87).** Decide the default for a node fed by two branches: run when any input carries output (today), or wait for all live inputs. Offer the other as an edge option.
- **Subworkflows (B-27, B-76).** Decide how a subworkflow names its child: a pinned Library object, or a child folder carried in the bundle. Decide whether `caller_policy` is checked at validation, and whether a waiting child makes the parent node wait instead of fail.

### AD-13 — Roles

- **Fable in the ladder (L-23).** SOLUTION-DESIGN 9's strong ladder `claude/opus -> claude/fable -> gpt` conflicts with ruling 87 (no more Fable) and his standing rule (Fable only when he asks). Decide the default ladder without Fable.

### AD-15 — Traces and events

- **Event keys (B-18).** Add node id, iteration and partition to node events in SD 3.2, and name the events that set span status `gate` and `cancelled`.

### AD-16 — Runaway guard, ladder and watchdog

- **Guard defaults (B-38, L-49).** Pick one table. SD 17 (2M tokens, 16 agents, 1,000 tool calls, 4 h) or Appendix H and settings.py (400k, 12, 2 h). Add a `runaway.tool_calls` default either way.
- **What counts as a token (B-49).** Decide whether cache reads count toward the token guard. Counting them trips 400k after about 20-25 turns.
- **Wall time across waits (L-48).** Decide whether time asleep in a `wait` node or a retry backoff counts toward `runaway.wall_seconds`.
- **Degrade width (L-46).** Decide whether `on_runaway: degrade` lets the whole held batch through or only up to the guard.
- **Join words (B-23).** Add a join reason to SD 3.2's waiting reasons, a direction setting for `no_progress_rounds`, and an inbox line for a late partition failure after a join fired.

### AD-10 / AD-22 — Triggers and versions

- **Enable and disable symmetry (B-68).** Decide whether disabling a trigger also disables its pinned version when no other enabled trigger uses it.

### AD-14 — Library contract

- **Artifact types (B-83).** Decide whether run files carry typed artifacts (card, source) or stay `run-file` with a path.

### AD-17 — Inbox

- **Decision cards (B-88).** Decide whether non-irreversible human points (sign a promotion, accept a lesson, approve a tightening) become inbox decision cards, or stay result cards until `human_gate` (Appendix G L15) is widened.

### AD-20 / AD-25 — Workers

- **WorkerPort shape (L-42).** Reconcile `LocalWorker.run(job, executor, emit)` with the contract's `WorkerPort.run(NodeJob)` and streamed events before any remote worker (Appendix G L8).

### AD-7 / AD-26 — Replay

- **Replay on an edited folder (B-82).** Decide the engine call for "replay this past run on an edited folder" (fork at the first changed step, replay the suffix on a fix set and a guard set). Without it the Lab's RV marks every edit untested.

## Harness round 2 (HG3) list

Each line is one request to the harness, with what it unblocks.

1. **Per-chat tools allow-list on NewChat (H2), B-51 and B-70, high.** Unblocks `llm` nodes with no tools and `agent` nodes whose `tools: []` is real. Today a resumed chat still called Glob, Bash and TaskList.
2. **Persist `compact_at` and hooks with the chat record, B-6 and L-7, medium.** Unblocks resuming an agent attempt after a host restart with 40% compaction, the PreCompact memory note and live tool spans still on.
3. **Close and delete a chat through a public call, B-50 (and B-8, L-18), medium.** Unblocks clean ends for engine attempts: no stale chat in the list, no live CLI waiting for the reaper, and no leftover "Plan usage meter" session rows.
4. **Per-chat appended system prompt, B-53, medium.** Unblocks caching the node brief across chunks, so each chunk pays only for its own items (EP11 saw about 5,470 tokens written per chunk).
5. **Ask levels for engine tools, B-5, medium.** Unblocks "saving a draft and running a test never ask" in default mode, as H17 and AD-22 meant. Today the effect table sets only the mandatory ask.
6. **Tell a REST call from an agent tool call in qmx-control, B-65, medium.** Unblocks correct principals: his UI saves stop being recorded as `agent:qmx-control`.
7. **Public ControlService construction, B-11, medium.** Unblocks the engine host (and scripts) reading settings without importing `qma.harness.routes`. Appendix G L1 removes the need once the engine sits in `qma.serve`.
8. **Session home per Background chat, B-56, medium.** Unblocks AD-35 for engine chats: the home is written on `node_started` and any surface can resume the session (Appendix G L17).
9. **Ship `py.typed`, B-10, low.** Unblocks strict typing for every consumer without the pyright `extraPaths` workaround.

Harness bugs to fix in the same round: `meter()` cooldown so it does not spend a haiku turn on every call after a None (L-16), `meter()` cleanup order (L-17), pruning `Harness._options` (L-8), `_observer` catching CancelledError (L-9), and `GET /api/runs` listing chat journals as agent runs (B-67). A live proof that compaction fires at 40% (L-10) belongs in the round's lanes.

## Hardening program candidates

Input for the next plan, in a sensible order. Each step lists IDs; duplicates are given once.

**Step 0. Before landing the stack (hours, not a program).**
- B-75: one-line qma-core test update, so `just ci` is green.
- B-95: default `roles.test_only` and `test_order` to haiku via the plan; Kimi only for provider-proof lanes.
- B-44: drop or gate `--mode live` in the CLI.
- L-23: take `claude/fable` out of the default strong ladder (after the AD-13 decision).

**Step 1. Security (after the AD-24, AD-28 and AD-11 amendments).**
1. B-30: host scripts cannot reach the plan login or the keyring.
2. B-89 / L-25: money lint over script text and prompts, call-shaped verbs; host scripts cannot import `keyring` or `qmn`.
3. B-17: refuse broker credential refs in the lint.
4. B-39 / L-50 / L-52 / L-58: one redaction pass for ledger, inbox, explain and REST, with the glued-key shapes.
5. B-45 / L-53, L-51: only a user principal publishes or enables; published means on `main`.
6. B-31: Job object and parent-death signal; sweep orphans before resume.
7. B-13 / L-24: shared money matcher and spelling variants.
8. L-39: containment check in `effects.restore()`.
9. L-71: write down the rule that lane scripts never read his real control token (already fixed for x13 in the EP13 round).

**Step 2. Run-state and resume bugs (his core ask is that runs resume alone).**
1. B-69: resend the full prompt when a saved agent chat holds no task.
2. B-63: time `wait` nodes write a wake row and resume on their own.
3. B-73: a resumed run on a `wait` reads `waiting`, not `running`.
4. B-72: `run-now` reports why no run started.
5. B-25 / L-36: the ledger refuses a second `run_created`; fold keeps the first.
6. L-32: fold compares the attempt on node endings.
7. L-37: one UTC formatter for wait times.
8. L-38: idempotency keys cannot collide (forbid `:` in node ids or encode the key).
9. B-57: `after_unknown` honours a declared irreversible effect (must land before Appendix G L6).
10. B-29: per-attempt file attribution in a shared write zone.
11. L-40: a junction in the write zone fails the attempt, not the engine.
12. B-55 / L-44, L-60: the watchdog keys on executor progress; warm-first chunks emit their own event.
13. L-45: the runaway guard checks in-flight attempts every tick.
14. L-63, B-54: a stale reset does not hold a run; a test run returns `waiting` at a limit.
15. B-66, L-69: cancel reaches subworkflow children; a cancelled fire frees its slot.
16. L-68: `workflow_runs_list` shows in-flight runs.
17. B-42: settings edits reach runs without a reopen (configurable means editable live).
18. B-60, B-61: triggers apply role and effort pins; a resumed test run writes a fresh report.
19. B-26, B-37: script idle timeout and stdout spill; operator stop goes through `run_cancelled`.
20. L-80, B-92, B-77: export tolerates moved files; the draft view shows `needs_unmet`; the fake switch covers `agent` nodes.
21. B-43: a draft edited after its variant resolved keeps `variant_of` (draft ownership itself waits for Appendix G L11).

**Step 3. Harness round HG3.** The nine requests and five harness bugs above. Steps 1-2 do not wait for it, except that B-70 is only fully closed by request 1.

**Step 4. Template grading holes.** L-81, L-86, B-84 (a pack-wide rule: grade inputs are evidence plus final output only, with a test over every definition), then L-82, L-83, L-87, L-88.

**Step 5. Hygiene sweep.** B-90 (`expr.check` at validate), B-22 (validate loop, join and wait parameters), L-22 (lint aliases and `importlib`), B-48 / L-19 and B-86 (role defaults), B-79 (`needs` agreement test), B-71 (spans in explain text), B-96 (record test costs), B-21, B-62, then the low bug batch (L-28, L-29, L-31, L-33, L-34, L-47, L-54, L-55, L-56, L-57, L-61, L-64, L-65, L-70, L-75, L-43) and the script and evidence lows (L-3 to L-15, L-21, L-27, L-30, L-41, L-59, L-62, L-66, L-67, L-72, L-73, L-74, L-76 to L-79, L-85, L-89, L-90, B-7, B-9, B-19, B-59, B-74, B-85, B-91).

The SPEC-GAP decisions feed steps 1 and 2. The LATER-PACKET rows are not hardening work. They go to their Appendix G packets or to the six new packets named in section 5.

## Duplicates

Items that appear in both BACKLOG and lows:

| BACKLOG | Low | Issue |
|---|---|---|
| B-6 | L-7 | compact_at and hooks held in memory only |
| B-7 | L-6 | stale refusal text pointing at POST /api/usage/meter |
| B-8 | L-18 | "Plan usage meter" session row left in qmx-control |
| B-19 | L-35 | memo validity: events vs the `ledger.memo` valid flag |
| B-25 | L-36 | a second `run_created` is accepted and moves chunk boundaries |
| B-38 | L-49 | runaway guard defaults: SD 17 vs settings.py |
| B-39 | L-50 | provider and node failure messages reach the inbox unredacted |
| B-45 | L-53 | agent or workflow callers can publish and enable |
| B-48 | L-19 | `gpt` role rows name no model |
| B-55 | L-44 | watchdog counts the worker's own heartbeat |
| B-80 | L-84 | script env has no run id or home; `week.py` derives them from cwd |
| B-89 | L-25 | money lint does not read script text, prompts or other fields |

Duplicates inside BACKLOG: B-89 = B-93 (money lint), B-75 = B-94 (qma-core CI test), B-46 = B-81 (grader llm mode), B-51 = B-70 (per-chat tools allow-list, H2).

Closely related but not the same: B-13 and L-24 (money matcher), B-39 and L-58 (redaction shapes), B-69 and L-74 (empty-chat resume and the lane that missed it), B-78 and L-86 (test vs live mode in scripts), B-24 and B-87 (multi-input readiness).
