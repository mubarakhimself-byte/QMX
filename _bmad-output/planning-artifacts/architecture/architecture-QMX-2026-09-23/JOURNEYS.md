---
name: Journeys — pack-and-grant kit
sitting: architecture-QMX-2026-09-23
---

# Journeys

Parent JOURNEYS.md remains. These are the missing ones.

## J-KIT-01 — Headless pack, no copilot

Operator enables a pack with operations and no views and no copilot profile. Main authoring session invokes an op via CLI/wire. Run produces a JobHandle. No in-app panel exists. Work continues if a future UI tab is closed.

## J-KIT-02 — Optional in-app panel

App-use session on instance A. Panel asks why the last run failed. Host returns `failure_class=workflow` plus JobHandle. Panel cannot edit the pack. Operator mints a change-request; authoring applies v2; v1 instance stays.

## J-KIT-03 — Main session references another app

Authoring session with no instance on the session row. Operator selects exactly one `instance_id` in `selected_refs`. Invoke uses that instance's GrantRecords. Zero or two instance refs refuse. Nested call does not widen tools.

## J-KIT-04 — Widget starts a workflow

User (or agent) presses a widget bound to `start` of template T. Envelope `caller_kind=user` or `agent`. Widget dispose does not cancel the Mission.

## J-KIT-05 — Workflow calls another workflow

Template A has a node that starts template B as a nested Mission. B has its own JobHandle. Crash of A does not splice B's Task Graph into A's. Recursion budget applies.

## J-KIT-06 — Ordinary retry

A `read` op flakes. Host retries. Operator is not paged. An `external-egress` without a receipt becomes `unknown`. No second send.

## J-KIT-07 — Weak model builds

An older model authors a pack by filling descriptor schemas and requested capabilities. Host validate fails closed on missing dep. Model prose cannot add an op.
