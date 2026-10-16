> STATUS 2026-10-16 (rubric walk): SUPERSEDED. See 27-rubric-walk.md. Rulings in 26 win.

# 06 — QMX through the eyes of five quants

Written 2026-10-16 by a Fable design agent. Charting only. Nothing here is ratified.

For the operator, `19-centralized-design.md` supersedes this file, `07` and `12`. This file keeps the CIS runs, the lenses, the cross-lens findings and the unmentioned angles as background.

Superseded in part by `12-design-synthesis.md` (second pass, after the operator's corrections): section 5 (journeys) is replaced by `12` section (a), which shows the situational mix of hub copilot, sub-agents and workflows per journey; "modes" in sections 3 and 4 are replaced by capability packs. The CIS runs, the cross-lens findings and the unmentioned angles still stand.

## Assumption stated up front

The operator named four quant types and forgot the fifth. This file treats the fifth as the **risk quant** (risk manager and model validator). Reason: every fund that runs the other four has one, the other four never police themselves, and the operator's own rulings ("agents read money, never move it", gates that cannot be loosened) describe that job. If he meant a different fifth (data engineer, execution quant, ML engineer), the lens below covering data quality and compute is the closest stand-in and the rest of the file still holds.

## How to read the claim labels

Following the operator's probabilistic-thinking clipping, claims carry one of three tags.

| Tag | Meaning |
|---|---|
| `[retrieved]` | Read from a file in this repo or a clipping. The source is named. |
| `[remembered]` | From training. No file backs it. Check before acting on it. |
| `[inferred]` | Reasoned from the other two. These are the design calls. |

On open questions the file lists the candidate answers first and picks one after, so the operator can see the set, not just the draw.

## How this file was made

The BMad Creative Intelligence Suite skills (`bmad-cis-design-thinking`, `bmad-cis-problem-solving`, `bmad-cis-innovation-strategy`) were read and run by hand, in role. Where a facilitator would ask the human, the agent answered as each of the five quants. Methods used, from the skills' own method tables:

| Skill | Methods run | Section |
|---|---|---|
| Design thinking | Empathy map, Jobs to be done, Point of view, How might we, Journey mapping, Storyboarding, Assumption testing | 2, 3, 5 |
| Problem solving | Problem statement refinement, Is/Is-not, Five whys, Fishbone, Force field, Constraint identification | 6 |
| Innovation strategy | Jobs to be done, Blue ocean four actions, Three options, Three horizons, Decision gates | 7 |
| Advanced elicitation | Pre-mortem, Red team, Assumption audit, Stakeholder lens rotation | 8 |

Inputs: `01-bmad.md`, `02-pocock-pstack.md`, `03-workflow-engines.md`, `05-qmx-today.md`, `BACKLOG.md`, `README.md`, `UI-NOTES.md`, and the ten clippings named in the brief. The superseded files under `archive/` were not used.

---

## 1. The design challenge

**Challenge statement.** One non-technical operator wants to run the research desk of a small quant fund by himself, with agents doing most of the work while he sleeps, without ever letting an agent move money. QMX today has a working agent harness and a mini-app runtime, but no workflow engine, no session homes, one locked plugin, empty skills, and no memory beyond a per-workspace file (`[retrieved]` 05 §gaps 1-14).

**Success looks like.** He describes a routine or an idea roughly, QMX turns it into a gated pipeline, the pipeline runs unmanaged overnight inside half of his spare Claude usage, and in the morning he gets a picture and three decisions, not a log.

---

## 2. Empathy: what each quant says, thinks, does and feels

The five quants are personas for the operator's own hats. He wears all five, badly on some days, which is the point of writing them down.

| Quant | Says | Thinks | Does | Feels |
|---|---|---|---|---|
| Researcher | "Is this edge real or did I fit the noise?" | Every good backtest is guilty until proven innocent. | Reads, forms a hypothesis, codes a signal, runs a test, logs the result, moves on. | Excited at 2am, embarrassed by Friday. |
| Trader | "What is my exposure right now and what happens at 8:30?" | Fills, slippage and events kill more strategies than bad signals. | Pre-open brief, watches positions, journals after close. | Wants to be told, fast, in one line, with a source. |
| Developer | "Where does this job run and can I rerun it?" | If it is not reproducible it did not happen. | Builds tools, data feeds, tests, mini apps, workflows. | Tired of rebuilding the same scraper. |
| Portfolio manager | "Which of these take turns, and how much goes in each?" | One strategy is a bet; a book is a business. | Reviews correlation and drawdown against budget, promotes and demotes, signs. | Wants fewer, better decisions on his desk. |
| Risk quant | "Who checked this, and with what?" | The builder must never grade his own work. | Re-runs validation independently, stress-tests, watches limits, signs off or refuses. | Calm only when the gate is a script, not a promise. |

Sources: the roles come from BMad's organogram mapping (`[retrieved]` 01 §Q3) and ml4t's seven-stage strategy workflow (`[retrieved]` 02 §3). The feelings are `[inferred]`.

### Point of view statements

- The researcher needs a loop that tests many ideas overnight because his attention is the bottleneck, and he needs that loop to count its own trials because more testing finds more bogus signals (`[retrieved]` "The Loop Runs While You Sleep": Man Group's AlphaGPT note).
- The trader needs alerts that arrive with a source link and a suggested action, because an alert he cannot verify is noise (`[retrieved]` Skydive clipping: "never pass me anything you cannot give me a link for").
- The developer needs one skill format and one place to run jobs, because every mini app, workflow and scraper otherwise becomes its own convention (`[retrieved]` 05 §1: two unconnected mini-app halves, no SDK).
- The portfolio manager needs strategies that take turns, not a holy grail, because rebalanced uncorrelated losers can become a winning book (`[retrieved]` "Why a Portfolio of Trading Strategies": Parrondo, Shannon's demon).
- The risk quant needs gates that an agent cannot loosen, because a prompt can be argued with and a script cannot (`[retrieved]` BuildAlpha: "it cannot loosen the gate to make results look better"; 01 §scripts: "if identical input gives identical output, script").

### How might we

1. How might we let the researcher run wild in the Lab while the gate stays rigid?
2. How might we wake a model only when something changed, so the 50% cap buys more work?
3. How might we make every agent output a picture and a decision, never a block of text?
4. How might we keep negative results so revolution 400 is smarter than revolution 4?
5. How might we let the copilot build and maintain mini apps without ever publishing one on its own?
6. How might we keep the whole system working on any capable model, not only Claude?
7. How might we give the Portfolio copilot a purpose that survives the risk and sizing redesign?

---

## 3. The five lenses

Each lens answers the same seven questions. "Today" cites `05-qmx-today.md`.

### 3.1 Quant researcher

| Question | Answer |
|---|---|
| Daily loop | Read (papers, news, Library), form one hypothesis with a mechanism and kill criteria, pull data, prototype the signal, backtest net of costs, judge, log the result (especially a negative one), next idea. |
| QMX journeys | Ideation (grill the idea), hypothesis term sheet, Lab experiment (notebook, node graph or code), backtest, validation (walk-forward, deflated Sharpe, untouched holdout), hand-off card to the PM, Library search for prior work and dead ends, small mini apps for data and signal views. |
| Organogram role | The Lab copilot with the most freedom (prototype, arena, hill-climb, autonomous-run). A review panel of lenses at the gate (overfit hunter, leak hunter, regime skeptic, cost realist). The hub copilot for "what next". |
| Workflows that serve him | Hill-climb loop with an overfitting brake; literature and news scan; backtest sweep; strategy review crew; deep-research template with hard caps. |
| Overnight loop | Generate, backtest, validate, detect plateau, change the search space (signals, fitness, filters), restart. Every revolution writes what it tried and why to memory. `[retrieved]` BuildAlpha loop. |
| Gates he never lets an agent loosen | Holdout data stays untouched. Every trial is counted and the Sharpe is deflated by the count. Costs on. No lookahead. "Sharpe above 2 on daily data: assume lookahead until proven otherwise" (`[retrieved]` ml4t). |
| Output he wants | One result card per run: the number, the run count, the spread, and what could fake it (costs off, leakage, survivorship). An equity and drawdown picture. A trial log. "What I cut and why." |
| Today | Agents can only run pre-registered QMB configs; no sweep, optimize, walk-forward or robustness tool; no notebooks; no board object (`[retrieved]` 05 §2, gaps 7-8). |

### 3.2 Quant trader

| Question | Answer |
|---|---|
| Daily loop | Pre-open brief, exposure check, events calendar, watch fills and slippage, adjust within rules, post-close journal. |
| QMX journeys | Monitoring, paper-to-live per pod, road to live, kill matrix, events and news watch, journal summary, broker connections in Settings. |
| Organogram role | The Portfolio copilot in "watching" mode; standing trader agents (PULSE-style monitors) that read and report; a notifier. |
| Workflows that serve him | News and sentiment scan with cross-source confirmation; daily decay-spotting (the old WF3); position reconcile; morning brief. Scanners are zero-token scripts; the model wakes only on change (`[retrieved]` Hermes `wakeAgent`; "Not Every Agent Workflow Needs AI"). |
| Overnight loop | Scan events and filings, reconcile positions against the broker read, spot decay, draft the brief. Nothing moves money. |
| Gates he never lets an agent loosen | The money hook (read-only, always). Demo accounts only for trials. The kill switch is human-only. Live promotion is his click. Max exposure is a script. |
| Output he wants | A brief under 150 words, pictures first (`[retrieved]` pstack ketchup). Alert cards with instrument, signal, confirmations, source links, suggested window. A "needs you" list with defaults and "what happens if you do not answer". |
| Today | Broker reads and unsigned proposals exist; `propose_order` never opens a broker connection; no read model for pods, MIS or kill switch; no scheduler for any chat (`[retrieved]` 05 §5, gap 2, gap 9). |

### 3.3 Quant developer

| Question | Answer |
|---|---|
| Daily loop | Build or fix a tool, check data quality, write tests, keep runs reproducible, watch compute. |
| QMX journeys | Mini app create, edit, test, publish, rollback, delete; workflow build from a rough description; skill build with evals; data pipelines; compute placement; CI. |
| Organogram role | The hub copilot plus builder skills (`build-mini-app`, `build-workflow`, `debug-app`), a toolsmith for new skills, a two-model code review. |
| Workflows that serve him | Overnight builder (tracer-bullet tasks with tests first); app road stages (build, tests, sandbox, shadow, live); zero-token cron checks on data freshness. |
| Overnight loop | Take a ticket, write the failing test, make it pass, run the road stage, leave evidence. Publish waits for the operator. |
| Gates he never lets an agent loosen | Publish and install ask. Tests before publish. Versions are immutable and content-hashed. Secrets never appear in chat. Deterministic lint before review. |
| Output he wants | A PR-style card: the smallest visual (file tree, diff sketch), evidence before and after, door type (one-way or two-way) and blast radius (`[retrieved]` 02 Pocock `pr`). |
| Today | The runtime, road and control door exist. Skills are empty placeholders, there is no delete or uninstall, trust is caller-chosen, and the harness loads exactly one SHA-locked plugin (`[retrieved]` 05 §1 gaps 1-6). |

### 3.4 Quant portfolio manager

| Question | Answer |
|---|---|
| Daily loop | Review the book (exposure, correlation, drawdown against budget), read briefs, decide promotions and demotions, rebalance by rule, allocate. |
| QMX journeys | Portfolio overview and pods, correlation, portfolio backtest, promotion card signing, road to live, Library view of what is in the book. |
| Organogram role | The Portfolio copilot in chief-of-staff mode: owns a standing goal, works through background agents, more instruction and less freedom than the Lab (`[retrieved]` BACKLOG B26). An Anti-Consensus panel for go/no-go calls (`[retrieved]` 01 party mode). |
| Workflows that serve him | Read-only portfolio simulations (correlation, rebalance frequency, sizing variants) ; regime and decay reports; draft promotion and demotion proposals. |
| Overnight loop | Run the simulations, compare against the current book, draft at most three proposals with a recommendation and a default. |
| Gates he never lets an agent loosen | Allocation changes need his signature. Sizing authority lives in the GitBook and node docs, not in QMX chat (`[retrieved]` memory `qmx-operator-standing-rules`). The risk budget is a script. An agent never picks its own trust level. |
| Output he wants | A one-page book picture (which strategies zig when others zag), three decision cards with recommendation, default and consequence of silence. |
| Today | UI tools (`pod.bring_from_lab`, `promotion.prepare_card`, `risk.explain`) have no backend twin; the risk and sizing unit is unsettled, so pods may change (`[retrieved]` 05 §5). |

### 3.5 Risk quant (assumed fifth)

| Question | Answer |
|---|---|
| Daily loop | Validate models independently, run stress and scenario tests, watch limits, keep the model inventory, challenge assumptions, sign off or refuse. |
| QMX journeys | The validation stage (re-run by a different context and model family), stress board, interventions, kill matrix, pre-live checklist, model inventory in the Library. |
| Organogram role | A validator lens at every gate, deterministic risk scripts, and an independent reviewer on a different model family (`[retrieved]` pstack interrogate: "adversarial signal comes from model diversity"). |
| Workflows that serve him | Independent re-validation of live pods against their original assumptions (drift, regime); limit-breach watch as a no-agent cron; model inventory audit; pre-mortem on every promotion card. |
| Overnight loop | Re-run every live pod's validation on fresh data, compare to the term sheet, flag drift, write a red/amber/green list. |
| Gates he never lets an agent loosen | The builder never grades itself. Gates bind to the graph's content hash. Limits are scripts. The audit trail is append-only. "The model proposes, the pipeline decides" (`[retrieved]` BuildAlpha). |
| Output he wants | Pass or fail with an evidence pointer, a red/amber list, and for every number "what would push it outside the range". |
| Today | Nothing. There is no validation role, no independent reviewer, no gate bound to a hash, and the significance gates in QMB are library calls agents cannot reach (`[retrieved]` 05 §2 table, gap 8). |

---

## 4. Crossing the lenses

### 4.1 Where all five agree

| Agreement | Who says it loudest | Design consequence |
|---|---|---|
| Anything a rule can decide is a script, not a model call. | Developer, risk | A `script` and `rule` node kind that costs zero tokens, and a zero-token precheck before every loop (`[retrieved]` 03 §9). |
| Agents read money, never move it. | Trader, PM, risk | Already a hook (`[retrieved]` BACKLOG ruling 10-13 04:14). Keep it out of every prompt and in the hook. |
| Stop on evidence, never on confidence. | Researcher, risk | Every loop has a checkable stop predicate and a trial budget (`[retrieved]` harness/loop/graph clipping). |
| Negative results are an asset. | Researcher, PM | A negative-results memory the next run reads before its first generation (`[retrieved]` BuildAlpha). |
| Briefs, not logs. | Trader, PM | Output methodology: picture first, under 150 words, decisions with defaults (`[retrieved]` Karpathy post; pstack ketchup). |
| One pipeline, roles as lenses. | All | One capability graph idea to library; personas are thin menus over shared workflows (`[retrieved]` 01 §Q3). |

### 4.2 Where they conflict, and the recommended resolution

| Conflict | Side A | Side B | Resolution `[inferred]` |
|---|---|---|---|
| Freedom vs rigidity | Researcher wants the Lab loose. | Risk wants gates rigid. | Freedom inside the Lab, rigidity at the gate. The gate is a node in the graph, not a persona's opinion. The Lab copilot can propose anything; only a tested method is promoted. |
| Speed vs the usage cap | Trader wants alerts in minutes. | Background work is capped at 50% and pauses. | Scanners are scripts that never touch the cap. The model wakes only when the script reports a change. Pausing applies to model nodes, never to scripts. |
| Flexible plugins vs one locked plugin | Developer wants mini apps to contribute skills and tools. | The harness refuses any plugin whose SHA differs. | A signed plugin registry with a trust ladder. Agent-built plugins install disabled. The lock stays; it just covers more than one plugin. |
| Allocation help vs unsettled sizing | PM wants sizing suggestions. | The risk and sizing redesign is in another session. | The Portfolio copilot runs read-only simulations and explains. Sizing suggestions wait for that session's ruling. |
| Hill-climbing vs multiple testing | Researcher wants the loop to climb all night. | Risk knows more tests find more bogus signals. | The trial count is part of the loop state. Deflated Sharpe and the untouched holdout are nodes in the loop, not advice in a prompt. |
| Persistent sessions vs fresh review | Operator: no fresh session per decision. | Risk: the builder must not grade itself. | The working session persists. The reviewer is a separate child session on another model family, started by the graph. Both rules hold. |
| Model-agnostic vs one Claude engine | Developer wants any model. | The engine is the Claude Agent SDK. | QMX owns the graph; Claude is one node executor; `llm` nodes go through the relay to any provider. Skills name roles, never models. |

### 4.3 The one constraint behind the conflicts

Theory of constraints, from the problem-solving skill: the binding constraint is the operator's attention and judgment, a few hours a day, zero at night. Every conflict above resolves the same way: spend his attention only on taste gates and money, and make everything else a script, a loop with evidence, or a default he can override later.

---

## 5. The journeys, stage by stage

The pipeline every lens uses, with who owns each stage, which role serves it, what gate closes it, and what exists today.

| Stage | Owner lens | Organogram role | Workflow or template | Gate (deterministic unless marked) | Today `[retrieved]` 05 |
|---|---|---|---|---|---|
| 1 Ideation | Researcher | Hub or Lab copilot, grilling rounds with recommended answers | Grill the idea; arena of 2-3 variants on different models | None (taste only) | Nothing; no skill content |
| 2 Hypothesis | Researcher, risk | Lab copilot | Term sheet: mechanism, kill criteria, capacity, data needed | Term sheet complete (script checks fields) | Nothing |
| 3 Lab experiment | Researcher, developer | Lab copilot; Experimentation Board | Notebook, node graph or code; run one step, a section or all | Draft never runs live; only published versions do | Editor panel is demo only; no board object; `run_scope` deleted (§3, §7) |
| 4 Backtest | Researcher | Lab worker role | Backtest sweep template on QMB | Costs on; data snapshot and engine version in the memo key | QMB exists; agents can run only pre-registered configs |
| 5 Validation | Risk | Validator lens on another model family; scripts | Walk-forward, deflated Sharpe, CPCV, leakage checks, holdout | All pass, bound to the graph hash; no self-grading | QMB has significance gates as library calls only |
| 6 Portfolio | PM | Portfolio copilot | Correlation, portfolio backtest, promotion card | His signature; sizing from the authority docs | UI only; no backend pod or promotion object |
| 7 Paper | Trader | Trader agent (monitor) | Paper run per pod, decay spotting | Paper length and metric thresholds (his values) | QMN modules exist; no read model |
| 8 Live and monitoring | Trader, risk | Trader agents, limit watch cron | Morning brief, limit-breach watch, re-validation | Kill switch human-only; money hook | Broker reads only |
| Library (Strats) | All | Librarian lens | Catalogue, dedupe, retire, negative results | Nothing promotes without stage 5 evidence | Five unjoined stores (§4) |
| Mini apps | Developer | Hub copilot plus builder skills | Grill, prototype variants, tracer-bullet build, review, road stages | Publish and install ask; tests before publish | Runtime and road exist; skills empty; no delete |

### Storyboard: one week in the designed QMX `[inferred]`

1. Monday evening. He says "I think funding-rate spikes on perps predict a reversal within two hours." The Lab copilot grills him in two rounds (five numbered questions, each with a recommended answer; "yes" accepts) and writes a term sheet with a kill criterion.
2. Monday night. A hill-climb loop runs inside the cap: script loads data, model proposes one change, script backtests, script validates, model reads the verdict, repeat. Plateau after 40 trials. The loop moves the search space once (adds a volume filter class), climbs again, stops at the trial budget. It writes four negative results to memory.
3. Tuesday morning. The home screen shows a picture (equity, drawdown, trial spread), 120 words, and two decisions: promote candidate 3 to validation (recommended yes), widen the universe (recommended no, costs unknown). He taps yes on the first.
4. Tuesday night. A validator child session on a different model family re-runs walk-forward and deflated Sharpe on untouched holdout. It passes. The gate node records the graph hash.
5. Wednesday. The Portfolio copilot runs a read-only correlation check against the book and prepares a promotion card. He signs it in the UI. A paper pod starts.
6. Thursday to Sunday. A trader agent watches the paper pod; a zero-token cron checks limits every five minutes and wakes a model only on breach. Sunday night's brief says "paper Sharpe 1.1 after 4 days, inside the term sheet range; nothing needs you."

---

## 6. Problem solving: why solo quant research fails

Problem statement, refined. A solo quant with good tools still ships almost nothing to a live book, because the parts of the job that need attention (judging a plateau, validating independently, remembering dead ends, deciding what goes in the book) happen only while he is awake and only in prose.

### Is / is not

| | Is | Is not |
|---|---|---|
| Where | Overnight, unattended; at the hand-off between stages | Inside a single backtest run (QMB is fine) |
| When | After the first good-looking result; after three weeks away from a project | During a focused afternoon with the operator present |
| Who | The operator judging his own work | A script deciding a threshold |
| What | Prose outputs, lost negative results, loosened gates, fresh sessions that forget | Compute, data access, model intelligence |

### Five whys, three chains

| Symptom | Why 1 | Why 2 | Why 3 | Root cause |
|---|---|---|---|---|
| Strategies backtest well and die live | The loop climbed into noise | No trial count, holdout touched | The gate was advice in a prompt | Gates are not scripts bound to the graph |
| Research stalls for weeks | The plateau call needed him | Nothing watches evidence while he sleeps | No loop with a stop rule | No autonomous loop with evidence and budget |
| The same dead end is found twice | Last month's run left no trace | Memory is per workspace and unstructured | No negative-results store | No memory scopes and no lessons table |

### Fishbone (categories from the skill)

| Category | Causes |
|---|---|
| People | One head wears five hats; builder grades his own work; attention runs out at night |
| Process | No gate ladder; no term sheet with kill criteria; promotion by feel |
| Materials (data) | No point-in-time discipline; survivorship; costs off by default |
| Equipment (tools) | No workflow engine; one locked plugin; empty skills; five unjoined Library stores |
| Environment | 50% usage cap; one Claude account; outputs as text |

### Force field

| Driving forces | Restraining forces |
|---|---|
| A harness that runs chats, approvals, usage and delegation already exists (HP8-HP17 built) | No engine, no homes, no scheduler |
| The operator's rulings are clear on money, cap and trust | The risk and sizing unit is unsettled, so the Portfolio half is blurry |
| ml4t gates are Apache-2.0 Markdown, ready to port | Skills are empty and nobody has written QMX's format |
| Clippings and research already contain the loop and output methods | The methodology document itself does not exist |

### Constraint and the lever

The constraint is attention. The lever (BMad bmad-loop, pstack orchestrate): no LLM in the control loop. Plain code picks the next item, sets budgets, runs the gates and decides completion. Models do only the creative step, in fresh contexts. The operator's attention is spent on taste gates and money. Everything in this map is in service of that one move.

---

## 7. Innovation strategy: where QMX's edge is

### Jobs to be done

The operator hires QMX to turn rough trading ideas into a gated, growing book of strategies that take turns, while he keeps the only hand on money. He does not hire it to be a chatbot, a terminal, or a strategy vending machine.

### Blue ocean four actions `[inferred]`

| Eliminate | Reduce | Raise | Create |
|---|---|---|---|
| Logs and text blocks as the primary output | Tokens spent on mechanical work (scripts, prechecks) | Validation rigor (independent model family, deflated Sharpe, hash-bound gates) | Methodology as data: a capability graph with gates the engine reads |
| The single holy-grail strategy hunt | Human touches per run (push checkpoints right, defaults) | Negative-results memory | "Vibe coding for trading strategies": a messy board whose runnable parts promote only when tested |
| LLM extraction for the Library (parse the edges that already exist) | Claude-only pieces (roles, relay, fallbacks) | Visual briefs with sources | A lessons loop that turns repeat mistakes into checks |

### Three strategic options

| Option | Description | Pros | Cons |
|---|---|---|---|
| A. Quant OS for one operator (methodology first) | Ratify the methodology, build the small engine, ship five templates, wire homes and plugins; everything model-agnostic. | Fits the rulings; each piece reusable; no API spend. | Slower first visible result; engine is new code. |
| B. Strategy factory (Astra-style eight bots) | Named bots per stage, scanners on a cheap model, hypothesis and backtest on a strong one, Telegram alerts. `[retrieved]` RohOnChain clipping. | Fast demo; clear roles. | Needs paid APIs he refuses; bots as personas duplicate work; no gate ladder; the clipping is marketing (`[inferred]`). |
| C. Notebook plus copilot | Keep the Lab as notebooks with a helper; no engine; no loops. | Cheapest. | Nothing runs while he sleeps; fails the stated goal. |

**Recommendation.** Option A, borrowing B's pipeline shape (scan, hypothesize, backtest, validate, deploy-to-paper, risk, notify) as the first template set, not as eight standing agents.

### Three horizons

| Horizon | Contents |
|---|---|
| H1 (this map) | Methodology umbrella, engine contract, homes, plugins, skill format, role table, five templates, output and memory methods, build plan. |
| H2 | Experimentation Board object, lessons loop, mini-app lifecycle by the copilot, Strats read contract joined to the graph, evals on every skill. |
| H3 | Trader agents on demo with computer use (after B17a), server runs for days (B46), phone approvals (B14), voice (B15). |

### Decision gates for the strategy itself

- Go past H1 only when one template (the hill-climb with brake) has run three nights unmanaged inside the cap and produced a brief he could act on.
- Pivot if the engine takes more than the harness did (HP3-HP17) to reach that point; the fallback is chats-as-steps on background chats with a scheduler, no graph.

---

## 8. Pre-mortem and red team

### Pre-mortem: it is March 2027 and the methodology failed. Why?

| Failure | Cause | Prevention (ticket) |
|---|---|---|
| The engine never shipped | Scope grew to LangGraph parity | Thin contract first (`workflow-engine-contract`); chats-as-steps fallback named in the contract |
| The methodology became a 2,000-line AGENTS.md nobody reads | Every ruling got pasted in | Small verified index; "each line must change agent behaviour"; audit only shrinks it (`[retrieved]` 01 §Q2 12) |
| Loops were useless under the cap | Every tick woke a model | Zero-token prechecks; scheduler parking; drain not kill (`pause-at-cap`, `triggers-and-scheduler`) |
| A gate got loosened | The gate lived in a prompt | Gates are scripts bound to the graph hash (`strategy-pipeline-gates`) |
| He drowned in approval asks | Checkpoints were not pushed right | Autonomy policy with defaults and expiry (`autonomy-policy`) |
| The Library graph never joined | Waited for an LLM to extract | Parse the edges that exist today (`library-read-contract`) |
| "Model-agnostic" was a lie | Workflow tool, TS-only hooks, auto memory | Fallback per piece (`model-agnostic-audit`) |
| The Portfolio copilot had nothing to do | Sizing stayed unsettled | A purpose that is read-only now and grows later (`portfolio-copilot-purpose`) |

### Red team: attacking the premises

| Premise | Attack | Verdict `[inferred]` |
|---|---|---|
| "Methodology is the umbrella that compiles the organogram and workflows." | A document cannot compile anything; only data the engine reads can. | Holds if the methodology is stored as data (capability graph, gate table, role table, autonomy table) plus a short constitution. The ticket `methodology-umbrella` asks for both. |
| "Workflows are mostly autonomous work." | Autonomous work under a 50% cap on one account is a few hours of model time a night. | Holds only with scripts doing most steps. The capacity should be measured in the first template run (`[remembered]` nothing yet measures model minutes per night). |
| "Vibe coding for trading strategies." | Vibe coding ships untested code; in trading that loses money. | Holds with the promotion rule: the board is messy, only tested methods leave it. The gate ladder is the difference. |
| "One plain copilot that compiles everything across." | A hub that does everything becomes a bloated prompt. | Holds if the hub routes by scanning artifacts against the capability graph, not by remembering (`[retrieved]` 01 §Q2 3). |
| "Any capable LLM." | The engine is the Claude Agent SDK. | Holds at the node level (relay), not at the engine level. Say so in the umbrella. |
| "Memory matters most for autonomous workflows." | Unstructured memory makes loops worse (stale facts, last-write-wins). | Holds with scopes, size limits, one writer per scope and a consolidation step (`[retrieved]` 03 §9.3; Hermes memory rules). |

### Assumption audit (weakest first)

| Assumption | Confidence | Impact if wrong | Test |
|---|---|---|---|
| Background chats can be started by a scheduler soon | Medium (`NewChatIn` has no `kind`; Python API only) | High | First engine packet |
| The Claude Workflow tool works from the SDK on a Max login | Low (`[retrieved]` 03 open question) | Medium; it is only one node type | Probe in `workflow-engine-contract` |
| `SDKUsageReport.rate_limits` arrives often enough to govern | Low (experimental) | High for pause-at-cap | Probe in `pause-at-cap` |
| The five Library stores can be joined by parsing alone | Medium-high (CT-07 edges are typed) | Medium | `library-read-contract` |
| He will accept review by a second model family on a key provider | Medium (he pays OpenRouter keys) | Medium | `role-to-model-table` |

---

## 9. Angles the operator has not mentioned

Each is `[inferred]` from the lenses unless a source is named.

| Angle | Why it matters | Where it lands |
|---|---|---|
| Negative results as a Library kind | The cheapest edge; nobody keeps them (`[retrieved]` BuildAlpha). | `memory-scopes-and-lessons`, `library-read-contract` |
| Kill criteria at hypothesis time | A term sheet without a kill rule never dies (`[retrieved]` ml4t). | `strategy-pipeline-gates` |
| Independent validation on another model family | Same model writing and grading shares blind spots (`[retrieved]` harness clipping, pstack interrogate). | `role-to-model-table`, `strategy-pipeline-gates` |
| Gates bound to the graph's content hash | A gate that moves with the prompt is not a gate. | `workflow-engine-contract` |
| Point-in-time data and survivorship | The silent killers; no QMX document names them. | `strategy-pipeline-gates` |
| Refusal as an output | "I could not check this" beats an invented section (`[retrieved]` Skydive; 40M-docs refusal ladder). Labels retrieved/remembered/inferred on every claim. | `output-methodology` |
| Parse, do not extract, for Strats | The 40M-documents build got 929M edges for zero model calls and found that its LangGraph agent loop was worse than the plain pipeline (`[retrieved]` clipping headings). | `library-read-contract` |
| Capacity and cost realism in the term sheet | A great edge on $10k is not a strategy. | `strategy-pipeline-gates` |
| Alpha decay watch as a zero-token cron | Decay is the one thing the loop must watch forever. | `triggers-and-scheduler`, `first-templates` |
| Idempotent side effects in nodes | Resume after a pause reruns a node; a non-idempotent script double-posts. | `workflow-engine-contract` |
| One writer per memory scope | Two agents writing MEMORY.md is last-write-wins (`[retrieved]` Deep Agents note). | `memory-scopes-and-lessons` |
| Pre-flight estimate before a long run | Time, share of the window, and what pauses it (`[retrieved]` UI-NOTES spin 9). | `output-methodology`, `pause-at-cap` |
| Paper-trading length rule | He has never set how long paper must run. | `strategy-pipeline-gates` (HITL) |
| Evals re-run when the model changes | Model-agnostic means re-checking skills per model (`[retrieved]` 01 §Q5). | `evals-harness` |
| Session persistence vs fresh review are different things | He ruled against fresh sessions per decision; review still needs a fresh context. | `autonomy-policy` |
| Standing orders pasted into every spawn | pstack `preferences.md`; the cheapest way to make every agent behave like he wants. | `operator-mode-skill` |
| Variants as git branches with a UI comparison | He raised it (B36); nobody has tied it to the engine's fan-out. | Fog |
| Compute placement per node | "Show where every job runs" applies to each node, not only to jobs. | Fog |

---

## 10. Open questions, with the candidate set shown before the pick

| Question | Candidates | What would make each right | Pick `[inferred]` |
|---|---|---|---|
| What is the Portfolio copilot for? | (a) Chief-of-staff watcher: explains the book, prepares cards, runs read-only sims. (b) Allocator: proposes sizing and rebalancing. (c) Monitor: decay and limit reports, kill recommendations. | (a) if sizing stays elsewhere; (b) only after the risk session rules; (c) if trader agents do not exist yet. | (a) plus (c) now; (b) later. |
| Is the Experimentation Board a backend object? | (a) Yes, small: board = notes plus a workflow draft with run scope. (b) No: Lab layouts plus Library drafts. (c) Notebook is the board. | (a) if "run this section" must survive restarts; (b) if docs' client-only rule stands; (c) if notebooks ship first. | (a), because run scope needs the engine's checkpoint. |
| Where does the methodology live? | (a) A plugin file set (constitution plus data tables) loaded per home. (b) `docs/` only. (c) The system prompt. | (a) if the engine reads tables; (b) if it is documentation; (c) never. | (a) with a short constitution. |
| How do trader agents trade on demo? | (a) Not yet; read-only monitors only. (b) Through `propose_order` on demo accounts with an allow rule. (c) Computer use. | (a) until B17a is designed; (b) if the broker layer accepts demo-scoped writes; (c) on hold. | (a) now, (b) as the next step. |
| What runs a node's model? | (a) Role name resolved by a settings table. (b) A profile name in the workflow file. (c) The engine picks. | (a) keeps skills model-agnostic; (b) is what `delegate` does today; (c) needs the orchestrator from B35. | (a), with (b) as the storage under it. |
| Sync or async nodes for delegation? | (a) Keep sync depth-1 and run fan-out in the engine. (b) Add job handles to `delegate`. | (a) if the engine owns concurrency; (b) if chats must spawn children on their own. | (a). The engine owns fan-out; `delegate` stays a helper call. |

---

## 11. What this file asks of the operator (HITL items, with the recommended answer)

The Wayfinder map in `tracker/qma-v2/wayfinder/` holds the full tickets. The top five are:

1. Workflow engine contract: adopt the `03 §9` shape (script, rule, llm, agent, human, subflow, grader, fanout nodes; SQLite checkpoints; drain-not-kill). Recommended yes.
2. Session homes: a home is `{kind, project_id}` on the control session, chosen at start, never silently changed; it selects plugins, workspace, memory scope and the UI badge. Recommended yes.
3. Copilot roster: one hub copilot plus Lab and Portfolio modes of the same copilot, with lenses as review panels, not three agents. Recommended yes.
4. Pipeline gates: the eight-stage ladder in section 5 with the listed deterministic gates; paper length and metric thresholds are his numbers. Recommended adopt the ladder, numbers later.
5. Portfolio copilot purpose: watcher plus monitor now; allocator after the risk session. Recommended yes.
