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

## 0. Locked defaults (Codex R6)

| Lock | Rule |
| --- | --- |
| **Possession first** | Initial possession is on the **authenticated local daemon**. Home may stage **before** an instance exists. That yields a **local-complete fp1**. It is **not** a remote placement. |
| **Then transfer** | When instance / execution placement is known and is not this daemon: explicit host command `transfer_artifact` (or refuse). Destination **verifies hash**. Never silent local fallback. |
| **Byte transport** | Authenticated **HTTP PUT** `/artifacts/stage` with **Content-Length**. Same pairing auth as queries (`Authorization: Bearer pairing:<id>`). **Not** a JSON-RPC body. **Not** REST `/invoke`. **Not** a UI BFF. |
| **Max size** | Registry row `registry:artifact.stage_max_bytes`. Oversize PUT refuses; no object. |
| **Interrupted v1 PUT** | **Refuse.** No resume. No partial fp1. Daemon **deletes** the incomplete object. Retry is a **new PUT of full bytes** (new staging attempt). Same content hash **may reuse** an already-complete object. |
| **Completeness proof** | Daemon-recomputed hash **plus** byte count after it holds complete bytes. Browser hash is not possession. |
| **Knowledge cite** | After CT-44 `cite`: composer kind remains **`artifact`**. No kind `knowledge`. Library verb matrix unchanged. |

## Honesty at `34c148b`

| Claim | Fact |
| --- | --- |
| `SELECTED_REF_KINDS` | `{artifact, research_ref, contribution, template, dataset, run, attempt, node_ids}` — **no** `instance_id`, **no** `knowledge`, **no** `local_path`, **no** `upload_bytes` |
| kit `instance_id` kind | Specified DEC-0463; **absent** in code |
| CT-44 `cite` | **Present.** Copies bytes, returns `Citation` + `artifact_ref` / `content_fp1`. Cite-copy is **not** an ArtifactHit |
| `stage_artifact` / HTTP PUT `/artifacts/stage` | **Absent.** Backend add (local AD-22). Byte channel is PUT, not JSON-RPC |
| `transfer_artifact` host command | **Absent.** Backend add. Explicit remote placement after local possession |
| `registry:artifact.stage_max_bytes` | **Specified here.** Absent at inspect |
| `facade_search` concatenate | Types + in-process tests; **not** live HTTP; `E2E_ADOPTION_CLOSED = False` |
| QMB `library.search` | **Present** (fp1 + kind). Occupancy `query` |
| Hypothesis listing on facade | **Refused.** `qml.research` has save/read by `research_ref`; **no** browse-all |
| Library UI | **Absent** |

DEC-0286 stands.

## 1. Closed `selected_refs`

Parent AD-8 kinds plus kit `instance_id` (DEC-0463). Nothing else.

| Kind | Id | Notes |
| --- | --- | --- |
| `artifact` | content fp1 | Durable bytes the host **possesses**. A local-complete fp1 is local possession, not remote placement. Provenance metadata may ride **on** the chip; it is not a second kind |
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
| file / image upload | `selected_refs` kind **`artifact`** fp1 **after** a **complete** PUT `/artifacts/stage` on the local daemon | Browser-computed hash is **not** possession. Home may attach with **no** instance. Result is **local-complete** fp1, not remote placement. Do not mint `upload_bytes` / `local_path` |
| existing stored file | kind **`artifact`** / **`dataset`** / **`run`** as the stored object already is | Pointer to an already-stored identity. Machine path is not a portable id |
| Knowledge citation | CT-44 `cite` returns copied bytes + `artifact_ref` / `content_fp1`; composer kind remains **`artifact`** | Chip **shows Knowledge provenance** (`source_ref`, `snapshot_ref`, `locator`, evidence label). **Do not mint** kind `knowledge`. Cite-copy is not an Artifact-rail Library hit |
| widget result **message-only** | **chrome context** on the conversation (view_id, snapshot cursor, filters) until **Save** | After Save: kind **`artifact`** or **`run`**. Never persist view/filter JSON as a selected ref |
| app instance | kind **`instance_id`** | Kit add. Cross-app reference does not merge histories or union grants (J-UI-04) |
| research | kind **`research_ref`** | Viewing cited seed does not mint `research_ref`. Save is explicit `save_authored_hypothesis` |

Message-only widget refs die with chrome (tab/layout not durable). Save is an explicit operator act on the **owning** rail. Ungoverned projection remains a return value until save (Workbench AD-5).

Cross-app: composer on `psess:` A may cite B’s artifact/instance. Authority stays A’s GrantRecords. Unavailable B is labelled; the draft remains.

## 3. Ingest owner — local possession, then transfer (local AD-22)

Chosen design: **initial possession on the authenticated local daemon**, then **explicit transfer** to execution placement when instance/placement is known. Not target-bound staging before the first upload. Home may attach first.

### 3.1 Local possession — HTTP PUT `/artifacts/stage`

| Field | Contract |
| --- | --- |
| Owner | **COMP-QMA-DAEMON** |
| Transport | Authenticated **HTTP PUT** `/artifacts/stage` with **Content-Length**. Body = raw bytes. **Not** a JSON-RPC body. **Not** REST `/invoke`. **Not** a UI BFF (local AD-12). Same daemon HTTP origin as snapshot queries |
| Auth | Same pairing proof as queries: `Authorization: Bearer pairing:<id>`. Paired Origin. MCP/json-render/native frames **must not** PUT; host chrome does. Not a GrantRecord pack-op |
| Max size | `registry:artifact.stage_max_bytes`. Missing Content-Length, oversize, or unpaired Origin → refuse; no object |
| Store | Existing artifact registration path (`before_artifact_register` / content fp1). **No new sqlite class.** Not a Workbench AD-3 kind unless a later register on that rail says so |
| At `34c148b` | **Absent.** Knowledge `cite` already copies through `before_artifact_register` into an in-memory `_artifacts` map — that is the pattern to reuse, not a Library database |
| Instance | Staging **does not** require `selected_refs` kind `instance_id`. Home may stage first. Result is a **local-complete fp1**. It is **not** a remote placement. **Run** of those bytes later still needs exactly one `instance_id` |
| Client hash | Advisory progress only. Browser hash ≠ possession |
| Completeness proof | After the daemon holds **complete** bytes: daemon-recomputed hash **plus** byte count. That pair is possession. Inventory of a possessed object is `complete` (later `missing` / `expired` per parent AD-26). v1 does **not** emit a composer-visible `partial` fp1 |
| Interrupted v1 PUT | **Refuse.** No resume. No partial fp1. Daemon **deletes** the incomplete object. Retry = a **new PUT of the full bytes** (new staging attempt). If a **complete** object with the same content hash already exists, reuse that object — do not mint a second fp1 for the same complete bytes |
| Return | durable fp1 + byte count + completeness `complete`. Composer then CAS-inserts `selected_refs` kind `artifact` |
| Forbidden | JSON-RPC body bytes; inlining bytes on InvocationEnvelope; treating a local path as global id; hashing in the browser and skipping the daemon write; resume of a partial; treating local-complete fp1 as remote possession |

PUT is the named **byte channel**. Pack invoke stays `dispatchInvoke` / InvocationEnvelope. Queries stay HTTP GET. Commands stay JSON-RPC WebSocket. Pairing HTTP stays `/pair/*`. This PUT does not mint a fourth protocol family and does not grant tools.

### 3.2 Explicit transfer — `transfer_artifact`

When the operator later selects an instance whose execution placement is **not** this local daemon:

| Field | Contract |
| --- | --- |
| Command | Host command `transfer_artifact` (CT-40, **not** a pack op, **not** `dispatchInvoke`) |
| Input | Local-complete fp1 + destination placement / instance |
| Destination | Verifies **hash** (and byte count) on arrival. Incomplete destination object is deleted; no runnable remote ref |
| Success | Placement possesses the same fp1. Invoke may cite it **on that placement** |
| Failure / refuse | Typed refusal. Local fp1 remains local-complete. **Never** silent local fallback (J-UI-09, P1-PLC-002). Remote failure does not rewrite the ref into a laptop path |
| Interrupted transfer | Destination has no complete object. Do not invoke remotely against local-only possession. Do not finish the run on local disk |

If the selected instance runs **on this daemon**, no transfer is required; the local-complete fp1 is already on the execution placement.

`stage_artifact` (PUT) and `transfer_artifact` are backend **adds**. UI depends on them. The UI must not invent an upload BFF or a REST invoke API.

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

### T-R6-01 — Home attach, later remote instance

1. Operator attaches a local image on Home. **No** `instance_id`.
2. Host issues authenticated **HTTP PUT** `/artifacts/stage` with Content-Length and `Authorization: Bearer pairing:<id>`. Not JSON-RPC.
3. Daemon holds complete bytes, recomputes hash + byte count, returns **local-complete** fp1. Composer chip kind `artifact`. Client hash alone never enables Run.
4. Operator later selects a **remote** instance. Local fp1 is still not remote possession.
5. Host command `transfer_artifact` (or typed refuse). Destination verifies hash. Invoke may then cite the fp1 **on that placement**.
6. Remote failure does **not** silently run locally. Later invoke still needs exactly one `instance_id` ref.

### T-R6-02 — Dataset / version

Pointer to an already-stored dataset uses kind `dataset` (or artifact/run if that is the stored identity). Not a path. Stale/unavailable badge from listing/as-of. Remote job: `transfer_artifact` or refuse (J-UI-09). Local-complete is not remote placement.

### T-R6-03 — App instance

Chip kind `instance_id`. Cross-app reference keeps histories and grants separate (J-UI-04). Zero or many instance refs on invoke → `INVALID_INPUT`. Kind absent at `34c148b` until FEAT-0058-class amend.

### T-R6-04 — Widget result

Message-to-copilot adds **chrome context** only. Reconnect may drop it (layout not durable). Save registers artifact or run; then kind `artifact` or `run`. View/filter JSON never becomes a selected ref.

### T-R6-05 — Knowledge citation

Pin snapshot → cite → copied bytes + fp1. Chip kind `artifact` with Knowledge provenance. Library Knowledge rail unchanged; Artifact rail does not gain a cite-copy hit. Unpinned retrieve → `StaleSnapshot`.

### T-R6-06 — Missing / deleted

Library and composer show `unavailable` or `tombstone`. Invoke refuses that identity. No silent other version (J-UI-05, parent AD-30). Surrounding draft remains.

### T-R6-07 — Interrupted PUT leaves no runnable ref

1. Home attach starts PUT `/artifacts/stage`. Connection drops before Content-Length bytes arrive.
2. Daemon **deletes** the incomplete object. **No** fp1. **No** partial runnable ref. Completeness is not `partial` on the composer.
3. Retry is a **new PUT of the full bytes**. If a complete object with that content hash already exists, reuse it.
4. A later interrupted `transfer_artifact` likewise leaves **no** complete object on the destination. Local-complete fp1 (if any) stays local. Do not invoke remotely. Do not silently finish on local disk (P1-PLC-003, J-UI-09).

### T-R6-08 — Locate in Library / return

From a mini-app preview of a saved artifact: Locate → platform Library focuses `fp1`+kind → Return restores the mini-app interior, viewport, and selection. No new object. No `psess:` layout write.

## 8. Backend adds / reuse

| Item | Owner | Class vs `34c148b` |
| --- | --- | --- |
| HTTP PUT `/artifacts/stage` (local possession) | COMP-QMA-DAEMON | **add** (absent); reuse artifact register / `before_artifact_register`. Not JSON-RPC body |
| `registry:artifact.stage_max_bytes` | COMP-QMA-DAEMON registry | **add** (absent) |
| `transfer_artifact` (explicit remote placement) | COMP-QMA-DAEMON | **add** (absent); destination hash verify; or refuse |
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
