# Rerun: research → architecture → plan (after the first engine build run)

The planning lead runs this in the ongoing session (ruling 101): no poteto-mode, no skills by default. The lead You never write product code. You run Opus agents, at most 3 at once, all in the background. Every brief says "do not spawn sub-agents". Fable is not used (ruling 87).

## Binding inputs (read first)

Everything is under `D:\QMX-worktrees\agent-system\tracker\qma-v2\`.

1. `research/methodology/26-operator-rulings-and-alignment.md`: rulings 1-97. The latest ruling wins, and this file outranks every other file.
2. `research/methodology/33-state-of-play.md`.
3. `WORKFLOW-SHIP-PREP.md`, the "mistakes not to repeat" list. Adapt it; don't follow it verbatim.
4. Memory rules (operator feedback):
   - Light verification: one build and one check per PR, one fix round, low findings are logged and never block.
   - No unplanned work during a run; findings go to the run's backlog.
   - Tests use haiku through the plan login. OpenRouter is used only to prove other providers work. There is no spend cap.
   - Don't resume stale agents after long gaps.
   - Output: interactive explainer pages, not walls of text.

## What already exists

- **The engine is built.** It is stacked as PRs on `engine/*` branches from `engine/base`, which sits at `ed704c92` on `rebuild/base`. The run's store is `D:\QMX-worktrees\qma-ship\engine\`:
  - `BACKLOG.md`: run findings;
  - `lows.md`;
  - `review/`;
  - `ledger.tsv`.
  
  Another session is reviewing that stack.
- **The three architectures** are in `architecture/workflow-engine/` (37 ADs), `architecture/library-and-data/` and `architecture/lab-and-pods/`.
- **The post-run work:**
  - `research/methodology/34-engine-run-triage.md`: 164 issues, sorted into classes;
  - `35-architecture-amendment-after-run.md`: an amendment already written into the engine architecture (AD-24 rewritten; new AD-36 money scan and AD-37 redaction; HG3 harness requests H2 and H18-H25);
  - `36-amendment-review.md`: an independent review of that amendment. It found 3 critical holes, which are **not yet applied**:
    - agents keep PowerShell and Monitor;
    - the money-scan verb rule is undefined;
    - 10 of the 31 templates break.

    It also gives verdicts on open decisions D, E and F.
- **New research:**
  - `37a-hermes-architecture-loop.md`;
  - `37b-hermes-extensibility.md`;
  - `37c-hermes-operations.md` (may still be landing);
  - `38-provider-routing-options.md`: Claude goes through the plan, GPT through its lane, and third-party models through a pool. Candidate pools: opencodex (https://github.com/lidge-jun/opencodex, the operator's preference), CLIProxyAPI, a hybrid, or Hermes as a provider. This file may also still be landing.

## The steps (the same workflow as 2026-10-16, Opus in place of Fable)

1. **Finish context collection: Hermes, in full (ruling 93).**
   - Mirror the whole Hermes docs site (developer guide, user guide, guides and tutorials, reference) into `research/sources/hermes-docs/` as markdown, so agents read it complete. Research lives in the repo. Opus agents have a 1M-token context window, so give them all of it; don't cap it.
   - Then one or two Opus agents read the full mirror and the source on GitHub. They extend 37a, 37b and 37c with everything those studies missed. The operator named:
     - shared helpers via symlink;
     - git worktrees, and their logic for workflows;
     - the security, permission and authorization model (compare it with ours; he says Hermes misses little here);
     - session storage;
     - the skills curator;
     - tool search;
     - LSP;
     - document extraction;
     - built-in plugins;
     - desktop-app UI patterns (for the UI session).
   - Write each addition as a section or appendix in the matching 37 file.
2. **Settle provider routing (rulings 92, 95, 96).** Use file 38. Choose the third-party pool (opencodex as-is, a hybrid, and so on). Record exactly what QMX keeps, replaces and loses from what is already coded.
3. **Architecture pass.** One Opus agent runs the BMad architecture skill (`C:\Users\Mubarak\Desktop\QMX\.claude\skills\bmad-architecture\`) headless, in amend mode, with `codebase-design`. It folds in:
   - file 36's criticals and should-fixes;
   - the routing decision;
   - the Hermes adopt-list (the top-10s plus the extended ones);
   - the open SPEC-GAP and LATER-PACKET items from 34;
   - the Library and Lab touches.

   Keep `lint_spine.py` clean and AD ids stable. Write `research/methodology/39-architecture-rerun.md`.
4. **Re-triage.** One Opus agent maps every item in `BACKLOG.md` and `lows.md` to the amended architecture: resolved, still open, or a new packet.
5. **Independent review.** One Opus reviewer attacks the amended design against the built code (`git show` on the `engine/*` branches) and the rulings. Say "Opus reviewed Opus" in its report.
6. **Apply, then fix-check.** The architect applies the review's findings. A fresh Opus agent then checks the result independently, and its critical findings are applied.
7. **Re-centralize.**
   - Update `33-state-of-play.md`, `UI-HANDOFF.md` (including the Hermes UI ideas) and the Wayfinder map (`wayfinder/`, `frontier.py` clean).
   - Archive superseded files under `archive/<date>-<name>/` with a `SUPERSEDED.md`.
8. **Plan the next program.** It is a hardening program plus the next packets, in order:
   - security fixes (AD-24 and AD-36 done right);
   - bugs;
   - the harness round (HG3, narrowed per file 36);
   - the provider pool;
   - hygiene (including the red one-line CI test and the haiku test default);
   - then the later packets (memory, Library, gate folding, and so on).

   `check-plan.mjs` must report 0. Use autopilot-stack and light verification, with at most two agents at once. Keep tests few and behavioural. Probes come first. Name every override. Mark every default.
9. **Write the coding prompt.** Use the technical-writing and unslop skills. Run a decision trail (`decisions.tsv`). Ask him only his real calls, through AskUserQuestion, with your recommendation first. Commit on `plan/agent-system`, create the base branch locally, and end with an "Attention" list and a short paste prompt for a fresh coordinator session.

## Rules for you

- Keep your own context under 40%. Agents do the reading; you read their summaries. Commit after each step.
- Speak plainly. The operator dictates, so expect transcription noise. Facts are yours to find. Product and money calls are his.
- Show him the result as an interactive explainer page, not a wall of text.
