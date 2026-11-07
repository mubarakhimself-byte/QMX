# Round two: common brief for every agent

Mubarak (not a programmer or a trader, dictates by voice, so read for meaning) is building QMX, a trading system. A session from 1 to 7 Nov 2026 was meant to finish the risk management and position sizing part of its "unit", as a configurable baseline. Tuesday's wide work was sound. On Friday the work went wrong: a dollar simulation became the test, and the design narrowed to one go-live policy. He rejected the result and asked for the run to be done again from Tuesday, using what exists plus his newer words.

All paths are under `D:\QMX-worktrees\risk-plan\tracker\risk-core\` unless stated.

## Read first

1. `review-2026-11-07/TIMELINE.md`: what was intended at each step and what happened.
2. His words, verbatim: `seeds/operator-words-2026-11-06.md` M49 to M54 (M50 is the vision), then `seeds/operator-words-2026-11-03.md` (M10, M31 to M38), then `seeds/operator-words-2026-11-01.md` (M5, M7, M8). "I think" from him means exactly that. Numbers from him are examples.
3. `harvest/H1` to `H5` for your area, then their sources. `unit-baseline/SWAP-CHART.md` for plans against code. `review-2026-11-07/system-map.md` for what is built.

Treat `funnel/HYBRID-FATES.md` fates and `architecture/SPINE.md` as records of a wrong test. They are material, never verdicts.

## The goal

QMX is a canvas: "ink a paintbrush and a canvas". His creativity, or a user's, is the limit. "This is not set in stone."

- **The deliverable:** a baseline that works, plus a layer anyone can customize and extend. The unit can trade, can size itself, can configure itself, has a template. Someone new can use it.
- **The unit is what ideas finally become.** QML is its SDK, so agents don't produce slop. Python covers what QML can't express.
- **Placeholders are swapped out.** The build shipped labelled stand-ins for sizing, exits and halts so that builders could test. This session plans what replaces them. Sockets must widen where the swap chart says so.
- **The technical lens carries beyond the unit.** MIS, SQS, brakes, accelerators, the node and QML itself are open for enhancement or overhaul where it makes sense.
- **Pods and mini apps are the customization layer.** Pod questions are configuration, never policy to ask him.
- **Agents carry the load.** He may run about 200 units. Anything that needs him to monitor is wrong by default.
- **Performance, not only safety.** He rejects "sitting duck" designs. Don't default to the safest reading.
- **It trades many instruments and styles.** A scalper is handled differently from intraday.
- **It must be maintainable,** from a developer's point of view.

## The test, replacing dollars

Ask of every idea or rule:
1. **Is this configuration?** Then it's a block, preset, template or pod setting, not a law and not a question to him.
2. **If it's left out now, does the core get reworked later?** Then the core must leave room: a socket, input, record or hook.
3. **Otherwise,** it's content someone adds later, or it belongs to another session (name it).

No dollar simulation may decide what goes in. A simulation may only test that a mechanism behaves as described.

## Fixed lines

Agents never touch money. Only he promotes to live. Exits are never blocked. Only his hand lowers the kill switch. Never print keys or tokens.

Everything else is open, including Book and BMS. A reckless setup must be expressible.

## Out of scope for this round

- **Numbers talk:** budgets, targets, game plans. They wait in `PARKED-FOR-NUMBERS-TALK.md`. Don't argue values.
- **Methodology:** how a unit is proven valid, per type. Prepare hand-offs only.
- **Agentic upgrade, UI build, and the running repair program** (DeepSeek, `D:\QMX-worktrees\repair-ship\`). Don't touch their files.

Overhaul is allowed (M31, M32, M56): if a thing makes no sense, including pods or the UI, propose something new, and name it plainly so he can go through every overhaul.

The UI is a proposal and mostly outdated (M55). Use it and the UI notes to understand intent. No screen, slot list or block name binds the design.

Design for complexity, never a complex system. Earlier generations were called "too much machine". Check code claims at `D:\QMX-worktrees\bld-repair-24`.

## Rules

- Do not spawn subagents. Do not use Firecrawl. Do not use Fable unless named. No pushes, merges or test suites.
- Write only the output file you are given. Make no other change on disk, except scratch work under `D:\Temp`.
- Load the skills your brief names with the Skill tool, and apply them headless: nobody is available to answer questions. Infer, label assumptions, and carry on.
- Every claim cites a path, a line or a source. Say UNKNOWN when you did not verify.
- Plain words. Explain any id or term the first time. His screen words matter.
- Reply to the lead in under 120 words: file path, counts, and what the lead most needs to know.
