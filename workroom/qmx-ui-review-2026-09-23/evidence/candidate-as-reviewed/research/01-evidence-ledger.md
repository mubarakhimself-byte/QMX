# Evidence ledger — original Excalidraw storyboard

**Sitting:** architecture-QMX-UI-2026-09-23  
**Ledger date:** 2026-09-23  
**Class legend:** **U** = current user direction; **P** = assistant proposal to evaluate; **E** = observed evidence; **historical** = superseded by later user correction or withdrawn study.  
**Precedence:** `02-CURRENT-DIRECTION.md` overrides historical studies. The original Excalidraw images and full dictation remain the foundation. Later Codex, dashboard, n8n, and live-research captures add context; they do not replace this board.

This ledger distinguishes **observation** (what is on the board or in a PNG) from **inference** (what a later reading or study claimed). Coordinates are from `scene-text.json` / `scene.json` of the afternoon board.

---

## 1. Provenance

| Item | Path / fact |
|---|---|
| Live original | `C:/Users/Mubarak/Documents/brain/brain/Excalidraw/qmx-ui-storyboard.md` |
| Afternoon extract (authoritative for this sitting) | `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/live-research/board-current/` |
| Afternoon source copy | `.../board-current/qmx-ui-storyboard.source.md` |
| Afternoon scene text (20 ids) | `.../board-current/scene-text.json` |
| Afternoon decoded scene | `.../board-current/scene.json` |
| Attachment map | `.../board-current/attachments.json` |
| Afternoon provenance | 99,181 bytes; last write `2026-09-23T12:24:53`; SHA-256 `12046358167505791BC11CE13C19463C87FFEBB4FBB5EAEACB3ABD19034456F1` (`board-current/provenance.json`) |
| Morning snapshot (superseded as live file) | `.../evidence/session/evidence/qmx-ui-storyboard.source.md`; 99,027 bytes; SHA-256 `2c27d55f4414e2c044bcbc2be36e087503fbe34655a258b1bfefac4d1d89e929` (`evidence/provenance.json`) |
| Dictation audit | `.../evidence/session/live-research/dictation-audit.md` |
| Initial reading (incomplete vs afternoon audit) | `.../evidence/session/storyboard-reading.md` |
| Layout correction | `.../evidence/session/layout-fidelity-reset.md` |
| Current direction | `.../02-CURRENT-DIRECTION.md` |
| Source map | `.../04-SOURCES-AND-SKILLS.md` |
| Unique PNGs (10) | `.../evidence/session/evidence/source-images/` |
| Later website captures (not original board) | `.../evidence/session/live-research/visual-evidence-index.md` |

**Observation.** Afternoon scene: 141 live elements; 20 text; 11 image placements; 23 arrows; 61 rectangles; 6 diamonds; 6 lines; 12 ellipses; 1 freedraw; 1 embeddable. Ten unique PNGs; OpenBB file is placed twice. Markdown `## Text Elements` IDs match `scene-text.json` (dictation-audit: no wording differences after wrapping/whitespace normalize).

**Observation.** The seven website URLs are **not** separate text elements. They sit inside `JHZj5SdT`. The only scene-level element link is embeddable `Qs9yTVu0` → `[[terminal-preview.mp4]]`.

---

## 2. Board geography (layout regions)

Approximate canvas clusters from `scene.json`. Names below are **ledger region names**, not labels printed on the board.

| Region | Group / cluster | Approx. coords | What sits there |
|---|---|---|---|
| **A. Mini-app shell wireframe + layout refs** | `EWgyhr4XBq2FOzt9BNnHG` | x ≈ −3445…5600, y ≈ −5355…−3400 | Hand-drawn shell, top-bar callout, OpenBB overview placement, VS Code placement, texts `YJYDP26I`, `viURg15y`, `UEafaJLm`, `lDsh2tno`, `rbuAuIXL` |
| **B. Main-copilot wireframe** | `Uxd5W2WO_kbnYcWxjf66n`, `jviA8oKKkH8bWxU3GaVlg` | x ≈ −2795…1900, y ≈ 740…2700 | Compact vs expanded copilot sketches; texts `tD33M0Ny`, `rrUMAlEq`, `C39LFtm1` |
| **C. Agent-workspace screenshot stack** | `znF7wW2xoyBf4hoa8hPzw` (inside `jviA8oKKkH8bWxU3GaVlg`) | x ≈ 5870…7550, y ≈ −921…2970 | Hermes, Codex, Cowork images; arrows from the copilot sketch |
| **D. Alternate-layout cluster** | `8deutGIVcWyUeDW210tbp` | x ≈ −727…6200, y ≈ 6636…10450 | Diamond `EIWGwk1g`; Manus, Voices, workspace-selector, Settings images |
| **E. Isolated settings note** | `Fs06Cdeht8F4k_-itNjU3` | x ≈ 15462, y ≈ 1741 | Text `qhuD191N` only (no image in that group) |
| **F. Annotated mini-app example** | `EgXLF6bkT_kJu_EzejnIu` | x ≈ −6185…11700, y ≈ 15700…31070 | Large OpenBB placement, ticker crop, red/navy annotations, full dictation `JHZj5SdT` |
| **G. Expanded-view callout** | `4AaMrriVEU1CBbzD3I7Xm` | x ≈ 4521…5435, y ≈ 14137…15014 | Orange `hoGJ6iaL`, empty source rect `h9v3h1pU`, unbound arrow `PU0175lM` |
| **H. LSE video** | ungrouped | x ≈ −12908…−10140, y ≈ 27987…29937 | Embeddable `Qs9yTVu0`, label `4AhOiPPo` |

**Observation.** Reconstruction PNGs under `evidence/session/evidence/` (`shell.png`, `agent-layouts.png`, `alternate-layouts.png`, `annotated-dashboard.png`, `settings.png`) are reading aids. They are not a new design and are not pixel-exact Excalidraw exports (`storyboard-reading.md`).

---

## 3. Complete text-element ledger (all 20 ids)

Every id in `scene-text.json` is listed once. Short quotes are truncated; full strings remain in `scene-text.json` and, for `JHZj5SdT`, in §4.

| # | id | xy (rounded) | Short quote | Spatial role | Class | Notes |
|---|---|---:|---|---|---|---|
| 1 | `rbuAuIXL` | 3677, −4181 | “or” | Region A, between OpenBB overview (`XNgN469F`) and VS Code (`l34HKwYF`) | **U** | Same group as both layout screenshots. |
| 2 | `lDsh2tno` | 3932, −4821 | “the layout is what I'm picking… The layout” | Region A, above VS Code | **U** | Explicit layout pick. Visible VS Code/OpenBB chrome is **E**, not instructions (`02`, fidelity reset). |
| 3 | `UEafaJLm` | 1974, −4896 | “this open bb” | Region A, above first OpenBB placement | **U** | Labels image `XNgN469F`. Speech later says “OpenBloomberg”; the PNG is branded OpenBB. |
| 4 | `viURg15y` | −1854, −5004 | “this ideal wireframe… first layout, or… up layout” | Region A, above the hand-drawn shell | **U** | Leaves naming open. |
| 5 | `YJYDP26I` | −3392, −5277 | “this top bar is ideal… reusable component… some apps might not need it” | Region A, boxed callout `XJnBycj3` with arrow `cXtYxg2B` from the shell top bar | **U** | Current direction still treats the bar as reusable/optional. |
| 6 | `qhuD191N` | 15462, 1741 | “idea setting or settings page… this one is global, and I believe each app needs its own” | Region E, far right, isolated from the Settings screenshot | **U** | Points at a settings *idea*, not at image `J6WAqID0` by binding. |
| 7 | `EIWGwk1g` | −727, 8472 | “Or we can try these ones” | Region D, diamond hub | **U** | Hub for four alternate screenshots. Not a chosen shell. |
| 8 | `tD33M0Ny` | −777, 1102 | “or/and” | Region B, between compact left sketch and expanded copilot | **U** | Relates two copilot sketches, not two products. |
| 9 | `rrUMAlEq` | 918, 827 | “preview panel… not where we design or make workflows from… terminal can also be in here” | Region B, over the large right work/preview rectangle | **U** | Preview types listed; authoring location deferred. |
| 10 | `C39LFtm1` | 58, 1846 | “open sessions, history settings for the agents” | Region B, under the inner left column of the expanded copilot | **U** | Main-copilot sidebar only. Fidelity reset: do not copy this sidebar onto every mini-app. |
| 11 | `nLB3FO70` | 11370, 16367 | “message icon” | Region F, red box `ZFvR7Rap` from ellipse `Oh8I9yu3` on the ticker crop | **U** labeling **E** | See mapping table. |
| 12 | `Y3XcLbSh` | 9165, 15809 | “this thing (editing the set up of widgests)” | Region F, red box from ellipse `97Gn7MCA` on large OpenBB header-control row | **U** labeling **E** | Dictation: edit/placement. |
| 13 | `wLhO8DpA` | 9181, 18597 | “thing at the bottom i mentioned” | Region F, red box `GqD8KmCk` from ellipse `iwfCTXs3` at the bottom of the large OpenBB | **U** labeling **E** | Dictation infers add-panel; the PNG does not name that control. |
| 14 | `C2K3xORn` | 7902, 18646 | “risk mgt and bms stuff” | Region F, red box `VO5JRm70` from rect `BldEX4aI` over Revenue Per Business Line | **U** proposing reuse of **E** | Adaptation, not OpenBB semantics. |
| 15 | `Ibr804Se` | 7950, 15931 | “history thing i mentioned” | Region F, red box from ellipse `wrOHWMtI` on a widget-header clock-like control | **U** labeling **E** | |
| 16 | `NJidF6Tg` | 10811, 17446 | “this can help s go from preview mode to library” | Region F, **navy** `#1971c2` box `lYsuH7Nz` from thick-stroke ellipse `fwMS8fCb` on a small copilot-table control | **U** proposing a jump from **E** | Screenshot does not say “library”. |
| 17 | `w6Wra1LH` | 6671, 15799 | “this is the exapansion tool” | Region F, red box from ellipse `yOERraUc` on a widget-header expand control | **U** labeling **E** | |
| 18 | `JHZj5SdT` | −6185, 17701 | Full 16,804-character dictation (see §4) | Region F, large block left/below the annotated OpenBB | **U** | Foundation dictation. One later passage (LSE as layout representation) is overridden by `02`. |
| 19 | `hoGJ6iaL` | 4834, 14192 | “this is for the expanded view of a widget or workflow” | Region G, orange `#f08c00` | **U** | Arrow end is **unbound**; source rect `h9v3h1pU` is empty. Not pinned to a widget image. |
| 20 | `4AhOiPPo` | −11561, 29868 | “lse vide” | Region H, orange box `i51GbhaS` under video embed `Qs9yTVu0` | **U** labeling **E** | Later `02` rejects LSE ML Studio **as QMX layout**. The video remains a capability/reference clip, not an approved shell. |

**Observation.** None of the 20 scene texts is assistant-authored **P**. Assistant proposals live in later studies (`experience-v01`…`v03`) and in `02` rows marked P. Those studies are **historical** as implementation baselines.

---

## 4. Full bottom dictation `JHZj5SdT` — inventory, not paraphrase

Source: `scene-text.json` id `JHZj5SdT`; also `qmx-ui-storyboard.source.md` Text Elements. Character count in the audit: **16,804**. Group `EgXLF6bkT_kJu_EzejnIu`. Color `#1e1e1e`.

The block is one element. Thematic cuts below are ledger headings only.

### 4.1 Mini-apps as dashboards; OpenBB as layout option

Exact: “most of the mini apps that we are going to have will most likely just have dashboards.”  
Exact: “OpenBloomberg, I think, gives us the best option.”  
Exact: “it has widgets… each widget could expand.”  
Exact: “ticker information… summarized preview. But I can zoom in, which means all that data needs to be filled in.”  
Exact: “this is mostly a dashboard, and you are seeing most of them are editable.”

**Observation.** The attached PNG is OpenBB (`pro.openbb.co`), not Bloomberg Terminal.  
**Inference to avoid.** Do not treat Bloomberg Terminal behavior as proven (`storyboard-reading.md`).

### 4.2 Message icon → copilot

Exact: “some sort of message icon… like a message icon with a plus in between.”  
Exact: “I'll circle it… It's global, so it's almost on every widget.”  
Exact: “I think this is the way we can connect multiple apps to the copilot. I think this is how Bloomberg Terminal does it.”

Supports labels `nLB3FO70` and crop `Pasted Image 20260922155654_792.png`.  
**Observation.** The crop shows a speech-bubble header control; a plus-in-the-icon is **not** clearly readable at the inspected resolution.  
**Inference (user).** Global widget→copilot attach.

### 4.3 Preview, chat, edit, scroll, bottom add, assembly

Exact: “how do we preview data? How do we preview code?”  
Exact: “There is also a chatting thing… just a chatting platform.”  
Exact: “This shows that we can edit.”  
Exact: “Scroll bars.”  
Exact: “note the assembly thing.”  
Exact: “this thing at the bottom. I think this can help us add new panels or add new stuff.”

Supports `Y3XcLbSh`, `wLhO8DpA`. Bottom-add is **user inference** from an unnamed bottom control.

### 4.4 Revenue widget → risk/BMS; blue icon → local vs server

Exact: “revenue per business baseline… for risk management and question sizing, this can help the BIMS, the book.”  
Exact: “Even to show what is on a server, what is local, for example, the trading node, you see that blue icon in this thing I've highlighted.”

Supports `C2K3xORn`.  
**Observation.** The PNG widget title is “Revenue Per Business Line”. A small blue square sits at that widget’s lower-right. The PNG does not say BMS, Book, server, or local.  
“BIMS”/“BMS”/“market sentient” may be dictation noise (`storyboard-reading.md`). Preserve; do not invent modules.

### 4.5 History; mini-app example; copy/paste

Exact: “the history thing, we shall see how to do this.”  
Exact: “This is most this is an example of a mini app. You see how intentional it is?”  
Exact: “small, small details like copy, paste.”

Supports `Ibr804Se`.

### 4.6 Library jump — self-correction inside the same element

First: “QMX Global Library, I think, can open up as a tab here on top anywhere in any mini app.”  
Then: “Or actually, no, no, no… if I am to click on top of this… this blue thing I've highlighted… we go back to the sidebar and we just have okay, we are transferred to the sidebar.”

Supports navy `NJidF6Tg` / ellipse `fwMS8fCb`.  
**Observation.** The correction is in the source dictation, not a later study.  
**Still open (U in `02`):** types, ownership, location/version, lifecycle; no accepted taxonomy.

### 4.7 Expansion; SDK/design system; node editor not done

Exact: “this expansion tool, this right here gives us a better view.”  
Exact: “the hardest part designing the mini apps, and we have to give them, I think, an SDK or a design system.”  
Exact: “we haven't done the node editor yet, but this is just a dashboard of a mini app, an example.”  
Exact: “We can design it in terms of code or a note-based editor… the mini app is more like universal view.”

Supports `w6Wra1LH`. Authoring UX is **not drawn**.

### 4.8 Two copilots, different permissions

Exact: “in the agent or in the co-pilot setup, we have two different things to consider.”  
Exact: “the version that is made. So it's the one above, the one with multiple black screens.”  
Exact: “this one, which has access to a mini app, this is a different version, it has different permissions and tools, as well as different access. This is where MCP apps configuration comes into play a lot.”

**Aligned with later U (`02`):** shared copilot capability, independently scoped conversations, copilot optional per app.

### 4.9 json-render, dashboards, main-copilot left sidebar

Exact: “for the widgets, I was proposing JSON render.”  
Exact: “the left-hand sidebar in the main co-pilot view, the one above… has more tools, more access… singular mini apps, singular widgets, singular workflows.”  
Exact: “I think it can fit into that preview panel.”

Supports `C39LFtm1` + `rrUMAlEq`. json-render is a **user-floated** integration lead, not a selected renderer (`02` still P on adapters).

### 4.10 Multi-app rail: home / divider / opened apps

Exact: “we open multiple mini apps… on the sidebar, the left-hand sidebar, yeah, to show which is active.”  
Exact: “that main home dashboard, which shows all everything running.”  
Exact: “we can draw like some sort of a line, a thick one… this is where most of the menu ends.”  
Exact: “the remaining new icons below that line represent active applications or applications that have opened.”

**Observation.** The hand-drawn rail (`de1tWGR3`, ~73×1174) is a narrow left strip. A thick **horizontal** divider inside that rail is **described**, not clearly drawn as a labeled divider.  
**U in `02`:** “Persistent narrow rail, shared destinations, divider, opened apps.”

### 4.11 Top menus: Overview vs Financials vs expansion-as-tab

Exact: “this top bar where you see overview financials. Let me highlight it… in orange.”  
Exact: “a mini app is a composition of widgets and workflows.”  
Exact: “this could represent a view, an expanded view, yeah, of a widget or a workflow.”  
Exact: “overview… summarized version of everything, which means a mini app should also have menus.”  
Exact: “financials is representing the visuals or rather the widgets in the mini app.”  
Exact: “these menus on top change, they're dynamic.”  
Exact: “when we expand… it could open a new tab on top or a new menu on top… like a browser… then it shows a detailed view.”  
Exact: “This is very, very difficult… lots of things I'm going to need you to… think through.”

Supports `YJYDP26I`, `w6Wra1LH`, `hoGJ6iaL`.  
**Observation.** Saved scene has **no** orange outline on the Overview/Financials tab row of either OpenBB placement. Orange `#f08c00` is used for Region G (`hoGJ6iaL`) and Region H (`4AhOiPPo` / video). Dictated orange highlight of the tab row was **not completed** in the saved file.

### 4.12 Missing representations; placement during building

Exact: “we actually haven't looked at a widget representation, a mini-app representation we have… workflow representation. We haven't looked at any of those.”  
Exact: “ML, maybe one is in research and hypothesis.”  
Exact: “it is meant to be specified during the building.”

**U in `02`:** vary mini-app composition; historical sample apps are examples, not a closed backlog.

### 4.13 Embedded URLs (all inside this one text id)

1. https://json-render.dev/  
2. https://modelcontextprotocol.io/extensions/apps/overview  
3. https://xynth.com/  
4. https://primemarket-terminal.com/  
5. https://quantx.es/  
6. https://minara.ai/docs/agent  
7. https://www.londonstrategicedge.com/terminal  

Exact: “for more inspiration… how they present their dashboards and apps.”  
Exact: “LSE, I believe, is I think the best option… it is what we are using in terms of data for machine learning… the video they have… might be the best representation.”  
Exact: “I'll add the video.”

**Later override (`02` U):** “LSE's ML Studio UI is rejected as a layout/model for QMX. Its ML capabilities can inform coverage.” The LSE **layout** claim in this passage is **historical**. LSE as **data/capability** source remains user direction.

### 4.14 Session-start / delegation (end of the same element)

Exact: “for the sub-agents, you are going to use lower-end models… We might need browser use.”  
Exact: “I might prefer to use Grokbot… Give it very clear instructions.”  
Exact: “If you receive this message, the session has begun.”

**Observation.** These are sitting-process instructions, not UI widgets. `storyboard-reading.md` under-recorded this closing passage.

---

## 5. Unique source images (all 10)

Directory: `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/evidence/source-images/`  
Each PNG was opened with the Read tool. Labels below are **visible in the image** or **absent**. User circles exist on the **Excalidraw scene**, not baked into these PNG files (except as ordinary product UI).

### 5.1 `Pasted Image 20260922150714_899.png`

| | |
|---|---|
| fileId | `9519524b10183db42c0fe087cb7e01a37c1d7e43` |
| Placements | **Two:** `XNgN469F` (Region A, overview, slightly rotated) and `N6HsaKzkebjAZMVg4JloE` (Region F, large annotated copy, ~3501×2291) |
| Dictation ids supported | `UEafaJLm`, `lDsh2tno`, `YJYDP26I`, `JHZj5SdT`, plus Region F labels `Y3XcLbSh`, `Ibr804Se`, `w6Wra1LH`, `wLhO8DpA`, `C2K3xORn`, `NJidF6Tg` |

**Observation — layout regions.** macOS window, URL `pro.openbb.co`. **Most of the width is a widget canvas.** A **substantial right copilot** is titled “Revenue Growth Analysis”. A **very thin left strip** shows a small blue square (window/panel handle), not an app page list.

**Observation — top navigation (above canvas, not a left sidebar).** `Overview` (selected), `Financials`, `Technical Analysis`, `Comparison Analysis`, `Ownership`, `Company Calendar`, `Estimates`, then a pencil and an X.

**Observation — widgets (dense, different sizes).**  
- **Ticker Information** `AMZN`: sparkline, Price `$220.79`, Day’s Change, volume, “Trading Inside of the Normal Range”, “Specialty Retail | US | NASDAQ”. Header controls: clock-like, speech-bubble, ⋮, expand, close.  
- **Price Performance**: candlestick + volume, Date Range, TradingView mark.  
- **Key Metrics**: Beta, Vol Avg, Market Cap, Range, 52-week High.  
- **Management Team**: name/title/compensation table with a vertical scrollbar.  
- **Revenue Per Business Line**: stacked bars, FY, pager `1 / 4`, **small blue square** at the widget’s lower-right.

**Observation — right copilot.** Prompt about Apple revenue; “OpenBB Copilot”; “Step-by-step reasoning”; table `statement_id` / `fiscal_year` / revenue years 2020–2024; “Trend Analysis”; “Key Observations”; context chip “Using dashboard widgets”; composer “Ask a question…”; footer “OpenBB Copilot”. A small control sits at the lower-right of the result table (the navy annotation target on the board).

**Observation.** User arrows/circles are **not** in this PNG. They are Excalidraw overlays on placement `N6HsaKzkebjAZMVg4JloE`.

**Do not treat as instructions:** Apple/AMZN figures, OpenBB branding, exact tab names as QMX IA.

### 5.2 `Pasted Image 20260922151452_954.png`

| | |
|---|---|
| fileId | `f5e551b2d517638514042911b94ed38e2383a7df` |
| Placement | `l34HKwYF` Region A |
| Dictation ids | `lDsh2tno`, `rbuAuIXL` |

**Observation — layout.** VS Code window title `QMX`. **Left activity bar** (Explorer highlighted; Search, Git, Run, Extensions, additional icons). **Editor tabs** including `qml-research-epics-handoff.md`. **Center:** markdown document. **Right:** stacked agent panel with tabs `Chat`, `Claude Code`, `Codex`; conversation + file-edit card + composer.

**Observation.** Visible document/chat text is incidental QMX session content. `02` and the fidelity reset: **layout only**, not authority to execute that markdown.

### 5.3 `Pasted Image 20260922153805_586.png`

| | |
|---|---|
| fileId | `1efa6f5c3ee34c2384d1aa42a6025278f09da3fa` |
| Placement | `ZBR4Py0I` Region C, y ≈ −921 |
| Dictation ids | `C39LFtm1`, `rrUMAlEq`, `JHZj5SdT` (“multiple black screens” / main copilot) |

**Observation.** Hermes: **left sessions column** (`SESSIONS` / `BOTS`, New session, Capabilities, Messaging, Artifacts, Scheduled jobs, Crew, Kanban, search, pinned/home lists). **Center** “HERMES AGENT” + composer “Give Hermes a task”. **Right** `BROWSER` tab, `about:blank`. Top center tabs `NEW SESSION`, `TERMINAL`. Bottom-left repo `QMX`.

Supports main-copilot: sessions list + conversation + preview/browser, **not** a mini-app canvas.

### 5.4 `Pasted Image 20260922153840_932.png`

| | |
|---|---|
| fileId | `08d58f4f31dee383af1d3dee6e716c7c4f4e8f5a` |
| Placement | `lhI5ub0I` Region C, y ≈ 689 |
| Dictation ids | `rrUMAlEq` (preview variants: Review/Terminal/Browser/Files/Side chat) |

**Observation.** Codex desktop: **left** New chat, Pull requests, Scheduled, Plugins, Explore, Pinned, Projects. **Center** conversation “Restart QMX UI design”. **Right** launcher rows: Review, Terminal, Browser, Files, Side chat, each with a shortcut. Chat contents are incidental.

`02`: later red-circled Codex conversation-navigator screenshots are a **different** five-image set under `experience-v03/references/`. They must not reshape the mini-app canvas.

### 5.5 `Pasted Image 20260922153920_566.png`

| | |
|---|---|
| fileId | `7ea17c736d35f92c520165c93d27607170bde619` |
| Placement | `74eMr8Ev` Region C, y ≈ 2139 |
| Dictation ids | `rrUMAlEq` (empty/start composer), `C39LFtm1` (narrow left nav) |

**Observation.** Cowork-style: **narrow left nav** (`Cowork`/`Code`, New, Projects, Artifacts, Scheduled, Customize). **Large empty center** “You're here!” with a single composer and three “Ideas for you” rows. No widget canvas, no right copilot.

### 5.6 `Pasted Image 20260922154128_267.png`

| | |
|---|---|
| fileId | `df49334ceff2d5ea4b740f0010d8606553a8ffad` |
| Placement | `bOuRtdFN` Region D |
| Dictation ids | `EIWGwk1g` |

**Observation.** Manus 1.6, project **Fones**. Left: New task, Agents, Search, **Library**, Projects. Overlay “Hide tasks in the Project”. Center: composer, cards **Instructions**, **Files**, **Skills**, a Tasks list. Footer promo “Share Manus with a friend”.

**Observation.** Nouns Instructions/Files/Skills are in the screenshot. `storyboard-reading.md`: not a requirement to import those nouns.

### 5.7 `Pasted Image 20260922154153_959.png`

| | |
|---|---|
| fileId | `f5779af0facb130fbac8fae56c7f32f58333db37` |
| Placement | `al0Me1H3` Region D |
| Dictation ids | `EIWGwk1g`, `NJidF6Tg` / `JHZj5SdT` (library *layout* lead only) |

**Observation.** Dark library/browse UI. **Persistent left rail** grouped VOICE TOOLS / LIBRARY / LIVE / STUDIO / PLATFORM. LIBRARY → **Voices** selected. **Second filter column:** Search, Category, Language Japanese, Accent, Use case chips, Reset Filters. Main: “No voices found”, three create cards, “Design a Voice”.

Useful as **browse + filter column** geometry. Voice domain is incidental.

### 5.8 `Pasted Image 20260922154354_046.png`

| | |
|---|---|
| fileId | `ef4c1922cd5a776627fa329b0a711ff9ac487dc2` |
| Placement | `uNUtaSsB` Region D |
| Dictation ids | `EIWGwk1g`; startup/workspace selection is later U in `02`, not named on this image |

**Observation.** “Select Workspace”. Tabs Local / Remote. Search, “+ New Workspace”, radio list (`awesome`, Empty Workspace, `od`, `od`). Back / Next. Top: Dashboard, Sessions, Droids. Bottom composer. A selection form, not a required wizard.

### 5.9 `Pasted Image 20260922154421_046.png`

| | |
|---|---|
| fileId | `22180a4043401316eb5f9194d5d12ffe6647b84e` |
| Placement | `J6WAqID0` Region D (not next to `qhuD191N`) |
| Dictation ids | `EIWGwk1g`, `qhuD191N` (by user note, not by scene binding) |

**Observation.** “SETTINGS”. Tabs General, Integrations, **Session** (selected), API Keys, Billing & Usage. Panels: Local Repositories (empty); Factory Bridge (Root Directory `~/library`, Browser Tools toggle); Remote Workspaces table (rows `od` Failed, `awesome` Success).

Global settings *reference*. `qhuD191N` still wants app-level settings as well.

### 5.10 `Pasted Image 20260922155654_792.png`

| | |
|---|---|
| fileId | `242a1cf3bdc536d1342f8e6cb637715d993922b3` |
| Placement | `d5Z7dzE0` Region F, small crop beside the large OpenBB |
| Dictation ids | `nLB3FO70`, `JHZj5SdT` (message icon + ticker expand) |

**Observation.** Crop of **Ticker Information** only. Header: title, `AMZN`, then **clock**, **speech-bubble**, **⋮**, **expand**, **close**. Body: green sparkline, price, day’s change, volume, specialty/US/NASDAQ. No plus is clearly visible in the speech-bubble at this resolution. Red ellipse `Oh8I9yu3` in the scene sits on this crop’s header-icon row.

---

## 6. Mapping table — required surfaces

| Surface | Board evidence (ids / images / shapes) | Observation | Inference / still open | Class now (`02`) |
|---|---|---|---|---|
| **Platform rail** | Wireframe strip `de1tWGR3` (~73px) inside shell `Nqb8WQP1`; dictation `JHZj5SdT` home + thick line + opened-app icons; VS Code activity bar in `…151452_954.png`; Hermes/Cowork left columns as copilot refs | A **narrow left strip** is drawn on the mini-app shell. Icons and a **drawn** rail divider are not labeled on that strip. | Divider and “opened apps below” are **spoken**, not fully drawn. Home contents, attention, search, responsive placement remain open (`02`). | **U** |
| **Main copilot** | Sketch group `Uxd5W2WO_kbnYcWxjf66n`: sessions column `nGonDSxT` + `C39LFtm1`; preview `IQ6F7au4` + `rrUMAlEq`; `tD33M0Ny`; screenshots Hermes/Codex/Cowork | Two sketches: compact black-screen stack vs expanded sessions + preview. Preview may hold browser, mini-app/widget/workflow preview, CLI, cards, video, diff, terminal. | Exact split/dock, attachment meaning, concurrent work open. Do **not** impose this inner sidebar on mini-apps (fidelity reset). | **U** |
| **Mini-app** | Shell Region A; OpenBB both placements; `viURg15y`, `YJYDP26I`, `JHZj5SdT` (“composition of widgets and workflows”; dynamic top menus) | Canvas-majority + app-specific **top** nav + optional **right** copilot. No permanent Overview/Workflows/Results **left** sidebar in the source. Widgets are dense charts/tables. | Tab names Overview/Financials are OpenBB **E**, not QMX IA. Switching apps must change navigation/composition (`02`, fidelity reset). | **U** |
| **Authoring** | Spoken only: `rrUMAlEq` (“not where we design or make workflows”; “similar to what we had above”); `JHZj5SdT` node editor “haven’t done”; code vs “note-based” editor | **No authoring canvas, n8n shot, or node graph is on this board.** VS Code is a **layout** ref in Region A, not an editor spec. | `02` later U: app/VS Code-like family; graph can hold code/data/model ops; n8n is a later reference lead (fidelity reset). Study 03 authoring placeholders were inadequate. | **U** (need exists); layout **still to design** |
| **Library** | Navy overlay `NJidF6Tg`, `fwMS8fCb`, `pFkLyt2S`, `lYsuH7Nz`; dictation self-corrects tab → **sidebar**; Voices PNG as browse/filter **E**; Manus left item “Library” is incidental product chrome | User marks a **small copilot-table control** in navy and claims a jump to a global library. OpenBB does not label it Library. | Taxonomy unset. Study 03 Library was **not approved**. | **U** (need + jump idea); structure **open** |
| **Settings** | `qhuD191N` isolated; Settings PNG `…154421_046.png` via `EIWGwk1g` | One global-settings **reference screenshot**; a separate note that global ≠ per-app. | Boundaries among global / app / widget / agent settings open (`02` does not freeze this). | **U** as idea; **E** as one layout |
| **Expansion** | `w6Wra1LH` + ellipse `yOERraUc` on widget expand control; `hoGJ6iaL` orange callout; dictation: new top tab/menu, browser-like, detailed view | Header **expand** control is visible on OpenBB widgets. Orange callout is **not bound** to that control. Expansion behavior left difficult/open in-dictation. | `02` P: select → inspector; explicit expand → detail tab; compare with these arrows before accepting. Fidelity reset: expanded view must show real chart/table/workflow, not a paragraph. | **U** (need); mechanism **open** |
| **Message-icon** | `nLB3FO70`; ellipse `Oh8I9yu3`; crop `…155654_792.png`; dictation “global… connect multiple apps to the copilot” | Speech-bubble (and nearby header icons) on **every visible OpenBB widget header**. Crop isolates that row. | Plus-in-icon, Bloomberg-equivalence, and exact attach semantics are **not** visible. Shared copilot + scoped sessions is later U; identical panels everywhere is not. | **U** (widget↔copilot affordance) |
| **Library-jump** | Same as Library row: navy `#1971c2` thick stroke (user: “Navy blue… darker stroke”) | Distinct from red widget-header marks. Target is a **small icon on the copilot result table**, not a top tab. | Jump-to-sidebar is the **in-dictation correction** of “open as a tab”. Visual aesthetic of that transfer is explicitly unknown. | **U** (intent); **E** does not prove OpenBB does this |

---

## 7. User-drawn overlays on the annotated OpenBB (Region F)

All in group `EgXLF6bkT_kJu_EzejnIu` unless noted. Colors from `scene.json`.

| Mark | Color | Scene ids | Points at (observation) | User label |
|---|---|---|---|---|
| Ellipse + arrow + box | red `#e03131` | `Oh8I9yu3`, `rU0H6BtV`, `ZFvR7Rap`, `nLB3FO70` | Ticker-crop header speech-bubble | message icon |
| Ellipse + arrow + box | red | `97Gn7MCA`, `sxguLJan`, `2sR3VDKM`, `Y3XcLbSh` | Large OpenBB, upper widget-header control cluster | editing the set up of widgets |
| Ellipse + arrow + box | red | `wrOHWMtI`, `ZnLZbkfh`, `LvjytBKs`, `Ibr804Se` | Header clock-like control | history |
| Ellipse + arrow + box | red | `yOERraUc`, `uL7jsPGm`, `j9z6A3zR`, `w6Wra1LH` | Header expand control | expansion tool |
| Ellipse + arrow + box | red | `iwfCTXs3`, `0ag2OJD0`, `GqD8KmCk`, `wLhO8DpA` | Bottom of the large OpenBB (near copilot composer / window bottom) | thing at the bottom |
| Rect + arrow + box | red | `BldEX4aI`, `ndhLsHDN`, `VO5JRm70`, `C2K3xORn` | Revenue Per Business Line band | risk mgt / bms |
| Ellipse + thick arrow + box | **navy** `#1971c2`, strokeWidth **8** | `fwMS8fCb`, `pFkLyt2S`, `lYsuH7Nz`, `NJidF6Tg` | Small control on copilot table | preview → library |
| Orange callout (separate group) | `#f08c00` | `h9v3h1pU` (empty), `PU0175lM` (end unbound), `Cja6zvvf`, `hoGJ6iaL` | Not bound to an image | expanded view of a widget or workflow |

**Observation.** Dictation promised an orange outline on Overview/Financials. That outline is **missing** in the saved scene. Do not invent it.

**Observation.** Shell Region A has a black arrow `gRzN29RU` from the drawn right-copilot column `cC5xJZdV` toward the first OpenBB image — layout comparison, not a widget control.

---

## 8. Conflicts: afternoon board vs morning copies vs later studies

### 8.1 Afternoon board vs morning copy

| | Morning | Afternoon (use this) |
|---|---|---|
| File | `evidence/session/evidence/qmx-ui-storyboard.source.md` | `live-research/board-current/qmx-ui-storyboard.source.md` |
| Bytes / hash | 99,027 / `2c27d55f…1d89e929` | 99,181 / `12046358…34456F1` |
| 20 text ids | Present in morning `storyboard-text.md`, including `hoGJ6iaL`, `4AhOiPPo`, full `JHZj5SdT` | Same 20 ids; audit found no wording drift |

**Observation.** `04-SOURCES-AND-SKILLS.md`: “Afternoon snapshot supersedes the earlier morning copy.” Delta is **154 bytes** of drawing JSON (expanded-view group `4AaMrriVEU1CBbzD3I7Xm` carries later `updated` timestamps `1790155491554`), not a new text-id set.

**Conflict is in the readings, not the 20 quotes:**

- `storyboard-reading.md` (banner: superseded for completeness) missed: home+divider correction; library tab→sidebar correction; seven URLs; “session has begun”; treated “one complete widget journey first” as an ordered proposal the user later overrode by asking for full reference grounding.
- `dictation-audit.md` is the complete text/structure pass.

### 8.2 Later assistant studies vs this board

| Study | What it did | Conflict with this board / `02` | Status |
|---|---|---|---|
| Study 01 | Exploratory | Not a baseline | **historical** |
| Study 02 | Aesthetic treatment + attachment picker | User rejected look and picker; some attach/question/preview ideas remain evaluable (`02`) | **historical** as baseline |
| Study 03 | One three-column shell; Overview/Workflows/Results as **permanent left sidebar**; sparse text cards; Codex preview used to reshape app canvas | OpenBB/VS Code: top nav + dense canvas + right copilot; main-copilot sidebar is **not** universal; expanded widget was a paragraph instead of a working surface | **WITHDRAWN** (`layout-fidelity-reset.md`, `experience-v03/README.md`) |
| Study 03 Library | Unified catalogue UI | User did not approve; ideas may be reconsidered one-by-one | **historical** as structure |
| Live-research LSE ML Studio shots | Train/Optimise forms (`visual-evidence-index.md`) | `JHZj5SdT` called LSE a strong representation; **`02` rejects LSE UI as QMX layout** | Layout claim **historical**; capability coverage still allowed |
| Codex five screenshots (`experience-v03/references/`) | Preview tabs, context, launcher, red-circled conversation nav | Valid as **main-copilot / preview** leads; must not replace OpenBB mini-app geometry. Expanded plus menu **not** captured (`02`) | **E** for those controls only |
| n8n docs (fidelity reset follow-up) | Mapping UI, executions | Not on the original board | Later **reference**, not storyboard **E** |

### 8.3 Internal dictation tensions (same afternoon file)

| Tension | Leave as |
|---|---|
| Library as top tab vs sidebar transfer | Sidebar correction is later **inside** `JHZj5SdT`; still “I don’t know how that is explained in visual aesthetics.” |
| Overview as summary vs Financials as widgets vs expansion as extra top tab | Three **levels** left open (`dictation-audit.md`). |
| “Message icon with a plus” vs crop showing a speech-bubble | Record both; do not draw a plus that is not readable. |
| “OpenBloomberg” vs OpenBB PNG | Use OpenBB as the **image**; do not import Bloomberg Terminal behavior. |
| Copilot always present in the OpenBB example vs copilot optional per app | Example is **E**; optionality is later **U** in `02`. |
| json-render / MCP Apps / SDK | User leads, not selected contracts (`02` P on adapters). |

### 8.4 Current direction overrides that matter for reconstruction

From `02-CURRENT-DIRECTION.md` (do not let the board’s LSE enthusiasm or Study 03 win):

- Original Excalidraw + full dictation remain foundation.  
- Persistent narrow rail; destinations above divider; opened apps below; shared resources.  
- Main copilot: sessions/history, conversation, tabbed preview/work.  
- Mini-app: app-specific nav where useful, substantial widget canvas, optional right copilot.  
- LSE ML Studio UI **rejected** as layout.  
- Neutral dark shadcn-svelte; Qt out; skip BMAD UX.  
- Studies 01–03 are not implementation baselines. The assistant owned those errors; the source was not missing.

---

## 9. Observation vs inference register

**Observation**

- 20 text ids, 10 unique PNGs, 11 placements, 1 video embed.  
- Mini-app shell: narrow rail, top bar, 2×2-ish widget rectangles, right copilot column.  
- OpenBB: dense widgets, top tabs, right copilot, header icon row repeated.  
- VS Code: activity bar + editor + right agent.  
- Main-copilot sketch is a different cluster than the mini-app shell.  
- Red vs navy vs orange overlays are distinct.  
- `hoGJ6iaL` arrow is unbound.  
- Alternate screenshots hang off “Or we can try these ones,” not off the shell.

**Inference (allowed as user-stated, not as proven product behavior)**

- Speech-bubble = copilot attach.  
- Clock = history.  
- Expand = detailed view, possibly a new top tab.  
- Navy table icon = library jump to sidebar.  
- Revenue widget pattern → risk/BMS/Book.  
- Blue square → server vs local / trading node.  
- Bottom chrome → add panels.  
- OpenBB ≈ Bloomberg-like multi-app attach.

**Rejected inferences (later studies / over-reading)**

- One universal three-column app shell.  
- Permanent mini-app left sidebar of Overview/Workflows/Results.  
- Text cards as a substitute for charts/tables.  
- Codex work-area chrome as the mini-app layout.  
- LSE Train/Optimise as QMX’s ML surface.  
- Approved Library taxonomy from Study 03.  
- Exact pixel coordinates frozen (`02`: thoughtful improvements allowed).

---

## 10. Coverage checklist

| Required | Status |
|---|---|
| Every `scene-text.json` id (20) | §3 |
| Full `JHZj5SdT` | §4 |
| Every unique PNG in `evidence/session/evidence/source-images/` (10) | §5; each opened |
| Mapping: rail / main copilot / mini-app / authoring / library / settings / expansion / message-icon / library-jump | §6 |
| Afternoon vs morning vs studies | §8 |
| Observation vs inference | throughout, §9 |
| `02` overrides historical studies | §1, §8.4 |

No application code. No files edited except this report.
