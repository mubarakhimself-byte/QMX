---
name: reconcile-inputs
sitting: architecture-QMX-2026-09-23
created: 2026-09-23
updated: 2026-09-23
status: review
scope: sitting inputs vs child spine AD-1..AD-8 (quiet requirements the AD structure dropped)
inputs:
  - .memlog.md
  - research/SDK-HYBRID-AND-CORE.md
  - Codex preserve 2026-09-23 (memlog constraint)
  - named sitting themes (optional copilot; many-to-many; host observability; default retry; weak models; JSON Render + MCP Apps adapters)
companions_consulted: [REQUIREMENTS-ADDENDUM.md, CONTRACTS.md, JOURNEYS.md, COPILOT-AND-APPS.md, IMPLEMENTATION-SEQUENCE.md]
not_architecture: [research/INVESTIGATION-SYNTHESIS.md, research/DONOR-DEEP-RESEARCH.md]
---

# Reconcile — sitting inputs vs child spine

Compares load-bearing sitting inputs against `ARCHITECTURE-SPINE.md` (local AD-1..AD-8) plus companions. Focus: **quiet requirements the AD structure dropped**, not parent 09-18 completeness (that sitting already has its own reconcile). Companions count as landed only when an AD Prevents/Rule binds the same law; a journey or addendum bullet with no AD clause is a factory hole.

**Verdict: LANDED WITH QUIET MISSES.** The named sitting themes have ADs (pack-and-grant SDK, optional copilot, composition, host observability, default retry, weak models, unpinned adapters). Home/general as authoring-with-absent-instance is a named parent amendment. Codex preserve mostly maps onto parent AD-8/AD-9/AD-17 plus local AD-3 restatements. What the AD set still thins: (1) the **tested promotion path** (idea / loop → reusable workflow → mini-app after tests) this sitting was explicitly told 09-18 missed; (2) **observability field rosters** this sitting claimed to own (`health()` schema, metric families, per-node visibility, diagnosable **how**); (3) Codex **independently scoped** and **backend-not-UI** as local Prevents, not only companion/inherit.

**Autofixable** = can be written into an existing local AD / companion from already-stated sitting law, with no new investigation and no new operator question.

---

## Per-input

### 1. `.memlog.md` (sitting constraints and decisions)

| Class | Items |
|---|---|
| **Landed** | No sixth COMP; no fourth observability product; no QMN `FAILURES.md` reuse (AD-5). Logs ≠ evidence; harness telemetry; OTel export-port; agents must not author telemetry; `correlation_id` join never fp1 (AD-5). JobHandle stays QMA AD-17 vocab (AD-5). Pack-and-grant kit; screen-kit / automation-kit rejected (paradigm, AD-1). Kit nouns over the whole platform; QMA host not owner of every op (AD-2). Copilot one capability; in-app panel optional; no third `ProductSessionProfile`; authoring `app_instance_id` MAY be absent (AD-3 + named amendment). Nested invoke does not union grants; caller `user \| agent \| workflow`; workflow-to-workflow = nested Mission, no live Task Graph merge (AD-4). Default host retry per parent AD-24; tighter not looser; no blind `external-egress`; implementation repair is `change_request`; app-use cannot apply (AD-6). Headless packs first-class (AD-1). Daemon stdlib JSON-lines with QMN field names where they apply + instance/op/invocation/graph ids (AD-5). QMB LogSink may remain; no third logger (AD-5 closes the QMN/QMB/QMA log-divergence or defers by keeping QMB). UI chrome / GAP-0081 / GAP-0100 deferred. JSON Render + MCP Apps presentation adapters, unpinned (AD-8). Weak/older models via schemas (AD-7). `34c148b` fixtures ≠ e2e (conventions + sequence step 0). |
| **Dropped / thinned (quiet)** | **Loops can become mini-apps** (memlog “missed vs 09-18”) — no AD, no journey, no addendum bullet. Parent AD-6 still says runtime Loops are node state, not template cycles; this sitting never binds the *promotion* of a tested loop/experiment into a versioned pack. **Daily idea → yap at copilot → tools → reusable workflow → mini-app after tests** is the CORE origin path; AD-1 is how a pack *declares*, not how work *graduates*. **Diagnosable what/when/why/how** — REQUIREMENTS and AD-5 keep what/when/why + `failure_class`; **how** (the run’s actual steps) is unbound. **Ask-why logs as product surface** folded into diagnosis query (J-KIT-02, AD-5) rather than copilot-cited work records (parent AD-9 “explanations cite saved records”). **n8n-like CLI-in-node as visibility, not a monitoring product** — AD-5 is daemon JSON-lines + a headless diagnosis query, not per-node/CLI visibility. **No new CT unless named amendment** — memlog constraint; spine Prevents sixth COMP, not a new contract id. **Live-money blast radius = `effect_class` + grant + owner COMP, not a widget property and not a QMB/QML core rewrite** — implied by AD-2/AD-4/AD-6, never a Prevents. **Mini-app is pack+instance grouping, not a registry kind** — parent AD-2/AD-10; child AD-2 says install/instance rows, never “not a registry kind.” **Unattended is a placement, not the kit** — Deferred GAP-0058/0062 only. |
| **Conflicts** | None with memlog decisions. Self-repair coaching fork (observe+explain vs auto-retry vs auto-apply) was closed as host retry + `change_request` (AD-6); that is a landing, not a drop. |

### 2. `research/SDK-HYBRID-AND-CORE.md`

Coaching evidence, not ratified — but it is the sitting’s stated hybrid and the origin list the spine was distilled from.

| Class | Items |
|---|---|
| **Landed (match)** | Pack-and-grant hybrid; Screen kit and Automation kit rejected (paradigm, AD-1). SDK = host contract QMA implements, not “everything in qma-daemon” (AD-1, AD-2). Placement table: pack/sessions/Task Graph on QMA; op execution on owning COMP; widget display-only; venue QMN (AD-2, AD-4). Two copilot firepowers; `sess:` is engine not a third chat; home folded into authoring-with-nothing-selected (AD-3). Weak models fill schemas; skill≠grant; hit≠grant; hooks cannot override privilege (AD-7). Observability relationship: listing axes, instance health distinct from published, JobHandle, typed refusal, `correlation_id`, harness telemetry (AD-5). Default host retry; no sixth COMP; no app-specific live-money redesign (AD-6, Deferred). CORE inherit vs APP do-not-re-elicit for AD-11/14/22/23/25. |
| **Dropped / thinned** | **Copilot sees only grants ∩ health** — parent AD-9 already; local AD-3/AD-5 never restate the intersection as what *both* seats see. Factory reading only the child can show published ops to app-use. **Workflows may be deterministic, agentic, or both** — one paradigm sentence (“deterministic graph, agent node, or both”); no AD Prevents that a Graph Template may contain an agent node. Factory can ship DAG-of-ops only. **On-prem and VPS both exist; unattended is a placement, not the kit** — Deferred row, not an AD. **No new CT** — explicit SDK-HYBRID already-decided; not in child Prevents. **AD-28 market cutover / AD-31 full catalogue over-fit as kit law (keep identity principle)** — inherit table lists AD-11/14/22/23/25 as do-not-re-elicit; AD-28/AD-31 unclassified (GAP-0100 defers the dashboard, not the over-fit ruling). **QMF is the toolbox, not the application** — paradigm sentence; AD-2 Prevents stuffing apps into qma-daemon / QMB/QML forks, not QMF-as-app. Donor hybrid last sentence is stronger. |
| **Deliberate resolution (not a miss)** | Donor “tell app-use something broke by composing an n8n-style error workflow, not by patching QMA.” Spine chose **host-owned diagnosis** (`failure_class` query + JSON-lines) so packs do not ship an error-workflow dialect. Record so a later epic does not “helpfully” add per-pack error graphs. |

### 3. Codex preserve 2026-09-23

Memlog: independently scoped resumable agent sessions; running work separate from UI panels; broad main workspace plus optional app-scoped assistant panels through **shared capabilities**; context transfer explicit; permissions enforced in **backend**; check current core before adding mechanisms; final UI and handoff under discussion. Maps onto parent AD-8/AD-9/AD-17 plus optional in-app copilot. Do not mint a second session kind or a second permission system.

| Preserve item | Landed? | Where | Quiet hole |
|---|---|---|---|
| Independently scoped resumable `psess:` | **Thin** | Companion sentence; AD-3 reconnect + “tab as session” Prevents; parent AD-8 isolation | Local AD-3 never Prevents two concurrent sessions sharing grants, `selected_refs`, or memory. “Independently scoped” is not a child Rule. |
| Running work separate from UI panels | **Yes** | AD-3 “Running work is not cancelled by panel dispose (parent AD-17)”; J-KIT-01/04 | — |
| Broad main workspace + optional app-scoped assistant via **shared** capability | **Yes** | AD-3 one identity, two profiles, panel optional; COPILOT table | — |
| Explicit context transfer | **Yes** | AD-3 “`selected_refs` or `change_request` only”; J-KIT-03 | — |
| Permissions enforced in backend | **Thin** | AD-1 GrantRecords; AD-7 hooks cannot override; AD-8 adapters cannot grant; parent AD-9 ∩ GrantRecord | Codex wording is **backend vs panel**. Child never says the UI/MCP iframe/json-render catalog cannot be the privilege gate. Inherit implies it; factory can still “check in the panel.” |
| Check current core before new mechanisms | **Sequence only** | IMPLEMENTATION-SEQUENCE step 0; conventions DEC-0286 | Not an AD. Acceptable as factory honesty if epics bind the sequence; vanished if epics are sliced from ADs/addendum alone. |
| Final UI / handoff under discussion | **Yes** | Deferred GAP-0081 / GAP-0100 | — |
| No second session kind | **Yes** | AD-3 closed `{authoring, app-use}`; named amendment; no third seat | — |
| No second permission system | **Yes** | AD-1 GrantRecords as the only grant | — |

### 4. Named sitting themes

| Theme | AD | Landed? | Quiet remainder |
|---|---|---|---|
| Optional copilot | AD-1, AD-3 | **Yes** | Pack may omit profile; instance may omit panel; headless first-class. |
| Many-to-many composition | AD-4 | **Yes** | Four parent AD-10 modes restated; nested Mission; no fifth widget-to-widget mode. **Promotion** of a composition into a pack is still missing (see §1). |
| Host observability | AD-5 | **Partial** | Relationship exists (listing, JSON-lines, `failure_class`, JobHandle, `correlation_id`). Sitting-owned gaps from INVESTIGATION-SYNTHESIS still unbound as schemas: instance `health()` field roster, metric families, operator-log roster beyond the six required keys, per-node CLI visibility, diagnosable **how**. `healthy` in CONTRACTS is a boolean axis. |
| Default retry | AD-6 | **Yes** | Host/SDK, on by default, effect-class matrix, tighter-not-looser, no blind egress. (Parent-consistency residual on `reconcile_policy` / `unknown-blocked` is that lens, not this one.) |
| Weak models | AD-7 | **Yes** | Descriptors, grants, `input_schema`, typed refusals, host-intercepted tools. J-KIT-07 is build-only; operate is implied, no weak-model operate journey. |
| JSON Render + MCP Apps adapters | AD-7, AD-8, CONTRACTS §7 | **Yes** | Unpinned; not identity/persistence/runtime/authority; catalog `action` names existing `op_id` (CONTRACTS, parent AD-17); host intercepts `tools/call`. Child AD-8 thins the MUST-name-`op_id` sentence into “cannot add ops or fields”; parent still binds. |

### 5. REQUIREMENTS-ADDENDUM / JOURNEYS / COPILOT-AND-APPS (inverse map)

Addendum has no `FR-*` ids this sitting. Must-bullets map to ADs except as noted. Inverse: several sitting constraints have **no Must and no AD**.

| Addendum Must | Spine | Map |
|---|---|---|
| Pack declares ops, optional views, requested access, optional copilot | AD-1 | ok |
| Install ≠ enable ≠ GrantRecord | AD-1 | ok |
| Some packs/widgets/workflows have no copilot; main can still reference | AD-3 | ok |
| Every public run diagnosable headless: what, when, why, which failure_class | AD-5 | **thin** — memlog **how** dropped |
| Ordinary failures retry in host; change-request; app-use cannot apply | AD-6 | ok |
| Weaker models through schemas and grants | AD-7 | ok |
| Compose via operations; nested calls do not stack permissions | AD-4 | ok |
| JSON Render and MCP Apps paint; they do not grant | AD-8 | ok |

**Journeys:** J-KIT-01..07 cover headless, optional panel, selected_refs isolation, widget-start, nested Mission, ordinary retry, weak-model **build**. **No journey** for: loop/experiment → tested pack; weak-model **operate** + ask-why; CLI-in-node visibility; two independently scoped sessions side by side.

**COPILOT-AND-APPS** is the only place “independently scoped resumable `psess:`” and “UI panels are not sessions” are said in those words. AD-3 has the work/panel split and reconnect; it does not carry independent-scope as a Prevents.

**ADs with no addendum Must:** none of AD-1..AD-8 is addendum-orphan. The orphans are sitting inputs that never became Musts (promotion path, no-new-CT, independently scoped, backend-not-UI, health schema, grants ∩ health, agentic workflow as law).

---

## Landed (summary)

- Pack-and-grant is the SDK; screen-kit and automation-kit rejected; QMA is host; ops stay on existing COMPs; no sixth COMP; no fourth observability product.
- One copilot capability; two profiles; in-app panel optional; home = authoring with `app_instance_id` absent (named parent amendment); no third seat; `sess:` is not a chat.
- Context transfer is explicit `selected_refs` or `change_request`. Nested invoke does not union grants. Running work survives panel dispose.
- Four AD-10 composition modes; caller_kind closed; workflow-to-workflow is nested Mission; live Task Graph merge refused.
- Host diagnosis + daemon JSON-lines; `failure_class` closed; logs ≠ evidence; OTel export-port; QMN stack stays QMN.
- Default host retry by effect class; `change_request` for implementation edits; app-use cannot apply; no blind `external-egress`.
- Weak models operate through descriptors ∩ grants; skills/hooks/MCP HTML/json-render cannot grant.
- JSON Render and MCP Apps unpinned presentation adapters; chrome remains GAP-0081.

## Dropped (summary — quiet requirements AD structure lost)

1. **Tested promotion path / loops-can-become-mini-apps** — memlog miss-vs-09-18 + SDK-HYBRID origin (`Daily idea → yap at copilot → tools → reusable workflow → mini-app after tests`). Spine binds how a pack declares and how workflows invoke; it does not bind graduation of a tested loop/experiment into a versioned mini-app. Highest quiet miss: factory slice success can look like “we have a pack SDK” and never a path from daily idea to installed instance.
2. **Sitting-owned observability schemas** — INVESTIGATION-SYNTHESIS named operator-log roster, metric families, instance `health()` schema, who owns “what went wrong,” diagnosis journey, self-repair matrix. Self-repair matrix and a diagnosis *query* landed (AD-5/AD-6, J-KIT-02). `health()` field roster, metric families, and diagnosable **how** did not. `healthy` is a boolean listing axis. Not even Deferred as named rows (except QMA `FAILURES.md` “when first host failure ids ship”).
3. **CLI-in-node visibility** — operator 09-18 voice / memlog: n8n-like per-node visibility, not a monitoring product. AD-5 is daemon logs + failure_class, not a per-step inspect surface the app-use copilot can ask why against.
4. **Copilot sees only grants ∩ health** — SDK-HYBRID pin; parent AD-9. Child AD-3 does not restate the intersection for either seat.
5. **Independently scoped sessions (Codex)** — companion words; not a local AD Prevents. Two panels can be implemented as one `psess:` with extra chrome.
6. **Permissions enforced in backend (Codex)** — GrantRecords landed; “the panel is not the gate” did not.
7. **No new CT** — memlog + SDK-HYBRID already-decided; child Prevents sixth COMP only.
8. **Deterministic and agentic workflows as law** — paradigm only; no AD that a template may contain an agent node (and must still be diagnosable / retry-classed).
9. **Live-money blast radius is not a widget property** — memlog; implied, not Prevents.
10. **QMF = toolbox not application; unattended = placement not kit; AD-28/AD-31 over-fit** — paradigm / Deferred / unclassified inherit. Tone that blocks QMF-as-app, VPS-SKU, and cutover-as-kit-epic.
11. **Check current core before new mechanisms** — sequence step 0 only.
12. **Ask-why cites work records** — folded to `failure_class` + JobHandle; parent AD-9 record-citation not restated as the app-use ask-why surface.

## Conflicts

| Id | Conflict | Resolution in package |
|---|---|---|
| K1 | Donor n8n error-workflow as the observability copy vs host-owned diagnosis | **Spine wins** (AD-5). Deliberate: packs do not ship error-workflow dialects. |
| K2 | Memlog “ask-why logs as product surface” vs AD-5 “logs are not evidence” | **Spine wins on logs≠evidence.** Ask-why landed as diagnosis query, not log-tail. Residual: **how** and work-record citation unbound. |
| K3 | Codex “maps onto parent AD-8/AD-9/AD-17” vs child AD-3 restating only a subset | Mapping is declared. Quiet miss is the un-restated subset (independent scope, backend-not-UI), not a contradiction. |
| K4 | SDK-HYBRID “no new CT” vs local AD-4 `caller_kind` envelope field (parent-consistency F-1) | Out of this lens’s verdict except as: sitting said no new CT; child minted an envelope field without tagging a contract amendment. Flag, do not invent a CT id. |

No local AD silently overrides a sitting *decision*. The drops are omissions, not overrides.

## Top gaps (priority)

1. **Promotion path / loops-can-become-mini-apps** — the quiet requirement most likely to vanish in epics. Needs an AD-1/AD-3 Prevents (or a Must + journey): a tested loop or experiment may graduate to a versioned Graph Template and then to an installed pack; graduation is not a new registry kind and is not live-graph splice. Autofixable from memlog + SDK-HYBRID + parent AD-6 Loop-as-node-state.
2. **`health()` schema + metric families + diagnosable how** — this sitting owned the observability *relationship* and left it as a boolean + log line. Autofixable as AD-5/CONTRACTS field roster without minting a fourth product; metric families can be Deferred by name if the sitting will not specify them.
3. **Codex independently scoped + backend-not-UI** — one AD-3 Prevents sentence each. Autofixable from the memlog preserve block; no new session kind.
4. **grants ∩ health on both copilot seats** — one AD-3 sentence pointing at parent AD-9. Autofixable.
5. **No new CT / agentic workflow as law / blast-radius-not-widget / CLI-in-node** — short Prevents on AD-2, AD-4, AD-5. Autofixable. CLI-in-node can stay “visibility via diagnosis query + per-node JobHandle,” not a monitoring product.

## Path

`C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/reviews/reconcile-inputs.md`
