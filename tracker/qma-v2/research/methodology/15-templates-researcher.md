> STATUS 2026-10-16 (rubric walk): PARTLY-STALE. See 27-rubric-walk.md. Rulings in 26 win.

# 15 — Template catalogue: the quant researcher

Written 2026-10-16 by an ideation agent. Charting, not ratification. Inputs: files `01` to `14` in this folder, with `12` (design synthesis) as the base and `13` for failure handling and the RLM step. Where this file and `12` disagree, `12` wins until he rules.

Claim labels: `[retrieved]` from a file in this folder or a source it cites, `[inferred]` designed here.

Words used below:
- **Template**: a workflow folder that ships with QMX, for example `workflows/research.paper-scout/`.
- **Variant**: his own copy of a template, made with the builder. It has its own topic, sources, skills and schedule. It can tighten the template's gates but never loosen them.
- **Methodology**: a pack of variants, skills and gate tightenings that belong together, for example "EURUSD macro desk".
- **Mode**: **C** copilot only, **C+S** copilot plus sub-agents, **W** workflow alone (the copilot only shows the result), **C+W** the copilot starts or edits a workflow. `[retrieved]` `12` §(a).
- **Step kinds**: `script`, `rule`, `model`, `agent`, `rlm`, `human`, `subflow`, `grader`, plus the `fanout` modifier. `[retrieved]` `12` §(c).
- **Model role**: a name such as `reader` or `validator`. Settings maps each role to a model. No template names a model. The role table is in "Shared building blocks".

---

## Summary table

| # | Template | One-line purpose | Mode | Trigger | Main output | Feeds next |
|---|---|---|---|---|---|---|
| R0 | Idea grill to term sheet | Turn his rough idea into a testable term sheet with a kill rule | C | He talks | Term-sheet card | R3, template B, R7 |
| R1 | Paper scout to research note | Find new q-fin papers worth his time and write one note per keeper | W | Every 6 h + manual | Explainer document per paper | R2, R3, Library knowledge |
| R2 | Paper to component card | Pull one reusable, testable piece out of a paper | C+W | From R1, R4 or manual | Component card + code stub | Template B (ablation), Library |
| R3 | Replicate a paper in the Lab | Rebuild a paper's headline result on our data, then test it after publication | C+W | Manual, or R1 marks "replicable" | Replication scorecard | R2, template B, dead ends |
| R4 | Literature review on a topic | Map what is known on one topic, from papers and video creators | C+S, or W on schedule | Manual, or monthly per topic | Explainer with a methods matrix | R2, R3, R6, variants |
| R5 | Understand and extract (funnel 4-5) | Turn a captured paper, video or TradingView script into claims and cards | W (subflow of template A) | Template A stage 3 output | Claim list, cards | Template A stage 6 audit |
| R6 | Hypotheses from dead ends | Mine the negative results for new, honest hypotheses | W, then C | Weekly, if new dead ends | Hypothesis cards, short list | R0, template B |
| R7 | Calibrate | Put an honest confidence on headline claims and numbers | subflow | Called by R1-R6, R8 | Calibration block inside the report | The calling template; R9 metrics |
| R8 | Big-data question (RLM) | Answer a question over more data than fits in context | C+W | Manual | Explainer with evidence pack | R6, template B |
| R9 | Weekly research-harness review | Find what the research templates got wrong and propose fixes | W | Weekly | Change card (parked) | All templates, after his OK |

Template A (Fill the Library) and template B (Build and prove) are in `12` §(d). This catalogue plugs into them; it does not replace them.

---

## Template cards

### R0 — Idea grill to term sheet

| Field | Design |
|---|---|
| Purpose | Turn "I think funding spikes predict reversals" into a term sheet that can die. |
| Mode | C. No helper and no run unless he asks for a Library check by a sub-agent. |
| Trigger and pre-check | He talks in any home. Pre-check is a `script` Library search for prior term sheets, dead ends and rejected ideas on the same mechanism. It runs before the first question, so known facts are shown and never asked. |
| Steps | 1 `script` Library and dead-end search. 2 `model` grill round 1: up to five numbered questions, each with a recommended answer; "yes" accepts. 3 `model` round 2, only while open questions remain. 4 `model` draft term sheet JSON. 5 `grader` field check: mechanism, universe, timeframe, data needed, entry, exit or `unresolved`, kill criteria, capacity guess, a "what would fake this" line. 6 `human` he corrects the card, not the code. |
| Gates and kill rules | No term sheet saves without a kill criterion and a mechanism. If the Library holds a dead end with the same mechanism and market, the card says so on top and asks what is different this time. |
| Human points | Answers questions; approves the card. |
| Memory and lessons | Operator scope: what he rejected and why (BMad distillate rule, `[retrieved]` `01`). Board iteration counter: round trips per idea. |
| Roles | `grill` (questions), `writer` (card). |
| Failure policy | Chat; no engine retries. If the grader fails, the copilot names the missing field. |
| Budget guard | Two rounds by default, a third only if he asks. |
| Output | Term-sheet card. |
| Feeds | R3 if a paper sits behind it; template B "Pick"; R6 later if it dies. |

### R1 — Paper scout to research note

| Field | Design |
|---|---|
| Purpose | Read the new q-fin feed so he does not have to, and keep only papers with something testable. |
| Mode | W. The copilot only shows the notes. A "deep read this one" request from him runs the same steps in C+S. |
| Trigger and pre-check | Cron every 6 h plus manual. Pre-check `script`: diff arXiv RSS for q-fin.TR, PM, ST, RM and the alphaXiv `get_hot_feed` (free, no quota) against `seen_ids` in workflow memory. Wake only on new IDs (`{"wake": false}` otherwise). The 1-request-per-3-seconds arXiv rule lives in this script. `[retrieved]` `11` §1. |
| Steps | 1 `script` fetch titles and abstracts for new IDs. 2 `model` triage against his watch topics (stored in the variant's `settings.toml`); keep top N (default 3). 3 `agent` × N, `fanout`: one reader per paper, one `answer_pdf_queries` call with the batched question battery (claim, data and source, sample period, universe, costs assumed, out-of-sample result, number of variants tried, code link). 4 `script` if a code link exists, `read_files_from_github_repository` lists the tree; no code is run here. 5 `grader` citation checker: every claim maps to a page; uncited claims are dropped or flagged. 6 `subflow` R7 calibrate on the note's headline claims. 7 `model` write the note JSON with "testable as a strategy or component: yes or no, and why", and "replicable with our data: yes, proxy, no". 8 `rule` testable and replicable → open a proposal for R2 or R3; otherwise file as knowledge. 9 `grader` render check (schema, numbers resolve, Mermaid parses, headless render). |
| Gates and kill rules | Kill a paper at triage if it has no data section, no out-of-sample test and no mechanism. Flag "Sharpe above 2 on daily data: assume lookahead until shown otherwise" (ml4t, `[retrieved]` `02`). A paper that reports no costs gets a red "costs unknown" chip. |
| Human points | None in the run. He reads the notes; a proposal to R3 lands as a card he can accept with one tap. Under the Lab rule this is not an approval ask, just a choice. |
| Memory and lessons | Workflow scope: `seen_ids`, last output (Hermes `continuity`). Home scope: authors and topics he starred or dismissed. Lessons: triage misses he flags ("this was relevant") become eval cases for R9. |
| Roles | `triage` (cheap), `reader`, `citation-checker`, `writer`, `judge` (render grader second pass, optional). |
| Failure policy | Feed fetch failure: spend-neutral retry ladder 5, 15, 30 min. Reader failure: retry once, then the note ships with that paper marked "could not read". alphaXiv quota or 429: step waits, run parks. A reader is never re-paid on resume (cached by paper ID and question hash). |
| Budget guard | N readers at most 3 per tick, 10 tool calls per reader, hard stop 20. Per-run cost cap with reserve-then-refund (`[retrieved]` `11` §2). Admission control under the usage cap. |
| Output | Explainer document per paper: mechanism diagram, key-results chart, "will it survive costs?" box, page-linked citations, calibration chips. A dashboard tile "3 new papers, 1 testable". `[SILENT]` when nothing passes triage. |
| Feeds | R2, R3, Library knowledge notes, R4 (as a seed list), digest. |

### R2 — Paper to strategy component card

| Field | Design |
|---|---|
| Purpose | Take one piece of a paper (a signal, a filter, an exit, a sizing rule, a regime classifier) and make it a card the Lab can test on its own. |
| Mode | C+W. He or R1 picks the piece in chat; the workflow does the rest. |
| Trigger and pre-check | From an R1 or R4 proposal, or manual ("make a component from section 4 of this paper"). Pre-check `script`: does a component with the same formula hash or name already exist in the Library? If yes, link to it and stop. |
| Steps | 1 `agent` extract with `answer_pdf_queries`: inputs, formula, parameters and the paper's default values, data frequency, warm-up length, claimed effect with page, stated failure cases. 2 `grader` card schema: every parameter has a value or `unresolved`; nothing invented (the "do not invent exits" rule applied to components, `[retrieved]` `08` §2b). 3 `agent` write a code stub in the Lab sandbox plus a unit test against any worked example or table in the paper. 4 `script` run the unit test; check no future data is read (ml4t lookahead skill as a script lint). 5 `model` ablation plan: which two or three host strategies from the Library to attach it to, and the test "host with vs without". 6 `subflow` R7 calibrate on the claimed effect. 7 `script` Library write (one writer). |
| Gates and kill rules | Unit test fails twice after one repair → card saved as `fragment` with the failure note. Lookahead lint fails → stop; card marked `blocked: lookahead`. |
| Human points | None by default. Ambiguity that changes meaning (two readings of a formula) → `human` with both readings and a recommended one. |
| Memory and lessons | Lineage edge paper → component. Repairs that worked go to a "formula traps" lesson file (for example, "annualisation factor missing"). |
| Roles | `reader`, `builder`, `validator` (lint review on another family where one exists). |
| Failure policy | Build step: retry, then doctor repair (bigger model or more turns), then escalate with the stub and the failing test. |
| Budget guard | One builder agent, 30 turns max, two repair rounds. |
| Output | Component card (rendered as an explainer: formula, picture of the signal on sample data, ablation plan) plus code stub and test in the Lab. |
| Feeds | Template B as an ablation run; Library `component` class (recommended in `08` Q15). |

### R3 — Replicate a paper's result in the Lab

| Field | Design |
|---|---|
| Purpose | Check whether the paper's headline number comes back on our data and engine, then check whether it lived after publication. |
| Mode | C+W. The copilot sets the scope with him; the workflow runs. |
| Trigger and pre-check | Manual, or an R1 proposal marked "replicable". Pre-check `script`: data availability against the replication spec (market, period, frequency, fields). If the data is missing, stop before any model call with a "could not test: data missing" card and the proxy options. |
| Steps | 1 `agent` write the replication spec from the paper: universe, period, signal, rebalance, costs, the reported numbers with page refs, the number of variants the authors say they tried. Uses `read_files_from_github_repository` when code exists. 2 `grader` spec complete; each open item becomes a labelled assumption. 3 `rule` more than two meaning-changing assumptions → `human` with recommended picks; at most two assumption branches are built, and both count as trials. 4 `agent` build in the Lab sandbox (experiment spec: code ref, data snapshot, costs as the paper states them, seed). 5 `script` QMB run on the paper's own in-sample period. 6 `script` compare with reported numbers inside a tolerance band (default: Sharpe within ±0.3, sign of every reported effect the same). 7 `script` costs-on run with our cost model. 8 `script` post-publication run: the period after the paper's sample end is the natural holdout, touched once. 9 `subflow` R7 calibrate: rerun spread across seeds and block bootstraps. 10 `model` verdict JSON. 11 `script` Library write (result and any dead end). |
| Gates and kill rules | Verdicts are set by scripts, not prose: **replicated**, **partially** (sign right, size off), **not replicated**, **could not test**. Daily Sharpe above 2 → lookahead audit before the verdict. Post-publication run is never re-run with changed settings; a second look is a new trial and is counted. |
| Human points | Assumption picks (step 3) only when more than two; he sees the scorecard after. |
| Memory and lessons | Replication ledger row per paper (paper ID, spec hash, verdict, decay ratio). "Not replicated" is a negative result with the reason. Lessons on spec traps ("returns were excess of risk-free") go to the replication skill. |
| Roles | `reader`, `builder`, `validator` (re-reads the spec against the paper in a fresh context), `writer`. |
| Failure policy | Build: retry, repair, escalate. QMB failure: script retry; engine refusal is a result, not a failure. A finished backtest never reruns on resume (memo key). |
| Budget guard | One builder, two repair rounds, at most 2 assumption branches, cost cap per run. |
| Output | Replication scorecard: reported vs ours vs ours-with-costs vs post-publication, one bar per number, tolerance band shaded, verdict on top, assumptions listed. |
| Feeds | Replicated → R2 for its parts and template B "Pick". Not replicated → dead ends for R6. Decay ratio feeds R9 (which sources tend to hold up). |

### R4 — Literature review on a topic

| Field | Design |
|---|---|
| Purpose | Answer "what methods exist for X, which hold up, which could we test" across papers and the video creators he follows. Example topic: portfolio optimisation methods (mean-variance, shrinkage, risk parity, hierarchical risk parity, Black-Litterman, CVaR). |
| Mode | C+S when he asks in chat; W when a variant runs it monthly per topic. |
| Trigger and pre-check | Manual, or a variant's schedule. Pre-check `script` (scheduled runs only): new papers on the topic since the last review (alphaXiv feed filter, arXiv query) or new uploads from his listed creators; otherwise `[SILENT]`. |
| Steps | 1 `model` clarifier, only when he started it: up to three numbered questions with recommended answers (scope, market, depth). Skipped on cron. 2 `model` planner: class the question (straight, breadth, depth), write a plan file and 3-5 searcher briefs (objective, output format, sources, sources to avoid, scope). Effort scaling follows Anthropic: comparison = 2-4 searchers, complex = up to 5 here (`[retrieved]` `11` §2). 3 `agent` × 3-5 `fanout` paper searchers: alphaXiv `discover_papers` (quota), arXiv API, `answer_pdf_queries` for the claims. 4 `agent` × 1 video searcher on a **browser lease**: B3 "read as me" on youtube.com in the QMX Browser profile for his subscriptions and playlists, B1 isolated for public search. It lists videos; a `script` pulls captions (`watch --detail transcript`), frames only on flagged windows. 5 `model` synthesiser reads only the findings files; may loop to the planner once. 6 `grader` citation checker: every claim maps to a page or a timestamp. 7 `subflow` R7 calibrate on the methods matrix verdicts. 8 `grader` judge with the rubric (accuracy, citations, completeness, source quality, efficiency), 0-1 plus pass or fail. 9 `model` writer: report JSON. |
| Gates and kill rules | Evidence tiers on every row: peer-reviewed paper with out-of-sample test > preprint > practitioner paper > video with shown backtest > video claim. Video claims never set a verdict alone. Judge below 0.7 → one revision round, then ship with a "weak review" banner. |
| Human points | Clarifier answers (attended runs). B3 lease: first use per origin per session asks (`[retrieved]` `14` §3.8). A login wall or CAPTCHA stops the lease and asks him; never typed for him. |
| Memory and lessons | Workflow scope: the topic's source list and last review date, so the next run is a delta. Home scope: creators he rates as trustworthy or not. Lessons: searcher briefs that duplicated work. |
| Roles | `clarifier` (cheap), `planner` (lead), `searcher`, `synthesiser`, `citation-checker`, `judge`, `writer`. |
| Failure policy | A failed searcher leaves a gap row ("not covered: X"); the run still delivers. Browser lease held by someone else → the video searcher waits in the queue, the rest proceeds; if the lease never comes, the report says videos were not covered. |
| Budget guard | Searchers: 5-15 tool calls each, hard stop 20 or 100 sources. Run cap in dollars with reserve-then-refund; at the cap deliver partial results. Video frames cap per run (his number). Multi-agent runs cost about 15x a chat, so scheduled variants run monthly, not daily. |
| Output | Explainer document: headline ("3 of 6 methods beat equal weight after costs in out-of-sample studies"), methods matrix with evidence tier and calibration chip per cell, a "what QMX could test" list, creator cards with timestamps. |
| Feeds | R2 (each "could test" row is a component proposal), R3 (key papers), R6 (methods that failed in studies), new variants (a deeper review of one row). |

### R5 — Understand and extract (strategy funnel stages 4-5)

| Field | Design |
|---|---|
| Purpose | Turn one captured source into located claims and typed cards, faithfully, with its holes kept. |
| Mode | W, as a `subflow` inside template A. Also callable from chat on one item ("pull the rules out of this video"). |
| Trigger and pre-check | Template A stage 3 output with bucket `component`, `full strategy` or `hint`. Pre-check `script`: the transcript or text hash is not already processed. |
| Steps | 1 `rule` branch on source type. **Paper:** `script` PDF to Markdown, `model` section map, `fanout` `model` per section with the extraction question battery. **Video:** `script` time map from triage, `fanout` `model` per section on transcript only, `script` collects flagged windows ("look at this candle", settings screens), `script` `watch --start/--end` frames for those windows only, `model` visual pass per window. **TradingView:** `script` Pine parse (inputs, `strategy.entry/exit` calls, `request.security` with `lookahead_on`, `calc_on_every_tick`, `barstate` use, repaint risk), `model` reads the logic; the comment thread is a separate, lower-tier claim set. 2 `agent` reconciler: joins claims across sections so one rule stays one rule; writes the coverage map (minutes or pages never read). 3 `agent` extractor: strategy cards (A-I DNA, class), component cards, knowledge notes, hint cards. 4 `grader` template check (`validate.py`) and "no invented exits" check. 5 `subflow` R7 calibrate on each card's entry and exit rules. |
| Gates and kill rules | Every claim carries a locator and a tag: source-stated, visual, inferred, unresolved (`[retrieved]` `08` stage 4). A card with an inferred entry rule is a `hint`, not a strategy. Pine with a repaint or lookahead flag → card tagged `repaints`, never sent to template B until fixed in a labelled child. Futures sources stay futures; a spot version is a labelled transfer hypothesis. |
| Human points | None. Meaning-changing ambiguity goes to template A's stage 6 exception list. |
| Memory and lessons | Per item: claims, coverage map, card IDs. Lessons: creator vocabulary ("BOS" means break of structure) into the Library knowledge base, via the one writer. |
| Roles | `section-reader` (cheap), `vision-reader`, `reconciler`, `extractor`. Audit (stage 6) is template A's `validator` on another family. |
| Failure policy | Section worker fails: retry once; still failing → that section is a coverage gap, not a run failure. Frames fail: card ships with "visual not checked". |
| Budget guard | Frames only on flagged windows, cap per item and per run (his numbers). Transcript-only triage stays in template A. |
| Output | Claim list JSON, coverage map, cards. Rendered as a source explainer: timeline of the video with claims pinned, cards below. |
| Feeds | Template A stage 6 audit, then stage 7 Library entry. |

### R6 — Hypotheses from Library dead ends

| Field | Design |
|---|---|
| Purpose | Use the negative results, the cheapest edge nobody keeps (`[retrieved]` `06` §9), to propose new hypotheses without fooling himself. |
| Mode | W for the mining; C when he reviews the short list. |
| Trigger and pre-check | Weekly cron. Pre-check `script`: count dead ends added since the last run; wake only if at least 5 (his number). |
| Steps | 1 `script` load dead ends with their failure bucket: died on costs, out-of-sample decay, regime-only edge, too few trades, lookahead found, not replicated. 2 `script` cluster by bucket, market, mechanism and source. 3 `model` per cluster, propose hypotheses using fixed moves: **condition** (works only in regime X → test a regime filter), **slow down** (died on costs → lower frequency), **invert** (reliably wrong → the opposite, flagged as suspicious), **transplant** (component worked inside a dead strategy → attach elsewhere), **drop** (cluster is a true dead end → write "do not retry" note). 4 `rule` dedupe against open term sheets, existing cards and his rejected ideas. 5 `grader` each hypothesis has a mechanism, a kill rule, the dead ends it came from, and a test on **data the parent never touched**. 6 `subflow` R7 calibrate (candidate answers across two roles on "is this a real mechanism or a fitted story?"). 7 `script` rank (evidence, cost to test, data on hand). 8 `human` he picks from a short list of up to 5. |
| Gates and kill rules | A hypothesis born from a failed test inherits the parent family's trial count; deflated Sharpe in template B counts it. No hypothesis may be tested on the parent's holdout. "Invert" hypotheses need a mechanism, not just a sign flip. |
| Human points | Picks from the short list (or ignores it; nothing runs without a pick). |
| Memory and lessons | Workflow scope: which dead ends were already mined. "Do not retry" notes become Library rows R0 shows him. Picked vs ignored is a taste signal for R9. |
| Roles | `miner` (hypothesis writer), `validator` (devil's advocate in R7), `writer`. |
| Failure policy | Model step: retry, then ship whatever clusters finished. |
| Budget guard | One model call per cluster, at most 10 clusters per run. |
| Output | Hypothesis cards in a short list: each card shows the dead ends behind it as small tiles, the move used, and the kill rule. |
| Feeds | R0 (he grills the one he likes), template B "Pick". |

### R7 — Calibrate (probabilistic confidence step)

| Field | Design |
|---|---|
| Purpose | Give each headline claim or number a confidence QMX computed, not one the model asserted. |
| Mode | `subflow` called inside other templates. Never runs alone. |
| Trigger and pre-check | Called with a list of up to 5 headline items (claims or numbers). Pre-check `rule`: skip items that are pure script outputs with a source row, since they need no calibration. |
| Steps | 1 `script` **basis labels**: each claim tagged `retrieved` (has a source pointer that resolves), `remembered` (model knowledge, no pointer), `inferred` (reasoned from other claims). The tag comes from the pointer check, not from the model. 2 `fanout` `model` **candidate answers**: the same question asked K times (default 3: two samples on the `reader` role, one on the `validator` role on another family where one exists), each blind to the others. 3 `script` **agreement**: exact match for categorical answers; spread for numbers. 4 `script` **rerun spread** for numeric results from the Lab: reruns across seeds and block bootstraps (default 20), giving a 5-95% band. 5 `rule` confidence: **high** = retrieved and K of K agree (or band excludes zero); **medium** = retrieved with 2 of 3, or inferred with full agreement; **low** = remembered, or split answers, or band crosses zero. 6 `script` write the calibration block. |
| Gates and kill rules | A **low** headline claim cannot be the headline; the writer must demote it or mark "contested". A number whose band crosses zero can never be called an edge. |
| Human points | None. |
| Memory and lessons | Every calibration row is stored with the claim. When an audit or a later test settles the claim, R9 scores calibration (Brier score per template and per role): do "high" claims actually hold? |
| Roles | `reader` (samples), `validator` (other family). |
| Failure policy | A failed sample counts as disagreement, so the item goes to medium or low. Never retried more than once. |
| Budget guard | At most 5 items × 3 samples per call. Rerun spread uses scripts only (zero tokens). |
| Output | A calibration block in the report JSON; rendered as a chip per claim (basis, agreement, band) with a click-through to the candidates. |
| Feeds | The calling template's writer; R9 calibration metrics. |

### R8 — Big-data question (RLM kernel)

| Field | Design |
|---|---|
| Purpose | Answer questions like "across 3 years of ticks on 40 symbols, where does strategy X break?" without pasting data into context. |
| Mode | C+W. He asks in chat; the copilot writes the question and data handles; the workflow runs. |
| Trigger and pre-check | Manual. Pre-check `script`: data handles resolve, total size known, a dry estimate of sub-calls and cost shown to him if it exceeds his "ask above" number. |
| Steps | 1 `script` mount data handles read-only in a fresh research sandbox. 2 `rlm` root model writes Python against the data as variables and fans out sub-calls to the `rlm-sub` role through QMX's provider layer, not its own. Kernel snapshot after each cell; sub-call results cached by (model, prompt hash). 3 `script` **reproduce**: the cells that produced the headline finding are re-run by a script from the saved snapshot without any model; the number must match. 4 `subflow` R7 calibrate. 5 `grader` evidence pack complete (cells, sub-call log, cost). 6 `model` writer. |
| Gates and kill rules | Finding not reproduced by step 3 → not reported as a finding. Sandbox only: no network except the data store, no live or Portfolio paths (`[retrieved]` `13` §2). |
| Human points | Cost estimate above his threshold. |
| Memory and lessons | Evidence pack in the content store; regime breaks found become Library knowledge rows linked to the strategy. |
| Roles | `rlm-root`, `rlm-sub` (cheap), `writer`. |
| Failure policy | Cell error: the root retries inside its turn budget. Crash: resume from the last kernel snapshot; cached sub-calls are not paid again. Budget hit: pause and park in the inbox. |
| Budget guard | Max children, tokens, dollars and wall-clock per run, read by the kernel. `rlm` is off until this template is wanted (`[retrieved]` `12` §(c)). |
| Output | Explainer: the finding as a heatmap or regime map, reproduced-by-script badge, evidence drawer. |
| Feeds | R6 (regimes where things die), template B (a regime filter child), R2. |

### R9 — Weekly research-harness review

| Field | Design |
|---|---|
| Purpose | Make the research templates better each week from evidence, without silent changes. |
| Mode | W. He only sees the change card. |
| Trigger and pre-check | Weekly cron. Pre-check `script`: at least one research run finished this week. |
| Steps | 1 `script` collect traces, costs, grader and judge scores, citation failures, his thumbs, board iteration counts, calibration outcomes (Brier per template and role), replication decay ratios, triage misses he flagged. 2 `model` cluster failures by signature. 3 `model` propose at most 3 edits (prompt, question battery, brief, skill text, pre-check rule). 4 `script` test each edit the CRO way: fork past failed runs at the first step the edit changes, replay only the suffix on a **fix set**, and run a **guard set** of past good runs (`[retrieved]` `13` §1). 5 `grader` eval set (about 20 cases per template) before and after. 6 `rule` lint: an edit that loosens any gate, threshold or budget is rejected outright. 7 `human` he approves the diff. 8 `script` new folder version; old runs keep the version they ran with. |
| Gates and kill rules | No edit ships without a fix-set gain and no guard-set loss. Gates and thresholds are out of scope for this review; only he changes them in Settings. |
| Human points | Approves or rejects each edit. |
| Memory and lessons | Lessons table: proposal, evidence, result, approved or not. Rejected proposals are not proposed again unless the evidence changes. |
| Roles | `analyst` (clusters), `proposer`, `judge`. |
| Failure policy | Partial review still ships; replay failures mark the edit "untested", which cannot be approved. |
| Budget guard | Replay only suffixes; cap replays per edit (default 10 fix + 10 guard). |
| Output | Change card: what failed, the proposed edit, score before and after, cost of the review. |
| Feeds | Every research template, by new version. |

---

## User-creatable variants: cloning a template into a methodology

Model: BMad's builder and `customize.toml` layering, Pocock's loop-me interview, and Anthropic's skill-creator test loop (`[retrieved]` `01` §Q1, `02` §6). Every template is a folder; a variant is a thin folder that points at its base and overrides values.

### Template folder

```
workflows/research.lit-review/            # shipped template, SHA-locked
  workflow.yaml                           # steps, edges, step kinds, gates (bound to content hash)
  settings.toml                           # defaults: roles per step, budgets, schedule, caps
  prechecks/new_items.py                  # zero-token wake check
  scripts/                                # fetch, parse, rank, library_write
  skills/                                 # question batteries, evidence tiers, rubric
  schemas/                                # report JSON, findings file, calibration block
  render/explainer.methods-matrix         # which fixed QMX template renders the output
  tests/  fixtures/  evals/               # fake-model run, recorded inputs, ~20 eval cases
  README.md  CHANGELOG.md
```

### Variant folder

```
workflows/mine.eurusd-macro/
  variant.toml        # extends = "research.lit-review@1.4"
  overrides.toml      # topic, sources, creators, skills added, roles, schedule, caps
  skills/             # his own skills (e.g. "ECB statement reader")
  evals/              # 3-5 cases he clicked good or bad
```

Rules for `overrides.toml`:
- May set: topic, watch lists, sources and creators, schedule, skills added, role per step (from roles that exist), output template among the allowed ones, budgets **lower** than the base.
- May tighten: any gate threshold, evidence tier minimums, number of calibration samples.
- May not: loosen a gate, raise a budget above his global cap, remove a grader, remove calibration, add a money tool. The builder's lint rejects these; changing a gate is his click in Settings.
- When the base template gets a new version, the variant is re-tested on its evals before it moves; otherwise it stays pinned.

### How he and the copilot make one

Example: "Macro analysis for EURUSD using these skills."

1. He says it in the hub. The copilot loads the workflow builder (`[retrieved]` `12` §(i)).
2. The builder looks up facts first: which macro templates exist (the macro snapshot T4, R4), which skills he has, which data feeds exist. It does not ask what it can look up.
3. One grill round, numbered, each with a recommended answer:
   1. Base: macro snapshot plus a monthly R4 review on "ECB vs Fed divergence"? (recommended: yes)
   2. Triggers: ECB and Fed decisions, euro-area and US CPI, NFP, plus a weekly Sunday run? (yes)
   3. Sources: arXiv q-fin and econ for papers, ECB and Fed statements, his two named YouTube macro creators on a B3 lease? (yes; lease asks on first use)
   4. Skills: his "rate differential" and "positioning" skills attached to the searcher brief? (yes)
   5. Output: scrollytelling page with "what it means for open EURUSD units"? (yes)
4. The builder writes the variant folder, runs the fake-model dry run on fixtures and the grader on the output, and shows the result card.
5. The variant installs **disabled**. He enables it. First run is a canary: it runs once, delivers, and waits for a thumbs up before the schedule takes over.
6. If he wants several variants together ("EURUSD desk": macro, COT positioning, rate-paper scout), the pack builder groups them into one methodology pack with a `plugin.toml`.

Other variant examples: "Paper scout for crypto microstructure only", "Lit review: regime detection methods, monthly", "Replicate every momentum paper R1 marks replicable", "Dead-end miner for prop-firm scalps only".

---

## Shared building blocks

### Reusable sub-workflows

| Block | Steps | Used by |
|---|---|---|
| `research-harness` | clarifier (attended only) → planner → 3-5 searchers `fanout` → synthesiser → citation checker → judge | R1 (deep read), R4, T4 macro, variants |
| `paper-read` | `answer_pdf_queries` with a question battery in one batched call; page-tagged output kept as evidence | R1, R2, R3, R4, R5 |
| `calibrate` (R7) | basis labels → K candidates → agreement → rerun spread → confidence rule | R1-R6, R8 |
| `audit-other-family` | fresh context, re-opens evidence windows not the card, tries to disprove | template A stage 6, R3 spec check, R2 lint review |
| `library-write` | one writer lease, IDs, files, catalog, lineage edge | R2, R3, R5, R6 |
| `render-and-grade` | schema valid, numbers resolve, Mermaid parses, headless render, screenshot | Every template's last step |
| `lab-run` | experiment spec (code ref, data snapshot, costs on, seed) → QMB → memo key | R2, R3, template B |
| `overfit-gates` | walk-forward, untouched holdout, deflated Sharpe over all trials, Monte Carlo, cost stress at 1.5x | R3 post-publication, template B |

### Pre-check scripts (zero tokens)

| Pre-check | Wakes when |
|---|---|
| `feed_diff` | New IDs on arXiv q-fin RSS or alphaXiv hot feed vs `seen_ids` |
| `new_rows` | New inventory rows or new dead ends above a count |
| `data_available` | The data a spec needs exists in the store |
| `library_dup` | No card with the same formula hash, source hash or mechanism |
| `creator_new_uploads` | New videos from listed creators (B1 public page, no login) |
| `preflight` | Keys, skills, MCP servers and delivery target resolve; else `blocked_config`, one alert, no model call (`[retrieved]` `11` §3) |

### Skills (folders under `agents/_shared/skills/`)

| Skill | Source | Purpose |
|---|---|---|
| `paper-question-battery` | new | The fixed questions every paper read asks (claim, data, period, costs, OOS, variants tried, code) |
| `evidence-tiers` | new | Ranking of papers, preprints, practitioner notes, videos |
| `lookahead-bias`, `point-in-time`, `survivorship-bias`, `transaction-costs`, `data-leakage` | ml4t, Apache-2.0 (`[retrieved]` `02` §3) | Lints and checklists, ported as script checks where possible |
| `deflated-sharpe`, `walk-forward-cv`, `cpcv`, `purging-embargo`, `backtest-overfitting` | ml4t | Gate code and explanations for `overfit-gates` |
| `pine-reader` | new | Pine parsing rules and repaint or lookahead flags |
| `replication-spec` | new | Spec fields and known traps |
| `research-operator` | ml4t pattern | Small typed tool set, read skills first, checkpoint each call, negative result allowed |
| `term-sheet` | ml4t `strategy-workflow` | Mechanism, kill criteria, capacity before code |
| `brief-template` | pstack orchestrate | GOAL, SCOPE, CONTEXT, ACCEPTANCE, VERIFY, TIMEBOX, FORBIDDEN, REPORT for every searcher |

### Model roles (Settings maps each to a model; reviewer roles on another family where one exists)

| Role | Kind of work | Cost class |
|---|---|---|
| `triage`, `section-reader`, `clarifier`, `rlm-sub` | Sort, short reads | cheap |
| `reader`, `searcher`, `extractor`, `miner`, `writer` | Read and write with tools | mid |
| `planner`, `synthesiser`, `reconciler`, `builder`, `rlm-root`, `grill` | Plan, join, code | strong |
| `validator`, `citation-checker`, `judge` | Review and grade | other family, mid |
| `vision-reader` | Frames | vision-capable, mid |
| `analyst`, `proposer`, `doctor` | Harness review, repair | mid, cheap-first for `doctor` |

### Default failure policy (every template unless its card says otherwise)

1. Before any model call: spend-neutral retry ladder 5, 15, 30 min.
2. Transient errors inside a step (429, timeout, network): retry with backoff, small cap; usage cap = `waiting`, not failed.
3. Same failure twice: the run doctor sorts it (transient, bad input, bad output, logic wrong) and may repair locally inside the budget: bigger model, more turns, cleaned input. It forks at the step and replays only the suffix.
4. Still failing: `escalate`, which pauses the run with one inbox item (cause, what was tried, cost so far, buttons: retry, bigger model, skip step, open trace, stop).
5. A gap is a result: missing sections, uncovered videos and unread papers appear in the report, not as silent omissions.
6. Finished steps never rerun; model calls are cached by (model, prompt hash, params). `[retrieved]` `13` §4.

### Default budget guard

- Per-run dollar cap, reserve-then-refund before each model call; at the cap, deliver partial and park.
- Admission control under the usage cap; scripts keep running while model steps wait.
- Searchers: 5-15 tool calls, hard stop 20 or 100 sources. Readers: 10 calls.
- Fan-out caps per template (readers 3, searchers 5, clusters 10, calibration 5 × 3).
- A pre-flight estimate is shown before any attended run above his "ask above" number.

### Memory scopes and tagged rows

| Scope | Holds | Writer |
|---|---|---|
| run | findings files, claims, evidence | the run |
| workflow | `seen_ids`, last output, topic source list | the workflow |
| home (Lab, Library) | creators and authors rated, formula traps, replication ledger | `library-write` |
| operator | rejected ideas and why, taste, "ask above" numbers | the hub, with his approval |

Tagged rows across scopes: `negative_result`, `do_not_retry`, `lesson`, `calibration_outcome`, `triage_miss`.

### Notifications

- Inbox: proposals (R1 → R3), short lists (R6), change cards (R9), escalations.
- Phone push: only escalations he marked urgent; research is rarely urgent.
- Digest: every research run, cost, silent ticks counted.

---

## Open questions (with recommended answers)

| # | Question | Recommended answer |
|---|---|---|
| 1 | Does calibration (R7) run on every claim or only headlines? | Only headlines, at most 5 per report, 3 samples each. Rerun spread on Lab numbers always, since it costs no tokens. |
| 2 | What if no second model family is configured? | Use a fresh context on the same family with a hostile brief, and label the check "same family" on the chip. Recommend one key-based family for `validator`. |
| 3 | alphaXiv: key or OAuth, and what uses quota? | API key in the keyring (`qmx/alphaxiv`). Free feed tools for pre-checks; `discover_papers` only in R4; `answer_pdf_queries` batched one call per paper. |
| 4 | May unattended runs use the B3 "read as me" YouTube lease? | Only if he sets a standing rule per origin. Otherwise scheduled R4 runs use B1 public pages and attended runs use B3. |
| 5 | What when a paper's data is something we do not have (for example, US equities with delisted stocks)? | "Could not test" result with proxy options. A proxy dataset may run as a labelled branch; its verdict never reads as a replication. |
| 6 | Is the post-publication period the holdout for R3? | Yes. Touched once; a second look is a new, counted trial. |
| 7 | Do hypotheses from dead ends share the parent's trial count? | Yes. Deflated Sharpe in template B counts the whole family, dead parents included. |
| 8 | Who may change gate thresholds? | Only him, in Settings. Variants may tighten; R9 may not propose loosening. |
| 9 | Where do research notes and component cards live? | Notes as Library knowledge rows, components as the new `component` class (`08` Q15), both in whatever store B8 settles. |
| 10 | Should R8 (RLM) ship in the first wave? | No. Keep `rlm` off until he asks a question that needs it; then build the small kernel pattern in QMX (option (a) in `13` §2). |
| 11 | What metric does R9 optimise? | Two: accepted cards per million tokens, and calibration Brier score. Plus his board iteration count from `12` §(e). |
| 12 | Pilot order? | R1 first (cheap, scheduled, shows the output format), then R5 inside template A's 4-item pilot, then R3 on one well-known paper, then R4, then R6 once 5 dead ends exist. |
| 13 | Video claims in a literature review: count or not? | Count as the lowest tier; they can raise a "could test" row, never set a verdict. |
| 14 | Whisper costs for uncaptioned videos? | Groq key only, only for uncaptioned items, cap per run (as in `08` Q12). |
