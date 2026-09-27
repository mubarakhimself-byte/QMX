# Unattended adapters

Upstream BMAD skills stay unmodified for other sessions. This factory
runs **adapters**. Do not claim an unmodified interactive skill ran.

## bmad-build

Interactive checkpoints (greet, numbered questions, `open_spec`,
sprint-status, "find at least ten issues") become:

- Intent = the story record (id, brief, AC, sources, components, design
  refs, files). If a required field is missing, `validate-inputs` already
  blocked the unit.
- Context = `docs/AGENTS.md`, ADR-0026, `docs/lenses/ui/`, this
  `design-system-entry.md`.
- Implementation = one `build:` agent in `ui-epic-build.rhai`.
- Completion = `story N.N:` commit. No editor launch.

`bmad-build-auto` is a nested development loop. Do not start it from
this orchestrator.

## bmad-code-review

Use layer prompt files (`edge-case-hunter.md`, `verification-gap.md`) as
read-only recipes. Disable the quota "find at least ten issues". Empty
blocking list is valid after inspecting `git diff ui-integration...HEAD`.
Each blocking item needs file:line evidence. Advisory items stay in the
report and do not silently vanish from `all_green` (they are listed;
they do not flip green to green-without-trace).

## testarch-framework / testarch-ci

One-time setup for the host app and `.github/workflows/ui-quality.yml`.
Do not re-init Playwright on every story.

## testarch-atdd / test-design

Use when a story's AC cannot be executed yet. Output fixtures into the
worktree. Skip if AC already map to vitest/playwright IDs.

## qa-generate-e2e-tests vs testarch-automate

Pick one generator per gap. Prefer extending existing Playwright specs.

## Reticle family

Prefer MCP `reticle_act_and_wait` / `reticle_assert`.
`verify-unattended` CLI is allowed when MCP tools are absent and must be
labeled CLI-not-MCP. Workspace rule: user-facing promotion still needs
`verified: "yes"`. `unknown` stays incomplete.

## Interactive leftover

If a skill still demands a human choice that specs already answer, take
the spec. If specs conflict, block the unit (`incomplete` /
`blocked`) and continue independent work.
