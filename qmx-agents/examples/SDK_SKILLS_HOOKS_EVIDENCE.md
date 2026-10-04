# Local focused skills/hooks evidence

Verified October 4, 2026, in the isolated clone
`C:\Users\Mubarak\Documents\Codex\2026-10-04\task-11\skills-hooks-native`, branch
`codex/sdk-skills-hooks`, based on native-combined candidate
`1f3b98f6b6f268e98f0f14edbb918b727069eb9c`.

The original research review remains in the earlier isolated research clone,
commit `45ebd77e5aa557d27dab78a193946e8cd5f416b5`, at
`task-11\skills-hooks\qmx-agents\examples\SKILLS_HOOKS_REUSE_REVIEW.md`.
This implementation follows that reuse decision: selective released SDK
middleware, not a replacement custom harness. Original transcripts/reconciliation
and broader requirements remain authoritative; this evidence concerns the bounded
generic path only.

## Results

| Check | Result | Scope |
|---|---|---|
| Final focused integration/regression selection | 157 passed in 62.15 seconds; no skips | 11 files named below; generic authenticated flows, child workflow, grants, replay and native SDK/daemon fixtures |
| Additional native Codex bridge selection | 37 passed in 14.55 seconds | `test_native_codex_bridge.py`; released SDK protocol peers |
| Ruff changed Python files | All checks passed | new modules/tests and five existing Python integration files |
| Strict Pyright | 0 errors/warnings | new modules/tests and changed request-runtime files; process checked separately with 0 errors/warnings |
| `git diff --check` | Passed | whitespace integrity |
| `uv lock --check --offline` | Passed; 79 packages resolved | lock consistency with the dependency pins |
| Final independent reviewer run | 155 passed in 68.32 seconds; no skips | eight focused files including actual native SDK/daemon fixtures |

These are deterministic offline results, not provider quality, live auth, provider
spend, native subscription policy, OS sandbox or whole-platform acceptance proof.
The skill procedure reaches a real granted synthetic callback in the generic
graph; the daemon also loads it through operator startup and a real paired
WebSocket. No secrets or files outside the approved synthetic host roots are used
by the skill fixtures. SDK packages/source and the existing native environment
are read as dependency infrastructure; they are not skill roots.

## Exact local commands

The native SDK environment was already installed by the separate native lane.
It is used read-only; bytecode writing is disabled. Generic SDK dependencies were
installed only into `task-11\sdk-deps` from pins, and `qmx-agents/uv.lock` was
resolved for `deepagents==0.7.21`, `PyYAML==6.0.3`, `langchain==1.4.3` and
`langgraph==1.2.12`. It records core 1.6.6, checkpoint 4.2.0 and prebuilt 1.1.0.
No live provider, credentials, plugin install or global environment mutation occurs.

```powershell
$repo = 'C:\Users\Mubarak\Documents\Codex\2026-10-04\task-11\skills-hooks-native'
Set-Location -LiteralPath "$repo\qmx-agents"
$env:PYTHONPATH = @(
  'C:\Users\Mubarak\Documents\Codex\2026-10-04\task-11\sdk-deps',
  "$repo\qmx-agents\packages\qma-core\src",
  "$repo\qmx-agents\packages\qma-wire\src",
  "$repo\qmx-agents\packages\qma-daemon\src",
  "$repo\packages\qmf-core\src",
  "$repo\packages\qmf-data\src",
  "$repo\packages\qmf-registry\src",
  "$repo\packages\qmf-risk\src"
) -join ';'
$env:PYTHONDONTWRITEBYTECODE = '1'
$python = 'C:\Users\Mubarak\Documents\Codex\2026-10-04\task-6\sdk-venv\Scripts\python.exe'
& $python -m pytest `
  packages/qma-daemon/tests/test_agent_extensions.py `
  packages/qma-daemon/tests/test_agent_extensions_daemon.py `
  packages/qma-daemon/tests/test_research_workflow.py `
  packages/qma-daemon/tests/test_request_runtime_provider_config.py `
  packages/qma-daemon/tests/test_request_runtime_configured_daemon.py `
  packages/qma-daemon/tests/test_langgraph_runtime.py `
  packages/qma-daemon/tests/test_request_runtime_tool_loop.py `
  packages/qma-daemon/tests/test_request_runtime_daemon.py `
  packages/qma-daemon/tests/test_native_sessions.py `
  packages/qma-daemon/tests/test_native_operator_routing.py `
  packages/qma-daemon/tests/test_native_configured_daemon.py `
  --basetemp=C:\Users\Mubarak\Documents\Codex\2026-10-04\task-11\test-final-focused-008 -q
& $python -m pytest packages/qma-daemon/tests/test_native_codex_bridge.py `
  --basetemp=C:\Users\Mubarak\Documents\Codex\2026-10-04\task-11\test-native-bridge-009 -q
```

For another run choose new unused basetemp names: pytest resets its basetemp.
The explicit repository source paths are required for native fixture subprocesses;
pytest's parent-only `pythonpath` setting is insufficient. The SDK/parser bounds
regressions are in `test_agent_extensions.py`, and the startup/socket/disk-reopen
integration is in `test_agent_extensions_daemon.py`. The full evidence matrix and
contracts are in [SDK_SKILLS_HOOKS.md](SDK_SKILLS_HOOKS.md).

## Independent review

Reviewer `/root/reuse_review` did not edit the implementation. It found and caused
fixes for three concrete defects:

1. A safe YAML alias graph expanded 295 raw bytes into 371,368 metadata characters
   before the SDK context cap. Streaming PyYAML admission now rejects aliases and
   anchors before object construction and bounds depth/events; the exact fixture
   is a regression.
2. Global extension presence widened unrelated profile/workflow budgets. Budgets
   now follow the applicable selection; explicit host limits remain authoritative.
3. Rewriting model-facing messages reset model/tool counters and reused `call-1`.
   Accounting now reads independently deserialized canonical graph state. The
   repeated-response regression stops at four graph model steps and records three
   distinct observed effects.

The fixture clock also now forwards boot/count parameters, removing collection
order dependence. Initial native daemon fixture failures were caused by missing
inherited repository import paths; they pass with the commands above. Earlier
native skips and failed diagnostic runs are not counted as final proof.
The reviewer completed its final pass against the corrected implementation with
155 passing tests, no remaining bounded-increment blocker, and no claim of full
platform completion. Graph-step limits explicitly allow an unknown model call to
repeat only on owned explicit resume; they are not a spend cap over all retries.

## Reviewable integration scope

Existing shared files changed: `process.py`, `provider_config.py`, `domain_tools.py`,
`research_workflow.py`, `tool_loop.py`, daemon `pyproject.toml`, workspace `uv.lock`,
and additive pointers in `MATURE_AGENT_RUNTIME.md` and `SDK_REQUEST_RUNTIME.md`.
The native lane's shared overlap is `provider_config.py` and `domain_tools.py`;
its native SDK adapter modules are not edited. New modules, tests and documents
are separate. No protected branch, other worktree, QMB/spot change, UI or whole
platform acceptance run is included. Parent integration remains paused.
