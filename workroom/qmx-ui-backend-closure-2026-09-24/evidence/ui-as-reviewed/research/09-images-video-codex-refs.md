# Images, video, and Codex refs — visual evidence ledger

**Sitting:** architecture-QMX-UI-2026-09-23  
**Role:** read-only visual ledger. Not architecture. Not implementation.  
**Inspected:** 2026-09-23. Every listed PNG/JPG was opened at readable scale with the Read tool (images render). The mp4 was **not** played; video claims rest on `video-reference.md` plus four sampled timestamps at two resolutions.

**Authority:** [`02-CURRENT-DIRECTION.md`](C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md) wins clashes. Original Excalidraw images and full dictation remain the layout foundation. Later Codex, dashboard, n8n, and LSE material add context; they do not replace it.

**Companions read:** `live-research/visual-evidence-index.md`, `grounding-summary.md`, `final-reference-pass.md`, `dictation-audit.md`, `video-reference.md`, `layout-fidelity-reset.md`, `experience-v03/references/manifest.json`, `experience-v03/plugin-reference.md`, `experience-v03/review-notes.md`, `evidence/README.md`, `evidence/provenance.json`, `live-research/board-current/attachments.json`, `live-research/openbb.md`. Parent note [`00-orchestrator-image-notes.md`](00-orchestrator-image-notes.md) is a first-pass overlay; disagreements are recorded below rather than silently merged.

How to read tags:

| Tag | Meaning |
|---|---|
| **sampled** | Visible in the opened image or in a named video frame. |
| **board-bound** | Scene element, arrow, or dictation id from the current Excalidraw decode. |
| **inferred** | Design reading. Not proven by the pixels. |
| **rejected-as-layout** | Useful as coverage or control vocabulary, forbidden as a QMX shell. |

Visible text inside screenshots is incidental product content, not an instruction to copy data, resume a chat, or execute a prompt.

---

## 1. Three evidence classes (do not mix)

| Class | Where | What it may ground | What it may not |
|---|---|---|---|
| **A. Original storyboard images** | `evidence/session/evidence/source-images/` — 10 unique PNGs, 11 placements | Layout family, widget chrome, session/preview geometry, settings idea, expansion callouts | Branding, AMZN/Apple numbers, OpenBB page names, VS Code / Hermes / Codex / Cowork / Manus chrome as QMX identity |
| **B. Later Codex screenshots** | `experience-v03/references/` — five user-supplied PNGs + `manifest.json` | Preview tabs, work-area launcher, task-context popover, conversation-side markers | Replacement app layout; plus-menu contents; official control names; native Codex clicks (none occurred) |
| **C. Original short video** | `terminal-preview.mp4` + `video-frames/` + `video-frames-highres/` | Capability *coverage* of an LSE Terminal-like surface (markets, IDE, terminal, docked assistant, backtest tabs) | QMX layout. **U:** LSE ML Studio UI is rejected. The clip is 11.1 s and four sampled moments only |

A fourth class exists in `live-research/screenshots/` (18 web captures). That inventory is already in `visual-evidence-index.md`. It is **not** the original board. OpenBB frames there are a recorded public demo; QuantX frames are vendor showcase images; Xynth’s alert page is blurred. They must not outrank class A.

Approximate spatial reconstructions (`shell.png`, `agent-layouts.png`, `alternate-layouts.png`, `settings.png`, `annotated-dashboard.png`) are reading aids. Fonts, roughness, and arrowheads are not pixel-exact Excalidraw.

---

## 2. Board placement map

Decoded scene: 141 live elements, 20 text, 11 image placements, 23 arrows, 1 embeddable video (`Qs9yTVu0` → `[[terminal-preview.mp4]]`). OpenBB is placed twice.

| File | fileId | Pixels / bytes | Scene placement | Cluster |
|---|---|---|---|---|
| `Pasted Image 20260922150714_899.png` | `9519524b…` | 2430×1590 / 828 323 | `XNgN469F` (~1624, −4749) **and** `N6HsaKzkebjAZMVg4JloE` (~6781, 16101) | Top layout pair; **and** lower expanded-view cluster |
| `Pasted Image 20260922151452_954.png` | `f5e551b2…` | 1919×1029 / 309 589 | `l34HKwYF` (~3875, −4608), joined by text `or` (`rbuAuIXL`) | Top layout pair |
| `Pasted Image 20260922153805_586.png` | `1efa6f5c…` | 1919×1033 / 683 560 | `ZBR4Py0I` (~5874, −921) | Main-copilot ellipse |
| `Pasted Image 20260922153840_932.png` | `08d58f4f…` | 1919×1029 / 174 440 | `lhI5ub0I` (~5951, 689) | Main-copilot ellipse |
| `Pasted Image 20260922153920_566.png` | `7ea17c73…` | 1919×1026 / 63 739 | `74eMr8Ev` (~5988, 2139) | Main-copilot ellipse |
| `Pasted Image 20260922154128_267.png` | `df49334c…` | 2732×1536 / 561 010 | `bOuRtdFN` (~4544, 6636) | “Or we can try these ones” |
| `Pasted Image 20260922154153_959.png` | `f5779af0…` | 800×449 / 122 750 | `al0Me1H3` (~4736, 8044) | Alternate compositions |
| `Pasted Image 20260922154354_046.png` | `ef4c1922…` | 800×449 / 65 877 | `uNUtaSsB` (~4718, 8806) | First-run / workspace pick |
| `Pasted Image 20260922154421_046.png` | `22180a40…` | 800×561 / 137 378 | `J6WAqID0` (~4652, 9633) | Settings idea |
| `Pasted Image 20260922155654_792.png` | `242a1cf3…` | 532×183 / 44 490 | `d5Z7dzE0` (~10603, 16516) | Message-icon crop beside the second OpenBB |

Hashes in `evidence/provenance.json` match the packet copies. Original paths under `C:/Users/Mubarak/Documents/brain/brain/` are provenance, not a second source of truth.

---

## 3. Source images — one ledger row each

Each subsection: **sampled** geometry, storyboard role, what to preserve, branding **not** to copy, which `02-CURRENT-DIRECTION` / fidelity-reset corrections apply.

### 3.1 OpenBB Workspace — `…150714_899.png`

**Storyboard role:** primary **mini-app layout source**. Board label `UEafaJLm` “this open bb”. Dictation `lDsh2tno` picks this layout (with VS Code as the sibling). Dictation `YJYDP26I` likes the top bar and treats it as reusable / omitable. Full dictation `JHZj5SdT` uses this screen as the dashboard/widget/expand/message example. Placed a second time in the lower cluster as the annotated mini-app.

**Sampled geometry (full-resolution 2430×1590):**

- macOS window chrome; URL `pro.openbb.co`. No QMX-style global activity rail.
- **App-owned top navigation sitting above the widget canvas**, not a permanent left app sidebar: Overview (selected) · Financials · Technical Analysis · Comparison Analysis · Ownership · Company Calendar · Estimates, plus a small edit/close cluster on the right of that bar.
- **Dense two-column widget canvas occupying most of the remaining width** (visually about three-fifths to two-thirds of the content area). Widgets of unequal height:
  - **Ticker Information** — compact sparkline + price / day’s change / volume / sector chips.
  - **Key Metrics** — compact labelled table (Beta, Vol Avg, Market Cap, Range, 52-week High).
  - **Price Performance** — large candlestick + volume histogram; TradingView mark; date-range footer.
  - **Management Team** — scrollable table.
  - **Revenue Per Business Line** — stacked bars with pagination `1 / 4` and a **blue stacked-squares control** at the lower-right of that widget.
- **Repeated widget chrome** on every card: title, ticker chip (`AMZN`), then a row of small actions that read as **history/refresh (clock) · speech-bubble · overflow (⋮) · expand · close**.
- **Substantial right copilot**, full height, visually about one-third to two-fifths of content width. Own title “Revenue Growth Analysis”. Prompt chip, “OpenBB Copilot”, step-by-step toggle, a **rendered results table**, prose analysis, footer chip “Using dashboard widgets”, composer, model picker. Copilot is beside the canvas, not a second left sidebar and not a metadata paragraph.
- A thin left-edge handle / dock remnant is visible; it is not a destination rail.

**Preserve:** app-specific top nav over a *working* canvas; mixed widget sizes with real charts/tables/controls; optional right copilot of meaningful width; per-widget history / discuss / edit / expand / close; linked ticker parameter across widgets; canvas majority vs copilot minority (copilot is large, not a strip, but it does not eat the dashboard).

**Do not copy:** OpenBB / “Open Bloomberg” / Bloomberg Terminal branding; AMZN prices and Apple revenue table; page names Overview/Financials/… as QMX IA; TradingView watermark; Copilot product chrome; the assumption that OpenBB’s speech-bubble *is* QMX attach-to-copilot, or that the blue squares *are* Library.

**02 corrections:**

- Reconstruct the mini-app from this OpenBB/VS Code relationship. **No invented permanent app sidebar** (study 03 failure).
- Populate widgets with realistic charts/tables, not explanatory cards.
- Expanded widget must show detailed working content, not a metadata paragraph. Top-tab/menu expansion is the user’s *proposal*; exact behavior remains open (`02` table “Still to design”).
- Copilot is **optional per app**. This screenshot shows one on; that is not a mandate for every destination.
- Shared global rail is a QMX requirement from dictation, **absent from this screenshot**. Do not freeze OpenBB’s missing rail as QMX geometry.
- “Open Bloomberg” in dictation names this OpenBB image. Do not substitute Bloomberg Terminal behavior.

---

### 3.2 VS Code + right agent — `…151452_954.png`

**Storyboard role:** **layout sibling** to OpenBB, not a second product to clone. Joined by `rbuAuIXL` “or”. `lDsh2tno` (verbatim): the speaker shifted to VS Code because “the layout is kind of similar, if not very, very the same” and “the layout is what I’m picking.” `02` assigns the **authoring/ML** surface to an “original app/VS Code-like family” (central graph/code, detail expansion, right copilot).

**Sampled geometry (1919×1029):**

- Narrow **activity rail** on the far left (Explorer, Search, SCM, Run/Debug, Extensions, account/settings).
- **Editor group as the large centre:** markdown tabs across the top (`qml-research-epics-handoff.md` active among several files); line numbers; dense document. This is a working surface, not a splash.
- **Right agent panel of substantial width** (visually around two-fifths of the window — a more even split than OpenBB’s canvas/copilot). Panel tabs: Chat · Claude Code · Claude Code · **Codex**. Conversation, “Edited 5 files” card with paths, composer with `+`, “Ask for approval”, model picker, “IDE context”.
- Status bar across the full bottom.

**Preserve:** work-area + adjacent copilot as one family with OpenBB; tabbed documents in the work area; right conversation that can show diffs/file cards without replacing the editor; a *narrow* left rail of destinations (this is closer to QMX’s **platform rail** than OpenBB’s screenshot, but VS Code’s rail is *activity* icons, not QMX’s home/divider/opened-apps story). Authoring/ML should feel like this family, not like LSE’s Train/Optimise form.

**Do not copy:** VS Code product chrome, Codicon set, Claude Code / Codex tab labels, the markdown document (historical QMX research text — incidental, not current authority), GPT model names, “Work locally”.

**02 corrections:**

- This is **not** the main-copilot sessions/history screenshot. Sessions/history live on Hermes/Codex/Cowork (`C39LFtm1`). Do not flatten VS Code’s explorer/activity bar into a generic secondary sidebar on every mini-app.
- Do not let later Codex *preview* screenshots reshape this work canvas.
- LSE ML Studio UI is rejected; develop this graph/code workspace with right copilot and node/detail expansion instead.
- Parent note `00-orchestrator-image-notes.md` labelled this “main copilot proportions.” That over-assigns. Board geometry puts it in the **OpenBB “or” pair**; `02` puts the VS Code-like family on **authoring/ML**. Main copilot’s conversation column is the Hermes/Codex cluster.

---

### 3.3 Hermes Agent — `…153805_586.png`

**Storyboard role:** **main-copilot layout reference** — sessions/history left, conversation centre, tabbed preview right. Board text `C39LFtm1` (“open sessions, history, settings for the agents”) and `rrUMAlEq` (preview pane for browser, mini-apps, widgets, workflows, CLI, strategy/model, diff, terminal). Clustered with Codex and Cowork inside the large agent ellipse.

**Sampled geometry (1919×1033):**

- Far-left icon strip plus a **SESSIONS | BOTS** column: New session, Capabilities, Messaging, Artifacts, Scheduled jobs, Crew, Kanban, search, PINNED sessions, HOME project list with message counts.
- **Centre:** tab row `NEW SESSION` · `TERMINAL` · `+ NEW SESSION`. Branded splash “HERMES AGENT” and a composer (`Give Hermes a task`, git chip `main`, `1 changed`, model picker).
- **Right:** tab row `LOCALHOST` · `BROWSER` · `+`, address `about:blank`, empty browse prompt. Preview is a first-class column, not a drawer.
- Approximate thirds: session list / conversation / preview. Preview is as wide as conversation.

**Preserve:** main-copilot *interior* as three regions (session/history, conversation, flexible tabbed work/preview). Browser and terminal as preview types. Composer at the bottom of the conversation column. Extra session tabs.

**Do not copy:** Hermes branding, splash copy, bot/crew/kanban nouns, “Grok 4.6 Ultra”, version footer. Do not impose this left session list on mini-apps (`layout-fidelity-reset`).

**02 corrections:** keep this layout specific to the main copilot. Shared copilot capability with independently scoped conversations is accepted; identical panels in every app are not.

---

### 3.4 Codex desktop (storyboard) — `…153840_932.png`

**Storyboard role:** second main-copilot variant, especially **work-area launcher** in the empty right pane. Same family as Hermes. Chat contents are incidental (a prior “Restart QMX UI design” thread).

**Sampled geometry (1919×1029):**

- Left: **Codex** header, New chat, Pull requests, Scheduled, Plugins, Explore, Pinned, Projects (`data_narl`, `STRATS`, `QMX`, `sdl-factory`).
- Centre: conversation titled “Restart QMX UI design”, bubbles, “Worked for 2m 19s”, composer with **`+`**, **Full access**, model picker, mic.
- Right: empty dark pane with five stacked launchers and shortcuts: **Review** `Ctrl+Shift+G` · **Terminal** `Ctrl+\`` · **Browser** `Ctrl+T` · **Files** `Ctrl+P` · **Side chat** `Ctrl+Alt+S`. This is the same launcher later captured as Codex ref `04-work-area-launcher.png`.
- Composer `+` is **visible, not expanded**.

**Preserve:** conversation column that stays useful while the work area is empty; explicit launch of Review / Terminal / Browser / Files / side chat as preview types (`rrUMAlEq`). `+` as a compact composer entry (contents unknown).

**Do not copy:** Codex product IA, project names, “Full access”, chat transcript, shortcut chords as QMX requirements.

**02 corrections:** later Codex refs inform **preview/conversation controls**, not a replacement app layout. Native Codex was not operated. Plus menu unobserved.

---

### 3.5 Cowork empty home — `…153920_566.png`

**Storyboard role:** **empty / start-state** variant of the agent workspace. `viURg15y` (upper wireframe as a possible “up layout”) sits with the top sketch; this screenshot is the spacious composer-first landing in the agent cluster.

**Sampled geometry (1919×1026):**

- Narrow left nav: Cowork | Code toggle; New, Projects, Artifacts, Scheduled, Customize; Tasks; user chip.
- Vast empty centre. Greeting “You’re here!” then a **centred composer** (`Type / for skills`, `+`, model picker, send), a project/folder chip, and three idea links.

**Preserve:** a start state that is mostly working space, not a wall of study notes. Composer-first empty home is allowed for the main copilot. Persistent left destinations.

**Do not copy:** Cowork branding, daisy mark, “GPT 5.6 Sol (native)”, the three idea prompts, Code/Cowork product split.

**02 corrections:** startup/splash/first-run is in scope (`02` U, UX-01) but this screen is not the PyCharm/DaVinci splash the user asked for, and it is not the mini-app canvas. Do not let a centred empty composer become the mini-app interior.

---

### 3.6 Manus project home — `…154128_267.png`

**Storyboard role:** **alternate composition** under `EIWGwk1g` “Or we can try these ones”. Evidence that an app interior may use a **left app nav + project body**, not OpenBB’s top tabs. Not a requirement to adopt Manus nouns.

**Sampled geometry (2732×1536):**

- Left: New task, Agents, Search, **Library**, Projects (`Fones` selected), All tasks list, share promo, bottom view icons.
- Centre: project header, composer with attach/tools, three cards **Instructions / Files / Skills**, a Tasks list.
- Onboarding popover “Hide tasks in the Project” (incidental).

**Preserve:** interiors **differ by destination** (`02`: switching app must change navigation and working composition). Library as a reachable destination is a lead. Project-scoped instructions/files/skills is a mental model for authoring context, not a taxonomy lock.

**Do not copy:** Manus branding, credit promo, “Manus 1.6”, the left nav as a universal shell. **Do not** take this left nav and put it on every mini-app (the exact study 03 error).

**02 corrections:** Library/authoring have room to design; this is not approval of the rejected Library mock. A copilot is optional; this screenshot does not even show one.

---

### 3.7 Voices / library empty — `…154153_959.png`

**Storyboard role:** **library browsing + filter column** reference, independent of the voice domain. Same alternate cluster.

**Sampled geometry (800×449):**

- Left grouped nav: VOICE TOOLS, **LIBRARY** (Voices selected), LIVE, STUDIO, PLATFORM.
- Second column: Filters (Search, Category, Language, Accent, Use case chips, Reset).
- Main: “No voices found” empty state with three creation actions (Design a Voice, Instant Clone, Pro Voice Clone). Active filter chips on the content header.

**Preserve:** grouped destinations; a filter column beside results; honest empty state with creation entries (UX-05 / empty-state checklist). This is closer to Library than to a dashboard.

**Do not copy:** voice-product IA, “NewCompany”, filter chip colours, “Design a Voice”.

**02 corrections:** no accepted Library taxonomy. Do not freeze a two-column filter chrome as the only Library.

---

### 3.8 Select Workspace — `…154354_046.png`

**Storyboard role:** **first-run / reconnect target picker** (local vs remote). Dictation and `02` U both require startup, provider/CLI-proxy, and target connections. `qhuD191N` sits nearer the settings screenshot; this dialog is the selection form in the same alternate stack.

**Sampled geometry (800×449):**

- Dark app chrome: Dashboard · Sessions · Droids; user menu.
- Centred card **Select Workspace**: Local | Remote tabs, Search, `+ New Workspace`, radio list (local and remote rows, some with `main` / `gh-pages`), **Back** / **Next**.
- Bottom composer still present (“Type @ to search your codebase”).

**Preserve:** local vs remote as an explicit choice; search + create + list + progression. First-run can be a card without inventing a compulsory wizard.

**Do not copy:** “Droids”, orange brand buttons, listed workspace names, the leftover composer-as-global-chat.

**02 corrections:** UX-01 launch/first-run/reconnect. Exact provider mechanism unverified. This is not the mini-app canvas.

---

### 3.9 SETTINGS — `…154421_046.png`

**Storyboard role:** **settings idea**, not a locked settings IA. Board text `qhuD191N`: “this is an idea setting or settings page… this one is global, and I believe each app needs its own.”

**Sampled geometry (800×561):**

- Title SETTINGS + subtitle.
- Category tabs: General · Integrations · **Session** (selected) · API Keys · Billing & Usage.
- Cards: Local Repositories (empty), Factory Bridge (path + Browser Tools toggle), **Remote Workspaces** table (NAME, REPOSITORY, BRANCH, CREATED BY, CURRENT STATUS Success/Failed, ACTIONS).

**Preserve:** global settings as a distinct surface; tabbed categories; session vs API keys vs integrations as separable; a table of remote targets with status. Per-app settings remain an open design (`02` table).

**Do not copy:** billing tab as a QMX requirement, Factory Bridge product, orange Create Workspace, this vendor’s session model.

**02 corrections:** scoped settings are in the shared-conventions list. Provider credentials/API keys and CLI proxy belong in first-run/settings, not inside every widget.

---

### 3.10 Ticker Information crop — `…155654_792.png`

**Storyboard role:** **message-icon / compact-widget callout**. Board text `nLB3FO70` “message icon”. Dictation: the speaker cropped this because the icon is small; “it’s like a message icon with a plus in between”; “it’s global, so it’s almost on every widget”; proposed as the way to connect widgets/apps to the copilot.

**Sampled geometry (532×183):**

- One compact widget: title **Ticker Information**, ticker chip `AMZN`, then header actions **clock · speech-bubble · overflow · expand · close**.
- Body: green sparkline, Price `$220.79`, Day’s Change `↑ 0.91 (+0.42%)`, “Trading Inside of the Normal Range”, Volume, Specialty Retail | US | NASDAQ.
- The speech-bubble is the circled target in the lower cluster (red ellipse `Oh8I9yu3` on the crop). A **plus superimposed on the bubble is not unmistakable** in this crop; that plus is **dictation wording**, not a clear pixel.

**Preserve:** compact summary that is still a *working* widget (chart + metrics + chrome), not a caption. Repeated discuss/expand actions in the header. Compact vs expanded is a real content change (`JHZj5SdT`: ticker is a summarized preview; zooming in must fill in the data).

**Do not copy:** AMZN figures, OpenBB icon glyphs, the claim that OpenBB’s bubble already implements QMX attach-to-copilot.

**02 corrections:** attaching context must not silently grant permissions. Shared copilot with independently scoped conversations. Widget-level discuss is a QMX control to design; do not clone the glyph.

---

## 4. Lower expanded-view cluster (the “bottom of the board”)

This is the cluster the operator said was under-read. Group `EgXLF6bkT_kJu_EzejnIu`: second OpenBB placement + ticker crop + eight red/blue arrows + the 16 804-character dictation `JHZj5SdT`. Separate orange group `4AaMrriVEU1CBbzD3I7Xm` is the expanded-view annotation.

| Callout id | Colour | What the arrow is bound to | User wording | QMX reading (inferred) | What the screenshot does **not** prove |
|---|---|---|---|---|---|
| `w6Wra1LH` | red | Expand control on Ticker Information | “this is the exapansion tool” | Compact → detail. Dictation proposes a **new top tab/menu**, browser-like | OpenBB docs (`openbb.md`) describe resize and in-widget view toggles, **not** a documented new-tab expansion |
| `Ibr804Se` | red | Clock on widget chrome | “history thing i mentioned” | Per-widget history | Clock might be refresh; OpenBB docs mention refresh frequency. History semantics are QMX |
| `Y3XcLbSh` | red | Overflow / edit cluster | “this thing (editing the set up of widgests)” | Layout/widget edit | Overflow menu contents not captured |
| `nLB3FO70` | red | Speech-bubble on the **crop** | “message icon” | Attach/discuss this widget with the (scoped) copilot; global on widgets | Plus-on-bubble not clearly visible; OpenBB “Add to context” is documentation, not this click |
| `wLhO8DpA` | red | Lower-right of Revenue widget | “thing at the bottom i mentioned” | Add panel / add widget | Dictation also says “I don’t know what it does.” OpenBB docs mention a plus at the dashboard lower-right for adding widgets |
| `C2K3xORn` | red | Revenue Per Business Line chart | “risk mgt and bms stuff” | Dense quantitative widget as a **pattern** for Book/BMS / local-vs-server cues | The source widget is revenue mix, not risk. Blue icon as “trading node local/server” is a QMX adaptation |
| `NJidF6Tg` | **navy, thick** | Control near copilot table / blue squares | “this can help s go from preview mode to library” | Jump from preview to **QMX Global Library**. Dictation **self-corrects**: not a new top tab; **return to the platform sidebar** | OpenBB’s control is not a library router. Screenshot cannot prove the jump |
| `hoGJ6iaL` | **orange** | Arrow `PU0175lM` starts at **empty** rect `h9v3h1pU`; **end unbound** | “this is for the expanded view of a widget or workflow” | Expanded detail is a further view, for widget **or** workflow | No image target. Do not invent which widget it points at (`dictation-audit`) |

**Navigation levels the dictation separates** (keep them separate):

1. Platform rail: home / defaults **above a divider**, opened mini-apps **below** (`JHZj5SdT`; `02` U).
2. App-owned menus: Overview vs Financials vs Technical Analysis as **dynamic in-app sections**, not a permanent left sidebar. Overview is a summary; other sections are the app’s widgets.
3. Widget/workflow **expansion**: may open a top tab/menu with a detailed working surface. Behavior still open (`02` P: select for inspector, explicit expand into a detail tab, preserve return).

Study 03 collapsed (2) into a generic secondary sidebar and replaced (3) with prose. That is the failure `layout-fidelity-reset.md` records.

---

## 5. Codex refs (class B) — five user-supplied screenshots

Copied 2026-09-23. Manifest hashes in `experience-v03/references/manifest.json`. Evidence type: **user-supplied screenshot; not live computer-use**. Native Codex controls were unavailable; **no plus menu was expanded** (manifest line: “None of these screenshots shows the expanded plus menu. No menu contents inferred.”). `02`: “The red-circled Codex screenshot is a conversation-navigation reference; its official name/complete behavior is unverified.”

These shots show Codex **hosting** a rejected study-02 HTML preview. The HTML’s mint-green Copilot, “Research review / App planning” column, and “ML studio” rail are **study 02**, which `02` rejects as aesthetic/layout baseline. Use the **Codex chrome around** that preview, not the preview’s styling.

### 5.1 `01-workspace-preview.png` — 1919×1028

**Sampled:** Codex conversation left (“Review QMX UI storyboard”), file-edit card, composer with `+` / Full access / GPT-6 Astra High. Right work area is a **browser tab** `QMX - Main wo…` beside a **Subagents** tab, address bar pointing at `experience-v02/main-workspace.html`. The loaded page is study 02 (left rail Copilot/Library/Authoring/OPEN APPS, dual conversation list, “What are we working on?”, Attach chip, mint Send). User bubble in the left conversation **rejects that styling** while keeping preview/ask-question ideas.

**Role:** tabbed **workspace preview beside the conversation**.  
**Preserve:** conversation remains usable while a document/app preview occupies the work area; Subagents and Browser as sibling tabs.  
**Do not copy:** study 02 tokens, mint buttons, dual-conversation column, “ML studio” label as a rigid app.  
**02:** user rejects study styling; Codex is the host, not the app layout.

### 5.2 `02-tabbed-subagents.png` — 1906×1029

**Sampled:** same conversation left (now with image thumbnails above the user bubble). Right: **Subagents** tab selected; Browser tab still present; `+` to add a tab. List: Active 0; Done 7 (Design rules, Evidence catalog, Xynth prime live, Openbb live research, Dictation coverage, Backend inventory, Video reference) with relative times.

**Role:** the **same right-hand work area** hosts a Subagents view, not only a browser. Composer can carry image thumbnails.  
**Preserve:** work-area tabs that switch *kind* (browser / subagent list / later review/terminal).  
**Do not copy:** this run’s subagent names as QMX IA.  
**Inferred, not sampled:** how a subagent is opened, attached, or permissioned.

### 5.3 `03-task-context-panel.png` — 1919×1032

**Sampled:** conversation continues; a **floating context card** on the right: project **QMX** / branch **main** with line stats; **Subagents** “7 done” with colour dots; **Sources** (github.com/vercel-labs/json-render, ChatGPT App Tools, Web search, View all) and a `+` on Sources.

**Role:** inspect **what this task can see** (project/branch, subagents, sources) without being a plugin-attachment UI.  
**Preserve:** a compact, dismissible context inspector separate from the composer.  
**Do not copy:** GitHub-centric “Sources”, ChatGPT App Tools. Manifest: “Does not show plugin attachment semantics.” Local `plugin.json` files establish package shape only (`plugin-reference.md`).

### 5.4 `04-work-area-launcher.png` — 1914×1034

**Sampled:** conversation left with four image thumbnails. Right pane empty except the same five launchers as the storyboard Codex screenshot: Review, Terminal, Browser, Files, Side chat, with shortcuts.

**Role:** **empty work-area launcher** — the control that turns the right column into a typed preview.  
**Preserve:** explicit, labelled entry points for review/diff, terminal, browser, files, side chat. Matches `rrUMAlEq`.  
**Do not copy:** shortcut table; do not treat this launcher as mini-app chrome.

### 5.5 `05-conversation-navigator.png` — 1919×1028

**Sampled:** user **red ellipse** around the **left edge of the conversation column**. Visible: a vertical stack of short tick/marker lines; a **hover-style card** of an earlier exchange (“Morning. So, I’m going to give you access…”) with a **bookmark** icon; the current long user bubble continues below. Task-context card still at far right. Composer `+` still unexpanded. A small overlay at the bottom-right of the bubble records the user asking to try “this plus icon” and noting the preview is on the right — the plus menu itself is **not** open in the frame.

**Role:** **conversation navigation** — jump/preview earlier turns from a left-edge marker, with an optional bookmark.  
**Official name:** **unverified**. Do not call it “timeline”, “minimap”, or “bookmarks rail” as if Codex documented that. Manifest: “exact interaction not tested.”  
**Preserve as a QMX question (UX-03):** long conversations need a way back to earlier exchanges without scrolling blindly.  
**Do not copy:** the red circle (user annotation), Codex’s undocumented marker behavior as a spec.

**Plus menu (all five shots):** the `+` control is visible on the composer. **Contents were never captured.** Do not infer Tools / plugins / files / apps from these pixels. `02` and `plugin-reference.md` already forbid that inference.

---

## 6. Video — sampled frames vs inferred behavior

**Source:** `C:\Users\Mubarak\Documents\brain\brain\terminal-preview.mp4` (4 948 211 bytes, SHA-256 `9de8b26e…`). Board label `4AhOiPPo` “lse vide”. Scene embed `Qs9yTVu0`.

**Method (from `video-reference.md`, confirmed by opening the JPEGs):** no audio transcript; mp4 not played in this pass. Four encoded keyframes at 512×288, then the **same timestamps** at 1600×900: 00:00, 00:01, 00:05, 00:09. Clip length ~11.1 s. Intermediate clicks, hovers, and speech are **not** established.

### 6.1 Sampled (visible in named frames)

| Timestamp | Files | What is on screen |
|---|---|---|
| **00:00** | `frame_0001.jpg` / `cue_0000.jpg` | Window title **“EUR/JPY 1h - LSE Terminal.”** Header **London Strategic Edge**. Top sections **Markets** (selected), Backtest, Economic, Workspace, Research. Markets subview **Price & Charts** (Options, News, Screener adjacent). Centre: EUR/JPY 1h candlesticks with overlay and a sharp drop then recovery. Left **Watchlist** grouped by asset class (Forex, Stocks, Crypto, Indices, Commodities, …). Right **trading ticket** EUR/JPY Buy/Sell plus docked **LSE Assistant** with three suggested prompts (risk check, 2y/10y yields, Z-score mean-reversion). Bottom positions: balance/equity and a BTC/USD row. Windows taskbar visible (this is a desktop capture, 16 Aug 2026 in the clock). |
| **00:01** | `frame_0002.jpg` / `cue_0001.jpg` | **Workspace** selected. Sub-tabs **IDE, Data Visualisation, Notebook**. File `curve_regime_overlay.py` open. Left: **Library** (Import LSE Data), **Workspace (15)** strategy scripts, **Data (11)** sample files, **Notebooks (0)**. Centre: Python editor; lower **Terminal** pane (Windows cmd prompt). Right: LSE Assistant with quick actions `list_datasets`, `preview_dataset`, `run_backtest`, `read_guide` (one label clipped). |
| **00:05** | `frame_0003.jpg` / `cue_0002.jpg` | Still Workspace / IDE / same file. High-res **corrects** the low-res impression of a blank workspace. Assistant shows user prompt: *“Long spx500 only when the 3m10y curve is not inverted and price is above its 200 period moving average. Backtest it.”* Collapsed activity row beneath. **No backtest result.** |
| **00:09** | `frame_0004.jpg` / `cue_0003.jpg` | Title **“GOLD - Gold 1h - LSE Terminal.”** **Backtest** selected; sub-tabs **Algo Development, Machine Learning, Manual**. Editor tabs include `spx500_curve_ma200_trend.py` selected. Library/Workspace/Data remain. Terminal still open. Assistant shows generated strategy/code, **Copy** and **To strategy IDE**, and a follow-up: run on SPX500 1h, walk-forward or cost pass. Cursor over those actions. **No metrics, no completed run.** |

Low-res 512 px frames are the same four moments; high-res is for label reading. Fine type can still be soft.

### 6.2 Inferred (not in the frames)

- Any click path between 00:00 → 00:01 → 00:05 → 00:09 (how Markets became Workspace, how Backtest opened, whether the assistant actually ran a backtest).
- Dataset import completion, model training, walk-forward execution, fill quality, live exchange connectivity.
- Meaning of “LSE” as a legal name, or that QMX must ship a watchlist + ticket + positions strip.
- That **Machine Learning** as a Backtest sub-tab is a graph/code studio. The tab **label** is sampled; no training UI is shown. Public **ML Studio** (`lse-ml-studio.png` in live-research) is a **different** surface (Train/Optimise form) and is **rejected as QMX layout** (`02` U).

### 6.3 What the clip may inform (coverage only)

Docked assistant beside a domain workspace; Library / workspace files / sample data / notebooks as left resources; editor + **terminal** as a lower pane; top-level sections that change the interior (Markets vs Workspace vs Backtest); suggested prompts and “send to IDE”. These are **capability vocabulary** for UX-07/08/09/12, not a shell to reproduce.

**Do not copy:** LSE branding, EUR/JPY demo account, the Markets-first terminal chrome, the Train/Optimise ML Studio form, paper-trading chrome on non-trading tools.

---

## 7. OpenBB vs VS Code proportions (the layout pick)

`lDsh2tno` is explicit: pick **the layout**, quoting the similarity. Side-by-side from the opened pixels:

| Region | OpenBB (mini-app example) | VS Code (authoring/ML family) | QMX obligation |
|---|---|---|---|
| Far left | Almost none (tiny handle) | Narrow activity rail | QMX **platform rail** is from dictation, not from OpenBB. Keep it narrow. Do not grow it into study 03’s secondary sidebar |
| Primary work | Widget canvas, **majority** width, dense charts/tables | Editor group, **majority** width, dense document | Substantial working surface. No prose-card substitute |
| Top of work | **App-owned page tabs** (Overview…) | **Document tabs** | App/authoring owns this row. Reusable; some apps omit it (`YJYDP26I`) |
| Right | Copilot ~⅓–⅖, full height, results table + composer | Agent panel ~⅖, conversation + file cards + composer | Optional, independently scoped, **wide enough to work in** |
| Bottom | Widget footers / date range | Status bar; VS Code has no extra session list here | Terminal may dock in the **main copilot preview** (`rrUMAlEq`), not necessarily under every mini-app |
| Secondary sidebar | **Absent** | Explorer is not the hero in this shot | Do not add a permanent app sidebar “because VS Code has one” |

Hermes/Codex then **rearrange** that family for the main copilot: they spend the left column on **sessions/history** and keep a tabbed preview as the right (or centre-right) work area. That rearrangement is destination-specific.

---

## 8. `02-CURRENT-DIRECTION` corrections that these pixels must survive

Drawn from `02` U/P rows and `layout-fidelity-reset.md`. Applied to this ledger:

| Correction | What the images would get wrong if ignored |
|---|---|
| Original Excalidraw images **outrank** later Codex / dashboard / n8n / LSE | Using `01-workspace-preview.png`’s study-02 HTML as the mini-app; using LSE Terminal as the shell |
| Differentiated interiors: main copilot ≠ mini-app ≠ authoring | One three-column template everywhere (study 03) |
| Main copilot = sessions/history + conversation + tabbed preview | Treating OpenBB’s widget canvas as the main agent, or Hermes’ session list as mini-app chrome |
| Mini-app = app nav + substantial widget canvas + optional right copilot | Moving Overview/Workflows/Results into a left sidebar |
| Authoring/ML = VS Code-like family; **not** LSE ML Studio Train/Optimise | Recreating the public ML Studio form (`lse-ml-studio.png`) as default ML UX |
| Widgets need charts/tables/controls and real expansions | Metadata banners, “this would be a chart” cards |
| Codex refs = preview/conversation controls only | Reshaping the app canvas to match Codex’s launcher |
| Conversation-nav official name unverified; plus menu unobserved | Specifying a Codex “minimap” or plus-menu contents |
| Study 02/03 rejected; assistant owns the error | Inheriting mint tokens or attachment picker |
| Library/authoring not approved by the rejected mocks | Shipping Manus/Voices chrome as Library |
| Neutral dark baseline later; geometry/density **now** | Treating “aesthetics undecided” as permission to go sparse |
| Paper trading only where trading/risk runs | Putting a ticket/positions strip on every app because 00:00 of the video has one |
| Headless/optional copilot | Requiring the OpenBB right column on every capability |

---

## 9. Especially called-out controls

### Message-plus icon

- **Pixels:** speech-bubble in every OpenBB widget header; cropped in `…155654_792.png`; circled by `nLB3FO70`.
- **Dictation:** “message icon with a plus in between,” global on widgets, path from widget to copilot.
- **Honesty:** plus overlay is **not clearly sampled**. Design the *behavior* (scoped attach/discuss) rather than the OpenBB glyph.
- **Must not:** merge main-copilot and app-copilot sessions (`02` U). Mini-app copilot has different permissions/tools (`JHZj5SdT`).

### Library jump

- **Pixels:** navy thick annotation `NJidF6Tg` on a blue control near the copilot table / revenue widget’s stacked-squares.
- **Dictation path:** first “open Global Library as a top tab in any mini-app,” then **correction:** click returns to the **sidebar**.
- **Honesty:** OpenBB does not document this control as a library router (`openbb.md`). QMX Library is still undesigned (`02` table).

### Widget / workflow expansion

- **Pixels:** expand icon on widget chrome (`w6Wra1LH`); compact ticker vs large Price Performance as two densities on the same dashboard; orange unbound annotation `hoGJ6iaL`.
- **Dictation:** expand may open a **new top tab/menu** with a detailed view; applies to widget **or** workflow; speaker calls it hard and leaves it open.
- **`02` P:** select → compact inspector; explicit expand → detail tab/work area; preserve graph/app viewport and return. Prototype against these arrows before locking.

### Codex conversation navigation

- **Pixels:** `05-conversation-navigator.png` red circle, left-edge markers, hover preview, bookmark icon.
- **Name/behavior:** unverified. Not operated.
- **Use:** UX-03 long-thread wayfinding. Not a layout source.

### Plus menu

- **Pixels:** `+` on Codex composers (storyboard `…153840_932.png` and refs 01/04/05).
- **Contents:** **not captured.** Local plugin manifests ≠ picker behavior. Do not invent Tools/plugins/files/apps rows.

---

## 10. Live-research visual index — how it sits beside this ledger

`visual-evidence-index.md` inventories **18 web captures** from the afternoon reference pass. Useful as *comparison* when a QMX interaction is still unresolved (`final-reference-pass.md` same rule). Limits that matter here:

- OpenBB `openbb-dashboard.png` / `openbb-copilot-panel.png` / `openbb-app-gallery.png` are **recorded-demo** frames, not the user’s 2430×1590 storyboard PNG. Prefer the storyboard OpenBB for proportions.
- LSE ML Studio captures are **actual public controls** and are **layout-rejected**.
- QuantX images are **vendor showcase**, not an operated editor.
- Minara chat/strategy/workflow are actual public apps; asset-copilot doc capture is **broken**.
- Prime matrix vs expanded detail is layout evidence with a date inconsistency.
- Xynth alert screenshot is **blurred**.

`grounding-summary.md` is the whole-board reminder: home + divider + opened apps; main agent vs mini-app vs widget detail vs scoped copilot vs global library vs authoring. This file supplies the **pixels** behind those rows.

`dictation-audit.md` is the text/binding proof (20 text ids, unbound orange arrow, eight screenshot arrows). This file does not re-transcribe `JHZj5SdT`.

---

## 11. Disagreement with `00-orchestrator-image-notes.md`

Keep the parent’s pixel descriptions; correct one assignment:

- `00` called VS Code “**main copilot proportions**.”
- Board placement, `lDsh2tno`, and `02`’s authoring/ML row put VS Code in the **OpenBB layout pair** and the **graph/code family**.
- Main-copilot session/history geometry is **Hermes / storyboard Codex / Cowork**.

Both OpenBB and VS Code still teach “large work + right copilot.” That shared geometry is real; the destination mapping is what `00` over-compressed.

---

## 12. Unresolved on purpose

- Exact expand interaction (tab vs split vs overlay vs replacement) — user left open; `02` offers a proposal to prototype.
- Whether every widget must carry history/discuss/edit/expand/close.
- Library object types, ownership, unavailable states.
- Plus-menu contents; conversation-marker official behavior.
- How terminal docks in mini-app vs main copilot vs authoring.
- Whether local-vs-server status uses a blue node glyph (`C2K3xORn` / dictation) or another cue.
- Widget, workflow, and standalone mini-app representations other than this one dashboard (`JHZj5SdT` says those have not been looked at).
- No QMX UI was rendered or Reticle-proved in this pass.

---

## 13. Source paths (packet-local)

- Storyboard images: `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/evidence/source-images/`
- Codex refs: `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/experience-v03/references/`
- Video notes: `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/video-reference.md`
- Sampled frames: `…/video-frames/frames/frame_0001.jpg`–`frame_0004.jpg` and `…/video-frames-highres/frames/cue_0000.jpg`–`cue_0003.jpg`
- Live-research index: `…/live-research/visual-evidence-index.md`

End of ledger. No implementation.
