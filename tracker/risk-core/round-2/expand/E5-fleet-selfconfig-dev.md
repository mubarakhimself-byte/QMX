# E5: watching 200 units, how a unit configures itself, a newcomer's first day, a developer's path

Written 7 Nov 2026 for round two. Nothing here is a verdict. It feeds the funnel.

**Short paths.** `RC` = `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. `W` = `D:\QMX-worktrees\bld-repair-24\` at 351e7521, read only. `T` = `W\qmx-agents\packages\qmx-engine\src\qmx_engine\templates\`. `UI` = `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair\apps\qmx-ui\`. `SWAP` = `RC\unit-baseline\SWAP-CHART.md`. `MAP` = `RC\review-2026-11-07\system-map.md`. `Temp` = `D:\Temp\e5\`, where every test script and result file sits. M49 to M54 are his messages in `RC\seeds\operator-words-2026-11-06.md`.

**Words.** R is a result in units of the amount risked on that trade. A card is a proposal he clicks. A block is one small QML piece (`entry.json` plus `block.py`). A socket is a place in the unit a block plugs into. A template (workflow) is a shipped job in `T`. A replay is QMB running a unit over past bars.

**Labels, from the brief's test.** **CONFIG**: a setting, preset or pod choice, never a law. **SEAT**: leave it out and the core gets reworked, so the core must leave room. **CONTENT**: someone adds it later. **OTHER**: another session's, named.

**About the tests.** They are mechanism tests on made-up worlds where the right answer is known. No account, no compounding, no dollars. The settings inside them (win rates, trades a day) are test settings, not proposals. They show how a mechanism behaves. They say nothing about real markets, and no test result below decides what goes in; the brief's test does.

## The short version

1. **Fleet watch.** As built, the decay job would send about **91 cards a night for 200 healthy units**, and 96% of them get flagged within 90 days (Temp `m3_fleet.py`). The fix is to stop treating the unit as the thing watched. Scripts keep one row per unit and rank them. An agent looks only at the top few plus each new incident, so its work stays the same at 20 or 200. He gets a digest, a few cards and rare pages.
2. **Self-configuration.** Every earlier design assumed a unit configures itself by learning from its own closed trades. That premise is mostly wrong. Three different jobs were folded into one: **find** a starting value (a replay over past bars), **track** the market (read facts), **correct** a replay that lied (the built motion engine). Stacked, these beat each one alone in the tests. No new "applier" part is needed; the built engine already does that job.
3. **Newcomer.** Walking install to a unit finds 17 gaps. The largest: no installer a stranger can run; a cTrader approval that takes about a day; one dummy template; first-run steps that tick when opened and not when done.
4. **Developer.** Good parts exist: contract tests that enrol blocks automatically, a field census, upgraders. What's missing is one guide, a way to debug a size (the receipt is a literal today), and a plan for compiler bumps, because one bump means every deployed unit needs a new test record. **So widen all sockets in one bump.**

---

# 1. Fleet watch

His words: "Do you know what it means to monitor 200 units?... Why not just have an agentic workflow that can cater for that?... As a mini app also. As a mini app or so." (M49)

## 1.1 The premise, and the census

**Premise on disk:** a watcher judges each unit and raises what it finds (`T\dc-decay-and-limit-report\scripts\read.py`; `RC\expansion\X7-agents.md` H31; `X6` X6-25).

**Census:** I ran the shipped rule, with its shipped defaults, on units where nothing is wrong. Mix: a quarter at 40 trades a day, half at 6, a quarter at 0.5. All have a real edge: +0.10R, 44% winners at 1.5R. 90 nights, 8 seeds. Script: Temp `m3_fleet.py`, part A. Rule copied from `read.py:79-88`.

| Units, all healthy | Cards a night | Of which Alarm | Units flagged at least once |
|---|---|---|---|
| 20 | 9.0 | 7.1 | 97% |
| 200 | 91.4 | 70.9 | 96% |

**Why.** `alarm_at_r` is 0 and it judges the last 20 trades. The noise of 20 trades (about 0.27R here) easily covers a 0.10R edge, so about a third of healthy units read Alarm on any night. Each flagged unit gets a fresh card every night (`read.py:104`, `land.py`).

**This is not a bug in the template.** Its README says these rules are "the starting form" and that the risk session settles the decay definition. It is this session's placeholder to swap. Settings are editable.

**What the census says.** The load comes from one thing: a per-unit threshold on a window the noise covers. More units just multiply it. So fixing the threshold value won't help: at any threshold, 200 independent judges either flood or go blind. The role has to move.

## 1.2 The design, from built pieces

**One rule: scripts decide what is true, agents explain and propose, he sees exceptions, and nothing here touches money.** (Existing shape: "numbers from scripts, words from a writer, a receipts grader checks every number", `T\dm-demo-monitor\README.md`.)

| Layer | Who | When | What it does | Built from |
|---|---|---|---|---|
| 0. Inside the unit | Unit rules and guard, no agent | Each trade | Brakes act at once. Silent, recorded. Never waits for anyone | Socket work; his ruling that the fast lane has no agents (`audit-ship\RULINGS-NOW.md`, via H4 I-54) |
| 1. Health | Script | Every 5 minutes | Node and unit state words. Fires only when the hash changes, at zero tokens | The `monitor` node (`qmx_engine\nodes\monitor.py`), `T\gw-guard-watchdogs` |
| 2. Nightly fold | Script | Nightly | One row per unit: state, evidence score, rank, family score, silence against expected trade rate, cost assumed against paid, skips by reason, number moves, brake fires against expected | `t7` (digest view), `dm-demo-monitor` (fills), `s2` (market tags), new fold |
| 3. Grouping | Script | With 1 and 2 | Folds rows sharing a root-cause key (broker, feed, node, class, event, family) into one incident | New; design in `X6` X6-16, `X7` H17 |
| 4. Triage | Agent, narrow | Nightly, plus each new incident | Reads the top K rows and each incident. Names a cause from a fixed list: cost, fills, regime, code, signal, unknown (H4 I-40). Proposes one next step | `writer` role, `receipts-grader`, `rk8-incident-post-mortem` |
| 5. Slow jobs | Agents | Weekly or on demand | Studies benched units, reruns `u1` and `u2`, tunes in replay (section 2) | `rv-weekly-review`, `d3`, `d4`, `u1`, `u2` |
| 6. To him | Script chooses, agent words it | Morning, or on a page condition | Digest, ranked cards, pages | `morning-digest`, `pp-proposal-pack` (already "at most three cards"), `UI\src\lib\settings\GeneralSection.svelte` "Alert me when" |

**Why the agent is narrow.** April's departments mostly did not work (`X7` RP2, H18), and in sources, simple controls often beat agent runs (H4 hard facts). Agents have evidence behind them for counting, explaining and watching. So they get those jobs here. His department picture (M50, "I think") isn't refused: it lives in layer 5 and in pods (`OTHER`: agentic upgrade).

**A fixed list of agent jobs, each stating why a script can't do it:**
- **Triage:** reading a journal and a chart of skips and naming a likely cause needs judgment.
- **Morning words:** the script picks the facts, the writer says them.
- **Coroner:** studies benched units. A pattern seen repeatedly becomes a tested detector (H4 I-40).
- **Sitting-duck advocate:** finds units that brakes hold below baseline (`X7` H32). This is the performance check: a watch that only finds danger drifts into safety. **CONTENT**, but it needs the same rows.

## 1.3 What reaches him

Tiers come from `X6` X6-14 and X6-17. His Settings screen and `UI-NOTES-UNITS.md` section 12 already cover a good part. He told me to check (M49), and it holds: six alert switches, quiet hours, an editable wake list. Phone push is a notification matter (M49, Q7). **OTHER**: UI.

| Tier | Goes to | Examples | Limit |
|---|---|---|---|
| Silent | Journal | A clamp binds, a spread gate refuses, a brake steps inside its band | None |
| Digest | One morning screen | A number moved. A brake fired and cleared. How many units in each state | One screen, whatever the fleet size |
| Card | Needs-you inbox | A strict bar crossed, an incident that needs a choice, a market to drop | The attention budget. Overflow becomes one digest line |
| Page | Phone | Money at risk now, system can't fix it, his action changes the outcome. Safe step already taken | Rare by construction. Trips are never deduplicated, only pages (X6-16) |

**The fixed lines hold.** Agents touch no money. Only he promotes to live. Exits are never blocked. Only he lowers the kill switch. Whether a rule may step a unit down, or back up, is a pod setting (**CONFIG**). He said so of Q5 in M49. A reckless setup stays expressible.

**When he is away.** A card carries what silence means (`T\pp-proposal-pack\README.md`: "the default if he does not answer"). The unit keeps running under its pod's rules. Nothing waits for him unless the pod says so.

## 1.4 The alarm budget: two lists, not one threshold

One bar can't do both jobs, so split them.

**List one, "who gets looked at".** Each night, rank by evidence and show the top K to the triage agent. There is no threshold, so a false alarm is impossible by construction; K is the cost. It finds a broken unit fast. **CONFIG.**

**List two, "who gets acted on".** A strict bar under one fleet budget: expected false alarms a month across all units. It may trigger a pod rule or a card.

The evidence score is an e-detector: a running bet that the unit's results fell below a baseline. It has a known false-alarm bound (`X5` H16, `2501.04130`). Tested with one broken unit, edge going from +0.10R to -0.10R, against a baseline of +0.05R. Scripts: Temp `m3_fleet.py` parts B to D, `m3b_threshold.py`. Baselines and bars are test settings; values belong to the numbers talk.

| What is measured | 20 units | 200 units |
|---|---|---|
| Top 3 a night: nights until the broken unit is listed. 40, 6 and 0.5 trades a day | 1.5, 4.5, 55.5 | 3, 24.5, 90 or more (test ended) |
| Strict bar at the theory value: false alarms a month | 0 | 0 |
| Same bar: days to catch. 40, 6, 0.5 trades a day | 31, 162, 1043 | 39, 210, 1702 |
| Bar at 1/100 of theory: false alarms a month | 0.5 | 0.33 |
| Same bar: days to catch | 13, 41, 85 | 22, 97, 478 |
| Bar at 1/10,000 of theory: false alarms a month | 471 | 1565 |

**What this shows.**
- **A correction to H4 I-34.** It warns that ten times the units means a ten times higher bar, so demotion "gets much slower". The bar does rise tenfold, but evidence builds exponentially, so catch time grew by about 30% to 135% for the two active styles. The slowest style did worse, 63% at the theory bar and about 5.6 times at the 1/100 bar. So it's much less than tenfold where units trade often, and the slow units were already too slow.
- **The theory bar is loose by far.** Measured false alarms were 0 against a budget of 1 a month. Setting the bar by replaying a unit's own shuffled record can recover much of that slack. But it has a cliff: at 1/10,000, the fleet floods.
- **A strict bar alone is too slow at 6 trades a day** (97 to 210 days at 200 units). That's why list one exists.
- **A slow unit can't be judged alone.** At 0.5 trades a day it takes years. The screen must say "too thin to judge", as `read.py` already does, and never imply it's fine. His scalper-first plan hides this at first; his swing and ORB units will meet it.

**Family pooling.** One logic fading on ten markets at 6 trades a day: watching each alone took 179 days, pooling their trades took 51 (`m3_fleet.py` part D). So the unit must publish a family id. It already has one (`family_id` in the dummy template). **SEAT**: it must reach the rows.

## 1.5 One incident, one card

A shared bad session where 30% of units each lose six trades: as built, this adds about 3 cards at 20 units and about **29 cards at 200**, on top of the nightly noise (`m3_fleet.py` part E). With an event key it is one card listing the units.

Rules, from `X6` X6-16 and `X7` H17:
- One key, one window, one card, with every contributor listed. A repeat shows only if it worsens.
- **Known weak point:** a key can hide a second problem (X7 H17). So a unit whose fault doesn't fit the key's facts stays on its own card.
- **Trips are never folded.** Each unit's brake still acts. Only the telling is folded.
- The key must be written where the fault is seen, by the node or the script. **SEAT:** a free-text key field on `stand_down`, `risk_event` and order failure rows. Mapping keys to incidents is **CONTENT**.

## 1.6 Twenty against two hundred

| | 20 units | 200 units | Cause |
|---|---|---|---|
| Rows the decay job reads nightly (my arithmetic, this mix) | about 24,000 | about 236,000 | It rereads 90 days of trades. `journal_query` shows no row limit or roll-up in my search. Time and memory UNKNOWN; not measured |
| Same with the fold | 20 rows plus today's | 200 rows plus today's | The fold keeps running scores |
| Agent reads | K plus incidents | K plus incidents | Same at any size, by design |
| Digest | One screen | One screen, counts by state and family | His view can't grow |
| Finding a broken 6-a-day unit | About 5 nights | About 25 nights at K of 3 | Raising K buys speed with agent tokens. Family pooling helps both |
| Number moves | Few | Many; 21% to 45% of units moved a filter on the peak day of a shared volatility shift | See section 2.6 |
| Upgrades | Manual is possible | Needs a workflow | Section 4.5: a compiler bump means a new test record per deployed unit |

## 1.7 As a mini app

He asked for a workflow as a mini app, softly: "As a mini app or so." The honest state, read in code:

| Need | State | Evidence |
|---|---|---|
| An app ships a workflow | The manifest has `entrypoints.workflows`, but it's only checked to exist. My search of `qmx-agents\packages` found no installer | `qmx_apps\manifest.py:373` |
| An app reads journals | `data_reads` acts on `market` only | `qmx_apps\supervisor.py:891` |
| An app lands a card | An output lands as an `artifact` whose type is the contract's name. Whether a `proposal-card` from an app reaches the inbox: UNKNOWN | `qmx_apps\artifacts.py:1-20` |
| A guide for building one | Placeholder: "Pending authoring" | `qmx-agents\plugin\skills\build-mini-app\SKILL.md` |
| Risk label | `shows` fits. The `mis` app is the pattern | `qmx-agents\apps\mis\app.toml` |

**So:** build it as workflow templates in `T`, which work today, with a thin mini app as its face, reading what they land. Once the agentic upgrade gives apps those three doors, it moves whole. **CONTENT** plus **OTHER** (agentic upgrade). The unit's part is only the rows.

**Reuse map for the swap:**

| Template | Keep | Change |
|---|---|---|
| `dc-decay-and-limit-report` | Land step, grader | Replace the read rule with the fold, score and two lists. No nightly card per unit |
| `t7-trade-journal-review` | Digest counts | One paragraph per listed unit, not per unit |
| `dm-demo-monitor` | Fill counts | Slippage and latency once fill rows carry the asked price and time (its README says they don't) |
| `gw-guard-watchdogs` | All of it | Add equity and kill-line distance once rows carry them (its README lists this) |
| `rk8-incident-post-mortem` | All of it | Takes "the newest" incident; needs every incident in the window |
| `s2-tag-units-to-markets` | All of it | Counts toward the card budget |
| `morning-digest`, `pp-proposal-pack` | The cursor, the three-card shape | Takes the ranked list |
| `rk2`, `p2` | Later | Waiting on node reads and a broker token, per their READMEs |

## 1.8 What the unit must publish

All **SEAT**. Pulls together H4 section 4 and H3 section 5 with what the above needs.

| Row or field | Today | Needed for |
|---|---|---|
| Identity on every row: unit, version, compiled fingerprint, family id, free type tag, market, world | Most exist; type tag doesn't | Pooling, ranking, per-type views |
| State word with stamp and reason; UNKNOWN when stale | Node health only (`X6` X6-01) | Layer 1 |
| Decision row with closed, appendable reason codes | Built (`journal_kinds\unit.py`) | Skips, silence |
| Trade row: net and gross R, costs by kind, exit mechanism, MAE, MFE | `r` only, exits read `close` (H3 T62) | Cost cell, triage |
| Sizer receipt: real inputs, binding clamp, residue | Literal `"0/1"` (`qml\protocol\unit.py:827-830`) | "Why this size" |
| `would_have` rows | Kind declared, nothing writes them (`SWAP` row 29) | Brake scoring, evidence while stopped |
| `risk_event` rows | Placeholder kind | Brake fires against expected |
| Calibration rows | Built (`unit.py:855-872`) | Digest lines |
| Root-cause key, event id | None | One incident, one card |
| **An expectation at birth:** trade rate, spread of R, loss streaks, from the replay | None. Scripts can't read Library items, so the record is "the unit's own journal" (`dc` README) | A new unit has a baseline from its first day, and silence can be seen. Same data as the "find" step in section 2 |
| A fleet read: one query over all units | None; `units` is per node, `journal_query` is rows | Everything in 1.2. Agents otherwise read 200 units one at a time |

---

# 2. How a unit configures itself

His words: "How it configures itself... I don't think I have any opinion. I'm going to leave that part to you. Maybe double check, triple check... Have an agent go at it. More of a hill climb challenge." (M49) Earlier: "that number 5%, for example, has to have a reason as to why it's 5, not 10"; "it should have a range regardless"; "some are self-configuring, others are user-configured" (`RC\seeds\operator-words-2026-11-01.md`).

"Hill climb" has two readings, and I treat both. This section is the attack on the design (reading one). Section 2.5 covers the product job an agent would run (reading two, M50's blacksmith).

## 2.1 What already moves

Read at `W`. Fuller table in `SWAP` section 2.5.

| Kind | What moves it | Runs today for | Refused for |
|---|---|---|---|
| `fixed` | Nothing | Every number | |
| `derived`, `percentile_of_own_history` | The market: a percentile of a slot's output, each bar (`stdlib\percentile-of-own-history\1\block.py`) | Logic numbers (`rsi_low`, `rsi_high`) | Sizer, stop, target, per-bar exits (`compiler.py`, `_bound_on`); `scaled` and `state_table` are refused |
| `calibrated`, `shrink_from_own_trades` | The unit's closed trades: stamp and R, every N trades, only when flat, one step, in range, shrunk toward default (`motion\engine.py:127-159`, `trend-floor-from-record\2\block.py`) | Logic numbers (`min_trend_strength`) | Anything without a logic-slot stamp (`compiler.py:618-643`); `learned` |

**Code findings not on disk before:**
1. **The engine's memory never ends.** `SlowState.read` keeps every trade it has read (`engine.py:124`). All of it goes to the rule on each run and into every snapshot (`unit.py:356`). My cross-check held 1,602 rows after 3,000 signals. At 40 trades a day that's about 14,600 rows a year per calibrated number (my arithmetic). Every other block declares a `state_bound`. This one has no bound. The rule also can't forget: a year-old regime counts the same as today. **SEAT:** a bounded window.
2. **The built engine already is an applier.** Cadence, wait for flat, step limit, range, min count, journal row, restart survival. X1-H03 and R7 say "QMX has the learner and no applier", which holds for the `authority` field (one value, read by nothing) but not for the job.
3. **It sees only taken trades.** A floor gets no evidence below itself. Empty buckets count as fine (`block.py:64-67`), so it drifts down until a negative bucket stops it. This acts as cheap exploration, and it's why it does better than I expected in the tests.

## 2.2 The premise, and the census

**Premise, in every design from X1-H02 to the spine:** a unit configures itself by learning its numbers from its own closed trades.

**Census one: what the numbers depend on.** Of the 172 ledger v1 rows whose listed inputs I could classify, 119 read facts only, 30 read the unit's own record only, 23 read both (Temp `census.py`, rough pattern match over `RC\ledger\v1\variables.yaml`; 663 rows list no input or matched neither pattern). The dummy has 7 fixed, 2 derived, 1 calibrated.

**Census two: what own trades can afford.** Telling two settings apart by 0.05R takes about 1,600 trades, at a spread of 1R and about two standard errors. Arithmetic in the same form as `R3` section 1.1.

| Difference to tell apart | Trades | Days at 60 a day | Days at 6 a day | Days at 0.5 a day |
|---|---|---|---|---|
| 0.25R | 64 | 1 | 11 | 128 |
| 0.10R | 400 | 7 | 67 | 800 |
| 0.05R | 1,600 | 27 | 267 | 3,200 |
| 0.02R | 10,000 | 167 | 1,667 | 20,000 |

**Reading the skew.** Facts are plentiful and nearly free of noise. Own trades are scarce and noisy. So most self-configuration should never have been learning. Own trades got the whole role because "learner" was the first picture on disk, and VPA (the Kubernetes tuner R7 matched) learns from samples that arrive every few seconds.

## 2.3 Mechanisms compared

**Test one: a filter number.** The dummy's floor, range 0 to 0.0030. Score: R lost per 100 signals against the true best value. Lower is better.

**Controls, which X1's gap 8 said nobody had proposed:**
- **C-right:** fixed at the true starting value, a person who set it correctly.
- **C-wrong:** fixed at 0, the dummy's default.
- **C-walk:** random steps, same cadence as the engine.
- **C2:** the "find" machinery fed shuffled outcomes, so there is nothing to find.

**Mechanisms:**
- **M1:** the built engine. My fast copy matched the real `calibrate` and real block on all 80 runs of a cross-check (Temp `m1_selfconfig_floor.py`).
- **M3:** learner with bounds plus an applier with a dead band and split directions (X1-H02, H03), my implementation, one tuning.
- **M4:** rolling hill climb over recent replay.
- **M2:** facts alone: hold the same percentile of recent strength.
- **S:** one replay over earlier bars finds the number; facts then track volatility and cost; nothing else moves.
- **S+M1:** S, with the built engine still correcting from the unit's own trades.

Results (20 seeds; 16 for the flattering-replay rows, which also skip the columns left blank; standard errors are in `m1c_results.json`). W6 (regime flips) read like W5, and W8 (replay costs too low) equalled calm because the test's cost read repairs it, so both are left out here. Scripts: Temp `m1c_stack.py`, `m1d_attack.py`. All movers start from the wrong 0 except C-right.

| Style, world | C-right | C-wrong | C-walk | C2 | M1 built | M4c rolling | S | S+M1 |
|---|---|---|---|---|---|---|---|---|
| **Scalper** (60 a day), calm | 0.00 | 8.50 | 2.27 | 0.42 | 0.29 | 0.97 | **0.04** | 0.14 |
| Volatility doubles | 0.72 | 8.49 | 3.16 | 0.21 | 0.51 | 1.53 | **0.04** | 0.14 |
| Costs rise, seen | 0.15 | 11.32 | 2.98 | 0.24 | 0.32 | 1.13 | **0.04** | 0.07 |
| Edge fades, unseen | 0.30 | 10.01 | 2.99 | 0.21 | 0.39 | 1.22 | 0.34 | **0.12** |
| Edge never real | 0.00 | 9.98 | 4.32 | 0.00 | 0.78 | 1.00 | **0.00** | **0.00** |
| Edge not a straight line | 0.00 | 8.50 | 2.27 | 0.01 | 0.29 | 0.94 | **0.08** | 0.11 |
| Replay flatters the edge | 0.00 | 8.50 | | | 0.30 | | 1.44 | **0.17** |
| **Intraday** (6 a day), calm | 0.00 | 3.04 | 1.73 | 1.60 | 0.53 | 2.11 | **0.10** | 0.30 |
| Volatility doubles | 0.34 | 3.04 | 2.03 | 1.14 | 0.67 | 2.12 | **0.16** | **0.16** |
| Costs rise, seen | 0.39 | 5.33 | 3.17 | 1.06 | 0.81 | 2.79 | **0.11** | 0.17 |
| Edge fades, unseen | 0.33 | 3.87 | 2.43 | 1.06 | 0.72 | 2.48 | 0.38 | **0.21** |
| Edge never real | 0.00 | 2.99 | 2.40 | 0.09 | 1.28 | 2.13 | 0.10 | **0.07** |
| Edge not a straight line | 0.00 | 3.04 | 1.73 | 1.33 | 0.54 | 2.06 | **0.25** | 0.46 |
| Replay flatters the edge | 0.00 | 3.04 | | | 0.55 | | 0.73 | **0.24** |
| **Swing** (0.5 a day), calm | 0.00 | 1.88 | 1.68 | 2.07 | 1.41 | 1.88 | **0.93** | **0.93** |
| Volatility doubles | 0.22 | 1.88 | 1.75 | 1.55 | 1.59 | 1.88 | **0.75** | **0.74** |
| Costs rise, seen | 0.48 | 3.91 | 3.55 | 1.42 | 3.06 | 3.91 | 0.91 | **0.84** |
| Edge fades, unseen | 0.24 | 2.43 | 2.22 | 1.39 | 1.96 | 2.43 | 0.77 | **0.75** |
| Replay flatters the edge | 0.00 | 1.88 | | | 1.41 | | 0.67 | **0.53** |

**How to read it fairly.**
- In the scalper world, not trading at all is close to the best floor, because costs take most of the edge. That's why C2 scores well there: on shuffled data it often decides there's nothing to trade. Read the scalper rows against that.
- Facts alone can't rescue a wrong start: M2 equals C-wrong. My first round handed M2 the true start, which flattered it. I found that and reran it (section 5).
- The costs read in S is perfect in the test, so "costs rise, seen" is an upper bound. Real measured costs are noisier.

**Other results.**
- **M3, the learner and applier, adds machine and little gain.** Same starts, scalper: 0.34 against M1's 0.29 from a wrong start, 0.32 against 0.51 on a volatility shift, 0.25 against 0.40 on an unseen fade. Intraday it's worse: 1.25 against 0.51, 1.00 against 0.65, 0.96 against 0.70. Swing: 1.88, it never moves (Temp `m1_results.json`). Other tunings may do better; that's UNKNOWN.
- **Would-have rows don't belong in the live rule by default.** Feeding them to the built rule helps some shifts (scalper volatility 0.40 against 0.52) and hurts calm (intraday 0.73 against 0.21), and moves the number up to 13 times as often (Temp `m1b_variants.py`). Their value lies in watching and in replay.
- **A window alone gained nothing over 120 days** (Temp `m1b_variants.py`). It's still needed for the memory defect above.

**Test two: a size number.** The fair control here is the same multiplier series shuffled in time, so a mechanism earns no credit for simply being bigger. Score: return per unit of swing, against constant size. 200 seeds. Temp `m2_press.py`.

| World | Style | Constant | Shuffled | Own-record press | Same, with applier | Fact: size by volatility | Replay among 3 presets |
|---|---|---|---|---|---|---|---|
| No persistence | Scalper | 0.049 | 0.048 | 0.047 | 0.045 | 0.049 | 0.049 |
| | Intraday | 0.050 | 0.046 | 0.046 | 0.043 | 0.049 | 0.047 |
| | Swing | 0.053 | 0.052 | **0.033** | 0.036 | 0.051 | 0.043 |
| Good and bad runs, about 10 days each | Scalper | 0.056 | 0.051 | **0.096** | 0.095 | 0.055 | 0.056 |
| | Intraday | 0.056 | 0.053 | **0.070** | 0.051 | 0.055 | 0.052 |
| | Swing | 0.064 | 0.060 | 0.049 | 0.045 | 0.062 | 0.055 |
| Volatility swings, edge constant | Scalper | 0.037 | 0.035 | 0.038 | 0.038 | **0.053** | 0.037 |
| | Intraday | 0.036 | 0.035 | 0.034 | 0.031 | **0.052** | 0.034 |
| | Swing | 0.027 | 0.027 | 0.006 | 0.008 | **0.045** | 0.015 |

**What this says.**
- With no persistence, a moving size has no timing at all. Own-record press averaged 1.13 to 1.22 times the size, in line with the X1 roundtable's report of R9: "a 12 % size increase in disguise".
- With real runs of good and bad, own-record press is a large gain for a scalper and a modest one intraday. It's a loss for swing. His "the way you handle a scalper is going to be different" (M50) shows up in the arithmetic: a run of 10 days holds 600 scalper trades and 5 swing trades.
- The applier's cadence, counted in trades, hurt intraday: 20 trades is over 3 days of a 10-day run.
- The volatility fact helps every style, and costs nearly nothing when it isn't needed. **Caveat:** this world assumes R's spread moves with volatility, which holds only if the stop doesn't. A stop set in ATR already does this through the built sizer, because it divides by stop distance.
- Whether real units have such runs is the open question. It's **OTHER** (methodology and the numbers talk). The design need only make each case expressible.

## 2.4 The simplest thing that truly makes a unit self-configure

**Three jobs, in order. Each uses data suited to it.**

| Job | When | Data | Who does it | What it changes | Status |
|---|---|---|---|---|---|
| **Find** | At birth, in the Lab, or on demand | Years of bars through QMB | A script scores. An agent may choose what to try. Each try counted | Starting values and ranges: a new unit version with a reason on each number | Backtest, `qmb\optimize\study.py`, `d3` exist. Blocked on the workflow Library read |
| **Track** | Every bar or trade | Facts: equity, stop distance, value per point, volatility, spread, measured cost, session | Pure arithmetic in the unit, no learning | The number's live value, inside its range | `derived` runs for logic only. Needs `scaled` mode, `reads`, sizer and exit numbers |
| **Correct** | Every N trades when flat | The unit's own closed trades | The built motion engine | Moves inside the range, one step, journalled | Built for logic numbers. Needs a bounded window, an off switch, and to reach risk numbers |

**The test's clearest lesson.** Track alone can't fix a wrong start. Find alone is fooled by a flattering replay (scalper 1.44, intraday 0.73). Correct alone is slow, and nearly useless for swing. Together they held up across every world I tried. Correct's cost is some wander in calm conditions (scalper 0.04 to 0.14, intraday 0.10 to 0.30). This is the price of catching a replay that lied, and it's why it needs an off switch per type.

**What moves, from which data, under whose authority:**

| Number | Moves by | Data | Authority |
|---|---|---|---|
| Lots | Track | Money at risk, stop distance, value per point, lot step | Arithmetic. His "why lots" is answered by splitting the sizer: money rule first, a shared converter for each instrument's units (`H3` T4) |
| Money at risk per trade | Find sets it, track may scale it | Equity, cushion, volatility fact | **CONFIG:** pod or template. Value is the numbers talk |
| Stop and target multiples | Find, then track through ATR | Bars | Template's range. Correct only if the pod opts in; moving these changes what R means, so the row must record it |
| Filters, thresholds | Find, track, correct | Bars, own trades | Built path |
| Press and accelerators | Correct, per pod | Own trades | Pod setting. Off by default where trades are few |
| Cost gate, news window | Track | Measured spread, calendar | His M51 frame: "I'm trying to observe them, see what I can do" |
| Brake levels | Find, from the unit's own replay (loss streaks, spread of R) | Replay | Pod setting. This gives "why 5, not 10" a reason |
| Markets, sessions | Find, then `u1`, `u2`, `s2` | Replay, journals | Card, or a pod rule |
| Never-self-tune list | Nothing | | Per template, editable by the user (`H3` T29). **Fixed line:** the kill switch is lowered only by his hand |

**Authority rules, using what exists.** The identity table already says a move inside range is a calibration row, not a new version (`qml\identity\table.py`, `qmx_control\service.py:431`). A range change or a rule change is a new version. So:
- Inside the range, the unit may move by its own declared rule. No agent, no click.
- Outside it, a new version, a counted try, then the existing promote click.
- Agents write in the Lab and on cards, never on a running unit. Their output may reach a unit only as a fact it chose to read (`H4` I-52).

**What I would not put in the baseline** (**CONTENT**, all can be added later as blocks or pods without reworking the core): a separate applier part, dead band, retune share cap, target-with-bounds as a new status object, bandit over presets, pooled priors, Simplex fallback. Each is on disk (`X1` H02, H03, H08; `X2` H52, H53). The tests did not earn them a place. A rule block is any pinned block with the answer shape (`SWAP` 2.5), so direction-split motion ("size down, but not quickly") is just a rule, not a core change.

**SEATS this leaves in the core:**
- `authority` gets a real meaning: `off` (compute and journal, don't apply) and `motion_inside_range`. Room for `at_new_position` and period anchors, because "flat" doesn't work for a multi-position unit. Today `flat` means every market holds nothing (`unit.py:543`), and `cadence.at` refuses (`compiler.py:1008-1014`).
- A calibrated number need not have a logic stamp: the rule reads R alone, or a declared fact.
- A bounded window on the engine's memory.
- `scaled`: a derived number equal to a fact times a multiple. One block, with `reads` opened.
- A reason on every resolved value (`H3` T28), and `Origin` gains a value for "found by replay".
- `MotionSwitch` already lets QMB report with and without motion (`unit.py:97-101`). Report both, always. That's the fair control, built in.

## 2.5 The hill climb as a product job

An agent going at it, reading two, tested on the filter number (Temp `m1_results.json`, `m1c_results.json`):

| Climb | Scalper, wrong start | Intraday | Note |
|---|---|---|---|
| Small steps, honest guard (M4a) | 3.10 | 2.38 | Stalls. One step's gain sits below the noise, so no honest guard passes it. Built engine: 0.29, 0.51 |
| Small steps, no guard (M4b) | 1.08 | 0.96 | Moves, and wanders when nothing is wrong (0.14, 0.41 from a right start) |
| Whole range, recent window, guarded (M4c) | 0.97 | 2.11 | Better, still poor: a 40-day window is too little |
| Whole range, long history, once (S) | 0.04 | 0.10 | Works. Needs the flattering-replay correction |

**So a live climb on recent trades is the wrong place for it.** The climb belongs in the Lab, on long history, off the money path, with every try counted, ending in a new version. That fits his blacksmith picture (M50) and the existing door: `d3-iterate-against-qmb` proposes children, retests, and stops on a budget; `l4-overnight-lab-loop` runs overnight; `run_study_generations` drives trials (`qmb\optimize\study.py`). All wait on the workflow Library read. **CONTENT** plus **OTHER** (agentic upgrade, methodology for what counts as better).

**A warning from sources, not from me:** every LLM-found strategy failed certification with all tries counted in `2608.27734`, and simple controls beat 31 of 36 agent runs (H4 hard facts). So the agent's job is choosing what to try. A script scores it, and a shuffled-outcome control runs beside it.

## 2.6 Help or harm by style

| | Scalper | Intraday | ORB and event units | Swing |
|---|---|---|---|---|
| Find | Helps, plenty of history | Helps | Inferred: helps, few signals per day, pool across opens (`X5` H40) | Helps most; nothing else can do this job. Still weak at 360 signals (0.93) |
| Track | Helps; costs matter most | Helps | Inferred: volatility and session facts fit | Helps |
| Correct, filter | Helps on unseen shifts (0.34 to 0.12), costs a little in calm | Same, smaller | UNKNOWN, not tested | Does nothing useful: about 2 moves in 120 days |
| Correct, size press | Large gain if runs exist; small harm if not | Modest gain, harm if cadence is long | UNKNOWN | **Harm**. Default off |
| Cadence | In trades, short | In trades, shorter than a run | Calendar | Calendar |

These defaults are **CONFIG**: per-type presets. The core needs a free type tag and presets as data (`H4` section 4), never a fixed list of types. M49: "those are like four different types of units".

**Herding,** at 200 units with one shared volatility shift, intraday (Temp `m1b_variants.py`, 6 seeds):

| Rule | Peak share of units moving in a day | Lost, no cap | Lost, 10% daily cap |
|---|---|---|---|
| Built engine | 21% | 0.66 | 0.82 |
| Facts, percentile | 45% | 0.15 | 0.17 |
| Learner and applier with would-have rows | 9% | 1.03 | 1.05 |

A daily cap only delayed a correct response, so it costs a little and I see no case for it in the baseline. **Limit:** this is a filter. Many units cutting or raising size together is a book-level matter this test doesn't reach. So the share cap stays possible as a pod rule, and X1's herding question stays open for sizes. The core needs a place for a group-level rule, not this rule.

---

# 3. A newcomer's first day

His words: "Someone who hasn't been part of developing KMX can use tomorrow to have their own system trading" (M49). "anyone can use, you know, like right out of the box" (M49).

**The premise to attack is "tomorrow".** The walk below needs an outside approval of about a day before any demo order. So the honest target is: **day one, a unit tested on history and on replay; day two, on paper with a broker.** The walk is on paper. I ran nothing. Scope: technical path; UI is judged by code here, and it's another session's.

| # | Step | What exists | Gap | Kind |
|---|---|---|---|---|
| 1 | Get QMX | `tools/build_release.py`, `release/install.py`, CPython 3.14, `uv`, `npm` needed to build | **G1.** No installer a stranger can run. `release\README.md` is a release-candidate note ("does not certify"), says native Windows is "NOT RUN", and describes `qmb host start` | **OTHER:** release, but it's the first wall |
| | | `install.py:28-43` lists qmf, qml, qmb, qmn packages and no `qmx_` one, though the builder also builds `qmx-agents` | **G2.** Install and launcher describe the older host, not `python -m qmx_host`. Whether the bundle installs a working host today: UNKNOWN | **OTHER** |
| 2 | First start | `python -m qmx_host first-start`: new folder, open, restore, bring in. Refuses sync folders and network drives. Solid (`qmx_host\first_start.py`) | **G3.** It hands over "to the desktop app". `UI\package.json` shows no Tauri or Electron, and I found no such folder. Which app a stranger opens: UNKNOWN | **OTHER:** UI |
| 3 | Open the UI | Four steps: broker, model, data, first strategy or pod (`UI\src\lib\workbench\day-one.ts:100-127`) | **G4.** A step "ticks off once opened" (`GetStarted.svelte:3`), not when done. **G5.** With demo off "nothing ever has content yet" (`UI-LEDGER.md:321`); the UI branch is separate from `W` and unwired | **OTHER:** UI |
| 4 | A model | Provider sign-ins, router, a plan you already pay for | Not traced end to end for a stranger's account: UNKNOWN | |
| 5 | A broker | Connect dialog (`qmx_host\connect_node.py`): cTrader app request, keys, clock, install, signature, sign-in, self-test, passport. Waiting steps don't block others | **G6.** Spotware approves the app "about a day" (`connect_node.py:8-9`). **G7.** Never run against a real broker; R24's lanes wait for his sign-in (`MAP` section 1). cTrader only for orders | Outside, plus repair |
| 6 | Data | `download-dukascopy`, `download-ccxt`, `download-binance`, instrument records through the node's `records` | **G8.** Instrument records come from a bound account, and `unit_check` needs a record per market. Can a newcomer backtest before a broker exists? UNKNOWN; I did not trace it | **SEAT** if the answer is no: the first day should not need a broker |
| 7 | A unit | `unit_new`, `unit_check`, `unit_explain`, `blocks_*`, the `build-unit` skill, a Write hook | **G9.** One template: a dummy trend pullback (`qml\unit\templates\`). **G10.** A copilot has "no real risk choice to make from the shelf" (`SWAP` section 3): halts, reads, sessions as a field, other exits all refuse. Adding a JSON file there makes a template with no other change (`SWAP` section 3), so templates are cheap once sockets exist | **SEAT** then **CONTENT** |
| 8 | Size and brakes | `fixed-fraction-at-stop`, a labelled placeholder. Nothing else | **G11.** The swap this session plans. A newcomer needs a working default, and one screen saying what it does | This session |
| 9 | Test it | `backtest_run` links a G test-report (`functions.py:802`), `judge_run` gives a verdict. R14: a chat on haiku builds, checks, backtests, gets a verdict | **G12.** The skill still says "You never publish, test..." (`build-unit\SKILL.md`), against the tools. **G13.** The dictionary's risk blocks cannot be tried | **OTHER:** agentic upgrade |
| 10 | Save it | His yes publishes; a card | "He", "his" and "the operator" run through skills and persona. **G14.** A stranger reads someone else's rules (`plugin\QMX.md`, `qmx-overview`). Wording, but it's every first impression | **OTHER** |
| 11 | Paper | `POST /api/units/promote`: needs a passing G test-report, not a judge verdict (`promote.py:10-12, 569`). This fits M49: "I can have a unit made through the lab... those are like four different types of units. All of them can trade" | Node needs a binding; paper "ends at its paper account beside the binding" (`runtime.py` head). `first_real_start.py` says a unit needs the judge; the code checks only G. Docstring is stale, or I misread it | Note only |
| 12 | Watch it | Separate morning templates, each installed and enabled by hand ("enabling it is yours", `morning-digest` README) | **G15.** Section 1. Nothing joined; no one-click "watch my units" | **CONTENT** |
| 13 | Live | His click, a "deliberate live path", placeholders must be acknowledged (`promote.py:382-394`) | Exists. Equity read once at sign-in (`MAP` section 2). **G16.** Cost and fact feeds absent | Socket work |
| 14 | Customize | Library kinds `template`, `pod`, `book`, `bms` are empty shells (`SWAP` section 3). Lab: no pods. "New pod" sends a sentence to the copilot (`day-one.ts`) | **G17.** See E2 | E2, Lab |

**Count: 17 named gaps.** Six belong to this session or to its sockets (G8, G9, G10, G11, G13, G16). The rest belong to release, UI, agentic upgrade or repair.

**What the baseline must carry for this walk:**
- **Working templates per type:** at least a scalper, an intraday, an opening-range and a swing shape, each compiling and passing G on synthetic bars. Not validated strategies, which is methodology. Each says plainly "this is a shape, not an edge" (his M49 correction: "we don't have any proof").
- **A default size and brakes that run,** with reasons on each number and a range, so a newcomer sets nothing to get to paper. **The values wait for the numbers talk**; any labelled default works until then, as he said: "something that can work even if we don't have the numbers set yet" (M50).
- **A walk that's a test.** `tools/first_real_start.py --rehearsal` already runs setup on a throwaway folder with a fake cTrader. Extend it: from template to check, backtest, promote to paper, one trade on the journal, one row in the fleet fold. If this test passes, the newcomer's walk holds, and it can't quietly rot.

---

# 4. Maintainability

His words: "And it's maintainable, please. From a developer's perspective, there are lots of things you were meant to add. I don't know how you didn't do this." (M52)

**The premise to attack is "maintainable means a guide".** A guide helps, but it rots: `docs\AGENTS.md` still opens "QMF V1... not itself a trading application" and was last verified 25 Sep. What lasts is structure: a new block that breaks a contract fails a test without anyone remembering. Much of that exists. So: extend the structure, and generate the guide's facts from it where possible.

## 4.1 Module map

| You want | Go to | Note |
|---|---|---|
| The document shape | `qml\src\qml\unit\model.py`, `parse.py`, generated `qmx.unit.1.schema.json` | One JSON document |
| Checks | `qml\check\layers.py` (B to F), `numbers\check.py` (C), `check\layer_g.py` (G, on a recorded slice) | Heuristics warn, facts error |
| What runs | `qml\compile\compiler.py` (1,104 lines), refusals in `_shape_problems` | A refusal names what isn't built |
| The unit at runtime, one handler for both hosts | `qml\protocol\unit.py` (1,134 lines) | Exits, entries, motion, receipts |
| Block contract | `qml\blocks\api.py`, `blocks\stdlib\<id>\<v>\` | |
| Motion | `qml\motion\engine.py` | Pure function |
| Identity, upgrades | `qml\identity\`, `qml\unit\upgrade.py` | |
| The door | `qml\door.py`: `new`, `check`, `compile`, `find`, `explain` | Pure; host passes data |
| Backtest host | `qmb\src\qmb\host\unit_handler.py` (727 lines), `unit_runner.py` | |
| Node host | `qmn\src\qmn\app\runtime.py` (3,161 lines), `stand_down.py`, `server.py` | Biggest file a risk change meets |
| Journal kinds, reason codes | `packages\qmf-data\src\qmf\data\journal_kinds\unit.py` | Closed, appendable |
| Agent tools | `qmx-agents\packages\qmx-control\src\qmx_control\catalog.py`, `qmx-tools\functions.py` | One row per tool |
| Workflows | `T`, `_shared\` | |
| Apps | `qmx-agents\packages\qmx-apps`, `qmx-agents\apps\`, `examples\apps\` | Examples run in CI |

**A trap for anyone arriving.** There are two risk worlds. `packages\qmf-risk` holds older sizing, control and exit modules, still imported by `qmb\results\accounting.py`, `qmn\capital\*`, `qmn\protection\*` and others. The new risk runs through QML blocks. Nothing tells a developer which to use. **SEAT:** a one-line statement per module, and a plan to subtract what the swap retires. `qmn\capital\kill_line.py` isn't on the path at all (`MAP` section 2).

## 4.2 Adding things: today against what's needed

| Adding | Steps today (`SWAP` section 2) | What bites | Needed |
|---|---|---|---|
| **A logic block** | `block.py` plus `entry.json`, `stdlib` folder or Library `component`, dictionary page, golden case. Auto-enrolled. `blocks_check` for agents | An agent can check but not save: "No row saves a new entry yet" (`build-unit\SKILL.md:59-62`). QML sits in the node's lock, so a stdlib change bumps the money app and needs his signature | A save row; a scaffold; a Library path traced end to end (today UNKNOWN) |
| **A sizer** | Same, with `component_type: sizer` | A sizer's face isn't checked: a trigger-shaped block compiles (S3). 5,000 lots passes the QML host (S1c). A moved number arrives in `evidence`, while `make` holds only the start, so copying the placeholder ignores motion (M6). No side passed. No inputs allowed | Face check by shape. Sizer answers money, a shared converter gives lots, with limits in one place. Copyable reference block that reads `evidence` |
| **A brake** | Can't. Five shipped halts refuse (`compiler.py`, `halts_not_built`); no host computes their statistics | | A host that runs them; a "required statistics" list (`R7` 7.1, Bevy); each block declares what it reads; `would_have` for shadow |
| **An instrument class** | `InstrumentClass` enum in `qml\numbers\records.py`; instrument record keys; calendar package under `extensions\` (four exist); venue adapter (cTrader only); cost profile and margin rule in QMB; `packs.json` for MIS. Roll refused | Good news: in `qml`, `qmb`, `qmn` and `qmx-agents` source, I found `instrument_class` read in only two files, so behaviour lives in record keys, not branches. Keep it so | **SEAT:** a test that fails on branching by class in the money path. A "needs list" per block (`H3` T18) and two-adapter contract tests per class |
| **A number that moves** | `numbers` entry, `motion` block | Section 2.1 | Section 2.4 seats |
| **A check layer** | `check\layers.py` | Checker stops at F | Layers open to additions (`X7` H30) |
| **A tool for agents** | One catalog row | Tools declare approval, not direction (`catalog.py:26`) | **OTHER** |

## 4.3 Contract tests

**Exists, and worth keeping:**
- `qml\tests\test_socket_contracts.py`: every shipped sizer, exit or halt enrols by itself.
- `test_every_field_of_the_schema_is_in_the_census` (`test_unit_refuses.py:457`): a new schema field fails until someone decides run, refuse or label.
- Golden tests per family (`test_wave1_exits.py:143`), upgrader rule at import (`unit\upgrade.py`).
- Layer F source scan, layer G determinism and restore.
- `tools\qml\placeholders.py`, the rip-out list.
- `test_shipped_apps.py`, examples in CI.
- Failure register convention: a designed failure with no entry is incomplete (`conventions\failure-register.md`).

**Missing, in order:**
1. **Same decision in both hosts,** by socket: a table of block, bar sequence, expected answer, run through QMB and the node. Today's differences (partial closes, stops past entry, target held by the node) are listed only in `SWAP` 2.6. Make each one an explicit test with a reason.
2. **Exits never blocked,** as a property: any failure in guard, sizer, reads or fold still lets a close through. `CHECK` B3 found this was a real risk.
3. **Every refused field is either running or labelled.** Exists as the census; extend to `authority` and `reads`.
4. **Every number has a reason and range,** at check. Layer C warns on some origins.
5. **Motion:** range, step, flat and bounded state, per mode. Plus a shuffled-outcome control run, using Temp `m1c_stack.py` as a start.
6. **Every template reaches paper** on rehearsal.
7. **No agent path to money,** by tool table. The `money_path_scan.py` tool exists.
8. **Fleet row:** `RiskState` from one fold in every reader (`H3` T59).

## 4.4 Debugging a size, and logs

**His question will be "why this size?" Today:** the receipt says `inputs_used` the four names and residue `0/1`, whatever happened (`unit.py:827-830`, `SWAP` S1b). A sizer's skip reason survives, and the decision row and reason codes are good. A developer can use `TraceLevel.EVERY_BAR` and rerun in QMB, if they can reproduce the inputs. Nothing stores them: "Schema has optional slots. Nothing writes them" (`SWAP` 4.1 row 15).

**Needed: one decision row that replays.** **SEAT.**
- The row stores: inputs with their timestamps, resolved numbers each with a reason (`user`, `default`, `calibrated`, `stale_so_default`), each step wanted to approved to filled, the binding clamp, the version and compiled fingerprint.
- `explain_size(row)` is a pure function reading it, used by a developer, the copilot, the UI and the triage agent alike (`H4` I-41, `X6` 9.15).
- A test: replaying the row through the block gives the same size.

**Logs and journals are already separated, correctly.** "Logs ≠ journals" (`qmn\observability\__init__.py`). JSON lines, forbidden keys for secrets, one log context (`logging.py`). Journals are evidence with closed kinds. Keep both. Add:
- One trace id from reading to fill, on rows and logs.
- Applier and motion counters (X1 gap 12) as plain rows.
- A choice of observability stack: `X6` Q4 and DEC-0212 against OpenObserve remain unresolved, and `HOST_SECRETS` names OpenObserve. **OTHER**, with a note that risk rows are evidence and may not be dropped. Retention on a server at scalper rates is unmeasured (`X6` gap 7).

## 4.5 Versions and migrations

**The biggest hidden cost.** `COMPILER_FORMAT_VERSION` is 4. A bump moves every unit's compiled fingerprint, and the node refuses a fingerprint its G record didn't test (`SWAP` 2.3; `runtime.py:559-565, 2756`). At 200 units, each bump means 200 new test records. So:

1. **Widen all sockets in one bump.** The funnel should treat this as a sequencing rule. Sizer inputs, reads, exits, halts, motion on risk numbers, sessions, receipts and multi-position all change compile. A slice-by-slice build meets this cost repeatedly, unless units aren't yet deployed. None are today, so **the cheap moment is now.**
2. **A re-test workflow** that reruns G per unit after a bump, and reports which changed behaviour. **CONTENT**, needed by 200 units.
3. **Pins with diffs and lineage** (`H3` T9, T52), and a forwarding map for block versions (`R7` 7.3, Simulink), so a placeholder swap needn't cost a unit its record (`SWAP`, identity table).
4. **Keep what's built:** the upgrader chain, the "newer than I read" refusal, snapshots of another state schema restoring cold (`upgrade.py` head). A cold restore loses calibrated values, so the journal's calibration rows must be able to rebuild them. Whether they do: UNKNOWN.
5. **A file extension.** He doesn't mind one (M50: "I don't care"). `qmx.unit/1` as JSON with a `.unit` or similar name is a one-line **CONFIG** of tooling, and no core change.

## 4.6 A single guide, generated where possible

`qml\EXTENDING.md`, short, one page per thing added, each ending in the test that proves it. **Generated:** the socket list, refused fields with reasons (`_shape_problems`), block shapes, reason codes, journal kinds. **Written:** why, and the traps in 4.2. A test fails if a generated part is stale. **CONTENT**, but scheduled with the swap because the swap's builders need it first.

---

# 5. Grilling my own drafts

Nobody was available, so I answered from the record. Where the answer changed the draft, I say so.

| Question | Answer | Changed? |
|---|---|---|
| Did I hand my favourite the right answer? | Yes, in round one: M2 and C0 started at the true value. M2's 0.07 on a wrong start was false. Reran with one shared wrong start | **Yes.** Facts alone equal C-wrong |
| Is the world built to suit facts and straight lines? | Partly, I wrote it. Added a non-line world, fat tails, and shuffled-outcome controls. S held up on non-line and fat tails | Numbers kept, caveat stated |
| What beats S? | A flattering replay, in W10: 1.44 for a scalper. It lost to the built engine | **Yes.** Recommendation moved from S to S+M1, and the motion engine stays |
| Is "R lost" a dollar target in disguise? | No account, no compounding, no go-live, and it measures distance from a known truth. Nothing was admitted or dropped because of it; labels come from the brief's test | No |
| Did I cut the applier because it's tidy? | Partly. M3 is my own tuning, so "others may do better" is stated. But the code finding stands on its own: the engine already does the job | Worded down |
| Does cutting the share cap ignore a real herd risk? | For filters the test says no. For sizes it wasn't tested | **Yes.** Limited the claim; room for a group rule stays |
| Is a nightly K of 3 going to starve a real problem? | With five real problems, yes for a while. The strict bar bypasses K, K is a setting, and overflow is a digest line | Stated |
| Does the watch need him? | Only for cards he wants. Units run under pod rules. "Anything that needs him to monitor is wrong by default" (brief) | No |
| Did I slip a policy question in? | Checked: what a rule may do, K, bars, cadence, who resumes, are all marked CONFIG. No question to him here | No |
| Is the mini-app claim fair? | He said it softly ("or so"). I checked the doors in code instead of assuming | **Yes.** Workflow first, app as face |
| H4 says 10x units means much slower demotion. True? | Measured: 30% to 135% slower for active units, up to 5.6 times for the slowest | **Yes.** A correction |
| Is `first_real_start`'s "passing the judge" true? | The code path I read checks a G report only. I did not read the node's whole accept path | Marked as a note, not a finding |
| Did I measure what I think on the 91 cards? | The rule is copied from `read.py`. The trade stream is mine. With a stronger edge, fewer cards; that changes the count, not the shape | Stated as a test setting |

**Not verified:** nothing was run against the real hosts except `calibrate` and one block. No real market data. Results for ORB and multi-position units are inferred or absent. Time and memory for journal reads at 200 units are not measured. Windows behaviour of any new piece: not checked.

---

# 6. Flaws for the agentic upgrade session

| # | Flaw | Where | What it blocks |
|---|---|---|---|
| 1 | `build-mini-app` skill is a placeholder | `plugin\skills\build-mini-app\SKILL.md` | Every agent-built app, including the fleet face |
| 2 | An app's `workflows` entrypoint is checked for existence, and I found nothing that installs it | `qmx_apps\manifest.py:373` | "Agentic workflow as a mini app" |
| 3 | An app's `data_reads` acts on `market` only | `supervisor.py:891` | An app reading journals |
| 4 | App to inbox path unconfirmed | `artifacts.py`, `X7` H36 | App-raised cards |
| 5 | A workflow script can't read Library items | READMEs of `dc`, `dm`, `s2`, `s4`, `d3`, `l4`, `rs6`, `u4` | Baselines at birth; all hill-climb jobs |
| 6 | Cron has no per-market clock; a landing event names no unit; no event triggers from the node | READMEs of `t7`, `dc`, `rk2`, `pp` | Per-market and per-trade triggers |
| 7 | No fleet read; `journal_query` shows no limit or roll-up in my search | `qmx_tools\journals.py`, `catalog.py:341,373` | 200 units |
| 8 | No attention budget across templates; one card per flagged unit; only `pp` limits itself | `dc` `land.py`, `pp` README | His inbox |
| 9 | Card asks are a closed list: paper, live, admit, drop, tighten, bench. No "look at this", no incident | `kinds\proposal-card.schema.json` | One incident, one card |
| 10 | A `tighten` card doesn't say what to tighten | `dc` README | A click he can make |
| 11 | No save row for blocks | `build-unit\SKILL.md:59-62` | QML growth |
| 12 | One unit template | `functions.py:811-812` | Type templates, M50's copilot use |
| 13 | Skill says never test; tools and R14 do | `build-unit\SKILL.md`, `MAP` section 3 | Agents following the skill stop short |
| 14 | Judge lands as the operator (H4 section 6) | `functions.py` near 688 | Agent report cards |
| 15 | Tools declare approval, not direction | `catalog.py:26` | Safe widening |
| 16 | No triage job, no fixed cause list in any prompt | `T` | Layer 4 |
| 17 | Replay of past runs isn't built, so every edit is "untested" | `rv-weekly-review` README | Agents improving themselves |
| 18 | Skills and persona speak of one person ("his yes") | `plugin\QMX.md`, skills | A stranger's first day |
| 19 | Copilot isn't told about Lab pods; Lab "on no model's surface" | `qmx_control\lab.py` | Pod building by copilot |

**Already good, don't rebuild:** the `monitor` node, receipts grader, zero-token quiet paths, `proposal: true` landings, operator-only promote, `ev-copilot-eval-battery`.

# 7. Hand-offs

- **Methodology:** what counts as "better" in a climb; whether real units show runs of good and bad; per-type start-to-finish; reading detectors and fair controls. Scripts in Temp are a starting kit.
- **Numbers talk:** K, bars, baselines, default size, press strength. All values here are test settings.
- **UI:** tiers against Settings' "Alert me when"; first-run ticks on done, not opened; one fleet screen; an explain-size panel; the walk's wording for strangers.
- **Repair:** nothing asked. Flagged only: `SlowState.read` has no bound (`engine.py:124`), and it reaches snapshots.
- **Release:** G1, G2, G3.

---

# 8. What the unit baseline must carry

All **SEAT**. Leave them out and the core gets reworked. Values aren't argued.

**Self-configuration**
1. Numbers on any socket can be `derived` or `calibrated`, not only logic numbers: sizer, stop, target, per-bar exit, halts. (`_bound_on`, stamp search.)
2. `reads` open, with a timestamp and declared fail mode per input (`H4` section 4), so numbers can read volatility, spread, measured cost and session.
3. A `scaled` motion block: fact times a multiple.
4. The motion engine: a bounded memory, `authority` with a real `off`, a stamp no longer required, room for non-flat anchors and calendar cadence.
5. A reason on every resolved value; `Origin` value for "found by replay"; a range on every number.
6. A sizer that answers money, a shared converter to the instrument's quantity. Answers "why lots".
7. Report with and without motion, always (`MotionSwitch` exists); room for a shuffled-outcome control.
8. A never-self-tune marker on a number, the list being per template.
9. An expectation at birth stored with the version: trade rate, spread of R, streaks, from replay.

**Watching**

10. Identity on every row, including a free type tag and family id.
11. State word with stamp and reason, UNKNOWN when stale; a state input the guard reads that refuses entries and never exits.
12. Trade row with net and gross R, costs by kind, exit mechanism, MAE, MFE.
13. `would_have` and `risk_event` rows actually written.
14. A root-cause key and event id on failure and stand-down rows.
15. One fold, one fleet read across all units, scoped by unit, family, pod and account.

**Newcomer**

16. Working template per type, each compiling and passing G, each saying it's a shape and not an edge.
17. A default size and brakes that run with nothing set, labelled, with reasons.
18. First day doesn't need a broker for history and replay (if it does today: G8).
19. The walk as a rehearsal test.

**Developer**

20. All socket widening in one compiler bump, before units deploy.
21. A decision row that replays, and one pure `explain_size`.
22. The contract tests in 4.3, starting with same-decision-both-hosts and exits-never-blocked.
23. A face check on sizers, and limits in one place.
24. One statement per risk module saying which world it belongs to; subtract what the swap retires.
25. A block save path, and a pin plus forwarding map so a swap keeps a unit's record.
26. A generated extension guide with a staleness test.
