# QMA v2 architecture brief (shared by every design runner)

This brief exists so each runner starts from the same inputs. Planning only.
- Runners write no product code, make no commits, and spawn no sub-agents.
- Runners never run `git checkout`, `git switch` or `git reset` in `D:\QMX-worktrees\agent-system`. Read code with `git show origin/rebuild/base:<path>`.
- Never read, print or ask for credentials.

## The operator and the goal

- One non-technical operator, a solo quant trader.
- QMX is a Windows desktop trading-research workbench. The backend is Python 3.14 (FastAPI `qmx-control`). The UI is SvelteKit, shipped first as a browser app.
- He wants the agent system rebuilt as **QMA v2** ("Quant agents"): designed for complexity, no stone unturned, a clean starting point for coding on 2026-10-13.
- **Wednesday minimum:**
  - the copilot works;
  - he can create, run, maintain and edit mini apps and workflows (agentic, non-agentic and mixed);
  - the organogram works;
  - sub-agents work;
  - workflows can run off his machine.

## Inputs (read all, in this order; paths relative to `D:\QMX-worktrees\agent-system\`)

1. `tracker/qma-v2/README.md`: the planning order, the re-run rule, the pass log.
2. `tracker/qma-v2/PRD.md`: 148 FRs (81 WED), 39 NFRs, constraints, glossary, port list, questions (§9.1 belongs to the operator; §9.2 is for the architecture to answer).
3. `tracker/qma-v2/HOW-WHY.md`: pass 1 plus "Delta pass 2". It says what exists, what can be reused, why the code is shaped as it is, conflicts X1-X14 with resolutions, and facts G1-G15 the design must not get wrong.
4. `tracker/qma-v2/USER-JOURNEYS.md`: 21 journeys, 25 spin ideas, coverage gaps, the Wednesday demo script.
5. `tracker/agent-system/research/`:
   - 30 (databases)
   - 31 (tools, skills, prompts, comms)
   - 32 (DevOps and UI protocol)
   - 19 (two-SDK study: the Engine mapping and mismatches; ignore its "keep LangGraph")
   - 21 (mini-app and workflow seeds)
   - 22 (cookbook templates and system-prompt rules)
   - 24 (integration surface)
   - 01 (Claude Agent SDK audit)
   - 05 (usage telemetry)
   - 20 (direction; §4 overrides §1-3)
6. `rebuild/research/2026-10-12-agent-system/models-routing.md`: vendor terms, Sign in with ChatGPT.
7. The operator's clippings in `C:\Users\Mubarak\Documents\brain\brain\Clippings\`. "Agent Harness Engineering vs. Loop Engineering vs. Graph Engineering.md" is his chosen building block for QMX workflows. Also read the loop-vs-graph, self-improving-quant-loop, "Not Every Agent Workflow Needs AI" and "The Loop Runs While You Sleep" clippings.

## Ratified constraints (never reopen)

**Engines**
- Two engines sit behind one QMA `Engine` interface.
- **Claude Agent SDK:** Claude Code's capabilities, never the CLI. Only on his **Max 5x subscription**: never Anthropic API spend.
  - It uses a custom QMA system prompt, `setting_sources=[]` and its own `CLAUDE_CONFIG_DIR`.
  - Each session is one child process of about 1 GB.
- **OpenAI Agents SDK:** in-process, any OpenAI-compatible provider by API key, with no limit on providers.
- **GPT** only through his ChatGPT subscription ("Sign in with ChatGPT"); never OpenAI API spend.

**Building blocks**
- **Plugins** (tools/MCP, skills, model, hooks) are the unit of the organogram. The Claude plugin format is the standard. A loader carries plugins into the OpenAI SDK, and a cross-engine delegate ships as a plugin.
- **QMA's own graph and loop engine.** No LangGraph. Keep the `workflow.v1` JSON format. Deterministic work first; an agent is a property of a node.
- **The router** balances usage across accounts and sessions, never single requests. It replaces CLIProxy.
  - Model switching mid-conversation is allowed, with a cost-confirm step.
  - The orchestrator reads router status through a tool.
- **Approvals:** policy lives in QMA's own tool wrappers. There is one approval queue. The approval, credential and terminal routes are REST-only (G1).

**Rules and limits**
- No modes.
- **Money-path barrier:** agents never place live orders, size positions or touch the kill switch; they propose. Live-account testing gets a seam only.

**Placement**
- His Windows PC, plus **rented on-demand compute from several providers** (qmx-remote). **No owned server.**
- No sandboxes by default.

**Code and docs**
- Branch: ship into **`rebuild/base`** for now; `integration` is not ready. `main` moves only by his click.
- Code quality and **live documentation** during shipping.

**Out of scope (named seams only):** the Library (git-style object model in SQLite as the seam), QMB, QML changes, WF1/WF2.

## Required output of a design runner

Follow the pstack `/architect` skill: `~/.claude/skills/architect/SKILL.md`, `references/runner-prompt.md`, `references/rationale-template.md` and `references/design-red-flags.md`. Phase A grounding is already done (HOW-WHY and the research); add targeted reads only where you doubt a fact.

**The design package must contain:**
- a whole-shape design: module boundaries, plus Python types and signatures with `...` bodies;
- each of these areas:
  - Engine, SessionRef
  - plugin loader
  - router and accounts
  - prompt assembly
  - memory
  - approvals and policy
  - effects ledger
  - graph and loop runtime
  - triggers and scheduler
  - mini apps
  - sub-agents and the comms broker
  - orchestrator
  - placement and remote runs
  - the DevOps planes
  - the event protocol to the UI
  - concurrency and variants
  - self-improvement
  - storage
  - security
- the existing code each part keeps, rewraps or replaces;
- the red-flag screen;
- interface depth;
- the risks.

Answer every PRD §9.2 question.
