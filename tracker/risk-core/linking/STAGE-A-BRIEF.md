# Stage A: take sources apart into components

Every Stage A agent reads this file first. Your prompt names your subject cluster.

## Why

QMX's risk-and-sizing design has gathered a lot of research. Stage B will link logic across all of it: a method from one paper, a piece of an MQL5 article series, a pattern from Kubernetes, an old QMX rule. Stage B can only do that if every source is first broken into **components**: small, named mechanisms with clear inputs, outputs and assumptions. That is your job. Do not design QMX and do not rank anything. Take sources apart honestly and completely.

**The deliverable all of this serves:** a malleable, self-configuring, extensible risk-and-sizing **template for the unit** that ships. The operator's principles (all in `STATE.md` items 25 to 28):
- Performance with intention, not just safety.
- Nothing is off limits, including replacing the Book/BMS shape. QMA changes are flagged, not designed.
- Research is not anchored to the Book or to a dollar budget.
- The multi-instrument lens crosses every topic.

## Sources

All paths are in `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. Take what bears on your cluster:

- **Research:**
  - `research\R1-platforms-risk-sizing-extensibility.md` (LEAN, StrategyQuant, MQL5 classes, n8n, Nautilus, Bloomberg)
  - `research\R2-trader-practice-windows-drift-isolation-breadth.md`
  - `research\R3-edge-verification-and-analogues.md` (clinical trials, grids, SRE, insurance, Basel zones)
  - `research\R4-alphaxiv\`: assistant chats and synthesis. **Still growing**: take what exists now and note the last chat you covered.
  - `research\R5-mql5-corpus-ideas.md` (about 110 MQL5 articles, borrowed logic from other fields). Open the original article at `C:\Users\Mubarak\Desktop\QMX\.worktrees\mql5-library\data\mql5-library\md\<id>.md` when a component needs its detail.
  - `research\R6-alphaxiv-papers\` (48 papers read in full). Use `mcp__alphaxiv__get_paper_content` or `answer_pdf_queries` when a component needs more detail than the notes give; the account is on a paid plan now.
  - `research\R7-software-patterns-self-configuring.md` (Kubernetes and VPA, Argo Rollouts, TCP, resilience4j, Envoy, CSS cascade, Terraform, and more)
- **Grounding:** `grounding\G1`-`G11` for the old QMX generations and the shipped stack. Old rules are sources too.
- **Drafts:** the stopped drafts in `expansion\drafts-stopped\` (X1 template shape, X4 scenarios, X5 edge verification). Treat their ideas as components with evidence "idea".
- **The operator's words:** `seeds\SEEDS.md` and `seeds\operator-words-2026-11-03.md`. When he proposed a mechanism himself, record it as a component with source "operator".
- **The ledger:** `ledger\variables.yaml` and `ledger\README.md`, for existing variable ids.

## Component schema

Write one YAML list to `linking\components\<your-file-id>.yaml`. Each component is one mechanism; split a paper with three mechanisms into three components.

- `id`: `<your-file-id>-NNN`
- `name`: plain words
- `source`: file and line, paper id with link, MQL5 article id, or "operator M<n>"
- `kind`: one of these, or `other` with a word:
  - sizing rule, allocator, budget, brake, detector, gate/test, exit/stop, accelerator, cost model, config/override pattern, versioning/rollout pattern, control loop, workflow, agent role, measure/telemetry, scenario
- `what_it_does`: two or three plain sentences
- `inputs`, `outputs`: lists, in plain words
- `assumptions`: what must be true for it to work
- `levels`: trade, position, unit, cluster, methodology, portfolio, account, node, system
- `instrument_classes`: which classes it was shown on, and `class_notes` on how it would change for FX, indices, metals, energy, crypto, futures and stocks
- `styles_timeframes`: what it suits, for example scalper 1m or intraday 15m
- `evidence`: one of
  - live (real money);
  - controlled test (with a fair control, for example a random brake that fires as often);
  - author backtest;
  - simulation;
  - idea;
  - old QMX rule (and whether it ever ran)
- `known_failures`: where it breaks, from the source or the trap lists in R5 and R6
- `performance_note`: how it could add growth; `survival_note`: how it protects or endangers the floor
- `ledger_ids`: existing ledger ids it reads or sets, plus `new_variables` it would need (name and one line each)
- `qmx_layer`: X0 trading lens, X1 template shape, X2 sizing and accelerators, X3 brakes/exits/drift, X4 scenarios, X5 edge verification, X6 observability, X7 agents (one or more)
- `link_hints`: other components (by id, or by name if not yet given an id) it could combine with, and why, in one line each. Read the combination lists in R4, R5 and R6 and carry them over.

## Unit idea bank

Some sources hold trading signals or market readings rather than risk and sizing, for example multi-level order flow imbalance for scalping. Do not make them components. Write them to `linking\unit-ideas\<your-file-id>.md` as seeds. Each seed gets:
- the source;
- the signal or reading;
- the style, timeframe and instrument classes it suits;
- the data QMX would need;
- whether it implies a new MIS reading or QML block;
- its evidence.

## Rules

- **Be complete in your cluster.** Every source section that bears on it gets taken apart. Breadth matters, and so does keeping each component exact.
- **Files.** Read-only everywhere except your own two output files. Never commit. Never touch other worktrees' files.
- **Agents.** Do not spawn subagents of your own.
- **Writing.** Plain words. Mark your own opinions **[judgment]**.
- **Commands.** Time-limit every command.
- **Validate.** At the end, run a quick YAML parse of your file: `uv run --no-project --with pyyaml python -c "import yaml,sys; d=yaml.safe_load(open(sys.argv[1],encoding='utf-8')); print(len(d))" <file>`.

Return a summary of at most 12 lines: component count by kind and evidence, unit seeds count, the last R4 chat you covered, and the thinnest spots in your cluster.
