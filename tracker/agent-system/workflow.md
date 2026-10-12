# How we use the skills, in order (planning → shipping)

The aim is to stop picking skills at random. **pstack's `/poteto-mode` already chains its skills inside its playbooks.** So we mostly invoke one playbook, and it runs `how`, `why`, `architect` and the rest in the right order.

The 24 principles do not have to be chosen by hand either. `poteto-mode` reads its principles index at the start of every task, opens the specific principle when a step needs it, and must name the principle it applied in its reply.

## A. Planning (now, with the operator)

| Step | Skill | What it does |
|---|---|---|
| 1 | Pocock **Wayfinder** map (this folder) | Organises the effort. One decision ticket at a time. |
| 2 | **`/grilling` + `/domain-modeling`** on every operator ticket (02, 03, 04, 06, 07, 08, 15) | The conversation that settles each decision. Charting skipped this step; it starts properly at ticket 02. |
| 3 | **`/how`** (and **`/why`** when it is about why something was built that way) | Run before any decision that touches shipped code: what the code does now, and the reasons from git history and PRs. Fresh background agent: Sonnet explores, Opus explains. |
| 4 | **`/architect`** | Only for tickets that define module shapes (04 tools, 08 memory, 11 events, 13 folders). It runs `how`/`why` itself, then one Opus design pass (arena is capped at one runner). |
| 5 | **`/poteto-mode` → multi-phase-plan playbook** | Once the decisions are made: writes the shipping plan file (ticket 16) under `/technical-writing`, checks it with its own script, then stops until the operator says go. |

## B. Shipping (tonight or overnight, after the operator's go)

| Step | Skill | What it does |
|---|---|---|
| 6 | **`/poteto-mode` → feature (or refactoring) playbook**, one packet at a time | `how` → `architect` → code written by a `poteto-agent` subagent on Opus → verify on the real surface → small ordered commits → `/interrogate` only if the design is contested → open a PR into `rebuild/base`. |
| 7 | Default: **sequential**. Overnight: **autopilot-stack playbook** | Builds and verifies a linear stack of PRs. It does not land them; the operator or the next step does. Parallel only when usage allows. |
| 8 | **Shipping playbook** | Every PR is verified independently, then the verified run is landed bottom-up into `rebuild/base`. "Green" alone is never trusted (the P16b lesson). `main` still moves only by the operator's own merge. |
| 9 | **session-pickup / pause-safely playbooks** | Resume a stopped session, or stop one cleanly before usage runs out. |

## C. After shipping (QA)

- **`/create-verification-skill`, then `/maintain-verification-skill`.** A QMX-specific skill that drives the real app through complex user journeys. Pair it with the UI wiring.
- **`/benchmark-checklist`** before trusting any measured number (latency, cost, cache hits).
- **`/teach`** if the operator wants a subsystem explained. Pocock's `tdd` vs pstack's `tdd` gets compared then (only Pocock's is installed).

## Not used by default

- **`arena` / `swarm`:** multi-model fan-out, high usage. `arena` runs only inside `architect`, capped at one runner.
- **`figure-it-out`:** the fallback when no playbook fits.
- **`no-comments` / Comment Sicko:** optional before a PR.
- **`typescript-best-practices`:** for the UI session (SvelteKit + TypeScript). The backend is Python.
- **BMAD:** not needed in this flow. The shipping plan replaces the architecture-to-epics step. The `docs/` update uses `/documentation-factory` (backlog), and the project's `CLAUDE.md` pipeline text should be updated to match.

## Model settings

Subagent roles are set in `~/.agents/pstack-models.md`: Claude only, Sonnet for explorers, Opus for judgment and code, and two reviewers for `interrogate`.

## Agreed operating terms (2026-10-12)

- **Decisions:** asked through the AskUserQuestion tool, each with a recommended answer and options.
- **Planning depth:** pstack skills run as dedicated background `poteto-agent` sub-agents, one at a time and sequential, told "planning only, write no code". Their output goes into the ticket's folder. Design for complexity. Each ticket also checks the research corpus for how others solved it (cookbooks, Hermes, Codex, big-company patterns).
- **Where work runs:** planning stays in the main session. Shipping runs in a separate session (one orchestrator, or one agent per slice) as soon as a slice is decided, while planning continues. The UI wiring track gets its own session later.
