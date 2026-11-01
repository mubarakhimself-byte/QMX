# Hand-off: risk and sizing, a design conversation with the operator

## Start here (updated 2026-11-01, after the unit-system planning)

The section below this one is the 27 Oct version and is superseded: its paths point at the old `agent-system` worktree. Use this prompt. Paste it into a fresh Claude Code session started in `C:\Users\Mubarak\Desktop\QMX`.

```text
/poteto-mode This is a design conversation with me about risk management and position sizing inside a QMX unit. It is not a build run. Nothing about risk or sizing is decided without me: one small mistake here costs real money. Ask me decisions through the question tool, one at a time, each explained in plain words first. Use agents for heavy reading, Opus only, few at once, and tell them not to spawn their own.

The unit system's build is running in another session from D:\QMX-worktrees\unit-plan\tracker\risk-sizing\build\UNIT-PLAN.md, with labelled placeholders where sizing, exits and account halts go. This session designs what replaces them. Same approach as the units (STATE midday ruling 6): a small, complete, solid core that everything else is built on, like mini apps, the lab and the pods. The pods already represent risk and sizing.

Read first, from the branch plan/unit-system in D:\QMX-worktrees\unit-plan\tracker\risk-sizing\:
1. STATE.md: "RESUME HERE", then "Operator round 2026-10-31 midday" (rulings 1-55) and the older operator rounds. His rulings outrank every file.
2. RISK-SIZING-PACK.md in full: his own words on risk and sizing (sections 1-5), the questions moved here from the unit planning (section 6), and the build's placeholders (section 7).
3. build\RISK-SIZING-PLACEHOLDERS.md: every placeholder the build leaves, where it sits, and what this session must replace.
4. The risk and sizing points each design part found: architecture\parts\A-qml-dictionary-unit\RISK-SIZING-POINTS.md, architecture\parts\B-qmb-journals-workflows\RISK-SIZING-POINTS.md, architecture\parts\C-node-mis-external\RISK-SIZING-POINTS.md; the "for the risk session" sections of architecture\funnel\solutions\00-index.md and architecture\funnel\experience\design-thinking.md; the risk rows of architecture\funnel\edge-cases\catalogue.md.
5. The design the risk core plugs into: architecture\level-0\ARCHITECTURE-SPINE.md (its "for the risk session" list and the risk socket), and part A's risk socket and its contract tests (build slice A15).
6. Research: research\05-academic.md (sizing and Kelly), research\24-earning-a-specialist.md, research\26-quant-judging.md, and the rest the pack names.
7. How to work: architecture\00-how-the-best-session-worked.md.

Rules: risk and sizing authority is the GitBook and the node docs; the old QMX-discussion folder is barred as an authority. Report in USD. Only I promote anything to live. The only automatic move in trading is a risk rule stopping a unit, logged. Agents never touch money. Never print keys or tokens.

Start by walking me, in plain words, through what the build leaves as placeholders and what this session must decide. Then we design it together.
```

---

## The 27 Oct version (superseded)


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
