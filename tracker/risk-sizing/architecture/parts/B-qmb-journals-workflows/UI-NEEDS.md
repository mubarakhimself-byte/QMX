# UI needs and screen proposals from part B

Design intent and proposals for the UI session. No UI code is written or edited (STATE midday ruling 45: his designs are not touched). The UI is judged by its design, by running it (ledger UI-03). These build on what mini apps and Library kinds were designed to do: an app's screen is its `entrypoints.ui` folder once its kind is `both`, and every Library kind already declares a **card** (preview) and a **page** (detail view) with tabs in its schema file (Library AD-33), so most of what follows is data part B writes into kind files and the UI renders. His words: "we have a preview and a detailed view. So, design for both." (T1:1574).

## 1. QMB's screen: what ran and who ran it

QMB ships `headless`; this screen arrives when the UI session adds QMB's `ui` folder and flips its kind to `both` (one manifest line). Until then the same facts show through the Library's generic pages.

- **Runs list.** One row per run, newest first: when; who ran it (a copilot chat, a workflow run, him), linking to that chat or run; the unit and version; the tester (app and version); the markets; the window; the status (queued, running, finished, failed, killed); the verdict word if judged; the family's try count. Filters: unit, family, tester, status, who. Source: `try` items and `backtest-result` fields (`principal`, `place`, `tester`, `status`).
- **A run's page.** The `backtest-result` kind's tabs: Summary, Equity (in R and in money, a toggle), Trades (with MAE and MFE in R, costs split, the context receipt), Robustness (three-word readouts plus numbers), Journal (new: signals taken and skipped with reasons), Slices (new: by session and by readings state), Data used (cards, seams crossed), Comparable runs, Who ran it (new), History. Labels shown as banners, never hidden: "costs uncalibrated", "no trades", "placeholders in this unit" (with the list), "crosses a data seam".
- **Versions and variants panel.** Installed testers, which is the default, each one's last conformance result (pass, or the diff), and a parity diff between two testers on one request. Changing the default is a setting that refuses a tester without a passing check; the panel says why.
- **Queue and health.** The app's own logs already hold `job_completed`, `tool_error` and `breaker_open` with reasons (`qmx_apps/supervisor.py`); the screen shows the running and queued runs and the last health stop in plain words ("QMB stopped after 3 errors at 14:02 and started again at 14:02:05"; it restarts itself with back-off). A failed run is a result with its reason, never a health stop. A health stop is never shown as a risk stop.

## 2. The unit's journal, preview and detail

- **Preview card** (the `unit` kind's card, Part A's kind; part B supplies the journal facts): state per market, today's trades and R, a one-line "why it didn't trade" when it skipped, the tries behind its verdict, a spark line of its last 30 trades in R.
- **Detail page tabs** (proposal; Part A owns the `unit` page): Journal (by world: backtest, stress, paper, demo, live, with a world filter that never mixes paper into live figures), Markets (per market: lifecycle state with who moved it last, the judge or his click or a risk rule, record in R, the readings range it earned in), Calibrations (each move of a calibrated number with its receipt), Runs (QMB results), Notes and proposals (agents' notes rendered with their receipts; proposal cards with his click), Lineage (source to unit to version to result), History.
- **"Why didn't it trade?"** One sentence from the latest `signal` rows: the reason code in plain words, the gate, and the market minute it points at ("Skipped: spread was 2.4 pips against its 1.5 limit at 08:01 London").

## 3. The judge and his click

- **Verdict view.** Per market: raw result, pulled-back result, trades, pass or fail per step with what each step can and cannot catch; the effective number of tries; the preset used; "too thin to judge" with how many more trades or weeks.
- **Proposal card.** What it asks (paper, live, add or drop a market, tighten, bench), the verdict, the try count, the placeholders still in the unit, the evidence links, who proposed it. One button: his click. Nothing on the card moves a unit by itself.
- **Study spec editor** (the UI-editable run config). Markets, windows, record needed, preset, holdout (off by default), cost and fill rules, allow gaps, motion. Before any result: edit freely. After a result: the editor says "this edit counts as a try" before saving.

## 4. Journals home and data health

- **Maintenance list** (built screen, `GET /api/maintenance`): add "Bring node records home" with its off switch, the last round's counts per node, "oldest month still on the node", and how many months each node keeps pinned until This PC confirms them.
- **Daily data note.** Gaps, clock flags, fetch failures, seams and cross-source offsets per market, as a short list with links to the cards.

## 5. Workflow outputs

- Notes, almanac pages, shortlists and forecasts render as Library pages; each number links to the tool receipt behind it.
- A forecast shows its call, when it was made, and its score once scored, so he can see which analyst lane earns its keep.
- Template cards show their loop counts and windows as editable numbers (no caps), and a draft says in plain words which door it waits for.

## 6. Words on his screens (his to veto)

"Try", "study", "verdict", "baseline", "proposal", "world", "health stop" and "risk stop" are the glossary's working words. "Tester" is used for a QMB version or variant on the versions panel; he may prefer "QMB version".
