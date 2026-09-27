---
name: reconcile-inputs
sitting: architecture-QMX-UI-2026-09-23
created: 2026-09-23
updated: 2026-09-23
status: independent-review
scope: candidate vs handoff 02/03/05; UX-01..12; quiet requirements the AD structure dropped
handoff:
  - workroom/qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md
  - workroom/qmx-ui-architecture-handoff-2026-09-23/03-EXPERIENCE-SCOPE.md
  - workroom/qmx-ui-architecture-handoff-2026-09-23/05-RETURN-FOR-REVIEW.md
candidate_root: _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23
law: [START-HERE.md, ARCHITECTURE-SPINE.md, EXPERIENCE-AND-LAYOUT.md, COMPONENT-CONTRACTS.md, DESIGN.md, CHANGE-IMPACT.md, JOURNEYS.md, DELIVERY-AND-QA.md, DECISIONS-AND-OPEN.md]
not_law: [research/]
---

# Reconcile — UI candidate vs handoff packet

Independent review. Does not implement. Does not amend the spine.

**How this lens scores.** `research/` is evidence, not ingestible law (`START-HERE.md`). A UX row is **landed** only when a local AD or a named companion binds the behavior 03 asked for. Coverage that lives only in research is **partial** at best. Spine YAML `binds: [UX-01..UX-12]` is a claim, not coverage.

**Headline.** The candidate is an honest client-over-pack-and-grant architecture with a real inspect baseline and a real storyboard ledger. It is **ready for Codex focused review**. It is **not ready for Documentation Factory**. Factory would have to invent UX-08 charts/data chrome, UX-06 authoring chrome, UX-10 trading/risk surfaces, Home contents, and the expand/return comparison 03 required against the original arrows. The best first-run, Library, and pack-view material is trapped in `research/` after the sitting told Factory not to treat that folder as law.

---

## UX-01..12

Legend: **landed** = AD/companion explains the required behavior; **partial** = structure or constraint exists, chrome/states/trace incomplete or parked in research; **missing** = 03 obligation has no candidate explanation a factory could ingest.

| ID | Surface | Score | Where it lives | What is still not explained |
|---|---|---|---|---|
| **UX-01** | Launch, first run, reconnect | **partial** | Spine AD-11, AD-12, AD-13; J-UI-11; sequence in `research/14-firstrun-packaging-placement.md` | EXPERIENCE §6 is one paragraph that defers to research. PyCharm/DaVinci “deliberate splash” is thinned to “small splash/status.” CLI-proxy card vs QMA credential refs vs QMN venue refs is research-only. Terminal access as a first-run item is not in AD-11. Partial-readiness law is good; the walk is not law. |
| **UX-02** | Home and platform navigation | **partial** | Spine AD-3, AD-4, AD-14; EXPERIENCE §1 rail mermaid; J-UI-01 | Rail + divider + opened-apps-are-instances landed. **Home contents, attention states, global search/commands, responsive placement** remain the 02 “still to design” cells — still undesigned. Home vs worker health is “consume listing axes,” not a screen. Multiple-instance chrome unnamed. |
| **UX-03** | Main copilot and composer | **partial** | Spine AD-4, AD-7; EXPERIENCE §2; P-ATTACH; J-UI-04 | Sessions / conversation / tabbed preview family is correct (Hermes/Codex/Cowork, not VS Code). Rejected study-02 picker is named. Missing as contracts: keyboard, conversation-navigation (red-circled Codex ref; name unverified), concurrent stream routing by stable ids beyond one sentence, question ownership, “what will this conversation use?” chip provenance as UI, work-area launcher vs unobserved plus-menu. |
| **UX-04** | App workspace and widget expansion | **partial** | Spine AD-8; EXPERIENCE §3; WidgetFrame/DetailHost | OpenBB family (top nav omit-able, dense canvas, optional right copilot, widget message/expand) landed as layout law. Add/edit widgets, linked parameters, layout-editing mechanics, and compact-inspector vs split vs top-tab **were not compared to source arrows** (`w6Wra1LH`, unbound `hoGJ6iaL`) before AD-8 adopted “Open/Expand → work-area tab.” Shared-filter non-leakage is a Prevents, not a mapping UI. |
| **UX-05** | Library | **partial** | Spine AD-10; EXPERIENCE §5 (four sentences); full verb table in `research/13-library-lifecycle.md` | “One chrome over typed hits, not a new kind; platform destination not a mini-app tab” landed. Discover/filter/preview/open/use/reference/save/fork/lineage/upgrade/rollback/import-export as **operator-visible** behavior is research. Fork is unresolved even there. Factory ingesting only AD-10 gets a destination name, not a Library. |
| **UX-06** | App composition and extension authoring | **partial** (chrome **missing**) | Spine AD-6, AD-15; COMPONENT §5; verbs in `research/11-pack-view-contribution-ui.md` | Pack-requests / host-grants / no `ui_view` point / headless-valid landed as trust law. 03 asked for build-views, draft-vs-installed preview, resource picker, validation/diff/review, optional packaging, version-compatibility UI, install vs grant as distinct acts. Those screens are not in EXPERIENCE or JOURNEYS (J-UI-12 is lifecycle honesty, not an authoring workspace). |
| **UX-07** | Workflow/ML graph and code | **partial** | Spine AD-9; EXPERIENCE §4 mermaid; J-UI-03 | Family (graph + compact inspect + explicit expand + named version + no lossless round-trip + LSE Train/Optimise refused) landed. 03 §3 required a **source-linked** layout/state diagram vs original arrows and screenshot proportions, and a decision on split inspector vs squeezed canvas. The mermaid is not source-linked. Nested work, run-from-boundary chrome, run-history surface, local/VPS placement as UI are unnamed. |
| **UX-08** | Research, charts and data | **missing** | Spine frontmatter lists UX-08; DESIGN chart tokens; P-CHART; CHANGE-IMPACT `lightweight-charts` row; parent notes in `research/06` | No AD, no EXPERIENCE section, no journey. Instrument/time/query selection, linked views, provenance/units/timezone/freshness cues, missing vs empty vs truncated as chrome, large tables, streaming plots — absent. “Ordinary analytics ≠ financial charting” is a decision row, not a surface. Factory would invent a research app. |
| **UX-09** | ML evaluation | **partial** | Spine AD-9 (non-trading ML, no Book wrap, no LSE form); J-UI-01 as switch-during-run | Constraint law is correct. Dataset/features/split/version, leakage controls, GPU availability, reproducibility, progress/logs, cancellation-vs-interrupt chrome, run comparison, metrics/model/artifact lineage as **evaluation views** are not designed. Folding ML into the graph family is the right refusal of a rigid Studio; it is not coverage. |
| **UX-10** | Trading / risk / position-sizing | **partial** (surface **missing**) | AD-9 one sentence on paper; DELIVERY “Paper trading”; origin extract `research/03`; first-run paper fence in `research/14` | No-universal-paper-gate and “QMA-paper does not exist” landed as constraints. 03 still required: existing Book/BMS default vs alternative compositions as UI; exposure/constraints/account/environment identity; paper/simulation **where relevant**; readiness/transition evidence; financial-effect ops distinct from analysis. None of that is a companion surface. Origin “Book/BMS is default not the kit; the whole chain adopts a replacement” is not a local Prevents. |
| **UX-11** | Operations and observability | **partial** | Spine AD-13, AD-14; J-UI-06..08; transport in `research/10` | Consume-don’t-duplicate, close≠stop≠cancel, `unknown`≠failed landed. Correlated run/events/logs UI, queue/backpressure, target capacity, diagnosis as a useful screen, GAP-0100 readiness chrome — named, not composed. Home attention is a badge, not an ops workspace. |
| **UX-12** | Settings, local files, terminal, previews | **partial** | AD-11/12; EXPERIENCE §6; WorkAreaTabs “unsupported preview”; mapping in `research/14` | Preview≠grant/install is law. Global/app/session/instance **scope UI**, file location vs remote availability, persisted layout (client-local), terminal as preview-not-privileged-shell, unsupported-preview fallback — research/COMPONENT one-liners, not a settings contract. |

**Roll-up:** 0 landed · 11 partial · 1 missing (UX-08). Two partials (UX-06, UX-10) are constraint-landed and chrome-missing — Factory-fatal if companions are the ingest set.

### Cross-cutting 03 obligations vs candidate

| 03 obligation | Score | Note |
|---|---|---|
| Independent dimensions (presentation / execution / invocation / definition-vs-instance / authority / observation) | **landed** | Spine AD-5. Headless without a nav pane is law. |
| Loading / empty / unavailable / failed / recovery / keyboard on every surface | **partial** | EXPERIENCE §7–§8 is a checklist, not a per-surface map. COMPONENT states are names without errors or a11y per row. |
| Graph → inspect → expand → code/diff → run → return, source-linked | **partial** | Mermaid in EXPERIENCE §4; not tied to `w6Wra1LH` / `hoGJ6iaL` / OpenBB header expand. Split-inspector question unanswered. |
| Composer: content vs tools vs target; file-upload ≠ path pointer; snapshot vs live | **partial** | AD-7 + P-ATTACH. Widget as `selected_refs` kind correctly refused. Chip provenance UI thin. |
| Example compositions (widget-heavy research + graph/code) | **landed** | COMPONENT §5. Headless pack as Home/Library row is there. |
| Per-component purpose / owner / inputs / events / states / errors / persistence / a11y | **partial** | Table omits owner, errors, and per-component a11y. `research/11` has a richer name list (`PackLifecycleCue`, `ActionDispatchGuard`, …) that the companion did not promote. |

---

## 05-RETURN deliverable table

| Deliverable | Score | Path that satisfies it, or gap |
|---|---|---|
| Reading and evidence ledger | **satisfies** | `research/01-evidence-ledger.md` (all 20 scene-text ids, full `JHZj5SdT`, 10 PNGs, overlays, observation vs inference). Origin transcripts: `research/02-origin-explore-node-editor.md`, `research/03-origin-mimi0apps.md`. Visible-session steering: `research/04-session-visible-steering.md`. Visual classes A/B/C: `research/09-images-video-codex-refs.md` + `research/00-orchestrator-image-notes.md`. Studies salvage: `research/12-rejected-studies-salvage.md`. |
| Current-state baseline | **satisfies** | `research/05-repo-core-baseline.md` (`main@92279dfe` dirty docs; `integration@34c148be` inspect; `ui@af66288` not a UI base). Frontend absence: `research/07-existing-frontend-scan.md`. Honesty also in `START-HERE.md` table and `CHANGE-IMPACT.md`. Daemon swallows TCP bytes; `caller_kind` / optional home instance / `copilot_profile` / instance `health()` / JSON-lines specified-absent. Types ≠ e2e. |
| Architecture candidate | **satisfies, with holes** | `ARCHITECTURE-SPINE.md` AD-1..AD-16. Ownership: UI client of `qma-wire` / `qma-daemon`; no sixth COMP; no new CT; Rust not a second orchestrator. Local/VPS and visual/headless combinations: AD-5, AD-12. Alternatives: `DECISIONS-AND-OPEN.md`. Holes: UX-08 has no AD; several P defaults sit **inside** ADOPTED ADs (P-ATTACH in AD-7, Tauri-optional in AD-12), so Factory can misread proposals as law. |
| Experience and component contracts | **partial** | `EXPERIENCE-AND-LAYOUT.md` (rail, three interiors, expand/return mermaid, composer pointer). `COMPONENT-CONTRACTS.md`. `DESIGN.md` (one provisional authority; Rhea/neutral dark; study tokens dead). Differentiated layouts exist as mermaid, not source-linked proportion diagrams. Library lifecycle / first-run / settings / pack authoring are research-depth, companion-shallow. |
| Change-impact map | **satisfies** | `CHANGE-IMPACT.md`. Reuse / adapt / add / unresolved; owners and inspect evidence; live JSON-RPC as **backend add**; no screen-to-service invention; no new sqlite class; QMB remains the only operator CLI. |
| BDD reconciliation | **satisfies (research); thin (law)** | Frozen 85: SHA `1c2c865d…` verified in `research/08-bdd-reconciliation.md`; namespaces not collapsed; written ≠ executable ≠ executed. Sitting journeys: `JOURNEYS.md` J-UI-01..12 (one-paragraph traces). SCN-0023..0027 honesty (untracked on main, absent at inspect) is in research/08, only hinted in JOURNEYS. |
| Delivery and verification plan | **partial** | `DELIVERY-AND-QA.md`. Sibling streams, Reticle vs process evidence, paper scoped, no experiments this sitting. Vertical slice is a four-bullet proposal. Clean-machine / packaging / performance are unknowns pointed at `research/14` and Deferred. Combined deployment candidate is a sentence, not a plan. |
| Decision / open-issue record | **satisfies** | `DECISIONS-AND-OPEN.md`. U / P / E / Conflict legend. Rejected studies, LSE-as-layout, old `ui` branch, universal paper gate, widget `caller_kind`. Open issues tagged non-blocking **if defaults hold** — that claim is too strong (see quiet drops and UX-08). |
| Independent challenge | **this file; package incomplete** | `reviews/reconcile-inputs.md` (here). No sibling seats (`review-adversarial`, `review-currency`, `review-parent-consistency`, `review-rubric`, `gate-summary`) unlike the 09-23 kit sitting. `START-HERE.md` “See `CODEX-REVIEW-LAUNCH.txt`” — **that file does not exist**. `companions/` and `contracts/` directories are empty; real companions sit at sitting root (mapped in START-HERE — not a content gap). |

---

## Quiet requirements the AD structure dropped or thinned

These are 02 **U** / 03 obligations that did not become a local Prevents or companion contract. Research often still has them. Factory ingesting ADs+companions would lose them.

### Product and tone

1. **Goals, not performance claims.** 02: risk management, position sizing and compounding *motivate* QMX; they are not financial-performance claims. Spine opens on discover/construct/test/reuse/operate and never restates the claim fence. Autofixable as a paradigm sentence + UX-10 Prevents.
2. **Non-trading exploration is first-class**, not only non-trading ML. AD-9 covers ML without Book wrap. General data tools / headless utilities as first-class uses are implied by AD-5, not said.
3. **Historical sample apps are examples, not a closed launch backlog.** Origin 02-extract agrees. No local Prevents. Factory can slice “the” mini-app catalogue from OpenBB tab names or origin energy/LSE examples.
4. **Do not turn every capability into a service, every object into a graph node, or every activity into a required workflow.** AD-1 blocks a sixth COMP. “Every object a node” and “every activity a workflow” are not local Prevents.
5. **Capability / extension / workflow / mini-app / widget vocabulary** (origin table the operator accepted). Spine uses pack / contribution / `view:*` / instance / JobHandle — the right core reconcile — and never binds the five-noun user vocabulary. Factory can ship packs and lose the product language 02 asked to keep.

### Headless, paper, Book

6. **Headless may have an optional configuration/inspection surface without making that surface a runtime requirement.** AD-5 + J-UI-02 get “no pane.” The optional later inspector is a JOURNEYS clause, not an AD Prevents (easy to implement as “headless = hidden”).
7. **Paper trading only where the capability executes trades or materially affects trading/risk. No universal week-or-two paper gate.** Landed as DELIVERY paragraph + AD-9 one-liner + research/14 fence. **Not** a spine Prevents on first-run, Library, or ML. Highest quiet leak into Factory checklists.
8. **Book/BMS is the default portfolio/risk/sizing stack, not the kit.** Origin `research/03` (user 1101). Dummy Book stays `INVALID_INPUT` in BDD research. Local ADs never Prevents “every future composition masquerading as a Book” except the ML sentence. Replacement-stack **whole-chain adopt** (authoring, backtest, MIS, node, paper, then live) is not UI law.
9. **QMA-paper does not exist; never “paper trade from copilot.”** `research/14` only.

### Original layouts (not later references)

10. **Original Excalidraw images + full dictation remain the foundation; Codex / dashboard / n8n / LSE do not replace them.** EXPERIENCE opening + AD-3 study-03 Prevents. **n8n-as-runtime** is rejected in DECISIONS; **n8n-as-authoring-lead** the operator expected to be looked up is not a companion diagram. Coordinates-not-frozen is said; **navigation transitions** 02 invited are unspecified (Library jump motion, expand-as-top-tab vs work-area tab).
11. **Compare expand/return with the original arrows before accepting a mechanism.** 02 P and 03 §3. AD-8 **adopted** Open/Expand → work-area tab without that comparison. `hoGJ6iaL` remains unbound in the ledger. Quiet ratification of a proposal.
12. **VS Code image is the authoring/ML family, not the main-copilot interior.** EXPERIENCE corrects an early orchestrator note (`research/00` still says main-copilot proportions). DECISIONS records the clash. Residual: 00 was not errata’d; a Factory reader of research/00 can put a VS Code editor in the main copilot.
13. **Do not claim native Codex clicks; plus-menu contents unknown; red-circle is conversation-navigation, name unverified.** EXPERIENCE one sentence on plus-menu. Not a Prevents. Easy to over-specify a plugin picker.

### First-run and host

14. **Deliberate splash inspired by PyCharm / DaVinci Resolve**, then practical configuration — not Electron-instant chrome. AD-11 thins to “small splash/status.”
15. **First-run includes provider/API keys, the mentioned CLI proxy, target connections, and terminal access. Exact provider mechanism unverified.** AD-11 “provider/proxy/API-key cards.” Vendor-neutral proxy card, “keys stay in the proxy,” OpenCodex-unverified, terminal as a **separate** preview — `research/14` only.
16. **Do not block all work behind one unavailable provider.** AD-11. Landed.
17. **Close window ≠ stop work; closing desktop may stop a host-owned sidecar only when the operator chose “stop local runtime.”** AD-12 proposal default. Close-dialog copy and the explicit Stop action are not companion UX.

### Process / pipeline (quiet, but Factory-adjacent)

18. **Skip BMAD UX. Figma is not the workflow. Stitch/Superdesign are optional helpers, not blockers.** START-HERE and `.memlog.md` record the skip. No AD Prevents a later epic from “helpfully” running BMAD UX or treating archived Stitch HTML as a skeleton (`research/07` already warns).
19. **No application code on `main`; UI integration sibling of backend; combine only a tested candidate; operator squash-merge.** AD-16. Landed.
20. **User-facing implementation requires Reticle `reticle_act_and_wait` / `reticle_assert`; `unknown` is not a pass.** AD-16 last sentence + DELIVERY. Landed as delivery, not as a coding-agent Prevents.
21. **Passing static/unit checks is not evidence of UI interaction, process recovery, or clean-machine install.** DELIVERY evidence-class table. Landed as table, easy to ignore in epics.
22. **This sitting does not start the deferred backend code review.** AD-16. Landed.

### 03 items that never became ADs

23. **Home contents / attention / global search / commands / responsive placement** — 02 table “still to design.” Still open. Not a drop of a decision; a **named undesigned** that Factory cannot fill.
24. **Attachment snapshot vs live** is P-ATTACH inside ADOPTED AD-7. A proposal wearing an ADOPTED badge.
25. **Generated output must not become an untracked in-process execution path.** AD-6/AD-15. Landed.
26. **Profile representative graph size, chart rate, table volume, conversation length, memory, startup time on declared hardware.** Deferred “need a shell.” Honest, but 03 asked the architecture to plan it. DELIVERY does not name hardware or budgets even as TBD numbers.
27. **Independent challenge record of what changed after review.** Cannot exist until after this gate. START-HERE promised `CODEX-REVIEW-LAUNCH.txt` — missing.

---

## Conflicts (candidate vs handoff, not vs parent)

| Id | Clash | Winner in the packet | Residual |
|---|---|---|---|
| C1 | Research richness vs “research is not law” | START-HERE | Factory hole unless named research is promoted (14, 13, 11, 08, 10). |
| C2 | AD-8 expand/return adopted vs 02/03 “compare with original arrows first” | Spine (silent) | Mechanism ratified without the required comparison. |
| C3 | P-ATTACH / P-PROCESS / P-LIBRARY sitting inside ADOPTED ADs | Unlabelled | Codex/Factory can treat proposals as sitting law. |
| C4 | `research/00` VS Code = main copilot vs EXPERIENCE correction | EXPERIENCE / DECISIONS | 00 not marked superseded. |
| C5 | DECISIONS “no consequential operator question required” vs 02 still-to-design Home/search and 03 split-inspector | DECISIONS is wrong | Those are consequential if Factory is next. They are not blocking **Codex review**. |
| C6 | Spine YAML binds UX-08 with no AD | Claim | Missing surface. |
| C7 | LSE video still in the ledger vs LSE ML Studio UI rejected as layout | 02 U / AD-9 | Ledger is correct if Class C stays coverage-only (`research/09`). |

No local AD silently overrides a 02 **U** decision. The failures are omission, thinning, and proposal-as-ADOPTED.

---

## Codex six questions (05-RETURN)

1. **Source layouts and latest ML/headless corrections?** Mostly. Three interiors, LSE form refused, headless first-class, study 03 three-column refused. Weak: expand mechanism not compared to source arrows; authoring canvas was never on the board (honest) and is still a mermaid; Home contents still blank.
2. **Observation vs proposal vs historical?** Strong in START-HERE, CHANGE-IMPACT, evidence ledger, DECISIONS legend. Weak where P rows hide in ADOPTED ADs.
3. **Journey → component state → contract → backend owner → recovery?** Partial. J-UI-01..12 are traces, not state machines. COMPONENT states lack errors. CHANGE-IMPACT names owners. Weakest on UX-08/06/10.
4. **Extension model without duplicating core or forcing one shape?** Strong. AD-1, AD-5, AD-6, AD-15, `research/11`.
5. **Local/remote lifecycle, version/authority, compatibility, installed-product testability?** Partial. Honest about `DaemonProcess` as backend add, cwd-relative daemon root, CredRead unwired, Tauri optional. J-UI-12 exists as prose. Not concrete enough to test an installer.
6. **Can Documentation Factory ingest without guesswork?** **No.** See verdict.

Experiments this sitting: **none** against a running daemon or UI. Stack pins are a 2026-09-23 web check (`research/15-stack-currency-orchestrator.md`). Inspect did not start `qma-daemon` or run pytest (`research/05`). Limits are declared; do not read them as runtime proof.

---

## Verdict

**Ready for Codex focused review. Not ready for Documentation Factory.**

Send Codex the candidate at:

`C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/`

Entry: `START-HERE.md`. This file is the independent-challenge start. Do not start Documentation Factory, epics, or coding from this packet as-is.

Expected Codex outcome under the 05-RETURN rubric: **ready after listed corrections**, not “ready for Documentation Factory,” and not a backend code-review.

### Corrections that must land in law (companions or ADs) before Factory

Autofixable from this sitting’s own research; no new operator question if the P defaults already in DECISIONS hold.

1. Promote `research/14` first-run walk (splash → probe → partial shell → provider/proxy/target cards → reconnect) into EXPERIENCE. Keep provider mechanism **unverified**. Keep paper off splash.
2. Promote `research/13` Library verbs (per-rail preview/open/use/reference/save; fork remains unresolved) into EXPERIENCE. Keep “not a new kind.”
3. Promote `research/11` install/enable/grant/open-view and the extra QMX component names into COMPONENT-CONTRACTS. Add errors + a11y per component.
4. Write an EXPERIENCE section for **UX-08** (linked views, provenance cues, analytics vs tape) and a thin **UX-10** surface (environment identity + financial-effect vs analysis, no universal paper gate, Book default not ceiling).
5. Source-link the graph/expand/return diagram to `w6Wra1LH` / `hoGJ6iaL` / OpenBB header expand; record split-inspector as an open P, not an adopted squeeze.
6. Relabel P-ATTACH, P-PROCESS, P-LIBRARY so they are not ADOPTED body text. Add Prevents: no universal paper gate; sample apps ≠ backlog; skip BMAD UX; no Codex-click fiction.
7. Design or explicitly defer **Home contents / attention / global search** as named open chrome — do not let Factory invent a dashboard.
8. Add `CODEX-REVIEW-LAUNCH.txt` or delete the START-HERE pointer.

### Not blocking Codex (named, leave open)

Live JSON-RPC on `DaemonProcess`; `caller_kind` / optional authoring instance / `copilot_profile` / instance `health()` amends; Tauri vs browser+daemon v1 (P-PROCESS); exact `sv create` lockfile; `ui_view` contribution point; GAP-0073 search; GAP-0058/0062/0070; envelope crypto; workload numbers; combined `main` promotion.

### What this review did not do

Did not re-inspect `integration@34c148b`. Did not re-hash the 85. Did not open the PNGs (ledger claims they were opened in-session). Did not implement, merge, or start Documentation Factory.
