# Canonical request join v1

Engineering contract for the controlled local integration. Status: prepared;
runtime activation waits for the reviewed Study pin and composed authority seams.
This chooses routine implementation details within the delegated packet. It does
not ratify the task-22 architecture draft or change inherited domain rules.

## Authority and mapping

The daemon owns the mapping and admission. A behavioral catalog route is not a
Quant, Agent, Task, Mission or CT47 author. Keep its original actor, effect,
checkpoint and memory keys verbatim. Canonical attribution is additional data.

Mapping key: `(principal, behavioral_actor_id)`. One key names exactly one
canonical Quant for its lifetime. One Quant may have several explicitly admitted
behavioral aliases; aliases do not share memory implicitly. CopilotProfile's
behavioral profile_id selects a catalog route, never the canonical owner. The
canonical ontology Profile remains presentation-only and cannot be a routing or
permission key. Each immutable mapping revision pins
the canonical ActorId and catalog digest. Identical registration is idempotent;
conflicting registration refuses. A host catalog upgrade may append a new
immutable revision for the same key and same Quant using compare-and-set against
the prior revision; it cannot change the lifetime canonical owner. Accepted work
continues using its retained exact mapping/catalog revision, never the new route.
If the original version or provider cannot be resolved, continuation refuses.
Retirement is permanent for that mapping key,
preserves history, stops new admission and new model/tool dispatch, and never
rewrites accepted work. A new identity requires a new explicit behavioral key.
Quant retirement independently refuses admission and continuation. There is no
automatic mint from a syntactically valid ActorId.

The mapping resolves an actual nonretired Quant from the daemon's existing
ontology/mailbox records. Existing TaskGraphDispatcher supplies a separately
dispatched Task, its current DispatchLease and durable graph/ledger. Existing
AgentCapabilityStore supplies the actual frozen Agent that holds that lease.
Canonical Agent owner, Task owner/mission, mapping Quant and exact catalog route
must agree. ProductSession has a principal/context rather than a Quant owner:
require the paired principal to match it and host-admitted Task input references
to link the original ProductSession, behavioral profile and canonical Agent
session, following ExperimentAuthoring's existing admission. Required capability snapshots
come from the recorded spawn set. Renderer, prompt and provider identity fields
cannot replace any of those host records. Reject conflicting canonical owner,
behavior, role, parent, audience and authority refs before dispatch. A legacy
catalog request with no join remains a bounded execution and claims no canonical
Task, lease, CT47 authorship or JobHandle admission.

## Identity and cardinality

Freeze in one daemon journal acceptance record: contract version, mapping key and
revision, full catalog digest, workflow/role version pins, behavioral identity,
canonical owner, actual executing Agent, canonical Agent session, Request id,
original ProductSession/context binding, Task/Mission/graph ids, current lease,
Task ledger attempt, canonical JobHandle id/logical_run_id/attempt_id and Request
attempt. Keep the existing zero-based Task attempt and positive JobHandle attempt
as separate fields; do not infer an off-by-one conversion.

One joined bounded Request attaches to one already admitted canonical execution
Task and its one existing JobHandle. One `(Task id, Task ledger attempt)` admits
one logical Request; idempotent acknowledgement/reconnect returns that Request.
No request submission synthesizes a second Mission, graph, lease or JobHandle.
Retry under unchanged admitted authority preserves Request id, canonical logical
run and effect keys and records a distinct Request attempt. Canonical attempt
changes require independently admitted replacement work and a new Request.
Reassignment never transfers an old acceptance to a new holder: preserve the old
receipt and reconcile old effects first, then admit replacement authority.

Finite catalog child steps are inner execution activities under that same Task
and JobHandle. Child activity/thread and behavioral role versions remain distinct
from canonical Agent ids. They have no independent Task ledger lease or CT47
write authority. A future canonical leaf Subagent must use existing frozen spawn
narrowing and this same acceptance contract; a child name alone grants nothing.
Separate nested operation invocation retains the inherited exactly-one nested
Mission/TaskGraph/JobHandle cardinality. Its independently admitted operation
Task and JobHandle are referenced by effect receipt; they are not folded into
the catalog child's thread or substituted for the parent execution Task. General
graphs still compile through existing MissionCompiler/TaskGraph machinery.

CT47 author attribution remains ExperimentAuthoring/ExperimentSpecService-owned:
the actual admitted authoring Task lease holder, Task attempt and observed model
deployment produce provenance. The mapping supplies no experiment.register
permission. Catalog children cannot inherit authoring_task_id implicitly. Study
operation acceptance and original-context public projections stay with the Study
lane, including cross-owner/stale-context refusal.

## Certainty, recovery and terminal precedence

Request, child, JobHandle and Task states remain separate vocabularies. The join
returns an observation and evidence references; only JobHandleService and its
dispatcher mapping may apply canonical terminal transitions or release leases.

1. An independently reconciled canonical terminal receipt wins over request or
   child telemetry. Report actual canonical state (`done`, `failed`, `cancelled`,
   `aborted`) and its evidence, keeping contradictory Request state visible.
2. Any unresolved observed non-read effect, missing acknowledgement after intent,
   unknown nested JobHandle or lost canonical owner is `unknown` certainty.
   Retain canonical leases. Request `failed`, `interrupted`, `cancelled` or even
   `completed` cannot settle it. Refuse resume/retry until existing authorized
   reconciliation supplies a durable resolution.
3. Completed child/effect receipts may repair the graph cursor without replaying
   observed effects. Persist intent before effect, observed result before cursor
   progress, and reconcile all effect namespaces before a Request retry.
4. In-flight work with no unresolved effect reports running, queued or requested
   cancellation separately. Cancellation intent is not a terminal outcome.
5. Fully observed bounded success is a candidate for the host completion adapter,
   never proof of canonical completion by itself. Failure known to precede any
   effect can be proposed to existing canonical completion rules. No unknown
   inference is relabeled exactly-once; explicitly permitted retry is a new
   observed attempt and retains accounting.

Cancellation targets the canonical JobHandle.cancel authority for joined work.
The existing service applies a terminal cancelled transition immediately, so the
join must first inspect effect intent/receipts and child/nested certainty while
holding the existing completion/authority locks. Unresolved effects or unknown
children require existing lost-certainty handling and refuse terminal cancel;
they retain leases until unknown.resolve. Otherwise the host propagates bounded
Request/child cancellation and applies canonical cancel only after known
noncompletion or a never-dispatched observation. A racing completed canonical
receipt wins by the existing first-terminal rule. Named child cancellation uses
the same parent gate. Detach cancels nothing. Accepted operations may finish
after cancellation intent; persist their real receipts before terminal resolution.
After an independently justified canonical terminal transition, late receipts
remain evidence and never overwrite that first terminal or replay the effect.
Resume targets the
original Request only after original input/identity, current context/grants,
mapping and canonical authority are revalidated. JobHandle unknown.resolve stays
an independent privileged reconciliation command, never a Request resume alias.
Its current outcomes are terminal: after resolution the original canonical
JobHandle cannot be revived by Request retry. Repair a missing Request projection
from recorded evidence without a provider call; further work needs independently
admitted replacement authority. AgentCapabilityStore is currently volatile:
restart requires rehydrating the original authoritative frozen spawn record via
its owning host path. Missing records refuse; never respawn from renderer fields
or treat the join's audit snapshot as a new capability grant.

## Provider-neutral memory compatibility

Use the complete existing ActorMemoryScope(principal, behavioral_actor_id,
role.key, MemorySource(host-workflow key, workflow digest, role locators,
original authority binding)).namespace unchanged. Canonical attribution never
substitutes its ActorId into the namespace. Changes to role/workflow/authority
continue isolating memory. Two jobs at identical complete scope may recall its
existing admitted memory; fresh child threads do not change that scope. Mapping
aliases, canonical reassignment and app/global contexts do not pool it. Provider
selection remains reserved to the user; this contract installs or selects none.

## Activation gate and acceptance

Study's reviewed final commit must first be composed without uncommitted source
imports. Review shared process.py callbacks before attaching this join. Reuse the
existing execution admission/completion/acceptance hooks and their lock ordering;
do not add a scheduler or parallel authoring implementation. If those hooks
cannot preserve this contract, report the concrete seam rather than duplicating
Study ownership. Prepared contract text does not claim activated runtime behavior.

Gate: actual paired two-job journey, host admitted Quant/Task/Agent/JobHandle join,
mapping collision/retirement and conflicting caller refs, child grant narrowing,
unchanged exact memory scope, disk restart after effect observation before final
Request persistence, unknown child retaining lease, late completion after cancel,
retry refused until reconciliation, original-context/cross-owner result refusal
and zero duplicate observed non-read effects. Keep exact source import paths,
commands, failures and skipped/unrun gates. Independent runtime/conflict review
is required before calling the composed join accepted.

## Source anchors

Implementation checkpoint clarification (2026-10-04): the host admission/continuation
guard and owned result observation are implemented as a local candidate. Bounded
success remains observed while the canonical JobHandle stays running until its
existing owner completes it; no Task Ledger fact is manufactured. Interrupted
joined Requests cannot retry. Reassignment to a second Task attempt is conservatively
refused and needs a separate reconciliation facade; independently admitted fresh
Tasks remain supported. Missing final snapshots recover observed bytes into an
interrupted Request only, with unchanged disclosure checks. Restart retains durable
uncertainty and refuses missing volatile authority. These explicit v1 limits narrow
the proposed contract, rather than claiming the full lifecycle gate above is done.
The delivery manifest records exact tests and independent findings/fixes.

- qma.core.ontology.actor_id.ActorId / ontology.records.Quant, Agent, Subagent.
- qma.daemon.bus.mailbox.MailboxStore.quant_for (actual ontology record lookup).
- qma.daemon.capabilities.spawn.AgentCapabilityStore (frozen recorded spawn).
- qma.daemon.taskgraph.dispatcher.TaskGraphDispatcher task_for,
  dispatch_lease_for, accepted_task_for_invocation and durable projection.
- qma.daemon.envs.jobs.JobHandleService / core.ports.jobs (canonical ownership,
  exactly one handle per Task, coordinated cancel and unknown.resolve).
- request_runtime.experiment_authoring.ExperimentAuthoring (existing CT47 owner).
- request_runtime.service.RequestRuntime (acceptance and execution hooks).
- request_runtime.actor_workflow / durable_memory.ActorMemoryScope (legacy keys).
- task-22 ARCHITECTURE-SPINE AD-2, AD-5, AD-8..10 and packet 03; existing CT46,
  CT47, Task ledger and compile/nested-Mission cardinality rules.
