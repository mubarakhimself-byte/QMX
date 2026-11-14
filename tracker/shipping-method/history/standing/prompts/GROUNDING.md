# Grounding agent prompt (step 0)

Used twice: by PLAN-REVIEW against the parent tip, and by COORDINATOR at arm time against the build branch tip. The session fills the {PLACEHOLDERS} and spawns one background agent (`subagent_type: "poteto-agent"`, `model: "opus"`). For more than about 15 briefs, split the slices into groups of related ones, one agent per group, each with its own report file.

---

Read the poteto-mode skill's `SKILL.md` in full, including its Principles section, before any work. Do not spawn sub-agents.

You ground the briefs of program `{PROGRAM}` against the code at `{TIP}` (`{TIP_NAME}`), before any builder starts. Your slices: {SLICE_IDS}.

Read first: `{PROGRAM}/PROGRAM.yaml`, `{PROGRAM}/SCOPE.md`, `{PROGRAM}/SLICES.md`, `{STANDING}/PROJECT-RULES.md`, and each of your slices' `slices/<id>/BRIEF.md`.

Make a detached checkout at the tip: `git -C {REPO} worktree add --detach {CHECKOUT} {TIP}`. Read code only there. Remove it with `git -C {REPO} worktree remove {CHECKOUT}` when done.

For every brief, check:

1. Run each fact block's command in the checkout and compare its output with the expected output exactly, as the dispatch script will.
2. Compare the Files block with what the change forces: pins, counts, census rows, schema copies, reason-code lists, version rows, `app.toml`, `uv.lock`. Grep for every symbol and value the brief changes, and every caller.
3. Look for collisions with code that already exists, where the brief builds something the tip already has or contradicts it.
4. Look for collisions between slices, where two briefs change the same symbol or file with no `depends on` edge between them.
5. Read for clarity. Flag anything a builder could read two ways, any literal a test could not assert, and any named skill that spawns agents (`arena`, `swarm`, `interrogate`, `no-comments`, `code-review`).

A mismatch is never fixed from the code alone, because the code may be wrong. For each one, read the intent behind the brief (the decision files PROGRAM.yaml lists, then the planning session's transcript by search under `C:/Users/Mubarak/.claude/projects/`), and the intent behind the code it collides with (that PR's body with `gh pr list --search <sha> --state merged`, and its plan section). Check the blast radius of each way to resolve it. Then sort it:

- **Mechanical.** Both intents agree, and only a name, path or value moved. Correct the brief (and the files column of `SLICES.md`) yourself, and rerun the fact until it passes.
- **Design call.** The intents differ, or the blast radius reaches beyond the slice. Change nothing; list it.

Write `{REPORT}`. One section per slice: each check with PASS, FIXED (old line, new line, the command that proves it) or CALL (both intents quoted with their source, the options and each option's blast radius). End with a list of every CALL, one line each, and the line `END {TIP} grounding`.

Reply with only the report path, the count of slices with no change, FIXED and CALL, and the slice ids with a CALL.
