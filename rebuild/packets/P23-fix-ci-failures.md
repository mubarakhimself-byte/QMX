# P23: Fix the two recurring CI failures

## Goal
`just ci` passes with zero failures on Windows and Linux. Two failures have shown up in every recent run:
1. **Watcher startup timeout:** the `weekend-watcher` example app (P12) sometimes misses its startup deadline under load. P22 reproduced it on a clean base. The reproduction command is in PR #43.
2. **Linux-only failure:** a test fixture runs the Windows-only command `cmd /c mklink`. It was reported in PR #40/#41.

## Steps
1. Reproduce both with the commands from PRs #40, #41 and #43.
2. **Watcher:** find why startup is slow (dependency import, venv creation, first-run lock, fixed short deadline).
   - Fix the cause.
   - If the startup budget is too tight for a loaded laptop, make it a named, configurable value with a sensible default (for example 30 s). Assert on readiness events, not on wall-clock sleeps.
   - Do not just raise a number without explaining why in the PR.
3. **mklink fixture:** use a cross-platform way to create the link (`os.symlink`, falling back to a junction or copy on Windows without privilege), or mark the test Windows-only with a clear reason if it tests Windows behaviour specifically.
4. Run `just ci` three times in a row. All three must pass.

## Done when
Three consecutive green `just ci` runs, with the summaries pasted in the PR.
