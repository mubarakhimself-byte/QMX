# Clean ownership seams after composition — DRAFT

The integrator exclusively owns `process.py`, `request_runtime/provider_config.py`,
`request_runtime/domain_tools.py`, daemon `composition.py`, startup/operator
routing and shared dependency manifests/locks. Other lanes propose changes there
and deliver reviewed patches/commits. UI remains Claude-owned. No worktree is
accepted as a substitute for a pinned reviewed patch.

| Bounded next lane | Existing substrate to reuse | Proposed isolated implementation | Shared join/acceptance owned by integrator |
|---|---|---|---|
| Durable scoped memory (assigned by parent) | `memory/admission.py`, `MemoryProvider`, existing request-runtime scopes; preserve context/knowledge/ledger distinction | New durable memory module and its targeted restart/scope tests from `bf3c6b` | Explicit request config/runtime binding; actual query scope, persistence and refused leakage tests |
| Actor lifecycle + operator ingress | `qma.core.ontology` Desk/Role/Quant/Agent/Subagent, `bus/mailbox.py:open_for_quant`, durable journal, frozen capability spawn | New `actors/registry.py` service with canonical typed records and journal fold; operator-owned creation/admission; role behavior resources are declarative | Composition injects registry; mailbox owner lookup joins canonical actors; add strict wire command/capability only after contract review. Reopen real Quant without recreating identity; deny renderer-forged lease/model |
| General workflow/child execution | `taskgraph/dispatcher.py`, `nested.py`, graph templates, RequestRuntime and LangGraph checkpointer | New authored workflow compiler/runner module using existing TaskGraph identities/leases; bounded child scopes and checkpointable state | Integrator binds startup/routing; parent/child result joins, cancellation/unknown occupancy and restart with no repeated observed effect. No second scheduler/task graph |
| Legitimate CT47 authoring | `experiments/service.py:register`, dispatcher current accepted task/lease/attempt; actual ProviderResult deployment | New `request_runtime/experiment_authoring.py` parsing spec content into existing ExperimentSpec; never accept caller-supplied owner/Agent/deployment authority | Host derives actual dispatch and observed deployment, routes into existing registration; same registering/executing task and mission. Real recorded provider protocol can prove transport; synthetic identity cannot prove legitimate production authoring |
| Public persisted QMB projection | `backtest/service.py` durable expected/result artifact verification; `qmb/host/operator_replay.py:project_operator_replay`; CLI door payload | New host selector/context bridge module; named resolved-run selector extension with compatibility for existing spec selector; no arbitrary latest selection | Integrator places read query with correct occupancy and grants. QMB door consumes original pinned context, predicate and as-of. Publication separately requires legitimate dispatch; deny crossowner, ambiguity, corrupt/missing artifacts |
| Paired observations/correction fold | QMF CT15 authority, source boundary, CT10 raw bytes; QMB replay resolution | Owner proposes versioned paired representation preserving original native receipt identity, then correction resolution fold | Compatibility/version evidence, bid+ask frontier, immutable old replay and corrected new replay; no receipt/native-ID relabeling |
| CI/quality/dead code (assigned by parent) | Existing gate/scanner/task scripts; preserved red gate evidence | Isolated pipeline/test-quality fixes; reachability/compatibility inventory before deletion | Review shared-file changes; preserve security/coverage floors and product behavior. No scanner-count milling |

These are clean implementation proposals, not claims of completed capability or
permission to provision remote infrastructure. Existing code bodies explain why
the actor and authoring seams are needed: MailboxStore currently caches Quant
objects in `_quants`, and `open_for_quant` records a mailbox projection rather
than an operator-facing durable actor lifecycle. `ExperimentService.register`
checks a supplied lease and deployment but cannot establish that a provider
actually authored the content. Normal process routing requires canonical
ownership/dispatch records before QMB execution and correctly refuses their absence.

Recommended order: reviewed combined milestone; durable memory integration;
canonical actor/dispatch ingress; legitimate CT47 authoring; public projection;
general workflow/child execution. Data paired/correction work can proceed through
its own reviewed contracts. Remote transport/endurance remains a separate future
execution acceptance task without provisioning in this sitting.
