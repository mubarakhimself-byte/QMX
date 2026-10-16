> STATUS 2026-10-16 (rubric walk): KEEP-AS-SOURCE. See 27-rubric-walk.md. Rulings in 26 win.

# 08 — The strategy funnel: where it came from and what it should be today

Research date: 2026-10-16. Read-only study. Nothing was changed except adding this file.

The funnel takes "garbage" in (videos, podcasts, hints, papers, TradingView scripts and threads, notes) and pushes a few strategies out to paper/demo trading. This file traces it back to the old WF1 and WF2, reads the Strats/Stats library that it is meant to fill, and lays out a stage-by-stage design for today.

## How to read the citations

- `disc:` = `C:\Users\Mubarak\Documents\Claude\QMX-discussion\` (old QMX version; history, not the plan).
- `gpt:NNNN` = line in `disc:07-Source-Material/gpt-trading-algorithm-research.md` (the operator's long dictated GPT conversation, the origin of WF1/WF2).
- `layout:NNN` = line in `C:\Users\Mubarak\Desktop\# Resolve QMX folder layout.txt` (the transcript).
- `stats:` = `C:\Users\Mubarak\Desktop\Stats\` (the real library). `strats:` = `C:\Users\Mubarak\Desktop\strats\`.
- `skill:` = `C:\Users\Mubarak\.agents\skills\strats-video-populate\` (the population skill the transcript produced).
- `main:` = `C:\Users\Mubarak\Desktop\QMX` on `main`. `plan:` = `D:\QMX-worktrees\agent-system\tracker\`.
- `05` and `06` = the sibling files in this folder.

---

## 1. WF1 and WF2 as they were

There are two layers of history. First, the operator's own words (spring 2026). Second, the formal LangGraph specs written later from those words. They do not fully agree; the operator's version is the funnel he remembers.

### 1a. In the operator's own words (the origin)

From `gpt:1400` (dictated; "one best data" is a dictation slip for "unbiased data", confirmed by the GPT summary at `gpt:18531`):

**WF1 = generation and evaluation. It ends at reports.**

1. Sources: "most of such [ideas] come from youtube or articles".
2. A process turns the source into **unbiased data** (a neutral, word-for-word capture).
3. An agent writes a **TRD** (technical requirements document) for the bot archetype.
4. Code is written through the QuantMind library, in two forms:
   - **vanilla**: "the logic as it comes from the source", with risk and sizing stripped out, because the system's own risk and sizing layer handles that.
   - **spiced**: vanilla plus ideas from cTrader articles. Later ruled **optional**; most bots may have no spiced version (`gpt` snippet "spiced variants are optional").
5. Each version goes through: standard backtest → report; Monte Carlo → report; walk-forward (out-of-sample) → report.
6. "Those are all stored. Now that's where workflow one ends."

**WF2 = improvement ("the annealing workflow"). It ends at paper trading.**

1. Agents pick up existing bots and their WF1 reports.
2. They rewrite the bots to make them better (for example, adding indicators from the library).
3. Every rewrite goes back through the same backtest pipeline and is filtered again. "Some are killed off and some remain."
4. Survivors go to paper trading. "WF1 doesn't handle paper trading ... WF2 is the one that handles paper trading."
5. The point: "we are technically improving and also making sure that we don't overfit".

GPT's summary of the same design (`gpt:18531-18700`) adds the key rule: **Monte Carlo and walk-forward are diagnostics, not variant generators.** WF2 is a loop: interpret reports → list strengths, weaknesses and regime sensitivity → form hypotheses about *why* → make 3-4 **structurally different** children (trend-optimised, volatility-adaptive, session-filtered, order-flow) → send each back through WF1's tests → repeat. Expected scale: "WF1 producing around 80 strategies" at a time.

Roles (old five-department model, `disc:bmad-docs/planning-artifacts/agentic-system-context-gpt-extract.md:20-34`): **Research** turns video into the TRD; **Development** writes code in WF1 and owns WF2; **Trading** and **Portfolio** validate later; a Floor Manager runs the workflows.

### 1b. In the formal specs (the later LangGraph design)

The specs (`disc:02-Components/14-agentic-system/09-wf1-variant-generation-pipeline.md`, `11-wf2-variant-improvement.md`, `disc:bmad-docs/planning-artifacts/workflows-architecture.md:95-390`) kept the split but **moved the source intake out of WF1**. WF1 starts from an "opportunity signal", not a video.

**WF1 stages** (`09-wf1...md`, "Hidden graph pipeline"):

| Stage | What | Who |
|---|---|---|
| S1 | Opportunity intake | Trading/Portfolio agent |
| S2 | Archetype selection | Trading agent |
| S3 | Feature-stack assembly from the indicator catalogue | Development agent |
| S4 | BotSpec draft | Development agent |
| S5 | Composition validation (loops back to S4 on fail) | **Script** (deterministic validator) |
| S6 | Portfolio risk review (loops back to S4) | Portfolio agent |
| S7/S7W | Backtest dispatch and wait | Backtest service |
| S8 | Report enrichment: session, overlap, regime, spread/cost labels | Enrichment agent |
| S9 | Evidence pack + handoff token to WF2 | Packaging step |

Gate rule: **WF1 never registers a bot** (`09-wf1...md`, "No registration writes occur in this workflow"; ruling D6 at `disc:bmad-docs/brainstorming/brainstorming-session-2026-04-28-125147.md:164`).

**WF2 stages** (`11-wf2...md`): A intake (from WF1, from WF3 decay rehab, or from an operator request) → B diagnosis into weakness buckets → C reviewer mail loop (Development + Portfolio risk) → D bounded hypotheses → E mutation plan → F child variants → G retest through WF1's contract → H scenario stress probe (fail = dropped) → I.0 **first registry write** (script, exactly once) → I.1 paper window wait and review (pass / fail / re-paper) → I.2 **operator-only live gate**.

WF3 (pool cleaning, `12-wf3-pool-cleaning.md`) ran a mini-WF2 on decaying live bots. Out of scope here.

### 1c. Where the video intake lived

The front of the funnel became separate tools:

- **Video ingest tool** (`disc:02-Components/14-agentic-system/08-video-ingest-tool.md`): intake → transcription (pluggable provider) → distillation (agent extracts claims, indicator refs, strategy patterns, regimes, timestamped citations) → tagging → review queue (auto-approve if high confidence) → wiki, mail to Development, opinion nodes. It "does not start or control WF1/WF2/WF3 directly".
- **Wiki ingestion pipeline** (`disc:02-Components/13-quantmindwiki.md:190-218`): fetch → preprocess (transcript, PDF, web) → research agent → "actionable strategy?" (no = archive log) → **TRD distillation** → draft → **human review** → live vault. Gates: under 200 words held, TRD schema check, duplicate check (similarity > 0.92), source citation required.

### 1d. What was automated

Planned as fully autonomous (`disc:bmad-docs/planning-artifacts/prd.md:469`): WF1 and WF2 end-to-end agentic, WF3 deterministic. Human gates: wiki draft approval, and the paper → live promotion (I.2). Nothing of this shipped as working code; the PRD's demo targets were "WF1 produces ≥1 BotSpec", "WF2 mutates ≥1 variant" (`prd.md:412-413`). Today the backlog row B10 "WF1/WF2 rework" says "Strategy-from-anything workflows ... He handles it" (`plan:qma-v2/BACKLOG.md:64`).

### 1e. Lessons from the history

1. The operator's WF1 **starts at the source**; the formal spec dropped that. Today's funnel should put the source back at the front.
2. **Vanilla first, spiced optional.** Source logic is kept faithful; house risk and sizing are not the strategy's job.
3. **Tests diagnose; agents create.** Monte Carlo and walk-forward kill or explain; they never invent variants.
4. **Registration happens late**, only for survivors.
5. **Paper → live is always the operator's click.**

---

## 2. The Strats folder layout

### 2a. What the transcript actually settled

The transcript is titled "Resolve QMX folder layout", but the layout had already been built by the time it ran. The agent found "the layout phase is complete" (`layout:61`, `layout:75`). The transcript then settled **how the folder gets filled**. Final decisions (the back-and-forth removed):

1. **One source ≠ one strategy.** A source can yield zero, one or several strategies, fragments, dictionary entries, knowledge notes, or "no usable strategy found" (`layout:100-152`, confirmed `layout:262`).
2. **Neutral evidence first.** Metadata plus a word-for-word timestamped transcript, with no interpretation, before any analysis (`layout:193`, `layout:256`).
3. **Transcript and visuals together.** Long videos: map the transcript, cut it into meaningful sections, then do focused visual passes on the windows that matter (charts, settings, timeframes, entries, stops). `watch` is used for those passes; it is not the backbone, because its best range is under 10 minutes (`layout:233`, `layout:264`, `layout:470-481`).
4. **Source-faithful vs inferred stays separate.** Missing information stays missing. Incomplete strategies may branch into labelled hypotheses; they are never quietly completed (`layout:259`, `layout:262`).
5. **Expansion is explicit.** Scopes: single item, list, playlist, full channel, saved collection, discovery-only. One good video never authorises a whole channel; the operator curates (`layout:494`, `layout:545-554`; `skill:references/workflow.md` "Scope modes").
6. **Futures sources are captured as futures.** A Forex or crypto-spot version is a separately labelled transfer hypothesis (`layout:556`).
7. **The A-I DNA is a minimum, not a prison.** New optional fields may be added (`layout:556`).
8. **Six roles plus one writer:** Population Lead, Source Librarian, Video Researcher, Knowledge Curator, Strategy Architect, Evidence Auditor; **Canonical Writer** is the only role that assigns IDs and writes library files (`layout:1000-1010`; `skill:references/workflow.md` "Role roster").
9. **Work ledger per run**, crash-safe, so a fresh agent resumes from files, not chat memory (`layout:568`, `layout:914`).
10. **Harness-neutral.** The workflow belongs to the library, not to Hermes, Grok Bot or QMA; it ships as a shared skill (`layout:498`, `layout:568`).
11. **Books are out.** QMX ingests books itself (`layout:193`).
12. **Autonomous acceptance after audit.** The operator is needed only for logins, deletion or overwrite, publishing, meaning-changing ambiguity, and changes to locked contracts or existing dictionary entries (`layout:170`; recommended, not explicitly re-confirmed later).

The result is the skill `skill:SKILL.md`, which has 26 passing self-tests and was never run on real content (`layout:916-922`). Its item state machine is: discovered → acquired → normalized → researched → proposed → audited → committed | no_output | blocked. It has six gates: inventory, acquisition, research, proposal, audit, commit (`skill:references/workflow.md` "State machine", "Gates").

### 2b. The layout itself (from the library's own files)

The settled tree is in `stats:STRATS-BUILD-STATE.md` and `stats:README.md`:

```
Stats/
├── dictionary/      239 seed entries in family files (12 fields each); append-only, never rewrite
├── schema/          strategy-dna.md (A-I lock), ids.md, graph.yaml.md, strats.sql
├── backend/         import / export_catalog / validate / rebuild; strats.sqlite is derived
├── strategies/      _template/ + STRAT-000001 (layout demo, class entry_hypothesis)
│   └── STRAT-NNNNNN-slug/  identity.md, evidence/, specification/, logic/graph.yaml, review/, lineage/
├── sources/items/   SRC-NNNNNN-slug/ manifest, transcript, notes; indexes/ (channels, creators, playlists...)
├── knowledge/       mini knowledge bases (sessions, liquidity, prop-firms overlay, creator terminology...)
├── lineage/         cross-package pointers: variants, composites, families, relationships
└── catalog/         one-line indexes only (strategies.md, sources.md, dictionary.md generated)
```

Strategy classes (`stats:schema/strategy-dna.md`, section A): `complete`, `entry_hypothesis` (exits missing), `fragment`, `descriptive_pattern`, `composite`. Rule F: **do not invent exits**. Exit slots are labelled `source_defined`, `external_policy`, `deliberately_open` or `unresolved`. Markets are Forex and crypto spot; horizons are scalp, intraday and swing. Prop-firm rules are an overlay, not a third library.

### 2c. How it matches the real folders today

| Folder | State |
|---|---|
| `Desktop\Stats` | **The real library.** Matches the build state exactly: 239 dictionary entries, 1 demo strategy, 0 sources, empty knowledge areas, empty lineage. **Population has not started** (`stats:README.md` "Pause before populate"). The skill's preflight passed against it (`layout:701`). |
| `Desktop\strats` | **Debris, not a library.** Empty directories named `-C`, `-xzf`, `tar`, `strats-tmp`, and `strats-scaffold.tgz` (a folder, not an archive) are left over from a mis-typed `tar -xzf ... -C ...` command. The only real file is `resume-strats-ground-state-work-20260827.json`, a Hermes session export (97 KB). |

One clash to note: QMX's docs on `main` ban "STRATS" as product language and call this tree the **seed corpus**. Hypotheses are not Library objects until registered as a CT-33 bot (`main:docs/glossary.md:935`, `:1246-1248`; `main:docs/decisions/ADR-0023-qml-research-expansion.md` AD-1, AD-2, AD-18). The operator, by contrast, says "The Library's name is **Strats**" (`plan:qma-v2/BACKLOG.md:91`, row B8, handled in its own session). See question 2.

---

## 3. The funnel for today, stage by stage

The design below joins three things: the operator's old WF1 → WF2, the population skill's gates, and the Lab and validation stages in `06` section 5. "Script" means deterministic code with no model. "Model" means one bounded call. "Agent" means a model with tools that loops. "Human" means the operator.

```
drop anything ─► 1 intake ─► 2 capture ─► 3 triage ─► 4 understand ─► 5 extract cards ─► 6 audit
   ─► 7 Library entry ─► 8 Lab build ─► 9 backtest ─► 10 robustness gates ─┬─► 12 paper/demo (his click)
                                                   ▲                      │
                                                   └── 11 improve (old WF2) ◄┘  (dead ends kept)
```

Stages 1-7 are the old WF1 front end (the population skill). Stages 8-10 are WF1's back end (code, backtest, Monte Carlo, walk-forward). Stage 11 is WF2. Stage 12 is WF2's paper step.

### Stage 1 — Intake

- **What:** the operator drops a URL, a list, a playlist, a channel, a saved collection, a PDF, a TradingView link, a pasted note or a one-line hint. Each input becomes an inventory row with a scope mode, and expansion follows the rules in 2a.5.
- **Who:** **script** (URL normalising, `yt-dlp` listing, de-duplication, hashing). Human only to approve full-channel or account expansion.
- **Kept:** every item, including duplicates (merged with all their provenance) and skipped items with a reason (`skill:references/workflow.md` "Inventory gate").
- **Unclear:** how logged-in sources (Instagram saves, X bookmarks) are reached inside QMX. The transcript used Grok Bot or Hermes browser profiles; QMA v2 has SDK computer use (memory: harness rulings). TradingView pages may need a browser too.

### Stage 2 — Neutral capture ("unbiased data")

- **What:** video gets native captions, with Whisper as the fallback, plus metadata and chapters; frames are not taken yet. A paper becomes PDF → Markdown. A TradingView script gets its Pine source, inputs, description, and the comment thread saved as separate text. Notes and hints are stored as written.
- **Who:** **script**. The `watch` skill already does captions-first with a Whisper fallback and can run in `transcript` mode with no frames (`C:\Users\Mubarak\.agents\skills\watch\SKILL.md`, "Recommended limits", `--detail transcript`). It needs a Groq or OpenAI key for Whisper; with no key, uncaptioned videos fail (same file, Step 0).
- **Kept:** the raw transcript, immutable and labelled native/automatic/ASR/partial; known gaps are listed (`skill:references/workflow.md` "Acquisition gate"). Large media stays in a cache outside the library (`layout:162`).
- **Unclear:** whether QMX stores media at all, or only locators and hashes. Whisper costs money per minute; that clashes with "no Anthropic API spend" only if the operator counts Whisper too.

### Stage 3 — Triage

- **What:** sort each item into one bucket:
  - **useless**: promo, chatter, a course pitch with no rules;
  - **hint**: an idea with no rules, for example "funding spikes predict reversals";
  - **component**: one reusable piece, such as a filter, an exit, an indicator or a session rule;
  - **full strategy**: entry logic present;
  - **knowledge**: market facts, terminology, prop-firm rules.

  One item can land in several buckets (2a.1). Long videos also get a time map, for example "strategy 01:20-08:45, promo 08:46-11:00".
- **Who:** **script** pre-filter first (duration, keyword hits such as "entry", "stop", "timeframe", near-duplicate transcripts). Then one **model** call per item on the transcript only, the cheapest model that works. No frames at this stage.
- **Kept:** every verdict with a one-line reason. Useless items stay as inventory rows marked `no_output` and are never deleted, so the same video is not processed twice.
- **Unclear:** whether the operator wants to review triage in bulk (a table he can flip), or trust it. The old wiki pipeline held items under 200 words for a human (`disc:02-Components/13-quantmindwiki.md:216`).

### Stage 4 — Understanding

- **What:** for strategy, component and hint items, build a whole-source map. Split the source into meaningful sections, extract atomic claims with exact locators (timestamp, page, line of Pine code), then run focused visual passes on the windows the transcript flags ("look at this candle"). Reconcile across sections, so a rule started in hour one and finished in hour five stays one rule (`layout:470-479`; `stats:STRATS-GROUND-STATE.md` section 5.5).
- **Who:** an **agent** (the Video Researcher role) fans out section workers, each one a **model** call. Visual passes use `watch --start/--end` or `--timestamps`, which are built for exactly this (`watch\SKILL.md`, flags). For papers, the agent maps sections. For TradingView, a **script** parses the Pine inputs and the logic is read by a model.
- **Kept:** the claim list, each claim tagged source-stated, visual, inferred or unresolved (`stats:STRATS-GROUND-STATE.md` section 4.6), plus a coverage map showing which minutes were never looked at.
- **Unclear:** how much visual work is affordable. Frames cost tokens, and Max 5x is the budget.

### Stage 5 — Extraction into cards

- **What:** turn claims into typed cards. A **strategy card** is a package with A-I DNA and one class from 2b. A **component card** is a dictionary entry (append-only) or a reusable piece. A **knowledge note** goes into a mini knowledge base. A **hint card** is a one-paragraph idea marked as a hint, which can later seed the Lab's grilling step (`06` stage 1-2). Futures sources stay futures, and any spot version is a labelled transfer hypothesis.
- **Who:** an **agent** (Strategy Architect, plus Knowledge Curator for knowledge notes). The A-I template and `validate.py` are the **script** check.
- **Kept:** the strategy card keeps its holes. Exits not given by the source stay `unresolved`, and the card stays `entry_hypothesis` (`stats:schema/strategy-dna.md`, F).
- **Unclear:** where component cards live in QMX. Today Stats has dictionary entries but no "component" class, and QMX's typed mechanism vocabulary is deferred (GAP-0085, `main:docs/decisions/ADR-0023...md` AD-16).

### Stage 6 — Independent audit

- **What:** a fresh context re-opens the original evidence windows, not the card text, and tries to disprove each card. Failed work goes back to the responsible role with a revision packet.
- **Who:** an **agent** on a different model family where possible, the same idea as the validator lens in `06` stage 5. **Human** only for the exceptions in 2a.12.
- **Kept:** accepted and rejected claims, each with a reason (`skill:references/workflow.md` "Audit gate").
- **Unclear:** under one Claude Max plan, the "different model family" may not exist. A fresh Claude context with a hostile brief may be the only option.

### Stage 7 — Library entry

- **What:** the Canonical Writer allocates `STRAT-`, `SRC-` and `kb-` IDs, writes the files, appends catalog lines and rebuilds the index. In QMX terms, this card is a **Stage 0 research hypothesis** with a `research_ref`. It is **not** a registry kind and not a Library object yet (`main:docs/decisions/ADR-0023...md` AD-1, AD-15, AD-21).
- **Who:** a **script** (one writer lease, atomic writes, `backend/validate.py`).
- **Kept:** everything audited, including `no_output` and `blocked` items with their reasons.
- **Unclear:** whether this stage writes into `Desktop\Stats` (seed corpus, read by QMX through a snapshot, DEC-0382) or into a QMX-owned `research_root`. B8 "Strats v2 as a git-style database" (`plan:qma-v2/BACKLOG.md:91`) may replace both.

### Stage 8 — Lab build

- **What:** pick a card and build a runnable bot. **Vanilla** is the source logic only; house risk and sizing come from the Book/BMS layer. **Spiced** is optional. Missing exits get a **house exit policy** labelled `external_policy`, which is never written back as source truth. The bot graduates through `graduate_to_governed` into a CT-33 bot definition (`main:docs/decisions/ADR-0023...md` AD-7, AD-17).
- **Who:** an **agent** writes the code (Lab copilot or a builder role). A **script** checks it: compile, `gate_registration`, composition validation (the old S5).
- **Kept:** a lineage edge from the card to each bot version, and both vanilla and spiced if spiced was built.
- **Unclear:** who picks which cards get built. With "~7,000 strategies" as the aspiration (`stats:STRATS-GROUND-STATE.md` section 4.8), building all of them is not possible. The Lab backend has no sweep, walk-forward or robustness tools for agents yet (`05` gap 8).

### Stage 9 — Backtest

- **What:** one ExperimentSpec per run: code ref, config, data snapshot, costs on, seed, lineage (`main:docs/contracts/ct-47-qma-experiment-spec.yaml`, purpose). Run on QMB.
- **Who:** a **script**. A model is not needed to run it.
- **Kept:** every run in the QMB ledger, including failures and refusals (`05` section 4, QMB ledger row).
- **Unclear:** the ExperimentSpec machinery is deleted in D3 with no replacement (`05` gap 14). Agents can only run pre-registered configs (`05` gap 8).

### Stage 10 — Robustness gates

- **What:** Monte Carlo (fragility), walk-forward (out-of-sample), an untouched holdout, cost stress, regime and session breakdown (the old S8 enrichment), and deflated Sharpe that counts every variant tried (multiple-testing honesty). Pass or fail is decided by numbers, not prose.
- **Who:** **script** for every gate. A **model** only reads the report afterwards to explain it or to feed stage 11. **Human** sets the thresholds once (his values, `06` stage 5 and 7).
- **Kept:** failed bots stay as **negative results** with the reason, the run ID and the variant count. This is the "dead ends" record. Nothing is deleted.
- **Unclear:** threshold values, and whether passing needs every gate or a scored mix.

### Stage 11 — Improve (the old WF2)

- **What:** diagnose the reports, form hypotheses about *why*, make a few **structurally different** children, and send them back to stage 9. Stop on a budget or a plateau. Lineage records parent → child and what changed.
- **Who:** an **agent** (diagnosis and code edits), a **script** (tests and gates), and **human** only for the budget.
- **Kept:** every child, including the dead ones, with its semantic difference from the parent.
- **Unclear:** the loop budget, and how to stop it from becoming curve-fitting. The fix is that deflated Sharpe counts all children, and the holdout is touched once.

### Stage 12 — Paper/demo (the confirmation step)

- **What:** survivors run on demo or paper for a set window. A trader-agent monitor and a zero-token limit cron watch them (`06` storyboard, steps 5-6). Outcomes are pass, fail or re-paper (old I.1).
- **Who:** **human** signs the promotion card into paper. A **script** runs paper and checks limits. Live is always the operator's click (old I.2, `06` stage 8).
- **Kept:** the paper journal, and the outcome next to the backtest evidence.
- **Unclear:** paper length, minimum trade count, and what counts as "matches the backtest". No paper read model exists yet (`05` gap 9).

### Who does what, in one table

| Stage | Script | Model | Agent | Human |
|---|---|---|---|---|
| 1 Intake | ● | | | channel approval |
| 2 Capture | ● | ASR fallback only | | |
| 3 Triage | pre-filter | ● one call per item | | optional bulk review |
| 4 Understand | Pine parsing, `watch` frames | section workers | ● reconciler | |
| 5 Extract cards | template check | | ● | |
| 6 Audit | coverage checks | | ● fresh context | exceptions only |
| 7 Library entry | ● writer | | | |
| 8 Lab build | compile, gates | | ● | picks what to build? |
| 9 Backtest | ● | | | |
| 10 Robustness | ● | explains report | | sets thresholds once |
| 11 Improve | tests | | ● | sets budget |
| 12 Paper | ● | | monitor | ● promotion click |

---

## 4. Open questions for the operator

Each question has a recommended answer. Saying "yes" accepts the recommendation.

1. **Is today's funnel one workflow, or two like WF1 + WF2?**
   Recommended: **two templates that hand off.** "Fill the Library" covers stages 1-7 and runs in big unattended batches. "Build and prove" covers stages 8-12 and runs per chosen card. This matches his old split and keeps the costly ingestion apart from the Lab.

2. **What is the Library called, and where does stage 7 write?** The docs ban "Strats" as product language (calling it the "seed corpus"), but he calls the Library Strats (B8).
   Recommended: **Strats is the name; his word beats the docs.** Stage 7 writes in the A-I shape in whatever store B8 settles on. Until then it writes into `Desktop\Stats`.

3. **Can the funnel accept cards into the Library without him?**
   Recommended: **yes, after the independent audit.** He is asked only for logins, overwrites or deletions, dictionary edits, and real meaning-changing ambiguity (the transcript's Q4).

4. **Is spiced still a thing?**
   Recommended: **yes, optional,** as a labelled child of vanilla. It is never built by default and never replaces vanilla.

5. **What happens when a strategy has no exits (most videos)?**
   Recommended: **test it with a house exit policy labelled `external_policy`.** The library card stays `entry_hypothesis`, and the source is never "corrected".

6. **Who chooses which cards go to the Lab?**
   Recommended: **a script ranks cards** (class `complete` first, then evidence strength, then market fit). **He approves a weekly short list** of about 5-10. Building all of them is not affordable.

7. **Robustness thresholds.**
   Recommended: **ship editable defaults:** at least 100 trades; walk-forward out-of-sample Sharpe at least half of in-sample; Monte Carlo 95th-percentile drawdown inside his risk limit; deflated Sharpe above 0 with every tried variant counted; profitable after 1.5x costs. He changes them in the UI (his standing rule: configurable means UI-editable).

8. **Improvement loop budget (old WF2).**
   Recommended: **3 generations × 4 children per parent at most.** Stop early after 2 generations with no gain. Every child counts toward deflated Sharpe.

9. **Paper window.**
   Recommended: **at least 2 weeks and at least 30 trades.** Pass if results sit inside the backtest's Monte Carlo band. Re-paper once on a borderline result.

10. **Which sources first?**
    Recommended: **YouTube, then Instagram and TikTok saves, then X and TradingView, then papers,** the order the transcript agreed (videos first, `layout:332`). Books stay out.

11. **Full-channel ingestion.**
    Recommended: **only from a list he curates** (podcasts, prop-firm channels). Everything else is single item or playlist.

12. **Budget guard for video work** (Max 5x, no API spend).
    Recommended: **transcript-only triage; frames only on flagged windows.** Add a per-run cap on frames and items that he sets. A Whisper key (Groq) is the only paid add-on, and only for uncaptioned videos.

13. **Reuse the `strats-video-populate` skill?** It was built and self-tested for Hermes/Grok, and never run.
    Recommended: **yes, reuse its ledger, gates and roles as the stage 1-7 template inside QMA v2,** after B33 picks a workflow engine (`05` gap 1). Run a 4-item pilot first (one long chart video, one reel, one X thread, one article; `layout:178`).

14. **The `Desktop\strats` debris folder.**
    Recommended: **move it to an archive folder** (the one JSON is a session export worth keeping). This needs his explicit go, because deletions do.

15. **Component cards: a new class or just dictionary entries?**
    Recommended: **a new `component` class next to `fragment`,** so a reusable exit or filter can be tested on its own and attached to many strategies. This is his Lego vision; DNA A-I is "a minimum, not a prison" (`layout:556`).

16. **Where do hints go?**
    Recommended: **hint cards in the Library, tagged `hint`.** They feed the Lab's grilling step (`06` stage 1) instead of being thrown away.
