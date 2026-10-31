# Solutions funnel: index

Written 2026-10-31 by agent F1 (the solutions funnel). It generates and converges solutions for every part of the foundation; it does not write the architecture, which is the next step. Read the frame first (`architecture/00-frame-after-grounding.md`); where this folder and `STATE.md` differ, `STATE.md` wins.

## Read me first

1. The foundation is a small core that already mostly exists, plus seven new shapes and three mini apps.
2. The core: QML and its checker, the dictionary, the unit document, the judge and the count of tries, the journals, and one page of facts per market.
3. The three mini apps: QMB (the backtester), the trading node (the only thing that sends orders) and the MIS's publishing process.
4. A unit tunes itself at two speeds: numbers that follow price move every bar; numbers that follow its own record move slowly and carefully. The rules themselves only change by his click.
5. The dummy unit is a trend pullback on EURUSD and gold, built only from indicators QMX already runs, and it proves the whole chain on real parts.
6. Making the trading node a mini app lets it run natively on his Windows PC for practice and on a Linux server for live, with no WSL.
7. No question for him came out of this step; every open choice is a lead's call below, with how to undo it.

## How this was made

- **Skills, in order.** `bmad-party-mode`, explicit non-interactive, session mode, inline cast (18 voices, 18 rounds): `party-transcript.md`. `bmad-brainstorming` headless, techniques chosen from `brain.py list --all` and switched about every ten ideas: 160 ideas (S001 to S160) and 8 insights logged through `memlog.py` into `.memlog.md`. Convergence per `references/converge.md`: Affinity Clustering (ideas by part), then a Solution Matrix on standing order 6 (hard cases, maintain and debug, explain), then MoSCoW for the first build (§6). Status `complete` in the memlog. Activation scripts ran (`resolve_customization.py`, `resolve_config.py`, `resolve_party.py`); the stale factory facts and `on_complete` endings were ignored, and nothing was written to `_bmad-output`.
- **Deviations, each a lead's call.** No HTML keepsakes (his "No need for an explainer site." (T2:602), ledger P-19). No separate `brainstorm-intent.md`: this index is the intent digest, because the brief names only the part files and the index. The GPT voice that built the dictionary was not cast, because it may speak only from research 39's record and research 39 was not read in full here; its ideas reached the room through G1 §8 and research 43.
- **Harvest before generating.** Read in full: the frame, the workflow note, `STATE.md`, the ledger, G1, G2, G3, G4a, G4b, research 54, 53, 43 (§1 to §8 and Appendix B), his 31 Oct messages from 09:12 to 10:00 in T3, the five earlier funnels' intent files, `QMB-BACKTEST-DOOR-HANDOFF.md`. Read in part: research 52 (§4, §9), research 08 (§0 to §1.5), research 38 (§3.8), `funnel4-qml/cis/seams-options.md` (§4, §6, §7), the risk pack (§4), the risk-lab `grounding/07-qmb-lineage.md` (§0 to §2, §7 to §10) and `decisions.md` (QML section), his messages in T1, T2 and T3 matching QMB and backtesting (by script). Not read directly: research 01 to 07, 09 to 42 beyond what research 43 and the groundings cite, the funnels' full field and CIS files, the explainer sources beyond page titles and QMB lines, the Hermes files (10, 39, 40, 41). Each part file's "Harvest" table names the file and section of every solution it carries.
- **Labels.** Every claim in the part files is CHECKED (file and section, or run) or INFERRED. Code facts come through the grounding files that checked them at `origin/engine/base` `c93407ca`; five were rechecked here in the read-only checkout (the empty unit schema, the mini-app isolation and breaker defaults, the `app_op` docstring, the CT-13 docstring, the supervisor's restart and breaker lines).
- **His voice is quotes only.** A script (`quotecheck.py` in this agent's scratchpad) checked every `"quote" (Tn:line)` in this folder against the cited transcript line, with files opened `newline=''`: see §11.

## 1. The parts and the recommended pick, one line each

| Part | File | Core or mini app | Recommended pick |
| --- | --- | --- | --- |
| QML | `qml.md` | core | Upgrade in place: a declared skeleton of slots filled by tested code blocks, compiled once into today's factory seam; a five-verb door; a checker in seven layers reaching agents through a catalog row, the Library's save and (after a probe) a core-plugin hook |
| The dictionary | `dictionary.md` | core | One kind with three faces (trader words, machine spec, implementation), status computed by script, three homes per class; builders port the 239 and expand with no cap |
| The unit | `unit.md` | core (a Library kind and a template) | `qmx.unit/1` with every number carrying kind, range, motion, authority and origin; two tuning speeds with the motion running inside the backtest; the identity table and a per-market lifecycle |
| QMB | `qmb.md` | mini app (first) | QMB as a mini app with a contract any version implements and a conformance pack; the core keeps the landing, run id and try count; rebuild the reader and the runner, extend results with R, keep the measuring parts |
| Judging | `judging.md` | core | A core judge with a study spec written first; one rule for every market, each a counted try, pulled toward the whole; cheapest-first chain; paper as the honest test |
| Journals | `journals.md` | core | One envelope on CT-13 with typed kinds; one writer per partition; nodes write locally and ship one way to the PC |
| The MIS | `mis.md` | readings core; publisher a mini app | Readings as catalogue blocks a unit computes itself; an `mis` app with node and PC instances; defaults for every class; models in shadow |
| Instruments | `instruments.md` | core (a part he did not name) | One record per instrument per venue, refreshed from the venue; its data-level table drives the checker, the MIS and the futures seam |
| The trading node | `node.md` | mini app (second, risk money) | Keep the organs, replace the shell; a money mini app on the QMX host; practice on This PC, live on a trading server under a trading profile; self-healing by desired state |
| External connections | `external.md` | core ports, adapters behind | One venue-client port with cTrader and a CCXT adapter (Binance, Bybit, Hyperliquid); order flow in three layers; futures routes designed and off |
| Contracts | `contracts.md` | core | Seven new shapes through the doors that exist; twenty connection points; versioning rules |
| Copilot and agents | `copilot-and-agents.md` | core (built) | Register, do not rebuild: rows, skills, one hook, one validator change, a parity test; slow-lane agents as templates |
| Workflows | `workflows.md` | content on the core engine | Build the shared core and the first families; fix the hard-coded holdout and loop caps |
| DevOps and clocks | `devops-and-clocks.md` | core | OpenObserve only; UTC stamps, market-zone sessions, every machine reporting its own clock |
| Mini apps | `mini-apps.md` | the cross-cutting verdict | Three default apps on the unchanged mini-app core; QMB's app as the worked template |

## 2. Is the frame's shape right?

Mostly yes. Five refinements, each argued in its part file:
1. **The judge and the try count belong in the core, not in QMB.** Once QMB is a swappable mini app, a new version must not be able to change the score (`judging.md`, insight I3).
2. **The MIS is two things.** Its readings are core code every unit runs; only its publishing process is a mini app, the third one (`mis.md` §3).
3. **The instrument record is a core part he did not name.** The checker, QMB, the node and the MIS all read it, and it is how "futures accounts and every instrument now" is designed without trading them yet (`instruments.md`).
4. **The node as a mini app does more than simplify.** It removes QMN's three Linux-only pieces, so the practice node runs natively on Windows and the WSL fallback is rarely needed (`node.md` §3, insight I2).
5. **The node comes late in the build, but its practice placement is needed for proof mark P8** (the dummy trading on demo). Late, not last.

## 3. The weak spots, and where each is solved

| Weak spot | Solved how, in one line | Where |
| --- | --- | --- |
| 1. Two speeds of tuning | Every number declares its motion source (price, own record, a reading, fixed) and cadence; record-driven numbers wait for a minimum count, shrink toward the default and move one step at a time; the motion runs inside the backtest, so live motion is not a new try | `unit.md` §4 |
| 2. The dummy unit moving a real number | Trend pullback on EURUSD and XAUUSD M15: the RSI trigger moves every bar as a percentile of its own history; a minimum trend-strength filter moves nightly from the unit's own closed trades by a shrunk rule; exits and sizer are labelled placeholders | `unit.md` §8 |
| 3. Trade counts and the luckiest market | Rules written before results; the same rule for every market; every judged market a counted try; results pulled toward the unit's overall result; correlated markets as one record; counted in the core | `judging.md` §4 |
| 4. Feedback while agents write | A pure checker in seven layers returning every problem with a pointer and a hint; through a catalog row, the Library's save (no path skips it) and a core-plugin hook after a probe; a CI gate over a known-good corpus keeps false positives at zero | `qml.md` §7; `copilot-and-agents.md` §3 |
| 5. The dictionary's form and growth | One page per concept with three faces and a computed status; per-class meaning tables and transfer status; builders port and expand with directions and no cap; later growth through the authoring door, checked by the same scripts | `dictionary.md` §4 to §8 |
| 6. Journals across instruments, brokers, accounts, platforms, nodes and worlds | One envelope with every slicing key, typed kinds with depth, one writer per partition, per-market state so a unit can go back to paper on one market, one-way shipping from nodes | `journals.md` §3 to §5 |
| 7. Futures order flow with no paid platform | Free real order flow from crypto venues (and Hyperliquid's index, gold and FX perps); computed broker-side estimates on cTrader; a futures data route he switches on later; units read order flow as readings with data levels and fallbacks | `external.md` §5 |
| 8. Clocks across regions | UTC stamps; venue and receive time on market events; every machine reporting zone, offset and sync; sessions in the market's zone; display in his chosen zone; clock bands block entries when time is wrong | `devops-and-clocks.md` §4, §5 |
| 9. A newcomer starts a node and deploys with little stress | A "Trading node" kind in the connect dialog: practice on This PC first, checked steps, a self-test passport, the word "running"; deploy is one button on the unit page; the dummy unit ships installed | `node.md` §6; `mini-apps.md` §8 |
| Research 53: a unit cannot show tuning through a placeholder | The dummy moves a logic number, not a placeholder | `unit.md` §8 |
| Research 53: breadth is not independence | Correlated markets count as one record; the MIS publishes dispersion and herding counts for the risk session | `judging.md` §4; `mis.md` §4 |

## 4. Lead's calls (each: what, why, how to undo)

| # | What | Why | How to undo |
| --- | --- | --- | --- |
| LC-01 | QML's door is five verbs (new, check, compile, find, explain); "promote" is never a verb an agent can call | promote is only his click (CC-11); backtest belongs to QMB | add verbs to the door |
| LC-02 | Refusal functions and old `GAP_*` constants that contradict the rulings leave QML's public surface; "invented exit" and "never sizes" become labels | a builder reading the surface takes them as current law (G1 trap 4) | re-export them |
| LC-03 | The compiler's runnable artifact is a closure with a decision trace; a generated Python rendering is exported read-only | one artifact runs, so it cannot drift from what was tested | make the rendering the runnable artifact |
| LC-04 | The scan's deny list widens (importlib, `__import__`, eval, exec, unseeded numpy.random) as errors for agent-written blocks and warnings for human-written Python | agents get no holes; QML never stops a human (CC-08) | revert the deny list |
| LC-05 | The checker's catalog row and Library door are Must; the core-plugin hook is Should after a probe | the hook's firing under the Agent SDK is unproven | promote the hook to Must |
| LC-06 | Every number has a typed unit of measure; pips are an error unless source-stated and defined for that market | a wrong scale is the costliest small mistake | relax to a warning |
| LC-07 | The dictionary extends the BUILT `component` kind rather than adding a new kind | reuses a kind with no writer | add an `entry` kind |
| LC-08 | Multi-meaning words: one entry with a per-class meaning table; split into `same-word-as` entries only when the code differs | one place to look, no silent mixing | one entry per meaning |
| LC-09 | Market settings live inside the unit document | one item, simple | separate linked items per market |
| LC-10 | The dummy unit is a trend pullback on EURUSD and XAUUSD M15 with the two moving numbers in `unit.md` §8 | built only from blocks that run; enough trades to move the slow number | pick another strategy; the proof list is unchanged |
| LC-11 | Motion rules run inside the backtest; motion on and motion off are both reported | live motion stays honest and is not a new try | none needed |
| LC-12 | `applies_to_open_positions` defaults to false | exits are the risk session's | the risk session sets it |
| LC-13 | A perps twin of the dummy comes after the first slice runs | one proof at a time | add it to the first slice |
| LC-14 | QMB is a mini app; the core keeps the landing, run id, try ledger, judge and conformance pack | variants side by side without a swapped tester changing the score | keep QMB as a library behind a host door |
| LC-15 | The copilot reaches QMB through the existing `backtest` rows forwarding to the app; `app:qmb` in the home preset is the fallback | the rows already exist and reach the copilot with no settings line | use the preset |
| LC-16 | A QMB tool call waits up to 600 s, then returns a handle | tool calls should not idle for hours; workflows wait fully | change the number |
| LC-17 | The study spec fixes the shrinkage estimator before any run; default: k estimated from the spread between the unit's markets | honest and not tunable after the fact | a fixed k in the preset |
| LC-18 | Journals write events and near misses by default; per-bar traces only on request for a time box | answers "why didn't it trade" at a fraction of the volume | turn per-bar traces on for the first days of each deployment |
| LC-19 | The MIS's publishing process is a mini app from the first build | templates need its logs; the node's setup installs it | ship reading blocks only and add the app later |
| LC-20 | "Regime" takes his meaning (trend against range); the shipped volatility buckets are renamed "volatility state" | these are the words on his screens | keep "regime" for volatility and name the trend reading "trend state" |
| LC-21 | The node keeps its organs and replaces its shell; the old host, seats, promotion, Book paper, doors, deploy recipes, bench and Grafana stack are deleted in the same wave once the shell trades on demo | his "fresh start" (T3:1562) without rewriting the parts that are right | keep QMN's host and refactor it instead |
| LC-22 | The node is a money mini app inside the host's supervisor, with its own inner supervisor; the server's host is a systemd service that always restarts; host updates only on his click when the node is safe | one install and one monitoring path, with trading protected | run the node as its own service the host adopts |
| LC-23 | A live-capable grant is stored only by the node app on a machine he marked "trading server"; that host runs a trading profile with no chats and no agent steps; every other host keeps refusing | ruling 135 handled technically; agents never work where a live key lives | none needed |
| LC-24 | Both soak numbers are kept as settings: 24 hours on the PC before a release, one week on demo before a live binding | both have a reason; neither is a cap | change either number |
| LC-25 | The node's seven blank boot values get starting defaults (`node.md` §10) | blank values block boot | change the numbers |
| LC-26 | Hyperliquid goes through CCXT's class first, with a testnet probe; a native client only if the probe fails | the pinned package already has it | build the native client |
| LC-27 | No Databento adapter in the first build; the data-route port and data levels only | nothing spends his money before he chooses | build the adapter dormant |
| LC-28 | The feed keeper lives inside the node app | the node's lifeline must not depend on another app | a separate feed app per machine |
| LC-29 | Seven new shapes carried by existing doors; breaking changes are new schema versions with upgrade scripts | fewer contracts, one catalog | a separate internal API |
| LC-30 | Workflow agent steps stay without file tools (AGW not built) | units do not need it | build AGW through the undo phrase in the build store |
| LC-31 | A unit-builder sub-agent in the core plugin is a Should | content only, a clean helper for the copilot | drop it |
| LC-32 | The shared workflow core and the first families are built in the coding phase | his "build them" (T3:903), ledger W-01 | none |
| LC-33 | One zone rule: storage in UTC; market-tied jobs in the market's zone; his own routines in his PC's zone | three defaults disagree today | pick another default |
| LC-34 | OpenObserve is the only monitoring stack; QMN's Grafana, Loki and Prometheus are deleted | one place to look | keep both |
| LC-35 | The first-start card offers one click to turn on QMB, the MIS and the practice node | enabling is his act; out of the box stays simple | enable each app separately |
| LC-36 | Units are never mini apps; a "unit companion" app template is parked | only the node sends orders | build the companion template |
| LC-37 | Moving a unit from tested to paper is his click by default; the automatic switch after the cheap checks exists and is off | his rule that only he promotes (CC-11) read strictly, though paper holds no money | turn the switch on |
| LC-38 | No HTML keepsakes and no separate intent file; this index is the brainstorm's intent digest | his "No need for an explainer site." (T2:602); the brief names only these files | render them from the memlog |

## 5. Open clashes from the party, and where each landed

| Clash (party round) | Landed as |
| --- | --- |
| Compiler output: closure or generated source (P1) | LC-03 |
| The hook: Must or Should (P2) | LC-05 |
| Scan deny list for agent blocks (P2) | LC-04 |
| Multi-meaning words (P3) | LC-08 |
| Fast motion while a position is open (P4) | LC-12, for the risk session |
| A perps dummy in the first slice (P5) | LC-13 |
| The copilot's door to QMB (P6) | LC-15 |
| The shrinkage weight k (P7) | LC-17 |
| Per-bar decision logging by default (P8) | LC-18 |
| The regime word in code (P9) | LC-20 |
| A dormant Databento adapter (P10) | LC-27 |
| The node inside the host's supervisor or beside it (P11) | LC-22 |
| Soak length before live (P12) | LC-24 |
| Native Hyperliquid client or CCXT first (P13) | LC-26 |
| Agent steps writing files (P15) | LC-30 |
| The MIS as a mini app from day one (P17) | LC-19 |

## 6. The foundation's first build (MoSCoW)

| Must | Should | Could | Won't this time |
| --- | --- | --- | --- |
| The unit schema in the Library kind; the checker layers A to G; the `unit_check` row and the Library validator returning every problem; the build-unit skill | The core-plugin hook (after its probe) | A Databento adapter, dormant | News units |
| QML's compiler into the existing seam; the laws lifted for units; the old refusals off the public surface | The trading-server kind and live trading on a Linux VPS | Futures venue clients (Rithmic, CQG) | Automatic promotion to live |
| The dictionary's form, checker and status script; the port of the 239; the first content wave with no cap | The MIS node instance and the board | A unit-builder sub-agent | Agents in the fast lane |
| Instrument records for cTrader FX, gold and index CFDs; futures records as `specified` | The CCXT venue client for orders and the Hyperliquid testnet probe | A perps twin of the dummy | MT5 live units; IBKR; TopstepX |
| The QMB app with the core landing and try ledger, the windowed reader, the typed-partition entry, a runner that trades a unit, R and receipts, the conformance pack | The shared workflow core and the first families; the decay check; the node watcher | Models in shadow through the Lab | A compiled hot path |
| The core judge, the study spec, the default chain | The dictionary-expansion and librarian templates | | A unit chat home; agent steps writing files |
| The journal envelope, the writer library, `journal_query` | A copilot parity test | | |
| The dummy unit passing proof marks P1 to P7 | Proof mark P9 (a haiku agent writing a unit, needs his sign-in) | | |
| The practice node on This PC: the shell with the kept organs, the feed keeper, cTrader demo orders with protection at the broker, reconcile, the kill switch, per-unit paper, the self-test, the connect-dialog kind; proof mark P8 | | | |
| The MIS reading blocks for bars and quotes; the `mis` app's PC instance | | | |
| The one-way shipping job (journals and MIS history) | | | |
| Clock reporting on every machine; OpenObserve only | | | |
| CCXT opened for reads of contract markets | | | |

## 7. Parked (good ideas, not foundation)

| Idea | Why parked | Where |
| --- | --- | --- |
| A compiled hot path for tick-speed order-flow units | the network is the floor at 1-minute speed | `qml.md` §13 |
| Exporting a unit to a cBot or EA for a cross-check | not needed to prove the unit | `qml.md` §13 |
| Units reading other units live | breaks standing alone; build-time composition instead | `unit.md` §13 |
| Rules that rewrite themselves | only he promotes | `unit.md` §13 |
| A GA sampler, a Rust speed path, ML and RL inside QMB | after the first slice | `qmb.md` §13 |
| A meta-test of each judge step's lift | needs many judged units | `judging.md` §12 |
| Portfolio optimisation from journals; WF3-style performance studies | the risk session's or later | `journals.md` §11 |
| News readings; fundamentals; vision chart readers; market twins | news is out; later | `mis.md` §13 |
| Options chains; stocks through MT5 | after the first doors | `instruments.md` §10 |
| A passive second trading server; brain and arm beyond agent wallets; MT5 live | not yet | `node.md` §14 |
| IBKR, TopstepX, a dormant Databento adapter | awkward or his money | `external.md` §11 |
| Generated TypeScript client types; webhook signatures | the UI session; backlog | `contracts.md` §10 |
| A unit chat home; AGW; analyst desks by trading style | not needed for units | `copilot-and-agents.md` §10 |
| Crossover across families, a sensor scout, template health, MQL5 article mining | later families | `workflows.md` §10 |
| The unit companion app template; fixing the two broken example apps | no need yet; backlog | `mini-apps.md` §11 |

## 8. For the risk session (points found here; no maths designed)

1. **The placeholder list to rip out:** the dummy's exit set (a protective stop beyond the last swing point plus a buffer, a 2R target, a 48-bar time-out), its sizer (0.5% of equity at risk, rounded down to the lot step, skipped below the minimum lot), its empty halts slot, and the node's kill-switch effect-matrix values (blank in code).
2. **Open positions:** may a number that moves with price change an open trade's exits (`applies_to_open_positions`, default false)?
3. **Stopped to paper:** may a unit's stop rule land it on paper directly, since that moves toward safety, or does paper always need his click?
4. **The kill line flattens; standing order 7 says a risk rule "stops".** Which verb the risk socket uses (G3 trap 11).
5. **A broker stop on every live order?** The foundation places protection at the broker for every placeholder exit set because cTrader has no cancel-on-disconnect; whether every live order must carry one is pack §2.10 C7.
6. **Which risk rules count as the one automatic transition**, and what happens after a decay alarm (an automatic fallback to pooled settings would change live behaviour without his click, research 24 §4.2).
7. **The socket's shape.** The slots follow option R-A (an exit-set port, a sizer port, halts at three scopes) without closing R-B to R-E (seams §6.2).
8. **Rounding sizes:** round down to the lot step and record the residue in R, refusing only below the minimum order (`qmb.md` §7); the risk session may want another rule.
9. **Netting accounts:** one virtual position per unit, or one unit per symbol; who wins a conflict.
10. **The budget share** the sizer slot reads, and how it splits when one unit trades many matching markets or units are added to a small account (pack "expects back" item 7).
11. **The judge shows every result with the unit's sizer and with a fixed-size baseline**; replaying the old "radioactive" (T1:1574) sizing is the risk session's.
12. **Trade rows carry equity before, session, streak and the tuned values in force**, so any sizing rule can be replayed later (`journals.md` §4).
13. **Margin and liquidation in QMB** for perps and futures (a new port) and **trigger price basis per exit** (Hyperliquid stops trigger on mark price).
14. **A cross-unit hook point before every order** for correlation control; the MIS publishes dispersion, herding counts and dated pair readings for it.
15. **A unit with no price stop has no 1R**: R shows as undefined and the money result is flagged (research 43 F1; pack C7).

## 9. UI notes (for the UI agent; notes only, no UI code)

- QMB's runs list, run page and versions panel: `qmb.md` §9.
- The node page, the deploy dialog and the connect dialog's "Trading node" kind: `node.md` §12.
- The unit's preview card and detail page, and the "why didn't it trade" line: `journals.md` §7.
- The calibration dial per number on the unit page: `unit.md` §4.
- Node tiles shown in his chosen zone with each node's office time and clock band: `devops-and-clocks.md` §7.
- The first-start card's one click for the default apps: `mini-apps.md` §7, §8.

## 10. Files in this folder

| File | What it holds |
| --- | --- |
| `00-index.md` | this file |
| `party-transcript.md` | the party, 18 rounds, clashes left open |
| `.memlog.md` | the brainstorm's canonical log: 160 ideas, 8 insights, 15 decisions, status complete |
| `qml.md`, `dictionary.md`, `unit.md`, `qmb.md`, `judging.md`, `journals.md`, `mis.md`, `instruments.md`, `node.md`, `external.md`, `contracts.md`, `copilot-and-agents.md`, `workflows.md`, `devops-and-clocks.md`, `mini-apps.md` | one part each |

## 11. Quote check

Run on 31 Oct after the last edit, over the 17 Markdown files in this folder: 181 of 181 quotes of his words found on their cited transcript lines, 0 not found. The script (`quotecheck.py`, kept in agent F1's scratchpad) reads every `"quote" (Tn:line)` pair, opens each transcript with `newline=''` so its line numbers match `grep -n`, and normalises whitespace and curly quotes before matching. Fragments of his words used without a line (for example inside a lead's call) were either given their line or rewritten as plain reference to the ledger row, so nothing in his voice goes unchecked.
