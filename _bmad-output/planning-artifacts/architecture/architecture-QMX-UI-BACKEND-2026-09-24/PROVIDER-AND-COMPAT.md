---
name: Provider setup and compatibility
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
---

# Provider setup and compatibility

## Shell versus provider (small reconciliation)

| Surface | What “ready” means |
| --- | --- |
| Clean-machine **shell** | `qmb host start` (AD-17 bootstrap) + pairing TTL + pair + initialize. Home/Library chrome may load disconnected or without models |
| **Provider** use | An allowlisted `cred://models\|inference\|compute\|sandbox\|corpus\|knowledge\|telemetry/` ref **already** in the OS store, resolvable by the broker, and healthy |

Lack of a browser secret writer is not a shell blocker. External credential provisioning (OS store / later QMB write-once helper) is a **prerequisite** for provider cards to become usable. The page receives refs and health only.

ReadinessCard states: `absent_ref` \| `unresolved_ref` \| `unhealthy` \| `usable`.

Broker allowlist is **not** widened with an operator-login family. Operator identity is AD-17 host-control, not a dummy provider ref.

Broker `_reader` injection remains an adoption gap. Local model-proxy stays QMA AD-15, outside pairing.

## Capability advertisement (AD-13)

`initialize` advertises: `pairing`, `list_mailbox`, `cancel_job`, `caller_kind`, `stage_artifact` (authenticated PUT `/artifacts/stage` exists — not a `WireCommand`), `transfer_artifact`, `transfer_complete`, `pack_ui_request`, `get_pack_ui_request`, `save_editor_draft`, `get_editor_draft_head`, `publish_editor_draft`. Missing required capability → typed mismatch (J-UI-13).

Local model-plane CLI proxy stays QMA AD-15 (behind ModelDeployment). Classify as **already planned / adoption gap** of that parent, not a QMB or broker write. First-run ownership is the `cred://inference` ref form, not a proxy UI.

## Installed product (J-UI-14)

| Concern | Rule |
| --- | --- |
| Data root | `QMA_DAEMON_ROOT` per-user |
| Shell start | `qmb host start` + configure TTL + pair |
| Provider | External provision prerequisite |
| Client bits | Static SPA ≠ daemon sqlite |
| Update | Replace client files; do not rewrite journals |

No native-performance or build-success claim.
