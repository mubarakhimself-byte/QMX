---
ticket: funnel (divergent half A)
title: Party rounds and brainstorming over the unit system and the strategy kit
date: 2026-10-24
author: opus funnel agent A (read-only everywhere; this file is the only write)
method: one context voiced every persona (bmad-party-mode, session mode, inline cast). Then bmad-brainstorming run headless by me as the brainstormer (techniques listed in §3). No subagents.
status: DIVERGENT ONLY. Nothing here is ranked, chosen or agreed. Convergence happens in 07-funnel.md.
labels: CHECKED (file) = a fact taken from an input file, which itself checked it. INFERRED = my reasoning or a persona's claim. Persona opinions are opinions, not facts.
numbers: every number is a starting point and must be configurable (UI-editable), never a baked default.
---

# 07a: The funnel party (divergent half A)

## How to read this

- **§1** is the cast.
- **§2** is ten rounds, one per big open question. Each round has a short exchange, then what the room agreed on, then the disagreements that stayed open. I did not resolve them.
- **§3** is the brainstorming list: 170 numbered ideas from 14 techniques. Each idea gives:
  - **Lens:** A = agents and code, T = traders, C = creators (plain Python).
  - **Surface:** Lab, Pods, Copilot, Mini app, or Algo (QML, QMB, QMF, MIS, node).
  - **Touches:** the part it changes.
  - **Lever:** E = edge per trade, N = trade count, S = right size, D = less drag, P = proof the Judge step can use. "Parked" means it doesn't fit yet.
- **§4** lists every disagreement in one place, for the converge step.

Short source names: `SEEDS` = `workroom/risk-lab-2026-10-05/seeds.md`; `DEC` = `decisions.md` beside it; `G09` = `grounding/09-original-design-recovery.md`; `01`-`05` = the research files in this folder.

**Two process notes.**
- The brainstorming skill normally writes a memlog and an HTML keepsake. The brief allows one output file, so neither was written. The idea log lives here.
- "The Operator's voice" speaks only positions written in `SEEDS` or `DEC`. It never invents new rulings.

---

## 1. The party roster

| Icon | Name | Who they are | What they keep dragging the room back to |
|---|---|---|---|
| 🪙 | **Kofi** | Scalps FX and gold at IC Markets on cTrader. Trades London-open sweeps of the Asian range. | "Will it fill at that price at 07:02 London?" |
| 📈 | **Dana** | Futures day trader: ES and MES, DOM and tape, NinjaTrader. | Real volume, roll weeks, the cash open. |
| 🌊 | **Rin** | Trades Hyperliquid perps, including HIP-3 stock perps. Thinks in funding hours and maker rebates. | Venue limits nobody else models. |
| 🛡️ | **Margaret** | Former prop-firm risk manager. Has closed hundreds of accounts. | Floors, caps, and who is allowed to loosen anything. |
| 🔬 | **Dr. Ilya** | Quant researcher with an overfitting obsession. Carries the deflated-Sharpe paper everywhere. | "How many tries was that?" |
| ⚙️ | **Priya** | Market-microstructure expert: OFI, queues, spread dynamics. | Information per bar; what each venue's data can and cannot show. |
| 🤖 | **Tomás** | ML engineer: meta-labeling, drift, calibration. | Where the learned model sits, and what it was trained on. |
| 🏗️ | **Hal** | Platform architect who once built a backtester that lied. | Determinism, replay, "one loop for backtest and live". |
| 🧬 | **Sven** | Ten years as a StrategyQuant X power user. Ships `.cfx` workflows. | Speed, workflows, "SQ already does that". |
| 🎨 | **Amira** | Non-technical creator. Wants to write what she imagines in one Python file. | "Don't make me fill four forms." |
| 🧠 | **QA-7** | An AI agent that will use QML and QMB every day. | Doors, refusals with the fix named, cost before launch. |
| 🦨 | **Grumble** | The skeptic. Has seen every "self-tuning" system tune itself to zero. | "Show me it works on one thing first." |
| 🎙️ | **The Operator's voice** | Speaks only from `SEEDS` and `DEC`. | Compounding through breadth, the router, units that configure themselves. |

Running bits that formed during the session:
- Grumble versus the fail branch (from round 4 on).
- Ilya's tries counter: he keeps a tally on a napkin.
- Hal and Sven's speed-versus-determinism feud.
- Amira's "one file" refrain.

---

## 2. The rounds

### Round 1: What is a unit, and what sits outside it?

*(Starting facts on the table: `DEC` baseline unit = strategy + risk profile + conditions + journal, "never agreed". `SEEDS`: unit = bot + its own risk and sizing tuned from its own record, with the MIS outside. The Library already has a `unit` kind with empty fields plus "Markets" and "Family tree" tabs: CHECKED (01 §4.2, §7.6). Ruling 14 says "the unit lives inside the trading node": CHECKED (01 §6 row 7).)*

🎙️ **Operator's voice:** One bot that configures itself. Its own risk and sizing, tuned from its own record. The MIS stays outside, and bots never read it.

🏗️ **Hal:** Then make the unit a *value*, not a process. Logic fingerprint, profile version, a pointer to its record. QMB hosts it in replay and the node hosts it live. "Lives inside the node" just means "hosted by". The same bytes in both places, or you can't prove anything.

🛡️ **Margaret:** Fine, but write this in blood: the account guard sits *above* every unit. Kill line, daily budget, correlation, news, the kill switch. A unit can tighten itself. It can never touch the guard.

🪙 **Kofi:** My gold bot must stay flat during the LBMA fix. Is that rule the unit's or the router's?

⚙️ **Priya:** The router's. A fix window is a market fact. Facts stay at the node, outside the unit (the `DEC` 20 Oct lean says facts stay mandatory at the node).

🪙 **Kofi:** No. My edge *is* "don't enter in the fix". That's strategy logic, so it goes in the bytes.

🤖 **Tomás:** Harder question. A meta-labeler is trained on one unit's trades plus the market state at entry. It decides take or skip and scales size. Where does it live? Inside the unit, the unit reads the MIS. Inside the router, the router carries one model per unit.

🦨 **Grumble:** "A sidecar the bot never sees" is still reading the MIS with extra steps.

🤖 **Tomás:** It's reading it *outside the rules*. That's exactly what `SEEDS` asks for. The bot's if-else stays clean.

📈 **Dana:** Bigger question. Is a unit one *logic* or one *cell*? My ES open-drive on RTH and on Globex are different animals: different costs, different volume.

🎙️ **Operator's voice:** Same logic on 1m and 5m = two registry entries, each with its own proof.

🏗️ **Hal:** Two *entries*, yes. But one unit with two seats, or two units? If the record splits per seat anyway, the unit becomes "logic + profile family", and each cell gets its own record slice.

🎨 **Amira:** Whatever you pick, I write one Python file. Something else fills the profile and the record.

🧠 **QA-7:** Give me one manifest with slots. I fill the strategy slot. The system fills profile defaults from the bot's type and starts the record empty. If you refuse me, name the missing slot.

🧬 **Sven:** In SQ the money management is baked into the exported EA. That's why nothing there adapts. You're already better if sizing sits beside the bytes, not inside them.

🛡️ **Margaret:** And pods. You have three readings of "pod" (01 §6 row 8). I say a pod is the frame: guard plus allocator. Units live inside it.

🏗️ **Hal:** The Lab already designed pods as a seven-slot sizing stack that compiles to Book + BMS (CHECKED 01 §4.1). Throwing that away is the scope rule's "don't casually remove". Map the slots: some belong to the pod, some to the unit.

**Agreed in the room:**
- The account guard sits outside and above all units. Units can tighten their own settings but never the guard's.
- Bots' if-else rules never read MIS opinions.
- The record belongs to the unit, not to the slot or the pod (a reversal of the old vault, where house money belonged to the slot: CHECKED G09 A.9).
- The unit should be a hostable value: one set of bytes runs identically in QMB and on the node.

**Live disagreements:**
1. **Unit grain.** One logic with many cell seats (Hal) versus one unit per cell (Dana).
2. **Whether time windows are logic or placement.** Kofi wants fix and session filters in the bytes. Priya and the `DEC` lean put them at the node and in the router.
3. **Where a meta-labeler lives.** A unit sidecar (Tomás) versus the router's per-unit model versus "don't build it" (Grumble).
4. **What a pod is.** The frame (Margaret, `DEC:75`) versus the Lab's seven-slot sizing stack (Hal, LP AD-10/11) versus both with the slots split.
5. **How much the creator sees.** One file (Amira) versus an explicit manifest with slots (QA-7).

---

### Round 2: The identity rule (new strategy vs variant vs profile version)

*(`DEC` identity lean: changed logic → new strategy; same logic on a new instrument or timeframe → variant; profile retune → new profile version. Library lineage edges `variant-of`, `branches-from` and `derived-from` exist, and the identity-rule table is designed but not built: CHECKED (01 §2 row 14).)*

🔬 **Ilya:** Identity should follow *tries accounting*. A family is whatever shares one luck budget. Two bots with different code that trade the same entries are one family. I don't care what the diff says.

🏗️ **Hal:** Identity must be bytes. The source-manifest fingerprint, full stop. Behaviour clustering is a second layer called *family*. Mix them and lineage becomes a matter of opinion.

🧬 **Sven:** SQ's "dismiss similar" uses ±5 % on trades, profit and drawdown. Crude, but it's behaviour, and it works better than diffs.

🪙 **Kofi:** I move my stop from 1.0 ATR to 1.2 ATR. Is that a new strategy?

🦨 **Grumble:** By your own rule, yes. `DEC` says exits are part of the strategy, and changed logic means a new strategy. So you'll have ten thousand "strategies" by Friday.

🧠 **QA-7:** Split it. A number inside a declared range is a *setting*: same strategy, but every setting tested is a try. A new range or a new block is logic: new strategy, new version.

🎙️ **Operator's voice:** A sniping window gets its own sizing profile once proven.

🛡️ **Margaret:** So a window is a cell *and* a profile? Then a profile version must never wipe the record. Sizing doesn't change entries.

🤖 **Tomás:** It does when it skips trades for size, or when HME changes which trades exist after a loss streak. Profile changes can change the trade list, so log them as trials too.

🌊 **Rin:** Same logic, same coin, different venue: Hyperliquid BTC versus IC BTCUSD CFD. 02 says separate proof (costs, hours and price source all differ: CHECKED 02 §9.0). Variant.

📈 **Dana:** And WTI_X6 to WTI_Z6 is *not* a new variant. That's the same contract chain. A registry keyed on symbol loses the unit's history at every roll (CHECKED 02 §5.3).

🎨 **Amira:** I ask the Copilot to "rewrite this to be smarter" and a stronger model changes half the logic. New strategy?

🎙️ **Operator's voice:** Every node is a variant in the lineage. Parent, pairs, history. One idea becomes many variants.

🏗️ **Hal:** Then "rewrite" is an edge kind, `rewritten-from`, on a new strategy id. Lineage keeps the parent, identity stays honest.

**Agreed in the room:**
- Venue × instrument × timeframe × window cells are variants with their own proof.
- A futures or futures-CFD roll needs an "instrument chain" identity, so history survives the contract month.
- Every tested setting, profile retune that can change trades, and rewrite counts as a try, whatever its identity label.

**Live disagreements:**
1. **What identity is.** Bytes (Hal) versus behaviour (Ilya, Sven). Or both, as identity versus family.
2. **Whether an exit tweak is a new strategy.** The strict reading of the `DEC` lean (Grumble's reductio) versus "settings within declared ranges stay the same strategy" (QA-7).
3. **Whether a window is a cell, a profile, or both.**
4. **Whether a stronger model's rewrite is a new strategy or a variant.**

---

### Round 3: The registry (preferred, hypotheticals, sniping) and where the MIS router lives

*(`SEEDS`: preferred = cells with proof from QMB's run-on-every-bot; hypotheticals = look-alike markets to test, not trade; mostly key-value; an agent or workflow fills it. Where the MIS sits "is not settled", and the operator warned it is "less simple than change a key-value pair". Today: no router, no similarity search, no registry writer: CHECKED (01 §2 rows 3, 11-13, 39).)*

🏗️ **Hal:** The first law: a router you can't replay can't be proven. freqtrade's volume pairlist doesn't backtest at all (CHECKED 04 §4.2). Every placement must be recomputable from recorded inputs.

⚙️ **Priya:** Then split it by speed. Spread, tick rate, depth and cost ratio are fast, near-zero-lag states (CHECKED 05 §1.1, T1). They belong at the node, near the venue. Regime labels lag by hours to weeks (CHECKED 05 §1.1, T3). That's a placement planner, central, days-scale.

🛡️ **Margaret:** And when the node loses the PC? `SEEDS` says the node keeps trading when his laptop is closed. So the plan has to be *cached on the node with an expiry*, signed, and it degrades safely when it runs out.

🌊 **Rin:** My router inputs aren't even "market state". Hyperliquid gives each address one action per 1 USDC traded, plus a 10,000 starter buffer (CHECKED 02 §8.1). A maker bot can burn that. The router has to budget *requests*, not just capital.

🔬 **Ilya:** Hypotheticals must never trade full size. Give each cell a state: hypothesis, incubating, proven, closed-thin, failed (05 §7.5 proposes this). A Thompson budget over shrunk posteriors decides which hypotheses get paper or min-lot slots (05 §8.4).

🦨 **Grumble:** "Preferred" means "the backtest looked good". By QMB's own rules nothing it produces counts as proof today: costs are uncalibrated and fills are tainted optimistic (CHECKED 01 §7.4). Your registry is built on sand.

🧠 **QA-7:** Then the registry write door refuses any entry without proof-run ids and a calibration version. If you refuse me, tell me which artifact is missing.

🪙 **Kofi:** Sniping is where I make my money. London 07:00-09:30 UTC for gold sweeps. I want that window to carry its own size.

🤖 **Tomás:** Careful. Window discovery is What-If, and What-If is hindsight. SQ's own admin says filtering bad days after the fact is pointless (CHECKED 03 §2.3).

🎙️ **Operator's voice:** The MIS can help find and confirm windows, including in historical data. Each window gets its own sizing profile *when proven*.

🔬 **Ilya:** "When proven" means on a month the search never touched. Then I'm happy.

🧬 **Sven:** You're overbuilding "key-value". In SQ a databank is a query, and the old workbench said the same: "a candidate set is a query, not a copied table" (CHECKED 01 §1.3). Make the registry a *view* over results, not a second store.

🏗️ **Hal:** Half right. Proof is a query over results. But a *placement decision* must be a stored, signed record, or replay fails.

**Agreed in the room:**
- Router decisions must be replayable from logged inputs.
- Hypotheticals never trade full size.
- Registry proof must cite run ids and a cost calibration version.

**Live disagreements:**
1. **Where the router lives.** Central (planner), node (gate), or split two-speed.
2. **What the registry is.** A stored key-value record per unit (`SEEDS`) versus a query over Library results (Sven) versus "query for proof, stored record for placement" (Hal).
3. **How hypotheticals get picked.** By market similarity (`SEEDS`) versus by a bandit exploration budget (Ilya) versus both.
4. **Who promotes a hypothetical to preferred.** An agent or workflow on a numeric rule, or the operator's click.
5. **Whether sniping windows can be found in history at all** without hindsight bias (Tomás, wary) versus with a post-search seal (Ilya, fine).

---

### Round 4: Domain expansion and its stopping rule

*(`SEEDS`: the same logic becomes many variants across instrument × timeframe × window. It is a workflow, designed after QMX is live. Claude's opinion there: expand only from an out-of-sample parent, count every expansion as a try, stop thin cells, and make the fail branch strictest. 05 §7: alpha-investing/LORD, e-values, ONC effective N, a four-condition numeric rule.)*

🔬 **Ilya:** It's online multiple testing. Every cell is a hypothesis in a stream. LORD spends error "wealth" on each test and earns it back on discoveries (CHECKED 05 §7.2). That is literally "expand only from a parent that passed".

🧬 **Sven:** SQ uses "backtest on additional markets" as a *gate*: fail any market and you're dropped. You want it as a *map*. SQ's own doc admits a robust strategy "does not have to perform equally well on all markets" (CHECKED 03 §2.3).

📈 **Dana:** And 1m plus 5m on one pair is one bet. Count it once.

🤖 **Tomás:** Cells will be thin. A 70 %-win scalper needs about 550 trades to prove anything (INFERRED, 05 §2.4). Shrink each child toward its parent. Empirical Bayes.

🦨 **Grumble:** Now the fail branch. "Most strategies can work" is how retail traders blow up. Search 200 contexts and one will look great by luck.

🎙️ **Operator's voice:** Even strategies that plainly fail get tested this way: find *why* it failed, ask if QMX has any context where its rules are met, iterate there, rejoin the funnel.

🔬 **Ilya:** I'll defend him, with one condition. The fail branch pays double. Every projected context is a trial, and the proof comes only from months sealed *after* the search (05 §7.3).

🦨 **Grumble:** Then most fail-branch work ends in "closed-thin". You're burning compute to learn nothing.

🏗️ **Hal:** Compute is cheap; false proof isn't. But give the stopping rule a compute budget too. Alpha wealth plus a machine-hours cap per family.

🛡️ **Margaret:** A new cell must also add *breadth*. If its rolling P&L correlates with live units above a cap, it adds tries and no breadth (05 §7.3 condition 4).

🎨 **Amira:** I just want a "where else does this work?" button that tells me honestly "nowhere yet".

🧠 **QA-7:** And when I expand, may I change the logic to fit the new market (the rewrite branch), or only the cell?

🎙️ **Operator's voice:** Rewrite branch: keep the logic as is on a new timeframe, OR rewrite or adjust it to fit. Cheap workhorses do the bulk; a stronger model attempts the rewrites.

🔬 **Ilya:** Then a rewrite starts a new family's tries budget, but inherits nothing as proof.

**Agreed in the room:**
- Expansion is a stream of tests that spends a luck budget.
- Correlated cells count as fewer effective tries.
- A child borrows its parent's estimate as a prior, but never as proof.
- The fail branch's proof must come from data after the search.

**Live disagreements:**
1. **Should the fail branch exist?** Grumble says no; the Operator's voice and Ilya say yes, under the strictest rule.
2. **What the stopping rule is made of.** Pure statistics (alpha wealth + MinTRL reachability, Ilya) versus a compute and time budget (Hal) versus operator judgment per branch.
3. **Whether expansion may mutate logic** (the rewrite branch) or must keep logic frozen (variant only).
4. **Whether a rewrite inherits the parent's luck budget** or starts a fresh one.

---

### Round 5: Self-tuning sizing and exits

*(`DEC`: Kelly as a ceiling, house money (HME), reverse house money (RHME), loss points, the sizer "tighten, never loosen" (a lean). 05 §4: a one-way ratchet on noisy estimates drifts to minimum size; put the ratchet on the floor (Grossman-Zhou); loosen only through an e-value gate. At the kill line 40 % below seed: full Kelly 60 %, half 22 %, quarter about 3 % chance of touching it with a known edge, INFERRED arithmetic (05 §4.1). The sizing ladder has never sized a real trade: CHECKED (01 §7.7).)*

🛡️ **Margaret:** Units never loosen on their own. Ever. Loosening is a human click.

🔬 **Ilya:** Then every unit drifts to minimum size over a year, even with an unchanged edge. A running minimum of a noisy estimate only goes down (INFERRED, 05 §4.6). Tighten fast on rules. Loosen slowly, on evidence gathered after the tightening.

🪙 **Kofi:** House money worked for me in London. Up on the session, I press.

🔬 **Ilya:** It works only if your own trades are serially correlated (CHECKED 05 §4.4, Kaminski & Lo). Measure your autocorrelation. If it's zero, RHME just cuts your return.

🪙 **Kofi:** Fine. Measure it. But don't take the knob away before measuring.

🛡️ **Margaret:** And on $300 the minimum lot can force more risk than the Kelly ceiling. Skip the trade, and *count* the skips, or the record lies (05 §4.7).

🤖 **Tomás:** Shrink the Kelly bet by how sure you are: t²/(1+t²) of the edge's t-stat (my derivation in 05, INFERRED). Use the deflated or held-out t, never the in-sample best.

⚙️ **Priya:** Exits now. Nobody ships exits *measured as blocks* (04 §5 #6). Run the same entries with five exit blocks, read MFE and MAE, and let each instrument and session pick.

📈 **Dana:** Trailing stops on ES trend days are real. On chop days they're a donation.

🌊 **Rin:** On perps the cleanest exit rule I know: never hold across the funding hour unless the edge pays for it.

🤖 **Tomás:** Competing hazards: time-to-target versus time-to-stop, updated in-trade with OFI and the vol ratio. Exit when the stop hazard overtakes. No peer-reviewed trading evidence yet (05 §5.1).

🏗️ **Hal:** Every safety exit must run inside QMB's replay too. NinjaTrader's ATM strategies can't be backtested, so their value can never be shown (CHECKED 04 §3.5).

🦨 **Grumble:** And every exit variant you try is a trial. You'll tune exits to the same trades you judge them on.

🪙 **Kofi:** So can my unit swap exits by itself within proven blocks? Or is the exit frozen in "compiled"?

🎙️ **Operator's voice:** Stress, paper and live are compiled: logic is frozen and only the risk profile tunes, within its ranges.

**Agreed in the room:**
- Bleeding control is fast rules (loss points). Decay detection is slow statistics.
- Safety exits must be replayable.
- Exit variants are trials.
- Skips caused by size limits must be counted.

**Live disagreements:**
1. **Who loosens size.** Tighten-only with a human loosen (Margaret) versus an evidence-gated automatic loosen (Ilya) versus a floor ratchet only.
2. **House money's default.** On by default (Kofi) versus off until the autocorrelation test passes (Ilya).
3. **Whether exits belong to frozen logic** or to the unit's tunable profile (choosing among pre-proven exit blocks).
4. **Whether signal strength should feed size at all** before it is shown to be calibrated.

---

### Round 6: The agent and creator kit (QML contract, blocks, Lab, plain Python, agent door)

*(04 §0: all seven platforms converged on one contract, and QML's shipped protocol already has its shape. The gap is ergonomics and blocks. `DEC`: QML rebuilt from scratch, a fixed contract + any code + a growing block catalogue. Today `research.qml_run` refuses agents: CHECKED (01 §1.2). Six runnable indicators; VWAP, ATR and Bollinger are not runnable: CHECKED (01 §1.1).)*

🎨 **Amira:** One Python file. I write `when_to_enter`, `how_to_exit`. I don't write a declaration.

🧠 **QA-7:** I'll write the declaration *for* you, from your code. You confirm it in plain words. Then I run validate, look-ahead, recursive and smoke, in that order, and you get a red line naming what broke.

🏗️ **Hal:** And keep the denial set: no clock, no I/O, no undeclared randomness (CHECKED 04 §3.8). cTrader lets Python do HTTP in backtests. That's how you get backtests nobody can reproduce.

🧬 **Sven:** SQ's AlgoWizard went AI in build 143: text → strategy (CHECKED 03 §1.4). Templates with random placeholders are the real power. Fill slots, don't write from blank.

⚙️ **Priya:** Copy MT5's Wizard vote: signals return strength, a combiner decides with thresholds (CHECKED 04 §1.1). But make the combiner a block whose rule is itself a parameter.

🔬 **Ilya:** And a parameter that picks *which* indicator is a structure search. Tries, again.

🦨 **Grumble:** The STRATS dictionary is 239 entries with about 7 runnable and 9 name collisions (CHECKED 01 §1.2). Add a "librarian" that grows it from agents' custom code and you get a junk drawer with a search box.

🎙️ **Operator's voice:** Agents must search blocks before writing new code. A scheduled librarian proposes new blocks from repeated custom code.

🧠 **QA-7:** Copy QuantConnect's MCP shape: compile on write, a few-seconds smoke run, push the result when done ("do not poll"), estimate before a sweep (CHECKED 04 §3.9).

🎨 **Amira:** And let me write it the pandas way: the whole frame at once. That's how every tutorial looks.

🏗️ **Hal:** Vectorised for research only, compiled into the per-instant protocol, with an equality check between the two. If they differ, it doesn't register.

🧬 **Sven:** Graph view or code view first in the Lab?

🎨 **Amira:** Code, with the graph drawn from it. NinjaTrader's builder shows the code live (CHECKED 04 §1.3).

**Agreed in the room:**
- One contract with three doors (plain function, helpers, blocks), all compiling to the same artifacts.
- Look-ahead and recursive checks are conformance gates.
- The agent door returns typed refusals that name the fix, and estimates cost before a sweep.
- The denial set stays.

**Live disagreements:**
1. **Rebuild QML from scratch** (`DEC` 13 Oct) versus extend the existing roughly 14k lines (Hal, 04 §5 #1). Carried into round 9.
2. **Vectorised authoring.** Allowed with a parity check (Amira, Hal) versus event-only (a purist minority in the room).
3. **How the catalogue grows.** Curated (Grumble) versus librarian-grown (the Operator's voice).
4. **Graph-first or code-first Lab.**
5. **Who writes the declaration.** Inferred by an agent and confirmed by the creator (QA-7) versus written explicitly.

---

### Round 7: QMB as a StrategyQuant-beating test bench

*(03 §0: SQ has no correction for the number of tries; practitioners found no lift from its robustness funnel. QMB already has What-If (`analysis/project.py`), a stable-region flag (`optimize/sensitivity.py`) and the grid (`sweep/axes.py`): CHECKED (03 §0.6). QMB's reader needs about 16 GB for a month of M1, and it replays bid/ask only: CHECKED (01 §0.4-0.5).)*

🦨 **Grumble:** Before any of this beats StrategyQuant, it has to load one month of one-minute gold. It can't (01 §0.5). Everything else is a slide deck.

🧬 **Sven:** And SQ runs thousands of backtests a second. QMB is process-per-run. You'll lose on speed every day.

🏗️ **Hal:** You win on *truth*, not speed. One loop for replay and live. No export gap.

🧬 **Sven:** Truth at one backtest per minute is a hobby.

🏗️ **Hal:** Then a fast lane. Vectorised screening is marked "ungoverned value", and anything promising reruns in the governed loop. Both lanes count tries.

🔬 **Ilya:** The real edge over SQ is three things nobody ships (04 §5 #3):
- tries counted automatically;
- each gate's lift measured (03 H1);
- the whole recipe backtested (03 H15).

Wiecki found the *amount* of backtesting predicts disappointment (CHECKED 05 §6.2).

📈 **Dana:** For scalpers the fidelity ladder *is* the bench. A strategy that dies between M1-OHLC and real-tick-with-spread was never a strategy.

🧬 **Sven:** I want a fitness score. Users sort by one number.

🔬 **Ilya:** DEC-0162 bans stored composites, and `sweep/rank.py` enforces it (CHECKED 03 §6.4). Sort by any lens you like, but store per-lever measures.

🤖 **Tomás:** Monte Carlo shuffle can't change total profit, so an overfit list passes it (CHECKED 03 §2.3, the Ali Casey demo). Use MC for *sizing*, not selection.

🧬 **Sven:** SQ users swear by MC.

🔬 **Ilya:** SQ users also say fewer than 10 % trade live like their backtests (03 §2.3).

**Agreed in the room:**
- Tries ledger, test-lift and recipe backtests are the differentiators.
- The windowed reader and calibrated costs come before any claim.
- The fidelity ladder is the scalper gate.

**Live disagreements:**
1. **Speed.** A fast vectorised screener (Sven, Amira) versus a single governed loop (Hal), or both lanes.
2. **Scoring.** A stored fitness or composite (Sven) versus sort-only lenses (DEC-0162, Ilya).
3. **Monte Carlo.** A selection gate (Sven) versus a sizing input only (Tomás).
4. **Driving SQ through its MCP** as an external generator, licences permitting (03 §6.2): Sven yes, Hal "never trust a black box".

---

### Round 8: Supporting any instrument a broker offers

*(02: classes differ in costs, time, data, and how the contract ends. CCXT is spot-only in QMX; there is no funding, expiry or dividend model anywhere; IC stock CFDs are on MT5 only; cTrader has L2 but no tape: CHECKED (02 §0, §10). Docs still ban futures and options "ever" (DEC-0015): CHECKED (01 §7.12). `DEC`: don't limit what we trade.)*

🌊 **Rin:** HIP-3 means "crypto venue" now also means 24/7 Tesla and gold perps with weekend internal pricing (CHECKED 02 §8.2). Model the session *state*, not the asset class.

📈 **Dana:** And futures are a ratified ban. Overturn DEC-0015 out loud, with a decision record, or someone's agent will refuse futures in six months citing it.

🪙 **Kofi:** And if I want a stock-CFD scalper at IC, it's MT5 only. The node has no MT5 execution (CHECKED 01 §2 row 37).

⚙️ **Priya:** The instrument spec should carry *data capabilities*: real volume, depth levels, tape, open interest, funding history. Then a block that needs the tape simply can't be placed on a cTrader CFD.

🦨 **Grumble:** "Any instrument" before one instrument works is scope suicide.

🎙️ **Operator's voice:** Don't limit what we trade; trade what can make money now and build up cash.

🏗️ **Hal:** Both can be true. Build the *spec shape* for every class now (cheap, all data), and the *mechanics* (funding, expiry) one class at a time.

🌊 **Rin:** Hyperliquid's candle API returns only the last 5,000 candles (CHECKED 02 §8.3). If you don't record from day one, you'll never have perp history to backtest.

🤖 **Tomás:** Results in R make cross-instrument comparison possible. QMB stores money today (CHECKED 01 §1.3).

📈 **Dana:** R isn't enough. A 1R loss on ES at the roll is not a 1R loss on EURUSD at 03:00. Carry the costs per cell.

**Agreed in the room:**
- A typed instrument spec with data capabilities.
- Fees per (venue, account, instrument).
- Calendars from the venue schedule.
- Record perp data from day one.
- Overturn DEC-0015 explicitly.

**Live disagreements:**
1. **Breadth-first spec versus depth-first FX.** Grumble versus Rin and the Operator's voice; Hal's split (spec now, mechanics per class) is a third option.
2. **Is R normalisation enough** to compare across classes (Tomás), or must cost context travel with every comparison (Dana)?
3. **Funding history.** Modelled from recorded history versus treated as pure live cost at first.

---

### Round 9: What to keep versus rebuild

*(`DEC`: QML rebuilt from scratch, with old code salvaged as ideas and tests. `SEEDS`: every algo-facing part is due a clean refactor, QMN especially (about 98k lines, never deployed). The scope rule says don't casually remove shipped work. 04 warns that QML's contract already matches the standard. 03 warns not to rewrite `project.py`, `sensitivity.py` or `sweep/axes.py`.)*

🏗️ **Hal:** Strangler pattern. Write the new QML API and let it call the old conformance and footprint underneath. Delete old parts only when the new ones pass the same golden slices.

🎙️ **Operator's voice:** QML gets rebuilt from scratch as a clean new package. Old code is salvaged as ideas and tests, not copy-pasted, then deleted once replaced.

🦨 **Grumble:** A rewrite is three weeks of nothing working. You just got the data round merged.

🧠 **QA-7:** I don't care which, as long as the door ships first. Build the door against the *contract*. Then the inside can be rebuilt without breaking me.

🛡️ **Margaret:** QMN: keep the kill line, the KSA levels, reconciliation. Those are scar tissue. Cut the proof campaigns and the ML pipeline.

🧬 **Sven:** QMB: don't touch What-If, sensitivity or the sweep. That's your StrategyQuant already.

🔬 **Ilya:** And pick *one* home for the anti-luck maths. Today the deflated Sharpe sits idle in template scripts, PBO is deferred in QMB, and the Lab designs a third home (CHECKED 01 §7.5).

🏗️ **Hal:** And `qmf-registry` versus the Library. Two registries in code today (CHECKED 01 §6 row 11). The unit should land in the Library kind that already has its tabs.

**Agreed in the room:**
- Door first, built against the contract.
- Keep QMB's analysis, optimise and sweep pieces.
- Keep QMN's safety core.
- One home for the anti-luck maths.
- The unit lands in the Library `unit` kind.

**Live disagreements:**
1. **QML.** Clean rebuild (`DEC`) versus strangler refactor (Hal) versus "freeze it, add on top" (Grumble).
2. **The QMN cut line.** What exactly is "basic".
3. **Registry.** `qmf-registry` or the Library as the long-term record home.

---

### Round 10: The Judge (how each part proves it compounds)

*(MAP: a part is good if it raises edge per trade, trade count or right size, or cuts drag, and the Judge step can prove it.)*

🔬 **Ilya:** Ablation. Replay the whole unit system on held-out months, with the router on and off, with the self-tuner on and off. A part that shows no lift goes on the backlog, not into the money path.

🏗️ **Hal:** That only works if every part is replayable. So "replayable" is the admission ticket for any money-path part.

🛡️ **Margaret:** Add a fifth lever the room keeps forgetting: *losing less in the bad weeks*. A guard that never raises growth but halves the worst month earns its seat.

🦨 **Grumble:** And a baseline that's embarrassingly simple. Static preferred list, 1/N risk, no MIS. If the clever system can't beat that, you've built a hobby.

🤖 **Tomás:** And a placebo: random entries with the same exits, sizing and cells. The edge is measured against the placebo, not against zero.

🎙️ **Operator's voice:** We can't win on speed, so we win on compounding.

🧬 **Sven:** Then measure compounding directly: geometric growth per unit of drawdown, per cell, after costs.

**Agreed in the room:**
- Ablation on held-out data.
- Replayability as the admission rule.
- Simple baselines to beat.

**Live disagreements:**
1. **A fifth lever.** Is "tail loss" its own lever (Margaret) or part of drag?
2. **The baseline.** Placebo (Tomás) versus simple-system (Grumble), or both.
3. **One growth number** (Sven) versus per-lever measures only (Ilya).

---

## 3. Brainstorming idea list

Techniques run, in order:
1. First Principles
2. Morphological Analysis (instrument × timeframe × window × strategy type × fidelity × venue)
3. Analogical Thinking / Cross-Pollination: load balancers, Kubernetes, ecology, immune systems, insurance, clinical trials, venture capital, sports scouting, software engineering, plus miscellany
4. SCAMPER on the unit
5. Reverse Brainstorming / Anti-Solution
6. TRIZ Contradiction
7. Assumption Reversal
8. Swarm Logic / Ecosystem Thinking
9. Kill the Crown Jewel
10. Time Horizon Ladder
11. Cursed Genie
12. Kit-focused Starbursting (creators and agents)
13. Build on What Works (QMB, Pods, node)
14. Wildcards

Format: **Lens** · **Surface** · **Touches** · **Lever**. Nothing here is ranked.

### 3.1 First principles (what is irreducible)

1. **The bet atom.** Store every trade, backtest or live, as one atom:
   - signal reason and strength
   - entry, exit plan and size
   - venue cell and times
   - result in R, MFE and MAE
   - the entry-time MIS state vector

   Every later idea reads this. · A, T · Algo (QMB measures, node journals) · `qmb` measures, `qmf-risk realized_r`, Library `trade` kind · P (prerequisite).
2. **Unit as a pure value.** (logic fingerprint, profile version, record pointer). Hosting belongs to QMB or a node seat. · A · Algo · Library `unit.schema.json`, ATC/PolicyPair seam (01 §7.6) · P.
3. **Cost ratio as the first column of every cell.** Round-trip cost ÷ the unit's average target, against its proven ceiling. · T · Pods, MIS · SQS, registry, QMB cost port · D, E.
4. **Proof as a sealed-data event.** A registry proof counts only if its run read through the market-data door with the seal. The door stamps a proof grade. · A · Algo · `qmx_host/market_data.py`, `library_landing.py` · P.
5. **Tries as a currency.** Every call at the QMB door is auto-ledgered as a trial with a family id, with no opt-out. · A · Algo · QMB ledger roles `trial`/`replicate` · P.
6. **The speed limit is information per bar** (Lorden). The router's fast lane reads only directly observed states (spread, tick rate, depth, high-low range). Regimes go to a slow lane. · A, T · MIS · `qmn/mis/labelers.py` · D.
7. **Sizing has three honest inputs:** shrunk edge, variance, distance to the floor. Everything else (HME, strength, sessions) must show marginal lift to stay. · T, A · Pods, unit · `qmf-risk/sizing.py` · S.
8. **A placement is a claim with an expiry.** Every router placement is a dated claim: "unit U in cell C until T, because evidence E". · A · node/router · new Library `placement` record · P, D.
9. **The record is the unit's memory.** Sizing, exits and placement all read the same record. One fold, many views. · A · Algo, Pods · Library `unit` "Markets" tab · S, P.
10. **A guard is a bet too.** Every guard (SQS block, news block, bench) has a cost (blocked winners) and a benefit (blocked losers), and both are measurable in replay. · A, T · node, QMB · guards, `analysis/project.py` · N, D.

### 3.2 Morphological analysis (instrument × timeframe × window × type × fidelity × venue)

11. **Gold × 1m × post-LBMA-fix × sweep reversal.** Avoid fix entries and trade the revert after the fix. · T · registry cell, window axis · QMB window axis (missing, 01 §2 row 16) · N.
12. **Index CFD × 5m × first 30 min of the cash open × noise-area breakout with a VWAP trail** (the Zarattini design, CHECKED 02 §4.3). The first *reference unit* to drive the whole pipeline end to end. · T, A · Lab template · QML templates, QMB, VWAP runnable · P, N.
13. **HIP-3 stock perp × weekend × internal-pricing state × reversion inside the discovery bounds.** A hypothesis cell only; the evidence is contested (02 §8.2). · T · registry hypotheticals · instrument spec session state · N.
14. **Perp × 1m × funding-hour boundary × a "don't hold across the hour unless paid" exit block.** · T · QML exit block · QMB financing port (perps missing) · D.
15. **FX cross × Asian session × range mean reversion with a change-point stand-aside.** · T · Lab template · `qmf-indicators`, T2 flag · E.
16. **ES/MES × RTH open × tape absorption sniper.** Parked: needs a futures broker and paid data first.
17. **Crypto spot × 16-17 UTC liquidity peak × momentum with maker entries** (CHECKED 02 §8.3). · T · registry window · CCXT spot path · N.
18. **Fidelity as a grid axis.** Run every cell at M1-OHLC and at tick-with-real-spread; the cell's proof takes the worse one. · A · QMB sweep · `execution/fidelity.py`, `sweep/axes.py` · P, D.
19. **Venue as a grid axis.** Run the same logic on IC cTrader, IC MT5 and Hyperliquid as cost-twin cells. The registry shows which broker is cheapest for each unit. · T · registry, Pods · instrument spec, cost port · D.
20. **Find a logic's native clock.** Test it on tick, volume, range and Renko bars as well as time bars (LEAN consolidators, 04 §3.4). · A, T · QMB · runloop BarSpec derivation · N, E.
21. **A window library generated from venue schedules.** Opens, overlaps, fixes, rolls, funding hours and close-only phases, as data. The window axis draws from it. · T · MIS, calendars · `qmf-calendar` beyond forex · N.
22. **Mean reversion only in the post-news cooldown** (30-90 min after high-impact news; entries stay off during news). Hypothesis cells only. · T · registry window · news windows (exist) · N.
23. **Auto-built type × data-capability matrix.** The Lab greys out blocks an instrument's data cannot feed (no tape on cTrader CFDs). · C, A · Lab · instrument spec data caps, block catalogue · D.
24. **Account type as an axis.** Raw versus swap-free (pays a rollover commission, 02 §2.1), netting versus hedging. Each is a distinct cost cell. · T · registry · instrument spec, cost port · D.
25. **Holding-time band as an axis.** The same logic with time barriers of 5, 15 and 60 min forms a cell family. It shows where a "scalper" is really an intraday bot. · T · QMB sweep · exit time barrier · E.
26. **Direction as an axis.** Long-only and short-only cells per instrument. Many FX/gold edges are one-sided by session. · T · registry · sweep axis · E.
27. **Gap regime as an axis.** Monday-open, post-holiday and post-rollover cells kept separate from normal cells. · T · registry · gap-event labeler (exists) · D.

### 3.3 Analogies: load balancers and Kubernetes

28. **Health checks.** The router probes each seated unit nightly with a live-versus-replay drift check. An unhealthy unit is drained, not killed. · A, T · node/router · `analysis/compare.py`, node journals · D.
29. **Connection draining.** An unseated unit may only manage and close its open trades. No new entries. · A · node seats · CT-23 intents · D.
30. **Weighted round robin by proof weight.** Capital per cell ∝ shrunk posterior × breadth factor. · A, T · Pods allocator · pod blocks · S.
31. **Canary seat.** A new cell gets a min-lot canary seat while the parent keeps full size. It is promoted when an e-value crosses its threshold. · A, T · node, registry · seat admission · S, P.
32. **Sticky sessions.** A trade opened in cell X is managed under X's profile until it closes, even if the router moves the unit. · A · node seats · D.
33. **Circuit breaker with a half-open state.** A benched unit gets one probe trade at min size. A win closes the breaker; a loss re-opens it for longer. · T · unit risk profile · bench (exists in the node) · S.
34. **Taints and tolerations.** Cells taint themselves: high spread, roll week, close-only, funding extreme, HIP-3 weekend pricing, data degraded. Units declare which taints they tolerate. The router schedules on that. · A, C · router, registry · registry schema, MIS labelers · D, N.
35. **Affinity and anti-affinity.** A unit can prefer cells near its proven ones (affinity) and is kept apart from units in its own correlation family (anti-affinity). · A · router · ONC families · D.
36. **Resource quotas.** Hyperliquid's request budget, cTrader's 50 + 5 requests per second and the open-order caps become node-level resources the router allocates across units. · T, A · node/router · venue adapters · D.
37. **Autoscaling.** Seats per unit scale with proven breadth, not ambition, with a symmetric scale-down rule. · A · Pods · N.
38. **Blue-green profile switch.** A new profile version runs in shadow beside the live one for N trades before cut-over. · A · node paper · profile versioning · S, P.

### 3.4 Analogies: ecology

39. **Niche vector.** Register each unit's state profile as its niche. Two units in the same niche compete; route only the stronger one there (competitive exclusion = correlation control). · T, A · registry, Pods · ONC clustering · D.
40. **Carrying capacity per cell** (our own slippage impact). Parked: irrelevant at $300, matters later.
41. **Succession.** Formalise the vault's young → mature session specialists (CHECKED G09 A.3) as a maturity stage in the cell states. · T · registry · cell state machine · P.
42. **Invasive-species check at admission.** A newcomer highly correlated with the book but with a lower edge is refused. · A · Pods admission · D.
43. **Seasonal migration (three capitals).** Separate capital pots for Tokyo, London and New York, as the operator described (CHECKED G09 A.6). Test against a single daily budget. · T · Pods · budget block · S, N.
44. **Fossil record.** Retired units are kept with their cause of death. Agent memory checks fossils before generating ("rejected ideas are not proposed again", with an expiry; 03 H20). · A · Copilot memory, Library · P.
45. **Keystone units.** Find the units whose removal hurts the whole book most (marginal tail contribution). Protect their seats. · T · Pods · fit-to-portfolio · S.
46. **Food web of signals.** Map which blocks feed which units. A broken block (a bug) shows every unit it touches. · A · Library edges · `uses` edges · D.

### 3.5 Analogies: immune system

47. **Self versus non-self.** A unit's "self" is its replay distribution (the MC cone). Live behaviour outside it triggers a graded response: shrink, then paper, then bench. · T, A · unit, node · Predict & Verify (03 row 18) · S, D.
48. **Memory cells.** When a state signature once broke a unit, store it. The router shrinks pre-emptively when it recurs, but only after the signature is proven out of sample. · A · MIS, registry · D.
49. **An autoimmunity guard.** Measure each guard's blocked-trade cost: what the blocked trades would have done in replay. A guard that blocks winners must justify itself. · A, T · node guards, QMB · N, P.
50. **Clonal selection = domain expansion.** A proven unit clones into neighbour cells; only clones that bind (prove out of sample) proliferate. · A · domain-expansion workflow · N.
51. **Fever.** A system-wide stress state (correlation spike, one eigenvalue dominating) lowers every size at once. · T · account guard · eigenvalue spread (G09 D.2) · S, D.
52. **Vaccination.** Every new unit is run against a library of named stress episodes (flash moves, holiday gaps, roll days) before paper. · A · QMB · `stress-scenario` kind (exists) · D, P.

### 3.6 Analogies: insurance

53. **Actuarial reserve.** Each unit's capital floor comes from its MC loss tail (03 H7). · T · Pods · S.
54. **Deductible.** A unit absorbs its first loss points itself before the pod escalates. · T · unit, pod · loss points · D.
55. **Reinsurance cap.** Total exposure to one correlation cluster is capped at the pod. · T · Pods caps · D.
56. **Credibility weighting.** A unit's size credibility = n ÷ (n + k), Bühlmann's formula. It is the same maths as shrinkage, in words an operator can read. · T, A · unit sizer · S.
57. **Moral hazard split.** The agent that built a unit never proposes its promotion. A separate judge agent with separate memory does. · A · Copilot · P.
58. **Exclusions clause.** Each unit's admission lists the states and venues it is *not* covered for. The router reads these as hard taints. · T, C · registry · D.

### 3.7 Analogies: clinical trials

59. **Phases.** Phase I = safety (does it break, do costs fit). Phase II = efficacy on an unseen month. Phase III = live min-lot incubation. Registry states follow the phases. · A, T · registry, Lab · P.
60. **Data-safety monitoring board.** An independent monitoring agent with pre-registered stopping rules can stop a trial early for harm or futility. · A · Copilot · P.
61. **Pre-registration.** The study plan is locked before data is touched, and the ledger refuses verdicts that don't match it (03 H14). · A · QMB, Library `setup` kind · P.
62. **Response-adaptive randomisation.** A Thompson budget allocates paper and min-lot slots across hypotheses. · A · Pods exploration slot · N.
63. **Placebo arm.** Every study runs a random-entry twin with the same exits, sizing and cells. The edge is measured against the placebo, not zero. · A, T · QMB · new robustness method · P.
64. **Intention-to-treat.** Trades skipped for size or blocked by guards stay in the unit's analysis as their own category, so the record can't flatter itself. · A · QMB measures · P.

### 3.8 Analogies: venture capital

65. **Follow-on funding = alpha-investing.** A proven parent earns "wealth" that funds its children's tests; a failure spends wealth (05 §7.2). · A · domain-expansion workflow · P, N.
66. **Power-law exploration.** Many tiny bets, most die, budget for the few winners. · T · Pods exploration budget · N.
67. **Term sheet per admission.** Every unit enters live with explicit terms: max loss, review date, kill conditions, toleration list. One plain page for the operator's click. · T, C · Lab, Portfolio UI · P.
68. **Pro-rata rights.** A proven unit has first claim on budget freed by retired units in its niche. · T · Pods · S.

### 3.9 Analogies: sports scouting and minor leagues

69. **Farm league table.** Paper units ranked per cell, in plain words. Units get "called up" to live by the operator. · C, T · mini app · P.
70. **Scouting reports.** Agent-written, plain-words page per unit: strengths, weaknesses, niche, cost sensitivity. · C · Copilot, Lab · P.
71. **Positional roster.** A pod needs types covering states (mean reversion for range, momentum for expansion, sniper for change-points). The router fills positions. · T · Pods · D, N.
72. **Injury list.** Benched units show why, since when, and their return condition (freqtrade-style lock records, 04 §4.2). · C, T · Portfolio UI · D.

### 3.10 Analogies: software engineering

73. **Semver for strategies.** Major = logic change (new strategy), minor = new cell (variant), patch = profile retune. One plain rule for the identity question. · C, A · Library, registry · P.
74. **Blame for numbers.** Library blame (DR7/8, CHECKED 01 §5) traces each profile number to the evidence run that set it. · A · Library · P.
75. **Proof lockfile.** A unit's proof pins data-month fingerprints, the cost-calibration version, the QMB version and the seed. · A · `library_landing.py` · P.
76. **Feature flags with an ablation button.** Every guard and sizer feature toggles per unit, with "replay without it". · A, C · Lab · P.
77. **CI for strategies.** Every bot version runs look-ahead, recursive, smoke and 2× cost-stress. Red cannot register. · A · QML conformance · P, D.
78. **Package registry for blocks.** Each block carries its proof stats ("raised E in 14 of 20 units it was tried in"). · C, A · block catalogue · E.
79. **Deprecation policy.** A block found buggy is marked deprecated, and every unit using it gets a rerun ticket. · A · Library edges · D.

### 3.11 Analogies: miscellaneous

80. **Weather ensemble.** The router runs several state models; their disagreement means uncertainty, which means a smaller size. · A · MIS · S.
81. **Chess opening book.** Per instrument × window, a book of unit types that historically worked there. New units start from the book. · T · registry · N.
82. **Air-traffic separation.** No two units enter the same instrument in the same direction within N seconds unless whitelisted. · T · node · D.
83. **Kidney-exchange matching.** Bipartite matching of units to cells that maximises total shrunk edge under correlation caps: a formal router. · A · router · N, S.
84. **Spinning reserve.** Keep budget slack for the premium windows. Don't spend London's budget in a weak Tokyo. · T · Pods budget · S.
85. **Credit ratings.** A plain letter grade per unit from proof grade, MinTRL coverage and drift. · C · Portfolio UI · P.
86. **Franchise kit.** A unit template that a new instrument adopts with local adjustments (costs, sessions). Variant creation as a guided flow. · C · Lab · N.
87. **Airline overbooking.** Admit slightly more paper hypotheses than live slots, knowing most will fail. · T · Pods · N.
88. **Restaurant health inspection.** A random audit agent picks one live unit a week and re-derives its proof from scratch. · A · Copilot · P.

### 3.12 SCAMPER on the unit

89. **Substitute** heavy self-tuning with fixed-fractional sizing plus credibility shrinkage. One tuned number. · T · unit · S.
90. **Combine** each unit with its placebo twin, always run together in paper. · A · node paper · P.
91. **Combine** the registry with What-If. Hypotheticals are auto-created from projections and graduate on unseen windows (03 H3). · A · registry, QMB · P, N.
92. **Adapt** freqtrade protections as lock records with reasons for the "why is it paused" screen (04 §3.5). · C, T · Portfolio UI, unit · D.
93. **Magnify** the record so a unit knows its own MFE/MAE paths and *proposes* exit retunes as new versions for the judge. · A · Copilot, QMB · E.
94. **Minify** self-tuning to at most three numbers: risk fraction, loss-point limit, session weights. · T · unit · S.
95. **Put to other use:** the MC cone as a live "expected path" ribbon on each unit's page. · C · Portfolio UI · P.
96. **Put to other use:** QMB's sweep machinery to backtest the router itself (router replay). · A · QMB · P.
97. **Put to other use:** the SQS seasonal baseline as the template for every fast state (vol, tick rate, depth, cost; 05 §8.1). · A · MIS · D.
98. **Eliminate** HME and RHME per unit until its autocorrelation test passes. · T · unit · S, D.
99. **Eliminate** stored pass/fail entirely: read-time folds only (DEC-0162). · A · QMB, Lab · P.
100. **Reverse:** markets "bid" for bots. Each cell posts its conditions and units bid with proof (the old slot auction, CHECKED G09 A.1, scored by proof). · A · router · N.
101. **Reverse:** units start as hypotheses everywhere and proof prunes top-down, instead of growing bottom-up. · A · registry · N.
102. **Rearrange:** sizing decided *before* the router (unit says "I'd risk x here"); the router picks the best marginal x across units. · A · router, Pods · S.

### 3.13 Reverse brainstorming: how would we lose money? (each with its inversion)

103. Trade the 1m and 5m variants of one logic at full size together. **Fix:** the correlation ledger counts them as one bet with a shared budget. · T · Pods · D.
104. Let the fail branch search 200 contexts and trade the best. **Fix:** post-search sealed months plus alpha wealth. · A · workflow · P.
105. Trust uncalibrated costs. **Fix:** no registry proof without a calibration artifact; an interim "2× cost-stressed" proof grade. · A · QMB · D, P.
106. Let the router decide on unrecorded live inputs. **Fix:** a router decision journal, recomputable. · A · node · P.
107. Let agents run raw Python against the libraries and skip the seal (CHECKED 01 §7.14). **Fix:** money-relevant proof only through doors; shell runs are tagged "ungoverned". · A · Copilot, QMB · P.
108. Let a tighten-only ratchet drift units to minimum size. **Fix:** a floor ratchet plus evidence-gated loosening. · T · unit · S.
109. Key history by symbol across futures-CFD expiries. **Fix:** an instrument chain id. · T, A · instrument spec · D.
110. Place a stop beyond the liquidation price on a perp. **Fix:** an admission check of the stop against the liquidation price per size and leverage. · T · node · D.
111. Let the min lot force an over-bet on $300. **Fix:** skip, and count "skipped for size". · T · unit · S.
112. Stack guards until nothing trades. **Fix:** each guard's blocked-trade cost (idea 49). · A · node · N.
113. Let a martingale grid pose as an 85 %-win scalper. **Fix:** an averaging-down detector guard (02 §11 row C). · T · QMB, Copilot · D.
114. Hard-code session clocks and break on daylight saving. **Fix:** windows only from the venue schedule. · T · calendars · D.
115. Trade on a stale feed. **Fix:** the feed-state labeler (exists) as a mandatory fact. · A · node · D.
116. Promote five units the same week. **Fix:** an admission rate limit, "one in flight". · T, C · Portfolio · S.
117. Let a cTrader token refresh on one machine kill the others (CHECKED `SEEDS`). **Fix:** one owner per grant. · A · node · D.
118. Fund hypotheticals from an unproven similarity measure. **Fix:** validate that feature distance predicts the performance gap first (05 §2.3). · A · QMB · P.
119. Let a composite Lab score seduce the operator. **Fix:** a per-lever scorecard only (03 H5). · C · Lab · P.
120. Let the same agent build, test and judge. **Fix:** role separation (idea 57). · A · Copilot · P.
121. Re-label the past when a regime model is refit. **Fix:** store labels as computed at the time (05 §1.5). · A · MIS, QMB · P.

### 3.14 TRIZ contradictions

122. **Breadth versus luck.** More cells mean more tries. Separate in structure: hierarchical pooling plus ONC effective N, so near-duplicate cells cost fractional tries. · A · QMB, registry · P, N.
123. **Fast versus false alarms.** Separate by error cost. The fast lane may only shrink or pause (cheap errors); the slow lane may change placement (costly errors). · A, T · MIS, router · D.
124. **Agent freedom versus determinism.** Separate in space. Anything goes in an "open" scratch area; only compiled artifacts through the door count. · A, C · Lab · P.
125. **Self-tuning versus stability.** Separate in scale. Units tune within their ranges; only the pod or a human changes ranges. · T · unit, Pods · S.
126. **Creator simplicity versus governance.** One Python file; an agent infers the declaration and the human confirms it in plain words. · C · Lab, Copilot · N.
127. **Edge versus correlation.** Route by *marginal* edge given the live book, not raw edge (fit-to-portfolio, 03 row 10). · T · router, Pods · D, S.
128. **Speed versus truth in QMB.** Separate in time. A fast ungoverned screener first, then a governed rerun of survivors; both count tries. · A · QMB · N, P.

### 3.15 Assumption reversal

129. **"Bots never read the MIS" → bots may read declared *facts* (session, spread) but never MIS *opinions*.** Opinions go only to the router and the meta-labeler. This reconciles the `DEC` lean with `SEEDS`. · A, T · QML, MIS · footprint declared streams · E.
130. **"The router places bots" → two layers.** Placement routing (days) plus trade-level routing (the meta-label take/skip/size, 05 §3.2). · A · router, unit · E, S.
131. **"Units tune themselves" → the family tunes them.** A unit with few trades borrows its type family's sizing prior. · T · unit sizer · S.
132. **"Proof comes from backtests" → backtests mainly reject.** Proof comes mostly from live min-lot incubation (the SQ practitioner pattern, 03 §2.3). · T · Pods, node · P.
133. **"Exits are part of the strategy" → entries frozen, exits chosen.** A swappable set of pre-proven exit blocks the unit picks among; the exit becomes a variant axis. · T · QML, unit · E.
134. **"Stage tags are linear per strategy" → stages per cell.** Live on EURUSD-London while still in research on gold. · A · registry · P.
135. **"One node" → many small nodes near venues,** each with a router slice. Parked: later (latency is out of scope today).
136. **"The operator promotes" → the operator sets policy and the system promotes within it.** A provocation only; it conflicts with the standing rule that the human promotes. Kept to mine the principle: make his click a *policy* click where possible. · C · Portfolio · S.
137. **"Strategies are found, then placed" → markets are studied, then strategies are written for them.** A market dossier per instrument × window comes first; agents write logic to fit it. · T, A · Copilot · E.

### 3.16 Swarm logic and ecosystem

138. **Dumb local rules.** Each unit shrinks on its own loss points, pauses on its own drift, and asks for more only with an e-value. No master allocator in v1. · T · unit · S.
139. **Stigmergy.** Cells where many unit types thrive get exploration priority for new types. · A · registry · N.
140. **Quorum sensing.** If several independent units in different niches all hit loss points in the same hour, treat it as a market event, not unit failure (fever, idea 51). · T, A · account guard · D.

### 3.17 Kill the crown jewel (baselines every part must beat)

141. **No router.** Units trade all their preferred cells, gated by facts only. The router must beat this. · A · QMB ablation · P.
142. **No backtester.** Pure live min-lot incubation across many cells on a fixed monthly spend. This bounds what QMB is worth. · T · Pods · P.
143. **No self-tuning.** Fixed 1/N risk per unit (the honest default, 05 §3.3). Every sizer must beat it. · T · Pods · S, P.
144. **No MIS states.** Placement by session and time only. · A · QMB ablation · P.
145. **No exits innovation.** Fixed ATR stop and target for all units. Every exit block must beat it. · T · QMB · E, P.

### 3.18 Time horizon ladder

146. **1 month:** one reference unit (idea 12) end to end: Python → door → windowed replay → registry cell → paper. Everything else waits on it. · A · all · P.
147. **1 year:** about 10 units on FX, gold and index CFDs, one node, R everywhere, tries ledger live. · T · all · N.
148. **3 years:** shift to spot only (`SEEDS` horizons). Design the R-normalised record now so units port to spot later. · T · registry · D.
149. **Later:** cross-venue latency nodes. Parked (02 §11 row 9 drops it).

### 3.19 Cursed genie (granted wish → disaster → patch)

150. "Find where every strategy works." → Everything works somewhere in-sample. **Patch:** alpha wealth plus a post-search seal. · A · workflow · P.
151. "Units tune themselves." → Everything tunes to zero size. **Patch:** a floor ratchet and a minimum risk unless benched. · T · unit · S.
152. "Agents build any strategy." → 10,000 near-duplicates. **Patch:** `blocks.search` before writing, family dedupe, a per-agent tries budget. · A · Copilot · P.
153. "Any instrument." → Buys depth on 30 exchanges. **Patch:** data-entitlement cost shown and approved per instrument class (fees CHECKED 02 §7.2). · C · Connections UI · D.
154. "Never lose money." → Never trades. **Patch:** the blocked-trade cost of every guard (idea 49). · A · node · N.

### 3.20 Kit-focused starbursting (creators and agents)

155. **"Explain my strategy back to me."** An agent reads the Python and writes plain-words rules plus a flow diagram. The creator confirms, and that becomes the declaration. · C · Lab, Copilot · N.
156. **Video → tested strategy in one visible flow.** Source kind → idea card → template slot fill → validate → smoke → first backtest, with tries shown. (Intake templates exist, CHECKED 01 §2 row 19.) · C, A · Copilot templates · N.
157. **Vanilla and spiced pairs revived** (CHECKED G09 A.10). Each source idea yields a vanilla and a spiced variant, both tested and counted. · A · Copilot · N, E.
158. **Notebook → bot compile.** A Lab notebook cell marked "this is my strategy" compiles to the QML artifacts. · C · Lab · N.
159. **A template per scalper type** (the 9-type draft as revised in 02 §11), with default exits and default router tolerations. · T, C · QML templates · N.
160. **Strength calibration curve.** QMB reports strength versus realised R per block; strength feeds size only once calibrated. · A · QMB · E, S.
161. **Mandatory signal expiry for resting entries** (LEAN Insight period, 04 §3.1). · T · QML intents · E, D.
162. **Dry-plan door.** The agent submits a study plan; the door returns cost, tries it will consume, and whether the seal opens. · A · QMB door · D, P.
163. **Golden-scenario tests by creators.** "At this chart moment I expect a long", kept with the bot. · C · QML conformance · P.
164. **"Why did it fail?" button.** QMB attributes losses to states, costs and exits. Feeds the fail branch. · C, A · Lab · P.
165. **Per-agent tries budget shown in the Copilot.** "40 tries left in this family this month." · A · Copilot · P.
166. **ONNX models as declared, hashed artifacts** (MT5 pattern, 04 §3.8). · A · QML · E.

### 3.21 Build on what works (QMB, Pods, node)

167. **The windowed M1/tick reader as the first card for anything scalper** (CHECKED 01 §0.5). · A · QMB `host/replay.py` · N (enabler).
168. **MIS labelers run inside QMB on replay data,** the same code, stamping states on every backtest trade (01 §7.9). · A · QMB, MIS · P.
169. **Break-even cost per cell.** Report the cost multiple at which the edge hits zero. One readable number per cell. · T, C · QMB sweep cost axis · D.
170. **Two-speed router.** A central planner (days) writes a signed placement plan with an expiry. The node gate applies fast facts and taints, and runs on the cached plan if the PC disconnects. · A · node, router · D.

Further ideas logged during the run, beyond the 170:
- **Router self-test on connect** (from the `SEEDS` self-test idea). On connect, the node replays yesterday's placement decisions and must match them. · A · node · P.
- **Rising floor with a kill-line readout.** A Grossman-Zhou rising floor with α previewed in the pod simulator, plus a "chance of touching the kill line" readout (05 §8.5). · T, C · Pods · S.
- **Eigenvalue-spread correlation "right now".** Rolling, across live cells. Dominance means breadth counts as one bet. · T · Pods · D, S.
- **Pod/unit slot split (a hybrid for round 1).**
  - The pod holds inputs, guards, allocator, caps, ledger and the exploration budget.
  - The unit holds sizer and throttles.
  - Blast radius: LP AD-10/11, `PodCompilerPort`. · A · Pods · S.
- **Shadow paper on every preferred cell,** even when not seated: continuous evidence with no capital. Conflicts with DEC-0261 (no per-bot paper), so it would be a recorded overrule. · A · node paper · P.
- **Operator veto diary.** Each rejection, with its reason, becomes judge-agent memory. · C, A · Copilot memory · P.
- **"Market weather" mini app.** Plain-words daily state per instrument from the MIS. · C · mini app · P.
- **Animated family-tree explainer per strategy** (his preference for explainer pages). · C · Lab · P.
- **Hummingbird budget.** A fixed monthly real-money "data purchase" for min-lot exploration across many cells. Live incubation treated as buying evidence. · T · Pods · N, P.
- **Strategy-cell "dating" mini app.** Shows agent-proposed unit ↔ cell matches with their proof. · C · mini app · P.
- **Drive a licensed SQX through its MCP as an external generator** (03 §6.2). Its candidates enter as dev-zone tries. Needs his licence decision. · A · Copilot · N.
- **cTrader twin as an independent parity check on QMB numbers** (04 §5 #9). Parked: later.
- **Units as portable shareable cards across QMX installs.** Parked: doesn't fit yet.

---

## 4. Disagreement register (for the converge step; unresolved on purpose)

| # | Question | Side A | Side B | Other positions |
|---|---|---|---|---|
| D1 | Unit grain | One logic with many cell seats (Hal) | One unit per cell (Dana) | — |
| D2 | Time windows | In the strategy bytes (Kofi) | Router/node facts (Priya, `DEC` lean) | Both: logic may declare windows; the router adds proven ones |
| D3 | Meta-labeler home | Unit sidecar (Tomás) | Router per-unit model | Don't build it (Grumble) |
| D4 | What a pod is | Frame: guard + allocator (Margaret, `DEC:75`) | Seven-slot sizing stack (Hal, LP AD-10/11) | Slot split (idea list, "further ideas") |
| D5 | Identity basis | Bytes (Hal) | Behaviour (Ilya, Sven) | Identity = bytes, family = behaviour |
| D6 | Exit tweak | New strategy (strict `DEC` lean) | A setting within ranges (QA-7) | Exit as a variant axis (idea 133) |
| D7 | Router location | Central planner | Node gate | Two-speed (idea 170) |
| D8 | Registry form | Stored key-value (`SEEDS`) | Query over results (Sven) | Query for proof, record for placement (Hal) |
| D9 | Hypothesis selection | Similarity (`SEEDS`) | Bandit budget (Ilya) | Both, with similarity validated first |
| D10 | Promotion authority | Numeric rule, agent or workflow | Operator click | Operator sets the policy (idea 136, provocation) |
| D11 | Fail branch | Exists, strictest rule (Operator's voice, Ilya) | Shouldn't exist (Grumble) | — |
| D12 | Stopping rule | Statistics (alpha wealth + MinTRL) | Compute and time budget (Hal) | Operator judgment per branch |
| D13 | Expansion mutates logic? | Yes, rewrite branch (`SEEDS`) | Frozen variants only | Rewrite starts a new tries budget |
| D14 | Loosening size | Human only (Margaret) | Evidence-gated automatic (Ilya) | Floor ratchet only |
| D15 | House money default | On (Kofi) | Off until the autocorrelation test (Ilya) | — |
| D16 | Exits | Frozen in compiled logic (`DEC`) | Unit picks among proven exit blocks | — |
| D17 | QML | Clean rebuild (`DEC`) | Strangler refactor (Hal, 04) | Freeze and add on top (Grumble) |
| D18 | Vectorised authoring | Allowed with a parity check | Event-only | — |
| D19 | Block catalogue growth | Curated (Grumble) | Librarian-grown (`DEC`) | — |
| D20 | QMB speed | Fast screener lane (Sven) | Single governed loop (Hal) | Both lanes, tries in both |
| D21 | Scoring | Stored composite fitness (Sven) | Sort-only lenses (DEC-0162) | — |
| D22 | Monte Carlo | Selection gate | Sizing input only (Tomás, 03 H7) | — |
| D23 | Instruments | Breadth-first spec (`DEC`, Rin) | FX depth-first (Grumble) | Spec now, mechanics per class (Hal) |
| D24 | Cross-instrument comparison | R is enough (Tomás) | Cost context must travel (Dana) | — |
| D25 | Tail-loss lever | A fifth lever (Margaret) | Part of drag | — |
| D26 | Judge baseline | Placebo (Tomás) | Simple system (Grumble) | Both |
| D27 | Registry store | Library | `qmf-registry` | — |
| D28 | Using SQX via MCP | Yes, licences permitting (Sven) | Never trust a black box (Hal) | — |

## 5. Not verified

- Every persona claim that is not tagged CHECKED is an opinion or an INFERRED reading.
- Facts tagged CHECKED were taken from the input research files (01-05, G09, `SEEDS`, `DEC`). I did not re-read code for this file.
- No web sources were used here. The research files already cite theirs.
- The arithmetic quoted (MinTRL, Kelly drawdown, detection lags) is 05's INFERRED arithmetic. It was not re-derived.
