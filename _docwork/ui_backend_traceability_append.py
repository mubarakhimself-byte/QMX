"""Append UI-host + backend-delta locator rows to docs/knowledge/traceability.md."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs" / "knowledge" / "traceability.md"
text = PATH.read_text(encoding="utf-8")

text = text.replace("verified: '2026-09-23'", "verified: '2026-09-25'", 1)

old_intro = (
    "and `DEC-0452`–`DEC-0467`), gap (`GAP-0001`–`GAP-0064` and `GAP-0070`–`GAP-0091` "
    "and `GAP-0092`–`GAP-0100` and `GAP-0101`–`GAP-0108`), and inventory feature "
    "(`FEAT-0001`–`FEAT-0039`, `FEAT-0040`–`FEAT-0046`, `FEAT-0047`–`FEAT-0050`, "
    "and `FEAT-0051`–`FEAT-0057`, and `FEAT-0058`–`FEAT-0063`), including ADR-0022"
)
new_intro = (
    "and `DEC-0452`–`DEC-0468`, and `DEC-0469`–`DEC-0510`), gap (`GAP-0001`–`GAP-0064` "
    "and `GAP-0070`–`GAP-0091` and `GAP-0092`–`GAP-0100` and `GAP-0101`–`GAP-0108` "
    "and `GAP-0109`–`GAP-0114`), and inventory feature (`FEAT-0001`–`FEAT-0039`, "
    "`FEAT-0040`–`FEAT-0046`, `FEAT-0047`–`FEAT-0050`, and `FEAT-0051`–`FEAT-0057`, "
    "and `FEAT-0058`–`FEAT-0063`, and `FEAT-0064`–`FEAT-0071`), including ADR-0022"
)
if old_intro not in text:
    raise SystemExit("intro range string not found")
text = text.replace(old_intro, new_intro, 1)
text = text.replace(
    "and ADR-0025 / the 2026-09-23 pack-and-grant kit.",
    "and ADR-0025 / the 2026-09-23 pack-and-grant kit, and ADR-0026 / the 2026-09-25 UI host plus backend-delta.",
    1,
)

text = text.replace(
    "| DEC-0430 | `ratified` | [ADR-0024](../decisions/ADR-0024-workflows-construction-kit.md) (AD-17 UI host contracts; chrome GAP-0081) |",
    "| DEC-0430 | `ratified` | [ADR-0024](../decisions/ADR-0024-workflows-construction-kit.md) (AD-17 UI host contracts; chrome answered by ADR-0026 / DEC-0509; still no `ui_view`) |",
    1,
)

text = text.replace(
    "| GAP-0081 | `deferred` | `false` | [Gap report](../gap-report.md); [qma-wire](../components/qma-wire.md). UI presentation, UI SDK and `qma-ui-contract` beyond a stub; the wire contract and variables registry bind now (DEC-0304, DEC-0333). |",
    "| GAP-0081 | `answered` | `false` | [Gap report](../gap-report.md); [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [qma-wire](../components/qma-wire.md). Chrome is the Svelte host (DEC-0509). `qma-ui-contract` types remain GAP-0114. Still out-of-scope as a kit hole (DEC-0468). |",
    1,
)

text = text.replace(
    "GAP-0101..GAP-0108 stay deferred. Inspect `integration@34c148b` (DEC-0465).",
    "GAP-0101..GAP-0108 are answered sitting law (DEC-0468). Inspect `integration@34c148b` (DEC-0465).",
    1,
)

marker = "| FEAT-0057 | 24 | [COMP-QMA-DAEMON](../components/qma-daemon.md), [COMP-QMA-WIRE](../components/qma-wire.md) | `planned` | FEAT-0055, FEAT-0056. Safety fixtures (≥2 of stream cancel+cutover; outbox restart; UNKNOWN blocks handover; stale predecessor refused; grant refuses other instance) (DEC-0438, DEC-0439, DEC-0441, DEC-0437, DEC-0443). |"
if marker not in text:
    raise SystemExit("FEAT-0057 marker not found")
if "### UI host plus backend-delta decisions — DEC-0469 through DEC-0510" in text:
    print("skip: UI locator already appended")
else:
    append = """

### UI host plus backend-delta decisions — DEC-0469 through DEC-0510

These decisions absorb the 2026-09-23/24 UI host spine and the 2026-09-24 backend-delta spine as ADR-0026. Preflight is reuse — no COMP-UI, no new CT (DEC-0505). Inspect `integration@34c148be` (DEC-0507). Implementation authorization remains factory-pipeline-only.

| Decision | Status | Primary document and section |
|---|---|---|
| DEC-0468 | `ratified` | [ADR-0025](../decisions/ADR-0025-pack-and-grant-kit.md) (catalog correction; GAP-0101..0108 answered kit law) |
| DEC-0469 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [stack](../architecture/stack.md) (UI AD-2 host stack seed) |
| DEC-0470 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [SCN-0034](../scenarios/SCN-0034-home-vs-copilot-rail.md) (rail destinations) |
| DEC-0471 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (UI AD-5 unique issuers seed) |
| DEC-0472 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (native-first presentation) |
| DEC-0473 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (composer splits) |
| DEC-0474 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [WidgetFrame](../lenses/ui/screens/widget-frame.md) (widgets bind; expand/return) |
| DEC-0475 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [authoring](../lenses/ui/screens/authoring.md) |
| DEC-0476 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [library](../lenses/ui/screens/library.md) |
| DEC-0477 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (first-run partial readiness) |
| DEC-0478 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (Python daemon owns runtime; Tauri later) |
| DEC-0479 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (close/stop/cancel/unknown distinct) |
| DEC-0480 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (operations chrome consumes kit queries; GAP-0100) |
| DEC-0481 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [qma-core](../components/qma-core.md) (PackUiRequest; copilot_profile sibling) |
| DEC-0482 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (UI integration stream) |
| DEC-0483 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (chart provenance) |
| DEC-0484 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [CT-48](../contracts/ct-48-qma-mailbox-envelope.yaml) (chat is mailbox) |
| DEC-0485 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [SCN-0028](../scenarios/SCN-0028-first-operator-pair.md) (pairing bearer) |
| DEC-0486 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (ActionContext) |
| DEC-0487 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [SCN-0033](../scenarios/SCN-0033-publish-then-enable.md) (drafts) |
| DEC-0488 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [SCN-0032](../scenarios/SCN-0032-artifact-put-transfer.md) (artifact ingest) |
| DEC-0489 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [SCN-0035](../scenarios/SCN-0035-cancel-queued-to-running.md) (dispatchCancel) |
| DEC-0490 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (producer_id per tab) |
| DEC-0491 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [SCN-0028](../scenarios/SCN-0028-first-operator-pair.md) (Origin never sufficient) |
| DEC-0492 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [SCN-0029](../scenarios/SCN-0029-origin-revoke-vs-renew.md) (proof vs record; origin-revoke) |
| DEC-0493 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [CT-40](../contracts/ct-40-qma-wire-envelope.yaml) (AM-01) |
| DEC-0494 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [qmb](../components/qmb.md) (host verbs) |
| DEC-0495 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [CT-48](../contracts/ct-48-qma-mailbox-envelope.yaml); [SCN-0031](../scenarios/SCN-0031-mailbox-lost-ack.md) |
| DEC-0496 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [CT-46](../contracts/ct-46-qma-execution-environment-job.yaml) |
| DEC-0497 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [SCN-0032](../scenarios/SCN-0032-artifact-put-transfer.md) |
| DEC-0498 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [qma-core](../components/qma-core.md) |
| DEC-0499 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [SCN-0033](../scenarios/SCN-0033-publish-then-enable.md) |
| DEC-0500 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [qma-wire](../components/qma-wire.md) (addable names) |
| DEC-0501 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (reload/clone/cold start) |
| DEC-0502 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [qma-wire](../components/qma-wire.md) (HTTP byte channels) |
| DEC-0503 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [SCN-0030](../scenarios/SCN-0030-recover-control.md) |
| DEC-0504 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (umbrella) |
| DEC-0505 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (preflight reuse) |
| DEC-0506 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (AM-01..AM-17) |
| DEC-0507 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (honesty @ 34c148be) |
| DEC-0508 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (dead-list honors) |
| DEC-0509 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md); [gap report](../gap-report.md) (GAP-0081 / GAP-0100 answered) |
| DEC-0510 | `ratified` | [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md) (cheap-veto A10–A14) |

| Gap | Status | Blocking | Primary boundary |
|---|---|---:|---|
| GAP-0100 | `answered` | `false` | [Gap report](../gap-report.md); [ADR-0026](../decisions/ADR-0026-ui-host-and-backend-delta.md). Home attention plus kit diagnosis/health queries (DEC-0480, DEC-0509). Trading ticket chrome is GAP-0113. |
| GAP-0109 | `deferred` | `false` | [Gap report](../gap-report.md). Pairing TTL number; row exists, sitting mints no duration (DEC-0492, DEC-0510 A10). |
| GAP-0110 | `deferred` | `false` | [Gap report](../gap-report.md). `artifact.stage_max_bytes` number; missing row refuses PUT (DEC-0497, DEC-0510 A11). |
| GAP-0111 | `deferred` | `false` | [Gap report](../gap-report.md). CodeMirror 6 versus Monaco after a fidelity spike. |
| GAP-0112 | `deferred` | `false` | [Gap report](../gap-report.md). Tauri installer / sidecar supervisor (DEC-0478). |
| GAP-0113 | `deferred` | `false` | [Gap report](../gap-report.md). UX-10 trading/risk ticket chrome. |
| GAP-0114 | `deferred` | `false` | [Gap report](../gap-report.md); [qma-wire](../components/qma-wire.md). `qma-ui-contract` types beyond a stub. |

The 2026-09-25 UI host plus backend-delta fold adds eight implementing features (ADR-0026, DEC-0504): `FEAT-0064` chrome, `FEAT-0065` host lifecycle, `FEAT-0066` pairing, `FEAT-0067` mailbox field, `FEAT-0068` artifacts, `FEAT-0069` drafts, `FEAT-0070` PackUiRequest, `FEAT-0071` cancel. All `status: planned`, `size: multi-pass`. Preflight reuse — no COMP-UI, no new CT. Do not duplicate FEAT-0058..FEAT-0063. Do not launch these from this documentation-factory sitting.

| Feature | Wave | Component | Status | Blocker summary |
|---|---:|---|---|---|
| FEAT-0064 | 12 | client of [COMP-QMA-WIRE](../components/qma-wire.md) | `planned` | FEAT-0058. Differentiated-shell Svelte host (DEC-0469, DEC-0470). |
| FEAT-0065 | 10 | [COMP-QMB](../components/qmb.md), [COMP-QMA-DAEMON](../components/qma-daemon.md) | `planned` | FEAT-0042. `qmb host` plus recover-control (DEC-0494, DEC-0503). |
| FEAT-0066 | 12 | [COMP-QMA-DAEMON](../components/qma-daemon.md), [COMP-QMA-WIRE](../components/qma-wire.md), [COMP-QMB](../components/qmb.md) | `planned` | FEAT-0065, FEAT-0041. Pairing admission (DEC-0491, DEC-0493). |
| FEAT-0067 | 12 | [COMP-QMA-DAEMON](../components/qma-daemon.md), [COMP-QMA-WIRE](../components/qma-wire.md) | `planned` | FEAT-0045, FEAT-0041, FEAT-0066. Mailbox `product_session_ref` (DEC-0495). |
| FEAT-0068 | 12 | [COMP-QMA-DAEMON](../components/qma-daemon.md), [COMP-QMA-WIRE](../components/qma-wire.md) | `planned` | FEAT-0042, FEAT-0066. Artifact PUT plus transfer (DEC-0497). |
| FEAT-0069 | 13 | [COMP-QMA-DAEMON](../components/qma-daemon.md), [COMP-QMA-WIRE](../components/qma-wire.md) | `planned` | FEAT-0058, FEAT-0068. Editor drafts plus publish (DEC-0487, DEC-0499). |
| FEAT-0070 | 12 | [COMP-QMA-DAEMON](../components/qma-daemon.md), [COMP-QMA-WIRE](../components/qma-wire.md) | `planned` | FEAT-0058. PackUiRequest sibling of Epic 60.1 (DEC-0481, DEC-0498). |
| FEAT-0071 | 19 | [COMP-QMA-DAEMON](../components/qma-daemon.md), [COMP-QMA-WIRE](../components/qma-wire.md) | `planned` | FEAT-0055, FEAT-0066, FEAT-0041. `cancel_job` plus originating field (DEC-0489, DEC-0496). |
"""
    text = text.replace(marker, marker + append, 1)

PATH.write_text(text, encoding="utf-8")
print("traceability appended")
