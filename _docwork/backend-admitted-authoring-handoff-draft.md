# Admitted request authoring checkpoint — draft

Successor of reviewed composition `33165e84146b2a6da32c7e536b698c4fa609be3f`,
on isolated branch `backend/admitted-authoring-projection-20261004`. This is an
opt-in backend authoring seam, not full backend or authenticated-provider acceptance.
No UI, canonical documentation, originals, credentials, trading, push or deployment changes.

## Host setup and Claude API handoff

An operator profile may add `authoring_task_id` inside `agent_sdk.profiles` in
the existing operator configuration. This is a host field: renderer
`submit_agent_request` still accepts its existing DTO, never an Agent, Task,
lease, owner, deployment or Experiment Ledger receipt supplied by the renderer.
Only `authority_profile=authoring` permits the binding.

Before configuring request workers, the trusted host must:

1. Admit a real Agent through `process.agent_capabilities.spawn(SpawnRequest(...))`,
   with its actual owner/session and frozen role permission `experiment.register`.
   The profile does not mint this Actor and does not confer permission by itself.
2. Materialize the real TaskGraph and dispatch its Task through
   `process.task_dispatcher.dispatch_task`, using that Agent as the lease holder.
   The Task must remain RUNNING and resolve in the durable graph and Task Ledger.
3. Pin the Task inputs `agent_session_ref`, `authoring_product_session_ref`,
   `authoring_profile_id`, `authoring_data_ref`, `authoring_environment_ref`, and
   `authoring_resolved_config_ref` to the actual admitted host scope and refs.
   These are not convenience defaults or fabricated authoring evidence.
4. Install the trusted provider and bound policy with
   `process.configure_agent_requests(...)` before binding the listener. Ordinary
   native tools remain denied. Native adapters lacking actual deployment metadata
   correctly refuse this CT47 registration path.

The authenticated paired client initializes the normal agent request capabilities,
submits a request and polls `get_agent_request`. The provider proposes one bounded
JSON object: `data_ref`, `environment_ref`, `resolved_config_ref`, `seed`,
`cost_assumptions`, optionally `code_ref` and `mechanisms`. Unknown or duplicate
fields and caller provenance are refused. The host supplies the observed provider
deployment and harness version, computes the ExperimentSpec identity, registers
through the existing service and verifies SQLite registration plus authored
deployment evidence before writing `experiment.authoring_receipt`.

When existing disclosure authority permits it, `get_agent_request` adds the
actual journal receipt as `experiment_authoring`: request/attempt, product-session,
spec fingerprint, actual dispatch lease/Task attempt, observed deployment and
provider-output SHA256. Existing `content_withheld` behavior also withholds this
receipt. A registration does not manufacture Task completion or QMB execution.

General operator-facing durable Actor/Task ingress is still a separate capability.
The process-owned capability store does not automatically resurrect a running
Agent after restart. Current authoring setup therefore needs legitimate host
admission; do not reconstruct or widen Agent authority from a receipt.

## Recovery and concurrency

Accepted requests persist an immutable SHA256 over canonical Task, lease, Task
attempt, Agent session and frozen capabilities. Rebinding, reassignment including
A→B→A, cancellation, changed context or changed Task pins cannot register a recipe.
One composed Task lock covers the public graph/lease/Task Ledger mutators and
projection cache fill. A shared ProductSession/grant-ledger lock fences canonical
revocation, regrant, hydration and context mutation through registration. Lock
order is runtime → Task → session/grant → journal/SQLite. Provider execution and
both public dispatch execute callbacks stay outside these host locks.

The actual validated provider proposal is journaled before the registration effect.
If registration/receipt/final-snapshot persistence fails, the request reports
`authoring_effect_uncertain`. A lost final snapshot restores this observed result
as failed/uncertain rather than replaying its provider turn. Ordinary interrupted
retry also consults the durable observation and refuses replay. Recovered content
contains no SDK transcript-resume handle.

`process.reconcile_experiment_authoring(request_id)` is an explicit trusted host
maintenance method, not a renderer command or query effect. It repairs only a
missing receipt for an exact existing SQLite registration, with the original
observed output and unchanged legitimate authority. It cannot mint registration,
call a model, transfer author identity, or convert the request into a claimed
fully successful execution. Missing Agent authority on cold start is a blocker.

## Evidence and next connection

The source-first offline authoring suite is reproducible from task-12 with:

```powershell
.\run-local-check.ps1 -Suite authoring
```

`authoring-77481702f6a1448a9c4d39c12f92f71c`: **153 passed**, no failures/skips,
31.89 seconds. This includes actual paired socket request execution from the
real spawn/materialize/dispatch path; SQLite and receipt reopen; missing
permission/deployment; malformed, recursive and foreign recipe fields; cancellation;
ABA reassignment; mutable Task input changes; queued restart retargeting; receipt
repair; total final-snapshot refusal/restart; optimistic undurable cache refusal;
and forced concurrent service/direct-ledger revocation. The injected provider is
explicitly `synthetic:offline-authoring-v1`, with one actual adapter execution per
successful proof. Dummy data/config refs in these fixtures do not prove a data run.
Owned strict types and Ruff lint/format pass. All earlier red and intermediate
evidence remains in task-12/evidence; initial loop-lifecycle fixture failure was
corrected without weakening the single-daemon substrate invariant.

Public owned-DONE projection remains the next bounded connection. QMA must select
exactly one owned DONE QMB JobHandle, reopen its checked expected and COMPLETE proof
artifacts, and send its original run invocation to QMB. `run_fp1` is the actual
QMB run fingerprint, not an ExperimentSpec fingerprint. QMB owns
`project_operator_replay` and source CT32/CT29 selection. Public read must not
implicitly publish `analysis.published` into the Experiment Ledger. The missing
QMB CLI projection bridge and the real authenticated data→backtest→projection
journey remain explicit dependencies; synthetic authoring proves neither.

Full native authentication, unrestricted native tools, remote endurance and
DeepSeek policy-cap/key remain unverified or pending. Existing coverage floors,
component failures and hosted/Linux limitations are retained in the main ledger.
