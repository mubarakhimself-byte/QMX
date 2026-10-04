# Native session SDK lane: reviewed boundary and handoff

Base: `ecda9c06c191eab34469bddbf41041a8d5c7bb76`, isolated linked worktree
`task-6/native-sessions`, branch `native-subscription-sessions`. This addendum
preserves the migration acceptance matrix. The parent's combined candidate
`ffb7590bbda1ec8d5dc126b9fdc3205c888dffac` is not modified or merged here.

## Result and admission decision

**Neither public native subscription backend is admitted on this Windows host.**
Both reject before constructing an SDK client, advertise `available=False`, and
advertise `resume=False` through `NativeSessionProvider`. There is no operator
configuration escape hatch. Existing generic API inference remains separate.
No subscription connection, authentication, live inference or spend is verified.

The SDK lifecycle implementations and host activity are concrete, tested code,
not fabricated SDK methods or a custom JSONL transport. They are retained as
private offline seams pending an enforceable host boundary:

| Provider | Reviewed official pair | Concrete blocker |
| --- | --- | --- |
| Codex | `openai-codex==0.160.0`, `openai-codex-cli-bin==0.160.0` | Both installed 0.159.3 and bundled 0.160.0 generated read-only policies have only `type` and `networkAccess`. No restricted read roots. Approval denial/hook coverage cannot enforce the complete host-approved read scope. |
| Claude | `claude-agent-sdk==0.2.163`, existing CLI 2.1.286 (also SDK expected CLI version) | Builtins can be removed, but managed machine/account policy hooks can execute outside that tool boundary. `disableAllHooks` does not disable managed hooks. This Python SDK has no reviewed managed-policy isolation option. Empty settings sources alone cannot certify account-delivered policy. |

The separate optional [requirements](native-session-requirements.txt) and
[hashed lock](native-session-requirements.lock) preserve dependency-file ownership.
The native test module skips when these optional SDKs are absent. Native testing
must install them; a skipped test is not native readiness evidence.

### What must change to run

No dangerous configured Claude policy was discovered in the metadata checks:
`C:\Program Files\ClaudeCode\managed-settings.json`, its fragment directory,
and the HKLM/HKCU `SOFTWARE\Policies\ClaudeCode` keys were absent. Those checks
do not inspect credential values or prove the later authenticated account has
no server-managed policy. The blocker is an unreviewed native launcher policy
boundary, not a finding that malicious hooks are configured on this machine.

The smallest plausible **Claude smoke scope** is supplied text, native session
storage/authentication in the dedicated home, official provider HTTPS, and one
host-mediated corpus-metadata callback. Ordinary tools stay removed with
`tools=[]`; no Agent/Task/Skill, discovered MCP, project/user settings, CLAUDE.md,
prompt @file expansion, arbitrary filesystem/network tool, or API fallback is
part of that scope. Effective managed policy must first be reviewed after an
authorized human login. On a confirmed personal unmanaged native installation,
that review may be sufficient for a separately authorized one-time smoke under
the trusted native-launcher boundary; the present task cannot establish that
authenticated condition. Merely setting `can_use_tool` is not the proposal.

For **ordinary native tool access or a hard process boundary**, the concrete
proposal is a local Linux container/VM worker with a read-only base filesystem,
only its scratch workspace and dedicated native auth/session home mounted,
and provider-only HTTPS egress. Deny localhost/private-network access and mount
no QMX realmoney storage, broker/exchange configuration, daemon/admin sockets,
Docker socket, host home, or general repository roots. Native login occurs in
the worker through the unmodified CLI; no credentials are copied into QMX.
QMX remains outside the worker and admits host operations through the official
SDK's control/MCP channels. Each callback rechecks the original job's current
grant; the worker cannot invoke QMX control-plane operations by ordinary tools.

That proposal needs approval for the worker setup and egress rule, an available
container/VM runtime, and independent adversarial file/network boundary tests.
It changes where the native process runs, stores its auth/session home there,
and adds local isolation infrastructure; it does not change realmoney security
rules or authorize hosted subscription use. None was configured here. Codex's
official SDK supports a launch command override; Claude's official SDK supports
a transport seam. Their worker-launch bindings require implementation and
verification while leaving protocol encoding/decoding to the SDK. They are not
claimed implemented in this lane. No permanent provider prohibition is proposed.

## Entry points and ownership

- `native_sessions.SessionBackend`: explicit `start`, `resume`, `cancel`,
  `events`, `close`, provider availability and immutable backend binding identity.
- `NativeSessionProvider.bind_runtime(runtime)`: host-only QMX composition.
  `execute` implements the existing synchronous daemon provider seam;
  `activity` is one async bounded activity usable by LangGraph;
  `results(request_id)` revalidates host scope before returning observed results.
- `native_codex.CodexSessionBackend` and `native_claude.ClaudeSessionBackend`:
  public, unavailable production boundaries. Provider config is deliberately not
  extended to advertise an unsafe runnable protocol.
- `_CodexSDKLifecycle`: official `AsyncCodex.thread_start/thread_resume`,
  `AsyncThread.turn`, typed `AsyncTurnHandle.stream`, `interrupt` and `close`.
- `_ClaudeSDKLifecycle`: official `ClaudeSDKClient.connect/query`,
  `ClaudeAgentOptions.resume`, `receive_response`, `interrupt`, `disconnect`;
  official `tool/create_sdk_mcp_server` for host-mediated operations.

The native harness owns its inner reasoning/tool loop and session context.
LangGraph owns only a surrounding activity cursor. No native session becomes
`BaseChatModel`, and no second agent loop calls the native harness repeatedly.
The existing `ToolLoopProvider.dispatch` is reused only for QMX admission and
durable effect receipts; its inference `execute` is never invoked.

Conversation resume is selected from the authoritative journal, never from a
model-supplied native ID. The binding includes principal, product session,
profile/instructions, provider/model, context/grant fingerprint, workspace,
backend home/runtime identity and tool manifests. Each operation's effect ID
includes the current QMX request/job ID. Current grants are revalidated before
start/resume, after connection before query, during monitoring, before dispatch,
after the host callback before disclosure, and before result access.

Missing/mismatched terminal evidence leaves a pending native record and refuses
automatic replay or fallback. Cancellation requests SDK interruption and drains
terminal evidence; only an explicit interrupted terminal proves cancellation.
Claude uses `terminal_reason=aborted_streaming|aborted_tools`, not an invented
error subtype. Cleanup has a separate two-second cooperative deadline. Session
activity serialization prevents duplicate calls within one provider instance.
This is not distributed ownership or forced termination of arbitrary callbacks.

## Offline verification

`tests/test_native_sessions.py` exercises real RequestRuntime, ProductSession
grant dispatch, authoritative journal and retained-corpus metadata operation.
Native processes/models are fakes. One test uses the released Claude SDK's
actual MCP server and released MCP client over in-memory protocol streams,
executes `qml.research.browse@1`, then resumes the same native session ID.
Codex fakes use the released SDK's typed notification models.

Regressions cover retained resume IDs and reconstruction, changed native home
binding, missing/wrong terminal IDs, cancellation drain and connection races,
cleanup deadlines, real grant expiry/revocation, result access after revocation,
subagent refusal, API routing environment rejection and absence of paid fallback.
No runtime hook enforcement is claimed: the Python hook callback test verifies
the callback decision only. Public production backends remain blocked.

From `qmx-agents`, with the isolated SDK interpreter:

```powershell
python -m pytest packages/qma-daemon/tests/test_native_sessions.py -q
python examples/native_sdk_offline_check.py --installed-codex <installed-codex.exe> --claude <claude.exe> --output <report.json>
```

The offline checker uses only `--version` and schema generation, binds public SDK
method signatures, and verifies the released Claude transport constructs empty
tools, empty settings sources and strict MCP flags. It never starts app-server,
reads account state, performs login or sends a prompt. The checked runtime report
is [native-session-runtime-check.json](native-session-runtime-check.json).
Codex 0.159.3 passes the SDK's nominal version floor (0.151.0); that is not full
session/permission compatibility proof. The installed executable is not selected
as a production override. Python test environment is 3.14.7.

## Minimal human login and later live proof

1. Resolve and independently verify the host isolation/policy blocker first.
   A login does not resolve it. Do not enable the private lifecycles directly.
2. After separate parent approval, the human signs into the official native CLI
   in its dedicated native home. Reuse the prepared Codex login helper only if
   its exact executable/home match the subsequently reviewed runtime. Claude
   likewise uses its unmodified native login. Do not copy credentials into QMX,
   translate tokens, configure API keys or create persistent permission rules.
3. After explicit live-proof authorization, perform exactly two bounded native
   turns: start a synthetic session with one harmless granted corpus-metadata
   operation; resume its retained ID and verify the prior marker plus operation
   receipt. Persist native IDs, matching terminal evidence and QMX receipts.
   An ordinary text reply or two fresh native sessions does not satisfy proof.
   Stop on unknown outcome; do not retry/fallback. Interruption proof is a
   separate authorized test requiring an explicit interrupted terminal.

There is currently no admitted live command to run. No UI, shared migration or
integrator files, protected branch, remote repository or credential store changed.

## Official evidence

- [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk) and
  [Python API reference](https://github.com/openai/codex/blob/main/sdk/python/docs/api-reference.md)
  establish native lifecycle ownership. Context7 `/openai/codex` was consulted;
  installed published package source and generated schemas supply version evidence.
- [Claude Python SDK](https://code.claude.com/docs/en/agent-sdk/python),
  [permissions](https://code.claude.com/docs/en/agent-sdk/permissions), and Context7
  `/anthropics/claude-agent-sdk-python` distinguish tool availability from approval.
- [System prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)
  says empty settings sources disable CLAUDE.md loading. Installed SDK source
  confirms `verbatim_prompts` requires CLI >=2.1.248; 2.1.286 meets that floor.
- [Managed settings](https://code.claude.com/docs/en/settings) and
  [hooks](https://code.claude.com/docs/en/hooks#disable-or-remove-hooks) establish
  the remaining Claude boundary. Independent review identified this blocker;
  the public backend was made unavailable instead of weakening host authority.
