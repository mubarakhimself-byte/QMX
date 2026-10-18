# 48. Review of the unlock pass (43) and the studies-folded pass (47)

Written 2026-10-18 by an independent reviewer. **Opus 5.5 reviewing Opus 5.5 work**, so expect shared blind spots. The reviewer used no sub-agents, made no commits and edited no design file. It applied the blast-radius method (find the one fact each change is safe because of, then prove it where cheap) and the codebase-design vocabulary.

**Read:** `43`, `47`, `26` (rulings 1-119), the scenario catalogue of `46` §5, the engine spine, SOLUTION-DESIGN §27-§28 (plus the §6, §26 rows they override), HARNESS-REQUESTS, all three OPEN-DECISIONS files, the Library and Lab spine diffs, UI-HANDOFF §14-§15 and `DELETION-PLAN.md`. Diff `1514a828..0ce09c14`.

**Code truth:** `origin/engine/base` 132169c7, `origin/rebuild/base` 4345eafa and `origin/integration` a0e87697, read with `git show`, `git grep` and `git ls-tree`. `rebuild/base` differs from `engine/base` only in HP2 probe scripts and two test conftests, with no harness source change, so the design's reading of engine/base holds for harness code. `integration` carries only the old `qma-core`, `qma-daemon`, `qma-wire` and `qma-ui-contract` packages. The installed SDK is `claude-agent-sdk` 0.2.166 with bundled CLI 2.1.299 (`D:/QMX-worktrees/eng-ep12/qmx-agents/.venv`).

**Counts:** 0 critical, 8 high, 15 medium, 10 low.

---

## How sure each load-bearing fact is

Each fact below is placed on the five-step evidence ladder from the blast-radius method.

| Fact | Evidence level | Proof |
| --- | --- | --- |
| The SDK cannot change a chat's skills, plugins or system prompt after it connects. The `skills` filter becomes `--allowedTools Skill(name)` entries on the command line. | 4, ran it | The scratchpad script `sdk_facts.py` ran against the installed SDK. It lists `ClaudeSDKClient` coroutines as `connect, disconnect, get_context_usage, get_mcp_status, get_server_info, interrupt, query, reconnect_mcp_server, rewind_files, set_model, set_permission_mode, stop_task, toggle_mcp_server`, and finds no setter for skills, plugins or the prompt. A built command gives `--allowedTools => Skill(qmx:workflow-builder),Skill(pack-macro:bias-read)`. |
| The CLI keeps an MCP switch-off in its own state for the workspace. A switch-off sent while a server is still connecting does not hold. | 2, line cited | `qma/harness/chat.py:175-180` and `:450-462` on engine/base say "measured, S35". This is why the harness keeps a `_keep_off` poll loop and a gate denial. |
| The CLI already advertises `tools/list_changed` for in-process servers. | 2 | `qma-harness/tests/fixtures/helper_turn.jsonl:1`, a real init from CLI 2.1.299, lists the capability `sdk_mcp_tools_list_changed`. |
| The `claude_code` preset puts the working directory into the system prompt. A recorded prompt is reused after resume unless `snapshot` is set to false. | 2, library source | `types.py:45-69` (`exclude_dynamic_sections`, `snapshot`) and `_internal/client.py:109-151`, which sends both in the initialize request. |
| `--append-system-prompt-file` already works with the inline `append`. | 2 | `scripts/probes/qma/FINDINGS.md:14` (HP0 S20 OQ4, PASS) on engine/base. |
| No live Python import outside the deletion set and DELETION-PLAN's lists survives AD-59. | 2 | Results of a `git grep` for imports are in finding L1. Path-string users are listed there too. |

---

## Critical

None. No finding opens a path to money, loses committed data or blocks every packet.

## High

### H1. Per-attempt working folders break the prompt cache and contradict AD-18 and AD-34

- **Evidence.** AD-60 (engine spine `:443`) and AD-24 (`:228`) make an agent attempt's working folder its overlay, `<zones_root>/<run_id>/attempts/<node>.<iteration>.<partition>.<attempt>/` (AD-51 `:389`). The SDK states that the `claude_code` preset carries "working directory, auto-memory, git status" sections and offers `exclude_dynamic_sections` "when you want the prompt-caching prefix to hit" (`types.py:45-56`). Nothing in `tracker/qma-v2` mentions it. Today every chunk shares one workspace (`nodes/agent.py:280-289` uses `self.agent.workspace`), which is why the warm-first gate (`:117-130`) pays off. AD-18 (`:186`) still says the agent chat workspace is `<qmx_home>/workspaces/wf-<workflow_id>/`.
- **Failure scenario.** A 300-video playlist runs as 30 chunks. Each chunk's system prompt names a different overlay path, so chunk 2 onward reads nothing from the cache. The warm-first gate still holds chunks back while the first one warms the cache, so the design pays its latency and gets no saving. H21's check ("a two-chunk run reads the brief from cache on chunk 2") fails, or passes only in a test that reuses one folder. The CLI's auto memory also splits into one folder per attempt.
- **Fix.** Set `exclude_dynamic_sections: true` for every Background and Child chat that the Surface builds, and add that case to P-SET: two chats in different folders, with a cache read on the second. Correct AD-18's workspace sentence so it names the attempt overlay as the working folder, and state where the auto memory lives.

### H2. A recorded system prompt makes the slot design and the surface digest stale after resume

- **Evidence.** In SDK 0.2.166, `snapshot` is treated as true when omitted: "every later request, including after resume, sends the recorded prompt, so changing `append` has no effect until the session is compacted or you start a new session" (`types.py:56-69`). The design relies on relaunch-by-resume in several places:
  - AD-55 (`:413`): a published pack joins at the next relaunch.
  - AD-35 (`:293`): an installed pack joins by resume, and so does the P-TG fail path.
  - AD-62 (`:455`): pack layers, the skills index, persona and methodology all ride the system text.
  - The surface digest records the newly computed text.
- **Failure scenario.** He adds the macro pack to a Lab session. The chat resumes with the new plugin list. The pack-layer slot and the persona edit never reach the model, but the digest on the chat record and every span says they did. "What did the model see" (UI-HANDOFF §15.2) then gives a wrong answer, and AD-66's battery tests a prompt the live chat is not running.
- **Fix.** The Surface sets `snapshot: false` whenever a chat's slots may change across relaunches, and accepts one cache miss on each change. Hash the digest over the prompt actually sent, recorded at launch, rather than over the computed slots. Add a resume case to P-SYS: change `append`, resume, and confirm the model sees the new text.

### H3. "Writes only under the overlay" cannot be enforced for a declared `Bash`

- **Evidence.**
  - AD-60 (`:443`) says the `engine` policy "allows the declared tools with writes only under the overlay".
  - AD-24 (`:228`) says the agent "writes there, never elsewhere".
  - E55 (SOLUTION-DESIGN `:1607`) says "a write outside the overlay is denied".
  - P-PERM (HARNESS-REQUESTS `:126`) tests only an *undeclared* `Bash`.

  The policy sees a Bash command string and cannot know which paths the command writes. The SDK's `sandbox` setting is not used (AD-24 retired isolation). The guard's floor protects QMX stores, logins and keys, not his other folders.
- **Failure scenario.** A build template declares `Bash` to run tests. The agent runs `cd ..\..` and then `pip install -e .`, or a script writes into his Desktop QMX checkout. The policy allows the call and nothing is recorded as outside the overlay. E55 passes because it probes only the `Write` tool, so the test result is a false green.
- **Fix.** State the real boundary in AD-60 and AD-24: `Write`, `Edit` and `NotebookEdit` are confined by path, and `Bash` runs with the overlay as its folder, the guard's floor and nothing more, the same as Claude Code with Bash allowed. Either accept that boundary in plain words for him, or make the `engine` policy refuse Bash commands that name absolute paths or `..` outside the overlay, `zones_root` and the read-only folders. Add a declared-Bash write outside the overlay to P-PERM and E55.

### H4. Runs homed on the server are invisible to the PC's UI and copilot while they run

- **Evidence.**
  - Each engine instance keeps its own ledger, inbox and incidents (AD-3 `:96`, AD-17 `:180`, AD-10 `:138`), and Contabo is the default home for schedules.
  - The UI and copilot call their local `qmx_engine.service` (AD-21 `:204`).
  - Only the heartbeat travels to the Hub (AD-65 `:473`). Its schema (SOLUTION-DESIGN §28.5) carries host facts, claims and the pause flag, but no run states, inbox items or incidents.
  - Run summaries reach the Library only at the end of a run.
  - Ruling 117 requires "logs and monitoring for remote runs". Ruling 77 says provider failures are the one thing that must reach him.
- **Failure scenario.** At 03:00 the Kimi key on Contabo returns 401. Contabo's inbox raises a `normal` item with `retry` and `stronger_model` actions. The PC UI's inbox is empty. K-15's "brief waited 14 minutes for a chat slot on Contabo" cannot be answered from the PC, because the spans are in Contabo's ledger. K-22's app incident stays on Contabo.
- **Fix.** Keep it to one mechanism. The PC's `qmx_host` forwards engine-service reads and inbox answers for `home_engine = contabo` to the node's engine REST routes over the tailnet, using the host pass of AD-28. `ops` and the run lists merge both homes, keyed by `home_engine`. No replication is needed. Add an E-check: a 401 on a Contabo-homed run shows in the PC inbox, and `retry` from the PC resumes it.

### H5. While the PC is the Library primary, every server-homed chain stalls when the PC sleeps

- **Evidence.**
  - `main` and `refs/drafts` are owned by the primary (Library AD-7 `:98`, AD-19 `:170`).
  - The primary stays `pc` until P-LAT passes, and stays `pc` permanently if P-LAT fails.
  - AD-64 (`:467`) fires `event` triggers on landings in the ref log.
  - AD-18's landing is a fast-forward of `main` (Library `:164`).
  - Library AD-14 (`:140`) promises that the hub keeps serving runs while the PC sleeps. It promises nothing about landings.
- **Failure scenario (K-09, K-17).** The macro app on Contabo lands `bias` at 06:00. The signal app on Contabo waits for that landing, but `main` can move only on the sleeping PC. The webhook home on Contabo (`AD-10`, "so the PC may sleep") starts a run whose downstream chain then stops at the first hand-off. Consolidation into `refs/memory/home/*` waits as well.
- **Fix.** Either make event triggers match a passed live run's output on `refs/runs/<run_id>` of the store that minted it (the Hub owns those refs, AD-11 `:122`), with the landing on `main` following later, or make the flip to `primary = server` unconditional at Contabo setup. In the second case a P-LAT failure becomes a latency bug to fix, not a reason to stay on the PC. Trace K-09 with the PC asleep in E63.

### H6. Scope switching rests on a toggle the merged code measured as unreliable, while a simpler mechanism is advertised

- **Evidence.**
  - AD-61 (`:449`), AD-35 (`:293`) and H47 make every toolset its own in-process server: 13 core toolsets plus one per pack and per app. All are registered on every chat, those outside scope "start switched off", and scope changes go through `toggle_mcp_server`.
  - The merged harness measured that the CLI "keeps a switch-off in its own state for the workspace" and that a switch-off sent during connect does not stick (`chat.py:175-180`, `:450-462`, commit d6be117a). It needs a perpetual `_keep_off` poll loop plus a gate denial to cope.
  - The CLI advertises `sdk_mcp_tools_list_changed` (init fixture). 47 C8 retired P-PK, the list-changed probe, in favour of P-TG.
  - P-TG (HARNESS-REQUESTS `:128`) tests neither persistence nor the connect race.
- **Failure scenario.** Two hub chats share a workspace. One switches `app-macro` off, and the CLI writes that into the workspace state. The other chat relaunches by resume and finds `app-macro` disabled. Every launch has to toggle about 40 servers and poll until they settle. The design has no such loop, so a stale set reaches the model, and the guard refuses calls the model was told it could make. Each toggle also changes the tool list, so the cache prefix is lost on lanes without tool search.
- **Fix.** Bring P-PK back as the first option: one in-process server per chat whose tool list follows the Surface and emits `tools/list_changed`. It needs no per-workspace state, no keep-off loop and no persisted switch-off. Keep per-toolset servers with toggling only if P-PK fails. Extend P-TG to cover a switch-off during connect, persistence across two chats in one workspace and across resume, and launch time with 40 servers.

### H7. RUN1 deletes the only working remote compute before its replacement exists

- **Evidence.** AD-57 (`:425`) deletes `qmx_remote/worker.py`, `runs.py`, `store.py` and the control `runs_*` and `jobs_*` operations. engine/base has no remote `WorkerPort` adapter: `qmx_engine/workers/` holds only `local.py` and `effects.py`. The replacement needs the sidecar, the Hub, passes and the vault (Library AD-11 to AD-13, AD-28). In 43 §10 and 47 §7, RUN1 has no dependency on those packets, and DEL1-DEL4 follow RUN1. `qmx_remote/code.py` appears on neither the keep list nor the delete list. Ruling 117 says remote workflows are "very important", and ruling 118 says to keep what works.
- **Failure scenario.** RUN1 lands after the one-host packet. Until the remote worker, Hub and sidecar packets land, QMX cannot place any job on E2B, Modal or Contabo.
- **Fix.** Order RUN1's delete step after the remote `WorkerPort` adapter passes E57 on a real placement. Until then, keep `runs_start_remote` as a thin shim that starts a one-node engine run, or leave it untouched. Classify `code.py`.

### H8. The spines disagree on which skills, agents and commands a chat sees, and the SDK cannot change them mid-chat

- **Evidence.**
  - AD-35 (`:293`) says every chat launches "with the plugins of every enabled pack (their skills, agents and commands listed natively)".
  - AD-55 and AD-62 (`:413`, `:455`) filter skills by the session's pack set through the SDK `skills` option.
  - Lab AD-14 says the Lab pack loads in the hub "mid-session included".
  - UI-HANDOFF §14.5 (`:234`) and §15.1 (`:246`) say adding an app turns it on at once.
  - Proven at level 4: the filter is fixed at connect.
  - Plugin agents and commands have no per-chat filter in the SDK, so every enabled pack's agents appear in every chat's agent list. AD-64 (`:467`) says an app's own agents serve only that app's sessions.
- **Failure scenario.** He adds the Lab pack to a hub chat. The Lab tools appear at once, but the Lab skills, including "the Lab prompt layer is a skill" (Lab AD-14), stay hidden until a relaunch, which H2 then makes stale. On Kimi, with 20 packs enabled, every chat carries every pack's agent descriptions, the same kind of bloat AD-61 removes for tools.
- **Fix.** Write one rule in AD-35, AD-55 and Lab AD-14: tools join at once, while skills, agents and commands join at the next relaunch by resume (with H2's fix applied). The Surface also generates `Agent(<plugin>:<agent>)` deny rules for packs outside the set, which must go into P-PL. Fix the two UI-HANDOFF rows so they say "tools now, skills on your next message".

---

## Medium

### M1. A run whose home machine dies cannot resume on another machine

- **Evidence.** Each run's ledger exists only on its home instance (AD-3 `:96`). The Deferred row (`:747`) says the ledger is "rebuildable except for in-flight runs". `runs.fetch_home` (AD-65) makes a test-mode fork only. Ruling 117 lists "resume across machines".
- **Failure scenario.** The PC disk dies halfway through a PC-homed fan-out (K-33). All memos are lost and every chunk is paid for again. A Contabo outage stalls its schedules with no move to the PC.
- **Fix.** State that resume across machines works at the attempt level only. Add `runs.adopt(run_id)`, which replays a run's journaled events, already append-only, from a copy pushed to the Hub at each node end. Alternatively, record this explicitly as a deferred row with an owner and say it to him in plain words.

### M2. E55's crash case contradicts overlay deletion

- **Evidence.** E55 (`:1607`) kills the host mid-attempt and expects "the resumed chat keeps `compact_at` … its policy still applies". AD-51 deletes an overlay when its attempt ends `unknown`. S7 (`:1410`) folds every open attempt to `unknown` at restart, and AD-8 retries in a new attempt.
- **Failure scenario.** The resumed chat's working folder no longer exists, so it either fails to start or is never resumed.
- **Fix.** Pick one behaviour. Either a crash retries in a new attempt with a fresh chat, so E55 drops the resume claim and H19's persistence serves copilot and helper chats, or an `unknown` agent attempt keeps its overlay until its retry decision is made.

### M3. A live run cannot be steered with an edit (K-20)

- **Evidence.** `runs.fork` takes only live-start overrides, and any edit becomes a test-mode replay fork (AD-7 `:120`, 47 C11). Test runs never land (Library AD-18), and `irreversible_external` steps are stubbed in test mode (AD-24). A live fork may only use "the same pinned object".
- **Failure scenario.** At 02:00 he says "skip audio-only items". The steered run's results never land, and its delivery never happens.
- **Fix.** Allow a live `runs.fork(run_id, from_node, object=<newly published version>)` that reuses memos under the replay rule (definition hash and input hash unchanged). Publishing stays his click.

### M4. Claims are renewed through one channel and held in another

- **Evidence.** Library AD-24 (`:200`) holds claims as a compare-and-swap on the primary. AD-65 (`:473`) renews them in the heartbeat pushed to the Hub. With `primary = pc` these are different machines. When the primary cannot be reached, each engine claims locally.
- **Failure scenario.** K-13 at 07:00 with the PC asleep: Contabo claims locally and builds the paper. The PC wakes, runs its catch-up, claims on its own store and builds the same paper again. The "rare duplicate" becomes the normal case for K-13.
- **Fix.** Hold claims on the Hub store whatever the primary is, since they are transient and AD-24 already exempts them from backup, and renew them in the heartbeat call the Hub already receives.

### M5. The pause flag's path from the Hub to each host is unspecified

- **Evidence.** AD-10 (`:138`) says the flag is "synced to every host through the Hub heartbeat". AD-65 describes the heartbeat as a push from each host to the Hub, which only reports the flag each host sees.
- **Failure scenario.** He presses pause on the PC. Contabo never learns of it, or keeps firing during a Tailscale outage.
- **Fix.** The Hub's reply to each heartbeat carries the authoritative flag. A host that cannot reach the Hub for a set period honours the last value it knew and shows "pause state unknown" on the doctor page.

### M6. Memory rows are invisible to the marks walk

- **Evidence.** `marks()` walks the `consumed`, `derived-from`, `uses` and `compiles-to` edges (Library AD-22 `:188`). A `memory-row` cites its sources through the `refs[]` identity field and the `source_run_ids[]` annotation (Library AD-3 `:74`), and neither is an edge.
- **Failure scenario.** K-03 and K-07: a lesson learned from a run on quarantined dataset r12 is not down-weighted.
- **Fix.** `consolidate` and the retain worker write `derived-from` relations at birth to the results or sessions each row came from. Add memory rows to the P-TAINT fixture.

### M7. The eval battery runs on haiku, which cannot measure a change of model

- **Evidence.** AD-66 (`:479`) "runs before a change of the copilot's default model" and "runs on haiku through the plan login".
- **Failure scenario.** He switches the copilot to Kimi. The battery passes on haiku and says nothing about Kimi.
- **Fix.** The battery runs on the model under change, and on the current model as the baseline. Haiku is used only for the template's own tests (ruling 105 covers software tests, not model evaluation).

### M8. Test mode and live mode run different executors for every `llm` node

- **Evidence.** Live defaults put key providers first (AD-13 `:156`), so `llm` nodes call `router.complete`. Tests resolve to `claude/haiku` on the plan, which uses the one-turn chat.
- **Failure scenario.** The default test suite never runs `complete`, the path every live `llm` node takes.
- **Fix.** Add a recorded-transport adapter for `complete` in unit tests. Make one provider-proof lane per release (the OpenRouter or DeepSeek row, which ruling 105 allows) a gate for any packet that touches `complete`.

### M9. The CLI's own scheduling and remote tools are not addressed by the Surface

- **Evidence.** A real init (fixture `helper_turn.jsonl:1`) lists the tools `CronCreate`, `ScheduleWakeup`, `RemoteTrigger`, `Workflow` and `EnterWorktree`, and the skills `schedule` and `loop`. Built-in plugins load even with `setting_sources=[]` (FINDINGS `:14`). No AD names them. Interactive chats run with `tools=None`.
- **Failure scenario.** The copilot schedules a cloud routine or an in-CLI cron job. That bypasses AD-10's single scheduler and AD-57's "every unit of work … is an engine run", and runs off his machine where QMX cannot see it.
- **Fix.** The Surface's built-in list for every chat kind leaves these out, and the skills filter leaves out the CLI's own scheduling skills. Add an E60 case for each.

### M10. Removing the money gate rests on the architect's reading of ruling 116 and drops a cheap name check

- **Evidence.** Ruling 116 says "the harness's existing behaviour (its money gate included) stays as built". Ruling 118 lists 105-117 as still binding. The "keep rested on the lock" reading is the architect's annotation in `26`, not his words. The gate's name check is what kept "an external MCP server that offers an order tool" from launching (harness `SIGNOFF.md:134`, S35). The guard keeps no such check for pack operations or external servers. AD-54's unit test covers only core rows.
- **Failure scenario.** A copilot-built mini app wraps a broker REST API under a `qmx/tool/*` key and exposes `place_order`. Nothing refuses it.
- **Fix.** Confirm the reading with him in one line, since money is a topic he is to be asked about. Whatever he answers, run the vendored word list the lint already keeps against `qmx app check` operation names and external MCP tool lists. That is one function and ordinary hygiene, not money machinery.

### M11. Six of the eleven new probes have no pass or fail line

- **Evidence.** P-MEM, P-LAT, P-TAINT, P-SRCH, P-OPS and P-EV (SOLUTION-DESIGN `:1723-1729`) measure and record but never define a pass. P-MEM has no branch for a failure, although ruling 119 fixes the choice of Hindsight. Contabo's `overhead_mb` (`:975`, 6,144) leaves out Hindsight and its embedding model, so AD-30's "4 sessions" figure is too high once Hindsight moves there.
- **Fix.** Give each probe a number:
  - P-LAT: Library screen p95 latency in milliseconds over the tailnet.
  - P-TAINT: the walk finishes within a set number of milliseconds.
  - P-EV: a fire happens within N ticks.
  - P-OPS: heartbeat bytes and CPU per host.
  - P-MEM: maximum RAM, plus the fallback if it is exceeded (Hindsight stays on the PC, or FTS5 answers on the server).

  Add Hindsight to the Contabo overhead figure.

### M12. Some probes come after the work they gate

- **Evidence.**
  - CAT is the first packet to toggle servers, but its gate lists only P-NM (47 §7 `:222`). P-TG is listed only under PACK.
  - TRG2's `event` trigger has no gate (`:219`), but P-EV sets its tick.
  - OPS does not list P-OPS (`:227`).
  - P-PERM leaves out a declared Bash (see H3).
  - P-PL leaves out the agent scope and adding a pack mid-session (see H8).
- **Fix.** Put P-TG (or a revived P-PK, see H6) before CAT, P-EV before TRG2's event part and P-OPS before OPS, and extend P-PERM and P-PL.

### M13. `@folder` and `@file` copy his files into the Library

- **Evidence.** AD-63 (`:461`) says outside sources "are stored first by hash". Ruling 42 says his PC has little space and the PC is the primary until the server flip.
- **Failure scenario.** Attaching a repository folder copies gigabytes onto the PC store.
- **Fix.** Pin a folder by a manifest of paths and hashes, and store bytes only for files the model actually reads. Claude Code and Hermes both read a folder at turn time.

### M14. The recursive-delete floor blocks ordinary interactive work

- **Evidence.** The guard denies "recursive deletes outside the run's zones" in every mode, and his always-allow list cannot lift it (AD-54 `:407`). Copilot chats have no run zone.
- **Failure scenario.** In his own project the copilot can never run `rm -rf dist` or remove `node_modules`. That falls short of the "Claude Code-like" standard of rulings 115 and 117.
- **Fix.** Scope the floor row to outside the chat's working folder or worktree, and in Interactive chats ask him instead of refusing.

### M15. Agent-made tools cannot load locally

- **Evidence.** Library AD-3 (`:74`) says `agent-tool` is "loadable only into sandboxed tiers while `unreviewed`". Those tiers were retired (AD-24 `:222`). AD-61 still offers a `run:<run_id>` toolset.
- **Failure scenario.** Under the default local isolation, ruling 52's agent-made tools have nowhere to load.
- **Fix.** Restate the rule as follows. An unreviewed agent tool loads only into the run that made it (its `run:<run_id>` toolset) and only after his review elsewhere. Remove the word "sandboxed".

---

## Low

- **L1. The deletion caller list is incomplete in 43 and AD-59.**
  - 43 §2 row 23 (`:55`) says the money word-list import "was the only live tie". It was not:
    - `qmx_apps/supervisor.py:29` and `qma/harness/tools.py:29` also import `qma.core` (AD-59 names both).
    - Five `qmx-agents/plugins/*/daemon/plugin.py` files import it.
    - `qmx-agents/tests/test_workspace_scaffold.py` imports it.
    - `qmb/tests/test_operator_study_cli.py` imports both `qma.daemon` and `qma.core`.
    - `scripts/live/{smoke_agent,smoke_firecrawl,copilot_build_app}.py` import `qmx_agents`.
    - `qmx-agents/examples/{scoped_tool_request,scaffold_overview}.py` import the old packages.
    - `scripts/probes/qma/name_barrier_diff.py` imports `qma.core`.

    DELETION-PLAN D1-D3 already list most of these, and the caller-scan gate would catch the rest. Two QML tests pass a deleted path to `rglob`, so after deletion they pass without checking anything: `qml/tests/test_generation_gaps_unfilled.py:62` and `test_generation_ownership.py:274`. Delete or repoint them.
  - The line counts hold within 6%. Python-only source counts are 74,104, 24,341, 15,435 and 3,538 lines, against the claimed 78,572, 24,453, 16,049 and 3,538.
- **L2. DELETION-PLAN still points QMB at a forwarder AD-52 deletes.** D2 retargets the QMB spawn to `qma.serve` (DELETION-PLAN `:136`), which AD-52 deletes after one release. Point it at `qmx_host`.
- **L3. Old SOLUTION-DESIGN rows contradict §27.** SOLUTION-DESIGN `:311` says "its own `qma.serve`", `:575` describes the polling `wait_turn`, and `:1410` (S7) says the desktop host starts `qma.serve`. §27's precedence rule covers these, but builders read §6 and §26 first. Mark the rows superseded in place.
- **L4. The Lab pack's server count disagrees.** Lab AD-14 names one server, `pack-qmx-lab`. AD-61 and §28.1 name two toolsets, `lab` and `pods`, each its own server. Pick one.
- **L5. The example apps have no migration.** `examples/apps/*/app.toml` carry `[budget] runs, cpu_seconds`, `[schedule]` and `capabilities.secrets QMX_MODEL_KEY = "qmx/cliproxy"`, a raw model key, which AD-19 forbids. The `docker-nodes.yml` CI uses these apps, and AD-57 states no manifest migration.
- **L6. AD-63 names no owner for flipping `pending` to `ready`.** Resolving the status at read time from the Library would need no owner.
- **L7. The `library-skills` view fails the hash check.** It aggregates many objects, so AD-55's "bytes hash to its object id" check has nothing to check against. Hash a manifest of member ids instead.
- **L8. The skills filter uses the command-line budget H21 frees.** It rides `--allowedTools` (proven above). A launch with 150 skills adds several kilobytes.
- **L9. Draining Contabo before an update has no owner.** AD-48's desktop host drains only the PC.
- **L10. P-SYS repeats a finished probe.** Its core question was answered by HP0 S20 OQ4 (FINDINGS `:14`). Keep only the 60,000-character size, cache and resume parts (see H2).

---

## Scenario traces (14 of 46's 34, plus 46 §5.0 failure rows)

| Scenario | Path through the design | Holds? |
| --- | --- | --- |
| Provider limit mid fan-out (§5.0, S10) | AD-9 lease refused → `waiting(resume_at)` → drain → wake row. A 429 inside a turn is made non-retryable by AD-50, and `run_turn` reports `failed` with a reason, so the attempt waits. A `complete` 429 is handled by the classifier and the pool. | Yes on the home machine. For a Contabo-homed run, the inbox item raised after `alert_after` never reaches the PC (H4). |
| Crash mid-chunk, same machine (S7) | Orphan sweep → `unknown` → model call retried once → memos stand. | Yes, but E55's resume claim contradicts this (M2). Chunk cache is lost (H1). |
| Crash, resume on another machine (K-33) | The ledger is only on the home machine. | No (M1). |
| K-02 a session moves and pulls context | `NewChat.home`, `packs` and `attached` live on the chat record and are reopened by session id. | Partly. The video reads `pending`, but no one flips it to `ready` (L6). A folder is copied (M13). Skills added mid-session lag (H8). |
| K-03 memory follows the subject | Retain worker → `memory-row` → Hindsight by `item:` tag, with FTS5 when Hindsight is down. | Partly. A tainted lesson is not down-weighted (M6). |
| K-07 bad data found later | Mark on root → walk at read time → preflight refuses pinned inputs → node fails `bad_input`. | Yes for results and pinned triggers. A trigger that reads "latest" fails at the node, not at preflight, which is acceptable. Memory rows are missed (M6). |
| K-09 apps feed apps across machines | Landing → ref-log event trigger → `app_op` on the consumer. | No while the PC is primary and asleep (H5). |
| K-13 two machines build the same thing | `claim` CAS on the primary. | Weak: duplicates whenever the PC sleeps (M4). |
| K-15 one ops picture | `ops` reads heartbeats and local spans. | No for runs homed on Contabo (H4). |
| K-18 a loop outlives the laptop | Builder converts the loop into a workflow homed on Contabo; references move as pinned Library objects. | Yes, if he clicks before closing the laptop. Its outputs then hit H5. |
| K-20 steer a running workflow | Live fork, or a test replay fork. | No for edits (M3). |
| K-21 a standing research employee | `agent` item → plugin view, triggers on Contabo, `ask` operation. | Yes. Its agents also show in unrelated chats (H8). |
| K-22 a mini app breaks at 3 a.m. (remote monitoring) | Supervisor breaker on Contabo, incident class `dependency`, consumers read the last good output marked `stale`. | Partly. The incident and app health stay on Contabo (H4). Nothing starts the "fix drafted by morning" step. |
| K-24 version skew | Kind digest in the heartbeat → preflight refuses → `node needs update`. | Yes for placement. Draining Contabo has no owner (L9). |
| K-28 pause all autonomy | One Settings flag. | Sync direction unstated (M5). |
| K-30 fork a session | `Harness.fork` on the SDK's `fork_session`, P-FK. | Yes, given P-FK. |

## Complexity and oversimplification verdicts

- **Creep:**
  - H6: about 40 servers per chat plus a keep-off loop, where one list-changed server would do.
  - M13: copying folders into the Library.
  - Everything else new (marks, hypotheses, claims, the heartbeat, the Surface) is the smallest mechanism for its scenario and follows the Claude Code or Hermes shape.
  - `qmx_host` as a new package rather than a larger `qma.serve` is justified: the engine may import only the harness's exports, so the harness cannot compose the engine without an import cycle.
- **Oversimplification:**
  - H3: the boundary is stated stronger than it is.
  - H7: remote compute is deleted early.
  - M10: the name check is dropped.
  - M14: the delete floor is too blunt for Interactive chats.
  - Deleting `core/simulate.py` is fine: its tests move onto `Engine` through the existing `executors=` seam.

## Checked and cleared

- The polling claims: `harness_adapter.py:44` and `:221-246`, with `Reject(REJECTION)`. `Chat.next_end` exists (`chat.py:815`).
- The single semaphore of 3 (`settings.py:55`, `workers/local.py:47`).
- `PLUGIN_SHA256` (`home.py:73`) and `money.py` at 1,198 lines.
- The engine host mounts no chat routes (`qmx_engine/host.py`).
- In the harness, only `money.py` and `tools.py` import `qma.core`. `qma` is a namespace package with no `qma/__init__.py` in `qma-core`, so the harness survives the deletion.
- `apps/qmx-ui` is a fixture shell with no live wire to the daemon.
- `release/*.json` and `qa/backend-quality/ci-inventory.json` name daemon paths, but no code reads them.
- Broker and prop-firm origins stay always-deny in AD-44 after the gate is removed.
- The QMB host's pairing and recover-control branches are handled by DELETION-PLAN D2.
- SDK facts cited by 43 and 47 exist as stated: `skills` (`types.py:2664`), `toggle_mcp_server` (`client.py:417`), `fork_session` (`types.py:2604`) and `settings` as a path (`types.py:2460`). What 43 and 47 missed is what those facts *don't* do (H2, H6, H8).

## Before any of this is built

The cheapest checks that catch the real bugs:

1. A two-chunk agent run in two overlay folders, comparing cache reads with and without `exclude_dynamic_sections` (H1).
2. Change `append`, resume, and confirm the model sees the new text (H2).
3. A declared-Bash write outside the overlay in P-PERM (H3).
4. Two chats in one workspace, each switching a different server off, then relaunching (H6).
5. The PC asleep with `primary = pc` while a Contabo app hands off to a Contabo app (H5).

Checks 1, 2 and 4 cost one haiku turn each on the plan login. Check 3 needs no model call beyond the probe's own turn.
