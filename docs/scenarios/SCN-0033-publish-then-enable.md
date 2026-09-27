---
id: SCN-0033
title: Publish editor draft then enable local authoring pack
type: scenario
status: ratified
component: COMP-QMA-DAEMON
depends_on: [COMP-QMA-WIRE]
decisions: [DEC-0487, DEC-0499]
sources: [DEC-0487, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# SCN-0033: Publish editor draft then enable local authoring pack

First Run is publish into the local authoring pack then parent AD-30 enable, never a mutable draft (DEC-0487).

This scenario is specification of intended behavior, not inspect proof. Pairing, qmb host, list_mailbox, cancel_job, PUT /artifacts/stage, and Svelte chrome are absent at integration@34c148be (DEC-0507). Class/test existence is not e2e (DEC-0286).

## Given

Authoring operator. First save omitted `editor_draft_id`. Daemon returned `{editor_draft_id, editor_revision=fp1}`. QMA AD-22 RefinementProposal is not the store (DEC-0499).

## When

`publish_editor_draft` with `expected_revision` equal to current head fp1. Then enable that local authoring pack (parent AD-30). Then grant, select that instance, `dispatchInvoke`.

Negative: `dispatchInvoke` against the mutable draft. First save that supplies an `editor_draft_id`.

## Then

Publish revalidates immutable fp1 and writes the local unpublished roster item (DEC-0499). Enable remains compile identity. Draft Run refuses (DEC-0487). Supplied id on first save refuses. Distributable export is not this path.

## Worked numbers

`editor_revision` is the content fp1. CAS uses exact equality of `expected_revision`.
