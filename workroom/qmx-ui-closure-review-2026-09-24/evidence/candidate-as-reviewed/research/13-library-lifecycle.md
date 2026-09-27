# UX-05 Library — shared resource discovery, not a new backend object type

**Sitting:** architecture-QMX-UI-2026-09-23  
**Role:** research only. Not architecture. Not a taxonomy. Not an implementation brief.  
**Inspect:** `integration@34c148be404a375cbfd79fd4ce6997452e4f1d20` via `C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect` (story 59.5). Parent honesty constants in that tree still name `270e992` as the pre-ContributionHit inspect SHA. Docs checkout is `main@92279dfe`.  
**DEC-0286 stands:** class, fixture, and package-test existence is not e2e product surface.

## How to read this file

| Tag | Meaning |
|---|---|
| **law** | Parent sitting rule (Workbench, mill, Workflows). Binds this UI sitting unless `02-CURRENT-DIRECTION.md` **U** supersedes chrome. |
| **code@34c148b** | What the inspect tree actually contains. |
| **specified-not-e2e** | Types/fixtures/tests exist; `E2E_ADOPTION_CLOSED` is false; no live UI. |
| **U** | Current user direction for this sitting. |
| **proposal** | Assistant or this report’s recommendation. Not ratified. |
| **unresolved** | Open for the UI architecture candidate. Do not fill by inventing a kind list. |

Do **not** treat `LIBRARY-ADAPTATION.md` (2026-09-16) as current. It is superseded by `QML-EXPANSION.md`. That first distill’s “adapt to STRATS as a language / two-rail Library as the product” is dead. The mill is Stage 0 on `qml.research`; STRATS is a KnowledgeSource corpus, never a Library kind.

Do **not** adopt study 03’s catalogue (`Apps / Widgets / Workflows / Datasets / Results / Tools / Files`). That study was withdrawn. `02-CURRENT-DIRECTION.md` Library row: **no accepted final taxonomy.**

---

## 1. Existing typed hits and which APIs exist at 34c148b vs specified

Parent law (Workflows AD-2 / `COPILOT-AND-APPS.md` Artifact Library / DEC-0415 / DEC-0449): product discovery **concatenates typed hits**. It is never a fourth store, never a door **run**, never `COMP-LIB`, never a copied-row sqlite. UI may show one Library chrome. It **must not collapse kinds.**

### 1.1 The four rails (identity stays split)

| Rail | Hit / listing | Identity | Search owner | On Library facade? |
|---|---|---|---|---|
| Artifact | `ArtifactHit` `{hit_class: artifact, fp1, kind}` | `fp1` + Workbench AD-3 kind, or query-hit tags `saved-view` \| `analysis.published` | COMP-QMB `library.search` (B-15 + ledger merge + Experiment Ledger refs) | Yes |
| Knowledge | `KnowledgeHit` `{hit_class: knowledge, source_ref, snapshot_ref, locator}` | Snapshot + locator. Durable detail requires a **Citation** after `cite`. Cite-copy `artifact_ref` is **not** an Artifact-rail hit | COMP-QMA-DAEMON CT-44 | Yes |
| Contribution | `ContributionHit` `{hit_class: contribution, plugin_id, point, qualified_id, package_id, package_version}` (+ `availability_revision`, `availability`) | Live `published_contributions()` tuple. **Never fp1, never a registry kind, never `ArtifactHit.kind`.** Pin = `(qualified_id, package_version, availability_revision)` | COMP-QMA-DAEMON `published_contributions()`; DTO COMP-QMA-WIRE additive CT-40 | Yes (third class) |
| Hypothesis | **refused** on the facade | `research_ref` (fp1-shaped class `qml-research-hypothesis`). Not a registry kind | `qml.research` / host `research_root` blobs | **No.** Listing surface name is `qml.research` |

Hypothesis is a **fourth listing surface**, not a fourth federated hit class. KnowledgeHit display aliases must not say `hypothesis` or `research candidate` (UX-DR2). Viewing cited seed does not mint `research_ref`.

Refused forever on this DTO: `hit_class: strats`, `qml_candidate`, Graph Template / Skill / Routine / staging / JobHandle / Project / Workspace as Artifact kinds, `view:*` as a ContributionHit (GAP-0081), mini-app as a registry kind.

### 1.2 Artifact kinds that **are** Library objects (Workbench AD-3 — unchanged)

Kind owner: `COMP-QMF-REGISTRY`. Shared objects cited by `fp1`:

| Kind token | Contract |
|---|---|
| `bot-definition` | CT-33 |
| `confluence` | CT-34 |
| `strategy-family` | CT-06 |
| `book-definition` | CT-22 |
| `bms-definition` | CT-27 |
| `book-binding` | CT-28 |
| `split-manifest` | CT-12 |
| `source-observation` | CT-10 |
| `performance-result` | CT-32 |
| `experiment-spec` | CT-47 (coordinated lane only) |

Query-hit tags (not registry kinds): `saved-view`, `analysis.published` (QMB search also spells the latter `analysis-publication`; federated mapping folds it to `analysis.published`).

**Not** Library objects (projection may mention them only as query hits or not at all): QMA staging / RefinementProposals, JobHandles, Graph Templates, Skills, Routines, derived datasets, recipe **definitions**, mini-app instances, contributions, hypotheses, STRATS packages, logic-source-manifests (cited from CT-33), Project/Workspace.

### 1.3 APIs at `34c148b` vs specified

Honesty split: Workflows honesty docs freeze **270e992** as “ContributionHit not on the wire.” That is still the named inspect SHA inside the code (`FEDERATED_HIT_INSPECT_SHA = "270e992"`, `CONTRIBUTION_HIT_WIRED_AT_INSPECT_SHA = False`). **This sitting’s inspect is 34c148b**, where stories 52–53 (and pack fixtures 58.5) have landed as **types, concatenate services, and tests**. `PackLifecycleFixture.E2E_ADOPTION_CLOSED` is `False`. Fixtures are not a running Library UI.

| Surface | Specified (parent) | code@34c148b | Missing / honesty |
|---|---|---|---|
| `qmb.library.search` | Search by kind + optional `fp1` over three query surfaces; occupancy `query`; no fourth store; no staging read | **Present.** `qmb.registryread.search.search_library`; CLI `library.search` (`qmb/src/qmb/doors/cli/__init__.py`). `LibraryHit` identity is `fp1`. Occupancy `query` | Ranked/semantic stays GAP-0073 (not this API). No UI. Autocomplete/resolve is B-15 `RegistryReadPort` over one as-of set |
| B-15 as-of | Immutable `registry_as_of` set; dated pointers; `supersedes` (CT-07); stale evidence severity | **Present.** `qmb.registryread.as_of` + `port.py` | UI chrome for as-of / zone is unspecified |
| CT-44 Knowledge | `search` / `retrieve` / `cite` against a **pinned** `snapshot_ref`; hybrid → `unsupported-capability`; uncopied snapshot → `StaleSnapshot` | **Present.** `KnowledgeService` in `qma-daemon/knowledge/service.py`; `PlainFileLibrarySource.search/retrieve`. Cite copies bytes, returns `Citation` + `artifact_ref` that is **not** an ArtifactHit | No hybrid index (GAP-0073). No write-back into the corpus. Browse/cite without pin is refused (story 49.3 law) |
| Federated `facade_search` / `facade_get` | Concatenate Knowledge + Artifact + Contribution. Occupancy **none**. Daemon never `import qmb`; QMB never opens daemon sqlite | **Types + service present.** CT-40 query enum includes both names (`query.v1.schema.json`). `FederatedDiscoveryService.search` concatenates three injected ports. Artifact port is a Protocol of `{fp1, kind}` rows | No daemon HTTP query dispatcher file was found that routes `facade_search` into a live listener. Concatenate tests inject stand-in ports. **Not e2e.** Ranked/semantic refused |
| `published_contributions()` | Live roster query; pack `contributes` `{point, local_id}` expand at enable; `availability_revision` publishes with roster swap | **Present** on `PluginLoader.published_contributions()` (in-memory `_published` list + revision). Concatenate maps rows with `qualified_id` to `ContributionHit`; singleton rows without `qualified_id` are skipped | Listing overlay (`ContributionListingService`) is a query overlay with five independent axes. A hit is not a grant |
| Contribution pin / tombstone | Pin tuple; invoke revalidates; disable → `unavailable`; uninstall → `tombstone`; never another version; never stale fp1 | **Types + tests + usage examples present.** `ContributionPin`; `ContributionPinService` in `plugins/pins.py`; SCN-0018 tests. Pack lifecycle **fixture** reuses the same pin/invoke | `PACK_LIFECYCLE_WIRED_AT_INSPECT_SHA` still false vs 270e992; fixture `E2E_ADOPTION_CLOSED = False` |
| `qml.research` | Stage 0 types; `research_ref`; host blob store; listing **off** Library facade | **Present as a pure module** (`qml/src/qml/research/`): `Hypothesis`, `mint_hypothesis`, `save_authored_hypothesis`, `restore_hypothesis`, `project_layout_demo`, dictionary helpers. Host persist: `qml.host.research_store.save_research_hypothesis` / `read_research_blob` under `research_root`. QMA must not write this root in v1 | **No `browse()` function in `qml.research`.** No directory listing API over `research_root`. Sitting catalog publishes a representative descriptor `qml.research.browse` (requires `snapshot_ref`) — that is a door-matrix example, not a federated hit and not a hypothesis index. Librarian is optional Skill/Graph Template over `search`/`retrieve`/`cite` + Stage 0 helpers, not a wizard |
| `view:*` / UI contribution | Wire DTO only until GAP-0081 | **Present as refusal.** `register_ui_widget_contribution` always returns GAP-0081 deferred. `view:*` is not a ContributionHit | Chrome later. json-render / MCP Apps: `stores=False`, `executes=False` |
| Library UI pages | GAP-0081 | **Absent.** `ui@af66288` has no Library pages. `qma-ui-contract` is a stub | This sitting’s job is chrome over existing hits, not a new store |

### 1.4 Identities the chrome must keep separate (Workflows AD-13)

| Thing | Identity | Must not be shown as |
|---|---|---|
| Artifact | `fp1` + kind | A contribution, a hypothesis, a mini-app |
| Knowledge cite | `source_ref` + `snapshot_ref` + `locator` (+ Citation after cite) | `fp1` Artifact; Stage 0 hypothesis |
| Contribution | `(qualified_id, package_version)` live tuple; pin adds `availability_revision` | `fp1`; registry kind |
| Hypothesis | `research_ref` | Library facade row; CT-33 |
| Mini-app instance | `instance_id` on plugin-install row | Registry kind; Library object |
| Graph Template | `(qualified_id, version)` from plugin at enable | Artifact fingerprint |
| Recipe definition | `(recipe_def_id, recipe_def_version, recipe_def_hash)` | Release `fp1`; Library kind (CT-06 recipe deferred) |
| Recipe/derived output | release `fp1` + CT-07 lineage | The definition |
| Product session | `psess:` | QMA `sess:`; a tab |
| Pack states | installed ≠ enabled ≠ session-granted | One “available” bit |

`product_session.selected_refs` closed kinds at 34c148b: `artifact`, `research_ref`, `contribution`, `template`, `dataset`, `run`, `attempt`, `node_ids`. Layout/widget/json-render trees are refused as selected refs. Referencing is not a Library kind mint.

---

## 2. UI chrome: one Library surface over typed hits that MUST NOT collapse kinds

**law** (`COPILOT-AND-APPS.md`): “UI may show one ‘Library’ chrome over typed hits. It must not collapse kinds.”  
**U** (`02-CURRENT-DIRECTION.md`): Library is **shared resource discovery and reuse, accessible from apps**. Types / ownership / location / version / lifecycle / unavailable / deleted / deprecated remain **to design**. No accepted final taxonomy.  
**U** (`03-EXPERIENCE-SCOPE.md` UX-05): discover / search / filter; preview source / version / location; open / use / reference / save / fork where appropriate; dependencies / lineage; unavailable / stale / deleted; upgrade / rollback; import / export. **Library navigation is not a new universal backend object type.**  
**U** (D-015): platform destinations above the rail divider exist independently of opened apps. Do not give each app an isolated copy of Home / Library / Authoring.

### 2.1 What one chrome is allowed to do

- One **platform destination** named Library (see §4). Same destination from Home, Main copilot, and any mini-app.
- Search/filter that **keeps `hit_class` visible**. Concatenate is a query fold, not a unified row cache (`refuse_unified_row_cache` / `refuse_copied_row_library_index` at 34c148b).
- Per-hit inspector that shows the **owning identity** (fp1 / snapshot+locator / published tuple / `research_ref` if the research surface is linked, not folded).
- Contribution listings that show **five independent axes**: published, configured, granted, reachable, healthy. Collapsing those into one green “available” is refused (`refuse_collapsed_listing_status`).
- Knowledge vs Artifact vs Contribution vs Hypothesis as **different result kinds**, even if the filter chip is “all”.
- Locate-existing vs save-new as **different actions** (S-06; study 03 stated this and was still rejected as a taxonomy — keep the distinction, drop the catalogue labels).

### 2.2 What one chrome must not do

- Mint `COMP-LIB`, a Library sqlite, or a “database” store. Operator “database” in the origin transcript was a **seed slogan**, thinned: upgrade is **discovery**, not a new database (C-06; confirmation rubric).
- Register hypotheses, skills, graph templates, mini-apps, widgets, recipes, or `strats` as Artifact kinds.
- Treat a ContributionHit as an Artifact or as a grant. Discovery ≠ invoke.
- Show Knowledge locators as `fp1`.
- Show cite-copy `artifact_ref` as an Artifact-rail hit.
- Imply ranked / semantic search (GAP-0073).
- Imply that listing a headless pack’s contribution is a mini-app page.
- Use study 03’s Apps/Widgets/Workflows/Datasets/Results/Tools/Files as law.

### 2.3 Filters that already have owners (do not invent a parallel ontology)

| Filter the UI may offer | Backed by |
|---|---|
| Artifact kind (AD-3 roster) | `library.search(kind=…)` |
| Query-hit tags saved-view / analysis.published | same, mapped on the facade |
| Knowledge `source_id` + pinned `snapshot_ref` | CT-44; pin first |
| Contribution `point` / `package_id` / availability | `published_contributions()` + listing overlay |
| Hypothesis class / origin | `qml.research` types only, **off facade** |
| As-of instant / zone | B-15 as-of; not a new index |

`instance_id`, grants, and health are **not** Library kinds; they are overlays on contributions / sessions.

---

## 3. Preview / open / use / reference / save / fork / unavailable / stale / deleted / upgrade / rollback

UX-05 lists these as coverage. Ownership is **per rail**. A generic Library verb that ignores kind is a collapse.

Legend: **owned** = parent already names the behavior; **code@34c148b** = implemented at inspect as library/fixture (not UI); **UI-only** = chrome/return/label, no new backend object; **unresolved** = this sitting must not fake it.

| Verb | Artifact (`fp1`) | Knowledge (snapshot/locator) | Contribution (live tuple) | Hypothesis (`research_ref`) |
|---|---|---|---|---|
| **Preview** | **owned:** B-15 resolve / as-of read; saved-view is a citation of a CT-32, not a new kind. Recipe **preview ≠ export ≠ stream** (AD-31) is not an Artifact kind | **owned:** `retrieve` returns cited bytes against the **pinned** snapshot. LAYOUT-DEMO is a read-only projection of cited bytes; viewing it is not a save | **owned:** listing is not invoke. Preview of a contribution is descriptor/health, not a run | **owned:** `restore_hypothesis` / `project_layout_demo`. Viewing cited seed does **not** mint `research_ref` |
| | **UI-only:** copilot preview pane (`rrUMAlEq`) is not Library identity | same | same | same |
| **Open** | **owned:** resolve `fp1` through B-15. Opening a definition does not replace a running instance (UX-05 dimension) | **owned:** retrieve/cite. Open ≠ live-tree substitution | **unresolved as “open app”:** mini-app open is `instance_id` + product_session, **not** a Library object. Contribution open ≠ grant | **owned:** host blob read by `research_ref`. No list-all-hypotheses API |
| **Use / invoke** | **owned:** consume saved artifact by fp1 (AD-10 mode 1). Analysis projection/query vs door **run** occupancy | **owned:** Citation as evidence; never governed seat | **owned:** invoke through AD-3 envelope ∩ GrantRecord ∩ health. Pin revalidates. Hit is not a grant. Disable/uninstall → typed `unavailable`/`tombstone` | **owned:** Stage 0 never sizes, never emits CT-23, never seats. Graduation is `graduate_to_governed`, not Library use |
| **Reference** | **owned:** `selected_refs` kind `artifact` + fp1 id; composer chips are UX | **UI-only** until a selected_ref kind exists for citations; Knowledge is not `artifact` | **owned:** `selected_refs` kind `contribution` + `qualified_id`/`package_version` | **owned:** `selected_refs` kind `research_ref` |
| **Save** | **owned:** registration writes `fp1`. Ungoverned projection is **return value only**, not durable, not a Library object. Governed saved-view homes: sidecar vs daemon `analysis.published` (Workbench AD-5) | **owned:** `cite` copies bytes (durable Citation). Not a registry kind | **owned:** pin is **not** save. Enable publishes. Session-granted is AD-8, not a pack state | **owned:** explicit `save_authored_hypothesis` / host persist. View ≠ save |
| **Fork** | **unresolved as a Library verb.** Closest owned: derived dataset = **new** fp1 + CT-07 lineage, **not** a Library kind (Workbench AD-13). Bot identity must **not** fork on writer (QL). QMA may register a `dev`-zone candidate with a predecessor edge; it must not assemble CT-33 | **unresolved.** Cite is a copy of bytes, not a fork of the corpus. No write-back | **unresolved.** Side-by-side pack versions allowed; that is not “fork this contribution into a new kind” | **unresolved.** Graduation is collapse, not fork |
| **Unavailable** | **owned:** B-15 `unavailable` / missing as-of member | **owned:** missing binding / locator | **owned:** availability `unavailable` after disable/leave-roster; invoke of pin refuses, never retargets | **code@34c148b:** missing blob → invalid `research_ref` |
| **Stale** | **owned:** `stale_evidence_severity` on RegistryReadPort; as-of is the source instant, never query time | **owned:** `StaleSnapshot` when snapshot bytes were not retained or pin does not match. Retrieve never silent-substitutes live tree | **owned:** stale pin / cursor refuses invoke (AD-17). Availability revision mismatch | **unresolved UI:** label a restored hypothesis vs newer seed snapshot |
| **Deleted / tombstone** | **owned:** CT-07 `supersedes` in the as-of set (newer replaces older). Not a soft-delete table | **unresolved:** corpus file removed vs snapshot retained. Cite-copy may still exist | **owned:** uninstall → `tombstone`. GC only when pin leases empty. In-flight pinned runs keep the bytes they started with | **unresolved:** blob delete / GC not specified as a Library action |
| **Upgrade** | **owned:** new `fp1` / successor ExperimentSpec edge (`branches-from`). Display rename does not change identity | **owned:** new snapshot; old pin stays. Re-pin is explicit | **owned:** pack states + migrations `prepare/commit/rollback` or `forward_only` with operator confirmation. Failed validation restores last usable roster. Side-by-side versions | **owned:** new `research_ref` on save of new canonical bytes |
| **Rollback** | **owned:** software rollback **cannot undo fills** (AD-14). Restore as-of / prior fp1 is a read of history, not time-travel of live seats | **owned:** stay on pinned snapshot | **owned:** last usable roster; pin does not resolve to another version | **unresolved UI:** restore previous `research_ref` blob |
| **Import / export** | **owned:** pack export/import are **host** operations (AD-18/AD-30). Independent `ExportScanReport` is the oracle; `exports_secrets: false` is not evidence. CSV/file import is CT-15 ingest, not a Library store | **owned:** bind `root_path` to a KnowledgeSource; no copy of Stats into QMX | **owned:** same pack export scanner; rewrite secrets to typed refs | **owned:** research blobs stay under `research_root`; not seed `root_path`; not in pack transcripts |

### 3.1 Extra verbs UX-05 names that are already owned elsewhere

- **Dependencies / lineage:** CT-07 `supersedes` and ExperimentSpec successor edges; recipe release lineage to definition + input revisions; cite provenance (`source_ref`, `snapshot_ref`, `locator`, `content_fp1`). Derived datasets have a lineage edge and still are **not** a Library kind.
- **Installed ≠ enabled ≠ granted:** Workflows AD-13 / AD-30. UI that shows one “installed” for all three is a collapse.
- **Headless:** a pack with no views still appears as ContributionHits / workflow steps. Library must not hide it for lack of chrome (GAP-0081).

### 3.2 What is UI-only

- The Library **destination** in the platform rail, return-location chip, filter chrome, empty/loading/failed states, keyboard.
- “Locate in Library” from a preview (`NJidF6Tg`) focusing an existing identity without copying it (S-06).
- Copilot preview of a widget/result **before** it has a saved identity: offer save only if that rail supports save; do not imply it is already a Library object.
- Showing published vs granted vs healthy as badges (data is owned; layout is UI).

### 3.3 What remains unresolved (do not fill with a new kind)

- A generic **fork** command across rails.
- Hypothesis **directory listing** / search over `research_root` (save/read by ref exists; browse-all does not).
- Whether Library chrome **links** to the `qml.research` surface as a separate tab/filter, or only federated three-class results (parent: hypotheses stay off the facade; UI may still **navigate** to research without folding the DTO).
- Collections / favorites / shared-vs-private (study 03 questions; not law).
- Mini-app definition vs configured instance vs run as Library rows — they are **not** AD-3 kinds; instance is plugin-install; run is CT-32 / JobHandle / experiment ref.
- Recipe-definition browsing (not a Library kind; CT-06 deferred).
- Import UX for arbitrary files as “Library items” (ingest is CT-15 / Knowledge bind, not a universal object).
- Live HTTP `facade_search` adoption (`E2E_ADOPTION_CLOSED = False`).
- GAP-0081 view contributions as searchable Library hits (refused until named increment).

---

## 4. How Library opens from a mini-app (proposal: platform destination, not a new object)

**proposal (this sitting’s default, matching U):** Library is a **platform destination above the rail divider**, the same way Home, Main Agent, and Authoring are. Opening it from a mini-app does **not** mint a Library object, a per-app database, a tab-owned store, or a `product_session` field. It **selects the existing platform destination** and, when the caller had a typed identity, **focuses that hit**.

### 4.1 Dictation (binds intent; layout not frozen)

`NJidF6Tg` (short label on the highlighted control):

> “this can help s go from preview mode to library”

`JHZj5SdT` (same control, then correction):

> “This can help us go from preview mode to library. Now, the library is more like a database for the application. Now, QMX Global and I think a mini app library, but I think QMX Global Library is the best. Okay, so QMX Global Library, I think, can open up as a tab here on top anywhere in any mini app. **Or actually, no, no, no**, I think it when I use that, for example, if I am to click on top of this, what will happen on this blue thing I've highlighted? What will happen is that we go back to the sidebar and we just have okay, we are transferred to the sidebar.”

Sequence that binds:

1. Preview (widget / result / mini-app canvas) has a control to **go to Library**.
2. Operator names **QMX Global Library** as better than a per-mini-app library.
3. Operator **rejects** “open as a tab on top of the mini-app.”
4. Operator **corrects** to: jump to the **sidebar** (platform rail / shared destinations).

`02-CURRENT-DIRECTION.md` U: platform destinations above the divider exist independently of opened apps; opened apps use shared platform resources. Library row: shared discovery, accessible from apps.

D-015: do not give each app an isolated copy of Library infrastructure.

S-06 (experience-storyboard, **proposal** not U): “Locate in library” selects the global library destination, focuses the existing object, retains a labelled **return** to the app/detail. A transient result without a saved identity offers an explicit save path only if supported.

### 4.2 Mapping onto backend (no new object)

| UI move | Backend |
|---|---|
| Click “locate in Library” on a saved artifact preview | Navigate to platform Library; `facade_get` / `library.search` by `fp1`+kind; do not register a new kind |
| Same on a knowledge preview | Focus KnowledgeHit; require pinned `snapshot_ref`; do not mint `research_ref` |
| Same on a contribution / tool chip | Focus ContributionHit; do not treat as grant; do not fingerprint onto Artifact rail |
| Same on an unsaved preview | Do not invent an fp1. Offer save on the **owning** rail if that rail has save; else keep it transient |
| Return to mini-app | Client return location. Not a `product_session` field. Tabs are not durable (AD-8: tab/layout not durable) |
| Library with no app open | Legal. Platform must work with zero opened apps (U) |

Mini-app **open** remains instance navigation below the divider. Library **open** is platform navigation above it. Mixing those is the tab idea the operator crossed out.

---

## 5. Conflicts: “mini-app library” vs global library (dictation)

| Claim | Source | Status |
|---|---|---|
| Library is “a database for the application” | `JHZj5SdT` | **Thinned.** Origin “upgrade = database” was a seed, not a sixth store (C-06, confirmation rubric). **law:** upgrade is discovery over existing stores |
| QMX Global Library **and** a mini-app library | `JHZj5SdT` first pass | **Superseded in the same breath.** Operator: Global is best, then **no tab**, go to sidebar |
| Library as a tab on top of any mini-app | `JHZj5SdT` | **Rejected by the operator in-dictation** |
| Jump to sidebar / platform rail | `JHZj5SdT` correction + `NJidF6Tg` control | **Current U**, aligned with D-015 and `02` platform destinations |
| Study 03 typed catalogue inside the app chrome | withdrawn study | **Rejected.** Keep “typed hits + inspector” as a **behavior** idea; discard that taxonomy and that layout |
| Per-app Library storage | implied by “mini-app library” | **Conflicts** Workbench AD-3, AD-16 (no new sqlite), AD-1 (no COMP-LIB), federated concatenate (no copied-row index) |
| Hypothesis / workflow / mini-app as Library kinds | various assistant drafts | **Conflicts** AD-2 / AD-3. Workflows = Graph Template / Task Graph / ungoverned call, none of which are Library kinds. Mini-app = installed instance |
| Federated three-class search **is** the global Library | parent AD-2 | **law** for discovery. Chrome may **link** to `qml.research` without putting hypotheses on the facade |
| ContributionHits invisible in Library chrome | OD-03 (operator never asked) | Parent default: **show typed hits**. Do not hide contributions unless this sitting’s operator says so |
| Librarian wizard | mill / research_surface | **Optional** Skill/Graph Template. Not a required Library page. Tab-close cancels nothing |

### 5.1 What this sitting should not reopen

- Workbench AD-3 kind roster.
- ContributionHit as fp1.
- Hypotheses as federated hits.
- A sixth COMP or Library database.
- Study 03 taxonomy.
- LSE as a Library layout (LSE ML Studio UI is already rejected as a layout model).

### 5.2 What this sitting still owes (chrome only)

- Exact sidebar vs overlay **motion** (operator invited thoughtful transitions; coordinates not frozen).
- Return-location presentation.
- Whether the Library destination includes a **linked** research pane (off-facade) or only the three federated classes plus an explicit “open in research” action.
- Locate vs save copy for each rail, with honest empty states when save is unsupported.
- Filters that name **hit_class** and AD-3 kinds, not a new universal type enum.

---

## Sources (absolute paths)

- `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/COPILOT-AND-APPS.md`
- `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md` (AD-2, AD-13, AD-17, AD-18, AD-30)
- `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-14/ARCHITECTURE-SPINE.md` (Workbench AD-3)
- `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-16/LIBRARY-ADAPTATION.md` (superseded)
- `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-16/QML-EXPANSION.md`
- `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md`
- `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/03-EXPERIENCE-SCOPE.md`
- `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/evidence/storyboard-text.md` (`NJidF6Tg`, `JHZj5SdT`)
- `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/decisions.md` (D-015, D-028)
- Inspect tree: `C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect/` — `qmb/src/qmb/registryread/{library,search,as_of,port}.py`; `qmx-agents/packages/qma-wire/src/qma/wire/{federated_discovery,contribution_pin,contribution_listing}.py`; `qmx-agents/packages/qma-daemon/src/qma/daemon/{discovery/federated.py,discovery/listing.py,discovery/research_surface.py,knowledge/service.py,plugins/loader.py,plugins/lifecycle.py,sessions/product_session.py}`; `qml/src/qml/research/`; `qml/src/qml/host/research_store.py`
