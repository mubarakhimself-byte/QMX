---
name: Provider setup and compatibility
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
---

# Provider setup and compatibility

## Credentials (AD-12)

QMA AD-24 broker: exact-ref resolve; Windows Credential Manager first backend; allowlist in `qma-core` source. Venue/broker/exchange keys stay out of QMA.

Inspect: `proxy/broker.py` `_reader` mapping; UI research recorded WinCred reader **uninjected** in `DaemonProcess.compose`. That is an **adoption gap**, not a new broker.

v1 browser:

- May select an already-stored **ref** on a ReadinessCard.
- Must not send secret values on CT-40, pairing, traces, or diagnostics (`FORBIDDEN_SECRET_SURFACE_KEYS` includes `token`/`bearer` — pairing ids are session ids, not those keys).
- Must not write the OS store from page JavaScript.

A later **QMB/native** helper may write-once into the OS store and return a ref. Revisit when first-run cannot complete without a write path. Reconnect never resubmits a secret (`update_configuration` CAS; lost ack queries health).

Local model-proxy (`auth_mode: none`, QMA AD-15) stays outside QMA’s namespace. v1 browser does not speak to it. Classify as **reuse** of QMA AD-15, not a new pairing path.

## Capability advertisement (AD-13)

`initialize` already negotiates `protocolVersion` and capabilities (Epic 41.1). Advertise at least:

`pairing`, `list_mailbox`, `cancel_job`, `caller_kind`, `stage_artifact`, `transfer_artifact`, `pack_ui_request`.

Missing required capability → typed mismatch (J-UI-13). Shell remains usable for surfaces that do not need it. Do not silent-downgrade. Do not send the operator through pack enable (J-UI-10) for a protocol miss.

Same-major changes additive (Epic 41.2). `product_session_id`, `originating_psess`, PackUiRequest extras: unknown fields ignored by older clients.

## Installed product (J-UI-14)

| Concern | Rule |
| --- | --- |
| Data root | `QMA_DAEMON_ROOT` per-user (HOST-LIFECYCLE) |
| Start | `qmb host start` or interim recipe |
| Client bits | Static SPA (or later Tauri webview) ≠ daemon sqlite |
| Update | Replace client files; do not rewrite journals or widen grants |
| Recovery | Reconnect query; in-flight JobHandles unchanged |
| Clean machine | No checkout required; lock + pair + initialize |

No native-performance or build-success claim. Isolated scaffold remains UI-stream unexecuted.

## Local vs remote

Probe HTTP reachability of loopback or the recorded HTTPS origin. Remote failure **never** retargets local. Pairing table is per daemon origin. Loopback pairing does not authorize a remote host.
