# Investigation synthesis — 2026-09-23 observability / self-repair sitting

Coaching-path evidence only. Not architecture. Not ratified.

Freshness: docs `main@92279dfe`; implementation `integration@34c148b` via `.worktrees/integration-inspect`. Parent freeze still cites `270e992` in ADR-0024 honesty.

## Operator voice

`architecture-mimi0apps` is the 2026-09-18 Stage A/B/C dump, not a new transcript.

Spoken in Explore-Node-Editor (not a forgotten AD, but a forgotten *relationship*):

- Workflows **should have logs**; copilot should look at work records / logs / traceability.
- App-use: “what happened / why is this like this.”
- Live “what is going on” in the app; n8n-like CLI-in-node as visibility, not a monitoring product.
- Validate custom nodes; GPU/entitlement readiness; cutover dashboard (later chrome, GAP-0100).

**Self-heal / doctor-as-product / observability stack for mini-apps was not spoken in 09-18.** That half of this sitting is a new operator ask.

## What already binds (do not reinvent)

- Logs ≠ journals ≠ telemetry ≠ ledgers (DEC-0112, DEC-0322, parent AD-16).
- QMN: zero-authority Prometheus/Grafana/Loki; alerts ≠ permission; `/health` independent states; liveness heartbeat notify-only (TN-15, DEC-0200/0212/0261).
- QMA: telemetry store off journal; OTel at export port only, no SDK in daemon core; agents must not author telemetry; closed eight store classes.
- `correlation_id` is the only designed cross-QMA/QMB/QMN join key.
- Pack validate/enable is a **hard gate** + roster restore, not Hermes warn-and-continue.
- App-use mints `change_request`; authoring + operator applies (AD-29, SCN-0019).
- QMA `RefinementProposal` apply is operator-principal only (GAP-0074 is evaluation gates, not live auto-fix).
- n8n Retry-On-Fail as same-task mutation: refused. HMR / hot-apply: dead/deferred.

## Code at 34c148b (Workflows 53–59 landed as types/fixtures)

Present: ContributionHit, InvocationEnvelope, GrantRecord, product_session, DAG, durable outbox/join/JobHandle, ATC PolicyPair, streams, fencing, pack lifecycle fixtures.

Absent: CheckpointManifest (AD-27); mini-app `health()` / doctor; Workflows `FAILURES.md` / FR-WF entries; operator logger on qma-daemon; envelope/grant/outbox diagnostic emit.

Divergence already in tree:

| Plane | Operator logs | Metrics | Tracing |
|---|---|---|---|
| QMN | stdlib JSON-lines | prometheus_client `qmn_*` | none (no OTel V1) |
| QMA daemon | **none** | telemetry kind `"metric"` only | OTel-shaped export adapter |
| QMB | custom JSONL LogSink | none | correlation_id only |
| QML | none | none | none |

DEC-0286 still applies: fixtures ≠ e2e product surface.

## The gap this sitting owns

Parent binds identity, grants, durable control-flow, typed refusals, and “logs are not evidence” so a run is *reconstructible from stores*. It does **not** bind:

- operator-log field roster for a mini-app / `graph_run`
- metric families for that plane
- instance `health()` schema
- Workflows failure-register
- who owns “what went wrong”
- a diagnosis journey (copilot + headless)
- self-repair policy matrix

No existing journey: “mini-app/workflow failed; I see what/when/why/how; it does or does not repair itself.”

## Coaching forks (not decided)

1. **Observability relationship:** extend QMA telemetry + add daemon operator logs (inherit QMN field conventions where they apply) vs mint a fourth observability product. Investigators lean: no fourth product, no second telemetry store, no QMN allow-list reuse for mini-apps.
2. **Self-repair:** observe+explain+`change_request` vs bounded auto-retry of `none`/`read` (already AD-24) vs auto-apply of fixes (conflicts L17, AD-8/9/29, money-path).
3. **Join key:** `correlation_id` (recommended) vs minting a workflow-run id.
4. **Chrome:** contracts + headless now; GAP-0081/0100 later.

## Deliverable default until operator answers

Spine as build-substrate. Optional later: contracts addendum, one diagnosis/repair journey, ops-lens patch. Not a UI dashboard sitting.
