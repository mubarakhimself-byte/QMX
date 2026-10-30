# The workflows field: candidate QMX workflow templates around units

Written 2026-10-30 by the workflow-templates expansion agent. Read-only grounding plus a party-mode round (`party-transcript.md`, rounds P1 to P12) and a headless brainstorm (`.memlog.md`, ideas W001 to W152; summary in `brainstorm-intent.md`). **Nothing here is a design or a choice.** It maps the playing field: candidate templates, the skills, hooks and scripts they would need, questions, delivery options, a cross-map and a parked list.

## How to read this

**Labels.** CHECKED = read at the cited path, line or command output on 2026-10-30. INFERRED = my reading. Every candidate template is INFERRED as a proposal; the facts it rests on carry their own labels.

**Marks.** Each candidate is either **Seed-expanded** (it names the seed it grows from) or **New** (in no seed I found). The five operator seeds from the brief are abbreviated:

| Mark | His seed | His words (verbatim, checked by script) |
| --- | --- | --- |
| S-WF | Take the Hermes workflows (Friendly greeting, the gold mine) and the old WF1/WF2, enhance them | "the templates inside the friendly greeting and the gold mine are more similar to WF2 and WF1 in the old QMX system" (T2:1148); "It's far better to enhance them." (T2:1148) |
| S-FUN | The strategy funnel: source, idea, build, test, then pass, fail and rewrite branches; cheap models for bulk; agent memory | "Think of it like levels, okay? With branches." (T1:513); "most of the work I've been talking about is done by cheap workhorses" (T1:513) |
| S-ANL | Agents as analysts of markets and of units, separate families, 24/7, proving their claims | "analysis based off the markets themselves and also analysis based off the units themselves" (T2:385); "We are literally trading 24/7, my days." (T2:325) |
| S-JDG | Judging as a skill: hooks plus deterministic scripts that call QMB; agents propose, he approves, proposals in the UI | "a skill literally has hooks and deterministic scripts and so on and so forth, which means it can call QMB" (D27:9); "the proposal should be rendered in the UI" (D27:9) |
| S-DLV | Two delivery options: build in the coding phase, or write up in detail now and code later, maybe as the Lab's first job | "We either build them during the coding phase" (T2:1148); "the lab, that's one of the first things the lab maybe might do" (T2:1148) |

Source keys: `T1:n` = `operator/transcript-2026-10-20-to-28.md`, `T2:n` = `operator/transcript-2026-10-29-to-30.md`, `D27:n` = `operator/2026-10-27-review-dictation.md` (all `grep -n` line numbers; 64 quotes checked, 0 missing). `R08`, `R11`, `R18`, `R19`, `R39`, `R40`, `R42` = `research/<n>-*.md`. `KB` = `research/funnel3/cis/problem-solving.md` knot (b). `PF` = `research/funnel3/party-brainstorm/playing-field.md`. `QF` = `research/funnel4-qml/party-brainstorm/qml-field.md`. `TIP` = `origin/build/sy5` at `074670ac` in `C:/Users/Mubarak/Desktop/QMX`; template facts were read there with `git show` by this run's parser (`tpl.py` in the session scratchpad). `P1`..`P12` = party rounds. `Wnnn` = brainstorm ideas.

**Template short names used below** (all CHECKED at TIP, folder `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/`): `a` a-fill-the-library, `b` b-build-and-prove, `l1` l1-idea-to-first-result, `d3` d3-iterate-against-qmb, `d4` d4-variant-comparison, `l4` l4-overnight-lab-loop, `rs0`..`rs8` the research templates, `dc` dc-decay-and-limit-report, `t7` t7-trade-journal-review, `dm` dm-demo-monitor, `db` db-desk-brief, `t3` t3-news-calendar-watch, `t4` t4-research-desk-overnight, `rv` rv-weekly-review, `pp` pp-proposal-pack, `rev` revolution-loop, `cry` crystallise-a-workflow, `atp` ask-the-panel, `syn` synthetic-data.

---

## 0. What matters most (short)

1. **His funnel already exists as draft shapes.** `b` is WF1 from idea to a paper card, `d3` and `l4` are WF2, `rs6` mines dead ends, `dc` and `t7` read journals. All are drafts waiting on `qmb-door` or `trading-node` (R42 §1.8, CHECKED). His "I think WF1 and 2 are built. I'm not certain anyway." (T2:1148) is half right: the shapes are built, and none runs.
2. **What no template has: the chain, the judge, the skill.** No template uses an event trigger, so nothing starts when another finishes (R42 §1.2, CHECKED). No node names a skill (R42 §1.3, CHECKED). The overfit maths is copied into each template's own scripts (`deflated_sharpe.py` sits in both `b` and `d3`, CHECKED by listing). INFERRED: the cheapest big step is one shared judge block plus event-trigger wiring between existing templates.
3. **"Hooks" means two things.** A workflow cannot declare its own Claude hooks; a pack's hooks are never written (`HAR/packs.py:8`, `:44`, R42 §7, CHECKED). What a workflow does have is grader and script nodes the agent cannot skip. INFERRED: his "judging skill" can be a shared judge subworkflow (the hooks) plus a skill that explains its verdict.
4. **The builder default contradicts his seed.** `roles.builder` defaults to the strong tier, `roles.judge` and `roles.triage` to cheap (`ENG/settings.py:175-188` at TIP, CHECKED). He wants cheap workhorses to build and a stronger model for rewrites (T1:513). It is a UI-editable setting, so the question is the default, not new machinery.
5. **The analyst families have no data door yet.** No catalog row reads a unit or a journal, the unit kind has no fields, and agents cannot pass a holdout or run id through a tool call (R42 §1.7, CHECKED). Every market-analysis and unit-analysis template below waits on at least one of these.
6. **The proof seed has a buildable core.** Receipts (every number cites a tool call), a forecast ledger scored later by a script, and a landmark field for the window together answer "Who's comparing?" (T2:385): the market compares (KB options 1, 3, 6). INFERRED.
7. **Approval is a card plus an event.** `human_gate` is planned only (R42 §1.1, CHECKED). His publish click lands an item, and an event trigger can fire on a landing (R42 §1.2, CHECKED). INFERRED: approve-and-chain is buildable today.

**Five templates that matter most for the field** (most seeds touched, most reuse, least new machinery; INFERRED, not a choice): **D1** the funnel conveyor, **C1** the judge block, **F2** where failed rules hold (with **F1** death certificates), **H1** the session-close weather service with a forecast ledger, **I1** the traded, skipped and missed review.

---

## 1. What is on the shelf, by funnel stage

| Stage of his funnel | Shipped templates (runnable / draft) | Waits on | Gap found (CHECKED unless marked) |
| --- | --- | --- | --- |
| Source intake | `a`, `rs1`, `rs2`, `rs4`, clippings, `feed`, extract-source (runnable) | none | No copilot-chat or operator-words intake; no channel dossier; no book-specific path (INFERRED from the list) |
| Idea to card | `rs0` (runnable); `l1` card step (draft) | `l1`: qmb-door | `l1` has a `complete` rule node before building |
| Build | `l1`, `d3`, `d4`, `bc` builder agents (drafts) | qmb-door, sandbox | Builder role defaults strong; nothing blinds the builder to in-sample results; `d3` blinds only the diagnoser (`blind.py`) |
| Test and judge | `b`, `d3`, `d4`, `l4` (drafts); `_shared/overfit-gates` | qmb-door | Gates hard-written per README (`b`: 100 trades, WFE 0.5, MC 5th pct > 0, 1.5x costs, DSR 0.95); no shared judge subworkflow |
| Pass branch (expand) | `d4` variants by instrument and timeframe (draft) | qmb-door | No expansion matrix, no "where it broke" output |
| Fail branch | `rs6` hypotheses from dead ends (draft) | real-library | Fixed moves: condition, slow down, invert, transplant, drop; test data must start after every parent window |
| Rewrite branch | `l4` plateau then one fixed move; `rev` loop (runnable, no QMB inside) | qmb-door | No model escalation step |
| Family tree | `lineage.py` in seven templates (`b`, `bc`, `d3`, `d4`, `l1`, `p1`, `rev`) | varies | Seven copies of one script |
| Market analysis | `db`, `t3`, `t4`, `atp` (runnable) | none | `db` leaves out node facts and the MIS grid (R18 §1.5); no call is scored later |
| Unit analysis | `dc`, `t7`, `dm`, `rk8` (drafts) | trading-node | No journal read path anywhere (R42 §1.7) |
| His approval | `pp` bundle for approval (draft), every template's deliver card | trading-node, risk-session | No in-workflow approval step |
| Cost | `cry` crystallise (runnable) | none | Today it derives a word rule from twenty recorded labels (`cry/README.md`), so it suits labelling steps, not analysis yet |

Template memory scopes declared at TIP: `workflow` everywhere, `run` in `dm`, `operator` in `pp` and `t7` (parser, CHECKED). Whether any step reads or writes memory rows at run time is not checked; `rs6`'s README says its "do not retry" notes need the real Library's one-writer door (CHECKED).

---

## 2. The candidate template map

Each block: purpose, trigger, steps, agents (by engine role, with today's default tier), skills, hooks (graders and script gates), scripts, what it reads and writes, what it extends, what it waits on, and the ideas behind it. Roles and tiers are CHECKED at `ENG/settings.py:175-188` (TIP); everything else in a block is INFERRED unless cited. Numbers are starting defaults to edit (standing order 5), never settled.

### Family A. Intake and sources

**A1. Copilot chat to idea cards.** Seed-expanded: S-FUN ("a conversation between me and the co-pilot, or between me and any agent, a transcript per se", T1:513).
- Purpose: turn his chats with the copilot or any agent into idea cards that cite message ids.
- Trigger: session end (the `session` trigger is partial, R18 §1.2) or a cron over finished sessions; also his "save this" phrase.
- Steps: collect finished transcripts → quarantine-mark text as data → cheap triage per chunk → extractor writes idea cards with message ids → quote grader → deliver card.
- Agents: triage (cheap), extractor (mid). Skills: idea-card format. Hooks: quote grader (exists in `a`). Scripts: transcript reader, chunker, quote check.
- Reads: harness chat store. Writes: idea cards, source records (operator words).
- Extends: `a` (same shape after intake) and clippings. Waits on: a read path to chat transcripts (not checked). Ideas: W001, W002, W012.

**A2. Operator words as a source kind.** Seed-expanded: S-FUN ("Book, bloody hell, even just me explaining.", T1:513).
- Purpose: store his dictations raw, so every idea traced to him cites a line, and label them idea-evidence, never market-evidence (R39 H8).
- Trigger: manual or after A1. Steps: save source → split by turn → link cards. Agents: none. Scripts: save_source (shared block exists).
- Reads: operator transcripts. Writes: source records. Extends: `_shared/save-source`. Waits on: nothing found. Ideas: W002.

**A3. Channel dossier.** Seed-expanded: S-WF (R39 H12: seed video → channel dossier → episodes → guests → related channels).
- Purpose: score the creator, not only the item: specialty, instruments, whether they give exits, which of their ideas survived.
- Trigger: manual, or event on a new video source landing from `a`.
- Steps: fetch channel metadata (script) → playlists and guests (script) → cheap triage → writer dossier → link to every item from that creator.
- Agents: triage (cheap), writer (mid). Hooks: citation grader. Reads: video metadata. Writes: dossier record. Extends: `a` intake. Ideas: W003, W004.

**A4. Indirect source miner.** Seed-expanded: S-WF (R39 H18; STATE item 9 "Use the articles later inside QMX through mini apps and workflows").
- Purpose: mine MQL5 CodeBase inputs, forum comments, parameter names and TradingView script inputs for primitives and ranges.
- Trigger: cron weekly, or manual per site. Steps: fetch (script) → parse inputs (script) → extractor maps parameters to dictionary entries or "unmatched" → append requests.
- Agents: extractor (mid). Skills: dictionary lookup. Writes: append requests, component cards. Extends: `rs2`, `feed`. Ideas: W006, W018.

**A5. Long source economy block.** Seed-expanded: S-WF (R39 H14, R40 #2).
- Purpose: a shared subworkflow for long transcripts, books and videos: chapters, overlapping chunks, cheap relevance per chunk, 10-minute clips for vision models, compact evidence packets for one strong reader.
- Trigger: called by A1, A3, `a`, `rs2`. Agents: triage (cheap), reader (mid). Scripts: chunker, clipper. Extends: `_shared/extract-source`, `understand-extract`. Ideas: W007, W008, W010, W126.

**A6. Paper or article to unit idea.** Seed-expanded: S-FUN; R11 §1 (none of the eight papers tests what QMX trades).
- Purpose: after `rs1` writes a note, decide whether its test domain transfers (stock cross-section vs FX, CFD, crypto intraday) and only then make an idea card.
- Trigger: event on a `rs1` note landing. Agents: reader (mid). Hooks: research-claim checklist grader (R11 J9). Extends: `rs1`. Ideas: W011.

**A7. Source scorecard.** Seed-expanded: STATE "knowing where high performers come from narrows the search over time".
- Purpose: per source, count ideas, units built, units surviving judge and paper. Feeds triage ranking in A1, A3, `a`.
- Trigger: weekly cron. Agents: none (script). Reads: lineage edges. Writes: source score rows. Ideas: W004.

### Family B. Building units

**B1. Card to vanilla and spiced unit.** Seed-expanded: S-WF (old WF1 vanilla and spiced, R19 §1); S-FUN (cheap builders).
- Purpose: build the first two nodes of a family from one complete card: vanilla (the source's logic as is) and spiced (plus the blocks QMX already handles).
- Trigger: event on an idea card landing with status "complete", or manual.
- Steps: completeness grader (the eight-part checklist, R39 GM 2724) → match report (script maps rules to QML entries) → builder writes the unmatched rest → alignment re-read by another model family → compile → deliver to C1.
- Agents: builder (strong by default; cheap per his seed, Q16), reviewer (strong) for the re-read. Skills: unit-building skill (QML verbs, card format; none exists, R42 §7). Hooks: completeness grader, alignment grader, "outside QML" tagger. Scripts: match report, compile.
- Reads: card, dictionary. Writes: unit draft (governed kind, lands on drafts for his yes, `LIB/landing.py:8-11`, R42 §1.5), lineage edge.
- Extends: `l1` (card, `complete` rule, builder, run), `bc`. Waits on: qmb-door, unit kind fields. Ideas: W013, W014, W015, W016, W018, W020, W021.

**B2. Red-team builder.** Seed-expanded: QF B111.
- Purpose: a cheap agent tries to pass QML checks with an empty, lookahead or always-on unit. Each success becomes a missing-check card.
- Trigger: weekly cron, or after a QML release lands. Agents: builder (cheap). Hooks: the checks under test. Writes: check-gap cards. New template. Ideas: W022.

**B3. Rebuild with a newer model.** New.
- Purpose: when a new model arrives, rebuild a sample of families from their stored cards and diff the units against the old builds.
- Trigger: manual. Reads: build replays (card, model, prompt, output). Writes: diff report. Extends: `atp` spread idea. Ideas: W024.

**B4. Missing block to dictionary request.** Seed-expanded: QF B076; STATE "Plain Python is always possible".
- Purpose: collect every "outside QML" block a builder wrote, cluster them, propose dictionary entries.
- Trigger: event on a unit draft with outside-QML parts. Agents: extractor (mid). Writes: append requests. Ideas: W021, W023.

### Family C. Testing and judging

**C1. The judge block.** Seed-expanded: S-JDG ("I don't think it should be really up to agents", D27:9); R11 §4 J1 to J10; R39 K9.
- Purpose: one shared subworkflow that every finding, expansion and rewrite template calls, so judging is the same everywhere. The scripts decide; an explaining skill writes the reasons; he decides what passes.
- Trigger: called as a subworkflow by B1, D1, E1, F2, G1, `b`, `d3`, `d4`, `l4`.
- Steps: sealed spec (`b`'s `spec.py`) → staged tests, cheap to expensive, early stop (semantic, screening, ablation, sensitivity, locked challenge) → try ledger update (every screen, child and best-of counts) → deflated Sharpe over the family (`_shared/overfit-gates`) → per-period table, cost stress, three-instrument challenge (C2) → holdout-once ledger → verdict grid → writer explains → render and grade.
- Agents: writer (mid) only for prose. Skills: judging skill (explains the grid). Hooks: render_and_grade (every number in prose matches a script output, existing convention), fake-pass graders (rerun counter, window from the sealed spec, costs present, dead children present). Scripts: spec, qmb call, try ledger, holdout ledger, DSR, grid.
- Reads: unit, family try ledger, sealed spec, data. Writes: verdict grid with judge@version, try ledger rows, negative results.
- Extends: replaces the copied gate scripts inside `b`, `d3`, `d4`, `l4`. Waits on: qmb-door. Ideas: W025, W026, W029, W031, W034, W036, W099.

**C2. Three-instrument challenge.** Seed-expanded: S-WF (R39 K1: home pair, close analogue, adversarial compatible pair).
- Purpose: a stage inside C1, or alone: test the unchanged unit on three instruments picked by a similarity script.
- Agents: none. Scripts: instrument similarity, rerun. Ideas: W027.

**C3. Judge negative control.** Seed-expanded: KB option 9; `syn` template.
- Purpose: weekly, run C1 on shuffled or synthetic series (`syn` already makes moving-block bootstrap series, R18 §1.5). A pass is a judge bug.
- Trigger: weekly cron. Agents: none. Writes: judge health rows. Ideas: W030.

**C4. Paper stage in the verdict.** Seed-expanded: STATE "Judge from historical AND paper trading".
- Purpose: paper results flow back into the same verdict grid, so one page shows backtest, stress and paper side by side.
- Trigger: event on paper trades landing (event source missing). Waits on: trading-node, journal read. Ideas: W033.

**C5. Model-memory probe.** Seed-expanded: R11 T4, J5. Bounded by his correction: analyst agents read live data, so the probe applies to agent-built units judged on history, not to live analysis ("They are going to be using live markets", T2:385).
- Purpose: for an agent-built unit, check its judged window starts after the building model's training cutoff, or that a probe ran.
- Agents: builder (the same model, no search) for the probe. Ideas: W028.

**C6. Disputed verdict panel.** Seed-expanded: `atp`; R19 §8 (models as review lenses, not votes).
- Purpose: when two windows or two judge views disagree, several model families write reasons. Numbers still decide.
- Trigger: event on a grid with a split. Agents: reviewer (strong) x3 families. Extends: `atp`. Ideas: W037, W094.

### Family D. The funnel itself

**D1. Funnel conveyor.** Seed-expanded: S-FUN ("It all started from one bloody idea.", T1:513); S-WF (old WF2's three entry triggers, R19 §1).
- Purpose: wire the stages with event triggers so each landing starts the next: card → B1 → C1 → pass (E1) / fail (F1, F2) / rewrite (G1) → his card. Every box is a family-tree node.
- Trigger: event triggers on Library landings filtered by kind and producer (`ENG/triggers/event.py`, R42 §1.2, CHECKED). No new node kind.
- Steps: none of its own; it is a set of trigger rows plus a routing script that reads the verdict grid and lands a routing item ("pass", "fail", "rewrite", "park").
- Agents: none. Hooks: a loop guard (a child landing must not re-fire its own parent's build; Q40). Scripts: router of verdicts.
- Reads: verdict grids. Writes: routing items, lineage edges.
- Extends: links `l1`, `b`, `d3`, `d4`, `l4`, `rs6`. Waits on: qmb-door for the stages, nothing for the wiring. Ideas: W111, W112, W115, W116.

**D2. Approve and chain.** Seed-expanded: S-JDG ("the proposal should be rendered in the UI", D27:9).
- Purpose: his publish click on a card lands an item; an event trigger starts the next stage. Decline reasons are kept as a taste signal.
- Trigger: event on his publish. Agents: none. Writes: decision rows. Waits on: whether event filters see a publish (Q03). Ideas: W112, W135, W136, W141.

### Family E. Pass branch: expand the domain

**E1. Expansion matrix.** Seed-expanded: S-FUN ("you need to know when to expand. And when not to expand", T1:513).
- Purpose: rerun the unchanged unit across instrument × timeframe × session × broker × data class. No agent.
- Trigger: event on a C1 grid routed "pass", or manual.
- Steps: pick cells (script; analyst-tagged similar markets first) → reruns → C1 on every cell (tries inherited, fresh windows) → card "where it held, where it broke" with the MIS state per cell → stop rule (a named number on try-corrected expected value, default to be set, Q36).
- Agents: none by default. Hooks: C1's graders. Scripts: cell picker, rerun. Reads: unit, MIS labels, data. Writes: expansion grid, sibling variants (`variant_of` per `d4`'s label table).
- Extends: `d4` (instrument and timeframe variants), old WF4 "Ecological + feature mutation" (R19 §1). Waits on: qmb-door. Ideas: W038, W039, W040, W043, W046, W047, W048.

**E2. Timeframe transplant.** Seed-expanded: S-FUN ("(1) get the logic as is, or (2) rewrite the logic or adjust it to fit the 1 minute interval", T1:513).
- Purpose: move a unit from 5m to 1m (or any pair of clocks). Try as is by script; only if that fails, a builder rewrites; both are kept as siblings.
- Agents: builder (cheap first, strong on the second try). Extends: E1, G1. Ideas: W041, W053.

**E3. Sniping overlay.** Seed-expanded: S-FUN ("some domain expansions can come with sniping", T1:513); R39 FG 902 (sniping spans roles).
- Purpose: add a timing or liquidity-window overlay to a passing unit as one more expansion axis. Agents: builder. Ideas: W042.

**E4. Universe and fingerprint proof.** Seed-expanded: STATE 10-28 (System 1 live, System 2 in research; Path A, a System 2 version is earned from a record).
- Purpose: from E1's grid, write the unit's universe and condition fingerprint, the inputs System 1 would use live. Agents: none. Writes: universe record on the unit. Ideas: W045.

**E5. Asset-class transfer.** Seed-expanded: STATE (units span instruments); R40 #7 (crypto base and quote).
- Purpose: FX unit to crypto spot, perps or indices with a transfer-caveat check: costs, hours, funding, weekend. Agents: reviewer for caveats. Ideas: W044.

### Family F. Fail branch: why it failed, and where its rules hold

**F1. Death certificate and graveyard.** Seed-expanded: S-FUN ("If they fail, we need to be able to know why is it failing.", T1:513); R19 §8 (the July Coroner and Graveyard Index, judged on recurrence of known causes).
- Purpose: every failed unit gets a typed cause from an appendable list (no trades, costs ate it, one-period luck, late trigger, data gap, lookahead, regime-only), and a per-family recurrence count.
- Trigger: event on a C1 grid routed "fail".
- Steps: classify by script where possible (signal funnel counts, cost share, best-period share) → cheap agent only for the unclassified → reviewer from another family on agent-assigned causes (old WF2's guard against false diagnosis, R19 §1) → graveyard row.
- Agents: scanner (cheap), reviewer (strong) only when contested. Hooks: receipts grader. Writes: death certificate, graveyard index, do-not-retry notes (read by every builder).
- Extends: `rs6` inputs, `rk8` post-mortem shape. Waits on: qmb-door. Ideas: W049, W050, W060, W062.

**F2. Where would its rules hold.** Seed-expanded: S-FUN ("do we have any context under QMX in which these rules are met?", T1:513).
- Purpose: search contexts (MIS state, session, instrument, timeframe, news window) where a failed unit's rules held, with proof only on a window the search never touched.
- Trigger: event on F1 landing, if the cause is not "lookahead" or "data gap".
- Steps: context list (script) → per-context reruns on a search window → every context counted as a try → the best context tested once on a sealed window → card.
- Agents: planner (strong) proposes contexts beyond the fixed list. Hooks: C1, sealed-window grader. Writes: context grid, a conditioned child (`derived_from`).
- Extends: `rs6` "condition" move. Waits on: qmb-door, MIS labels readable in QMB. Ideas: W051, W052.

**F3. Hypotheses from dead ends, extended.** Seed-expanded: S-WF (`rs6`; old WF2 rehab tokens, R19 §1).
- Purpose: `rs6` as shipped plus more fixed moves (add exit, change timeframe, swap trigger keep level, R39 G15) and an event trigger on N new dead ends (5 today).
- Agents: writer (mid) per cluster. Extends: `rs6`. Waits on: real-library (possibly already met by PR 216's script reads, Q45). Ideas: W052, W116.

**F4. Rehab while parked.** Seed-expanded: R08 §2.1 (July rider: keep collecting on paper so decay data keeps flowing).
- Purpose: a parked parent keeps a paper journal while F2 and G1 try children. A child that works links back. Waits on: trading-node. Ideas: W056.

**F5. Failure as a veto.** New.
- Purpose: a rule that fails reliably becomes a veto block offered to other units ("when this fires, don't"). Tested like any block. Ideas: W059.

### Family G. Rewrite branch and evolution

**G1. Plateau then rewrite.** Seed-expanded: S-FUN ("So you can bring in a Claude model, for example", T1:513).
- Purpose: cheap builders loop; on a plateau, a strong model rewrites once; on a second plateau the family parks.
- Trigger: plateau landing from `l4` or `d3` (plateau today = 30 trials without a better validated score, `l4` README).
- Steps: read the family's tree and death certificates → strong builder writes one structural rewrite → C1 → back to D1 routing.
- Agents: builder at the strong tier for this step only (per-step tier, Q43). Writes: new version with parent link and rewrite count. Extends: `l4` plateau move, `d3` children. Ideas: W053, W054, W061.

**G2. Crossover across families.** Seed-expanded: S-FUN ("hybrids, tribrids, quadbrids, whatever", T1:264); R39 G9.
- Purpose: combine blocks from two parents in different families; the child carries both families' try counts. Agents: planner, builder. Writes: `composed_from` edges (R39 G4). Ideas: W055.

**G3. Overnight evolution, extended.** Seed-expanded: S-WF (`l4`, old WF2 "AlphaForge", R19 §1).
- Purpose: `l4` with cheap builders in bulk, a script selection rule and breeding of survivors; every child counted; mutation sprawl shown on each node. Extends: `l4`. Ideas: W058, W061, W129.

**G4. Corrected successor.** Seed-expanded: R39 G8.
- Purpose: when a failure traces to an ambiguity in the card, the fix is a corrected successor, not a variant. Agents: reader re-reads the source. Ideas: W057.

### Family H. Market analysis

**H1. Session-close weather service with a forecast ledger.** Seed-expanded: S-ANL ("we can have agents that can look or request for that day's data", T2:325); R19 §8 (the Cartographer, judged on calibration of weekly calls); KB option 3.
- Purpose: at each session close, scripts compute per-market state; agents write dated calls for the next session with a confidence; a script scores them when that session closes.
- Trigger: cron per market family from a clock table (Sydney, Tokyo, London, New York closes; crypto on a rolling clock, numbers to set).
- Steps: data read with a landmark window (script) → state per market (script) → flag markets that changed state (rule) → desk agents only on flagged markets write calls → receipts grader → forecast ledger rows → at the next close, scoring script → calibration board.
- Agents: scanner (cheap) on flags, synthesiser (strong) for the summary. Skills: market-reading skill. Hooks: receipts grader, landmark grader. Scripts: state calculator, scorer.
- Reads: bars, calendar, MIS labels. Writes: forecast ledger (no such kind exists, Q35), calibration rows.
- Extends: `db` (runs before each session today), `t4`. Waits on: data door open by default (PR 207), holdout or window via tool call, MIS state readable. Ideas: W063, W073, W087, W089, W090, W092, W114, W122.

**H2. Week-Map.** Seed-expanded: R19 §8 (living Week-Map: regime narrative, event-risk calendar, per-pair weather).
- Purpose: a weekly per-market narrative written Sunday and scored Friday. Agents: synthesiser. Extends: `rv`, `t3`. Ideas: W064.

**H3. Specialist desks.** Seed-expanded: S-ANL ("think of an organogram", T2:325; "agents that can specialize", T2:325).
- Purpose: desks by style (mean reversion, trend, news, crypto funding), each a subworkflow writing calls into H1's ledger; a script shows where desks disagree.
- Agents: one role per desk; tiers per desk. Hooks: H1's. Extends: `atp` (several members, a spread script). Ideas: W065, W066.

**H4. MIS replication check.** Seed-expanded: S-ANL ("They can use the TA, they can use the MIS logs and the MIS itself.", T2:325).
- Purpose: agents label a day independently; a script compares with the MIS labels; disagreement days become MIS research cards.
- Waits on: MIS labels readable outside the node (MIS code lives only in the never-deployed node, R18 summary in STATE). Ideas: W068.

**H5. Market tagging.** Seed-expanded: S-ANL ("you can consider tagging", T2:325).
- Purpose: scripts tag markets per period with behaviour; agents propose new tag kinds; tags are dated. Feeds E1's cell picker and the air-traffic view (H6). Ideas: W069, W048.

**H6. Air-traffic view and desk brief, extended.** Seed-expanded: STATE System 1; R18 §1.5 (`db` leaves out node facts and the MIS grid).
- Purpose: per market, which units' declared conditions are met now; added to `db` before each session. Agents: writer. Extends: `db`. Waits on: unit condition declarations, MIS state. Ideas: W067, W070.

**H7. Fundamentals and router journal review.** Seed-expanded: S-ANL ("the fundamentals", T2:325); STATE router journal.
- Purpose: calendar surprises, rate decisions, crypto funding and open interest, plus weekly spread, fee and slippage facts per instrument and broker. Extends: `t3`, `t4`. Waits on: router journal (missing, R42 §6). Ideas: W071, W074.

### Family I. Unit analysis

**I1. Traded, skipped, missed review.** Seed-expanded: S-ANL ("why did this unit trade this, or when it traded this", T2:325); STATE journal (signals detected but not taken, missed trades).
- Purpose: per unit per session, three lists with the condition values at each moment, joined to H1's calls for that session.
- Trigger: cron per clock, or event every N closed trades (10 is named in `dc`'s README, left out for lack of an event source).
- Steps: journal read (script) → replay of the same session in QMB (I2) → five-whys walk by script (trade → signal → condition → market → data quality), stopping at the first anomaly → cheap agent writes the diary entry from those numbers → receipts grader.
- Agents: scanner (cheap). Skills: unit-reading skill. Hooks: receipts grader. Writes: journal notes (agents may write there, STATE), analysis items.
- Extends: `t7`. Waits on: trading-node, journal kind and read path. Ideas: W075, W076, W080, W083.

**I2. Replay match.** Seed-expanded: R08 §2.3 (would a replay of the same day have taken the same trade).
- Purpose: mismatches classed as signal, fill or cost drift. Agents: none. Waits on: qmb-door, journal. Ideas: W077.

**I3. Decay check, extended.** Seed-expanded: S-WF (old WF3 pool cleaning, R08 §2.1); `dc`.
- Purpose: `dc` as shipped (CUSUM, band, cost and behaviour tests, tighten-only cards) plus an upside alarm and an event trigger per N trades. "Sense, do not dispose" (R08 §2.1).
- Agents: scanner (cheap) only on flagged units (existing pattern). Extends: `dc`. Ideas: W078, W079, W082.

**I4. Unit diary and self-explanation.** Seed-expanded: S-ANL ("the copilot can just help me understand what the workflows have done", T2:325).
- Purpose: a short daily entry per active unit, written by a cheap model from script numbers only; the copilot reads diaries on request. Ideas: W083, W084.

**I5. Missed-trade blocker audit.** Seed-expanded: STATE journal (missed trades); D27:9 (guards must run independently).
- Purpose: count signals that fired while blocked, by blocker (news switch, spread sensor, guard, late router), so each guard's cost shows. Agents: none. Waits on: trading-node. Ideas: W085.

**I6. Unit, family and pair over time.** Seed-expanded: S-WF (old WF3 performance over time); STATE ("WF3-style performance-over-time studies (unit, family, pair) come from the journals").
- Purpose: sibling comparison on the same days, family curves, pair and session tables. Feeds E1 and the family-tree page. Ideas: W081, W043, W134.

**I7. Analyst notes into variant proposals.** Seed-expanded: S-ANL ("it is not just as a result of the growth from QMX, but the agents would have already seen this also", T2:325).
- Purpose: when a System 2 variant is proposed, attach the unit analysts' "why" notes and the market calls behind it. Agents: writer. Writes: proposal card sections. Ideas: W082, W132.

### Family J. Agent proof

**J1. Calibration board.** Seed-expanded: S-ANL ("We need them to be able to prove what they are producing in terms of analysis.", T2:385).
- Purpose: per agent, desk and model, a calibration score over scored calls, with the number of calls behind it. Agents: none. Reads: forecast ledger. Ideas: W090.

**J2. Planted-fake drill.** Seed-expanded: KB F2 and option 9.
- Purpose: periodically feed an analyst a shuffled day or a mislabeled instrument; it must flag it. Agents: the analyst under test. Ideas: W093.

**J3. Failure-mode replay study.** Seed-expanded: S-ANL ("We also need to know in which ways they can be wrong before we define the tools.", T2:385); KB "What would separate them".
- Purpose: replay recorded days through two analyst setups (with and without receipts and typed claims) and count failure modes F1 to F15 by script. Decides which proof tools matter first. A study template, run once and rerun on new models. Ideas: W097.

**J4. Recompute hook.** Seed-expanded: KB option 4.
- Purpose: a grader that reruns every cited receipt and fails the claim when the output differs. Shared by H, I and F families. Ideas: W091.

### Family K. Housekeeping, cost and meta

**K1. Crystallise sweep.** Seed-expanded: `cry`; R19 July razor ("anything a deterministic script/hook/plugin can do is NOT an agent").
- Purpose: monthly, find agent steps across templates whose replays agree and offer to replace them with scripts. Today `cry` handles labelling steps only (README). Ideas: W123.

**K2. Template health.** New.
- Purpose: treat templates like units: each has a journal of runs, finds, cost and a decay check ("does this template still find anything?"). Ideas: W150, W128.

**K3. Morning proposals card.** Seed-expanded: S-JDG; `morning-digest`; `pp`.
- Purpose: one card listing proposals awaiting his click, ranked by evidence, each with receipts and a cost line. Maximum per day is a number (default to set, Q20). Extends: `morning-digest`, `pp`. Ideas: W132, W133.

**K4. Graveyard tour.** Seed-expanded: R19 §8 Coroner.
- Purpose: weekly, the copilot walks him through three dead units and their causes. Ideas: W145.

**K5. Article to template.** Seed-expanded: S-WF ("there are so many ideas there for agentic workflows and non-agentic, depending", T2:1148).
- Purpose: an agent reads an article or a Hermes session and proposes a new template card; `build-workflow` turns an accepted card into a tested draft (R18 §1.6). Ideas: W149, W151.

**K6. Ecosystem page data.** New.
- Purpose: which template feeds which, last run, next trigger, cost per week. Ideas: W121.

**Map size: 57 candidate templates** (A 7, B 4, C 6, D 2, E 5, F 5, G 4, H 7, I 7, J 4, K 6). Of these, 53 are Seed-expanded and 4 are New (B3, F5, K2, K6). New ideas inside seed-expanded blocks are marked in the memlog (for example W019 inside B1's family). Counted by hand from the blocks above.

---

## 3. Skills, hooks and scripts the map needs

| Piece | Kind | Used by | Exists? |
| --- | --- | --- | --- |
| Unit-building skill (QML verbs, card format, outside-QML tagging) | skill (plugin file or Library skill) | B1, B2, E2, G1, G2 | No skill for QML exists (R42 §7, CHECKED) |
| Judging skill (explains a verdict grid) | skill | C1, K3 | No |
| Market-reading skill (data toolset, landmarks, receipts) | skill | H1 to H7 | No |
| Unit-reading skill (journals) | skill | I1 to I7 | No; no journal read path |
| Source-reading skill (contribution table, eight-part checklist, timestamps) | skill | A1, A3, A5, `a` | Partly in `a`'s prompts (`prompts/extract.md`, not read in full) |
| Completeness, alignment, receipts, landmark, recompute, fake-pass, sealed-window graders | grader nodes (deterministic) | B, C, F, H, I, J | Pattern exists (`render_and_grade`, quotes and citation graders) |
| Try ledger, holdout ledger, verdict grid, lineage writer, router of verdicts | shared scripts under `_shared/` | C1, D1, E, F, G | Partly: `overfit-gates` shared; `lineage.py` copied seven times |
| Units and journals catalog row | tool row | H, I, C4 | Missing (R42 §1.7) |
| Holdout or window through a tool call | tool fix | H, I | Missing (PR 207 departure, R42 §1.7) |
| Trade-closed, N-trades, plateau, dead-end-count, publish event sources | Library landings | D1, D2, F3, I1, I3 | Event trigger exists; these landings do not (except whatever PR 234 adds for host jobs) |
| His own Claude hooks for engine agent steps | settings | all agent steps | Merged into chat launches (`HAR/home.py:449-474`); reaching engine agent steps is INFERRED (R42 §7) |
| Forecast ledger, death certificate, verdict grid, proposal card | Library kinds | H1, F1, C1, K3 | None exists as a kind (INFERRED from R42 §6.1 list) |

---

## 4. Questions

Tags: `research` (a source or a run can answer it), `operator` (his call), `lead` (settle in planning and report in one line), `fog` (the seed is unclear; needs his words or a sketch). Questions already asked or answered elsewhere are noted so nobody re-asks.

**Research (18)**
- Q01 research: Do his Claude hooks in `settings.toml` reach engine agent steps? (R42 §7, INFERRED)
- Q02 research: Does the `memory` toolset read and write durable rows today, and does a template's declared memory scope do anything at run time? (no template uses the toolset, R42 §1.3)
- Q03 research: Can an event trigger fire on his publish of a draft, and can its filter tell his click from a run's landing?
- Q04 research: How do trading desks structure daily and weekly reviews for 24/7 crypto against session-bound FX?
- Q05 research: How do forecasting tournaments score calibrated calls, and how many calls before a record means anything?
- Q06 research: Which of F1 to F15 appear when cheap models analyse a recorded day? (J3 answers it)
- Q07 research: Are vision models reliable on chart images, and does a synthetic-chart benchmark separate them? (R40 #28)
- Q08 research: How do StrategyQuant and Build Alpha users separate "same strategy on another market" from "new strategy"?
- Q09 research: How well do cheap models build a QML unit from a complete card, and where do they fail?
- Q10 research: What would `cry` need to crystallise analysis steps, not only labels?
- Q11 research: Which events will the node journal emit once units run (trade closed, signal skipped, blocked)?
- Q12 research: How far do an agent's independent labels of a day agree with the MIS labels?
- Q13 research: Does the engine memo make an identical rerun cost no model call?
- Q14 research: At QMX trade counts, can a context search on failed rules be told apart from luck with one sealed window?
- Q15 research: What do alpha factories count as a try, and how do they treat expansion?
- Q16 research: How do desks split a trade's result into signal, execution and cost (transaction cost analysis practice)?
- Q17 research: Which Hermes experiment templates (test manifests, run results, experiment ledger, R40 #8) survive on disk to import?
- Q18 research: Does the engine pause at the usage limit and resume a long overnight loop cleanly? (`l4` README says the engine pauses; not checked)

**Operator (11)**
- Q19 operator: Should cheap models build by default, given the shipped setting makes the builder strong?
- Q20 operator: How many proposals a day on his morning card, at most? (a number; default to name)
- Q21 operator: Copilot chats mined for ideas automatically, or only when he says "save this"?
- Q22 operator: Is a sourceless generator branch wanted beside sourced ideas, given "no vibe trading" (STATE)?
- Q23 operator: Build now, document now, or the Lab first? (§5)
- Q24 operator: Should the fail branch exist at all? Already asked by the lead on 28 Oct (T1:1137, T1:1161); seeds.md keeps it as a seed. Check his answer before asking again.
- Q25 operator: Should market calls influence anything (router direction, a shortlist) or stay advisory until a calibration record exists?
- Q26 operator: Is "invert" acceptable as a move, given costs bite both ways?
- Q27 operator: Desks by style or by market?
- Q28 operator: Store his dictations as Library sources?
- Q29 operator: Does he want a weekly graveyard tour?

**Lead (27)**
- Q30 lead: One shared judge subworkflow, or the same scripts copied per template (today's pattern)?
- Q31 lead: Does the try ledger live in a family record in the Library or in the engine ledger?
- Q32 lead: Does `d4`'s label table (instrument and timeframe = `variant_of`; structural = `derived_from`) carry over to units?
- Q33 lead: Which candidates extend shipped templates with `extends` patches, and which are new definitions?
- Q34 lead: How does a template read a unit before the unit kind has fields?
- Q35 lead: Forecast ledger as a new kind, a trade-like record, or memory rows?
- Q36 lead: Loop defaults in shipped templates (`d3` 3 generations, `l4` 6 revolutions or 200 trials, `rev` 3, `d4` 12 variants and 4 builders): keep, expose in the UI, or drop, given "nothing capped"?
- Q37 lead: Does blind building remove the backtest toolset from the builder, or only hide result files?
- Q38 lead: Death certificate by a script classifier, an agent with a fixed list, or both?
- Q39 lead: How do seven `lineage.py` copies become one?
- Q40 lead: How does the conveyor stop a child's landing from re-firing its own family's build?
- Q41 lead: Default placement per template: which stay on This PC, which spill?
- Q42 lead: Do analyst families share one data read per session?
- Q43 lead: Builder tier per node or per template input?
- Q44 lead: Are graders presented to him as the judging skill's hooks, and how is that explained in plain words?
- Q45 lead: Can `rs6`'s `real-library` need be dropped now that PR 216 lets scripts read the real Library?
- Q46 lead: Copilot-chat intake on the partial `session` trigger, or a cron over finished sessions?
- Q47 lead: How does an agent step pass a landmark window to the data door?
- Q48 lead: Which candidates need no model (C2, C3, D1, E1, E4, I2, I5, J1, A7) and can ship first once their doors exist?
- Q49 lead: How are tries counted for backtests he or the copilot runs by hand, outside workflows?
- Q50 lead: How is "where it broke" stored so the expansion card and the unit page share it?
- Q51 lead: Which first: the units and journals catalog row, or the holdout through tool calls?
- Q52 lead: The `library` node kind: executor or deletion? (R42 Q8)
- Q53 lead: One market-analysis template with a clock table input, or one per market family?
- Q54 lead: Proposal card: reuse `pp`'s shape or a new kind?
- Q55 lead: How is cost shown per run on each card (tokens, calls, minutes)?
- Q56 lead: Does the MQL5 article corpus become an A4 intake run now (STATE item 9)?

**Fog (10)**
- Q57 fog: What exactly must agent memory hold across runs: dead ends, causes, his tastes, market notes? ("this is why we needed agent memory, dude", T1:513)
- Q58 fog: Where is the line between why a unit traded and what the market did? (his split into two families, T2:385)
- Q59 fog: When is a cheap loop "stuck" enough to call a strong model?
- Q60 fog: What does "impeccable placement" look like as an output: a universe, a condition fingerprint, a session table? ("It gives us almost an impeccable placement.", T1:513)
- Q61 fog: What counts as "a context" in the fail branch?
- Q62 fog: Does market analysis replicate the MIS or challenge it? (T2:325 says "replicating")
- Q63 fog: What is a template's "done" for him: a card, a unit on paper, a note?
- Q64 fog: Do specialist desks belong in workflows or mini apps? ("We can either build it now or propose building it with as a mini app", T2:325)
- Q65 fog: One judging skill, or a family (historical, paper, analyst-claim)?
- Q66 fog: With no end of day, what is "that day's data" for a review?

**Counts: 66 questions. research 18, operator 11, lead 27, fog 10.**

---

## 5. Build now or write now: the options

His two options are seeds (S-DLV), so the field below widens them. Each row is judged on the three standing-order tests: hard cases, maintenance and debugging, and whether it explains in a few plain sentences. All INFERRED.

| # | Option | What happens | Hard cases | Maintain and debug | Explain to him | Main risk |
| --- | --- | --- | --- | --- | --- | --- |
| O1 | Build all in the coding phase | Templates are coded once the doors exist | Strong: real runs show real failures | Strong: definitions validate at install | "We build them when QMB and the node can run them" | Late: analyst families wait on the node |
| O2 | Write detailed cards now, code later | Each template written as a card (purpose, trigger, steps, roles, graders, reads, writes) | Weak: nothing runs against real data | Weak: cards validate against nothing and drift as doors are redesigned (P12, Morrow) | "We write the recipe now and cook later" | Rot; the 23 drafts already cite doors redesigned since |
| O3 | The Lab's first job | The Lab builds templates from cards as its first workload | Medium: depends on the Lab's maturity | Medium | "The Lab learns by building its own tools" | The Lab is a workspace only today; its agent rows are closed (`CTL/catalog.py:586-674`, R18 §1.4) |
| O4 | Hybrid: build the structure, write the rest | Code the shared pieces now (judge block, graders, try and holdout ledgers, lineage writer, event wiring, proposal card); write the templates as cards | Strong where reuse is highest | Strong for the core; cards for leaves | "We build the parts every recipe uses, and write the recipes" | Choosing the core wrong |
| O5 | Real drafts now | Write `definition.json` drafts with `meta.needs` naming the missing doors, the shipped pattern for 23 templates | Medium | Strong: they validate at install and say what they wait for (`model.py:193-205`, R18 §1.5) | "They sit ready and say what they wait for" | More drafts that never run |
| O6 | Copilot first, then crystallise | Run each flow by hand with the copilot; `build-workflow` turns a settled run into a draft; `cry` replaces settled agent steps | Strong: learns from real runs | Medium | "We do it by hand first, then make it automatic" | Depends on his time |
| O7 | No-model templates first | Code the templates that need no model (expansion, replay, decay, scorecard, negative control) first; agent ones later | Strong for the measured parts | Strong: scripts are easy to debug | "Free parts first" | Analyst seeds wait longest |

Combinations seen in the party and brainstorm (not ranked): O4 + O5 (structure built, leaves as validated drafts); O7 + O6 (scripts first, agent steps learned by hand); O2 feeding O3 (cards become the Lab's input). His words leave room for any of them: "We either build them during the coding phase" (T2:1148) and "the lab, that's one of the first things the lab maybe might do" (T2:1148).

---

## 6. Cross-map

### 6.1 Candidates against his seeds

| Seed | Candidates that grow it |
| --- | --- |
| S-WF (Hermes and WF1/WF2) | A3, A4, A5, B1, C2, F1, F3, G3, I3, I6, K5 |
| S-FUN (funnel with branches, cheap bulk, memory) | A1, A2, A6, B1, D1, E1, E2, E3, F1, F2, G1, G2 |
| S-ANL (market and unit analysts, proof) | H1 to H7, I1 to I7, J1 to J4 |
| S-JDG (judging as a skill) | C1 to C6, D2, K3 |
| S-DLV (delivery) | §5; K5 (article to template); K2 (template health) |

### 6.2 Candidates against missing doors

| Door or piece | Status (R42, CHECKED) | Candidates waiting |
| --- | --- | --- |
| qmb-door (a real backtest runner) | PR 204 runner places no trades | B1, C1, C2, C3, D1 stages, E1 to E5, F1, F2, G1 to G4, I2 |
| trading-node and journals | No trading-server path; no journal kind | C4, F4, I1, I3, I5, H4 |
| Units and journals catalog row | Missing | H6, I1 to I7 |
| Data door open and window via tool call | PR 207 opens the door; window via tool missing | H1 to H7 |
| Event sources (trade closed, plateau, publish, dead-end count) | Event trigger shipped; these landings missing | D1, D2, F3, I1, I3 |
| Skills (unit, judging, market, unit-reading) | None written | B1, C1, H, I |
| New Library kinds (forecast ledger, verdict grid, death certificate, proposal card) | None | C1, F1, H1, J1, K3 |
| Nothing missing | — | A2, A7, K1, K4, K6 (and A1 if transcripts are readable) |

### 6.3 How the pieces combine

| From | Relation | To | Why (INFERRED) |
| --- | --- | --- | --- |
| C1 judge block | enables | B1, D1, E1, F2, G1 | One verdict grid every branch routes on |
| D1 conveyor | depends on | C1, event sources | Routing needs a grid and a landing to fire on |
| F1 death certificate | enables | F2, F3, K4, G1 | Causes decide which branch is worth trying |
| H1 forecast ledger | enables | J1, I1, H3 | Calls are scored once and read by both families |
| I1 review | depends on | H1 | "Why it traded" reads "what the market did" |
| E1 expansion | enables | E4, H5, I6 | Where it held and broke is the universe and the tags |
| G1 rewrite | conflicts with | his cheap-builder seed if builder stays strong | The escalation only means something if the base tier is cheap |
| C1 graders as hooks | conflicts with | "hooks" read as Claude hooks | Workflows can't declare Claude hooks (R42 §7) |
| Shipped loop defaults | conflicts with | standing order 9 (nothing capped) | A default no one edits acts as a cap (P11) |
| A1 copilot intake | conflicts with | KB F11 (sources that steer agents) | His enthusiasm is idea-evidence, not market-evidence |
| H3 desks | conflicts with | KB F7, F9 | A style desk finds its own style everywhere; scoring is the check |
| K1 crystallise | enables | lower cost for H and I | Agent first, script later |
| O4 hybrid | depends on | C1, D1, §3 shared scripts | The structure it builds first is this list |

### 6.4 Numbers named (starting defaults to edit, never settled)

| Number | Starting default | Where it comes from |
| --- | --- | --- |
| Plateau | 30 trials without a better validated score | `l4` README (CHECKED) |
| Overnight loop stop | 6 revolutions, 2 without gain, 200 trials | `l4` README (CHECKED) |
| Generations in `d3` | 3, 2 without progress | `d3` definition (CHECKED) |
| Variants and builders in `d4` | 12 variants, 4 built | `d4` README (CHECKED) |
| Judge gates | 100 trades, WFE 0.5, MC 5th pct > 0, 1.5x costs, DSR 0.95 | `b` README (CHECKED) |
| Dead ends that wake F3 | 5 new | `rs6` README (CHECKED) |
| Trades per unit-review event | every 10 closed trades | `dc` README, "left out" (CHECKED) |
| Instruments in the challenge | 3 (home, analogue, adversarial) | R39 K1 |
| Session clocks | four FX closes plus a rolling crypto clock | INFERRED, to set |
| Calls before a calibration score shows | 100 | New, INFERRED |
| Proposals on his morning card | 5 | New, INFERRED |
| Expansion stop | try-corrected expected value under a bar | New, value to set |

---

## 7. Parked

Out of this field by the brief, by a ruling, or because they need a different session. Each one stays a seed.

- Exit maths and sizing maths inside the judge, including the old special sizing (W035 keeps only the idea of showing results two ways). Risk-and-sizing session.
- Routers that switch units on or off (STATE: the router does not switch). H-family calls stay advisory (Q25).
- MIS design itself. H4 only compares labels.
- Automatic promotion of anything to live (standing order 7). Every template ends on a card.
- Agents in the trade path (R11 C7). Analysts write dated data, never live decisions.
- 512-agent simulations, fine-tuning, RL units (R11 C6; QF B086).
- Building `human_gate` (engine work, planned only).
- Driving the Gemini web app and NotebookLM by computer use for intake (R40 #29; R39 N4). Needs its own study.
- n8n as an outside intake (R39 N2, placed outside the library by him).
- Obsidian or Open Knowledge as the knowledge store (R40 #24, #25).
- A tournament leaderboard as anything more than a view (W144).
- Mirror units built to trade against each unit (W148). Needs QMB first.

---

## 8. Counts and how this was run

| What | Count |
| --- | --- |
| Candidate templates | 57 in 11 families (A 7, B 4, C 6, D 2, E 5, F 5, G 4, H 7, I 7, J 4, K 6) |
| Seed-expanded / New | 53 / 4 |
| Brainstorm ideas | 152 (W001 to W152), 6 insights |
| Party rounds | 12, with 12 clashes left open |
| Questions | 66: research 18, operator 11, lead 27, fog 10 |
| Delivery options | 7 |
| Operator quotes checked | 64, 0 missing |

**How the skills ran.** Party mode in session mode, non-interactive, inline cast of twelve. The four limited voices spoke only from their sources (operator quotes, R42 plus TIP files, R19, R39). Brainstorming ran headless in "ideate for me" with twenty techniques, one batch per domain, shifting about every ten ideas. The memlog was written with `memlog.py` (init, 174 appends, status set); entries were appended per technique batch from a prepared list. No subagents. No commits.

**Not verified.**
- No template was run. Template behaviour is read from definitions and READMEs at TIP.
- Whether event filters can see his publish click (Q03) and whether his Claude hooks reach engine agent steps (Q01).
- The `a` template's prompts were listed, not read.
- Line numbers in `T2` follow `grep -n`; Python's line split runs one line ahead of `grep -n` somewhere between lines 385 and 1125 of that file (a line break counted differently). The quote check allowed a two-line window.
