## Findings

Paths are relative to `D:/QMX-worktrees/agent-system/tracker/qma-v2/`. "HS" means `D:/QMX-worktrees/harness-survey/qmx-agents/packages/`.

### 1. [critical] Control operations that agents can call already inject broker credentials, and money.classify cannot see it
**Location:** `sketch/qmx_control/server_changes.py:47` ("Existing 52 rows convert mechanically … who=ANY"); `sketch/qmx_control/agent_ops.py:115` `ControlAgentOps` (catalog = every who=ANY row); `sketch/qma2/money.py` `classify` steps 2-4.
**Finding:** Agents get every existing row as `mcp__qmx__*`. That includes `run_job` and `runs_start_remote`. A `RunBundle` takes `credentials_scope: {ENV: "qmx/<label>"}` (HS/qmx-remote/src/qmx_remote/models.py:73, validated only as `qmx/*`). `RunManager._launch` resolves each label with `keyring.get_password` inside the control process and injects it into a job whose `command` the caller wrote (runs.py:111-116). The job's output then comes back through `job_logs` and `runs_fetch`.
**Evidence:** A single tool call such as `run_job{bundle:{kind:"job", command:[...print env...], credentials_scope:{"K":"qmx/ctrader"}}}` reaches the broker secret. `classify` sees only the op name (tokens run/job, no money act) and the descriptor (no money meta). It checks MoneySurface labels only for shell and file tools, never inside QMX-op arguments. This goes against the design's "real guarantee, injection" claim (HARNESS.md:126). It also defeats the "credentials on the trading node" fallback (:128), because the bundle can target a remote node.
A second likely path, which I did not run: `apps_create(path, trust="operator")`. `trust` is a parameter the caller sets (service.py:657). The manifest is written by the agent and declares `capabilities.secrets`, which `apps_start` resolves from the keyring into the app's env (supervisor.py:411-418).
**Suggestion:** Make the agent catalog an explicit allow-list, not "all who=ANY". Add a third `who` level (or keep `run_job`, `runs_start_remote`, `apps_create/update/start/publish/restore`, `settings_put` and `backup_*` out of the agent catalog). Make `classify` treat any `OperatorSecretRef` label that appears anywhere in a QMX op's arguments as a `MoneyHit`. Add a live check that calls `run_job` with a broker ref.

### 2. [critical] An agent can forge the operator principal and remembered rules by writing harness.db, and no barrier covers that file
**Location:** `sketch/qma2/store.py:117` `operator_sessions` and `:87` `rules`; `sketch/qma2/operator.py` (`verify` = hash lookup); `money.MoneySurface.state_paths` (only broker/portfolio paths); `policy.Workspace.protected` (relative `.git/.claude/.qmx` under the workspace roots).
**Finding:** The operator cookie is checked only as "hash present in harness.db and not expired". Once any Bash or python command is allowed, the agent can run `sqlite3 ~/.qmx/harness.db "insert into operator_sessions values(sha256('x'),…)"`. That hands it a full operator principal. With it the agent can call `approvals_answer`, `threads_set_mode` (bypass), the accounts rows, and the sign route, which the design promotes to an operator row. Inserting `rules(scope='user', behavior='allow', rule_text='Bash(*)')` gives it self-granted approvals for all future calls. Neither table sits on MoneySurface or behind protected paths. The tension-2 list (HARNESS.md:136) names only cookie theft and `pair` as speed bumps. This write also creates a second writer on harness.db, which is the WAL-bug precondition the store exists to avoid.
**Suggestion:** Bind operator sessions to an HMAC key held as an `OperatorSecretRef`, not to a bare hash in the DB. Add `harness.db`, `control.db`, `~/.qmx/config/**` and `<cwd>/.qmx/**` to MoneySurface state paths (write → `MoneyHit`). State this speed bump honestly alongside the keyring one.

### 3. [critical] The gate's failure path is undefined, so the Claude engine fails open, including for MCP money tools in bypass mode
**Location:** `sketch/qma2/host/claude.py:41` `permission_mode=mirror(spawn.mode)` and `_pre_tool_use`/`_can_use_tool`; HARNESS A8 (:250-255) records the hook timeout but no behaviour on timeout.
**Finding:** If `_pre_tool_use` raises (link EOF during a control restart, a decode error) or exceeds the SDK's hook-callback timeout (PreToolUse user hooks run inside it through `policy.evaluate`), Claude treats that as a non-blocking hook error. It then continues with its own mode, rules and `can_use_tool`. Under mirrored `bypassPermissions`, the call runs with no QMX decision. That includes an external broker MCP tool, which never reaches `money.classify`. This breaks "no mode (including bypass) can unlock it" (HARNESS.md:125). The CallOp grant only protects `qmx` tools.
**Suggestion:** Catch everything in the callback and return deny. Make `_can_use_tool` deny any call that has no matching QMX `Pending`. Never mirror bypass or acceptEdits to the SDK: mirror only `plan`, otherwise `default`. Keep the total PreToolUse hook time under the SDK timeout and record that limit in U1.

### 4. [warning] On the Claude engine, MCP money checks are name-only, so the two engines are not identical
**Location:** HARNESS.md:118 and :125; `money.ToolCatalog` ("Built once per segment from ResolvedConfig + PROPOSAL_TOOLS + control ops"); `host/claude.py:46` `mcp_servers={**to_sdk_mcp(spawn.mcp), …}`.
**Finding:** On Claude, the CLI connects the MCP servers, so the control side never sees their tool descriptors (`money_path` meta, annotations, parent surfaces). `check_descriptor` therefore degrades to name tokens. On OpenAI, QMX connects the servers itself and sees the full descriptors. The behaviour differs by engine, against "identical by construction".
**Suggestion:** Either have QMX connect to MCP servers on both engines and re-expose them through the `qmx` SDK server, or list each server's tools at segment start and deny any MCP tool name that is not in the catalog.

### 5. [warning] Agents and the client token can escalate through thread operations open to anyone
**Location:** `sketch/qmx_control/agent_ops.py:22-30` (`threads_create`, `threads_send`, `threads_steer`, `threads_fork` all `who=ANY`); `model.ThreadSpec` (`profile`, `origin`, `cwd`).
**Finding:** `set_mode` is operator-only, but an agent (or a mini app holding the bearer token, per HOW Gotcha 8) can do either of two things. It can create a thread whose `profile` carries a permissive mode, or with `origin=OPERATOR` to skip the 50% background cap, or with `cwd` set to the home directory. Or it can `threads_send` work into an existing thread the operator put in bypass mode. Either way the agent runs commands under a mode it was never given, which defeats "an agent must never raise its own permission mode" (harness.py `set_mode` docstring).
**Suggestion:** Agent and client callers of `threads_create` must get `origin=AGENT`, the caller's own mode or lower, and no profile choice. `threads_send`/`steer` from the agent link should be limited to threads the agent spawned. Alternatively make these rows operator-only on the client door.

### 6. [warning] Project `.qmx/` config is honoured without a trust step, and an agent can write it
**Location:** HARNESS A4 (:242); `config.load`; `policy` protected paths.
**Finding:** A cloned repo's `<cwd>/.qmx/settings.json` supplies allow rules, profiles, and `PermissionRequest`/`PreToolUse` hooks. QMX runs those hooks inside the qmx-control process on the first tool call. Vanilla Claude Code asks for workspace trust first; QMX does not. An agent can also write this file through Bash, where protected-path detection is a heuristic, or through Windows path aliases (finding 17). That plants a PermissionRequest hook that answers every future approval with allow, which is the agent answering its own approval.
**Suggestion:** Add a per-root workspace trust record that only the operator can set, and ignore project hooks and allow rules until it exists. Reload config only between segments, and show the operator a diff when it changes.

### 7. [warning] An input rewritten by a PermissionRequest hook skips the money re-check
**Location:** `sketch/qma2/harness.py:313` (`if pr.decision in {"allow","deny"}: return as above`).
**Finding:** The chain re-runs money only after PreToolUse and after an operator edit. A Claude-format PermissionRequest hook can return `allow` with `updatedInput`, and that input reaches the engine without passing `classify`.
**Suggestion:** Send every input-changing step (PreToolUse, PermissionRequest, operator edit) through one `recheck_money(call)` before any Allow.

### 8. [warning] The actor design deadlocks on approvals, and the obvious fix breaks item ordering
**Location:** `sketch/qma2/harness.py:261` ("Mailbox-driven; one asyncio task") and `:293` (`Ask(Await) -> reply(await self._pending[aid])`).
**Finding:** If the mailbox loop awaits the approval future, it never processes the `resolve()` that would complete it. It also stops handling Gate asks from parallel sub-agents, Emits and Interrupt. Gate likewise blocks the mailbox while user hooks run. If the builder spawns a task per Ask, `LoadItems` (OpenAI resume and compaction) can then overtake Emits that are not yet committed. `_pending` and `_granted` would also gain several writers, breaking "sole writer".
**Suggestion:** Say it explicitly. Ask handlers run as child tasks. State changes (`_pending`, `_granted`, status) go back to the actor as messages. `LoadItems` waits on a per-thread "items committed up to seq N" barrier.

### 9. [warning] The one-shot CallOp grant cannot be keyed by tool_use_id on the Claude engine
**Location:** HARNESS invariant (:167); `wire.CallOp`; harness.py:296.
**Finding:** Python SDK `@tool` handlers receive only `args`. The existing recipe has no tool_use_id there and invents one (`operation(op_name, arguments, uuid.uuid4().hex)`, HS/qma-daemon/.../native_claude.py:194-202). The Claude host therefore cannot fill `CallOp.tool_use_id`. Separately, the grant check (`tool_use_id in _granted`) never compares the CallOp's `name` and `args` with what the gate allowed. `_granted` also collects the id of every allowed non-qmx call and never drops it, which leaks memory over days-long threads.
**Suggestion:** Bind the grant to (name, canonical args digest), consumed FIFO, and add a probe of the `@tool` handler context to U1. Add only qmx-tool calls to `_granted`.

### 10. [warning] The approval "ask" path drops hook-updated input, and the fallback correlation then fails
**Location:** `sketch/qma2/host/claude.py:117` (`Pending -> {"permissionDecision": "ask"}`); `_can_use_tool` FIFO (name, input digest).
**Finding:** On Pending, `gate` has already applied the PreToolUse `updatedInput`, and the approval stores that rewritten call. The host still returns a bare "ask", so the SDK passes the original input to `can_use_tool`. The FIFO digest then fails to match the stored approval, and "allow original input" is ambiguous between the pre-hook and post-hook versions.
**Suggestion:** Return `updatedInput` together with "ask". Compute the digest over the input the SDK will actually pass.

### 11. [warning] U1's live checks do not prove U1's claim, and some of them cannot run
**Location:** `research/architect/candidate-1-opus/units.md:44-54`; HARNESS A5, A6, A8.
**Evidence:**
- Every tool U1 exercises (Glob, Read, WebSearch) is one Claude allows on its own in default mode. A turn would pass even if the in-code PreToolUse hook never fired. Nothing checks a QMX-originated deny or money refusal. So "one QMX policy point decides every tool call" is never observed.
- "The env dump inside a Bash tool call" cannot run, because U1's stub gate denies Bash.
- "Grep of ~/.qmx finds no token" contradicts A6, since `claude-home/.credentials.json` sits under `~/.qmx`.
- "A second thread keeps streaming while the first host is killed" and the restart Done-when need the SSE route, store and resume, which A5 moved to U1b.
- units.md still lists the pre-A5 scope.
**Suggestion:** Rewrite U1's checks. A Bash call must be denied with the QMX reason. A money-path Read must be refused. Record the hook-fired counter versus the tools seen in `init`. Run the env check through a gate-allowed probe. Put the remaining checks in U1b's list.

### 12. [warning] The parallel lanes hide dependencies
**Location:** units.md:11-22 and U4 (:105-123).
**Finding:**
- U4 runs "parallel with U2", but `accounts_put_api_key` is `Who.OPERATOR`, and operator pairing ships in U2.
- U4's Done-when ("approval cards, the hook block … behave exactly as on Claude") and its live check ("H6, H7 and H8 re-run") need both U2 and U3.
- `LinkSession` needs `items` and `LoadItems`, which A5 moved to U1b.
- U1b and U0 are missing from the dependency graph.
- U5, U6 and U7 all edit `host/openai.py` and the `items` active/seed semantics: switch-seeding, archive, AgentTool and ProcessTable.
- U2 and U4 both edit `server.py`, the `who` column, `HARNESS_OPERATIONS` and the one-file console.
**Suggestion:** Redraw the dependency graph: U0 → U1 → U1b → {U2, U4-core}. Put U4's parity checks after U2 and U3. Give `host/openai.py` changes one owner per wave.

### 13. [warning] The 50% background cap cannot be enforced as designed
**Location:** `sketch/qma2/router.py` `pick`; `host/claude.py:58` `max_turns=None`; units.md U5 Done-when (:137).
**Evidence:**
- Claude reports `utilization` only when the status changes (H1 fact 10). The router uses the last snapshot, which may predate a reset, because `resets_at` expiry is not checked. It counts "unknown as allowed while status=allowed", so 49% and 89% look the same.
- The cap applies only at turn boundaries, and Claude turns have no turn limit. One background turn can use the whole window.
- LockedOut is per actor, so other threads on the same Max account keep sending into a rejected window.
- U5's live Done-when means pushing his real window past 50%, which the A10 budget (15 turns) rules out. It will be simulated, and the units contract says fakes never count.
**Suggestion:** Keep an account-level lockout state. Expire snapshots at `resets_at`. Set a budget per background turn, either `max_budget_usd` or a token cap, checked from usage rows. Probe `get_usage` (open question 7) before U5 and treat the cap as best-effort until it is proven.

### 14. [warning] OpenRouter and other keys can buy Claude or GPT through the API
**Location:** `model.ApiKeyAccount` docstring; `accounts.put_api_key` (refuses only first-party base URLs).
**Finding:** An OpenRouter key serves `anthropic/claude-*` and `openai/gpt-*`. The router, or a switch, can land on those models when the Max window is locked out. That contradicts the operator ruling "no API for Claude or GPT" (WHY, operator 17:11).
**Suggestion:** Add a model-family guard in `router.pick` and `quote_switch`, plus an account model filter, and test it.

### 15. [warning] "Recovery re-projects" has no mechanism behind it
**Location:** HARNESS.md:276; `Harness.open` pseudocode (only interrupts turns and expires approvals).
**Finding:** Items are written to harness.db, then blocks to control.db. Nothing records which item seq has been projected, and `sessions_append` is not idempotent. A crash between the two writes either loses blocks or, if re-projected naively, duplicates them. Separately, the Claude JSONL can hold messages that never reached `items` (host killed after the CLI wrote them), yet `items` is called the canonical transcript and used for export and engine-switch seeding.
**Suggestion:** Add `threads.projected_seq` with an idempotency key carried in the block content, and re-project from it on open. Document that a Claude-segment export also reads the JSONL.

### 16. [warning] OpenAI Responses replay will break on reasoning models
**Location:** `sketch/qma2/host/openai.py:99` (`reasoning_item_created -> reasoning.done (summary only)`); `LinkSession.add_items` no-op (:32).
**Finding:** On the ChatGPT route (`store:false`, no `previous_response_id`, H1 fact 17), history is replayed by hand. Function-call items must be accompanied by their reasoning items, including `encrypted_content`, which needs `include=["reasoning.encrypted_content"]`. Storing only the summary makes the next turn's replay fail or lose reasoning continuity.
**Suggestion:** Store reasoning items verbatim in `engine_payload_json`. Set the include flag in `PromptBuilder.model_settings`. Add a two-turn tool-using replay to U4 and U8.

### 17. [warning] The Windows path normaliser misses common aliases
**Location:** `sketch/qma2/policy.py` `normalize`; `money.classify` step 4.
**Finding:** The listed rules cover 8.3 short names, trailing dots and spaces, `\\?\`, case, and links. They miss:
- alternate data streams (`.credentials.json::$DATA`, `.qmx\settings.json::$DATA`);
- loopback UNC and admin shares (`\\localhost\C$\…`);
- `\\.\` device paths, `subst` and mapped drives;
- junctions or symlinks to paths that do not exist yet.

Step 4 also checks "under credential_paths". A `Grep`/`Glob` whose path is an *ancestor* of a credential path (for example `path=~`) is missed.
**Suggestion:** Reject ADS, UNC and device forms outright. Resolve with `GetFinalPathNameByHandle` where the path exists. Treat "ancestor of" as a hit for search tools.

### 18. [warning] The Claude engine loses CLAUDE.md after native compaction and loads MEMORY.md twice
**Location:** `wire.Spawn.context_prefix` ("prepended to the segment's first user message"); U3 scope (ProjectContext includes the MEMORY.md head).
**Finding:** With `setting_sources=[]`, the CLI does not re-inject CLAUDE.md after `compact_boundary`. A first user message gets summarised away, and no re-injection happens on `compacted`. U6 tests "still follows CLAUDE.md after compaction" only on OpenRouter. H1 fact 7 says auto memory loads whatever `setting_sources` is set to, so on Claude MEMORY.md arrives natively and again through ProjectContext.
**Suggestion:** Re-send ProjectContext as a system-reminder on the next turn after `compacted`. Drop MEMORY.md from ProjectContext on the Claude engine. Add a Claude-engine compaction check.

### 19. [warning] Agent MCP configuration multiplies the control.db writers
**Location:** HARNESS "Known gaps" (:268); config `mcp` → each host.
**Finding:** The domain servers `qmx-mcp-data|backtest|research|node` each build a `ControlService`, which makes each one a control.db writer (HOW plug-in table, `TOOLS/service.py:127`). Configured as agent MCP servers, they are spawned once per live host (by the Claude CLI or the OpenAI host). With up to 8 hosts, that is up to 8 extra writer processes. The design's "no writer added to control.db" holds only for the harness's own code.
**Suggestion:** Refuse qmx-tools stdio servers in agent MCP config until B1 is fixed, or expose the domain functions through `AgentOps`.

### 20. [warning] Usage dedupe key collides
**Location:** `sketch/qma2/model.py:483` and `host/claude.py:76` (dedupe on turn+model).
**Finding:** One QMX turn can produce several `ResultMessage`s: a steer sent as an extra `query`, a `/compact` query, or a Stop-hook re-run. With INSERT-OR-IGNORE, later rows are dropped silently and usage is undercounted, which feeds directly into the cap. H1 does not settle whether `model_usage` and `total_cost_usd` are per query or cumulative per session; if cumulative, summing them double-counts.
**Suggestion:** Key on the result message's own id or session+sequence, and add a probe to U1.

### 21. [warning] The operator principal does not fit the existing auth stack
**Location:** `sketch/qmx_control/server_changes.py` `resolve_principal`/`require`; HS/qmx-control/src/qmx_control/server.py:180-213.
**Finding:** Every route has `Depends(authenticate)` (bearer token), and `BearerGate` wraps the whole app. Cookie-only console requests would get 401 unless both layers are rewritten; the design says BearerGate "keeps its role". How `qmx_control pair` reaches a running `serve` is not specified. If it goes over REST with the client token, every mini app that holds `qmx/control-token` can mint the operator principal.
**Suggestion:** Specify one auth dependency that accepts the cookie or the bearer and returns a Principal. Make re-pairing a local-only channel (stdin, or a named pipe ACL'd to the user), never the client token.

### 22. [nit] The design contradicts itself after the amendments
- HARNESS call site 4 (:73) and `sketch/qma2/config.py:20-21` read project `.claude/settings.json`, `.claude/agents` and `.claude/skills`. A4 forbids that.
- A9 says "`fastapi.sse` … is not a real module". It is: the current `server.py:18` imports `from fastapi.sse import EventSourceResponse, ServerSentEvent`.
- Open questions 4 and 5 put the probes in U2; A8 moves them to U1.
- `agent_ops.threads_switch` says "body carries the quote id", but `SwitchQuote` has no id. If the client sends the whole quote back, `cost`/`cache_epoch` can be forged; the server must store quotes.
- `create_app(service, harness, …)` takes a `Harness`, yet its docstring says the lifespan opens it.

### 23. [nit] Import edges put policy code into hosts
`wire.py:29` imports `qma2.config`, which imports `qma2.policy`, which imports `qma2.money`. So every host process loads `policy.decide`. "Hosts never decide" is therefore not enforced by the import contract. Move `AgentDef`/`McpServerDef` into `model` or `wire`, and forbid `qma2.policy`/`qma2.money` imports from `qma2.host`.

### 24. [nit] operator.py has no way to write operator_sessions
`operator.pair` and `verify` are module functions, but `operator_sessions` lives in harness.db, writable only through `Store`, and only `harness.py` constructs a Store. Either `Harness` gains a pairing verb (outside the 19) or operator.py opens a second writer.

### 25. [nit] WebFetch and WebSearch are auto-allowed
The U1 stub and policy "read-only defaults" allow WebFetch and WebSearch. Claude Code's own tool table (not in H1; verify) marks both as needing permission. WebFetch after an auto-allowed Read is also a prompt-injection exfiltration channel.

### 26. [nit] suggest_rule widens interpreter commands
"First two tokens + `*`" (`policy.py:193`) turns an approved `python -c …` or `node -e …` into an always-allow for arbitrary code. Refuse interpreter and `-c`/`-e`/`-Command` prefixes.

### 27. [nit] Kill-tree and link integrity
- The supervisor must assign the host to its Job Object before sending `Spawn`. Python's Popen cannot start a process suspended and resume it.
- On POSIX, `setsid` children escape the process group.
- `main()` rebinds only `sys.stdout`. fd 1 is still the link, so it needs `os.dup2(2, 1)` after the dup, and every host child needs explicit `stdin=DEVNULL` and piped stdout. Otherwise inherited Windows std handles reach the link.

### 28. [nit] Smaller gaps
- Idle reaping (30 min after the turn ends) kills `background=true` sub-agents still running in the host.
- The behaviour at `max_live_hosts` overflow is unspecified.
- Managed settings still load under `setting_sources=[]` (H1 fact 3) and can add native hooks and rules; `doctor` should report them.
- `fork(at_turn)` on Claude has no H1-documented option; `fork_session` forks at the end.
- `qmx_apps → qma2.money` pulls both SDKs, including the bundled CLI, into qmx_apps and the qmx-remote worker environments unless the host dependencies become an extra.