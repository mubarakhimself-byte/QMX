> STATUS 2026-10-16 (rubric walk): KEEP-AS-SOURCE. See 27-rubric-walk.md. Rulings in 26 win.

# 20 — Review B: technical feasibility of `19` against the real code

Reviewer: adversarial feasibility pass, 2026-10-16. I read `19` in full and checked it against `03`, `05`, `10`, `13`, `14`, `18`, the one-engine `DESIGN.md`, `DELETION-PLAN.md`, `BACKLOG.md`, the wayfinder map and tickets (`python frontier.py` run), and the shipped harness on branch `qma/hp17` (read with `git show`, nothing checked out). I also read the installed Python SDK (`claude_agent_sdk` 0.2.166 in `D:/QMX-worktrees/qma-hp17/qmx-agents/.venv`) and the HP17 sign-off (`qmx-agents/packages/qma-harness/docs/SIGNOFF.md` on `qma/hp17`).

Short verdict: the contracts are sound as product ideas, but `19` treats the shipped harness as more flexible than it is. Five of its central promises (per-folder plugins, a cheap `model` step on the plan, "the Lab never asks", agent-step replay, and the browser lease) collide with invariants the operator already signed in DESIGN.md or with plain SDK facts. Wave 1 cannot start as drawn: the map blocks its packet plan behind wave 2 and wave 3 tickets, and the harness source is frozen during the deletion program. Four of the seven wave 2 pilots need a trading node that the map itself calls premature.

Paths: `hp17:` means `git show qma/hp17:<path>` in `C:\Users\Mubarak\Desktop\QMX`. `H/` is `qmx-agents/packages/qma-harness/src/qma/harness/`. `SDK/` is the installed `claude_agent_sdk` package.

---

## Findings, ranked by severity

### Critical (blocks a wave or breaks a signed invariant)

**1. Wave 1 has no way to start. The map blocks it behind wave 2 and wave 3 work.**
- Where in 19: §8 Wave 1 (lines 350-360); MAP "Destination".
- Problem: `build-plan-into-qma-v2` is the only ticket that produces build packets. It is blocked by `methodology-umbrella`, `strategy-funnel-template` and `first-templates`. The umbrella waits on 19 tickets, including `methodology-builder`, which is wave 3 work. `first-templates` is the wave 2 pilot grilling. So no wave 1 packet can be written until wave 2 and 3 design is closed. The map does not show this cycle.
- Second block: the deletion program freezes the harness source. `DELETION-PLAN.md:43` says "No PR touches ... `qmx-agents/packages/qma-harness/src/`". D1 needs HP17 merged and his sign-off (`DELETION-PLAN.md:72`), and SIGNOFF.md says the status is "waiting for the operator". Every wave 1 track needs harness changes (findings 2, 3, 4).
- Fix: add a ticket "Wave 1 packet plan" blocked only by `workflow-engine-contract`, `plugin-unit-and-loading`, `session-homes`, `role-to-model-table` and `autonomy-policy`. Order it after the HP stack merge and D4. Keep `build-plan-into-qma-v2` for waves 2-4.

**2. The engine's `model` and `agent` steps need a harness API that does not exist, and the `model` step cannot run on the Claude plan at all.**
- Where in 19: C2 (line 120: "`model` (one relay call...)"), C4 budget class B1 (line 128: "at most one cheap call (about 8k tokens)"), §8 Wave 1 Engine track.
- Problem, `model` step: the relay mints grants only for `KeyProvider | GptPlan` (`hp17:H/relay.py:170`, `:411`). DESIGN rules that no QMX process sits on the plan path and that "a relayed plan launch cannot be built" (DESIGN.md:189, 285). So on the Claude plan, every model call is a full Claude Code CLI chat: a process start, the Claude Code system prompt and tool list, and a chat slot. B1's "one call, about 8k tokens" cannot exist on the plan. It works only on key providers.
- Problem, `agent` step: the public harness API is `start_chat(NewChat)` and `send`. `NewChatIn` has title, model, effort, mode, workspace and profile, and it forbids extra fields (`hp17:H/routes.py:130-137`). It has no structured output (the SDK has `output_format`, `SDK/types.py:2742`, but the harness never passes it; `H/launch.py:376-426`), no per-chat tool allow-list, no per-chat `max_turns` or budget (these come from global `[budgets]`, `H/launch.py:177-188`), no per-chat plugin set, and no home. A Background chat can be started only from Python in the same process; REST cannot start one (`05` §6 hook 1).
- Fix: (a) state in C2 that `model` steps run on key profiles only, and that a plan step is a short Background chat turn with a measured token floor. (b) Add a harness packet "engine hooks" to wave 1: `NewChat` gains `output_format`, `allowed_tools`, `max_turns`, `max_budget_usd`, `plugins` and `home`. (c) Run the engine inside the `qma.serve` process, so that it calls `Harness` directly and no new REST door has to accept injected text.

**3. "The Lab never asks" contradicts the shipped effect table. Unattended Lab work would fail every night.**
- Where in 19: Decision 2 (line 18), C3 autonomy table (line 124), §10 row 1 (line 414).
- Problem: `MANAGE` always asks (`hp17:H/tools.py:56-90`, the `asks()` function). `run_job`, `workflows_run`, `workflows_put`, `apps_update`, `apps_call`, `apps_start` and `apps_publish` are all MANAGE (`H/tools.py`, table near lines 126-160). DESIGN departure 19 and S29 make sure an allow rule cannot pass an asking QMX tool, and AllowAlways returns `invalid`. In a Background or Child chat, an ask waits `unattended_ask_seconds` (default 300, `H/launch.py:184`) and is then rejected. So L4, D3, B and D7, running unattended, would be rejected at their first `run_job` or `apps_update`. A "standing allow rule" has nowhere to live in the harness.
- Fix: choose one and record it as his ruling. (a) The engine does MANAGE acts itself, as `script` steps under a standing rule stored in the engine's trigger row. Agents inside the Lab only return JSON proposals. This needs no harness change, and I recommend it. (b) Add a per-home MANAGE policy to the harness. That changes R35, a signed-off rule.

**4. Per-folder plugins clash with three harness checks, and C1's slots let folder code run outside the money gate.**
- Where in 19: C1 (line 116), §10 row "Core plugin locked plus a registry" (line 422).
- Problem, loading: the harness loads exactly one plugin and refuses to launch if its hash differs from a constant in code (`hp17:H/home.py:70-105`). After launch it closes the chat if the init message lists any plugin other than `qmx@inline` (`H/chat.py:611-620`), or any command or agent not named `qmx:` (`H/chat.py:585-609`). A registry of approved folders means rewriting all three checks and `build_options` (`H/launch.py:409`). §10 says "no conflict"; that is wrong.
- Problem, safety: the plugin check refuses only `!` shell lines in `.md` files (`H/home.py:90-102`). C1 and `14` §2.3 add `hooks/hooks.json`, `.mcp.json`, `tools/<name>.py`, and through the plugin format also `monitors/`, `bin/` and `settings.json`. Command hooks and monitors run shell commands that the PreToolUse money gate never sees. An in-process `tools/*.py` would run agent-written Python inside qmx-control, the process that holds the relay keys.
- Problem, hashes: C1 puts `pending/` inside the folder. Any byte written there changes the folder's content hash, so an approved folder would fail its own launch check.
- Fix: the registry packet must (a) take a list of `(path, sha256, trust)` rows; (b) refuse `hooks/`, `monitors/`, `bin/`, `settings.json` and `.lsp.json` in any folder except the core plugin; (c) run folder tools as stdio MCP servers that pass `vet_mcp_servers` and the unattended external-tool rule (`H/money.py:640-646`), never in process; (d) move `pending/` to host state.

**5. Four wave 2 pilots need a trading node that does not exist, and the guard lock-out contradicts the guard reader.**
- Where in 19: §8 Wave 2 orders 1, 2, 6 and 7 (lines 366-372); C7 (line 140); Wave 0 row "Account guard lock-out" (line 336).
- Problem: P2 "proves the account-guard reader"; RK1 needs the kill line, guard state and a heartbeat; T5 needs demo units with journals; T9 needs real fills. `05` §5 says QMN has "no read model or powers path" and that the only Portfolio backend is broker reads plus unsigned proposals. The map lists node internals as "premature". So these pilots cannot run.
- Contradiction: the lock-out ticket says "every read and write attempt is denied" (`wayfinder/tickets/account-guard-lockout.md`, and Wave 0 line 336: "agents cannot read or write the guard"). C7's reader serves "guard state, the guard config hash". P2 and RK1 depend on that read.
- Also: RK1 runs "every 30 s with open risk" (§9). A kill-line watchdog inside a QMX engine on a desktop PC stops when the PC sleeps or QMX is closed (`qma.serve` is not a service). It belongs with the node and the guard. QMX should only read its heartbeat.
- Fix: split the lock-out into "no write path at all" (a deny rule) and "read only through the C7 reader". Move RK1, T5, T9 and every template whose core input is a running unit's journal or fills (T6, T7, RK2, RK3, RK6) to wave 4, beside P1, P3 and P4. P2 pilots on `qmx-broker` reads only, with guard fields rendered as "could not check".

**6. The browser design as written gives any agent with Bash full control of his logged-in profile, and the money gate does not cover browser navigation.**
- Where in 19: C6 (line 136); §10 row "QMX Browser profile as the first step" (line 421).
- Problem, CDP port: C6 binds CDP to `127.0.0.1` and says the broker "holds the single CDP connection". Chrome accepts many CDP clients on that port. Agent Bash runs as the same OS user (DESIGN.md:314-315 accepts this), so it can open the port, list every tab, and read every cookie with `Network.getAllCookies`. Leases, levels and "one controller per tab" then mean nothing. Playwright MCP over `--cdp-endpoint` also attaches to the whole browser, not to one leased tab.
- Problem, money: the gate checks broker hosts only for `WebFetch` and shell tools (`hp17:H/money.py:658-664`), and the host list is cTrader only (`H/tools.py:232`). A Playwright `browser_navigate` to a broker web terminal, an MT5 web terminal or a prop-firm dashboard in the logged-in profile is not denied.
- Fix: start Chrome with `--remote-debugging-pipe` owned by the broker, so there is no TCP port. The broker serves one proxied CDP endpoint per lease, behind a per-lease token (the relay's grant pattern), and filters `Target.*` to the leased tab or context. The broker enforces an origin deny list that covers broker and prop-firm domains. Add the browser tools' URL fields to the gate's host check, and keep the host list in one place.

### High

**7. Fan-out widths exceed the chat-slot cap.**
- Where: C4 B3 ("fan-out of at most 6 children"), `research-harness` (3-5 searchers), §3 sub-agent roles.
- Problem: `max_live_chats` defaults to 4 across every chat, interactive ones included (`hp17:H/launch.py:182`). `delegate` is refused at once when no slot is free, and it blocks the parent until the child ends (`H/harness.py:401-445`). Native sub-agents need no slot, but they share one CLI. Their results are lost if that CLI dies mid-turn, so they do not give the engine's "finished items kept".
- Fix: engine fan-out width = `max_live_chats` minus an interactive reserve (default 2 free slots). Durable per-item fan-out runs as separate engine steps. Native sub-agents serve cheap, non-durable fan-out inside one step.

**8. Reviewers on another model family cannot be native sub-agents.**
- Where: §3 ("Validator and judge run on another model family"), C4 reviewer rule, `audit-other-family`.
- Problem: DESIGN rules out "cross-provider sub-agents inside one CLI" (DESIGN.md:285). Inside a relayed CLI, a sub-agent's `model` can only name that provider's tier aliases. `delegate` is denied inside native sub-agents (R33; S11 PASS in SIGNOFF).
- Fix: any step bound by the family rule runs as its own engine step on a key profile. Write that into C4 and into the role table.

**9. Pause-at-cap rests on telemetry the Python SDK does not have.**
- Where: C2 ("a usage-cap hit marks the step `waiting`"), C4 admission control; ticket `pause-at-cap`.
- Problem: `SDKUsageReport` and `rate_limits` appear only in the TypeScript reference (`03` §2). A grep of the installed Python SDK 0.2.166 finds no `usage_report`, `rate_limits` or `user:profile`. The harness reads rate limits from `rate_limit_event` frames while a plan chat streams (`H/chat.py:1137-1145`). SIGNOFF.md (S10 meter note) says `/usage` no longer reaches Python. Events fire only when a status changes (DESIGN.md:279). The cap is checked when a prompt is sent (`H/harness.py:346-360`), not mid-turn, so a step that started at 49% can run to its 50 turns. His own use of claude.ai or Claude Code on the same account shows up only at the next QMX reading.
- Fix: the governor uses the last reading plus `resets_at`, and each agent step gets a small `max_turns` (needs finding 2's API). A parked run resumes at `resets_at` and spends one short probe turn to get a fresh reading. Remove the `user:profile` probe from the ticket; it does not apply to Python.

**10. SQLite: the engine would hit the known WAL-reset bug. 19 never mentions it.**
- Where: C2 run ledger, C8 gate store, C9 ledgers, C10 memory, trigger rows. BACKLOG B1.
- Problem: Python 3.14.6 ships SQLite 3.50.4. The WAL-reset fix is in 3.51.3. qmx-control opens one connection per call (BACKLOG B1). The earlier QMA spine needed one connection in one thread to stay safe (`hp17:_bmad-output/.../architecture-QMA-2026-08-28/ARCHITECTURE-SPINE.md:126`). An engine that writes a span per step, from parallel steps run through `asyncio.to_thread`, plus a watchdog and a scheduler, meets the bug's stated precondition.
- Fix: B1 is a wave 1 prerequisite. Give the engine one writer connection on one thread in its own DB file, or move to a SQLite of 3.51.3 or later (`pysqlite3-binary` or a newer CPython build).

**11. The engine cannot replay "the saved prefix" inside an agent step, and side effects inside agent steps repeat on retry.**
- Where: C2 ("sub-calls inside agent and `rlm` steps are logged so a retry replays the saved prefix"; "model calls are cached by (model, prompt hash, params)").
- Problem: the CLI owns the agent loop and its transcript. QMX cannot feed cached tool results back into a Claude Code turn. It can only resume or fork the session (`resume`, `fork_session`; `SDK/types.py:2604`). Tool calls made before a crash, such as `library_save` (DOMAIN_WRITE, allowed by default), workspace edits or Bash, run again on retry. The `run_id:node_id:attempt` key covers engine script steps only.
- Fix: rule in C2 that agent steps write only to their workspace and return JSON. Script steps commit results with idempotency keys. Before a retry, roll the workspace back with file checkpointing (already on, `H/launch.py:419`). Cache results by `(model, prompt hash, params)` only for key-profile `model` steps.

**12. No sandbox exists on this PC for RLM, model-written Lab code or agent-built mini apps.**
- Where: C2 `rlm`, §10 row `rlm`, Lab "total creative freedom", D7.
- Problem: the PC runs Windows 11 Home, which has no Windows Sandbox or Hyper-V client. SIGNOFF.md says no Docker engine runs. Mini apps at trust `agent` refuse local install and need Docker at T2 (`05` §1). Inferred, to verify: Claude Code's own `sandbox` setting (`SDK/types.py:1141`) supports macOS, Linux and WSL2, not native Windows. Model-written code therefore runs as his user, and agent Bash can read every `qmx/*` keyring entry (SIGNOFF.md, "Money posture").
- Fix: probe 6 below. Until it passes, `rlm`, L4 and D7 run attended only, and C2 says so.

**13. The cost model has a dependency cycle.**
- Where: C8 ("profitable at 1.5x the live cost model"), C9 ("written by T9 from real fills"), wave 2 orders 6 and 7.
- Problem: B's gate reads the live cost model. T9 writes that model from real fills. Real fills exist only after B promotes a unit and it trades on demo. Wave 2 puts B before T9.
- Fix: ship cost model version 0 from the broker's symbol specs and measured spreads (`qmx-broker` `symbol_info` and `quotes`). Let T9 replace it later, logging the version change.

**14. The funnel pilots depend on a QMB door that another session owns.**
- Where: `spec-compile` (D2: "register through the host validator"), `lab-run`, RK4, L1, B, D3.
- Problem: the only backtest door is `run_backtest(config_ref)` with pre-registered configs (`10` §6.7). QMB is the operator's tamper-proof tool, edited only by its own session (BACKLOG B7; `DELETION-PLAN.md:12`). The overfit gates also need per-trial returns, walk-forward folds, 200 noise runs and 1,000 random-entry runs per candidate. Nobody has measured that compute on his PC.
- Fix: add an external ticket "QMB register and batch door", owned by the QMB session, and block L1, B, D2, D3 and RK4 on it. Run probe 9.

**15. "Runs move to the server" is premature, and two hosts on one plan break the 50% cap.**
- Where: C2 (`runs_on`), C4 per-workflow `runs_on`, wave 1 Engine track.
- Problem: the harness has never run on Linux (SIGNOFF.md: "Linux container lane. Not run"). Without user systemd, as in a typical container, there is no memory cap (DESIGN.md:273). A plan login on the server is a second device on the same account. Each host would run its own governor and each would allow 50%. Inferred: unattended server use of a consumer plan also needs a terms check.
- Fix: in wave 1, `runs_on` is a field only. Server runs use key profiles only until B44 passes, which matches B44's "OpenRouter for remote agents". There is one governor per account.

### Medium

**16. Packs cannot be added mid-session.**
- Where: C3 ("A session may add packs").
- Problem: plugins are fixed at launch, and nothing hot-reloads (DESIGN departure 11; the ConfigChange guard). The SDK client can toggle MCP servers given at launch (`SDK/client.py:417`) but cannot add a plugin. The SDK's `skills` option is "a context filter, not a sandbox" (`SDK/types.py:2680`), so it cannot scope a pack.
- Fix: a pack set is part of the launch config. "Add pack" is a quote and apply RELAUNCH with `resume`, which already shows the uncached-resend warning (DESIGN call site 4). Optionally, preload a home's pack MCP servers and toggle them.

**17. Packs will press on the Windows command-line limit.**
- Where: C1 slots `AGENTS.md` and `SOUL.md`; C3 packs.
- Problem: the harness puts instructions into `--append-system-prompt` and the MCP config into `--mcp-config`, and refuses a launch above 30,000 characters (`H/launch.py:325-360`). Plugins have no `AGENTS.md` slot, so every pack's `AGENTS.md` and `SOUL.md` would go into the append text.
- Fix: settle DESIGN open question 4 (`--append-system-prompt-file`) before packs ship.

**18. The approval answers are wrong in `05`, `10` and `19`.**
- Where: §8 Wave 0 UI ("the five approval answers").
- Problem: the code has four answers: `allow_once` (with optional edited input), `allow_always`, `reject` (with a message) and `answers` (`hp17:H/routes.py:180-205`). `allow_always` saves a rule for one workspace, not a global rule, and returns `invalid` for asking QMX tools. "For this errand" does not exist.
- Fix: correct the wave 0 UI list. Add "expired, re-run from here".

**19. Phone push has no channel.**
- Where: C2 notifications, §5.7 ("black ... pushes every 10 minutes"), wave 2 order 2 ("proves the push router").
- Problem: BACKLOG B14 is undecided. Sending a push message is a send on his behalf, which needs his choice of provider.
- Fix: make "push channel" a wave 0 decision for him. Until then, the router writes to the inbox only.

**20. Cron fires only while the PC is awake and QMX is running.**
- Where: C2 triggers, §9 watchdog cadences.
- Fix: say so in C2. Merge missed fires, as Hermes does. Optionally use Windows Task Scheduler wake timers. Nothing safety-critical lives in QMX schedules (see finding 5).

**21. Webhooks need a public door, and agents can read the signing secret.**
- Where: C11 (`accepts` webhook routes signed by a `qmx/*` secret).
- Problem: qmx-control binds `127.0.0.1`, so outside webhooks need a tunnel or relay. The signing secret sits in the keyring, which agent Bash can read (SIGNOFF.md money posture). A forged event can fire a trigger, which gets around "a run cannot create a trigger".
- Fix: a separate listener behind a tunnel, with rate limits. Event triggers may start only templates with no MANAGE or money effects. Say plainly that this is a speed bump until U10.

**22. "Settings read-only to agents" is a speed bump, not a lock.**
- Where: C8 ("read-only to agents ... the engine lint rejects it").
- Problem: agent Bash can read the qmx-control bearer and call the REST door (DESIGN.md:314). The lint and the allow-list cover tool calls only.
- Fix: write C8 honestly. Make loosening visible: every threshold version is logged with a diff and shown in run chrome, and a gate verdict records the threshold version it used.

**23. The live view would stream logged-in pages to any local process.**
- Where: C6 (watch pane "served only on `127.0.0.1`").
- Fix: serve frames behind the same BearerGate as the UI, never store them, and start the stream only when the pane is open.

**24. Stagehand is not model-agnostic in QMX's setup.**
- Where: C6 tools, wave 3 "Stagehand replay".
- Problem: Stagehand is a Node/TypeScript library that calls model APIs itself. It cannot use the plan login. `18` line 88 leaves attaching it to an existing Chrome over CDP unconfirmed.
- Fix: replay with Playwright MCP's `--codegen` scripts (no model at all), or run Stagehand on a key profile through its own relay grant.

**25. Structured output from agents is unproven on relay providers and not wired in the harness.**
- Where: C5 ("Agents emit structured JSON"), C2 `model` step "with a JSON schema".
- Fix: probe 10. Add `output_format` in the finding 2 packet. Keep a grader-side JSON repair retry.

**26. The map hides edges for the wave 2 pilots.**
- Where: ticket `first-templates`, `blocked_by`.
- Missing edges: `browser-for-copilot-and-workflows` (pilot 4 uses B3 capture), `session-homes` and `capability-packs` (L1 uses C3), `memory-scopes-and-lessons` (C10 is named by 9 of the pilot templates), `triggers-and-scheduler` and `pause-at-cap` (the exit gate is "three nights unmanaged"), `experimentation-board-vibe-coding` (pilot 5 is the Board), and the external items: the QMB door (finding 14), the node read model (finding 5), the HP merge and D4 (finding 1), and B1 (finding 10).
- Fix: add these edges. Pilot 4 can also drop the browser: `yt-dlp` captions through the `watch` skill plus WebFetch or Firecrawl for articles. The X thread then waits for the browser.

**27. The UI waves claim more than the backend gives.**
- Where: §8 UI lines for waves 0-3.
- Problem: B12 (UI wiring) waits for the harness event protocol to merge (BACKLOG B12), and the HP stack is unmerged. The wave 1 run timeline, job panel and inbox need run and node event kinds and an `approvals` topic, and none exists (`05` gaps 13). The chat model has no `failed` or `cancelled` state; those come only with engine runs. The wave 3 Library lineage tab needs Strats v2 (B8), which is in another session.
- Fix: wave 0 UI starts after the HP merge. Wave 1 UI builds against recorded fixtures until the engine emits events. The lineage tab moves to "after B8".

### Low

**28.** C3 tool names `lab.*` and `wf.<name>.*`: MCP tools surface as `mcp__<server>__<tool>`. Inferred, to verify: the Anthropic API's tool-name pattern does not allow dots. Use `mcp__lab__run`.

**29.** The wave 0 row "three empty skills rewritten as examples" edits `qmx-agents/plugin/`, which changes `PLUGIN_SHA256` in `H/home.py:73`, a harness source file the deletion program freezes. D1 ports the same three skills (`DELETION-PLAN.md:77`). Do this after D1, in the same packet that bumps the constant.

**30.** MAP's Destination says "the 49 templates", but `19` §7 counts 48. The table holds 48.

**31.** "No wall-clock in control flow" (C2) sits beside L4's "deadline 07:00" and `continuity`'s "today vs yesterday". Pass time in as trigger inputs and handle deadlines as engine events.

**32.** A `delegate` child takes the parent's model tier or falls back to `opus` (`H/harness.py:419`). C4's per-step model override needs a model parameter on the delegate path or the engine API.

---

## Model-agnosticism: what silently assumes Claude

| Piece in 19 | Works on key providers through the relay? | Note |
|---|---|---|
| Hooks, skills, plugins, sub-agents, permission rules | Yes | The CLI is the same Claude Code, only the base URL changes. |
| `model` step | Keys only | No plan path (finding 2). |
| `agent` step structured JSON | Unverified | Probe 10. |
| Reviewer family rule | Needs a key profile | One CLI holds one provider (finding 8). |
| GPT lane | Unproven | DESIGN open question 10; translator probes P2 and P3. |
| `Workflow` tool node (§10 last row) | Claude only, and off in QMA | DESIGN departure 16 and S3. Drop it from the engine contract. |
| `rlm` sub-calls | Keys only in practice | On the plan each sub-call is a CLI chat taking one of 4 slots. |
| Stagehand | Its own API key | Finding 24. |
| Tool search with large pack tool lists | Off on OpenRouter and GPT | SIGNOFF S8 note, DESIGN GptPlan quirks. Large packs cost context there. |
| Provider switch inside a run | Unverified | S36 was skipped in run 2. |

---

## Probes needed before building (one session each)

1. **Engine-in-harness spike.** From inside `qma.serve`, start a Background chat with `output_format`, `max_turns=5` and a tool allow-list, once on the plan and once on Kimi. Record the JSON returned, the tokens of the first request, and the wall time. This settles finding 2 and B1's real floor.
2. **Cap telemetry over one 5-hour window.** Run a background loop of short plan turns. Log every `rate_limit_event` with its utilization and status, and how far a turn runs past the cap once it starts. Use his account with extra usage switched off.
3. **Two plugins at once.** Pass two local plugins through `plugins` with `setting_sources=[]`. Record the init `plugins` list, whether `dependencies` resolve, whether a plugin `.mcp.json` loads under `strict_mcp_config`, and whether a plugin PreToolUse hook that returns allow can beat the money gate's deny.
4. **Pack relaunch.** Resume a chat with a different plugin set. Measure the seconds and the uncached tokens. Test `toggle_mcp_server` on servers preloaded but turned off.
5. **CDP broker.** Start Chrome with `--remote-debugging-pipe`, run a small broker that exposes one proxied endpoint per lease, and point Playwright MCP at it. Then (a) two native sub-agents share one Playwright MCP instance, to test tab clobbering; (b) agent Bash tries to reach Chrome directly; (c) `browser_navigate` to a cTrader web URL.
6. **Sandbox on Windows 11 Home.** Check WSL2 and Docker Desktop (the operator accepts any terms). Run a model-written Python cell with no keyring and no network. Check whether the SDK `sandbox` setting does anything on native Windows.
7. **SQLite under engine load.** Run 6 parallel steps plus a watchdog writing spans, first with per-call connections and then with one writer connection. Record `sqlite3.sqlite_version`, and check that `pysqlite3-binary` installs on Windows.
8. **Fan-out under the slot cap.** With 4 slots, an open interactive chat and a 6-wide engine fan-out, record the refusals. Kill a Background chat in the middle of a native sub-agent fan-out and see what survives.
9. **QMB door.** Can an agent-written spec be registered and run? Time 200 trials and one full RK4 battery on his PC. This needs the QMB session's go.
10. **Relay providers.** Run Kimi and GLM through the relay with `output_format` and 60 or more MCP tools. Record schema compliance and context cost.
11. **Agent-step retry.** Kill the CLI after a `library_save` call and before the result arrives. Resume, and count the duplicate rows.
12. **Server lane (B44).** Run the harness on Linux in Docker with a key profile only and no user systemd. Check the run_all `--no-login` rows.

---

## Corrected wave order

| Wave | Contents | Gate to enter |
|---|---|---|
| 0 | His decisions (the ten, plus a push channel and the MANAGE policy of finding 3). Specs only: C1 with the slot refusals, C5 schemas, C7 facts with the reader/lock-out split, C8 table, C9 with cost model version 0. Probes 1-4, 7, 10 and 11 as scripts under `scripts/live/`, with no harness edits. Research tickets as listed. | None |
| 0.5 | HP stack merged, D1-D4 merged, B1 fixed. Wave 0 UI wiring with the corrected approval list. | His merge click |
| 1a | Harness packets: engine hooks (finding 2), plugin registry with slot refusals (finding 4), `home` on the session and `kind` on create, packs as launch config (finding 16), per-home MANAGE policy if he chose that route. | Wave 0.5 |
| 1b | Engine core inside `qma.serve`: ledger on one writer, `script`, `rule`, `agent`, `human` and `grader` steps, fan-out capped by slots, triggers, preflight, pause-at-cap on `rate_limit_event`, watchdog, inbox. C4, C8, C9 and C10 (minimal) stores. C5 renderer. | 1a |
| 2 | Pilots in this order: RS1 with RS7 (no money, no browser, no QMB; proves the engine, fan-out, cap and grader), then T1 without RK1, P2 on broker reads only, A with `yt-dlp` and WebFetch capture, RS0. Then L1 with D2 and L2, and B with D3 and RK4, once the QMB door ticket closes. | 1b; the QMB door for the last two |
| 2b | C6 first step after the B17a un-hold and probe 5: pipe-owned CDP, lease proxy, origin deny list, an authenticated watch pane. | His go on B17a |
| 3 | The rest of the research, Lab and developer catalogue; the builder and variants; T2, T3, T4, T8 and T10 with unit facts as "could not check". `rlm` and L4 unattended only after probe 6. | Pilots' exit gate |
| 4 | Everything that reads a running unit or the guard: RK1, RK2, RK3, RK5, RK6, T5, T6, T7, T9, P1, P3, P4. Mini apps D7-D9 (they need Docker T2). The server after B44. The cloud browser. Library lineage after B8. | Node read model, risk session, probe 6, B44 |
