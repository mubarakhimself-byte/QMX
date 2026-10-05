# Draft canonical partition retry authority v1

Starting source: d73aa3723ad438173d52a0b1eed576d74516001c. This is a bounded implementation contract, not ratified documentation or live-operation authority.

## Supported vertical slice

Only an existing canonical authored deterministic path with exactly two read nodes followed by collect is supported. The first read must have an exact observed effect. The next read must carry durable known pre-dispatch refusal evidence from its own validator, before any effect intent exists. Missing evidence, abrupt loss, timeout, pending intent and UNKNOWN effect never become FAILED partitions.

`CanonicalRequestJoin.reconcile_partition_retry(request_id, *, principal, owner, dispatch_lease, partition_id, definition_revision, join_revision) -> Result[JoinRetryPlan]` is host-only explicit admission. It uses the existing TaskGraphStateService JoinState and partial retry algebra at the collect node and its exact incoming edge. Original Task, Job, graph, dispatch lease, Agent/session, tool, catalog, capabilities, ProductSession, grant and memory binding are unchanged. Current original-owner reconciliation remains required and paired resume is a separate action.

A pre-dispatch context refusal for the second read records its exact request attempt, partition identity, tool and exact authored arguments before interruption. The bounded Request is interrupted, and the canonical Task/Job remains UNKNOWN. Storage loss, arbitrary exception and outcome_unknown do not mint this evidence.

Admission requires definition revision equal to the authored workflow version and join revision 1, the selected second read exactly, one DONE first partition with its original effect identity and one FAILED known refused second partition. The immutable plan is volatile and targets exactly the next Request attempt. Durable join/retry receipts are history and cannot authorize work after restart. Admission rechecks current grants and original frozen authority. Changed join/effect/refusal snapshots after admission refuse before execution. Successful partition identity remains unchanged.

Separate resume continues the existing LangGraph cursor without another Request submission or canonical Task/Job attempt. The retry effect keeps the original second-read logical identity; no accepted or pending effect is redispatched. Existing join retry result folding records the newly observed second effect and keeps the successful first result identity. The admission receipt binds the exact join ID; canonical projection refuses a missing or mismatched graph/edge and exposes the exact two partition identities under the unchanged join definition. A sibling join on the same graph/edge cannot substitute. Request completion does not resolve canonical UNKNOWN.

## Refusal journeys

No explicit partition admission; wrong partition/revisions/owner/principal/lease; missing known failure; pending or UNKNOWN effect; mutated graph/catalog/Task/Mission/tool/capabilities/session; revoked or expired grant; changed join snapshot before resume; released/replaced live lease; durable receipt without fresh admission. Original owner reconciliation alone cannot bypass a recorded partition refusal.

## Evidence and remaining boundary

Real authenticated paired sockets, canonical owners and persisted journals are exercised. Availability/fault fixtures and all inference are explicitly synthetic; no live model, trading, remote service or credential use. Independent review and frozen-source regression gates remain required. Replacement/reassignment, unknown-effect resolution, broader partition topology, environment settlement, cron and production stale-writer handling stay outside this slice. Production writer locks are never cleared by runtime changes.
