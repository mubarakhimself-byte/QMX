# Journeys and scenarios

Every user journey, scenario and walkthrough found, checked against the code on `origin/engine/base` (`3ae41ffc`, 2026-11-08). For the UI session and for QA click-through tests.

## Read this first

- **No screen is wired.** The UI on `engine/base` is the 1 October baseline (`apps/qmx-ui`, last commit 2026-10-01). The UI rebuild branch `ui-review/repair` exists only on this PC. There is no desktop shell in the repo either (no Tauri or Electron). The host is a command line with exit codes meant for a desktop app (`qmx-agents/packages/qmx-host/src/qmx_host/__main__.py`). So "matches" below always means the **backend** does it. You reach it through the copilot, a REST route or a command, never through a screen. Read in code.
- **Nothing has run on his real folder or a real demo account.** The first real start and the cTrader demo proofs wait for his one sign-in on cTrader's demo page (PR #328 body, PR #352 body). Read on GitHub.
- **Risk and sizing are placeholders.** The risk-core build (#353-#369) is open and not shipped. Every journey that needs a real risk rule is at most "partly". Proved by gh.

**Status words.**

| Word | Meaning |
|---|---|
| Matches | The shipped code does each step. Proved by a merged PR, and the main file was read in code where cited. Not click-tested, because there are no screens. |
| Partly | Some steps are shipped and some are not. The row says which. |
| Never built | No merged PR does it. |
| Superseded | Written for an older design whose code was deleted or replaced. |

**Who it is for.** Him = the operator as the trader. Newcomer = a new user out of the box. Copilot = his chat agent. Agent = a QMA workflow agent with nobody watching.

---

## A. The main journeys: J1 to J25 (most important)

Source: `tracker/risk-sizing/architecture/funnel/experience/design-thinking.md` on branch `plan/unit-system`, written 2026-10-31 with `bmad-cis-design-thinking`. It is the journey set the unit build (#235-#328) and the repair (#329-#352) were built for. Companion screen intent: `tracker/risk-sizing/build/UI-NOTES-UNITS.md` (section F below) and `funnel/experience/ui-needs.md`.

| ID | For | Steps in short | Shipped feature it exercises | Status |
|---|---|---|---|---|
| J1 | Newcomer (and him on his first real start) | First-start card (new, open, restore, bring in). "Getting started" list. Get practice data. Open the example unit. Backtest it. Ask the copilot for a unit. Start a node on This PC. Sign in to cTrader demo. | First start #209-#214, #219, #228, #234. Dummy unit lands as a draft on first start #256. Dukascopy download template. QMB backtests the dummy end to end #261. Node on This PC #282, #288. cTrader sign-in #211, #221. | **Partly.** No "getting started" list exists in code (no match for it anywhere). Every other step has a backend. None of it has run on his folder. |
| J2 | Him, through the copilot | He gives an idea. The copilot writes a unit. On each save a list of every problem comes back, and the copilot fixes them. Checks pass. Backtest runs. Result in money and R, with tries counted. The unit waits as a draft for his yes. | Copilot writes and checks a unit #258. Problems fed back while it writes #262. Check at every layer #253. Backtest #261. Journal #267. Judge counts tries #275, #340. Plain rules like "ADX above 25" #334 (R05). Refuses what it cannot run #332 (R04). | **Matches** (backend). The side panel is UI work. |
| J3 | Agent, unattended | A trigger fires. The agent writes a unit. A script step checks it, a loop sends problems back, a script backtests it, a script judges it. In the morning, a "Needs you" card lists proposals. | Agent step writes its file #243. Build-and-prove templates #283, #296. Judge #275, #340, #341. Event triggers #160. | **Matches** (backend). The "Needs you" card is UI. The "at most 5 proposals" default was not checked in code. |
| J4 | Him | He opens a unit's numbers. He taps a number that moved and sees why (which trades, which rule, inside which range). He taps a trade and sees its stop worked out. | A unit tunes its own number with a receipt #251. Journal in every run #267. Readable journals #291. Self-tuned number reads short trades too #334. `qml/src/qml/motion/` exists. | **Matches** (backend). The Numbers tab is UI. |
| J5 | Him | A "road to live" line. A click card admits a unit to paper. Later a live card. | Promote route, his click only #302 (`qmx_host/promote.py`, operator principal only). Paper lane per unit #293. Promote edge fixes #348. | **Partly.** Paper by his click is shipped. The deliberate path to bind a live account (plan C-21) was never built. |
| J6 | Him | Start a trading node on This PC, see each setup step tick, see "Ready". Then add a server in London the same way. | Smallest node #282. Connect dialog for This PC #288. Server setup with the same steps #325. Clock proof #247. Node link #277. | **Matches** in code. Never run on a real server or demo account. |
| J7 | Him | Deploy a unit to a node: pick node, account, markets. A preflight list runs. Warm-up, then trading. Withdraw or roll back. | Promote deploys #302. Only his chosen markets #327. Records a deploy reads #323. Deployed units run, wrong symbol refused by name #349 (R22). | **Partly.** Deploy, withdraw and named refusals are shipped. A full preflight list and "back to v2" were not found in code. |
| J8 | Him | Watch a forex node in London and a crypto node in Singapore on one clock. Nodes strip, world clock, his time first. | Watch nodes without touching them #306. Bring node records home #300. Clock proof per machine #247. Calendars for every market #263. | **Partly.** The backend reads are there. The world clock and the 7-day daylight-saving notice were not found in code. |
| J9 | Him | A unit stops on a risk rule. An urgent item says what, when, which rule, what happened to open trades. He resumes, sends it back to paper, or retires it. | Node status tells the truth ("Paused, risk stop on XAUUSD") #327. Stops kept through restarts #301. Phone alarms #303, #346. Every way out acts #345 (R21). | **Partly.** The stop and its report are shipped. The risk rules are placeholders until the risk-core build lands. |
| J10 | Him | Put a unit inside a mini app: its own screen, chart, state and journal. | Mini-app core (`qmx-agents/packages/qmx-apps/`). App jobs told what to do by a workflow #236. | **Partly.** The app core is there. No "unit app" template exists (no match in code). |
| J11 | Him | Open a workflow template that reads MIS readings. Change an input. Validate. Test run. Publish. | MIS as an app #295, publishes by itself #350 (R18). Agents read readings #294. Templates `s1-pre-session-shortlist`, `s3-mis-check`. Validate, test, publish routes (engine EP9 #102). | **Matches** (backend). The graph editor is UI. |
| J12 | Him | Something fails at 3 a.m. Most things heal alone. Five kinds of trouble wake him. The rest wait for the morning card. | Node heals itself #301. Phone and liveness watcher #303. Alarms follow the market calendar #322. Alarms reach him #346. Broker wins after a cut #343. Back-off on a broken connection #351. | **Partly.** Healing and alarms are shipped. The single morning card is UI plus the slow-lane notes (#305). |
| J13 | Him | "Why didn't it trade?" He sees the gate trail at that minute, or "missed, node offline". | Readable journals with one harvester #291. Spread at that minute #344 (R19). | **Matches** (backend). |
| J14 | Him | A drift alarm becomes a "Send back to paper?" card. He clicks. Later "Back to live?". | Decay template `dc-decay-and-limit-report`. Lifecycle moves only by his click #250, #337. | **Partly.** Back to paper by his click works. Back to live needs the live path (C-21), which was never built. |
| J15 | Agent, then him | The slow lane proposes adding a market to a unit. He clicks "attach". | Slow lane on This PC #305. Templates `s2-tag-units-to-markets`, `u1-run-on-every-market`. Markets chosen on deploy #327. | **Partly.** Proposals are made. A separate "attach" step was not found; markets are chosen at promote. |
| J16 | Him | Build a new QMB version, or run two variants side by side. Results name their version. | Prove a QMB version before it becomes default, variants side by side #281. | **Matches** (backend). |
| J17 | Him | Add Hyperliquid perps through CCXT, testnet first. A perp unit counts funding. Deploy to a Singapore node. | Contract markets read on This PC #265. Hyperliquid through CCXT on testnet #298. | **Partly.** Testnet only, never run against a real testnet wallet. |
| J18 | Him, newcomer | Write a unit in plain Python or bring a trained model. The checker labels it and treats it like any unit. | `qml/src/qml/check/layers.py` and `compile/compiler.py` mention plain Python. The repair refuses features QMX cannot run #332. | **Partly.** Not traced end to end in this pass. |
| J19 | Him | Update QMX while a node trades. "Update London-1" waits for a safe moment. Roll back. | Store versions and upgrade after a backup #213. A repair to the node waits for his signature #331. | **Partly.** "Update a server's node at a safe moment" (plan C-19) was never built. |
| J20 | Him | His PC is off for two days. On return, the node's records come home. | Bring node records home #300. | **Matches** (backend). |
| J21 | Him | A unit retires and still teaches: cause, lineage, family tree, counts of which sources made survivors. | `death-certificate` Library kind. Build-and-prove template writes one. | **Partly.** No monthly source count was found. |
| J22 | Him | Daily and weekly rhythm: one morning card, a pre-session shortlist, weekend reviews. | `morning-digest`, `s1-pre-session-shortlist`, `rv-weekly-review` templates. Slow lane #305. | **Partly.** The templates exist. No single morning card joins them. |
| J23 | Him | The week London and New York are 4 hours apart. Session rules follow each market's own clock. | Session blocks use the market's clock #337 (R06). Calendars #263. | **Partly.** The clock is right. The 7-day notice was not found. |
| J24 | Him | Switch on a paid futures feed later. Order-flow units wait for data until then. | Futures replayed contract by contract #278. A Databento provider file exists (`qmx_broker/providers/databento.py`). | **Partly.** Not checked as a working feed. |
| J25 | Agent | The dictionary meets a new word. The agent drafts an entry. It stays "named" until it has code and a test. | Dictionary doors #266. 239 entries ported #270. Checks and true status #337 (R06). Template `u3-dictionary-expansion`. | **Matches** (backend). |

---

## B. The repair's "You see" lines: the newest promises (best click-through checklist)

Source: `tracker/risk-sizing/build/repair/REPAIR-PLAN.md`. It is only on the LOCAL branch `plan/unit-system` (worktree `D:/QMX-worktrees/unit-plan`), not on origin. Each line is written to him. All 24 PRs merged (#329-#352, proved by git). These are the latest statements of what he should see, so QA should test these first. Each is "Matches" by merged PR, unless marked.

| Repair | For | What he should see, short | PR | Status |
|---|---|---|---|---|
| R01 | Him | Nothing changes. About 46,000 misleading lines removed. | #329 | Matches |
| R02 | Him | Nothing on screen. The checks stop reading red for no reason. | #330 | Matches |
| R03 | Him | QMB and the MIS pick up a repair at the next start. The node waits for his signature. A stuck install stops after 30 minutes. | #331 | Matches. Note: #328 said the uv wait had no time limit; R03 carries that fix. |
| R04 | Copilot, him | A unit using something QMX cannot run is refused, naming the field. A long-only unit never sells short. | #332 | Matches |
| R05 | Him, copilot | "Only enter when ADX is above 25" builds a unit that does that. Level 99 places no trades. | #334 | Matches |
| R06 | Him | Dictionary pages show their real status. New York open stays 9:30 New York time all year. No setting moves a unit to paper without his click. | #337 | Matches |
| R07 | Him | Backtests use the contract facts in his Library. A market with no record says so. | #333 | Matches |
| R08 | Him | Download a month, ask for a backtest on it, the result names the data. A missing month is named before anything starts. | #335 | Matches |
| R09 | Him | Long history runs faster. Short data is reported. Holidays are not "missing data". | #338 | Matches |
| R10 | Him | Results show drawdown and how close each trade came to its stop, in R. Costs say "not calibrated". A restart closes a run as failed. | #339 | Matches |
| R11 | Him | The judge cannot be argued with. A friendlier study is a counted try. No market can be dropped for looking bad. | #340 | Matches |
| R12 | Him | One paper per decision with the real reason. A model cannot talk a failed unit into a pass. | #341 | Matches |
| R13 | Agent | Agents can build and prove a unit on any market with a record. | #336 | Matches |
| R14 | Him | One short message of what now works, and one thing to ask the copilot: "Build me a unit on EURUSD from the dictionary blocks that only enters when ADX is above 25, backtest it on March 2025, and tell me in plain words what the judge says." | #347 | **Partly.** The proof runner `tools/proof_foundation.py` shipped. Its check 18 (the real sentence on a real host) runs only with `QMX_TEST_LIVE=1`. The PR says some checks were on other branches at that head. Read on GitHub. **This sentence is the best first QA click-through.** |
| R15 | Him | Every practice-node trade reaches his Library and counts toward its paper score. | #342 | Matches |
| R16 | Him | Phone alarms work on the installed node. Log-server outages are reported. | #346 | Matches |
| R17 | Him | A promote click on a slow node waits and lands once. A refused deploy can be clicked again. | #348 | Matches |
| R18 | Him | The MIS publishes readings by itself after a download. | #350 | Matches |
| R19 | Him | "Why didn't it trade at 08:00?" shows the spread at that minute. | #344 | Matches |
| R20 | Him | After a cut, the node learns the broker's truth: stop fills at broker price, hand-moved stops show. | #343 | Matches |
| R21 | Him | RED closes every position at that scope. Flatten really closes. Refused closes keep trying. | #345 | Matches |
| R22 | Him | Promote a unit on gold and prices arrive with no restart. A wrong symbol is refused by name. A 5-minute unit is refused on 15-minute bars. | #349 | Matches |
| R23 | Him | Back-off on a broken connection. A forex node reads "closed" on weekends. Manual trades read "not ours, never touched". | #351 | Matches |
| R24 | Him | One script checks the node is ready for a unit on his real folder. With no unit it says "no unit has passed the judge yet". | #352 | Matches in code. Never run on his real folder. |

---

## C. The unit build's "You see" lines (one per planned PR)

Source: `tracker/risk-sizing/build/UNIT-PLAN.md` on `plan/unit-system`. 91 sections. All are written to him. The table is in Appendix 1 at the end of this file, one row per section, with its PR and status. In short:

- 87 of 91 sections were built and merged (#235-#328). Proved by git.
- 4 were **never built**: C-15 (prove attribution and refresh on a cTrader demo), C-19 (update a server's node at a safe moment), C-20 (cut the old node shell, about 47,000 lines), C-21 (the deliberate path to bind a live account).
- Many sections say "Nothing yet" or "Nothing on screen". They are plumbing, not journeys.
- Several were later changed by the repair. Appendix 1 names the repair PR beside them.

---

## D. Earlier programs' "You see" lines (October)

Sources on `plan/agent-system` under `tracker/qma-v2/`: `HARDENING-PLAN.md` (58), `DATA-PLAN.md` (30), `WRAPUP-PLAN.md` (12), `LOCAL-FIRST-PLAN.md` (8), `LOOSE-STRINGS-PLAN.md` (7), `BACKUP-RESTORE-PLAN.md` (7), `SYNC-PLAN.md` (5), `MOCK-DATA-PLAN.md` (3). These "You see" lines are mostly check lines for builders (a command and its expected output), not journeys for him. All rows are in Appendix 2. What matters for the UI session:

| Plan section | What it promised | Status today |
|---|---|---|
| Data DR3B, holdout lock in the price door | Sealed months refused | **Changed.** WU11 (#207) opened the door by default; a holdout is now his choice per study, and R08 (#335) keeps a study's sealed months out of every run. |
| Data DR5B, cTrader sign-in through the server | Server holds the token | **Never built.** LF7 (#211) and LS3 (#221) sign in on This PC instead. |
| Data DR2E, Hindsight on the server | Memory engine on the server | **Never built.** |
| Data PRB-CT, cTrader probes on demo | Three probe rows | **Never built.** It waits on his demo sign-in. |
| Wrap-up WU4, agent backtests run and land | Copilot backtests an example bot | **Not merged (PR #204 open).** The unit build's QMB app (#261) covers the backtest path for units instead. |
| Wrap-up WU10, cTrader reads through the server | PC read goes through the server | **Never built** (#211 body: waits on G-CT). |
| Hardening AGW, agent steps write local files | Agent commits a component file | **Never built** in that form. B17 (#243) later let an agent step write only the file it was asked for. |
| Hardening RTR7, the Claude-plan router lane | Opus copilot asks Kimi and Qwen reviewers | **Never built** (skipped by its probe, per HANDOFF-2026-10-24). |
| Local-first LF5, no server in the defaults | No connection to the old server address | Matches (#208). Every server journey in the hardening and data plans is now opt-in. |
| Backup B6 and B7 | Off-site copies; keys sealed with a passphrase | B6 folded into SY3 (#233). B7 was **dropped** (SYNC-PLAN: "he never asked for it"). |

---

## E. Domain scenarios K-01 to K-34

Source: `tracker/qma-v2/research/methodology/46-domain-expansion.md` (34 kept scenarios out of 214 ideas, BMad party mode and CIS techniques), with coverage in `47-studies-folded.md` section 5. Branch `plan/agent-system`. Written 2026-10-18, before most of the code. For him and the copilot unless marked.

| ID | Scenario | Shipped feature | Status |
|---|---|---|---|
| K-01 | One idea end to end: video, hypothesis, tests, verdict, paper | Sources and hypotheses in the Library (#131, #136), build-and-prove (#296), judge, paper lane (#293) | Partly. Video intake goes through the upload door (#193); not traced end to end. |
| K-02 | A session moves between places and pulls context from anywhere | Context references (#143), sessions saved as Library items (#141) | Partly. `POST /api/chats` had no `home` field per HANDOFF-2026-10-24; not rechecked. |
| K-03 | Memory follows the subject and can forget | Memory on Hindsight with built-in search as backup (#153); `memory` toolset has `forget` | Matches (backend) |
| K-04 | The hypothesis ledger | Hypotheses get a status (#136) | Partly |
| K-05 | Honest numbers everywhere | Judge (#275, #340, #341), costs "not calibrated" (#339) | Matches for backtests |
| K-06 | Family and holdout accounting across agents | Tries counted (#275), friendlier study counts as a try (#340), study seals (#335) | Matches |
| K-07 | Bad news travels: taint, supersede, recover | Marks travel upstream (#136), `library_mark` reaches a chat (#201) | Partly |
| K-08 | The Lab and a mini app use one object | Workflows read the Library, apps run from it (#188) | Partly |
| K-09 | Mini apps feed mini apps across machines | Apps ask each other (#146), app homes across machines (#161), event triggers (#160) | Partly. Server parts are now opt-in (LF5). |
| K-10 | One app, many setups | App setups (#146), `app-profile` kind | Partly |
| K-11 | Ask the panel; show the spread | `ask-the-panel` template | Matches (template) |
| K-12 | Four writers on one workflow | Branch, merge, blame (#195) | Partly. Workflow merge driver not checked. |
| K-13 | Two runs start the same build at once | Claims on the Hub (#157) | Partly. HANDOFF-2026-10-24 says no caller passes claims in production. |
| K-14 | Remote work and data gravity | Steps placed next to their data (#197), remote worker (#159) | Partly. Opt-in since LF5. |
| K-15 | One ops picture across machines | Heartbeat and incident shape (#134), server runs on the PC (#162), OpenObserve (#192, #260) | Partly |
| K-16 | Scheduling in market time | Trigger kinds with market time (#133), calendars (#263) | Matches (backend) |
| K-17 | Market events drive work | Webhook trigger route `POST /api/hooks/{trigger_id}` | Partly. HANDOFF says webhooks had no sender signature check. |
| K-18 | A copilot loop outlives the laptop | Remote steps (#159), adopt a run (#163) | Partly |
| K-19 | Workflows crystallise | `crystallise-a-workflow` template (#154) | Matches (template) |
| K-20 | Steer a running workflow | `delegate` has `steer` (#151) | Partly |
| K-21 | A standing research employee | Overnight templates (`t4-research-desk-overnight`, `l4-overnight-lab-loop`) | Partly |
| K-22 | A mini app breaks at 3 a.m. | Crash breaker, restart with back-off (#242) | Matches (backend) |
| K-23 | Long training on a rented GPU | Training on the PC's GPU (#194) | Partly. No rented GPU. |
| K-24 | Version skew and upgrades | Store versions (#213), install picks fresh source (#310, #318) | Partly |
| K-25 | Library hygiene at scale | Curator and parse-first search (#139) | Partly |
| K-26 | Ask QMX about its own past | Library reads "as of a date" (#136), search (#139) | Partly |
| K-27 | A secret lands in the Library | Redaction at one seam (#118), purge (#157) | Matches (backend) |
| K-28 | Pause all autonomy | Pause switch (#133, #162) | Matches (backend) |
| K-29 | A notebook cell graduates into a workflow | none found | **Never built** |
| K-30 | Fork a session for parallel what-ifs | Rewind exists (`/api/sessions/{sid}/rewind`); no fork found | **Never built** (fork) |
| K-31 | His clippings flow into research | `clippings-into-research` template (#154), real Library (#216) | Matches |
| K-32 | The morning digest | `morning-digest` template (#154, #216) | Matches (template) |
| K-33 | Disaster recovery | Backup and restore (#225-#229), sync and restore from a storage (#230-#234) | Matches (backend) |
| K-34 | Reproduce a months-old result | Results name their data and versions (#187, #261) | Partly |

---

## F. Screen walkthroughs for the unit system (UI-NOTES-UNITS)

Source: `tracker/risk-sizing/build/UI-NOTES-UNITS.md` on `plan/unit-system`. Written for the UI session. Each section is a screen and what it must show. For him. Backend status from the PRs above. No screen exists.

| § | Screen | Backend status |
|---|---|---|
| 0 | The words on the screens | Words are fixed in code (status words, refusals). Read in PR bodies. |
| 1 | First start and the getting-started panel | First start shipped. Getting-started panel has **no backend**. |
| 2 | Home | Partly. Inbox and heartbeat routes exist (`/api/inbox`, `/api/doctor`). |
| 3 | The copilot while it writes a unit | Shipped (#258, #262) |
| 4 | The unit in the Library, card and page | Shipped (#256, `unit` kind) |
| 5 | Publish, promotion and the deploy dialog | Paper shipped (#302); live never built |
| 6 | The journal view | Shipped (#267, #291) |
| 7 | The judge and his click | Shipped (#275, #340, #341) |
| 8 | The dictionary pages | Shipped (#266, #270, #337) |
| 9 | The QMB app: what ran and who ran it | Shipped (#261, #281, #289) |
| 10 | The trading node app | Shipped as a headless app with 20 operations (`qmx-agents/apps/trading-node/app.toml`) |
| 11 | Several nodes, one clock | Partly (#306, #247); world clock not in code |
| 12 | Stops, cards that need his click, and alarms | Shipped (#327, #303, #322) |
| 13 | The MIS on his PC | Shipped (#295, #350) |
| 14 | Workflows | Shipped (engine and templates) |
| 15 | Apps | Shipped (mini-app core, three first-party apps) |
| 16 | Settings | Partly. Settings routes exist (`PUT /api/settings/*`) |
| 17 | The maintenance list and data health | Shipped (`GET /api/maintenance`, #300) |
| 18 | What these screens do not need | (no journey) |
| 19 | Gaps the UI will meet | Read this section before designing. |

The October screen list is `tracker/qma-v2/UI-HANDOFF.md` (26 sections, last brought current 2026-10-28). Its section 26 lists what screens needed that the backend still lacked at that date; several were closed later by the wrap-up and unit programs, so recheck each.

---

## G. Journeys for work that is not shipped

| Source | For | What it walks through | Status |
|---|---|---|---|
| `tracker/risk-core/round-2/WALKTHROUGH.html` and `round-2/UI-LOOK.md` (local branch `plan/risk-core`) | Him | The round-two risk and sizing design | **Never built.** Its build is open PRs #353-#369. Proved by gh. |
| `tracker/risk-core/expansion/X4-scenarios.md` (local branch `plan/risk-core`) | Him | Risk stress scenarios | **Never built.** Design input only, and the first template was rejected by him on 7 Nov (`REVIEW-2026-11-07.md`). |
| `tracker/qma-v2/architecture/lab-and-pods/` (`UI-TO-BACKEND-MAP.md`, `LLD.md`, screenshots 36-58) on `plan/agent-system` | Him, copilot | Lab compare, pods test and paper, build a pod, train with model slots | **Partly.** The Lab backend workspace and PC training shipped (#194) and there is a `lab` toolset. **Pods were never built** (no pod code, only `pod` and `pod-block` Library kinds). HANDOFF-2026-10-24: "Pods wait on the unit work." |
| `tracker/qma-v2/research/methodology/23-ui-clickthrough.md` with `23-ui-shots/` | Him | The October UI demo, screen by screen | Design record of the old demo. Not a journey for shipped code. |

---

## H. Older journeys and scenarios (August to September design)

These were written for the old daemon, wire, pack and grant architecture. PR #169 deleted `qma-core`, `qma-wire` and `qma-daemon`, and the P16 PRs (#48-#70) retired the rest. Proved by git (merge commits in history) and read in code (those packages are gone). Keep them only as ideas.

| Source (all on `main` and `engine/base`) | Items | Status |
|---|---|---|
| `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/JOURNEYS.md` | J-UI-01 to J-UI-14 (switch apps mid-run, headless invoke, stale reconnect, duplicate submit, cancel racing success, pack install, protocol mismatch, client update) | **Superseded.** J-UI-11 (first-run provider failure) partly matches today's "host names what did not open" (#222) and provider test (#201). J-UI-07 and J-UI-08 ideas live on in idempotent clicks (#302, #348). |
| `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/JOURNEYS.md` | J-KIT-01 to J-KIT-07 (headless pack, in-app panel, widget starts a workflow, nested workflow, retry, weak model builds) | **Superseded.** Headless apps (all three first-party apps are `kind = "headless"`) and nested subworkflows (engine EP7 #100) carry the spirit. |
| `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/JOURNEYS.md` and its Codex challenge folders | J01, J03, J03b, J06/J13, J08/J24, J10, J12, J17, J26, J27; 85 frozen P1/P2 challenge IDs (`SCENARIO-CATALOG.jsonl`) | **Superseded.** Book/BMS composition paths belong to the old node shell (`qmn/`), which plan C-20 meant to cut and never did. |
| `docs/scenarios/SCN-0001` to `SCN-0035` (golden scenarios) | 35 scenarios: core freeze, source correction, sealed holdout, off-machine backup, uncertain venue submission, Book paper transition, agent cannot promote to live, news windows, synthetic stress, same-tick risk arbitration, qualifying-loss bench, agent replay backtest, quant over the wire, money-path barrier, experiment lanes, pack lifecycle, mailbox, pairing, cancel | **Mostly superseded.** Ideas that live on: SCN-0003 sealed holdout (now per study, #207, #335); SCN-0004 off-machine backup (#225-#234); SCN-0005 uncertain venue submission (node reconcile #292, #343); SCN-0007 agent cannot promote to live (promote is operator-only, #302); SCN-0009 synthetic data cannot prove edge (`world: synthetic` label, #187); SCN-0012 agent runs a replay backtest (#261). SCN-0013, 0014 and 0018-0035 describe deleted machinery (wire, money gate, packs, mailbox, pairing). |
| `_bmad-output/planning-artifacts/prds/prd-QMX-2026-08-21/discovery-decisions-scenarios.md` | PRD discovery scenarios | Superseded design input. |
| `qa/epics/epic_03` to `epic_23` `PLAN.md` (engine/base) and `_bmad-output/test-artifacts/test-design-*.md` | QA test designs for the QMF packages and QMB (data intake, calendars, venue, structure, risk, substrate, robustness, synthetic data, reports) | Test designs for the September QMF/QMB code, much of which still ships under `packages/qmf-*` and `qmb/`. They are tests, not user journeys. |

---

## I. Plans with no journey found

| Plan | Note |
|---|---|
| `rebuild/packets/P01-P23` (engine/base) | No journey found. Builder packets only. |
| `HARNESS-PLAN.md` (harness HP0-HP17) | No journey found. HP15's console is the nearest thing to a walkthrough (PR #88 body). |
| `ENGINE-PLAN.md` (EP0-EP14, TP1-TP4) | No journey found beyond builder checks. |
| `MOCK-DATA-PLAN.md` | Three check lines only (Appendix 2). |
| `tracker/qma-v2/PROMPT-*.md`, `DELETION-PLAN.md` | No journey found. |
| `D:/QMX-research/` | No journey found. It holds outside research (harnesses, memory, LangChain, cookbooks). |

---

## J. Shipped areas with no journey at all

These areas shipped (proved by git), but no journey, scenario or walkthrough describes using them. The UI session will need to invent the flow, and QA has nothing to test them against:

1. **Model providers and the router.** Provider rows, Test, the account pool, sub-agents on other providers, the GPT lane on his ChatGPT plan (#140-#149, #89, #201, #203). Only builder check lines exist.
2. **The usage page and plan limits.** Plan windows, readings, the overage stop (#83, #94, `GET /api/usage`).
3. **Chat controls.** Interrupt, rewind, model and effort switch with the cost warning, export a session, approvals (#85, `qma/harness/routes.py`).
4. **Delegate and helpers.** Start helpers, list, steer, stop (#151, `delegate` toolset).
5. **Memory management.** Recall, note, check, forget, rebuild (#153, `memory` toolset). K-03 is a scenario, but no click-through exists.
6. **Library maintenance.** Branch, merge, blame, marks, purge, "as of" reads (#136, #157, #195). Only design scenarios.
7. **Backups and sync from Settings.** Copies on This PC, a second drive, rclone storages, restore from Settings, keys to fill after a restore (#225-#234). Only builder check lines.
8. **The connect dialog for storage, compute (server, Modal, E2B) and deep logs** (#230, #232). Only builder check lines.
9. **Clocks and the doctor.** "Clock 3 ms off time.windows.com" and "Windows Time is stopped" (#247, `qmx_host/clock_probe.py`). One "You see" line only.
10. **The vault and keys.** Owner-only vault, pass key per host, refused host secrets in app manifests (#316, #326, #313). Only "Nothing new" lines.
11. **cTrader's MCP for agents, demo only.** Settings "cTrader for agents" (#324). One "You see" line only.
12. **The eval battery for the copilot** (#138, `ev-copilot-eval-battery` template).
13. **The Lab workspace and model training on the PC** (#194, `lab` toolset). The Lab journeys in section G assume pods, which do not exist.
14. **About 55 workflow templates** (`qmx-agents/packages/qmx-engine/src/qmx_engine/templates/`). Most have no journey. Only those named in J3, J11, J14, J15, J22, K-11, K-19, K-31 and K-32 do.

---

## Appendix 1. Unit build "You see" lines, one per plan section

| Section | What he sees (plan words, short) | PR | Status |
|---|---|---|---|
| A0 | Nothing changes for him. Builders and agents stop reading the old refusals as current rules. | #235 | Matches (merged) |
| B1 | Nothing on screen yet. A workflow can now tell an app's job what to do and read its answer. | #236 | Matches (merged) |
| A1 | Nothing yet. The size a unit chooses can now travel to the node without being dropped. | #237 | Matches (merged) |
| B3 | Nothing yet. | #238 | Matches (merged) |
| A2 | The written form of a unit exists, with a real example he can read. | #239 | Matches (merged) |
| B4 | Nothing yet. | #240 | Matches (merged); changed by R07 #333, R08 #335 |
| A3 | Nothing on screen. A stop can no longer mean ten times what was intended on another market. | #248 | Matches (merged) |
| B8 | Nothing yet. | #241 | Matches (merged) |
| A4 | Nothing on screen. The dummy's parts exist as tested pieces. | #249 | Matches (merged) |
| B5 | Nothing yet. | #252 | Matches (merged) |
| A5 | The first unit runs inside QML and tunes one of its own numbers from its own trades, with the receipt. | #251 | Matches (merged); changed by R05 #334 |
| C-05a | Nothing yet. An app that crashes comes back by itself when it opted in. | #242 | Matches (merged) |
| A6 | A unit gets every mistake named at once, and a unit that would trade nonsense is flagged before any backtest. | #253 | Matches (merged); changed by R04 #332, R13 #336 |
| B5b | Nothing yet. | #254 | Matches (merged) |
| A7 | The dummy unit waits in his Library as a draft on first start, with its checks passed and one yes to publish. A unit he publishes has always passed every check. | #256 | Matches (merged) |
| B6 | He asks the copilot "backtest the dummy unit on EURUSD for January" and gets a run number and the result in money and R. The result is in his Library with who ran it. | #261 | Matches (merged) |
| A8 | He can ask the copilot for a unit and watch it get written and checked, every problem fixed in a loop. | #258 | Matches (merged) |
| B9 | A backtest result now has the unit's journal. The copilot can say what the dummy did on a given day, why it skipped, and when its trend floor moved. The Journal tab itself is the UI session's. | #267 | Matches (merged) |
| A9 | What counts as a new unit is one table he can read in Settings. Nothing reaches paper or live without his click. | #250 | Matches (merged); changed by R06 #337 |
| A10 | A restart or an upgrade never silently changes what a unit does. | #255 | Matches (merged) |
| C-02 | Instrument pages for forex, gold, indices and perps in his Library, with contract unit, funding interval and data levels. | #257 | Matches (merged) |
| A11 | The dictionary has its new pages, and agents search them before writing code. | #266 | Matches (merged); changed by R06 #337 |
| A12 | His Library holds the ported dictionary as one collection, 239 pages, all passing, waiting for one publish click. The card that asks for it is the UI session's. | #270 | Matches (merged); changed by R06 #337 |
| A13a | The dictionary has every indicator a MetaTrader trader expects, each with working code. | #273 | Matches (merged) |
| A13b | The dictionary can name the state of a market in numbers a trader knows, each with its freshness and its fallback. | #276 | Matches (merged) |
| A13c | The dictionary speaks futures, indices, metals and perps, not only forex. | #279 | Matches (merged) |
| A13d | The dictionary holds the exits traders use, ready for the risk session to choose from. | #280 | Matches (merged) |
| A15 | The risk session gets a list, not a hunt. `build/RISK-SIZING-PLACEHOLDERS.md` names each item the query finds. | #272 | Matches (merged) |
| B7 | A twenty-year backtest on one-minute bars finishes on his PC. | #268 | Matches (merged); changed by R09 #338, R10 #339 |
| B10 | Results say "costs uncalibrated" until real fills exist, and a loss through a gap shows as it was, never capped at 1R. | #274 | Matches (merged); changed by R10 #339 |
| B11 | Each data card says its clock and where its data changed shape. | #278 | Matches (merged) |
| B12 | The copilot can say which QMB version is the default and which passed its check. The versions panel is the UI session's. | #281 | Matches (merged) |
| B13 | A verdict on the dummy unit in plain words, with the number of tries behind it. | #275 | Matches (merged); changed by R11 #340, R12 #341 |
| B14 | "Run on every market" works, and each night's live day can be replayed against the test. | #289 | Matches (merged); changed by R12 #341 |
| B15 | He can ask "why didn't the dummy unit trade this morning?" and get the reason with the spread at that minute. | #291 | Matches (merged); changed by R19 #344 |
| B17 | A workflow's agent can now save the file it was asked to write, and nothing else. | #243 | Matches (merged) |
| A14 | When the copilot saves a broken unit, the problems come back to it at once, the way a linter error does, and it fixes them before he sees the draft. | #262 | Matches (merged); changed by R13 #336 |
| C-03 | A crypto workflow no longer waits for Monday. | #263 | Matches (merged); changed by R06 #337, R09 #338 |
| C-05b | Nothing yet. | #244 | Matches (merged) |
| C-05c | Nothing yet. | #246 | Matches (merged) |
| C-08 | Nothing yet. | #271 | Matches (merged) |
| C-09 | The copilot can show the MIS readings for the markets he has data for, each with its freshness word. The MIS tab is the UI session's. | #295 | Matches (merged); changed by R18 #350 |
| C-24 | The copilot can tell him what the MIS read for a market last week, and the facts of any instrument. | #294 | Matches (merged) |
| C-01 | The doctor says "Clock 3 ms off time.windows.com", or "Windows Time is stopped, turn it on" with a button for his click. | #247 | Matches (merged) |
| C-04 | "Deep logs" opens with this PC's real events, or says "Telemetry off" when it is off. | #260 | Matches (merged) |
| C-05d | Nothing yet. | #264 | Matches (merged) |
| C-05e | Nothing yet. A backup or a move of a node never carries its trading grant. | #245 | Matches (merged) |
| C-06 | The copilot's "node state" answers "no trading node is set up yet" instead of an error. | #277 | Matches (merged) |
| C-07 | Perps positions, funding and open interest in his market tools. | #265 | Matches (merged) |
| C-10 | On a throwaway folder the node starts and its card reads "Ready, no units yet". Starting it from the setup list arrives in C-11. | #282 | Matches (merged) |
| C-11 | The setup list, with "Waiting for cTrader to approve your app" as a step that ticks when he pastes the id. | #288 | Matches (merged) |
| C-12a | On a throwaway folder against the test venue, the node card says "Trading, 1 unit". | #287 | Matches (merged) |
| C-12b | A position that is not the node's shows as "not ours, protected". | #292 | Matches (merged); changed by R20 #343, R23 #351 |
| C-12c | The unit's journal shows its first paper trade. | #293 | Matches (merged); changed by R15 #342 |
| C-23 | "Promote to paper" on a tested unit, then the node shows the unit warming up. The button is the UI session's, and the route is ready for it. | #302 | Matches (merged); changed by R17 #348 |
| C-13 | The node card reads "Healing" with a line on its Heals list, then "Trading" again. | #301 | Matches (merged); changed by R21 #345 |
| C-12d | On the node, "cTrader demo, signed in" after his one sign-in on cTrader's own page, and a passport whose five self-test lines read ok. | #311 | Matches (merged); changed by R23 #351 |
| C-26 | Nothing new. An app runs the code that was landed. | #310 | Matches (merged) |
| C-26b | Nothing new. The node runs the risk and venue code that was landed. | #318 | Matches (merged) |
| C-12e | The node's position always matches cTrader's, including after a partial fill or a dropped feed. | #319 | Matches (merged); changed by R20 #343 |
| C-37 | A unit's trailing stop moves on cTrader instead of the position closing. | #321 | Matches (merged) |
| C-35 | The node reads "Paused, risk stop on XAUUSD" or "Killed at EURUSD", never "Trading" while anything holds, and a kill on a market the node does not trade says so. | #327 | Matches (merged); changed by R21 #345 |
| C-34 | After his sign-in, his account, cTrader and each market he picked appear in the Library with their facts, and the promote card finds them. | #323 | Matches (merged); changed by R07 #333 |
| C-38 | Signing in to cTrader works on the installed node, alarms follow market hours, and after a restart your node comes back by itself. | #327 | Matches (merged) |
| C-14 | After he lands the stack and signs in once on cTrader's own demo page, his own practice node trades the dummy unit on his demo account. | #328 | Matches (merged); changed by R24 #352 (new job) |
| C-15 | Nothing new on screen. The passport gains "attribution proven on demo" and "refresh proven on demo" once the demo run passes. | none | **Never built** |
| C-16 | A Hyperliquid testnet binding on the practice node, once he approves a testnet agent wallet on Hyperliquid's own page. | #298 | Matches (merged) |
| C-25 | Nothing new. A chat asked to open a grant is refused with one plain sentence. | #312 | Matches (merged) |
| C-17 | "London-1, Ready" on his PC, with its clock, its round trip to cTrader and its passport, once he rents and names a server and enters its keys in its own window. | #325 | Matches (merged) |
| C-18 | A test notification on his phone during setup, once he names his ntfy topic. | #303 | Matches (merged); changed by R16 #346 |
| C-19 | "Update London-1", with "waiting for a safe moment" while trades are open. | none | **Never built** |
| C-20 | Nothing changes in what he uses, and about 47,000 fewer lines of old node code remain. | none | **Never built** |
| C-31 | Gold backtests read real gold prices, and a month landed wrong earlier shows "landed at the wrong price scale, download it again". | #315 | Matches (merged) |
| C-32 | Nothing new when the vault is right. A doctor row "your keys folder was readable by other users, fixed" when start repaired it. | #316 | Matches (merged) |
| C-33 | Nothing new. Enabling an app with a trigger never hangs his host. | #317 | Matches (merged) |
| C-27a | Both example apps install and run with no host pass, and MQL5 articles still reach the Library one item per article. | #314 | Matches (merged) |
| C-27 | An app that asks for the host's own pass fails to install, with one plain sentence. | #313 | Matches (merged) |
| C-28 | Nothing new. Pairing a server reads the same. | #326 | Matches (merged) |
| C-29 | A unit promoted onto EURUSD alone trades EURUSD alone. A deploy the node refused reads "Refused" with its reason on the deployment. | #327 | Matches (merged); changed by R22 #349 |
| C-30 | His phone buzzes for a risk stop during London hours, and stays quiet for a stale feed at the weekend. | #322 | Matches (merged) |
| C-36 | Settings, "cTrader for agents", with one place to paste a demo account's token. Chats and workflows can then read his demo account's prices, bars and positions and act on that demo account. A live token reads "refused, agents... | #324 | Matches (merged) |
| C-21 | "Bind a live account" ends with the soak card, and going live stays his click. | none | **Never built** |
| C-22 | On the node, which of a unit's markets the board favours now. The node page is the UI session's, and the copilot can read it from the node's status. | #309 | Matches (merged) |
| B2 | The four example apps and the three first-party apps (QMB, the MIS and the trading node) start without crashing. | #304 | Matches (merged) |
| B18a | Nothing new on screen yet. The build templates' parts exist. | #283 | Matches (merged) |
| B18b | Nothing new on screen yet. The slow-lane templates' parts exist. | #297 | Matches (merged) |
| B18c | Template cards show their loop counts as numbers he can change. | #284 | Matches (merged) |
| B19 | "Turn a strategy idea into a tested strategy" runs from a sentence to a verdict. | #296 | Matches (merged) |
| B20 | Each morning a short note per unit (traded, skipped, missed, and why), a market almanac, and a shortlist before each session, all marked as proposals. | #305 | Matches (merged); changed by R13 #336 |
| B16 | "Bring node records home" on the maintenance list, with the last round's counts, what each node still keeps pinned, and its off switch. | #300 | Matches (merged) |
| B21 | A watcher that tells him when a node is unwell and why, and never touches it. | #306 | Matches (merged) |

87 of 91 sections built. Status "Matches (merged)" is proved by git; the behaviour was read in the PR body, not click-tested.


## Appendix 2. October programs' "You see" lines

Most are builder check lines (a command and the output it should print). Who it is for: him, through a builder's check.


### Hardening (build program): `tracker/qma-v2/HARDENING-PLAN.md` (58 sections)

| Section | What it checks, short | PR | Status |
|---|---|---|---|
| HYG0 | `python -m qmx_engine run <folder> --mode live` exits 2 with a usage error, and the qma-core suite passes. | #113 | Matches (merged) |
| PRB-H | `FINDINGS.md` has a PASS or FAIL row for each of the six probes, with the fallback each one triggers and the log it came from. | #112 | Matches (merged) |
| PRB-R | `FINDINGS.md` has a PASS or FAIL row for P0, P1 and P1k, with the env values P0 found and the method and path list P1 recorded. | #114 | Matches (merged) |
| PRB-L | `FINDINGS.md` has a PASS or FAIL row with a number for each of the five probes. | #117 | Matches (merged) |
| CAPE | `python -m qmx_engine check` on every shipped template prints no `runaway`, and a looping-agent fixture ends `stalled(loop)` with its summary as output. | #115 | Matches (merged) |
| CAPH | With `[budgets]` empty, the usage page shows readings only, and a Background chat's launch options carry no budget and no turn cap. | #116 | Matches (merged) |
| CAPX | A run with 40 rule nodes and 12 agent chunks shows no rule waiting and his Interactive chat starting while the chunks run. | #123 | Matches (merged) |
| SEC1A | A failing fixture whose provider error echoes `key_sk-or-v1-…` shows `[redacted…]` in `explain` and in the inbox item. | #118 | Matches (merged) |
| SEC2A | After a three-chunk run, `work/` holds only the declared outputs, and no attempt folder is left. | #120 | Matches (merged) |
| BUG1 | A run held on `wait seconds: 90` reads `waiting` in `runs list` and resumes on its own after 90 s. | #124 | Matches (merged) |
| BUG2 | `python -m qmx_engine check` refuses a definition with a nested fan-out and names the node. | #126 | Matches (merged) |
| BUG3 | `runs list` shows an in-flight run as `running` and a held one as `waiting`, and answering a gate item moves the run on. | #128 | Matches (merged) |
| HOST | One `qmx_host` process answers `GET /api/health`, lists chats and lists workflow runs on the same port. | #119 | Matches (merged) |
| TURN-H | A Background chat started with `tools: []`, a hook sink and `compact_at: 0.4` keeps all three after the host restarts, and its turn ends with no polling. | #121 | Matches (merged) |
| TURN-E | `git diff --stat` shows `harness_adapter.py` near 150 lines, and a two-chunk agent run on haiku ends `passed`. | #129 | Matches (merged) |
| GUARD | A copilot WebFetch of a broker's public documentation page succeeds, and a copilot `cat` of the plan login file is refused with the guard's reason. | #125 | Matches (merged) |
| AGW | The `bc-build-a-component` template on haiku ends `passed` with its component file committed under `work/`. | none | **Skipped; B17 #243 later** |
| CAT | A hub chat on haiku lists tools named `<toolset>_<op>`, and a Kimi-shaped intake node fixture lists only its declared toolsets. | #127 | Matches (merged) |
| SURF | A Kimi-shaped intake node declaring `toolsets: [library, research, data, memory]` lists only those tools plus its built-ins, and its span carries the digest. | #132 | Matches (merged) |
| RUN1a | Enabling a fixture app with a 60 s interval creates one trigger row, and its runs appear in the run list beside workflow runs. | #130 | Matches (merged) |
| TRG2a | With "pause everything" set, `explain_trigger` on a due cron trigger says it is paused, and clearing it fires once. | #133 | Matches (merged) |
| OPS1 | The copilot's `ops` toolset answers "what is running here and why is it slow" from heartbeats and the capacity queue. | #134 | Matches (merged) |
| LIB1 | After a passed test run of a template, its run summary and artifact are Library objects with `run-of` and `produced-by` edges, and a run-made workflow sits on `refs/drafts/<item>`. | #131 | Matches (merged) |
| LIBM | `verify.py` on the copy prints step 0's counts beside the new store's counts, equal per kind. | #135 | Matches (merged) |
| SES | A Lab-home chat shows up in a Library search from the hub with its Lab home and last turn. | #141 | Matches (merged) |
| LIB2 | A result built on quarantined dataset r12 reads "built on quarantined input" with its path. | #136 | Matches (merged) |
| LIB3 | A search for a pod's name returns the pod first, with the edge that admitted each other result. | #139 | Matches (merged) |
| REF1 | A Lab session with pod v7 attached and reopened in the hub lists pod v7, and after v8 is saved it reads "newer version exists". | #143 | Matches (merged) |
| PACK | A hub chat on haiku with a fixture pack added mid-session answers with the pack's tool at once and lists the pack's skill on the next message. | #144 | Matches (merged) |
| APP2a | The macro fixture app lands `bias`, and the copilot reads it as a Library artifact with its freshness. | #146 | Matches (merged) |
| MEM | A new hub chat asked "what did we find about pod P" recalls the Lab session's note with its source. | #153 | Matches (merged) |
| EVAL | The Settings change card for a default-model switch returns the battery's pass^3 per task for both models. | #138 | Matches (merged) |
| RTR0 | `python -c "import qmx_router.relay, qma.harness.relay"` works, and a key-profile chat on the fake model runs through the relay as before. | #137 | Matches (merged) |
| RTR1 | The provider rows list every bundled provider, and Test on the OpenRouter Kimi row answers with one token. | #140 | Matches (merged) |
| RTR2 | One chat with a Kimi main and a DeepSeek sub-agent on the OpenRouter rows shows two providers in the journal for one session. | #142 | Matches (merged) |
| RTR3 | A sub-agent on an OpenCode Go row (or the OpenRouter row standing in) finishes a three-tool task under a Kimi main. | #145 | Matches (merged) |
| RTR4 | With two OpenRouter keys under one provider row (or two fake keys), a forced 429 on the first moves the next request to the second, and the readings show both. | #147 | Matches (merged) |
| RTR5 | A 50-abstract list into an agent node gives 2 chunks on a 1M model and 7 on a 200k model. | #148 | Matches (merged) |
| RTR6 | A Kimi-main chat on the OpenRouter row lists `deepseek-reviewer` and `qwen-reviewer`, and asking for both reviews runs both through the router. | #149 | Matches (merged) |
| RTR7 | With the lane on for his account, his Opus copilot on the plan asks a Kimi reviewer and a Qwen reviewer, and the journal shows the plan requests and both reviewers in one session. | none | **Skipped by its probe** |
| DLG | His copilot on haiku starts three helpers on the OpenRouter Kimi, DeepSeek and Qwen rows, keeps talking to him, and receives three results between turns. | #151 | Matches (merged) |
| TPL1 | The template list shows 31 plain titles, and each reads `tested`. | #150 | Matches (merged) |
| TPL2 | He types "every weekday at 7, pull the ECB calendar, summarise it, and save it to the Library", and a tested draft appears with a publish card. | #152 | Matches (merged) |
| TPL3 | The five templates appear on the shelf with plain titles and read `tested`. | #154 | Matches (merged) |
| QMBH | `uv run qmb host start`, `status` and `stop` exit 0 and the running process is `qmx_host`. | #122 | Matches (merged) |
| DEL2 | The scan prints nothing, and `python -m qmx_host serve` starts. | #165 | Matches (merged) |
| DEL3 | The scan prints nothing, and `just ci` passes. | #169 | Matches (merged) |
| PRB-S | `FINDINGS.md` has both rows with numbers and the derived `overhead_mb`. | #156 | Matches (merged) |
| LIB4 | On a throwaway PC home paired with Contabo, a save lands on the Hub and mirrors back, and the doctor shows `primary: server`. | #157 | Matches (merged) |
| RTRP | A key rotated in Settings on the PC is used by the next relayed request on Contabo within one sync. | #158 | Matches (merged) |
| REM | A one-node CPU job on `contabo` lands as a `workflow-run` the PC's run list shows. | #159 | Matches (merged) |
| TRG2b | With the PC's host stopped, the macro fixture app on Contabo lands `bias`, and the signal fixture app on Contabo runs on it. | #160 | Matches (merged) |
| APP2b | The macro fixture app moves from the PC to Contabo, and its next scheduled run happens there with its state intact. | #161 | Matches (merged) |
| OPS2 | A 401 on a Contabo-homed run shows in the PC's inbox, and pressing `retry` on the PC resumes it on Contabo. | #162 | Matches (merged) |
| ADOPT | A PC-homed fan-out cut mid-run resumes on Contabo after `adopt`, and the PC, restarted, shows its copy as moved. | #163 | Matches (merged) |
| RUN1b | `POST` to the old remote-run route returns 404, and `SL/smoke_remote.py` runs its job as an engine run on Contabo. | #164 | Matches (merged) |
| DEL1 | The scan prints only the two example apps' git pins, and a hub chat lists the ported agents and skills. | #166 | Matches (merged) |
| DEL4 | In a fresh venv after `uv sync --frozen --all-packages --all-groups`, `uv pip list` shows none of the nine. | #167 | Matches (merged) |

### Data round: `tracker/qma-v2/DATA-PLAN.md` (30 sections)

| Section | What it checks, short | PR | Status |
|---|---|---|---|
| DEL4R | `git grep` of the nine names in every `pyproject.toml` prints nothing, and `uv lock --check` passes at the root and in `qmx-agents/`. | none | **No PR found** |
| DEL2R | `python -m qma.console` with no host on its port starts `qmx_host`, and `python -m qma.serve` fails with `No module named qma.serve`. | #172 | Matches (merged) |
| RUN1C | On a throwaway home, the run list shows one `backup-weekly` run after a forced cron fire, and `GET /api/jobs` answers 404. | #175 | Matches (merged) |
| MWH | An external MCP server whose tool is named `place_order` is vetted like any other tool, and a workflow definition with a node named `submit_order` lints with no money-word problem. | #174 | Matches (merged) |
| DR0 | `ssh` to the server, `ls /srv/qmx/data/raw-backup/` shows both folders and `MANIFEST.sha256`, owned by `qmx`. | #173 | Matches (merged) |
| PRB-DP | `SP/data/FINDINGS.md` has a P-MDREAD-DUCK row and a P-DUKA row, each with PASS or FAIL and its numbers. | #176 | Matches (merged) |
| PRB-DS | `SP/data/FINDINGS-server.md` has P-HS, P-DOCLING and P-OO rows with memory and time numbers. | #177 | Matches (merged) |
| PRB-CT | `SP/data/FINDINGS-ctrader.md` has the three rows. The demo account shows no new position. | none | **Waits on his demo sign-in** |
| DR1A | On a scratch store with a cut last line, `status()` reads `torn`, `quarantine/` holds the line, and every other record reads back. | #171 | Matches (merged) |
| DR1B | After the switch-over on a throwaway copy of his home, a copilot `library_search` answers from `<home>/library/` and `<home>/migration/retired/library.db` exists. | #178 | Matches (merged) |
| DR2A | The doctor on a throwaway home shows free disk, the floor and free RAM from live readings, and no budget constant. | #179 | Matches (merged) |
| DR2B | On scratch roots with `primary = server`, a PC search finds a phrase that exists only in a server-extracted text, and opening the item fetches its original. | #180 | Matches (merged) |
| DR2C | With the PC's host stopped, a restarted scratch server host serves a model call through its relay with a key it opened itself. | #181 | Matches (merged) |
| DR2D | On scratch roots, the inbox shows "Move the Library to the server" with one button, and nothing flips until it is pressed. | #182 | Matches (merged) |
| DR2E | The doctor on the scratch server shows the memory engine as Hindsight with its Postgres reachable. | none | **Not built** |
| DR3A | A scratch import of one month of EURUSD ticks shows one `dataset` card with the month, its row count, its fingerprint and a coverage strip. | #184 | Matches (merged) |
| DR3B | On a scratch home with one imported month, the copilot's `data.bars` returns that month's bars with the card id, and a read of a sealed month is refused with "this month is sealed for the final look". | #185 | Matches (merged); Changed by WU11 #207 and R08 #335 |
| DR3C | On a scratch server root, one year of EURUSD imports into one ticks card whose months match the raw files of that year. | #186 | Matches (merged) |
| DR4 | On a scratch home with one imported month, the copilot runs a backtest of an example bot and the Library shows one `backtest-result` card with its equity curve and its data used. | #187 | Matches (merged) |
| DR5A | On a scratch home, Settings list a Dukascopy and a Binance data connection with `ok`, and a stub broker key that can trade a live account shows `needs_you` with nothing stored. | #189 | Matches (merged) |
| DR5B | On demo, after the sign-in page, the scratch server's Connections row reads `ok`, the PC's keyring and the vault document hold no token, and a PC read of the demo account's balance goes through... | none | **Not built; LF7 #211 instead** |
| DR6 | On a scratch server home, a Dukascopy download of one month lands one card per price side, and the calendar feed lands one month of events with a revision kept as a second row. | #191 | Matches (merged) |
| DR7 | On scratch roots, a 400-page PDF uploaded on the PC is searchable on the PC by a phrase on page 312, and the hit opens at that page. | #193 | Matches (merged) |
| DR8 | Two chats on haiku edit different lines of one note and both edits land. When they edit the same line, the inbox shows one conflict with both sides and the base. | #195 | Matches (merged) |
| DR9 | A workflow whose input is `@run:<Tuesday's run id>` starts and its first node reads that run's outputs from the Library. | #188 | Matches (merged) |
| DR10 | On the scratch server, OpenObserve shows one run's trace across the PC and the server under `trace_id = run_id`. | #192 | Matches (merged) |
| DR11 | The grep prints no capacity limit. | #196 | Matches (merged) |
| DR12 | On a scratch home, `view(<backtest-result id>, card)` returns the bot version, dataset and months, headline measure, trades and the hypothesis outcome, and `view(..., page)` returns its seven tabs. | #190 | Matches (merged) |
| DR13 | On a scratch home, "New experiment" creates a project collection with its template installed, and a training run on the PC lands a `model` item with its data fingerprints, code version and seed. | #194 | Matches (merged) |
| DR14 | A two-node workflow with `runs_on: [pc, contabo]` whose data sits on the server runs its data step on the server. | #197 | Matches (merged) |

### Wrap-up: `tracker/qma-v2/WRAPUP-PLAN.md` (12 sections)

| Section | What it checks, short | PR | Status |
|---|---|---|---|
| WU1 | On a throwaway home, a new chat lists an enabled example app's tools, and a pack published a minute ago shows its skills in the next chat. | #198 | Matches (merged) |
| WU5 | On a throwaway home, `templates install --template backup-weekly` then enabling its trigger answers ok instead of `409 unknown_object`. | #199 | Matches (merged) |
| WU2 | A chat asked to "test my OpenRouter provider" answers with the row's result and its latency. | #201 | Matches (merged) |
| WU6 | `just ci` ends with exit 0 on a clean check copy. | #200 | Matches (merged) |
| WU3 | With an OpenRouter row and no Kimi key, a strong-role chat runs on OpenRouter on the first try. | #203 | Matches (merged) |
| WU7 | Nothing on screen. The data health read reports one copy for a server-made file. | #202 | Matches (merged) |
| WU4 | On a throwaway home with one imported month, the copilot runs a backtest of an example bot and the Library holds one `backtest-result` card. | none | **Not merged: PR #204 is open** |
| WU8 | On a scratch home with a fake cTrader token endpoint, the sign-in link opens, the receiver forwards the code, and the Connections row reads `ok`. | #205 | Matches (merged) |
| WU9 | `qmx node setup --dry-run` on the PC prints the commands in the new order with one root. | #206 | Matches (merged) |
| WU9b | `sudo qmx-recover status` on the server prints one plain line per part, each ending PASS or FAIL with a reason. | #206 | Matches (merged); Inside #206 |
| WU10 | A PC read of the demo account's balance goes through the server, and the Connections row reads `ok`. | none | **Not built (#211 body)** |
| WU11 | From a chat, `read_bars` for a 1996 window answers rows on a throwaway home with an empty `[data]`. | #207 | Matches (merged) |

### Local-first: `tracker/qma-v2/LOCAL-FIRST-PLAN.md` (8 sections)

| Section | What it checks, short | PR | Status |
|---|---|---|---|
| LF5 | On a fresh throwaway folder the host starts and runs one chat, and no connection to `155.133.27.86` or any address but the model provider's is attempted. | #208 | Matches (merged) |
| WU11 | From a chat, `read_bars` for a 1996 window answers rows on a throwaway folder with an empty `[data]`. | #207 | Matches (merged) |
| LF1 | `python -m qmx_engine templates list` with no folder anywhere answers in one line that no QMX folder was found and to start QMX once or pass `--home`, and creates nothing. | #209 | Matches (merged) |
| LF6 | A run card's record says "ran on pc, by default". | #212 | Matches (merged) |
| LF2 | A throwaway folder after one chat, one recall, one script workflow and one mini app shows only the five parts and the label. | #210 | Matches (merged) |
| LF7 | On a throwaway folder with a fake token endpoint, the sign-in completes with no server and the connection reads `ok`. | #211 | Matches (merged) |
| LF3 | Opening a folder written by a pretend newer release says, in plain words, which version is needed. | #213 | Matches (merged) |
| LF4 | On a synthetic old-layout folder, the first start's report lists items per kind, what was filtered and what moved. | #214 | Matches (merged) |

### Loose strings: `tracker/qma-v2/LOOSE-STRINGS-PLAN.md` (7 sections)

| Section | What it checks, short | PR | Status |
|---|---|---|---|
| P1 | On a scratch profile, `python -m qmx_host first-start --serve --port <p>` with a synthetic old folder answers `POST /api/first-start/bring-in` with 202 and a job id, `GET... | #219 | Matches (merged) |
| P2a | On a throwaway folder, an interval trigger's "Clippings into research" run killed before its first summary is resumed by the ticker at the next host start, and both clippings are on `main` with... | #218 | Matches (merged) |
| P2b | `POST /api/workflows/clippings-into-research/run` with the body `{"folder": "<scratch folder>"}` starts a run whose `run_input` holds that folder, and its clippings land. `PUT... | #220 | Matches (merged) |
| P3 | On a throwaway folder with fakes, a cTrader connection with no protocol fields signs in and reads its account, an expired pair is refreshed once, and a read with no sign-in says "Sign in to... | #221 | Matches (merged) |
| P5 | With a head host on a throwaway folder, `python -m qmx_engine templates install --home <folder>` prints a line per template as before, and `GET /api/templates/install/<id>` showed `done` rising... | #223 | Matches (merged) |
| P6 | A head host on a throwaway folder with an unusable `[data]` answers `GET /api/data/instruments` with 503, the refusal's category and a plain line. | #222 | Matches (merged) |
| P4 | Saving a new kraken demo row in Settings answers 400 with the named line, and nothing is saved. | #224 | Matches (merged) |

### Backup and restore: `tracker/qma-v2/BACKUP-RESTORE-PLAN.md` (7 sections)

| Section | What it checks, short | PR | Status |
|---|---|---|---|
| B1 | On a throwaway folder with `filled_folder(secrets=True)`, `run_round` with one folder target writes `backups/quick/snapshots/<stamp>/manifest.jsonl` and... | #225 | Matches (merged) |
| B2 | On a throwaway folder with a second-drive copy and 3 runs and 12 Library ref moves made after it, `stage` answers those counts, and `finish` then leaves `data/` equal to the copy file for file and... | #226 | Matches (merged) |
| B3 | A head host on a throwaway folder with one folder target answers `GET /api/backups` with the quick undo and the target, each with its last copy's time and `"result": "copied"`, within two minutes... | #227 | Matches (merged) |
| B4 | On a scratch profile with no QMX folder, the card lists the copies of a lane target, `POST /api/first-start/restore/check` answers what the copy replaces, `POST /api/first-start/restore` with... | #228 | Matches (merged) |
| B5 | A head host answers `POST /api/backups/restore` with 202 and a job that ends `finished` with "Restart QMX to finish the restore; the work it replaces is set aside in... | #229 | Matches (merged) |
| B6 | With `RCLONE_CONFIG` on an empty file, a round to the target `{kind = "rclone", remote = ":local", path = "<lane folder>/remote", config = "<lane empty file>"}` writes `<lane... | #233 | Matches (merged); Folded into SY3 #233 |
| B7 | On a second scratch profile with a fake key store, after the card restores a copy, `POST /api/first-start/keys` with the passphrase answers the names and files it wrote, and the fake store holds... | none | **Dropped (SYNC-PLAN)** |

### Sync and connect: `tracker/qma-v2/SYNC-PLAN.md` (5 sections)

| Section | What it checks, short | PR | Status |
|---|---|---|---|
| SY1 | On a throwaway folder with `filled_folder(secrets=True, writers=True)`, a round to one folder storage logs `copied` for This PC and the storage, the storage's manifest lists no path of... | #231 | Matches (merged) |
| SY2 | A head host on a throwaway folder answers `POST /api/connect/jobs` for kind `folder` with a path in the lane folder with 202, the job ends `finished` with one line per step, `[engine]` gains one... | #230 | Matches (merged) |
| SY3 | A round of lane 2's folder to an rclone `local` storage leaves `QMX-backup/<home_id>/packs/`, `index/` and `snapshots/<stamp>/manifest.jsonl` whose header says `qmx-backup/2`, and a restore of... | #233 | Matches (merged) |
| SY4 | On a head host with the fake shell and terminal, a server connect job stops at each of his five cards in order, runs the setup steps and the PC half, writes one `[engine]` row with `provider =... | #232 | Matches (merged) |
| SY5 | On a second scratch profile, the card lists `restore-storage`, connects an rclone `local` storage, lists its copies with machine, time and counts, restores one with moving counts, hands over, and... | #234 | Matches (merged) |

### Mock data: `tracker/qma-v2/MOCK-DATA-PLAN.md` (3 sections)

| Section | What it checks, short | PR | Status |
|---|---|---|---|
| MD1 | On a throwaway folder, "Clippings into research" stores a clipping that the Library search route finds, and the morning digest lists it after the run lands. | #216 | Matches (merged) |
| MD2 | The broker `account_state` tool's text for a demo account carries `environment: demo` beside the balance. Whether a model repeats "demo" in its own words is its choice; a chat that drops it is... | #215 | Matches (merged) |
| MD3 | On a synthetic old folder, the bring-in report says how many items were made by test runs and that they are archived, not deleted. | #217 | Matches (merged) |
