# Session-visible steering for the QMX UI architecture sitting

Research only. Not architecture. Not an implementation brief.

**Authority:** [`02-CURRENT-DIRECTION.md`](C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md) wins any clash with the visible export, the last full assistant answer, `decisions.md` IDs, or this note. The export is 15 user turns captured 2026-09-23 from Codex task `Review QMX UI storyboard`; the active turn is **partial** after the last user message. Images, tool logs, and internal reasoning are not in the export.

**Sources read in full:**

- [`session-visible-messages.md`](C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/session-visible-messages.md) (turns 1–15; last assistant *final_answer* is turn 14)
- [`session-audit.md`](C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/handoff-working/session-audit.md)
- [`CURRENT.md`](C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/CURRENT.md)
- [`decisions.md`](C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/decisions.md)
- [`02-CURRENT-DIRECTION.md`](C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md)
- [`03-EXPERIENCE-SCOPE.md`](C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/03-EXPERIENCE-SCOPE.md)

Turn index (user messages):

| # | Turn id | Export anchor |
|---|---------|----------------|
| 1 | `01a0cd39-1fb2-7262-8c5f-669d6af576ce` | L7 |
| 2 | `01a0cd95-5154-7a11-95dd-ff3f9ed0bc8b` | L84 |
| 3 | `01a0cda3-45ec-7690-bb83-a517095db315` | L182 |
| 4 | `01a0cda5-2463-71f3-9a5a-5f044216d119` | L220 |
| 5 | `01a0cda8-cd80-7512-a442-66d505cdbc10` | L250 |
| 6 | `01a0cdc5-a3f5-7743-852f-abe0d2b4c167` | L324 |
| 7 | `01a0cdd0-fe11-7092-8ce3-7d81296508b5` | L381 |
| 8 | `01a0cdd6-fb46-7802-92ae-ba7a03415699` | L421 |
| 9 | `01a0cdec-884f-75c0-b07b-3f41510e30b6` | L499 |
| 10 | `01a0cdf8-85fa-7c60-b2d4-450cfa684436` | L577 |
| 11 | `01a0ce00-b296-79b3-b7f2-f56f867d8cae` | L634 |
| 12 | `01a0ce0f-2522-7c63-a42d-70356cff64e2` | L691 |
| 13 | `01a0ce22-80c8-71c0-8c6f-f3f6707a23f3` | L789 |
| 14 | `01a0ce37-7979-7280-9c12-e37b015e7f43` | L917 |
| 15 | `01a0ce50-d47e-79e0-9751-f8c86ace1a45` | L1036 |

Legend in `02`: **U** = current user direction (binds this sitting); **P** = assistant proposal to evaluate; **E** = observed evidence.

---

## 1. Turn-by-turn user corrections that bind this sitting

### 1.1 Chronology

**Turn 1 — fresh pass, old BMAD UX out, Excalidraw first.** Start over. Old BMAD UI/UX files “might poison your context.” Ground in the Excalidraw board (“a lot of text, a lot of pictures”). Know the backend because some UI will need backend additions. Keep a durable record in this one session. Lower-end sub-agents for bulk inventory.

**Turn 2 — dictation and live references, not a single journey.** The tell that the dictation was not used: “I didn’t see you going or using browser use.” The suggested “expand widget → discuss → library → return” journey “is missing a lot of things.” Take time. Worktree is a question, not an order: “Just asking. I’m not saying we should.” Expanded-view arrows exist on the board. This becomes **D-007**.

**Turn 3 — reread before resume.** “First read this entire session.” Continuity over restart.

**Turn 4 — continue this session.** Asks what is next if continuing. No new product constraint.

**Turn 5 — experience-first; Grok codes later; layout ~70%.** “I agree with your direction.” Grok implements; this session produces ingestible documents plus transcript. BMAD architecture later, not now. Layout “mostly around 70% sorted.” Need upgrade/copilot-build guardrails. Node editor is a curiosity, not a pick. **D-009–D-013.**

**Turn 6 — platform above the divider; json-render / MCP Apps; copilot variants.** “Opened apps all connect to everything above… the things above are independent of the things below.” json-render is “very, very important”; MCP Apps must be accounted for. Copilot: a powerful main copilot plus optional per-app copilots, *or* “one global with multiple sessions.” Library is under-attended. Authoring needs real design. Grok is expanding the core; treat prior backend inventory as historical. **D-014–D-016.**

**Turn 7 — copilot direction in; this session is UI, not architecture.** Accepts the shared-capability / independently scoped sessions recommendation and reports sending it to Grok. Add attachments, references, and structured user questions. Cross-project reference is a comparison, not a merge of histories. “This session is not for architecture.” App-to-app / workflow-to-workflow communication is a Grok concern. **D-017–D-019.**

**Turn 8 — portable artifacts, fewer questions.** “Just do as you wish, just make sure it’s transferable.” Minimize questions. Grok is not about to ingest this yet. **D-020.**

**Turn 9 — study 02 look and attach picker rejected; show a mini-app and Library.** “I really don’t like the attach thing and also the way you’ve perhaps rendered the entire thing.” Colors/design-system sheet: “This is very ugly.” Attached-item *appearance* is useful; what attaching a dataset or an app *means* is not settled. Preview concept is useful; prefer Codex’s tabbed work area. Question cards can work. Next: an application, then Library. Codex plus-menu / plugins are research references. Permission to *inspect* BMAD UX for a design-system hint (later revoked). **D-021–D-025.**

**Turn 10 — study 03 withdrawn; original layouts bind; BMAD UX out.** “What you’ve designed is very, very different from what I designed.” “In an application, the layout changes.” OpenBB and VS Code images already showed it. “Every time I tell you to use the BMAD skill, you mess up badly… let’s not use it again.” “No, I’ve refused it.” Library/authoring had more room; n8n is the authoring lead they expected to be looked up. **D-026–D-028.** Binding layout (assistant restatement the user did not contradict):

- Main copilot: sessions/history, conversation, preview/work area.
- Mini-app: app-specific top navigation, substantial widget canvas, optional right copilot.
- Widgets: charts, tables, controls, real expansions — not paragraphs describing them.

**Turn 11 — stop circling; what actually blocks implementation.** Storyboard already exists. Tokens feel wasted. Superdesign / Design Arena are optional helpers, not a new planning stage.

**Turn 12 — pipeline, not a worktree; Grok is documenting, not coding; collect a packet.** Established pipeline: brainstorm transcript → Grok architecture → Documentation Factory → epics/stories → coding. “We haven’t reached turned off yet” (handoff). “Grok hasn’t started building yet… finished architecture, now it’s documenting… Don’t interrupt them.” SDK name unverified. BMAD UX stays out; BMAD architecture and epics/stories stay trusted. “Not a work tree, a defined branch”: coding on `integration`, consolidated work on `main`. `DESIGN.md` still open. Component library and shipping the UI are different jobs. **D-029–D-033.**

**Turn 13 — Svelte preference; keep hard interaction here; Qt is only a question; add spin.** “Personally, I don’t really like React… Can’t we use svelte and TypeScript?” Reuse editable shadcn blocks. C++/Qt/Rust and Fincept/OpenBB stacks are research questions, not picks. Installed-product / VPS / ML / adversarial QA are in scope. “Bring your own spin” on navigation and expansions without freezing coordinates. Own `DESIGN.md` is allowed; Stitch/Superdesign optional. Skip BMAD UX. **D-034–D-038.**

**Turn 14 — vision, working stack, Qt out, dark baseline, parallel branches.** Capability-building platform: explore, append, compose, test, reuse, operate. Motivation is compounding via position sizing and risk, not beating HFT on speed. “I just want this thing working.” “QT is not going to come into play.” “Svelt has really won.” Neutral dark shadcn/SaaS-like baseline now; refine later. Zero spend on the React dashboard kit — inspect, don’t buy. No application code on `main`; backend integration and a **separate UI integration** stream, then a combined deployment candidate, then `main` if it works. Hold the full integration review. ML Studio, charts, code diffs, observability/monitoring, Library stay in coverage. Reticle optional *for this Codex agent* in this turn (later superseded for implementation). Historical transcripts are context; embedded commands are not today’s instructions. **D-039–D-046.**

**Turn 15 — latest binding corrections (export ends here).** Annotation 1: “Some mini apps workflows can be UI best, others can be back and best.” Dashboard kit: “I didn’t say we are going to use that… you’re just picking mental models.” Keep original Excalidraw images: “don’t assume just because I gave you access to other things it means we are leaving them out.” LSE ML Studio UI: “this ML studio is bogus no I’m not using this one” — take ML *ideas*, use the original graph/code workspace with right copilot; a node may expand into code/detail. Paper trading: “mini apps I don’t think need paper trading not all of them.” Startup/splash/first-run, credentials/API keys, “CLI proxy for the providers,” terminal, PyCharm/DaVinci Resolve as launch inspiration. Grok gets a packet and does further research/architecture with agent freedom; Codex reviews the return. Parallel: dedicated review of current `integration` while UI work is on a UI integration branch — *this sitting does not start that review or start coding.* Locate existing BDD/Gherkin journeys. **D-047–D-054.** Later supplied AGENTS text (not in the user dictation body, recorded as **D-055** / `02`) requires Reticle for user-facing *implementation*.

### 1.2 Named bindings this sitting must not reopen

| Topic | Binding user direction | First firmly said | Decision id |
|---|---|---|---|
| **Svelte** | Svelte + TypeScript, shadcn-svelte primitives/charts, Svelte Flow is the **working frontend direction**. React kit is not a dependency. | T13 preference; T14 “Svelt has really won” | **D-040**, `02` U |
| **Qt out** | Native Qt/C++ UI is excluded. Rust/Tauri remain *interest/candidates*, not a speed proof. | T14 “QT is not going to come into play” | **D-040**, `02` U |
| **Dark shadcn** | Neutral dark shadcn/SaaS-like baseline is acceptable so work can proceed. Refine identity later. Does **not** revive rejected study palettes or layouts. | T14 “default black sass-like feeling… I just want this thing working” | **D-041**, `02` U |
| **Layouts** | Original Excalidraw images + full dictation are layout authority. Main copilot ≠ mini-app. Mini-app interiors **change with the app**. Shared rail, divider, opened-app icons. Thoughtful improvements allowed; coordinates not frozen. Codex screenshots inform preview/conversation controls only. | T2, T5 (~70%), T10 rejection, T15 “those things are very important for our layout” | **D-012, D-026, D-037, D-048** |
| **Headless** | UI presence, execution location, and run lifetime are independent. Apps/workflows may be UI-first, backend/headless, or mixed. A useful capability need not have a screen. Closing a view is not stopping a durable job. | T6 platform vs apps; T14 workflows without an app open; T15 “UI best… back and best” | **D-015, D-047**, `02` U |
| **Paper-trading scope** | Paper/sim applies where a capability executes trades or materially affects trading/risk. Not a platform-wide week-or-two gate. Non-trading ML, data tools, headless utilities use their own evaluation. | T14 “I don’t know if that’s the journey anymore”; T15 “not all of them” | **D-053**, `02` U |
| **LSE UI rejected** | Do not recreate LSE ML Studio (Train/Optimise forms) as the QMX ML layout. LSE may inform *capability coverage* only. ML workspace = original app/VS Code-like graph/code + optional right copilot + node→detail/code expansion. “ML Studio” is a working label, not a rigid app. | T15 “this ML studio is bogus” | **D-049**, `02` U |
| **Study 03 rejected** | Withdrawn as a **structural** failure (generic shell, permanent extra sidebar, prose cards), not a color tweak. Not a base to polish. Study 02 tokens/scaffolding also rejected. Study 01 is exploratory. Assistant owns the miss; the source was not missing. | T9 (02 look), T10 (03 layout) | **D-021, D-026** |
| **Parallel backend / UI branches** | No application code on `main`. Backend integration and **separate** UI integration, then a combined deployment candidate, then `main` after validation. A worktree is not required. Exact branch names are **not** minted here. Do not interrupt other Grok agents. | T12 branch not worktree; T14 two integration streams; T15 parallel review vs UI work | **D-032, D-043, D-052**, `02` U |

Also binding, even if not in the prompt’s short list:

- **Vision:** extensible capability-building platform. Book/BMS are current default policy implementations, not the only stack. Historical app ideas are not a launch backlog. **D-039.**
- **Copilot (direction only):** one shared platform capability, multiple independently scoped sessions, optional per-app panel, restore-on-switch without merging histories. **D-017.** Schemas/deployment/retention remain P.
- **json-render and MCP Apps** must be *considered*. Their importance does not pick an integration architecture. **D-016.**
- **Pipeline:** this sitting prepares a Grok architecture packet. User controls later Documentation Factory → epics/stories → coding. BMAD UX skipped; BMAD architecture/epics remain usable. **D-029, D-031, D-051.**
- **Zero spend** on the supplied dashboard kit. Free shadcn-svelte is the working component source. **D-044, D-048.**
- **Startup:** splash/first-run, credentials, mentioned CLI proxy, terminal, local/server readiness. **D-050.**
- **n8n** is the authoring *reference lead*, not a dependency. **D-028.**

---

## 2. Assistant proposals still marked P (not accepted)

`decisions.md` still lists many P rows. Several were later accepted, superseded, or killed. Below is the **live** P set for this sitting. Do not treat a live P as user law.

### 2.1 Closed P rows (do not revive as open proposals)

| ID | Fate | Why |
|---|---|---|
| P-003 | Superseded | **D-007:** do not start from one expand→library journey. |
| P-005 | Superseded | **D-032:** worktree is not required; branch workflow instead. |
| P-009 | Accepted as **direction** | **D-017.** Remaining: schemas, deployment, context-retention, per-app defaults. |
| P-016 | Effectively accepted as process | **D-029 / D-051:** packet → Grok architecture → DF → epics → coding. |
| P-017 | Superseded | React default replaced by P-020 then **D-040**. |
| P-020 | Accepted as working stack | **D-040** Svelte + TS + shadcn-svelte + Svelte Flow. Versions, SvelteKit vs Vite, chart/table/editor pins remain unspecified. |
| P-022 | Rejected | **D-040** Qt out. Rust/C++ only at measured boundaries (`02` P, not a Qt UI). |
| P-026 | Accepted as this packet’s method | **D-051.** Not architecture approval. |

### 2.2 Still P — product / experience

| ID | Proposal | Why it is still P |
|---|---|---|
| **P-001** | Main copilot and mini-app as related layouts **inside one shell** | Shared rail is U. “One shell” that flattens interiors is exactly what T10 rejected. |
| **P-002** | App pages and expanded artifact tabs are different navigation kinds | User proposed top tabs for expansion; exact chrome is open (**Q-002**, `02` “Still to design”). |
| **P-004** | Common widget actions and rendering contracts before per-widget design | Reasonable; never ratified. |
| **P-006** | QMX-owned design system + versioned app contribution contract | User wants both *kinds* of artifact. No contract, catalog, or DESIGN.md was accepted. |
| **P-007** | App composition ≠ workflow-logic editing; no lossless code↔graph round-trip | Aligns with later n8n/graph talk; not an accepted rule. `03` §3 repeats it as a proposal. |
| **P-008** | v01 draft: app pages + separate detail tabs, per-app retained context, library return location | Discussion mock only. **D-009** accepted the six-area *direction*, not these behaviors. |
| **P-010** | Evaluate json-render against a QMX catalog; MCP Apps for hosted tool UI; allow coexistence | **D-016** requires the *question*. Integration architecture is unselected. |
| **P-013** | Study 02: next-message vs conversation context; pending questions/drafts per conversation; unavailable-source state | Theme/geometry rejected. These interaction splits were never accepted. |
| **P-014** | Study 03: typed Library, source/version inspector, separate file/resource/tool paths, Research mini-app, tabbed work area | Study 03 withdrawn. Ideas may be re-proposed one by one (**D-028**). |
| **P-015** | Reconstruct source side-by-side; show a second genuinely different app; keep study notes off the product surface | User-forced *standard* after T10, not a signed-off reconstruction (none was built). |
| **P-024** | Origin capability vocabulary (extension / workflow definition / run instance / app composition / widget / resource) | `02` keeps this P: reconcile with current core; do not mint a parallel ontology. |
| **P-025** | Click = compact inspect; explicit Open/Expand = detail tab; preserve graph viewport/selection/version/return | `02` P. Compare with original arrows before accepting. |
| **P-027** | Six independent dimensions: presentation, execution target, invocation, definition/instance, conversation/authority, observation | **D-047:** user accepted UI vs headless vs mixed. The six-way schema is assistant framing to validate. `03` §1 is the same P, written as coverage obligation. |

### 2.3 Still P — runtime, host, delivery

| ID | Proposal | Why it is still P |
|---|---|---|
| **P-011** | Deepen main workspace in five states (start/resume, attach, reference, question, inspect) | Useful coverage list. Not the agreed next build step (T15 sent work to Grok architecture). |
| **P-012** | Portable HTML studies + semantic tokens + Wayfinder map | Process used for v02/v03; not a delivery method going forward. |
| **P-018** | Desktop host evaluated separately from frontend; runnable web proof first; test Python lifecycle before Tauri/Electron/browser-only | Tauri is a candidate only (`02` P). |
| **P-019** | Bounded vertical slice to grow the component kit; do not build an exhaustive library first | Sensible sequencing; this sitting must not treat it as authorization to code. |
| **P-021** | XR-01–XR-08 in `interaction-runtime-draft.md` (view/session/job lifetimes, connection vs execution, local vs remote identity, cancellation acknowledgement, expansion, attachments) | Explicitly “proposals until reconciled/accepted.” |
| **P-023** | Review contracts before coding; promote an identified tested candidate; branch names are not environments | User described a similar merge story. Exact promotion/CI is unselected (`02` P). |

### 2.4 P items that live in `02` / `03` without a P-id, still not U

- Headless capability may have an **optional** config/inspect surface that is not a runtime requirement.
- Own QMX semantics; json-render / MCP Apps remain **adapters** until host contracts exist.
- Provisional DESIGN.md (density, type, semantic tokens, chart colors) as one visual authority — baseline dark is U; the file contents are not.
- Composer: compact entry that separates content/resources from tools/targets; snapshot vs live link; how long references last (`03` §4). Previous picker is rejected; replacement is P.
- Split inspector beside the graph, without permanently squeezing the canvas (`03` §3).

---

## 3. Studies 01 / 02 / 03: what they got wrong vs what can be salvaged

`02`: “Study 01 is exploratory. None is an approved implementation baseline. The assistant owns those errors; the source was not missing.”

### Study 01 — `experience-v01` (interactive storyboard)

**Wrong**

- Arrived after a premature single journey (turn 1 suggestion), even though v01 itself tried to widen to six areas.
- Illustrative always-visible app copilot (later: copilot is **optional** per app).
- Generic/demo content and unresolved styling presented in the same surface as product structure.
- P-008 behaviors (detail-tab grouping, library return location, per-app retained context) were never accepted.
- Did not yet carry json-render / MCP Apps (user had to raise them in T6).

**Salvage (as questions or later U, not as the mock)**

- Six-area map: Home/nav, main agent, mini-apps, detail, Library, authoring — T5 agreed to turn the storyboard into that map (**D-009**).
- Design system vs **app-building contract** as two artifacts (T6: “you actually already know what to do”).
- App composition vs workflow-logic editing (P-007; n8n later named as authoring lead).
- Platform destinations above the divider vs opened apps below — user confirmed in T6 (**D-015**).
- Copilot as one capability / many sessions — user accepted in T7 (**D-017**).

### Study 02 — `experience-v02` (main-workspace HTML + “design system” sheet)

**Wrong**

- Visual treatment and tokens: “This is very ugly” (T9). **D-021:** do not promote tokens or new wireframe scaffolding.
- Attachment **picker** rejected: “I really don’t like the attach thing.” Too many unanswered “what happens when you attach a dataset / an app.”
- Input/composer styling treated as if aesthetics had started.
- Local HTML never opened in-browser (policy block). Syntax check ≠ interaction proof (**C-005**).
- Let a Codex-like preview study outrun the original app layouts.

**Salvage (re-propose against original layout, not by polishing v02)**

- Attached-item **appearance** / chips: “I like how they look when I attach something.”
- Structured “ask the user a question” can work (Claude-like also named; this version “can work also”).
- Preview as a **tabbed work area** (Codex reference), not a fake document pane.
- P-013 splits still worth evaluating: per-message vs conversation context; pending question/draft stays with its conversation; explicit unavailable-source.
- Five workspace states (P-011) as a coverage checklist for the main copilot, not a screen to copy.

### Study 03 — `experience-v03` (app + Library wireframe) — **withdrawn**

**Wrong (this is the hard miss)**

T10: “insanely very different”; “it’s just text, most of it. It’s unusable.” `layout-fidelity-reset.md` names the departures:

1. One three-column generic shell on every destination (permanent extra left column).
2. Mini-app pages stuffed into a **permanent secondary sidebar** instead of **dynamic top navigation**.
3. Large widget canvas replaced by two prose-heavy cards / “explanatory banners.”
4. Codex screenshots used to reshape the app, instead of preview/conversation chrome only.
5. Mini-app interior did not **change with the application**.
6. Study notes lived on the product surface.
7. BMAD UX inspection correlated with the miss; **D-027** then **D-031**: UX skill stays out; architecture/epics later still allowed.
8. Library and authoring placeholders were **not** approved even though those surfaces had more room (**D-028**).

Changing colors would not have fixed it. There is **no** corrected replacement mock.

**Salvage (individual ideas only)**

- Problem statement: dataset reference ≠ app reference ≠ enabling tools; do not silently upload, merge conversations, or execute.
- Plugin package (skills/connectors/tools) ≠ opened mini-app (**C-006**).
- Tabbed work area (user already preferred this from Codex).
- Red-circled Codex control as a **conversation navigator** candidate (name/behavior unverified; plus menu never seen).
- Typed Library, source/version inspector, locate vs save as **open questions** (Q-003, O-04) — not as v03’s catalogue.
- “Plus picker” must be redesigned, not reused.

---

## 4. Remaining user-open questions vs questions the architecture should default

Ask the user only where evidence cannot close a **consequential** choice (`01-GROK-PROMPT.md`). Everything else: propose a default, mark it P, do not silently promote it to U.

### 4.1 Leave user-open (do not invent a quiet decision)

| Open item | Evidence | Why the user still owns it |
|---|---|---|
| Visual identity beyond the temporary dark baseline; canonical DESIGN.md contents | T12–T14 still hunting Stitch/Superdesign/old design.md; **D-033, D-038, D-041** | Baseline is a *working* permission, not a brand lock. |
| Desktop host: Tauri vs Electron vs browser-only; bundled vs external Python | T12–T14 interest in Tauri/Rust “for speed”; no benchmark | `02` P: evaluate against workloads. |
| Exact expansion/return chrome (top tabs vs in-place vs split inspector) | T2 arrows; T13 “add your own spin”; T15 node→code expansion; **Q-002, P-025** | User invited judgment **and** comparison with original arrows. |
| Which capabilities are UI-first, headless, or mixed | T15 names the axes, not the roster | Per app/workflow; historical examples are not a backlog. |
| Library taxonomy, ownership, locate vs save, whether a library *tab* exists | T6 “libraries is a very complex thing”; **C-002, Q-003, O-04** | Greater design room is not approval of v03. |
| Attachment semantics: snapshot vs live; dataset/app/widget/file meaning | T9, T7; `03` §4 | Picker rejected; meaning still asked. |
| json-render vs MCP Apps vs custom views — actual host architecture | **D-016**, P-010 | Must be considered, not selected. |
| Copilot schemas, deployment topology, retention, which apps default the panel on | **D-017** | Direction accepted; mechanism not. |
| Exact UI-integration branch name, base SHA, merge/CI | **D-043, D-052** | Streams are U; names are not. |
| Provider CLI-proxy implementation | T15 “I’m certain we use a CLI proxy”; **D-050** “exact provider mechanism is unverified” | Cover the *surface*; do not pick a proxy. |
| Paper/live duration and acceptance for **trading** capabilities | T14 “week or two” doubted; **D-053** scopes *where*, not *how long* | No universal gate; trading-path criteria still unset. |
| Global search/commands, Home contents, attention states | `02` table “Still to design” | Board has a persistent home for running work; contents not specified. |
| Q-001: visible panels when switching/closing a mini-app vs durable sessions | Backend already: tab close ≠ end product session | Visual restore vs explicit stop is UX to design. |
| Q-004 / O-06: how global vs app vs widget agent context is shown and enforced | Grants live in core | UI must not invent a second permission system. |
| Q-005: which default apps ship first | “User’s priority work, not copied competitor menus” | Architecture must not mint a launch roster from brainstorm lists. |
| Q-009: BMS/BIMS / “market sentient” in the dictation | Unclarified | Do not guess domain labels. |
| Superdesign / Stitch / Design Arena in the build path | Optional helpers, untested on QMX | Not blockers (`02` U). |

### 4.2 Architecture should default (mark P, do not re-ask)

These are settled enough to proceed. If the candidate disagrees, it must say so against U, not re-litigate in a questionnaire.

| Default | Basis |
|---|---|
| Svelte + TypeScript + shadcn-svelte + Svelte Flow as the frontend starting stack. Pin versions from evidence; choose SvelteKit vs Vite with a stated default. | **D-040** |
| Neutral dark shadcn-svelte working theme; one provisional visual convention; no paid kit; no second style authority. | **D-041, D-044** |
| Qt UI = out. Do not dual-track a Qt shell. | **D-040** |
| Tauri = candidate host evaluated on Python lifecycle, packaging, local/VPS, webviews — no automatic speed claim. | `02` P / P-018 |
| Original Excalidraw family: distinct main-copilot vs mini-app vs authoring/ML interiors; shared narrow rail + divider + opened apps; no permanent generic secondary sidebar; widgets are real charts/tables/controls. | T10, **D-026** |
| Authoring/ML: graph/code workspace, optional right copilot, node may represent code or another capability; explicit expand/return; **no** LSE Train/Optimise clone. | **D-049**, P-025 as the working expand rule until arrows contradict it |
| n8n as authoring *reference*, not a vendor embed. App composition ≠ workflow graph. | **D-028**, P-007 |
| Presentation vs execution vs run lifetime independent. Headless invoke without a pane is valid. Closing UI ≠ cancelling a durable job. | **D-047** |
| Shared copilot capability, independently scoped sessions, optional app panel, no merged histories, no extra permissions via the panel. | **D-017** |
| Platform destinations (Home / Library / Authoring / main agent) exist with **no** app open. Opened apps consume them. | **D-015** |
| Paper/sim only on trading/risk-affecting capabilities. | **D-053** |
| Book/BMS = current default policy implementations, not a costume every app must wear. | T14 / `02` U |
| Historical sample apps = examples, not a closed backlog. | **D-039** |
| json-render and MCP Apps in the design, as **adapters** behind QMX contracts and backend auth; no implied grant bypass. | **D-016**, `02` P |
| Pipeline: research/architecture candidate → Codex review → user-run Documentation Factory → epics/stories → factory coding. No BMAD UX. No implementation in this sitting. | **D-029, D-031, D-051** |
| No app code on `main`. Backend integration ∥ UI integration → combined **tested** candidate → main. Do not mint branch names. Do not interrupt other agents. | **D-043, D-052** |
| Startup/splash/first-run, credentials, mentioned CLI proxy, terminal, local/server readiness specified as UX-01 even without a brand file. | **D-050**, `03` UX-01 |
| Reuse 85 existing BDD scenario IDs; add UI-observable cases; do not start an empty journey catalog. | **D-054** |
| User-facing implementation later needs Reticle `act_and_wait` / `assert` verdicts; `unknown` is not a pass. This document sitting has no runtime claim. | **D-055** / `02` (wins over T14 “you don’t need reticle”) |
| Classify each UI need as reuse / adapt / add / unresolved against **current** core. Do not assume the old inventory or that an “SDK” already exists. | T12, **D-014, D-030** |
| Zero spend; free shadcn-svelte + Svelte Flow. Dashboard sites and LSE are mental models. | **D-044, D-048, D-049** |

`03` UX-01…UX-12 and the independent-dimension table are **coverage obligations for the candidate to specify**, not a demand for twelve dashboards or every combination.

---

## 5. Contradictions: `session-visible-messages` vs `02-CURRENT-DIRECTION` (`02` wins)

The last **complete** assistant answer is turn 14 (L974–L1032). Turn 15 is the last **user** message; the export then has only a short assistant commentary (L1064–L1072) and no final_answer. `02` was written to carry those last corrections. Where the two disagree, **use `02`**.

| # | Session-visible (usually T14 assistant, or earlier U later revised) | `02` (wins) |
|---|---|---|
| 1 | **Paper trading.** T14 assistant: “Paper operation still belongs in the trading lifecycle… not the need to distinguish experiments, paper operation and live operation.” (`session-visible-messages.md` L1028) | “Paper trading is relevant only where a capability executes trades or materially affects trading/risk behavior… No universal week-or-two paper gate is approved.” User T15: “mini apps I don’t think need paper trading not all of them.” |
| 2 | **LSE as ML UI.** T14 assistant built ML Studio coverage around LSE Train/Optimise, dataset selection, disabled downstream actions (L1016). | “LSE’s ML Studio UI is rejected as a layout/model for QMX. Its ML capabilities can inform coverage. Do not recreate a fixed Train/Optimise form.” User T15: “this ML studio is bogus.” |
| 3 | **Dashboard kit.** T14 assistant clicked Analytics/Notes/Chats and treated patterns as component work to concentrate on (L990–L993), then still pointed “next work” at building those components. | “External dashboards are mental models. The commercial React kit is no longer a dependency candidate.” User T15: “I didn’t say we are going to use that no bloody hell no.” |
| 4 | **Start coding.** T11 assistant: “We should move into frontend implementation.” T14 assistant: “The next work should be the shared components and representative application experiences on the UI integration branch” (L1032). | “Prepare this packet now… Application implementation belongs to the later coding stage” (prompt/02). T12: not at handoff yet; T15: Grok does research/architecture; return here for review. |
| 5 | **Reticle.** T14 user: “for you you don’t need reticle because you have a lot of tools” → **D-046** optional for this agent. | “Current supplied AGENTS instructions require Reticle proof for user-facing implementation changes… Earlier tool-discretion wording is superseded.” Documentation-only packet still makes no runtime claim. |
| 6 | **Independent dimensions as user law.** T14/T15 commentary and some packet drafts treated a multi-axis lifetime schema as the user’s decision. | U is only: visual / headless / mixed, and UI ⇏ execution. “P: model presentation, execution location, conversation scope, activation and run lifetime separately.” **D-047** calls the broader schema assistant framing. |
| 7 | **SDK exists / Grok is implementing.** T7 user “you are turning this into an SDK”; T7/C-004 reported SDK work. | T12 / **D-030**: Grok finished architecture and is documenting; “SDK naming itself remains unverified.” Do not interrupt. `02`: “Do not assume a new SDK exists because an earlier message used that word.” |
| 8 | **Worktree as the implementation seat.** T2 assistant recommended a worktree; P-005. | **D-032 / D-043:** branch streams, worktree not required, names not created here. |
| 9 | **Study 02/03 as things to iterate.** T9 “this one can work for now” on ugly styling; T11 “add your own spin” could be misread as polish-the-mock. | Studies 02/03 are not baselines. Rejection of 03 is layout+density, not palette. Do not revive study 03. |
| 10 | **Export completeness.** Header: 15 turns, “active turn is partial.” A reader of only the last assistant *final_answer* (T14) will miss T15. | “The latest visible user turn is the authority for this handoff.” `02` exists so T15 is not lost. |
| 11 | **React recommendation lingering.** T12 assistant P-017 React+TS. T13–T14 user moved to Svelte; T14 assistant did switch — but any summary that stops at T12 is wrong. | Svelte + TypeScript + shadcn-svelte + Svelte Flow is U. React kit is reference-only, unpaid. |
| 12 | **BMAD wording.** T10 “stop using BMAD”; T12 restores architecture + epics. | “Skip BMAD UX. BMAD architecture and epics/stories remain usable.” Do not extend the UX ban to the architecture skill. |
| 13 | **Original images vs later tabs.** T14 assistant spent the turn on shadcn dashboard / transcripts; user T15: “I saw you looking at some other another image I don’t know why you are no longer considering the images in the Exicali draw diagram.” | “The original Excalidraw images and full dictation remain the foundation. Later Codex, dashboard and n8n references add context; they do not replace it.” |
| 14 | **T15 user sketched UI coding in ~two days in parallel with integration review.** | Parallel *review of backend integration* vs UI integration is allowed as a **later** workflow. “This packet does not start that review.” No application implementation in this stage. |

### Non-contradictions worth keeping straight

- T5 “layout ~70%” is **D-012**: strong starting point, **not** measured completion or frozen geometry (`02`: “without freezing exact coordinates”).
- T14 “I also have reticle” plus T14 “you don’t need it” is resolved by **D-055** for future user-facing code, not by this research file running Reticle.
- `CURRENT.md` already tracks T15 (headless, LSE UI rejected, paper scoped, study 03 withdrawn, parallel branches). It agrees with `02`. The dangerous document is the **T14 assistant final_answer** inside the export, not `CURRENT.md`.

---

## Carry-forward for architecture (not decisions)

1. Reconstruct from original OpenBB/VS Code + dictation, not from `experience-v01/v02/v03` HTML.
2. Keep U / P / E labels in any spine. Promoting P-021, P-025, or P-027 to “user decided” is the same class of error as the T14 paper-trading generalization.
3. Coverage the studies never reached and T14–T15 demanded: startup/splash, terminal, credentials/CLI proxy, charting, code diffs, observability, graph/code ML expansion, installed-product launch — specify them; do not ship twelve unrelated dashboards.
4. If this research disagrees with a later user turn **after** the 2026-09-23 capture cutoff, that later turn plus `02` still win; this file is not a live session log.
)
