# QMX UI host + backend-delta — documentation-factory Stage 9 brief (2026-09-25)

Route **e**, change mode, Stage 9. Do not restart Stages 1–8. Do not implement code. Do not rewrite the 2026-09-16 QML fold, the 2026-09-19 Workflows fold, or the 2026-09-23 pack-and-grant fold. Do **not** emit a BMAD epics-and-stories prompt.

Planning checkout: this `main` workspace. Implementation inspect: `integration@34c148be` via `.worktrees/integration-inspect`. Parent freeze for ADR-0024 original Decision: `270e992`. Do not switch branches.

Codex 2026-09-24 focused closure + 2026-09-25 recheck: **PASS**. Operator launched Documentation Factory the same day. That launch is the fold stamp.

## Authority

1. **Operator rider (ratified this session):** `_docwork/riders/ui-and-backend-delta-2026-09-25.md`.
2. **UI package:** `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/` — live law is the spine + companions listed in the rider. Historical `reviews/` and early `.memlog.md` lines that say `pairing_session_id` are not current law.
3. **Backend-delta package:** `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/` — live law is the spine + companions + `PARENT-AMENDMENT-MAP.md` + `DEPENDENCY-MAP.md` + `CLOSURE-C1-C2.md` + `CLOSURE-J1-J5.md`.
4. **Codex:** `workroom/qmx-ui-final-closure-2026-09-24/REVIEW.md` and `RECHECK-2026-09-25.md`.
5. **Parents (do not reopen as a new kit):** ADR-0024 / DEC-0414..DEC-0451; ADR-0025 / DEC-0452..DEC-0468. Named amendments of inherited contracts are AM-01..AM-17 (new DECs). Do not whole-supersede DEC-0421 / DEC-0437 / DEC-0304 / DEC-0319.

**Do not fold as current law:** leftover YAML `status: draft` / `not operator-accepted` in sitting folders; first-pass reviews that still say `pairing_session_id`; research notes as product pins; json-render / MCP Apps as required runtime; Tauri as v1-required; inspect types as e2e.

## Standing of claims

| Set | Stamp |
|---|---|
| Rider standing corrections | ratified (`authority: rider`) |
| UI AD-2..AD-24 product rules | ratified |
| Backend AD-3..AD-17 product rules (skip AD-1 sitting-scope / AD-2 classification meta) | ratified |
| Named AM-01..AM-17 | ratified (do not whole-supersede parent DECs) |
| ADR-0026 + SCN-0028..SCN-0035 | ratified (docs authority only; not implementation) |
| ADR-0024 / ADR-0025 original Decision | unchanged; dated follow-up only |
| ADR-0023 mill package | stays **provisional** |
| GAP-0081 / GAP-0100 | **answered** as this sitting's chrome law; remain out-of-scope *as kit holes* |
| New normative sentences on already-ratified parent docs | cite new DECs; dated follow-up or annotation |

`verified: 2026-09-25` on every doc you touch.

## ID block

| Kind | Range | Use |
|---|---|---|
| SRC | SRC-27 UI folder; SRC-28 backend folder; SRC-29 this rider; SRC-30 Codex closure |
| EXT | EXT-2464.. as needed | rider + local ADs + umbrella + preflight + AM map + honesty + dead-list + cheap-veto + catalog restamp |
| DEC | DEC-0469.. as assigned in the YAML append script (one product DEC per foldable local AD, plus umbrella/preflight/honesty/dead-list/catalog/cheap-veto) |
| GAP | GAP-0081 and GAP-0100 restamped answered; GAP-0109 TTL number; GAP-0110 stage_max_bytes number; GAP-0111 editor (CodeMirror vs Monaco); GAP-0112 Tauri installer; GAP-0113 UX-10 trading ticket chrome; GAP-0114 `qma-ui-contract` types beyond stub |
| FEAT | FEAT-0064..FEAT-0071 |
| ADR | ADR-0026 |
| SCN | SCN-0028..SCN-0035 |
| CT | **no new id** | additive CT-40 / CT-42 / CT-48 annotations |
| COMP | **none** | **no COMP-UI; no sixth application** |

Cite UI rules as `UI AD-n`. Cite backend-delta rules as `backend AD-n`. Cite parents as `parent AD-n` / `kit AD-n` / `QMA AD-n`.

## Preflight verdict (record in ADR-0026)

**reuse** existing applications. **new COMP: none. new CT: none.**

| Work | Owner | Class |
|---|---|---|
| Svelte host chrome (rail, Home/Copilot/Library/Authoring, unique issuers) | client of COMP-QMA-WIRE (UI lens docs; not a COMP) | extend parent AD-17 chrome |
| `qmb host` + `host_control` + `recover-control` | COMP-QMB + COMP-QMA-DAEMON | named AM-10 / AM-15 |
| Pairing HTTP + bearer proof + origin-revoke barrier | COMP-QMA-DAEMON + COMP-QMA-WIRE + COMP-QMB | named AM-01 / AM-03 / AM-11 |
| Mailbox `product_session_ref` + `list_mailbox` | COMP-QMA-DAEMON + COMP-QMA-WIRE | named AM-02 / AM-08 / AM-14; delivery still Story 46.4 / FEAT-0045 |
| `cancel_job` + `originating_product_session_ref` | COMP-QMA-DAEMON + COMP-QMA-WIRE | named AM-04 / AM-09 |
| PUT `/artifacts/stage` + `transfer_artifact` / `transfer_complete` | COMP-QMA-DAEMON + COMP-QMA-WIRE | named AM-05 / AM-06 / AM-13 |
| `editor_draft_head` + `publish_editor_draft` | COMP-QMA-DAEMON + COMP-QMA-WIRE | named AM-03 / AM-07 / AM-09 / AM-17 |
| `PackUiRequest` / `get_pack_ui_request` / ActionContext | COMP-QMA-DAEMON + COMP-QMA-WIRE | named AM-16; Epic 60 `copilot_profile` **reuse** |
| Live JSON-RPC/HTTP/event serving | COMP-QMA-DAEMON + COMP-QMA-WIRE | **adoption** of Epic 41–42 / FEAT-0041–0042 (not a new feature) |
| `caller_kind`, optional authoring instance, `copilot_profile` | COMP-QMA-CORE + WIRE + DAEMON | **already planned** FEAT-0058 / Epic 60 |

Candidates refused: COMP-UI / sixth COMP; new CT-*; third ProductSessionProfile; cookie login; `ui_view` contribution point; AD-22 as graph draft store; json-render/MCP as identity; QMB sqlite writer; reminting `local_operator` on recover; Origin-only issuance.

No existing component's authority shrinks. No new `depends_on` edge. No new contract id.

## Feature slices (implementation still factory-pipeline-only)

| FEAT | Name | Primary DECs | Blocked by |
|---|---|---|---|
| FEAT-0064 | Differentiated-shell Svelte host (rail, stack seed, unique issuers, UI lens) | UI AD-2..AD-17 chrome DECs | FEAT-0058 |
| FEAT-0065 | QMB host lifecycle + first operator + recover-control | backend AD-6, AD-17 | FEAT-0042 |
| FEAT-0066 | Pairing admission (proof vs record, Origin-never-sufficient, CORS, renew, origin-revoke) | backend AD-3, AD-4, AD-5, AD-14 | FEAT-0065, FEAT-0041 |
| FEAT-0067 | Mailbox `product_session_ref` + `list_mailbox` + `dispatchChat` | UI AD-18, backend AD-7 | FEAT-0045, FEAT-0041, FEAT-0066 |
| FEAT-0068 | Artifact PUT + reachable transfer + `transfer_complete` | UI AD-22, backend AD-9, AD-15 | FEAT-0042, FEAT-0066 |
| FEAT-0069 | Editor drafts + `publish_editor_draft` + local authoring-pack first Run | UI AD-21, backend AD-11 | FEAT-0058, FEAT-0068 |
| FEAT-0070 | PackUiRequest ingest + ActionContext + `get_pack_ui_request` | UI AD-15, AD-20, backend AD-10 | FEAT-0058 |
| FEAT-0071 | `cancel_job` + `originating_product_session_ref` + `dispatchCancel` | UI AD-23, AD-24, backend AD-8 | FEAT-0055, FEAT-0066, FEAT-0041 |

Do not launch these from this sitting. Independent planned epics 60–65 **continue**. Hold only stories whose **contract** conflicts (DEPENDENCY-MAP Hold vs continue): Story 41.4 unauthenticated-bind sentence; Story 46.4 Envelope field list; Epic 57 handle record for the optional originating field. Epic 60.1 is **not** held.

## Gaps

| GAP | Status after this fold |
|---|---|
| GAP-0081 | **answered** — chrome designed (Svelte differentiated shell). `qma-ui-contract` types beyond stub stay GAP-0114. Delivery FEAT-0064+ |
| GAP-0100 | **answered** — Home attention + kit diagnosis/health queries. Not a fourth observability product. Trading ticket chrome is GAP-0113 |
| GAP-0109 | deferred non-blocking — pairing TTL number |
| GAP-0110 | deferred non-blocking — stage_max_bytes number |
| GAP-0111 | deferred — CodeMirror 6 vs Monaco after fidelity spike |
| GAP-0112 | deferred — Tauri installer / sidecar supervisor |
| GAP-0113 | deferred — UX-10 trading/risk ticket chrome |
| GAP-0114 | deferred — `qma-ui-contract` package beyond stub |

GAP-0101..0108 stay answered kit law (FEAT-0058..0063). Do not re-open them as UI holes.

## Honesty at 34c148be

See rider. Docs must keep the START-HERE honesty tables. `source-inspected` ≠ e2e.

## Desk cleanup from Codex (non-blocking, must land in prose)

AM-10 / ADR / qmb.md / security-model: running-daemon host-control verbs require the current token. The **narrow** exception is `qmb host stop` when the `host_control` file is missing or unreadable, allowed only for the OS owner of `QMA_DAEMON_ROOT`, so `recover-control` can run. Do not describe a broader unauthenticated stop path.

Bearer wording in docs: `pairing:<proof>` and `qmx.pair.<proof>`, not `pairing:<id>`.

## Docs to touch

**New:**
- `docs/decisions/ADR-0026-ui-host-and-backend-delta.md`
- `docs/scenarios/SCN-0028-first-operator-pair.md`
- `SCN-0029-origin-revoke-vs-renew.md`
- `SCN-0030-recover-control.md`
- `SCN-0031-mailbox-lost-ack.md`
- `SCN-0032-artifact-put-transfer.md`
- `SCN-0033-publish-then-enable.md`
- `SCN-0034-home-vs-copilot-rail.md`
- `SCN-0035-cancel-queued-to-running.md`
- `docs/lenses/ui/design-system.md`
- `docs/lenses/ui/screens/home.md`
- `docs/lenses/ui/screens/copilot.md`
- `docs/lenses/ui/screens/library.md`
- `docs/lenses/ui/screens/authoring.md`
- `docs/lenses/ui/screens/bootstrap.md`

**Update:** constitution L7/L31 annotations; AGENTS.md; qma-core, qma-daemon, qma-wire, qmb; overview (replace deferred-Rust-UI node), stack (Svelte seed + Node pin), dependencies notes only; glossary; gap-report; traceability; index; changelog; ADR-0024 **dated follow-up** (chrome no longer GAP-0081-deferred); ADR-0025 dated follow-up (GAP-0081/0100 answered by UI sitting); CT-40 named AM-01 carve-out + addable names; CT-42 copilot_profile stays Epic 60; CT-48 additive `product_session_ref` excluded from fp1; security-model pairing/host-control; logging-spec redaction of proofs; test-strategy J-UI traces unexecuted; registry two null rows; GAP-0081/0100 public cells.

Do not add a `COMP-*` row for the Svelte host.

## Drafting rules

- Cite new DECs on every new normative sentence. Self-contained sections. No hedges. No TODO without a GAP id.
- Product nouns: Home / Copilot / Library / Authoring; pack / mini-app / widget / workflow; `pairing_proof` / `pairing_record_id`; `product_session_ref`; `originating_product_session_ref`.
- Banned: sixth COMP; COMP-UI; third profile; claiming live CT-40 / pairing / `qmb host` exist at `34c148be`; claiming envelope/grant/`product_session` types are absent; rewriting ADR-0024/0025 Decision; duplicating FEAT-0058..0063; cookies as login; Origin-only issuance; `pairing_session_id` as the live field.
- UI lens screens describe chrome against wire contracts. They do not fetch stores.

## What not to do

- Do not mint COMP-UI, CT-52, or a sixth store.
- Do not fill GAP-0085 / 0063 / 0061 / 0062 / 0058.
- Do not rewrite ADR-0020/0023/0024/0025 original Decision sections.
- Do not claim implementation.
- Do not start epics.
