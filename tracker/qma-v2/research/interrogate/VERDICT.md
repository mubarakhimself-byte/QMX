# Interrogate verdict: QMA v2 harness design

Lead reviewer: the planning session (Opus 5.5), 2026-10-13. The findings are in `reviewer-A-opus.md` (A1-A28) and `reviewer-B-fable.md` (B1-B23). Every "Act on" item below is binding on the coding session through `HARNESS.md` Amendment A11.

## Intent

> QMX gets one agent harness ("qma2") whose floor is vanilla Claude Code and Codex. It runs on two engines with one QMX policy point, and money is read-only for agents. Sessions last days. A router works across his accounts. A usage page and a temporary browser console let him sign off. It plugs into today's qmx-control without adding writers to control.db, and ships as small PRs. The first PR proves one live Claude turn.

## Reviewers

- Reviewer A: Opus 5.5, 28 findings (3 critical).
- Reviewer B: Fable 5.1, 23 findings (2 critical).

## Act on

The findings group into six themes. Each theme is one design rule.

### V1. Agents cannot escalate or self-approve through QMX's own surfaces

Raised by A1, A2, A5, A6, B1 and B22. A5 and B1 are a consensus finding.

1. **The agent catalog is an explicit allow-list, not "every `who=ANY` row".** Ops that inject secrets or run code stay out of it:
   - `run_job`, `runs_start_remote`, `runs_resume`;
   - `apps_create`, `apps_update`, `apps_start`, `apps_publish`, `apps_restore`;
   - `settings_put`, `backup_*`;
   - `sessions_append`.
   
   `Op` gains a third audience, so the rows read `who=OPERATOR | CLIENT | AGENT`. The MCP export and the agent catalog are each derived from the `who` field.
2. **`money.classify` scans QMX-op arguments.** Any `OperatorSecretRef` label (for example `qmx/ctrader`) anywhere in a QMX-op argument is a `MoneyHit`.
3. **Thread ops called by an agent are confined.**
   - The new thread gets `origin=AGENT` and `parent=<caller thread>`.
   - Its mode is `min(caller mode, requested mode)`. The agent cannot choose the profile.
   - `send`, `steer`, `interrupt`, `fork` and `archive` work only on threads in the caller's lineage.
   - The type for this is `ChildThreadSpec`, which has no `profile` or `origin` field.
   - QMX never offers an ALLOW_ALWAYS rule for `mcp__qmx__threads_*`.
4. **Operator sessions are bound to an HMAC key held as an `OperatorSecretRef`,** not to a bare hash in harness.db. A forged row in the database does not verify. Pairing happens only over a local channel (stdin of `serve`, or a pipe restricted to the user), never through the client token.
5. **QMX's own state files count as protected money state.** Writes to `harness.db`, `control.db`, `~/.qmx/config/**` and `<cwd>/.qmx/**` from agent tools are a `MoneyHit`. This is a speed bump against deliberate code, and the doctor page says so. The real guarantee for these files is U10.
6. **Workspace trust.** Project `<cwd>/.qmx/` hooks and allow rules are ignored until the operator trusts that root, the same as vanilla Claude Code's trust prompt. Config reloads only between segments.

### V2. The Claude engine fails closed and cannot route around QMX policy

Raised by A3, A4, A7, B2, B6, B14 and B15. A3, B2 and B6 are a consensus finding.

1. **Mode mirroring.** `mirror()` sends only `plan` to the SDK. Every other mode is sent as `default`, and `policy.decide` owns the semantics of the modes. The pinned SDK's docstring says `can_use_tool` is skipped for calls that `acceptEdits` or `bypassPermissions` already permit.
2. **`_pre_tool_use` catches every exception and returns deny.** `_can_use_tool` denies any `tool_use_id` that has no matching QMX Pending entry, and emits `tool.finished(denied, source=LIMIT)`.
3. **The SDK hook-matcher timeout is set above QMX's total hook budget.** QMX command hooks run with a timeout that leaves margin under it. The numbers are recorded in U1.
4. **MCP servers are pinned.** QMX passes `strict_mcp_config=True`. The actor refuses `Started` if the engine's `tools` list contains any name the catalog does not know, as the old recipe did. This closes the hole where a repo `.mcp.json` claims the reserved `qmx` name.
5. **On the Claude engine, MCP tool descriptors are listed by QMX at segment start.** An unknown MCP tool name is denied, so the money check sees the same descriptors on both engines.
6. **Every input-changing step passes one `recheck_money(call)` before any Allow.** That covers PreToolUse, PermissionRequest and operator edits.
7. **The control-process `ANTHROPIC_*` check is deleted** from `accounts.claude_status`. The assertion inside `host_env` is the one that matters.

### V3. Grants, actor and link are correct under concurrency and crashes

Raised by A8, A9, A10, A15, A27, B3, B4, B5, B10 and B13. Three pairs are consensus: A8 with B5, A9 with B3, and A15 with B13.

1. **The CallOp grant is bound to `(name, canonical args digest)`.** Grants are consumed FIFO. The actor executes the op with the stored allowed input and ignores the host's args. Only qmx-tool calls enter the grant table.
2. **Ask handlers run as child tasks.** State changes (`_pending`, `_granted`, status) return to the actor as messages. `LoadItems` waits on an "items committed up to seq N" barrier. The harness docstring states this.
3. **On Pending, the host returns `ask` together with the hook-updated input,** so `can_use_tool` receives the input the approval stored.
4. **Projection is idempotent.** `items.block_seq` is set after `sessions_append` returns, and every block carries its item `source_key`. On open, QMX re-projects only items whose `block_seq IS NULL`. A Claude-segment export also reads the Claude JSONL.
5. **Link integrity.** After the dup, the host runs `os.dup2(2, 1)`, and every host child gets `stdin=DEVNULL` and piped stdout.
6. **Process order.** The supervisor creates the host, then assigns it to the Job Object, then writes `Spawn`. The kill check asserts that the killed host's CLI pid is gone.

### V4. Routing and usage tell the truth

Raised by A13, A14, A20, B11 and B17. A13 and B11 are a consensus finding.

1. **A model-family guard.** Claude and GPT models are never reached through an API key, including through OpenRouter (`anthropic/*`, `openai/*`). This applies in `router.pick`, `quote_switch` and the account model list, and it is tested.
2. **Lockout is per account,** not per actor. Limit snapshots expire at `resets_at`.
3. **Each background turn has a budget,** a token cap checked from the usage rows. The 50% cap is labelled best effort until `get_usage` is proven. U5 probes `get_usage` first.
4. **Usage rows are keyed on the result message's own id** (or session plus sequence), not on turn plus model. A U1 probe records whether `model_usage` is per query or cumulative.
5. **Probes the pinned SDK source already answers are dropped:**
   - `tool_use_id` is always present in `can_use_tool`;
   - `exclude_dynamic_sections` exists;
   - modes shadow `can_use_tool`.
   
   The FIFO correlation fallback is deleted.

### V5. Parity details the baseline depends on

Raised by A16, A18, A25, B8, B9, B12 and B21 with A26 (a consensus finding).

1. **Shell family.** On Windows the OpenAI kit ships both `Bash` (git-bash, when present) and `PowerShell`. Rule and hook matching treats them as one `shell` family, and `BUILTIN_EFFECTS` has rows for every kit name.
2. **The env allow-list is per OS.** The Windows set adds `SYSTEMDRIVE`, `PROGRAMFILES`, `PROGRAMDATA`, `ALLUSERSPROFILE`, `USERNAME`, `COMPUTERNAME`, `NUMBER_OF_PROCESSORS`, `PROCESSOR_ARCHITECTURE` and `PSMODULEPATH`.
3. **Reasoning items are stored verbatim** with `include=["reasoning.encrypted_content"]`. U4 and U8 include a two-turn tool-using replay.
4. **After `compacted` on Claude,** ProjectContext is re-sent as a reminder. MEMORY.md is dropped from ProjectContext on the Claude engine, which loads it natively. U6 adds a Claude-engine compaction check.
5. **WebFetch asks per domain and WebSearch asks,** as in vanilla Claude Code. They are not auto-allowed.
6. **`suggest_rule` offers exact-command rules** for interpreters (`python`, `node`, `pwsh`, `bash`, `sh` with `-c`, `-e` or `-Command`), never a prefix.
7. **Design text.** "Tool processes carry no keys" is true on the OpenAI engine. On the Claude engine the CLI's tools can read `claude-home/.credentials.json`, which is vanilla behaviour. `redact` exact-matches that file's token so it never lands in items, blocks, logs or exports.

### V6. The unit plan matches the design

Raised by A11, A12, A19, B16, B18 and B23. A11 with B16 and A12 are consensus findings.

1. **The plan is rewritten from `HARNESS.md`,** not from `candidate-1-opus/units.md`.
2. **The dependency graph is U0, then U1, then U1b, then U2 and the U4 core.**
   - U4's parity checks run after U2 and U3.
   - U4's key entry depends on the operator principal, either by moving pairing into U1b or by making U4 depend on U2.
   - `host/openai.py` has one owner per wave.
3. **U1's check proves the policy point.**
   - A Bash call is denied with the QMX reason.
   - A money-path Read is refused.
   - A hook-fired counter matches the tools seen.
   - The env check moves to U2, when Bash is allowed.
4. **Host capacity.** A full `max_live_hosts` raises `no_host_slot` and names the pinned threads. Approvals expire after a configurable window, and the console shows the wait time with an expire button.
5. **The qmx-tools stdio servers are refused in agent MCP config** until backlog B1 is fixed. Otherwise every host multiplies the writers on control.db.
6. **U2's keyring check includes a git-bash path spelling,** so the limit of the speed bump is on record.

## Consider

- **A17. Windows path aliases** (ADS, UNC, device paths, `subst`). Rejecting ADS, UNC and device forms outright is cheap, so do that. Full `GetFinalPathNameByHandle` resolution is worth it only if U2 finds a bypass. This is a speed-bump layer either way.
- **A23. Import edges put policy code in hosts.** Moving `AgentDef` and `McpServerDef` into `model` or `wire` and banning `qma2.policy` and `qma2.money` imports from `qma2.host` is a five-minute change that makes "hosts never decide" structural. Do it in U0.
- **A28. Smaller gaps.**
  - Idle reaping kills running background sub-agents, so reap only when no background child is alive.
  - `doctor` reports managed settings.
  - Fork-at-turn on Claude is not in H1, so U9 probes it.
  - `qmx_apps → qma2.money` must not pull the SDKs; host dependencies become an extra.

## Noted

- **A24.** Pairing needs a Harness verb. Fold it into V1.4.
- **A22 and B19, the `fastapi.sse` claim.** Both reviewers are right that `fastapi.sse` is real (`qmx_control/server.py:18`). Amendment A9 was wrong and is corrected.
- **A22 and B20, `.claude` vs `.qmx`.** Text contradictions. A4 wins, and call site 4 plus the sketch `config.py` are corrected by the builders.
- **A22, quote forgery.** `SwitchQuote` has no id, so quotes must be stored server-side and referenced by id. Folded into U5.

## Dismissed

None. Every finding traced to a concrete path in the sketch or the SDK source, so none was a hypothetical or a style preference. Two findings were downgraded from the reviewers' severity:
- A17 to Consider, because it extends a layer already labelled a speed bump.
- B17 to "simplify", because it removes work rather than finding a defect.

## Agreement map

- **Consensus.** Seven issues were found independently by both models:
  - thread-op escalation;
  - mode mirroring and fail-open;
  - CallOp binding;
  - actor deadlock;
  - fd 1;
  - re-projection;
  - the background cap.
  
  These are the highest-signal items, and every one is a concrete path.
- **Single-model findings.** Opus found the two most dangerous issues no one else saw: broker secrets reachable through `run_job` (A1), and operator forgery through harness.db (A2). Fable found more of the Windows and SDK-source specifics (B9, B12, B14, B17). Both reviewers misjudged `fastapi.sse` the same way the design text did. The design was wrong, and both caught it.
- **Pattern.** No finding attacks the shape: the host process, one policy point and the actor all survive. Every finding is about a path around the shape or a missing rule inside it. The base pick stands.
