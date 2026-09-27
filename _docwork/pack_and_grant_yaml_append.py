#!/usr/bin/env python3
"""Append pack-and-grant change-mode YAML. Run once from project root. Idempotent by id."""
from pathlib import Path

ROOT = Path(r"C:/Users/Mubarak/Desktop/QMX")


def already(text: str, needle: str) -> bool:
    return needle in text


def append_if_missing(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if already(text, marker):
        print(f"skip {path.name}: {marker} already present")
        return
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + block, encoding="utf-8")
    print(f"appended {marker} -> {path.name}")


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if label in text and old not in text:
        print(f"skip {path.name}: {label} already patched")
        return
    if old not in text:
        raise SystemExit(f"{path.name}: block not found for {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {label} -> {path.name}")


def patch_gap_0081(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "2026-09-23 pack-and-grant: optional in-app panel is a contract" in text:
        print("skip gaps.yaml: GAP-0081 2026-09-23 already patched")
        return
    old = """    note: "AD-5 wire. The qma-ui-contract package ships as a stub only in v1. The wire contract (AD-5) and the variables registry (AD-26) are NOT deferred and bind now. Carried forward: the UI reads as a trading/research terminal, not a generic agent dashboard (operator, T-5071, T-5082-5084). 2026-09-19 Workflows: UI-host contracts (AD-17 / DEC-0430 DTOs) fold now; chrome stays deferred on this row (DEC-0446)."
    date: 2026-09-19"""
    new = """    note: "AD-5 wire. The qma-ui-contract package ships as a stub only in v1. The wire contract (AD-5) and the variables registry (AD-26) are NOT deferred and bind now. Carried forward: the UI reads as a trading/research terminal, not a generic agent dashboard (operator, T-5071, T-5082-5084). 2026-09-19 Workflows: UI-host contracts (AD-17 / DEC-0430 DTOs) fold now; chrome stays deferred on this row (DEC-0446). 2026-09-23 pack-and-grant: optional in-app panel is a contract (a pack may omit copilot_profile) and is not chrome; chrome still deferred (DEC-0459, DEC-0462)."
    date: 2026-09-23"""
    replace_once(path, old, new, "GAP-0081 2026-09-23")


def patch_gap_0093(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "2026-09-23 inspect 34c148b: product_session types/fixtures exist" in text:
        print("skip gaps.yaml: GAP-0093 2026-09-23 already patched")
        return
    old = """    note: "Workflows AD-8/AD-29. product_session is a journal-projected record kind, not a new store class."
    date: 2026-09-19"""
    new = """    note: "Workflows AD-8/AD-29. product_session is a journal-projected record kind, not a new store class. 2026-09-23 inspect 34c148b: product_session types/fixtures exist (Workflows 53-59); class/test existence is not e2e (DEC-0286, DEC-0465). Authoring app_instance_id optionality is the named parent AD-8 amendment (DEC-0463, GAP-0102)."
    date: 2026-09-23"""
    replace_once(path, old, new, "GAP-0093 2026-09-23")


def patch_gap_0096(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "2026-09-23 inspect 34c148b: InvocationEnvelope and GrantRecord types exist" in text:
        print("skip gaps.yaml: GAP-0096 2026-09-23 already patched")
        return
    old = """    note: "Workflows AD-3/AD-24. Manifests request; host grants structured GrantRecords."
    date: 2026-09-19"""
    new = """    note: "Workflows AD-3/AD-24. Manifests request; host grants structured GrantRecords. 2026-09-23 inspect 34c148b: InvocationEnvelope and GrantRecord types exist as fixtures; caller_kind is absent (DEC-0464, DEC-0465, GAP-0101). Class/test existence is not e2e (DEC-0286)."
    date: 2026-09-23"""
    replace_once(path, old, new, "GAP-0096 2026-09-23")


def patch_gap_0100(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "2026-09-23 pack-and-grant restates GAP-0100" in text:
        print("skip gaps.yaml: GAP-0100 2026-09-23 already patched")
        return
    old = """    note: "Workflows deferred. Operator confirmed this is UI, not backend contracts. Do not invent chrome in FEAT-0051..0057."
    date: 2026-09-19"""
    new = """    note: "Workflows deferred. Operator confirmed this is UI, not backend contracts. Do not invent chrome in FEAT-0051..0057. 2026-09-23 pack-and-grant restates GAP-0100 as later UI; diagnosis queries bind now (DEC-0456, DEC-0459)."
    date: 2026-09-23"""
    replace_once(path, old, new, "GAP-0100 2026-09-23")


MANIFEST = r"""
- id: SRC-24
  path: _bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/
  kind: rider
  role: primary
  status: harvested
  note: "2026-09-23 QMX pack-and-grant kit architecture sitting (child feature spine; local AD-1..AD-9 inherit parent 09-18 AD-1..AD-31): ARCHITECTURE-SPINE.md, REQUIREMENTS-ADDENDUM.md, CONTRACTS.md, JOURNEYS.md, COPILOT-AND-APPS.md, IMPLEMENTATION-SEQUENCE.md, .memlog.md, reviews/gate-summary.md, research/SDK-HYBRID-AND-CORE.md. Operator accepted the sitting as the plan to fold. Spine YAML leftover status draft / not operator-accepted is stale paperwork. Parents bind read-only. Local AD ids do not renumber parents. Planning on main@92279df; implementation inspected on integration@34c148b. Parent freeze 270e992 still applies for ADR-0024 original Decision (DEC-0450)."
- id: SRC-25
  path: _docwork/riders/pack-and-grant-kit-2026-09-23.md
  kind: rider
  role: primary
  status: harvested
  note: "Operator-direct rider for the 2026-09-23 documentation-factory change-mode session: pack-and-grant SDK; kit nouns over the whole platform; one copilot many sessions in-app panel optional; named parent AD-8 and AD-24 amendments; host observability JSON-lines; default host retry none/read; no sixth COMP; no new CT; no UI chrome; JSON Render/MCP Apps unpinned; wiring honesty @ 34c148b; DEC-0286 fixtures not e2e. Citation surface for DEC-0452..DEC-0467."
"""

EXTR = r"""
  - id: EXT-2286
    type: decision
    summary: "Operator-direct standing corrections for pack-and-grant fold: pack-and-grant is the SDK; screen-kit and automation-kit rejected as the center; mini-app/widget/workflow are kit nouns over the whole platform and QMA is host not owner of every op; one copilot identity, many independently scoped psess: sessions, in-app panel optional; home is authoring with app_instance_id absent; nested workflow is one nested Mission not merged live graphs; host observability is inherited JSON-lines plus JobHandle plus failure_class; default host retry none/read only; JSON Render and MCP Apps stay unpinned presentation adapters; no sixth COMP, no new CT, no UI chrome, no QMB/QML core fork."
    quote: "Pack-and-grant is the SDK. Mini-app, widget, and workflow are kit nouns over the whole platform. QMA is host/runtime, not owner of every op. One copilot product identity. In-app copilot panel is optional."
    cite: SRC-25
    topics: [pack-and-grant, rider, standing-corrections, no-sixth-comp]
    authority: rider
  - id: EXT-2287
    type: decision
    summary: "kit AD-1 Pack-and-grant is the SDK: a pack declares operations, optional views, requested access, optional copilot_profile request blob. Host grants GrantRecords. Installing/enabling is not granting. Headless packs are first-class. view:* is a wire DTO not a contribution point."
    quote: "The SDK is the host contract a pack author gets: versioned operation descriptors, GrantRecords as the only grant, InvocationEnvelope as the only invoke."
    cite: SRC-24
    topics: [pack-and-grant, ad-1, sdk]
    authority: rider
  - id: EXT-2288
    type: decision
    summary: "kit AD-2 Kit nouns span the platform; QMA is host not owner of every op. Bytes of a pack live in plugin tree plus daemon install/instance rows. Execution of each op_id is owned by the COMP named on the descriptor. Widgets never own invoke. Broker/venue stays QMN."
    quote: "Mini-app / widget / workflow are kit nouns over the whole platform, not a QMA-only product. QMA is host/runtime."
    cite: SRC-24
    topics: [pack-and-grant, ad-2, placement]
    authority: rider
  - id: EXT-2289
    type: decision
    summary: "kit AD-3 One copilot capability; many independently scoped resumable sessions; in-app panel optional. ProductSessionProfile remains authoring or app-use. Authoring with absent app_instance_id may not invoke until exactly one selected_refs kind instance_id. Nested invoke does not union grants. Running work is not cancelled by panel dispose."
    quote: "Copilot is one shared platform capability, not bundled into every app. Multiple independently scoped sessions. In-app copilot panel is optional."
    cite: SRC-24
    topics: [pack-and-grant, ad-3, copilot]
    authority: rider
  - id: EXT-2290
    type: decision
    summary: "kit AD-4 Caller is user, agent, or workflow on one InvocationEnvelope (named parent AD-24 amendment). Widgets bind or display ops; they do not add a fifth composition mode. Workflow-to-workflow at runtime is one nested Mission / one Task Graph / one JobHandle. Include-at-author is a new versioned Graph Template. Merging two live Task Graphs is refused."
    quote: "Every public call carries parent AD-24 InvocationEnvelope including named-amendment caller_kind user | agent | workflow."
    cite: SRC-24
    topics: [pack-and-grant, ad-4, caller-kind, nested-mission]
    authority: rider
  - id: EXT-2291
    type: decision
    summary: "kit AD-5 Host observability is a relationship every pack inherits: listing axes including healthy; instance health(); JobHandle; typed refusal; correlation_id; harness-authored QMA telemetry. Failure class closed grant|workflow|view|dependency|host. qma-daemon emits stdlib JSON-lines. Logs are not evidence. Do not extend qmn/FAILURES.md."
    quote: "qma-daemon emits stdlib JSON-lines operator logs. QMA telemetry store remains the trace/metric plane. Do not extend qmn/FAILURES.md allow-list."
    cite: SRC-24
    topics: [pack-and-grant, ad-5, observability]
    authority: rider
  - id: EXT-2292
    type: decision
    summary: "kit AD-6 Default host retry for effect none and read. Does not retry every effect. Parent AD-24 / SCN-0021 matrix remains: no blind external-egress retry; CAS conflict is not a retry; unknown-blocked never auto-retried. Implementation edits are change_request; app-use may mint and must not apply."
    quote: "Default retry is host/SDK behaviour for every mini-app/workflow. Retry lives in QMA host/SDK, not reinvented per app."
    cite: SRC-24
    topics: [pack-and-grant, ad-6, retry]
    authority: rider
  - id: EXT-2293
    type: decision
    summary: "kit AD-7 Weak/older models operate through descriptors, GrantRecords, input_schema, typed refusals, and host-intercepted tool calls. Skills describe; they do not grant. MCP App HTML and json-render catalog entries cannot add ops or fields."
    quote: "Build and operate must work for a weaker/older model. Load-bearing surfaces are descriptors, GrantRecords, input_schema, typed refusals."
    cite: SRC-24
    topics: [pack-and-grant, ad-7, weak-models]
    authority: rider
  - id: EXT-2294
    type: decision
    summary: "kit AD-8 Presentation adapters stay unpinned. JSON Render is a catalog-constrained generative view. MCP Apps are an optional sandboxed view. Native QMX panes remain first. Do not pin @json-render/* or @modelcontextprotocol/ext-apps. Chrome remains GAP-0081 / GAP-0100."
    quote: "JSON Render and MCP Apps stay presentation adapters. Do not pin @json-render/* or @modelcontextprotocol/ext-apps."
    cite: SRC-24
    topics: [pack-and-grant, ad-8, adapters]
    authority: rider
  - id: EXT-2295
    type: decision
    summary: "kit AD-9 Tested work graduates to a pack: yap at authoring, Graph Template, runs with JobHandles, pack export of those operations after validate. A Loop remains node state. Graduation does not skip parent AD-18/AD-30 enable/validate."
    quote: "Daily idea path is: yap at authoring then Graph Template then runs with JobHandles then pack export of those operations after validate."
    cite: SRC-24
    topics: [pack-and-grant, ad-9, graduation]
    authority: rider
  - id: EXT-2296
    type: decision
    summary: "Umbrella: 2026-09-23 pack-and-grant child spine adopted in full as DEC-0452 through DEC-0460. Inherit parent 09-18 AD-1..AD-31. Named parent amendments DEC-0463/DEC-0464. ADR-0025 and SCN-0023..0027 are docs authority only. Implementation authorization remains factory-pipeline-only."
    quote: "Operator accepted the sitting as the plan to fold. Fold this increment into existing docs/. Do not rewrite the 2026-09-16 QML fold or the 2026-09-19 Workflows fold."
    cite: SRC-25
    topics: [pack-and-grant, umbrella]
    authority: rider
  - id: EXT-2297
    type: decision
    summary: "Preflight: reuse existing applications. new COMP none. new CT none. No new depends_on edge. No existing component authority shrinks. Work owners are QMA-CORE/DAEMON/WIRE extends; QMB/QML/QMN remain execution owners of their ops."
    quote: "No sixth COMP. No new CT. No QMB/QML core fork."
    cite: SRC-25
    topics: [pack-and-grant, preflight, reuse]
    authority: rider
  - id: EXT-2298
    type: decision
    summary: "Named amendment of parent AD-8 / DEC-0421: app_instance_id MAY be absent when ProductSessionProfile=authoring; remains required when profile=app-use. Closed selected_refs kinds gain instance_id. Authoring with absent session instance may not invoke until exactly one selected_refs kind instance_id is present; envelope instance_id remains required on invoke. No third profile. Do not set DEC-0421 superseded_by."
    quote: "Home/main with no app open is ProductSessionProfile=authoring with app_instance_id absent. Named parent amendment of Workflows AD-8. App-use still requires instance. No third seat."
    cite: SRC-24
    topics: [pack-and-grant, parent-ad-8, amendment]
    authority: rider
  - id: EXT-2299
    type: decision
    summary: "Named amendment of parent AD-24 / DEC-0437: InvocationEnvelope gains closed caller_kind user | agent | workflow. Envelope instance_id remains required on every invoke. Do not set DEC-0437 superseded_by. No new CT number."
    quote: "InvocationEnvelope gains closed caller_kind: user | agent | workflow. Envelope instance_id remains required on every invoke."
    cite: SRC-24
    topics: [pack-and-grant, parent-ad-24, amendment]
    authority: rider
  - id: EXT-2300
    type: context
    summary: "Wiring honesty at integration@34c148b: InvocationEnvelope, GrantRecord, and product_session types/fixtures exist (Workflows 53-59). Class/test existence is not e2e (DEC-0286). Absent as product surface: caller_kind; optional authoring app_instance_id; selected_refs kind instance_id; pack copilot_profile; daemon JSON-lines operator logger; diagnosis failure_class; default host retry loop; nested Mission invoke as first-class. Parent freeze 270e992 still applies for ADR-0024 original Decision (DEC-0450)."
    quote: "Inspect implementation at origin/integration (currently 34c148b) for connect/amend vs existing. Parent freeze honesty at 270e992 still applies for ADR-0024. Fixtures are not e2e (DEC-0286)."
    cite: SRC-25
    topics: [pack-and-grant, wiring, source-inspected, 34c148b]
    authority: rider
  - id: EXT-2301
    type: death
    summary: "Dead list honored: DEC-0084/0085/0086; DEC-0361 marketplace; DEC-0362 solver; DEC-0366 HMR; DEC-0408..0413 mill deaths. Screen-kit and automation-kit as the center stay dead. Third ProductSessionProfile un-minted. Merged live Task Graphs refused. JSON Render / MCP Apps as identity/persistence/runtime/authority stay dead. No sixth COMP. No new CT."
    quote: "Screen kit and Automation kit rejected as the center. No sixth COMP. No new CT. Merging two live Task Graphs is refused."
    cite: SRC-25
    topics: [pack-and-grant, dead-list]
    authority: rider
  - id: EXT-2302
    type: decision
    summary: "Cheap-veto A7-A9: A7 failure_class closed set grant|workflow|view|dependency|host; A8 daemon JSON-lines extra fields when present; A9 host retry attempt ceiling is a registry row and this sitting mints no number. Not vetoable: no sixth COMP; no new CT; no third profile; envelope instance_id required on invoke; no live-graph merge; app-use cannot apply; no blind external-egress retry."
    quote: "This spine does not mint a number for the host-registered attempt ceiling. Failure class is closed: grant | workflow | view | dependency | host."
    cite: SRC-24
    topics: [pack-and-grant, cheap-veto]
    authority: rider
"""

LEDGER = r"""
  - id: DEC-0452
    title: "kit AD-1 — Pack-and-grant is the SDK"
    statement: "The SDK is the host contract a pack author gets: versioned operation descriptors (parent AD-3), parent AD-2 contribution points for operations only, GrantRecords as the only grant, InvocationEnvelope as the only invoke, listing axes (parent AD-15: published / configured / authorized / reachable / healthy — authorized is not a session GrantRecord), typed refusals. A pack manifest requests contributes (operations only), optional view:* wire DTOs (parent AD-17, not a contribution point), optional copilot_profile request blob (not a contribution point and not a grant), and requested_capabilities. Installing a pack does not grant. Enabling after validate still does not grant until GrantRecords exist for a session. Headless packs are first-class: they appear as reusable parent-AD-3 steps with no navigation and no copilot panel. Screen-kit and automation-kit are rejected as the center."
    status: ratified
    rationale: "Absorbed from architecture-QMX-2026-09-23 AD-1. Operator rider 2026-09-23; sitting accepted as the plan to fold."
    sources: [EXT-2287, EXT-2286]
    authority: rider
    component: COMP-QMA-CORE
    tags: [pack-and-grant, ad-1, sdk]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md#ad-1"

  - id: DEC-0453
    title: "kit AD-2 — Kit nouns span the platform; QMA is host not owner of every op"
    statement: "Mini-app, widget, and workflow are kit nouns over the whole platform, not a QMA-only product. Bytes of a pack live in the plugin tree plus daemon install/instance rows. Execution of each op_id is owned by the COMP named on the descriptor. Display is a wire DTO consumed by a later UI host. A new idea that no existing COMP can execute is a named connect/extend of that COMP, not a kit rewrite and not a QMA-owned fake. Widgets never own invoke. Broker/venue stays QMN. Closed QMA store classes stay closed. QMA is host/runtime (plugins, product sessions, graph templates)."
    status: ratified
    rationale: "Absorbed from architecture-QMX-2026-09-23 AD-2. Operator rider 2026-09-23."
    sources: [EXT-2288, EXT-2286]
    authority: rider
    component: COMP-QMA-DAEMON
    tags: [pack-and-grant, ad-2, placement]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md#ad-2"

  - id: DEC-0454
    title: "kit AD-3 — One copilot capability; many sessions; in-app panel optional"
    statement: "QuantMind/QMX Copilot is one product identity over QMA. Tool availability for every seat is parent AD-9 intersection (published ContributionHits intersect host grants intersect session GrantRecords intersect health). ProductSessionProfile remains authoring or app-use (parent AD-8). Authoring is the main/general seat (build, edit, version). App-use is the weaker seat (inspect, invoke granted ops, mint change_request, must not apply). A pack may omit a copilot profile. An instance may omit an in-app panel. Authoring with absent app_instance_id may not invoke. An invoke from that seat MUST carry envelope instance_id taken from a selected_refs kind instance_id; zero or many such refs is INVALID_INPUT. Nested invoke still does not union grants (parent AD-10). QMA sess: remains the engine run, not a third chat. Running work is not cancelled by panel dispose (parent AD-17). Reconnect resumes queries/events; it does not replay unacked intent. Context transfer is explicit selected_refs or change_request only. Headless packs remain valid."
    status: ratified
    rationale: "Absorbed from architecture-QMX-2026-09-23 AD-3. Operator rider 2026-09-23. Codex preserve 2026-09-23 maps onto this rule."
    sources: [EXT-2289, EXT-2286]
    authority: rider
    component: COMP-QMA-DAEMON
    tags: [pack-and-grant, ad-3, copilot]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md#ad-3"

  - id: DEC-0455
    title: "kit AD-4 — Caller is user, agent, or workflow on one envelope"
    statement: "Every public call carries parent AD-24 InvocationEnvelope including named-amendment caller_kind user | agent | workflow (DEC-0464). Widgets bind or display ops; they do not introduce a fifth composition mode. Many-to-many is Graph Template edges plus parent AD-10 modes (consume artifact, invoke op, coordinate, composite instance graph). Workflow-to-workflow at runtime is parent-AD-3 invoke of the callee template start / query-state / cancel / await (qualified_id plus version). That invoke creates one nested Mission / one Task Graph / one JobHandle (parent AD-7: one compile then one Mission). Occupancy and cancel follow that JobHandle. Include-at-author is a new versioned Graph Template, not a runtime merge. Merging two live Task Graphs is refused. Nested invoke depth is envelope call_depth against the host-registered recursion ceiling already implied by parent AD-10; exceeding it is INVALID_INPUT. This sitting mints no numeric ceiling. Partial failure does not silently substitute another instance, version, or account."
    status: ratified
    rationale: "Absorbed from architecture-QMX-2026-09-23 AD-4. Operator rider 2026-09-23."
    sources: [EXT-2290, EXT-2286]
    authority: rider
    component: COMP-QMA-CORE
    tags: [pack-and-grant, ad-4, caller-kind, nested-mission]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md#ad-4"

  - id: DEC-0456
    title: "kit AD-5 — Host observability is a relationship every pack inherits"
    statement: "For every public operation and every Task Graph run the host MUST expose, headless: (1) parent AD-15 listing axes including healthy; (2) instance health() as the existing component typed-report (DEC-0112), distinct from pack published; (3) JobHandle in QMA AD-17 vocabulary; (4) typed refusal; (5) correlation_id join (never fp1); (6) harness-authored QMA telemetry (agents must not write it; OTel remains export-port only). Failure class is closed: grant | workflow | view | dependency | host. view means the wire DTO failed to mount, was stale, or was unhealthy — it is not an invoke. qma-daemon emits stdlib JSON-lines using QMN field names where they apply (ts, level, event, correlation_id) plus instance_id, op_id, logical_invocation_id, graph_run_id when present. How-it-failed is that log line plus JobHandle attempt_id plus typed refusal; no fourth store. QMB LogSink may remain; new daemon code does not invent a third logger product. Logs are not evidence (parent AD-16, DEC-0112). Mini-app typed failures, when first ids ship, live in that owning package's FAILURES.md — never on the QMN alert allow-list. Do not mint a fourth observability product. Do not extend qmn/FAILURES.md."
    status: ratified
    rationale: "Absorbed from architecture-QMX-2026-09-23 AD-5. Operator rider 2026-09-23. Inherited DEC-0112 / DEC-0200 / DEC-0322."
    sources: [EXT-2291, EXT-2286]
    authority: rider
    component: COMP-QMA-DAEMON
    tags: [pack-and-grant, ad-5, observability]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md#ad-5"

  - id: DEC-0457
    title: "kit AD-6 — Default host retry; implementation repair is change-request"
    statement: "Retry is host/SDK behaviour. Default on means: for effect none and read, the host retries until success, until typed retryability=NO, or until the host-registered attempt ceiling (registry row; this sitting does not mint a number — GAP-0108). It does not mean retry of every effect. Parent AD-24 / SCN-0021 remain the matrix: append-evidence dedupes; mutate-config is CAS (conflict is not a retry); place-run uses logical invocation identity (outbox replay is not a second dispatch); external-egress obtains a receipt or becomes unknown and MUST NOT blind-retry. reconcile_policy never-retry and unknown-manual win. Parent AD-25 unknown-blocked is never auto-retried. A pack may set attempts to zero. A pack MUST NOT exceed the host ceiling or the effect-class matrix. Implementation edits (code, graph, grants, account target) are change_request (parent AD-29): app-use may mint; authoring plus operator apply. Alerts never authorize. HMR and hot-apply stay dead."
    status: ratified
    rationale: "Absorbed from architecture-QMX-2026-09-23 AD-6. Operator rider 2026-09-23."
    sources: [EXT-2292, EXT-2286]
    authority: rider
    component: COMP-QMA-CORE
    tags: [pack-and-grant, ad-6, retry]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md#ad-6"

  - id: DEC-0458
    title: "kit AD-7 — Weak models operate through schemas, not prose"
    statement: "Build and operate must work for a weaker/older model. Load-bearing surfaces are descriptors, GrantRecords, input_schema, typed refusals, and host-intercepted tool calls. Skills describe; they do not grant (parent AD-9). ContributionHit is not a grant. Hooks cannot override a failed privilege gate. MCP App HTML and json-render catalog entries cannot add ops or fields (parent AD-17). Model roster and prompt essays are not architecture."
    status: ratified
    rationale: "Absorbed from architecture-QMX-2026-09-23 AD-7. Operator rider 2026-09-23."
    sources: [EXT-2293, EXT-2286]
    authority: rider
    component: COMP-QMA-CORE
    tags: [pack-and-grant, ad-7, weak-models]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md#ad-7"

  - id: DEC-0459
    title: "kit AD-8 — Presentation adapters stay unpinned"
    statement: "JSON Render is a catalog-constrained generative view. MCP Apps (SEP-1865-class: tool plus ui:// resource, sandboxed iframe, host-proxied tools/call) are an optional in-conversation or in-panel view. Native QMX panes remain first. Do not pin @json-render/* or @modelcontextprotocol/ext-apps in this increment. json-render catalog actions must name existing parent-AD-3 op_ids and must not add or remove fields. MCP App HTML cannot grant tools; the host intercepts. Chrome, handoff UX, and dashboard layout remain GAP-0081 / GAP-0100. Local kit AD-8 is this adapter rule; parent AD-8 is product_session (cite parent AD-8 vs kit AD-8)."
    status: ratified
    rationale: "Absorbed from architecture-QMX-2026-09-23 AD-8. Operator rider 2026-09-23. Parent AD-17 stands."
    sources: [EXT-2294, EXT-2286]
    authority: rider
    component: COMP-QMA-WIRE
    tags: [pack-and-grant, ad-8, adapters]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md#ad-8"

  - id: DEC-0460
    title: "kit AD-9 — Tested work graduates to a pack"
    statement: "Daily idea path is: yap at authoring, then Graph Template (and/or ungoverned call), then runs with JobHandles, then pack export of those operations after validate. A Loop remains node state at runtime (parent AD-4). Packaging a loop exports the ops it calls; it does not mint a new loop engine. Graduation does not skip parent AD-18/AD-30 enable/validate."
    status: ratified
    rationale: "Absorbed from architecture-QMX-2026-09-23 AD-9. Operator rider 2026-09-23."
    sources: [EXT-2295, EXT-2286]
    authority: rider
    component: COMP-QMA-DAEMON
    tags: [pack-and-grant, ad-9, graduation]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md#ad-9"

  - id: DEC-0461
    title: "Pack-and-grant kit spine adopted in full (reuse existing applications; no sixth package)"
    statement: "The 2026-09-23 QMX pack-and-grant child spine (architecture-QMX-2026-09-23, local AD-1..AD-9) is adopted in full as DEC-0452 through DEC-0460. Parent architecture-QMX-2026-09-18 AD-1..AD-31 (DEC-0414..DEC-0444, ADR-0024) bind read-only. Local AD ids do not renumber parents. Named parent amendments are DEC-0463 (parent AD-8 / DEC-0421) and DEC-0464 (parent AD-24 / DEC-0437). Preflight reuse with no new COMP and no new CT (DEC-0462). Wiring honesty at 34c148b is DEC-0465. Dead-list honors are DEC-0466. Cheap-veto A7-A9 ride DEC-0467. ADR-0025 and SCN-0023..SCN-0027 are docs authority only. Implementation authorization remains factory-pipeline-only. Do not rewrite the 2026-09-16 QML fold or the 2026-09-19 Workflows fold."
    status: ratified
    rationale: "Operator launched Documentation Factory after accepting the sitting as the plan to fold; rider 2026-09-23 is authoritative."
    sources: [EXT-2296, EXT-2286]
    authority: rider
    component: COMP-QMA-CORE
    tags: [pack-and-grant, spine-adoption, umbrella, reuse]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md"

  - id: DEC-0462
    title: "Pack-and-grant preflight — reuse existing applications; no new COMP; no new CT"
    statement: "Preflight verdict: reuse existing applications. new COMP: none. new CT: none. No new depends_on edge and no existing component's authority shrinks. Work owners: pack SDK optional copilot_profile = COMP-QMA-CORE plus COMP-QMA-DAEMON plugin lifecycle; authoring app_instance_id optional and selected_refs kind instance_id = COMP-QMA-DAEMON plus COMP-QMA-WIRE (named amend DEC-0421); envelope caller_kind = COMP-QMA-CORE plus COMP-QMA-WIRE (named amend DEC-0437); daemon JSON-lines plus diagnosis query = COMP-QMA-DAEMON plus COMP-QMA-WIRE; default host retry none/read = COMP-QMA-CORE effects plus COMP-QMA-DAEMON; nested Mission invoke = COMP-QMA-DAEMON; listing axes plus instance health() = COMP-QMA-DAEMON plus COMP-QMA-WIRE; views = COMP-QMA-WIRE DTOs (parent AD-17). Candidates refused: COMP-WF / sixth COMP; new CT-*; third ProductSessionProfile; merged live Task Graphs; json-render/MCP as identity; QMB/QML core fork; fourth observability product; extending qmn/FAILURES.md; HMR/hot-apply; app-use applying change_request."
    status: ratified
    rationale: "Architecture preflight recorded for ADR-0025. Matches Workflows reuse pattern."
    sources: [EXT-2297, EXT-2296]
    authority: rider
    component: COMP-QMA-CORE
    tags: [pack-and-grant, preflight, reuse, no-new-comp, no-new-ct]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md"

  - id: DEC-0463
    title: "Named amendment of parent AD-8 / DEC-0421 — authoring app_instance_id optional; selected_refs kind instance_id"
    statement: "DEC-0421 product_session law is named-amended: app_instance_id MAY be absent when ProductSessionProfile=authoring (main/home, nothing selected). It remains required when profile=app-use. Closed selected_refs kinds gain instance_id. Authoring with absent session instance may not invoke. An invoke from that seat MUST carry envelope instance_id taken from a selected_refs kind instance_id; zero or many such refs is INVALID_INPUT (ambiguous instance). Envelope instance_id remains required on every invoke. No third ProductSessionProfile. The rest of DEC-0421 stands: psess: vs sess:, sessions own context and grants, tabs do not, app-use may mint change_request and must not apply. Do not set DEC-0421 superseded_by."
    status: ratified
    rationale: "Spine named parent amendment. Whole-supersession would erase standing product_session constraints the operator kept."
    sources: [EXT-2298, EXT-2289]
    authority: rider
    component: COMP-QMA-DAEMON
    tags: [pack-and-grant, parent-ad-8, amendment]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md"

  - id: DEC-0464
    title: "Named amendment of parent AD-24 / DEC-0437 — caller_kind user|agent|workflow"
    statement: "DEC-0437 InvocationEnvelope law is named-amended: every public call carries closed caller_kind user | agent | workflow. Envelope instance_id remains required on every invoke. The rest of DEC-0437 stands: logical invocation/attempt ids, contribution tuple, effect-specific idempotency, GrantRecord immutability, upgrade cannot widen. Do not set DEC-0437 superseded_by. Do not mint a new CT number for caller_kind (additive CT-40 family annotation until a format mint under FEAT-0058)."
    status: ratified
    rationale: "Spine named parent amendment. Additive field; not a second invoke API."
    sources: [EXT-2299, EXT-2290]
    authority: rider
    component: COMP-QMA-WIRE
    tags: [pack-and-grant, parent-ad-24, amendment]
    date: 2026-09-23
    spine_ref: "SRC-24:ARCHITECTURE-SPINE.md"

  - id: DEC-0465
    title: "Wiring honesty @ 34c148b — inherit DEC-0286; connect/amend vs absent"
    statement: "Inherit DEC-0286: class/test existence is not end-to-end demonstration. On integration@34c148b this session reconfirmed CONNECT (types/fixtures exist): InvocationEnvelope, GrantRecord, product_session / ProductSessionProfile, effect-class plus reconcile_policy, call_depth / parent_logical_invocation_id, Workflows 53-59 fixtures. AMEND: ProductSession.app_instance_id is required str; SELECTED_REF_KINDS lacks instance_id; envelope has no caller_kind. ABSENT as product surface: pack copilot_profile; qma-daemon stdlib JSON-lines operator logger; kit failure_class grant|workflow|view|dependency|host; default host retry loop; nested Mission invoke as first-class; CheckpointManifest. Parent freeze 270e992 still applies for ADR-0024 original Decision text (DEC-0450). Do not claim envelope/grant/product_session types are absent at 34c148b. Do not claim caller_kind, optional authoring instance, or daemon JSON-lines exist as wired product surface at 34c148b. Implementation authorization still arrives only through the factory pipeline."
    status: ratified
    rationale: "Operator rider evidence-honesty pin plus inspect SHA for this fold."
    sources: [EXT-2300]
    authority: rider
    component: COMP-QMA-WIRE
    tags: [pack-and-grant, wiring, source-inspected, 34c148b]
    date: 2026-09-23
    spine_ref: "SRC-25"

  - id: DEC-0466
    title: "Dead-list honors — screen-kit, automation-kit, third profile, live-graph merge, adapter-as-authority stay dead"
    statement: "This increment honors existing deaths and does not revive them: DEC-0084 / DEC-0085 / DEC-0086 stay dead; DEC-0361 marketplace, DEC-0362 solver, and DEC-0366 HMR stay dead; DEC-0408..DEC-0413 mill deaths stay dead. Screen-kit and automation-kit as the center stay dead. Third ProductSessionProfile stays un-minted. Merging two live Task Graphs is refused. JSON Render and MCP Apps as identity, persistence, runtime, or authority stay dead. No COMP-WF / sixth application. No new CT. No QMB/QML core fork. No fourth observability product. No extending qmn/FAILURES.md onto mini-apps."
    status: ratified
    rationale: "Rider dead-list section. This entry is ratified (honors deaths); it is not itself a dead entry."
    sources: [EXT-2301, EXT-2286]
    authority: rider
    component: COMP-QMA-CORE
    tags: [pack-and-grant, dead-list, honors]
    date: 2026-09-23
    spine_ref: "SRC-25"

  - id: DEC-0467
    title: "Pack-and-grant cheap-veto register A7-A9"
    statement: "Cheap-veto assumptions for kit sitting machinery, each individually overturnable without unwinding another call: (A7) diagnosis failure_class closed set grant | workflow | view | dependency | host — proceed; class is sitting law; spellings are machinery. (A8) daemon JSON-lines extra fields when present (instance_id, op_id, logical_invocation_id, graph_run_id) — proceed; required fields ts, level, event, correlation_id are operator-direct. (A9) host retry attempt ceiling is a registry row; this sitting mints no number (GAP-0108) — proceed. Not vetoable here: no sixth COMP; no new CT; no third profile; envelope instance_id required on invoke; nested live-graph merge refused; app-use cannot apply; no blind external-egress retry; logs are not journals; json-render/MCP unpinned; GAP-0081 chrome later."
    status: ratified
    rationale: "Workflows cheap-veto pattern for sitting machinery after operator-direct pack-and-grant class."
    sources: [EXT-2302, EXT-2286]
    authority: rider
    component: COMP-QMA-CORE
    tags: [pack-and-grant, cheap-veto, assumptions]
    date: 2026-09-23
    spine_ref: "SRC-25"
"""

GAPS = r"""
  - id: GAP-0101
    question: "When does InvocationEnvelope gain closed caller_kind user|agent|workflow on COMP-QMA-CORE / COMP-QMA-WIRE?"
    needed_by: [COMP-QMA-CORE, COMP-QMA-WIRE]
    blocking: false
    recommendation: "Feeds FEAT-0058. Absent at 34c148b (DEC-0465). Additive named amendment of DEC-0437 (DEC-0464). No new CT number."
    status: deferred
    answer: null
    note: "Pack-and-grant kit AD-4 / DEC-0455 / DEC-0464. Envelope instance_id remains required on invoke."
    date: 2026-09-23
  - id: GAP-0102
    question: "When may authoring omit app_instance_id, and when does selected_refs accept kind instance_id?"
    needed_by: [COMP-QMA-DAEMON, COMP-QMA-WIRE]
    blocking: false
    recommendation: "Feeds FEAT-0058. At 34c148b ProductSession.app_instance_id is required str and SELECTED_REF_KINDS lacks instance_id (DEC-0465). Named amendment of DEC-0421 (DEC-0463)."
    status: deferred
    answer: null
    note: "Pack-and-grant parent AD-8 amendment. App-use still requires instance. Envelope instance_id remains required on invoke. No third profile."
    date: 2026-09-23
  - id: GAP-0103
    question: "When may a pack omit copilot_profile as a request blob (not a contribution point and not a grant)?"
    needed_by: [COMP-QMA-CORE, COMP-QMA-DAEMON]
    blocking: false
    recommendation: "Feeds FEAT-0058. Absent at 34c148b (DEC-0465). Headless packs remain valid (DEC-0452, DEC-0454)."
    status: deferred
    answer: null
    note: "Pack-and-grant kit AD-1/AD-3. Optional in-app panel is a contract, not GAP-0081 chrome."
    date: 2026-09-23
  - id: GAP-0104
    question: "When does qma-daemon emit stdlib JSON-lines operator logs (ts, level, event, correlation_id)?"
    needed_by: [COMP-QMA-DAEMON]
    blocking: false
    recommendation: "Feeds FEAT-0059. Absent at 34c148b (DEC-0465). Do not extend qmn/FAILURES.md. Do not mint a fourth observability product."
    status: deferred
    answer: null
    note: "Pack-and-grant kit AD-5 / DEC-0456. Logs are not evidence (DEC-0112, parent AD-16)."
    date: 2026-09-23
  - id: GAP-0105
    question: "When does the host expose diagnosis failure_class grant|workflow|view|dependency|host plus instance health()?"
    needed_by: [COMP-QMA-DAEMON, COMP-QMA-WIRE]
    blocking: false
    recommendation: "Feeds FEAT-0059 and FEAT-0062. Absent at 34c148b (DEC-0465). Cheap-veto A7 covers spellings (DEC-0467)."
    status: deferred
    answer: null
    note: "Pack-and-grant kit AD-5 / DEC-0456. view is wire-DTO mount/stale/unhealthy, not an invoke."
    date: 2026-09-23
  - id: GAP-0106
    question: "When is default host retry of effect none/read wired to the parent AD-24 effect-class matrix?"
    needed_by: [COMP-QMA-CORE, COMP-QMA-DAEMON]
    blocking: false
    recommendation: "Feeds FEAT-0060. Effect types and reconcile_policy exist at 34c148b as fixtures; the host retry loop is absent (DEC-0465). No blind external-egress retry."
    status: deferred
    answer: null
    note: "Pack-and-grant kit AD-6 / DEC-0457. Attempt ceiling number is GAP-0108."
    date: 2026-09-23
  - id: GAP-0107
    question: "When is workflow-to-workflow a nested Mission invoke (one nested JobHandle) rather than a live Task Graph merge?"
    needed_by: [COMP-QMA-DAEMON]
    blocking: false
    recommendation: "Feeds FEAT-0061 after durable Task Graph edges FEAT-0055. Include-at-author remains a new versioned Graph Template."
    status: deferred
    answer: null
    note: "Pack-and-grant kit AD-4 / DEC-0455. Recursion ceiling number not minted."
    date: 2026-09-23
  - id: GAP-0108
    question: "What numeric host retry attempt ceiling is registered (registry row)?"
    needed_by: [COMP-QMA-CORE, COMP-QMA-DAEMON]
    blocking: false
    recommendation: "Out of this sitting. Spine minted no number (DEC-0457, DEC-0467 A9). Do not invent 3 or any other cap in stories until a registry row is ratified."
    status: deferred
    answer: null
    note: "Pack-and-grant cheap-veto A9. Distinct from parent AD-10 recursion ceiling, also unnumbered."
    date: 2026-09-23
"""

FEATS = r"""
  - id: FEAT-0058
    name: "Host SDK pack-and-grant (optional copilot_profile; authoring instance optional; caller_kind)"
    scope: >-
      In: pack manifest requests operations, optional view:* wire DTOs, optional
      copilot_profile request blob, requested_capabilities; host grants
      GrantRecords (DEC-0452, DEC-0453); ProductSessionProfile authoring may omit
      app_instance_id and selected_refs gains kind instance_id with exactly-one
      rule on invoke (DEC-0454, DEC-0463); InvocationEnvelope gains caller_kind
      user|agent|workflow (DEC-0455, DEC-0464); envelope instance_id remains
      required on invoke; no new COMP or CT (DEC-0462). Out: third profile;
      view:* as contribution point; installing as granting; chrome (GAP-0081).
      Done means the host SDK field changes are specified; implementation
      authorization still arrives only through the factory pipeline.
    decisions: [DEC-0452, DEC-0453, DEC-0454, DEC-0463, DEC-0464, DEC-0462]
    components: [COMP-QMA-CORE, COMP-QMA-WIRE, COMP-QMA-DAEMON]
    blocked_by:
      - id: FEAT-0052
        reason: "caller_kind and pack descriptors extend InvocationEnvelope / GrantRecord / operation descriptor FEAT-0052 lands (DEC-0416, DEC-0437, DEC-0464)"
      - id: FEAT-0053
        reason: "authoring app_instance_id optionality amends product_session CAS FEAT-0053 lands (DEC-0421, DEC-0463)"
    size: multi-pass
    status: planned
    notes: "First epic after this documentation-factory pass. Feeds GAP-0101, GAP-0102, GAP-0103. Implementation authorization factory-pipeline-only."

  - id: FEAT-0059
    name: "Daemon JSON-lines operator logs plus diagnosis query"
    scope: >-
      In: qma-daemon stdlib JSON-lines with required ts, level, event,
      correlation_id and optional instance_id, op_id, logical_invocation_id,
      graph_run_id when present (DEC-0456); headless diagnosis query returns
      failure_class grant|workflow|view|dependency|host plus JobHandle plus
      healthy (DEC-0456); QMA telemetry store remains the trace/metric plane;
      logs are not evidence. Out: fourth observability product; extending
      qmn/FAILURES.md; agents authoring telemetry. Done means diagnosis and
      daemon logs are specified; implementation authorization still arrives
      only through the factory pipeline.
    decisions: [DEC-0456, DEC-0465, DEC-0467]
    components: [COMP-QMA-DAEMON, COMP-QMA-WIRE]
    blocked_by:
      - id: FEAT-0058
        reason: "diagnosis fields join instance_id / op_id / logical_invocation_id from the host SDK envelope FEAT-0058 lands (DEC-0455, DEC-0456)"
      - id: FEAT-0042
        reason: "daemon JSON-lines and health queries extend existing daemon sqlite / journal projections FEAT-0042 lands, not a new store class (DEC-0429, DEC-0456)"
    size: multi-pass
    status: planned
    notes: "Feeds GAP-0104, GAP-0105. Implementation authorization factory-pipeline-only."

  - id: FEAT-0060
    name: "Default host retry for effect none/read"
    scope: >-
      In: host/SDK retries effect none and read until success, typed
      retryability=NO, or host-registered attempt ceiling (DEC-0457); parent
      AD-24 matrix unchanged — no blind external-egress retry; CAS conflict is
      not a retry; unknown-blocked never auto-retried; pack may set attempts
      to zero and must not exceed host ceiling. Out: per-pack retry dialect;
      retry of every effect; minting the ceiling number (GAP-0108). Done means
      default retry is specified; implementation authorization still arrives
      only through the factory pipeline.
    decisions: [DEC-0457, DEC-0464, DEC-0467]
    components: [COMP-QMA-CORE, COMP-QMA-DAEMON]
    blocked_by:
      - id: FEAT-0058
        reason: "retry is host behaviour on the pack-and-grant envelope and effect_class FEAT-0058 lands (DEC-0452, DEC-0457)"
      - id: FEAT-0052
        reason: "effect-class idempotency matrix and reconcile_policy FEAT-0052 lands remain the retry law (DEC-0437, DEC-0457)"
    size: multi-pass
    status: planned
    notes: "Feeds GAP-0106. Ceiling number is GAP-0108. Implementation authorization factory-pipeline-only."

  - id: FEAT-0061
    name: "Nested Mission invoke (workflow-to-workflow)"
    scope: >-
      In: workflow-to-workflow at runtime is parent-AD-3 invoke of the callee
      template start/query-state/cancel/await creating one nested Mission /
      one Task Graph / one JobHandle (DEC-0455); include-at-author is a new
      versioned Graph Template; merging two live Task Graphs is refused;
      nested invoke does not union grants. Out: live-graph splice; a fifth
      composition mode; widget-owned invoke. Done means nested Mission invoke
      is specified; implementation authorization still arrives only through
      the factory pipeline.
    decisions: [DEC-0455, DEC-0462]
    components: [COMP-QMA-DAEMON, COMP-QMA-CORE]
    blocked_by:
      - id: FEAT-0055
        reason: "nested Mission JobHandle occupancy assumes durable Task Graph edges and outbox FEAT-0055 lands (DEC-0439, DEC-0455)"
      - id: FEAT-0058
        reason: "callee invoke rides caller_kind=workflow and envelope instance_id from the host SDK FEAT-0058 lands (DEC-0455, DEC-0464)"
    size: multi-pass
    status: planned
    notes: "Feeds GAP-0107. Implementation authorization factory-pipeline-only."

  - id: FEAT-0062
    name: "Listing axes plus instance health() for copilot/CLI"
    scope: >-
      In: host exposes parent AD-15 listing axes including healthy, and
      instance health() as the existing component typed-report distinct from
      pack published (DEC-0456, DEC-0428); copilot and CLI consume the same
      headless queries. Out: chrome dashboard (GAP-0081 / GAP-0100); treating
      published as healthy. Done means listing and health queries are
      specified; implementation authorization still arrives only through the
      factory pipeline.
    decisions: [DEC-0456, DEC-0428, DEC-0462]
    components: [COMP-QMA-DAEMON, COMP-QMA-WIRE]
    blocked_by:
      - id: FEAT-0058
        reason: "health and listing join pack instance rows and GrantRecords the host SDK FEAT-0058 lands (DEC-0452, DEC-0456)"
      - id: FEAT-0051
        reason: "published vs authorized listing axes reuse ContributionHit concatenate FEAT-0051 lands (DEC-0415, DEC-0428)"
    size: multi-pass
    status: planned
    notes: "Feeds GAP-0105. Implementation authorization factory-pipeline-only."

  - id: FEAT-0063
    name: "Thin fixtures for pack-and-grant journeys (headless, optional panel, home pick, nested Mission, retry, diagnosis)"
    scope: >-
      In: thin fixtures proving J-KIT-01 headless pack with no copilot
      (DEC-0452, DEC-0454); J-KIT-02 optional in-app panel cannot apply
      (DEC-0454, DEC-0442); J-KIT-03 home authoring exactly-one instance_id
      (DEC-0463); J-KIT-05 nested Mission not live merge (DEC-0455);
      J-KIT-06 host retry none/read and no blind external-egress
      (DEC-0457); J-KIT-07 weak model fills schemas (DEC-0458). Out:
      inventing chrome; claiming e2e adoption at 34c148b (DEC-0465).
      Done means the fixtures are specified for factory stories;
      implementation authorization still arrives only through the factory
      pipeline.
    decisions: [DEC-0452, DEC-0454, DEC-0455, DEC-0456, DEC-0457, DEC-0458, DEC-0463, DEC-0465]
    components: [COMP-QMA-CORE, COMP-QMA-DAEMON, COMP-QMA-WIRE]
    blocked_by:
      - id: FEAT-0058
        reason: "kit journeys invoke the host SDK field changes FEAT-0058 lands (DEC-0452, DEC-0463, DEC-0464)"
      - id: FEAT-0059
        reason: "diagnosis journey reads failure_class and JSON-lines FEAT-0059 lands (DEC-0456)"
      - id: FEAT-0060
        reason: "retry journey requires default host retry FEAT-0060 lands (DEC-0457)"
      - id: FEAT-0061
        reason: "nested-workflow journey requires nested Mission invoke FEAT-0061 lands (DEC-0455)"
      - id: FEAT-0062
        reason: "headless listing/health journey requires listing axes FEAT-0062 lands (DEC-0456)"
      - id: FEAT-0056
        reason: "kit fixtures trail Workflows thin proof fixtures FEAT-0056 lands so change-request and pack export stay the same envelopes (DEC-0442, DEC-0443)"
    size: multi-pass
    status: planned
    notes: "Implementation authorization factory-pipeline-only."
"""


def main() -> None:
    append_if_missing(ROOT / "_docwork/manifest.yaml", "id: SRC-24", MANIFEST)
    append_if_missing(ROOT / "_docwork/extractions.yaml", "id: EXT-2286", EXTR)
    append_if_missing(ROOT / "_docwork/ledger.yaml", "id: DEC-0452", LEDGER)
    patch_gap_0081(ROOT / "_docwork/gaps.yaml")
    patch_gap_0093(ROOT / "_docwork/gaps.yaml")
    patch_gap_0096(ROOT / "_docwork/gaps.yaml")
    patch_gap_0100(ROOT / "_docwork/gaps.yaml")
    append_if_missing(ROOT / "_docwork/gaps.yaml", "id: GAP-0101", GAPS)
    append_if_missing(ROOT / "_docwork/feature_inventory.yaml", "id: FEAT-0058", FEATS)
    print("done")


if __name__ == "__main__":
    main()
