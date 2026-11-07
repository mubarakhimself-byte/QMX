# Harvest brief: use what the agents already produced

Mubarak (not a programmer or a trader, dictates by voice, so read for meaning) is building QMX, a trading system. Between 1 and 7 Nov, this session's agents produced a large body of work: research, 1,050 parts, 510 hybrids, a funnel, three architecture versions, a fold, checks and fixes. All of it is on disk under `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. The final page he received used almost none of it, and he rejected it. He is right. Your job is to recover the value, not to redo the work.

**Do not start new research. Read what exists.**

## Why the earlier funnel can't be trusted as it stands

Its fates ("core", "shadow", "later", "dropped") were judged by simulated dollars and by what was needed to go live on a $500 seed. Everything about pods, mini apps, the Lab and agents was pushed to "later". Read a fate as a record of that judgment, never as a verdict. Re-judge each idea with the lens below.

## The lens (his words, `seeds/operator-words-2026-11-06.md` M49-M53)

- QMX is a canvas: "ink a paintbrush and a canvas". Nothing is "set in stone". His creativity, or a user's, is the limit. Numbers are made later by him and the copilot, for each instrument, pod or mini app.
- The unit is what agents' ideas finally become. QML is its SDK, so agents don't produce slop. Python covers what QML can't express.
- Placeholders in the unit are swapped out for what this session designs. The unit is the most important part, but the technical lens "carries beyond more than a unit": MIS, SQS, brakes, accelerators and QML itself were all open for enhancement or overhaul.
- Ideas touch the unit. The unit baseline can't be designed before knowing them.
- It must trade many instruments and styles. A scalper is handled differently from intraday.
- Agents carry monitoring and analysis. He may have about 200 units.
- "I think" from him means exactly that. Numbers from him are examples.

Agents never touch money. Only he promotes to live. Exits are never blocked.

## What to write

Write only your one output file, under `harvest/`. Plain words. Every idea cites its source path. Do not filter to a top N: the only limit is relevance. Merge true duplicates.

1. **What's here.** The files you read, and how much of each you read in full.
2. **The ideas, best first.** For each:
   - what it is, in two or three plain sentences a non-trader can follow, with one small example where it helps;
   - where it came from (paper, article, trader practice, another field, or his own words), with the path;
   - what it touches in QMX (the unit's sizer, exit, halt or hook; a QML block or role; the MIS; SQS; the node; a pod; a mini app; the Lab; a workflow);
   - its earlier fate, and whether the dollar simulation or the go-live lens drove that fate;
   - your read: **seat** (the baseline must leave room for it, or the unit gets reworked), **content** (a block, template or preset someone adds later with no core change), **other session** (name it), or **drop** (say why);
   - whether it's real evidence, a proposal, or a guess. Don't oversell it.
3. **Designs and overhauls already proposed for this area,** including options that were never shown to him. If two conflict, keep both and say what each buys.
4. **What the unit baseline must carry** because of this area: inputs, sockets, records, hooks. Say what breaks if it's missing.
5. **Gaps.** What he asked for in this area that nothing on disk answers. Quote him.

No policy decisions. No fixed numbers, except to report what a source found. Don't argue about dollars or targets.

## Rules

- Do not spawn subagents. Do not use Firecrawl. Change no file except your output. No pushes or merges.
- If a report seems missing, the subagents' raw transcripts are at `C:\Users\Mubarak\.claude\projects\C--Users-Mubarak-Desktop-QMX\2928e6ee-7392-4c1c-87c8-23b375749b4f\subagents\` and `...\3843585b-786c-489b-aec5-b6c33ec14833\subagents\`. Use a script to pull final messages; don't read them whole.
- Code tip for fact checks: `D:\QMX-worktrees\bld-repair-24`. Unit plans: `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\`. A chart of placeholders against plans and code will land at `unit-baseline\SWAP-CHART.md`, and `review-2026-11-07\system-map.md` has an earlier map.
- Reply to the lead in under 150 words: file path, how many ideas, and the three he would most want to hear.
