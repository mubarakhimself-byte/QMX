# Native subscription session adapters: reviewed handoff

Base: `ecda9c06c191eab34469bddbf41041a8d5c7bb76`, isolated worktree
`task-6/native-sessions`, branch `native-subscription-sessions`. The first local
checkpoint is `4d92bf216863c68656a1fe649af02a3ce97a4e5f`. This increment replaces
that checkpoint's blanket refusal with a narrow supplied-text configuration.
The parent's combined candidate and UI are untouched.

## Implemented boundary

Both public backends implement native start/resume, events, interruption and
cleanup through official SDKs. The host provider supplies result access and one
bounded activity for LangGraph. Native sessions are not `BaseChatModel` instances.
No live subscription connection, login, account-status call or model call was
performed during this task. Passing offline checks does not verify authentication.

| Provider | Pinned pair | Supported configuration | Remaining gate |
| --- | --- | --- | --- |
| Codex | `openai-codex==0.160.0`, `openai-codex-cli-bin==0.160.0` | Supplied text; dedicated native home; empty workspace; verified effective configuration; empty native environments; explicitly registered host metadata callback | Ordinary native tools and subagents unavailable. Installed 0.159.3 is inspected, but not selected by this implementation. |
| Claude | `claude-agent-sdk==0.2.163`, native CLI 2.1.286 | Supplied text; dedicated native home; empty workspace; removed builtins; strict SDK MCP host callback; native subscription auth metadata | Operator must first review the personal unmanaged native policy. No managed-policy isolation claim. Ordinary tools and subagents unavailable. |

Unconfigured constructors advertise unavailable. Configured Codex can be composed
now; configured Claude additionally needs `native_policy_reviewed=True`. That
operator attestation is not a QMX grant or an OS security guarantee. Both expose
`native_tools=False`; unavailable configuration fails before client construction.
Authentication is checked only on a later, explicitly authorized launch.

This is a **trusted pinned native-launcher configuration**, not OS isolation.
It relies on the unmodified official runtime honoring tool/environment settings.
A compromised executable or hostile local process is outside that boundary.
No VM, container, firewall, hosted subscription setup or persistent permission
rule was provisioned. Ordinary native tools need a separate enforceable worker
boundary before admission: read-only base, scratch workspace/native home only,
provider HTTPS egress, no host home/repository/money storage/broker configuration,
admin sockets or localhost/private-network control surfaces.

Codex uses the public `CodexClient`, with an explicit server-request handler.
The SDK's permissive default approval handler is never used. Command/file approvals
are declined; permission grants are empty; unexpected requests fail the activity.
The pinned runtime's ordinary shell, patch and image tools require environments;
`thread/start` and `turn/start` use `environments=[]`. Configuration inspection,
feature flags, instruction sources, workspace, identities and every emitted item
are validated. The SDK owns all process/protocol encoding and decoding.
Production does not add a custom JSONL transport.

Claude uses `tools=[]`, no agents/skills/plugins/discovered MCP, empty setting
sources, strict MCP, no fallback model, denied unexpected tool requests and
verbatim prompts. These are not claims that `can_use_tool` or Python hooks cover
managed policy. Known local Windows managed settings/registry presence is refused;
authenticated account policy must be reviewed separately. Metadata checks found
no dangerous local managed policy configured; account policy remains unverified.
A future start accepts native `claude.ai` authentication in the dedicated home
and rejects API/provider-token routing. QMX never reads a credential file.

## Entry points and authority

- `native_sessions.SessionBackend`: explicit `start`, `resume`, `cancel`,
  `events`, `close`, availability and stable configuration binding identity.
- `NativeSessionProvider.bind_runtime(runtime)`: QMX composition. `execute`
  serves the synchronous daemon provider seam; `activity` is one bounded async
  LangGraph activity; `results(request_id)` revalidates current host scope.
- `native_codex.CodexSessionBackend`: public official `CodexClient` methods
  `thread_start`, `thread_resume`, `turn_start`, `turn_interrupt`, typed
  notifications and SDK-owned lifecycle/control channel. Experimental dynamic
  host tools require the explicit pinned initialization setting.
- `native_claude.ClaudeSessionBackend`: official `ClaudeSDKClient.connect/query`,
  options `resume`, `receive_response`, `interrupt`, `disconnect`, and official
  `tool/create_sdk_mcp_server` host callbacks.
- `native_composition.compose_native_metadata_provider`: real programmatic
  composition accepting an existing host-owned `qml.research.browse@1` binding,
  exact retained snapshot/locators and current `RequestRuntime`. One metadata
  operation per activity, no general host tool registry.

QMX owns job identity, grants, authoritative journal and domain effects. The native
harness owns its inner loop and session context. LangGraph surrounds that activity
without issuing a second inference/tool loop. Existing `ToolLoopProvider.dispatch`
is reused only for host admission and durable effect receipts, never inference.
Explicit QMX operations are admitted by current grants; ordinary native tools
cannot acquire money-control access through the supported tool manifest.

Resume IDs come only from the journal. Binding includes principal/product session,
profile/instructions, provider/model, context/grants, tool schema, workspace and
native home/runtime identity. Each domain effect ID includes the current request
identity. Checks occur before launch, after preflight/connect before query, during
monitoring, before dispatch, after callback before disclosure, and on result access.
Subagent/peer identities and nonhuman Claude origins are refused.

Missing/mismatched terminal evidence leaves an unknown pending native record,
preventing automatic replay or paid fallback. Cancellation requests SDK interruption
and drains terminal evidence; only an explicit interrupted terminal proves it.
Claude uses actual `terminal_reason=aborted_streaming|aborted_tools`, not an
invented error subtype. Proven pre-turn refusals permit retry after correction;
a possibly submitted turn stays pending. Cleanup has a separate two-second
cooperative deadline. Blocking SDK calls use fenced daemon workers so timeout
cannot hang the Python default executor or launch after a cancelled preflight.
Serialization is per provider instance, not distributed ownership or forced
termination of arbitrary host callbacks.

## Offline evidence and remaining integration

The optional [requirements](native-session-requirements.txt) and
[hashed lock](native-session-requirements.lock) keep shared dependency files
untouched. Missing SDKs cause explicit test skips, not native readiness evidence.
Python test environment: 3.14.7.

`tests/test_native_sessions.py` exercises real RequestRuntime, ProductSession
admission, authoritative journal and retained-corpus metadata. It includes the
released Claude SDK's actual MCP server/client protocol with fake native models.
`tests/test_native_codex_bridge.py` uses the released public CodexClient subprocess
transport against a test-only SDK-compatible protocol peer. The peer is a fixture,
not a production transport or a claim of live native-runtime behavior.

Regressions cover retained/reconstructed resume IDs, cancellation/startup races,
slow preflight, cleanup, unexpected native tools/approvals, terminal identity,
subagent authority, real scope expiry/revocation, result disclosure checks,
subscription-only routing, missing API fallback, effective configuration and pins.
They do not prove CLI hook coverage or account authentication.

Final selected regression run: **209 passed**, including **59 native tests**.
All ten owned Python files pass Ruff lint/format checks and strict Pyright
with zero errors/warnings. Independent requested Sol 6.1 High review found no
remaining material blocker, including the final documentation/proof additions.
The full repository suite was not run in this lane.

```powershell
python -m pytest packages/qma-daemon/tests/test_native_sessions.py packages/qma-daemon/tests/test_native_codex_bridge.py -q
python examples/native_sdk_offline_check.py --installed-codex '<installed-codex.exe>' --claude '<claude.exe>' --output '<report.json>'
```

The [runtime report](native-session-runtime-check.json) records only executable
versions, generated schemas and public SDK signatures. It does not initialize
app-server, read account state or send prompts. `native_session_admitted=false`
in that report means admission was not performed by this offline checker; the
public configured backend boundary above is implemented. Codex 0.159.3 satisfies
the SDK's nominal 0.151.0 floor, but only exact 0.160.0 is accepted by this bridge.
Both generated read-only policies lack restricted read roots; ordinary tools
remain gated. Claude 2.1.286 matches the SDK expected CLI and verbatim-prompt floor.

Programmatic composition and the original standalone proof are implemented. In
the isolated combined successor, shared operator JSON also accepts the explicit
`native-session` protocol. The daemon selects a separate native wrapper, resolves
the current session target and exactly one existing matching metadata grant for
each activity, then calls `compose_native_metadata_provider`. Native execution
does not enter the inference wrapper or `ToolLoopProvider.execute`; only existing
host dispatch/effect receipts are reused. Generic LangChain API options remain
independent. Native SDK imports stay lazy; absent optional packages fail with a
sanitized unavailable result and never select another provider.

Every native profile must contain exactly `tools: ["research_browse"]`, with an
explicit current instance revision and retained corpus scope. Native profiles
cannot enter the generic research workflow, including its default profile
selection. Claude additionally requires the operator's explicit
`native_policy_reviewed: true` attestation; this does not certify managed-policy
isolation or authentication. Configuration eligibility performs no native launch,
auth read or filesystem provisioning. Execution retains all backend preflight gates.

The [native operator example](native-session.operator-config.example.json) is a
nonsecret template requiring real operator-owned paths, instance and corpus pins.
The [integrated daemon proof](native_daemon_proof.py) supplies its own synthetic
configuration, app-use session and one narrow grant in a new proof store, then
uses authenticated CT-40 over loopback and two distinct daemon OS processes. It
requires a retained native ID, the prior marker omitted from the second prompt,
and exactly one observed durable host metadata receipt. Default mode performs no
store writes, native auth or model calls. Never reuse a previous/unknown proof root.

Offline Codex checks exercise that actual shared route with the released SDK's
transport and a test-only protocol peer. They also prove authenticated cancellation,
grant revocation/result withholding, forged session/provider/workspace denial and
no generic inference/API fallback. Runtime verification is disabled only in the
test fixture. They do not prove live Codex authentication or Claude daemon execution.

[Documentation drafts](NATIVE_SESSION_DOCS_DRAFT.md) propose canonical component,
stack and contract updates. They are not ratified or applied to canonical docs;
this lane does not claim completion of every migration acceptance-matrix row.

## Minimal human login and separately approved live proof

1. Obtain parent approval for authentication. Use the unmodified official CLI in
   a dedicated home; do not copy credentials into QMX or supply API keys.
   Codex must use the pinned bundled 0.160.0 executable. The prepared Oct 3 login
   helper currently targets 0.159.3; reuse requires reviewing its exact executable
   and home first. Claude additionally requires the native personal unmanaged
   policy review; absence of local managed files alone is insufficient.
2. Human-only login commands, after approval (not executed by this task):

   ```powershell
   $env:CODEX_HOME = '<dedicated-codex-home>'
   & '<sdk-venv>/Lib/site-packages/codex_cli_bin/bin/codex.exe' login
   # Or, for the separately reviewed Claude installation:
   $env:CLAUDE_CONFIG_DIR = '<dedicated-claude-home>'
   & 'C:/Users/Mubarak/.local/bin/claude.exe' auth login
   ```

3. The proof's default command is dry and makes zero auth/model calls or host-store
   writes. Supply existing dedicated home and empty workspace paths, and a new
   synthetic host-store path:

   ```powershell
   python examples/native_session_proof.py --provider codex --executable '<bundled-0.160.0-codex.exe>' --native-home '<dedicated-home>' --empty-workspace '<empty-directory>' --root '<new-proof-root>'
   ```

4. Only after a separate live-proof approval, add `--allow-live`. For Claude use
   `--provider claude`, its pinned executable, and `--native-policy-reviewed` after
   the actual review. The script executes two bounded 60-second native turns,
   requires one real granted metadata operation/observed receipt, retains the
   native session ID, and verifies a previous random marker that is not repeated
   in the resume prompt. It writes IDs/results/receipts to `proof-result.json` and
   the authoritative journal. It stops on failure/unknown outcome and refuses an
   existing proof store. Text-only output does not satisfy acceptance.
   Cancellation proof is a separate authorized exercise requiring an explicit
   interrupted terminal. No live proof has been run.

For the **integrated daemon path**, substitute `examples/native_daemon_proof.py`
for the standalone proof in steps 3-4. It uses the same pinned binary/native home,
empty workspace and new synthetic root, but restarts the real daemon between the
two turns and verifies the authenticated shared operator route. The report is
`daemon-proof-result.json`. No human login or live invocation has been performed.

## Official references

- [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk) and
  [app-server](https://learn.chatgpt.com/docs/app-server).
- Pinned runtime [tool-plan source](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/core/src/tools/spec_plan.rs)
  and [feature registry](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/features/src/lib.rs).
- [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview),
  [permissions](https://code.claude.com/docs/en/agent-sdk/permissions),
  [CLI reference](https://code.claude.com/docs/en/cli-reference),
  [settings](https://code.claude.com/docs/en/settings) and
  [hooks](https://code.claude.com/docs/en/hooks#disable-or-remove-hooks).
- Context7 `/openai/codex` and `/anthropics/claude-agent-sdk-python` were consulted;
  published package source and generated pinned schemas provide offline evidence.
