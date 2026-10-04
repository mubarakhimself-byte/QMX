# Provider-neutral memory lifecycle validation

This is implementation evidence for packet 5, not provider admission or a new
architecture decision. Baseline: actor `71518e4ef72733ca43ce06e0f1c31ef9b35b1277`
plus the reviewed central grant repair
`29f75aa6dabcb6101487d07e1171f475be6aa25e`. An isolated local bare clone and
worktree preserve the source checkout. Reuse COMP-QMA-DAEMON and its existing
CT-43 core port, admission gate, JournalRecords and AuthoritativeJournal.

The Mini Apps intent remains: workflows organize work, optional specialists
perform bounded steps, and one Copilot capability supports many sessions.
Behavior, context, retained knowledge, memory and authored ledgers have separate
owners. No Task/Job cardinality or canonical actor join is decided here.

## Actual scope boundaries

| Surface | Current implementation | Verified boundary / remaining gap |
| --- | --- | --- |
| Request/run | RequestRuntime admits principal, ProductSession, context revision, host behavior profile and provider. Graph and child threads are per request; memory IDs carry request/activity provenance. | Request/thread ID is not itself a memory grant or namespace. No dedicated Task/run memory provider scope is implemented by this adapter. Canonical Task attachment belongs to the integration lane. |
| Research workflow | ResearchMemoryScope hashes all seven fields: principal, application, profile, authority_binding, source_id, snapshot_ref, locators. Existing `research-summary:` encoding is retained. | Exact unchanged scope recalls across fresh jobs and disk reopen. Changing any field withholds previous memory. Specialist/version is provenance, not a separate field in this namespace; do not claim specialist-version isolation here. |
| Actor specialist | ActorMemoryScope hashes principal, behavioral actor_id, collection and complete MemorySource (source_id, snapshot_ref, locators, authority_binding), with existing `actor-memory:` encoding. | ActorWorkflowProvider supplies role:version as collection/locator, host-workflow:workflow:version as source_id, the full workflow digest as snapshot_ref, and admitted row.context_binding. Daemon restart journeys verify a workflow-version change and a combined role/workflow-version change. The immutable workflow pin requires a new workflow version for changed role references; independent role-only daemon isolation is not claimed. Lower-level tests vary each namespace field separately. Unchanged scope recalls after restart with new child threads. These behavioral actor IDs are not canonical ActorIds/leases. |
| Application | Research scope includes host-resolved app_instance_id (or home); actor scope includes the admitted context binding, not a separate app field. | No automatic cross-app pooling or namespace migration. Actor app separation depends on the host context binding and its validator. |
| Copilot session | ProductSession is authority/context; QMA Session and SDK thread are different identities. RequestRuntime hashes context payload, authority profile, app instance, selected refs, granted operation IDs and relevant revocations. | Session ID is not a direct field in either memory scope. Sessions with identical complete authorized inputs can address the same scope; any continuity beyond that requires its own admitted policy. |
| User/global | Principal participates in both namespaces. `global` is a behavior profile, not an all-memory disclosure grant. | No dedicated global preference scope, user-wide aggregation, sharing policy, cross-app consent bridge or native transcript continuity is implemented. Future sharing must be explicit and host admitted. |
| Desk binding | Core MemoryProvider port and MemoryProviderRegistry define singleton-per-desk binding; DurableMemory creates a local facade/gate for the existing journal adapter. | This facade is not proof of production provider admission or a globally composed desk registry. NoMemoryProvider/staged candidates remain the core unbound contract. |

Complete namespace and live authority must come from trusted host composition.
The memory facade cannot authenticate a caller by itself: its `validate` callback
is an explicit host obligation. Neither profiles, skills, hooks, ranked recall,
proposer strings nor a remembered grant reference confer authority. Actual request
composition uses validate_continuation/validate_active_request, current grants and
the shared invocation binder; no client memory namespace selector is added.

## Current schema versus lifecycle semantics

MemoryCandidate has the seven closed validation states proposed, validated,
admitted, superseded, invalidated, expired and contradicted. That vocabulary does
not imply every transition is implemented. The existing journal adapter stores
gate-admitted typed records and implements supersede, invalidate and expire.
No public validate/contradict/consolidate operation, autonomous reflection,
learned procedural application or background extraction is introduced.

| Behavior | Verification / limit |
| --- | --- |
| Admission and source pins | Gate computes confidence; proposer-supplied confidence refuses. Wrong scope, source, locator, snapshot, authority and write-hook denial leave the journal unchanged. Declared artifact refs are not proof of possession or fact truth. |
| Supersession | One scope snapshot atomically includes predecessor tombstone and successor. Prior get/search/recall excludes it; history remains. Inactive/foreign predecessor and conflicting ID reuse refuse. Capacity failure has no partial retirement. |
| Invalidation/explicit expiry | Durable terminal revisions; ordinary reads exclude content after restart. Replayed terminal edits append nothing; re-admitting a tombstoned ID refuses. History retains old bytes, so this is not privacy erasure. |
| Deadline expiry | At now >= expires_at_ns, content is withheld without writing a terminal revision. History can therefore still show admitted. Legacy summary fallback now honors the same deadline and rejects malformed deadlines/non-integer clocks. No automatic TTL thread or erase is added. |
| Restart and projection | Disk close/reopen reconstructs active heads/history from journal. SDK InMemoryStore is built fresh per search; repeated context reads append nothing. Semantic search needs an explicitly injected embedder; local deterministic embedding fixtures exclude retired/unauthorized bytes. |
| Revocation/narrowing | Live host validator blocks reads, history and mutations. Request-level grant revocation stops child continuation and withholds results; central ceiling prevents disallowed callback/effect. Namespace changes isolate rather than pool. |
| Invocation snapshot | Research delegation_input and actor_input freeze admitted invocation context for resumable graph input. Memory retirement changes future recall; it does not erase earlier invocation/checkpoint bytes. Current request/grant validation still gates each model continuation. Stronger snapshot-retirement semantics are not claimed. |
| Effect authority | Journal intent/observed effect receipts and current grants govern replay. Memory does not settle effects, release leases, complete canonical Tasks or replace Task/Quant/Experiment ledgers. Existing child restart tests reconcile completed children without repeating observed operations. |

## Repair and tests

`ScopedResearchMemory.recall` formerly returned an admitted legacy summary even
at its deadline. The regression first failed at `assert memory.recall() is None`
with expired content returned. The repair checks the optional deadline after
source/authority validation, withholds expired content, and refuses malformed
expiration or clock inputs. Unexpired/no-deadline legacy behavior, exact namespace
encoding, typed journal schema and read-only fallback remain compatible.

Tests: `test_durable_memory.py`, `test_memory_lifecycle_boundaries.py`,
`test_memory_actor_journeys.py`, existing configured paired-socket memory,
actor/research workflow, admission and core memory suites. New negative tests
vary each namespace field independently after disk reopen and assert zero
journal writes; retirement tests verify durable states and projection rebuilding.
Fake inference/extraction and local embeddings are test-only and use no service,
model API, credential or spend.

The runner and final logs, strict typing/lint/format, provenance and independent
Standards/Spec reviews are in task-26 delivery. Borrowed installed dependency
directories are read-only with PYTHONDONTWRITEBYTECODE. This is focused offline
evidence, not a clean-install, whole-workspace coverage, production, platform
gate or remote-endurance certification. Existing mandatory release gates are
not waived by this packet.

## Integration dependencies and provider gate

Only `request_runtime/scoped_memory.py` is changed at runtime. Actor/research
workflow composition, daemon process, SDK factory, invocation binder, ontology
and wire contracts stay with their owners. Preserve complete current namespaces
through canonical attribution; a canonical join never implicitly rewrites IDs
or enables pooling. The integration lane owns any future binding adaptation.

The user reserved provider selection at 17:24 and subsequently authorized
evaluation of the Hermes pattern for pluggable memory providers/configuration.
That pattern evaluation is recorded in HERMES_MEMORY_PROVIDER_FIT.md; it does
not activate a backend. Existing optional LangMem extraction is preserved and
tested with its installed pinned extra; no provider or default is selected.
CT-43/DEC-0317/DEC-0342 NoMemoryProvider/no-in-house-engine
wording and current JournalMemoryProvider usage remain an admission-provenance
and possible scoped-amendment discrepancy. Selection/admission blocks production
provider ratification, not these bounded provider-neutral lifecycle checks.
