#!/usr/bin/env python3
"""Append UI-host + backend-delta change-mode YAML. Run once from project root. Idempotent by id."""
from __future__ import annotations

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


def yaml_list(ids: list[str]) -> str:
    return "[" + ", ".join(ids) + "]"


def ext_block(eid: str, typ: str, summary: str, quote: str, cite: str, topics: list[str]) -> str:
    tops = "[" + ", ".join(topics) + "]"
    return (
        f"  - id: {eid}\n"
        f"    type: {typ}\n"
        f"    summary: {summary!r}\n"
        f"    quote: {quote!r}\n"
        f"    cite: {cite}\n"
        f"    topics: {tops}\n"
        f"    authority: rider\n"
    )


def dec_block(
    did: str,
    title: str,
    statement: str,
    rationale: str,
    sources: list[str],
    component: str,
    tags: list[str],
    spine_ref: str,
) -> str:
    return (
        f"  - id: {did}\n"
        f"    title: {title!r}\n"
        f"    statement: {statement!r}\n"
        f"    status: ratified\n"
        f"    rationale: {rationale!r}\n"
        f"    sources: {yaml_list(sources)}\n"
        f"    authority: rider\n"
        f"    component: {component}\n"
        f"    tags: {yaml_list(tags)}\n"
        f"    date: 2026-09-25\n"
        f"    spine_ref: {spine_ref!r}\n"
        f"\n"
    )


def gap_new(
    gid: str,
    question: str,
    needed: list[str],
    recommendation: str,
    status: str,
    answer: str | None,
    note: str,
) -> str:
    ans = "null" if answer is None else repr(answer)
    answered = ""
    if status == "answered":
        answered = "    answered_by: operator (architecture sittings 2026-09-23/24; Documentation Factory 2026-09-25)\n"
    return (
        f"  - id: {gid}\n"
        f"    question: {question!r}\n"
        f"    needed_by: {yaml_list(needed)}\n"
        f"    blocking: false\n"
        f"    recommendation: {recommendation!r}\n"
        f"    status: {status}\n"
        f"    answer: {ans}\n"
        f"{answered}"
        f"    note: {note!r}\n"
        f"    date: 2026-09-25\n"
    )


def feat_block(
    fid: str,
    name: str,
    scope: str,
    decisions: list[str],
    components: list[str],
    blocked: list[tuple[str, str]],
    notes: str,
) -> str:
    lines = [
        f"  - id: {fid}",
        f"    name: {name!r}",
        "    scope: >-",
    ]
    for para in scope.strip().split("\n"):
        lines.append("      " + para.strip())
    lines.append(f"    decisions: {yaml_list(decisions)}")
    lines.append(f"    components: {yaml_list(components)}")
    lines.append("    blocked_by:")
    for bid, reason in blocked:
        lines.append(f"      - id: {bid}")
        lines.append(f"        reason: {reason!r}")
    lines.append("    size: multi-pass")
    lines.append("    status: planned")
    lines.append(f"    notes: {notes!r}")
    lines.append("")
    return "\n".join(lines)


MANIFEST = """
- id: SRC-27
  path: _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/
  kind: rider
  role: primary
  status: harvested
  note: "2026-09-23/24 QMX UI host architecture sitting (local UI AD-1..AD-24) over parent 09-18 and kit 09-23. Closes GAP-0081 chrome and GAP-0100 observation surfaces as this sitting's job. Codex R1-R9 closed as candidate then reconciled with backend-delta. Operator launched Documentation Factory 2026-09-25 after Codex PASS."
- id: SRC-28
  path: _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/
  kind: rider
  role: primary
  status: harvested
  note: "2026-09-24 QMX UI backend-delta sitting (local backend AD-1..AD-17). Named AM-01..AM-17. C1/C2 and J1-J5 closed as candidate. Codex 2026-09-25 recheck PASS. Inspect integration@34c148be."
- id: SRC-29
  path: _docwork/riders/ui-and-backend-delta-2026-09-25.md
  kind: rider
  role: primary
  status: harvested
  note: "Operator-direct rider for the 2026-09-25 documentation-factory change-mode session."
- id: SRC-30
  path: workroom/qmx-ui-final-closure-2026-09-24/
  kind: rider
  role: primary
  status: harvested
  note: "Codex focused closure 2026-09-24 REVIEW.md plus 2026-09-25 RECHECK PASS. Non-blocking AM-10 stop-exception wording cleanup."
"""


def build_extractions() -> str:
    items = [
        ("EXT-2464", "decision",
         "Operator launched Documentation Factory 2026-09-25 after Codex PASS. Fold UI host plus backend-delta into existing docs/. No sixth COMP. No new CT. No COMP-UI. No epic rewrite this session. No application code.",
         "Ready for one integrated Documentation Factory pass.",
         "SRC-29", ["ui-host", "backend-delta", "rider"]),
        ("EXT-2465", "decision",
         "UI AD-2 Host stack seed: Svelte 5.57.1, SvelteKit 2.70.3 adapter-static ssr=false, TypeScript 5.9, Vite 8.3.0, Tailwind 4.3.3, shadcn-svelte 1.7.0 Rhea, bits-ui 2.19.3, @xyflow/svelte 1.6.6. Node.js >=22.12.0 <23.0.0 and pnpm. SPA static origin never daemon port 8765. Refuse React/Next, Qt, Kit 3 RC, Tauri 3 alpha.",
         "Seed is Svelte 5.57.1 + SvelteKit 2.70.3 + TypeScript 5.9 + Vite 8.3.0.",
         "SRC-27", ["ui-host", "ad-2", "stack"]),
        ("EXT-2466", "decision",
         "UI AD-3 Platform destinations: Home (work/attention/resume), Copilot (conversation), Library, Authoring independent above the divider. Shared components allowed. Not the same destination. Study-03 one-shell and LSE ML Studio layout refused.",
         "Home is work/attention/resume. Copilot is conversation. Authoring is back on the rail with Library.",
         "SRC-27", ["ui-host", "ad-3", "rail"]),
        ("EXT-2467", "decision",
         "UI AD-18 Chat send is mailbox not invoke. Unique issuer dispatchChat -> send_message. No instance required. Durable history is QMA mailbox with product_session_ref at write. Principal equality when that field is present.",
         "ConversationPane.send = CT-40 send_message mailbox, no InvocationEnvelope.",
         "SRC-27", ["ui-host", "ad-18", "mailbox"]),
        ("EXT-2468", "decision",
         "UI AD-19 v1 bootstrap owner is QMB CLI. Externally running daemon. Pairing proof is pairing_proof. HTTP Bearer pairing:<proof>. WS subprotocols qmx.ct40.v1 and qmx.pair.<proof>. Unauthenticated HTTP only /pair/start, /pair/confirm, CORS OPTIONS. Origin never sufficient for issuance.",
         "A remembered Origin never authorizes issuance of a new pairing_proof.",
         "SRC-27", ["ui-host", "ad-19", "pairing"]),
        ("EXT-2469", "decision",
         "Backend AD-4 pairing_proof is bearer; pairing_record_id is journal identity; hash-only in journal. Origin-revoke is journal_seq barrier (C2). --session is that record only. After barrier new /pair/start is legal.",
         "Origin-revoke is a barrier at journal_seq R; renew-then-revoke kills the new proof.",
         "SRC-28", ["backend-delta", "ad-4", "c2"]),
        ("EXT-2470", "decision",
         "Backend AD-6/AD-17 first operator is OS owner of QMA_DAEMON_ROOT plus host_control. recover-control on stopped daemon does not present the lost token (C1). QMB never writes sqlite. Stop without token only when file missing/unreadable and caller is OS owner.",
         "Lost host_control recovery does not require the lost token.",
         "SRC-28", ["backend-delta", "ad-17", "c1"]),
        ("EXT-2471", "decision",
         "Backend AD-7 mailbox delivery stays Epic 46 / Story 46.4. Additive product_session_ref excluded from Envelope fp1. list_mailbox addable Epic 41 query. AM-12 journal-lifetime collision for send_message pair+hash.",
         "Durable mailbox delivery is Epic 46 / Story 46.4.",
         "SRC-28", ["backend-delta", "ad-7", "mailbox"]),
        ("EXT-2472", "decision",
         "Named AM-01..AM-17: unauthenticated pairing carve-out; mailbox product_session_ref; journal projections pairing/draft/ticket/local_operator; originating_product_session_ref; PUT byte channel; reachable transfer; drafts not AD-22; addable list_mailbox/cancel_job/transfer_*/save_editor_draft/publish_editor_draft/get_pack_ui_request/get_editor_draft_head; qmb host group including recover-control; host-control outside 8765; _ref names.",
         "Every conflict with inherited contracts is named. Nothing silently overrides a parent.",
         "SRC-28", ["backend-delta", "amendments"]),
        ("EXT-2473", "decision",
         "Preflight reuse existing applications. new COMP none. new CT none. UI is a client of qma-wire. No COMP-UI. No new depends_on edge.",
         "The UI host is a client, not a COMP. No sixth COMP. No new CT.",
         "SRC-29", ["ui-host", "preflight", "reuse"]),
        ("EXT-2474", "context",
         "Wiring honesty at integration@34c148be: DaemonProcess discards TCP bytes. Pairing, qmb host, list_mailbox, cancel_job, stage_artifact, editor drafts, PackUiRequest read-back absent. Envelope/GrantRecord/product_session types exist as fixtures not e2e. Envelope has no product_session_ref. JobHandle has no originating_product_session_ref.",
         "Live CT-40 server: No. DaemonProcess._handle_client discards TCP bytes.",
         "SRC-28", ["honesty", "34c148be"]),
        ("EXT-2475", "death",
         "Dead list honored: no COMP-UI; no cookie login; no localStorage pairing; no ui_view contribution point; no AD-22 draft store; study 01/02/03 baseline rejected; LSE ML Studio layout refused; Qt refused; sixth COMP refused; json-render/MCP as identity refused.",
         "Chrome never becomes a sixth COMP, a second scheduler, or a second grant store.",
         "SRC-29", ["dead-list"]),
        ("EXT-2476", "decision",
         "GAP-0081 chrome and GAP-0100 observation surfaces are answered sitting law of the UI sitting, delivered by FEAT-0064..FEAT-0071. They remain out-of-scope as pack-and-grant kit holes. Inspect absence is wiring honesty not a gap.",
         "GAP-0081 chrome and GAP-0100 observation surfaces are answered sitting law of this UI sitting.",
         "SRC-29", ["gaps", "catalog"]),
        ("EXT-2477", "decision",
         "Cheap-veto A10-A14: pairing TTL registry row no number; artifact.stage_max_bytes registry row no number; Rhea compact visual seed; Node >=22.12 <23; Windows %LOCALAPPDATA%\\QMX\\qma-daemon product root. Not vetoable: no sixth COMP; Origin-never-sufficient; no cookies; no COMP-UI; Epic 60 copilot_profile sibling; recover-control preserves principal.",
         "TTL is registry:pairing.session_ttl with no number minted.",
         "SRC-29", ["cheap-veto"]),
        ("EXT-2478", "decision",
         "Unique invoke issuer dispatchInvoke. Unique cancel issuer dispatchCancel. Widgets never own invoke. Tab close does not cancel JobHandle.",
         "Widgets paint. One function, dispatchInvoke, is the only invoke issuer. Closing a tab does not stop work.",
         "SRC-27", ["ui-host", "issuers"]),
        ("EXT-2479", "decision",
         "Do not duplicate Epics 60-65 / FEAT-0058..FEAT-0063. copilot_profile stays Epic 60 sibling. caller_kind and optional authoring instance stay FEAT-0058.",
         "Avoid duplicating Epics 60-65.",
         "SRC-30", ["reuse", "epics-60-65"]),
    ]
    return "\n" + "".join(ext_block(*it) for it in items)


def build_ledger() -> str:
    R = "Operator rider 2026-09-25; Codex PASS; sitting accepted as the plan to fold."
    rows = [
        ("DEC-0469", "UI AD-2 — Host stack seed",
         "Frontend seed is Svelte 5.57.1 + SvelteKit 2.70.3 + TypeScript 5.9 (Kit 2 peer) + Vite 8.3.0 + Tailwind CSS 4.3.3 + shadcn-svelte 1.7.0 (Rhea, MIT) + bits-ui 2.19.3 + @xyflow/svelte 1.6.6. Toolchain is Node.js >=22.12.0 <23.0.0 and pnpm with apps/qmx-ui/pnpm-lock.yaml recorded at an unexecuted isolated-scaffold gate. Root layout sets ssr=false; @sveltejs/adapter-static. SPA fallback is 200.html on a static host; a later Tauri template may use index.html. The SPA is served from a static origin, never from daemon port 8765. Refuse React/Next dashboard kits, Qt, SvelteKit 3 RC as a required pin, Tauri 3 alpha, and wrapping every primitive. Optional json-render 0.21.0 and @modelcontextprotocol/ext-apps 2.0.0 remain adapters not authority. Optional Lightweight Charts 5.2.1 for financial tape and LayerChart 2.5.0 for ordinary analytics.",
         R, ["EXT-2465", "EXT-2464"], "COMP-QMA-WIRE", ["ui-host", "ad-2", "stack"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-2"),
        ("DEC-0470", "UI AD-3 — Platform destinations stay independent",
         "A persistent narrow platform rail holds destinations above a divider and opened-app icons below. Above, with zero opened apps: Home (work / attention / resume), Copilot (conversation workspace), Library, Authoring. Settings is chrome, not a fifth product destination. Home and Copilot may reuse SessionList / ConversationPane components; they are not the same destination or purpose. Authoring is independently reachable and uses the graph/code/ML family even with no app open. Mini-app interiors keep app nav above a dense widget canvas. Study-03 one three-column shell and LSE ML Studio as layout are refused. Home/Authoring use profile authoring; Copilot of an app-use panel uses app-use. No third profile.",
         R, ["EXT-2466", "EXT-2464"], "COMP-QMA-WIRE", ["ui-host", "ad-3", "rail"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-3"),
        ("DEC-0471", "UI AD-5 — Independent dimensions",
         "Visual, headless, and mixed packs are independent. A pack may omit view:* and copilot_profile. Enable is not grant. Headless invoke stays a first-class door via qmb / CT-40. Chrome must not require a pane to run granted work.",
         R, ["EXT-2464"], "COMP-QMA-WIRE", ["ui-host", "ad-5", "headless"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-5"),
        ("DEC-0472", "UI AD-6 — Three presentation lanes; native first",
         "Three presentation lanes: native Svelte mounts, optional json-render catalog views, optional MCP Apps sandboxed views. Native panes are first. json-render and MCP Apps are adapters not authority, identity, persistence, or grant. Host-minted ActionContext binds every mounted view (DEC-0486).",
         R, ["EXT-2464"], "COMP-QMA-WIRE", ["ui-host", "ad-6", "lanes"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-6"),
        ("DEC-0473", "UI AD-7 — Composer splits content, tools, and target",
         "Composer splits content, tools, and target. Tools come from parent AD-9 intersection. TargetPicker supplies bindActionContext for non-mount callers. Widgets never call the wire.",
         R, ["EXT-2478"], "COMP-QMA-WIRE", ["ui-host", "ad-7", "composer"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-7"),
        ("DEC-0474", "UI AD-8 — Widgets bind and display; expand is explicit",
         "Widgets bind and display. Expand/return is explicit layout change and must restore graph viewport. Widgets never own invoke. Unique invoke issuer is apps/qmx-ui/src/lib/host/dispatchInvoke.",
         R, ["EXT-2478"], "COMP-QMA-WIRE", ["ui-host", "ad-8", "widgets"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-8"),
        ("DEC-0475", "UI AD-9 — Graph, code, and detail stay one family",
         "Authoring/ML is one graph/code/detail family (VS Code image). Draft, immutable template version, pack instance, and JobHandle stay distinct (DEC-0487). LSE ML Studio UI is refused as layout.",
         R, ["EXT-2466"], "COMP-QMA-WIRE", ["ui-host", "ad-9", "authoring"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-9"),
        ("DEC-0476", "UI AD-10 — Library is one chrome over typed hits",
         "Library overlays typed hits and must not collapse kinds. Uploads become artifacts only after daemon PUT completeness (DEC-0488). Knowledge cite uses returned artifact fp1 plus provenance. Widget message-only refs are chrome until saved.",
         R, ["EXT-2464"], "COMP-QMA-WIRE", ["ui-host", "ad-10", "library"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-10"),
        ("DEC-0477", "UI AD-11 — First-run is partial readiness",
         "First-run is partial readiness. Splash then usable window. One provider failure does not block the shell. Clean-machine shell launch is not provider-ready. Secrets never enter the page.",
         R, ["EXT-2470"], "COMP-QMA-DAEMON", ["ui-host", "ad-11", "first-run"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-11"),
        ("DEC-0478", "UI AD-12 — Python daemon owns runtime; Tauri is optional later",
         "Python qma-daemon owns runtime. v1 is browser plus host-supervised daemon. Tauri 2 is an optional later desktop shell, not required for protocol. Rust in Tauri must not become a second orchestrator. UI must not import qmb/qml/qmn.",
         R, ["EXT-2465"], "COMP-QMA-DAEMON", ["ui-host", "ad-12", "process"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-12"),
        ("DEC-0479", "UI AD-13 — Close, stop, cancel, and unknown are distinct",
         "Panel dispose does not cancel JobHandle. Stop, cancel, and unknown are distinct chrome states. Cancelled display is not proof the worker stopped. Interrupt is not labelled cancelled.",
         R, ["EXT-2478"], "COMP-QMA-DAEMON", ["ui-host", "ad-13", "lifecycle"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-13"),
        ("DEC-0480", "UI AD-14 — Operations chrome consumes kit queries",
         "Operations chrome consumes kit listing axes, instance health(), JobHandle snapshots, and diagnosis queries. It does not mint a fourth observability product. Logs are not journals. GAP-0100 dashboard-as-kit-hole is answered by this chrome consuming those queries.",
         R, ["EXT-2476"], "COMP-QMA-WIRE", ["ui-host", "ad-14", "ops"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-14"),
        ("DEC-0481", "UI AD-15 — view:* stays a wire DTO; PackUiRequest is ingested request",
         "This sitting does not mint a ui_view contribution point. Packs still contribute operations only. Navigation and views are versioned request DTOs ingested at enable (qmx.ui.pack_ui_request.v1). Read-back is addable query get_pack_ui_request keyed by enabled instance_id plus availability_revision. Optional PluginManifest.copilot_profile stays the Epic 60 / kit sibling field; the UI request references it and must not replace or forbid it. Published still does not grant.",
         R, ["EXT-2479", "EXT-2464"], "COMP-QMA-DAEMON", ["ui-host", "ad-15", "pack-ui"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-15"),
        ("DEC-0482", "UI AD-16 — UI integration is a sibling of backend integration",
         "New UI work lives on a dedicated integration stream cut from integration@34c148be. Do not reuse the old ui branch at af66288 as the app base. Combine only for a tested deployment candidate, then the operator promotes to main. User-facing implementation later requires Reticle act-and-wait/assert plus process evidence Reticle cannot supply.",
         R, ["EXT-2464"], "COMP-QMA-WIRE", ["ui-host", "ad-16", "delivery"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-16"),
        ("DEC-0483", "UI AD-17 — Research charts keep provenance",
         "Ordinary analytics charts use shadcn-svelte / LayerChart. Financial candlesticks use a dedicated host (lightweight-charts or successor) behind WidgetFrame. Missing, empty, truncated, and denied are distinct chrome states. Streaming plots consume stream doors; a stream subscription is not trading permission. Preview is not export.",
         R, ["EXT-2465"], "COMP-QMA-WIRE", ["ui-host", "ad-17", "charts"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-17"),
        ("DEC-0484", "UI AD-18 — Chat send is mailbox, not invoke",
         "Unique chat issuer is apps/qmx-ui/src/lib/host/dispatchChat. ConversationPane.send calls that function only and issues CT-40 send_message. It does not call dispatchInvoke. No instance_id is required. A mailbox send does not grant tools. Durable history is the QMA mailbox. Each stored operator product-chat message persists product_session_ref at write (QMA _ref law; ProductSession own identity remains product_session_id). Replies inherit that field. send_message and list_mailbox admit only when the connection operator principal equals that session durable principal, when the field is present. Pre-ack identity is the wire pair (producer_id, id).",
         R, ["EXT-2467"], "COMP-QMA-DAEMON", ["ui-host", "ad-18", "chat"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-18"),
        ("DEC-0485", "UI AD-19 — v1 bootstrap owner is QMB CLI; pairing_proof is the bearer",
         "v1 requires an externally running qma-daemon. Privileged owner is COMP-QMB (qmb host start|status|stop|pair|configure|rotate-control|recover-control) over local host-control. Until that command exists, UI Start local is a setup instruction, not a spawn. Unauthenticated bootstrap is HTTP POST /pair/start and /pair/confirm plus CORS OPTIONS on named daemon HTTP routes (OPTIONS never issues a proof). Issuance: a remembered Origin never authorizes a new pairing_proof; require fresh QMB confirm of that pending or authenticated POST /pair/renew. Authenticated CT-40 uses bearer pairing_proof. HTTP sends Authorization: Bearer pairing:<proof>. WebSocket sends WHATWG subprotocols qmx.ct40.v1 and qmx.pair.<proof>. Cookies are not the v1 proof. The daemon maps Origin plus proof hash to the bootstrapped operator principal.",
         R, ["EXT-2468", "EXT-2469"], "COMP-QMB", ["ui-host", "ad-19", "bootstrap"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-19"),
        ("DEC-0486", "UI AD-20 — Mounted views carry host-minted ActionContext",
         "Each mount receives an immutable host ActionContext: psess, view_id, contribution tuple, instance_id, config_revision, grant_id, allowed_op_ids, account scope, snapshot cursor. Untrusted specs/frames supply only action name and schema-valid input. Matching GrantRecords: zero -> grant_id null (paint allowed, invoke refuses); one -> that record; two or more -> typed GRANT_AMBIGUOUS (no first-wins, no merge). dispatchInvoke intersects that context with parent AD-9.",
         R, ["EXT-2478"], "COMP-QMA-DAEMON", ["ui-host", "ad-20", "action-context"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-20"),
        ("DEC-0487", "UI AD-21 — Draft is not a runnable template",
         "Distinct ids: editor draft/revision, immutable Graph Template (qualified_id, version), pack instance, JobHandle. The daemon is the sole durable editor_draft_id issuer. First save omits that id (optional client_draft_correlation); a supplied id on first save refuses. Subsequent saves require durable id plus expected_revision. Addable publish_editor_draft authorizes the draft, checks expected_revision, revalidates immutable fp1, and writes the local authoring-pack contribution. First Run: publish_editor_draft into the local authoring pack, enable that pack (parent AD-30 compile-at-enable), grant, select that instance, then dispatchInvoke. Distributable export is later. Run refuses a mutable draft. QMA AD-22 stays one RefinementProposal type.",
         R, ["EXT-2472"], "COMP-QMA-DAEMON", ["ui-host", "ad-21", "drafts"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-21"),
        ("DEC-0488", "UI AD-22 — Artifact ingest is daemon-owned",
         "Uploads first possess bytes on the authenticated local daemon (HTTP PUT /artifacts/stage, not a JSON-RPC body). Completeness proof is daemon-recomputed fp1 plus byte count. Interrupted v1 uploads are refused; no resumable partial; no runnable incomplete ref. Remote execution requires explicit transfer_artifact only when the source daemon origin is recorded reachable TLS the destination can dial; default loopback is typed source_unreachable. Destination-authored transfer_complete is the verified completion ack. Invoke on that placement refuses until the ticket is complete. Home may attach before an instance exists. Silent local fallback is refused.",
         R, ["EXT-2472"], "COMP-QMA-DAEMON", ["ui-host", "ad-22", "artifacts"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-22"),
        ("DEC-0489", "UI AD-23 — Cancel has one host function",
         "Unique issuer apps/qmx-ui/src/lib/host/dispatchCancel. CT-40 addable command cancel_job. Fields: handle_id, logical_run_id, attempt_id, command_id, expected_state. Authority: operator of the JobHandle immutable originating_product_session_ref when that field is present (UI admit). Headless/QMB admits omit the field; UI cancel_job is then unavailable and Story 36.5 remains the abort door. queued to running does not invalidate the same command_id. Already-terminal handle records a no-op. unknown is not cancellable. Not an InvocationEnvelope invoke. Not seed stop_run.",
         R, ["EXT-2478"], "COMP-QMA-DAEMON", ["ui-host", "ad-23", "cancel"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-23"),
        ("DEC-0490", "UI AD-24 — Command identity is per producer and per session",
         "Cardinality: one producer_id per chrome tab or OS window. Two tabs of one psess: have two producer_ids. Wire command ids are unique per (producer_id, id). Product-session command_id values are unique per psess: across those tabs. Invocation idempotency_key is a third identity and applies only to dispatchInvoke.",
         R, ["EXT-2478"], "COMP-QMA-WIRE", ["ui-host", "ad-24", "producer-id"],
         "SRC-27:ARCHITECTURE-SPINE.md#ad-24"),
        ("DEC-0491", "backend AD-3 — Pairing issuance; Origin never sufficient",
         "A remembered Origin never authorizes issuance of a new pairing proof. Every new pairing_proof requires exactly one of: (1) fresh privileged local-control confirmation of that pending request (qmb host pair <code> then POST /pair/confirm); or (2) authenticated renewal presenting an existing unexpired unrevoked pairing_proof matching that Origin (POST /pair/renew with Authorization: Bearer pairing:<proof>). Origin match remains required and is never sufficient.",
         R, ["EXT-2468", "EXT-2469"], "COMP-QMA-DAEMON", ["backend-delta", "ad-3", "issuance"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-3"),
        ("DEC-0492", "backend AD-4 — Pairing record versus pairing proof; origin-revoke barrier",
         "pairing_proof is a bearer credential (RFC 6750). pairing_record_id is the nonsecret row identity. Journal projections pairing_pending and pairing_session store pairing_record_id, Origin, operator principal, proof_fp1, issued/expires/revoked, pending lineage — never the raw proof. Logs redact Authorization and qmx.pair.*. Confirm consumes once; lost confirm response requires re-pair. Renew rotates: new proof, old proof revoked, sockets on old proof closed. Expiry closes active WS. --session revokes that pairing_record_id only. --origin <origin> is an administrative barrier at journal_seq R: every pairing_session and pairing_pending for that Origin with journal_seq < R is revoked, including confirmed-unconsumed pendings and a renew that committed earlier. Origin-revoke is never discarded because a renew appended first. After R, /pair/renew and /pair/confirm of pre-R rows refuse; a new /pair/start after R is legal (re-pair). TTL is registry:pairing.session_ttl; this sitting mints no number; only qmb host configure pairing-ttl over host-control may write that row.",
         R, ["EXT-2469", "EXT-2477"], "COMP-QMA-DAEMON", ["backend-delta", "ad-4", "c2"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-4"),
        ("DEC-0493", "backend AD-5 — Unauthenticated bind is a named carve-out (AM-01)",
         "Named amendment to QMA AD-5, QMA AD-15, QMA AD-24, and Epic 41 Story 41.4: unauthenticated HTTP is allowed only for POST /pair/start, POST /pair/confirm, and CORS OPTIONS on the AD-15 HTTP routes that declare CORS. OPTIONS never returns a pairing proof, never upgrades to WebSocket, and never returns artifact bytes. POST /pair/renew is authenticated. Every other HTTP method and every WebSocket still authenticates before protocol bytes. Browser-paired AuthenticatedWireSession carries principal_class=operator and pairing_record_id; it does not populate credential_ref. Machine/worker clients still present credential_ref. Cookies are refused. Authenticated ACAO is the exact paired Origin; credentials omit; never *.",
         R, ["EXT-2472"], "COMP-QMA-WIRE", ["backend-delta", "ad-5", "am-01"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-5"),
        ("DEC-0494", "backend AD-6 — QMB owns process lifetime",
         "Privileged verbs are qmb host start|status|stop|pair|configure|rotate-control|recover-control (COMP-QMB add) over local host-control. start sets QMA_DAEMON_ROOT, spawns python -m qma.daemon if the lock is free, and on an empty root (no local_operator row) runs first-operator bootstrap. A root that already has local_operator but is missing host_control is not empty: start may spawn if the lock is free and does not remint a principal. stop stops the local daemon: current host_control or, if that file is missing/unreadable, the OS owner of the root (narrow exception so a lost token can still reach recover). QMB never writes daemon sqlite. recover-control runs a one-shot daemon recover entry that acquires .daemon_writer, appends the journal, releases the lock, and exits; it does not bind port 8765.",
         R, ["EXT-2470"], "COMP-QMB", ["backend-delta", "ad-6", "host"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-6"),
        ("DEC-0495", "backend AD-7 — Mailbox delivery stays Epic 46 with additive product_session_ref",
         "send_message remains the seed command. Durable record is the CT-48 mailbox Envelope / journal message.* (Story 46.4 / FEAT-0045). Named amendment to QMA AD-20 / Story 46.4: operator product-chat Envelopes persist additive product_session_ref (pointer at the product-session projection; excluded from Envelope fp1). Quant/machine rows with no product conversation omit the field. When product_session_ref is present, send_message and list_mailbox admit only if the connection operator principal equals that session durable principal. Addable query list_mailbox is an authenticated HTTP GET snapshot. Collision: same pair plus same hash returns the prior result; same pair plus different hash refuses for journal lifetime (AM-12, mailbox sends only).",
         R, ["EXT-2471"], "COMP-QMA-DAEMON", ["backend-delta", "ad-7", "mailbox"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-7"),
        ("DEC-0496", "backend AD-8 — Cancel binds originating_product_session_ref at admit",
         "Addable command cancel_job. handle_id is job_id. Named amendment to QMA AD-17 / parent AD-26 / Story 57.3 handle record (states unchanged): UI-originated admits store immutable originating_product_session_ref. Headless/QMB admits omit the field. UI cancel_job is unavailable when the field is absent; Story 36.5 remains the headless abort door. queued to running does not change the command_id hash. Nested children store the session that started that child, or omit the field if that admit was headless. Terminal is a recorded no-op. unknown is not cancellable.",
         R, ["EXT-2472"], "COMP-QMA-DAEMON", ["backend-delta", "ad-8", "cancel"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-8"),
        ("DEC-0497", "backend AD-9 — Artifact ingest is authenticated PUT then explicit transfer",
         "Initial possession is HTTP PUT /artifacts/stage on the authenticated daemon origin. Missing registry:artifact.stage_max_bytes refuses the PUT; this sitting mints no number. Completeness is daemon-recomputed fp1 plus byte count. Interrupted v1 PUT is refused and deleted. transfer_artifact issues artifact_transfer_ticket only when the source daemon origin is recorded reachable TLS that the destination environment network allowlist can dial. Default loopback is typed source_unreachable. Ticket binds dest machine credential_ref audience. Only that audience may GET /artifacts/<fp1> with X-QMX-Transfer-Ticket. Dest authors transfer_complete. Invoke on that placement refuses until complete. Daemon never dials in.",
         R, ["EXT-2472", "EXT-2477"], "COMP-QMA-DAEMON", ["backend-delta", "ad-9", "artifacts"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-9"),
        ("DEC-0498", "backend AD-10 — PackUiRequest is ingested request, not a grant",
         "Host ingests at most one qmx.ui.pack_ui_request.v1 document at enable. It is a versioned request DTO, not a contribution point. Optional PluginManifest.copilot_profile stays the Epic 60 sibling field. Read-back is addable query get_pack_ui_request keyed by enabled instance_id plus availability_revision. Nav items bind view_ids. Zero matching GrantRecords: paint, invoke refuses. One: that record. Two or more: GRANT_AMBIGUOUS. ActionContext remains host-minted and immutable.",
         R, ["EXT-2479"], "COMP-QMA-DAEMON", ["backend-delta", "ad-10", "pack-ui"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-10"),
        ("DEC-0499", "backend AD-11 — Draft head is not AD-22 staging",
         "Saved drafts are artifact-store bytes plus journal projection editor_draft_head. editor_revision is that content fp1. Daemon is the sole durable editor_draft_id issuer. First save_editor_draft omits editor_draft_id; optional client_draft_correlation makes lost-ack retry of the same fp1 return the same durable id. Reload-head is addable query get_editor_draft_head. publish_editor_draft checks ownership, expected_revision, reruns validation against immutable fp1, and writes the local authoring-pack contribution. Parent AD-30 enable remains compile identity. QMA AD-22 stays one RefinementProposal type (AM-07).",
         R, ["EXT-2472"], "COMP-QMA-DAEMON", ["backend-delta", "ad-11", "drafts"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-11"),
        ("DEC-0500", "backend AD-13 — Compatibility is additive and honest",
         "Same-major wire changes are additive. initialize advertises capabilities including pairing, list_mailbox, cancel_job, caller_kind, stage_artifact (meaning authenticated PUT /artifacts/stage exists), transfer_artifact, transfer_complete, pack_ui_request, get_pack_ui_request, save_editor_draft, get_editor_draft_head, publish_editor_draft. Missing capability yields typed mismatch; shell stays usable for surfaces that do not need it. Older clients ignore unknown fields. Client bits are not journals.",
         R, ["EXT-2474"], "COMP-QMA-WIRE", ["backend-delta", "ad-13", "compat"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-13"),
        ("DEC-0501", "backend AD-14 — Reload, clone, and cold start are different recoveries",
         "Browser home for pairing_proof / pairing_record_id / pending chat triple is memory plus sessionStorage only. localStorage, cookies, IndexedDB, and any other durable web store are forbidden for the proof. Same-tab reload may restore those values and reconnect with the same proof. Auxiliary/cloned tab copied storage is existing proof; the clone reconnects with a new live producer_id if the old is live. /pair/renew is not the clone path; it is an explicit rotate that closes sockets on the old proof. Cold start / closed tab: empty storage; /pair/renew impossible; new pair requires QMB confirm; selected psess: restores via list_mailbox; never auto-resend. Lost /pair/confirm response: proof unrecoverable; start a new pending.",
         R, ["EXT-2468"], "COMP-QMA-WIRE", ["backend-delta", "ad-14", "recovery"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-14"),
        ("DEC-0502", "backend AD-15 — HTTP PUT is a byte channel on the daemon origin",
         "Port 8765 carries: unauthenticated pairing POST plus CORS OPTIONS; authenticated HTTP GET snapshots (list_mailbox, get_pack_ui_request, get_editor_draft_head); authenticated HTTP PUT /artifacts/stage; authenticated HTTP GET /artifacts/<fp1> for machine transfer pull; authenticated JSON-RPC WebSocket; authenticated POST /pair/renew. Local host-control is a separate token-gated loopback channel under QMA_DAEMON_ROOT, not a second unauthenticated 8765 bind. PUT and artifact GET are byte channels, not invoke, not a BFF. SPA origin is not daemon origin.",
         R, ["EXT-2472"], "COMP-QMA-WIRE", ["backend-delta", "ad-15", "http"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-15"),
        ("DEC-0503", "backend AD-17 — First operator is local host-control; lost-token recovery",
         "Trust root is the OS user who owns QMA_DAEMON_ROOT plus a daemon-minted host_control token stored under that root with owner-only ACL. The channel is loopback-only and is not the CT-40 listener (named amendment of QMA AD-5 single inbound port). qmb host start on an empty root (no local_operator row) mints the first operator principal into journal projection local_operator and mints host_control; /pair/start and /pair/confirm refuse until qmb host configure pairing-ttl has written the registry row. A root that already has local_operator is never empty bootstrap, even if host_control is missing. Rotation while token is held: qmb host rotate-control. Lost-token recovery: daemon must be stopped; OS owner runs qmb host recover-control without presenting the lost token; one-shot daemon recover entry writes the journal; local_operator and journals preserved; does not remint a second principal; does not delete the data root. Live daemon with missing file: OS owner may stop without the token (DEC-0494), then recover. Other OS user refuses. Readable token file still present refuses recover-control (use rotate-control). Broker allowlist is not widened.",
         R, ["EXT-2470", "EXT-2464"], "COMP-QMB", ["backend-delta", "ad-17", "c1"],
         "SRC-28:ARCHITECTURE-SPINE.md#ad-17"),
        ("DEC-0504", "UI host plus backend-delta spines adopted in full (reuse; no sixth package)",
         "The 2026-09-23/24 QMX UI host spine (architecture-QMX-UI-2026-09-23, local UI AD-1..AD-24) and the 2026-09-24 backend-delta spine (architecture-QMX-UI-BACKEND-2026-09-24, local backend AD-1..AD-17) are adopted as DEC-0469 through DEC-0503. Parent architecture-QMX-2026-09-18 AD-1..AD-31 (DEC-0414..DEC-0444, ADR-0024) and kit architecture-QMX-2026-09-23 AD-1..AD-9 (DEC-0452..DEC-0468, ADR-0025) bind read-only. Local AD ids do not renumber parents. Named inherited-contract amendments are AM-01..AM-17 recorded in those DECs and summarized by DEC-0506. Preflight reuse with no new COMP and no new CT is DEC-0505. Wiring honesty at 34c148be is DEC-0507. Dead-list honors are DEC-0508. GAP catalog restamp is DEC-0509. Cheap-veto A10-A14 ride DEC-0510. ADR-0026 and SCN-0028..SCN-0035 are docs authority only. Implementation authorization remains factory-pipeline-only. Do not rewrite the 2026-09-16 QML fold, the 2026-09-19 Workflows fold, or the 2026-09-23 pack-and-grant fold.",
         R, ["EXT-2464"], "COMP-QMA-CORE", ["ui-host", "backend-delta", "umbrella"],
         "SRC-29"),
        ("DEC-0505", "UI plus backend-delta preflight — reuse existing applications; no new COMP; no new CT",
         "Preflight verdict: reuse existing applications. new COMP: none. new CT: none. No new depends_on edge and no existing component's authority shrinks. The Svelte host is a client of COMP-QMA-WIRE and is not COMP-UI. Work owners: chrome = UI lens docs over COMP-QMA-WIRE DTOs; qmb host / host_control / recover-control = COMP-QMB plus COMP-QMA-DAEMON; pairing = COMP-QMA-DAEMON plus COMP-QMA-WIRE plus COMP-QMB; mailbox field = COMP-QMA-DAEMON plus COMP-QMA-WIRE (delivery remains FEAT-0045); cancel field = COMP-QMA-DAEMON plus COMP-QMA-WIRE; artifacts/transfer = COMP-QMA-DAEMON plus COMP-QMA-WIRE; drafts/publish = COMP-QMA-DAEMON plus COMP-QMA-WIRE; PackUiRequest = COMP-QMA-DAEMON plus COMP-QMA-WIRE beside Epic 60. Candidates refused: COMP-UI / sixth COMP; new CT-*; third ProductSessionProfile; cookie login; ui_view contribution point; AD-22 as graph draft store; json-render/MCP as identity; QMB sqlite writer; reminting local_operator on recover; Origin-only issuance.",
         R, ["EXT-2473"], "COMP-QMA-CORE", ["ui-host", "preflight", "reuse"],
         "SRC-29"),
        ("DEC-0506", "Named inherited-contract amendments AM-01 through AM-17",
         "Conflicts with inherited QMA / parent / kit / planned-epic contracts are named AM-01 through AM-17 in architecture-QMX-UI-BACKEND-2026-09-24/PARENT-AMENDMENT-MAP.md and bound by DEC-0491..DEC-0503. Do not silent-override. Do not whole-supersede DEC-0304, DEC-0319, DEC-0323, DEC-0421, DEC-0437, DEC-0463, or DEC-0464. Epic 60 PluginManifest.copilot_profile is not moved into PackUiRequest. Envelope instance_id remains required on invoke. QMA _ref exception list is unchanged; new pointers use _ref (product_session_ref, originating_product_session_ref). QMA AD-22 stays one RefinementProposal type.",
         R, ["EXT-2472"], "COMP-QMA-CORE", ["backend-delta", "amendments"],
         "SRC-28:PARENT-AMENDMENT-MAP.md"),
        ("DEC-0507", "Wiring honesty @ 34c148be — inherit DEC-0286 and DEC-0465; UI/backend adds absent",
         "Inherit DEC-0286 and DEC-0465. On integration@34c148be this session reconfirmed CONNECT: InvocationEnvelope, GrantRecord, product_session / ProductSessionProfile, view:* DTOs, JobHandle types plus in-memory store, mailbox Envelope types, later_commands. AMEND relative to this sitting: Envelope has no product_session_ref; JobHandle has no originating_product_session_ref. ABSENT as product surface: live CT-40 server (DaemonProcess discards TCP bytes); /pair/*; qmb host; pairing table; list_mailbox; cancel_job; PUT /artifacts/stage; transfer_artifact / transfer_complete; save_editor_draft / publish_editor_draft / get_editor_draft_head; get_pack_ui_request; host_control / recover-control; PluginManifest.copilot_profile; first-party Svelte/Tauri frontend. Do not claim those absences are open design gaps. Do not claim envelope/grant/product_session types are absent. Implementation authorization still arrives only through the factory pipeline.",
         R, ["EXT-2474"], "COMP-QMA-WIRE", ["honesty", "34c148be"],
         "SRC-28:START-HERE.md"),
        ("DEC-0508", "Dead-list honors — no COMP-UI, no cookie login, no ui_view, no AD-22 draft store",
         "This increment honors existing deaths and does not revive them: DEC-0084 / DEC-0085 / DEC-0086 stay dead; DEC-0361 marketplace, DEC-0362 solver, and DEC-0366 HMR stay dead; DEC-0408..DEC-0413 mill deaths stay dead; DEC-0466 kit deaths stay dead. COMP-UI / sixth COMP stay un-minted. Cookie session and localStorage/IndexedDB pairing proof stay refused. ui_view contribution point stays un-minted. QMA AD-22 stays one RefinementProposal type. Study 01/02/03 as baseline stay rejected. LSE ML Studio as layout stays refused. Qt host stays refused. JSON Render and MCP Apps as identity, persistence, runtime, or authority stay dead. Origin-only issuance stays refused.",
         R, ["EXT-2475"], "COMP-QMA-CORE", ["dead-list", "honors"],
         "SRC-29"),
        ("DEC-0509", "UI catalog correction — GAP-0081 and GAP-0100 are answered sitting law",
         "A catalog gap is an unanswered design question. architecture-QMX-UI-2026-09-23 designed chrome and observation surfaces. GAP-0081 and GAP-0100 are answered sitting law of this UI sitting. Delivery is FEAT-0064 through FEAT-0071. They remain out-of-scope as pack-and-grant kit holes (DEC-0468 still true for the kit). Wiring honesty at 34c148be (DEC-0507) records connect versus absent as product surface; that honesty is not a gap. qma-ui-contract types beyond a stub remain GAP-0114. UX-10 trading ticket chrome remains GAP-0113. CodeMirror versus Monaco remains GAP-0111. Tauri installer remains GAP-0112. Pairing TTL and artifact stage_max_bytes numbers remain GAP-0109 and GAP-0110. Do not re-run architecture for sitting-answered rows. Do not write production code in the documentation-factory session.",
         R, ["EXT-2476"], "COMP-QMA-CORE", ["gaps", "catalog"],
         "SRC-29"),
        ("DEC-0510", "UI plus backend-delta cheap-veto register A10-A14",
         "Cheap-veto assumptions for sitting machinery, each individually overturnable without unwinding another call: (A10) registry:pairing.session_ttl exists; this sitting mints no duration — proceed. (A11) registry:artifact.stage_max_bytes exists; this sitting mints no number — proceed. (A12) shadcn-svelte Rhea compact is the working visual seed, not a brand freeze — proceed. (A13) Node.js >=22.12.0 <23.0.0 and pnpm lockfile at an unexecuted scaffold gate — proceed. (A14) product data root Windows %LOCALAPPDATA%\\QMX\\qma-daemon and the POSIX rows in HOST-LIFECYCLE.md — proceed. Not vetoable here: no sixth COMP; no new CT; Origin-never-sufficient issuance; no cookies/localStorage proof; no COMP-UI; Epic 60 copilot_profile stays a sibling field; recover-control does not remint a principal or wipe journals; QMB never writes daemon sqlite.",
         R, ["EXT-2477"], "COMP-QMA-CORE", ["cheap-veto"],
         "SRC-29"),
    ]
    return "\n" + "".join(dec_block(*r) for r in rows)


def patch_gap_0081(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "2026-09-25 UI sitting: chrome designed" in text:
        print("skip gaps.yaml: GAP-0081 2026-09-25 already patched")
        return
    old = """    status: out-of-scope
    answer: \"Out of the pack-and-grant kit. The user interface is not designed. Screens, chrome, Rust UI SDK, and qma-ui-contract beyond a stub are a later UI sitting. Pack-and-grant contracts bind without chrome. Optional in-app copilot panel is a contract (a pack may omit copilot_profile) and is not this row. Catalog id stays for history (DEC-0468).\"
    answered_by: operator (2026-09-23 gap correction)
    note: \"AD-5 wire. The qma-ui-contract package ships as a stub only in v1. The wire contract (AD-5) and the variables registry (AD-26) bind now. 2026-09-19 Workflows: UI-host contracts (AD-17 / DEC-0430 DTOs) fold now. 2026-09-23 pack-and-grant: operator removed this as a live kit hole (DEC-0468). Status out-of-scope, not deferred.\"
    date: 2026-09-23"""
    new = """    status: answered
    answer: \"Chrome is the 2026-09-23/24 UI sitting: differentiated-shell Svelte client over pack-and-grant host (DEC-0469..DEC-0504). Destinations Home / Copilot / Library / Authoring. No COMP-UI. qma-ui-contract types beyond a stub remain GAP-0114. Remains out-of-scope as a pack-and-grant kit hole (DEC-0468). Delivery FEAT-0064..FEAT-0071 (DEC-0509).\"
    answered_by: operator (2026-09-25 Documentation Factory after Codex PASS)
    note: \"AD-5 wire. The qma-ui-contract package ships as a stub only in v1. 2026-09-19 Workflows: UI-host contracts (AD-17 / DEC-0430 DTOs) fold now. 2026-09-23 pack-and-grant: out-of-scope as a kit hole (DEC-0468). 2026-09-25 UI sitting: chrome designed (DEC-0509). Status answered, not deferred.\"
    date: 2026-09-25"""
    replace_once(path, old, new, "2026-09-25 UI sitting: chrome designed")


def patch_gap_0100(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "2026-09-25 UI sitting: observation surfaces designed" in text:
        print("skip gaps.yaml: GAP-0100 2026-09-25 already patched")
        return
    old = """    status: out-of-scope
    answer: \"Out of the pack-and-grant kit and out of the Workflows epic set. A cutover readiness dashboard is user-interface work. AD-25 fencing remains the transition machine. Diagnosis queries bind now (DEC-0456). Catalog id stays for history (DEC-0468).\"
    answered_by: operator (2026-09-19 UI later; 2026-09-23 removed as a live kit hole)
    note: \"Operator 2026-09-19: UI, later. Operator 2026-09-23: no longer a catalog hole hanging over the kit (DEC-0468). Status out-of-scope.\"
    date: 2026-09-23"""
    new = """    status: answered
    answer: \"Observation surfaces are Home attention plus kit listing/health/diagnosis queries consumed as chrome (UI AD-14 / DEC-0480). Not a fourth observability product. AD-25 fencing remains the transition machine. Trading ticket chrome is GAP-0113. Remains out-of-scope as a kit hole (DEC-0468). Delivery FEAT-0064 (DEC-0509).\"
    answered_by: operator (2026-09-25 Documentation Factory after Codex PASS)
    note: \"Operator 2026-09-19: UI, later. Operator 2026-09-23: no longer a catalog hole hanging over the kit (DEC-0468). 2026-09-25 UI sitting: observation surfaces designed (DEC-0509). Status answered.\"
    date: 2026-09-25"""
    replace_once(path, old, new, "2026-09-25 UI sitting: observation surfaces designed")


GAPS_NEW = "\n" + "".join([
    gap_new("GAP-0109",
            "What duration is registry:pairing.session_ttl?",
            ["COMP-QMA-DAEMON", "COMP-QMB"],
            "Leave as a host-registered registry row. This sitting mints no number (DEC-0492, DEC-0510 A10).",
            "deferred", None,
            "Sitting law: the row exists and missing TTL refuses /pair/start and /pair/confirm issue. The number is operator-supplied later. Non-blocking."),
    gap_new("GAP-0110",
            "What is registry:artifact.stage_max_bytes?",
            ["COMP-QMA-DAEMON"],
            "Leave as a host-registered registry row. Missing row refuses PUT. This sitting mints no number (DEC-0497, DEC-0510 A11).",
            "deferred", None,
            "Non-blocking. FEAT-0068 must not invent a cap."),
    gap_new("GAP-0111",
            "Does authoring code use CodeMirror 6 or Monaco?",
            ["COMP-QMA-WIRE"],
            "Decide after an isolated fidelity spike. Do not pin in this fold.",
            "deferred", None,
            "UI AD-9 family is graph/code/detail. Editor engine unpinned. Non-blocking."),
    gap_new("GAP-0112",
            "When does the optional Tauri 2 desktop shell ship, and who supervises the Python sidecar?",
            ["COMP-QMB"],
            "v1 is browser plus host-supervised daemon (DEC-0478). Tauri later. Official Tauri 2 has no sidecar health/restart supervisor.",
            "deferred", None,
            "Non-blocking. Do not make Tauri v1-required."),
    gap_new("GAP-0113",
            "What is the UX-10 trading/risk ticket chrome?",
            ["COMP-QMN", "COMP-QMA-WIRE"],
            "Defer to a trading-app sitting. Book/BMS observation may appear on Home attention. Paper-then-live plus L17 remain for trading seats only.",
            "deferred", None,
            "Constraint-law only in this sitting. Non-blocking."),
    gap_new("GAP-0114",
            "When does qma-ui-contract ship types beyond STUB.md?",
            ["COMP-QMA-WIRE"],
            "Keep the stub until a later types increment. This sitting does not mint COMP-UI or a second contract package.",
            "deferred", None,
            "Wire contract CT-40 binds now. Stub remains honest at 34c148be. Non-blocking."),
])


FEATS = "\n" + "".join([
    feat_block(
        "FEAT-0064",
        "Differentiated-shell Svelte host (rail, stack seed, unique issuers, UI lens)",
        """In: SvelteKit static SPA host with platform rail Home / Copilot / Library / Authoring (DEC-0469, DEC-0470); unique issuers dispatchInvoke / dispatchChat / dispatchCancel (DEC-0474, DEC-0484, DEC-0489); native-first presentation lanes (DEC-0472); UI lens design-system plus screen specs; charts provenance (DEC-0483); sibling integration stream (DEC-0482). Out: COMP-UI; sixth COMP; Tauri as v1-required (GAP-0112); trading ticket chrome (GAP-0113); claiming a frontend exists at 34c148be (DEC-0507). Done means chrome contracts are specified; implementation authorization still arrives only through the factory pipeline.""",
        ["DEC-0469", "DEC-0470", "DEC-0471", "DEC-0472", "DEC-0473", "DEC-0474", "DEC-0475", "DEC-0476", "DEC-0477", "DEC-0478", "DEC-0479", "DEC-0480", "DEC-0482", "DEC-0483", "DEC-0504", "DEC-0505"],
        ["COMP-QMA-WIRE"],
        [("FEAT-0058", "shell consumes pack-and-grant host SDK fields FEAT-0058 lands (DEC-0452, DEC-0463, DEC-0464)")],
        "Feeds GAP-0081 / GAP-0100 answered delivery. Implementation authorization factory-pipeline-only.",
    ),
    feat_block(
        "FEAT-0065",
        "QMB host lifecycle plus first operator plus recover-control",
        """In: qmb host start|status|stop|configure|rotate-control|recover-control (DEC-0494, DEC-0503); local_operator journal projection; host_control token; product QMA_DAEMON_ROOT (DEC-0510 A14); C1 lost-token recovery without presenting the lost token; narrow OS-owner stop-when-file-missing exception. Out: browser spawn of Python; QMB writing daemon sqlite; reminting principal on recover; wiping journals. Done means host verbs are specified; implementation authorization still arrives only through the factory pipeline.""",
        ["DEC-0494", "DEC-0503", "DEC-0506", "DEC-0507"],
        ["COMP-QMB", "COMP-QMA-DAEMON"],
        [("FEAT-0042", "host-control and local_operator are journal projections on the daemon substrate FEAT-0042 lands (DEC-0334)")],
        "Implementation authorization factory-pipeline-only.",
    ),
    feat_block(
        "FEAT-0066",
        "Pairing admission (proof versus record, Origin-never-sufficient, CORS, renew, origin-revoke)",
        """In: pairing_proof bearer plus pairing_record_id journal identity (DEC-0492); issuance Origin-never-sufficient (DEC-0491, DEC-0485); unauthenticated carve-out AM-01 (DEC-0493); authenticated /pair/renew; origin-revoke barrier C2; sessionStorage-only client home (DEC-0501); CORS exact origin. Out: cookies; localStorage proof; Origin-only auto-approve; minting TTL number (GAP-0109). Done means pairing contracts are specified; implementation authorization still arrives only through the factory pipeline.""",
        ["DEC-0485", "DEC-0491", "DEC-0492", "DEC-0493", "DEC-0501", "DEC-0506"],
        ["COMP-QMA-DAEMON", "COMP-QMA-WIRE", "COMP-QMB"],
        [
            ("FEAT-0065", "pairing issue requires first-operator host-control and TTL configure FEAT-0065 lands (DEC-0503)"),
            ("FEAT-0041", "pairing HTTP and WS subprotocol sit on the CT-40 listener FEAT-0041 lands (DEC-0304, DEC-0493)"),
        ],
        "Implementation authorization factory-pipeline-only.",
    ),
    feat_block(
        "FEAT-0067",
        "Mailbox product_session_ref plus list_mailbox plus dispatchChat",
        """In: additive Envelope product_session_ref excluded from fp1 (DEC-0495, DEC-0484); list_mailbox addable query; dispatchChat unique issuer; principal equality when the field is present; journal-lifetime pair+hash collision (AM-12); lost-ack lookup by (producer_id, id). Out: routing Send through InvocationEnvelope; replacing Story 46.4; a parallel conversation store. Done means mailbox session binding is specified; implementation authorization still arrives only through the factory pipeline.""",
        ["DEC-0484", "DEC-0495", "DEC-0506"],
        ["COMP-QMA-DAEMON", "COMP-QMA-WIRE"],
        [
            ("FEAT-0045", "durable mailbox Envelope and journal message.* delivery FEAT-0045 lands remain the owner (DEC-0319, Story 46.4)"),
            ("FEAT-0041", "list_mailbox is an addable CT-40 query on the wire vocabulary FEAT-0041 lands (DEC-0304)"),
            ("FEAT-0066", "send_message and list_mailbox require a paired operator principal FEAT-0066 lands (DEC-0493)"),
        ],
        "Amends Story 46.4 field list; does not replace it. Implementation authorization factory-pipeline-only.",
    ),
    feat_block(
        "FEAT-0068",
        "Artifact PUT plus reachable transfer plus transfer_complete",
        """In: authenticated HTTP PUT /artifacts/stage (DEC-0488, DEC-0497, DEC-0502); refuse interrupted v1; transfer_artifact ticket on recorded reachable TLS; dest-authored transfer_complete; machine GET /artifacts/<fp1> with ticket header. Out: JSON-RPC byte bodies; silent local fallback; minting stage_max_bytes (GAP-0110); daemon dial-in. Done means ingest and transfer are specified; implementation authorization still arrives only through the factory pipeline.""",
        ["DEC-0488", "DEC-0497", "DEC-0502", "DEC-0506"],
        ["COMP-QMA-DAEMON", "COMP-QMA-WIRE"],
        [
            ("FEAT-0042", "artifact store and before_artifact_register live on the daemon substrate FEAT-0042 lands"),
            ("FEAT-0066", "PUT and transfer require authenticated pairing or machine credential FEAT-0066 lands (DEC-0493)"),
        ],
        "Implementation authorization factory-pipeline-only.",
    ),
    feat_block(
        "FEAT-0069",
        "Editor drafts plus publish_editor_draft plus local authoring-pack first Run",
        """In: daemon-issued editor_draft_id; editor_draft_head CAS expected_revision; get_editor_draft_head; publish_editor_draft into local authoring pack then parent AD-30 enable (DEC-0487, DEC-0499). Out: using AD-22 RefinementProposal as the graph editor store; draft Run; distributable export as first enable. Done means draft/publish/first-Run are specified; implementation authorization still arrives only through the factory pipeline.""",
        ["DEC-0487", "DEC-0499", "DEC-0506"],
        ["COMP-QMA-DAEMON", "COMP-QMA-WIRE"],
        [
            ("FEAT-0058", "first Run enable rides pack-and-grant host SDK and parent AD-30 FEAT-0058 lands (DEC-0452)"),
            ("FEAT-0068", "draft bytes use the AD-9 PUT channel FEAT-0068 lands (DEC-0497)"),
        ],
        "Implementation authorization factory-pipeline-only.",
    ),
    feat_block(
        "FEAT-0070",
        "PackUiRequest ingest plus ActionContext plus get_pack_ui_request",
        """In: ingest qmx.ui.pack_ui_request.v1 at enable; get_pack_ui_request; host-minted ActionContext; GRANT_AMBIGUOUS; nav view_ids (DEC-0481, DEC-0486, DEC-0498). Out: nesting copilot_profile inside PackUiRequest; ui_view contribution point; duplicating Epic 60.1. Done means pack UI request contracts are specified; implementation authorization still arrives only through the factory pipeline.""",
        ["DEC-0481", "DEC-0486", "DEC-0498", "DEC-0506"],
        ["COMP-QMA-DAEMON", "COMP-QMA-WIRE"],
        [("FEAT-0058", "PackUiRequest is additional beside optional copilot_profile FEAT-0058 / Epic 60.1 lands (DEC-0452, DEC-0454)")],
        "Do not hold Epic 60.1. Implementation authorization factory-pipeline-only.",
    ),
    feat_block(
        "FEAT-0071",
        "cancel_job plus originating_product_session_ref plus dispatchCancel",
        """In: addable cancel_job; optional originating_product_session_ref at UI admit; dispatchCancel unique issuer; queued-to-running same command_id; terminal recorded no-op (DEC-0489, DEC-0490, DEC-0496). Out: mapping cancel to stop_run; observer cancel; changing JobHandle states. Done means cancel authority is specified; implementation authorization still arrives only through the factory pipeline.""",
        ["DEC-0489", "DEC-0490", "DEC-0496", "DEC-0506"],
        ["COMP-QMA-DAEMON", "COMP-QMA-WIRE"],
        [
            ("FEAT-0055", "cancel rides durable JobHandle parent vocabulary FEAT-0055 lands (DEC-0439)"),
            ("FEAT-0067", "UI cancel authority uses the same operator principal as the originating product session FEAT-0067 lands (DEC-0495)"),
        ],
        "Amends Epic 57 handle record additively; states unchanged. Implementation authorization factory-pipeline-only.",
    ),
])


REGISTRY = """
  - name: pairing.session_ttl
    symbol: null
    value: null
    gap: GAP-0109
    formula: null
    units: duration
    type: duration
    component: COMP-QMA-DAEMON
    decision: DEC-0492
    configurable: true
    notes: "Pairing proof lifetime. Only qmb host configure pairing-ttl over host-control may create or change this row; CT-40 variable.set of this key refuses (DEC-0492, DEC-0503, DEC-0510 A10). Missing row refuses /pair/start and /pair/confirm issue. This sitting mints no number."

  - name: artifact.stage_max_bytes
    symbol: null
    value: null
    gap: GAP-0110
    formula: null
    units: bytes
    type: count
    component: COMP-QMA-DAEMON
    decision: DEC-0497
    configurable: true
    notes: "Maximum Content-Length for authenticated PUT /artifacts/stage (DEC-0497, DEC-0510 A11). Missing row refuses the PUT. This sitting mints no number. Set by operator-principal variable.set (AD-24)."
"""


def main() -> None:
    append_if_missing(ROOT / "_docwork/manifest.yaml", "id: SRC-27", MANIFEST)
    append_if_missing(ROOT / "_docwork/extractions.yaml", "id: EXT-2464", build_extractions())
    append_if_missing(ROOT / "_docwork/ledger.yaml", "id: DEC-0469", build_ledger())
    patch_gap_0081(ROOT / "_docwork/gaps.yaml")
    patch_gap_0100(ROOT / "_docwork/gaps.yaml")
    append_if_missing(ROOT / "_docwork/gaps.yaml", "id: GAP-0109", GAPS_NEW)
    append_if_missing(ROOT / "_docwork/feature_inventory.yaml", "id: FEAT-0064", FEATS)
    append_if_missing(ROOT / "docs/registry/variables.yaml", "name: pairing.session_ttl", REGISTRY)
    print("done")


if __name__ == "__main__":
    main()
