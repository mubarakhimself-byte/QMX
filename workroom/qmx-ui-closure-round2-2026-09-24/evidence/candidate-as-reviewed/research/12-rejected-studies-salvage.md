# Rejected studies 01/02/03 — salvage and leak fence

**Sitting:** architecture-QMX-UI-2026-09-23  
**Date:** 2026-09-23  
**Status:** research only. Studies 01, 02 and 03 are **not** a layout, visual, interaction or implementation baseline. Inspect them only to extract salvageable ideas and name errors to avoid.  
**Authority:** `workroom/qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md` supersedes the studies. Original Excalidraw images and full dictation remain the layout foundation. Later Codex, dashboard and n8n references add context; they do not replace that foundation.  
**Wayfinding:** unfinished tickets in `evidence/session/wayfinding/` are scratch trackers. They are **not** acceptance.

This report does not implement, reconstruct, or propose a replacement mock.

---

## How to use this file

| If the spine needs… | Do this |
|---|---|
| Layout geometry | Reconstruct from the original board (`JHZj5SdT`, `YJYDP26I`, `C39LFtm1`, `rrUMAlEq`) and the OpenBB / VS Code source images. Do **not** copy study HTML. |
| Interaction meaning | Re-evaluate salvage rows below as **proposals**. Keep them labelled P until the sitting accepts them. |
| Visual tokens | Neutral dark shadcn-svelte working baseline. Study palettes stay dead. |
| Runtime policy | XR-01..08 remain proposals. Current direction overrides any historical stack/tool wording in the same draft. |

The assistant owned the study errors. The source was not missing.

---

## What the three studies actually were

None was a QMX screen. All were disposable conversation visualizations with fixture data, no backend, no Reticle verdict, and no production UI change.

| Study | Artifact | What it tried | User verdict |
|---|---|---|---|
| **01** (exploratory) | `experience-v01/` — storyboard S-01..S-08, `whole-experience.html`, design-system/authoring rules, grok-handoff B-01..B-09 | Six-area map; Home / main agent / Research / ML / Library / authoring navigation; always-visible right copilot in the inline model; illustrative Research and ML labels | Broad experience-first direction and shared copilot/independent sessions were later accepted. Individual scene behaviors were **not**. Layout already used one three-column shell (`135px` rail + canvas + `205px` assistant) and metadata cards instead of working widgets. |
| **02** | `experience-v02/main-workspace.html`, `tokens.json`, `component-contracts.md` | Main-workspace attachments, next-message vs conversation chips, modal “Attach context” picker, question card, document-only preview, mint-green dark palette | **Rejected:** visual treatment and attachment picker. **Kept for evaluation:** attached-item chips, question pattern, preview concept. |
| **03** (withdrawn) | `experience-v03/app-and-library.html`, interaction-rules, plugin-reference | Research mini-app + Library; permanent 176px local sidebar; Overview/Workflows/Results as left pages; two prose cards as the canvas; plus-menu split; tabbed dock | **Rejected** for changing the layout and substituting text for usable interface space — **not** merely for unattractive colors. Library/authoring had more room to explore; neither study-03 Library nor authoring placeholders are approved. |

Study 03’s own README later said “continue from study 03.” That sentence is historical and **wrong** after the fidelity reset. Current direction: none of the three is an approved implementation baseline.

---

## 1. Explicit reject list

These items are dead. Do not refine them in place. Do not promote them by renaming.

### R-01. Generic three-column shell as the product layout

**Reject:** one imposed interior (`rail + permanent secondary column + workspace`) used for every destination.

- Study 01: `.qmx-shell { grid-template-columns: 135px minmax(0,1fr) 205px }` for Home, agent, Research, ML, Library and authoring.
- Study 02: `.shell { grid-template-columns: 82px 222px minmax(0,1fr) }` even while rail destinations were inert labels.
- Study 03: `.shell { grid-template-columns: 90px 176px minmax(0,1fr) }` with `<aside class="local">` always present; Library reused the same extra column as filter buttons.

**Required instead:** persistent **narrow global rail** (platform destinations above a divider, opened apps below). Selected destination determines the **interior**. Main copilot, mini-app and authoring/ML each have their own composition.

### R-02. Study 02 colors and “design system” sheet

**Reject as QMX defaults:**

| Token | Value | Why it is dead |
|---|---|---|
| `--bg` | `#111416` | User: styling is off / ugly; aesthetics deferred |
| `--surface` | `#191d20` | Same |
| `--accent` | `#abe6ce` (mint) | Same |
| `--accent-bg` | `#233e34` | Same |
| `--waiting` | `#edcd8c` | Same |
| `--error` | `#f4a8a2` | Same |
| `--focus` | `#c3dbff` | Same |
| radius / type / spacing in `tokens.json` | 8px, system-ui 14/22 | Extracted from rejected CSS; not an SDK schema |

D-021 / D-041: a later **neutral dark shadcn-svelte** working baseline is allowed so functional work can proceed. That permission does **not** resurrect these tokens, the mint primary button, or study 03’s grayscale `#f4f4f4` wireframe scaffolding as brand.

### R-03. Permanent secondary sidebar on mini-apps

**Reject:** treating the main-copilot left column (sessions / history / agent settings, source `C39LFtm1`) as a general app-shell requirement.

Study 03 moved Research pages **Overview / Workflows / Results** into `<aside class="local">` and kept that column for Library type filters. Source layout: mini-app navigation sits **above** a large widget canvas; some top controls are optional (`YJYDP26I`). Switching app must change navigation and working composition, not headings inside a cloned sidebar.

A session/history sidebar remains legitimate **on the main copilot only**, unless another destination has its own evidence-based need.

### R-04. Prose cards standing in for widgets

**Reject:** sparse text cards, metadata paragraphs, explanatory study copy, and dashed “design notes” **inside** the product surface.

Concrete study-03 canvas: two `<article class="card">` blocks (“Data coverage”, “Latest saved review”) plus a third card of explanation (“Opened views and execution are separate”). Expanded “detail” rendered `metadata()` — identity, version, origin, availability, and a paragraph of meaning — not a chart, table, or workflow. Study 01 expanded views were `<dl class="qmx-kv">` plus chips.

Source widgets are dense working surfaces: chart, metrics table, controls, different sizes, scrollable detail. Explanations live **outside** the app (study chrome, architecture docs), never as the canvas.

### R-05. LSE ML Studio form as the QMX ML layout

**Reject as layout/model:**

- Left model catalogue grouped Forecasting / Classification / Risk / Deep Learning / Time Series / Sentiment.
- Central fixed **Train** form (dataset, timeframe, date range, horizon, test split, hyperparameters, feature-engineering selectors).
- Separate **Optimise** tab that swaps the rail for Grid Search / Walk Forward / Monte Carlo / etc. and disables run until a trained model exists.
- Right “Model Guide” column as the default ML teaching surface.
- “ML Studio” as a separate rigid application with that chrome.

D-049 / current direction: LSE **capabilities** may inform coverage (dataset/version/split, target, logs, comparison, leakage, GPU, non-trading ML). The QMX surface is the original **app / VS Code-like family**: central graph can contain code, data and model operations; select a node for compact inspection; explicit expand into code / diff / inputs / parameters / outputs / run detail **without losing graph context**; optional right copilot. “ML Studio” is a **working label** for those capabilities, not approval of a third layout.

### R-06. Study 02 attachment picker

**Reject the control, not the need for attachments.**

What was shown: `<dialog id="picker">` titled **“Attach context”**, opened by **“＋ Attach”**, listing a flat sample of file / saved result / ML-studio workflow / unavailable server run. New items defaulted to next-message; a per-chip `<select>` flipped **Next message / This conversation**. One modal treated upload, library object, cross-app workflow and dead server source as the same kind of row.

User (D-022): “I really don’t like the attach thing”; chips after attach are useful; dataset vs app meaning was unexplained; use Codex plus-menu / plugin logic as **research**, not a cloned UI. Native Codex plus menu was **never clicked**. Local plugin manifests established package contents, not picker behavior.

Study 03’s replacement plus menu (Files & images / Library references / Tools & plugins) is a **QMX proposal**, not observed Codex, and it arrived inside a rejected layout. Salvage the **split of meanings**, not the HTML menu.

### Additional rejects (same class of error)

| ID | Reject | Why |
|---|---|---|
| R-07 | Study 02 document-only preview panel as the work-area design | User: preview **concept** is useful; prefer Codex **tabbed** work area. Study 02 preview was a single sheet of prose. |
| R-08 | Study 03 Library taxonomy and inspector as accepted Library | D-028: more room to explore ≠ approval. No final types, ownership, locate vs save, or storage model. |
| R-09 | Study 03 authoring placeholders | User named **n8n** as the authoring reference lead. Study did not reconstruct a graph/code workspace. |
| R-10 | Always-visible app copilot (study 01 inline model) | Shared copilot capability is accepted; a panel is **optional per app**, configurable, not mandatory chrome. |
| R-11 | Codex screenshots as the mini-app layout | They inform preview tabs, launcher, context panel, conversation navigator. They must not displace OpenBB/VS Code app proportions. |
| R-12 | BMAD UX as a UI-session workflow | D-027 / D-031: UX excluded. Architecture and epics/stories remain later pipeline tools. Study 03’s design-system-status BMAD split is not spine law. |
| R-13 | Research / ML / “Research desk” page names as the default roster | Illustrative only. Historical sample apps are examples, not a closed launch backlog. |
| R-14 | HTML studies, Node `--check`, and ZIP hashes as interaction proof | Syntax and packaging ≠ browser geometry, keyboard, or Reticle. File-URL navigation was policy-blocked for study 02. |
| R-15 | Wayfinding tickets 01–05 as done work | Map says “No ticket resolved.” Claimed/open status is not acceptance. |

---

## 2. Salvage list with conditions

Salvage means: **re-propose against the original layouts**. It does not mean copy the study HTML, CSS, page names, or contracts file.

### S-01. Attached-item chips — salvage

**Keep:** a visible, removable chip that names **what the copilot will receive** before send.

**Conditions:**

- Chip identity must distinguish at least: file/image content, dataset/version or query selection, saved result/run, workflow definition vs run, widget/view, app/instance, and selected tools. Study 02 flattened these.
- Show source, snapshot/version when known, and availability. Do not imply the whole dataset was pasted, the app was opened, or a tool was invoked.
- Removing a chip changes **future** context. Sent messages may keep a sent-reference record. Exact retention default (next message vs conversation vs session) stays **open** after D-022; study 02’s next-message default is **not** accepted.
- A chip is not a grant. Attaching does not widen tools, switch workspace ownership, or choose an execution target.

### S-02. Question cards (clarification vs approval) — salvage

**Keep:** a structured wait that belongs to **its conversation**, with choices plus optional free text, no self-submitting answer.

**Conditions:**

- Label **clarification** (information) separately from **approval** (permission for a stated action). Study 02 demonstrated clarification only; do not treat that as the whole pattern.
- Identify waiting task/run and question origin when the backend can say so.
- Switching conversations preserves the pending question, draft and references for that conversation. Answering in the visible app must not satisfy a question owned by another session.
- User: pattern “can work”; not a ratified card layout. Claude-style questioning was mentioned as an alternative, not selected.

### S-03. Preview / tabbed work area — salvage the concept, not the study chrome

**Keep:** inspect an artifact or result **without** losing the source conversation/app, and **without** closing implying cancel.

**Conditions:**

- Prefer a **tabbed work area** (Codex screenshots: browser / Subagents / Review / Terminal / Files / Side chat as **reference**, not a required tab set).
- Opening, focusing, or closing a preview does not edit, install, grant, or stop a run.
- Identify artifact + version/run/snapshot. A newer result is a distinct snapshot.
- App **pages** (Overview-class navigation) and **open detail/work-area tabs** stay different kinds of navigation (P-002; still a proposal).
- Study 02’s single document sheet and study 03’s object-details/document dock (side vs bottom) are **not** the design. Docking geometry remains open.
- Unsupported renderer → labelled fallback, not an empty canvas or a paragraph describing the missing view.

### S-04. Expansion-as-tab — salvage as a proposal to compare, not as law

Current direction already invites this: select once for a compact inspector; **explicitly expand** into a detail tab/work area for code or data; preserve graph viewport, selected node, draft/version and return location; **prototype and compare with the original expansion arrows** before accepting.

**Conditions:**

- Expanded surface must show the corresponding chart / table / workflow / code / diff — never study-03 `metadata()` prose.
- Expanding the same target again focuses the existing detail; comparison views are an explicit later action.
- Return restores source page and usable focus/scroll. Closing detail does not delete the resource or stop the job.
- App sections and open details must remain visually distinguishable even if both use top navigation.
- No universal lossless code-to-graph conversion.
- Do not squeeze the main canvas into a permanent narrow column to keep an inspector always open. A compact inspector is select-then-inspect, not a second permanent sidebar.

### S-05. Composer split: content vs tools vs target — salvage

Current experience-scope (section 4) and study-03 interaction-rules agree on the **meanings**. Rebuild the **entry** as a compact composer control, not the rejected modal and not a claimed Codex clone.

| Path | What it supplies | Must not imply |
|---|---|---|
| **Content** | Selected file/image after preparation; uploaded copy ≠ pointer to an existing file | Broad laptop access; silent substitution of empty content |
| **Resource references** | Dataset/version or query; result+run; workflow definition vs run; widget view; app identity + declared context | Opening the app, merging its history, pasting all rows, executing, placing a widget, acquiring every tool the app uses |
| **Tools / capabilities** | Selection of already available capabilities; connection/readiness visible if applicable | Installation, authorization, external connection, or invoking a tool |
| **Target** (separate from attach) | Where a command will run / which instance is the mutation target | Switching the visible app; attaching a cross-app reference; a local path becoming a VPS path |

**Conditions:**

- Three (or four) paths stay identifiable in the UI. Do not collapse them into one “Attach context” list.
- Provider/tool enablement and execution-target selection remain **named decisions**.
- Unavailable references are explicit. Study 02 blocked send until removal — that recovery policy is **not** accepted; reconnect / retry / exclude remain design options.
- Local plugin.json facts (plugin can bundle skills, `.app.json` connectors, MCP servers) may inform **labels**. They do not prove plus-menu behavior and must not equate plugin = QMX mini-app = connected external app.

### S-06. Independently scoped conversations — already accepted at the broad level

D-017: shared copilot capability; switching apps restores the relevant history; histories are **not** merged; copilot is optional per app.

**Still proposal (do not freeze from studies):** next-message vs conversation retention; whether tools are per-message or per-conversation; exact draft/question persistence across restart (studies only lasted while the HTML page was open).

### S-07. Status dimensions — salvage as language, not as a widget kit

Keep opened-view, running-operation, connection-health, and execution-location **separate** in any status component. An opened app is not “running.” Disconnected is not idle. Closing is not Stop.

### S-08. Contribution rules R-01..R-09 — salvage as a checklist, not a schema

Study 01’s identity / views / inputs / actions / agent-context / runtime / settings / evolution / quality list is a useful **authoring hygiene** list for later contracts. It is not an API, not json-render, and not proof the inspected backend has those fields.

### S-09. Scene intents S-01..S-08 — salvage coverage, not the cards

Home attention vs opened apps; main copilot with preview; mini-app switch/restore; expand/return; discuss-with-chip; locate vs save; draft/preview/activate; upgrade/compatibility. Use them as **coverage obligations** (see also UX-01..UX-12 in the handoff scope). Do not import the mermaid wizard, the Research/ML examples, or the inline model’s chrome.

### S-10. Library as a shared destination — salvage the role, not the wireframe

A platform destination for discover/inspect/reuse, reachable from apps, with locate ≠ save and definition ≠ instance ≠ run. Taxonomy, ownership, version, unavailable/deleted/deprecated handling, and whether storage is one catalogue or many domain-owned stores are **unset**.

### Do not salvage

- Study HTML/CSS/grid.
- `tokens.json`.
- Study 03 Research page set.
- LSE Train/Optimise form chrome.
- “Attach context” modal.
- Always-on copilot.
- BMAD UX DESIGN.md / EXPERIENCE.md as the visual system.
- Conversation-navigator hover/jump/bookmark behavior (screenshot candidate only; official name unverified).
- Any claim that native Codex clicks occurred.

---

## 3. XR-01..08 — useful proposals vs current-direction conflicts

Source: `evidence/session/interaction-runtime-draft.md`. Packet already labels them **proposals, not accepted contracts**. Historical React/Qt stack comparison in that same file is superseded (Svelte + TypeScript working direction; Qt out). That historical stack section is not XR law.

| ID | Title | Verdict | Why |
|---|---|---|---|
| **XR-01** | A view, conversation and operation have distinct lifetimes | **Useful proposal.** Aligns with D-017 and the headless/mixed correction (D-047). | Switching visible app must not cancel a durable run; close ≠ Stop; explicit Stop names an operation; UI cannot promise continuation until worker-vs-service ownership is known. **Wording hazard:** the example “Switching from ML Studio to Research” must not smuggle LSE’s rigid app into the spine. Use two **different app interiors** (graph/code ML workspace vs widget Research) as the example. “ML Studio” remains a capability label. |
| **XR-02** | Connection health is not job state | **Useful proposal.** No contradiction. | View / connection / command-ack / operation / display-freshness stay separate. Transport loss must not invent job Failed. No exactly-once guarantee. After reconnect, refresh then reconcile so old progress cannot overwrite a terminal result. |
| **XR-03** | Execution location and resource location must agree | **Useful proposal.** No contradiction. | Local file ≠ VPS access; no silent retarget, hidden upload, or similarly named dataset swap. Switching the visible app does not retarget an in-flight job. Remote failure must not silently start the same work locally. |
| **XR-04** | Cancel is a request until confirmed | **Useful proposal.** No contradiction. | Cancellation requested ≠ cancelled. Completion can win the race. Lost connection → uncertainty, not fake success. Decorative Stop when cancellation is unsupported is forbidden. |
| **XR-05** | Expansion preserves the object being examined | **Useful proposal; compare before accepting.** Does **not** contradict current direction; it **is** the invited mechanic. | Matches “select → compact inspector; expand → detail tab; preserve viewport/selection/version/return.” **Conflicts only if** the spine treats it as already chosen, skips comparison with original expansion arrows, or implements expansion as study-03 metadata prose. Filter-propagation into an already expanded view stays per-detail-contract. |
| **XR-06** | An attachment states what it supplies | **Useful proposal for meanings; picker is rejected.** | File / dataset / app-reference / widget-selection meanings survive. Enabling a connector/tool is a separate decision. Resolve availability before use; keep unavailable identity in the conversation. **Do not** import study 02’s modal, flat list, or next-message default. Lifetime/defaults remain open (D-022). Plugin manifests still do not prove Codex plus-menu. |
| **XR-07** | Conversations share capabilities without merging histories | **Broad direction already accepted (D-017).** Remaining bullets are still proposals. | Restoring the selected conversation on app change, keeping drafts/questions with their conversation, and routing results by identity rather than whichever panel is open: **useful**. Cross-app reference must not merge histories. Shared Library items may still have independent versions and permissions. Exact schemas/deployment/retention are **not** ratified by D-017. |
| **XR-08** | Heavy computation has an explicit execution boundary | **Useful proposal.** No contradiction. | Frontend shows bounded summaries, progress and requested slices. No unbounded event queues or mounting every row. Native/Rust is a measured-bottleneck candidate, not a rewrite. Does **not** revive Qt. Does **not** promise a speed win from Tauri. |

**None of XR-01..08 is currently in contradiction with current direction** if they stay labelled proposals and XR-01/XR-05/XR-06 keep the wording hazards above. They **would** contradict if the spine:

- freezes expansion-as-tab without the arrow comparison,
- ships the study-02 picker as XR-06,
- treats “ML Studio” as LSE’s Train/Optimise application,
- or copies the draft’s historical React/Qt recommendation.

---

## 4. What MUST NOT leak into the new architecture spine

The spine may **cite** these studies as rejected history. It must not **depend** on them as geometry, tokens, contracts, roster, or proof.

### Layout and chrome

1. One three-column product shell.
2. Permanent generic secondary sidebar on mini-apps (including study 03’s 176px `local` column and Library-as-the-same-column).
3. App pages parked on the left instead of app-owned top navigation.
4. Overview / Workflows / Results as the default mini-app IA.
5. Always-visible app copilot.
6. Study notes, dashed callouts, or “what this would be” paragraphs inside the canvas.
7. Prose cards, metric-less `<dl>` blocks, or `metadata()` as widget or expanded-detail implementations.
8. Codex preview/navigator screenshots replacing OpenBB/VS Code app proportions.
9. Frozen coordinates from any HTML study (or from Excalidraw — user allows thoughtful navigation/expansion improvement).
10. A universal page template because some top controls are reusable.

### Visual system

11. `experience-v02/tokens.json` and its mint/dark CSS custom properties.
12. Study 03 grayscale wireframe (`#f4f4f4` / `#222` / `#aaa`) as identity.
13. Study 02 “View design system” sheet as DESIGN.md.
14. Any claim that D-041 (neutral dark shadcn baseline) rehabilitates rejected palettes.

### ML / authoring

15. LSE Train / Optimise form, model-catalogue rail, and prerequisite-disabled Optimise tab as QMX ML IA.
16. “ML Studio” as a separate rigid application in the destination model.
17. Every model becoming a trade.
18. Study 03 authoring placeholders, or n8n as a dependency (reference lead only).
19. Lossless arbitrary code ↔ graph round-trip.

### Composer / attachments

20. Study 02 `<dialog id="picker">` / “Attach context” / “＋ Attach” as the component.
21. One list that treats files, datasets, apps, plugins and dead servers as the same attachable.
22. Next-message vs conversation `<select>` as ratified retention policy.
23. Block-send-until-remove as the unavailable-source product rule.
24. “We observed the Codex plus menu.” We did not.
25. Plugin = mini-app = connected external app = MCP server.

### Contracts, proof, process

26. `component-contracts.md` as existing APIs or SDK shapes.
27. Scene cards S-01..S-08, open questions O-01..O-08, or backend questions B-01..B-09 as accepted architecture (they are coverage/questions).
28. Wayfinding map or tickets 01–05 as acceptance.
29. HTML fixture journeys as e2e, Reticle, or backend validation.
30. Node `--check` or ZIP hashes as UI verification.
31. BMAD UX workflow, Figma, paid dashboard kits, or Stitch/Superdesign as blockers/dependencies.
32. Book/BMS as the shape every future composition must wear.
33. Every capability requiring a UI, a service, a graph node, or a workflow.
34. Paper trading as a platform-wide gate.
35. json-render or MCP Apps as mandatory host architecture (evaluate as adapters).
36. Historical backend inventory (`34c148b`) or origin-transcript commands as current implementation.
37. Study 01 grok-handoff sequence as the sitting’s work plan (Grok already owns this architecture pass; implementation is later factory lanes).
38. React as the working frontend (superseded). Qt as a UI kit (excluded).

---

## Errors to avoid on the next reconstruction

These are the **method** failures, independent of any one widget.

1. **Source was sufficient; application failed.** Re-read images at full resolution and the full bottom dictation. Do not “fix” a missing spec that was not missing.
2. **Do not excuse layout change as “low-fidelity wireframe.”** Hierarchy, geometry, density and meaningful content are required even in a prototype. Color deferral is not layout deferral.
3. **Do not impose the main-copilot interior on mini-apps.** Sessions/history sidebar is copilot-specific.
4. **Do not let a later reference overwrite an earlier layout authority.** Codex → preview/conversation controls. OpenBB/VS Code → app canvas. LSE → ML **coverage**, not chrome. n8n → authoring mental model, not a shipped editor.
5. **Do not put explanations in the product.** Study controls belong in study chrome or in this research folder.
6. **Do not ratify by drafting.** Permission to explore, a claimed Wayfinding ticket, or a portable ZIP is not acceptance.
7. **Do not clone a competitor control you did not operate.** Screenshots and `plugin.json` are not click-evidence.
8. **Do not ship a generic shell and rename the headings.** Switching app must change navigation and working composition.
9. **Do not reconstruct from study 03 “with better colors.”** The fidelity reset forbids using it as a baseline to refine.
10. **Show a second genuinely different app composition** before claiming the shell is differentiated (main copilot vs widget mini-app vs graph/code authoring/ML).

---

## Source trail

| Claim | Source |
|---|---|
| Studies are not a baseline; 03 rejected for layout + text-heavy surfaces; 02 picker/aesthetics rejected; 01 exploratory | `02-CURRENT-DIRECTION.md` “Evidence limitations and superseded material” |
| Differentiated interiors; LSE form rejected; expansion-as-tab to compare with arrows; Svelte/shadcn-svelte; Qt out | same file, Layout / Stack sections |
| Study 03 departures vs source | `evidence/session/layout-fidelity-reset.md` (workroom packet; sitting `evidence/` not copied) |
| D-017, D-021..D-028, D-041, D-047..D-049 | `evidence/session/decisions.md` |
| User reject of attach picker, colors; keep chips/questions/preview; want mini-app + Library | `session-visible-messages.md` user turn `01a0cdec-…` |
| User reject of study 03 layout; BMAD UX out of this UI session | same file, user turn `01a0cdf8-…` |
| LSE UI off; graph/code workspace + node expansion | same file, user turn `01a0ce50-…` |
| Study 02 picker/tokens | `experience-v02/main-workspace.html`, `tokens.json`, `README.md` |
| Study 03 sidebar + prose cards + plus split | `experience-v03/app-and-library.html`, `interaction-rules.md` |
| LSE Train/Optimise observation | `live-research/quantx-lse-minara.md`, `evidence/origin-context/ml-reference-notes.md` |
| XR-01..08 text | `interaction-runtime-draft.md` |
| Composer split as current ask | handoff `03-EXPERIENCE-SCOPE.md` §4 |
| Tickets unresolved | `wayfinding/map.md` |

No study HTML was executed for this report. No new mock was produced.
