---
id: ADR-0029
title: Controlled canonical request attribution in the QMA host
type: adr
status: draft
depends_on: [COMP-QMA-DAEMON, COMP-QMA-CORE, COMP-QMA-WIRE]
decisions: [DEC-0305, DEC-0311, DEC-0316, DEC-0317, DEC-0342, DEC-0421, DEC-0453]
sources: [_docwork/canonical-request-join-v1.md, docs/decisions/ADR-0028-mature-agent-runtime.md, docs/contracts/ct-43-qma-memory-provider.yaml, docs/contracts/ct-46-qma-execution-environment-job.yaml]
generated: 2026-10-04
verified: 2026-10-04
stale_after: 30d
---

# Controlled canonical request attribution in the QMA host

The October 4 delegation authorizes isolated backend integration, local commits,
offline tests and independent review. It supplies implementation scope, not a
ratification of every assumption in the task-22 architecture draft. This record
describes the bounded local candidate; production activation and corpus adoption
are separate acts. Source pins and failed, skipped and unrun gates remain in the
integrator's delivery manifest.

## Reuse preflight and scope

Verdict: **reuse COMP-QMA-DAEMON**. The dependency inventory, stack, daemon/core/wire
specifications and CT-46 assign execution admission, single-writer persistence,
Task state and JobHandle transitions to existing host owners. Core supplies
definitions and frozen capability records; wire supplies authenticated doors;
neither owns a second request scheduler. Existing RequestRuntime admission hooks,
TaskGraphDispatcher, AgentCapabilityStore, MailboxStore and JobHandleService carry
this change. The new internal attribution module owns only mapping and acceptance
receipts. No component, database, listener, numbered contract, canonical Agent,
Quant, Task, Mission or JobHandle is minted by it. QMB Study still enters through
its existing transport and ExperimentAuthoring remains the CT-47 authoring owner.

The blast radius includes the daemon, its definitions and wire contracts, current
Task/Job scenarios, ownership/disclosure security rules and existing runtime ADRs.
No UI, native session, provider authentication, money-path or deployment behavior
is changed. Existing named boundaries remain narrower than host configuration.

## Attribution and cardinality

An explicit trusted host plan binds `(principal, behavioral actor)` for its
lifetime to one existing active Quant. Same-owner catalog revisions advance one
step; retirement is permanent; accepted work pins its original mapping/catalog.
CopilotProfile remains behavior and is distinct from ontology Profile metadata.
Aliases naming the same Quant retain their separate exact behavioral memory scope.

Acceptance resolves an existing durable running Task, its retained dispatch lease,
actual frozen Agent capability snapshot, admitted Agent-session/ProductSession/
profile input references and the Task's existing active owned JobHandle. Caller
metadata cannot construct this authority. One bounded Request attaches to one Task
ledger attempt and one existing JobHandle. Child records remain inner activities
and do not confer canonical Subagent admission or CT-47 authorship. Task, Request
and JobHandle attempts keep their existing distinct meanings.

The v1 implementation refuses a second joined attempt on the same Task after
reassignment. It requires a separately admitted fresh Task; a general reassignment
and recovery facade must prove prior reconciliation before relaxing this fence.
Nested public operations retain one independently admitted nested Mission,
TaskGraph and JobHandle rather than merging live graphs.

Joined v1 routes are explicitly tool-free. Behavioral aliases are not canonical
qualified tool IDs; legacy toolset expansion can contain those aliases without
establishing Agent permissions. Nonempty joined routes therefore refuse before
inference. A separate host-owned bridge must resolve an actual callback binding
to an already admitted available ToolRecord, pin its descriptor/target/grant/scope,
and check both frozen Agent tools and permissions before admission and use.
The existing research-corpus search tool is not metadata browse. This candidate
does not register a browse tool, relabel search or invent a mapping from aliases.
Existing unjoined read workflows retain their ProductSession grant checks.

## Certainty, cancellation and recovery

Original canonical authority is checked before model/tool continuation. Lost
owner authority, lost child outcomes and pending effect receipts retain UNKNOWN
through existing JobHandleService before the attribution observation is appended.
Failure to append the observation cannot make the interrupted Request retryable.
The first canonical terminal state remains authoritative. Operator unknown.resolve
does not revive the old bounded Request. A fresh Task has its own authority; the
attribution module does not resolve UNKNOWN itself.

Bounded owner cancellation remains available after retirement or capability loss.
It sets the existing Request cancellation token and does not author a canonical
terminal outcome. Direct and paired canonical cancellation additionally require
the persisted bounded cancelled snapshot and exclusively observed effect receipts.
Running, interrupted or completed Request telemetry cannot prove noncompletion.

Persisted observed result bytes can repair a lost final Request snapshot into an
interrupted Request. This recovery performs no inference or effect and does not
settle the Task/JobHandle. Current ownership and disclosure checks still gate
public content. Missing volatile frozen Agent/dispatcher authority after restart
refuses continuation; receipts never recreate it. Durable Task uncertainty remains
stored even when the in-memory dispatch lease cannot be reconstructed.

Bounded success and known failure currently remain observations while canonical
completion stays with existing Task/Job owners. This candidate does not turn a
model result or harness trace into an agent-authored Task Ledger entry. An end to
end canonical completion/reassignment facade is a remaining implementation seam.

## Provider-neutral memory and scoped amendment direction

The delegation reserves memory backend selection to the user. The later attended
direction explicitly requests Hermes-style pluggable providers/configuration,
without choosing one provider. This is the provenance for reconsidering the
inherited CT-43/DEC-0317/DEC-0342 no-default/in-house-adapter conflict; the architecture
draft alone did not authorize that amendment. [DEC-0317] [DEC-0342]

The authorized direction is to reuse the existing typed provider/plugin seam with
host-selected identity and pinned revisions, deterministic host admission,
provider-neutral exact scopes and journal traceability. It permits adapters as
implementations of that seam; it does not activate a backend, a default provider,
cross-owner or user-wide pooling, automatic lifecycle effects or memory-derived
effect evidence. Existing journal-backed offline adapters and legacy exact-scope
compatibility are explicitly identified as the local candidate, rather than
claimed as the previously ratified CT-43 production binding. The provider projection
interface/configuration implementation remains a separately reviewed increment.

All original ActorMemoryScope/MemorySource fields and research scopes remain
unchanged. Behavioral memory continuity never grants canonical execution authority.
Expired legacy recall is repaired by the independently reviewed memory lifecycle
commit; admission, source/current-authority checks, tombstones and effect receipt
truth retain their owners.

## Acceptance limits

The candidate requires offline focused and composed gates, actual paired request
journeys, unknown-child/observation fault tests, cancellation, persisted ownership,
disk restart, source provenance and two independent reviews. A passing focused
suite does not imply release acceptance. Strict corpus and coverage failures,
missing production providers, unsupported canonical completion and untested live
operations must remain visible in the handoff.
