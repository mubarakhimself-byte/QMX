# Independent review — Epic 60 `copilot_profile` placement

**Subject:** `architecture-QMX-UI-2026-09-23/VIEW-AND-PACK-CONTRACT.md`, `EXAMPLES.md`  
**Against:** kit `architecture-QMX-2026-09-23/CONTRACTS.md` §1; `_bmad-output/planning-artifacts/epics-PACK-AND-GRANT-2026-09-23.md` Epic 60 / Story 60.1  
**Question:** do the UI contract and examples still forbid `PluginManifest.copilot_profile`, or nest that blob exclusively inside `pack_ui_request`?  
**Date:** 2026-09-24. Reviewer: independent. Contract files only. No epic rewrite. No implementation.

**Verdict: compatible with Epic 60.**

The exclusive-schema move is gone. `copilot_profile` is again an optional sibling field on the existing `PluginManifest`. `PackUiRequest` references it and must not replace it. Absence remains valid. Factory ownership stays Epic 60 / COMP-QMA-CORE. No parent amendment is required.

Leftover exclusive-forbids of `PluginManifest.copilot_profile`: **none found.** Residual phrasing still groups the blob with PackUiRequest emptiness; that is not a second live profile field.

---

## Authority (unchanged; not rewritten)

Kit CONTRACTS §1 (`architecture-QMX-2026-09-23/CONTRACTS.md:10-19`):

> A pack manifest **requests**:
>
> - `contributes`: list of `{point, local_id}` for operations only (parent AD-2)
> - optional `view:*` wire DTOs (parent AD-17) — not a contribution point
> - optional `copilot_profile` request blob — not a contribution point, not a grant
> - `requested_capabilities` — **request**
>
> Host **grants** GrantRecords into a `psess:`. Absence of `copilot_profile` is valid.

Epic 60 (`epics-PACK-AND-GRANT-2026-09-23.md`):

- Story 53.2 / 48.1 already owns `contributes` + `permissions`. This increment **closes** optional `copilot_profile` on that same manifest (`:290`).
- Factory touch: COMP-QMA-CORE (`PluginManifest` optional `copilot_profile`) (`:304`).
- Story 60.1 Then: the manifest **requests** operation contributes, optional `view:*`, optional `copilot_profile` request blob, and `requested_capabilities`. The blob is not a contribution point and not a grant (`:324-325`).
- Omit `copilot_profile` (and omit `view:*`) is valid; enable is not grant (`:327-330`).
- Final validation: `copilot_profile` is a request blob **on the existing manifest** (`:966`).

Epic 60’s “Do not leave two live request fields” (`:325`) is `requested_capabilities` as AMEND/alias of inspect `permissions`. It is not a ban on a later chrome DTO, and it is not a license to relocate the copilot blob.

---

## What the UI files now say

### `VIEW-AND-PACK-CONTRACT.md` — live field is the Epic 60 sibling

| Locus | Binding |
| --- | --- |
| `:22` | `PackUiRequest` v1 is (`nav`, `views`) only. Optional `copilot_profile` is **not** in that cell (the prior nested listing is gone). |
| `:24` | `PluginManifest.copilot_profile` — **Epic 60 / kit sibling field**. Not a contribution point. Not a grant. Absence valid. PackUiRequest **references** this field; it does not replace it. |
| `:36` | Manifest keeps Epic 60 fields including optional **`copilot_profile`**. At most one `pack_ui_request` for chrome. **Do not nest `copilot_profile` inside `pack_ui_request` as a replacement.** No parent amendment. Stories 60.1+ own the blob. |
| `:38-56` | Worked PackUiRequest JSON has `schema`, `pack_id`, `pack_version`, `nav`, `views`. **No** nested `copilot_profile`. |
| `:59` | Host reads optional `PluginManifest.copilot_profile` **beside** this document. |
| `:72` | `copilot_profile` is **not a PackUiRequest field.** Lives on `PluginManifest` (Epic 60). Host copies it at enable if present. |
| `:313` | Honesty: specified by kit AD-1 / AD-3; **absent** at `34c148b`. Matches Epic 60 / NFR-PG-04. |

That is the same schema Epic 60 already planned: one optional blob on `PluginManifest`; UI consumes it; chrome request is a different document.

### `EXAMPLES.md` — JSON places the blob on the manifest

Packs A (`:45-50`) and B (`:160-165`) put `copilot_profile` as a **sibling** of `pack_ui_request` on the pack object (`id` / `version` / `contributions` / `permissions` / `copilot_profile` / `pack_ui_request`). Nested `pack_ui_request` objects contain `schema`, `nav`, `views` only.

Pack C (`:229-247`) omits `copilot_profile` and may send an empty `pack_ui_request` or omit that key. That is Story 60.1 / SCN-0024 headless: absence is valid.

No example nests `copilot_profile` inside `pack_ui_request`. No example forbids a sibling manifest field.

---

## Leftover forbids

**Exclusive-forbid of `PluginManifest.copilot_profile` — absent.** Sitting-tree search for the prior exclusive sentence returns no hits:

> Do not also ship a sibling manifest `copilot_profile` or a sibling `views` array — that would be two live request fields.

That was the R4.1 conflict (`workroom/qmx-ui-closure-review-2026-09-24/reviews/experience.md`). It is not in the current contract or examples.

**Exclusive nest inside `pack_ui_request` — absent** from both JSON worked examples and the PackUiRequest field table (`VIEW-AND-PACK-CONTRACT.md:72`).

The only remaining `copilot_profile` **forbid** in these two files is the Epic 60-compatible one:

> Do **not** nest `copilot_profile` inside `pack_ui_request` as a replacement for the manifest field. (`VIEW-AND-PACK-CONTRACT.md:36`)

That forbids the old UI relocation. It does not forbid the planned manifest field.

---

## Residual phrasing (not a schema conflict)

These sentences still name `copilot_profile` in PackUiRequest emptiness language. They do **not** restore the sibling-field forbid. They do **not** put the blob inside the JSON schema. Independent builders who follow §1–§2 and EXAMPLES A/B still land on `PluginManifest`. Quote for honesty:

`VIEW-AND-PACK-CONTRACT.md:91` (ingestion table, PackUiRequest conditions):

> Key omitted or `{}` / `{schema, pack_id, pack_version}` with empty `nav`+`views` and no `copilot_profile` | yes | Headless. Valid.

`VIEW-AND-PACK-CONTRACT.md:290` (§11 headless):

> Equivalent: omit `pack_ui_request` from the manifest. Omit `nav`, omit `views`, omit `copilot_profile`.

`EXAMPLES.md:249` (pack C prose):

> Empty request: no `nav`, no `views`, no `copilot_profile`.

Reading: leftover grouping from the nested schema. A pack with `PluginManifest.copilot_profile` and empty `pack_ui_request` is mixed (panel, no nav/views), which kit law already allows. §4 still keys the panel on the blob (`:114`). §2 still copies the **manifest** field (`:59`, `:72`). These three lines should not be read as “put the blob only inside `pack_ui_request`” or as “do not ship `PluginManifest.copilot_profile`.”

---

## Parallel-builder check

| Builder | Shape they implement | Conflict with the other? |
| --- | --- | --- |
| Pack-and-grant factory (Epic 60.1) | Optional `PluginManifest.copilot_profile`; omit valid; not a hit; not a grant | No. UI contract names that field as owner. |
| UI pack / shell (this sitting) | Optional `pack_ui_request` (`nav`, `views`); host reads sibling `copilot_profile` | No. Examples A/B ship both as siblings. |

Two live **profile** fields: **no.** One blob, Epic 60 owner, UI consumer.

---

## Out of this review

Did not rewrite epics. Did not score R4.2 / R4.3. Did not treat specified-absent at `34c148b` as a contract fail. Documentation Factory not in scope.
