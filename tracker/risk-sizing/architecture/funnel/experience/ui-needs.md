# Experience pass: what the UI needs from this work

Written 2026-10-31 by agent F2. Index: `design-thinking.md` in this folder. These are notes and design proposals only, per his ruling 45 (STATE midday): no UI code is written or edited, and the UI session takes it from here. The lead appends what it keeps to `tracker/qma-v2/UI-NOTES.md` and `UI-HANDOFF.md`; this agent writes only this file.

## Ground rules this file follows

- **The UI is design, not code.** "don't look at the UI in terms of code, because the code is not right. Look at it in design." (T2:1148). Needs come from intent and the recorded screens, never from component code. I read the design from screenshots: Home, Apps, a mini-app page with Operations and Setup tabs, a bot's full page with Performance, Trading, Setup and "Road to live", Portfolio's Live and MIS tabs (`tracker/qma-v2/research/methodology/23-ui-shots/01`, `07`, `08`, `23`; `tracker/qma-v2/architecture/lab-and-pods/ui-shots/53`, `54`; CHECKED by viewing). I did not run the UI.
- **Fold before adding.** UI-HANDOFF's banner says not everything needs its own screen (CHECKED, `UI-HANDOFF.md:5`). Each section below says where it folds into an existing view.
- **Plain words, one vocabulary.** The same state words appear on every screen, in tool answers and in logs (design-thinking lead's call 3).
- **Demo mode off.** Unwired places say "Not connected" (UI-HANDOFF §0).
- **Proposals render in the UI.** "And the proposal should be rendered in the UI." (T1:1574).
- **Preview and detail.** "we have a preview and a detailed view. So, design for both." (T1:1574).

---

## 0. The words on the screens

| Thing | Words | Notes |
| --- | --- | --- |
| A trading node's state | Setting up · Starting · Ready · Trading · Healing · Paused · Stopped · Unreachable since `<time>` | One word plus one line of reason. "Healing" means restarting a part with back-off; "Stopped" names who or what stopped it |
| A unit's stage | Draft · Backtested · Stress-tested · Paper · Demo · Live · Retired | The journal's world on every row: backtest, stress, paper, demo, live, synthetic (the `trade` kind already carries a world, G3 §3.2) |
| Why a unit is not trading | Stopped by a risk rule · Stopped by a health check · Paused by you · Waiting for warm-up · Waiting for its market to open · Waiting for data · No new entries: `<reason>` | A risk stop and a health stop never share a word (design-thinking J9) |
| A number's kind | Fixed · Follows the market · Follows its record | Problem-solving WS1 |
| A number's origin | Source said · Builder chose · Unresolved · Placeholder | Funnel4 idea 4; placeholder per his ruling: "placeholders, I think is the right word" (T3:1087) |
| A reading's freshness | Live · Stale since `<time>` · Down since `<time>` · Unit used its fallback | Problem-solving WS4 |
| Machines | This PC · the name he gave the server | "A server can be a server." (T3:1102). No "trading server" or "workflow server" kinds on screens (design-thinking lead's call 4) |
| Times | His PC's zone first; UTC on hover; a node's local time beside it | Design-thinking J8 |

---

## 1. First start and getting started (the newcomer's first hour)

His words: "Remember, all this is meant to work right out of the box." (T3:1102).

**Shows.**
- The first-start card as designed (new, open, restore, bring in), unchanged.
- On Home, a "Getting started" panel with six lines, each ticking itself from facts: practice data, the example unit, a first backtest, your own unit with the copilot, a trading node on This PC, a broker demo sign-in. Each line has one button and one sentence. Skippable; it hides when all six are ticked or he dismisses it.
- A "What works today" line under it naming anything not connected, in plain words ("No broker signed in: everything up to backtests works without one").

**States.** Each line: not started · running (with its progress line) · done · needs you (one sentence why).

**Backend it needs.** A getting-started state computed from facts (host, MISSING). The starter pack installed on first start (Library, templates, the example unit; template install as a job is BUILT, PR 223). Practice data with a synthetic fallback (Library and QMB; downloader BUILT, synthetic generator BUILT for forex).

**Folds into.** Home's left column, above "Needs you", while unfinished.

---

## 2. Home

The design already has "Needs you", "Going on", Pods, Markets and News (screenshot 01).

**Adds.**
- **Needs you** carries: proposals (at most 5 a morning, the rest queued), units stopped by a risk rule, nodes that need him (sign-in ended, healing keeps failing), and the getting-started "needs you" lines. Each item: one line, one primary button, a link to its evidence.
- **Going on** carries backtests running (with "run by" and "on This PC"), node setups in progress, and deploys warming up.
- **A nodes strip** across the top or in Going on: one chip per node with its name, market class, state word, local time and a dot. Tap opens the node page.
- **Morning card** (the daily brief) when it lands: per live unit what it did (traded, skipped and why, missed), stops, nodes in one line, proposals. Long text is his pain; the card fits one phone screen.

**Backend it needs.** Proposal items in the Library rendered with evidence (Library, BUILT kinds for artifacts; proposal rendering MISSING); node state via `provides` and the held stream per node (mini-app core and host, BUILT streams, node state MISSING); the morning-brief template with unit and node facts (workflows, template BUILT without them).

---

## 3. The copilot while it writes a unit

His words: the agents should get feedback "the same way you yourself, when you write code, you can receive a linter error or something" (T3:1264), and "we have to make sure there are no false positives" (T3:1264).

**Shows.**
- The unit draft as a card beside the chat, filling in slot by slot (market and timeframe, entry parts, exit set, sizing), each number with its origin label.
- After each save, the checker's answer as a short list, every problem at once, each naming where and what. When it empties: "Checks passed: 12 of 12", each check named on tap.
- A backtest card in the chat: queued (place in queue, which machine), running, landed; the result opens the QMB run page.
- A "plain Python" badge when the unit was written outside the template; it still gets every other screen.

**Backend it needs.** The unit checker as a core tool returning every problem (QML, MISSING; the answer shape exists in `workflows_validate`, G4b Q2). QMB door bound with a runner that trades (QMB, MISSING). Run events on the existing event streams (BUILT).

**Folds into.** The copilot's right-hand panel (UI-NOTES §1 describes a right-hand panel with a terminal; the earlier screenshot set has one named "copilot draft panel widget in chat", which I did not open).

---

## 4. Library: the unit's card and its page

The design has a bot page with Performance, Trading and Setup tabs, an evidence-runs table, "Open in Lab" and "Road to live" (screenshot 08). The unit kind already has page tabs in its schema: Logic, Results, Family tree, Markets, Versions (G1 §3.5, CHECKED there).

**Card (preview).** Name and version; stage; market class and markets; origin (for example "video, 12:40"); family and tries; last 30 trades in R as a small line; a placeholder stripe when any slot holds a placeholder; open proposals count. (Round 2 explainer "Preview and detailed view" gives the same set.)

**Page (detail), proposed tabs.**

| Tab | Shows | Backend part |
| --- | --- | --- |
| Overview | Two sentences on what it does; its parts by slot; where it is deployed (node, account, world); stage line | QML template; trading node deploy state |
| Numbers | Every number: value now, range, kind (fixed, follows the market, follows its record), origin, last move, "at its limit" flag; tap a move for its receipt | QML motion field; journal calibration rows (problem-solving WS1) |
| Results | Runs in money and R, with tries, data label, QMB version and variant, who ran each | QMB results with R; tries counted (MISSING) |
| Journal | The journal view (section 5), filtered to this unit | Journals |
| Markets | Admitted markets per world; candidates with their judged numbers only, never a raw ranking; refused markets with the reason | QMB judge (WS3); Library admitted list |
| Readings | Which readings it declares, each with its fallback and freshness on each deployment | QML `reads` list (WS4) |
| Family tree | Parent and children, coloured by stage, sized by trades | Library links BUILT (PR 190) |
| Lineage | Source to idea to unit, with the source's timestamp | Library `source` kind BUILT |
| Versions | Each version and what changed, as a kind of edit | Library versions BUILT |
| Proposals | Agents' proposals for this unit, each with evidence and an expiry | Library proposals |

**Buttons.** Backtest · Deploy · Road to live · Open in Lab · Add to copilot.

---

## 5. The journal view

His words: "The journal is very important, please." (T3:903) and "this is literally the DevOps layer for that unit" (T1:1574).

**Shows.**
- One timeline per unit, filterable by world (backtest, stress, paper, demo, live), phase (for example "paper, after live, drift alarm 2"), instrument, timeframe, broker, account, platform and node. These are his 31 Oct dimensions (T3:903).
- Row kinds, each with its own mark: trade taken; seen, not taken (with the gate that said no); missed (found by replay); a number moved (receipt); a stop (rule and values); a heal on its node; an agent note (with evidence and expiry); a phase change.
- On a trade: entry and exit, result in R and money, costs in R, worst and best swing, the readings at entry, and the inputs of its market-following numbers ("stop 12.3 pips = 1.5 × ATR 8.2").
- "Why didn't it trade at 14:02?": tap a time on the chart, see the gate trail at that minute.

**States.** A row from a node that has not reached the PC yet shows "on London-1, not yet here".

**Backend it needs.** A unit journal with those keys and row kinds (journals, MISSING); the node-to-PC link (MISSING, G4b Q6); a journal read path for the screen and the copilot (MISSING, G1 §7).

**Folds into.** The unit page's Journal tab, and the Trading tab the design already has.

---

## 6. Road to live and the click card

The design has a "Road to live" button on the bot page and a "Road to live" tab in Portfolio (screenshots 08, 54).

**Shows.**
- A stage line per unit: Draft, Backtested, Stress-tested, Paper, Demo, Live, with where it is and what the next step needs.
- **One click card per promotion** that says, in one sentence, what it admits: unit version, world, node, account, markets; what may move by itself (each calibrated number and its range); whether it carries placeholders (a red stripe); which QMB version its evidence came from; activation now or at the next session open. His words: "nothing actually ever enters live without me" (T1:1574).
- "Withdraw" and "Back to paper" on any live or paper unit.
- When the node is unreachable at the click: "Waiting for London-1; it applies when London-1 is back."
- A live card for a unit with placeholders says why it is refused by default and what replaces the placeholders (design-thinking lead's call 9).

**Backend it needs.** Promotion as desired state sent to the node (trading node, MISSING on the PC side); the motion envelope from the unit (QML); placeholder marks on blocks (Library, WS2).

---

## 7. The QMB app (design proposal)

Basis: QMB as the first mini app (ruling 43); "So if one day I decide to build a new version of QMB, I should be able to." (T3:1383) and "Or improve it, or give multiple variants, because it can be a mini app, for God's sake." (T3:1383); "Because QMB was meant to be called as a tool, so that agents don't do that." (T3:1562). STATE ruling 43 records that its own screen shows what ran and who ran it.

What the mini-app core gives it as built (G4b Q5, CHECKED there): a manifest with operations (input and output schemas, approval, reversibility), `provides` and `feeds` with freshness, profiles, a suggested trigger, a home machine, its own logs, a breaker for health. The design's mini-app page already has Operations and Setup tabs (screenshot 07).

### 7.1 Tabs

| Tab | Shows |
| --- | --- |
| **Runs** (new, the default tab) | Every backtest, stress test, sweep and walk-forward: what ran (unit and version, data window, market list), **who ran it** (you, a copilot chat by name, a workflow run, an agent in the Lab), where it ran (This PC or a server, and whether by default, chosen, spilled or standing in), QMB version and variant, status (queued, running, waiting, passed, failed, stopped, interrupted), result in R and money, tries it added to its family. Filters by unit, by who, by variant, by status |
| **Run page** (opens from a row) | Inputs with their fingerprints; the judge rule declared before it ran; equity in money and R; trades; skipped signals; costs; the try count; links to the unit, the chat or workflow run that asked, and the data cards it read; "run again" and "run on variant…" |
| **Versions** (new) | Installed QMB versions and variants side by side, which is the default for workflows, what each changed; "compare on a unit" runs one unit on two variants and shows both results with their versions |
| **Queue** (new, or a line on Runs) | What waits, on which machine, in what order |
| Operations (as designed) | One card per operation: backtest, stress, sweep, walk-forward, compare; each runnable by hand with its inputs |
| Setup (as designed) | Defaults: fidelity, cost model, first-look window, judging window start, the judge's numbers |
| Logs | The app's own log and health line |

### 7.2 States and words

- A run: queued · running · waiting (with why) · passed · failed (with one line) · stopped · interrupted (with "resume").
- The app: running · stopped by a health check (`<reason>`) · not connected.
- "Who ran it" uses the door's principals (the screen user, a chat's agent, a workflow run, an outside observer), which the host already records (G2 §6, CHECKED there); each links to its source.

### 7.3 Backend it needs

A bound backtest door with a runner that trades a named unit, results in R, tries counted at the door, the version and variant on every result (QMB, MISSING; PR 204 STACKED). The run list with principal and place (host: place on each attempt BUILT, PR 212; the run read lacks it, UI-HANDOFF §26 row 1). The app's operations on the copilot's default surface (design-thinking lead's call 6).

---

## 8. The trading node app (design proposal)

Basis: "a mini app can have a server of its own" (T3:1562); "So that when we click a kill switch, it can automatically work." (T3:1562); "is it going to start as server, then show me that the server has started?" (T3:1102); "I want to be, should I won't say hands-free, but like less stress." (T3:1102); "How are we going to be able to receive results?" (T3:903).

### 8.1 Nodes list

One card per node: name (his), where (This PC or the server's name), market class, state word and reason, local time, clock dot, units (trading, paused, stopped), last heartbeat. Buttons: "Start on This PC" (when none there), "Add a server". The same cards appear in the Home strip and in Portfolio's "Servers" indicator (screenshot 53/54 shows a "Servers" control with dots in the Portfolio header).

### 8.2 Add or start a node (the setup flow)

- **This PC:** one button. Then a list of steps that tick as they run: checking this PC (disk, clock sync), installing, starting, signing in to the broker demo (cTrader's own page opens), starting the readings, self-test, ready. A note up front: "Runs while this PC is on. For round-the-clock trading, add a server."
- **A server:** the existing connect dialog's card-then-steps pattern (G3 §1.4), with a "trading node" kind: his cards (rent a server with Ubuntu, its address, a one-off Tailscale key, the password into a terminal QMX opens, the firewall approval), then the same step list.
- Any failed step shows one line and two buttons: "Run this step again" and "Help". Running the whole setup again picks up where it stopped.
- When the node app version carries his signature step (the core's rule for apps that touch money, problem-solving WS5), the flow shows "Your signature publishes this node version" as one step, not a separate screen.

### 8.3 Node page, proposed tabs

| Tab | Shows |
| --- | --- |
| **Overview** | The state word and reason in large type; local time and its zone; clock offset and band; broker link; readings on or off; units summary; version; "Pause all", "Kill switch" (with its levels), "Update", "Roll back" |
| **Checks** | The self-test lines and their last result: prices arriving, clock synced, broker reachable, kill switch drill on demo, disk, memory, readings fresh. Each line green or red with one sentence |
| **Units** | Each unit deployed: world, account, markets, state (trading, warming up 140 of 200 bars, paused by you, stopped by a risk rule, stopped by a health check), last trade, today's result in R. Buttons per unit: pause, resume (his click), withdraw |
| **Heals** | Every restart the node made by itself: what restarted, why, at what time (his time and node time), how many times today; when healing keeps failing, the item it raised for him |
| **Deploys** | Every deploy, withdraw, update and roll back: what, when, by whose click, from which PC, and whether it has applied ("waiting for London-1") |
| **Logs** | The node's logs, with a link out to the full log viewer (one log home, OpenObserve) |
| Operations and Setup | As the mini-app page designs them |

### 8.4 The deploy dialog

From a unit ("Deploy") or a node ("Add unit"): pick node (only Ready ones), account, markets (from the admitted list), world (paper by default). A preflight list runs by itself and explains every red line in one sentence: same unit fingerprint as tested; node's library versions match or the difference shown; warm-up history available; instrument record per market at this broker; minimum lot fits; clock ok; every declared reading available or with a fallback; no placeholder on a live account. Then: deploying, warming up, trading. "Withdraw" and "Back to v2" are always one click away.

### 8.5 Backend it needs

The node app's manifest with operations and `provides` (mini-app core); setup as rerunnable steps and a "trading node" kind (host and connect dialog, MISSING); a desired-state reconciler, the state vocabulary, the heartbeat carrying state, reason, units, clock, zone and version (trading node, MISSING); the held stream per node (BUILT); one log home (OpenObserve BUILT, never run on real telemetry); the money-app seam settled (problem-solving WS5).

---

## 9. Several nodes, one clock

His words: "the trading node is perhaps a firm" (T3:903) and "how is a trading node trading FX in London going to be able to also be monitored?" (T3:903).

**Shows.**
- **A world clock strip**: his time first (his PC's zone), then each node's local time with its name, and the market sessions as bands (Sydney, Tokyo, London, New York; crypto all day; futures with their exchange hours). The bands are drawn from each market's own zone, so they shift correctly through daylight saving.
- **A notice a week before a mismatch week**: "London and New York are 4 hours apart from 25 Oct to 1 Nov". (Research 54 §4.1 computed this week's mismatch.)
- **Every time on every screen** in his zone, with UTC and the node's local time on hover or tap.
- **An unreachable node** greys with "unreachable since 03:12 (your time)" and its last values; its account's positions still show from the PC's view-only broker read, labelled "read from the broker".

**Backend it needs.** Each node's zone, clock offset and band in its heartbeat (clocks, MISSING, G2 §9); market calendars beyond forex (clocks, MISSING); the time-zone database kept current (pinned at 2025.2, research 54 §4.1).

**Folds into.** The Home nodes strip and the Portfolio header; the strip is the same component of the design wherever it appears (the UI session decides).

---

## 10. Stops and alarms

**The stop card** (an urgent item, and a row in the unit's journal): what stopped, when (his time, UTC, node), which rule and its values, what happened to open trades (kept with broker stops, or closed), whether it was a risk rule or a health check, and what it takes to resume. Buttons: Resume (his click), Back to paper, Retire.

**What wakes him** (the inbox's urgent level now; phone alerts later, UI-HANDOFF §7): a risk stop with open trades; a node unreachable with open trades; a broker link down with open trades; a clock in the halt band for 5 minutes; healing that keeps failing. Everything else goes to the morning card. The list is editable in Settings (design-thinking lead's call 13).

**Backend it needs.** Stop rows with rule, values and scope (journals and trading node); the inbox's severities (info, normal, urgent, black) as UI-HANDOFF §9 row 9 lists them.

---

## 11. Portfolio, MIS tab

The design shows readings with Live and Shadow switches, a "since" time and a value (screenshot 53).

**Adds.**
- Per reading: its version, its clock, the markets it covers, its freshness word (live, stale since, down since), and which units read it with which fallback.
- A reading's history as a chart, with the moments its state changed.
- When a unit used its fallback, a badge on the reading and on the unit.
- Readings his models will replace later show "default" until he trains his own (`M-02`): "Let's make defaults for the MIS. I'll train the models when I can." (T3:1264).

**Backend it needs.** Readings stored as series with cards and state-change records (the MIS, MISSING; homes exist, G4b Q6); the node-to-PC link.

---

## 12. Workflows

**Adds.**
- Inputs that pick stored readings and journals ("trend state, FX majors, last 20 sessions"), never "the MIS" as a model. His words: "They should be using the logs from the MIS." (T3:903).
- Triggers per market session and per N closed trades, beside cron (research 30 §7 found both missing).
- The slow-lane templates as a group (pre-session shortlist, market review, daily data review, unit review, node watcher), each showing its last output and its score where it makes calls (the forecast ledger).

**Backend it needs.** Session and trade-count triggers (workflows, MISSING); reading series as inputs (the MIS); a scoring script per shortlist (workflows).

---

## 13. Apps

The design's Apps screen has Pinned, Markets, Watching, Research, Trading helpers (screenshot 23).

**Adds.**
- QMB and the trading node pinned by default, each card showing its one most useful line ("2 runs going on", "London-1 trading · 3 units").
- Unit apps (design-thinking J10): a card showing the unit's state; the app page shows the unit's journal through its feeds.
- "New app, from a unit" in the New app menu.
- The design's "Safe mode" switch and "Discover" stay as designed.

**Backend it needs.** A unit-app template (mini-app core); the two apps installed in the starter pack.

---

## 14. Settings

| Area | Adds |
| --- | --- |
| Places (Machines) | Nodes appear here as their server's place with a "trading node" mark; This PC first; each with its clock health |
| Connections | Where each broker key lives ("lives on: London-1"); CCXT rows that can read and trade perps; Hyperliquid with testnet; paid data feeds (a futures depth feed) as rows he adds later, with their monthly cost shown as a reading, never a cap; a data entitlement line per machine ("depth feed: not on this machine") |
| Clocks (new, small) | Display zone (default: this PC's), each machine's clock offset and sync state, a button to turn on this PC's time sync (his click) |
| Deep logs | As designed (off, This PC, a server); the node's logs land in the same place |
| Alarms | The five wake items, editable |
| Units defaults | First-look window, judging window start, record clock, evidence weight, proposals per morning |

**Backend it needs.** The cTrader app key entry (UI-HANDOFF §26 row 3, a gap); CCXT beyond spot and a Hyperliquid client (broker links, MISSING); a clock check on the PC host (clocks, MISSING, G3 §0 item 6).

---

## 15. What this file does not ask for

- No separate "risk" screens: risk and sizing get placeholders and their own session (R-01). The placeholder stripe and the stop card are the only risk surfaces here.
- No router screens: the router was dropped as a switch (M-05, M-06).
- No per-machine dashboards beyond the node page: the node card plus a link to the log viewer is enough.
- No screen for the dictionary's internals: agents use it; he sees it through a unit's origin labels and, if he wants, a dictionary shelf in the Library like any kind.

## 16. Gaps the UI will meet, by part

| Part | Gap |
| --- | --- |
| Host | Getting-started state; run read without its place (UI-HANDOFF §26 row 1); cTrader app key entry |
| QML | Unit template, motion field, `reads` list, placeholder marks; unit kind fields |
| The unit checker | A core tool returning every problem |
| QMB | A runner that trades; R; tries; version and variant on results; run list with who and where |
| Trading node | App manifest; setup steps; states; heartbeat content; deploy as desired state; per-unit paper |
| The MIS | Reading series, cards, state-change records |
| Journals | The unit journal and its read path |
| Clocks | Zone and offset per machine; calendars beyond forex |
| Broker links | CCXT beyond spot; Hyperliquid; paid feeds; data entitlement |
| The copilot | The two apps on its default surface |
