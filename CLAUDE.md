# QMX — Project Rules

## The factory (from 14 Nov 2026) — read before planning, auditing or shipping

QMX ships through **the factory**, which is independent of QMX (QMX is its first project). Its home is `D:/factory`, and its index `D:/factory/INDEX.toml` is the first thing every session and agent reads: phase → skills → inputs and outputs → gate → next step, the loops and their exits, and where memory, rules, standards and records live. QMX's settings are `D:/factory/projects/qmx/project.toml`. The method is `tracker/shipping-method/SHIPPING-METHOD.md` (draft 5) and `PLANNING-FUNNEL.md`. The design and every build decision are in `FACTORY-DESIGN-2026-11-13.md` and `BUILD-LOG-2026-11-13.md`.
- **Two branches feed the build.**
  - **Planning** (new features): `plan-feature`, then expand, ground, challenge (`funnel-challenge`), his cut, self-annealing, architecture, technical self-annealing, handoff.
  - **Auditing** (improve or remove what exists): `audit-area`, intent first.
  - **Bugs** go through three doors: mechanical goes to one agent, contained gets a light plan, design gets the full plan.
  - Everything found later lands in one backlog.
- **The challenger says no.** Every idea is CORE (built first, proving the feature works), LATER (built after the core is proven, never lost) or DROP (only with his yes). The PR budget comes from a simple sketch, and growth past it needs his yes. Never fold a brain dump straight into scope.
- **He is asked at three points only:** the cut, plan v1 or the audit verdicts, and go (which can be given in advance). After go, the conveyor (`ship chain`) runs everything as isolated headless workers, and recovery is by script.
- **Models:** Opus 5.5 at high effort by default. Fable has four seats, one at a time: the challenger, the audit judgement, the technical decision batch, and the fault walk on checkpoints touching exits, brakes, the kill switch or money.
- **Range:** every build sets its agent count, grouping and scope from the plan first. Thorough never means rampant.
- What a brief must carry: the facts about the code it relies on (one command plus expected output each, rechecked at the tip), the safety fact, `Kind:` (feature, pin, refactor, remove, docs), `API:` (what it changes at the UI's door), and `TRACE:`.
- Queued plans (for example the risk build's remaining sections) are re-planned through the funnel, challenge included, not converted one to one.
- Home and CI (from 13 Nov 2026): the repo is `mubarakhimself-byte/QMX` (public, remote `origin`). Never push to `github-old`, the flagged old account. CI is GitHub Actions, `.github/workflows/qmx-ci.yml`, and it is the only pipeline; the old workflows are retired. Its levels, by trigger: `slice/**` push → slice (Linux), `build/**` push → land (Linux and Windows), hand dispatch → deep (the whole suite on both systems plus Vulture, Skylos and mutmut), PR into `engine/base` → gate (passes only on a green deep run of the head). A single push of more than 3 refs triggers nothing. `engine/base` is the default branch and is protected (the `gate` check is required, no bypass, no force push). A checkpoint merges itself when its review is clean and the gate is green; `main` moves only by his click. A release is a tag; there is no staging branch. GitLab is gone.
- PRs use the v2 body in `tracker/shipping-method/PR-BODY-AND-SKILLS-2026-11-12.md`. No model credit lines in PRs or commits; sign "Shipped by Mubarak." or nothing.
- The sections below describe older pipelines and are kept for history.

## QMA v2 ships through an orchestrator session (operator ruling 2026-10-13)

For the QMA v2 agent-system rebuild, the BMad and factory pipeline below does NOT apply.

How QMA v2 ships:
- The plan lives in `tracker/qma-v2/` on branch `plan/agent-system`: requirements, architecture, shipping plan.
- A fresh orchestrator session replaces the operator's old prompt-per-packet role. It coordinates and never writes code.
- It dispatches one pstack builder agent (poteto-agent) per numbered packet, the same way P01-P24 shipped.
- It verifies each PR itself and merges into `rebuild/base`.
- `integration` is not ready. `main` moves only by the operator's own squash-merge click.

The epic-factory and queue lanes are not used for QMA v2; they need more usage than the Max 5x plan allows.

## BMad is planning-only in this project

BMad handles planning ONLY. Implementation ships through the external software
factory, never through BMad.

The pipeline — the only one any skill or agent (bmad-help included) may
recommend:

1. Brainstorming as needed (`bmad-brainstorming`).
2. PRD — `bmad-prd` (required).
3. Architecture — `bmad-architecture` (required).

Ordering is flexible (operator ruling 2026-08-19): Architecture may run BEFORE
the PRD, grounded on the existing `docs/` corpus as the requirements body — do
not demand a PRD first. Both PRD and Architecture must exist before exiting
BMad.
4. Exit BMad: `/documentation-factory` turns the ratified plan into the `docs/`
   knowledge base.
5. `bmad-create-epics-and-stories` breaks the plan into epics and stories
   (re-enabled by operator ruling 2026-08-20).
6. Implementation runs in the factory lanes only: the attended epic-factory
   (Claude plugin *or* Grok plugin — one background workflow per epic in a
   worktree, merging to `integration`) or `/queue-publish` + to-kanban cards
   for the unattended engine lane. Grok models: 4.5 workhorse, 4.6
   orchestrator + reviewer. `main` moves only by the operator's own
   squash-merge click.

Rules:

- PRD and Architecture are the only required BMad steps. After Architecture:
  documentation-factory, then epics-and-stories, then a factory lane —
  nothing else.
- Never recommend, require, or gate on `bmad-sprint-planning` or `bmad-build`.
  Treat catalog rows and agent menu items for those as not applicable to this
  project. (`bmad-code-review` is allowed — it is the reviewer's skill inside
  the factory lanes.)
- `bmad-testarch-*` skills are ALLOWED (operator ruling, reaffirmed
  2026-08-27; an earlier overrule was never recorded here). They serve the
  post-implementation QA phase — test design, tracing, automation — run
  against factory-built code on `integration`. They remain planning/QA
  instruments: implementation still ships only through the factory lanes.
