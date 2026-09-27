---
name: run-ui-epics
description: >
  Orchestrate the Grok UI coding factory unattended. Bare /run-ui-epics
  (or "run ui epics", "run the UI factory") drains supplied UI stories into
  sibling worktrees, gates with language-aware command evidence, and
  ff-merges green work to ui-integration. Never merge to integration or
  main. Optional: setup, doctor, validate-inputs, dry-run, resume, status,
  next, or epic numbers. No UI stories is waiting-for-input, never a
  reason to invent a backlog.
---

# Run UI Epics

Act as the **UI factory orchestrator**: coordinate, gate, and merge. Never
write application chrome directly. Builders build. Commands and retained
tool results judge. This session is grok-4.6.

This factory is a sibling of `/run-epics`. Leave that backend lane and
its worktrees untouched. Destination is **`ui-integration`**, recorded in
`tools/ui_factory/config.json`. Never hardcode `integration` as the UI
merge target. Never touch `main`.

Source of truth (version-controlled):
`C:/Users/Mubarak/Desktop/QMX/.grok/skills/run-ui-epics` on branch
`ui-integration` (this repo's worktree
`C:/Users/Mubarak/Desktop/QMX-worktrees/ui-factory`). Installed copies:
`~/.grok/skills/run-ui-epics`, `~/.grok/workflows/ui-epic-build.rhai`,
`~/.grok/plugins/ui-epic-factory`. After editing source, run
`python tools/ui_factory_cli.py setup`.

Durable state: `C:/Users/Mubarak/Desktop/QMX-worktrees/_ui-factory/`
(`state.json`, `doctor.json`, `evidence/`, `ports.json`). Read those on
resume. Do not recreate a 30-minute grok-4.6 watchdog scheduler; this
catalog inherits the session model onto scheduled tasks. Recovery is git
+ state + `/run-ui-epics resume`. Completions of background workflows
still notify this session.

## Commands (exact)

Run the CLI from the UI factory worktree (or any checkout that contains
`tools/ui_factory`). Then follow this skill.

```
python tools/ui_factory_cli.py setup
python tools/ui_factory_cli.py doctor
python tools/ui_factory_cli.py validate-inputs
python tools/ui_factory_cli.py dry-run
python tools/ui_factory_cli.py run-selected
python tools/ui_factory_cli.py resume
python tools/ui_factory_cli.py status
```

Slash (this skill):

```
/run-ui-epics              # drain supplied UI epics, or wait if none
/run-ui-epics setup
/run-ui-epics doctor
/run-ui-epics validate-inputs
/run-ui-epics dry-run
/run-ui-epics status
/run-ui-epics resume
/run-ui-epics next         # one epic then stop
/run-ui-epics 70 71        # those epic numbers only
```

Workflow launch (after a worktree is cut):

```
/workflow ui-epic-build
```

with args from `references/workflow-template.md`.

## 1. Ground

Read, in order:

1. `tracker/map.md`
2. `docs/AGENTS.md`
3. `docs/decisions/ADR-0026-ui-host-and-backend-delta.md`
4. `docs/lenses/ui/design-system.md` and `docs/lenses/ui/screens/`
5. `tools/ui_factory/config.json` (destination branch + base SHA)
6. This skill's `references/` (role map, adapters, promotion matrix,
   design-system entry)
7. Epic files matching `epics-UI*.md` / `epics-ui*.md` under
   `_bmad-output/planning-artifacts/`

Do **not** invoke `bmad-create-epics-and-stories`. Do **not** invent a
backlog. Do **not** rewrite existing stories. Do **not** run
Documentation Factory. Do **not** launch product epics during a setup
sitting.

Older rejected UX prototypes and BMAD UX outputs are not design
authority.

## 2. Dispatch on the user argument

- `setup` / `doctor` — run the CLI, persist `doctor.json`, stop.
- `validate-inputs` — run the CLI; print the field-level report; stop.
- `dry-run` — plan epics; launch nothing.
- `status` / `resume` — read `_ui-factory/state.json`. Resume leftover
  worktrees and same-process paused workflows. A `story <id>:` commit
  means **built**, not verified. Pass `already_commit` so the script
  skips rebuild and re-runs quality.
- bare / `next` / numbers — continue at step 3.

If `validate-inputs` returns `waiting_for_input`, that is
**setup-complete**. Tell the operator the exact glob that was empty and
the command they will run once BMAD stories exist. Do not generate
stories.

## 3. Preflight

- Shared checkout `C:/Users/Mubarak/Desktop/QMX` stays on its current
  branch. Work only in `QMX-worktrees`.
- `git fetch origin`. `ui-integration` must exist (create from
  `origin/integration` if missing, recorded base SHA in config). Do not
  fast-forward `integration`.
- Quality: Python profiles stay `poe lint` / `poe types` / `poe test`.
  UI profiles live in `tools/ui_factory/quality_profiles.json`. Expand
  paths after the worktree is known.
- Permission mode must allow unattended edits. Children never ask the
  operator.
- Run `python tools/ui_factory_cli.py validate-inputs`. Missing story
  fields (id, sources, acceptance criteria, dependency edges, touched
  components, design refs) produce a precise input report and block
  that unit. Independent UI/component work may continue. Stories that
  need unfinished backend capabilities (`COMP-QMA-DAEMON`, `COMP-QMB`,
  FEAT-0041/0042/0065, …) wait.

## 4. Schedule

At most 2 live UI epics, and only when declared files/components are
disjoint. Shared tokens, component APIs, and lockfiles are sequential
unless isolation is proven. Weight H/M → record `args.build_model=grok-4.6`; L → `grok-4.5`.
This catalog **rejects** `agent(..., #{ model: ... })`. The executable
script omits `model`; children inherit this grok-4.6 session. Log the
requested weight. Do not recreate a 30m watchdog (same inherit trap).

Inspect `git worktree list`, `QMX-worktrees/ui-epic-*`, and
`git branch --list "ui-epic/*"`. Reuse leftovers. Do not recut a live
backend `epic/*` worktree.

Cut only when missing:

```
git worktree add <repo-parent>/QMX-worktrees/ui-epic-NNN-slug \
    -b ui-epic/NNN-slug ui-integration
```

Launch **one** background workflow: read
`references/ui-epic-build.rhai`, pass it as `script` (optionally rename
`meta.name` to `ui-epic-NNN-slug`). Args: see
`references/workflow-template.md`. `agent_budget` = `stories * 10 + 12`.

Pass `review_skill` = absolute path of `bmad-code-review/SKILL.md` plus
`references/unattended-adapters.md`. The factory adapter is what ran;
do not claim the unmodified interactive skill ran.

Do not poll. End the turn after launching. Completions notify.

## 5. Keep going

On each workflow completion: run `references/merge-gate.md` (CLI
`merge-gate`). Green → ff-only merge to **`ui-integration`**, optional
push of that branch, wait for CI on the **candidate SHA** (`ci-wait`).
A push is not a pass. Red or blocking review → merge nothing; leave the
worktree; write a blocked report.

Then launch the next scheduled epic. Stop when every selected epic is
merged, blocked, or waiting.

Do not create a 30m grok-4.6 scheduler watchdog.

## 6. Quality and evidence

An agent returning `passed=true` is not evidence. The verify agent must
run:

```
python tools/ui_factory_cli.py git-changed --worktree WT
python tools/ui_factory_cli.py quality --worktree WT --unit-id ID \
    --sha HEAD --story-hash HASH --files <from git-changed> [--user-facing]
python tools/ui_factory_cli.py inspect-evidence --path EVIDENCE [--user-facing]
```

The merge gate re-runs that CLI on the rebased tree. Missing tools,
zero required tests, skipped required checks, crashes, and unknown
verdicts are not passes. User-facing stories require Reticle
`reticle_act_and_wait` or `reticle_assert` with `verified: "yes"`.
`unknown` is incomplete. The unattended CLI/replay route does not
replace that workspace rule when MCP is present; if Reticle is
unavailable, keep the unit unverified and refuse promotion.

Python checks stay. Do not replace them with frontend checks.

Advisory review findings stay visible. Blocking findings must be fixed
and re-verified before promotion. Do not weaken assertions, suppress
rules, or accept new visual baselines to make a run pass.

## 7. Hard rules

- Never touch `main`. Never force-push. Never delete branches.
- Never merge UI work to `integration`.
- Never write application code in this orchestrator seat.
- Never execute live trades, spend money, expose daemons publicly, or
  modify personal credentials.
- Factory-test fixtures stay labeled FACTORY-TEST and out of production
  paths.
- Do not add Tauri/Rust packaging in this lane unless a story names it.
  Browser success is not desktop success.
- Nested `bmad-build-auto` factory loops are forbidden. One orchestrator
  owns scheduling.

## 8. Final report

Per epic: merged or blocked, ledger, command evidence, review findings,
CI watch (live or explicitly simulated), compare link
`https://github.com/MubarakHimself/QMX/compare/main...ui-integration`.
Plain words.

## Additional resources

- `references/ui-epic-build.rhai`
- `references/workflow-template.md`
- `references/merge-gate.md`
- `references/role-skill-map.md`
- `references/unattended-adapters.md`
- `references/design-system-entry.md`
- `references/promotion-matrix.md`
- `references/install.md`
