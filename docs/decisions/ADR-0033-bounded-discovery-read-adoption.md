---
id: ADR-0033
title: Bounded CT-40 contribution discovery read adoption
type: adr
status: draft
generated: 2026-10-05
verified: 2026-10-05
stale_after: 30d
depends_on: [COMP-QMA-DAEMON, COMP-QMA-WIRE]
decisions: [DEC-0304, DEC-0305, DEC-0415, DEC-0443, DEC-0449, DEC-0491]
sources: [docs/architecture/dependencies.yaml, docs/architecture/stack.md, docs/registry/variables.yaml, docs/components/qma-daemon.md, docs/components/qma-wire.md, docs/contracts/ct-40-qma-wire-envelope.yaml, docs/scenarios/SCN-0018-contribution-hit-honesty.md]
---

# Bounded CT-40 contribution discovery read adoption

Verdict: **reuse COMP-QMA-DAEMON and COMP-QMA-WIRE**. MA-01 connects the existing
CT-40 query admission, live PluginLoader publication, Federation contribution
mapper and ContributionPinService revalidation. The dependency inventory,
component specifications and CT-40 already assign these responsibilities to
those owners. No new component, engine, independent store, dependency edge,
search index, grant or command is needed. This draft records bounded mounted
adoption; it does not revise existing ratified architecture or close other gaps.

The additive request/read schemas retain the existing ContributionHit and pin
identity grammars. Only live contribution discovery is mounted. Missing
Knowledge/Artifact owner dependencies and a real scoped health snapshot remain
typed unavailable. Health is not inferred from publication. Existing HTTP reads
and known-ID PackUiRequest remain unchanged. Current paired operator authority
is required; an explicit app-use session narrows discovery to its instance.

A successful read never appends a journal entry or grants invocation. Exact
pins are rechecked at facade_get, and an optional existing ContributionPin in
start_mission/launch_task is rechecked during current invocation admission,
before effects. Existing callers retain their original invocation shape.
This is a closed additive adoption, not a new candidate/publication lifecycle.

Read [the exact MA-01 contract](../../release/MA01-DISCOVERY-CONTRACT.md) for
routes, schemas, examples, scope and remaining unsupported features.
Serial installed acceptance passes; independent parent review is still required
before integration. Existing release quality, startup and platform
limits remain visible in that handoff. No numeric registry value is introduced;
existing literal discovery and CT-40 transport limits remain in force.
