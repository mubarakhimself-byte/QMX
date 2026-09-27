# Existing frontend scan — QMX repo family

**Sitting:** architecture-QMX-UI-2026-09-23  
**Date:** 2026-09-23  
**Status:** research only. No worktree created. No application code changed. No process killed.  
**Question:** is there a real QMX frontend to integrate against, or only docs and disposable HTML?

---

## Verdict

**There is no real QMX frontend.** No first-party Svelte/Vite/Tauri/web app exists in git history or in the inspected checkouts. The named `ui` branch at `af66288` is an August 2026 BMad epics-and-stories freeze (23 epics / 131 stories over the QMF+QMB+QML PRD), not a Svelte app and **not** the new UI integration base. What looks like UI is:

- self-contained HTML design studies (rejected or exploratory)
- archived BMAD UX / Stitch / Refero research HTML
- August 2026 research write-ups in HTML
- a Python **stub** (`qma-ui-contract/STUB.md`) plus wire DTOs (`view:*`) with **no chrome**
- third-party clones under `workroom/reference/` (not QMX)

**No running QMX UI was found.** Vite/Svelte/Tauri ports were not listening. Node processes on this machine belong to Codex CUA / Node.js, not a QMX dev server. `.reticle/` contains only a `.gitignore`.

If a dedicated UI integration checkout is created later, recommend **`C:/Users/Mubarak/Desktop/QMX/.worktrees/ui-integration`**, branched from **`integration@34c148be404a375cbfd79fd4ce6997452e4f1d20`**. Do **not** reuse `.worktrees/ui`. Do **not** create it in this sitting.

---

## Inspection pins

| Checkout | Path | HEAD | Branch | Dirty? |
|---|---|---|---|---|
| Operator root | `C:/Users/Mubarak/Desktop/QMX` | `92279dfe43922d60fabe38e29284ca52956ab75c` | `main` | **yes** (docs/planning; UX tree moved to archive; this sitting’s artifacts untracked) |
| Backend inspect | `C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect` | `34c148be404a375cbfd79fd4ce6997452e4f1d20` | `integration` (tracks `origin/integration`) | clean |
| Named `ui` worktree | `C:/Users/Mubarak/Desktop/QMX/.worktrees/ui` | `af6628888fb8901bf9e877cbd07e438dbb0f39b4` | `ui` | clean |
| Factory leftovers | `C:/Users/Mubarak/Desktop/QMX-worktrees/epic-*` | various | epic/chunk lanes | leftover from 53–59 drain; **not a product UI** |

Packet snapshot (`workroom/qmx-ui-architecture-handoff-2026-09-23/repository-snapshot.json`, captured 2026-09-23T13:07:01Z) already recorded the same three relevant worktrees and this limit: *“Existing ui checkout is not selected as the new UI integration base.”*

`af66288` **is an ancestor of** `main@92279df` (main is 12 commits ahead). The `ui` branch is a frozen August planning point, not a divergent product line. Backend packages (`qmx-agents/`, `qmb/`, `qml/`, `qmn/`, `packages/`) live on `integration`, not on `main` or `ui`.

Other local refs:

- `codex/plan-qmx-ui-design` @ `430fb7d` — later than `ui`, still planning/docs; HTML hits are the same August research write-ups. Not a frontend.
- Factory `_factory/HEARTBEAT.md` (2026-09-20): **QUEUE EMPTY.** Drain 53→59 done. `origin/integration` = `34c148b`. Do not recut leftover epic worktrees as a UI base.

Third-party trees under `workroom/reference/repos/` (OpenBB, jesse, nautilus, FinceptTerminal, …) were **not** treated as QMX frontend. They contain their own `package.json` / TSX / etc.

---

## What was searched

Roots required by this task:

- `C:/Users/Mubarak/Desktop/QMX` (dirty `main` — read only except this report)
- `C:/Users/Mubarak/Desktop/QMX/.worktrees/ui`
- `C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect`
- `C:/Users/Mubarak/Desktop/QMX/workroom/`

Markers: `package.json`, `svelte.config.*`, `vite.config.*`, `tauri.conf.*`, `apps/web`, `*.svelte` / `*.tsx` / `*.vue`, first-party `*.html`, `experience-v01|v02|v03`, `ui-reset-2026-09-23`.

Git: `git log --all -- package.json **/package.json apps/** src/**/*.svelte` returned **empty**. No first-party frontend package has ever been committed.

---

## 1. What exists vs what is a docs/prototype HTML

### 1.1 Real product frontend — **absent**

| Marker | First-party result |
|---|---|
| `package.json` in git | **never committed** |
| `svelte.config.*` / `vite.config.*` / `tauri.conf.*` | **none** (outside `workroom/reference/` and scratch `node_modules`) |
| `apps/web` | **none** |
| `*.svelte` / `*.tsx` / `*.vue` in first-party trees | **none** |
| `qmx-agents` on `main` / `ui` | **missing** (backend is on `integration` only) |
| Runnable UI host | **none** |

The only first-party `package.json` outside third-party clones is scratch tooling:

- `C:/Users/Mubarak/Desktop/QMX/.scratch/qmx-storyboard-tools/package.json` — `lz-string` + `sharp` for Excalidraw/storyboard extraction. Not a product app. Its `node_modules/` is local image tooling.

`adws/adw_data/harness_engineering/{subagents,themeMap}.ts` is **ADW/Pi coding-agent harness**, not QMX chrome.

### 1.2 Backend UI seam — stub + wire DTO, not a UI

On `integration@34c148b` only:

```
C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect/qmx-agents/packages/qma-ui-contract/STUB.md
```

Contents: explicit deferred exclusion (GAP-0081 / AR-Q08). **No** `pyproject.toml`, **no** `src/`, **not** a uv workspace member. `qmx-agents/pyproject.toml` members are exactly `qma-core`, `qma-wire`, `qma-daemon`.

What *does* exist is Python/wire, not screens:

- `qma.wire.view_presentation` — AD-17 `view:*` **DTO**. Comment in source: pack `view:*` is not a plugin contribution point; GAP-0081 chrome is not filled; JSON Render / MCP Apps are adapters, not a runtime.
- `product_session` journal projection — durable app-use/authoring **context**. A tab is not this row; closing a tab writes nothing.
- `research_surface.py` names JSON Render and MCP Apps with `stores`/`executes` = false and `qma_ui_contract: stub`.

This is the integration *boundary*, not a frontend to extend.

### 1.3 First-party HTML — all docs or disposable studies

**A. Current design session (2026-09-23) — disposable studies, not an app**

| File | Bytes | Kind |
|---|---|---|
| `workroom/ui-reset-2026-09-23/experience-v01/whole-experience.html` | 16 247 | Study 01 — portable conversation visualization; fixture data; no QMX connection |
| `workroom/ui-reset-2026-09-23/experience-v02/main-workspace.html` | 29 128 | Study 02 — self-contained; “no installation, server, external fonts, libraries or Codex runtime” |
| `workroom/ui-reset-2026-09-23/experience-v03/app-and-library.html` | 28 902 | Study 03 — **WITHDRAWN**; banner says do not implement |

Identical copies live under `workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/experience-v0{1,2,3}/` (packet snapshot, not a second app).

**B. August 2026 research write-ups (not a product UI)**

Same four files on `main`, `ui`, and `integration-inspect`:

- `workroom/artifacts/2026-08-17-qmf-minimal-core.html`
- `workroom/artifacts/2026-08-17-qmx-foundations.html`
- `workroom/artifacts/2026-08-18-five-locks.html`
- `workroom/artifacts/2026-08-18-three-deep-dives.html`

These are static research documents (`<title>QMX Foundations</title>`, etc.), not shells.

**C. Refero catalog (research, not QMX screens)**

- `workroom/research/2026-09-14-refero-exploration/index.html` — “16 captured references from Refero. These are product screenshots, not QMX mockups.”

**D. Archived BMAD UX (superseded 2026-09-23; do not revive)**

Moved from `_bmad-output/planning-artifacts/ux-designs/ux-QMX-2026-09-01` → `archive/ui-ux-before-2026-09-23/`. Root `_bmad-output/.../ux-designs/ux-QMX-2026-09-01` is **gone** (deletes on dirty `main`). Archive README: *preserved for reversibility, not active design guidance.*

| File | Kind |
|---|---|
| `archive/.../.working/department-layout-prototype.html` | “THROWAWAY UI STUDY” variants A/B/C; simulated data |
| `archive/.../.working/stitch-study.html` | Stitch **image viewer** (`Generated in Stitch · Screens are visual studies`) |
| `archive/.../.working/stitch-initial-export/.../0{1,2,3}_*/code.html` | Google Stitch HTML exports |
| `archive/.../.working/stitch-refined-export/code.html` | Stitch refined export |
| `archive/.../imports/lieflat-charts/templates/*.html` | **Vendor chart skill** templates (Lieflat), not QMX |

**E. Not first-party UI**

- `workroom/reference/repos/**` — cloned donor products (OpenBB, jesse, Fincept, …).
- `.worktrees/mql5-library/data/_probe_23763.html` — scrape probe, out of this sitting’s required roots.

### 1.4 Classification table

| Artifact | Real frontend? | Baseline for new UI? |
|---|---|---|
| Svelte/Vite/Tauri app | No | — |
| `qma-ui-contract` | Stub markdown only | Wire/GAP-0081 seam only |
| `view:*` / `product_session` | Python DTOs / journal | Backend contracts, not chrome |
| experience-v01 HTML | Prototype | Exploratory; not approved layout |
| experience-v02 HTML | Prototype | Visual + picker **rejected** |
| experience-v03 HTML | Prototype | **Withdrawn** |
| Stitch / department / Refero HTML | Prototype / research | Archived or research-only |
| August `workroom/artifacts/*.html` | Docs | Not UI |
| `.scratch/qmx-storyboard-tools` | Image tooling | Not UI |
| `workroom/reference/repos` | Other people’s apps | Donors, not QMX |

---

## 2. The `ui` branch (`af66288`) — old BMad epics, not a Svelte app

**Worktree:** `C:/Users/Mubarak/Desktop/QMX/.worktrees/ui`  
**HEAD:** `af6628888fb8901bf9e877cbd07e438dbb0f39b4`  
**Commit:** `Epics and stories: 23 epics, 131 stories over the PRD FRs (BMad epics-and-stories, validated)` — Mubarak, 2026-08-21.  
**Tracked files:** 491. **Working tree:** clean.  
**Frontend markers in that tree:** none (`package.json` / svelte / vite / tauri / `apps/web` empty).

Top-level at `af66288`: `.vscode`, `_bmad-output`, `_bmad`, `_docwork`, `adws`, `archive`, `docs`, `queue`, `recorder`, `tracker`, `workroom`. No `qmx-agents`, no `packages`, no `apps`.

`_bmad-output/planning-artifacts/epics.md` is a **QMX V1 (Phase 1: QMF + QMB + QML)** epic breakdown. Epic 1..23 are `qmf-core`, registry, data, calendar, indicators, venue, structure, risk, QML authoring/protocol, QMB substrate/run-loop/CLI/sweeps/optimization/robustness/synthetic data. There is **no UI epic**.

Sibling architecture in that worktree is August 2026 spines:

- `architecture-QMX-2026-08-19/`
- `architecture-QMB-2026-08-20/`
- `architecture-QML-2026-08-21/`

HTML in the `ui` worktree is only the four August research write-ups.

**Packet law (already written):**

- `repository-snapshot.json` → *“Existing ui checkout is not selected as the new UI integration base.”*
- `02-CURRENT-DIRECTION.md` / session `decisions.md` **P-005:** existing `ui` is an older August commit; do not assume it or root `main` is the correct base.
- `backend-grounding.md`: the `ui` worktree inventory did not reveal a frontend package.

**Why it cannot be the new UI integration base**

1. It is **~one month stale** vs `integration@34c148b` (Workflows 53–59, QMA/QMB/QML/QMN code).
2. It has **no backend packages** and **no frontend package**.
3. Its only “UI” content is BMad planning for **libraries**, not screens.
4. Reusing the path `.worktrees/ui` would collide with this freeze.
5. `main` has already moved past `af66288`; the interesting code is on `integration`, not here.

`codex/plan-qmx-ui-design` is likewise a planning ref, not an app.

---

## 3. Rejected studies — locations and why they cannot be a baseline

Canonical copies (edit nothing; Codex session owns them as history):

```
C:/Users/Mubarak/Desktop/QMX/workroom/ui-reset-2026-09-23/experience-v01/
C:/Users/Mubarak/Desktop/QMX/workroom/ui-reset-2026-09-23/experience-v02/
C:/Users/Mubarak/Desktop/QMX/workroom/ui-reset-2026-09-23/experience-v03/
C:/Users/Mubarak/Desktop/QMX/workroom/ui-reset-2026-09-23/layout-fidelity-reset.md
```

Packet copies under `workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/`.  
Salvage/leak fence for this sitting: `research/12-rejected-studies-salvage.md` (companion; this scan does not re-litigate salvage rows).

### Study 01 — exploratory, not a baseline

- `experience-v01/whole-experience.html` + `START-HERE.md` + `review-notes.md`
- Local conversation visualization. Fixture data. No backend, trades, jobs, or app activation.
- Review notes: “not a change to the QMX application.” Inline model had some browser checks; the standalone HTML’s styling is **not** visually verified. No Reticle verdict.
- Later accepted: experience-first direction; shared copilot / independently scoped sessions (D-009, D-017). **Not** accepted: individual scene behaviors, always-visible app copilot, Research/ML roster labels, the three-column shell.

### Study 02 — visual treatment and attachment picker rejected

- `experience-v02/README.md` (updated after rejection): *“the user subsequently rejected this visual treatment and attachment picker. Its tokens are not approved QMX defaults.”*
- `review-notes.md`: browser tool **refused** `file:///.../main-workspace.html`; no workaround. Node `--check` on extracted JS is syntax only. No Reticle.
- D-021: do not promote tokens or wireframe scaffolding into the QMX visual system.
- Ideas still **evaluable** (not inherited as structure): attached-item chips, question pattern, preview concept (Codex tabbed work area preferred).

### Study 03 — withdrawn; cannot be a baseline

Read `experience-v03/README.md` (first line) and `review-notes.md`.

README:

> **WITHDRAWN / REJECTED BY USER.** The layout departs materially from the original storyboard and its OpenBB/VS Code references. It is retained as history, not a baseline to refine or implement.

`review-notes.md` limits:

- Source-reviewed prototype only. Native Codex plus-menu was **not** clicked.
- Local-file browser navigation policy-blocked; no workaround.
- Inline JS `--check` ≠ rendering, keyboard, geometry, or Reticle.
- **No production QMX UI code has been changed.**
- Remaining: one app, fixture data, no filesystem, no model, no tools, no persistence, no authoring, no conversation navigator. Not a Codex clone. Does not prove Grok SDK interoperability.

`layout-fidelity-reset.md` (binding correction, not a replacement mock):

- Failure was **layout**, not merely color: generic permanent secondary sidebar, sparse text cards, study chrome inside the product surface.
- Mini-app interiors must change with the application (OpenBB/VS Code relationship: top nav, dense widget canvas, optional right copilot).
- Do not impose the main-copilot secondary sidebar on every destination.
- Study 03 Library and authoring placeholders are **not** approved.
- Next reconstruction was **not** produced in that turn.

`02-CURRENT-DIRECTION.md`: Study 03 rejected for changing the layout and presenting unusable text-heavy surfaces. Study 01 exploratory. **None is an approved implementation baseline.**

### Older BMAD UX / Stitch (also not a baseline)

`archive/ui-ux-before-2026-09-23/README.md`: fresh-start move; **do not load into the new design session.** D-001 excludes old BMAD UI/UX. Generated-layout reactions were later excluded as preference evidence, then a 2026-09-14 review selected some Stitch screens — all of that is **superseded** by the 2026-09-23 reset.

---

## 4. Whether any running UI exists

**Expected: no. Observed: no.**

| Check | Result |
|---|---|
| Listeners on 5173 / 3000 / 1420 / 4173 / 5174 / 8080 | **none** |
| Processes named `vite` / `tauri` / `electron` / `svelte` | **none** |
| `node.exe` | Codex CUA runtime (`...\OpenAI\Codex\runtimes\cua_node\...`) and generic `Program Files\nodejs` — **not** a QMX app |
| `.reticle/` | only `.gitignore` (no sessions, no instrumented app) |
| HTML studies | openable as local files in a browser; **not** a hosted QMX UI; study 02/03 were not even Reticle-verified |
| `qma-daemon` as a UI | Python daemon + wire. Closing a client does not stop agents. That is not a frontend. |

Reticle proof is required **when** a user-facing app exists (D-006). There is nothing to point Reticle at.

---

## 5. Recommended NEW UI integration worktree — **do not create it now**

### Do not use

| Location | Why not |
|---|---|
| `C:/Users/Mubarak/Desktop/QMX` (`main`, dirty) | D-043: **no application code on main**. Root has no backend packages. Dirty planning/docs. Operator checkout. |
| `C:/Users/Mubarak/Desktop/QMX/.worktrees/ui` @ `af66288` | Packet: **not** the new UI integration base. August BMad epics. No frontend, no current backend. |
| `C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect` | Read-only inspect of `integration`. Keep it clean for architecture evidence. |
| `C:/Users/Mubarak/Desktop/QMX-worktrees/epic-*` | Factory leftover lanes (QML/Workflows). HEARTBEAT: do not recut. Not a UI product tree. |
| `codex/plan-qmx-ui-design` | Planning ref, not an app. |

### Recommend (later, not this sitting)

**Path:** `C:/Users/Mubarak/Desktop/QMX/.worktrees/ui-integration`  
**Base:** `integration` at **`34c148be404a375cbfd79fd4ce6997452e4f1d20`** (newest locally visible backend; inspect worktree already pinned here).  
**Branch name:** **not invented here** (D-043: exact UI branch names and merge workflow are unset). When the operator creates one, cut it from that integration SHA, never from `ui@af66288` or dirty `main`.

Why this path:

- Persistent inspect/research worktrees already live under `.worktrees/` (`integration-inspect`, `mql5-library`, old `ui`).
- `C:/Users/Mubarak/Desktop/QMX-worktrees/` is the **factory epic drain** area; leftover `epic-049`…`epic-052` trees are still sitting there. A long-lived UI integration checkout should not look like an epic lane.
- Name `ui-integration` avoids colliding with the occupied `.worktrees/ui`.

Policy notes (do not override):

- **D-032:** a separate worktree is **not required**. Coding is on `integration`; `main` holds consolidated work. P-005 is superseded as a *presumed* workflow.
- **D-043 / packet:** backend integration and **separate UI integration**, then a combined deployment candidate, then `main` after validation.
- **This sitting:** architecture only. P-005 itself said the user asked for advice, not creation. **No worktree was created.**

---

## 6. Workroom files that look like another agent still owns them

**Do not edit.** Listed for coordination only. This scan read; it did not write outside the assigned report path.

### Leave alone — concurrent / other-agent ownership

| Path | Why |
|---|---|
| `workroom/ui-reset-2026-09-23/` **entire tree** | Live Codex UI/UX design session. Packet: Grok returns here for focused review. README still marks `backend-grounding.md` and `video-reference.md` as **agent-owned during initial pass**. |
| `workroom/ui-reset-2026-09-23/backend-grounding.md` | Codex subagent inventory; do not “refresh” in place. |
| `workroom/ui-reset-2026-09-23/video-reference.md` | Same. |
| `workroom/ui-reset-2026-09-23/experience-v0{1,2,3}/` | Study artifacts; v03 withdrawn. History, not a place to patch. |
| `workroom/ui-reset-2026-09-23/live-research/` | Codex browser/reference pass. |
| `workroom/ui-reset-2026-09-23/handoff-working/` | Codex packet-prep working files. |
| `workroom/qmx-ui-architecture-handoff-2026-09-23/` | **Input packet for this sitting.** Codex owns the review destination. Includes ZIP + `.sha256`. Do not mutate the packet. |
| `workroom/qmx-design-session-2026-09-23.zip` | Historical Codex checkpoint ZIP. |
| `workroom/research/2026-09-15_mis-fullread-ideas/` | MIS full-read factory. `IN_PROGRESS_IDEAS.md` says it is **rewritten as extracts land**. `STATUS.md` still says **“Hand to another agent.”** Includes `WORKLIST.json`, `packs/`, `shards/`, `waves/`, `extracts/`, `tools/`. Unrelated to UI; do not touch. |
| `workroom/research/2026-09-15_unbounded-market-intelligence/` | Prior MIS pass; STATUS calls it **not trusted**. Leave it. |
| `workroom/research/2026-09-16_grok-handoffs/` | Library/Workflows architecture prompts (already consumed by later sittings). |
| `workroom/research/2026-09-18_node-editor-architecture/` | Origin Explore / staged Workflows handoff. Historical; other agents’ staging. |

### Concurrent Grok work **outside** workroom (packet: leave its agents/files alone)

| Path | Why |
|---|---|
| `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/` | Pack-and-grant / observability sitting. D-030: *“Grok has finished architecture and is now documenting; it has not started building. Do not interrupt its agents.”* Status unverified in this scan. |
| `C:/Users/Mubarak/Desktop/QMX-worktrees/epic-*` and `_factory/` | Leftover factory lanes. HEARTBEAT: queue empty; do not recut. |
| Dirty files on `main` (`docs/`, `_docwork/`, `archive/ui-ux-before-2026-09-23/`) | Operator checkout. This sitting must not “helpfully” clean them. |

### Safe to **read** as evidence (still do not edit)

- `workroom/ui-reset-2026-09-23/CURRENT.md`, `decisions.md`, `layout-fidelity-reset.md`
- Packet `00-START-HERE.md` … `05-RETURN-FOR-REVIEW.md`
- `archive/ui-ux-before-2026-09-23/README.md` (supersession notice only)

---

## 7. Implications for this architecture sitting

1. **Greenfield frontend** on a **brownfield backend**. Architecture must specify a new Svelte + TypeScript host (working direction D-040) talking to existing `qma-wire` / daemon / libraries. There is no app tree to “resume.”
2. **Do not** scaffold onto `.worktrees/ui` or commit app code on `main`.
3. **Do not** treat study HTML, Stitch exports, or Refero catalogs as the implementation skeleton. Reconstruct layout from the original storyboard + OpenBB/VS Code images (`layout-fidelity-reset.md`). Salvage ideas only via `research/12-rejected-studies-salvage.md`.
4. **GAP-0081 chrome** is still empty. `view:*` and `product_session` are the seams to reuse/adapt; filling chrome is this UI increment’s problem, not proof it already exists.
5. **No Reticle / no running app** until a later coding stage actually boots one — in an isolated checkout, not here.
6. **Do not create** `ui-integration` in this sitting. Recommend the path; wait for operator / Documentation Factory / epics.

---

## Limits of this scan

- No `git fetch`. Remote may have moved past local `origin/integration@34c148b`.
- `workroom/reference/repos/` not inventoried as QMX (donor clones).
- Did not execute HTML in a browser or Reticle (studies already document that gap).
- Did not inspect every leftover `QMX-worktrees/epic-*` file for a hidden `apps/web`; factory HEARTBEAT and `backend-grounding.md` already classify those as backend epic lanes. Spot-check of worktree list names shows QML/Skylos/federated-discovery only.
- Node process list is a point-in-time snapshot on this Windows machine.

**Nothing in this report is an implementation, a worktree creation, or a branch rename.**
