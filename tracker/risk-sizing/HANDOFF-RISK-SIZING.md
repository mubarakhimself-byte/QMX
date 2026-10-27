# Hand-off: risk and sizing, a design conversation with the operator

Paste the prompt below into a fresh Claude Code session started in `D:\QMX-worktrees\agent-system`.

```text
This is a slow design conversation with the operator about risk management and position sizing inside a QMX unit. It is not a build run. Nothing gets decided without him. Risk and sizing is special to him: one small mistake here costs real money.

Read first:
1. D:\QMX-worktrees\agent-system\tracker\risk-sizing\STATE.md: his binding corrections, especially "Operator round 2026-10-27". It outranks everything else.
2. tracker\risk-sizing\seeds.md (his seeds).
3. Research files in tracker\risk-sizing\research\:
   - 05-academic.md §4 (sizing and Kelly)
   - 08-old-qmx-testing-and-decay.md (WF3, CUSUM, the decay check)
   - 07-funnel.md, the forge records F-5 (unit sizing), F-14 (new cells start small) and F-15 (house money)
4. The old system, from earlier summaries (read these, not the raw transcripts):
   - C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\grounding\01-old-system.md
   - 02-book-and-prior-sims.md
   - 06-qrmx-transcript-recovery.md §1-2 (the birth of the self-configuring unit, house money, reverse house money, loss points, session capital)
   - 09-original-design-recovery.md A.6 and A.9
5. The explainer pages "Sizing" and "Fast stops and slow checks" (the Decay page) at https://claude.ai/artifact/CXKb3w5rsfm1zcUeNP7BXN

What he wants:
- Combine the best of the two systems:
  - the old one, with its aggressive "radioactive" sizing: session capital, house money, reverse house money, compounding across sessions;
  - the new self-calibrating unit.
- Explain it mathematically and step by step, with worked examples in R and dollars from a $300 start (every number configurable). Pictures alone are not enough.
- Show concretely how a unit "configures itself". It has never been shown: which numbers move, from which journal data, by which rule, how often, and within which limits.
- Settle the account guard and the pod. His lean: the pod is effectively the BMS (not the whole Book), and the BMS already covered the account guard's jobs. Should they combine?
- Explain these plainly:
  - loss points (the fast stop)
  - CUSUM in R (the slow decay check, about 240 trades to catch a 0.1R edge going to zero)
  - the one-way ratchet on the account floor versus on a unit's size
  - the Kelly ceiling (the chance of touching a 40% kill line: full Kelly about 60%, half about 22%, quarter about 3%)
  - whether size may grow back after a cut
  - house money switching on only when a unit's record shows streaks
- Keep the scopes apart. Do not mix the overall portfolio with portfolio configuration, or live trading with strategy research and development. Take one at a time.

Rules:
- Design for complexity, never a complex system.
- Agents never touch money.
- Only he promotes units to live.
- Local first: everything runs on his PC; servers only extend.
- Nothing is limited by default.
- Ask him only real questions, with a recommended answer each, through the AskUserQuestion tool. Explain before you ask.
- Record every ruling in STATE.md and commit.

Done when he has agreed:
- how a unit sizes and recalibrates itself, with the formulas;
- the account guard and pod shape;
- grow-back and house money;
- the fast and slow protections.
Each is recorded as a ruling in STATE.md, and he has an explainer page for it.
```
