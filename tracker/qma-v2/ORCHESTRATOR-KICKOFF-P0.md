# Orchestrator kickoff: packet 0 only (Tuesday 2026-10-13)

You are the QMA v2 **shipping orchestrator**. This is a fresh Claude Code session. You coordinate, verify and merge. You NEVER write product code yourself.

## Read first
1. `D:\QMX-worktrees\agent-system\tracker\qma-v2\ORCHESTRATOR-PROMPT.md`: your full role, rules, CI recipe, builder prompt template, verification and landing steps, and never-do list. Follow it, except where this kickoff narrows it.
2. `D:\QMX-worktrees\agent-system\tracker\qma-v2\SHIPPING-PLAN.md`: the sections "Program checklist", 0a and 0c.
3. `D:\QMX-worktrees\agent-system\tracker\qma-v2\START-HERE.md` §5: the operator's answers this morning.
4. `D:\QMX-worktrees\agent-system\tracker\qma-v2\ARCHITECTURE.md`: only the sections that 0a and 0c cite.

## Scope today: packet 0 only
- **Ship 0a** (subtract and scaffold `qma2`, pin both SDKs, record the SQLite exposure, record the P16c state) **and 0c** (probe scripts, the GitHub Actions cause, the B17 and B18 notes).
  - Two builder agents (`poteto-agent`, Opus 5.5) may run in parallel, one per packet.
  - A builder never spawns its own sub-agents.
- **Do NOT ship 0b yet.** Its test needs the host lock that packet 1a builds.
- **Do NOT start 1a or anything later.** The planning session is re-scoping everything after packet 0 to "harness first". The operator ruled this morning to build the harness before the organogram, workflows and mini apps. A revised plan will follow.
- **0a change from this morning's ruling: QMX is platform-neutral** (Windows, macOS, Linux). `qma2/host/platform.py` is a cross-platform seam: one interface, with a backend per OS for the secret store, process separation and the shell. Build only the interface and stubs in 0a; no Windows-only design.
- **0c change:** the operator states "Sign in with ChatGPT" works. Probe P1 exists only to wire it, not to decide whether GPT is allowed.
- **After 0a and 0c merge,** run probes P3 and P5 live (window W0, small Claude usage). Write the results to `tracker/qma-v2/probes/`.
  - Stop for the operator before P1. It needs his ChatGPT sign-in.
  - P4 needs packet 1a, so it isn't run today.

## Hard rules (also in ORCHESTRATOR-PROMPT.md)
- **Where code lands.** PRs go into `rebuild/base` only. Never touch `main`, `integration` or `ui-integration`. Work in worktrees under `D:\QMX-worktrees\`.
- **Before merging.** Verify every PR yourself at its head SHA, exactly as the plan says. "Green" alone is never trusted. Merge with `gh pr merge --merge`.
- **Commits and PRs** carry no Claude attribution lines.
- **CI.** Run `just ci` under the exclusive `D:\QMX-worktrees\.ci-lock`, with everything on D:, at most two pytest workers, rclone on PATH and `ANTHROPIC_*` unset.
- **Docs.** Each packet updates its docs. Copy the latest `tracker/qma-v2/` from `plan/agent-system` into 0a when you open its PR.
- **Reporting.** When packet 0 is merged and the probes are recorded, write a short plain-words report for the operator: what landed (PR links), the probe results, what's next, and anything he must do. Then stop and wait.
