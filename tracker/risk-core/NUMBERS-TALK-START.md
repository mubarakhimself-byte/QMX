# Start here: the numbers and strategy talk

Written 9 Nov 2026 for a fresh session, at his request. The design phase is finished. Now we talk numbers, game plans and strategy with him. He leads.

## Where things stand

- **Design, finished on paper.** `round-2/arch/final/SPINE.md` (build substrate) and `SOLUTION.md` (plain words). The story of how we got here: `review-2026-11-07/TIMELINE.md` and `round-2/RUN.md`. His page: `round-2/WALKTHROUGH.html`.
- **The build is running in another session**, on DeepSeek first, with Claude Code later. Its store is `D:/QMX-worktrees/risk-ship/`. As of 9 Nov morning, 10 of 69 PRs were stacked. **Don't touch its files and don't steer it.** Read `risk-ship/RESUME.md` only if he asks how it's going.
- **Every value in the design is a labelled placeholder, owned by "numbers talk".** This talk sets values, presets and game plans. It doesn't change the shape. If an idea truly needs a shape change, say so and write it down for later; never edit the spine.

## Read first, in this order

1. `PARKED-FOR-NUMBERS-TALK.md`: everything he parked, in his words. This is the agenda.
2. His words: `seeds/operator-words-2026-11-06.md` M49 to M56 (M50 and M51 are the vision and the 500-to-5,000 frame), then M5, M7, M8 in `operator-words-2026-11-01.md`, and M10 in `operator-words-2026-11-03.md`. Use `round-2/SEEDS-2.md`'s register (the N group) to find the rest.
3. The levers the numbers sit on: `round-2/arch/final/SOLUTION.md`, then `OPEN.md`. Templates `scalper-mr`, `intraday-trend` with an `orb` variant, and `canary`; the 20-pod gallery in `round-2/expand/E2-pods-miniapps.md`; capital sharing as a row.
4. Raw material for methods (parts, not verdicts):
   - `harvest/H2-sizing-brakes-exits.md` Group B: methods for a large risk per trade without ruin. No run on disk compares them for that goal.
   - `research/R9-accelerators-and-brake-pairs.md`.
   - `harvest/H1` ideas 11 and 12 (cost tables, sniping windows).
   - `harvest/H4` section G (the unit idea bank).
5. The old model numbers, only to know what was said before: `architecture/` (superseded) and `explainers/risk-template.html` (rejected). They are not a starting point.

## What he has already said about this talk

- "This is not set in stone." Every number he gives is an example. The 55% win rate was ours, not his.
- His frame (M50, M51): start from $500 and aim at $5,000 in a month, then ask "how do we achieve this without getting ruined?", using accelerators and brakes. Cents per trade are out at this capital. First build a cash base, then breadth. Concentrate on the best basket, which may mean no crypto at first. "At 5,000, the math changes drastically."
- He believes human scalpers show what's possible, and wants a reality check, then solutions, not refusals. "You yourself, you said it's not impossible, but requires a large risk per trade... Those are the problems you're meant to be handling."
- Game theory interests him. Nothing on disk covers it: two MQL5 articles are listed unread in `research/R5-mql5-corpus-ideas.md`.
- Overfitting: he thinks it may not be bad here. Earlier I said fitting noise is never good and specialization is fine. He expects to be corrected ("you have more knowledge than me here").
- Fees are observed facts that QMX acts on, never removed. "Think of QMX more of as a data analyst."
- Where a unit goes is part of position sizing to him: which instrument, which window.
- Other parked topics: 8% against 1% and Kelly; dollars or percent; the 300/200 split; the floor and "sitting duck"; sweep caps; why 5 and not 10; one-unit users; paper period length; simulations of worst, realistic and best cases, "all factors considered".

## How to work with him

- **Short replies.** He dictates and doesn't read walls of text. Detail goes in files. Open with where we are, then answer what he asked.
- **Correct him plainly,** with maths and scenarios. Give opinions. Don't use luck as an argument. Never fit numbers to a survival-only frame: "I don't want just safety."
- **Use simulations to show how a plan behaves,** labelled as models, with worst, realistic and best cases. He wants these. Never let a model result silently become a rule: it becomes a preset value he agrees to.
- **Agents.** Opus by default, few and efficient, at most one Fable at a time. Every brief says no sub-agents and no Firecrawl, and names the skills to load. You orchestrate and check their results yourself.
- **No codenames, no "minimal viable",** and "I think" from him means exactly that.
- **Pages are static HTML with no scripts,** because his viewer doesn't run them. Artifact tools may or may not work in a new session.
- **Save his words verbatim** into `seeds/` as you go, and commit on `plan/risk-core`. Push and merge only on his word.
- **Never print keys.** The raw transcript holds a live Browserbase key, so never quote it or commit the transcript.

## The full record

- This whole session's raw transcript: `C:\Users\Mubarak\.claude\projects\C--Users-Mubarak-Desktop-QMX\2928e6ee-7392-4c1c-87c8-23b375749b4f.jsonl`, plus its 1 Nov part `3843585b-786c-489b-aec5-b6c33ec14833.jsonl`.
- Exported zips with every subagent transcript: `C:\Users\Mubarak\Downloads\session-export-1794218641711.zip` (latest) and `session-export-1794064562163.zip`.
- `STATE.md` top block points here.
