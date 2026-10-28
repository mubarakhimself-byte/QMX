---
title: Connect deep logs (OpenObserve) on any machine
type: grilling
mode: AFK
status: closed
blocked_by: [connect-dialog]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

Is OpenObserve the right tool, self-hosted or cloud, and how does it get set up "for multiple machines" (`words:185`) from the screen?

## Resolution

- **OpenObserve, self-hosted, one per person, on the machine he picks.**
  - He settled the tool: "Prometheus is already in open observe ... It's a whole in an all-in-one" (`words:219`).
  - He settled self-hosted: cloud's "$0.50 per GB ingested is kind of a lot ... my personal compute would be better" (`words:219`). This reshapes R123 (free tier as external monitoring); the latest word wins.
  - One program holds logs, metrics and traces. The Grafana route is three or four programs (`src:` 4.4).
- **The setting stays `[telemetry] send_to`**: `off` (default), `this-pc`, or a place name (`PK/qma-harness/src/qma/telemetry.py:1-46`). Saving it now checks the value. Today `PUT` stores anything and a bad value quietly sends nothing (UIH §26 gap 6). A doctor row for telemetry is added, built from the exporter's counters in `logs/telemetry.json`.
- **"Deep logs: on this PC" steps** (UIH §26 gap 7; LF10):
  - QMX fetches the pinned OpenObserve into `cache/openobserve/` and checks it (a 150 MB zip for v1.1.2, `src:` 4.1).
  - It starts OpenObserve under the host, with its root password in Credential Manager.
  - It sets `ZO_TELEMETRY=false`, a fixed disk cache (1 GB by default, editable), retention 30 days (editable), `ZO_DATA_DIR` under `cache/openobserve/`, and loopback binding (the Tailscale address when another machine sends here).
  - The defaults matter. OpenObserve keeps data 10 years, phones home, and grows its cache to half of free disk (`src:` finding 9), on a laptop with 17 GB free on C:. None of these limits what he does, so none is a usage cap (R106).
- **"Deep logs: on a server" steps:** install the unit files (`PK/qmx-host/deploy/openobserve.service`, `otelcol.service`), which today need hand steps (`inv:` 7). This is the server kind's monitoring step.
- **Every other machine** gets an OpenTelemetry Collector with an on-disk queue that sends to his one OpenObserve. An offline machine holds its records and sends later (`src:` 4.3).
- **No admin rights is the design.** OpenObserve's quickstart uses an Administrator prompt; whether a per-user run works was not tested (`src:` 4.1). The build's first check runs it per-user. If it needs admin, the dialog shows one card for his approval; the dialog's shape does not change.
- **The outside-agent door** (R126) is OpenObserve's own MCP endpoint, with an agent login the dialog makes, never the root login. The free edition cannot make that login read-only (`sources/openobserve-integration-ai-mcp-index.md`). The risk is accepted because OpenObserve holds only rebuildable data: the Library keeps every run's trace and logs (`PK/qmx-host/deploy/openobserve.service:3-7`).
- **No backup of OpenObserve's data.** It is the rebuildable class, so sync never sends it.

## Evidence

R126 (two DevOps layers from one source of events), R140 (local first, server second, monitoring included). `explore:` 5. `inv:` 7.
