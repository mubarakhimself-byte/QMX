# Explicit canonical owner reconciliation — local implementation draft

Base: reviewed `1531eecb4c057f35ede2ec7fc5085fbe1451b286`. Authorized boundary:
`authored-quality-composed/delivery/NEXT-TASK-BOUNDARY.md` in the October 5 delegation.
This describes a bounded backend increment; it does not ratify the corpus or activate a provider.

The chosen contract restores the **original** executing Agent and dispatch lease.
Replacement Agents, replacement Task/Job attempts, partition retries and cron remain outside scope.
The host explicitly spawns that Agent through the existing AgentCapabilityStore, then calls
`CanonicalRequestJoin.reconcile_owner(request_id, principal=..., owner=..., dispatch_lease=...)`.
Its owner, Agent session, full frozen capability digest, original lease and all Task/Mission,
graph/catalog, ProductSession, qualified callback/registry, grant and resource pins must match
the immutable acceptance. Current session and grants are rechecked, including expiry/revocation.
Receipts never reconstruct an Agent, renew a grant or queue a request.

Only an interrupted authored path with an exact contiguous **observed read prefix** and no
possibly started specialist or memory projection activity qualifies. Pending, missing/mismatched,
foreign or out-of-prefix effects refuse; no unknown effect is reclassified as failed.
Each process must explicitly admit recovery; historical admission receipts alone grant nothing.
Within that process an admission targets exactly one next Request execution attempt. Repeating
admission before resume is idempotent; paired `resume_agent_request` remains the separate action.
The runtime serializes the queue transition, so competing resume calls cannot execute twice.
The existing graph cursor and effect identity return predecessor observations without redispatch.
No graph/checkpoint scheduler is added.

TaskGraphDispatcher restores only its volatile Task/ledger cache and the admitted original
lease from the existing durable graph. It refuses conflicting Task/ledger/lease state or any
retained environment lease/slot. It restores only fresh-process cache loss; it refuses
a lease missing from an already materialized live Task and never reacquires a released lease. It does not mint/release environment slots, redispatch, reassign,
change attempts or fabricate terminal Job evidence. After abrupt loss the existing Job-to-Task mapping folds Job UNKNOWN into Task UNKNOWN
once its original dispatch authority is explicitly admitted. No UNKNOWN state is resolved.
The joined Job remains UNKNOWN, and bounded
success remains evidence. Its Task/Job owner retains resolution authority and accepted history.
Admission write loss cannot create a recovery token. Every execution/continuation checks the
current original lease, frozen pins and grant, so later loss or replacement refuses further work.

Required evidence: actual authenticated paired socket restart journeys, original effect and
acceptance preservation, current owner/lease/pin/grant negative journeys, independent process
loss/restart oracle, independent Standards/Spec review, immutable source seals, focused/composed/
Study regressions and unchanged strict gates. Scripted inference is synthetic; no external
provider quality is established. Existing documentation/coverage/QMB ambient debts remain visible.

Next bounded increment: explicit partition retry/join authority preserving successful partition
ids and UNKNOWN effect/lease state. Cron stays disabled; only later may an existing
RoutineScheduler/CT49 occurrence adapter be considered. No UI/CORTIS/Lab, new scheduler, remote
service, credentials, paid inference, live trading, publication or protected-ref changes.
