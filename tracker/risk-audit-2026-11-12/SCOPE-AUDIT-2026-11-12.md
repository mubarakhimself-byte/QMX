# Scope audit, 12 November: what he asked for against what the plan grew into

Read-only audit of `D:/QMX-worktrees/risk-plan/tracker/risk-core/round-2/build/PLAN.md` (69 sections, RC-01 to RC-69). Built rows come from `STACK-LIST.md` (28 built, none merged). His words come from the user turns of the planning transcript `2928e6ee-....jsonl` and the verbatim registers `seeds/operator-words-*.md` and `round-2/SEEDS-2.md`. M numbers are his message numbers in those registers. T-, H- and A- ids are rows in `SEEDS-2.md`. Today's rulings (12 Nov) are taken as given:

1. Demo is paper: paper means a broker demo account.
2. Brakes stop new trading. They never close trades, except at the kill switch's black-swan level.
3. Pods are portfolio-like (Book plus BMS) and versioned. A unit lives in one or more pods.
4. There are many accounts across many platforms.
5. Workflows and mini apps decide a unit's journey. Nothing hard-codes it, and QMB backtesting is the one required tool.
6. The UI may drop "the lab", because the copilot covers it.

## What he actually asked for

The ask, in his words of 7 Nov (M49, 13:00 UTC): "Let's just make sure that the unit can actually trade, it can self-configure, it has a template. That's all I wanted from you. Then we stop there." He gave more detail in the same message: "have a template that we can plug in our own configurations and stuff. That's it. Don't look at the numbers". At 14:32 (M50) he said: "My actual requirement from you was to help finish the unit as a whole". At 15:15 (M52) he said: "Just complete it and make sure it can work. And it's maintainable, please." He also said that stand-ins were the session's job: "sizing and exits... most of it is demo... they just swap it out".

**What he asked for beyond the unit.** On 7 Nov he asked for these things outside the unit itself:

- **A watch over 200 units.** "Why not just have an agentic workflow that can cater for that? As a mini app also." (M49)
- **Pod ideas.** "I remember asking you to see if you could figure out some pod ideas or configurations." (M49)

**He did widen the scope on 7 Nov, for honesty's sake.** At 15:24 (M53) he said: "Why not handle the entire thing? This changes the perspective from the unit baseline is part of the bigger problem". Earlier (M52) he had said: "the MIS, SQS, a lot of the breaks, the accelerators... I was proposing maybe overhauls or enhancements". So part of the growth was invited. Today he narrowed the program back to a unit template that pods can be built around. This audit measures against that narrower ask.

## Summary of counts

| Class | Count | Sections |
|---|---|---|
| CORE: the unit template he asked for | 39 | RC-01 to 15, 17, 21 to 30, 32 to 36, 39, 42, 47, 48, 64, 66, 67, 68 |
| CONFLICT: contradicts a ruling of today | 5 | RC-16, 18, 19, 53, 54 |
| POD: belongs to the pod design, so it waits | 7 | RC-49, 50, 51, 52, 55, 56, 57 |
| MINI-APP: mini app plumbing or a mini app | 5 | RC-58, 59, 60, 61, 62 |
| EXTRA: added by an agent, with no ask behind it | 13 | RC-20, 31, 37, 38, 40, 41, 43, 44, 45, 46, 63, 65, 69 |
| **Total** | **69** | |

**The 28 built rows.**

- **Keep: 25.** RC-13 needs a small rework of its verb list, and RC-20 needs its release note reworded.
- **Rework: 3.** These are RC-16, RC-18 and RC-19. Each conflicts with a ruling of today.
- **Remove: 0.** The one built EXTRA row that is not a stop-point step is RC-31, and it is clean and cheap to keep. RC-20, the stop A release step, is also kept.

**The 41 unbuilt rows.**

- **Build: 17.** Six of these are already in flight or parked.
- **Build after the demo sign-in: 2.**
- **Wait for the pod design: 7.**
- **Drop or merge: 6.** These are RC-45, 46, 53, 54 and 63, plus RC-66, which merges into RC-48.
- **Park: 9.** These are RC-37, 40, 41, 42, 43, 44, 58, 65 and 69.

Two of the 17 builds depend on a condition. RC-36 waits for his answer on news, and RC-38 is needed only if the repair deletes the old gate.

On the third bullet's terms, the program cut to his ask is 47 PRs, not 69: the 28 built rows plus 19 more.

**Mini apps.**

- **Existing: 7.** Three are core apps, `mis`, `qmb` and `trading-node`. Four are examples.
- **Proposed in the planning files: 42.**
  - 12 apps or desks.
  - 10 agent jobs.
  - The 20 pod configurations of `E2`. He said pods "are meant to be mini apps" (M10).
- **Owner words.** Only one proposed app has a direct ask in his own words: the fleet watch.
- **Verdicts on the 42.** Keep 4, merge 19, drop 8, ask him 4, wait 7.

## Per-section table

Columns:

- **Class:** see the counts above.
- **His words:** his own words with their source, or "none".
- **Verdict:**
  - For built rows: keep, rework or remove.
  - For unbuilt rows: build, after demo, wait (for the pod design), park, drop, merge or ask him.

| RC | Plain name | Built | Class | His words (source) | Verdict and why |
|---|---|---|---|---|---|
| 01 | Honest contract tests, Library blocks enrolled | yes | CORE | "How do agents talk to it? How do they know that the things are correct?" (M10, 3 Nov) | **Keep.** Any added block is judged by a true test. This is how the template is extended. |
| 02 | Refused fields named, developer guide started | yes | CORE | "And it's maintainable, please. From a developer's perspective" (M52, 7 Nov) | **Keep.** |
| 03 | Unit split into logic half and risk half | yes | CORE | "What if I want to change the way it is derived?" and "how will they be able to create new versions of our unit?" (M10) | **Keep.** It is how a unit is iterated: a size change does not re-prove its entries. |
| 04 | Node tests logic, trusts a click for risk | yes | CORE | "they're meant to just give me the units. I click and stuff" (M10, A-03) | **Keep.** It carries RC-03's stale qmb pin (STACK-LIST). |
| 05 | Typed amount, one converter for currency | yes | CORE | "Why lots? Because remember, you're not trading one instrument." (M49) | **Keep.** |
| 06 | Sizer answers money, absurd sizes caught | yes | CORE | "As long as it can size itself, the numbers we shall talk about them." (M49) | **Keep.** |
| 07 | Exchange rate at both hosts | yes | CORE | "Don't forget that we're also looking at multiple instruments." (M26) | **Keep.** It lands with rc-26's money fix (STACK-LIST reds). |
| 08 | One decision row per send, explain any size | yes | CORE | "There have to be reasons." (M8) | **Keep.** |
| 09 | A raising block never reaches its exits | yes | CORE | "closing a trade is never blocked" (M5, 1 Nov) | **Keep.** |
| 10 | One unit's fault never stops another | yes | CORE | "there is a possibility I could have 200 units" (M49) | **Keep.** |
| 11 | Every exit each bar, with reasons | yes | CORE | "stops are now part of a unit" (M5). "If you look at the dictionary has closing mechanisms." (M49) | **Keep.** |
| 12 | Shipped exit blocks read numbers from evidence | yes | CORE | "sizing and exits... most of it is demo... they just swap it out" (M52) | **Keep.** |
| 13 | A brake is a control row in the unit | yes | CORE | "So Brex first, accelerator second." (M8). "We need to be able to know what is breaking." (M8). "halt checkpoints, I think the same thing" (M52) | **Keep, small rework.** Take `flatten` out of the verbs a unit-level brake may use. Leave it only to the kill switch's black-swan row (ruling 2). |
| 14 | Every brake's state from one fold | yes | CORE | "We need to be able to know what is breaking." (M8) | **Keep.** |
| 15 | Risk events and would-have rows | yes | CORE | "it helped us detect alpha decay" (M10) | **Keep.** |
| 16 | A brake may flatten, stop and send to paper | yes | **CONFLICT** | Against it: "You are saying may a rule close position by itself? I think no." (M49), and ruling 2. | **Rework.** A brake stops entries only, and only the kill switch's black-swan level closes trades. "Send to paper" is a hard-coded journey under ruling 5, and under ruling 1 it means a demo account. Make it a card or a workflow step. |
| 17 | Canary template and its records | yes | CORE | "it has a template" (M49). "something that anyone can use, you know, like right out of the box" (M49) | **Keep.** |
| 18 | Draft to paper on his click, safety half of G, no judge pass | yes | **CONFLICT** | For the click: "they're meant to just give me the units. I click and stuff" (M10). Against it: rulings 1 and 5. | **Rework.** A fixed lifecycle row (draft, then paper, then live) is the hard-coded journey ruling 5 rejects. Skipping QMB ("no judge pass") skips the one required tool. Keep his click and the protected fields. Let the workflow pick the steps, and make a QMB run the one fixed requirement. |
| 19 | First filled paper entry from zero, on a practice venue | yes | **CONFLICT** | "Someone who hasn't been part of developing KMX can use tomorrow" (M49). Against it: "paper bloody trading is demo trading" (M7, 1 Nov) and ruling 1. | **Rework, mostly wording.** Keep the zero-to-first-fill test, renamed "test broker". Paper is the demo account, so add a demo check after his sign-in (PLAN-INTENT-A design call 7). |
| 20 | Ready stop point A for signature | yes | EXTRA | none. The stop points are an agent decision (PLAN-INTENT-B). | **Keep.** It is a version bump. Reword the release note so it does not say "trades on paper". |
| 21 | Named size modifiers | yes | CORE | "we are going to call them accelerators" (M5). "tools or timber to build the platforms" (M50) | **Keep.** |
| 22 | House money as one rule on one ledger | in flight | CORE | "I don't think I want to lose the house of money" (M5). "reverse House of Money was my idea" (M39) | **Build.** Fold `net_r`, not `gross_r` (PLAN-INTENT-A). |
| 23 | Every number: derivation, range, authority, reason | yes | CORE | "that number 5%, for example, has to have a reason as to why it's 5, not 10" (M7). "it should have a range regardless" (M8) | **Keep.** |
| 24 | Built engine widened to risk numbers | yes | CORE | "how do we make it, rather, so that a unit can configure itself without me configuring it?" (M8) | **Keep.** |
| 25 | A sizing and an exit number really move | yes | CORE | "How it configures itself. I'll leave that part to you." (M49) | **Keep.** |
| 26 | Open trades keep their numbers, restart safe | in flight | CORE | "it can self-configure" (M49) | **Build.** Carries rc-07's money fix. |
| 27 | Node's live account surface | yes | CORE | "what changes rather is the account" (M8) | **Keep.** It fits ruling 4 (many accounts). |
| 28 | Costs observed from fills, sizer reads them | in flight | CORE | "we need to know what are the fees, what are the costs, so that the unit can know" (M7). "think of QMX more of as a data analyst" (M51) | **Build.** Give the node a stated-commission cash port (design call 3b). He named market, instrument, timeframe and time, not session or world. |
| 29 | Feasibility verdict, account brakes on two units | parked | CORE | "do you think I can trade with less than $1?" (M49) | **Build.** Needs his yes to a third small fix: the day brake is off after an unwatched midnight (`QUESTIONS-FOR-OPERATOR.md`). |
| 30 | One base bar, every stream rolled up | yes | CORE | "we can have the highest market being scoped by a 1 minute scalper. Then we have the others at a 5 minute scalping" (9 Nov) | **Keep.** |
| 31 | A unit reads a second stream | yes | EXTRA | none. Several timeframes inside one unit was never asked for. | **Keep.** It is built, clean and cheap. Removing it costs more than keeping it. |
| 32 | More than one position per market | yes | CORE | "isn't there a possibility that one unit can hold more than one trade at a go?" (M7) | **Keep.** |
| 33 | Sessions and per-market settings | in flight | CORE | "Session opens, maybe we haven't catered for that" (M8) | **Build.** "Go flat before a session closes" is the unit's own exit, not a brake, so it is allowed. |
| 34 | Remaining logic roles run | in flight | CORE | "If you look at the dictionary has closing mechanisms." (M49). "enhance the dictionary under QML" (M38) | **Build.** Strike the `derivation` and combiner sentence (design call 4). |
| 35 | SQS as a gate slot, cost hurdle first | no | CORE | "I'm trying to observe them, see what I can do." (M51). "The kill switch has survived multiple versions." (M5), said of the kill switch and SQS. | **Build.** The gate may lower or block an entry, never close a trade. |
| 36 | Isolation, news and caution on one sticker | no | CORE | "I wouldn't trade that instrument on its news day" (M51). Against moving news: "on news days, we had the kill switch" (M10) | **Ask him.** Should news be a sticker or stay with the kill switch? Build the news half once he answers. Market isolation is portfolio-level (T-103: "perhaps at the BMS level"), so it waits for pods. |
| 37 | Node spread sensor, one curve per world | no | EXTRA | General invitation only: "I requested for maybe designs for the SQS systems, MIS systems" (M52) | **Park.** It is an SQS enhancement, not the template. Revisit with demo data. |
| 38 | Move the SQS rule before the old gate goes | no | EXTRA | none | **Build only if** the repair's C-20 really deletes the old gate. Otherwise drop it. |
| 39 | Scalper and intraday templates | no | CORE | "each unit should have its specific template" (M8). "one template by any type" (M10). "Remember, this thing is scalping." (M49) | **Build.** Say they "fill on the test broker", plus a demo check after sign-in (design call 7). |
| 40 | One admit seam, called by both hosts | no | EXTRA | none | **Park.** It is a refactor. Widen RC-06's seam in place when RC-35 needs it (design call 8). |
| 41 | Kill effects on entries, off switch on every veto | no | EXTRA | Tangential: "The kill switch has survived multiple versions." (M5) | **Park, except one small fix.** Make the node's entry guard read the kill table he can edit (design call 10). This follows his standing rule that what is configurable is editable in the UI. |
| 42 | Node in two passes, exits first | no | CORE | "closing a trade is never blocked" (M5) | **Park until many units share one node.** It is not needed for a first template on demo. |
| 43 | A parked entry gets a lifetime | no | EXTRA | none | **Park.** |
| 44 | Time budget for the entries pass, honest watchdog | no | EXTRA | none | **Park.** |
| 45 | A declared no-stop entry | no | EXTRA | none. Against it: "stops are now part of a unit" (M5). The plan's line "Your reckless scalper with no stop" is not his. | **Drop**, unless he asks for a stopless unit. |
| 46 | A no-stop position kept alive | no | EXTRA | none | **Drop**, with RC-45. |
| 47 | Copilot doors for one unit | no | CORE | "Copilot and I could do what exactly we are doing right here" (M50). "How do agents talk to it? How do they know that the things are correct?" (M10) | **Build.** Ruling 6 makes the copilot the main door, so this row matters more now. |
| 48 | Single-unit developer guide, stop B | no | CORE | "And it's maintainable, please." (M52) | **Build the guide.** Fold in RC-66's "add-a-thing" pages. Drop the stop-point framing. |
| 49 | Group document, limits as live facts | no | POD | "the BMS is the one that does the splitting" (M8). "Think of it like the pod manager in a hedge fund." (M7) | **Wait** for the pod design (Book plus BMS, versioned). |
| 50 | Group caps that can only cut | no | POD | "the BMS had rules" (M8) | **Wait.** |
| 51 | Default group rows, kill line, restart rules | no | POD | "it's a pod question" (M49), said of the portfolio day stop. "the BMS doesn't allow the floor to be touched" (M8) | **Wait.** He ruled the portfolio day stop a pod question. |
| 52 | Replay several units, group at 200 | no | POD | none direct. "I could have 200 units" (M49) | **Wait.** Group backtests come with pods, through QMB. |
| 53 | Pod as a recipe stamped into the unit | no | **CONFLICT** | "if we're able to templatize a pod" (M7). Against it: ruling 3. | **Drop and redo** after the pod design. A recipe stamped into a unit's risk half is not a portfolio a unit lives in. |
| 54 | One pod edit gives one plan and one click | no | **CONFLICT** | none. It builds paper twins, which the ratified ADR-0009 and ADR-0022 list as dead (PLAN-INTENT-B D5). | **Drop and redo** after the pod design. It rests on RC-53's recipe model and on dead twins. |
| 55 | Move risk in place, open trades untouched | no | POD | none | **Wait.** It delivers recipe rolls. Revisit as "change a unit's risk with no cold start" once pods are designed. |
| 56 | Stages: "at 5,000 the math changes" | no | POD | "at 5,000, the math changes drastically" (M51), which he also told the agent to "keep aside" for the numbers talk | **Wait** for the numbers talk and the pod design. |
| 57 | Seed the pod gallery (20 configurations) | no | POD | "I remember asking you to see if you could figure out some pod ideas or configurations." (M49) | **Wait.** Re-cut the 20 configurations against the Book-plus-BMS pod design. See the mini-app table. |
| 58 | Readings bus: publisher and fallback on every read | no | MINI-APP | "mini apps can provide output and input for other mini apps" (M50) | **Park.** It is an MIS overhaul. A template does not need it to trade. |
| 59 | Land items from a mini app; save a block through a door | no | MINI-APP | "how do we ship pods?" (M10). "Can we add external things like you know, external code?" (M10) | **Build the `blocks_save` half**, which is how the template is extended. The pod lander waits for pods. |
| 60 | Trace a Library block to a node deploy | no | MINI-APP | "I can have a unit made through the lab... or a unit come from a mini app. Those are like four different types of units. All of them can trade." (M49) | **Build, as a test inside RC-59**: a new Library sizer trades on the test broker. Leave out the reading trace. |
| 61 | Apps read journals and the fold, raise a card | no | MINI-APP | Needed by the next row | **Build.** The fleet watch cannot work without it. |
| 62 | Scripted fleet watch as a mini app | no | MINI-APP | "Why would I have to be there monitoring units?... Why not just have an agentic workflow that can cater for that? As a mini app also." (M49) | **Build.** It is the one mini app with a direct ask. |
| 63 | Report with and without motion; reserve the proposal row | no | EXTRA | none | **Drop or shrink to labels.** QMB already offers both arms as an option (design call D7). |
| 64 | Keep a unit's record when a placeholder is swapped | no | CORE | "they just swap it out" (M52) | **Build.** Use `@2 -> @3`, not `@1` (PLAN-INTENT-B). |
| 65 | Re-test every deployed unit after a compiler bump | no | EXTRA | none. General: "one single mistake in such a system is very costly" (M50) | **Park** until units are deployed on demo. |
| 66 | Finish the guide, ready stop point C | no | CORE | "And it's maintainable, please." (M52) | **Merge into RC-48.** |
| 67 | Signed stop, amended with a read-back | no | CORE | "for intraday, you now look at that dynamic SLNTP, because I think it was just moving the stop loss to break even" (M15, 3 Nov) | **After demo.** |
| 68 | Partial close and trailing on the node | no | CORE | The same "dynamic SLNTP" words (M15). Nothing on partial closes. | **After demo.** The trailing half traces to his words. The partial-close half is weak. |
| 69 | Venue targets, entry forms, netting per venue | no | EXTRA | none. Ruling 4 makes netting per venue matter later. | **Park.** Keep today's live-only netting refusal. |

## Mini-app table

There are 7 existing apps on `origin/engine/base` (`qmx-agents/apps/` and `examples/apps/`), and the risk tip `build/rc-25` has the same 7. The planning files propose 42 more:

- **12 apps or desks**, from `expand/E1`, `E3`, `E4`, `E5` and `funnel/FATES.md`.
- **10 agent jobs**, from FUNNEL section 8 and E5 section 1.2.
- **20 pod configurations**, from `expand/E2` section (d). He said pods "are meant to be mini apps" (M10).

### Existing

| App | What it does (from its manifest or README) | His words | Covered elsewhere? | Verdict |
|---|---|---|---|---|
| `mis` (qmx-agents) | Sets the markets it reads, each with an instrument snapshot, packs and shadow readings | "the MIS's job is to act like a router" (M5) | no | **Keep** |
| `qmb` (qmx-agents) | The backtester: its contract, run kinds, fidelities and markets | Ruling 5: QMB is the one required tool | no | **Keep** |
| `trading-node` (qmx-agents) | Hosts units on venues: state, kill level, safe-to-restart | "this version we are going to work on has to go live" (M5) | no | **Keep** |
| `exchange-status` (example) | A screens app showing exchange status | none | Example only | **Keep as an example**, outside this program |
| `macro-daily-bias` (example) | Reads the latest persisted daily bias as an artifact | "how can agents be used for macro, micro, agents used for news" (M25) | Example only | **Keep as an example.** It is the seed for the proposed macro desk. |
| `mql5-articles` (example) | Imports MQL5 articles daily (only network: mql5.com) | His interest in MT5 articles (3 Nov, U17) | Example only | **Keep as an example** |
| `weekend-watcher` (example) | Summarises a verified snapshot into an artifact | none | Example only | **Keep as an example** |

### Proposed apps and desks (12)

| Proposed app | What it does | His words | Covered by the copilot or another app? | Verdict |
|---|---|---|---|---|
| Fleet watch (RC-62) | Reads the fold nightly and on demand. Gives one ranked row per unit, two lists, one card per incident and a morning digest. No agent in it. | "Why not just have an agentic workflow that can cater for that? As a mini app also." (M49) | no | **Keep** |
| Risk Lab app (H3-T34, X1-H29) | Re-sizes a recorded trade list under another sizing rule | none | Copilot plus QMB. Ruling 6 may drop the lab. | **Drop.** If wanted, make it a QMB run kind. |
| Risk app with an MCP server (H4-I-58, X7-H36) | Exposes risk state to agents | "How do agents talk to it?" (M10) | The copilot doors (RC-47) | **Merge** into RC-47 |
| Instrument dossier (E1 idea 72) | One page per instrument | none | MIS plus copilot | **Merge** into MIS |
| Macro desk (E1 section 6) | Publishes a `usd-state` reading | "agents used for macro" (M25) | The `macro-daily-bias` example | **Merge** into that example. It belongs to the agentic session. |
| FX desk (E1 section 6) | FX readings and de-risk cards | "instrument specific mini apps" (M50) | none | **Ask him.** It belongs to the agentic session, not this program. |
| Futures desk (E1 section 6, E2) | His week-long futures example | "a mini app that is optimized for futures" (M50) | none | **Wait.** There is no futures route yet. It belongs to the agentic session. |
| Gold fast readings (E1) | Fast readings for gold, computed at the node | Gold sniping windows (M50), but no app ask | MIS and node sensor | **Merge** into MIS |
| Index "opens in play" (E1) | An ORB shortlist each day | ORB interest (M8), but no app ask | MIS | **Merge** into MIS |
| News calendar to stickers (RC-36, FUNNEL D29) | Calendar events become stickers | "I wouldn't trade that instrument on its news day" (M51). "on news days, we had the kill switch" (M10) | The kill switch, if he says so | **Ask him** where news lives |
| Three-stage placement (E4-N11) | Placement weights as configuration | none | MIS router | **Merge** into MIS. The weights are numbers talk. |
| Monitoring and triage app (E3, paper 2607.08010) | A monitor with an agent | "Why would I have to be there monitoring units?" (M49) | Fleet watch | **Merge** into the fleet watch |

### Proposed agent jobs (10)

| Job | What it does | His words | Covered? | Verdict |
|---|---|---|---|---|
| Triage | Reads the top ranked units and each incident, and names a cause | "agents can help us discover this earlier" (M49) | The fleet watch's agent layer | **Merge** into the fleet watch, later, in the agentic session |
| Morning words | Writes the morning digest from scripted facts | none | The fleet watch digest | **Merge** into the fleet watch |
| Coroner | Studies benched units and turns patterns into detectors | "a unit whose edge was never real... agents can help us discover this earlier" (M49) | Fleet watch plus copilot | **Merge** with drift explainer, into the fleet watch, later |
| Drift explainer | Explains live-against-backtest drift | "You're meant to size down, I think, but not quickly" (M10) | Copilot (`explain_size`, RC-47) | **Merge** with coroner |
| Sitting-duck advocate | Finds units the brakes hold below baseline | "I don't want just safety. I want something that can like perform" (M33) | The fleet watch's second list | **Merge** into the fleet watch |
| Prospector | Looks for new strategies | "agents that could be specialized at looking for strategies" (M50) | none | **Ask him.** It belongs to the agentic session. |
| Slow isolation cards | Proposes isolating a market | "It should kick in with... evidence that this market should be isolated" (M10) | none | **Wait** for pods, since isolation is portfolio-level |
| Per-class agents and event mapper | One agent per asset class, plus news-event mapping | "think of them like departments, macro structure, micro structure" (M50) | none | **Wait.** It belongs to the agentic session. |
| Template version drafter | Drafts a new template version | "using QML to make the unit maybe templates for a scalper" (M50) | The copilot's draft patch (RC-47) | **Merge** into the copilot |
| Tuning proposer | Proposes moved numbers under the applier | "More of a hill climb challenge." (M49) | Motion engine (RC-24, 25) plus copilot | **Merge** into the copilot |

### Proposed pod configurations (20, from E2 section (d), shipped by RC-57)

He asked for these: "I remember asking you to see if you could figure out some pod ideas or configurations." (M49). Under ruling 3, each must be re-cut as a Book-plus-BMS portfolio. None has run.

| Pod | What it is | His words | Covered? | Verdict |
|---|---|---|---|---|
| 1 Relentless | The old April system: half-Kelly, nine multipliers, many caps. About 20 new blocks. | Against it: "too much machine" (M1/M5) | none | **Drop** as a shipped pod. Keep it as a history note. |
| 2 Session relay | One pot passed through the day's sessions | "Session opens, maybe we haven't catered for that" (M8) | none | **Wait** |
| 3 Classic Book | The Book's ladder, with floor, sweep and virtual ledger | "the book is the right skeleton" (M10), though he called it open to change (M31) | none | **Keep.** It is the first input to the pod design. |
| 4 Cushion pair | House money and reverse house money as one rule | "reverse House of Money was my idea" (M39) | RC-22 | **Merge** into the RC-22 template preset |
| 5 The old pair, as it was | The old house money and streak pair | none | Pod 4 | **Merge** into pod 4 |
| 6 Scalper first | Costs, news, cooldown, several positions | "we are starting with scalpers" (M49) | The RC-39 scalper template | **Merge** into the template |
| 7 Human mimic | Order flow in chosen windows | "Order flow, I think, is already being handled" (M51) | Another session | **Drop for now** |
| 8 Best basket | Few units until capital allows volume | "Why not look for the best basket" (M50) | none | **Ask him** in the numbers talk |
| 9 Stage switcher | A stage line swaps sizing rows | "at 5,000, the math changes drastically" (M51) | RC-56 | **Wait** for the numbers talk |
| 10 Prop rider | A prop-firm rule sheet as data | Against it: "prop farm buffers are not ideal. I was just explaining" (1 Nov) | none | **Drop** |
| 11 Earned tiers | A prop-derived tier signal | Same as pod 10 | none | **Drop** |
| 12 Multi-manager | Soft and hard stops, the BMS as manager | "Think of it like the pod manager in a hedge fund." (M7) | none | **Keep.** It is the BMS half of the pod design. |
| 13 Own size, capped total | Each unit keeps its size, and only losing together is capped | "the more units I have, the less I can trade" (M49) | none | **Keep.** It is a pod design input and answers his complaint directly. |
| 14 Run together | A pod of pods | none | none | **Wait** |
| 15 Futures desk pod | His futures week | "a mini app that is optimized for futures" (M50) | Futures desk | **Wait.** There is no futures route. |
| 16 Model-sized hybrid | Taken from the old demo gallery | none | none | **Drop** |
| 17 Watched by agents | Units under agent watch | "Why would I have to be there monitoring units?" (M49) | Fleet watch | **Merge** into the fleet watch |
| 18 Volatility core | Taken from the old demo template | none | none | **Drop** |
| 19 Canary | Smallest possible, for a first run | "something that anyone can use... right out of the box" (M49) | The RC-17 template | **Merge.** It already exists. |
| 20 Full press | A reckless setup that the template layer can express | Against it: "aggressive and nuclear are two things" (M8) | The template layer | **Drop** as a shipped pod |

**Mini-app verdict tally for the 42 proposed:** keep 4, merge 19, drop 8, ask him 4, wait 7.

- **Keep:** the fleet watch, and pods 3, 12 and 13.
- **Merge:** risk MCP, dossier, macro, gold, index, placement, monitoring, the 7 merged jobs, and pods 4, 5, 6, 17 and 19.
- **Drop:** Risk Lab, and pods 1, 7, 10, 11, 16, 18 and 20.
- **Ask him:** the FX desk, the news calendar, the prospector, and pod 8.
- **Wait:** the futures desk, slow isolation cards, per-class agents, and pods 2, 9, 14 and 15.

## The program cut to his ask, in plain words

What he asked for is one unit template. A person who has never seen QMX can pick it, plug in their own settings, and have it trade on a demo account. It sizes itself in money across any instrument, configures its own numbers inside ranges, explains every size, and closes its own trades through its own exits. A developer or the copilot can extend it, and QMB backtests it. Pods are built around it later.

1. **Keep the 28 built rows.** They are the template's spine: logic and risk halves, a sizer that answers money, exchange rates, the decision row, fault walls that never block an exit, exits with reasons, brakes as rows, the fold, risk events, the canary template, the numbers that move, the live account, base bars, several positions. Three rows need reworking to match today's rulings:
   - **A brake never closes a trade** (RC-16). Only the kill switch's black-swan level does. Take `flatten` out of the brake verbs (RC-13).
   - **No fixed draft-to-paper lane** (RC-18). His click stays. The workflow chooses the steps, and a QMB backtest is the one fixed requirement.
   - **"Paper" means the demo account** (RC-19, RC-20). The practice venue is renamed the test broker. The stop A note stops claiming paper trading.
2. **Finish the six in-flight rows**:
   - **RC-22, house money.** Fold `net_r`.
   - **RC-26, open trades keep their numbers.**
   - **RC-28, costs from fills.** Add the node's stated-commission cash port.
   - **RC-29, feasibility.** Needs his yes to a third small fix.
   - **RC-33, sessions.**
   - **RC-34, logic roles.** Strike the combiner sentence.
3. **Build what the template still lacks:**
   - **RC-35:** the SQS gate slot with a cost hurdle.
   - **RC-39:** the scalper and intraday templates, worded as filling on the test broker, plus a demo check after his sign-in.
   - **RC-47:** the copilot's doors for one unit. This is now his main door, since the lab may go.
   - **RC-48 with RC-66:** the developer guide.
   - **RC-64:** swapping a stand-in keeps the unit's record.
   - **RC-59 (`blocks_save` half) with RC-60 as its test:** a new Library block, saved and traded with no core edit.
4. **Ship one mini app, the fleet watch** (RC-61 and RC-62). It is the only proposed app he asked for in his own words.
5. **After his demo sign-in, add the stop and trailing work** (RC-67, RC-68). This traces to his "dynamic SLNTP" for intraday.
6. **Ask him two things before building:**
   - Does news live on a sticker or with the kill switch (RC-36)?
   - Does he want a stopless unit at all? The default answer is no: drop RC-45 and RC-46.
7. **Let the pod design come first.** RC-49 to RC-52 and RC-55 to RC-57 wait for Book-plus-BMS pods. RC-53 and RC-54 are dropped and redone afterwards: they made a pod a recipe stamped into the unit, and they revive dead paper twins.
8. **Park or drop the rest.** These are node hardening for many units (RC-40, 42, 43, 44), SQS and MIS overhauls (RC-37, 38, 58), compiler re-tests (RC-65), motion reports (RC-63) and venue entry forms (RC-69). None has an ask behind it, and none is needed for a first template on demo. One exception: a one-line fix from RC-41, so the node's entry guard reads the kill table he can edit.

**Size of the cut:** the 28 built rows, plus 19 more:

- 6 in flight or parked.
- 9 to build: RC-35, 39, 47, 48 with 66, 59, 60, 61, 62 and 64.
- 2 after the demo sign-in.
- 2 that depend on his answers: RC-36 and RC-38.

That is 47 PRs against 69. One of the 9 build slots is shared by RC-48 and RC-66.
