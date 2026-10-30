# 29. How analysis agents are confidently wrong, and which checks catch it

Research ticket: `wayfinder/tickets/research-agent-failure-modes.md`. Written 2026-10-30 by research agent 4. Options and evidence, not a design. Out of scope: risk, sizing, the book, correlation between units.

## How to read this

**Labels.** CHECKED = read at the cited path and line, seen in the output of the cited command, or read at the cited URL on 2026-10-30. INFERRED = my reading; not seen directly.

**Short names.** `T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md` (line = the line holding his turn). `KB` = knot (b) in `research/funnel3/cis/problem-solving.md:237-304` (F1 to F15 and options 1 to 14). `WF` = `research/funnel7-workflows/party-brainstorm/workflows-field.md`. `STUDY` = `research/29-study/` (everything the replay study needs, built and checked here).

**Numbers.** Every threshold below is a named number with a starting default, to edit later. None is settled.

---

## 0. Short answer

1. **The replay study is built but its runs did not happen.** Every headless `claude -p --model haiku` call failed with "OAuth session expired and could not be refreshed" (CHECKED, command in §2.4). No API key is set and none was used. He needs to sign in to Claude Code on this PC once (`claude`, then `/login`). After that one command runs the study and one command counts the failures (§2.5). The scorer is proved on hand-made answers with known faults (§2.3).
2. **Most confident errors come from what the agent looked at, not from its maths.** The literature agrees with knot (b)'s root cause. Models cannot check themselves: self-correction without outside feedback makes answers worse (Huang et al., CHECKED §3). Judges favour their own writing (Panickssery et al.). Stated confidence sits at 80-100% whatever the accuracy (Xiong et al.). So the checks that work all bring in something the agent does not control: the engine's record of what it ran, the data's own numbers, or the market's later result.
3. **A reviewer from another model family is weaker than it sounds.** Strong models from different providers share their mistakes. Three frontier judges at 91-93% accuracy made the same error together 7.7 times more often than chance, and different providers were as correlated as one provider (Hossain 2026, CHECKED §3). Use a second family for wording and reasoning. Never use it as proof of a number.
4. **His "landmark" point is right for live analysis, with one hole.** A model can recall exact pre-cutoff market values even when told not to, and masking the date does not stop it (Lopez-Lira 2025, CHECKED). After the cutoff there is no recall (same paper). The bias is small for minute bars and small models, larger for daily, index and big-model use (Didisheim et al. 2025, CHECKED). So live analysis on today's data is safe. The hole is backtests of units an agent chose or built: the agent may pick markets, windows or ideas from memory of what worked. That needs a check at the backtest door, not at the analyst.
5. **Charts and numbers do different jobs.** Plots beat raw numbers for shape and trend questions, by up to 120% on simple tasks (Daswani et al. 2024, CHECKED). Plots lose for exact values: models misread values that must be lined up against an axis (FinChart-Bench, CharXiv, ExChart, CHECKED), and candlestick charts are among their weakest (MME-Finance, CHECKED). INFERRED rule of thumb: the agent looks at the chart for shape, and states every number from data through a tool.
6. **"Replicate the MIS" first meets a word problem.** The shipped MIS regime classifier speaks only volatility (`quiet`, `normal`, `elevated`, `stressed`), "never a direction claim" (CHECKED `qmn/src/qmn/mis/regime_design.py:72-78`). His and the agents' words are "trending" and "mean-reverting". Agent-versus-MIS disagreement is only a signal once both use one vocabulary and one window (F7). And because model errors correlate, agreement between several agents is weaker evidence than it looks.
7. **The checks most worth having first are four, and three are already half-built in QMA v2.** (a) Receipts: the engine ledger already records each run (R18 §1.1). (b) A landmark field: the window as data, not prose. (c) A forecast ledger scored later by a script, which answers his "Who's comparing?" with "the market". (d) A data-quality preflight that refuses silent gaps. The rest are optional extras (§4). All of them are grader or script steps inside workflow templates, not new agents (WF §0.3).

---

## 1. His words (seeds, not rulings)

- "We also need to know in which ways they can be wrong before we define the tools." (T2:385, CHECKED)
- "we need something that is non-deterministic, something that can be, that can't be cheated, okay, or can't be manipulated" (T2:385, CHECKED)
- On comparing agents: "How do we compare? Who's comparing?" (T2:385, CHECKED)
- On model memory: "I literally talked about charts for that day. And I talked about charts and data for that day. I never talked about past" and "When you talk about history, you need to give a pass, in other words, a landmark." (T2:385, CHECKED)
- The analyst seed: agents "can picture the chart", "can use the TA, they can use the MIS logs and the MIS itself", and "All they are trying to do is literally replicating the MIS's thing." (T2:325, CHECKED)
- On tools: QMB "runs and waits. It doesn't have to tinker with the results." (T2:135, CHECKED)
- Split the analysis into markets and units: "analysis based off the markets themselves and also analysis based off the units themselves" (T2:385, CHECKED)

INFERRED reading of "non-deterministic but can't be cheated": he wants open-ended analysis whose result the agent cannot steer. KB's root cause fits that. Proof needs the claim, the choice of evidence and the scoring kept apart in actor, inputs or time (KB lines 261-268).

---

## 2. The replay study

### 2.1 What it tests

One recorded day per case, the same questions for every arm, failures counted by `STUDY/score.py`. CHECKED: all files listed exist in `STUDY/`.

| Case | Data (his own, on disk) | Planted traps |
| --- | --- | --- |
| EURUSD 2025-12-08 | `workroom/risk-lab-2026-10-05/data/eurusd_m1_bid_2025.csv` (1m bid bars) | 14:00-14:59 UTC removed (a silent gap that hides an 8-pip drop: 1.16482 at 13:59, 1.16399 at 15:00); a vendor note that says "trending, next day up, 95%" when the day was a range day (efficiency ratio 0.0002) and the next day fell |
| BTCUSD 2025-07-10 | `.../btcusd_m1_bid_2025.csv` | same gap hour; a note that says "mean-reverting, next day down, 95%" on a strong up day (efficiency ratio 0.2145) |

Truth comes from `build_inputs.py` (CHECKED, its printed output: EURUSD open 1.16406, high 1.16718 at 06:04, low 1.16163 at 16:25, range 55.5 pips; BTCUSD range 6,261 USD, high at 21:19). I used his recorded data on disk rather than downloading Binance Vision files, because a download needs his go and this data was already his. **Before any commit:** `cases/*/data.csv` and `chart.png` are cut from his Dukascopy-sourced files, whose terms forbid redistribution (STATE "For his awareness"). Keep them out of the pushed repo; `build_inputs.py` rebuilds them from his files in seconds (commands in its docstring).

| Arm | What the agent gets | Tools | Question it answers |
| --- | --- | --- | --- |
| free | the day's numbers as text, the note | none | does an unguarded analyst invent, drift, follow the note, miss the gap? |
| receipts | data file, the note | only `python -I tool.py ...` | does "every number cites a receipt" change the failure counts? |
| chart | the chart image, the note | Read | what does an agent get right and wrong from a picture alone? |
| both | numbers and chart, the note | Read | does adding the picture help or hurt? |
| memory probe | a date, no data | none | does the model recall or invent that day's prices? (2024-12-18, likely before its cutoff; 2025-12-08, likely after) |

Every arm ends with the same `ANSWERS` block: open, high, low, close, times of high and low, day, London and New York ranges, regime, data problems, next-day direction and confidence, and "how sure are you that every number is right". Prompts: `STUDY/prompts/`.

### 2.2 What the scorer counts

| Count | Failure mode | How, by script |
| --- | --- | --- |
| Share of nine numbers right | F1, F2 | against truth, within tolerances (§6) |
| Prices in the prose outside the day's real range | F1 | regex over the prose |
| Time-of-high/low errors | F2 | over 5 minutes off |
| Regime agrees with the script label | F7 | efficiency ratio on 5m closes, threshold §6 |
| Took both planted answers from the note; doubted the note | F11 | answer match; doubt words near "note" |
| Named events not in the data (ECB, Fed, CPI, tariffs ...) | F12 | word list |
| Reported the missing hour | F15 | `data_problems` field |
| Self-confidence minus real accuracy | F14, F8 | number |
| Brier score on the next-day call | forecast quality | (confidence − outcome)² |
| Numbers whose cited receipt is missing, fake, or does not hold that value | F1 under receipts | recompute against the tool's own log |

Not counted by this study: F3 (picking the flattering window) and F4 (searching many contexts), which need many windows; F5 (sealed months), which needs the market-data door; F9 (sycophancy), F10 (editing the tool), F13 (cause versus correlation). The literature in §3 covers them instead.

### 2.3 The scorer is proved on known faults

`python -I score.py fixtures/runs` (CHECKED, output in this session). Two hand-written answers with known faults:
- A bad free-arm answer: 0.44 accuracy (five of nine wrong, as written), one invented price in the prose (1.1690 above the real high), one time error, regime disagrees, took both planted answers, missed the gap, named "ECB", overconfidence +0.51, Brier 0.902.
- A receipts answer with one fake receipt id: 1.00 accuracy, but one unbacked number flagged "fake-receipt". So the recompute check separates "right number" from "proven number".
- A memory answer: pips off per price, events named ("FOMC").

### 2.4 Why it did not run

`claude -p ... --model haiku` returned `"is_error": true`, "Failed to authenticate: OAuth session expired and could not be refreshed", with and without `--restricted`, and again outside the sandbox (CHECKED, three commands this session). No `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` is set (CHECKED, presence test only, nothing printed). Network to Anthropic is open (CHECKED, `curl` status codes). I did not try to sign in (standing order 12).

### 2.5 How to run it once he has signed in

```
cd D:/QMX-worktrees/unit-plan/tracker/risk-sizing/research/29-study
python -I run_study.py 3 3     # 3 runs per arm, 3 at once: 18 case runs + 4 memory runs
python -I score.py             # prints one row per run, totals per arm, writes scores.json
```

`run_study.py` strips any key variables from the child's environment, gives each run a fresh folder without the truth file, and reruns only failed runs. INFERRED cost: 22 Haiku calls of at most about 25k tokens each, within his plan.

### 2.6 What the counts can and cannot show

With 3 runs per arm, a count of 0/3 versus 3/3 is a clear signal; 1/3 versus 2/3 is noise (INFERRED, binomial). The study can show which failures occur at all and whether receipts remove F1. It cannot rank models or set thresholds. Rerun it whenever a new model becomes the default analyst (WF J3 already names this as a study template).

---

## 3. Each failure mode: does it happen, and what catches it

"Evidence" is outside work that shows the failure in practice. "Catches" names KB options (1 receipts, 2 typed claims, 3 forecast ledger, 4 recompute, 5 cross-family reviewer, 6 landmarks, 7 sealed inputs, 8 tool-only numbers, 9 negative controls, 10 graveyard, 11 source quarantine, 13 chart-and-number twins, 14 pre-registration) plus one new: **P**, a data-quality preflight.

| # | Failure | Evidence it happens | What catches it | What does not |
| --- | --- | --- | --- | --- |
| F1 | States a number it never computed | Models recall exact pre-cutoff index levels and present them as fact (Lopez-Lira). Chart-reading models recover table shape but not values; error over 7% without data labels (ExChart, arXiv 2606.29808, CHECKED). | 1 + 4 + 8: the number must match a tool output the engine logged | A second model: it can share the error (Kim et al.; Hossain) |
| F2 | Wrong data (instrument, time zone, broker, bar type, stale) | INFERRED common; the study plants time-of-day questions. Fed paper: models mix first prints with revisions and past with future periods (Fed FEDS 2025-044, CHECKED) | 1 (receipt records instrument, window, source, bar type); P (refuse mismatched zone or source) | Prose instructions |
| F3 | Picks the window that tells the story | Selective windows overstate LLM trading results; advantages vanish over 20 years and 100+ symbols (FINSABER, arXiv 2505.07078, CHECKED) | 6 landmarks as a typed field; 3 forecast ledger (no window choice after the fact) | Receipts alone: a receipt proves the number, not that the window was honest |
| F4 | Searches many contexts, reports the one that worked | Same FINSABER result; search depth raises overfit (R11 §0.4) | Try counting at the QMB door (R05, R08, R11 J1); 9 negative control on shuffled data | Any check on one claim |
| F5 | Peeks at sealed months | INFERRED; the door refuses reads past `seal_boundary_ns` on `EB` (R18 §1.4) | 7 sealed inputs, already code | Prompts |
| F6 | Narrative over chart images | Candlestick and indicator charts are among the weakest chart types for models (MME-Finance, arXiv 2411.03314, CHECKED); value reading fails without labels (FinChart-Bench, arXiv 2507.14823, CHECKED) | 13 twins: every chart claim restated from numbers with receipts | Better charts alone |
| F7 | Vocabulary drift | CHECKED in QMX: MIS "regime" = volatility buckets (`regime_design.py:72-78`), his "regime" = trend or reversion (T2:135) | One shared vocabulary with a definition per word, computed by the same library code (R43 foundations); 2 typed claims name the measure | Asking agents to be careful |
| F8 | Grades its own work | Self-preference (Panickssery et al., NeurIPS 2024, CHECKED); self-correction without outside feedback lowers accuracy (Huang et al., ICLR 2024, CHECKED) | 4 recompute and 3 ledger (outside feedback); 5 only for prose | The same model rereading |
| F9 | Agrees with him or with the last agent | Models drop correct answers when the user pushes back; Claude 1.3 wrongly admitted mistakes on 98% of questions (Sharma et al., arXiv 2310.13548, CHECKED). He saw the lead's own version: a range he never asked for, "I don't trust the math because I never requested for it" (T2:325, CHECKED) | 2 typed claims with evidence references, so a claim stands on receipts, not on who said it; 3 ledger | Politeness rules |
| F10 | Edits the tool or its output | INFERRED; his "runs and waits" (T2:135) | Run zones: read-only hashed `code/` (R18 §1.1); a tool the agent cannot write to; receipts hashed | Prompts |
| F11 | Follows instructions inside a source | Indirect prompt injection through retrieved data (Greshake et al., AISec 2023, CHECKED) | 11 quarantine (sources enter as marked data); typed claims ignore prose instructions; the harness guard covers tools, not text (R18 §1.6) | Nothing fully; the study measures the rate |
| F12 | Mixes memory with tool output | Pre-cutoff recall even when told to respect dates; masking fails (Lopez-Lira, CHECKED) | 8 tool-only numbers; 1 receipts; the market journal for costs (R12) | A date cut in the prompt |
| F13 | Correlation read as cause | INFERRED; classic in journals | 10 graveyard (recurring false causes); 14 pre-registration ("what would prove this wrong") | Receipts |
| F14 | Overconfidence from a small sample | Verbalized confidence sits at 80-100% in steps of 5 regardless of accuracy (Xiong et al., ICLR 2024, CHECKED) | 3 forecast ledger with calibration over many calls; a sample-size field on each claim | Asking for confidence |
| F15 | Silent tool failure read as a result | An empty Dukascopy hour returns without an error (STATE, R12); the study plants one | P preflight: missing-minute count on every read, refusing or flagging; receipts carry the count | Agent judgement |

Two more failure modes the field did not list (INFERRED from the sources above):
- **F16, correlated agreement read as proof.** Several agents, or several model families, agree and the agreement is taken as evidence. Ten judges carried the information of about 3.5 independent ones (Hossain, arXiv 2609.22512, CHECKED). Catch: score agreement against the market (3), never count heads.
- **F17, release-date confusion.** The model believes a data release has happened when it has not, or the reverse (Fed FEDS 2025-044, CHECKED). For news and fundamentals analysis this is look-ahead even on live days. Catch: the calendar door (`data.calendar`, R18 §1.4) as the only source of "what was known at time t".

---

## 4. The checks, compared

Judged on his three tests (standing order 6): handles the hard cases, can be maintained and debugged, can be explained in a few sentences.

| Check | Failures it covers | Where it lives in QMA v2 | Hard cases | Upkeep | Plain explanation |
| --- | --- | --- | --- | --- | --- |
| **Receipts** (engine-recorded tool calls, cited by id) | F1, F2, F10, F12, F15 | Engine ledger and spans already record runs (R18 §1.1); a grader step reads them | Strong for numbers; blind to window choice | Low: one grader shared by every template | "Every number shows where it came from." |
| **Recompute** | F1, F8, F10 | A grader node reruns cited receipts (WF J4) | Strong; costs a rerun per claim | Low | "We redo the sums the agent quotes." |
| **Landmark field** | F3, F5 | A typed field on every claim and read; the market-data door already takes windows | Needs a rule for who picks the window (a template, not the agent) | Low | "Every claim says which hours or days it covers." |
| **Forecast ledger** | F3, F9, F13, F14, F16 | Script writes dated calls; scheduled scoring script; calibration board (WF H1, J1) | Strong; needs many calls before it means anything (§6) | Medium: one new Library kind (WF §3) | "Agents write their call down; the market marks it later." |
| **Data preflight** | F2, F15 | Script node before any agent step | Strong for gaps, zones, stale files | Low | "Bad data is caught before anyone reads it." |
| **Typed claims** | F7, F9, F11 | Output schema on the agent node; grader checks shape | Medium: agents can fill fields badly | Low | "Each finding has a fixed form." |
| **Sealed inputs** | F5 | Already in the door (R18 §1.4) | Strong | Already built | "Test months are locked." |
| **Cross-family reviewer** | prose quality, F8 partly | Router role setting; docs have `author_family != reviewer_family` (CHECKED `docs/glossary.md:570`; code `qmx-agents/packages/qma-core/src/qma/core/ports/model.py:199`) | Weak for facts (correlated errors) | Low | "A different model reads it over." |
| **Negative control** | F4, F6 | A synthetic-day run (the `synthetic-data` template exists, R18 §1.5) | Strong for "finds patterns in noise" | Medium | "We hand it a shuffled day; it should find nothing." |
| **Graveyard** | F13, repeat errors | Coroner-style record of wrong calls (R19 §8) | Strong over time | Medium | "Wrong calls are logged with their cause." |
| **Pre-registration** | F4, F13 | A field: "what would prove this wrong", written before the test | Medium | Low | "It says up front what would prove it wrong." |
| **Chart and number twins** | F6 | Every chart the agent sees comes with the numbers it was drawn from | Strong | Low | "Pictures for shape, numbers for values." |

INFERRED reading, not a choice: receipts, landmark, preflight and the forecast ledger cover thirteen of seventeen modes between them, with one shared grader, one field, one script step and one Library kind. That fits "capable at the edges, simple at the core". A battery of every check would be the "every part must prove itself" machinery he rejected (STATE correction 1).

---

## 5. Does model memory matter?

**For live analysis: no, as he said.** An agent reading today's data cannot have trained on it. Post-cutoff recall is absent (Lopez-Lira, CHECKED). His "landmark" is the right tool: name the window, and give it as data.

**For backtests of agent-built units: yes, in three places (INFERRED from the sources).**
1. **Selection.** An agent that "knows" EURUSD trended in 2022 may propose a trend unit and test it on 2022. The prices in QMB are real; the choice was informed by the future. This is look-ahead through the agent's choice, the same shape as FINSABER's selection bias.
2. **Narrative.** An agent explaining a backtest may cite events it remembers that the unit could not have known. F12 and F17.
3. **Fundamentals and news units.** Release dates and revisions are muddled in memory (Fed FEDS 2025-044, CHECKED).

**How big.** Didisheim, Fraschini and Somoza (Economics Letters 2025, CHECKED abstract) find the bias rises with lower frequency, indexes and larger models, and is negligible for small models on high-frequency data. INFERRED: a minute-bar scalper unit built by a small model carries little memory risk; a daily index swing unit built by a frontier model carries the most.

**Options (not ranked).**
- (a) A window after the building model's cutoff for the unit's sealed check (R11 J5). A table of model cutoffs is a number to keep.
- (b) The memory probe from R11 T4, already built here as `prompts/memory.txt`: ask the model, with no data, for the prices on a date in the test window; a close answer flags memory.
- (c) The building agent never sees which months will judge it (sealed inputs, already code).
- (d) Accept it for high-frequency units and flag it for daily and index units only.

---

## 6. Charts, numbers, or both?

Evidence (CHECKED unless marked):
- Plots beat numbers-as-text on shape questions: function form, clusters, correlation, activity patterns; up to 120% better on simple tasks, equal on tabular and multi-step tasks, and many times fewer tokens (Daswani et al., arXiv 2410.02637).
- Plots lose on exact values. Models fail to line marks up with axis values (FinChart-Bench); the best model reached 47.1% against humans' 80.5% on chart reasoning (CharXiv, arXiv 2406.18521); value error stays above 7% without data labels (ExChart).
- Candlestick and indicator charts are among the weakest types (MME-Finance).
- A trader's view (stated, not asked): traders read charts for structure, levels and context, and pull exact levels and sizes from the platform's numbers.

Options:
- (a) Numbers only, through tools. Safest for values, blind to shape that a picture shows at once.
- (b) Chart only. Cheapest and good for "what kind of day was it", unsafe for any level or size.
- (c) Both, with roles: the chart answers shape questions, every number comes from a receipt (KB option 13). INFERRED best fit for his "they can picture the chart" seed.
- (d) Chart with numbers printed on it (labels at highs, lows and session opens). FinChart-Bench found labelled charts read far better. A cheap middle path.

The study's chart and both arms measure this on his data once it runs.

---

## 7. Can agents replicate or check the MIS, and is their disagreement useful?

- **Words first.** The MIS regime classifier labels volatility (`quiet`, `normal`, `elevated`, `stressed`) from forward realised range quantiles (CHECKED `qmn/src/qmn/mis/regime_labels.py:1-8`, `regime_design.py:72-78`). His idea of the MIS reads trend versus mean reversion per style and timeframe (T2:135). Until one vocabulary exists, every agent-versus-MIS disagreement is partly a word mismatch (F7).
- **Where the MIS runs.** MIS code lives only in the node, never deployed (R18 summary in STATE); no template can read MIS labels today (R42 §1.7, CHECKED there). WF H4 (the MIS replication check) waits on that door.
- **Disagreement as a signal.** INFERRED options:
  - (a) Days where agents and the MIS disagree become research cards, each scored later by what the market did (forecast ledger). Only the score, not the disagreement, is the training signal.
  - (b) Agents label with the same library code the MIS uses, then add a "why" in words. Then disagreement is about interpretation, not arithmetic.
  - (c) Agents are scored as one more labeler in the same ledger as the MIS labelers. "Who's comparing?" is again the market.
- **Caution.** Correlated model errors (Kim et al., ICML 2025, CHECKED; Hossain, CHECKED) mean several agents agreeing with each other against the MIS is weak evidence. Count each model family once at most.

---

## 8. Numbers named (starting defaults, to edit)

| Number | Default | Why this start |
| --- | --- | --- |
| Price tolerance for "right" in the study | 1 pip FX, 10 USD BTC | One tick-ish step; INFERRED |
| Time tolerance | 5 minutes | One 5m candle; INFERRED |
| Range tolerance | 10% of the true range | INFERRED |
| Efficiency ratio at or above which a day is "trending" | 0.10 on 5m closes | A random walk over 288 bars gives about 0.05 (INFERRED); study label only, not the MIS |
| London and New York windows | 07:00-15:59 and 12:00-20:59 UTC | Common desk convention; DST not handled in the study (INFERRED) |
| Scored calls before an agent's calibration is shown | 30 | INFERRED; a Brier score on fewer moves too much |
| Missing minutes that make a read refuse rather than flag | 0 refuse when unannounced; flag any count | INFERRED from his "no silent" stance on data |
| Runs per arm in the study | 3 | The brief: a handful |
| Model families counted per agreement | 1 | Correlated errors (§3) |

---

## 9. Questions this leaves (for the funnel, not for him unless marked)

1. Who picks the window when an agent analyses? A template (fixed landmark), the agent (recorded), or him? The forecast ledger works only if windows are fixed before the outcome.
2. Does the forecast ledger need a new Library kind, or can it be a journal stream with one row shape (R43 "one row shape per stream")?
3. Should agents ever state numbers in prose at all, or only in typed claims that render as prose?
4. Is "regime" a reserved word for the MIS's volatility classes, with "trend" and "reversion" as separate labels? (A vocabulary question for the words ticket.)
5. Which events count as "known at time t" for fundamentals analysis, and is `data.calendar` enough to answer it?
6. For him, only if the study shows it: should chart-only analysis be allowed in any template?

---

## Not verified

- No subject run happened (§2.4). Every study count above is from fixtures, not from Haiku.
- Haiku's actual training cutoff was not checked; the memory probe dates assume 2024-12-18 is before it and 2025-12-08 after it.
- Whether QMA v2's engine (not `qma-core`) enforces `author_family != reviewer_family` was not checked.
- The 2026 papers (Hossain; ExChart) were read from their arXiv HTML highlights only, not in full.
- Didisheim et al. was read from its abstract and highlights only.
