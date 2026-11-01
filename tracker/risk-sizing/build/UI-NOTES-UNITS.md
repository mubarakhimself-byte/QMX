# UI notes for the unit system

Design intent only, for the UI session. No UI code is written or edited in the unit system build (STATE midday ruling 45, "You're not going to touch my designs."). The UI is judged by its design and by running it, never from its code (ledger UI-03).

This file consolidates the three parts' UI needs (`architecture/parts/A-qml-dictionary-unit/UI-NEEDS.md`, `architecture/parts/B-qmb-journals-workflows/UI-NEEDS.md`, `architecture/parts/C-node-mis-external/UI-NEEDS.md`) and the experience pass (`architecture/funnel/experience/ui-needs.md`), screen by screen. Where they differed, the newer part file wins, and each such choice is marked "Settled here". Each screen names what it folds into, what it shows, and the backend it reads with the PR in `build/UNIT-PLAN.md` that ships it. Two rules from him hold everywhere. "we have a preview and a detailed view. So, design for both." (T1:1574), and "the proposal should be rendered in the UI" (T1:1574).

## 0. The words on the screens

One word, one meaning, on every screen, in tool answers and in logs.

| Thing | Words |
| --- | --- |
| A unit's state on one market | Draft · Tested · Parked · Paper · Live · Stopped · Retired |
| Where a figure came from (its world) | backtest · stress · paper · demo · live · synthetic. Every figure shows its world, and paper never mixes into live figures |
| Why a unit is not trading | Warming up (140 of 200 bars) · Waiting for its market to open · Waiting for data · No signal · At its position limit · Skipped, with the reason · Paused by you · Stopped by a risk rule · Stopped by a health check · No new entries, with the reason |
| A trading node's state | Setting up · Starting · Ready · Trading · Healing · Paused · Stopped by a risk rule · Stopped by a health check · Unreachable since `<time>` |
| A number's kind (his word to veto) | Fixed · Follows the market · Follows its record |
| A number's origin | Source said · Convention · Builder chose · Unresolved · Placeholder |
| A check result | Checks passed · N problems · Warnings only |
| A dictionary entry's status | Named · Specified · Has code · Tested on data · Used in a unit |
| A reading's freshness | Live · Stale since `<time>` · Down since `<time>` · Unit used its fallback |
| A QMB run | Queued · Running · Waiting (with why) · Finished · Failed (with one line) · Killed |
| Machines | This PC · the name he gave a server. No machine kinds on screens ("A server can be a server.", T3:1102) |
| Times | His PC's zone first, UTC on hover, a node's local time beside it |
| A market that is shut | "Shut until Sunday 22:00 your time", from its calendar |

- A risk stop and a health stop never share a word, and a failed QMB run is a result with its reason, never a health stop.
- "Trading node" names the app that trades. "Connect a server" names the QMX server setup that runs workflows and the Library. The two never share a word.
- "Regime" means trending or ranging, and the old volatility buckets read "volatility state" (his word to veto).
- "Tester" names a QMB version or variant on the versions panel. He may prefer "QMB version".
- Settled here. The experience pass's stage line (Backtested, Stress-tested) gives way to the lifecycle's per-market states, because the judge's verdict moves a unit to Tested, not the kind of run (Part B AD-207, Part A AD-115). The run kinds stay as worlds on figures.

## 1. First start and the getting-started panel

Folds into Home's left column, above "Needs you", while unfinished. His words, "Remember, all this is meant to work right out of the box." (T3:1102).

- The first-start card stays as designed (new, open, restore, bring in).
- A "Getting started" panel with six lines that tick themselves from facts. Practice data, the example unit, a first backtest, your own unit with the copilot, a trading node on This PC, a broker demo sign-in. Each line has one button and one sentence, and states not started, running, done, or needs you.
- One-click enables on the first-start card for QMB, the MIS and the trading node.
- The dummy unit waits as a draft from first start with its check result and a one-click publish. The ported dictionary waits as one collection, "239 pages, all passing", with one publish click.
- A "What works today" line names anything not connected in plain words ("No broker signed in. Everything up to backtests works without one").
- Backend. The dummy's landing (A7), the dictionary's landing and the collection publish route (A12, A13a), the QMB and MIS enables (B6, C-09). A getting-started state computed from facts is not built yet.

## 2. Home

Folds into the designed Home ("Needs you", "Going on", Pods, Markets, News).

- **Needs you** carries proposals (a few a morning, the rest queued), units stopped by a risk rule, nodes that need him (sign-in ended, healing keeps failing), and the getting-started lines. Each item is one line, one primary button and a link to its evidence.
- **Going on** carries backtests running (who ran them, on This PC or a server), node setups in progress, and deploys warming up.
- **A nodes strip**, one tile per node (name, This PC or the server's name, state word, local time, clock dot, units, last heartbeat age). Tap opens the node page. The same tiles sit in Portfolio's header.
- **A morning card**, which fits one phone screen. Per live unit what it did (traded, skipped and why, missed), stops, nodes in one line, proposals.
- Backend. Proposal cards (B13), node heartbeats through the host route (C-06), the morning templates (B20).

## 3. The copilot while it writes a unit

Folds into the copilot's right-hand panel. His words, the agents should get feedback "the same way you yourself, when you write code, you can receive a linter error" (T3:1264), "no false positives" (T3:1264).

- The unit draft as a card beside the chat, filling slot by slot (market and timeframe, entry parts, exit set, sizing), each number with its origin label.
- Under it the latest check. "N problems", each in one line (where, what, the hint), errors first. When empty, "Checks passed" with the layers named on tap. A "No progress" line when the same problems came back twice, with what the copilot stopped on.
- A backtest card in the chat (queued with place and machine, running, landed), opening the QMB run page.
- A "plain Python" badge when the unit was written outside the template. It still gets every other screen.
- Backend. `unit_check` with `qmx.check/1`, counts first, and `unit_explain` (A8), the hook's feedback (A14), `backtest_run` (B6).

## 4. The unit in the Library, card and page

Folds into the unit kind's card and page, whose tabs Logic, Results, Family tree, Markets and Versions exist in its schema.

**Card (preview).** Name and version, state per market, market class and markets, origin ("video, 12:40"), today's trades and R, a one-line "why it didn't trade" when it skipped, the tries behind its verdict, a spark line of its last 30 trades in R, a placeholder stripe when any slot holds a placeholder, open proposals.

**Page (detail).**

| Tab | Shows | Backend (PR) |
| --- | --- | --- |
| Overview (proposed) | two sentences on what it does, its parts by slot, where it is deployed (node, account, world) | `unit_explain` (A8), node `units` (C-10) |
| Logic (exists) | the slots in trader words, each with its block and status; the combiner in one sentence ("all of these", "2 of these 3") | `unit_explain`, pins (A8) |
| Numbers (proposed) | every number with its value now, its range as a dial, kind, origin, last move with its receipt on tap, an "at its limit" mark | number specs (A3), calibration rows (B9, B15) |
| Checks (proposed) | the latest check per layer, the G safety verdict and behaviour report (trades on the slice, exits fired and unfired, constant signal), the checker version | `qmx.check/1` (A6), the `test-report` G fields (A7, B6) |
| Blocks (proposed) | every pinned block, its version and status, and "a fix is available, making a new version re-tests it" | pins, entry status (A11) |
| Results (exists) | runs in money and R, with tries, data label, QMB version, who ran each | `backtest-result` (B3, B6) |
| Journal (proposed) | the journal view of section 6, filtered to this unit | `journal_query` (B15) |
| Markets (exists) | per market the lifecycle state with who moved it last (the judge, his click, a risk rule), record in R, data level offered against needed, candidates with their judged numbers only, refused markets with the reason | the lifecycle fold (A9, B13), layer D (A6, C-02) |
| Readings (proposed) | which readings it declares, each with its fallback and its freshness on each deployment | the unit's `reads` list (A2), reading history (C-24) |
| Calibrations (proposed) | each move of a calibrated number with its receipt | calibration rows (B9) |
| Notes and proposals (proposed) | agents' notes with their receipts, proposal cards with his click | `note` version 2 (B15), proposal cards (B13) |
| Family tree, Lineage, Versions (exist) | parent and children; source to unit to version to result; each version labelled by its edit kind ("range change, new version") | Library links, `qml.identity.classify` (A9) |

Buttons. Backtest · Promote to paper · Promote to live · Open in Lab · Add to copilot.

## 5. Publish, promotion and the deploy dialog

- **Publish (his yes on a draft).** One card. What the unit is in two sentences, the checks passed, the placeholders it carries (a stripe naming them), what may move by itself (each calibrated and derived number with its range). The button runs the full check, and if it fails the card lists every problem instead. Backend, the Library publish with the checker (A7).
- **Promotion toward paper or live.** One card per promotion, saying in one sentence what it admits (unit version, world, node, account, markets), what changes against what is live on that market (the document diff in trader words, the edit labels, the pinned blocks that differ), whether it is a new version or a new unit, "Admitting this version parks version N on EURUSD" when another is live there, which QMB version its evidence came from, and whether it carries placeholders. A live card for a unit with placeholders needs his tick on that line. "nothing actually ever enters live without me" (T1:1574).
- **The deploy dialog**, from a unit or from a node ("Add unit"). Pick a node (Ready ones only), an account, the market from his admitted list. Paper starts from the unit's defaults. Live starts from what paper learned, and the dialog shows those numbers. A preflight list runs by itself and explains each red line in one sentence. Same fingerprint as tested; this node's versions match; warm-up history available; a record for each market at this broker; minimum lot fits; clock fine; each reading available or with a fallback; placeholders on a live account need his tick; two units on one symbol of a netting account; the unit's files have reached that machine ("copying 3 files"). There is no size limit. Then accepted, compiling, warming up, trading. "Withdraw" and "Back to paper" stay one click away.
- When the node is unreachable at the click, "Waiting for London-1. It applies when London-1 is back."
- Backend. The This PC host route `POST /api/units/promote`, his principal only, not a catalog row (C-23), `qml.identity.diff` and `classify` (A9).

## 6. The journal view

Folds into the unit page's Journal tab and the Trading tab the design has. His words, "The journal is very important, please." (T3:903), "this is literally the DevOps layer for that unit" (T1:1574).

- One timeline per unit, filterable by world, phase ("paper, after live, drift alarm 2"), instrument, timeframe, broker, account, platform and node.
- Row kinds with their own marks. Trade taken; seen and not taken, with the gate that said no; missed, found by replay; a number moved, with its receipt; a stop, with its rule and values; a heal on its node; an agent note, with evidence and expiry; a phase change.
- On a trade, entry and exit, result in R and money, costs in R, worst and best swing in R, the readings at entry, and the inputs of its market-following numbers ("stop 12.3 pips = 1.5 × ATR 8.2").
- "Why didn't it trade at 14:02?" Tap a time and see the gate trail at that minute, in one sentence ("Skipped, spread was 2.4 pips against its 1.5 limit at 08:01 London").
- A row from a node that has not reached the PC yet shows "on London-1, not yet here".
- Backend. The journal kinds (B8), QMB run journals (B9), `journal_query` (B15), records home from servers (B16).

## 7. The judge and his click

- **Verdict view**, per market. The raw result, the pulled-back result, trades, pass or fail per step with what each step can and cannot catch, the effective number of tries, the preset used, and "too thin to judge" with how many more trades or weeks.
- **Proposal card.** What it asks (paper, live, add or drop a market, tighten, bench), the verdict, the try count, the placeholders still in the unit, the evidence links, who proposed it. One button, his click. Nothing on the card moves a unit by itself.
- **Study spec editor** (the run config, editable). Markets, windows, record needed, preset, holdout (off by default), cost and fill rules, allow gaps, motion. Before any result, edit freely. After a result the editor says "this edit counts as a try" before saving.
- Backend. The judge, its kinds and `judge_run` (B13), the conformance check (B12).

## 8. The dictionary pages

Folds into the Library's item page for the `component` kind (Code, Parameters, Uses, Used by, Versions exist). The entry faces are proposed as the top of that page. Agents use the dictionary most, and he sees it through a unit's origin labels and a dictionary shelf like any kind.

- **Entry page.** Three faces as three sections. What a trader means, with each class's meaning and the sources with their quotes and dates. What data it needs, with the data level, the fallback chain and its expected loss. The code, with status, golden tests and settle length. "Used by" lists the units that pin it.
- **The port card.** "Publish the ported dictionary, 239 pages, all passing", with a list he can scroll and one publish click.
- **Append requests.** Words an agent found in a source that match no page, each with its sentence and source, as proposals he can accept into drafts.
- Backend. `blocks_get`, `blocks_find`, `blocks_match` (A11), the port and its collection publish route (A12), the content wave (A13a to A13d).

## 9. The QMB app: what ran and who ran it

QMB ships `headless`. This screen arrives when the UI session adds QMB's `ui` folder and flips its kind to `both` (one manifest line). Until then the same facts show through the Library's generic pages and the copilot. His words, "So if one day I decide to build a new version of QMB, I should be able to." (T3:1383).

| Tab | Shows |
| --- | --- |
| Runs (the default) | one row per run, newest first. When, who ran it (a copilot chat, a workflow run, him, an agent in the Lab) linking to its source, unit and version, tester (app and version), markets, window, where it ran (This PC or a server), status, the verdict word if judged, the family's try count. Filters by unit, family, tester, status and who |
| A run's page | Summary; Equity in R and money (a toggle); Trades with MAE and MFE in R, costs split and the context receipt; Robustness as three-word readouts plus numbers; Journal (signals taken and skipped with reasons); Slices by session and by readings state; Data used (cards, seams crossed); Comparable runs; Who ran it; History. "Run again" and "Run on variant" |
| Versions | installed testers, the default, each one's last conformance result (pass, or the diff), a parity diff between two testers on one request. Changing the default refuses a tester without a passing check and says why |
| Queue | what waits, on which machine, in what order |
| Operations, Setup, Logs (as designed) | one card per operation, runnable by hand; defaults (fidelity, cost model, windows, the judge's numbers); the app's own log and health line |

- Banners, never hidden. "costs uncalibrated", "no trades", "placeholders in this unit" (with the list), "crosses a data seam".
- Health in plain words. "QMB stopped after 3 errors at 14:02 and started again at 14:02:05." It restarts itself with back-off.
- Backend. `try` items and `backtest-result` fields `principal`, `place`, `tester`, `status` (B3, B6), the app's own logs, conformance (B12), the run kinds (B14).

## 10. The trading node app

The mini-app page as designed, with Operations and Setup tabs. His words, "is it going to start as server, then show me that the server has started?" (T3:1102), "the trading node is perhaps a firm" (T3:903).

**Nodes list.** One card per node (name, where, market class, state word and reason, local time, clock dot, units trading, paused and stopped, last heartbeat). Buttons "Start on This PC" when none runs there, and "Add a server".

**Node page tabs.**

| Tab | Shows | Backend (PR) |
| --- | --- | --- |
| Overview | the state word and reason in large type; where it runs; its local time beside his; clock offset and band as a dot; each venue's session; units summary; kill level; "Pause all", "Kill switch" with its levels, "Update", "Roll back"; the broker's own app named as the last way to close everything | `status` (C-10) |
| Units | each deployment's world, account, markets, state per market, last trade, today's result in R; pause, resume (his), withdraw | `units` (C-10, C-12a) |
| Positions | each position with its stop shown at the broker and when it was last seen there; untagged positions flagged "not ours, protected" | `positions` (C-12b) |
| Readings | this node's markets and the readings computed here and by the MIS beside it, each with its freshness; a badge when a unit used a fallback | node `status`, `mis` `status`, `readings_query` (C-09, C-24) |
| Heals | every restart it made by itself, what, why, when (his time and node time), how many today, and the item it raised when healing keeps failing | node journal (C-13) |
| Deploys | every deploy, withdraw, update and rollback, by whose click, from which PC, applied or "waiting for London-1" or "copying 3 files to London-1" | `deployments`, the node link's outbox (C-06, C-23) |
| Checks and passport | the self-test lines with their last result, round trip to each venue, grant and agent-wallet expiry dates | `passport` (C-11, C-15) |
| Logs | the node's logs, with a link to that machine's deep logs | the log shipper, OpenObserve (C-04) |

**Starting a node.**

- On This PC, one button on the getting-started panel and on the Apps page. Steps that tick. Checking this PC (clock, disk); waiting for cTrader to approve your app, with the link and what to paste; installing; your signature for this node version, shown as one step; signing in on cTrader's page; measuring the round trip; a self-test with a small demo trade and its stop; ready. A note up front, "Runs while this PC is on. For round-the-clock trading, add a server."
- On a server, the connect dialog's card-then-steps pattern with the trading-node kind, the keys window on the server for the Hyperliquid agent wallet, and the same step list.
- A failed step shows one line and two buttons, "Run this step again" and "Help". Running the setup again picks up where it stopped.
- Binding a live account is a separate, deliberate flow on the node page. It turns off chats and agent steps on that server first and says so in one line, then the bind, then the soak card.
- Backend. The connect kind (C-11, C-17), the bind-live steps (C-21).

## 11. Several nodes, one clock

Folds into the Home nodes strip and the Portfolio header.

- A world clock strip. His time first, each node's local time with its name, market sessions as bands drawn in each market's own zone so they shift through daylight saving by themselves, crypto all day, futures with their exchange hours.
- A notice a week before a zone-mismatch week ("London and New York are 4 hours apart from 25 Oct to 1 Nov").
- An unreachable node greys out with "unreachable since 03:12 (your time)" and its last values. Its account's positions still show from the PC's view-only broker read, labelled "read from the broker".
- Backend. Clock facts in heartbeats (C-01), calendars for every market (C-03).

## 12. Stops, cards that need his click, and alarms

Each card is an urgent inbox item when trades are open, and a row in the unit's journal.

- **Stop card.** What stopped, when (his time, UTC, node), which rule and its values, what happened to open trades (kept with broker stops, or closed), risk rule or health check, and what it takes to resume. Resume (his), Back to paper, Retire.
- **Change card**, when a broker changes a symbol. The old and new facts side by side, the checker's rerun, the units paused. Accept, Keep paused.
- **Identity card.** "This node's disk moved or was copied." Two buttons, "This is the same node, moved" and "Take over a dead node", which asks him to confirm the old one is gone and shows its last heartbeat. Then a line, "Sign in on cTrader again. Sign-ins never travel with a node."
- **Twin alarm.** "Another copy of this node may be trading this account." Entries stopped, and what to check.
- **Soak cards** on a release and on a live binding. Time done against 24 hours on This PC and one week on demo. Shown, never blocking. His click decides.
- **What wakes him.** A risk stop with open trades, a node unreachable with open trades, a broker link down with open trades, a clock in the halt band for 5 minutes, healing that keeps failing. Everything else goes to the morning card. The list is editable in Settings.
- Backend. The stand-down table and risk stops (C-12c), healing (C-13), attribution (C-12b), alarms and the liveness ping (C-18).

## 13. The MIS on his PC

Portfolio's MIS tab as designed (Live and Shadow switches, a since time, a value). His question, "should it have some sort of like its own section in the QMN mini app?" (log 2026-10-31T10:43), is answered by both. The Readings tab on each node, and this tab on his PC, read one store.

- Per reading its version, its clock, its markets, its freshness word, and which units read it with which fallback.
- A history chart with its state changes.
- "default" on readings his models will replace. "Let's make defaults for the MIS. I'll train the models when I can." (T3:1264).
- A shadow model's record beside the default, and his yes to make a shadow reading live.
- Backend. The `mis` app and its board (C-09), reading records (C-08), `readings_query` (C-24).

## 14. Workflows

- Inputs that pick stored readings and journals ("trend state, FX majors, last 20 sessions"), never "the MIS" as a model. "They should be using the logs from the MIS." (T3:903).
- Triggers per market session and per N closed trades, beside cron. Not built in this program.
- The slow-lane templates as a group (pre-session shortlist, market review, daily data review, unit review, node watcher), each with its last output and, where it makes calls, its score from the forecast ledger.
- Notes, almanac pages, shortlists and forecasts render as Library pages, and each number links to the receipt behind it. A forecast shows its call, when it was made, and its score once scored.
- Template cards show their loop counts and windows as numbers he can change, with no caps, and a draft says in plain words which door it waits for.
- Backend. The shared pieces (B18a, B18b), the fixed templates (B18c), the build family (B19), the slow lane (B20), the node watcher (B21).

## 15. Apps

The design's Apps screen (Pinned, Markets, Watching, Research, Trading helpers).

- QMB and the trading node pinned by default, each card with its one most useful line ("2 runs going on", "London-1 trading · 3 units").
- Unit apps, a card showing a unit's state whose page shows its journal through its feeds.
- "New app, from a unit" in the New app menu. "Safe mode" and "Discover" stay as designed.
- Backend. The first-party apps (B6, C-09, C-10), the example apps running in CI (B2).

## 16. Settings

| Area | Adds |
| --- | --- |
| Clocks (small, new) | display zone; each machine's offset and sync state; a button to turn on this PC's time sync (his click) |
| Keys | where each venue key lives ("lives on: London-1"); expiry dates; "Rotate" |
| Alarms | the ntfy topic and the Healthchecks.io check, a "send a test" button, the short wake list (editable) |
| Machines | nodes as their server's place with a trading-node mark, This PC first, each with its clock health |
| Connections | CCXT rows that read perps; Hyperliquid with testnet; a paid futures data route as a row he adds later, with its monthly cost shown as a reading, never a cap; a data entitlement line per machine ("depth feed, not on this machine") |
| Units | the identity table he can read; `lifecycle.auto_paper` (off); first-look window, judging window start, record clock, evidence weight, proposals per morning |
| QMB | the default tester; `agent_wait_s`; the memory tolerance; the behaviour slice margin |
| Records | `open_harvest_s`, `tick_harvest_s`, "Bring node records home" on or off |

## 17. The maintenance list and data health

- The built maintenance screen (`GET /api/maintenance`) adds "Bring node records home" with its off switch, the last round's counts per node, "oldest month still on the node", and how many months each node keeps pinned until This PC confirms them (B15, B16).
- A daily data note. Gaps, clock flags, fetch failures, seams and cross-source offsets per market, as a short list with links to the cards (B11, B20).

## 18. What these screens do not need

- No separate risk screens. Risk and sizing get placeholders and their own session. The placeholder stripe and the stop card are the only risk surfaces here.
- No router screens.
- No per-machine dashboards beyond the node page and a link to the log viewer.
- No screen for the dictionary's internals.
- No browser stream, so nothing needs resuming.

## 19. Gaps the UI will meet

| Gap | Where it stands |
| --- | --- |
| A getting-started state computed from facts | not in this program; the facts exist (A7, B6, C-09, C-10, C-11) |
| The run list's place on each run | `backtest-result` carries `place` (B6); the run read lacks it (`tracker/qma-v2/UI-HANDOFF.md` section 26, row 1) |
| The cTrader app key entry | the connect kind's waiting step (C-11) |
| Session and trade-count triggers | not in this program |
| QMB's own screen | one manifest line once the UI session adds its `ui` folder |
