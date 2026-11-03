# Stage B: expansion by linking logic

Every Stage B agent reads this file first. Your prompt names your layer.

## What this stage is

QMX is a trading system. The operator, Mubarak, is not technical and not a trader. This session designs the **risk-and-sizing template for the unit**, the deliverable since his first message on 3 Nov. The template must:
- work out of the box with self-configuring defaults, each with a reason;
- extend in any way, by him, by the copilot or by agents;
- ship through builders.

Stage A took every source apart into **components**: about 900 of them, each with inputs, outputs, assumptions, evidence and link hints. Your job is to **link logic across them** for your layer:
- take a method from one paper, a piece of an MQL5 series, a pattern from Kubernetes and an old QMX rule;
- combine them into **hybrids**: seeds, pairs, triples, larger mixes;
- each hybrid serves a named need of the template.

This is still expansion: widen, do not converge. A later Fable judge funnels and ranks (`linking/RANKING.md`); you do not rank. Every hybrid must name the need it serves.

## Principles (his rulings; `STATE.md` items 25 to 38)

- **Performance with intention, not just safety.** Survival is a constraint, not the goal. A design that never touches the floor but grows nothing is the "sitting duck".
- **Nothing is off limits.** You may replace the Book/BMS shape, the levels or parts of the shipped stack, as long as the replacement performs better and makes sense. QMA (the agent system) changes are flagged, not designed. New mini apps, pod restructuring, new market physics and new MIS readings are all welcome.
- **Multi-instrument lens on everything:** FX, indices, metals, energy, crypto, futures, stocks. Every hybrid says how it behaves per class.
- **Trading lens, top-down:** portfolio, then style and timeframe (scalping, intraday, swing), then market structure, then technique. Do not anchor on any account size.
- **Brake, accelerator, restore and clamp** are defined in `research/R9-accelerators-and-brake-pairs.md` (Definitions). Use those definitions and extend them if your hybrids need new kinds.
- **The template must accept, without rework:**
  - the QMX Lab (designed, unbuilt: a seven-slot pod with allocator, caps and guards);
  - MCP-driven agents;
  - the future agent department (`handoff/AGENT-DEPARTMENT-SEEDS.md`).
  None of them ever sits in the order path. Agents never touch money. Only he promotes a unit to live. Exits are never blocked. The kill switch only goes down by his hand.
- **Self-configuring has a model:** Kubernetes and its Vertical Pod Autoscaler (`research/R7`).
  - A typed document carries defaults.
  - A learner proposes a value with low and high bounds.
  - An applier uses it in an owner-chosen mode: off/shadow, at start, live.
  - Tuned numbers are guesses with guards that fall back and freeze.
  - QMX today has the learner and no applier.
- **Every number needs a derivation,** and he can change *how* it derives, not only its value.
- **Facts that hold everywhere:**
  - costs must reach the sizer;
  - fast invalidation needs a real cut size per strategy;
  - count brakes must not punish frequency or fast-invalidation cuts;
  - the shipped stack's gaps (G8, G9, G11) are design inputs.

## Inputs

All paths are under `D:\QMX-worktrees\risk-plan\tracker\risk-core\`.

- **Components:** `linking\components\*.yaml` (A1 to A5). This is your main material. Search all files, not only your own layer's; the best links cross layers.
- **Unit ideas:** `linking\UNIT-IDEA-BANK.md`. Not your job to develop, but a hybrid may need a reading or a block a seed implies.
- **Variables:** `ledger\variables.yaml`, `ledger\README.md` and `ledger\check.py`.
- **Research:** `research\R1`-`R9`, with full paper texts in `research\papers\text\<arxiv-id>.txt` when you need a detail. `research\R4-alphaxiv\R4-alphaxiv-synthesis.md` lists about 60 combinations and 15 workflows; carry them in.
- **Grounding:** `grounding\G1`-`G11`, for the old generations and the shipped stack (stack tip at `D:\QMX-worktrees\bld-us-c13`).
- **His words:** `seeds\SEEDS.md`, `seeds\operator-words-2026-11-01.md` and `seeds\operator-words-2026-11-03.md`.
- **Drafts:** `expansion\drafts-stopped\`. X1 template shape and X5 edge verification are complete drafts; X4 scenarios stops at scenario 37. If your layer has a draft, revise and extend it; do not start over.

## Method

Run these yourself, non-interactively. No human is available, so play every role and never wait for input.

1. **BMad brainstorming in headless mode.** Skill: `C:\Users\Mubarak\Desktop\QMX\.claude\skills\bmad-brainstorming\SKILL.md` and its `references\headless.md`.
   - Topic: your layer.
   - Goal: hybrids for the unit template.
   - Context: this brief.
   - `doc_workspace`: `linking\stage-b\<your-file-id>\`.
   - Artifacts: intent only, no HTML.
   - Techniques, at least: Morphological Analysis (the components are the parameters), Concept Blending, Forced Relationships, Cross-Pollination, Trait Transfer, Evolutionary Pressure (breed hybrid variants under a selection rule you state) and Solution Matrix (problems against components, to show the empty gaps).
2. **`bmad-cis-problem-solving`** on every open problem in your layer, with at least two solutions each.
3. **A `bmad-party-mode` roundtable** to stress your strongest hybrids. Choose personas that fit your layer, and always include a pod-shop risk manager, a retail scalper, a platform engineer and the operator's voice taken from his words.

## Deliverables

**1. `expansion\<your-file-id>.md`** with these parts:
- **Hybrids.** For each:
  - an id;
  - the components it links, by id;
  - the need it serves;
  - what it does and how it works;
  - its levels;
  - its behaviour per instrument class and style;
  - the ledger ids it touches;
  - a performance note and a survival note;
  - its evidence chain (name the weakest link);
  - a maturity tag: solid, plausible or wild.
  Keep wild hybrids.
- **Problems and solutions:** at least two options each, with trade-offs.
- **Collisions:** with other layers, his words, the grounding, or between your own hybrids. Name them; do not resolve them.
- **Restructure proposals:** where your layer suggests replacing a level, a component of the stack or the Book/BMS shape, say what replaces it and why it performs better.
- **Gaps:** what no component covers.
- **Questions only he can answer:** keep this short.

**2. `ledger\additions\<your-file-id>.yaml`**, with every new variable in the ledger schema. Reuse existing ids. Run `uv run --no-project --with pyyaml python ledger\check.py ledger\additions\<your-file-id>.yaml` and fix what it reports.

## Rules

- Read-only everywhere except your outputs and your `doc_workspace`. Never commit. Never touch other worktrees' files.
- Do not spawn subagents of your own.
- No Firecrawl. For any web lookup, use the Exa tools (`web_search_exa`, `web_fetch_exa`; load them with ToolSearch "exa"), or the alphaXiv MCP for papers.
- Plain words, short sentences. Mark opinions **[judgment]**.
- Time-limit every command.

Return a summary of at most 15 lines:
- hybrid count by maturity;
- the five strongest hybrids, one line each;
- restructure proposals;
- the worst collisions;
- ledger additions count.
