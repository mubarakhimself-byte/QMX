# Experience pass: problem solving on the five weak spots

Written 2026-10-31 by agent F2. Index and lead's calls: `design-thinking.md` in this folder. His ruling 2 (STATE midday): the lead solves the weak spots itself and reports them in a line. His words: "So what I'm saying is try maybe solving the weak spots in your own way." (T3:1264). So each spot ends in one recommended solution the architecture can adopt, with the part it lives in, what it reuses, and the deterministic check that proves it.

## How this file was made

- **Skill.** `bmad-cis-problem-solving`, headless, YOLO at the first checkpoint, all nine steps. Its workflow block resolves to no prepend or append steps, no persistent facts and an empty `on_complete` (CHECKED, `uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-cis-problem-solving --key workflow`). Output moved from `_bmad-output` to this folder; template emojis dropped.
- **One problem set, five spots.** The skill works one problem at a time. The five spots share one root (see Step 3), so they run as one session with a row per spot in each step.
- **Labels.** As in `design-thinking.md`: CHECKED (path and line, a run, or CHECKED in a cited grounding file), INFERRED. Quotes are his words only, script-checked (last section).

The five spots, as the brief names them:

| Id | Weak spot |
| --- | --- |
| WS1 | The two speeds of self-tuning |
| WS2 | Placeholders that cannot show tuning |
| WS3 | The market-picking trap |
| WS4 | The unit-to-MIS connection in code |
| WS5 | Starting a node and seeing it run |

---

## Step 1. Define and refine the problem

**Problem title.** The unit's central claims are not yet visible or provable in daily use.

**Category.** Product design across QML, QMB, the MIS and the trading node; no sizing maths.

**Initial problem, in his words.** "A unit, it is self-optimizing, it's relying on very few things" (T3:1145). "When I say it works, I mean, does a unit actually make sense?" (T3:1145). "How, in terms of code?" (T3:903). "is it going to start as server, then show me that the server has started?" (T3:1102).

**Refined statements.**

| Id | What exactly is wrong | Gap between now and wanted |
| --- | --- | --- |
| WS1 | A unit's numbers move for two reasons at two speeds. Numbers that read the market (a stop at 1.5 × ATR) can change every bar and need no trade count. Numbers that read the unit's own record (a risk fraction, an entry threshold) need tens to hundreds of trades. Nothing records which number moves, by what, how often, or who allows it. Today live seats run only default numbers, and a tuned set mints a new bot (`qml/src/qml/declaration/bot.py:618-628`, G1 §1.4) | Now: numbers are frozen or re-minted. Wanted: each number says how it moves; slow moves are bounded, counted, journaled; he can read why |
| WS2 | Sizing and exits are placeholders by his ruling: "placeholders, I think is the right word" (T3:1087). A placeholder that never moves cannot show the unit tuning itself | Now: no mechanism, no stand-in. Wanted: the real mechanism with stand-in formulas that really move, labelled so the risk session rips them out by query |
| WS3 | When a unit is tried on many markets, sessions or hours, the best-looking one is partly luck: in research 24's simulation the best of 20 looked +0.23R and was truly +0.06R (STATE research table, CHECKED there). A raw ranking on any screen or shortlist lets luck reach his card | Now: nothing judges markets. Wanted: one rule fixed before results, results pulled toward the whole, every market a try, a forward check before his card |
| WS4 | He asked how a unit connects to the MIS in code. Today the MIS lives only inside the node and publishes to the Book door and the kill switch, "never bots" (`qmn/src/qmn/mis/signal_snapshot.py:1-4`, G1 §6.1); QMB imports nothing from the node, so backtest trades carry no readings | Now: no connection. Wanted: a unit reads readings the way it reads prices, never waits for the MIS, and gets the same values in backtest and live |
| WS5 | No shipped path sets up a trading node: the connect dialog has storage, compute and deep logs only (`qmx_host/connect.py:389`, G3 §1.4); the node's only profile is offline replay (G3 §1.1); it never ran (G4a §2.2) | Now: no node can start. Wanted: one click, named steps, a self-test, one word that says it is ready, healing on its own, visible from his PC |

**Success criteria.** Each spot has a solution that (1) handles the hard cases fully, (2) can be maintained and debugged, (3) can be explained to him in a few plain sentences (standing order 6), (4) changes legacy code only where needed, with the reason in a line (ruling 32), and (5) is proved by a script, never by an agent's word (standing order 18).

---

## Step 2. Diagnose and bound (Is / Is not)

| Id | Is | Is not |
| --- | --- | --- |
| WS1 | Numbers inside a unit's rules; both backtest and live; per deployment | Changing the rules themselves (that is a new version by his click, research 53 §3.2); the sizing formulas (risk session) |
| WS2 | The mechanism of motion and its labels; the dummy unit | The risk session's maths; anything that reaches a live account |
| WS3 | Markets, sessions, hours and weekdays chosen from results; agent shortlists | A unit with one declared market from the start; his own manual choice of markets (still shown with honest numbers) |
| WS4 | Condition inputs a unit reads per bar; the history QMB replays; what templates read | The MIS's models (his to train later, `M-02`); the router (gone, `M-05`); risk inputs |
| WS5 | Setup, self-test, states, healing, visibility from the PC, the PC placement and the server placement | Order logic, the kill-switch maths, the venue clients (node lens); sign-in with him (later, ruling 37) |

**Pattern.** All five sit where something moves on its own (a number, a market choice, a reading, a process) and he must still be able to say why. INFERRED.

---

## Step 3. Root cause analysis

Methods from `solving-methods.csv`: Five Whys (WS1, WS2), systems thinking (WS3), fishbone (WS4, WS5).

### WS1, Five Whys

1. Why can he not see a unit tune itself? No number says how it moves.
2. Why? QML's parameter space carries type, bounds, step, default, unit kind and a UI flag, and nothing about motion (G1 §1.9).
3. Why? In the April design the Book owned money and exits; tuning was offline optimisation that minted a new bot (G1 §1.4).
4. Why was a tuned set a new bot? To keep identity exact: the fingerprint covers the values.
5. Why does that block units? The unit is "a self-configuring trading bot" (T2:788). Identity bound to values forbids motion.

**Root cause.** Identity is bound to values instead of to the rules that move values. Put the motion rule and the range inside the identity, and values may move inside them without a new version. INFERRED.

### WS2, Five Whys

1. Why can the placeholder unit not show tuning? Its sizing and exits never move.
2. Why? Self-tuning was only ever described through sizing (house money, the Kelly ceiling, size growing back; explainer round 1 "What the calibrator tunes (v1)").
3. Why does deferring sizing defer the proof? The mechanism and the formula were never separated.
4. Why not? Nobody built the mechanism; it lived in prose.
5. Why does it matter now? His proof is a dummy unit on the real template, shown working (`CC-17`).

**Root cause.** Mechanism and formula were one idea. Separate them: the mechanism is real now; the formulas are labelled stand-ins. INFERRED.

### WS3, systems thinking

- Reinforcing loop: more markets tried, a higher best result, more attention to the best, more promotion of lucky picks, live disappointment, more trying.
- Missing balancing loop: a count of tries, a pull toward the whole, a forward check, and a score on every shortlist.
- Leverage point: the number shown. If the only number any screen or agent sees is the judged number, the reinforcing loop has nothing to feed on. INFERRED.

He knows the trap: "I get this logic. I know probability of overfit." (T2:219). So it is design, not a question (ledger "Settled", last row).

### WS4, fishbone

| Bone | Cause |
| --- | --- |
| Process | The MIS was designed for the Book door and the kill switch, "never bots" (G1 §6.1) |
| Technology | MIS code lives only inside the node; QMB cannot run it (G1 §6.1) |
| Materials | No reading history exists; nothing stamps readings on trades (G1 §7) |
| Methods | No rule says what a unit does when a reading is missing |
| Environment | The node-to-PC link is missing (G4b Q6), so templates cannot read readings either |

**Root cause.** Readings were an output to one consumer, not an input any unit can declare. INFERRED.

**A code fact that makes the fix small (CHECKED).** QML's runtime seam already takes host-injected inputs per declared key: `BotFactory.construct(*, declaration, assignment, read_surfaces: Mapping[str, ReadSurface])`, and `ReadSurface.at(instant)` returns "Evidence knowable at ``instant`` from one declared footprint key" (`qml/src/qml/protocol/__init__.py:111-140`). Every sample carries a presence state, one of `present`, `provisional`, `not_ready`, `gap`, `absent_by_schedule` (`qml/src/qml/protocol/evidence.py:73-84`), and a `knowable_at` instant; look-ahead is refused (`evidence.py:588-596`, G1 §1.4).

### WS5, fishbone

| Bone | Cause |
| --- | --- |
| People | No session owned the node after 4 Oct; the planned node session never ran (G4a §0 item 1) |
| Process | Built by the factory with proof campaigns and readiness packets, about 11,900 lines (G4a §2.2) |
| Technology | Linux-only supervision, powers door and secret store; no live profile; its own Grafana stack (G4a §2.2, G3 §5) |
| Environment | His PC is Windows with its time service stopped (G3 §0 item 6); servers are Linux VPSs |
| Materials | It never met a broker (G4a §2.2) |
| Methods | No PC-side setup, link or view (G3 §1.3) |

**Root cause.** The node was built as a world of its own (its own setup, its own monitoring, its own proof machinery) instead of as an app on QMX's core that uses QMX's setup, monitoring and states. INFERRED.

### The shared root

All five are one move: make a thing that moves on its own declare how it moves, and record each move where a script and he can read it. WS1 and WS2 declare number motion; WS3 declares the judging rule before results; WS4 declares reading inputs and their fallback; WS5 declares the node's desired state and its state vocabulary. INFERRED.

---

## Step 4. Forces and constraints

**Driving forces.** His rulings (units self-configure, units stand alone, only he promotes, the node as a mini app). Much already exists: the parameter space, the read-surface seam with presence states, the look-ahead guard, state snapshot and restore, the connect dialog's rerunnable steps, heartbeats and held streams, the mini-app supervisor (G1 to G4b). His tolerance for placeholders.

**Restraining forces.** The Book premise in four layers (QML intents, qmf-risk, QMB's run config, the node's seats; G1 §0 item 4). The node's size and its Linux-only pieces. No live run ever. Legacy QMA v2 code is to be changed surgically (rulings 24, 32). Trade counts: telling a +0.1R edge from zero takes about 270 trades to pass half the time (research 24 via STATE), so record-driven tuning is slow by nature.

**Constraints, real versus assumed.**

| Constraint | Real or assumed |
| --- | --- |
| A tuned value must mint a new bot | Assumed (an April safety rule; identity can bind the motion rule instead) |
| The MIS must stay inside the node | Assumed (it is code; QML-style library code runs anywhere) |
| A unit must wait for the MIS | Assumed, and forbidden by `CC-12` |
| Self-tuning needs real sizing | Assumed (the mechanism can be shown on any number) |
| The node must run on Linux | Real for servers (his ruling, T3:1096); assumed for the PC, since its logic runs on Windows (G4a §2.2) |
| Record-driven numbers need many trades | Real (arithmetic) |
| Only the node sends orders | Real (his design, T3:1562) |
| A `money` mini app is proposal-only | Real in code today (`qmx_apps/road/__init__.py:326-336`, `:360`: publishing a money app needs his bound signature and records `proposal_only`), and it does not fit a node that sends orders (see WS5) |

**Key insights.**
1. The smallest correct change for WS1 and WS2 is one field per number plus one journal row kind, plus parity in QMB. INFERRED.
2. The smallest correct change for WS4 is no new seam: readings become declared footprint keys served by read surfaces. INFERRED.
3. WS5's experience can be fixed by the shell around the node (app, steps, states, heartbeat), whatever the node lens decides about its insides. INFERRED.

---

## Step 5. Generate solution options

Methods: morphological analysis (WS1, WS4), assumption busting (WS2, WS5), reverse brainstorming (WS3), TRIZ on the one contradiction "numbers must move, identity must stay exact" (WS1).

### WS1 options

| Option | Shape |
| --- | --- |
| 1A | One `motion` field on every number: fixed, follows the market, or follows its record, with driver, clock, bounds and authority |
| 1B | Three kinds of number. A **fixed parameter** moves only by a new version. A **calibrated parameter** follows the unit's record on a slow clock, inside a range, by a declared rule. A **derived value** (a stop distance, a size in lots) is computed every bar from market readings and parameters by the unit's own logic, and its inputs are stamped on the trade. Only calibrated parameters are "self-tuning"; derived values are the rule itself |
| 1C | Self-tuning only offline: QMB re-optimises weekly and proposes a new version for his click |
| 1D | Self-tuning by an agent who reads the journal and edits numbers |
| 1E (TRIZ "separation in time") | Identity covers ranges and motion rules (fixed at compile); values move at run time inside them and each move is journaled |

Reverse check: how would we make tuning invisible and dangerous? Let any number move at any speed, by any agent, without a record. Reversed: few kinds, declared rules, script-driven moves, a receipt for each.

### WS2 options

| Option | Shape |
| --- | --- |
| 2A | Show the mechanism on a non-risk number only (an entry threshold that follows the record) |
| 2B | A stand-in sizing that really moves: a fixed fraction that halves after a losing streak and steps back after wins, inside a range |
| 2C | Both, plus one derived value (a stop at k × ATR) so the dummy unit shows both speeds |
| 2D | Placeholders are real blocks whose Library card says `placeholder`; the rip-out list is a query over blocks in use, not a document |
| 2E | Wait for the risk session (rejected by his ruling 1) |
| 2F | Use the old system's sizing as the stand-in (rejected: combining the two systems is the risk session's work, `R-05`) |

### WS3 options

| Option | Shape |
| --- | --- |
| 3A | A judge function in QMB: every candidate market judged by one rule fixed before results, each result pulled toward the unit's pooled result, correlated markets counted as one, every market a try |
| 3B | The honest number only: no screen, tool answer or template output shows a raw per-market ranking |
| 3C | A forward check: a candidate market needs fresh paper trades before it reaches his card |
| 3D | The run declares its universe before it runs; results outside it are labelled "exploration only" |
| 3E | Hold-out markets never used for selection (holdouts are his choice per study, off by default since PR 207, so not a default) |
| 3F | Every agent shortlist dated and scored by a script at the next session close (forecast ledger) |

### WS4 options

| Option | Shape |
| --- | --- |
| 4A | **Readings as declared inputs.** A unit declares each reading it uses (name, version, bar, fallback). Hosts serve it through a read surface. A missing or stale reading arrives as a `gap` sample and the declared fallback applies |
| 4B | The MIS as a network service the unit calls (rejected: a hot-path dependency, against `CC-12`) |
| 4C | Every unit computes every reading itself; the MIS only feeds the slow lane |
| 4D | On the node, readings ride the same local fan-out as prices (the feed keeper per broker connection, research 12 via STATE) |
| 4E | The MIS pushes state changes to subscribed units |

### WS5 options

| Option | Shape |
| --- | --- |
| 5A | **The node as an app on the core.** A manifest with a fixed operation set and `provides`; a home machine; setup through the connect dialog's new "trading node" kind as named rerunnable steps; a self-test; a closed state list; a desired-state reconciler inside; heartbeat into the PC's held stream; logs into OpenObserve |
| 5B | A fresh small node built on the venue laws and the QML seam, under the same shell as 5A |
| 5C | Keep the node as is with its own installer and Grafana, add a PC tunnel (rejected: a second monitoring world and the prove-itself machinery he rejected) |
| 5D | The node as a QMX server role running workflow steps (rejected: only the node sends orders, contained so the kill switch works, T3:1562) |
| 5E | The PC is the only node; servers only take over on a missed heartbeat (provotype; tests "PC is home") |

---

## Step 6. Evaluate and recommend

Criteria (standing order 6 plus his rulings): **hard cases** handled fully; **maintainable and debuggable**; **explainable** in a few sentences; **surgical** on shipped code; **stands alone** (`CC-12`); **deterministic proof** (`CC-10`). Scores: 2 good, 1 partial, 0 fails. INFERRED judgements.

| Option | Hard cases | Maintainable | Explainable | Surgical | Stands alone | Deterministic | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1A | 1 | 1 | 1 | 2 | 2 | 2 | 9 |
| **1B + 1E** | 2 | 2 | 2 | 2 | 2 | 2 | **12** |
| 1C | 1 | 2 | 2 | 2 | 2 | 2 | 11 (but it is not self-tuning) |
| 1D | 0 | 0 | 1 | 2 | 1 | 0 | 4 |
| 2A | 1 | 2 | 2 | 2 | 2 | 2 | 11 |
| **2C + 2D** | 2 | 2 | 2 | 2 | 2 | 2 | **12** |
| **3A + 3B + 3C + 3D + 3F** | 2 | 2 | 2 | 2 | 2 | 2 | **12** |
| **4A with 4D on the node** | 2 | 2 | 2 | 2 | 2 | 2 | **12** |
| 4C | 1 | 1 | 2 | 2 | 2 | 2 | 10 |
| 4E | 1 | 1 | 1 | 1 | 1 | 2 | 7 |
| **5A** (with 5B open to the node lens) | 2 | 2 | 2 | 1 | 2 | 2 | **11** |

### WS1 recommended: three kinds of number, identity on the rules (1B with 1E)

**In plain words for him.** A unit's numbers are one of three kinds. Some never move unless you approve a new version. Some follow the market every bar, like a stop measured against how much the price is moving. Some follow the unit's own record, slowly, inside a range you approved, by a rule written down in advance. Every slow move leaves a receipt in the journal.

**The shape.**
- **Fixed parameter.** Today's parameter space, unchanged.
- **Calibrated parameter.** Adds a `motion` block: what drives it (a journal statistic, named), its clock (every N closed trades, never mid-position, with a nightly floor), its range (the bounds already declared), its shrink (the value is pulled toward its default by evidence weight, trades ÷ (trades + k)), and its authority (moves by itself inside the range; a range change is a new version by his click).
- **Derived value.** A named output of a block, computed each bar (a stop distance, a size in lots). Its inputs are stamped on the trade row so the trade explains itself: "stop 12.3 pips = 1.5 × ATR 8.2 at entry".
- **Identity.** The unit's fingerprint covers ranges and motion rules; values moving inside them do not change identity. This replaces the "tuned set is a new bot" law for units only (`qml/src/qml/declaration/bot.py:618-628`), with its reason in one line: a self-configuring unit must be able to move a number without minting itself again.
- **Calibration is a pure function** of the journal rows up to a watermark, the motion rule and the prior state. Running it twice gives the same value (make-operations-idempotent). Its state rides the existing state snapshot and restore (G1 §1.9).
- **Parity.** QMB runs the same calibrator at the same clocks inside a backtest. Without it, live would differ from the test by construction.

**Hard cases.**
- A scalper reaches 20 trades in a day, a swing unit in a month: the clock is in trades, not days.
- A unit on several markets: one pooled calibration by default, each market pulled toward it (the same rule as WS3).
- A number pinned at its range edge: flagged "at its limit", and a slow-lane agent may propose a new version with a new range; only his click makes it.
- A unit stopped and resumed, or sent back to paper: calibration continues from its state; paper trades count, each tagged with its world.
- A move during an open position: deferred to the next flat moment, so no open trade's rules change under it.

**Why not 1A.** One field covering the market-following numbers turns plain logic into "self-tuning" and invites the slow machinery onto fast numbers. INFERRED.

### WS2 recommended: the real mechanism, labelled stand-in blocks (2C with 2D)

**In plain words for him.** The example unit really tunes itself now, with stand-in formulas. Its entry threshold follows its record. Its stop follows the market. Its size is a stand-in that halves after a losing streak and steps back after wins. Every stand-in is marked "placeholder", so the risk session can find and replace each one, and none can reach a live account by mistake.

**The shape.**
- The dummy unit carries one calibrated parameter that is not risk (an entry threshold or a lookback), one derived value (a stop at k × ATR), and one placeholder sizing block that moves by a simple record rule. It shows both speeds and the money part, with no sizing maths.
- **Placeholders are blocks.** A slot is filled by a block; a placeholder block's Library card says `placeholder` and names who replaces it (the risk session). The rip-out list is a query: every unit version using a block marked placeholder (build-the-lever: the list is a script, not a document).
- Placeholder blocks are refused on live accounts by default (lead's call 9 in `design-thinking.md`).
- Every record-driven number is measured in R, so when the risk session swaps the sizing, the unit's record stays valid. Numbers kept in money would not survive the swap.

**Hard case.** The risk session's real blocks will read inputs the stand-in did not (equity at entry, session, streak). The journal records them from day one (research 26 via STATE), so the swap needs no data it lacks. INFERRED.

### WS3 recommended: judge every market by one rule, show only the judged number (3A, 3B, 3C, 3D, 3F)

**In plain words for him.** When a unit is tried on many markets, QMX writes the test down before running it, counts every market as a try, pulls each market's result toward the unit's overall result, treats markets that move together as one, and asks for fresh paper trades before a market reaches your card. No screen ever shows the raw "best market".

**The shape.**
- A judge function in QMB, deterministic, run by a script step; its rule is declared in the run before results exist (the run names its universe).
- Shrink: each market's result is pulled toward the pooled result with weight trades ÷ (trades + k), k estimated from the spread between the unit's markets, and 100 when it cannot be estimated (research 43 §5, from research 24 §8; CHECKED there).
- Correlated markets (trade-result correlation above 0.6, research 43 §5) count as one record.
- A candidate market needs the later of 30 fresh trades or 2 weeks on paper before it reaches his card (research 43 §5).
- Every agent shortlist is dated and scored by a script at the next session close; the shortlist card shows its own hit rate. His "something that can be, that can't be cheated" (T2:385).
- The same rule covers sessions, hours and weekdays (research 30 §5's trap).

**Hard case.** A true one-market unit (gold only) has a pooled record equal to its market, so it pays no penalty. A broad unit with one special market earns that market's own settings, then its own version, from its record there, through the same forward check and his click. INFERRED.

### WS4 recommended: readings are declared inputs with a declared fallback (4A, 4D on the node)

**In plain words for him.** A unit reads the market intelligence the same way it reads prices. It lists which readings it uses and what to do if one is missing: work it out itself, ignore it, or take no new trades. The intelligence service writes every reading down with the moment it was known, so a backtest sees exactly what the unit would have seen. Nothing ever waits for it.

**The shape, in code terms (proposal on CHECKED seams).**
1. **Declaration.** The unit's template adds a `reads` list: reading name, version, bar, the instrument it applies to, and a fallback: `compute_here`, `treat_as_absent`, or `no_new_entries`. Each reading becomes a declared footprint key.
2. **The reading's code is library code.** One producer per reading, versioned. The same code runs in the MIS's publisher, in QMB on replay, and (for `compute_here`) in the unit's host on the node. Rule readings can compute anywhere; trained models cannot compute here, so they must declare `treat_as_absent` or `no_new_entries` (explainer round 2, option c').
3. **Hosts serve it through `read_surfaces`.** The factory already takes `read_surfaces: Mapping[str, ReadSurface]`, keyed by declared footprint keys (`qml/src/qml/protocol/__init__.py:130-140`, CHECKED). On the node, the surface reads the latest value from the local MIS store; past its `stale_after`, it returns a `gap` sample (`evidence.py:73-84`) and the fallback applies. In QMB, the surface reads the stored history, as published, or computes with the same producer when no history exists, labelled "computed in replay".
4. **No hot-path network.** On the node the MIS is its own local process writing a local store; readings fan out with prices (4D). A crash there is "readings down since", never a stalled unit.
5. **Stamping.** A trade row carries the readings the unit saw at entry and exit: value, version, `knowable_at`.
6. **Publishing for the slow lane.** The MIS writes readings as derived series beside the price partitions (`source = mis`, a kind per reading and version, with a dataset card) and a Library record when a state flips (G4b Q6, homes CHECKED there). Templates read those, never the model (`M-09`). The node-to-PC link carries them home.
7. **"Units pick."** Within the markets he admitted, a unit trades where its declared readings say its conditions hold now. New markets beyond that list come only as proposals for his click (design-thinking J15).

**A deterministic check that comes free.** Run the unit's backtest twice, once with its readings shuffled in time. If the results do not change, the unit never used the readings (funnel5's shuffled-readings idea, STATE research table). One script line in the judge. INFERRED.

**Hard cases.**
- A reading needs data the venue lacks (order flow on cTrader is an estimate from broker ticks and depth, ruling 40): the reading declares its data level; the deploy preflight refuses a market whose data cannot feed it, unless the fallback is acceptable.
- A reading's version changes: a new version is a new series and a new footprint key; a unit pinned to v1 keeps v1 until a new unit version.
- 24/7 markets: readings declare their own clock (bar, session, day), and the crypto day is 00:00 UTC by default.

### WS5 recommended: the node as an app on the core, set up by named steps, seen by one word (5A)

**In plain words for him.** The trading node is a mini app with its own server. You click "Start on This PC" or "Add a server". QMX shows each step as it happens, tests itself (prices arriving, clock right, broker reachable, kill switch working on demo), and then shows one word: Ready. While it runs it keeps itself to what you asked for, restarting anything that falls over and writing down every restart. It never restarts a unit that a risk rule stopped. You see every node from your PC, with its local time.

**The shape (the experience shell; the node lens decides the insides, 5A or 5B).**
- **Manifest.** A fixed operation set: `status`, `setup`, `self_test`, `deploy`, `withdraw`, `pause_unit`, `resume_unit`, `kill_switch`, `update`, `rollback`, `logs`. Managing operations ask him (the manifest's approval field, G4b Q5). `provides`: `node-state` (stale after 3 heartbeats), `unit-states`, `readings`, `journal-batches`.
- **A seam to settle.** In the mini-app core a `money` app is proposal-only: publishing it needs his bound signature and its evidence records `proposal_only` (`qmx_apps/road/__init__.py:326-336`, `:360`; start refused without it, `qmx_apps/supervisor.py:542-546`; CHECKED). A node sends orders, so either it declares a different risk kind and keeps its order power contained in its own process, or the core learns a fourth kind. The signature itself fits him: each node version he publishes carries his signature, which is "only he promotes" applied to the node. INFERRED; the node lens decides, surgically.
- **Setup as named steps,** each safe to rerun: check the machine (disk, clock sync), install, start, sign in to the broker on its own app, start the readings, self-test, ready. This is the connect dialog's step pattern (cards first, checked steps, one place row written last, a smoke run; BUILT for other kinds, G3 §1.4) with a new "trading node" kind. The firewall with its 5-minute undo and `qmx-recover` are reused on servers (G4a §3 row 12).
- **States.** Setting up, starting, ready, trading, healing, paused, stopped, and, seen from the PC, unreachable since. Each with a one-line reason. A health stop and a risk stop are different words.
- **Desired state.** A small document (units deployed per account and world, readings on, version) that the node keeps returning to: probe, compare, act (restart with back-off), log. Every heal is a journal event with what, why, and how many times. A heal never resumes a unit stopped by a risk rule.
- **Heartbeat.** Every 60 s: state, reason, unit summary, clock band and offset, zone, version, last broker contact. It lands in the PC's held stream per node (BUILT, G2 §6) and in OpenObserve (one log home; the node's Grafana stack is cut, G4a §4.2 item 5).
- **Placements.** On This PC: natively on Windows under the mini-app supervisor (Job object, breaker, logs; G4b Q5), practice accounts only. On a Linux server: systemd and its credential store. One product, two placements (the node docs' own DEC-0262, G3 §1.2). WSL only if all goes south (T3:1096).
- **The outer guard.** The mini-app breaker (3 errors, 10 s heartbeat timeout by default, `qmx_apps/manifest.py:108-110`, CHECKED) watches the node process; the node's own reconciler heals its parts inside. A node crash leaves broker stops in place (venue-resident stop, G3 §1.1).

**Hard cases.**
- The PC sleeps: a PC node stops with it, and the card says so before he starts it.
- Setup dies halfway: rerunning converges.
- The clock is unsynced (his Windows Time service is stopped, G3 §0 item 6): the node starts in the "no new entries" band and says why; turning on time sync is his click.
- Two machines share one cTrader grant: each node registers its own app (G3 trap 4).
- The node is unreachable: its units keep trading; the PC shows its last values and the PC's view-only broker read shows the account's positions.

---

## Step 7. Implementation plan

The build order follows the frame: QML first, then QMB, then the node, with the MIS beside them (`00-frame-after-grounding.md` §4). No dates (the skill forbids time estimates).

| Solution | Part | Reuses (CHECKED in grounding) | Smallest change, with its reason |
| --- | --- | --- | --- |
| WS1 | QML | Parameter space; state snapshot and restore; content identity `fp1` | A `motion` block on calibrated parameters; derived values named in the template; identity over ranges and motion rules. Reason: units must move numbers without re-minting |
| WS1 | Journals | `trade` kind; CT-13 decision events | A calibration row kind; derived-value inputs on the trade row. Reason: every move needs a receipt |
| WS1 | QMB | Execution ports, journal plumbing | Call the unit's calibrator at its clocks during replay. Reason: parity |
| WS2 | QML and the Library | `component` kind (G1 §2.4) | A `placeholder` mark on block cards; the dummy unit's three numbers. Reason: his placeholder ruling, made findable |
| WS2 | Trading node | Seat admission | Refuse placeholder blocks on live accounts by default. Reason: lead's call 9 |
| WS3 | QMB | Robustness batteries, try-shaped ledger lines | A judge function and a declared universe in the run config; results in R. Reason: luck must not reach his card |
| WS3 | Workflows | Grader node; event triggers | Shortlist templates read judged numbers only; a scoring script. Reason: agent claims scored by the market |
| WS4 | QML | `read_surfaces`, presence states, `knowable_at` guard | A `reads` list with fallbacks in the unit template. Reason: readings as inputs, never a dependency |
| WS4 | The MIS | Labeler code inside the node (G1 §6) | Producers as library code with versions; a publisher into price partitions and Library records; consumers opened to units. Reason: "never bots" contradicts `M-01` |
| WS4 | QMB | Typed partition reader | Read reading series in replay, or compute them with the same producer. Reason: parity |
| WS5 | The mini-app core | Manifest, supervisor, breaker, home machine | The node app's manifest; settle the money-app seam. Reason: ruling 43 |
| WS5 | The host and the connect dialog | Step runner, firewall undo, `qmx-recover`, held streams | A "trading node" kind; the PC side of the node link. Reason: "as simple as how, for example, I can set up a server from a provider" (T2:1148) |
| WS5 | Trading node | Venue laws, cTrader client, reconcile, kill switch, clock bands, heartbeat (G4a §4.1) | A desired-state reconciler, the state vocabulary, a live profile, a Windows placement; cut the proof machinery first. Reason: ruling 27 and his rejection of prove-itself machinery |

**Responsible parties.** The build's builders, one packet each; the Level 1 agents decide the packet split. **Resources.** Nothing new to buy; the first real start of the host on his folder is a named step (G4a §2.1).

---

## Step 8. Monitoring and validation

Each check is a script or a test a builder can rerun; none is an agent's judgement.

| Solution | Proof that it works | What would make us change course |
| --- | --- | --- |
| WS1 | Backtest the dummy unit twice from the same data: the calibrated parameter moves at the same trade numbers both times, stays inside its range, and each move has a calibration row naming rule and rows. Then restart mid-run: the same values | A move inside an open position; values differing between two identical runs |
| WS2 | A query lists every unit version using a placeholder block; the node refuses a placeholder on a live account with a one-line reason | A placeholder reaching any live account |
| WS3 | Simulate 20 markets with one true edge (research 24's study shape): the judged ranking does not crown the luckiest; correlated twins count once | A raw ranking found on any screen or tool answer |
| WS4 | Shuffled-readings test changes the results of a unit that uses readings and not of one that does not; kill the MIS on demo and the unit keeps trading on its fallback with "readings down since" | A unit that stalls when the MIS is down |
| WS5 | The J6 storyboard as a live lane: blank profile, start, "Ready", all self-test lines pass; kill the readings process and see "healing" then back; run setup twice, same end state | A step that cannot be rerun; a heal that resumes a risk stop |

**Risks and mitigation.**
- Calibration overfits on few trades: shrink toward the default, clock in trades.
- The motion field grows into a rules engine: the motion kinds are a closed, addable list; anything else is a new version.
- The node's money-app seam is settled wrongly: the node lens settles it with the mini-app owner's code, surgically, before the node packet.

**Adjustment triggers.** If the dummy unit's record-driven number never reaches its clock in a one-month backtest, shorten the dummy's clock (a number, not a design change). If the shuffled-readings test cannot separate users from non-users of readings, drop it from the judge and keep it as a study.

---

## Step 9. Lessons

- **What worked.** Reading the code seam before proposing: the read-surface protocol made WS4 small, and the money-app rule exposed a seam nobody had named.
- **What to avoid.** Treating every moving number as "self-tuning"; the fast speed is the rule, not tuning.
- **Pattern.** When something moves on its own, declare how it moves and record each move. The five spots are one idea.

---

## Quote check

Script: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\check_quotes.py`, run with `python -I check_quotes.py`. It reads every `"..." (Tn:line)` pair in `design-thinking.md`, `problem-solving.md` and `ui-needs.md`, splits each transcript on `\n` only (so line numbers match `grep -n`), normalises whitespace, and looks for the quote on the cited line.

Result of the final run on 2026-10-31, after the last edit to the three files: `85 quotes found on their cited lines, 0 not` (exit code 0). An earlier run found five quotes written in a form the script's pattern skipped (a comma before the line reference) and one phrase taken from STATE rather than a transcript; all six were rewritten into the checked form or reworded as plain reference, and the run above includes them. Citations that point at a line without quoting it (for example "his ruling, T3:1096") are references, not quotes, and are not counted.
