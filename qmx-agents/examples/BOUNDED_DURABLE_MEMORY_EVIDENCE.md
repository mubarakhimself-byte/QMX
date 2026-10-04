# Durable memory lane: local deterministic evidence

Verified October 4, 2026, in isolated `task-14/memory-lane`, branch
`codex/bounded-durable-memory`, based exactly on
`bf3c6b592e89917c17747eb1072203a28241e74a`. No other worktree was edited.
These results concern the bounded module and existing research request path,
not whole-platform, live-model, remote-worker, learning-quality or endurance
acceptance. Tests use synthetic corpus, actor IDs, artifacts and model responses.
No private persistent data, credentials, real provider model/embedding calls,
auth, deploy, merge, push or spend occurred.

## Final checks

| Check | Result | Scope |
|---|---|---|
| Final memory/request selection | 36 passed | typed lifecycle, grants, SDK extraction/search, real paired socket, restart, replay, legacy fallback and configured cap reduction |
| Existing workflow/skills regression | 57 passed in 36.06s | `test_research_workflow.py`, `test_agent_extensions.py`, `test_agent_extensions_daemon.py` |
| Ruff and formatting | All changed Python files clean | three modules, three new test files and changed existing workflow assertion |
| Strict Pyright | 0 errors/warnings | same seven files, explicit SDK/source paths, Python 3.14 |
| Whitespace integrity | `git diff --check` passed | isolated change set |
| Draft integration patch | `git apply --check` passed | optional extraction extra and two additive doc pointers; not applied |
| Independent final review | 36 focused tests plus independent edge probes passed | `/root/memory_review`; no remaining bounded blocker |

The extraction tests emit one upstream Trustcall 0.0.39 `Send` import
deprecation warning with LangGraph 1.2.12. The released SDK source is unchanged.
No test was skipped. Initial type checking used missing dependency paths;
final strict checks explicitly locate the installed SDKs and tested sources.
Earlier diagnostic runs are not counted as final proof.

## Actual behavior demonstrated

The configured daemon test loads normal trusted operator settings and the
existing research workflow, binds a real loopback listener, establishes pairing,
and submits three jobs through the existing JSON-RPC WebSocket. Job two receives
job one's admitted summary. The daemon closes and reopens from disk; job three
receives job two's admitted summary. Journal revisions preserve job one's
admitted and superseded states. Fetching an older terminal request starts no
new model call. The fake transport substitutes only model inference, while
real daemon admission, scope, knowledge, journal and workflow services execute.

Existing workflow tests separately prove interrupted job A retains its frozen
invocation context while job B evolves canonical memory; expired grants prevent
further inference/disclosure; actual source/operation binding, cancellation,
memory-deny hooks, no repeat observed reads and source isolation remain intact.
The existing skills tests verify untrusted skill bytes cannot add operation
authority and that authenticated skills, hook phases and replay still work.

Module tests inspect journal payloads and actual SDK results. They cover:

- Every supported memory type and nonempty source/artifact provenance; wrong
  scope, snapshot, locator, authority revision or type refuses without writing.
- Persistent actor/principal/collection binding differs from app/profile memory;
  different namespaces cannot list, get or retrieve history from one another.
- One journal append retires a predecessor and admits its successor atomically.
  Capacity refusal leaves the predecessor current; conflicting/concurrent
  successors cannot both win. Lost acknowledgment after a durable append is
  safe to retry without duplicate revisions or partial state.
- Invalidation and TTL exclude records from ordinary search/get/context, while
  host-authorized history retains terminal states. Replay cannot resurrect them.
- Disk close/reopen reconstructs identical active context, revisions and
  tombstones without an extra store database or embedding/model activity.
- Token/UTF-8 byte budgets omit whole records and do not change canonical state.
  Injected tokenization that crosses expiration refuses stale disclosure.
- Actual LangGraph Store semantic ranking runs with deterministic local vectors.
  Only active authorized bytes reach it; deleted/expired records are absent.
  Revocation during the first embedding stops subsequent document and query
  calls. Expiration during a search removes the record before return.
- Real released LangMem executes an injected fake chat model and creates
  stable proposed IDs. It writes nothing until the existing gate admits a
  candidate. Model-name strings, over-budget inputs/outputs and stale grants
  refuse, with zero model calls for pre-call refusals.
- Legacy exact-scope summary recall is read-only and checks source pins. Typed
  tombstones prevent legacy fallback. A smaller valid record cap has a usable
  default search; lowering the cap over existing data refuses before indexing.

## Independent review and fixes

Reviewer `/root/memory_review` read the port/gate, journal semantics, source
baseline, module/facade and evidence contracts and ran independent synthetic
probes, without editing lane source. Initial 27 focused tests passed but the
probes exposed missing mid-operation checks:

1. Revocation after embedding document one still allowed document two to reach
   the backend. Validation now occurs before every document put; the two-record
   regression proves only one document is received and no query executes.
2. Expiration crossing during search or tokenization disclosed stale memory.
   Search now rereads canonical heads and TTL at return; context/recall validate
   the selected canonical heads after rendering. Independent probes verify
   omission or refusal, with no rendered stale bytes.
3. Default `search(limit=64)` failed under a valid smaller configured cap. The
   default now uses the actual host cap. A final self-check also added an
   existing-state cap guard before SDK indexing after configuration narrowing.

The independent review reran the corrected focused suite and the probes, then
reviewed the real paired daemon proof, legacy/lost-ack tests and draft patch.
Approval concerns this bounded lane only. General actor routing, autonomous
consolidation/evaluation, rich learning and agent-authored ledgers remain open.

## Reproduction environment and commands

Use the existing base lock's LangChain 1.4.3, LangGraph 1.2.12, core 1.6.6,
checkpoint 4.2.0 and prebuilt 1.1.0. The base skill lane's SDK dependencies at
`task-11/sdk-deps` and native lane's Python 3.14.7 environment at
`task-6/sdk-venv` were read as dependency infrastructure. No shared environment
was modified. LangMem 0.0.30, Trustcall 0.0.39 and dydantic 0.0.8 were installed
only into `task-14/memory-deps` from official PyPI, with no dependency upgrading.
The optional requirements file records those additional exact pins; the
integration lead must generate the combined optional extra/lock separately.

The workspace companion `task-14/run_checks.ps1` sets explicit source/SDK
paths, disables bytecode writes and LangSmith tracing, and invokes:

```powershell
# From task-14; use an unused Run name for each basetemp.
.\run_checks.ps1 -Check focused -Run final02
.\run_checks.ps1 -Check workflow -Run final01
.\run_checks.ps1 -Check lint -Run final02
.\run_checks.ps1 -Check types -Run final02
```

Focused selection:
`test_durable_memory.py`, `test_memory_extraction.py`,
`test_durable_memory_requests.py`. Regression selection:
`test_research_workflow.py`, `test_agent_extensions.py`,
`test_agent_extensions_daemon.py`. Strict type configuration is the workspace
companion `task-14/pyright-memory.json`. Choose a fresh explicit test basetemp
under the writable task directory; pytest resets that directory.

Final logs: `task-14/focused-final02.txt`, `workflow-final01.txt`,
`lint-final02.txt`, `types-final02.txt`; independent probe artifact:
`task-14/memory_review_diagnostics.py`. The source/document mapping and honest
remaining limits are in `BOUNDED_DURABLE_MEMORY.md`. The base snapshots retain
their historic acceptance statements; the draft adds pointers without rewriting
earlier results or claiming the richer agent vision is complete.
