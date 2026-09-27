---
name: Origin extraction — grok-architecture-mimi0apps
sitting: architecture-QMX-UI-2026-09-23
source: workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/evidence/origin-context/grok-architecture-mimi0apps.txt
status: evidence-only
---

# Origin extraction: Grok/Codex architecture sitting (`mimi0apps`)

**This transcript is not today's implementation state.** It is the 2026-09-18 Workflows architecture sitting (Stage A freeze `qmx-workflows-arch-2026-09-18-a` → Stage C candidate `qmx-workflows-arch-2026-09-19-c`). Inspected pins in the export: docs `b8b4d21`, implementation `270e992`. Later pack-and-grant work and this UI sitting post-date it.

Line numbers refer to `grok-architecture-mimi0apps.txt` as displayed (1–1235). Speaker labels in the export are `## User` and `## Assistant`. Tool logs and memlog strings are assistant-side unless quoted as operator speech.

Cross-checked against:

- sibling reading `origin-context/grok-reading.md`
- current UI direction `workroom/qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md`
- parent `architecture-QMX-2026-09-18/COPILOT-AND-APPS.md` and `UI-HOST.md`
- child `architecture-QMX-2026-09-23/COPILOT-AND-APPS.md`

`02-CURRENT-DIRECTION.md` is later user law for this UI sitting. Where that file and this transcript conflict, current direction wins. This report records what the historical sitting actually said.

---

## 1. User corrections that still bind

These are operator speech in this export, or operator speech the assistant later recast from the attached Explore-Node-Editor transcript and the operator then let stand. They bind the UI sitting unless current direction supersedes a *process* detail (it does not supersede the product ones).

### 1.1 The product is a construction kit, not a Book/BMS permission puzzle

**User (1101), after rejecting OD-01 as the wrong question:**

> I think the best way to really look at this book or BMS question is in terms of portfolio management and optimization. What you are looking at is simply that. Nothing more, nothing less. Books and the BMS ideally are simply part of a more or a very specific … portfolio management or risk management and position sizing system. That's it. What I just requested for, or what we are trying to do, is to make sure that it is not the only way.

> Book, the book and BMS system actually came in this very version. Other versions were using very different things … they were still working either way, okay, in theory.

> if we are changing the book, or rather, the risk management and position sizing system or the portfolio optimization system. … everything else related to it has to change or has to adopt with it … live trading has to adopt, backtesting, optimization, and hypothesis generation, testing, so literally everything that comes or that is attached to a book, even the MIS … Literally, the entire trading node, things that come before live trading …

> what we were actually aiming for is just adaptability.

> What we were talking about is apps, mini apps, workflows, you know, widgets, stuff in that manner. What you're asking is very, very specific to a book and a BMS, which doesn't add up and it doesn't make sense. I don't intend on faking a book.

**Still binds:** Book/BMS is one default portfolio/risk/sizing implementation, not the kit and not a live-money architecture hold. A replacement stack must be adopted coherently across authoring, backtest/optimize, MIS, trading node, paper, then live. Never dummy Book/BMS. Research/sensing is not that system. The UI conversation is about apps, mini-apps, workflows, and widgets — not a broker-permission form.

The assistant's accepted recast (1180–1182) restates that without adding a new ask:

> Book and BMS are one specific portfolio / risk / position-sizing stack that this QMX version uses. They are not the kit. … When you do, **the whole chain adopts it**: QML authoring, QMB backtest/optimize, MIS, the trading node, paper, then live. Never fake a Book. Research is not that system. You do **not** swap it and trade tomorrow — paper first, then sequential cutover. That last part is how you already work, not a later “please approve live” architecture ask.

The factory-launch standing list (1213–1224) is the same operator list, not a new assistant invention: one framework / no sixth COMP; Book/BMS default not ceiling; never dummy; data/ML need not be a bot; sessions own context and grants, tabs do not; app-use cannot edit implementation or apply its own changes; specialists remain; trading-floor PM means Portfolio Manager; sequential cutover, not hot-swap of live positions; BDD is specification; mutmut optional, never `apply` on the shared worktree.

### 1.2 Process: fresh session, paste in chat, operator launches factory

**User (1065):** wrap the architecture sitting; Documentation Factory is next; **the assistant is not the one doing it**; everything runs in a **fresh session**; put remaining questions **in chat**, dumbed down.

**User (1101):**

> for documentation factory, I'll have to manually run it. … I'm going to export this session transcript, start a new Grok build session … I don't want you to run it in this very session. … I like a fresh session to start from a fresh slate instead of you or even a sub-agent. … The most you can do is just give me a prompt in chat that I can use to start the session.

**Still binds for this UI sitting's later factory/epics handoff:** operator-launched fresh session; paste-ready prompt in chat (not a path-only handoff). The user also had to ask for the Codex ZIP **path** after a prompt-only message (646–660) — path plus paste, not path instead of paste.

### 1.3 Assignment constraints the operator did not walk back

Opening **User** prompt (1–32) plus the spoken wrap (33–41): Stage A architecture over Artifact Library, capability discovery, app orchestration, and copilot — not just the canvas; mutmut is a test-strength principle, **optional tool not a mandatory dependency**; stop at Codex challenge in that sitting; do not simulate independent review, production coding, or factory in-session.

Nudge **User (93):** use the installed BMAD architecture skill. That sitting did. This UI sitting still uses BMAD architecture, not BMAD UX (`02-CURRENT-DIRECTION.md`).

**User (584, 646):** wants the Codex prompt **in chat** and the exact ZIP path. Communication preference, not product law, but it is how this operator works.

---

## 2. Assistant claims that were later rejected

These are assistant-side. Do not re-ratify them in the UI sitting.

| Claim | Where | What rejected it |
|---|---|---|
| Live/paper-on-venue without Book is **refused unless the operator amends L36**; honest no-Book is only ungoverned research / QMN sensing | Memlog decision (365); Stage A freeze (531): “Live trading without Book stays refused until you amend L36.” | **User (1101)** plus assistant recast **(1180–1182)**. Wrong frame: adaptability of the whole stack, not a live-permission gate. |
| The only remaining operator question is “live systems with no Book/BMS?” Recommended: **no**, keep L36 | Stage A “Only questions that need you” (551–552) | Same. Operator already said Book/BMS is default **not ceiling**. |
| OD-01: venue-touching ATC is designed and **refused at admission** (`venue_requires_book`) until L36 moves; option A = “after you personally approve”; option B = broker always requires Book | Stage C verdict (992, 1037–1045); dumbed-down ask (1090–1097) | **User (1101):** “your question is not even clear. … what do you mean after I personally approve? … There is no question that should have arose from your session.” |
| “If you do not want to think about it, reply **go** and I will take **1**” (personally-approve-later) | Assistant (1097) | User refused the question and demanded a transcript refresh. |
| “I will run Documentation Factory in a **fresh session**, not here.” | Assistant (1081) | **User (1101):** operator runs it; assistant may only paste a prompt. |
| Stage A candidate is architecture-complete enough to freeze live-without-Book as a hold | Freeze prose (524–556) | Codex Stage B plus Stage C (990): Stage A was “directionally coherent and **not architecture-complete**.” Stage C itself still said **not ratified** and **not ready** for an operator acceptance gate (980, 1059–1063) — that *honesty* still binds; the *OD-01 hold* does not. |
| Sensing / `UngovernedWorkConfig` could stand in for a second trading system | Early AF-01 framing the assistant had to unwind (992) | Operator + Codex: do not disguise sensing or research as a complete alternative (712). Dummy Book stays `INVALID_INPUT`. |

**Not rejected (still true as honesty, not as product law):** the candidate was never ratified in this sitting (980, 1059); at `270e992` TaskGraph was in-memory, ContributionHit proposed, product sessions absent, QML→QMB→QMN unsupported (1055, 1230); QMA tests were blocked by a nested venv (361, 539); `8510c03` absence claims are stale (212, 539). Those are evidence limits, not UI designs.

---

## 3. UI/host ideas already absorbed by the 09-18 and 09-23 sittings

The 09-18 sitting **wrote** these into parent law. The 09-23 pack-and-grant sitting **repeated** them as inherit-do-not-re-elicit. The UI sitting must not re-open them as ontology.

### 3.1 Construction kit, not a sixth app

**Assistant freeze (531):**

> QMX becomes a **construction kit over the existing libraries**, not a sixth application. The Experimentation Board is layout only. Workflows **reuse and extend QMA** (Graph Templates → Missions → CT-47) … **Artifact Library kinds stay as they are**; discovery adds a `ContributionHit` (never an `fp1`). Copilot has **authoring vs app-use** product sessions (`psess:`), distinct from QMA execution sessions.

Memlog (362–364, 372): QMF stays the toolbox; Board is a UX projection **not a registry kind**; four discovery rails stay typed (Artifact `fp1`, Knowledge cite, Contribution `plugin_id:local_id`, Hypothesis `qml.research` off-facade); Board draft ≠ Graph Template ≠ Task Graph / Mission; ungoverned library calls never become Missions; QMA `Session` is not a product session; skills never compile to Missions.

**Absorbed:** `architecture-QMX-2026-09-18/COPILOT-AND-APPS.md` (Library rails; mini-app as named grouping; headless packs valid). `architecture-QMX-2026-09-23/COPILOT-AND-APPS.md` (one product identity; independently scoped `psess:`; UI panels are not sessions).

### 3.2 Sessions, grants, change-request — identity and authority, not chrome

**Assistant (364):**

> Product sessions authoring vs app-use are host/wire authority overlays distinct from QMA Session. Copilot discovers host-granted contribution descriptors. App-use cannot edit implementation or self-grant. Change request is a staging artifact into a separate authoring session.

**Assistant Codex-preserve list (703–705)** and factory list (1218–1219): sessions own context and grants; tabs do not; app-use cannot edit implementation or apply its own changes.

**Absorbed:** parent AD-8 / AD-9 / AD-10 / AD-24 / AD-29; GrantRecord not op-id strings (AF-10, 1011); AF-14 app-use still cannot apply; 09-23 delta table (main authoring vs optional in-app panel vs engine `sess:`); context transfer is `selected_refs` or `change_request` only; nested invoke does not union grants.

### 3.3 json-render and MCP Apps are presentation adapters; they cannot grant

**Assistant memlog (366):**

> JSON Render and MCP Apps present DTOs only (DEC-0392).

**Assistant donor table (575–576):**

> JSON Render v0.20.0 — Catalog UI only; host implements actions. Not authority.  
> MCP Apps — Sandboxed tool HTML; host still grants tools. Native panes stay native.

**Absorbed verbatim** in `architecture-QMX-2026-09-18/UI-HOST.md`:

> Three presentation lanes: native QMX pane; JSON Render registered components; MCP Apps tool HTML. None own identity or permission.

Rich views: “none as ui_view”; “native pane vs json-render vs MCP App” deferred **GAP-0081**. App-use sessions **absent** at `270e992`. Reconnect “must not cancel jobs; must not replay intent.”

09-23 `COPILOT-AND-APPS.md`: “MCP Apps / JSON Render are views the host may mount; they cannot grant.” Spine AD-8: do not pin `@json-render/*` or `@modelcontextprotocol/ext-apps`; chrome remains GAP-0081 / GAP-0100.

`STACK-AND-EVALUATION.md` (09-18, written in this sitting): JSON Render is “Not domain execution; **host stack unchosen**.” MCP Apps are “Not native navigation.”

### 3.4 n8n / Hermes / OpenBB as mental models only

**Assistant (573–578):** borrow Hermes schema/handler and config vs state; refuse missing-dep warning-and-continue and in-process full trust. Borrow n8n descriptor vs graph vs run and draft vs published; **do not embed n8n** (Sustainable Use License / OEM). OpenBB providers ≠ widget/app declarations; **do not adopt the runtime**. mutmut optional, never a product dependency.

**Absorbed:** 09-18 stack record “No n8n/Hermes/OpenBB/LEAN import”; 09-23 stack table “Hermes / n8n / OpenBB / … mental models only.”

### 3.5 UI DTOs without authority; chrome explicitly deferred

AF-17 (1018): “UI DTOs without authority — **new** DTOs; chrome **deferred**.” Implementation sequence (09-18): “UI chrome (GAP-0081)” is later, not the Workflows slices. 09-23 deferred table: “GAP-0081 chrome / GAP-0100 cutover dashboard — UI sitting; contracts here are enough.”

That is the intended handoff **into** this sitting: contracts exist; chrome does not.

---

## 4. Ideas still OPEN for this UI sitting

These are either (a) explicitly deferred to GAP-0081 / host choice in 09-18/09-23, or (b) raised in this origin as UI-adjacent and **not** frozen as chrome, or (c) current-direction work this origin never decided. Do not treat the origin as having closed them.

### 4.1 Host chrome GAP-0081 (the actual UI sitting)

From 09-18 `UI-HOST.md`, still open here:

- Navigation **layout** (backend has desks/scope_path and plugin roster; host binds contribution descriptor; layout deferred).
- Command **palette chrome** (AD-3 `op_id` exists).
- Which surface uses **native pane vs json-render vs MCP App** (three lanes named; none chosen per surface).
- Parameter-form **styling** (catalog-constrained forms exist as contract).
- How Library chrome shows typed hits without collapsing Artifact / Knowledge / Contribution / Hypothesis (`COPILOT-AND-APPS.md`: “UI may show one Library chrome over typed hits. It must not collapse kinds.” OD-03 was a technical default to show ContributionHit — not a layout).

09-23 still parks: pin json-render or MCP Apps SDK “until UI host chooses”; GAP-0100 cutover dashboard; third `ProductSessionProfile` only if this sitting proves authoring-with-absent-instance is **not** the main workspace.

### 4.2 json-render / MCP Apps / app-building contract as *host* work

Current direction **U:** “json-render, MCP Apps, reusable components and a future app-building contract must be considered.” **P:** own QMX semantics; renderer integrations remain adapters until supported by **concrete host contracts**.

The origin absorbed the **authority** rule (paint, do not grant). It did **not** specify:

- catalog registration, action dispatch onto existing AD-3 `op_id`s, iframe/`ui://` messaging, fallback when a renderer fails;
- which QMX widgets are native vs generated;
- Svelte host wiring (this export never chooses a web framework — see §5);
- contribution metadata for optional views / optional copilot profile as a **request**, not a grant (09-23 named the request-blob; chrome and mounting remain).

### 4.3 Session UX vs session identity

Identity is closed: `psess:` vs QMA `sess:`; panels are not sessions; switching tabs must not retarget grants; reconnect must not replay intent or cancel jobs.

**Open as experience** (current direction + 03-EXPERIENCE-SCOPE, not this transcript): independently scoped conversations; switching apps restores the relevant history instead of merging; optional in-app copilot; attachment/reference semantics; concurrent work; change-request **handoff UX** from app-use to authoring; Home vs opened-app rail.

### 4.4 Headless vs UI-oriented capabilities

Origin: headless packs are valid workflow steps without navigation. Current direction **U:** mini-apps and workflows may be UI-oriented, backend/headless, or mixed. **Still to design:** how a headless capability is discovered, inspected, and optionally given a configuration surface without making that surface a runtime requirement.

### 4.5 Experimentation Board as layout

Origin: Board is UX projection, not a registry. **Open:** actual board layout, draft-vs-run distinction in the UI, expansion/return for graph/code (current direction invites this; LSE ML Studio layout is **rejected** by current direction and was never approved here).

### 4.6 Frontend stack was unchosen in this origin

This export does not mention Svelte, Qt, Tauri, or React. `STACK-AND-EVALUATION.md` from the sitting: JSON Render “host stack unchosen.” Current direction later: Svelte + TypeScript, shadcn-svelte, Svelte Flow; Qt out; Tauri/Rust of interest; commercial React dashboard kit is reference only, zero spend. **Do not** use this origin to reopen stack. **Do** treat host/process boundaries, first-run/splash, and native vs webview as open *this* sitting (`02-CURRENT-DIRECTION.md`).

### 4.7 What this origin must not drag into UI as a new ontology

Capability / extension / workflow / mini-app / widget vocabulary is already parent law. Reconcile chrome names with that kit. Do not mint a parallel UI object model, a sixth COMP, or a Library kind for views.

---

## 5. Dangerous historical examples — do not silently ratify

These appear in this sitting as **temptations, donor analogies, or rejected assistant frames**. The UI sitting may study them as references. It must not import them as runtime, identity, or permission.

### 5.1 Live-money as an architecture switch

**Danger:** treat “can the UI deploy / hot-swap live positions?” as a layout or grant shortcut.

Origin standing correction (1222, 1182): **sequential cutover, not hot-swap of live positions.** Paper first. L17 human promote remains constitution, not a UI button that is the architecture. Assistant Stage A/C “refuse live without Book until you personally approve” is the **rejected frame** (§2). Dummy Book/BMS is `INVALID_INPUT` (992). Current direction: paper trading is relevant only where a capability executes trades or materially affects trading/risk; no universal week-or-two paper gate.

### 5.2 n8n-as-runtime

**Assistant (574):**

> n8n — Borrow descriptor vs graph vs run, and draft vs published. Do **not** embed n8n (Sustainable Use License / OEM).

Current direction and 09-23 donor research repeat: n8n is a mental model (graph/run inspection, error-workflow observability as *shape*). Not an embedded engine, not a second scheduler (372: reuse QMA; do not mint a second scheduler). A later n8n screenshot or docs page does not select n8n's runtime.

### 5.3 React-as-decision (and any renderer-as-stack)

**This file never names React, React Flow, Qt, Svelte, or Tauri.** Sibling origin `Explore-Node-Editor-Architecture.md` (see `origin-reading.md`) floated React Flow; that is a historical candidate, not a requirement. Current direction: Svelte + TypeScript is the working frontend; the commercial React dashboard kit is **reference only** and is no longer needed as a dependency; zero spending on component kits.

JSON Render v0.20.0 in this sitting is a **catalog UI adapter**, not a React/Svelte stack choice. 09-23 notes upstream v0.21.0 and still **does not pin**. MCP Apps are sandboxed tool HTML, not native navigation, not a host framework.

**Do not** ratify: React dashboard kit as QMX UI; json-render as the app runtime; MCP Apps as identity, persistence, or grant path; replacing native panes wholesale with embedded mini-app HTML.

### 5.4 Other donor imports this sitting already refused

| Example | Origin stance | Do not ratify |
|---|---|---|
| Hermes portable plugins | Copy schema/handler, config vs state; refuse full-trust and warning-and-continue (573) | In-process full trust; missing-dep continue |
| OpenBB Workspace | Providers ≠ widget/app declarations; do not adopt runtime (578). User (1101) cites OpenBB only for **adaptability logic**. | OpenBB as QMX host or widget runtime |
| LSE | Stack record: catalogue→preview→builder as recipe/job/stream **phases**; “Do not clone UI or paid jobs.” Current direction separately rejects LSE ML Studio **layout**. | Recreating Train/Optimise as default ML chrome |
| mutmut | Optional WSL test-strength; never `apply` on the shared worktree (366, 577, 708, 1224) | Product dependency or shared-tree mutation |
| QMA `Session` | Confirmed not a product session (271, 364) | Chat tab = engine run |
| Sixth COMP / Board-as-registry / ContributionHit-as-`fp1` | Explicitly refused (362, 531) | New durable UI object kinds |
| Skills / MCP HTML / catalog actions granting tools | Skills never compile to Missions (372); MCP host still grants (576) | Generated UI as a back door around GrantRecords |

### 5.5 Proposed-as-implemented

Factory honesty pin (1230):

> Do not describe proposed connects as implemented. At 270e992: TaskGraph store is in-memory; ContributionHit is proposed; product sessions are absent; QML→QMB→QMN is unsupported integration.

UI-HOST at that pin: app-use sessions **absent**; rich views **none as ui_view**. Passing bounded QML/QMN tests (361, 539) is not UI interaction, process recovery, or clean-machine install. Current direction repeats: previous origin-transcript claims are dated; fresh source inspection is required.

---

## Coverage and how to use this file

**Read:** all 1,235 lines of `grok-architecture-mimi0apps.txt` (opening assignment 1–42; exploration and first decisions 43–379; Stage A freeze and donors 360–644; Stage B/C handoff 646–979; Stage C ledger 980–1105; operator wrap and OD-01 recast 1065–1235). Seven `## User` turns: assignment (1), BMAD nudge (93), Codex prompt request (584), ZIP path (646), Stage C paste (662), wrap-up (1065), OD-01 / factory process correction (1099).

**Do not use this origin to:** choose Svelte/React/Qt; pin json-render or MCP Apps; embed n8n; treat live-money hot-swap as a UI feature; mint chrome as a grant path; claim product sessions or `ui_view` existed at `270e992`; re-ask “may we go live without Book after you approve?”

**Do use it to:** keep adapter-vs-authority, session-vs-tab, app-use-vs-authoring, headless-packs-valid, Library-rails-stay-typed, no-sixth-COMP, and sequential-not-hot-swap as already-settled parent law while this sitting designs GAP-0081 chrome and host contracts.
