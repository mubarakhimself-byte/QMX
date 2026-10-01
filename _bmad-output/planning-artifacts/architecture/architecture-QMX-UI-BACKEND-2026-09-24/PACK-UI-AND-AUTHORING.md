---
name: Pack UI ingest and authoring drafts
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
closes: joint-review J3/J4
---

# Pack UI ingest and authoring drafts

UI R4/R5 intent stays. This file binds backend owners.

## PackUiRequest

Schema `qmx.ui.pack_ui_request.v1` as UI `VIEW-AND-PACK-CONTRACT.md`. Host ingests at enable (parent AD-30). Not a contribution point. Not a GrantRecord. `PluginManifest.copilot_profile` remains Epic 60 Story 60.1.

**Read-back:** addable query `get_pack_ui_request` (HTTP GET snapshot family) keyed by enabled **`instance_id` + `availability_revision`**. That is the document the Svelte host loads when opening an instance. Unknown schema still does not roll back the operations roster.

Grant matching: 0 paint/refuse invoke; 1 bind; ≥2 `GRANT_AMBIGUOUS`.

## Draft identity (J3)

**Daemon** is the sole durable `editor_draft_id` issuer. Owner is the operator principal of the first save. UI may keep a **`client_draft_correlation`** (provisional, not authority).

| Step | Request | Result |
| --- | --- | --- |
| First save | PUT bytes, then `save_editor_draft` **without** `editor_draft_id`; `expected_revision` empty/absent; optional `client_draft_correlation`; names local-complete fp1 | `{editor_draft_id, editor_revision=fp1}` |
| First save that includes `editor_draft_id` | — | Typed refuse (not the issuer path) |
| Lost first-save ack | Retry first save with the **same** `client_draft_correlation` and **same** fp1 | Same durable id + fp1. No second working copy |
| Same correlation, different fp1 | — | Typed refuse |
| Subsequent save | `editor_draft_id` + `expected_revision` = current head fp1 + new bytes PUT | New head fp1 |
| Stale CAS | expected hash ≠ head | typed conflict; head unchanged |
| Reload head | addable `get_editor_draft_head` `{editor_draft_id}` | Current `{editor_draft_id, editor_revision}` |

`editor_revision` **is** the content fp1. Changing bytes creates a new saved revision. Library facade excludes these blobs.

## Publication (J4)

Addable **`publish_editor_draft`** (COMP-QMA-DAEMON, operator of the draft):

- Checks ownership of `editor_draft_id`
- CAS `expected_revision` = current head
- Reruns validation against that **immutable fp1** (no mandatory extra validation record)
- Writes the `graph_template` contribution into the **local authoring pack**
- Returns pack contribution identity (still unpublished as a distributable)

Invalid bytes, changed hash, stale expected_revision, or unauthorized draft → refuse. Unsaved preview/validate remain legal and mint no JobHandle.

Then **enable** that local pack (parent AD-30) is compile identity → grant → select one `instance_id` → `dispatchInvoke`. No second enable machine. Export remains later parent AD-18.

## Honesty at inspect

`PackUiRequest`, `get_pack_ui_request`, `get_editor_draft_head`, `editor_draft_id`, `publish_editor_draft` absent.
