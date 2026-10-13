---
label: qma-v2:review-opus (adversarial, /interrogate stance)
created: 2026-10-12
reviewer: Claude Opus 5.5, single-model run (no sub-agents)
target: tracker/qma-v2/ARCHITECTURE.md (783 lines)
checked against: PRD.md, HOW-WHY.md, research 19/30/31/32, origin/rebuild/base (read via git show), claude-agent-sdk 0.2.144 source, openai-agents-python clone (2026-10-08), code.claude.com docs (hooks, agent-sdk/user-input)
---

# QMA v2 architecture: adversarial review

## Intent (as reviewed)

QMA v2 puts one Python package between `qmx-control` and two agent engines (Claude Agent SDK, OpenAI Agents SDK).
It claims five things. Approvals survive a restart on both engines. One policy point holds for every tool call. The money barrier is structural.
`control.db` has a single writer. And it says a seven-slice plan lands 81 WED requirements by Wednesday 2026-10-14.
I assume the builders are agents who read only the file they open, and that one non-technical operator runs the result on Windows 11.

Severity key. **BLOCKER** means unsafe or not shippable as written. **MAJOR** means it will fail in normal use or force an implementer to guess. **MINOR** means fix it cheaply now.

---

## A. Approvals and the door split

### 1. BLOCKER: "REST-only" is not a boundary. Every agent with a shell can approve itself
- **Claim.** L124-127 and L643: the approval answer route is "REST-only (G1): never exported as an MCP tool". L424 adds that it "refuses principal != operator (Y08)".
- **Why it fails.**
  - On `rebuild/base`, REST, MCP-over-HTTP and the sign door all take the **same bearer token** (`qmx_control/server.py:93-117` `BearerGate`, and `:178-196` `authenticate`).
  - That token lives in Windows Credential Manager (`local_token()`, `server.py:84-90`), under the same Windows user that runs every agent.
  - So the agent tools below can read the token and call the route:
    - Claude's `Bash`. Research 19 line 35: the Bash sandbox is **off on native Windows**.
    - The OpenAI base-kit `shell` and `qmx_python` (L332).
    - Any mini app process.
  - One line does it: `python -c "import keyring; print(keyring.get_password('qmx/control-token','control-token'))"`. A `curl -X POST /api/approvals/{id}` follows.
  - `by=Principal.operator` is hard-coded in the route handler (L127), so the Y08 check compares a constant with itself. It authenticates nothing.
  - The same door is open through MCP without a shell:
    - `settings_put` is an `OPERATIONS` row (`server.py:76`), so it is exported as an MCP tool.
    - The always-ask list is "a settings row" (L393, L709). An agent can empty it.
    - `sessions_append` (`server.py:79`) lets an agent write any block, including a forged `permission` or `needs_you` card, into any session.
- **Fix.**
  1. Give each principal its own credential. The operator UI gets a token that never enters an agent process. Agent MCP gets a separate token whose scope excludes the four doors. Mini apps get a third token scoped to `delegate`/`job_*`.
  2. Bind the answer route to an operator-only credential. A per-launch secret held in UI memory, or Windows Hello/DPAPI-protected, is better than keyring under the same user.
  3. Remove `settings_put` for the `approvals`, `deny` and `accounts` sections from `OPERATIONS`. Make `sessions_append` refuse `permission`, `needs_you` and `user` kinds from agent principals.
  4. Turn the L643 test into a negative test: "an agent shell holding the agent token gets 403 on all four doors".

### 2. BLOCKER: the money barrier rests on environment scrubbing, and Credential Manager is not scrubbed
- **Claim.** L17 and L439: "no broker credential is in any agent's environment, so Claude's `Bash` cannot reach an order door either. The barrier is structural."
- **Why it fails.**
  - The cTrader Open API credentials sit in Windows Credential Manager under `qmx/*` labels (operator memory, "broker credentials location").
  - Any same-user process can read them through `keyring`/`CredRead`: Claude `Bash`, OpenAI `shell`, `qmx_python`, an agent-written app.
  - With the credentials and the public cTrader Open API, a model can write its own order client. "No order tool in the registry" does nothing against a model that writes one.
  - `decide_builtin` "deny patterns" (L400, L440) are string matches on Bash commands. `python -c`, base64 or a script file defeats them.
- **Fix.**
  1. Move broker credentials out of the agent user's reach. Use a separate Windows account or a service (the node or the broker process) that holds them. QMX calls `propose_order` over a local socket that only accepts proposals.
  2. Alternatively, run agent shells under a restricted token or a separate low-privilege local user. In that case, document that the Job Object alone does not isolate credentials.
  3. Until either exists, NFR-015 must say "barrier against tool calls, not against arbitrary code". FR-102's acceptance test must include "Bash reads keyring: refused or empty".

### 3. BLOCKER: `defer`'s single-call limit is the common case, not the edge case, and the fallback has no resume path
- **Claim.**
  - L106: the single-call limit "is acceptable because QMA already serialises write and money tools (FR-109)".
  - L145: a multi-call turn is "the one case `defer` does not cover".
  - L573: "On timeout the row stays `pending`, the turn is interrupted, and the restart path above applies on the next answer".
- **Why it fails.**
  - Docs: "'defer' only works when Claude makes a single tool call in the turn. If Claude makes several tool calls at once, 'defer' is ignored with a warning and the tool proceeds through the normal permission flow" (https://code.claude.com/docs/en/hooks, "Defer a tool call for later").
  - Serialising tool **execution** (FR-109) does not stop the model **emitting** several `tool_use` blocks in one message. Claude does that routinely, for example a read followed by a write, or three parallel `Agent` calls.
  - `ClaudeAgentOptions` (0.2.144) has no `disable_parallel_tool_use` switch. OpenAI has `ModelSettings.parallel_tool_calls` (`docs/running_agents.md:194`); Claude does not.
  - FR-109 is **NEXT** in PRD.md:336, not WED. The justification cites a requirement nobody is building.
  - "The restart path above applies" is false for this case. The restart path works because `defer` preserves **one** pending `tool_use` that the hook re-fires on resume.
    - An interrupted multi-call turn preserves nothing that re-fires. The model re-plans on resume, often with different arguments.
    - That gives a new `call_seq`, so a new effect key (see #6), so a new approval.
    - The operator's later "approve" on the old row resolves nothing. It is an orphan that looks answered.
  - Docs (agent-sdk/user-input): "The callback can stay pending indefinitely." So P3b's "record the bound where it stops" (L728) probes a limit that does not exist on the SDK side. The real limits are:
    - QMA's own timeout;
    - the 600 s hook-callback default (research 19 §4);
    - the `Watchdog` (L323). This one will kill a session that sits on a live Future past "N min" unless the watchdog knows about approvals.
- **Fix.**
  1. Treat the live Future as the **primary** Claude path while the host is up. Keep it unbounded and make the watchdog approval-aware. Use `defer` as a bonus when the turn has one call.
  2. On host restart with a live-Future approval outstanding, mark the row `expired_by_restart`, not `pending`. The UI says "the agent will re-ask". Never show an answerable row that cannot resume.
  3. Add a system-prompt rule ("call one write tool per message"). Add a PreToolUse rule: when the hook sees a second sibling call to a write/external tool in the same assistant message, it denies that call with "issue it alone" (the hook input carries `tool_use_id`, and siblings show up in the transcript).
  4. Rewrite L106 and L145 so they do not cite FR-109.

### 4. MAJOR: `defer` is untested in the exact shapes QMA uses (persistent client, sub-agents, changed tools)
- **Claim.** L318-319 and L571: `ClaudeAdapter` holds "one `ClaudeSDKClient` per session" and resumes with `resume=ref.native_token`, and the hook "fires again for the same call".
- **Why it fails.**
  - The docs describe `defer` for `claude -p` runs that **exit** with `stop_reason: "tool_deferred"`.
    - The 0.2.144 SDK launches `--output-format stream-json --input-format stream-json` without `-p` (`_internal/transport/subprocess_cli.py:566,783`).
    - Whether a long-lived `ClaudeSDKClient` counts as "non-interactive" is not documented.
    - Whether it exits or idles after `tool_deferred` is also not documented. If it idles, `SessionCap` holds 1 GB per parked approval.
  - **Sub-agents.** Tool hooks from parallel Task sub-agents "interleave over the same control channel" (`types.py:293-305`, `agent_id` field). A `defer` returned for a call **inside** a sub-agent is undocumented. The resume model ("resume can only re-run one tool") talks about the main transcript only.
  - **Changed tools.** If a plugin or tool list changes before the answer, the resumed process exits `tool_deferred_unavailable` (same docs page). L224-225 and L590 say a spec/plugin-hash mismatch **refuses resume** and starts a fresh session. Either way the approved call is lost, and nothing marks the row.
  - **Permission mode.** Resuming with `-p` "doesn't restore any other stored permission mode". The adapter must pass identical options, and nothing in `_options` says so.
- **Fix.**
  1. Extend P3 with three more cases: (c) `ClaudeSDKClient` streaming mode, observing process state after `tool_deferred`; (d) a `defer` from inside a sub-agent; (e) resume after a tool-list change, expecting `tool_deferred_unavailable`.
  2. Add an `ApprovalStatus.orphaned` value. Map `tool_deferred_unavailable` and hash-mismatch onto it, and show it as an honest card.
  3. In `PreToolUse`, never `defer` when `agent_id` is present. Use the live path there.

### 5. MAJOR: plugin `PermissionRequest` hooks can approve in the fallback path
- **Claim.** L368: the lint ensures "hooks cannot relax deny-list". L352: "QMX hook kinds run on both engines".
- **Why it fails.**
  - `plugins=[{"type":"local",...}]` (L311) loads the plugin's `hooks/hooks.json` natively. These are shell commands that run as the operator's user.
  - The hooks docs, under PermissionRequest: "For a call that reaches a --permission-prompt-tool or the Agent SDK's canUseTool callback, the hooks run alongside your host, and whichever decides first applies."
  - So in exactly the multi-call fallback from #3, a plugin hook returning `allow` beats the `can_use_tool` Future. No approval row is consumed. Nothing reaches the operator.
  - Agent-written plugins arrive through `PluginLoader.install` (L370). Self-improvement drafts plugin versions (L601).
  - The lint only reads "deny-list" relaxations. A `PermissionRequest` hook, or any command hook (arbitrary code on every tool call), is not a deny-list relaxation.
- **Fix.**
  1. The lint refuses `PermissionRequest` and `PreToolUse` command hooks in any plugin whose trust is not `first_party`.
  2. QMA strips `hooks/hooks.json` when compiling for non-first-party plugins, and expresses QMX hook kinds only through `qma.toml`.
  3. Add a test: a fixture plugin with a PermissionRequest allow hook, a multi-call turn, and the write tool does not run.

---

## B. Effects, idempotency, crash recovery

### 6. MAJOR: effect keys come from a host counter, so they are not stable across restarts or re-plans
- **Claim.** L432 says `mint(ctx)` gives `"run:node:seq"`, "host-minted (X5), stable across resumes". L235: `call_seq` is on `CallContext`.
- **Why it fails.**
  - `call_seq` is a host-side counter. After a restart the counter state is gone unless it is rebuilt from somewhere, and the doc does not say from where.
  - The two re-execution paths both re-enter the invoker:
    - On OpenAI, `RunState.from_json` re-enters the invoker for the approved call.
    - On Claude, the resume re-fires the hook.
  - Neither path knows the old `seq`, so the "find the approved row by effect key" lookup (L571) misses. The hook defers again, which loops.
  - For copilot turns `node` is `None`, and the resumed turn is a **new run id** (approve resumes "the session", L298). So every key changes.
  - L593 relies on "the truncated-reply guard" for mid-tool crashes. That guard is FR-109, which is **NEXT**. Nothing on the WED path stops a re-planned duplicate external write after a crash in a copilot turn.
- **Fix.**
  1. Derive the key from engine-native ids: `claude:{session_id}:{tool_use_id}` (the PreToolUse input carries `tool_use_id`) and `openai:{session}:{call_id}` (from `ToolApprovalItem` / `RunState`).
  2. Add a second guard keyed on `(session_id, tool, args_sha256)` inside a time window for `unkeyed`/`irreversible` tools. It raises `outcome_unknown` instead of running.
  3. Pull the truncated-reply guard (only the "tool_intent without tool_result" check) into slice 1 as WED.
  4. Say how the key reaches FastMCP domain tools: an MCP `_meta` field, never a model argument.

### 7. MAJOR: OpenAI parked state is stored per approval row, so two answers run the same tool twice
- **Claim.** L224 and L420: `parked_state_ref` lives on `SessionRef` **and** `engine_state_ref` on each `ApprovalRow`. L571: each answer calls `Engine.approve`, which runs `RunState.from_json → approve(item) → run_streamed`.
- **Why it fails.**
  - One OpenAI run can pause with several `interruptions` (`docs/human_in_the_loop.md:53-61`, including nested `as_tool` approvals).
  - Answer approval A and the run resumes. Approval B pauses it again with a **new** state blob. Row B still points at the **old** blob.
  - Answering B then reloads the old state, which re-executes A.
  - Two answers arriving within the group-commit window cause two concurrent resumes of one session.
- **Fix.**
  1. Keep one `latest_state_ref` on the session only, with a per-session resume lock (a CAS on a `session.resume_epoch` column).
  2. `answer` records the decision. A single resumer applies **all** decided items in the latest state and resumes once.
  3. Answers arriving during a resume queue up for the next pause.

### 8. MAJOR: "node_runs row + checkpoint in one Write" is impossible across two files
- **Claim.** L514 and L577: "node_runs row + checkpoint in one `Write`". L612: checkpoints live in `checkpoints.db`, which has its own writer.
- **Why it fails.**
  - `node_runs` is in `control.db` (`work` rows, L611). Two files with two writer tasks make two transactions.
  - Even with `ATTACH`, SQLite in WAL mode is atomic only per file. A crash during COMMIT can apply one file and not the other (https://www.sqlite.org/lang_attach.html).
  - Resume (L591) then sees "node done, no checkpoint" or "checkpoint, node running". The doc defines neither case.
- **Fix.**
  1. Keep node checkpoints in `control.db` (prune them there).
  2. Or define the order: checkpoint first, then the node_runs `done` row; on resume, `done` without a checkpoint means re-run under the effects ledger. Write that rule into `Runner.resume`.

### 9. MAJOR: "every tool call goes through `ToolInvoker.invoke`" is false on both engines
- **Claim.** L17: every tool call "from either engine goes through one function, `ToolInvoker.invoke`".
- **Why it fails.**
  - **Claude built-ins** (`Bash`/`Write`/`Edit`/`WebFetch`) only get `decide_builtin`. The doc itself says so at L441, which contradicts L17.
  - **Plugin `.mcp.json` servers** are loaded natively by the CLI (L311 `**agent.mcp`, L344). They get the PreToolUse `decide` only. Effects intent/settle, journal `tool_result`, receipts, timeout and size cap never run.
  - On OpenAI, "plugin MCP" (L332) is passed as SDK MCP servers. `require_approval` exists for those, but the effects ledger does not wrap them.
  - **Tool names.** On Claude, SDK-server tools arrive at PreToolUse as `mcp__qmx__lab_backtest_run`. The deny-list and always-ask list are keyed on bare names (`apps_publish`, L353). One literal string match and the deny-list misses every Claude MCP call.
- **Fix.**
  1. Rewrite L17 to state the real coverage.
  2. Route all non-first-party MCP servers through the FastMCP proxy `ToolDef` (the D2 split), so that `invoke` really wraps them. Forbid `.mcp.json` in plugins unless they are first-party.
  3. Add `normalise_tool_name(engine, raw)` in `qma.types` with a test that every deny-list entry matches its `mcp__*__` form.

---

## C. Store and SQLite

### 10. MAJOR: the single-writer design has holes on Windows (second processes, PID lock, writer thread, batch failures)
- **Claim.** L254-258, L623-625: one writer task, group commit, a PID lock file, `integrity_check` before every backup.
- **Why it fails.**
  - **Second processes already exist.**
    - `qmx-control weekly-backup` builds a fresh `ControlService(home)` in its own process (`__main__.py`). Its constructor runs `PRAGMA journal_mode=WAL` and schema DDL (`service.py:120`). That is a write.
    - Either the PID lock refuses the scheduled backup, or the backup becomes a second writer.
    - `qmx-tools` imports `qmx_control` for `DomainContext` (L659, L664). If any domain tool touches `control.db`, the stdio server is another writer process.
  - **PID lock files on Windows go stale after a crash**, and PIDs are reused. The host refuses to start, or wrongly starts. The operator cannot debug either.
    - "Multiple windows" makes this real: he double-clicks the launcher twice, or `start` races `serve`.
  - **"Writer task."** Python `sqlite3` is blocking. An agent reading "one writer task" (L256) will write an asyncio task that calls `execute` on the loop. That stalls SSE, `/live` and all 40 OpenAI agents during every commit and every `integrity_check`.
  - **Group commit** has no failure semantics. One bad `Write` in a 100 ms batch rolls back everyone's approvals and blocks.
  - **`integrity_check`** on a growing `control.db` before backup takes seconds to minutes on the writer connection.
- **Fix.**
  1. The writer is a dedicated thread with a queue. Each `Write` runs in a `SAVEPOINT` inside the batch transaction, so a failure rolls back only that write and fails only its awaiter.
  2. Replace the PID file with an OS lock held for the process lifetime (`msvcrt.locking` / `portalocker` on `control.db.lock`). Windows releases it on process death.
  3. `weekly-backup` becomes a request to the running host (REST). When no host runs, it opens read-only and uses `Connection.backup` with no DDL.
  4. Run `PRAGMA quick_check` on a read-only connection before backup. Run the full `integrity_check` only at startup.
  5. Audit `qmx-tools` for `control.db` access in slice 0.

### 11. MINOR: the SSE tail and P4 measure the wrong thing
- **Claim.** L636: the tail "reads through `Store.read` off the loop, not a 50 ms sync poll". L729: P4 uses "8 SSE readers".
- **Why it fails.**
  - The doc never says what wakes the tail. Today's code is a 50 ms sleep loop per stream (`service.py:187-198`). Moving that loop into a read pool still polls: 7 topics × N tabs × 20 Hz.
  - P4's 8 readers do not match a real UI. One UI opens a stream per topic plus `/live`, he may have two windows, and the phone comes later.
- **Fix.** The writer thread signals an `asyncio.Condition` per topic after commit (same process). Readers wait on it and then read. P4 runs with 2 windows × 8 topics + 40 `/live`.

---

## D. Router, usage, model switch

### 12. MAJOR: "remaining usage" cannot be measured for subscriptions, so sticky routing herds sessions onto one plan
- **Claim.** L458 ranks by "remaining usage desc above reserve (FR-041)". L466: "A session keeps its pick for life."
- **Why it fails.**
  - Neither the Max plan nor SIWC exposes a remaining-quota API. The Claude SDK gives `RateLimitEvent`s and a `total_cost_usd` estimate (research 19 §usage).
    - So `Ledger.remaining` for the two most important rows is a guess.
    - With capability ranked first (FR-041), every hard role picks Opus on Max.
  - Forty sticky sessions on one 5-hour window hit the limit together. FR-029 failover is NEXT, so they all stall mid-task at once.
  - **Missing reports.** A watchdog-killed or hung Claude turn (L323) emits no `ResultMessage`, so the ledger records zero for the heaviest turns.
    - "latest result, never summed" (L564) is ambiguous between per-turn and per-session totals. One implementer double-counts and another under-counts.
- **Fix.**
  1. Define usage per turn: sum `AssistantMessage.usage` deduped by message id as `provisional`, and replace it with the `ResultMessage` totals when they arrive.
  2. Mark a killed turn `cost_source="estimated"`.
  3. For subscription rows, rank by recent consumption against a rolling window the operator sets (for example "Max: about N Opus turns per 5 h"), plus `RateLimitEvent` utilisation.
  4. Admission control: cap concurrent sessions per subscription row (a `max_concurrent` column) so stickiness cannot herd.

### 13. MINOR: model pinning contradicts itself
- **Claim.**
  - A-07 (L686): "A node's model is part of the graph version; changing it is a new version."
  - Also A-07: "The chain resolves at node start" through global → app → workflow → node.
  - K-11 / FR-099: the operator may switch models.
- **Why it fails.** A global or app override changes what a pinned version runs, and a crash resume of node 7 can land on a different model than the first attempt. Reproducibility and the version-hash gate (#16) both assume the model is pinned.
- **Fix.** Record the resolved `(account, model)` on the `node_runs` row at first attempt, and reuse it on resume. A different resolution on resume becomes a visible warning, not a silent change.

---

## E. Plugins and parity

### 14. MAJOR: on the OpenAI engine most of a Claude plugin silently does nothing
- **Claim.** L16: "QMA's loader turns the same folder into OpenAI SDK objects". L761: "the lint reads one declared baseline list".
- **Why it fails.** These items have no OpenAI mapping in §2.4 and would be dropped without an error:
  - `hooks/hooks.json` (A-03 admits it);
  - agent frontmatter `tools`, `model`, `permissionMode`, `hooks`;
  - skill frontmatter `allowed-tools`;
  - progressive skill loading (no "skill" tool is designed for OpenAI);
  - `commands/`, output styles, `${CLAUDE_PLUGIN_ROOT}` expansion in `.mcp.json`;
  - every Claude built-in a skill names (`Bash`, `Read`, `Grep`, `Glob`, `WebFetch`, `WebSearch`, `TodoWrite`, `Agent`);
  - auto memory (FR-091).

  Tool names also differ: a skill that says "call `mcp__qmx__lab_backtest_run`" is right on Claude and wrong on OpenAI, and the reverse. The L0-L3 byte-stable prompt is per engine, but the skills are shared files. A "declared baseline list" catches only what someone remembered to declare.
- **Fix.**
  1. The loader emits a per-plugin **parity report**: each file and frontmatter key is classified as mapped, emulated or dropped, from a closed table in `qma/plugins/compile.py`.
  2. An unknown key fails the lint instead of passing it through.
  3. Skills refer to tools by QMX bare name inside a `{{tool:lab_backtest_run}}` token that `render` expands per engine.
  4. Design the OpenAI "load skill" function tool. It is about 60 lines, and nothing works on OpenAI without it.

---

## F. Graph runner

### 15. MAJOR: agent nodes, approvals, timeouts and unattended mode collide
- **Claim.**
  - L519: `_agent_node` runs `engine.start` per attempt.
  - L504: `timeout_s` and `retries` are per node.
  - L603: "Unattended runs deny by default."
- **Why it fails.**
  - An agent node whose agent needs a write approval:
    - in an unattended (scheduled or remote) run, it is denied, so the node can never succeed;
    - in an attended run, it parks, and `timeout_s` measures wall time **including** the wait, then kills the node while the operator reads.
  - A crash during a 3-hour agent node: nothing inside the node is checkpointed. The resume starts a **new attempt**, a new session, and new effect keys (#6). The node's earlier external effects can run again.
  - `adopt_orphans` (L487) followed by automatic resume ("restart banner lists resumed", L589) gives a crash loop when a node crashes the host (OOM from six Claude sessions, a native-library fault). The operator sees the app die repeatedly.
- **Fix.**
  1. The node clock pauses while the run is `waiting_approval`.
  2. Unattended policy is per tool class: deny `external`, allow `write` inside the node's declared `write_scope`.
  3. An agent node checkpoints its `SessionRef` and resumes the **same** session first, before starting a new attempt.
  4. Add `resume_attempts` on the run row: after 2 crash-resumes the run goes to `interrupted` and waits for the operator.

### 16. MINOR: the gate's version binding contradicts itself and is too coarse
- **Claim.** L579: "An edit to the definition creates a new version; the running run keeps its hash and the gate asks again on the new version."
- **Why it fails.**
  - A run pinned to v1 never meets v2, so "asks again" can only apply to new runs. As written, an implementer will re-ask inside the old run.
  - `content_sha256` of the whole graph re-asks on a typo fix in an unrelated node's description.
  - The gate does not bind to what is being approved: the upstream node outputs.
- **Fix.** `revision_hash = sha256(gate node definition + upstream subgraph definition)`. `content_hash` covers the gate's **input values**. State that running runs never re-ask because of an edit.

---

## G. Remote placement

### 17. BLOCKER: idle teardown runs on the laptop, so a closed laptop means a machine that never stops
- **Claim.**
  - L555: `Placement.idle_sweep`, "teardown after N idle minutes".
  - L22: remote runs with the laptop off.
  - USER-JOURNEYS L466 marks idle teardown **WED** and names "surprise bills" as the main risk.
- **Why it fails.**
  - `idle_sweep` is a method on the laptop host. J09 is "laptop closed" (WED, USER-JOURNEYS L46). Nobody sweeps.
  - A remote run that parks on an approval or a gate is idle by any CPU measure, yet has nobody to answer it: G9 says remote cannot call the laptop, and the bucket mailbox is NEXT. It either burns money or is torn down mid-park, and the OpenAI `RunState` blob never got flushed.
- **Fix.**
  1. Every bundle carries `max_lifetime` and `idle_after`. `TurnHost.headless` enforces them itself:
     - it flushes the journal and state blobs to the bucket;
     - it writes `stopped_reason`;
     - it calls the provider's self-terminate (or is provisioned with a provider-side TTL where one exists, as on Modal and E2B).
  2. A remote run that reaches an approval saves its state and exits. It does not wait.
  3. The laptop's sweep is only a backstop.

### 18. MAJOR: remote credentials, approvals on return, and missed runs are not designed
- **Claim.** L22 and L139: remote runs use the OpenAI engine on key providers through `TurnHost.headless`. L553: the fetch imports "approvals ... as new rows".
- **Why it fails.**
  - **Keys.** Key-provider API keys must reach the rented box, and the doc never says how. The obvious implementation (env in the bundle) puts them in the bucket, which breaks FR-046's "no key in logs".
  - **Approvals.** Imported approval rows are answerable on the laptop, but no path carries the answer back to a stopped worker. They become orphans.
  - **Missed schedules.** With the scheduler NEXT and `watch` in slice 4, a `watch` node on a closed laptop just stops (USER-JOURNEYS L475 confirms the gap).
- **Fix.**
  1. Keys go by provider secret store (Modal secrets, E2B env at create), injected by `setup_verify` from Credential Manager over the provider API. Never through the bundle or the bucket.
  2. "Answer remote approval" equals "relaunch the bundle from its saved state with the decision attached" (resume with a decision file).
  3. Remote `watch` is refused for WED. `Placement` says so before launch.

### 19. MAJOR: Claude session files are tied to the cwd and the home, and orphan CLIs survive a host crash
- **Claim.** L313-319 and L614: transcripts live at `<home>/claude/projects/**.jsonl`; resume is by `native_token`; the home can move by setting (L618).
- **Why it fails.**
  - Claude stores a transcript under a project key that defaults to the **sanitised cwd** (`types.py:1500-1504`). `SessionRef` stores no cwd. Resuming from a different cwd finds nothing.
  - Changing the home setting (F20) breaks every parked session.
  - `setting_sources=[]` means `cleanupPeriodDays` keeps its 30-day default, so a parked approval older than 30 days vanishes (hooks docs).
  - On Windows a child does not die with its parent unless it sits in a Job Object. Job Objects are specified for apps (L660) only.
    - After a host crash, orphaned ~1 GB `claude` processes keep running and keep appending to the transcript.
    - The resumed session then has a second writer on the same JSONL, and `SessionCap` counts RAM that the orphans hold.
- **Fix.**
  1. Add `cwd` to `SessionRef` (a fixed `<home>/work/<session_id>`).
  2. Pass `settings={"cleanupPeriodDays": 3650}` explicitly.
  3. Put every Claude CLI child in a kill-on-close Job Object owned by the host (in `platform.py`).
  4. On startup, kill any `claude` process whose `CLAUDE_CONFIG_DIR` is the QMX home before `adopt_orphans`.

---

## H. Security beyond the doors

### 20. MAJOR: prompt injection has all three ingredients in the copilot
- **Claim.** L603: "Readers of downloaded content get read-only tool sets (NFR-017)."
- **Why it fails.**
  - The copilot itself has `WebFetch`/`WebSearch` (Claude built-ins), and on OpenAI it has `web_fetch` (L332).
  - It also reads news and video transcripts, and holds write tools plus Library and broker-read access.
  - That is the lethal trifecta in one context: private data, untrusted text, and an exfiltration channel (a GET with a query string to an attacker URL).
  - NFR-017 protects only sessions labelled "reader". Nothing forces downloaded content into a reader.
- **Fix.**
  1. Remove raw fetch from copilot and worker tool sets. Fetch only through `delegate(role="reader")`, which returns schema-validated JSON with quoted text fenced as data.
  2. Taint a session that has seen untrusted text: every `external` effect after taint becomes always-ask for the rest of the session.
  3. Put an egress allowlist on `web_fetch` (domains from settings).

### 21. MAJOR: agent-written apps gain trust and credentials too easily
- **Claim.** L660: trust is "host-assigned from an approval record (F1, F2)". L181: `QmaClient` for mini apps.
- **Why it fails.**
  - A non-technical operator cannot review app code (operator profile), so the approval record is a rubber stamp. Nothing narrows what the approved app can then do.
  - `QmaClient` auth is unspecified. If it uses the control bearer, an app can call every `OPERATIONS` row and, per #1, the doors.
  - `apps_call` returns app output straight into agent context, which is a second injection channel.
- **Fix.**
  1. `QmaClient` gets a per-app token scoped to `delegate`, `job_status` and `job_result`, with a per-app budget.
  2. Approved apps run with `unattended=True` policy.
  3. The approval card shows a mechanical capability diff (network hosts, files, tools), not code.

### 22. MINOR: secrets reach parked state, transcripts and the bucket
- **Claim.** L266: "Secrets scrubbed at write" (journal). L603: a value-pattern scrubber on user blocks.
- **Why it fails.**
  - Serialised `RunState` "includes your app context ... avoid placing secrets there" (`docs/human_in_the_loop.md:222`). If `CallContext` or the adapter context carries a `RouterPick` (`key: SecretStr`, L453), the key lands in `blobs/`. Remote runs flush the run folder to the bucket.
  - Tool outputs in OpenAI `SQLiteSession` rows and in Claude transcripts are not scrubbed at all.
  - Claude OTEL with tool details enabled exports tool parameters.
- **Fix.**
  1. Add a type-level rule: `RouterPick` never enters any SDK context object. Add a test that greps a serialised `RunState` for the test key.
  2. The bucket flush excludes `openai/*.sqlite` and Claude transcripts unless encrypted.
  3. Set `OTEL_LOG_TOOL_DETAILS` explicitly to off.

---

## I. Packaging and slices

### 23. MAJOR: the name `qma` is already taken on `rebuild/base`
- **Claim.** L13 and L167: "one Python package, `qma`" with `qma/types.py`, `qma/plugins/` and so on.
- **Why it fails.**
  - `rebuild/base` already ships `qma` as an implicit namespace across three distributions:
    - `qma-core/src/qma/core`;
    - `qma-daemon/src/qma/daemon`;
    - `qma-wire/src/qma/wire`.
  - None has a top-level `qma/__init__.py`.
  - These files still import `qma.core`/`qma.daemon`:
    - `qmb/tests/test_operator_study_cli.py`;
    - `qmn/examples/spot_paper_journey.py`;
    - `qa/integration/test_qma_*.py`;
    - the five `qmx-agents/plugins/*/daemon/plugin.py`.
  - The PRD keeps the `qma.daemon` anchor in QMB "until the QMB review" (PRD.md:91).
  - A regular `qma/__init__.py` shadows the namespace and breaks those imports. Without `__init__`, the import-linter contract "`qma` imports no `qmx_*`" also covers the old daemon code.
- **Fix.** Name the package `qma2` or `qmx_agent` for release 1, or schedule the deletion of `qma-core`/`qma-daemon`/`qma-wire` and the QMB anchor into slice 0 explicitly, with those tests edited in the same PR.

### 24. MAJOR: the slice plan is not realistic for Wednesday; slice 4 is the underestimate
- **Claim.** L736-750 and L766: "Slice 1 must be green by Tuesday noon"; about 3,600 lines in total.
- **Why it fails.**
  - Today is Monday 2026-10-12.
  - **Slice 0** quietly includes "`Store` single writer wired under `qmx-control`'s existing tables". That means rerouting every `_connect`, `Library.connect`, `RunIndex.record`, the maintenance loop and the backup (see #10). On its own that is a day.
  - **Slice 4** holds:
    - a new runner with 12 node kinds (including `watch` and `command`), checkpoints, gates, joins and loops;
    - the agent node with a checker;
    - `Broker` leases, `delegate`, `job_*` and `adopt_orphans`;
    - the full P10 test list passing.

    That is easily 1,500 of the 3,600 lines, and it starts only after slice 2 and P4.
  - **Slice 5** needs a rented-provider account, an image and the self-terminate work from #17, plus a live copilot rebuild of an app.
  - **The critical path** is serial:
    - P3 and P5 (on his PC, run by a non-technical operator);
    - then slice 2;
    - then P4;
    - then slice 4;
    - then slice 5;
    - then slice 6.
  - Any probe failure moves every slice after it.
  - L766's fallback (an in-memory `Store`) sacrifices FR-104 and FR-059, the two headline durability requirements.
- **Fix.**
  1. Cut WED slice 4 to `python`, `tool`, `agent`, `parallel`, `join` and `human_gate`. Move `watch`, `command`, `loop` and `subworkflow` to NEXT; A-08 already allows `watch` as a template.
  2. Cut slice 5 to "remote run of a code-only workflow with self-terminate". The Macro daily bias rebuild becomes a demo-day stretch.
  3. Write probe scripts that print PASS/FAIL plus one plain sentence, so the operator does not interpret logs.
  4. Name the critical path in §8.

### 25. MINOR: `SessionCap` formula and smaller Windows details
- **Claim.** L321: cap = "(free RAM − 4 GB) / 1 GB, default 6". L743: "survives `kill -9`".
- **Why it fails.**
  - On Windows, "free" is not "available". With Chrome and the UI open on a 16 GB machine, the cap can be 0 and every Claude session is refused at random.
  - The cap is re-read on each acquire, so it flaps.
  - There is no `kill -9` on Windows; the test must use `taskkill /F`.
- **Fix.** Use `psutil.virtual_memory().available`, a floor of 2 and a ceiling from settings, with hysteresis. Write the slice tests with Windows commands.

---

## J. Under-specified: an implementer will guess here

1. **Effect key source.** Counter vs engine call id. See #6.
2. **Who resumes after a crash.** Automatic or one click, and with what attempt limit. See #15.
3. **Where an approved Claude call resumes.** In which `run_id`, and whether the resumed turn is a new `work` row.
4. **`allow_session` / `remember` scope.** Tool name only, tool plus an args pattern, or per plugin. Where they are stored, and how they are revoked (G14 sets only the limits).
5. **`expires_at`.** Who sets it, its default, and what an expired gate does to its graph run.
6. **Writer concurrency.** Thread vs task, batch failure isolation, back-pressure when the queue is long. See #10.
7. **`QmaClient` authentication and the token model** for the UI, agents and apps. See #1 and #21.
8. **Claude session `cwd`** and the transcript location contract. See #19.
9. **Usage accounting units** per turn per engine, and how a killed turn is recorded. See #12.
10. **Parity table** for plugin keys on OpenAI. See #14.
11. **Remote credential delivery** and the remote approval round-trip. See #18.
12. **Handler timeouts.** How a 60 s `timeout_s` cancels a synchronous domain function. It cannot; the doc must say "proxy calls only" or "run in a killable subprocess".
13. **Tool block "updated in place"** (L639) vs append-only events with `Last-Event-ID` replay. Is an update a new event that carries the full block?

---

## Verdict

**Not ready to build as written. Fix four things first and the architecture can stand.**

The skeleton is sound: two adapters under a deep facade, one policy module, state rows plus a JSONL evidence journal, and a single writer. The rejection of a journal table is right, and so is the subtraction-first slice 0. The safety story claims more than the code can deliver:
- The approval door and the money barrier both assume that agents cannot read what the operator's Windows user can read. They can (#1, #2).
- The `defer` mechanism the synthesis leans on covers the minority case (#3, #4).
- Idempotency keys are not stable across the exact restarts they exist for (#6, #7).

The schedule assumes slice 4 and slice 5 fit into Tuesday afternoon. They do not (#24). The package name collides with live code (#23).

### The five changes that matter most

1. **Separate principals for real (#1, #2, #21).** The operator door gets a credential no agent process can read. Agents and apps get scoped tokens. Broker credentials move out of the agent user's Credential Manager.
2. **Make the live Claude approval primary and `defer` opportunistic (#3, #4, #5).** Keep the Future unbounded while the host lives. Mark live approvals `expired_by_restart` on crash. Refuse sibling write calls in one message. Strip non-first-party permission hooks. Extend P3.
3. **Key effects on engine call ids plus an args-hash guard, and pull the truncated-reply check into WED (#6, #7, #8).** Keep one latest parked state per session with a resume lock. Keep checkpoints in `control.db` or write the cross-file order rule.
4. **Make remote machines self-terminating and remote runs exit-on-approval (#17, #18).** The laptop sweep is a backstop, not the mechanism.
5. **Re-cut the WED scope and fix the name (#23, #24).** Rename or retire the existing `qma` namespace in slice 0, trim slice 4's node kinds and slice 5's demo, and name the critical path.
