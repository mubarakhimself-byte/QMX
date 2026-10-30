# Brainstorm intent: the unit's playing field

Headless `bmad-brainstorming` run, 2026-10-30. Source of truth: `.memlog.md` in this folder (176 entries: 150 ideas, 18 techniques, 7 connections). Input for the next step, the wayfinder chart. **Not converged on purpose:** this file lists what must not be lost, not what was chosen.

## Topic and goal

- **Topic:** everything QMX must be able to do for a unit (one complete trading algorithm that replaces the bot), and everything around it.
- **Goal:** widen the field into questions, lenses, contradictions and permutations. Answer nothing.

## What must reach the wayfinder chart

1. **Self-configuration has no mechanism yet** (B002, B004, B084, B134). It touches his click, the shared $300 budget and the risk socket.
2. **Selection bias moves rather than disappears** (B011, B018, B048). It shows up in the backtest grid, then the System 2 paper trail, then the agents' morning shortlist.
3. **The MIS is a grid, not one thing** (B021 to B030). Style × timeframe × data class × output form × place × clock. Some cells cannot exist because the venue has no such data (B027).
4. **Units stand alone versus System 1 needs the MIS** (B083, B053, B010). Every MIS output design must say what a unit does without it.
5. **Shared measurements need one owner and one version** (B041, B042, B060). Same indicator in unit and MIS; retrains that relabel the past.
6. **Agents as forecasters, not narrators** (B073 to B082). Timestamped predictions scored later, a landmark window, "what I did not see", and the open edge of "agents never touch money" when they shortlist markets (B088).
7. **The failure drill has never been written** (B053 to B062). Each outage needs a stated unit behaviour and a journal line.
8. **What wins in every future** (B095). Journals, a terrain record, labels on trades, a feed. These are also what the party found missing.
9. **Seven words carry two meanings** (B107 to B114). Router and MIS, correlation ledger, system one, node, workflow, sniping, dictionary.
10. **His rungs of use** (B099 to B106). Week 1 with one unit on demo, to year 2 with hundreds of units. Each rung needs different parts.

## Where to read the full map

`playing-field.md` in this folder: 20 lenses, 220 tagged questions, 38 contradictions, a 31-row cross-map, a parked list and counts.

## Assumptions made

- The topic and goal came from the planning brief, not from a human in the session.
- Source tags on each idea point to the transcripts (T1, T2), STATE, seeds and research 16 to 19. They show where the idea grew from, not proof that the idea is right.
- I wrote the HTML and this file myself instead of delegating them to subagents as the headless reference asks, because the brief forbids subagents.

```json
{
  "status": "complete",
  "intent": "brainstorm",
  "memlog": "D:/QMX-worktrees/unit-plan/tracker/risk-sizing/research/funnel3/party-brainstorm/.memlog.md",
  "html": "D:/QMX-worktrees/unit-plan/tracker/risk-sizing/research/funnel3/party-brainstorm/brainstorm.html",
  "intent_doc": "D:/QMX-worktrees/unit-plan/tracker/risk-sizing/research/funnel3/party-brainstorm/brainstorm-intent.md",
  "assumptions": ["topic and goal taken from the planning brief", "artifacts written without subagents per the brief", "on_complete hook (recommend bmad-prd) recorded but not followed; the run's next step is the wayfinder chart"],
  "external_handoffs": []
}
```
