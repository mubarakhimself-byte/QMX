# X7: where agents come in, for risk and sizing

Stage B expansion by linking, layer X7. File id `X7-agents`. Written 2026-11-03 by one Opus agent, headless, on `linking/STAGE-B-BRIEF.md`.

**What this layer is.** The risk-and-sizing template must let agents help without ever touching money. This file links components into hybrids for that: every risk and sizing job an agent could do, the door agents use, the tools behind it, how agent noise is kept away from him, and how the QMX Lab, MCP-driven agents and the later agent department (`handoff/AGENT-DEPARTMENT-SEEDS.md`) plug in without rework. QMA (agent system) changes are **flagged, not designed**. Nothing here ranks; the Fable funnel judge ranks (`linking/RANKING.md`).

**How to read it.**
- Component ids are short: `A4-104` means `A4-template-agents-telemetry-104`; `A1` sizing-allocation, `A2` brakes-drift-exits, `A3` structure-regimes-scenarios, `A5` topup.
- Ledger ids in `code` exist in `ledger/variables.yaml`; ids marked *(new)* are in `ledger/additions/X7-agents.yaml`.
- His asks are cited by `seeds/SEEDS.md` id (D41, C27) or TLH n ("What the technical lens must hold", item n).
- Opinions are marked **[judgment]**.
- Method record: brainstorming memlog `linking/stage-b/X7-agents/.memlog.md`, intent `brainstorm-intent.md`, problem solving `problem-solving.md`, roundtable `roundtable.md`, all in that folder.

---

## 0. Ground: what agents can and cannot do today

Checked at the stack tip `D:/QMX-worktrees/bld-us-c13` (d02af358) and in G2, G8, G9, G10.

| Fact | Source |
|---|---|
| The host names every caller. A chat is `agent:<session>`, an `/mcp` client is an agent, a workflow run is `workflow:<run>`. | `qmx-agents/packages/qmx-host/src/qmx_host/door.py:1-30` |
| A `manage` operation, and a `money` app's job, answer only to the operator principal. | `qmx_host/host_route.py:91-94` (`admits`) |
| The trading-node app (`risk = "money"`) serves an MCP server. Its `kill` (escalates, "never lowers"), `pause`, `resume`, `flatten`, `deploy`, `withdraw` and `bind` are `manage`. `status`, `units`, `positions`, `journal_tail` and `passport` are `domain_write` and agents can call them. | `qmx-agents/apps/trading-node/app.toml` |
| Agent rows write unit drafts only (`unit_new`, `unit_check`, `blocks_*`), and read journals, readings, instruments and the node. No row saves a block, runs the socket contract, publishes, promotes or sends an order. | G8 4.1 |
| Promotion (`POST /api/units/promote`) answers only to him. | G9 3.2 |
| Workflows that watch: `dc-decay-and-limit-report` (tighten-only cards), `s5-live-day-replay`, `dm-demo-monitor`, `s2-tag-units-to-markets`, `gw-guard-watchdogs`. All inform only. `pp-proposal-pack` (at most three cards) and `p1-portfolio-combination` wait for this session. | G9 7.2; G8 4.2 |
| Rulings: only he promotes (G2-1); the only automatic change in trading is a unit's own risk rule stopping it (G2-2); agents in the slow lane only (G2-5); only the node sends orders (G2-6); nothing a unit needs may depend on router, MIS, PC link or Library (G2-11). | G2 section 1 |
| Every generation kept one split: agents produce and diagnose, deterministic code gates and applies, he promotes. | G10 2.4 |

What this means for X7 **[judgment]**: half the door already exists (principals, operator-only `manage`). What is missing is (a) a declared *direction* on every operation, (b) a typed way for agent evidence to reach a unit without breaking G2-2 and G2-11, (c) a card format bound to its exact effect, (d) counting, and (e) a budget for his attention.

---

## 1. The job map: every risk and sizing job an agent could do

"Script" means deterministic code on a schedule or trigger. "Both" names which half each does. Direction: **cut** lowers risk, **raise** lifts it, **structure** is a new version or unit.

| # | Job | Script part | Agent part | Verdict | Direction | Hybrid |
|---|---|---|---|---|---|---|
| 1 | Propose isolation with evidence | two-tell confirmation, turbulence and absorption per bucket, SQS K-of-N, isolation lifecycle | read 20 days of readings and journals; nominate a scope with evidence fields and a time to live | both | cut | H21 |
| 2 | Explain drift | input-first checks, cone, CUSUM, e-detectors, cause decomposition; zone and size step | ranked hypotheses from a bounded cause list, next check, fix card when the cause is cost or code | both (script decides) | cut, none | H22 |
| 3 | Generate scenarios | harness runs, validation through the strategy, nightly stress-engine backtest, hidden rotating set | write adversarial scenarios; reverse-stress search; map regimes and news to shocks | both (agent-heavy) | none | H12, H23 |
| 4 | Propose tuning | learner target and bounds, plateau tuning, screening, conservative bandit among arms | add candidate arms; propose derivation swaps; explain the learner's target | both | structure | H24 |
| 5 | Find cost windows | hourly cost profile, cell estimates with pooling, out-of-sample confirmation | nominate candidate cells from cost and activity maps, fixes, funding, sessions | both (script-heavy) | raise or cut | H25 |
| 6 | Read micro and macro structure | spread, depth, flow imbalance, turbulence, regime probabilities | slow-cadence labels, macro vector with expiry, per-session summaries, capacity veto | both | cut | H26, H39 |
| 7 | Read journals | aggregates: loss points, fires, MAE and MFE, exit mechanism, FI cuts vs time exits | necropsy of benched units; patterns no script encodes; draft new detectors | both | none | H27 |
| 8 | Draft template versions | self-test card, resize replay, scenario battery, layer H, shadow | draft the profile version; write the card's plain words | agent drafts | structure | H28 |
| 9 | Draft promotion packs | pre-queue checks, effect digest, plan staleness, capability binding | assemble the pack (at most three cards) | agent drafts | structure | H29 |
| 10 | Check a unit's risk setup | preflight: couplings, placeholders, blanks, feasibility, broker reality, FI cut, scaled brakes, equity basis | explain failures, draft fixes; challenger attacks assumptions | script first | none | H30 |
| 11 | Watch for decay | nightly verification, zones, fire density vs expected, alarm budget, graded demotion | WF3 triage where ambiguous; rehab children with lineage | script decides | cut, structure | H31 |
| 12 | Explain a size or a brake | derivation receipts, override chain, binding clamp | the ten-word answer | agent explains | none | H47 |
| 13 | Narrate incidents | incident bundle with attribution first | plain-word note, review checklist, optional tighter-limit card | both | cut | H08 |
| 14 | Morning risk brief | budgets, distances to trip, isolations, events per class | the thirty-second glance and at most three cards | both | none | H46 |
| 15 | Map events to non-FX instruments | deterministic windows from the map | build and maintain the map for indices, metals, energy, crypto, stocks; human check per new mapping | agent then script | cut | H48 |
| 16 | Find restores and accelerators | e-value restore gate, block-persistence test | argue for growth with the money missed | both | raise | H32, H33 |
| 17 | Propose breadth and placement | placement score, same-bet check, effective bets, pooled proof | nominate markets and sessions; propose families | both | raise | H34 |
| 18 | Rebalance BMS slots | shadow allocator ablation, bounded tilts, cost charge | propose moves monthly at most | both | raise or cut | H35 |
| 19 | Escalate the kill switch in an incident | the kill op itself (his hand) | pre-fill a one-tap escalation card | agent drafts | cut | H43 |
| 20 | Red-team the door | injection and fault replay harness | write attacks; read the contagion map | both | none | H11, H23 |
| 21 | Curate the ledger | checker, layer H | propose new variables and couplings from data | agent then script | none | H42 |
| 22 | Settle a paper window | verification plan priced in trades | copilot explains; he settles | both | structure | H29 |

**Rule that falls out of the map [judgment].** Where a job's output is a number that acts, a script computes it. Agents act only on judgment work: nominating, explaining, drafting, attacking. That is the July razor ("anything a deterministic script can do is not an agent", A4-144), kept, and run in reverse by H27: agent findings that repeat become scripts.

---

## 2. Hybrids

Seven groups: A the door (H01-H08), B counting and honesty (H09-H14), C noise and his attention (H15-H20), D the jobs (H21-H31), E performance (H32-H35), F plug-ins (H36-H39), G more jobs, class rosters and wild ideas (H40-H49).

### A. The door

#### X7-H01 The three-surface door: read, propose, run
- **Links:** A4-131, A2-017 (Steward invariant core), A4-112 (proposal, evaluation and approval apart; no broker credentials), A4-176 (order of authority), A5-054 (approval channel outside the agent's reach), A4-095 (app manifest operations), A4-146 (tool rows), host door (`door.py`, `host_route.py`), G2 rulings 5 and 6.
- **Need:** TLH 33 and 34 (how agents reach risk and sizing; tools; agents propose); M36 (Lab and MCP agents plug in without rework); the boundary in the department seeds.
- **What and how:** Agents reach the template through three surfaces and nothing else.
  - *Read:* risk state rows, the ledger, derivation receipts, journals, readings, baseline cones, passports, the search ledger, the card queue. Point-in-time and typed.
  - *Propose:* expiring evidence records that can only cut (H03), and effect-bound cards for everything else (H04).
  - *Run:* sandboxed jobs that touch no money: resize replay, the X4 scenario harness, QMB checks, the preflight (H30), contract tests. Every run is a trial row (H09).
  - The core (guard, sizer, brakes, exits, kill switch) stays code on the node with no write path from any surface. Steward's line "no LLM number reaches the broker unchecked" becomes: no agent output reaches the node except as a typed evidence record its unit declared, or a card he signed.
- **Levels:** core at trade, unit, account and node; surfaces at system.
- **Per class and style:** the mechanism is the same everywhere. Class shows up in read schemas: currency legs for FX, contract and roll for futures and energy, venue and funding for crypto, cash and futures sessions for indices, earnings and halts for stocks. Scalpers mostly use read and run; evidence rarely reaches them (H03).
- **Ledger:** *(new)* `operation_risk_direction`, `agent_autonomy_level`; `kill_switch_level`, `risk_fraction`.
- **Performance:** agents can search, draft and argue without limit because they cannot act; the run surface is where his "sky's the limit" lives **[judgment]**.
- **Survival:** no path from any agent principal to an order, a raise, an exit block or a kill-switch lowering.
- **Evidence chain:** Steward, author backtest (102 paper days, one configuration) → host door built and running → FARSIGHT, simulation (no academic LLM design had a halt that skips inference). **Weakest link:** Steward's single rising window; the boundary itself is a design property a contract test can prove.
- **Maturity:** solid.

#### X7-H02 Monotone action lattice on every tool and operation
- **Links:** A5-054 (I-HITL: 9 of 10 models raised their own spending cap when the gate was reachable), A4-095 (approval tiers), trading-node `kill` "never lowers", A2-018 (de-risk-only channel), A2-101 (exit preservation), A2-097 (kill by his hand), A4-176.
- **Need:** "news and LLM output can only lower risk, never raise" made structural; D43 "how do they know that the things are correct?"
- **What and how:** Every catalog row and app operation declares a direction: `read`, `propose`, `cut`, `raise`, `money`. The host's `admits` grows from "manage answers only to the operator" to "an agent or workflow principal may call read, propose and cut-through-evidence; raise and money answer only to the operator". CI fails when an operation has no direction. Reduce-only actions (close, cancel, tighter stop) stay unblockable by any brake, but agents still cannot send them, because only the node sends orders.
- **Levels:** system, node.
- **Per class and style:** same mechanism; class-specific operations (roll a contract, close before funding) carry a direction too.
- **Ledger:** *(new)* `operation_risk_direction`.
- **Performance:** neutral; makes it safe to widen agent tool sets quickly.
- **Survival:** closes stealth raises at the tool level. Layer H's effect check (H04) is the backstop for a mislabelled tool.
- **Evidence chain:** host door (built, runs) → I-HITL (controlled test) → Steward (author backtest). **Weakest link:** the direction is declared by the tool's author.
- **Maturity:** solid. **QMA flag:** catalog and host change.

#### X7-H03 Evidence as a fact the unit's own rule reads
- **Links:** A4-104, A1-132, A2-018, A3-145 (three bounded agents feeding one deterministic service), A5-070 (per-agent evidence contract with expiry and permitted use), A3-137, A3-087, A4-193 (the node's fast lane feeds facts), A2-114 (declared fail mode), G2 rulings 2 and 11.
- **Need:** a de-risk channel that keeps ruling 2's letter; A25 "size down, but not quickly"; C27 isolation "on evidence".
- **What and how:**
  - The unit's risk template gets an `accepts_evidence` section. Each entry names an evidence kind (news, macro, micro label, structure summary, isolation nomination), the largest cut it may cause, the floor, the time to live it will honour, and its fail mode.
  - Agent records reach the node as a feed, through a relay like the MIS board's. The unit's own rule multiplies size by the smallest valid scale, clamped to the floor and to 1.
  - Expired, malformed or missing evidence means 1.0: no change. This is a third fail mode beside the MIS board (fails open) and isolation (fails closed); the preflight (H30) shows all three together.
  - Every applied cut is journalled as a `risk_event` with the record id. The unit decides; the agent only testifies.
  - Roundtable change: a style check. A kind is acceptable only if its time to live exceeds the unit's typical hold by a margin, because LLM decisions took about 187 seconds in one crypto study (A3-087).
- **Levels:** unit (the rule), book and BMS (their own `accepts_evidence`), node (the feed).
- **Per class and style:** scalpers at 1 minute accept session-level kinds only (session caution, class isolation); intraday units accept micro labels; swing units accept macro vectors. FX records must name every pair holding the currency; crypto needs weekend watchers and authenticity checks; energy price-impact windows are very short; stocks take earnings and filing records by ticker.
- **Ledger:** *(new)* `agent_risk_scale`, `agent_evidence_kinds_accepted`, `agent_evidence_max_cut`, `agent_evidence_ttl`, `agent_evidence_style_scope`, `agent_evidence_fail_mode`; `context_size_modifier`, `decision_freshness_bound`, `risk_fraction`.
- **Performance:** a measured cut around bad conditions can save more than the trades it skips, but only where it beats a random cutter (H11).
- **Survival:** an agent can never raise risk; a dead agent changes nothing.
- **Evidence chain:** SwingGuard (author backtest; LLM called only after a rule trigger) → Fake News, Real Crashes (simulation) → the assistant's de-risk-only architecture (idea). **Weakest link:** no paper tests a de-risk-only agent channel end to end against no agent.
- **Maturity:** plausible. Needs the evidence relay (unbuilt) and his reading of ruling 2 (collision C1).

#### X7-H04 Effect-bound card
- **Links:** A5-055 (effect-bound approval: card rendered from a canonical effect, signed, executed from storage, re-checked at use), A4-021 (Terraform plan, refused if state changed), A4-041 (identity table), A4-030 (shadow rows), A5-054, A4-120 (human-signed packet of one immutable artifact), A5-154 (bound approval packet), A4-083 (layer H).
- **Need:** approval bound to the exact action (brief); D43.
- **What and how:**
  - Every slow proposal becomes a card built from a canonical effect descriptor: artifact hash, base version, unit and scope, the ledger ids it touches, the identity-table result (calibration row, new version, new unit), its direction, a shadow summary, and an expiry.
  - The ledger ids come from walking layer H's `affects` edges from the edited ids. A change that raises risk indirectly is labelled `raise`, whatever the agent called it.
  - The card is rendered from the descriptor. Agent text is shown as untrusted.
  - His approval signs the digest through the operator-only path. Execution uses the stored descriptor and re-checks that the base has not changed; otherwise the card is queued again. Approvals are single use.
- **Levels:** unit, book, BMS.
- **Per class and style:** the descriptor carries instruments and class fields (contract month, venue, both FX legs).
- **Ledger:** *(new)* `approval_ttl`, `card_expected_value`; `effective_tries`.
- **Performance:** good changes ship fast without trusting descriptions.
- **Survival:** what runs is what he saw.
- **Evidence chain:** Approve What, Exactly? and Loopjacking (controlled tests) → Terraform (production) → C-23 operator-only promote (built). **Weakest link:** a human approving without reading is not measured (A5-056).
- **Maturity:** solid.

#### X7-H05 Two-speed authority: cut fast and automatically, raise slowly and on evidence
- **Links:** A5-139 (speed by signal type), A5-138 (any brake blocks every raise), A1-064 and A2-221 (loosen only on an e-value plus a minimum time), A4-197 (only tightening automatic), A4-147 (restore steps proposed as readily as tighten steps), A5-133 (AIMD day pair), A5-134 (memory ceiling after a trip), A1-056 (restore ladder).
- **Need:** performance with intention (M33); A25; C19 "brakes first, accelerators second"; no sitting duck.
- **What and how:**
  - Money signals cut at once on the node. Edge estimates cut in steps through unit rules. Agent evidence cuts only through H03.
  - Raises run on a restore ladder he approves once per template, not per step. After a cut, size steps back when an e-value on post-cut trades passes 1/alpha and a minimum time has passed. It regrows fast to just below the trip level and slowly near it.
  - No raise while any brake is active or a cut is settling.
  - Agents cannot trigger a raise. They file restore cards only where he has not authorised the ladder.
- **Levels:** unit, book, BMS.
- **Per class and style:** scalpers gather restore evidence in days, ORB and swing units in weeks. Crypto weekend trades are not independent evidence. Futures and energy restores wait past roll and event windows.
- **Ledger:** *(new)* `restore_preauthorised`; `grow_back_rule`, `drift_size_down_step`, `sequential_evidence_pass`, `size_levels`.
- **Performance:** the main way size comes back after brakes.
- **Survival:** raises stay evidence-gated and blocked by any active brake.
- **Evidence chain:** R9's field ratios (TCP, Topstep, pods; live in their own fields) → e-value arithmetic (simulation) → no trading test of a pre-authorised restore. **Weakest link:** slow for thin edges: +0.10R takes a median of about 604 trades to pass (A1-064).
- **Maturity:** plausible. An automatic raise collides with ruling 2 (C1).

#### X7-H06 Spec, status and suggestions: three parts, three owners
- **Links:** A4-019 (spec and status with separate write rights), A4-001 and A4-002 (VPA learner and applier), A4-020 (status stamped with its version), A4-057 (offer improved defaults, never apply them silently), A4-017 (never-self-tune list).
- **Need:** the self-configuring model in the brief (typed document, learner, applier); agents propose without writing.
- **What and how:** The risk document has three parts.
  - *Spec* holds his choices, including the applier mode per number (off/shadow, at start, live) and the never-self-tune list. Only he writes it.
  - *Status* holds the runtime's values: the learner's targets and bounds, brake states, calibration rows. Only the runtime writes it.
  - *Suggestions* hold agent proposals, linked to cards. Only agents write it, and nothing on the node reads it.
  - A suggestion reaches spec only through a card.
- **Levels:** unit, book and BMS documents.
- **Per class and style:** same; never-self-tune defaults differ by class (leverage caps for CFDs, margin for futures).
- **Ledger:** `number_motion_mode`, `applies_to_open_positions`, `calibration_min_trades`.
- **Performance:** learned values move freely in status; agents add ideas without touching either part.
- **Survival:** no learner or agent can rewrite a limit he set.
- **Evidence chain:** Kubernetes API conventions and MT5 read-only inputs (production). **Weakest link:** precedence when he edits a number the learner also moves.
- **Maturity:** solid. Overlaps X1's template shape; named as collision C10.

#### X7-H07 Feasible-by-construction proposals
- **Links:** A4-133 (SwingGuard: risk state fed into the proposal step), A4-152 (a RiskState row every pass), A4-109 (deterministic critic projects proposals onto limits), A5-163 (propose, constrain, execute one step), A4-091 (guard `before_order`: pass, shrink, refuse).
- **Need:** fewer refused proposals, so less noise; the "read risk state" tool.
- **What and how:** Every agent proposal step receives the current risk state (budgets, distances to trip, active brakes, isolations) and the ledger bounds. A deterministic projector then clips each proposal onto the limits (a restore shrunk to the allowed step; a window inside an isolated class dropped) or refuses it with a reason code. The agent sees the projection; only projected proposals enter the queue.
- **Levels:** unit to BMS.
- **Per class and style:** bounds are per class (leverage caps, minimum-lot feasibility).
- **Ledger:** `brake_state`, `budget_remaining`, `kill_line_distance`, `open_risk_at_stop`.
- **Performance:** SwingGuard raised Sharpe from 2.79 to 2.98 and cut drawdown from 8.62 % to 6.44 % by feeding risk state into proposals.
- **Survival:** no proposal can ask for what the limits forbid.
- **Evidence chain:** SwingGuard (author backtest, six months, two coins) → OpenPM critic (author backtest, short window). **Weakest link:** SwingGuard's window.
- **Maturity:** plausible.

#### X7-H08 LLM-free fast loop with an incident tap
- **Links:** A4-134 and A2-016 (SwingGuard four-state loop), A2-001 (FARSIGHT kill path outside model inference), A5-049 (incident bundle protocol), A2-019 (read-only narrator), A5-151 (external breaker governor).
- **Need:** an LLM-free fast risk loop (brief); agents explain without sitting in the path.
- **What and how:**
  - The node's loop is deterministic: states with hysteresis, minimum holds and staged re-entry (NORMAL, ALERT, SURVIVAL, RECOVERY in SwingGuard; ACTIVE, REDUCING, HALTED, RESTORE in QMX words).
  - The kill and halt path never waits for a model. A contract test runs it with the model service down.
  - When a state changes or a threshold fires, the node writes an incident bundle with attribution first (slippage, fees, sizing, exposure, market move, stale mark, missing fill).
  - The narrator reads the bundle afterwards and writes a fixed-form note: facts with evidence ids, ranked causes, the next check. It may draft a tighter-limit card. It never clears anything.
- **Levels:** unit, account, node.
- **Per class and style:** per-class fast tells: venue halts, limit moves, funding times, the 17:00 New York rollover.
- **Ledger:** `brake_state`, `kill_switch_level`, `exit_reason_code`.
- **Performance:** in SwingGuard's ablation, removing the fast controller did the most damage (Sharpe 1.87, drawdown 14.19 %).
- **Survival:** core.
- **Evidence chain:** SwingGuard ablation (author backtest) → FARSIGHT (simulation) → ReguSim (controlled test: logistic regression F1 89.2 % beat the best LLM at 70.9 %, so LLMs should not be the detectors). **Weakest link:** no live trading test.
- **Maturity:** solid.

### B. Counting and honesty

#### X7-H09 One search ledger for alpha search and risk search
- **Links:** A4-110 (append-only search ledger), A2-202 (trial ledger with deflation), A4-041 (identity table counts tries), A4-016 (explore and exploit tuner), A4-199 (bandit arms), A3-033 and A4-172 (windows counted), A5-149 (search ledger to promotion gate), A2-179 (deflated Sharpe).
- **Need:** a search ledger counting every trial (brief); honest tuning.
- **What and how:** Every agent-run trial gets an immutable trial id: a risk-number candidate, a window slice, an isolation threshold, a scenario-tuned limit, an accelerator switch, a derivation swap. Each row holds parent, hypothesis, model id and cutoff, data and code hashes, cost model, result and decision. Families are per unit family and per parameter. A risk-profile version's promotion is deflated by its family's effective tries, as strategies are. The card shows the try count.
- **Levels:** unit, methodology, system.
- **Per class and style:** windows and costs are counted per class and session cell; crypto weekend cells count separately.
- **Ledger:** *(new)* `risk_profile_tries`; `effective_tries`, `deflated_sharpe_min`.
- **Performance:** lucky settings stop replacing good ones; good ones pass with fewer, pre-registered tries.
- **Survival:** search luck cannot raise size.
- **Evidence chain:** 2608.27734 (author backtest: with every trial counted, no LLM-found strategy passed) → identity table (built). **Weakest link:** no paper applies deflation to risk-parameter search; the transfer is **[judgment]**.
- **Maturity:** plausible.

#### X7-H10 Funded proposals: testing wealth per agent
- **Links:** A4-121 (Promote lifetime budget), A2-220 (family error budget, agent stakes), A4-149 (agents stake family wealth), A4-027 (Numerai: payouts on live rounds only), A5-085 (the credit-limit lesson).
- **Need:** one currency for false discoveries and for noise.
- **What and how:** Each agent profile draws testing wealth from a lifetime budget. Each card or trial spends some. A proposal accepted and later proved (its e-value crosses) refunds; a failure burns it. After the roundtable, wealth only ranks the queue; his attention (H15) stays the hard limit.
- **Levels:** system.
- **Per class and style:** wealth can be kept per class family.
- **Ledger:** *(new)* `agent_proposal_quota`; `effective_tries`.
- **Performance:** agents that waste his time go quiet.
- **Survival:** false discoveries bounded for the system's life.
- **Evidence chain:** Promote (simulation: unadjusted repeated tests promoted a false rule in 94.5 % of null paths, Promote 0.0 %). **Weakest link:** agent staking was never tested.
- **Maturity:** wild.

#### X7-H11 A matched random de-risker for every agent and class
- **Links:** A2-135 (random-control brake test at matched frequency, MQL5 23482), A4-137 (ablation: no agent, features only, agent, agent plus service), A5-050 (evaluate a monitoring agent as an alerting system), A4-139 (separate scorecards for rules followed and money made), R5's trap that any brake looks good on a losing strategy.
- **Need:** prove agents add value; keep noisy agents out.
- **What and how:** For every evidence kind and class, a shadow random de-risker fires as often, with the same cut sizes, on the same units. Monthly, the run surface compares net R and drawdown under the agent's cuts, the random cuts and no cuts. The channel stays open in that class only while the agent beats random by a margin over enough fires; otherwise it drops to advice only. Results go on the agent's report card.
- **Levels:** unit, class bucket, system.
- **Per class and style:** judged per class. Scalpers may never collect enough agent cuts to be judged, which is one more reason they accept few evidence kinds.
- **Ledger:** *(new)* `agent_vs_random_lift`, `agent_precision`; `brake_precision`.
- **Performance:** removes agents that cost trades without saving money.
- **Survival:** keeps the channel credible.
- **Evidence chain:** MQL5 23482 (author's random-control mechanism) → ReguSim (controlled test). **Weakest link:** needs many fires per class, so months.
- **Maturity:** solid as a test design.

#### X7-H12 A sealed, rotating scenario set beside agent-written scenarios
- **Links:** A5-089 (daily stress-engine backtest; factors agents cannot see), A3-157 (validate scenarios through the strategy), A4-118 (sealed test scored once), A3-153 (reverse stress testing), A3-147 (mandatory scenario set).
- **Need:** agents generating scenarios without gaming them.
- **What and how:** Agents write scenarios into an open set without limit. Limits and profile versions are judged on the standing set plus a sealed set agents never see, rotated monthly from historical replays and generated tails. Each night yesterday's real moves run as a scenario, giving the stress engine its own error log.
- **Levels:** unit to BMS.
- **Per class and style:** class shock lists: SNB unpeg, weekend gap, flash crash, futures limit move, crypto exchange outage, EIA shock, earnings gap.
- **Ledger:** *(new)* `hidden_scenario_share`.
- **Performance:** limits bind with less padding once the engine has a record.
- **Survival:** catches books gamed to pass the visible set. In Cai, Haugh and Li, a book showed scenario P&L within ±$3 while its true expected loss was about −$20.
- **Evidence chain:** that study (simulation). **Weakest link:** one study.
- **Maturity:** plausible.

#### X7-H13 Rationale-blind admission check, separate challenger
- **Links:** A5-051 (withholding the proposer's rationale: false acceptance 6.2 % without it, 14.8 % with it, 1.6 % with an explicit checking instruction), A4-119 (frozen referee), A2-197 and A4-136 (independent challenger), A5-032 (FIDES: description, code and behaviour must agree).
- **Need:** D43 "how do they know that the things are correct?"
- **What and how:** Any LLM check of a proposal sees the rule, the state and the effect descriptor with an explicit checking instruction, never the proposer's rationale. A separate challenger agent, on another model or context, reads the full claim and writes a challenge note on the card; it never decides. Admission is deterministic wherever it can be.
- **Levels:** system.
- **Per class and style:** none.
- **Ledger:** none new.
- **Performance:** fewer bad cards reach him.
- **Survival:** persuasive text cannot carry a rule breach through review.
- **Evidence chain:** ReguSim bridge audit (controlled test) → bank effective-challenge practice (live in its field). **Weakest link:** a challenger may share the builder's blind spots.
- **Maturity:** solid.

#### X7-H14 Point-in-time agent inputs and post-cutoff evaluation
- **Links:** A3-057, A4-180 (availability-time gating), A4-113 (pinned model snapshots, logged cutoffs), A3-139 and A4-107 (MFAST rules).
- **Need:** agent evidence that can be tested honestly.
- **What and how:** Every record carries event time and available time. Replays of an agent's value use only data after its model's training cutoff. Model snapshots are pinned and logged per trial. A model or prompt change makes a new agent version, which restarts at advice-only and re-qualifies through H11 (problem P12).
- **Levels:** system.
- **Per class and style:** FX releases need vintages per jurisdiction; crypto news has first-public and ingestion times that differ.
- **Ledger:** *(new)* `agent_requalify_rule`; `decision_freshness_bound`.
- **Performance:** real agent value stays measurable.
- **Survival:** no look-ahead or memorised edge reaches a card.
- **Evidence chain:** MFAST (author backtest, post-cutoff, Sharpe 2.85 after 5 bp) → OpenPM. **Weakest link:** vendor timestamps.
- **Maturity:** solid.

### C. Noise and his attention

#### X7-H15 His attention budget
- **Links:** A5-053 (review-queue burn rate), A5-056 (approval-queue telemetry, AllPath), A4-032 (burn-rate alerting), A4-157 (one alert at a time), A4-145 (`pp-proposal-pack`, at most three cards), A4-033 (freeze changes when a budget is spent).
- **Need:** agent noise and cards he ignores; his rule that long answers go unread.
- **What and how:**
  - One hard cap on cards per day. It starts at three (the shipped pack's number) and then follows his measured accept and ignore behaviour.
  - Cards are ranked by expected money per minute of reading. The run surface computes that money, never the agent (H20).
  - Overflow becomes one-line digest entries in the morning brief (H46), or expires.
  - A growing backlog throttles every agent.
  - Urgent cuts bypass the queue, because they act through unit rules anyway.
- **Levels:** system.
- **Per class and style:** none; urgency weights can favour 24/7 classes overnight.
- **Ledger:** *(new)* `operator_attention_budget`, `card_value_floor`, `card_expected_value`, `review_queue_burn`, `card_ttl_waking_hours`.
- **Performance:** the few cards he reads are the ones worth money.
- **Survival:** a trusted queue is not muted. Alarm fatigue in hospitals: 85-99 % of alarms needed no action, and staff turned them off.
- **Evidence chain:** AllPath (live): human-gated revisions took a median 8.8 hours and caught two judgment errors that code gates passed; in the autonomous period the gates rejected none and the operator later removed 11 of 19 agent-added rules. Then alarm-fatigue studies (live in medicine). **Weakest link:** no study sets a card count for a solo operator.
- **Maturity:** plausible.

#### X7-H16 Card-type learning and graduation into pre-authorised rules
- **Links:** A5-056 (later reversals), A4-057 (offer improved defaults, never apply silently), A4-084 (trust ladder), A5-077 (gate strength by size and reversibility).
- **Need:** D41 "agents do most of the heavy lifting ... I click"; fewer repeat clicks.
- **What and how:** For each card type the system tracks accept, reject, ignore and later reversal. A type he ignores repeatedly moves to the digest. A type he accepts `card_graduation_count` times with no reversal earns an offer: approve a deterministic rule once, with a time to live and a re-confirm at expiry. After that, those steps run without cards. Raise types need a stricter count.
- **Levels:** system, unit.
- **Per class and style:** none.
- **Ledger:** *(new)* `card_ignore_rate`, `approval_reversal_rate`, `card_graduation_count`, `preauthorised_rule_ttl`.
- **Performance:** removes repeat clicks at the source.
- **Survival:** rules expire and must be re-confirmed (roundtable: rules approved once and forgotten are a Knight Capital risk).
- **Evidence chain:** AllPath reversal data (live) → n8n default-reach behaviour (production) → graduation (idea). **Weakest link:** graduation itself is untested.
- **Maturity:** plausible.

#### X7-H17 One incident, one card
- **Links:** A4-160 (dedupe by root cause; incident owner and timeline), A2-026 and A3-146 (hours clause: losses from one event in a window count as one), A5-053 (write-once incident ledger), A5-160 (alert rationalisation).
- **Need:** noise from shared faults.
- **What and how:** Alerts and cards are grouped by a root-cause key (broker, feed, host, class, event id) inside a window. One incident gets one card listing every affected unit, with facts written once.
- **Levels:** system.
- **Per class and style:** event ids per class (a release, a venue outage, a roll).
- **Ledger:** `loss_event_window`.
- **Performance:** less of his time per incident.
- **Survival:** a shared broker fault shows as one incident, not twenty.
- **Evidence chain:** SRE practice (live in its field) → write-once ledger (controlled test, about 4.9 times fewer tokens than rereading logs). **Weakest link:** grouping can hide two problems under one key.
- **Maturity:** solid.

#### X7-H18 Autonomy ladder per agent profile
- **Links:** A5-078 (AllPath: a drawdown moves a self-revising agent back to human-confirmed changes until a human resets; live), A4-084 (trust ladder), A2-198 (verification passport), A5-077, A4-124 (agent profiles as mini-harnesses).
- **Need:** noise; agents earning more room on record.
- **What and how:**
  - Level 0: notes only.
  - Level 1: may draft cards.
  - Level 2: may file evidence in classes where H11 passed.
  - Level 3: may file kinds that units accept at a larger cut.
  - Promotion needs a precision and reversal record over a minimum count. Agent-caused signals demote (reversals, a failed random test, an injection incident).
  - After the roundtable, book or BMS drawdown beyond a set level only freezes new grants; it does not demote.
  - Only he resets a demotion. A model change resets to level 0 (H14).
- **Levels:** system.
- **Per class and style:** levels can differ per class.
- **Ledger:** *(new)* `agent_autonomy_level`, `agent_precision`, `agent_freeze_drawdown`, `agent_proposal_quota`.
- **Performance:** good agents get more room, which keeps the slow lane useful.
- **Survival:** a bad agent loses its voice.
- **Evidence chain:** AllPath breaker (live, one case) → bank model inventory practice. **Weakest link:** one live case.
- **Maturity:** plausible.

#### X7-H19 Get-even guard on every raise
- **Links:** A5-085 (Garvey, Murphy and Wu: 150 prop day traders traded more and bigger after morning losses; those with the bias lost $4,300-14,400 more a year), R9's credit-limit lesson, A2-092 (reverse house money).
- **Need:** stop agents and humans compounding a losing session through bigger bets.
- **What and how:** A raise card (restore, accelerator, window lift, slot move) proposed within a set window after a loss in its scope is flagged and placed behind other cards. An agent whose raise requests cluster after losses gets the slowest quota growth.
- **Levels:** unit, book, BMS.
- **Per class and style:** applies everywhere; the window is in that scope's trading time.
- **Ledger:** *(new)* `post_loss_raise_window`; `session_result_r`, `loss_streak`.
- **Performance:** removes a measured money-losing behaviour.
- **Survival:** no compounding of a bad day.
- **Evidence chain:** the prop-trader study (live, human traders). **Weakest link:** human behaviour carried over to agents **[judgment]**.
- **Maturity:** solid.

#### X7-H20 Every card shows money both ways
- **Links:** A5-073 (cost of conservatism), A4-202 (trip tax), A4-186 (resize replay), A2-160 (demotion cause), A4-153 (binding clamp named on every trade).
- **Need:** performance with intention; ranking the queue.
- **What and how:** Every card shows growth gained (resize replay on the unit's own trades), loss avoided, trip tax, cost of conservatism, evidence tier, try count, reversibility and what bound the size. The run surface computes all of it. Cards below a value floor never reach him.
- **Levels:** unit to BMS.
- **Per class and style:** money and R both shown; pips mislead across classes.
- **Ledger:** *(new)* `card_expected_value`, `card_value_floor`; `brake_precision`.
- **Performance:** puts the "sitting duck" cost on the same screen as the loss avoided.
- **Survival:** a cut's cost is visible, and so is a raise's risk.
- **Evidence chain:** EvolveTrade cash analysis (author backtest) → ICU alarm study (observational). **Weakest link:** loss avoided needs a counterfactual that can be gamed.
- **Maturity:** plausible.

### D. The jobs

#### X7-H21 Slow isolation: nominate, confirm, apply with a time to live
- **Links:** A3-113 (slow isolation card with evidence and a time to live), A3-203 (scenario: isolation by agent evidence over days), A3-109 and A2-123 (two tells must agree, calendar-aware baselines, precision recorded), A3-107 (isolation lifecycle: time to live, staged resume, retrip back-off, lockout), A2-128 and A3-102 (his protocol), A3-106 (scope keys), A3-115 (the MIS publishes isolation), A3-086 (his structure agents), A5-152 (bucket stress workflow).
- **Need:** C27 and C28: switch off a class, region or instrument "with the evidence", including agent "analysis ... over 20 days".
- **What and how (two stages, from the roundtable):**
  - *Stage 1, works on the shipped stack plus a card template.* The agent reads readings and journals over a nomination window (spreads by hour against baseline, fills against the card, every unit against its record). It files an isolation card with evidence fields, a scope and a time to live. He clicks; the BMS stands the scope's instruments down.
  - *Stage 2, after the node gains `class:` and `region:` scopes.* A nomination triggers a deterministic two-tell check on the same window. If it confirms and he has allowed confirmed isolation to apply, the BMS applies it with a time to live, staged resume and retrip back-off. Otherwise it stays a card.
  - Entries stop; exits never do. Every isolation records whether a loss followed in the class.
- **Levels:** BMS, book, node.
- **Per class and style:** FX by region (Tokyo, London, New York) and currency legs; crypto with weekend baselines; energy by event type; indices by exchange; stocks by sector; futures by exchange. Every style in the scope stops new entries.
- **Ledger:** *(new)* `isolation_nomination_window_days`, `isolation_confirm_mode`; `market_isolation_trigger`, `isolation_scope`, `isolation_end_rule`, `cross_market_stress_reading`, `brake_precision`.
- **Performance:** other classes keep trading; a slow bleed is stopped before a month passes.
- **Survival:** class shocks stay inside the class; an agent cannot isolate alone.
- **Evidence chain:** X4 scenario (idea) → alarm-fatigue studies (live in medicine) → turbulence and absorption-ratio research (no lead time reported). **Weakest link:** no isolation rule has been tested against a random control.
- **Maturity:** plausible.

#### X7-H22 Drift explainer with a bounded cause list
- **Links:** A2-174 (separate decay from spread, slippage, volatility and faults), A2-166 (input-first drift checks), A5-049 (incident bundle), A2-160 (economic failure versus relative degradation, cause recorded), A4-148 (nightly verification job with an agent pass after it), A5-072 (judge live results against the current regime's expectation), A2-133 (his rule: size down slowly, never pull out on one bad day).
- **Need:** A25 ("it can be a bad day ... throw the issues to an agent"); E28 (agents solve issues).
- **What and how:** A nightly script per unit splits the drift: costs against the card, slippage, trade rate, holding time, replay match, the regime-conditional expectation, and signal tests (CUSUM, e-detector, cone). The unit's rule decides the zone and the size step. The agent ranks hypotheses from a fixed list (cost drift, fill drift, regime mismatch, implementation fault, signal decay, unknown), with evidence ids and the next check. Only when the cause is cost or code does it file a fix card. It never files a size card.
- **Levels:** unit.
- **Per class and style:** rollover (FX), funding (crypto), swap, rolls (futures, energy) and earnings gaps (stocks) are split out from decay. Scalpers see input drift in tens of trades; ORB units need calendar time.
- **Ledger:** `drift_state`, `drift_size_down_step`, `cost_drift_multiple`, `trade_rate_band`, `replay_match_floor`, `mc_cone_floor_percentile`.
- **Performance:** fixes the right thing, so units are not cut for a broker change.
- **Survival:** a unit whose costs doubled is caught as broken today, whatever its P&L.
- **Evidence chain:** practitioner practice (Carver) → assistant's split of decay causes (idea) → incident bundle (idea). **Weakest link:** causes interact, so a single label can mislead.
- **Maturity:** solid.

#### X7-H23 Adversarial scenario author
- **Links:** A3-153 (reverse stress from failure outcomes), A5-090 (average the factor moves on the book's worst days), A3-230 (Tail-GAN generator), A5-063 (CrashGym-style lab), A3-176 (his scenario ask: losing together, isolation, correlation, news, switching), H12.
- **Need:** scenario generation; TLH 48.
- **What and how:** The agent searches for the cheapest plausible path to the floor, or to a brake failing, under the current template: losing together across classes, the day-boundary hole in count brakes, a weekend gap through stops, a news window that swallows the day. It writes each path as a scenario spec and runs it on the X4 harness through the run surface. A confirmed weak spot becomes a card with a fix, and the scenario joins the standing library. Limits are still judged on the sealed set (H12).
- **Levels:** unit to BMS.
- **Per class and style:** class shock grammars; style-specific traps (scalper count brakes, ORB session hand-over, swing weekend gaps).
- **Ledger:** *(new)* `hidden_scenario_share`; `portfolio_floor`, `kill_line_floor`.
- **Performance:** finds the one weak spot instead of shrinking everything.
- **Survival:** finds failures nobody wrote down.
- **Evidence chain:** reverse stress testing (simulation) → Tail-GAN (author backtest). **Weakest link:** few near-failure observations make searches noisy.
- **Maturity:** plausible.

#### X7-H24 Tuning proposer under the VPA applier
- **Links:** A4-001 and A4-002 (learner with bounds; applier with owner-chosen modes), A4-017 (never-self-tune list), A4-198 (plateau tuning, then lock), A4-199 (conservative bandit among pre-approved configurations), A4-126 (screening rules and a cost grid), A5-162 (conservative tuning workflow), A4-006 (guarded guess with fallback and freeze).
- **Need:** self-configuring with a learner and an applier (brief, R7); D29 and D46 (every number derives, and he can change how).
- **What and how:** The deterministic learner publishes a target and bounds into status. Agents may do three things, each by card with a trial id: explain the target; add arms to a number's approved set (offline plateau tuning, screened on a cost grid); propose a derivation swap. He sets the applier mode per number. A conservative bandit moves among approved arms inside a floor relative to the baseline. A guard falls back with a named reason and freezes after repeated trips. The never-self-tune list is out of reach.
- **Levels:** unit, book.
- **Per class and style:** arms pooled within a class where configurations compare; funding (crypto), swap and rollover (FX, CFDs), roll (futures) in the cost grid.
- **Ledger:** *(new)* `risk_profile_tries`; `number_motion_mode`, `calibration_min_trades`, `calibration_shrink_k`.
- **Performance:** a unit can move to a better configuration live without a new version per move.
- **Survival:** exploration cannot cost more than a set budget below the default.
- **Evidence chain:** Kubernetes VPA (production) → TPE-AS and AutoQuant (author backtests) → conservative bandits (theory, no trading test). **Weakest link:** bandit guarantees break when markets change.
- **Maturity:** plausible (the structure is solid).

#### X7-H25 Cost-window prospector
- **Links:** A1-147 and A3-084 (hourly cost profile; refuse when missing), A1-070 and A3-033 (a window is a measured slice of net edge, proven out of sample), A4-172 (agents propose windows, a script confirms, findings land in the Library), A3-035 (fix windows as caution windows), A5-157 (shared cost ledger), A1-166 (partial pooling per cell), A3-039 (hourly spread profile).
- **Need:** costs must reach the sizer (brief); D8 sniping windows; TLH 36 and 40.
- **What and how:** A script builds the hourly cost profile per instrument and venue from bars and fills (mean and p95). Agents nominate cells from cost and activity maps (cheap and active hours, fixes, session hand-overs, funding times, venue maintenance), never from the unit's own P&L by hour. A script estimates each cell with pooling across the class and confirms it out of sample. Every slice tried is counted. Confirmed windows land in the Library as artifacts with evidence and a retirement rule. A unit may read one as a caution window (cut, by its own rule) or a size or frequency lift (raise, by card).
- **Levels:** unit, methodology.
- **Per class and style:** FX: London and New York overlap, 21:00-22:00 GMT widest, 17:00 New York rollover; gold: London fixes; indices: cash open; crypto: venue-deep hours and funding; energy: settlement; stocks: open and close auctions. Scalpers gain the most because costs dominate.
- **Ledger:** `premium_window_flag`, `session_windows`, `spread_cost`, `unit_cost_target`, `effective_tries`.
- **Performance:** turns gross edge net by trading the cheap hours harder.
- **Survival:** costly hours avoided; clock folklore cannot lift size.
- **Evidence chain:** R2's trader practice (idea) → MQL5 cost articles (author builds). **Weakest link:** windows lower cost; they do not create edge, and a search over many slices inflates false windows.
- **Maturity:** plausible.

#### X7-H26 Structure labeller with a capacity veto
- **Links:** A3-087 (deterministic microstructure features; an agent only labels them), A4-106 (microstructure agent with a capacity veto), A4-105 (macro regime probability vector with invalidation and expiry), A3-086, A3-145, A3-142 (macro researcher plus verifier), A5-070.
- **Need:** D6 and TLH 41 (micro and macro structure as numbers from agents, also as isolation evidence).
- **What and how:** Code computes the features. An LLM labels them at a slow cadence (per session), and a macro agent publishes a regime vector that expires at the next release. Three outputs: evidence records that can only cut; per-session summaries in the Library for placement and copilot jobs; and a capacity veto line on promotion packs (a unit whose claimed cost cannot be filled at its intended size is held: a cut applied to a promotion).
- **Levels:** unit, BMS, Library.
- **Per class and style:** crypto streams trades, book, funding and liquidations per venue; FX broker books are venue-specific and must be labelled so; gold reads real rates and USD; energy reads EIA, OPEC and weather. Labels reach intraday and swing units, rarely scalpers.
- **Ledger:** `microstructure_multiplier`, `cross_market_stress_reading`, `decision_freshness_bound`.
- **Performance:** capacity vetoes stop promoting units that cannot fill at their claimed costs.
- **Survival:** labels expire before they can touch a fast loop.
- **Evidence chain:** LiveMacroEval (live forecast scoring, not trading P&L) → assistant's design (idea). **Weakest link:** no paired test of labels against features alone.
- **Maturity:** plausible.

#### X7-H27 Journal coroner whose findings graduate into detectors
- **Links:** A4-144 (July Coroner persona and the razor), A2-019 (read-only narrator), A5-053 (incident ledger), A4-127 (tool registry with promotion gates), A4-084 (trust ladder), A2-086 and A4-143 (WF3 pool cleaning).
- **Need:** journals read for what no script encodes; agents solve issues (E28).
- **What and how:** Weekly, the agent necropsies benched or demoted units and incidents. A pattern that recurs a set number of times is drafted as a detector block (a halt or a reading). It then climbs the block ladder: socket contract, shadow, precision record, his yes for live. After that the agent stops doing that job and only explains the detector's fires.
- **Levels:** unit, system.
- **Per class and style:** patterns tend to be class-specific (fills worse after releases on one broker; funding-time slippage on one venue).
- **Ledger:** *(new)* `card_graduation_count`; `brake_precision`.
- **Performance:** insight turns into cheap, testable code.
- **Survival:** detectors are tested before they act.
- **Evidence chain:** July razor (old QMX rule, design) → skill-promotion lifecycle (idea). **Weakest link:** recurrence counts on thin data.
- **Maturity:** plausible.

#### X7-H28 Template version drafter: propose, shadow, card, click
- **Links:** A4-147 (the loop and nightly rp workflows), X1 draft ideas 43-46, A4-097 (self-test card), A4-186 (resize replay), A4-041 (identity table), A4-021, A4-030 (shadow rows), A5-055.
- **Need:** D43 (a user makes new versions after he is gone); D41.
- **What and how:** The agent drafts a profile version (`risk_profile_new` in X1's list). The run surface builds the self-test card: slot contract tests, a resize replay on the unit's own trades, the scenario battery, the preflight (H30) and the placeholders left. The version shadows live trades as would-have rows, then becomes an H04 card. The node adopts it at the next flat.
- **Levels:** unit, book.
- **Per class and style:** the self-test includes a class with different lot granularity.
- **Ledger:** *(new)* `approval_ttl`; `effective_tries`.
- **Performance:** a better profile proves itself without risking a dollar.
- **Survival:** nothing new sizes live without a shadow record.
- **Evidence chain:** Argo Rollouts (production) → MQL5 17956 regression gates (author mechanism) → X1 design (idea). **Weakest link:** shadow sizing cannot see the impact a bigger live size would cause.
- **Maturity:** solid.

#### X7-H29 Promotion pack with a bound capability
- **Links:** A4-120 (human-signed packet of one immutable artifact), A5-154, A5-057 (class-aware pre-queue checks and data-licence clearance), A4-165 (verification passport), A5-035 (statistical authorisation kept apart from portfolio vetoes), G9 3.2 (C-23 promote).
- **Need:** D41 and D19 (agents bring units, he promotes); D28 (paper window settled with the copilot).
- **What and how:** `pp-proposal-pack` (at most three cards) becomes a set of H04 packets. Class-aware checks run before he sees anything: reproducible inputs, no window reuse, realistic costs, capacity at the intended size, minimum-lot feasibility, licence. Risk vetoes are listed apart from the evidence verdict. The node then holds a narrow capability to run only that version with that profile; drift, staleness or a material change revokes it. The paper window per unit comes from the verification plan priced in trades; the copilot explains it; he settles it.
- **Levels:** unit, deployment.
- **Per class and style:** FX value dates and rollover; index vehicle; metal and energy roll; crypto venue and funding; futures margin; stock borrow and halts.
- **Ledger:** `paper_min_trades`, `paper_min_days`, `paper_to_live_carry_rule`.
- **Performance:** fast promotions that stay exact.
- **Survival:** what runs is what he approved.
- **Evidence chain:** AllPath (operational case) → C-23 (built). **Weakest link:** flooding and rubber-stamping not measured on humans.
- **Maturity:** solid.

#### X7-H30 Risk preflight linter plus challenger
- **Links:** A4-083 (checker layers A-G and the proposed layer H), A4-085 (placeholder labels and rip-out list), A4-101 (a blank value blocks live), A1-157 (minimum-size feasibility per class), A1-151 (broker reality check), A2-270 (FI cut sizes in every number), A2-078 (count brakes scaled to trade count), A2-115 (declared equity basis per money brake), A4-136 (challenger).
- **Need:** "checking a unit's risk setup" (starter question); D30 (no key setting blank).
- **What and how:** A deterministic preflight runs on every draft and nightly on running units. It checks that couplings are honoured, no placeholder is unflagged, no key is blank, the minimum size is feasible at current equity, the broker allows the trade mode, an FI cut size is declared, count brakes are scaled to trade count or set in money, every money brake declares its equity basis, cost keys exist, and each input feed's fail mode is declared (MIS open, isolation closed, agent evidence neutral). The agent explains failures in plain words and drafts fixes. The challenger attacks the claim card's risk assumptions. The certificate expires when the venue changes lot step, swap or margin.
- **Levels:** unit, book, account.
- **Per class and style:** feasibility rules per class (at $500, micro futures, metals and energy are often "possible to place" but not "small enough to risk", A1-157).
- **Ledger:** *(new)* `agent_evidence_fail_mode`; `min_lot`, `lot_step`, `fast_invalidation_cut_r`, `brake_equity_basis`, `loss_counting_rule`.
- **Performance:** units reach paper with fewer silent faults.
- **Survival:** nothing trades on a placeholder or a blank.
- **Evidence chain:** checker layers A-G (built, run) → Gen 3 blank rule (docs) → layer H (idea). **Weakest link:** layer H depends on the ledger's couplings being complete.
- **Maturity:** solid.

#### X7-H31 Decay watch: the script decides, the agent triages the branch
- **Links:** A4-148, A4-143 and A2-086 (WF3: breaker fire density as decay evidence), A2-088 (expected fire rate), A2-167 (stacked alert levels and a demotion ladder), A5-150 (graded live demotion), A2-229 (rehab as a counted try), A4-161 (alarm budget across units), A2-160.
- **Need:** A26 (the old circuit breaker caught alpha decay; improve it); his WF3.
- **What and how:** The nightly job computes zones, breaker fire density against the expected rate, and e-detectors under an alarm budget across all units. Size steps are deterministic unit rules. Confirmed failure suspends a unit, a dollar loss rule backstops both, and each demotion records its cause. The agent proposes the WF3 branch only where the deterministic branch is ambiguous (keep, reduce, demote, retire, rehab), and drafts rehab children with lineage, each a counted try.
- **Levels:** unit, methodology.
- **Per class and style:** observation unit is a completed campaign, not a fill; crypto has no weekday close; futures need per-contract P&L.
- **Ledger:** `breaker_fire_density`, `breaker_expected_fire_rate`, `drift_state`, `sequential_evidence_pass`, `effective_tries`.
- **Performance:** "reduce" keeps a decaying unit alive and measured.
- **Survival:** decay is seen days before a CUSUM on R can see it.
- **Evidence chain:** WF3 (old rule, never given numbers) → multi-stream e-detectors (simulation). **Weakest link:** WF3's thresholds were never written.
- **Maturity:** solid.

### E. Performance

#### X7-H32 The sitting-duck advocate
- **Links:** A5-073 (cost of conservatism), A4-202 (trip tax), A2-030 (brake precision), A1-064, A4-147 (restore steps as readily as tighten steps), A5-138.
- **Need:** M33 "I don't want just safety"; the $300 "sitting duck".
- **What and how:** One agent's only job is growth. It reads under-baseline share, trip tax and brake precision. It files restore, accelerator and brake-retirement cards carrying the money units missed while braked. It shares the attention budget, is subject to the get-even guard (H19), and its scorecard is growth regained without later reversals.
- **Levels:** unit, book, BMS.
- **Per class and style:** reads class-specific trip taxes (news windows swallow FX days; weekend rules idle crypto).
- **Ledger:** `brake_precision`, `grow_back_rule`.
- **Performance:** growth gets a voice in his queue equal to safety.
- **Survival:** its raises still pass every gate.
- **Evidence chain:** EvolveTrade (author backtest: losing windows held 27.1 % cash against 17.1 %, and 40.1 % against 4.3 %, and missed recoveries). **Weakest link:** the counterfactual ignores that a braked unit might have hit the floor.
- **Maturity:** plausible.

#### X7-H33 Accelerator scout: persistence first
- **Links:** A5-131 (block-persistence test), A5-121 (press-and-ease pair, switched on only after persistence is shown), A5-119 (pressing after wins), A3-195 (scenario: winning together), A5-138, A5-148 (venue capacity ceiling).
- **Need:** A21 (keep accelerators); R9's finding that regime persistence pays where independence does not.
- **What and how:** The agent runs block-persistence tests per unit and class on the run surface, each counted. Where persistence shows, it proposes switching on a press-and-ease pair in the unit (a deterministic accelerator), capped by venue capacity, never while a brake is active.
- **Levels:** unit, book.
- **Per class and style:** trend units and session-open units first; mean-reverting scalpers rarely show block persistence.
- **Ledger:** `size_levels`, `house_money_winnings_share`.
- **Performance:** size rises where results cluster, which R9 says is the only place an accelerator beats fixed size.
- **Survival:** the "winning together" scenario checks that accelerators do not fire five times on one move.
- **Evidence chain:** R9 (simulation and field analogues). **Weakest link:** persistence measured in sample.
- **Maturity:** plausible.

#### X7-H34 Breadth and placement proposer
- **Links:** A1-133 (placement ranking score n x EV^2 / s^2), A1-082 (breadth across sessions), A3-032 (one ORB logic on every open), A2-188 (pooled proof across a family, discounted for correlation), A4-149 (agents propose families), A3-163 (effective independent bets), A1-115 (same bet counted once).
- **Need:** D2 placement; D11 ORB breadth ("brilliant"); C1 "risk less, but do it so many times".
- **What and how:** Agents propose new markets or sessions for a unit with cell estimates. A deterministic placement score ranks them. A same-bet check and effective bets stop one bet being stacked. Proof is pooled by family, discounted for correlation. On the risk side, the BMS document's cluster caps update.
- **Levels:** unit, book, BMS.
- **Per class and style:** ORB breadth across FX, index and metal opens; crypto has activity sessions instead of clock sessions; pooled proof must not cross a shared driver such as one US release.
- **Ledger:** `effective_independent_bets`, `cluster_exposure_cap`, `ranking_score`, `effective_tries`.
- **Performance:** more good bets is the biggest lever an agent can pull **[judgment]**.
- **Survival:** effective bets stop breadth becoming one bet.
- **Evidence chain:** fundamental law (theory) → pooled proof (idea). **Weakest link:** correlation estimates on short records.
- **Maturity:** plausible.

#### X7-H35 BMS slot rebalancer with an anti-chasing governor
- **Links:** A4-174 and A1-090 (BMS self-optimises slots through agent proposals), A1-102 (slow, capped, cost-charged reweighting), A1-103 (performance-chasing warning), A5-020 (bounded tilts on a hierarchical risk-parity base), A5-024 (shadow allocator ablation), A1-110 (slots).
- **Need:** C26 "reduce the number of scalpers ... open up more slots ... if the capital allows".
- **What and how:** At most monthly, an agent proposes slot or capital moves between styles. A shadow allocator replays the same units under rival rules. Moves are bounded tilts on a risk-parity base, charged for turnover. He clicks.
- **Levels:** BMS.
- **Per class and style:** style sleeves (scalper, intraday, swing) and class sleeves.
- **Ledger:** `slot_rebalance_rule`, `style_capital_split`, `concurrent_unit_slots`.
- **Performance:** capital follows units that earn it, slowly.
- **Survival:** no daily rotation to recent winners (the adaptive-allocation trap).
- **Evidence chain:** RL-BHRP (author backtest; drawdown was worse, so only a bounded overlay) → shadow allocator (idea). **Weakest link:** RL-BHRP's own drawdown.
- **Maturity:** plausible.

### F. Plug-ins

#### X7-H36 The risk mini app with an MCP server: one implementation, two names
- **Links:** A4-094 (Risk Lab app around the template), A4-095 (app manifest: risk class, declared operations and approvals, typed contracts), A4-146 (tool rows), X1 idea 43 (tool list), host door, A5-054.
- **Need:** M36 (Lab and MCP agents without rework); D43 (how agents talk to it); the department seeds.
- **What and how:** The door ships as a `risk = "runs"` mini app. Its MCP server declares:
  - read: `risk_state`, `ledger_query`, `risk_explain`, `search_ledger_query`, `card_queue_read`;
  - run: `resize_replay`, `scenarios_run`, `preflight`, `random_control_run`, `window_cell_estimate`;
  - propose: `evidence_file` (cut), `card_draft`, `suggestion_write`.
  Each operation has a direction (H02), an approval tier and schemas. There is no `manage` operation. Catalog rows are thin aliases, so chat agents, the copilot, workflows, outside MCP clients and the department's shepherds all reach one implementation. The node reads only the evidence feed through the relay, and executes only signed cards through the existing operator-only operations.
- **Levels:** system.
- **Per class and style:** none in the mechanism.
- **Ledger:** *(new)* `operation_risk_direction`.
- **Performance:** one surface for every agent that comes later.
- **Survival:** the app cannot hold trading keys (only `trading-node` may).
- **Evidence chain:** the MIS app proves an app can run QML blocks by entry id (built) → manifest validation (built). **Weakest link:** an app cannot yet land component entries or cards in the Library, or reach the node beyond the board relay (G8 6.4).
- **Maturity:** solid as a shape. **QMA flag:** a lander for cards and evidence; the evidence relay.

#### X7-H37 The Lab as a tenant of the run surface
- **Links:** A4-096 (Lab pod spine: seven slots compiling to Book and BMS fragments), A4-094, A5-161 (interactive simulation bench), A5-024 (shadow allocator), A4-182 (profiles bred inside ranges).
- **Need:** M36: the Lab uses the template without rework and never sits in the order path.
- **What and how:** Lab pods run candidates through the same run surface (resize replays, the scenario harness, the simulation bench). Their outputs are draft Book, BMS or profile versions that enter the same H04 cards. Their trials go into the same search ledger (H09).
- **Levels:** book, BMS.
- **Per class and style:** venue modules per class in the bench.
- **Ledger:** `effective_tries`.
- **Performance:** variants compared cheaply, side by side.
- **Survival:** the Lab never sizes a live trade.
- **Evidence chain:** Lab design (architecture document, unbuilt) → simulation bench (idea). **Weakest link:** the Lab is unbuilt.
- **Maturity:** plausible.

#### X7-H38 Shepherd-ready call contract
- **Links:** A4-128 (Shepherd: fork, inspect, replay, select, apply or discard), A4-124 (profiles as mini-harnesses with forbidden context), A4-129 (loop budgets and stop rules), A4-127 (memory, skills and tools registries), A5-076 (information, action and commitment boundaries).
- **Need:** the department's "Shepherd protocol" plugs in later without the door changing.
- **What and how:** Every door call carries a run id, an agent profile id, a model id with its cutoff, and a budget. Proposals are retained, not applied, so a shepherd can fork, replay with one condition changed, and select. Loop budgets stop runaway agents. Each profile lists the context it must not receive (a validator does not see the builder's incentives).
- **Levels:** system.
- **Per class and style:** shepherds may be clustered by style or class, as he pictured.
- **Ledger:** *(new)* `agent_inference_cost`.
- **Performance:** a one-condition replay shows what actually improved a unit.
- **Survival:** nothing an agent makes lands without selection.
- **Evidence chain:** Shepherd (early-alpha open source) → QuantHarness (controlled test of boundaries). **Weakest link:** Shepherd's maturity.
- **Maturity:** plausible. **QMA flag.**

#### X7-H39 Evidence contracts per kind
- **Links:** A5-070 (per-agent evidence contract with expiry, permitted use and corroboration), A4-104, A3-137 (news record), A4-107 (event time apart from availability time), A3-138 and A4-108 (provenance, corroboration, cap on one item, one feed counted once), A4-105, A3-087.
- **Need:** the shapes the future department's agents must emit; "news and LLM output can only lower risk".
- **What and how:** Typed schemas per kind:
  - news: lives minutes to hours;
  - macro: lives to the next release;
  - micro label: lives one session;
  - structure summary: lives days;
  - isolation nomination: lives days to weeks;
  - journal finding: lives weeks.
  Each declares permitted use, largest effect, time to live, how much corroboration widens it, provenance, a single-item cap, and source independence (one model family or one feed counts once). Credibility cues ("BREAKING", a named source) are stripped before a model reads an item.
- **Levels:** system (schemas), unit and BMS (use).
- **Per class and style:** FX pair-relative surprises; futures contract month; crypto venue and product; stocks ticker and filing accession; energy event type.
- **Ledger:** *(new)* `agent_evidence_ttl`, `single_item_effect_cap`, `corroboration_widening_step`, `evidence_source_independence`.
- **Performance:** analysis keeps its value as context without becoming a command.
- **Survival:** removing credibility cues dropped fake-news success from 62 % to 0 % in the sandbox; a capped item can only cut a little.
- **Evidence chain:** MarketSenseAI 2.0 (author backtest) → Fake News, Real Crashes (simulation). **Weakest link:** a simulated sandbox with one reference design.
- **Maturity:** solid.

### G. More jobs, class rosters and wild ideas

#### X7-H40 Agent prediction market on risk events
- **Links:** A4-105 (scored on calibration, not P&L), A4-140 (FinAbstain: disagreement raises uncertainty), A4-149 (staking).
- **Need:** a cheap, honest score for agent judgement.
- **What and how:** Agents post probabilities on risk events ("unit X demoted within 30 days", "class Y isolated this week"). A deterministic aggregator scores them by Brier and reliability. Scores set quota and autonomy. Disagreement between agents lowers what their evidence may cut.
- **Levels:** system.
- **Per class and style:** events per class.
- **Ledger:** `agent_precision` *(new)*.
- **Performance:** finds which agents see trouble early.
- **Survival:** no money touch.
- **Evidence chain:** weather-forecast scoring practice → FinAbstain (simulation). **Weakest link:** few events to score.
- **Maturity:** wild.

#### X7-H41 Ghost tracks for accepted and rejected cards
- **Links:** A4-030 (shadow rows), A2-178 (paper twin and random twin), A5-056 (later reversals).
- **Need:** labels for agent learning; a measured value for his own decisions.
- **What and how:** Every card, accepted or rejected, runs on as a would-have track for a set period. The system learns which rejected cards would have paid, and which accepted ones he later reversed for good reason.
- **Levels:** unit, BMS.
- **Per class and style:** none.
- **Ledger:** `approval_reversal_rate` *(new)*.
- **Performance:** agents learn from outcomes, not from his clicks alone.
- **Survival:** none added.
- **Evidence chain:** idea. **Weakest link:** shadow results ignore market impact and change his incentives if shown.
- **Maturity:** wild.

#### X7-H42 A ledger that proposes its own couplings
- **Links:** A4-098 (the ledger as schema source of truth), A4-099 (a default needs a derivation), A4-083 (layer H).
- **Need:** M14 (the ledger expands); D50.
- **What and how:** Agents mine journals for numbers that move together and propose new variables or `affects` edges. Layer H and `check.py` validate the proposal; a card asks him to accept it.
- **Levels:** system.
- **Per class and style:** couplings may differ by class.
- **Ledger:** none new.
- **Performance:** coupling gaps close faster.
- **Survival:** layer H gets more complete over time.
- **Evidence chain:** idea. **Weakest link:** correlation found in data is not a coupling.
- **Maturity:** wild.

#### X7-H43 One-tap kill escalation card
- **Links:** A2-097 (kill by his hand, four scopes), trading-node `kill` (escalates, never lowers), A5-049 (incident bundle), A5-055, G9 4.4 (no class scope).
- **Need:** C21 kill switch kept; fast response during an incident while the kill stays his.
- **What and how:** During an incident the narrator pre-fills a kill escalation (for example YELLOW on one account or instrument scope) as an H04 card, rendered from the incident bundle. He presses once. No agent ever lowers a level. Class and region scopes need the node change in H21.
- **Levels:** node.
- **Per class and style:** class scope wanted for crypto weekends and region scope for news.
- **Ledger:** `kill_switch_level`, `kill_switch_scope`.
- **Performance:** none.
- **Survival:** minutes saved in an incident.
- **Evidence chain:** kill switch (built) → effect-bound approval (controlled test). **Weakest link:** an escalation card at 03:00 his time waits for him.
- **Maturity:** plausible.

#### X7-H44 Governed self-evolution of risk agents
- **Links:** A5-071 (EvolveTrade: update an agent's procedure every five days, never its limits), A4-132 (Steward reflector with a deterministic gate), A4-115 (protocol patches for the next cycle only).
- **Need:** agents that improve (department seeds) without touching the core.
- **What and how:** A reflector proposes changes to the risk agents' own procedures on batched feedback (weekly, not daily). A protected-field list (limits, permissions, brakes, sizing) is out of reach. Any edit that changes what an agent may cut becomes a new agent version (H14, H18). Every version is kept for rollback.
- **Levels:** system.
- **Per class and style:** each class may need its own update clock.
- **Ledger:** *(new)* `agent_requalify_rule`.
- **Performance:** agents improve without anyone hand-editing them.
- **Survival:** risk limits are out of the loop's reach.
- **Evidence chain:** EvolveTrade (author backtest; daily updates did worst) → Steward (two quarterly cycles). **Weakest link:** two cycles are too few.
- **Maturity:** wild. **QMA flag.**

#### X7-H45 Per-class agent roster
- **Links:** A5-057 (class mechanics checklist), A5-094 (energy overlay), A3-143 (energy event windows), A3-144 (earnings, filings, halts), A3-235 (crypto liquidation-cascade warning), A4-107 (non-FX classes need event mapping).
- **Need:** the multi-instrument lens (M26) on the agent layer.
- **What and how:** Evidence agents are rostered by class, each with its own contract and clock: an FX currency-leg news mapper and rollover and swap watcher; an index session and gap watcher with earnings season; a metals fix and real-rates reader; an energy calendar and roll keeper (EIA, OPEC, expiry); a crypto weekend, venue-outage, funding and stablecoin watcher; a futures margin and limit-move reader; a stocks filings, earnings and halts mapper.
- **Levels:** class bucket, BMS.
- **Per class and style:** this hybrid is the class lens.
- **Ledger:** `instrument_class`, `news_impact_level_map`.
- **Performance:** classes beyond FX get covered, so breadth can grow safely.
- **Survival:** halts make exits impossible for stocks and futures, so no agent may promise an exit there.
- **Evidence chain:** R4's class table (assistant) → MQL5 24250 (calendars keyed on currency do not reach other classes). **Weakest link:** energy and single stocks are thin in the research.
- **Maturity:** plausible.

#### X7-H46 Morning risk brief
- **Links:** A4-163 (thirty-second glance), A4-145 (morning slow lane), A4-152 (risk state rows), H15.
- **Need:** his attention; D49 (the UI shows what is wrong, right, up, on, trading).
- **What and how:** Before the first session, a script computes budgets, distances to trip, active isolations and evidence, and today's events per class. The agent writes the glance (healthy, overnight result, what needs him), the digest lines, and at most the day's cards.
- **Levels:** system.
- **Per class and style:** events per class.
- **Ledger:** `budget_remaining`, `kill_line_distance`, `brake_state`.
- **Performance:** decisions batched once a day.
- **Survival:** nothing hidden overnight.
- **Evidence chain:** unit plan's morning slow lane (built in part). **Weakest link:** 24-hour trading has no single morning.
- **Maturity:** solid.

#### X7-H47 Provenance walker: explain any size in ten words
- **Links:** A4-049 (inspector that says where each value came from), A4-054 (derivation receipts), A4-153 (binding clamp), A4-135 (read-only explainer), X1 idea 47.
- **Need:** D33 ("dumb it down for me"); A13 (every move states its reason).
- **What and how:** From a decision row, the copilot walks the receipts, the override chain and the binding clamp, and says in ten words why a unit is at this size, with the long form one click away. The text is never an input to anything.
- **Levels:** trade, unit.
- **Per class and style:** money and R shown together.
- **Ledger:** `risk_fraction`, `control_rank_table`.
- **Performance:** finds which clamp holds size down: the place to look for growth.
- **Survival:** none added.
- **Evidence chain:** April's per-trade audit naming the binding clamp (old rule, lost code). **Weakest link:** receipts are not written yet.
- **Maturity:** solid.

#### X7-H48 Event-to-instrument mapper for non-FX classes
- **Links:** A4-107, A3-131 (event-to-instrument driver tags), A3-143, A3-144, A3-129 (calendar ingest that fails closed when stale).
- **Need:** C28 (on news days, find which instruments are affected, then isolate).
- **What and how:** Agents build and maintain the map from events to instruments for indices, metals, energy, crypto and stocks (the currency-keyed map covers only FX). Each new mapping needs his or a deterministic check once. The node then runs windows from the map deterministically.
- **Levels:** node, BMS.
- **Per class and style:** this hybrid is class work.
- **Ledger:** `news_impact_level_map`, `news_blackout_before`, `news_blackout_after`.
- **Performance:** non-FX classes can trade outside their windows instead of being excluded.
- **Survival:** windows block entries, never exits.
- **Evidence chain:** MQL5 24250 (author build) → G9 (news parked). **Weakest link:** news is parked in the build.
- **Maturity:** plausible.

#### X7-H49 Readiness for agent-trader units (Steward intent)
- **Links:** A4-131 and A1-131 (agent intent only; code sizes at the smaller of the agent's weight and fixed risk at the stop), A2-253 (a falsifying condition on every trade), D44 (parked by him).
- **Need:** M35 (agents as traders later), without rework of the template.
- **What and how:** The template defines a unit type whose entries are agent intents (symbol, direction, conviction, a falsifying condition) while sizing, exits and brakes stay the template's. The falsifying condition becomes a thesis-based fast-invalidation exit. Nothing is built now; the type is reserved so the template does not need rework.
- **Levels:** unit.
- **Per class and style:** swing first (LLM latency); never scalping.
- **Ledger:** `fast_invalidation_trigger`, `risk_fraction`.
- **Performance:** opens a whole class of units.
- **Survival:** Steward contained a 24.6 % sector drawdown to a 0.3 % loss.
- **Evidence chain:** Steward (author backtest, one window). **Weakest link:** puts an LLM in the entry path, against G2-5 (collision C8).
- **Maturity:** wild.

---

## 3. R4's 15 workflows: which belong to risk and sizing

Source: `research/R4-alphaxiv/R4-alphaxiv-synthesis.md:816-834`, carried in Stage A as A5-149 to A5-163. "Risk core" means it runs in or beside the node with no agent in its path. "Door" means it is part of how agents reach the template.

| # | Workflow | Belongs to | Agent role | Hybrids |
|---|---|---|---|---|
| 1 | Search ledger to promotion gate | shared: X5 for units, **risk and sizing for profile versions** | agents log every trial | H09, H29 |
| 2 | Graded live demotion | **risk core** (X3, X5) | explain and triage only | H31, H22 |
| 3 | External breaker governor | **risk core** (X3); agent-free by definition | none in the loop; narrator after | H08 |
| 4 | Bucket stress isolation | **risk core** (X3); agent evidence feeds its slow form | nominate | H21 |
| 5 | Read-only LLM risk narrator | **door** (X7, X6) | the narrator | H08, H46 |
| 6 | Bound approval packet | **door** (X7) | drafts the packet | H04, H29 |
| 7 | Governed research pipeline | agent department and X5 (alpha); risk only through costs and sizing contracts | the whole pipeline | H38 |
| 8 | Staged ramp ladder | **sizing** (X2) | proposes steps where not pre-authorised | H05 |
| 9 | Shared cost ledger | **sizing input** (X2, X6) | nominates cost windows | H25 |
| 10 | Meta-label exit and size gate | sizing (X2, X3); the classifier is trained in the Lab | trains offline, never live | H37 |
| 11 | Event calendar control | **risk core** (X3) | maps events for non-FX classes | H48 |
| 12 | Alert rationalisation | X6, and it governs agent noise | none; it rations agents | H15, H17 |
| 13 | Interactive simulation bench | X4 harness | runs it through the run surface | H23, H37 |
| 14 | Conservative parameter tuning | **self-configuring sizing** (X1, X2) | adds candidate arms | H24 |
| 15 | Propose, constrain, execute one step | **sizing door**: the guard's projection (`before_order` shrink) | none; units propose, the guard projects | H07 |

So eight belong to risk and sizing proper (2, 3, 4, 8, 9, 11, 14, 15), two are the agents' door (5, 6), one is shared (1), and four live elsewhere but touch it (7, 10, 12, 13).

---

## 4. The tools agents need

Direction per H02. "Built" means a row or job exists at the stack tip (G8 4.1, G9 7.2). Every run-surface call is a trial row (H09).

| Surface | Tool | Direction | Status | Notes |
|---|---|---|---|---|
| read | `risk_state(scope)`: equity series, drawdown, open risk, exposure, budget used, each brake's distance to trip, trading state, kill level | read | new | the RiskState row (A4-152); fed into every proposal (H07) |
| read | `ledger_query(id)`, `risk_explain(unit, number)` | read | new | X1's list; walks receipts and the override chain |
| read | `journal_query`, `readings_query`, `instrument_get` | read | built | |
| read | node `status`, `units`, `positions`, `journal_tail`, `passport` | read | built | trading-node app, callable by agents |
| read | baseline card and cone read | read | new | scripts cannot read Library items today (G9 7.3) |
| read | `search_ledger_query`, `card_queue_read`, `incident_bundle_read`, `evidence_active(unit)` | read | new | |
| run | `resize_replay(trades, profile)` | run | new | X1 idea 45; the core sizing test |
| run | `scenarios_run(profile, set)` | run | new | the X4 harness; the sealed set is not visible to agents |
| run | `preflight(profile)` incl. layer H | run | partly built | `unit_check` runs layers A-F |
| run | `backtest_run`, judge, robustness, walk-forward, Monte Carlo | run | built | QMB app jobs: "the QMB checks" |
| run | `blocks_contract(entry)` | run | new | the socket contract on a Library block |
| run | `random_control_run(kind, class)`, `ablation_run(agent)` | run | new | H11 |
| run | `cost_profile_build`, `window_cell_estimate`, `block_persistence_test` | run | new | H25, H33 |
| propose | `evidence_file(record)` | cut | new | only kinds a unit declares; time to live, scope, provenance |
| propose | `card_draft(effect)` | propose | partly built | the shared proposal-card block, rebuilt as H04 |
| propose | `suggestion_write`, `risk_profile_new`, `blocks_save` (draft), `scenario_save` (open set), `trial_register` | propose | new | drafts only |
| never | `promote`, `deploy`, `withdraw`, `resume`, `pause`, `kill`, `flatten`, `bind`, publish, sign | raise or money | built, operator only | the host answers these only to him |

---

## 5. How agent noise is kept away from him

In one list, pointing at the hybrids:
1. **One hard budget:** cards per day (H15). Everything else is ranking.
2. **Ranked by money both ways,** computed by the run surface, not the agent (H20).
3. **Feasible before queued:** proposals projected onto limits first (H07).
4. **Checked before queued:** class-aware pre-queue checks (H29), preflight (H30), rationale-blind check (H13).
5. **One incident, one card** (H17).
6. **Agents earn room:** autonomy ladder (H18), quota or testing wealth as ranking weight (H10).
7. **Agents must beat random** to keep a cut channel in a class (H11).
8. **Repeat cards graduate** into rules he approves once; ignored types fall to the digest (H16).
9. **Raises after losses go slow** (H19).
10. **Findings become scripts** so the agent stops repeating them (H27).

---

## 6. Problems and solutions

Full working in `linking/stage-b/X7-agents/problem-solving.md`. Each problem has at least two options.

| Problem | Option 1 (trade-off) | Option 2 (trade-off) | Option 3 |
|---|---|---|---|
| P1 Ruling 2 forbids automatic size-down from agent evidence | Evidence as a fact the unit's own rule reads, H03 (keeps the ruling's letter; needs a relay and a template section) | Amend ruling 2 to "automatic changes are monotone toward less risk" (covers drift, isolation and BMS breakers in one sentence; his call) | Cards only (no change; cuts arrive hours late) |
| P2 Noise | One attention budget, H15 (simple; a low cap can starve a good card) | Per-agent credit, H18 and H10 (self-tuning; new agents start starved) | Graduation H16; dedupe H17 |
| P3 Stealth raises | Monotone lattice, H02 (structural; QMA change) | Effect descriptor walks the ledger's edges, H04 (catches indirect raises; needs complete couplings) | Shadow first (slow for rare units) |
| P4 Search luck in tuning, windows, isolation rules | One search ledger with deflation, H09 (honest; slower promotions) | Funded tests on fresh results, A4-121 (lifetime control; no power for tiny edges) | Plateau tuning plus a few bandit arms, H24 |
| P5 Poisoned inputs | Cut-only, capped, corroborated records, H39 (a fake costs a little and expires) | Strip credibility cues, aggregate hierarchically (the only tested defence) | Scheduled red team, A4-138 and A5-058 |
| P6 Who switches a class off on 20 days of evidence | Nominate, confirm, apply, H21 stage 2 (acts without him on confirmed evidence; needs class scope) | Card only, H21 stage 1 (works now; waits for him) | The MIS publishes isolation and placement fails closed (collides with "the MIS never switches") |
| P7 The cut-only ratchet starves growth | Pre-authorised restore ladder, H05 (growth returns without him; ruling question) | Advocate agent, H32 (growth gets a voice; more cards) | Every cut carries a release rule (A5-103) |
| P8 Tools for the Lab, MCP agents and the department | Risk mini app with an MCP server, H36 (one surface for all; app lander missing) | Catalog rows only, X1-43 (fast; outside MCP clients need a bridge) | Both, one implementation (two names for one tool) |
| P9 Proving an agent adds value | Ablation, A4-137 (clean; needs a fixed tape) | Matched random de-risker, H11 (strongest filter; months of fires) | Alerting scorecard against a cheap detector, A5-050 (agents may lose detection jobs, which is the point) |
| P10 Which styles may receive agent evidence | Eligibility by holding time, H03 (honest about latency; scalpers get little) | Evidence acts only from the next session (simple; slow for intraday shocks) | |
| P11 He is away or asleep | Rules by direction: cuts act through unit rules, raises and structure wait (safe; growth waits) | Card time to live in his waking hours plus a morning brief, H46 (cards do not die unread; he must state his hours) | |
| P12 Model upgrades change agent behaviour | New model = new agent version at level 0, re-qualified (safe; slow to adopt) | Shadow the new model on the same tape and promote by scorecard (cheaper; doubles inference while shadowing) | |
| P13 Many agents on one model or feed | Count evidence once per model family and per feed (honest; less corroboration) | Measure agent independence from record correlation (new measure; no component has it) | |
| P14 Money MCPs as a second road | Venue MCPs only inside the trading-node app (keeps the operator guard) | A read-only broker MCP for agents, enforced by credentials (market data direct; scope must hold) | |
| P15 When an agent should stop a job | Graduation by recurrence, H27 (cheaper over time; agents shrink their own role) | Job registry with a quarterly razor review (light; someone must run it) | |

---

## 7. Collisions

Named, not resolved.

- **C1. Ruling 2 against automatic cuts and restores.** G2-2 allows only a unit's own rule stopping it. H03 (agent evidence), H05 (pre-authorised restore), drift size steps (A2-133) and confirmed isolation (H21 stage 2) all change trading automatically. A4-176 already notes ruling 2 blocks the automatic size-down that drift needs.
- **C2. "Agents do the heavy lifting; just give me the units" against clicks.** D41 and old WF2 registered into paper with no human gate. The unit build made every move toward paper his click (G2-4). Every card in this file adds clicks his attention budget must absorb.
- **C3. "The sky's the limit" against rationing.** D42 wants agents proposing freely. H09, H10, H15 and A2-220's family error budget all ration proposals. The roundtable split: unlimited run surface, limited queue.
- **C4. Isolation "should kick in with evidence" against "an agent cannot switch a class off".** His words want automatic isolation on evidence (C27). A3-113 keeps it a card. A3-115 wants the MIS to publish it, against A3-184 "the MIS amplifies and never switches".
- **C5. Cut-only agents against performance with intention.** The de-risk-only channel is a one-way pressure toward trading less: the sitting duck (M33). H05 and H32 push back; they add raises the core must then guard.
- **C6. Three feeds, three fail modes.** The MIS board fails open (G9 4.3); isolation needs fail closed (A3-115); agent evidence fails neutral (H03). A unit reading all three has three different meanings for "missing".
- **C7. Proof is slow; he wants paper short.** E-value restores and Promote are slow for weak edges (+0.10R about 604 trades; 5 bp never crosses). He called 14 paper days too long (D22).
- **C8. Steward's intent model against G2-5.** Steward is built for agents that choose trades. QMX units are deterministic logic, and G2-5 keeps agents out of the fast lane. H49 (agent-trader units, his parked D44) puts an LLM in the entry path, though not the risk path.
- **C9. A money MCP outside the host door.** The trading-node app's MCP keeps kill, pause, resume, flatten and deploy operator-only. The cTrader MCP the build session is shipping, and a Hyperliquid one he wants, were not checked; if either is a separate server with order or position tools, it bypasses the door.
- **C10. Two homes for one tool set (with X1).** X1's draft puts agent tools as `qmx_control` catalog rows (X1 idea 43); H36 puts them in a risk mini app's MCP server. H06 (spec, status, suggestions) also overlaps X1's template document. In the ledger, X1's `x1_proposal_expiry` and this layer's `agent_evidence_ttl` share the alias `evidence_expiry_by_type` (the checker warns when both files load).
- **C11. Hidden scenarios against "show me everything".** H12 hides a scenario set from agents. He can see it; the copilot, which is an agent, cannot, so it cannot explain why a version failed on it.
- **C12. Post-cutoff evaluation against using agents now.** H14 judges agents only on data after their model's training cutoff. Fresh models have little such history, so agents start at advice-only for months.
- **C13. Autonomy against the market.** A5-078 demotes an agent's autonomy on drawdown. The roundtable changed that to a freeze, but a long book drawdown still freezes good agents for reasons that are not theirs, and "a human reset becomes routine".
- **C14. Rationale-blind checker against the challenger.** H13 hides the rationale from the admission check; the challenger (A4-136) needs it to attack. Two roles, one card.
- **C15. Graduation against heavy lifting.** H27 shrinks agent work into scripts, the July razor. His D41 wants agents to do more, not less.
- **C16. Expiring evidence against 20-day evidence.** Evidence records live minutes to days (H39). His isolation evidence is "analysis over 20 days". The nomination window (H21) and the record's time to live measure different things.
- **C17. Inside this file.** H10 (testing wealth) and H15 (attention budget) are two budgets on one flow; H16 (graduated rules run without clicks) and H05 (raises need evidence) disagree on whether a graduated raise rule still needs an e-value.
- **C18. With X3 and X5.** H31 lets scripts make size steps on decay; X5's draft has an agent pass after a nightly deterministic job (A4-148) and X3 owns the brakes. Who owns the size step (X3's brake or X5's zone) is not settled in this layer.

---

## 8. Restructure proposals

- **RP1. Restate ruling 2 by direction.** Replace "the only automatic change is a unit's own risk rule stopping it" with "automatic changes are monotone toward less risk and are always a declared rule of a unit, Book or BMS; raises are his, once (pre-authorised rule) or per step (card)". *Why it performs better:* drift size steps, confirmed isolation, agent evidence and restore ladders all become possible without new rulings each time; size comes back without waiting for clicks. His call (question 1).
- **RP2. Replace departments and personas with a job registry and an autonomy ladder.** April's Portfolio department and July's personas (Cartographer, Coroner, Crowd Watcher, Scout, BMS Reader) become rows: job, cadence, output kind, direction, autonomy level, and the reason a script cannot do it (H18, H27). *Why:* only Research and Development ever worked in April (G10 2.1); a registry is measured and can shrink.
- **RP3. Give the unit and the BMS an evidence intake.** The Book/BMS shape gains `accepts_evidence` (H03) beside its limits, and pods ship with their risk agents and evidence contracts inside the bundle (A4-094). *Why:* agent analysis reaches risk as declared, testable inputs instead of prose cards; a scalping pod carries its own watchers.
- **RP4. Kill switch and stand-downs gain class and region scopes, and an escalation card path** (H21, H43). The kill still goes down only by his hand. *Why:* his isolation protocol needs a class scope; today none exists anywhere (G9 4.4).
- **RP5. Replace tighten-only decay cards with deterministic steps plus a restore ladder.** `dc-decay-and-limit-report` today lands one tighten-only card per flagged unit. Steps both ways become unit rules; cards remain only for structure (H05, H31). *Why:* a tighten-only ratchet on noisy estimates drives units to minimum size (A1-064); cards per unit per night flood him.
- **RP6. One card format everywhere.** The shared proposal-card block used by `b-build-and-prove`, `dc-decay`, `pp` and `p1` becomes the effect-bound card (H04). *Why:* one checker, one queue, one budget.
- **RP7. QMA flags (not designed here).** Direction field on catalog rows and app operations; `admits` extended by direction; a call contract with run, profile and model ids; agent profile and autonomy storage; a reflector for agent procedures; an app lander for cards and evidence; a host relay for the evidence feed.

---

## 9. Gaps: what no component covers

- **His own decision quality.** No component measures the value of his approvals and rejections (H41 is wild).
- **Agents across venues.** Nothing scopes agent evidence across a cTrader account and a Hyperliquid account at once.
- **Inference spend against value.** A4-139 measures cost; nothing budgets inference per job against the value of what it changes.
- **Re-qualifying an agent after a model change.** A4-113 pins snapshots; no component says how a new model earns trust again.
- **Agent independence.** Nothing measures how many independent agents there are when many run on one model or one feed.
- **Style eligibility.** No component says which styles may receive agent evidence at all; H03's rule is new.
- **Hours he is away.** No component says what cards and evidence do while he sleeps, beyond "loss of the service means no change".
- **The queue during an incident.** Nothing says whether non-urgent cards freeze while a kill level is raised or a budget is spent (A4-033 freezes releases, not proposals).
- **The cTrader and Hyperliquid MCPs.** Their tool lists were not read; whether they are inside the trading-node app's door is unknown.
- **Data licences for agent inputs.** A5-057 names the check; no component gives the register.

---

## 10. Questions only he can answer

1. May a unit's or the BMS's own declared rule **cut** size automatically on agent evidence (cut only, expiring, missing means no change)? This is ruling 2 (RP1).
2. May class or region isolation apply **automatically** once a deterministic check confirms an agent's nomination, or always after your click?
3. May you approve a **restore or accelerator rule once**, so its steps run without a click each time?
4. How many **cards a day** will you read? A number, or "let the system measure me".
5. Should the template **reserve a unit type for agent traders** now (agents choose entries; the template sizes, exits and brakes), knowing it puts an LLM in the entry path?

---

## Appendix A. Method record

- **Brainstorming (headless):** memlog `linking/stage-b/X7-agents/.memlog.md`, about 190 entries, 132 ideas. Techniques: Morphological Analysis (11 parameters from the components, combined into job configurations, with the forbidden corner named), Concept Blending, Forced Relationships, Cross-Pollination (casinos, ER triage, nuclear control rooms, bank model risk, card-fraud teams, underwriting, Wikipedia bots, flight dispatch, peer review, weather services, power grids, clinical monitoring boards), Trait Transfer (TCP, SRE, VPA, Terraform, Argo, HotSpot, Numerai, Topstep, poker, MetaEditor), Evolutionary Pressure (four generations; selection rule: survival gate, then growth per minute of his attention, then fewest new variables, then day-one fit), Solution Matrix (12 problems against 18 components; six empty cells became the gaps), then domain shifts (failure modes, his experience, growth and compute, wildcards, the class lens). Intent: `brainstorm-intent.md`. No HTML (brief).
- **Problem solving:** `problem-solving.md`, 15 problems, at least two solutions each.
- **Roundtable:** `roundtable.md`, eight voices (pod-shop risk manager, retail scalper, platform engineer, his voice from his words, red-teamer, model-risk validator, SRE lead, statistician), seven rounds. Changes it forced are in H02, H03, H11, H15, H16, H18, H21, H32, H36 and H13.
- **Grounding read:** host door and app manifests at the stack tip; G2, G8, G9, G10; SEEDS D26, D41-D45, A25-A28, C26-C28, TLH; R4 workflows; components across A1 to A5 (all 114 tagged X7 plus about 70 from other layers).

## Appendix B. UI needs for the UI session

- One card screen: at most the day's budget of cards, each with a ten-word headline, money both ways, evidence tier, tries, reversibility, one button; agent text marked untrusted.
- The digest: one line per overflow item.
- Per unit: active evidence records with kind, cut, expiry and source; the three fail modes of its feeds.
- Agent report card: precision, lift over random per class, reversals, ignored cards, inference cost, autonomy level.
- Attention meter: cards today against the budget; queue burn.
- A "why" link on every number (H47).
- Pre-authorised rules: list, expiry, re-confirm button.
- Incident view with the one-tap kill escalation (H43).
