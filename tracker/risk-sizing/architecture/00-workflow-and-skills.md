# 00. The workflow from here to the build, and which skills to stack at each step

Written 2026-10-31 by agent P1 of the midday program. It is the lead's own view of the skills, asked for in his midday ruling 4, compared with Fable's view (research 53 §6) and with his. His workflow is fixed; this file works out how to run it, step by step, so each step is one sub-agent with a clear stack, inputs and outputs. The companion file `00-ledger.md` holds every decision these steps must honour.

Labels: **CHECKED** means read at the cited path or line, or run as a command this session. **INFERRED** means my judgement. Paths are absolute where an agent needs them.

---

## 1. The short answer

His workflow (STATE.md "Operator round 2026-10-31 midday", ruling 4) is the spine. His later rulings the same day add three things this file builds in: an edge-case catalogue before the architecture, the versions judged against it, and more than one review (ruling 19); QMB on its own pass, so five part agents (ruling 22); and every part judged as core or as a mini app on the core (ruling 23). I keep every step he named and add a few small things, each for a reason tied to his own words.

| Step | His ruling | My stack, in order | What I add, and why |
| --- | --- | --- | --- |
| 1 | Party mode with brainstorming, for the solutions | `bmad-party-mode` (non-interactive, session mode) → `bmad-brainstorming` (headless, then its converge step) | Nothing. Bound it to the foundation parts and his named weak spots, so it does not become another open expansion ("if we spend this time just expanding, we're not going to do much", T3:1264). |
| 2 | CIS for his day-to-day experience | `bmad-cis-design-thinking` (YOLO) → `bmad-cis-problem-solving` (YOLO) | Problem solving on the weak spots, because his ruling 2 makes them the lead's to solve ("try maybe solving the weak spots in your own way", T3:1264). |
| 2b | Edge cases catalogued before the architecture (ruling 19) | `bmad-review` edge-case lens over the ledger, the grounding files and the step 1 options → `bmad-advanced-elicitation` pre-mortem and red team → `research` on how white-label platforms keep a small core with stable extension points | The trading and resilience lists already on disk (the 24 Oct money-path list, the 22 Oct resilience list in the planning-workflow memory) as the starting set, so the catalogue harvests before it generates (ruling 18). |
| 3 | Party mode again, for the versions of the architecture and the foundation set; Winston joins | `bmad-party-mode` with Winston in the cast → `principle-exhaust-the-design-space` → `codebase-design` → `domain-modeling` | `domain-modeling` at the end. Wrong words have cost him most ("you know how wrong wording has messed us up so far", T2:1208); the words are fixed once, before Level 0. The versions are judged against the step 2b catalogue, and each part gets a core-or-mini-app verdict. |
| 4 | bmad-architecture is required; blast radius sits inside it | `bmad-architecture` (headless create, Level 0 parent spine) → `codebase-design` → `blast-radius` on the shipped seams the spine changes → a quick review of the spine against the catalogue (`bmad-review` adversarial and edge-case lenses, a fresh agent) | `codebase-design`, which he named "maybe" (T3:1264). It is the deep-module vocabulary QML was built on. |
| 5 | bmad-architecture per part (five agents; QMB has its own, ruling 22) | `bmad-architecture` (headless, inheriting the Level 0 spine) → `codebase-design` → `principle-exhaust-the-design-space` on real forks → `blast-radius` on the shipped files the part touches | Nothing beyond step 4's stack. |
| 6 | The full review, every part against the catalogue (ruling 19), one fix round | `bmad-review` lenses edge-case, adversarial, verification-gap, one agent; fresh agents for the one fix round | He also said "BMAD review might be used while coding" (T3:1264); it runs per PR in the build too. |
| 7 | The build plan | poteto-mode `playbooks/multi-phase-plan.md` → `check-plan.mjs` to 0 problems → `technical-writing` → `unslop` | Keep the plan checker ("Plan checker, I don't know about it", T3:1264). It is poteto-mode's own checker, and his last build plans passed it (CHECKED below). |
| 8 | The orchestrator prompt | poteto-mode `playbooks/autopilot-stack.md` as the execution playbook; `tracker/qma-v2/PROMPT-DATA.md` as the template | Nothing new. |
| 9 | poteto-mode runs the coding | poteto-mode Feature playbook and its principles; `tdd` at the plan's seams; `blast-radius` per PR on shipped seams; `bmad-review` and `bmad-code-review` by a fresh reviewer per PR; `show-me-your-work` | `blast-radius` per PR as well as in step 4, because the QML, QMB and QMN seams carry live trading later. |

Two more, outside his list. **Wayfinder** stays as a small decision index, not a driver: he asked for it on 31 Oct 04:08 ("I told you to use the wayfinder skill.", T3:913) and the midday ruling did not withdraw it. **The dummy unit** goes early in the build order as a thin vertical slice, so "does a unit actually make sense?" (T3:1145) is answered in the first days of the build, not the last.

---

## 2. What is available

Inventory run 2026-10-31 by a script over every `SKILL.md` in the five roots the brief named, reading each front matter (CHECKED, script output kept in the agent's scratchpad). 434 files, 280 distinct by content: `C:\Users\Mubarak\.claude\skills` 123, `C:\Users\Mubarak\.agents\skills` 1 new (its other 50 folders are copies of the first root), the QMX project `.claude\skills` 69 (BMad), `_bmad` 0 (it holds the scripts and config, not skills), `C:\Users\Mubarak\.claude\plugins` 87 (35 of them Airflow and Astro). The BMad set has 20 deprecated forwarders.

| Group | Skills that matter here | Notes |
| --- | --- | --- |
| Ideation | `bmad-party-mode`, `bmad-brainstorming`, `bmad-cis-design-thinking`, `bmad-cis-problem-solving`, `bmad-cis-innovation-strategy`, `bmad-cis-storytelling`, `bmad-forge-idea`, `bmad-advanced-elicitation`, the CIS persona agents (Carson, Dr. Quinn, Maya, Victor, Sophia) | Party mode, brainstorming and the two CIS workflows are the ones his workflow names. |
| Architecture and design | `bmad-architecture`, `bmad-agent-architect` (Winston), `codebase-design`, `domain-modeling`, `architect`, `how`, `why`, `blast-radius`, `figure-it-out`, `improve-codebase-architecture`, `bmad-spec`, `bmad-prd`, the `principle-*` set | `improve-codebase-architecture` and `wayfinder` carry `disable-model-invocation: true` (CHECKED in their front matter): an agent can read and follow them but cannot invoke them through the Skill tool. |
| Mapping decisions | `wayfinder`, `grilling`, `grill-me`, `grill-with-docs`, `to-questionnaire` | Grilling tickets are worked with a live human only (wayfinder SKILL.md, "Ticket Types"). |
| Review | `bmad-review` (lenses adversarial, edge-case, verification-gap, structure, prose), `bmad-code-review`, `code-review`, `interrogate`, `correct`, `no-comments`, `false-green-tests` | `false-green-tests` and the Reticle family target running web apps. |
| Build and verify | `poteto-mode` (playbooks, `scripts/check-plan.mjs`), `tdd`, `agentic-tdd`, `prototype`, `implement`, `show-me-your-work`, `principle-prove-it-works`, `principle-test-behavior-not-implementation`, `benchmark-checklist` | `prototype` is excluded by his ruling. `agentic-tdd` drives a running web app through Reticle; the backend packets do not need it. |
| Hooks and agent tooling | `plugin-dev:hook-development`, `hookify` writing-rules, `plugin-dev:mcp-integration`, `writing-for-agents` | Useful to the builder of the QML in-loop check (ledger Q-06). |
| Words and pages | `bro`, `unslop`, `technical-writing`, `wait-what`, `anatomy`, `documentation-factory` | `bro` and `unslop` on everything he reads. |
| Research | `research`, `bmad-deep-recon`, `watch`, `strats-video-populate` | Only inside a step or packet that owes a fact. |
| Lanes and factories | `epic-factory:run-epics`, `queue-publish`, `to-kanban`, `sssf`, `morning-brief`, `ship-check`, `swarm`, `arena` | Retired or off by default (CHECKED: `CLAUDE.md` retires the factory; `~/.agents/pstack-models.md` says arena and swarm are not used by default). |
| Not for this work | Airflow and Astro (35), M5 devices, math, MCP server building, shadcn and front-end design, office files, receipts, session reports | none |

---

## 3. Facts that decide how these skills run inside a sub-agent

All CHECKED unless marked.

1. **Party mode has one non-live path.** "The one exception is an explicit `--non-interactive`" (`C:\Users\Mubarak\Desktop\QMX\.claude\skills\bmad-party-mode\SKILL.md`, "How It Runs"). Its modes are session, auto, subagent and agent-team; a sub-agent that may not spawn falls back to **session**, "one mind behind every voice". The default in `customize.toml:47` is already `session`. An inline-named cast "IS the roster for the session".
2. **Brainstorming has a headless mode** (`bmad-brainstorming/references/headless.md`). It needs a machine signal (`headless: true` in the payload), then the agent generates the ideas itself, aims past 100, shifts domain every ten ideas, and logs every idea through `memlog.py`. Its HTML and intent artifacts are "delegated to a subagent"; a no-spawn agent writes `brainstorm-intent.md` from the log itself, as the 30 Oct funnel agents did (STATE.md funnel rows).
3. **The CIS workflows pause after every template output** with `[a] Advanced Elicitation, [c] Continue, [p] Party-Mode, [y] YOLO` (`bmad-cis-design-thinking/SKILL.md:75`, `bmad-cis-problem-solving/SKILL.md:75`). Headless means choosing **YOLO** at the first checkpoint and supplying the context through the "data attribute" the Inputs section names.
4. **bmad-architecture has a headless mode and supports layering.** `references/headless.md` takes a payload (intent, altitude, purpose, driving input, a parent spine path, `doc_workspace`) and returns JSON with `assumptions[]`, `open_questions[]` and `conflicts_with_prior_decisions[]`. "Inheriting a parent spine" treats the parent's decisions as binding and read-only (SKILL.md). The reviewer gate runs `scripts/lint_spine.py` and every `finalize_reviewers` lens "as a parallel subagent"; without sub-agents, "run sequentially, write the file first, then flush it from context" (`references/reviewer-gate.md`).
5. **The QMX overrides for BMad are stale.** `C:\Users\Mubarak\Desktop\QMX\_bmad\custom\bmad-architecture.toml` loads a persistent fact that routes implementation to the retired factory lanes and says never to recommend any `bmad-testarch-*` skill, and its `on_complete` sends the user to `documentation-factory` and epics. `bmad-brainstorming.toml` ends by recommending `bmad-prd`; `bmad-agent-architect.toml` (Winston) carries the same factory fact. `CLAUDE.md` (13 Oct ruling) retired the factory for QMA v2 and allows the testarch skills. Every brief that runs these skills must say: ignore the factory facts and the `on_complete` steps. I did not edit these files (my brief names only two files to write); the lead may want them corrected.
6. **BMad's default output folders sit in the main checkout.** Party mode, brainstorming and CIS write under `{output_folder}` = `C:\Users\Mubarak\Desktop\QMX\_bmad-output` (`_bmad/config.toml`; party `customize.toml:52,68`; brainstorming `customize.toml:67-68`). That checkout is on `main`. Every run passes an absolute `doc_workspace` under `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\architecture\`. The BMad scripts themselves live only in `C:\Users\Mubarak\Desktop\QMX\_bmad\scripts` (`memlog.py`, `resolve_config.py`, `resolve_customization.py`); the plan worktree has no `.claude\skills` and no scripts there. `uv` 0.12.9 and Node 24.18 are on the PATH.
7. **Wayfinder's grilling tickets need him live.** "A grilling agent that answers its own questions has broken this" (`wayfinder/SKILL.md`, "Ticket Types"). In this run a grilling question becomes a one-line lead's call in a veto ledger, never an answer written in his name.
8. **The poteto-mode plan checker exists** at `C:\Users\Mubarak\.claude\skills\poteto-mode\scripts\check-plan.mjs` (185 lines). The playbook calls it as `node pstack/skills/poteto-mode/scripts/check-plan.mjs`; locally the path above is the one to run. It requires, per PR, nine blocks in order (Depends on, Files, Build, You see, Verify unit, Verify live, Verify perf, Review gate, Merge), ten numbered live lanes each with a ``Save `...` `` artifact and a "Pass when" predicate, four perf boxes, a "How to read this" section with five fixed markers, a Program checklist with five fixed sub-headings, and an appendix titled "Prototype evidence".
9. **His earlier plans reconciled that checker with light verification.** Run on 31 Oct, the checker prints "8 PR sections, 0 problems" for `tracker/qma-v2/LOCAL-FIRST-PLAN.md` and "30 PR sections, 0 problems" for `tracker/qma-v2/DATA-PLAN.md`. `LOCAL-FIRST-PLAN.md:99-110` writes "Ten lanes on `haiku` at the PR head ... Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.", each lane saving a log, not a screenshot. The coordinator runs lanes 1 to 4 and at most one menu lane (`PROMPT-DATA.md` rule 2). That matches his light-verification rule (memory `light-verification-per-pr.md`).
10. **The multi-phase-plan playbook's step 2 says to settle open questions by prototype.** His midday ruling 1 rules out a throwaway prototype. The plan keeps the required "Appendix A. Prototype evidence" and fills it with "No throwaway prototype, by his ruling; the proof is the dummy-unit packet", naming the packet.
11. **The pstack model file names Fable for three roles**: `architect runners: opus, fable`, `arena cross-judge pool: opus, fable`, `interrogate reviewers: opus, fable` (`C:\Users\Mubarak\.agents\pstack-models.md`). His midday ruling 16 stops Fable agents until he asks. Any skill that reads those lines runs Opus only, and none of them can spawn inside a sub-agent anyway.
12. **The builder agent type exists.** `C:\Users\Mubarak\.claude\agents\poteto-agent.md` (CHECKED by listing). `bulk-worker.md` sits beside it and is banned by his 13 Oct ruling.
13. **The orchestrator prompt has a working template.** `tracker/qma-v2/PROMPT-DATA.md` has the shape his last build run used: who you are, read first, fifteen rules, a builder prompt template that starts "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents.", an "Attention, for the operator" list and a short paste prompt.
14. **`tdd` asks the user to confirm the seams first** ("No test is written at an unconfirmed seam", `tdd/SKILL.md`). In the build, the plan's "Verify, unit" block for each packet is the confirmed seam list, so a builder never needs to ask.

---

## 4. Rules for running a live-conversation skill inside one sub-agent that stands in for him

These hold for every step below. They make the agent a faithful stand-in, not an inventor of his opinions.

1. **His voice is quotes only.** Wherever a skill casts "the user" or a persona of him, every line in his voice is a verbatim quote from the transcripts, with its `T1`, `T2` or `T3` line, taken from `00-ledger.md` or the transcripts themselves. The agent never writes a new sentence and attributes it to him. A script checks every such quote before the file is handed back (the ledger's own check is the template: 279 of 279 quotes found on their cited lines).
2. **Process choices are pre-set in the brief.** Stance, technique flow, party mode, cast, YOLO, altitude, purpose: the lead decides them in the brief, so the skill never stops to ask how to run.
3. **Content questions are answered from the ledger, by status.** A RULED or LEAD'S CALL row answers it; the agent cites the row. A SEED row is material to expand, never an answer. Anything the ledger does not settle becomes a lead's call: the agent proposes a default, writes one line for the veto ledger (what, why, how to undo), and carries on (his midday ruling 2; poteto-mode's never-block-on-the-human principle). Only money, his values and the words on his screens may become a question for him, and the ledger's "settled" section lists what must never be asked again.
4. **Live-only skills do not run headless.** `wayfinder` grilling tickets, `grilling`, `grill-me`, `prototype` and `improve-codebase-architecture` are not run inside a sub-agent. Their questions go to the veto ledger.
5. **Spawning steps run in sequence.** Party mode's subagent mode, brainstorming's artifact step, the architecture reviewer gate, `bmad-review`'s one-agent-per-lens step, `bmad-code-review`'s layers, `how`'s explorers and `blast-radius`'s arena step all fall back to the agent doing each part itself, writing each part's file before starting the next (the skills' own fallbacks, fact 4).
6. **Ignore the stale BMad endings** (fact 5) and write only under the step's own folder (fact 6).
7. **Clash stays clash.** Party mode and the CIS runs keep disagreements open in their files; convergence happens only where the step says so, and the lead's pick is logged as a lead's call.
8. **Read before you run.** Each agent reads the poteto-mode SKILL.md, the standing orders, `00-ledger.md`, and the SKILL.md of every skill in its stack before starting, per his "you can't tell the agents to use what you don't know" (T2:439).
9. **Harvest before generating** (his ruling 18). Every generative step starts from what is on disk: the 20 to 28 Oct transcript and its platform studies, the Hermes gold mine, the 30 Oct funnels, this run's grounding, and the agents' outputs. New ideas come on top.
10. **Agents never ask him.** A question that is truly his goes to the lead, who asks it with the question tool (his ruling 20).
11. **New information means a fresh agent.** When a nudge or a finding changes a running agent's job, the lead cuts it and starts a fresh one with the new information (his ruling 17).

---

## 5. The steps

Proposed folders sit under `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\architecture\`. Names are recommendations; the lead may rename them.

### Step 0. Grounding and this ledger (running now)

- **Purpose.** Know what is built before designing (ledger CC-03), and carry every decision forward (ledger P-04).
- **Stack.** poteto-mode Investigation playbook (read-only, cited answer); `how` in its simple path (one explainer, no explorers, since a sub-agent may not spawn); `research` with Exa for outside facts (futures platforms and order-flow feeds, Sierra Chart's cost, platform languages and API standards); context7 for library docs.
- **Outputs.** `grounding/` (three files, one per lens), `00-ledger.md`, this file.
- **Done when.** Each grounding file tags every part built, stacked, missing or never run, with paths.

### Step 1. Party mode with brainstorming, on the solutions

- **Purpose.** Generate and argue solutions for the foundation parts (his midday ruling 7 list: QML with its dictionary, the MIS, contracts and APIs, the trading node, QMA workflows, the unit) and for the weak spots he handed to the lead.
- **Stack, in order.**
  1. `bmad-party-mode`, run with `--non-interactive --mode session`, an inline cast, memory on, memlog in this step's folder.
  2. `bmad-brainstorming` headless, over the party transcript plus the inputs, its memlog in the same folder.
  3. `bmad-brainstorming` `references/converge.md`, to narrow each part to two or three solution options with a recommendation.
- **Cast (recommended).** A cTrader FX and gold scalper; a futures order-flow trader; a perps trader; a quant obsessed with overfitting; a QMA v2 harness engineer (hooks, workflows); a cheap building agent turning a video into a unit; a deep-modules designer; the GPT voice that built the dictionary, quoted only from research 39; him, quoted only from the ledger.
- **Inputs.** `00-ledger.md`; `grounding/`; his midday message verbatim (T3:1264); research 43 (§2, §3), 52 (§4, §9) and 53 (§3) as material; research 34, 35, 36, 39, 45 for QML; research 22, 23, 37 for the MIS; research 31, 32, 38 for the node and connections; the explainer sites' sources under `explainers/` (ledger P-06).
- **Outputs.** `funnel/solutions/party-transcript.md`, `funnel/solutions/.memlog.md`, `funnel/solutions/solutions.md` (per part: options, recommendation, what it touches in shipped code, the ledger rows it honours).
- **Headless notes.** Brainstorming's payload is `headless: true`, `topic`, `goal`, `context` (file paths), `doc_workspace` (absolute), `artifacts: intent`. Skip the HTML keepsakes (his "No need for an explainer site.", T2:602). Bound the topic to the foundation parts and the weak spots, so the run widens solutions, not scope.
- **Done when.** Every foundation part has two or three options and a recommendation; every quote of his passes the script check.

### Step 2. CIS on his day-to-day experience (parallel with step 1)

- **Purpose.** How he, and someone who was not in the planning, uses QMX each day to make money with units; and the lead's own solutions to the weak spots.
- **Stack, in order.**
  1. `bmad-cis-design-thinking`, YOLO at the first checkpoint. Personas: him as the daily user, quoted only from his words (T2:858 "how am I going to be using units", T3:1102 the newcomer, T3:1264 the mini-app pattern); a newcomer who installs QMX out of the box and starts a trading node; the copilot as a user of the same doors (ledger A-01); a cheap QMA agent writing a unit.
  2. `bmad-cis-problem-solving`, YOLO, on the weak spots: the two speeds of self-tuning; placeholders that cannot show tuning; the market-picking trap; the unit-to-MIS connection in code; starting a node and seeing it run.
- **Inputs.** The ledger; research 30 (desk rhythms, his day) and 43 §1 ("Your day with QMX"); the mini-app ADRs and the `d9-mini-app-pipeline` template (53 §2 item 10); `tracker/qma-v2/UI-NOTES.md` and `UI-HANDOFF.md` for what the screens already promise.
- **Outputs.** `funnel/experience/design-thinking.md`, `funnel/experience/problem-solving.md`, and a short "UI needs" list the step-5 agents pick up.
- **Headless notes.** Override `default_output_file` with the paths above; pass the context through the data attribute; record each checkpoint's output as the skill asks, then continue without waiting.
- **Done when.** His day and the newcomer's first hour are written as journeys, each step naming the part and door it uses; each weak spot has a proposed solution the architecture can adopt.

### Step 2b. The edge-case catalogue (parallel with steps 1 and 2)

- **Purpose.** List the hard cases the foundation must handle before any version is drawn, so the simplest version that handles them wins (his ruling 19). His picture is white-label software, Shopify or Wix: a small core with stable extension points.
- **Stack, in order.**
  1. Harvest the lists already on disk: the 24 Oct money-path list (funding flips, futures expiring mid-trade, weekend gaps, partial fills and minimum sizes, stale feeds and venue outages, a unit in the wrong market, correlation spiking, self-tuning drifting toward bigger risk, look-ahead in proof; T1 line 682 onward), the 22 Oct resilience list (retries, rate limits, abrupt offline, caching, corruption, backups, reconnects; memory `planning-workflow-that-worked.md` step 10b), and the node and venue facts in research 31, 32 and 38 (token refresh logging out the other machine, no cancel-on-disconnect on cTrader, Hyperliquid's switch cancelling stops, unsynchronised clocks).
  2. `bmad-review` with the edge-case lens only, over the ledger, the grounding files and the step 1 options, read as documents that define behaviour; the lens lists only unhandled paths.
  3. `bmad-advanced-elicitation`, with the pre-mortem and red-team methods picked by name (`scripts/pick_methods.py show`), on the question "how does this foundation fail in six months of daily use?".
  4. `research` (Exa) on how white-label and plugin platforms keep their core small and their extension points stable, and on how trading platforms (MT5, cTrader, NinjaTrader) expose theirs.
- **Outputs.** `funnel/edge-cases/catalogue.md`: each case with where it bites, which part owns it, what the foundation must guarantee, and the check that proves it.
- **Done when.** Every case maps to one part and one check; the catalogue is the yardstick for steps 3, 4 and 6.

### Step 3. Party mode again, on the versions of the architecture and the foundation set (Winston joins)

- **Purpose.** Compare two or three versions of the whole architecture and of the foundation set (which parts, what is in the first build, where the seams sit), and pick one.
- **Stack, in order.**
  1. `bmad-party-mode`, `--non-interactive --mode session`. Cast: Winston (the installed `bmad-agent-architect` persona: Fowler's pragmatism, Vogels's realism, boring technology, rule of three, CHECKED in its `customize.toml`), Amelia (the developer), Murat (the test architect, `bmad-tea`), an on-call engineer for the node and its monitoring, the scalper and the order-flow trader from step 1, the newcomer, and him in quotes only.
  2. `principle-exhaust-the-design-space`: two or three competing versions, each written as a short sketch, compared side by side.
  3. `codebase-design`: judge each version by depth, seams, the deletion test and "one adapter is a hypothetical seam, two is a real one".
  4. `domain-modeling`: fix the words once (unit, logic, market context, reading, journal kinds, market settings, market version, server), in a glossary file in this folder, not `CONTEXT.md` in the repo root.
- **Judging rule.** His three tests (standing order 6: handles the hard cases, can be maintained and debugged, can be explained in a few plain sentences), his foundation test (QMX can grow on top without rework, ledger CC-01), the step 2b catalogue (ruling 19), and for each part a verdict: core, or a mini app on the core with defaults out of the box (ruling 23, ledger CC-26).
- **Inputs.** Steps 1, 2 and 2b; the ledger; `grounding/`; research 43 §7 (the implementation shapes still open) and 52 §9 (the parts and their connections).
- **Outputs.** `funnel/versions/party-transcript.md`, `funnel/versions/versions.md` (the versions, the pick, the losers kept), `funnel/versions/GLOSSARY.md`, and veto-ledger lines for each pick.
- **Done when.** One version is picked with its reasons; the glossary has one meaning per word.

### Step 4. bmad-architecture, Level 0 and the connections (blast radius inside)

- **Purpose.** The parent spine: the parts, what each owns, every connection point and the data that crosses it (ledger CC-16, C-01).
- **Stack, in order.**
  1. `bmad-architecture`, headless create. Payload: `intent: create`, `altitude: initiative`, `purpose: build-substrate`, driving input = `funnel/versions/versions.md` plus the ledger and `grounding/`, brownfield path = the QMX code at `origin/engine/base`, `doc_workspace` = `level-0/`. Run the reviewer gate in sequence: `lint_spine.py --workspace <level-0>` to 0 findings, the rubric walker, the two configured reviewers, each writing `level-0/reviews/review-<slug>.md`.
  2. `codebase-design` on each seam the spine fixes.
  3. `blast-radius` on the shipped seams the spine changes. Candidates from research 52 and 53 (CHECKED there): QML's "the bot may not size" (`qml/src/qml/protocol/intents.py:1-8`), the forbidden condition fields (`qml/src/qml/declaration/confluence.py:51-61`), the conformance gate (`qml/src/qml/conformance/__init__.py:1-6`), the factory seam (`qml/src/qml/protocol/factory.py:1-6`), QMB's silent runner (`build/wu4:qmb/src/qmb/host/backtest_door.py:60`), QMN's seat door (`qmn/src/qmn/seats/dispatch.py:1-8`). For each, prove the one fact the change is safe because of, by running real code.
- **Inputs.** Step 3's outputs; the ledger; `grounding/`.
- **Outputs.** `level-0/ARCHITECTURE-SPINE.md`, `level-0/.memlog.md`, `level-0/reviews/`, `01-connections.md` (one writer: this step), `level-0/blast-radius.md`.
- **Headless notes.** Ignore the QMX override's factory facts and `on_complete` (fact 5). Blast radius needs real code to run: the lead provides one read-only checkout of `origin/engine/base` on D: before this step, because standing order 13 forbids agents from making worktrees (INFERRED need; the main checkout is on `main`, CHECKED in the session's git status).
- **Quick review before step 5** (his ruling 19, "review more than once"). A fresh agent runs `bmad-review` with the adversarial and edge-case lenses over the spine and `01-connections.md`, against the catalogue; the Level 0 author fixes once before the part agents start.
- **Done when.** `lint_spine.py` reports 0 findings; every connection names who calls whom, where, and the data shape; the blast-radius file shows each safety fact proven by a run, or marked unproven; the quick review's findings are fixed or logged.

### Step 5. bmad-architecture per part (five agents, in parallel)

- **Purpose.** One design pass per part, each in its own folder, each inheriting Level 0 (his "one area per file, one lens per area").
- **Groups (recommended).** One agent each, grouped so each holds related reading once (ledger P-09). QMB has its own agent (his ruling 22):
  - **A. QML, the dictionary, the unit template and the authoring door** (priority one). The unit document and its compiler into the existing factory, the block catalogue, the dictionary's new form and its first content packet (ledger D-06), the deterministic check and the in-loop hook the copilot and QMA agents both hit (Q-05, Q-06), self-tuning at two speeds (U-06), the dummy unit.
  - **B. QMB, on its own.** The runner that trades, results in R, the windowed reader, tries counted at the door, the what-if split, the judge; built so he can make a new QMB version, improve it, or run several variants side by side, and judged as the first candidate to sit as a mini app on the core (ledger B-00, CC-26).
  - **C. Journals and the Library.** Journal kinds in depth (J-01), one writer per stream, the agent read door, recording into the Library, the preview and detail views the UI needs.
  - **D. The trading node, external connections, clocks and DevOps** (priority two). How orders are placed per venue, deploy from the PC and results back, the kill switch, Linux node with the WSL fallback, clocks across regions, one observability stack, the order-flow feed for futures (X-03).
  - **E. The MIS, QMA v2 copilot and agents, workflow templates and mini apps** (priority three). MIS defaults per instrument class with room for his models, the analyst workflows reading the MIS's logs, the templates and their doors, units inside mini apps.
- **Every part states its verdict:** core, or a mini app on the core with defaults out of the box (his ruling 23).
- **Stack, in order, per agent.**
  1. `bmad-architecture`, headless create, `altitude: epic`, with the Level 0 spine as the parent (inherited decisions binding and read-only; a conflict is surfaced, never overridden). `doc_workspace` = `parts/<group>/`.
  2. `codebase-design` on the part's modules and seams.
  3. `principle-exhaust-the-design-space` where a real fork exists (for example group D's "node as its own Linux program or a trading role of the Windows host", research 52 §11 question 3).
  4. `blast-radius` on the shipped files the part touches, proving each safety fact by running code.
  5. `research` through Exa, or context7, only for a fact the part owes (group D: platform languages, API standards, the free order-flow feed, Sierra Chart's cost).
- **Each part file also carries** a "UI needs" section and a "Risk and sizing points" section, and a "Contract changes" section. The agents do not write into `UI-NOTES.md`, `RISK-SIZING-PACK.md` or `01-connections.md` themselves; one writer consolidates each after step 6 (poteto-mode's separate-before-serializing principle).
- **Done when.** Each part's spine lints to 0; each part names what exists, what is added, what must not break, how it is checked, and which ledger rows bind it.

### Step 6. One review and one fix round

- **Stack.** `bmad-review` with lenses edge-case, adversarial (at least ten real findings) and verification-gap, one agent, the lenses in sequence, over Level 0, the connections file and the five part folders, checking every part against the step 2b catalogue (his ruling 19) and weighted toward the money-adjacent paths (order placement, the kill switch, journals that record trades, the unit runtime). Then one fix round by fresh agents, one per affected group, each given the original brief, the findings and the files (poteto-mode "Fresh subagents by default").
- **Outputs.** `review/findings.md`; the part files amended once; the consolidated `UI-NOTES.md` section, `RISK-SIZING-PACK.md` section (with the placeholder list, ledger U-04) and `01-connections.md` changes, each written by one writer.

### Step 7. The build plan

- **Stack, in order.** poteto-mode `playbooks/multi-phase-plan.md` (copy its skeleton, one section per PR) → `node C:\Users\Mubarak\.claude\skills\poteto-mode\scripts\check-plan.mjs <plan>` until it prints 0 problems → `technical-writing` → `unslop`.
- **Execution playbook named in the plan.** `playbooks/autopilot-stack.md`: builders stack PRs onto `build/unit-system`; nothing merges; he lands it (ledger P-14; memory `never-merge-unasked.md`).
- **How to satisfy the checker without heavy verification.** Follow `LOCAL-FIRST-PLAN.md`: ten lanes on haiku that save logs, lanes 1 to 4 the proving set, 5 to 10 a menu (fact 9). Appendix A "Prototype evidence" states that there is no throwaway prototype and names the dummy-unit packet (fact 10).
- **Order of packets (recommended).** Subtract first (the replay reader's copies, the "Book owns sizing and exits" laws for units); then the data shapes everything rests on; then a thin vertical slice, the dummy unit written as a document, compiled by QML, run through QMB with real trades, writing its journal, one number moving by its declared rule; then widen each part; the dictionary's first content packet runs beside the QML packets with no cap (ledger D-06). The slice answers "does a unit actually make sense?" early (INFERRED; poteto-mode's sequence-verifiable-units principle).
- **Done when.** The checker prints 0 problems and every packet names its Files block, its seams and the ledger rows it carries out.

### Step 8. The orchestrator prompt

- **Template.** `tracker/qma-v2/PROMPT-DATA.md` (fact 13) plus the planning-lead playbook §6.
- **It must say.** `/poteto-mode`, then `playbooks/autopilot-stack.md`; the store and `RESUME.md` first; the plan read from the plan branch with `git show`; probes first; builders write, push and run fast checks only, and the coordinator runs the long checks in the background (memory `subagents-never-wait-on-long-commands.md`); at most two builders with disjoint Files blocks; light verification, one fix round, lows logged; never merge, never push `main`; never stop to ask, log the default in `QUESTIONS-FOR-OPERATOR.md`; no Fable; lanes on haiku through his plan login; disk D:; speak plainly.
- **The builder model.** Name it. The default is Opus through `poteto-agent` (`CLAUDE.md`; memory `builders-always-opus.md`); his 30 Oct "I'll hand over the coding to other models" (T3:515) goes in the prompt's notes for him as the switch he can make (ledger "owed" item 15).

### Step 9. The builder prompt, and the skills builders use

- **Builder prompt.** Opens with "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents." Then the packet's plan section, the brief, the Files block, the parent SHA, and the ledger rows the packet carries out.
- **Skills while coding.**

| Skill | When | Why |
| --- | --- | --- |
| poteto-mode Feature playbook | every packet | `how` over the subsystem, `architect` sketch (Opus only, no arena), the throughput checkpoint, owning the diff directly, verifying, small ordered commits. A builder that may not spawn "satisfies this by owning the diff directly with the same review separation" (`playbooks/feature.md` step 4). |
| `principle-model-the-domain`, `principle-foundational-thinking`, `principle-type-system-discipline` | the unit document, the block catalogue, journal kinds, the instrument record | data shapes first; illegal states unrepresentable |
| `principle-boundary-discipline` | broker adapters, the authoring door, the data door | guards at the boundary, trusted internals |
| `principle-make-operations-idempotent` | order placement, resend, reconcile, deploy | a crash and retry converge to one end state |
| `principle-separate-before-serializing-shared-state` | journals (one writer per stream), the feed keeper | no two writers on one file |
| `principle-subtract-before-you-add`, `principle-migrate-callers-then-delete-legacy-apis` | the replay reader fix, the QML laws lifted for units | remove first, migrate callers in the same wave |
| `principle-encode-lessons-in-structure`, `correct` | the QML check and hook | a repeated agent mistake becomes a lint whose error names the fix (his "linter error", T3:1264) |
| `plugin-dev:hook-development`, `hookify` writing-rules | the in-loop authoring hook packet | how hooks feed an error back to a writing agent; ground first on QMA v2's own hook mechanism, which may differ |
| `principle-build-the-lever` | the dictionary port of the 239 entries, codemods | one script that reruns, not hand edits |
| `tdd` | the compiler, the checker, the QMB runner, the journal writer | red then green at the plan's named seams (fact 14) |
| `principle-test-behavior-not-implementation` | every test | a test that passes when every import returns nothing is rewritten |
| `blast-radius` | any packet touching a shipped seam of QML, QMB, QMN or the broker adapters | prove the safety fact by running code |
| `principle-prove-it-works` | before "done" | the real artifact, not "it compiles" |
| `show-me-your-work` | every packet | the `decisions.tsv` trail the coordinator reads |
| context7 | any library call | current docs, his 31 Oct addition |
| `technical-writing`, `unslop` | PR text | plain words |

- **Skills while reviewing** (a fresh Opus reviewer agent per PR, the 26 Oct exception in memory `merge-reviews-no-subagents.md`). `bmad-code-review` (allowed by `CLAUDE.md`); `bmad-review` edge-case lens on money-adjacent PRs (node, order path, connections, journals) and verification-gap on the checker; `blast-radius` where the diff touches a shipped seam. The coordinator runs the suites and lanes itself. `no-comments` spawns its own agent, so the coordinator runs it or it is skipped; `deslop` is not installed, so the builder rereads its diff before commit (poteto-mode "Harness").
- **After the build (optional, allowed by `CLAUDE.md`).** `bmad-testarch-test-design` and `bmad-testarch-trace` for the QA pass over the built code.

---

## 6. Three views, side by side

| Step | Mine | Fable (research 53 §6.2) | His (midday rulings 4, 19, 22, 23) |
| --- | --- | --- | --- |
| Expansion on the solutions | party mode, then brainstorming headless, then converge; bounded to the foundation parts; harvest first | dropped ("expansion is done") | party mode with brainstorming |
| His daily experience | CIS design thinking, plus problem solving on the weak spots | not in the stack | CIS |
| Edge cases | a catalogue beside the funnel (edge-case lens, pre-mortem and red team, research on white-label cores), the yardstick for the versions and both reviews | the one review only | catalogue before the architecture, versions judged against it, review more than once |
| Core or mini app | a verdict per part in steps 3 and 5 | not raised | "most things can actually become mini apps"; QMB first |
| Versions of the architecture | party mode with Winston, then exhaust-the-design-space, codebase-design, domain-modeling | none; codebase-design then domain-modeling before Level 0 | party mode again; Winston joins |
| Level 0 | bmad-architecture headless parent spine, codebase-design, blast-radius | codebase-design, domain-modeling, bmad-architecture parent spine | bmad-architecture required |
| Per part | bmad-architecture inheriting the spine, codebase-design, exhaust-the-design-space, blast-radius, research only for owed facts; five agents, QMB on its own | the same, three agents | bmad-architecture; QMB gets its own pass (five agents in the amended program) |
| Proof in code | a thin vertical slice early in the build: the dummy unit on the real template | a two-day throwaway with the `prototype` skill | no prototype skill; a dummy unit on the real parts |
| Blast radius | inside steps 4 and 5, and per PR in the build | per part | inside the architecture step |
| Review | a quick review of Level 0, the full review of every part against the catalogue, then per PR in the build | one planning review | bmad-review may serve during coding; review more than once |
| Wayfinder | a small decision index; destination the orchestrator prompt; grilling questions become veto-ledger lines | re-chart once, small | asked for it at 04:08; not in the midday list |
| Build plan | multi-phase-plan playbook, check-plan to 0, the LOCAL-FIRST lane form | check-plan to 0 | "Plan checker, I don't know about it" |
| Orchestrator and builder prompts | PROMPT-DATA template, autopilot-stack, Opus `poteto-agent` by default | coordinator prompt per CLAUDE.md, builder template | poteto-mode runs the coding |
| Coding skills | Feature playbook and the principles above, tdd, blast-radius, show-me-your-work | show-me-your-work, bmad-code-review, tdd, light verification | poteto-mode |
| Fable-model roles (architect, arena, interrogate) | Opus only, or skipped | not used | no Fable agents |

**Where I agree with him.** The funnel stays. Fable dropped party mode, brainstorming and CIS as "done", but he kept them because the workflow "was meant to help us cover a lot of ground and not miss multiple things" (T3:1264), and the foundation's solutions have not been argued yet; only the field of questions was. bmad-architecture is the spine of the design. No throwaway prototype. Blast radius belongs inside the architecture. Edge cases first and reviews more than once. QMB on its own pass, and every part judged as core or mini app. poteto-mode runs the coding.

**Where I add something, and why.**
- **domain-modeling** at the end of step 3: the word drift (funding, regime, System 2, journal) is the biggest repeated cause of wrong designs in this run (ledger "missed" items 11 to 19).
- **codebase-design** in steps 3 to 5: it is the deep-module vocabulary he gave as the reason QML looks the way it does (ledger Q-07).
- **CIS problem solving** beside design thinking: his ruling 2 makes the weak spots the lead's job, and that is the CIS method built for it.
- **The plan checker**: it is poteto-mode's own, and the precedent shows it fits his light verification.
- **Wayfinder as an index only**: he asked for it, and its grilling tickets are exactly the questions he refuses to be asked, so they become one-line calls.

**Where I would do it differently, as a recommendation.**
- Put the dummy unit early in the build order as a thin end-to-end slice, not last, so the answer to "does a unit make sense" arrives in the first days.
- Keep step 2b's catalogue to cases a part must guarantee, each with its check, so it stays a yardstick and does not turn into another open expansion.

**Where I disagree with Fable.** The `prototype` skill and the two-day throwaway: he ruled them out, and the same proof comes from the first build slice. Dropping party mode, brainstorming and CIS: his workflow keeps them. **Where I agree with Fable.** The parent spine then child spines; no arena, swarm or interrogate; research only where a packet owes a fact.

---

## 7. Risks in the stack itself

1. **Party mode in one sub-agent is one mind voicing everyone** (fact 1). The clash is weaker than in a live room. Mitigation: feed it the real disagreements on disk (research 43 against 52 and 53, his midday words against the morning program, the node's Linux code against his Windows preference), and keep the clashes open in the file.
2. **The stale BMad overrides** (fact 5) can steer a headless run toward the retired factory or a PRD. Every brief says to ignore them.
3. **Default output folders in the main checkout** (fact 6) would write onto `main`. Every brief passes absolute folders.
4. **Blast radius needs runnable code**, and agents may not create worktrees. The lead provides one read-only checkout before step 4.
5. **Five parallel part agents can drift on shared words and contracts.** The glossary and `01-connections.md` each have one writer; part agents propose changes in their own files.
6. **The checker's ten-lane form can grow into heavy verification.** Holding to "lanes 1 to 4 proving, 5 to 10 a menu" keeps it to his one build and one check per PR.
