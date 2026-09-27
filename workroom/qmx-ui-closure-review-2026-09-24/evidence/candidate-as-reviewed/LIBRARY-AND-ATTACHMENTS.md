---
name: Library and attachments
sitting: architecture-QMX-UI-2026-09-23
closes: Codex R6
status: candidate — not operator-accepted
inspect: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20
governs: local AD-7, local AD-10, local AD-22
---

# Library and attachments — closed refs, ingest, verb matrix

Law in `ARCHITECTURE-SPINE.md` (local AD-7, local AD-10). This companion maps every promised composer source onto the **closed** `selected_refs` catalogue, names byte ingest, and promotes the per-rail Library verb matrix from `research/13-library-lifecycle.md`. Research stays evidence; this file is the binding contract.

**Provenance:** **CANDIDATE** sitting default for Codex R6. Not user-accepted. Not implementation.

**Forbidden:** a generic Library database, `COMP-LIB`, a copied-row sqlite, a sixth store class, a new `selected_refs` kind other than kit `instance_id`, collapsing Artifact / Knowledge / Contribution / Hypothesis identities.

## Honesty at `34c148b`

| Claim | Fact |
| --- | --- |
| `SELECTED_REF_KINDS` | `{artifact, research_ref, contribution, template, dataset, run, attempt, node_ids}` — **no** `instance_id`, **no** `knowledge`, **no** `local_path`, **no** `upload_bytes` |
| kit `instance_id` kind | Specified DEC-0463; **absent** in code |
| CT-44 `cite` | **Present.** Copies bytes, returns `Citation` + `artifact_ref` / `content_fp1`. Cite-copy is **not** an ArtifactHit |
| `stage_artifact` daemon command | **Absent.** Backend add (local AD-22) |
| `facade_search` concatenate | Types + in-process tests; **not** live HTTP; `E2E_ADOPTION_CLOSED = False` |
| QMB `library.search` | **Present** (fp1 + kind). Occupancy `query` |
| Hypothesis listing on facade | **Refused.** `qml.research` has save/read by `research_ref`; **no** browse-all |
| Library UI | **Absent** |

DEC-0286 stands.

## 1. Closed `selected_refs`

Parent AD-8 kinds plus kit `instance_id` (DEC-0463). Nothing else.

| Kind | Id | Notes |
| --- | --- | --- |
| `artifact` | content fp1 | Durable bytes the host **possesses**. Provenance metadata may ride **on** the chip; it is not a second kind |
| `research_ref` | fp1-shaped class `qml-research-hypothesis` | Hypothesis; off Library facade |
| `contribution` | `(qualified_id, package_version)` | Live tuple; never fp1 |
| `template` | `(qualified_id, version)` | Registered Graph Template |
| `dataset` | dataset / release identity | Not a machine path |
| `run` | run identity | Saved run, not a widget cursor |
| `attempt` | `attempt_id` under a run | |
| `node_ids` | node-id set **citing a template** | Induced DAG of a registered version |
| `instance_id` | plugin-install instance | Kit add. Envelope copies this on invoke |

**Forbidden kinds:** `local_path`, `upload_bytes`, `knowledge`, `citation`, `widget`, `view_id`, `layout`, json-render trees, `pane`. Do not mint them.

Live ids (instance, dataset, contribution, template) show a **stale / unavailable** badge when listing axes say so. Snapshot bytes (artifact fp1) do not pretend to track a moving file.

## 2. Attachment map

Every composer/content source the session promised. Chip inspect/remove is chrome over these rows. Unavailable recovery: keep the surrounding draft; refuse invoke of that identity; never silent substitute (J-UI-05; tombstone ≠ other version).

| Source | Durable representation | Notes |
| --- | --- | --- |
| file / image upload | `selected_refs` kind **`artifact`** fp1 **after** daemon `stage_artifact` | Browser-computed hash is **not** possession. Do not mint `upload_bytes` / `local_path` |
| existing stored file | kind **`artifact`** / **`dataset`** / **`run`** as the stored object already is | Pointer to an already-stored identity. Machine path is not a portable id |
| Knowledge citation | CT-44 `cite` returns copied bytes + `artifact_ref` / `content_fp1`; composer kind remains **`artifact`** | Chip **shows Knowledge provenance** (`source_ref`, `snapshot_ref`, `locator`, evidence label). **Do not mint** kind `knowledge`. Cite-copy is not an Artifact-rail Library hit |
| widget result **message-only** | **chrome context** on the conversation (view_id, snapshot cursor, filters) until **Save** | After Save: kind **`artifact`** or **`run`**. Never persist view/filter JSON as a selected ref |
| app instance | kind **`instance_id`** | Kit add. Cross-app reference does not merge histories or union grants (J-UI-04) |
| research | kind **`research_ref`** | Viewing cited seed does not mint `research_ref`. Save is explicit `save_authored_hypothesis` |

Message-only widget refs die with chrome (tab/layout not durable). Save is an explicit operator act on the **owning** rail. Ungoverned projection remains a return value until save (Workbench AD-5).

Cross-app: composer on `psess:` A may cite B’s artifact/instance. Authority stays A’s GrantRecords. Unavailable B is labelled; the draft remains.

## 3. Ingest owner — `stage_artifact` (local AD-22)

| Field | Contract |
| --- | --- |
| Owner | **COMP-QMA-DAEMON** |
| Command | `stage_artifact` (CT-40 host command, **not** a pack op, **not** `dispatchInvoke`) |
| Store | Existing artifact registration path (`before_artifact_register` / content fp1). **No new sqlite class.** Not a Workbench AD-3 kind unless a later register on that rail says so |
| At `34c148b` | **Absent** as a product command. Knowledge `cite` already copies through `before_artifact_register` into an in-memory `_artifacts` map — that is the pattern to reuse, not a Library database |
| Auth | Authenticated principal **before** protocol bytes (parent CT-40). MCP/json-render/native frames **must not** call this; host chrome does. Not a GrantRecord pack-op |
| Instance | Staging **does not** require `selected_refs` kind `instance_id`. **Run** of those bytes later does |
| Input | Streamed bytes + declared media/schema. Optional client hash is advisory progress only |
| Host proof | Daemon **recomputes** fp1 after it holds complete bytes. Client hash ≠ possession |
| Completeness | `complete` \| `partial` \| `missing` \| `expired` (parent AD-26 inventory vocab). Partial is not a runnable ref |
| Interrupt / retry | P1-PLC-003: interrupted staging or path-escape → no partial/unauthorized read; clean **resumable or refused** state. Resume uses the same staging identity; it does not mint a second fp1 for the same complete bytes |
| Return | durable fp1 + completeness. Composer then CAS-inserts `selected_refs` kind `artifact` |
| Remote placement | Stage **onto the placement that will run**, or **refuse**. Never silent local retarget (J-UI-09, P1-PLC-002). Remote failure does not rewrite the ref into a laptop path |
| Forbidden | Inlining bytes on InvocationEnvelope; treating a local path as global id; hashing in the browser and skipping the daemon write |

`stage_artifact` is a backend **add**. UI depends on it; the UI must not invent an upload BFF or a REST invoke API (local AD-12).

## 4. Knowledge cite — provenance without a new kind

CT-44: pin `snapshot_ref` first (story 49.3). `cite` copies bytes, returns `Citation` `{source_ref, snapshot_ref, locator, evidence_label, evidence_confidence, artifact_ref, content_fp1, authored_by}` plus retained `ArtifactCopy`.

Composer:

1. Kind = **`artifact`**. Id = `content_fp1` (host possession).
2. Chip metadata (not a `selected_refs` kind): Knowledge provenance from the Citation. Label the chip as a Knowledge cite, not as a Workbench AD-3 ArtifactHit.
3. Library Artifact rail **must not** grow a row from this cite-copy. Knowledge rail stays `KnowledgeHit`.
4. Retrieve without pin → `StaleSnapshot`. No live-tree substitution. No write-back into the corpus.
5. Citation digest / `artifact_ref` is **not** `research_ref` and not mill `originating_research_ref`.

This is the named resolution of Codex Team-A (collapse Knowledge into ArtifactHit) vs Team-B (mint kind `knowledge`). Neither. Closed kind `artifact` + provenance metadata.

## 5. Library chrome — one destination, typed hits, no database

Library is a **platform rail destination** (local AD-10; dictation `JHZj5SdT` / `NJidF6Tg`: jump to sidebar, **not** a tab on the mini-app). Same destination from Home, Copilot, Authoring, and any mini-app. Zero opened apps is legal.

Facade concatenate (parent AD-2): ArtifactHit + KnowledgeHit + ContributionHit. Hypothesis listing stays on `qml.research`, **off** the facade. Chrome may **navigate** to research without folding the DTO.

Mini-app “library” is a **filter** over the same hits, not a second taxonomy and not a canvas-replacing tab (D-015).

`hit_class` stays visible. Concatenate is a query fold, not a unified row cache. Ranked/semantic search stays GAP-0073.

Headless packs still appear as ContributionHits. Lack of `view:*` is not a hide rule (local AD-5).

### 5.1 Locate-in-Library and return

| Step | Contract |
| --- | --- |
| Control | From preview / widget / composer chip: **Locate in Library** |
| Navigation | Select the **platform Library** destination (above the divider). Do **not** open a Library tab on the mini-app |
| Focus | Existing typed identity (`fp1`+kind, KnowledgeHit snapshot+locator, Contribution tuple, or `research_ref` on the research surface). Do not copy/register a new kind |
| Unsaved preview | Do not invent an fp1. Offer Save on the owning rail if that rail has save; else keep transient |
| Return | Client **return location**: previous interior (mini-app / Authoring / Copilot / Home), viewport, selection. **Not** a `psess:` field. Tabs are not durable |
| Backend | `facade_get` / `library.search` / CT-44 retrieve against the focused identity |

## 6. Per-rail verb matrix

Promoted from `research/13-library-lifecycle.md` §3. Status:

- **owned** — parent already names the behavior; chrome calls it
- **UI-only** — destination, label, return, badges; no new backend object
- **deferred** — honest unsupported chrome; revisit condition named

A generic Library verb that ignores `hit_class` is a collapse.

### 6.1 Artifact (`fp1` + Workbench AD-3 kind)

| Verb | Status | Contract |
| --- | --- | --- |
| Preview | owned | B-15 resolve / as-of read. Recipe preview ≠ export ≠ stream |
| Open | owned | Resolve fp1. Opening a definition does not replace a running instance |
| Use / invoke | owned | Consume saved artifact by fp1 (parent AD-10 mode 1) |
| Reference | owned | `selected_refs` kind `artifact` |
| Save | owned | Registration writes fp1. Ungoverned projection is return-value only until save |
| Fork | **deferred** | Closest owned: derived dataset = **new** fp1 + CT-07, **not** a Library kind. **Revisit after facade e2e** |
| Unavailable | owned | B-15 `unavailable` / missing as-of |
| Stale | owned | `stale_evidence_severity`; as-of is the source instant |
| Deleted / tombstone | owned | CT-07 `supersedes`. Never silent other version |
| Upgrade | owned | New fp1 / successor edge. Rename does not change identity |
| Rollback | owned | Restore prior fp1 is a read of history. Software rollback cannot undo fills (parent AD-14) |
| Import / export | owned | Pack export is host AD-18/AD-30. CSV ingest is CT-15, not a Library store |

### 6.2 Knowledge (snapshot + locator)

| Verb | Status | Contract |
| --- | --- | --- |
| Preview | owned | `retrieve` against **pinned** snapshot |
| Open | owned | retrieve/cite. Open ≠ live-tree substitution |
| Use | owned | Citation as evidence; never a governed seat |
| Reference | owned (this companion) | After `cite`: kind `artifact` + Knowledge provenance on the chip. No kind `knowledge` |
| Save | owned | `cite` copies bytes (durable Citation). Not a registry kind |
| Fork | **deferred** | Cite is a byte copy, not a corpus fork. No write-back. **Revisit after facade e2e** |
| Unavailable | owned | missing binding / locator |
| Stale | owned | `StaleSnapshot` |
| Deleted | **deferred** | corpus file removed vs snapshot retained; cite-copy may still exist. Revisit after facade e2e |
| Upgrade | owned | New snapshot; old pin stays; re-pin is explicit |
| Rollback | owned | Stay on pinned snapshot |
| Import / export | owned | Bind `root_path` to a KnowledgeSource; no copy of Stats into QMX |

### 6.3 Contribution (live tuple)

| Verb | Status | Contract |
| --- | --- | --- |
| Preview | owned | Descriptor + five listing axes. Not a run |
| Open | UI-only as inspect | Contribution open ≠ grant ≠ opened-app mint ≠ invoke. Mini-app open is `instance_id` + `psess:`, not a Library object |
| Use / invoke | owned | Envelope ∩ GrantRecord ∩ health. Pin revalidates. Disable → `unavailable`; uninstall → `tombstone`; never another version |
| Reference | owned | kind `contribution` |
| Save | owned | Pin is **not** save. Enable publishes. Session-granted is AD-8, not a pack state |
| Fork | **deferred** | Side-by-side pack versions are not “fork this contribution into a new kind.” **Revisit after facade e2e** |
| Unavailable | owned | availability after disable/leave-roster |
| Stale | owned | stale pin / `availability_revision` mismatch refuses invoke |
| Deleted / tombstone | owned | uninstall → `tombstone`. GC when pin leases empty. In-flight pinned runs keep starting bytes |
| Upgrade | owned | pack migrations prepare/commit/rollback or `forward_only` + operator confirmation. Failed validation restores last usable roster |
| Rollback | owned | last usable roster; pin does not resolve to another version |
| Import / export | owned | same pack export scanner; rewrite secrets to typed refs |

Installed ≠ enabled ≠ session-granted. One green “available” bit is refused.

### 6.4 Hypothesis (`research_ref`) — off facade

| Verb | Status | Contract |
| --- | --- | --- |
| Preview | owned | `restore_hypothesis` / `project_layout_demo`. Viewing cited seed does **not** mint `research_ref` |
| Open | owned | host blob read by `research_ref` |
| Use | owned | Stage 0 never sizes, never emits CT-23, never seats. Graduation is `graduate_to_governed`, not Library use |
| Reference | owned | kind `research_ref` |
| Save | owned | explicit `save_authored_hypothesis` / host persist. View ≠ save |
| Fork | **deferred** | Graduation is collapse, not fork. **Revisit after facade e2e** |
| Listing / browse-all | **deferred** | save/read-by-ref exists; **no** directory listing API. **Revisit after facade e2e** |
| Unavailable | owned at inspect | missing blob → invalid `research_ref` |
| Stale / deleted / rollback UI | **deferred** | label vs newer seed; blob GC unspecified as a Library action. Revisit after facade e2e |
| Upgrade | owned | new `research_ref` on save of new canonical bytes |
| Import / export | owned | blobs stay under `research_root`; not seed `root_path`; not in pack transcripts |

**Revisit gate for every deferred fork / hypothesis-listing row:** live HTTP `facade_search` adoption (`E2E_ADOPTION_CLOSED` becomes true) plus an explicit operator ask. Until then the chrome shows **unsupported** with the typed identity, not a fake CRUD.

### 6.5 UI-only (all rails)

Library destination in the platform rail; return-location chip; filter chrome that names `hit_class` and AD-3 kinds; empty/loading/failed/unavailable/tombstone; keyboard; Locate in Library; published vs granted vs healthy **badges** (data owned, layout UI); copilot preview of a widget/result **before** it has a saved identity (offer save only if the rail supports it).

### 6.6 Still not Library objects

Graph Templates, Skills, Routines, JobHandles, QMA staging / `change_request`, mini-app instances, `view:*`, STRATS packages, recipe **definitions**, Project/Workspace, study-03 Apps/Widgets/Workflows/Datasets/Results/Tools/Files catalogue.

Dependencies / lineage: CT-07 `supersedes`, ExperimentSpec successor edges, cite provenance, recipe release lineage. Derived datasets have a lineage edge and still are **not** a Library kind.

## 7. Closure traces (architecture, unexecuted)

### T-R6-01 — File / image upload

Operator attaches a local image on Home (no instance). Host calls `stage_artifact`. Daemon possesses complete bytes, returns fp1. Composer chip kind `artifact`. Client hash alone never enables Run. Later invoke still needs exactly one `instance_id` ref.

### T-R6-02 — Dataset / version

Pointer to an already-stored dataset uses kind `dataset` (or artifact/run if that is the stored identity). Not a path. Stale/unavailable badge from listing/as-of. Remote job: stage or refuse (J-UI-09).

### T-R6-03 — App instance

Chip kind `instance_id`. Cross-app reference keeps histories and grants separate (J-UI-04). Zero or many instance refs on invoke → `INVALID_INPUT`. Kind absent at `34c148b` until FEAT-0058-class amend.

### T-R6-04 — Widget result

Message-to-copilot adds **chrome context** only. Reconnect may drop it (layout not durable). Save registers artifact or run; then kind `artifact` or `run`. View/filter JSON never becomes a selected ref.

### T-R6-05 — Knowledge citation

Pin snapshot → cite → copied bytes + fp1. Chip kind `artifact` with Knowledge provenance. Library Knowledge rail unchanged; Artifact rail does not gain a cite-copy hit. Unpinned retrieve → `StaleSnapshot`.

### T-R6-06 — Missing / deleted

Library and composer show `unavailable` or `tombstone`. Invoke refuses that identity. No silent other version (J-UI-05, parent AD-30). Surrounding draft remains.

### T-R6-07 — Partial remote transfer

Staging to a remote placement is interrupted. Completeness `partial`. No unauthorized leftover. Resume or refuse (P1-PLC-003). Do not invoke against partial. Do not silently finish on local disk.

### T-R6-08 — Locate in Library / return

From a mini-app preview of a saved artifact: Locate → platform Library focuses `fp1`+kind → Return restores the mini-app interior, viewport, and selection. No new object. No `psess:` layout write.

## 8. Backend adds / reuse

| Item | Owner | Class vs `34c148b` |
| --- | --- | --- |
| `stage_artifact` | COMP-QMA-DAEMON | **add** (absent); reuse artifact register / `before_artifact_register` |
| CT-44 cite | COMP-QMA-DAEMON | **reuse** |
| `facade_search` / `facade_get` | COMP-QMA-DAEMON + WIRE | reuse in-process; **add** HTTP query door |
| QMB `library.search` | COMP-QMB | **reuse** |
| `selected_refs` kind `instance_id` | COMP-QMA-DAEMON + WIRE | **adapt** DEC-0463 |
| Hypothesis browse-all | COMP-QML | **deferred** (after facade e2e) |

No new sqlite. No Library row cache. Client layout/return location is local.

## Sources

- `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/ARCHITECTURE-SPINE.md` (local AD-7, AD-10)
- `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/research/13-library-lifecycle.md`
- `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md` (parent AD-2, AD-3, AD-8, AD-13, AD-18, AD-30)
- `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-review-2026-09-23/REVIEW.md` (R6)
- `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/03-EXPERIENCE-SCOPE.md` (UX-03, UX-05)
- Inspect: `.worktrees/integration-inspect/qmx-agents/packages/qma-daemon/src/qma/daemon/sessions/product_session.py` (`SELECTED_REF_KINDS`); `knowledge/service.py` (`cite`, `ArtifactCopy`)
