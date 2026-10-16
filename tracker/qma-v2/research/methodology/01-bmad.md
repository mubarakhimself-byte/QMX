> STATUS 2026-10-16 (rubric walk): KEEP-AS-SOURCE. See 27-rubric-walk.md. Rulings in 26 win.

# 01 — What QMX can borrow from BMad

Research date: 2026-10-16. Read page by page in the built-in browser (tab of its own), following site navigation. No bulk dumps (`llms-full.txt`) were used.

## Versions seen

- **BMad Method v7 is "preview alpha".** The install page says the v7 release ETA is October 16, 2026 (today). The stable line is **v6.12**, frozen except for bug fixes. https://docs.bmad-method.org/start/install-bmad/
- The `bmod-method` module record on `main` says `version = "6.13.0-next"`. https://github.com/bmad-code-org/BMAD-METHOD/blob/main/skills/bmod-method/bmod.toml
- v7 installs through the Skills CLI (`npx skills add bmad-code-org/BMAD-METHOD`) or a Claude Code or Codex plugin marketplace. v6.12 still uses `npx bmad-method install`.
- **QMX's local install** (`_bmad/_config/manifest.yaml`): core and bmm **6.11.0**, CIS **v0.3.1**, TEA **v1.23.3**, installed 2026-08-19 for the claude-code, codex, antigravity and pi tools. **BMad Builder (bmb) is not installed.** Locally, `bmad-build` still uses step files (`step-01-clarify-and-route.md` … `step-05-present.md`), and TEA skills use `steps-c/`, `steps-e/` and `steps-v/` folders (create, edit and validate modes).
- The docs are moving between versions. The builder docs still describe the v6 module format (`module.yaml` + `module-help.csv` + a setup skill). The new Toolsmith docs call that the "old module" format, now replaced by the "bmod format". Several Toolsmith pages say "This page is being written." https://docs.bmad-method.org/toolsmith/migrate-an-old-module/

---

## Q1. BMad's building blocks

### Skill: the single packaging unit
- In BMad, everything is a skill: an agent, a workflow or a utility. It is a folder containing a `SKILL.md`, and it follows the open Agent Skills standard. https://bmad-builder-docs.bmad-method.org/explanation/what-are-skills/
- Optional subfolders: `resources/` or `references/` (reference data), `scripts/` (deterministic code), `templates/` or `assets/` (output building blocks), `prompts/` (stage instructions), and `agents/` (subagent definitions).
- A `SKILL.md` has YAML frontmatter (`name`, `description`). The model always sees the frontmatter and loads the body only when the skill triggers. https://bmad-builder-docs.bmad-method.org/explanation/progressive-disclosure/
- The description rule is "[5-8 word summary]. [Use when user says 'X' or 'Y'.]" https://bmad-builder-docs.bmad-method.org/explanation/skill-authoring-best-practices/
- A skill does one of three things: loads an agent persona, runs a multi-step workflow, or runs a single task. https://docs.bmad-method.org/reference/skills-and-agents/

### Agent = skill + persona + capabilities (+ memory)
- An agent adds three traits to a skill: a **persona**, **capabilities**, and optional **memory**. https://bmad-builder-docs.bmad-method.org/explanation/what-are-bmad-agents/
- There are three agent types:
  - **Stateless**: one SKILL.md, every session is independent.
  - **Memory**: a lean bootloader plus a "sanctum" folder the agent reloads on every wake.
  - **Autonomous**: memory plus a `PULSE.md` that runs on a schedule with no human present.
- The sanctum lives at `_bmad/memory/<agent>/`, outside the skill, so the agent cannot rewrite its own instructions. It holds six core files: `INDEX`, `PERSONA`, `CREED`, `BOND`, `MEMORY` (kept under 200 lines) and `CAPABILITIES`. Session logs go in `sessions/YYYY-MM-DD.md`. They are not loaded on wake, and they are curated into MEMORY.md and pruned after about 14 days. https://bmad-builder-docs.bmad-method.org/explanation/agent-memory-and-personalization/
- "First Breath" is the first conversation, in which the agent learns its owner. It comes in two styles: Calibration (deep) and Configuration (focused). A `wake.py` script loads the whole sanctum in one pass.
- **Capabilities** come in three kinds: internal prompt commands, external skills the agent calls by name, and scripts. A memory agent can also be "evolvable": the user teaches it new capabilities, and it writes them into a "Learned" section.
- **What a shipped agent looks like on disk (v7)**: `bmad-agent-analyst/` holds three files: `SKILL.md`, `customize.toml` and `bmod.toml`. https://github.com/bmad-code-org/BMAD-METHOD/tree/main/skills/bmad-agent-analyst
  - `SKILL.md` fixes the identity ("You are Mary, the Business Analyst"). It defines an 8-step activation: resolve customization, run prepend steps, adopt the persona, load persistent facts, load config, greet, run append steps, then dispatch or show the menu. https://github.com/bmad-code-org/BMAD-METHOD/blob/main/skills/bmad-agent-analyst/SKILL.md
  - `customize.toml` holds icon, role, identity, communication_style, principles, persistent_facts, activation hooks, and a **menu**: `[[agent.menu]]` items, each with a `code` (BP, MR, DR…), a description, and either a `skill =` or a `prompt =`. https://github.com/bmad-code-org/BMAD-METHOD/blob/main/skills/bmad-agent-analyst/customize.toml
  - `bmod.toml` names the module the skill belongs to and lists `recommended_skills`, so the agent can offer to install a menu skill that is missing.
- **Agent menus thin out the agent itself.** Mary's menu mostly forwards to shared workflow skills, for example `bmad-deep-recon` with a research type already chosen. The persona is a front door, and the work lives in reusable workflows.
- The v7 roster has five named agents: Analyst (Mary), PM (John), Architect (Winston), Developer (Amelia) and UX (Sally). The Tech Writer is "on hiatus". Menu codes are scoped per agent. https://docs.bmad-method.org/reference/skills-and-agents/

### Workflow = skill that produces an outcome
- A workflow has a clear start and end, little persona, and is generally stateless. https://bmad-builder-docs.bmad-method.org/explanation/what-are-workflows/
- There are three tiers:
  - **Simple Utility**: input→output, often script-driven.
  - **Simple Workflow**: 3–8 inline steps.
  - **Complex Workflow**: SKILL.md acts as a router, with `prompts/01-…md` stage files, resources, agents and scripts. https://bmad-builder-docs.bmad-method.org/reference/workflow-patterns/
- **Four progressive-disclosure layers**, from lightest to heaviest:
  1. Frontmatter vs body.
  2. On-demand resources.
  3. Dynamic routing: the body dispatches to different prompt flows.
  4. **Step files**: the agent reads one step at a time, never sees ahead, and waits for confirmation.
  BMad now warns that Layer 4 is "very rigid". Use it only for strict compliance or audit flows; "the lowest level needed is best". This is the old "micro-file architecture", now demoted to a last resort. https://bmad-builder-docs.bmad-method.org/explanation/progressive-disclosure/
- **State and resume**: the "document-as-cache" pattern stores workflow state in the output document's YAML frontmatter (inputs, current stage, status), so a run survives context compaction. Unattended runs use the plan file's `status:` field (draft → ready-for-dev → in-progress → in-review → built → done / blocked) as their state machine. https://docs.bmad-method.org/build/autonomous-development-loops/
- **Execution modes**: Guided (default, with soft gates), YOLO (draft everything, then refine) and Headless (`-H`, no interaction, for schedulers and orchestrators). https://bmad-builder-docs.bmad-method.org/explanation/skill-authoring-best-practices/
- **Elicitation**:
  - "Soft gates" ("Anything else, or shall we move on?") at transitions, instead of hard menus.
  - Intent-before-ingestion: find out why the user is here before reading any documents.
  - Capture-don't-interrupt: note ideas the user raises out of order instead of redirecting them.
  - `bmad-advanced-elicitation`: the model re-examines its own last output through a named method (pre-mortem, first principles, red team, Socratic, inversion…). https://docs.bmad-method.org/reference/skills-and-agents/
- **Dual output**: a human document plus an LLM "distillate" for downstream skills, which also records rejected ideas so they are not proposed again.

### Scripts: the determinism boundary
- Scripts handle anything with a right answer (validate, count, parse, diff, transform). The LLM handles judgment. The test: "Given identical input, will this operation always produce identical output? If yes, script." https://bmad-builder-docs.bmad-method.org/explanation/scripts-in-skills/
- Scripts are written in Python, not Bash (to work on Windows), use the standard library first, and declare dependencies inline (PEP 723) so `uv run` works with no setup.
- **Graceful degradation**: describe a script step as an outcome, so that if scripts cannot run, the LLM does the same work by hand.

### Subagent patterns
- The filesystem acts as a blackboard: `status.json`, `knowledge.md`, `/tasks/{id}/input.md` → `result.json` + `summary.md` (≤200 tokens). The parent's context stays tiny. https://bmad-builder-docs.bmad-method.org/explanation/subagent-patterns/
- There are six patterns: delegated data access, temp-file assembly, shared-file pipeline, hierarchical lead-worker, persona-driven parallel reasoning (Architect / Red Teamer / Pragmatist / Innovator…), and evolutionary/emergent (generations scored by an evaluator, stakeholder simulation, swarm).
- The most common mistake is that "the parent reads first", which wastes the tokens the subagents were meant to save. The fix is defensive wording in the skill. Every subagent feature needs a sequential fallback.

### Party mode
- `bmad-party-mode` puts installed agents or custom personas into one conversation, with the user steering. https://docs.bmad-method.org/customize/run-multi-agent-discussions/
- It has four modes: `session` (one model voices everyone), `auto`, `subagent` (each persona runs as an independent agent, so the voices do not converge) and `agent-team` (Claude Code only).
- If the tool cannot run the requested mode, it falls back automatically: agent-team → subagent → session.
- Saved parties ship as templates: the "Code Review Crew" and the "Anti-Consensus Club" (Wildcard, Level the claim checker, Killjoy the loop stopper, Splinter the consensus challenger). The Anti-Consensus Club "returns the decision to you".
- A party can have memory, and it can end with an HTML keepsake of the session.

### Modules
- A module is a package of skills, with shared config and registration in the help system. https://bmad-builder-docs.bmad-method.org/explanation/what-are-modules/
- A module is either **standalone** or an **expansion** of another module. An expansion must still work, in a reduced way, when its parent is missing.
- Architecture advice is "agent-first thinking": one agent with rich routed capabilities often beats many single-purpose agents.
- A multi-agent module can keep a module-level shared memory as well as each agent's own memory.
- **The v7 "bmod" record**: a skill such as `bmod-method/` holds a `bmod.toml` (`code`, `version`, `update_source`, the `skills` list, `required_skills` with versions), plus `roster.toml`, `retired.toml`, `migration-1.toml` and a `help/` folder. https://github.com/bmad-code-org/BMAD-METHOD/tree/main/skills/bmod-method

### Tasks
- In v7, a "task" is just a skill that "runs a single task", such as `bmad-review` or `bmad-advanced-elicitation`. It no longer has its own file type.

### The Builder (bmb) and Toolsmith
- The **BMad Builder** has three builders: Agent Builder (BA), Workflow Builder (BW) and Module Builder (IM ideate, CM create, VM validate). https://bmad-builder-docs.bmad-method.org/reference/builder-commands/
- **The six-phase build**:
  1. Discover intent. The agent builder detects the agent type through natural questions, such as "does it need to remember?".
  2. Capabilities strategy, or classify the workflow type.
  3. Gather requirements, including "folder dominion": read zones, write zones and deny zones.
  4. Draft and refine.
  5. Build, with a deterministic **lint gate** (`scan-path-standards.py`, `scan-scripts.py`).
  6. Summary, then offer Quality Optimize.
- The builder accepts four kinds of input: a rough idea, an existing skill (edit), a foreign skill or tool (convert), or docs and code (extract intent).
- **Quality Optimize (QO)** has three tiers: lint scripts; pre-pass scripts that extract metrics; and five LLM scanner subagents in parallel (structure, prompt craft, execution efficiency, cohesion, enhancement). It produces one report and protects persona voice from being "optimized" flat.
- **Convert (`--convert`)** rebuilds any skill headless and produces an HTML before/after comparison report.
- **Evals**:
  - *Artifact evals* (`evals.json`) grade the files and the transcript.
  - *Trigger evals* (`triggers.json`) check whether a description fires on the right queries, three runs per query.
  - Every eval runs in an isolated clean room, a grader subagent cites evidence for each expectation, and the run folders are kept permanently.
  https://bmad-builder-docs.bmad-method.org/explanation/what-are-evals/ and https://bmad-builder-docs.bmad-method.org/explanation/why-bmad-eval-runner/
- **v7 Toolsmith**:
  - "Smithy" (`bmad-toolsmith`) replaces the three builders with one agent that builds a skill of any shape. Shape is "an outcome of the conversation, not a starting choice".
  - `bmad-eval` measures skills.
  - A `CUT` mode rewrites a skill into the fewest words that steer the model just as far, then a checker restores any rule that was lost.
  https://docs.bmad-method.org/toolsmith/toolsmith/ and https://docs.bmad-method.org/toolsmith/modes/

---

## Q2. How BMad keeps a large ecosystem coherent

1. **One unit, one format.** Every agent, workflow and utility is a skill folder. Composition is "invoke another skill by registered name".
2. **A capability registry with a dependency graph** (v6): `module-help.csv` has 13 columns, one row per capability: module, skill, display-name, menu-code, description, action, args, phase, preceded-by, followed-by, required, output-location, outputs. https://bmad-builder-docs.bmad-method.org/explanation/module-configuration/
   - `preceded-by` and `followed-by` form a graph.
   - `required=true` makes a capability a blocking gate.
   - `output-location` + `outputs` let the help agent **detect completion by scanning for artifacts on disk**. There is no separate status database.
3. **A help/router agent.** `bmad` (formerly `bmad-help`) answers questions and recommends the next skill. It reads the active initiative, sees which `<type>-<slug>/` folders already exist, and ranks the next steps. It also runs `bmad setup`, `bmad status` and `bmad migrate`. The docs claim it "handles over 80% of questions". https://docs.bmad-method.org/start/get-answers-about-bmad/
4. **Layered customization without forking.** Each skill ships a `customize.toml`, which is both its schema and its defaults. Overrides live in `_bmad/custom/<skill>.toml` (team, committed) and `<skill>.user.toml` (personal, gitignored). https://docs.bmad-method.org/customize/customize-bmad/
   - Merge rules depend only on the shape of a value:
     - Scalars: the override wins.
     - Tables: deep merge.
     - Arrays of tables keyed by `code` or `id`: merge by key.
     - Other arrays: append.
   - There is no removal (to hide an item, override it with a no-op).
   - A Python resolver performs the merge, and the LLM applies the same rules by hand if Python is missing.
   - A conversational `bmad-customize` skill writes the overrides, so users never hand-edit TOML.
5. **Central config + roster.** `_bmad/config.toml` (installer-owned) plus `_bmad/custom/config.toml` (human-owned) hold install answers and an `[agents.<code>]` roster: name, title, icon, description, team. Party mode reads the roster, so a fictional or custom agent needs only a descriptor.
6. **Author discipline on knobs.** "Every customization knob you ship is a promise."
   - Three questions decide whether a knob earns its place: Does it vary across real users? Is it identity or consumed context? Would hiding it force a fork?
   - Naming conventions: `<purpose>_template`, `<purpose>_output_path`, `on_<event>`.
   - "Ship one good default over a permutation forest of toggles." https://bmad-builder-docs.bmad-method.org/explanation/customization-for-authors/
7. **Naming conventions.**
   - kebab-case, and the folder name equals the skill name.
   - `{module}-agent-{name}` for agents, `{module}-{name}` for workflows.
   - The `bmad-` prefix is reserved for official skills.
   - Old names stay as forwarders to the renamed skills. https://bmad-builder-docs.bmad-method.org/reference/builder-commands/
8. **Manifests and versioning.** v6 `_bmad/_config/manifest.yaml` tracks every module's version and source. v7 `bmod.toml` lists skills, required skills with versions, the update source and migration files. https://docs.bmad-method.org/customize/add-modules/
9. **Anti-zombie registration.** Re-running setup first deletes all of a module's old rows, so setup is idempotent and stale entries never pile up.
10. **Output layout as shared state.** Every artifact lands in `<type>-<slug>/` inside an "active initiative" folder. Skills find each other's outputs by type pattern (`brief-*`, `prd-*`, `spec-*`, `research-*`). https://docs.bmad-method.org/plan/choose-a-planning-path/
11. **Quality gates on the ecosystem itself.** Lint scripts, a Validate Module step (checks for orphan CSV rows, duplicate menu codes and broken before/after references) and evals keep a large library from rotting.
12. **Less context, kept true.** BMad's own "Theory of Project Context" cites evidence that bloated AGENTS.md files hurt: no gain, and +20% cost. A small, verified index of knowledge the model lacks helps. Each line must "change agent behaviour"; refresh and audit commands only shrink the file. https://docs.bmad-method.org/existing-codebases/theory-of-project-context/

---

## Q3. What maps to QMX

### Organogram BMad's approach would suggest for trading research
BMad's pattern: a few **named personas as front doors**, each with a **menu** that forwards to **shared workflows**, plus one **hub/router**, plus **review panels** built from lenses. Translated to QMX (names are placeholders):

| Role (persona) | Front door for | Menu forwards to (shared workflows) |
|---|---|---|
| **Copilot / hub** (the `bmad` equivalent) | Daily driver, "what next?", status, routing | Every other skill; reads the Library and Lab state to rank next steps |
| **Research Analyst** | Ideation, market/regime research, literature | idea-forge, deep-research, hypothesis-brief |
| **Quant Researcher** | Hypothesis → spec → build | strategy-spec, build-strategy (code / node / notebook), backtest |
| **Validator / Skeptic** | Robustness | walk-forward, Monte Carlo, overfit and leak checks, out-of-sample gate |
| **Risk Officer** | Sizing and risk limits | risk-review, sizing-check (deterministic scripts; authority = existing risk docs) |
| **Portfolio Manager** (Portfolio copilot) | Combining strategies | correlation, allocation, portfolio backtest, promotion to Library |
| **Lab Assistant** (Lab copilot) | Notebook, node editor, code experiments | experiment-run, explain-result, convert notebook → node or strategy |
| **Librarian** | Strategy Library hygiene | catalogue, dedupe, tag, retire |
| **Toolsmith** | Building new skills/agents | QMX builder (see below) |
| **Trader agents** (autonomous, PULSE-style) | Scheduled watch/act within limits | read-only monitors by default; actions gated by deterministic risk checks |

- BMad's "agent-first thinking" warns against too many agents. A plain copilot, a Lab copilot and a Portfolio copilot can be **one hub plus two personas**. Analyst, Quant, Validator and Risk can start as **menus and lenses**, not separate always-on agents.
- Review lenses suit trading well. Examples: a "Strategy Review Crew" (overfitting hunter, data-leak hunter, regime skeptic, cost/slippage realist, pragmatist), and the Anti-Consensus Club for go/no-go calls.

### Daily-driver copilot methodology (from the BMad hub + agent activation)
- Activation order:
  1. Resolve customization.
  2. Prepend hooks.
  3. Adopt persona.
  4. Load persistent facts.
  5. Load config + active workspace.
  6. Greet.
  7. Append hooks.
  8. Dispatch the user's intent directly if it is clear; otherwise show the menu.
- Intent-before-ingestion, soft gates, and capture-don't-interrupt.
- The hub recommends the next step by **scanning artifacts on disk** against a capability graph, not by remembering.
- Persistent facts plus a small curated memory (≤200 lines) and session logs that are curated, not loaded.

### Workflow templates
- Use BMad's three tiers (utility / simple / complex router) plus the document-as-cache resume pattern.
- A QMX research pipeline is a capability graph: idea → hypothesis → spec → build → backtest → validate → portfolio → library. `required=true` marks the gates (for example, validation before portfolio). Completion is detected from artifacts.
- The plan-file status state machine and "deferred findings" output from `bmad-build-auto` map directly to unattended backtest and validation runs.
- **bmad-loop** shows the right shape for unattended work: "No LLM in the control loop." Plain code picks the next item, sets budgets, runs verify gates and decides completion. LLMs only do the creative step, in fresh sessions. Review runs in a fresh context, optionally on a different model. https://github.com/bmad-code-org/bmad-loop
- This fits QMX's need for deterministic and mixed graphs, and matches the LangGraph shift.
- **bmad-manticore** is a non-software BMad module, an AI video production pipeline. It shows the pattern outside coding: a gate for every "taste decision", previews at each step, all external tools optional, and "post-publish notes edit the pipeline's own files" (the pipeline learns from its retros). https://github.com/bmad-code-org/bmad-manticore

### A builder that turns a rough description into a skill or agent
- Copy the **six-phase conversational build**: discover intent, classify, gather requirements (including read/write/deny "folder dominion"), draft, build with a deterministic lint gate, then quality-optimize.
- Copy the agent-type detection by natural questions ("does it need to remember?", "should it act while you're away?").
- Copy the input kinds: a rough idea, edit an existing skill, convert a foreign one.
- Copy YOLO / Guided / Headless modes.
- Add **evals**: trigger evals plus artifact evals, run in a clean room. This is how a user-built skill is proven before it joins the Library.

---

## Q4. What NOT to copy

- **The agile delivery chain**: sprint planning, sprint status, epics/stories/tickets (`bmad-ticket`, `tickets.toml`), retrospectives on epics, correct-course, PRD/PRFAQ/product brief as delivery documents. QMX researches strategies; it does not ship software increments.
- **Software-team personas** (PM John, Dev Amelia, UX Sally, Architect Winston) and their menus.
- **Step files (Layer 4) as the default.** BMad itself now calls them rigid. Keep them only for compliance-style flows, such as a pre-live checklist.
- **Claude-only or IDE-only pieces**:
  - party-mode `agent-team` (Claude Code only);
  - evals that run `claude -p` and watch the "Skill tool";
  - the `.claude-plugin/marketplace.json` naming (BMad says it does not need Claude, but the name is Claude-shaped);
  - skill-folder conventions tied to IDE directories (`.claude/skills`, `.agents/skills`).
  QMX is its own app and owns its own skill registry.
- **The "Sacred Truth" / "sleep, not death" persona mysticism** in memory agents. Keep the mechanics (sanctum files, wake, curation), not the theatre.
- **Persona-heavy defaults** for money-path agents. Trading agents should be terse and evidence-led. BMad's own note, "keep phrasing that captures the intended voice", is for companions.
- **v7 churn.** v7 is alpha, Toolsmith docs are unwritten, and the module format just changed. Borrow concepts, not file formats.

---

## Q5. How BMad stays model-agnostic

- **Plain Markdown + TOML + Python**, following the open Agent Skills standard. Any agent that can read files and run a command can execute a skill. https://bmad-builder-docs.bmad-method.org/explanation/what-are-skills/
- **The installer targets many tools.** Skills land in each tool's own directory (Claude Code, Cursor, Windsurf, Codex, Cline, Antigravity and others), and the content is identical. https://docs.bmad-method.org/reference/skills-and-agents/
- **Graceful degradation everywhere**:
  - If scripts cannot run, the LLM does the work by hand.
  - If the resolver is missing, the LLM merges the three TOML files with the same rules.
  - If subagents are unavailable, work runs sequentially.
  - Party mode falls back from agent-team to subagent to session.
- **Determinism lives in scripts, not in model behaviour**, so results depend less on which model runs.
- **Cross-platform scripts**: Python, not Bash; standard library first.
- **bmad-loop** runs any of six coding CLIs (claude, codex, gemini, copilot, antigravity, opencode) as TOML profiles, mixable per stage, with cost-weighted budgets. Review can use a different model from implementation.
- **The builder says that tuning varies by model**: "different models and tools may need more explicit guidance". Evals are how you check a skill on a new model.
- **A weak spot**: the eval runner and some modes are Claude-specific. QMX should build its own eval harness against its own model adapter.

---

## Ideas for QMX

1. **Make "skill" the one unit for every agent, workflow and tool**: a folder with SKILL.md + optional scripts/references/templates. *Why*: one format keeps a large Library composable and lets the builder target a single shape.
2. **Persona = identity + menu that forwards to shared workflows.** *Why*: the Lab, Portfolio and plain copilots stay thin, and work is never duplicated across personas.
3. **One hub copilot that routes by scanning artifacts on disk against a capability graph.** *Why*: "what next?" stays correct without fragile model memory.
4. **A capability registry with `preceded-by`, `followed-by`, `required` (gate), `output-location` and `outputs`.** *Why*: this encodes the idea→library pipeline and its validation gates as data, which LangGraph can also read.
5. **Three-layer overrides (shipped defaults → workspace → personal), merged by value shape, edited through a conversational "customize" skill.** *Why*: this satisfies the "everything UI-editable, nothing forked" rule.
6. **A strict determinism boundary: backtests, metrics, risk and sizing checks are scripts; the LLM only interprets.** *Why*: money-path numbers must be reproducible and testable.
7. **Deterministic orchestrator, LLM workers (the bmad-loop shape) for autonomous workflow and trader agents.** *Why*: budgets, gates and completion are decided by code, never by model prose.
8. **Plan-file status state machine plus a "deferred findings" output for unattended runs.** *Why*: runs become resumable, inspectable and safe to leave overnight.
9. **Document-as-cache: each research artifact's frontmatter holds its inputs and stage.** *Why*: long Lab sessions survive context compaction and model swaps.
10. **Review panels as saved parties of lenses (overfit hunter, leak hunter, regime skeptic, cost realist), run as independent agents.** *Why*: independent voices catch more than one model playing five roles.
11. **Memory agents with a small curated MEMORY (≤200 lines), session logs curated rather than loaded, and memory stored outside the skill.** *Why*: copilots remember the operator without context bloat or self-editing.
12. **A QMX Builder: six-phase conversational build, YOLO/Guided/Headless modes, a deterministic lint gate, and quality scanners.** *Why*: the operator can describe a skill roughly and get a correct one.
13. **Evals for every user-built skill (trigger + artifact, clean room, grader cites evidence).** *Why*: this is how a new skill earns a place in the Library, and how it is re-checked when the model changes.
14. **Folder dominion (read, write, deny zones) declared per agent.** *Why*: trader and autonomous agents get hard boundaries away from broker credentials and live accounts.
15. **Every subagent or advanced feature declares a sequential fallback.** *Why*: QMX stays model-agnostic and works on weaker or local models.
16. **Keep agent context small and verified: only facts the model lacks, audited to shrink.** *Why*: BMad's cited evidence says bloated instruction files add cost without improving results.
17. **Use human taste gates at each stage (from Manticore): previews, with the operator approving every judgment call.** *Why*: this suits "vibe coding for trading strategies" while keeping the operator in charge.
18. **Expansion modules must degrade gracefully when the parent is missing.** *Why*: mini apps and community add-ons can install without breaking the core.
