---
name: Pack UI ingest and authoring drafts
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
---

# Pack UI ingest and authoring drafts

UI R4/R5 stay closed. This file names backend owners.

## PackUiRequest

Schema `qmx.ui.pack_ui_request.v1` as UI `VIEW-AND-PACK-CONTRACT.md`. Host **ingests** at enable (parent AD-30). Not a contribution point. Not a GrantRecord.

- Unknown schema version: ignore chrome request; operations roster still enables (headless-valid).
- Nav item with empty or unknown `view_ids`: drop **that item**, do not fail enable.
- `PluginManifest.copilot_profile` remains Epic 60 Story 60.1. **No parent amendment** to nest it in this document.

Durable: pack metadata projection beside the plugin-install row (availability_revision). Immutable `ActionContext` is minted per mount (UI AD-20), not stored as a grant.

Grant matching (already UI-closed): 0 paint/refuse invoke; 1 bind; ≥2 `GRANT_AMBIGUOUS`.

## Drafts (AM-07)

QMA AD-22 staging stays **one** record type: RefinementProposal. Graph editor drafts are **not** that type.

| Record | Store |
| --- | --- |
| Saved revision bytes | Existing artifact store (content-addressed `editor_revision`) |
| Head pointer | Journal projection `editor_draft_head`: `editor_draft_id`, head hash, owner principal, optional `psess:` |

Save = PUT bytes then addable command `save_editor_draft` `{editor_draft_id, fp1, expected_revision}`. `editor_revision` **is** that fp1. Daemon mints `editor_draft_id` on first save. Stale CAS → typed conflict. Library facade excludes these blobs. Validate/preview uses descriptor validation; compile identity remains parent AD-30 enable (no second validator record). Two restored clients: second save refuses until reload of head fp1.

Unsaved buffer stays client-local.

## First Run (reuse parent AD-30)

Publish immutable Graph Template **into the local authoring pack** → **enable** that pack (compile-at-enable) → grant into authoring `psess:` → select exactly one `instance_id` → `dispatchInvoke`.

No second enable machine. Distributable export is later parent AD-18.

Draft Run remains refused.

## Honesty at inspect

`PackUiRequest` absent. `copilot_profile` absent. `editor_draft_id` absent. Graph Template contribution at enable **specified** parent AD-4; live Svelte editor absent (UI stream).
