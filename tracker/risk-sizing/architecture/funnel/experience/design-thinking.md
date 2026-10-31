# Experience pass: design thinking on QMX in daily use

Written 2026-10-31 by agent F2 (the experience pass of the funnel). It gives the architecture the journeys it must make easy. It designs no part. Where it proposes, the proposal is marked and logged in "Lead's calls" near the end.

## Files in this folder

| File | What it holds |
| --- | --- |
| `design-thinking.md` (this file, also the index) | The journeys, step by step: what the person sees, what must be true underneath (needs named by part), the failure stories, and the out-of-the-box defaults. Then the needs per part, the defaults table, the lead's calls, and the points for the risk session. |
| `problem-solving.md` | The five weak spots the lead must solve, each worked through `bmad-cis-problem-solving` to a proposed solution the architecture can adopt. |
| `ui-needs.md` | What the UI needs from this work, screen by screen, as design intent. Includes the proposed screens of the QMB and trading-node mini apps. |

## How this file was made

- **Skill.** `bmad-cis-design-thinking`, run headless. The workflow block was resolved with the BMad resolver: no prepend or append steps, no persistent facts, empty `on_complete` (CHECKED, `uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-cis-design-thinking --key workflow`). YOLO was taken at the first checkpoint, so all seven steps ran straight through. The output path was moved from `_bmad-output` (which sits on `main`) to this folder. The template's emoji headers were dropped.
- **His voice.** Quotes only, each with its transcript line: `T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md`, `T3` = `operator/transcript-2026-10-30-to-31.md`. Line numbers follow `grep -n`. A script checked every quote against its line before hand-back (last section).
- **Labels.** CHECKED = read at the cited path and line, run, or CHECKED in the cited grounding file (`G1` to `G4b`, `research/NN`). INFERRED = my reasoning. A need written in a journey table is a proposal unless it carries a status word: BUILT (merged on `engine/base` `c93407ca`), STACKED (open PR), MISSING.
- **Rulings used.** `STATE.md` midday rulings 1 to 45, the morning rulings, his six answers, and the ledger rows by id (for example `CC-15`). The frame (`00-frame-after-grounding.md`) sets the shape: QML and the dictionary first; QMB and the trading node as the first two mini apps; agents only in the slow lane; risk and sizing as placeholders.
- **What I did not do.** I did not run the UI. I read its design from the recorded screenshots in `tracker/qma-v2/research/methodology/23-ui-shots/` and `tracker/qma-v2/architecture/lab-and-pods/ui-shots/` (CHECKED: Home, Apps, a mini-app page, a bot page, Portfolio Live and MIS tabs). No UI code was read or written.

## The parts, named once

Every need below names one of these parts. The names are the frame's; nothing here creates a part.

| Part | In one line | Today |
| --- | --- | --- |
| QML | The library units are written with: the unit template, the dictionary, the compiler into the runtime seam | Runtime seam and checks BUILT; unit template and dictionary-in-repo MISSING (G1 §0) |
| The unit checker | QML's conformance gate extended to the unit, reached as a tool row, a workflow script step and, optionally, a hook | Gate BUILT, unreachable by agents (G1 §1.7, G4b Q2) |
| QMB | The backtester, first mini app | Measures BUILT; a runner that trades a named unit MISSING; door STACKED in PR 204 (G4a §2.4) |
| The trading node | The only part that sends orders, second mini app | 98,063 lines, never run, no live profile, no setup path (G4a §2.2) |
| The MIS | Reads markets and publishes readings; units pick; none needs it to trade | Execution-health labelers inside the node only (G1 §6) |
| Journals | The unit journal (its DevOps layer) and the market journal | `trade` kind BUILT; unit journal MISSING (G1 §7) |
| The Library | Store of record: the unit kind, runs, journals' cards, readings' cards | BUILT; unit kind has a page and no fields (G4b §1.5) |
| Workflows | Templates and slow-lane agents | Engine BUILT; 22 runnable templates, 23 drafts (G4b §1.3) |
| The copilot | And QMA agents, through one catalog | BUILT (G4b Q3) |
| The mini-app core | Manifest, supervisor, operations, `provides` and `feeds` | BUILT; no real app installed (G4b Q5) |
| The host and the connect dialog | Places, first start, servers | BUILT; no trading-node kind (G3 §1.4) |
| Monitoring | Heartbeats, inbox, OpenObserve | BUILT, never run on real telemetry (G4a §1.2) |
| Broker links | cTrader, CCXT, Hyperliquid, futures feeds | cTrader reads BUILT on the PC; orders only in the node; CCXT spot reads only (G3 §2) |
| Clocks | Time on every machine and screen | UTC instants BUILT; zone and offset per machine MISSING (G2 §9) |
| The UI | Design only, by his ruling 45 | Rebuild branch on this PC only (G2 fact 2) |

---

## Step 0. Harvest: what earlier passes already found

Read first, per his ruling 18 and standing order 2. Each row says where it lives, and what the newest rulings do to it.

| Found earlier | Where | Against today's rulings |
| --- | --- | --- |
| The unit's life from source to retirement, 18 stages | `research/funnel3/cis/design-thinking.md` "J1" | Keep the stages. Drop "router switches", "System 1 breadth" and "small siblings live" (router never switches, `M-05`; only he promotes, `CC-11`; the names are not to be raised, `U-13`). Paper is per unit, so the node's Book-level paper must change (G3 §5). |
| The steps a unit takes before it places a trade | funnel3 "J2" | Keep. Step 7 (others on this bet) goes to the risk session (`R-06`). Step 6 (context fits) is now a read of declared readings with a declared fallback (problem-solving WS4). |
| His week: morning brief, proposals, stops, weekend review | funnel3 "J3"; `research/30-desk-analysis.md` §8.2; `research/43-convergence.md` §1 "Your day with QMX" | Keep, and widen to nodes in several regions (`T-01`) and to the slow-lane agents of ruling 44. |
| The market-analysis agent's session and the unit-analysis agent's review | funnel3 "J4", "J5" | Keep. Templates read the MIS's logs, not the model (`M-09`). Proof that cannot be cheated (`A-03`). |
| The copilot attaching a market by hand, meaning undefined | funnel3 "J6" | Settled here as a lead's call (J15 below). |
| A cheap agent turns a loose YouTube source into a unit | `research/funnel4-qml/cis/design-thinking.md` "J1" | Keep. Its pains (invented numbers, missing exits, wrong session clock) become checker rules and labels (J2 below). |
| He reads and approves a unit; "what will move by itself?" | funnel4 "J2" | Keep; it is weak spot 1 (problem-solving WS1). |
| Plain Python or an ML ensembler beside QML | funnel4 "J3" | Keep (`CC-08`, `MA-03`). |
| The analyst reads a unit's record; changes logged with their kind | funnel4 "J4" | Keep; the journal's calibration lane (J4 below). |
| Source to live unit, 15 stages, with what exists | `research/07b-funnel-cis.md` §2.3 | Keep the inventory. "Router places the unit" and "seat warm-up" are gone. |
| The proof receipt, tries meter, cell map, world clock, instrument passport, morning unit brief, settled-decisions guard | 07b §2.5 | Keep the receipt, the tries meter, the world clock and the instrument passport as screen intent (`ui-needs.md`). Drop the router placement explainer. |
| The story of a unit, "every unit comes with a receipt" | 07b §4 | Keep the arc. Its "goes back to paper on its own" clashes with standing order 7 (only a risk rule moves a unit by itself); see J14. |
| The six places every retail platform stalls | `research/30` §8 | Keep as the yardstick for "a beefier advantage compared to a person just using a simple bot" (T2:858). |
| Desk rhythm by style, and a cadence per analysis | `research/30` §2.4, §7 | Keep as defaults for workflow triggers; per-session clocks and "every N trades" triggers are missing (`research/30` §7, CHECKED there). |
| One trade row, the unit's front page, back-to-paper triggers, the calibrator v1, two files, the library's promises | `explainers/src/pages2.mjs` (sections "One trade row", "The front page shows", "Back to paper when", "What the calibrator tunes (v1)", "Two files", "Promises the library keeps") | Keep the trade row and the promises. The calibrator's sizing items go to the risk session; the mechanism stays (WS1, WS2). |
| What a unit needs (hard and soft), guards stand alone, one clock per job, PC and node take turns, what the unit journal keeps, one id from source to trade, preview and detailed view | `explainers/round2/src/pages-b.mjs` (sections of those names) | Keep all. "Router offers" in the needs table drops out. |
| The weak spots and the seven pass marks | `research/53-fable-next-steps.md` §3.2, §3.3 | Keep the weak spots; the throwaway prototype is replaced by the dummy-unit packet (`CC-17`). |

What the harvest did not cover, and this pass adds: the newcomer's first hour; starting a node and seeing it run; deploying with little stress; several nodes in several time zones; the 3 a.m. failures as he lives them; QMB and the node as mini apps with their own screens; updating QMX while a node trades; the PC away for days; a paid feed switched on later; the dictionary meeting a new word.

---

## Step 1. The design challenge

**Challenge.** QMX is meant to be used every day, by him and by someone who was not in the planning: "Remember, we are going to use QMX on a daily." (T3:1093), "So assume that you have an end user in mind, okay?" (T3:1093), "factor in the logic of a person who has no clue how it's built or it's meant to be building" (T3:1102). The question he set for this lens is "how am I going to be using units, okay, to literally trade and make money" (T2:858), and why that gives "a beefier advantage compared to a person just using a simple bot" (T2:858).

**Challenge statement.** How might QMX let one person turn an idea into a unit, prove it, start a trading node, deploy the unit with little stress, and watch it trade on its own in any region, so that every number has a reason he can read, every failure says what happened and what it needs, and someone new gets a first unit backtested in the first hour without help?

**Users.** Him, every day. A newcomer. The copilot. A cheap QMA agent in an unattended workflow. The engineer or builder agent who maintains the parts next (per the experience-first principle, the maintainer is a user too).

**Constraints (rulings).** Only he promotes; the only automatic move is a risk rule stopping a unit (`CC-11`). Units stand alone (`CC-12`). Local first (`CC-06`). Nothing capped (`CC-07`). Plain Python always possible (`CC-08`). Determinism over agent judgement (`CC-10`). Placeholders for sizing and exits (`U-04`). Only the node sends orders (STATE mid r27). Windows first-class; the node on Linux servers (`CC-14`, `N-03`). UI is notes only (ruling 45).

**What success looks like, in his words.** "Remember, all this is meant to work right out of the box." (T3:1102). "is it going to start as server, then show me that the server has started?" (T3:1102). "I want to be, should I won't say hands-free, but like less stress." (T3:1102). "When I say it works, I mean, does a unit actually make sense?" (T3:1145).

---

## Step 2. Empathize

Methods chosen from `design-methods.csv`: empathy mapping (his transcripts read as interviews), journey mapping, shadowing (here, reading what each persona can reach in code today, from G1 to G4b), and diary study (his rulings over twelve days read as a diary).

### 2.1 Persona: him, every day

| Says (quotes only) | Thinks (INFERRED) | Does (CHECKED in the transcripts) | Feels (INFERRED) |
| --- | --- | --- | --- |
| "nothing actually ever enters live without me" (T1:1574) | The system works while I sleep, but money moves only by my click or a risk rule | Dictates long messages, often from his phone: "I'm texting you from my phone" (T3:904) | Tired of repeating himself: "I don't really like repeating myself further." (T3:1264) |
| "How are we going to be able to receive results?" (T3:903) | Where is the node, what did it do, can I trust the numbers | Watches on a second monitor, interrupts with nudges (T3:1338) | Wants calm, not dashboards to babysit |
| "The journal is very important, please." (T3:903) | The journal is how I know a unit is not luck | Asks when a word is new: "What is R, by the way?" (T3:903) | Distrust of agent self-reports |
| "the trading node is perhaps a firm" (T3:903) | Each node has its own office hours | Thinks in places: London, Singapore | Uneasy about time zones he cannot see |
| "We are literally trading 24/7, my days." (T2:325) | There is no end of day any more | Lives in UTC+3 with no daylight saving (research 54 §4.1, CHECKED there) | Wants to sleep without missing a stop |
| "WSL is a headache to sort out." (T3:903) | One operating system on my PC, please | Codes and merges on this laptop (T3:1562) | Annoyed by extra machinery |

**Pains.** Text walls. Re-asked decisions. Numbers without a reason. Machinery he did not ask for. Not knowing whether a thing "built" ever ran.

**Gains.** One card each morning. A reason for every move. One click per decision he understands. Freedom: "No limits, okay? That's why nothing is capped." (T3:1105).

### 2.2 Persona: the newcomer, out of the box

Role-played (INFERRED) from what the first-start code gives today (UI-HANDOFF §19, CHECKED there) and his words "Remember, all this is meant to work right out of the box." (T3:1102).

| Says | Thinks | Does | Feels |
| --- | --- | --- | --- |
| "Where do I start?" | Is there a sample I can run? | Installs, accepts the suggested folder, looks at Home | Lost if Home is empty or full of demo numbers |
| "Why is nothing happening?" | Does it need a broker? A key? Data? | Clicks around; tries the copilot | Gives up if the first thing needs a sign-in |
| "Is this a real strategy?" | The example made money in the backtest, so I can trade it | Promotes the example | Burned if a placeholder ever reaches money |
| "What is a node?" | Do I need a server? | Expects one button | Needs plain states: starting, ready, trading |

**What the newcomer can reach today (CHECKED in grounding).** The first-start card (new, open, restore, bring in), template install as a job, the price door open by default, the Dukascopy and Binance downloaders, cTrader sign-in on This PC out of the box once his own app keys sit in Credential Manager (G4a §2.3; UI-HANDOFF §23). Not reachable: any unit, any backtest that trades, any node.

### 2.3 Persona: the copilot, a user of the same doors

His rule: "Remember, anything that an agent under QMA can do, the copilot should already be able to do." (T3:1264). The copilot sees every core toolset by default; a running app's operations are cut from its surface unless a home names `app:<id>` (G4b Q3, CHECKED there). So if QMB and the trading node become mini apps, the copilot loses them by default. That is the sharpest experience gap this pass found for the copilot.

| Says (role) | Needs |
| --- | --- |
| "I wrote the unit; the checker lists two problems; fixed." | A unit check that returns every problem at once, like `workflows_validate` (G4b Q2) |
| "Backtest queued on This PC; I'll tell you when it lands." | A backtest that runs and waits like a test suite: "It runs the same way you run your tests." (T2:135) |
| "Your London node is healing: the broker link dropped twice." | The node's state as a tool answer, not "No node configured" (G2 §3, CHECKED there) |
| "Why didn't it trade? The trend reading said ranging." | A journal read path; none exists (G1 §7) |

### 2.4 Persona: a cheap QMA agent writing a unit, unattended

Role-played from the shipped workflow shape (G4b Q1, CHECKED there): an agent step has no file or shell tool, writes JSON output or saves to the Library; a script step runs Python with `qml` and `qmb` importable; a grader routes pass or fail; a loop sends problems back.

| Thinks | Danger | What saves it |
| --- | --- | --- |
| "The source says 'strong candle'; I'll write 70 %" | Silent invention | The checker requires a label on every number: source said, builder chose, unresolved (funnel4 idea 4) |
| "London open is 08:00" | Wrong clock, wrong season | Sessions are named market sessions with their zone, never a raw hour (research 54 §4.2) |
| "My backtest looks great" | Look-ahead, luck, one of many tries | `knowable_at` guard BUILT (G1 §1.4); tries counted at QMB's door; landmark window after the model's training cutoff (research 11 via STATE) |
| "I'll wait for QMB" | Idle agent, cache expiry | Long work runs as a script step or background job (idea logged, G4b §1.3) |

### 2.5 Persona: the next maintainer

The builder agent or engineer who owns a part next. He judged the earlier run for mixing areas: "So don't combine the MIS work with the QML work and the unit work." (T3:903). This persona needs one area per file, a name per thing, and every state visible in a log a script can read. INFERRED.

### 2.6 Key observations

1. Every persona's top pain is a missing "why": why it traded, why a number moved, why the node is not ready, why the check failed. The journal and the node's state are the experience, not side features. INFERRED.
2. The newcomer and the 3 a.m. version of him need the same thing: a small set of plain states with one line of reason each. INFERRED.
3. Making QMB and the node mini apps (ruling 43) helps the screens (each gets its own page) and hurts the copilot (app tools are cut from its default surface) unless one default is changed. CHECKED gap (G4b Q3); fix INFERRED (lead's call 6).
4. Nothing has ever run on his folder (G4a §2.1). The dummy unit's first run is also QMX's first real start. So the newcomer's first hour and his first hour are the same journey. INFERRED.

---

## The journeys

Each journey has a step table (what the person sees; what must be true underneath, by part), then failure stories, then out-of-the-box defaults. Status words in the "underneath" column refer to today's code. Numbers are named defaults, editable (standing order 5); they are gathered in "Out-of-the-box defaults" further down.

### J1. A newcomer's first hour: install, start, first unit backtested without help

| # | Sees | Underneath, by part |
| --- | --- | --- |
| 1 | The first-start card: a suggested new folder on the roomiest drive, or open, restore, bring in old data | Host: BUILT (PRs 209-214, 219, 234; UI-HANDOFF §19) |
| 2 | Home with a "Getting started" list of six steps, each with a tick when done, and a "What works today" line for anything not connected | Host: a getting-started state computed from facts (practice data present, example unit present, a backtest landed, a node started, a broker signed in). MISSING. Library: starter pack installed on first start (templates, the example unit, the QMB and trading-node apps with triggers off). Template install as a job BUILT (PR 223) |
| 3 | "Get practice data": one click; a progress line; a data card for one month of EURUSD 1-minute bid and ask | Library: `download-dukascopy` template BUILT (QMX's own fetcher, G1 §5). If the download is refused, the step offers synthetic practice data labelled "not evidence": QMB's generator BUILT, forex only (G1 §4.4) |
| 4 | "Open the example unit": a page with two sentences on what it does, its parts, its numbers with ranges, and a stripe "placeholder sizing and exits" | QML: unit template MISSING. Library: `unit` kind fields MISSING (G4b §1.5). The example is the dummy unit packet (`CC-17`) |
| 5 | "Backtest it": queued, then running, then a result: trades, money and R, "1 try in this family", the data label, "run by you on This PC" | QMB: a runner that trades a named unit MISSING; typed partitions into the trading replay MISSING; R in results MISSING (G1 §4.5). Result landing BUILT (PR 187). "Who ran it" from the door's principals BUILT (G2 §6) |
| 6 | "Ask the copilot for your own unit": see J2 | Copilot, checker, QMB |
| 7 | "Start a trading node on This PC (practice)": see J6 | Trading node |
| 8 | "Sign in to a cTrader demo": cTrader's own page opens; back in QMX the account shows with "demo" | Broker links: sign-in BUILT (PRs 211, 221). It needs his own cTrader app id and secret in Credential Manager, and no screen can enter them (UI-HANDOFF §26 row 3, CHECKED there) |

**Failure stories.**
- Dukascopy refuses the download (its 2026 bot wall; research 12 and 33 via STATE). The step says so in one line, offers synthetic data, and retries later. The first backtest still runs. INFERRED.
- The port is taken (host exit code 4, UI-HANDOFF §19 row 3). The desktop app picks the next free port without asking. INFERRED.
- He picks a OneDrive folder; the card refuses with its one line (BUILT, UI-HANDOFF §19 row 8).
- The first backtest asks for a long window and memory climbs, because the replay reader copies history every step (G1 §4.3, CHECKED there). The starter backtest uses one month; the windowed reader is still a must for anything longer.
- The copilot has no model signed in. The getting-started step says which model it will use and how to sign in; Claude's sign-in is his own `/login` (UI-NOTES §7). INFERRED.
- A newcomer has no cTrader app. Step 8 explains that cTrader needs his own app key and that approval takes about a day (research 38 §3.1 via G3 §1.6); every step before it works without a broker. INFERRED.
- The newcomer promotes the example to live. The click card shows the placeholder stripe; the node refuses a placeholder on a live account by default (lead's call 9).

**Out of the box.** Starter pack on first start; practice data = the last full month of EURUSD 1-minute bid and ask; synthetic fallback; the example unit; QMB and the trading node installed as apps; the node starts on This PC in practice mode; display time = this PC's zone.

### J2. He asks the copilot for a unit and watches it get written, checked, backtested and journaled

| # | Sees | Underneath, by part |
| --- | --- | --- |
| 1 | He dictates an idea or drops a video link; the copilot says the idea back in two lines and shows the source saved | Library: `source` kind BUILT; `@youtube` and `@url` refused until REF2 (UI-HANDOFF §18 row 4). Lineage source to idea to unit: "We're not trying to vibe trade or vibe code here." (T1:1574) |
| 2 | A unit draft fills in on the side panel: template (scalper, intraday...), slots, each number with a label: source said, builder chose, unresolved | QML: unit template and dictionary as data the agent can search, MISSING (dictionary outside the repo, G1 §2.1). Stage 0 role and graph types BUILT |
| 3 | On every save, a short list: "3 problems: stop distance has no range; 'London' needs a market session; exit set empty (placeholder allowed)". The list empties as the copilot fixes | The unit checker as one catalog row returning every problem (G4b Q2 point A). Optional: a hook that shows the same list right after each write, his "the same way you yourself, when you write code, you can receive a linter error or something" (T3:1264) |
| 4 | "Checks passed: 12 of 12", each named | QML: Layer 1, Layer 2, prediction linter BUILT (G1 §1.5), extended to the unit |
| 5 | A backtest card: queued on This PC, running, landed; he keeps chatting meanwhile | QMB: tool runs and waits; the agent is not left idle (background job or script step) |
| 6 | Result in money and R, trades, skipped signals with reasons, "best of 3 tries in this family" | QMB: R measure MISSING; tries counted at the door MISSING (G1 §4.4). Journals: backtest phase written by QMB |
| 7 | The unit sits as a draft: "waiting for your yes" | Library: governed kinds land as drafts BUILT (`LIB/landing.py`, G4b §4.1) |

**Failure stories.**
- The checker flags something correct (a false positive). His demand: "we have to make sure there are no false positives" (T3:1264). The checker only refuses what the schema or the compiler cannot accept; style advice never blocks. Every verdict carries the checker's version, so a wrong refusal is a reproducible bug. INFERRED.
- The source names a concept the dictionary lacks. The copilot drafts a dictionary entry; the unit cites it as "unresolved" and can still be backtested with the part left as a labelled placeholder (J25). INFERRED.
- The copilot writes plain Python instead of filling the template. Allowed (`CC-08`); the unit lands labelled "plain Python" and still gets QMB, the journal and the same screens (J18).
- The agent loops on the same problem. The stuck detector stops it with a reason (BUILT, G4b §1.2).
- The result looks too good. The card leads with the try count and the data label, and a look-ahead check result. INFERRED.
- QMB is busy with an overnight sweep. The card shows its place in the queue and which machine it waits for. INFERRED.

**Out of the box.** First look window = last 3 months of the unit's market; judging window starts March 2020 (research 12's default via STATE) with no lookback cap; the checker's tool sits in a core toolset so the copilot has it by default.

### J3. A workflow agent does the same, with nobody watching

| # | Sees (next morning) | Underneath, by part |
| --- | --- | --- |
| 1 | Nothing during the night | Workflows: a schedule or a Library event fires (event triggers BUILT, PR 160) |
| 2 | Nothing | An agent step writes the unit as JSON output or a Library save (no file tools by design today, G4b Q1) |
| 3 | Nothing | A script step runs the unit checker; a grader turns it into pass or fail with feedback; a loop sends problems back. Shape BUILT in `d3-iterate-against-qmb`, waiting on the QMB door (G4b Q1) |
| 4 | Nothing | A script step or an `app_op {app: qmb}` node runs the backtest (route STACKED in PR 204) |
| 5 | Nothing | A judge step (a script, never the agent) applies the judging rules, counts tries, and writes a proposal only if the unit passes |
| 6 | Home, "Needs you": "2 units passed the first look (best of 14 tries). Open to read." | Library: proposal items rendered: "And the proposal should be rendered in the UI." (T1:1574) |

**Failure stories.**
- The model provider's limit is reached at 02:00. The run shows "waiting, resumes at 05:00" and resumes by itself (BUILT, UI-HANDOFF §22 row 3), then lands.
- The agent writes 200 near-copies. Tries are clustered (research 26 via STATE), and the morning card shows at most 5 proposals, the rest queued (research 43 §5 default).
- The agent's backtest reads months its model may remember. Units built on history get a landmark window after the model's training cutoff by default, his "you need to give a pass, in other words, a landmark" (T2:385), applied here to history (research 11 via STATE).
- A data month is missing. The run fails with one named line and lands in the digest, not as an alarm. INFERRED.
- Two runs edit the same unit. Library branches and merge BUILT (PR 195).

**Out of the box.** The unit templates install as drafts until the QMB door exists, then as published with triggers off; proposals per morning = 5.

### J4. He reads a unit's journal and sees why a number moved

| # | Sees | Underneath, by part |
| --- | --- | --- |
| 1 | The unit's Numbers tab: each number with its value now, its range, how it moves ("follows the market" or "follows its record"), and its last move | QML: parameter space with bounds, step, default, UI flag BUILT (G1 §1.9); a `motion` field per number MISSING (problem-solving WS1) |
| 2 | Taps "risk fraction 0.50 % → 0.35 %": a receipt. "After trades 181 to 200, rule 'halve after 4 losses in a row' (placeholder), inside 0.10 % to 1.00 %, at 14:20 your time" | Journals: a calibration row kind MISSING. The unit runtime: state snapshot and restore BUILT (G1 §1.9) |
| 3 | Taps a trade: "stop 12.3 pips = 1.5 × ATR 8.2 at entry" | Journals: the inputs of fast numbers stamped on the trade row (explainer round 1 "One trade row") |
| 4 | A filter: show moves only, show trades only, show both | UI over one journal |

**Failure stories.**
- A number sits at the edge of its range for weeks. The page flags "at its limit since 3 Oct"; a slow-lane agent proposes a new version with a wider range; only his click makes it (WS1). INFERRED.
- Too few trades to move a record-driven number. The number stays near its default and the page says "thin record: 12 of 20 trades". INFERRED.
- The same unit runs on two nodes. Each deployment keeps its own calibration state and the receipt says which. INFERRED.
- The node restarts mid-calibration. A calibration is a pure function of the journal rows up to a watermark, so running it again gives the same result (make-operations-idempotent). INFERRED.

**Out of the box.** Record clock = every 20 closed trades or nightly, whichever comes first; evidence weight starts at trades ÷ (trades + 100) (explainer round 1 "Trust grows with its own record"); both editable on the unit's Numbers tab.

### J5. He promotes a unit to paper, then live, by his own click

| # | Sees | Underneath, by part |
| --- | --- | --- |
| 1 | The unit's "Road to live" line: draft, backtested, stress-tested, paper, demo, live; where it is now | Journals: the world on every row (`trade` kind has `world`: backtest, paper, demo, live, synthetic; G3 §3.2) |
| 2 | One click card: "Admit Gold London breakout v3 to paper on node London-1, markets XAUUSD, account IC demo. It may move by itself: risk fraction 0.10-1.00 % by its record. It carries placeholder sizing." | Library: a unit is a governed kind and lands as a draft waiting for his yes (BUILT, `LIB/landing.py`, G4b §4.1). Trading node: promotion is human-only in code (G3 §1.1) |
| 3 | After the click: "Paper since 09:00. 4 trades. Inside its backtest band." | Journals: paper phase per unit. The node today has Book-level paper only (G3 §5), so per-unit paper must be built |
| 4 | Later, the live card adds "live account; the key lives on London-1" and lists what the click admits | Broker links: live keys only on the node; the PC refuses a live grant (G3 §1.6) |

**Failure stories.**
- He clicks while the node is unreachable. The click is stored as the node's desired state and shows "waiting for London-1"; it applies when the node returns. INFERRED.
- The evidence came from an older QMB version. The card says "tested on QMB 1.2; current 1.3; re-run?" INFERRED.
- The account cannot meet the instrument's minimum lot at this size. The card shows it before the click (instrument record, 43 F6). INFERRED.
- He promotes by mistake. "Withdraw" stops new entries at once; open trades keep their broker stops; closing them is a separate, named choice. INFERRED.
- The market is closed. Activation waits for the session and says when, in his time.

**Out of the box.** Activation default = at the next session open of the unit's market; "now" is a choice on the card. (The node's code has a second activation click at the next day boundary, G3 §1.1; lead's call 11 folds it into one card.)

### J6. He starts a trading node on his PC and sees it started; then on a server in London

| # | Sees | Underneath, by part |
| --- | --- | --- |
| 1 | Apps, Trading node, "Start on This PC" | Mini-app core: the node as an app with a home machine (G4b Q5). His picture: "a mini app can have a server of its own" (T3:1562) |
| 2 | A step list that ticks: checking this PC (disk, clock sync); installing; starting; signing in to the cTrader demo; starting the market readings; self-test; ready | Trading node: a setup made of named steps, each safe to rerun (the connect dialog's pattern, BUILT for storage, compute and deep logs, G3 §1.4) |
| 3 | One word and a line: "Ready · This PC · practice · 0 units · clock ok" | Monitoring: heartbeat per machine BUILT (PR 134). Trading node: a live profile MISSING (G4a §2.2) |
| 4 | "Add a server": the connect dialog with a new kind, "trading node". His cards: rent a server (Hetzner or Contabo with Ubuntu), its address, a one-off Tailscale key, the password typed into a terminal QMX opens, the firewall approval | Host: connect dialog step runner, firewall with a 5-minute undo, `qmx-recover` BUILT and tried on his server (G4a §3 row 12). Trading-node kind MISSING |
| 5 | The same step list runs on the server, then "Ready · London-1 · 11:05 local · clock ok" | Trading node: installer for Linux servers (QMN recipes in check mode only, G3 §1.1); clocks: the node reports its zone and offset |

His words for this journey: "a trading node should be as simple as how, for example, I can set up a server from a provider" (T2:1148) and "is it going to start as server, then show me that the server has started?" (T3:1102).

**Failure stories.**
- His PC's Windows Time service is stopped (G3 §0 item 6, CHECKED there). The clock step fails with "this PC's clock is not synced; turn on time sync?" Turning on a system service is his click. Until then the node runs in a "no new entries" clock band. INFERRED.
- The PC sleeps or loses power. A node on This PC stops with it. The card says so up front: "Runs while this PC is on. For round-the-clock trading, add a server." That matches "PC is home, servers stand in" (memory rulings 136-139). INFERRED.
- The cTrader app is not approved yet. The sign-in step shows "needs you" and the node finishes setup without trading. INFERRED.
- The PC's own view-only sign-in and the node share one cTrader grant, and a token refresh logs the other out (G3 trap 4). Each node registers its own app; the step explains it once. INFERRED.
- Setup stops halfway (SSH drops). Running "Start" again picks up where it stopped (make-operations-idempotent). INFERRED.
- The firewall step locks him out. The 5-minute undo restores access (BUILT).
- The node cannot run natively (an unforeseen Linux-only piece). WSL is the fallback, his "we can go with WSL, okay? If all goes south." (T3:1096).

**Out of the box.** The node on This PC runs practice accounts only (paper and demo); live keys live on servers (ruling 135 handled as code, `N-10`). Self-test on every start: feed live, clock band ok, broker reachable, kill switch drill on demo.

### J7. He deploys a unit to the node with little stress

| # | Sees | Underneath, by part |
| --- | --- | --- |
| 1 | On the unit page, "Deploy", or on the node page, "Add unit" | Trading node: a `deploy` operation. The node side of a click-gated pull exists, the PC side does not (G3 §1.1 "How a bot reaches the node") |
| 2 | Pick node (only ready ones), account, markets from the admitted list, world (paper, demo, live) | Library: the admitted markets per unit |
| 3 | A preflight list that runs by itself: same unit fingerprint as tested; node's QML and QMB versions match the test or the difference is shown; warm-up history available; an instrument record for each market at this broker; minimum lot fits; clock ok; every reading the unit declares is available or has a declared fallback; no placeholder on a live account | QML: content identity `fp1` BUILT; `derive_horizon` gives the warm-up BUILT (G1 §1.9). Broker links: per-broker instrument record MISSING (G1 §5) |
| 4 | "Deploying · warming up 140 of 200 bars · trading" | Trading node: history bootstrap BUILT (G4a §2.2 `data`) |
| 5 | "Withdraw" or "Back to v2" any time | Trading node: deploys as desired state, rollback recipes BUILT in check mode (G3 §1.1) |

His words: "How are we going to be able to deploy units from my machine?" (T3:903).

**Failure stories.**
- The PC goes off mid-deploy. A deploy is a desired-state document the node applies whole or not at all; sending it again gives the same end state. INFERRED.
- Version skew: the node runs an older QML. The preflight names it: "London-1 runs QML 0.3; this unit was tested on 0.4. Update the node first." INFERRED.
- A fresh server has no history. The node fetches warm-up bars from the broker; if the broker has too little (Hyperliquid keeps about 5,000 candles, research 54 §1.4), it says how long the warm-up will take. INFERRED.
- The same unit is deployed twice on one account. Flagged at preflight; whether both may run is the risk session's (`R-06`).
- The market is shut for the weekend. "Starts Sunday 22:00 UTC, 01:00 your time." INFERRED.

**Out of the box.** World default = paper; warm-up = the unit's derived horizon; preflight always on, and a preflight line never blocks a paper deploy except a missing feed or a missing instrument record.

### J8. He watches a forex node in London and a crypto node in Singapore together, on one clock

| # | Sees | Underneath, by part |
| --- | --- | --- |
| 1 | A nodes strip: "London-1 · FX · trading · 11:05 local · ●" and "Singapore-1 · crypto · trading · 19:05 local · ●" | Monitoring: one held stream per node BUILT (G2 §6 "Across machines") |
| 2 | A world clock: his time first (UTC+3), the market sessions as bands (Sydney, Tokyo, London, New York; crypto all day), each node's local time beside it | Clocks: every stamp is UTC BUILT (G2 §9); each node reports its zone, offset and clock band MISSING (G2 §9) |
| 3 | Journal rows in his time by default; hover shows UTC and the node's local time | UI over UTC stamps |
| 4 | A notice a week before a daylight-saving mismatch: "London and New York are 4 hours apart from 25 Oct to 1 Nov" | Clocks: zone database pinned at 2025.2 while 2026.6 exists (research 54 §4.1, CHECKED there) |

His words: "how is a trading node trading FX in London going to be able to also be monitored?" (T3:903) and "the trading node is perhaps a firm" (T3:903). The firm picture fits the display; rules run in each market's zone, never the node's (research 54 §4.2 point 4).

**Failure stories.**
- The Singapore node's clock drifts 0.3 s. It enters the "halt" band (default 250 ms, research 54 §4.3), stops new entries and shows "clock off by 0.3 s" on the strip. INFERRED.
- One node is unreachable. Its card greys with "unreachable since 03:12 your time" and its last values. Its units keep trading (`CC-12`). The PC's view-only broker read still shows that account's positions, so he is not blind (read adapters BUILT, G3 §2.1). INFERRED.
- Crypto has no end of day. Daily reviews run at 00:00 UTC by default, and per-session handovers where a unit trades sessions (funnel3 idea 18). INFERRED.
- Only the forex market calendar exists (G2 §9). A crypto unit's session rules need a 24/7 calendar; a futures unit needs the exchange's. Until they exist, the deploy preflight says which calendar is missing. INFERRED.

**Out of the box.** Display zone = this PC's zone; UTC on hover; heartbeat every 60 s; "unreachable" after 3 missed heartbeats; daylight-saving notice 7 days ahead.

### J9. A unit stops on a risk rule and he learns why

| # | Sees | Underneath, by part |
| --- | --- | --- |
| 1 | An urgent item: "EURUSD scalper stopped at 03:12 your time (00:12 UTC, London-1). Rule: session loss limit −3R reached (placeholder). Open trades: 1, kept with its broker stop. Stays stopped until you resume." | Trading node: automatic escalation and operator-only resume BUILT (G3 §1.5). Journals: a stop row with the rule, the values and the scope |
| 2 | On the unit page, the stop sits in the journal timeline with the trades before it | Journals |
| 3 | "Resume" (his click), "Back to paper", or "Retire" | Trading node: resume is his act in code (G3 §1.5) |

**Failure stories.**
- The rule fires but the broker is unreachable, so nothing can close. The broker-side stop placed with every order protects the trade (venue-resident stop BUILT, G3 §1.1). cTrader has no dead man's switch (G3 trap 3). The item says which protection is in force. INFERRED.
- The rule fires on a bad price spike. The journal keeps the prices that fired it, so he can judge and resume. INFERRED.
- The node restarts after a stop. The stop survives the restart; a heal never resumes a unit (lead's call 10).
- A health stop looks like a risk stop. The card names the kind: "stopped by a risk rule" or "stopped by a health check (crashed 3 times)". INFERRED.
- The kill line flattens, while standing order 7 says "stops" (G3 trap 11). The card says what was done to positions. This verb belongs to the risk session.

**Out of the box.** Every stop is an urgent item; resume is always his click; the reason line follows one template: what, when (his time, UTC, node), the rule and its values, what happened to open trades, what it takes to resume.

### J10. He puts a unit inside a mini app

His words: "units might be need to be integrated in mini apps" (T3:1102), "If I want to rewrite the logic of a unit, maybe as part of a mini app" (T1:1574).

| # | Sees | Underneath, by part |
| --- | --- | --- |
| 1 | Apps, "New app", "from a unit": the copilot builds an app around the unit (its own screen, a chart, its state, its journal) | Mini-app core: `apps_admin` builds apps BUILT; the `build-mini-app` skill is a placeholder (G4b Q5) |
| 2 | Or an app that holds a unit's logic in plain Python, or an ML ensembler | Mini-app core: operations, `provides`, `feeds` BUILT |
| 3 | The app card on Apps shows the unit's state; the app page shows its journal | Mini-app core: `feeds` from the unit journal |
| 4 | To trade, the app's unit is deployed to a node like any unit | Only the node sends orders (STATE mid r27) |

**Failure stories.**
- The app's process crashes three times and the breaker stops it (`APPS/supervisor.py`, G4b Q5). For a research app that is fine. For anything that trades, the trading happens on the node, so an app crash never stops a trade. INFERRED.
- The copilot cannot call the app's operations, because app tools miss the default surface (G4b Q3). Lead's call 6.
- Two apps both claim to be "the" unit. A unit's home of record is the Library; an app refers to a unit by id (G1 trap 16 warns of two registries). INFERRED.

**Out of the box.** A "unit app" template (an app whose operations are `check`, `backtest`, `latest` and whose `provides` publishes the unit's state), as G4b Q5 lists. Ruling 24 allows "a mini-app template built with what exists".

### J11. He edits a workflow template that reads the MIS's logs

| # | Sees | Underneath, by part |
| --- | --- | --- |
| 1 | Workflows, "Pre-session shortlist", graph view | Workflows: the UI editor is DESIGNED; agents edit drafts and validate today (G2 §4) |
| 2 | An input "market readings: trend state, volatility state; FX majors; last 20 sessions". He changes 20 to 40 and adds gold | The MIS: readings stored as series with a dataset card, `source = mis`, read through the market door's features family (G4b Q6). Nothing writes them yet |
| 3 | Validate lists every problem: "no trend-state reading for metals" | Workflows: validate returns every problem BUILT |
| 4 | A test run on a cheap model with its cost; publish (his click) | BUILT (UI-HANDOFF §3) |

His words: "They should be using the logs from the MIS." (T3:903).

**Failure stories.**
- Readings are stale because the node is offline. The input says "readings up to 03:00, stale" and the agent's note says so; the run still lands. INFERRED.
- A reading's version changed mid-history. Each version is its own series; the template names the version it reads. INFERRED.
- "Session" means nothing for a 24/7 market. The input takes a session definition per market, with 00:00 UTC days as the crypto default. INFERRED.

**Out of the box.** Templates shipped with the MIS defaults: pre-session shortlist, market review (almanac), daily data review, unit review, node watcher (ruling 44). Each reads stored readings and journals, never the model.

### J12. Something fails at 3 a.m.

What happens alone, what wakes him, and what he reads in the morning.

| Failure | What happens by itself | What wakes him | Morning card |
| --- | --- | --- | --- |
| The node loses its broker link | Reconnect and gap replay (BUILT, G3 §1.1); no new entries while down; open trades keep broker stops | Only if down with open trades for more than 2 minutes | "Broker link down 03:10-03:14; 1 signal missed (found by replay)" |
| The server reboots for maintenance | The node restarts, returns to its desired state, warms units up | No | "London-1 restarted 03:20; trading again 03:31" |
| His PC loses power | A server node is unaffected; a node on This PC stops | No (it is asleep too) | On return: "This PC was off 7 h; London-1 traded 9 times" |
| The server disk fills | New entries stop; logs rotate | Yes | The cause and the fix |
| A token refresh fails | No new entries on that account; open trades keep stops | Yes, if trades are open | "Sign in to cTrader again" |
| The MIS process crashes | Units use their declared fallback; the strip shows "readings down since 03:05" | No | "Readings were down 03:05-03:40; 2 units ran on fallback" |
| A clock drifts past the halt band | No new entries on that node | Yes, if it lasts 5 minutes | The offset and the time source |
| A unit throws an error every bar | That unit alone is health-stopped; others trade | No, unless it holds open trades | "Gold breakout health-stopped: error in its exit block" |
| A heal keeps failing | Restarts with back-off | Yes, after 3 heals in 30 minutes | The heal log |

**Out of the box.** Only five things wake him: a risk stop with exposure, a node unreachable with open trades, a broker link down with open trades, a clock in the halt band for 5 minutes, a heal failing repeatedly. Everything else is the morning card. (Phone alerts come later, UI-HANDOFF §7; the inbox carries the item now.)

### J13. "Why didn't it trade?" (he did not name this one)

He sees a move on a chart that his unit sat out, and asks the copilot or taps the chart.

| # | Sees | Underneath |
| --- | --- | --- |
| 1 | The gate trail at that minute: clock ok, admitted, guards ok, feed fresh, instrument facts ok, reading "trend state" = ranging (the unit needs trending), so no signal | Journals: "seen, not taken" with a reason (explainer round 2 "What the unit journal keeps"); the readings at that minute, stored with when they were known |
| 2 | Or: "missed: the node was offline 03:10-03:14" | Journals: "missed" found afterwards by replay |

**Failure stories.** Recording every gate on every bar floods the disk. Record when the entry rule fires or a gate changes state; keep the full per-bar trail only in a rolling debug window. INFERRED. Default: 7 days.

### J14. A unit goes back to paper, and comes back

His words: "there are times whereby a unit will go back to paper trading. That is known." (T3:903).

| # | Sees | Underneath |
| --- | --- | --- |
| 1 | A drift alarm on the unit (live results left its backtest band) becomes a proposal card: "Send back to paper?" | Workflows: decay check as a script (`dc` draft, research 30 §7); the move itself is his click (standing order 7) |
| 2 | He clicks; the journal opens a new phase "paper, after live (drift alarm 2)" | Journals: phases inside a world, numbered |
| 3 | Later, "Back to live?" with the paper record since | Same click card as J5 |

**Failure stories.** Earlier designs sent a unit back to paper by itself (07b §4; explainer round 1 "Back to paper when"). That is an automatic transition that is not a risk stop, so it clashes with standing order 7 unless the risk session rules it a risk rule. Left to the risk session; until then it is a proposal. INFERRED.

### J15. The slow-lane agents propose a market, and he attaches it

| # | Sees | Underneath |
| --- | --- | --- |
| 1 | Morning card: "Attach GBPUSD to EURUSD scalper (paper first). Its rule-matched record on GBPUSD, pulled toward its overall record: +0.04R over 63 trades, 3 tries" | Workflows: market review and tagging templates (ruling 44). QMB: judge every market by one rule, shrink toward the whole (WS3) |
| 2 | He clicks "attach"; GBPUSD joins the unit's admitted markets in paper | Library: admitted markets per unit and world |

**Lead's call 12 settles the open meaning of "attach" (funnel3 J6):** attach adds a market to a unit's admitted list in a named world (paper by default). It never changes the unit's rules. A market's own settings come later, only from the unit's record there, and a market's own version is a new version by his click.

**Failure story.** The agent's shortlist is luck. Each shortlist is dated and scored by a script at the next session close (forecast ledger, research 29 via STATE), and shows its own hit rate. His "something that can be, that can't be cheated" (T2:385).

### J16. He builds a new QMB version, or runs two variants side by side

His words: "So if one day I decide to build a new version of QMB, I should be able to." (T3:1383), "Or improve it, or give multiple variants, because it can be a mini app, for God's sake." (T3:1383).

| # | Sees | Underneath |
| --- | --- | --- |
| 1 | Apps: "QMB 1.3" and "QMB 1.4 (fast fills)" as two installed versions or variants | Mini-app core: semver versions per app BUILT (G4b Q5) |
| 2 | On a unit, "Backtest on…" lets him pick one or both; results show side by side with the QMB version on each | QMB: every result names the QMB version and variant |
| 3 | The judge counts both runs as tries in the unit's family | QMB: tries counted at the door, whichever variant |

**Failure stories.** Two variants disagree. Promotion evidence always names its QMB version, and a unit's road-to-live line shows which variant its proof came from. A variant he marks "default" is what workflows use unless they name one. INFERRED.

### J17. He opens a new venue: Hyperliquid perps through CCXT

| # | Sees | Underneath |
| --- | --- | --- |
| 1 | Settings, Connections, "Add Hyperliquid": testnet first, then the account | Broker links: CCXT 4.5.85 carries Hyperliquid with orders, funding, testnet (G4a §2.6); QMX's adapter refuses contract markets (G3 §2.2) |
| 2 | A BTC perp unit: costs include funding in R; trades 24/7; its session rules use a 24/7 calendar | QMB: perps funding as a cost MISSING (G1 §4.4). Clocks: crypto calendar MISSING |
| 3 | Deployed to Singapore-1 | Trading node: a client beyond cTrader MISSING (closed set, G3 §3.2) |

**Failure stories.** Signed actions are rejected when the machine's clock drifts outside Hyperliquid's window (research 54 §4.1); the clock band covers it. Hyperliquid's dead man's switch also cancels protective stops (research 38 via STATE), so the node must not rely on it. Funding flips sign; the unit's cost model reads it hourly. INFERRED.

### J18. Plain Python or an ML ensembler beside QML

A newcomer's freedom: "I want to give myself and people who might use this freedom to be able to create anything that, you know, their mind is able to conjure up." (T3:1102).

| # | Sees | Underneath |
| --- | --- | --- |
| 1 | He writes a unit in plain Python or brings a trained model | QML: a plain Python bot runs with zero QML imports (G1 §1.1, "ungoverned tunnel") |
| 2 | The checker labels it "plain Python": safety checks pass (no clock, no files, same result twice); the vocabulary checks are skipped | QML: Layer 2 BUILT; the scan's limits (G1 §1.6) |
| 3 | QMB, the journal and every screen treat it like any unit | QMB, journals |
| 4 | It can be deployed; the node hosts it through the same seam | Trading node: seats today demand full conformance (G3 §1.1); lead's call 14 |

**Failure story.** A model block needs weights from a file, and file access is denied (G1 §1.6). The host injects weights through a read surface. INFERRED.

### J19. He updates QMX while a node is trading

| # | Sees | Underneath |
| --- | --- | --- |
| 1 | The PC updates; each node card says "QMX 1.4 on this PC; London-1 runs 1.3" | Host: store versions BUILT (PR 213) |
| 2 | "Update London-1": the node finishes open decisions, stops new entries, updates, restarts, warms up, trades | Trading node: immutable tree per commit, switch and rollback recipes BUILT in check mode (G3 §1.1) |
| 3 | "Roll back" if anything looks wrong | Same |

**Failure stories.** A node never updates itself; an update is his click (desired state). An update during a session waits for a quiet window he can override. A PC on a newer version can still read an older node; when it cannot, the line names the side that is behind (the Library's rule, UI-HANDOFF §17 row 6). INFERRED.

### J20. His PC is off for two days

| # | Sees | Underneath |
| --- | --- | --- |
| 1 | Nothing; London-1 trades | `CC-12`; ruling 27 (the node trades alone) |
| 2 | On return: "London-1 traded 31 times while you were away. Journals, readings and logs are back on this PC." | The node-to-PC link: a one-way watermarked pull is designed on the node side, the PC side MISSING (G3 §1.1); this is "the real gap" in G4b Q6 |

**Failure story.** The node's copy fills before the PC returns. The node keeps everything it has not handed over, and its disk check warns well before. INFERRED.

### J21. A unit retires, and still teaches

He retires a unit; it stays in the Library with its cause ("decayed after 3 months; costs rose on its broker"), its lineage, its family tree. A monthly count shows which sources produced units that survived (explainer round 2 "Where winners come from"). Dead units still count, so the count is not biased toward survivors. INFERRED. Needs: Library status and a cause field; journals kept.

### J22. His daily and weekly rhythm

| When | He sees | Made by |
| --- | --- | --- |
| Morning | One card: per live unit what it did (traded, skipped and why, missed), stops, nodes' health in one line, at most 5 proposals, each with evidence | The morning-brief template BUILT, without node facts (research 30 §7); unit and node facts MISSING |
| Before each session the unit trades | Nothing, unless he opens the shortlist | Pre-session shortlist (ruling 44) |
| During the day | One word per node | Monitoring |
| Session close | Nothing; forecasts written and scored by a script | Forecast ledger (research 29) |
| Weekend | Per-unit lessons that passed a statistics check, the week's market map scored, the family tree, sources that produce survivors | Unit review, market review templates |

His words that set the goal: "a beefier advantage compared to a person just using a simple bot" (T2:858). The honest version of that advantage is breadth, memory and discipline; the edge still has to come from the unit's logic (research 30 §8.2).

### J23. The week London and New York are four hours apart

This week (25 Oct to 1 Nov 2026) London and New York are 4 hours apart, not 5 (research 54 §4.1, CHECKED there). He lives in UTC+3 with no daylight saving. Sessions computed in each market's zone stay right; a rule written as "London 13:00 = New York open" would be wrong. The checker refuses raw hours in session rules and requires a named market session; a notice reaches him 7 days before each mismatch. INFERRED.

### J24. A paid futures feed, switched on later

His words: "When the app is live, I'll be spoiled for choice" (T3:1562). Settings, Connections, "Add Databento" (or a futures broker). Until then, order-flow units show "waiting for data: needs a futures depth feed" and stay out of deploy. The feed's monthly cost shows as a reading, never a cap. Nothing in the core assumes a paid feed (research 54 §1.5). Needs: a data entitlement check per machine (research 54 §3.3).

### J25. The dictionary meets a new word

An agent meets "liquidity sweep" and the dictionary lacks it. It drafts an entry; the checker validates the entry's form; the entry's status is "named" until it has code and a test (funnel4 idea "status ladder"). A unit may cite a named entry, and the part stays "unresolved" until code exists, so it can be backtested only with that part as a labelled placeholder. Later growth goes through the same door the copilot uses (STATE mid lead-13). INFERRED.

---

## Step 3. Define

### 3.1 Point-of-view statements

- **He** needs every move (a trade, a skip, a number, a stop, a heal) to carry its reason in one line, because he approves money decisions from his phone and has been burned by self-reports.
- **The newcomer** needs a first unit backtested in the first hour with no broker and no server, because the first thing that needs a sign-in is where people give up.
- **The copilot** needs QMB, the node, the unit checker and the journals on its default surface, because his rule says it can do whatever an agent can.
- **The unattended agent** needs a check it cannot talk its way past, at every step, because nobody is watching.
- **The maintainer** needs one part per file and every state in a log a script can read, because the last run mixed areas.

### 3.2 How might we

1. HMW make "a node started" a fact he can see, not a log he has to read?
2. HMW let a deploy fail halfway and still be safe to click again?
3. HMW show the two speeds of a unit's numbers so "self-tuning" is visible?
4. HMW make a placeholder impossible to mistake for a strategy?
5. HMW stop the best-looking market from being the one that reaches his card?
6. HMW let a unit read the MIS without ever waiting for it?
7. HMW show London and Singapore on one clock he understands, through daylight saving?
8. HMW wake him only for what needs him at 3 a.m.?
9. HMW let the copilot reach mini-app operations by default?
10. HMW let him build a new QMB version and compare it with the old on the same unit?
11. HMW let a newcomer trade nothing yet still learn the whole loop?
12. HMW keep the node's PC side and server side one product?
13. HMW tell a health stop from a risk stop at a glance?
14. HMW make "why didn't it trade?" a one-tap answer?
15. HMW keep his PC the home while servers do the round-the-clock work?
16. HMW make a unit inside a mini app trade only through the node?
17. HMW let agents propose markets without luck moving from backtests to shortlists?
18. HMW update QMX without stress while units trade?
19. HMW switch on a paid feed later without touching the core?
20. HMW make every number on every screen traceable to its rule and its data?

### 3.3 Key insights

1. **The experience lives in states and reasons, not features.** Most journeys end in "what does it say now, and why". A small closed vocabulary of states per part, each with a one-line reason template, serves him, the newcomer, the copilot and scripts at once. INFERRED.
2. **Desired state is the shape of his "less stress" (T3:1102).** Deploy, promote, update and node setup all become "here is what I want; converge to it", which survives a PC turning off, a click while the node is down, and a step dying halfway. INFERRED.
3. **The node and QMB as mini apps fit the screens and break the copilot unless one default changes.** CHECKED gap (G4b Q3); INFERRED fix.
4. **The first real start is the proof.** Nothing has run on his folder (G4a §2.1). The getting-started list doubles as the dummy unit's acceptance journey. INFERRED.

---

## Step 4. Ideate

Methods from the CSV: brainstorming, analogous inspiration, provotype sketching, SCAMPER design. Judgement deferred; the clusters at the end name what serves the journeys.

### 4.1 Analogous inspiration

| Field | How it handles a similar problem | Idea for QMX |
| --- | --- | --- |
| White-label platforms (Shopify, Wix), his picture: "it's like handing someone white label software" (T3:1338) | A small core, stable extension points, a starter theme so a new shop works on day one | A starter pack on first start; QMB and the node as the first two apps on the core |
| Hosted app platforms (Render, Fly, Heroku) | Deploy log as named steps; one status word; rollback to the last good release | The node's setup and deploy as named, rerunnable steps with one word at the end |
| Kubernetes and systemd | Desired state, restart with back-off, readiness versus liveness | "Ready" means all checks pass; "healing" means restarting with back-off; "stopped" means a person or a rule stopped it |
| Home Assistant add-ons | Each add-on has its own page, logs tab, start and stop, health | The node and QMB app pages: Operations, Health, Logs, Setup |
| Aviation crew alerting | Few warnings, ranked; cautions wait; advisories are silent | Five things wake him; everything else is the morning card |
| World clocks on trading desks | Local time plus a strip of market sessions | The world clock strip with each node's local time |
| Package lock files | A lock pins what was tested | A deploy pins the unit fingerprint and the QML and QMB versions it was tested on |
| Flight data recorders | Record what matters when it changes, keep a short full buffer | Gate trail on change, full trail for 7 days |

### 4.2 Generated ideas (unranked)

1. A getting-started list on Home that ticks itself from facts.
2. A "What works today" line naming anything not connected, in plain words.
3. Synthetic practice data so the first backtest needs no network.
4. The example unit with a placeholder stripe and the words "example, not a strategy".
5. Node states: setting up, starting, ready, trading, healing, paused, stopped, unreachable since.
6. Setup and deploy as named steps that tick, each safe to rerun.
7. A deploy preflight that runs by itself and explains every red line.
8. Desired state for deploy, promote, update.
9. A nodes strip with local times and one dot each.
10. A world clock with market session bands and his own time first.
11. A daylight-saving mismatch notice a week ahead.
12. A Numbers tab: value, range, how it moves, last move, receipt.
13. Fast numbers explained on the trade row; slow numbers by a calibration receipt.
14. The honest number only: no raw ranking of markets by profit anywhere.
15. "Why didn't it trade?" as a gate trail.
16. A stop card that always says what, when, which rule, what happened to positions, how to resume.
17. Health stop and risk stop shown as different kinds.
18. Five things wake him; the rest is the morning card.
19. QMB's "what ran, who ran it" list with the principal behind each run.
20. QMB versions side by side on one unit.
21. The node's heal log: what restarted, why, how many times.
22. The PC's view-only broker read as an independent view of positions when a node is unreachable.
23. A unit-app template.
24. Readings with "stale since" and "unit used its fallback" badges.
25. A forecast ledger: every agent shortlist scored later.
26. Placeholder units refused on live accounts by default.
27. One click card that says exactly what it admits.
28. An update that never runs by itself on a node.
29. A data entitlement line: "waiting for data" for order-flow units.
30. Provotype: a node with no screen, only a phone notification per state change.
31. Provotype: the PC as the only node, servers only as a backup that takes over on a missed heartbeat.
32. Provotype: no copilot at all; every journey by buttons. Shows which steps truly need an agent (only J2, J3, J15).

### 4.3 Top concepts (the skill asks for two or three)

1. **States with reasons.** One closed list of states per part, each with a one-line reason template (ideas 5, 16, 17, 24). Serves J6, J9, J12, J13.
2. **Desired state for every change that reaches a node.** Deploy, promote, withdraw, update (ideas 6, 7, 8, 28). Serves J5, J7, J19, J20.
3. **The first hour as the proof.** The getting-started list, synthetic data, the example unit (ideas 1 to 4). Serves J1 and the dummy-unit packet.

---

## Step 5. Prototype (as storyboards for the build's live lanes)

His ruling 1 rules out a throwaway prototype, and the prototype skill is dropped (`CC-17`, `P-02`). So this step makes no code. It turns the top journeys into storyboards that the build plan's live lanes can drive on the real app (lead's call 2). Each frame names what a lane saves.

| Storyboard | Frames | Proves |
| --- | --- | --- |
| The first hour (J1) | Blank PC profile; first-start card; new folder; getting-started list; practice data card; example unit page; backtest result in money and R with "run by you" | The dummy unit works on the real template, and a newcomer can reach it |
| Copilot writes a unit (J2) | A sentence; draft with labels; three problems, then none; checks passed; backtest landed; journal backtest phase | Agents can build units and backtest them: "Can they build units rather? Can they, you know, backtest them?" (T3:1093) |
| Overnight (J3) | Trigger; agent JSON; checker refusal fed back; pass; judge script; proposal on Home | The deterministic loop with no agent self-judging |
| A number moves (J4) | Backtest with recalibration; Numbers tab; receipt | Self-tuning shown, two speeds |
| Start a node on This PC (J6) | Step list ticking; "Ready"; self-test lines | A node starts and shows that it started |
| Deploy and withdraw (J7) | Preflight; warming up; trading; withdraw; deploy again gives the same state | Little stress, idempotent |
| A stop (J9) | Forced placeholder limit on demo; urgent item; journal row; resume | The only automatic transition, explained |

## Step 6. Test plan

| Test | With whom | What to observe |
| --- | --- | --- |
| Say-back | Him, on his phone | Can he say in one sentence what a click card admits, why a number moved, why a node is healing? |
| Cold start | A fresh agent with no planning context, on a blank profile, given only "use QMX" | Does it reach a backtested unit in the first hour without help? Where does it stall? |
| Cheap author | A Haiku agent through his plan login (memory: tests on Haiku) | Tries to a passing unit; invented numbers it was forced to label |
| 3 a.m. drill | The node on demo: cut the broker link, kill the MIS, skew the clock, fill the disk | Each failure produces the state and the line in J12, and only the five wake items |
| Copilot parity | The copilot on its default surface | Can it run a backtest, read a node's state, deploy to paper? |

**Assumptions to test.**
- A1. States with reasons are enough for him to trust a node without opening logs.
- A2. A newcomer accepts synthetic data for a first backtest if it is labelled.
- A3. Five wake items are the right five.
- A4. A deploy as desired state never leaves a node half-deployed.
- A5. The PC's view-only read is a useful second view when a node is unreachable.

## Step 7. Next iteration

**Refinements.** Fold the journeys into the Level 1 files by part (the table below). Fold the storyboards into the build plan's live lanes. Add the screens in `ui-needs.md` to the UI notes.

**Action items for the architecture (by part).** See "Needs by part". The first five the architecture must not miss: the unit checker as a core tool row; the QMB door bound with a runner that trades; the node as an app with a setup made of rerunnable steps and a live profile; the node-to-PC link; the copilot's default surface including the two apps.

**Success metrics.** A newcomer's cold start reaches a backtested unit; every state in J6, J9, J12 has a reason line; the say-back test passes on three click cards; the 3 a.m. drill wakes him exactly for the five items.

---

## Needs by part

Gathered from the journeys. Each Level 1 agent can take its own rows. "J" numbers point at the journeys.

| Part | Needs | From |
| --- | --- | --- |
| QML | A unit template with named slots; each number with value, range, motion (fast or slow), authority and origin label; named market sessions instead of raw hours; a placeholder label on a slot; a plain-Python path that keeps safety checks only | J1, J2, J4, J18, J23, J25 |
| The unit checker | One core catalog row returning every problem with where and what; the same function in a workflow script step; optionally a hook after writes; its version on every verdict; refuses only what the compiler or schema cannot accept | J2, J3 |
| QMB | A runner that trades a named unit on Library data; results in money and R; tries counted at its door; every result names its QMB version and variant and who ran it; a queue position; recalibration replayed inside backtests (parity); a judge step that applies one rule to every market | J1, J2, J3, J4, J15, J16 |
| The trading node | An app with a home machine; setup as named rerunnable steps; a self-test; a closed list of states with reasons; deploy, withdraw, update, roll back as desired state; per-unit paper; a stop that survives restarts; heals that never resume a risk stop; clock bands; reports zone, offset and version in its heartbeat; a live profile; clients beyond cTrader | J5, J6, J7, J8, J9, J12, J17, J19, J20 |
| The MIS | Default readings for every class in scope; readings stored with the time they were known and their version; a publisher into homes that exist; units read them through a declared fallback; "down since" visible | J8, J11, J12, J13 |
| Journals | Keys: unit and version, deployment, world, phase, instrument, timeframe, broker, account, platform, node, QMB version; rows for trades, seen-not-taken with reason, missed, calibration receipts, stops with rule and values, agent notes; fast-number inputs on the trade row; gate trail on change plus a short full buffer | J2, J4, J5, J9, J13, J14 |
| The Library | Unit kind fields; admitted markets per unit and world; status and cause on retirement; proposals rendered; starter pack; reading and journal cards | J1, J5, J15, J21 |
| Workflows | Unit templates (build, iterate, judge); slow-lane templates reading stored readings (shortlist, market review, daily data review, unit review, node watcher); triggers per session and per N trades; a forecast ledger scored by script | J3, J11, J15, J22 |
| The copilot | The unit checker, QMB, node state and journal reads on its default surface; `app:qmb` and `app:trading-node` in the default home toolsets | J2, J10, §2.3 |
| The mini-app core | A unit-app template; the node and QMB as apps; app pages with operations, health, logs; `provides` with freshness for node state and readings | J10, J16 |
| The host and the connect dialog | A getting-started state; a trading-node kind in the connect dialog; port fallback; the PC side of the node link | J1, J6, J20 |
| Monitoring | One held stream per node; five wake items; everything else to the morning card; OpenObserve as the one log home (the node's own Grafana stack is a second home, G3 §5) | J8, J12 |
| Broker links | Per-broker instrument records; CCXT beyond spot; a Hyperliquid client on the node; a data entitlement check; the PC's view-only read as a second view | J7, J8, J17, J24 |
| Clocks | UTC everywhere; each machine's zone, offset and band reported; calendars for crypto, futures, indices; the zone database kept current; a mismatch notice | J8, J17, J23 |

## Out-of-the-box defaults

Every row is a named number or choice with a starting default, editable in the UI (his standing rule). "Placeholder" means no evidence set it yet.

| Default | Starting value | Why this start |
| --- | --- | --- |
| Starter pack on first start | Templates, the example unit, the QMB and trading-node apps, triggers off | J1; ruling 24 allows a template built from what exists |
| Practice data | Last full month of EURUSD 1-minute bid and ask (Dukascopy) | Smallest real month that exercises a scalper; the reader still copies history per step |
| Practice data fallback | Synthetic EURUSD month, labelled "not evidence" | QMB's generator exists for forex (G1 §4.4) |
| First-look backtest window | Last 3 months | Fast feedback; placeholder |
| Judging window start | March 2020, any earlier start allowed | research 12 via STATE; no lookback cap (`B-05`) |
| Node on This PC | Practice accounts only (paper, demo) | Ruling 135 handled as code (`N-10`) |
| Heartbeat interval | 60 s | research 54 §4.3 |
| Unreachable after | 3 missed heartbeats | Placeholder; one missed beat is normal network noise |
| Heal back-off | 5 s, doubling, up to 5 min | Placeholder; the common pattern |
| Heal escalation | 3 heals in 30 min becomes a wake item | Placeholder |
| Broker down with open trades, wake after | 2 min | Placeholder |
| Clock bands | warn 25 ms, no new entries 100 ms, halt 250 ms | research 54 §4.3 (from the node spine) |
| Clock halt, wake after | 5 min | Placeholder |
| Daylight-saving notice | 7 days ahead | research 54 §4.3 |
| Display time zone | This PC's zone; UTC on hover | J8 |
| Crypto day boundary for reviews | 00:00 UTC | Placeholder |
| Proposals on the morning card | 5, rest queued | research 43 §5 |
| Record clock for slow numbers | 20 closed trades or nightly | research 43 §5 (placeholder there) |
| Evidence weight | trades ÷ (trades + 100) | Explainer round 1 |
| Gate trail full buffer | 7 days | Placeholder |
| Deploy world | Paper | J7 |
| Activation | Next session open of the unit's market; "now" on the card | J5 |
| Placeholder on a live account | Refused | Lead's call 9 |

---

## Lead's calls

Each is a default the ledger does not settle, with why and how to undo it. None is asked of him (`P-12`, ruling 2).

| # | Call | Why | How to undo |
| --- | --- | --- | --- |
| 1 | Personas: him, the newcomer, the copilot, the unattended agent, the maintainer. "The unit as a user" is not repeated | funnel3 already ran it; the maintainer is a user per the experience-first principle | Add a persona section |
| 2 | The skill's prototype step is met by storyboards that become the build's live lanes, not by code | His ruling 1 and `P-02` drop throwaway prototypes and the prototype skill | Drop the storyboards; lanes come from the plan only |
| 3 | The node's states on every screen: setting up, starting, ready, trading, healing, paused, stopped, unreachable since | One closed vocabulary serves him, the copilot and scripts | Rename in the node's state table |
| 4 | Screens call the app "trading node" (his word) and the machine by the name he gave it or "This PC". No "trading server" or "workflow server" kinds | "A server can be a server." (T3:1102). This supersedes UI-HANDOFF §17 row 14's "trading server" | Rename |
| 5 | Every change that reaches a node is a desired-state document the node converges to | Survives a PC off, a click while the node is down, a step dying halfway | Make deploy a direct call; lose the retry safety |
| 6 | The default copilot home lists `app:qmb` and `app:trading-node` beside the core toolsets (one shipped settings default, no code) | His rule that the copilot can do what agents can; app tools are cut from the default surface (G4b Q3) | Remove the two names; expose the operations as core catalog rows instead |
| 7 | The node on This PC runs natively on Windows under the mini-app supervisor for practice; Linux servers run it under systemd; WSL only as the fallback | "I would prefer using Windows than sorting WSL." (T3:903); the node's logic is not Linux-bound, only its supervision, powers door and secret store (G4a §2.2) | Run the PC node in WSL (his accepted fallback, T3:1096) |
| 8 | The node on This PC trades practice accounts only; live keys live on servers | Ruling 135 is in code and is the node pass's to handle, never a question (`N-10`, `CC-13`) | The node lens may place a live key store on the PC |
| 9 | A unit with any slot labelled placeholder is refused on a live account by default; the click card shows the stripe | Placeholders are for backtest and demo (`U-04`); "a small mistake in there is very costly" applies doubly to money | A setting he flips; the risk session replaces the placeholders anyway |
| 10 | A heal never resumes a unit stopped by a risk rule; a risk stop survives restarts | Standing order 7: only he resumes; a heal is not his click | None advised |
| 11 | Promotion is one click card with an activation choice (next session or now), folding the node's second activation click | "less stress" (T3:1102) | Restore two clicks |
| 12 | "Attach a market" adds it to a unit's admitted list in a named world, paper by default; never changes rules | Settles funnel3 J6's open meaning within `CC-11` | Make attach admit straight to live with his click |
| 13 | Five things wake him (J12); the rest goes to the morning card | Fewer alarms, more trust | Edit the list in Settings |
| 14 | A plain-Python unit may be deployed if it passes the safety checks (Layer 2), without the vocabulary checks | `CC-08`; the node's seats demand full conformance today (G3 §1.1) | Keep full conformance for anything on the node |
| 15 | A drift alarm proposes "back to paper"; it does not move the unit by itself until the risk session rules it a risk rule | Standing order 7 | The risk session may make it automatic |
| 16 | The getting-started list is computed from facts, never from clicks on the list | A list that ticks itself cannot lie | A manual checklist |
| 17 | The full per-bar gate trail is kept 7 days; decisions and gate changes are kept for ever | Disk; his 27 Oct ask to mind the data volume (STATE "Journal = the unit's DevOps layer") | Change the buffer days |

## For the risk session

Points this pass found that belong to risk and sizing (`R-01` to `R-13`). They are not designed here.

1. **The placeholders to rip out.** The example unit's sizing (a fixed fraction that halves after a losing streak and steps back after wins, inside a range), its exit set (a stop at a multiple of ATR, one target in R, a time exit), and its account halts (a session loss limit in R). Each carries the placeholder label; the risk session greps the label.
2. **The live refusal for placeholders** (lead's call 9) is a risk guard; the risk session owns its final form.
3. **Which risk numbers move, and at which speed.** The motion field (WS1) separates numbers that follow the market from numbers that follow the record. Volatility-scaled size is fast; evidence-weighted risk is slow. The risk session assigns each sizing and exit number its motion and its clock.
4. **Stop versus flatten.** The node's kill line flattens; standing order 7 says a risk rule "stops" a unit (G3 trap 11). The stop card needs the verb the risk session picks.
5. **Back to paper on drift** is a proposal until the risk session decides whether it is a risk rule (lead's call 15; research 24's conflict).
6. **Sticky stops and resume.** A risk stop survives restarts and heals; resume is his click (lead's call 10). The scopes (unit, account, node) and their order are the risk session's.
7. **Two units, one account.** The deploy preflight flags it; whether both may run, and how they share the budget, is the book and correlation question (`R-06`, `R-09`).
8. **What the journal must keep so the old sizing can be replayed later:** equity at entry, session, streak, and the trades a stopped unit would have taken (research 26 via STATE). The journal keys in "Needs by part" include them.
9. **Venue-resident stops are load-bearing.** cTrader has no dead man's switch; Hyperliquid's cancels protective stops (G3 trap 3, research 38). The risk session decides what every order carries at the broker.
10. **Funding and swap in R.** Perps funding and CFD financing must enter results in R, or sizing reads the wrong edge.
11. **Minimum lot against a small account.** At USD 300 the minimum lot may exceed the intended risk; the click card shows it (J5) and the risk session decides what happens.
12. **Per-unit paper** replaces the node's Book-level paper (G3 §5); the risk session decides how long paper lasts and what ends it.

---

## How the quotes were checked

A script read every `"..." (Tn:line)` pair in the three files of this folder and looked for the quoted text, with whitespace normalised, on the cited line of the cited transcript, splitting the files on `\n` only so line numbers match `grep -n`. The script and its result are recorded at the end of `problem-solving.md`, which was written last.
