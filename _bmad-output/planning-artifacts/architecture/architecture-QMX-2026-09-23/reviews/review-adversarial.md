---
review: adversary
target: ARCHITECTURE-SPINE.md (QMX pack-and-grant kit, 2026-09-23)
companions: [CONTRACTS.md, COPILOT-AND-APPS.md, JOURNEYS.md, IMPLEMENTATION-SEQUENCE.md, REQUIREMENTS-ADDENDUM.md]
parents_read: [architecture-QMX-2026-09-18 AD-1..AD-31, parent CONTRACTS.md envelope/GrantRecord/product_session, DEC-0300 contribution points, DEC-0304 correlation_id origins, DEC-0112/0200/0322 log-vs-journal-vs-telemetry, SCN-0021]
inspected: [docs/components/qma-core.md contribution roster, docs/components/qma-wire.md DEC-0304, docs/components/qma-daemon.md telemetry, docs/components/trading-node.md TN-15 JSON-lines fields, docs/scenarios/SCN-0021-outbox-jobhandle.md]
date: 2026-09-23
lens: 'Attack the spine as an adversary: construct two units one level down that each obey every local AD to the letter yet still build incompatibly — clashing shared-data shapes, two owners of one entity, conflicting mutation paths, copilot/session forks, observability field forks, retry dialects. Every pair is a hole. Also check local ADs do not weaken parent architecture-QMX-2026-09-18 AD-1..31.'
---

# Adversary review — pack-and-grant kit spine (2026-09-23)

## Method

For each local AD (AD-1..AD-8) and the inherited 09-18 joints this sitting binds, build **two conforming units one level down** — factory epics Sequence 1–4 would actually spawn (pack SDK / optional `app_instance_id`, `caller_kind` on the envelope, daemon JSON-lines + diagnosis query, default host retry, nested Mission invoke) — and ask whether both can obey every written local Rule plus every inherited parent Rule and still be unable to assemble.

Only pairs where **both readings are literal** are reported. Named parent amendments and Deferred rows count when Slice 0 must already pick a shape. Companions (`CONTRACTS.md`, `COPILOT-AND-APPS.md`, `JOURNEYS.md`) count when they are the only payload a factory lane would copy. Findings end with paste-ready Rule text.

Parent 09-18 AD-1..AD-31 bind read-only. A local AD that overloads a parent field (`app_instance_id`, `selected_refs` kinds, contribution `point`, `instance_id`, `correlation_id` mint origin, JobHandle vocabulary, listing axes, retry/reconcile) without a typed discriminator **and** a complete named parent amendment is a hole, not a license. Brownfield at `integration@34c148b` (fixtures) and parent freeze at `270e992` are in-scope: the spine cites both.

Named checks demanded by this pass: shared-data shapes; two owners of one entity; conflicting mutation paths; copilot/session forks; observability field forks; retry dialects; local ADs must not weaken parent AD-1..31. Each Critical below is one of those joints.

## Verdict

**Return for amendment — do not freeze Sequence 1–4 (pack SDK, diagnosis query, default retry, nested Mission, authoring-without-instance).** Intent is tight: no sixth COMP, json-render/MCP Apps are paint, nested invoke does not union grants, app-use cannot apply a change-request, logs are not journals. The AD set fails at the joints those epics would implement.

Five load-bearing joints let two conforming units ship incompatible products: (1) authoring `app_instance_id` MAY be absent, but envelope/GrantRecord still require `instance_id` and parent `selected_refs` cannot name an app/instance; (2) “default host retry” plus “pack may declare tighter” has no schema, so it forks against parent AD-24/AD-25/AD-26 and against change-request repair; (3) diagnosis is three surfaces (JSON-lines, QMA telemetry, headless query) with forked field names, a `widget` failure class, and `granted` vs `authorized` listing axes; (4) workflow-to-workflow is a nested Mission, an AD-10 invoke, and an AD-7 compile at once; (5) local AD-1 treats `view:*` / copilot profile as contribution points, which parent AD-2 / QMA AD-1 / DEC-0300 already forbade.

Sequence 1 as written **is** the work that forks. Closures that hold (no sixth COMP, app-use cannot apply, HMR dead, QMN allow-list not reused, two-valued `ProductSessionProfile`, adapters unpinned **if** `view:*` stays a wire DTO) are not the problem. The problem is the **new identity, owner, retry, and log surfaces** local AD-1/AD-3/AD-4/AD-5/AD-6 introduce without a single home.

| Tier | Count |
| --- | --- |
| Critical | 5 |
| High | 4 |
| Medium | 3 |

Pairs that could **not** be made to diverge (closures that hold): minting `COMP-WF` / a sixth application; json-render imported as a domain executor (the residual hole is contribution-point authority, not an n8n-style runtime); app-use applying `change_request`; HMR / hot-apply; stuffing mini-app alerts onto `qmn/FAILURES.md`; a third `ProductSessionProfile`; merging two live Task Graphs as an *allowed* path (refused in prose). Those are not the problem.

---

## CRITICAL

### C-1 — Local AD-3 × AD-8 amendment × parent AD-8/AD-9/AD-13/AD-24: authoring-without-instance cannot invoke (copilot/session fork, shared-data, two owners of grants)

**The rules as written.**

- Local named parent amendment: for `profile=authoring`, `app_instance_id` **MAY be absent** (main/home, nothing selected). For `profile=app-use` it remains required. No third profile.
- Local AD-3: main authoring may `selected_refs` other **apps**, templates, and artifacts; nested invoke still does not union grants (parent AD-10). Context transfer is explicit `selected_refs` or `change_request` only. An instance **may omit** an in-app panel. Pack **may omit** a copilot profile.
- J-KIT-03: authoring session with **no instance selected**. Operator selects app B as `selected_refs`. Invoke of B’s op uses **B’s GrantRecords**, not a union with A.
- Parent AD-8 durable fields include `app_instance_id` (pointer to plugin-install instance row) and `granted_ops` (array of `grant_id`). Closed `selected_refs` kinds: artifact fp1, `research_ref`, contribution `(qualified_id, package_version)`, template `(qualified_id, version)`, dataset/run/attempt refs, node-id sets citing a template. **Forbidden:** layout JSON, positions, widgets, json-render trees. **Not in the closed set:** `instance`, `app`, `mini-app`, `pack`, `psess`. Installation/upgrade MUST NOT retarget `app_instance_id` or mutate `granted_ops`.
- Parent AD-24: `InvocationEnvelope.instance_id` is bound and compared on every hop; ambiguous instance/config **refuses**. `GrantRecord.instance_id` is required. Envelope is not authority; host resolves GrantRecord from store.
- Parent AD-9: tool availability = intersection of published ContributionHits, host grants, **product_session GrantRecords**, health.
- Parent AD-13: `instance_id` (installed mini-app) is a distinct identity from contribution `(qualified_id, package_version)`.

**Unit A — home-session overlay (local amendment purist).** One `psess:` per principal with `profile=authoring`, `app_instance_id` null. `granted_ops` on that row is empty or principal-global. Selecting app B writes `selected_refs: [{kind: "instance"|"app", id: "inst:B"}]` (illegal parent kind, required by J-KIT-03). At invoke, host **looks up B’s GrantRecords by instance**, not from `product_session.granted_ops`. Envelope.instance_id is filled from the selection. Authoring `granted_ops` is unused. Copilot tools for B appear because the host special-cases home.

**Unit B — session-is-the-grant-bag (parent AD-8/AD-9 purist).** `granted_ops` on the authoring `psess:` **is** the intersection AD-9 reads. To invoke B, B’s `grant_id`s must already sit on that row — a **union of instance grants on one session**, which local AD-3 / parent AD-10 say nested invoke must not do. Select of B is a CAS `granted_ops` mutation (parent forbids install/upgrade from doing this; select is a named wire command, so B treats it as re-grant). `app_instance_id` is patched to `inst:B` when something is selected (making the “MAY be absent” amendment a no-op whenever invoke is possible). Envelope.instance_id always equals session.app_instance_id.

**Unit C — mint a hidden app-use child.** Authoring stays instance-less. Selecting B **creates** `psess:` profile=app-use with required `app_instance_id`. Invoke happens on the child. Context transfer is implicit session mint, not only `selected_refs` / `change_request` (local AD-3). This is a third seat in practice, which Deferred forbids.

All three obey some local AD-3/amendment sentence and some parent AD-8/AD-9/AD-24 sentence. What diverges:

- **Shared-data shape.** `app_instance_id` null vs sentinel vs patched; `selected_refs.kind` ∈ {contribution, instance, app, artifact}; envelope.instance_id sourced from session vs selection vs child session; `granted_ops` empty vs union vs child-only.
- **Two owners of one entity (the grant).** COMP-QMA-DAEMON product_session row vs GrantRecord store keyed by instance vs a child app-use session. AD-9 intersection has three different inputs.
- **Conflicting mutation paths.** A’s select writes only `selected_refs` (kind the parent does not list). B’s select mutates `granted_ops` and/or retargets `app_instance_id` (parent AD-8 install/upgrade ban, stretched over select). C mints a new `psess:` as a side effect of select (parent AD-29 mutate vs create).
- **Copilot/session fork.** A: one home copilot, tools teleport by selection. B: one session, tools = that row’s grants; selecting B silently widens. C: every “open app B” is a new independently scoped session (matches COPILOT-AND-APPS “independently scoped” better than A/B, and invents the third seat the spine refused).
- **Parent weakening.** Optional `app_instance_id` is named, but the amendment does **not** amend envelope/GrantRecord `instance_id`, AD-9 intersection, or the closed `selected_refs` kinds. Incomplete amendment = silent override of AD-24 “ambiguous instance refuses” (A guesses) or of AD-10 “no union” (B unions on the home row).

**Tightened Rule (replace the AD-8 amendment; fix local AD-3 / J-KIT-03 / CONTRACTS §3).**

> **Named parent amendment of 09-18 AD-8 (complete, or withdraw it).** `app_instance_id` MAY be null **only** on `profile=authoring` when no invoke is in flight. It is **not** a grant key, not an envelope field, and not a substitute for `instance_id`.
>
> Closed `selected_refs` kinds **gain one additive kind**: `{kind: "instance", id: "inst:…"}` (named amendment of 09-18 AD-8 closed set). Forbidden remain: layout, widgets, json-render trees, bare pack ids, `psess:` ids.
>
> **Invoke law for authoring-home.** Envelope and GrantRecord still require `instance_id`. Host resolves it from the **currently selected instance ref**, then evaluates GrantRecords whose `audience` is this `psess:` **and** whose `instance_id` matches that selection. `product_session.granted_ops` may hold grant_ids for many instances; evaluation is **filter-by-selected-instance**, never union across instances, never lookup of “B’s other session.” Absence of a selected instance ref ⇒ typed `instance_required` refusal, not a guess and not a child-session mint.
>
> Select is `mutate(..., payload.op=select_ref)` and MUST NOT retarget `app_instance_id` on an app-use row, MUST NOT mint a `psess:`, MUST NOT copy another session’s `granted_ops`.
>
> Strike “selects app B as `selected_refs`” unless the kind is `instance`. Strike any reading that authoring-home can invoke with `instance_id` absent on the envelope.

---

### C-2 — Local AD-6 × parent AD-24/AD-25/AD-26/AD-29: default host retry is an undeclared dialect (retry dialects, conflicting mutation paths)

**The rules as written.**

- Local AD-6: retry is **host/SDK behaviour, on by default for every pack**. Effect classes follow parent AD-24 / SCN-0021. A pack may declare **tighter** retry (fewer attempts) but MUST NOT declare looser than the effect class. Implementation edits are `change_request` (parent AD-29): app-use may mint; authoring + operator apply. Alerts never authorize.
- Parent AD-24: `none`/`read` may retry; `append-evidence` dedupes; `mutate-config` is CAS; `place-run` uses `logical_invocation_id` as run identity; `external-egress` obtains a receipt or becomes `unknown` and **MUST NOT blind-retry**. `reconcile_policy` is `query-then-decide` | `unknown-manual` | `never-retry`. Retry is an **evaluation moment** for GrantRecord. `attempt_id` is monotonic on the same `logical_invocation_id`.
- Parent AD-25: `unknown-blocked` is a **terminal branch of the attempt**; operator reconcile mints a **new** attempt/epoch — **never an automatic retry**.
- Parent AD-26: outbox crash recovery **replays** unacked/`dispatched`-not-accepted rows; join **partial retry** re-invokes only failed partitions. Dispatch is at-least-once; logical acceptance is under the receiver ledger.
- Parent descriptor / CONTRACTS §1: **no retry field**. Envelope has `reconcile_policy`, not `max_attempts`.
- J-KIT-06: a `read` op flakes; host retries; operator is not paged. `external-egress` without receipt becomes `unknown`. No second send.
- Research synthesis (not architecture, but the sitting’s own fork list): observe+explain+`change_request` **vs** bounded auto-retry of `none`/`read` **vs** auto-apply. The spine adopted both auto-retry **and** change-request without a matrix.

**Unit A — transport wrapper SDK.** Host retries only wire/transport `UNAVAILABLE` / timeout for `none`/`read`, max 3, exponential backoff, same `logical_invocation_id` + incremented `attempt_id`. Pack tighter = `retry.max_attempts` on the **pack manifest** (1 or 2). `never-retry` on the envelope disables even that. Task Graph outbox replay is a **different** mechanism; host retry does not wrap node dispatch. Fencing ops are excluded. After host retries exhaust, diagnosis `failure_class=host` and app-use mints a change-request.

**Unit B — effect-class re-executor.** “On by default for every pack” means the daemon re-invokes any non-terminal or `failed` JobHandle unless the effect class is `external-egress`. Pack tighter = set descriptor/envelope `reconcile_policy=never-retry` (the only parent knob). Place-run retries are “the same run” via `logical_invocation_id`. Outbox replay **plus** host retry **plus** join partial retry can fire three times for one successor. A deploy/fence op that returns `unknown` is retried because AD-6 did not name AD-25. Implementation failure (bad graph, wrong grant, wrong account) is also retried until a human pages — AD-6 Prevents “operator as the hiccup loop.”

**Unit C — pack-owned policy in the descriptor.** Each op ships `retry: {max_attempts, backoff_ms, retry_on: [UNAVAILABLE, ...]}`. Host is a library that reads it. Two packs with the same `effect_class=read` retry differently. Local AD-6 Prevents “per-pack retry dialects” — C **is** that dialect, licensed by “pack may declare tighter” with no schema.

All three obey “effect classes follow parent AD-24” and “tighter allowed.” What diverges:

- **Retry dialect.** Attempt cap unbounded vs 3 vs pack-defined; which errors; whether `failed` is retryable; whether `unknown` is retryable for non-egress; whether `never-retry` beats “on by default.”
- **Shared-data shape.** Retry config on manifest vs descriptor vs envelope `reconcile_policy` vs host global vs GrantRecord. No parent field exists; Sequence 3 must invent one.
- **Two owners.** qma-core SDK vs qma-daemon dispatcher vs COMP owner of the op (local AD-2: execution owned by the named COMP) vs Task Graph outbox (parent AD-26) vs fencing state machine (parent AD-25).
- **Conflicting mutation paths.** Host retry mutates JobHandle/`attempt_id`/outbox eligibility **without** a change-request. Change-request mutates code/graph/grants/account (local AD-6). Nothing says which path a flaky `read` that is actually a bad config must take. B’s auto-retry of `unknown-blocked` **weakens parent AD-25**. A+B together double-dispatch a successor (host retry ∩ outbox replay), weakening parent AD-26 “exactly-once logical acceptance.”
- **Parent weakening.** “On by default for every pack” can be read as overriding `reconcile_policy=never-retry` and AD-25 no-auto-retry. Incomplete: no named amendment of AD-24 envelope, AD-26 outbox, or AD-25 terminal branch.

**Tightened Rule (replace local AD-6).**

> **AD-6.** Host retry is **one** function, owned by `qma-daemon`, specified in qma-core, default **on** only for `effect_class ∈ {none, read}` and only for typed retryable refusals `{UNAVAILABLE, TIMEOUT}` (CT-04). Default cap: 3 attempts on the same `logical_invocation_id` with monotonic `attempt_id`. It MUST NOT wrap outbox replay, join partial retry, fencing/command-owner transitions, or `change_request` apply.
>
> `append-evidence` / `mutate-config` / `place-run` / `external-egress` follow parent AD-24 **only** — no extra host loop. `reconcile_policy=never-retry` and AD-25 `unknown-blocked` **win** over the default. Pack “tighter” is a single optional descriptor field `retry_max_attempts` ∈ `{0,1,2}` (0 means never-retry). It MUST NOT add error classes, raise the cap, or change effect class. No pack-manifest retry block. No per-pack backoff schema.
>
> Exhausted retry ⇒ JobHandle terminal `failed` or `unknown` as parent AD-26 already defines, plus diagnosis `failure_class=host|dependency`. Repair of implementation (code, graph, grants, account target) remains `change_request` only. Alerts never authorize. Host retry MUST share the outbox unique key so a retried dispatch cannot mint a second outbox row.

---

### C-3 — Local AD-5 × parent AD-2/AD-15/AD-16 × DEC-0200/0304/0322: three diagnosis surfaces, forked fields (observability field forks)

**The rules as written.**

- Local AD-5: for every public operation and every Task Graph run the host MUST expose, headless: (1) listing axes including `healthy`; (2) instance health distinct from pack published; (3) JobHandle in QMA AD-17 vocabulary; (4) typed refusal; (5) `correlation_id` join (**never fp1**); (6) harness-authored QMA telemetry (agents must not write it; OTel export-port only). Failure class closed: `grant` | `workflow` | `widget` | `dependency` | `host`. Daemon emits stdlib JSON-lines using **QMN field names where they apply** (`ts`, `level`, `event`, `correlation_id`) plus `instance_id`, `op_id`, `logical_invocation_id`, `graph_run_id` when present. QMB LogSink may remain; new daemon code does not invent a **third** logger. Mini-app typed failures live **beside the owning package**, not on the QMN allow-list.
- CONTRACTS §5 diagnosis query: `failure_class`, `job_handle` (or null), `correlation_id`, `healthy`.
- Local inherited table: AD-15 binds as five listing axes **published / configured / authorized / reachable / healthy**.
- Parent AD-2 listing axes: **published / configured / granted / reachable / healthy**.
- Parent AD-15 compute-placement states: **available / configured / authorized / reachable / healthy**.
- Parent AD-13 pack states: installed ≠ enabled/activated ≠ session-granted.
- QMN operator logs (TN-15 / DEC-0200): `ts` (UTC ISO-8601 `Z`, ms), `level`, **`logger`**, `event`, `correlation_id`, **`boot_epoch`**, **`composition_fp`**, typed-refusal fields (category, retryability, after-condition, reference ids).
- QMA telemetry (DEC-0322): `occurred_at` + `recorded_at` as **int64 ns**, `correlation_id`, **no `journal_seq`**, never agent-authored. Not `ts`.
- QMA wire (DEC-0304): `correlation_id` has **exactly three minting origins** — originating operator command, scheduled trigger, daemon-internal lifecycle act — copied verbatim downstream, never regenerated.
- Parent AD-16: logs are not evidence; **no other new sqlite**; closed store list. Parent AD-4: widgets are not a workflow layer. Local AD-2/AD-4: widgets **never own invoke**.
- Local AD-4 adds `caller_kind` `user` | `agent` | `workflow`. J-KIT-04 widget press uses `caller_kind=user` or `agent`.

**Unit A — logs-are-the-diagnosis epic.** Sequence 2 adds JSON-lines on qma-daemon with the four required keys plus kit extras. Copilot “why did this fail?” greps logs by `correlation_id`. Diagnosis query is a convenience fold over logs. `failure_class` is a **log field**. `ts` is ISO-8601. `correlation_id` is minted per copilot turn / widget press / workflow node (new origins). `healthy` is a log-derived bit. Listing axes copied from the inherited table (`authorized`). Widget failures log `failure_class=widget` even though the widget did not invoke.

**Unit B — telemetry-store epic (DEC-0322 honor).** Diagnosis is QMA telemetry records (`occurred_at` ns, `recorded_at`, `correlation_id`). JSON-lines are human-facing duplicates. No new sqlite (telemetry store already exists). `failure_class` is a telemetry attribute, not a log field. `correlation_id` copied from the originating operator command only (DEC-0304). Agent `caller_kind` **must not** mint telemetry (agents must not write it) — so agent-invoked ops have logs but no telemetry, or the harness authors a span the agent triggered. Listing axes from parent AD-2 (`granted`). `failure_class=widget` is refused (widgets don’t invoke); widget-originated invoke is `failure_class=host` or the op’s COMP.

**Unit C — JobHandle-is-diagnosis epic.** Headless query reads JobHandle + GrantRecord + task_graph_state. `job_handle=null` for grant refusals that never started a job. `failure_class` is computed, not stored. JSON-lines and telemetry may lag or disagree. Mini-app typed failures “beside the owning package” become per-plugin `FAILURES.md` (Deferred says register when first ids ship; C ships them now as the only typed vocabulary).

All three obey “headless diagnosis” and “no fourth observability product.” What diverges:

- **Observability field forks.** `ts` ISO-8601 vs `occurred_at` int64 ns; presence/absence of `logger`, `boot_epoch`, `composition_fp`, typed-refusal retryability; `instance_id` on logs vs envelope vs `app_instance_id`; `graph_run_id` vs JobHandle `logical_run_id` vs envelope `logical_invocation_id` (three ids, no equality law); `failure_class` vs CT-04 `family/codes`; `healthy` vs five listing axes vs three pack states.
- **`granted` vs `authorized`.** Parent AD-2 ≠ local inherited AD-15 table. Sequence 5 (“listing axes + instance health”) ships different enums.
- **Two owners of “what went wrong.”** qma-daemon JSON-lines vs QMA telemetry store vs JobHandle fold vs per-package FAILURES.md vs QMB LogSink (explicitly allowed to remain — that **is** a second logger; adding daemon JSON-lines **is** the third the Rule forbids, unless QMB LogSink is declared out of the count).
- **`correlation_id` mint fork.** A regenerates per caller_kind (violates DEC-0304 three origins if those are in scope). B copies operator origin and leaves agent/workflow joins unstated. Local Identity table lists `correlation_id` next to `grant_id` / `instance_id` as if it were product identity; parent says it is a tracing annotation excluded from fp1.
- **`failure_class=widget`.** Invents a failing object that local AD-4 says cannot own invoke. A classifies UI bind errors as widget; B refuses the class; copilot J-KIT-02 (`failure_class=workflow`) cannot be joined to a widget-started Mission (J-KIT-04) under both.
- **Parent weakening.** Treating AD-15 placement vocabulary as pack listing axes silently replaces parent AD-2 `granted` with `authorized`. Adding diagnosis as a durable failure table would be a new sqlite (parent AD-16). Minting extra `correlation_id` origins silently amends DEC-0304. Putting `correlation_id` in the Identity convention table invites fp1-adjacent misuse the Rule only half-blocks (“never fp1”).

**Tightened Rule (replace local AD-5; fix inherited table, CONTRACTS §5–6, Identity row).**

> **AD-5.** One headless diagnosis **query** owned by COMP-QMA-DAEMON, computed from existing stores (GrantRecord, JobHandle, task_graph_state, product_session). It is **not** a new sqlite class and **not** a log grep. Payload: `failure_class`, `refusal` (CT-04 shape), `job_handle` (null iff no job was accepted), `correlation_id`, listing snapshot `{published, configured, granted, reachable, healthy}` **using parent AD-2 words**, plus `instance_healthy: bool` distinct from pack `published`.
>
> Closed `failure_class`: `grant` | `workflow` | `dependency` | `host`. **Strike `widget`.** A widget-bound invoke fails as the op/Mission it started.
>
> Operator logs: stdlib JSON-lines, required keys `ts` (ISO-8601 `Z` ms), `level`, `logger`, `event`, `correlation_id` (copied, never regenerated; origins remain DEC-0304’s three; `caller_kind=agent|workflow` rides the parent origin). Optional when known: `instance_id`, `op_id`, `logical_invocation_id`, `graph_run_id`. Equality law: `graph_run_id` is the Task Graph / Mission run id; it is **not** `logical_invocation_id`; JobHandle.`logical_run_id` **is** `graph_run_id` for graph work and `logical_invocation_id` for standalone ops. Telemetry stays DEC-0322 (`occurred_at`/`recorded_at` int64 ns) joined **only** by `correlation_id`. QMB LogSink remains QMB-owned; daemon JSON-lines is the QMA operator log — count them as two allowed planes, not “no third logger” handwaving.
>
> Listing axes are parent AD-2, **not** AD-15. AD-15 remains compute placement (`available`…). Pack lifecycle remains parent AD-13. Identity table: `correlation_id` is a join annotation, not an identity.

---

### C-4 — Local AD-4 × parent AD-7/AD-10/AD-24: nested Mission vs nested invoke vs compile (two owners, shared-data, mutation)

**The rules as written.**

- Local AD-4: workflow-to-workflow callee is **invoked as a nested Mission** (`start` / `query-state` / `cancel` / `await` of that template `qualified_id`+version). Result is a JobHandle. Merging two live Task Graphs is refused. Recursion budget remains (parent AD-10). Partial failure does not silently substitute another instance, version, or account. Caller is `user` | `agent` | `workflow` on **one** envelope. Widgets bind or display ops; no fifth composition mode.
- J-KIT-05: template A has a node that **starts** template B as a nested Mission. B has its **own** JobHandle. Crash of A does not splice B’s Task Graph into A’s.
- Parent AD-7: author in Graph Templates; instantiate via Mission Compiler (**one template → one Mission**); persist one Task Graph per Mission; occupancy is environment_lease + door law, **not** a separate table; CT-47 one run per env (inherited diagram).
- Parent AD-10 modes: (1) consume artifact, (2) **invoke** exported op, (3) **coordinate** via Graph Template, (4) composite instance graph. Nested invocation does **not** union permissions. Bounded cycles of invocation require a recursion budget; template topology remains a DAG.
- Parent AD-24: nested **public calls** carry `parent_logical_invocation_id` + `call_depth`; child `logical_invocation_id` derives deterministically. Envelope binds `instance_id`, `grant_id`, contribution tuple.
- Parent AD-4: selected-subgraph execution is `MissionCompiler(template.qualified_id, template.version, node_ids)` of an **already-registered** template — not a live scribble. One compile → one Mission → one Task Graph.
- CONTRACTS §4: callee identity Graph Template `(qualified_id, version)`; verbs `start|query-state|cancel|await`; result JobHandle; no merge of live Task Graphs.

**Unit A — AD-10 mode 2 (invoke an op).** Nested workflow is an ordinary AD-3 op whose `op_id` is `workflow.start` / template start, envelope `caller_kind=workflow`, child logical id derived. One JobHandle. Occupancy/lease is the **parent** Mission’s. Cancel A cancels the child invoke (same envelope family). Grants: nested invoke intersection (parent AD-10), no new `psess:`. Host retry (local AD-6) wraps `start` as `place-run` or `read` depending on who labelled the descriptor.

**Unit B — AD-7 compile (new Mission).** Nested workflow is `MissionCompiler(B.qualified_id, B.version)` → new Mission → new Task Graph → new `graph_run_id` → new occupancy/lease. Own JobHandle (J-KIT-05). Crash of A cannot splice (good). Cancel A **does not** cancel B unless a new cascade rule exists (none written). CT-47 one-run-per-env: B may be refused while A holds the lease, or B is a second run (parent door law vs local “start”). Grants: B needs GrantRecords for its instance; if A’s grants are used, that is a union; if B has none, start refuses. `caller_kind` on B’s nodes is `workflow` (A) or preserved user/agent (unspecified).

**Unit C — AD-10 mode 3 (coordinate).** B is not nested at all: A’s Graph Template **includes** B’s subgraph at authoring time (local AD-4 “Authoring may include a subgraph into a new versioned template”). Runtime is one Mission, one Task Graph, one JobHandle. J-KIT-05 “own JobHandle” is then false, so C is a different product that still matches the include-sentence.

All three obey a sentence of local AD-4 and a parent AD. What diverges:

- **Shared-data shape.** One vs two `graph_run_id`; child id derived vs new Mission id; one vs two JobHandles; `caller_kind` rewritten vs preserved; occupancy shared vs second lease vs none.
- **Two owners of one entity (the running workflow B).** Mission Compiler (COMP-QMA-DAEMON) vs parent Task Graph dispatcher vs the pack node that “starts” B vs AD-3 op owner COMP. Local AD-2 says execution of each `op_id` is owned by the COMP on the descriptor — a `graph_template` contribution is not an op_id.
- **Conflicting mutation paths.** Cancel/await/retry on A’s envelope vs B’s Mission vs outbox of A vs outbox of B. Host retry of `start` (A) vs join partial retry inside B vs AD-25 if B places a run. Recursion budget on invoke depth vs DAG law on templates — different meters.
- **Parent weakening.** Treating “nested Mission” as a new composition path without saying it **is** mode 2 or mode 3, or a named extra mode, leaves AD-10’s closed four modes open. A second occupancy while CT-47 still says one run per env is a silent door-law break. Cascade-cancel unspecified ⇒ two cancel semantics.

**Tightened Rule (replace local AD-4 nested-workflow paragraph; CONTRACTS §4).**

> **Workflow-to-workflow is parent AD-10 mode 2, not a fifth mode and not a silent second compile.** Callee is an AD-3 operation with `lifecycle_verbs` `start|query-state|cancel|await`, contribution = the callee template `(qualified_id, version)`, envelope `caller_kind=workflow`, `parent_logical_invocation_id`/`call_depth` as parent AD-24. Host Mission-compiles **one new Mission** (parent AD-7: one template → one Mission) whose Task Graph is **not** merged into the caller’s. Two JobHandles; two `graph_run_id`s; child handle recorded on the parent node result.
>
> Occupancy: child **does not** inherit the parent’s `environment_lease`. If CT-47 occupancy collides, typed `unavailable` — no silent share, no second run in the same env. Recursion budget is `call_depth` (parent AD-10), checked before compile. Cancel parent **cancels** the child invoke (same as any nested public call); it does not splice graphs. Include-subgraph remains an **authoring** act that mints a new template version (already in AD-4) and is not this runtime path.
>
> Grants: child GrantRecords for the **child** `instance_id`; intersection with parent, never union, never reuse of parent `grant_id` on a different instance. Partial failure does not retarget instance/version/account.

---

### C-5 — Local AD-1 × parent AD-2/AD-17/QMA AD-1/DEC-0300: `view:*` and copilot profile become contribution points (parent weakening, shared-data)

**The rules as written.**

- Local AD-1: SDK contribution points are “ops, optional **`view:*`**, optional **copilot profile as a request**.”
- Local CONTRACTS §1: pack requests `contributes: {point, local_id}`, optional `view:*` DTOs (parent AD-17), optional `copilot_profile` (prompts, suggested ops) — request, `requested_capabilities` — request.
- Parent AD-2: pack `contributes` are `{point, local_id}` expanding to ContributionHit. **`view:*` is a wire DTO only (AD-17) — not a plugin contribution point and not a ContributionHit until a named GAP-0081 `ui_view` increment.** A hit is not a grant.
- Parent AD-17 / DEC-0430: pack `view:*` is a wire DTO, not a plugin point, not a json-render runtime id, not fp1. JSON Render catalog MUST name an existing AD-3 `op_id`. MCP App HTML MUST NOT grant tools.
- QMA AD-1 / DEC-0300: eight multi contribution points — `tool`, `tool_adapter`, `hook`, `skill`, `graph_template`, `model_deployment`, `toolset`, `worker_template`. **No `ui_view` in v1.** Retired candidate points `command`, `ui_view`, `mission_template` are gone. A point with no qma-wire schema may not be registered.
- Parent AD-8: packs ship a versioned **copilot integration profile as a request, not a grant.** It is not listed as a contribution `point`.
- Local AD-8 (this sitting): presentation adapters stay unpinned; json-render / MCP Apps cannot add ops or fields.

**Unit A — local AD-1 literal.** Pack manifest `contributes` includes `{point: "view", local_id: "heatmap"}` and `{point: "copilot", local_id: "default"}`. Enable publishes ContributionHits. Copilot discovery (parent AD-9) concatenates those hits. Suggested ops on the copilot profile are treated as published tools; GrantRecords still required **if** the implementer remembers AD-9. Json-render catalog keys off `view:*` contribution ids (parent said they must name `op_id` — A maps view → op informally).

**Unit B — parent AD-2 / DEC-0300 honor.** `contributes` may only use the eight QMA points. `view:*` is a wire DTO beside the manifest, never a hit. `copilot_profile` is manifest metadata, never a `point`, never in `published_contributions()`. Enable with a `view` point is `INVALID_INPUT`. Sequence 1 “pack manifest copilot_profile optional” stores a JSON blob on the plugin-install row, not a contribution.

Both obey a written Rule. What diverges:

- **Shared-data shape.** ContributionHit union includes `view`/`copilot` vs frozen eight points; pack `contributes` encodings differ; copilot_profile as hit vs blob vs skill; json-render catalog keyed by view contribution vs `op_id`.
- **Two owners.** COMP-QMA-WIRE DTOs vs COMP-QMA-DAEMON `published_contributions` vs GAP-0081 `ui_view` (deferred) vs json-render catalog.
- **Parent weakening (direct).** Local AD-1 **reopens** `ui_view` under a new spelling `view:*` and adds an unnamed `copilot` point. That is a silent override of parent AD-2, AD-17, QMA AD-1, DEC-0300, DEC-0430 — exactly what the Inherited Invariants paragraph says is a **conflict, not an override**, and then the Rule does it anyway.
- **Copilot fork.** A: omitting a copilot profile still publishes nothing; including one publishes hits that look like tools (ContributionHit treated as almost-grant — the 09-18 C-2 class of hole, back). B: profile cannot be discovered via AD-2 rails; copilot must read pack metadata through a new API the spine does not name.

**Tightened Rule (replace local AD-1 contribution sentence; CONTRACTS §1).**

> **AD-1.** Contribution points remain the parent AD-2 / QMA AD-1 roster. Pack SDK requests: `contributes` `{point, local_id}` with `point` ∈ existing multi points; `requested_capabilities`; optional `copilot_profile` **manifest metadata** (prompts, suggested `op_id`s) as a **request**, never a contribution point, never a ContributionHit, never a grant. Optional `view:*` remains a **wire DTO** (parent AD-17). Enable of `point=view|ui_view|copilot` is `INVALID_INPUT` until a named GAP-0081 increment.
>
> Json-render `action` names an existing AD-3 `op_id`. MCP `tools/call` is host-intercepted against GrantRecords. Suggested ops in `copilot_profile` are display hints; parent AD-9 intersection still gates tools.

---

## HIGH

### H-1 — `caller_kind` is either audit or a second permission system

Local AD-4 adds a closed `caller_kind` on the envelope. Parent AD-24 envelope has no such field; grants are the only invoke authority (parent AD-9/AD-17). Widgets “bind or display” but J-KIT-04 starts a Mission from a widget press.

**Unit A:** `caller_kind` is audit metadata. Any GrantRecord-allowed op is callable by user, agent, or workflow. Widget press sets `user` or `agent`. Failure class never depends on it.

**Unit B:** descriptors gain `allowed_callers`; workflow-only ops refuse `user`. Agent vs user is a privilege gate. Widget press as `agent` bypasses app-use “must not apply” if the agent is the in-app copilot. That is a **second permission system**, weakening parent AD-9.

**Shared-data:** envelope schema with/without required `caller_kind`; missing field refuse vs default `user`. **Mutation:** B uses caller_kind to block/allow change-request mint and graph start.

**Tightened Rule:** `caller_kind` is **required audit** on every public envelope, default none (missing ⇒ refuse). It MUST NOT appear in GrantRecord, MUST NOT gate ops, MUST NOT widen or replace AD-9. Widget press is `caller_kind=user` (human) or `agent` (copilot) and the host invokes; the widget is not the caller and not a grant subject.

### H-2 — Local AD-1..AD-8 collide with parent AD-1..AD-8

09-18 already minted local AD-1..AD-31 (DEC-0414..DEC-0444). This sitting reuses AD-1..AD-8 for different rules and says “Local ADs do not renumber them,” distinguishing parents only by the word “parent” in prose.

**Unit A (docs factory):** absorb as DEC-xxxx “AD-1 pack-and-grant SDK,” paralleling 09-18 AD-1 in every index, AGENTS.md, and epic card.

**Unit B:** continue the parent sequence as AD-32..AD-39 so “AD-1” remains construction-kit composition.

Citation, epic binding, and cheap-veto tables fork. This is how parent AD-8 (`product_session`) and local AD-8 (presentation adapters) get implemented as one ticket.

**Tightened Rule:** number this sitting **AD-32..AD-39** (or a prefixed `KIT-1..KIT-8`). Never reuse 09-18 AD-N. Named amendments cite `09-18 AD-8` explicitly.

### H-3 — Repair has two mutation paths with no precedence (change-request vs host retry vs outbox)

Local AD-6 Prevents “operator as the hiccup loop” **and** routes implementation edits to `change_request`. Parent AD-26 already retries dispatch. J-KIT-02 (panel asks why; mint CR) vs J-KIT-06 (host retries; operator not paged).

**Unit A:** flake ⇒ host retry; persistent fail ⇒ CR. No rule for “how many flakes before CR.”

**Unit B:** any `failed` JobHandle is a CR; host retry is transport-only (if A’s C-2 Unit A is not the partner team).

**Unit C:** Task Graph join partial retry **is** the repair; CR is only for source edits; copilot never sees `failure_class=host`.

Three repair owners: daemon retry, outbox, authoring apply. App-use copilot cannot apply (holds) but **can** cause A to retry forever without a CR.

Fold into C-2’s tightened Rule; add: copilot may **propose** CR after host retry exhausts; it may not start a second retry loop.

### H-4 — Copilot panel optional vs session lifetime (session fork, leftover of C-1)

COPILOT-AND-APPS: independently scoped resumable `psess:`; UI panels are not sessions; in-app panel optional; app-use instance required.

**Unit A:** app-use `psess:` exists whenever the instance is used headless (CLI/wire). Panel mount is chrome. Matches parent AD-21 / local AD-1 headless packs.

**Unit B:** app-use `psess:` is created on panel mount and disposed on panel dispose — except local AD-3 / parent AD-17 say dispose must not cancel work, so B leaves a zombie session or cancels queries only.

**Unit C:** one app-use session per instance per principal, created at first GrantRecord mint.

Reconnect (parent AD-29) has three referents. Sequence 1 “authoring app_instance_id optional” does not state app-use session cardinality.

**Tightened Rule:** Cardinality is **1 app-use `psess:` per (principal, instance_id)** created at first grant, independent of panels. Headless app-use is first-class. Panel mount/dispose writes nothing to `psess:`. Authoring cardinality is **1 home `psess:` per principal** (null `app_instance_id` until invoke; invoke law in C-1).

---

## MEDIUM

### M-1 — QMB LogSink + daemon JSON-lines + QMA telemetry is already three planes

Local AD-5 Prevents a fourth product and “a third logger” while allowing QMB LogSink to remain and requiring daemon JSON-lines **and** QMA telemetry. The sitting’s own research table lists QMN JSON-lines, QMA telemetry, QMB LogSink, QML none. Adding daemon JSON-lines is the missing QMA operator log (good) but the “no third logger” sentence licenses Unit A to kill QMB LogSink or Unit B to skip daemon logs and “reuse” QMB.

**Fix:** name two QMA planes (operator JSON-lines + telemetry store) and one QMB plane (LogSink). Do not say “third.”

### M-2 — `copilot_profile.suggested_ops` encoding unset

CONTRACTS: “prompts, suggested ops.” Parent AD-3 identity is `op_id`+version+contribution tuple. Suggested ops as bare `op_id` strings collide across packs; as ContributionHit they are hits-not-grants (09-18 C-2); as GrantRecord ids they are grants smuggled in a request.

**Unit A:** `suggested_ops: ["qmb.analysis.project"]`. **Unit B:** contribution tuples. Weak-model AD-7 says schemas not prose — this field is the schema, and it is not closed.

**Fix:** `suggested_ops: {op_id, op_version, qualified_id}[]`. Still a request. Still filtered by AD-9.

### M-3 — Envelope `caller_kind` vs widget bind DTO vs json-render action

Three invoke labels for one press: `caller_kind`, json-render catalog `action`=`op_id`, widget bound to template `start`. No single field says which descriptor was bound. Two UI-later units will disagree when GAP-0081 lands; this sitting claims contracts are enough.

**Fix:** bind record `{surface: native|json-render|mcp-app|cli, op_id, op_version, contribution}` on the envelope as audit, not authority. Still GAP-0081 chrome.

---

## Parent 09-18 AD-1..AD-31 weakening table

Local ADs that **restated without weakening:** AD-1 (no sixth COMP), AD-3 (envelope exists), AD-9 (skills don’t grant), AD-10 nested-no-union (stated), AD-16 logs≠journals, AD-17 adapters unpinned (local AD-8 — **if C-5 is fixed**), AD-21 headless, AD-29 app-use cannot apply, AD-30 install≠grant.

| Parent | Local effect | Weaken? |
| --- | --- | --- |
| AD-2 `view:*` not a contribution point; listing axes published/configured/**granted**/reachable/healthy | Local AD-1 lists `view:*` as a contribution point; inherited table replaces **granted** with **authorized** | **YES** — C-5, C-3 |
| AD-8 `app_instance_id` durable; closed `selected_refs` kinds | Named amendment makes it optional; J-KIT-03 selects “apps” | **YES if incomplete** — C-1. Named, but does not amend envelope/GrantRecord/selected_refs |
| AD-9 intersection includes product_session GrantRecords | Home session with empty `granted_ops` plus lookup of “B’s grants” | **YES** under Unit A — second grant owner |
| AD-10 four modes closed | “Nested Mission” unnamed vs mode 2/3 | **YES** — C-4 (open fifth path) |
| AD-15 placement `available/configured/authorized/reachable/healthy` | Inherited table relabels it as pack listing axes | **YES** — vocabulary smash with AD-2 |
| AD-16 no other new sqlite; logs not evidence | Diagnosis query unspecified as fold vs table; FAILURES “beside package” | **Risk** — H-3/C-3 Unit C |
| AD-17 / DEC-0300 no `ui_view` | Local AD-1 `view:*` contribution | **YES** — C-5 |
| AD-24 envelope fields closed; retry/reconcile specified | `caller_kind` additive (OK if audit); host default retry can override `never-retry` | **YES** under Unit B — C-2, H-1 |
| AD-25 no automatic retry of `unknown-blocked` | Default host retry for every pack | **YES** unless excluded — C-2 |
| AD-26 outbox exactly-once logical acceptance; JobHandle vocab | Host retry wraps node dispatch; diagnosis may invent `succeeded`/`awaiting_approval` (not written, but JobHandle “or null” is new) | **Risk** — C-2 |
| AD-7 one template → one Mission; occupancy | Nested compile vs invoke vs include | **Risk** — C-4 |
| DEC-0304 three `correlation_id` origins | Every public op/widget/agent must expose a join key | **YES** if new origins are minted — C-3 |
| QMA AD-1 eight contribution points | copilot profile as a point | **YES** — C-5 |

No local rule weakens parent AD-11 dummy-Book, AD-23 ATC, AD-25 fencing **except** via default retry (C-2), AD-31 recipes, or L36. Those were correctly not re-elicited.

---

## Slice 0 / Sequence map (what forks if frozen now)

| IMPLEMENTATION-SEQUENCE step | Hole |
| --- | --- |
| 1 Host SDK: optional copilot_profile; optional authoring `app_instance_id`; `caller_kind` | C-1, C-5, H-1, H-2, H-4, M-2 |
| 2 Daemon JSON-lines + diagnosis query | C-3, M-1 |
| 3 Default retry wired to effect-class matrix | C-2, H-3 |
| 4 Nested Mission invoke | C-4 |
| 5 Listing axes + instance health | C-3 `granted` vs `authorized` |

DAG-validator / no-sixth-COMP / app-use-cannot-apply remain the exceptions whose Rules are closed.

---

## Paste-ready amendment order

1. Renumber local AD-1..AD-8 → AD-32..AD-39 (H-2).
2. Apply C-5 (contribution roster) before any pack-manifest epic.
3. Apply C-1 (instance/select/grant invoke law) before optional `app_instance_id` ships.
4. Apply C-3 (one diagnosis query, AD-2 listing words, strike `widget`, correlation_id origins) before JSON-lines.
5. Apply C-2 (host retry function, tighter field, no wrap of outbox/fencing) before “default retry.”
6. Apply C-4 (nested = AD-10 mode 2 + new Mission, occupancy, cancel) before nested Mission.
7. Fold H-1, H-4, M-1, M-2 into CONTRACTS.md in the same pass.

Do not freeze Sequence 1–4 on the spine as written.
