> STATUS 2026-10-16 (rubric walk): KEEP-AS-SOURCE. See 27-rubric-walk.md. Rulings in 26 win.

# 09 — The self-configuring unit: what the risk session is proposing, and what we must keep loose

Written 2026-10-16 by a read-only research agent. Nothing here is a decision. Labels: `[retrieved]` from a file or transcript, `[inferred]` reasoned here.

Short names for sources:
- **HO** = `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\HANDOFF.md`
- **DEC** = same folder, `decisions.md` (the living record; "Agreed" vs "Baseline" vs "Open")
- **F05** = same folder, `grounding\05-findings-2026-10-13.md`
- **T13** = session `b3275c9d-…` ("QMX patient sizing risk management"), 2026-10-13, under `C:\Users\Mubarak\.claude\projects\C--Users-Mubarak-Desktop-QMX\`
- **T15** = session `ea2b5af9-…` ("Risk & sizing QML redesign"), 2026-10-15, same folder. This is the newest sitting. It stops at 09:30Z after one exchange.
- **UIL** = `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair\apps\qmx-ui\UI-LEDGER.md`

Branch `plan/risk-sizing` has no commits of its own. It points at the same commit as `main` (c3e8ec5e). The worktree `.worktrees/risk-sizing` is clean. Everything lives in the git-ignored workroom and the transcripts. `[retrieved]`

---

## 1. The proposal in plain words

### Where it came from
- **8 Oct (old session, his dad's account):** he proposed that each bot gets "its own self-configuring risk and sizing system", like game-engine characters or responsive web layouts, with a router in the middle "like a load balancer". The agent said it was buildable with one rule: **a bot may tighten its own brakes, never loosen them** (T13, assistant timeline 16:48Z and recap 15:55Z). `[retrieved]`
- **13 Oct:** "can we design the bots … to literally be self-adjustable, self-contained? … what do we actually need to have?" (T13 16:56Z). He also said the MIS is not out of scope, because it is "one of the key factors" in "an all-in-one [bot] with self-configuration" (T13 16:44Z). `[retrieved]`
- **15 Oct:** "remember the old systems were … separating all the things all together. This new thing I'm trying to create is combining all of them into one … so we can't just create one and then assume a baseline" (T15 09:29Z). `[retrieved]`

### What the "unit" bundles (baseline, NOT agreed)
DEC:68 records the baseline:
- **Strategy:** its DNA, including the strategy's own exits and the market conditions it needs.
- **Risk profile:** safety exits, house money, reverse house money, Kelly ceiling, size ramp and loss points. It tunes itself.
- **Conditions:** what the MIS must answer for this strategy.
- **Journal:** paper and live sections, measured in R.

A **router** sits in the middle and an **account guard** sits around everything. `[retrieved]`

Placement in the same baseline (DEC:70-74) `[retrieved]`:
- **Inside the unit:** house money, reverse house money, Kelly, bench and decay.
- **In the MIS:** it answers the unit's condition needs, with market physics inside the MIS. The SQS is a trade gate (block, optionally shrink).
- **In the account guard:** kill switch, news, money rules, correlation.

### What "self-configuring" means
- Each bot carries its own risk settings, and those settings **tune themselves from that bot's own record** (test, paper, live). This is the "Self-adjusting units" line under **Agreed** (DEC "System shape"). `[retrieved]`
- **Calibration:** statistics first (percentiles, Bayesian ramp, bandits), machine learning later. This is baseline (DEC:81). `[retrieved]`
- **15 Oct reframe (Claude's proposal, not yet answered by him):** the unit decides one thing, dollars risked per trade `r`. It derives `r` from the strategy's measured stats per context (win rate, average win, average loss, cost, trades per day, spread of results) and the account cushion `D = equity − kill line`, plus an accepted chance of hitting the kill line, `ε`:
  - `r ≤ 2·EV·D / (s²·ln(1/ε))`, capped by Kelly.
  - Strategies, time windows and MIS states are ranked by `n·EV²/s²`.
  - An MIS filter earns its place only if it raises that score after its own cost is counted.

  He was asked for one number, `ε` (T15 09:30Z). `[retrieved]`
- **MIS per type:** "different scalper types need different MIS configurations" (DEC, Agreed, System shape). `[retrieved]`

### Status: agreed vs open
| Item | Status | Source |
|---|---|---|
| Self-adjusting units: each bot gets its own self-tuning risk settings | **Agreed** (as a direction) | DEC System shape |
| Account limits (kill line, loss budget, correlation, kill switch, news, venue rules) sit **outside** units | **Agreed** | DEC; HO "Settled today" |
| MIS, SQS, physics and news are in scope; MIS configs differ per scalper type | **Agreed** | DEC |
| Exits belong to the strategy; safety exits exist; the safest exit wins | **Agreed** | DEC QML |
| One strategy record matures by stage tag (open: research to optimise; compiled: stress to live, where only the risk profile tunes) | **Agreed** | DEC QML |
| The unit's structure (what is in it, the router, pods vs units) | **Baseline, NOT agreed.** He said on 15 Oct the baseline "doesn't … have the right logic in mind" | DEC:68; T15 |
| Identity rule (new strategy vs variant vs profile version) | **Open**, he is "sleeping on it" | DEC:76-79; HO |
| "Tighten, never loosen" | Backed by the agent on 8 Oct and recalled on 13 Oct. **Not written in DEC** | T13 |
| Sizing from the cushion (the `ε` inequality) | **Proposal**, unanswered | T15 |
| Paper per bot | **Conflicts** with the docs ruling DEC-0261 (no per-bot paper on the node); marked to reopen | DEC Backlog; F05 D |

### The trading node is not in the unit
The brief says the node merges into the unit. The record does not say that `[retrieved]`:
- Venues and the node are a separate track (track 7, "ground in code first", HO plan item 3).
- The account guard stays outside units.

The nearest "merge" is a UI ruling from 3 Oct: the node screen folds into Portfolio as Live / trading servers (UIL:20, :106). `[inferred]` What merges into the unit is strategy, its risk/sizing settings, and its MIS condition needs. The node is where units run, not part of them.

---

## 2. Impact

### Portfolio: shrinks and changes job; does not vanish `[inferred unless cited]`
- **What stays (it is "outside the unit" by agreement):**
  - The account guard: kill line, account loss budget, correlation, kill switch, news, venue rules.
  - The trading servers (the node folded in on 3 Oct, UIL:106).
  - Positions and the promotion signature. "The human mainly promotes bots" (DEC).
- **What moves out:** per-bot sizing tuning. If risk settings travel with the unit and tune themselves, Portfolio no longer tunes sizing per pod. It watches, promotes, and holds the account guard.
- **"Pod" may change meaning.** The UI today treats a pod as a whole risk/sizing system you design (Lab Pods bench Design/Test/Paper; "Book + BMS is one method among many", UIL:113). The baseline makes a pod only the **frame**, meaning account guard plus router, with units inside (DEC:75). The method names "Classic Book" and "Book + BMS" already wait on this redesign (UIL:241).
- **"Run together / Allocate" may be replaced.** The router plus the `n·EV²/s²` score could pick who trades and how big, which makes hand allocation less central.
- **Still open:** whether the router lives in Portfolio (per account) or in the node.

### Lab: what it produces `[inferred unless cited]`
- **Its main output becomes a unit, not a bare strategy plus a separately designed pod.** A unit is a strategy record (with stage tag), its risk profile, its condition needs, and its journal.
- **Stages run inside the Lab, and they change what may be edited:**
  - Open stages (research, backtest, optimise): logic and settings can change.
  - Compiled stages (stress, paper, live): logic is frozen; only the risk profile retunes, within its ranges (DEC QML).
  - "New risk and sizing systems go through paper … in the Lab" (UIL:150).
- **New kinds of thing the Lab may produce, each needing lineage:**
  - variants (same logic on a new instrument or timeframe);
  - risk-profile versions;
  - MIS configurations per strategy type;
  - blocks (the catalogue grows, with a "librarian" proposing new ones, DEC QML).
- **The two benches may merge.** If the risk profile ships inside the unit, the Lab's separate Pods bench (Design/Test/Paper) may fold into the Strategies bench, or shrink to "frame" design only.
- **Paper per unit** reopens DEC-0261.

### Trading node `[inferred unless cited]`
- It must run units whose risk profile retunes itself in live, store profile versions, and log in R. Today the code has none of this:
  - backtest results come out in money, not R;
  - the kill line and the bench run only in test harnesses;
  - there is no symbol-metadata path for live trading (F05 B).
- It needs new venue adapters: Hyperliquid perps, futures, spot (DEC; HO plan item 3).
- It probably keeps the account guard and the kill switch, since they sit outside units.

### Agents: who may change what `[inferred, built on agreed rules]`
- **Money stays read-only for agents.** Live trading, promotion to live, and any loosening of a limit are the operator's signature ("the human mainly promotes bots", DEC). This fits the existing effect table: PROPOSE_MONEY always asks (`05-qmx-today.md:225`).
- **The self-tuning is a fixed recipe in code, not an agent writing numbers.** In live, a unit may only tighten itself within its declared ranges. Any loosening, or any change to a range, is a proposal the operator signs.
- **Lab agents may edit open-stage units freely:** logic, settings, blocks. They may not edit compiled logic; that becomes a new strategy or variant under the identity rule.
- **Agents call QMB but cannot edit it** (sealed packages in, signed results out; DEC Tooling).
- **Agents must not touch the account guard** (kill line, kill switch, correlation).
- **Decay and benching can be agent-run workflows** (daily decay spotting, session-preference discovery, DEC), but only through tightening actions: bench, back to paper, shrink.

---

## 3. What our methodology and workflow design must keep flexible until that session settles

1. **The noun for what the Lab hands to Portfolio.** Do not hard-code "strategy", "bot" or "pod" as the promoted object. Use one placeholder (for example "unit") whose parts are a list, not fixed fields.
2. **The meaning of "pod".** It may stay a full risk/sizing system or shrink to a frame (account guard plus router). Keep Portfolio copilot tools such as `pod.*` behind a renamable layer.
3. **The number of Lab benches.** The Pods bench may merge into Strategies. Lab workflows should key on the stage, not the bench.
4. **Stage names and the open/compiled line.** The six stages are agreed. Keep the list data-driven, because paper per unit is still in dispute (DEC-0261).
5. **Identity and lineage.** Keep the rules for new strategy vs variant vs profile version in one table the engine reads. Do not bake them into prompts.
6. **Where the router lives.** It could be Portfolio per account, the node, or inside units. Do not give any agent role ownership of routing yet.
7. **Who tunes risk settings.** Design for "a code recipe tunes, agents propose, the operator signs any loosening". Leave a slot for a statistics or ML calibrator added later.
8. **MIS ownership.** MIS configs may become per-unit Lab outputs rather than one shared service setting. Do not tie MIS editing to a single Portfolio role.
9. **Sizing method names.** "Classic Book", "Book + BMS" and the `ε` cushion rule are all live options. The methodology must not assume any one of them.
10. **Account-guard boundary.** This is agreed: it sits outside units. Lock agents out of it now; this one is safe to design hard.
11. **Venue list.** Keep it open: CFD (cTrader), Hyperliquid perps, futures, spot. Trader-agent and Portfolio workflows should not assume cTrader only.
12. **Decay and bench workflows.** Design them as tighten-only actions with a pluggable definition. Alpha decay, streak length and loss-point reset are all still open (DEC Open questions).
