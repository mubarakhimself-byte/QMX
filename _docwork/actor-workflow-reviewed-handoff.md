# Reviewed bounded actor/workflow handoff — 4 October 2026

Base reviewed successor: `5acb4a6483567976be771880d57b30482da4ec6b`.
Implementation commit: `e169d5521f771b7e9ad2aeac9d501353a111f3d5`.
Isolated branch: `actor-workflow`, worktree
`C:/Users/Mubarak/Documents/Codex/2026-10-04/task-21/repo/backend-actor`;
common Git directory is task21/repo/.git. The task12 source repository was not
used as the worktree's common Git directory or changed by this lane.

## Delivered behavior

Optional host-owned actor-workflows.json composes into the real configured QMA
daemon request path. Persistent Quant identity is distinct from per-job execution
Agents and child threads. Versioned analyst/reviewer roles actually execute with
injected providers; finite deterministic LangGraph nodes and bounded SDK agent
nodes share the existing queue, journal, checkpoints, scoped memory and skills.
Child activity receipts support authorized status/result reads and cooperative
named cancellation through the existing parent cancellation owner. Recovery
preserves observed effects, catalog pins and legacy effect namespaces.

No separate background server or orchestration loop was added. AsyncSubAgentMiddleware
and Agent Protocol were evaluated before retaining QMA transport. Native subscription
providers remain outside this inference-only catalog and retain their native harness.
Behavioral Quant identity does not create canonical Task/grant/CT47 authority.

## Shared integration seams for parent composition

Owned files are actor_profiles.py, actor_workflow.py and test_actor_workflow.py.
Four shared files have focused hunks:

- process.py: optional catalog binding between existing tool binding and bridge creation.
- daemon_bridge.py: authorized child receipts and optional owned-child cancellation.
- wire/agent_request.py: optional cancellation activity_id parsing and DTO roundtrip.
- tool_loop.py: optional child effect namespace; enforce an existing bound grant's
  parameter ceiling before invoking its SDK callback.

provider_config, domain_tools, native adapters, Study/projection/QMB, dependency
manifests and lock are unchanged. The raw in-process dispatch path outside this SDK
wrapper still needs parent follow-up for the inherited parameter-ceiling gap.
The early task21/ACTOR-SEAM-PROPOSAL.md records the proposed composition boundary.
Parent must reconcile the small process.py composition hunk with the separate Study lane.

## Evidence and reproducibility

Evidence root: `C:/Users/Mubarak/Documents/Codex/2026-10-04/task-21/evidence`.

| Check | Result | Evidence |
|---|---|---|
| Final dedicated actor tests | 17 passed, no skips,43.06s | focused-final-9.log |
| Final strict Pyright | 7 changed files,0 errors/warnings,7.924s | types-final-5.json |
| Focused integration before last two additions | 104 passed, no skips,72.63s | final-focused-7.log |
| Independent eight-file regression | 128 passed, no skips,79.79s | review-final-4/ |
| Independent dedicated actor check | 17 passed, no skips,35.94s | reviewer-final-5/ |
| Latest restart-memory extension independently checked | 1 passed,18.66s | reviewer-final-6-memory/ |
| Source-first import/worktree/package proof | All six source imports point into actor worktree | source-provenance-base.json |
| Ruff format/lint, staged whitespace, draft patch applicability | Passed | Local final checks |

The latest memory extension verifies a fresh job after disk reopen recalls the
analyst summary into a different thread under the same Quant. Independent review
found no remaining bounded implementation or documentation blocker. Earlier failed
setup/test/type logs are preserved. These results are local, injected, offline
checks; they are not coverage, a fresh dependency installation or a whole-platform gate.

Run task21/run-actor-check.ps1 with default tests, `-Check types`, or
`-Check provenance`. It places current repository source paths before borrowed
read-only dependency distributions and disables bytecode writes. The pinned
installed SDKs are DeepAgents0.7.21, LangChain1.4.3, core1.6.6 and LangGraph1.2.12.
The final process.py formatter adjustment only normalized a line ending; no
runtime behavior changed after these tests. Final committed import proof is
recorded separately in evidence/source-provenance-final.json.

## Drafts and remaining scope

Read actor-workflow-architecture-api-runbook-draft.md for the concrete host catalog,
API lifecycle, recovery runbook, memory scopes, mini-app/Copilot adaptation and SDK
architecture. Read actor-workflow-requirements-sdk-evidence-draft.md for the original
requirements → SDK mechanism → implemented/tested/remaining map.
actor-workflow-architecture-api-runbook.patch is an **unapplied** canonical-doc draft
and passes git apply --check.

Recommended next increment: make released create_deep_agent the default harness
for inference workflow agent nodes at the existing ToolLoopProvider graph factory.
Do not stack another create_agent loop. It requires admitted built-in tool visibility
in _TextActionModel.allowed/bind_tools, SDK summarization/model budget accounting,
explicit SDK delegation/filesystem profile limits and lifecycle verification first.
This factory switch was evaluated and documented, not implemented here.

Actor summaries currently share only in exact principal/Quant/role/workflow/authority
scope. App/session/global sharing policy, broad workflow authoring/joins, alternate
child providers, multi-version draining and canonical authored Task authority remain
outside this increment. Tracing execution is explicitly disabled; four checked
nonsecret tracing settings were unset. No hosted LangSmith integration is claimed.
LangMem remains optional existing extraction functionality, not automatic actor calls.

No external provider calls, credentials, UI, Cortis, Lab, push, merge, deployment,
remote unattended endurance or full-platform acceptance was exercised or claimed.
