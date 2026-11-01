# Risk core: state

Branch `plan/risk-core` (worktree `D:\QMX-worktrees\risk-plan`), cut from `plan/unit-system` at 09d36ab7. The old local branch `plan/risk-sizing` (at main c3e8ec5e) is stale and was left untouched.

## RESUME HERE

1. Grounding DONE 2026-11-01: G1-G5 in `grounding/` (G5 is the timeline), sims in `grounding/sims/`. Next: find the clean starting point with him, then design by scenarios.
2. Grounding files land in `grounding/`:
   - G1 operator sessions ("Risk & sizing QML redesign", "Agent team for MT5 article analysis", plus the 10-05 and 10-13 sessions they carried)
   - G2 the unit-plan risk state (rulings, risk socket, placeholders)
   - G3 the old system (QMX-discussion)
   - G4 the current Book and BMS (docs, `_docwork`, GitBook/node docs, shipped code)
3. After grounding: build a timeline of how his risk/sizing thinking evolved (`grounding/G5-timeline.md`): QMX-discussion (old system) → the 10-05 and 10-13 sessions → "Risk & sizing QML redesign" (10-15 to 10-20) → "Agent team for MT5 article analysis" (10-20 to 10-29) → the unit-plan risk pack (10-27 to 11-01). For each stage: what changed, what was dropped, and why. The timeline is for the lead's own understanding; report it to him only briefly.
4. Next: synthesis for the operator (the landscape), then his questions and seeds, then scenario math.

## Findings for the unit build (not ours to fix; pass on)

- G2: build slice A2's dummy unit writes `risk_fraction` "0.5" meaning 0.5 %, while the contract stores percent as a fraction (so read literally it is 50 %). A3 must fix it. Reported to the operator 2026-11-01.

## Operator opening, 2026-11-01

- Goal for now: combine the risk and sizing of the current system (Book + BMS) with the old system's (QMX-discussion). He is not sure yet what he wants to build.
- Core rule: nothing is set in stone, in any session or note. The whole point is to enhance.
- Work by math and scenarios. His example seed: a unit risking 8 % rather than 1 % may be what makes sense.
- He is not technical and not a trader: correct him, give opinions, broaden the landscape.
- Separate planning and coding branches.
- Use a few agents for heavy reading to keep the lead's context light.
- The old rule "QMX-discussion is barred as a risk/sizing source" is lifted for this session by his explicit ask: it is a source of ideas to combine.
