# Party mode transcript: solutions for the foundation

Run 2026-10-31 by agent F1. Skill: `bmad-party-mode`, run as an explicit non-interactive party (`--non-interactive --mode session`) on the brief's intent until a natural close. One mind voices every persona; nobody was spawned. Activation scripts ran from the QMX checkout: `resolve_customization.py` (party_mode `session`), `resolve_config.py` (user Mubarak, English), `resolve_party.py` (`installed_agents_resolved: false`, so the inline cast below is the roster; Vex and Grumbal come from the custom pool by name). An inline cast keeps no party memlog, so this file is the party's only record. The brainstorm that ran beside it logged its ideas S001 to S160 in `.memlog.md` in this folder; rounds below cite them.

**Rules of the room.**
- **The operator** speaks only in verbatim quotes, each tagged `(T1:n)`, `(T2:n)` or `(T3:n)`: T1 = `operator/transcript-2026-10-20-to-28.md`, T2 = `operator/transcript-2026-10-29-to-30.md`, T3 = `operator/transcript-2026-10-30-to-31.md`, n = the `grep -n` line holding his whole message. A script checked every quote in this folder against those lines (result in `00-index.md`).
- Nothing here is a decision. Clashes stay open and are marked **Open clash**. The convergence happens in each part file.
- Speaker tags are text, not emoji (project rule).

**The cast.**
- **Rafa**, a cTrader FX and gold scalper, ten years on IC Markets.
- **Dana**, a futures order-flow day trader on CME through a broker.
- **Kenji**, a perps trader on Hyperliquid.
- **Lena**, a forex swing trader who hates being rushed.
- **Priya**, a quant researcher who counts every try.
- **Sam**, an algo developer who shipped on cTrader cAlgo and MT5.
- **Winston**, the BMad architect (pragmatic, trade-offs not verdicts).
- **Mary**, the BMad analyst (patterns, structure).
- **John**, the BMad product manager (relentless "why").
- **Amelia**, the BMad developer (file paths, nothing else).
- **Murat**, the BMad test architect (risk in numbers).
- **Ines**, a site-reliability engineer who has carried a pager for trading desks.
- **Theo**, the QMA v2 harness engineer (hooks, the catalog, workflows).
- **Noor**, a newcomer who was not in the planning.
- **Haiku**, a cheap building agent that turns a video into a unit.
- **Vex**, the security engineer from the pool.
- **Grumbal**, the adversary from the pool.
- **The operator**, quotes only.

---

## P1. QML: what the library is, and what a small mistake looks like

**The operator:** "QML is very important, please." (T3:1264) "a small mistake in there is very costly" (T3:1264)

**Winston:** Then we start from what is there. QML already has the factory seam that QMB and the node both drive, the parameter space, the footprint with its derived warm-up, logic identity, the version graph and the conformance gates. G1 ran 385 tests green on Windows. I don't rebuild a protocol that matches every platform research 04 studied.

**Grumbal:** Lovely. And a third of its public names are refusal functions and old GAP constants. A builder reads `refuse_invented_exits` and treats it as live law. That's your small costly mistake, sitting in `__init__.py`.

**Amelia:** `qml/src/qml/generation/gaps.py`, `research/projection.py:203-255`. Move them out of the public surface. Labels where his rulings now allow placeholders.

**Sam:** On cAlgo, the costly mistakes were never the shape. They were units. Pips on a JPY pair, points on gold, a 5-digit broker against a 4-digit one. One wrong scale and the stop is ten times too wide and the size ten times too big.

**Priya:** And look-ahead through the back door. Everyone guards the price feed. Nobody guards the calibration. If a unit tunes a number from its own journal, the journal it reads in a backtest must stop at the instant.

**The operator:** "because you are building a bloody library, okay? Like React, JS. You can't assume anything here." (T3:904)

**Winston:** So the library's job is to make those mistakes unrepresentable. Typed units of measure that convert only through the instrument record. A journal read surface that obeys `knowable_at` like every other evidence. A pinned block version per unit.

**Mary:** Pattern: every costly mistake in the list is a mistake of meaning, not of code. Unit of measure, time of knowledge, version of a block. The checker exists for meaning.

**Haiku:** Practical question from the cheap seat. When I write a unit, how many things do I touch? If the answer is "190 names", I will guess.

**Theo:** Five verbs, then. `new`, `check`, `compile`, `find`, `explain`. Backtest belongs to QMB, promote to his click, watch to journals.

**Grumbal:** Research 07 said six verbs including `test`, `promote`, `watch`. Now five. Which is it?

**Winston:** QML's door is five. The agent-facing rows add `backtest` (a QMB operation) and `journal_query` (a journals door). "Promote" never becomes a verb an agent can call.

**Open clash:** Sam wants the compiler to generate Python source checked in beside the unit (readable diffs, debuggable in an IDE); Amelia wants a compiled closure with a decision trace per instant (no second artifact to keep in sync). Research 43 §7 low-level item 6 left it open too.

## P2. QML: the checker, and feedback while writing

**The operator:** "the same way you yourself, when you write code, you can receive a linter error or something" (T3:1264) "we have to make sure there are no false positives" (T3:1264)

**Theo:** Three seams already exist and none needs the agent system changed (G4b Q2). A catalog row: one `_row(...)` reaches the copilot by default and every workflow step that declares the toolset. The Library's save of a governed kind: today it returns only the first schema problem, and it can't run QML. And QMX's core plugin, which loads into every chat: a PostToolUse hook there feeds `additionalContext` back after a write.

**Vex:** The shell. Every chat has Python. An agent writes the unit with `python -c` and your Write matcher never fires.

**Theo:** Which is why the Library door is the backstop. A unit only exists once it is saved, and every path saves through the host.

**Murat:** False positives are the risk number here. One false error and the agent learns to ignore the checker, then it's worse than none. So the checker must be tested against a known-good corpus: every example unit, every ported dictionary block. Zero errors or the build fails.

**Grumbal:** And who decides "known-good"? The same people who wrote the checker.

**Murat:** The corpus grows every time an agent's unit passes QMB and his click. A unit he admitted that the checker now refuses is a checker regression by definition.

**Haiku:** What do I actually see?

**Theo:** The `workflows_validate` shape: every problem at once, each with kind, where, message, and a fix hint. Errors and warnings in two lists. Warnings never block.

**Priya:** What goes in errors? Only what can be decided from the document and the catalogue. Schema. A block id that doesn't resolve. A range where min is above max. A block that needs depth on a market whose venue offers none. A banned import. Never "this looks overfit".

**Sam:** And the golden slice of three instants valued one, two, three goes. A unit with a 50-bar warm-up emits nothing on it, so "permitted intent kinds" proves nothing.

**Amelia:** `qml/src/qml/conformance/slice.py:36`, `:104`. Replace with a recorded slice at least the derived horizon plus a margin. And Layer 2 in-process stamps `loaded_in_isolation=True` itself (`layer2.py:321`). Only QMB's sandbox may report isolation.

**Theo:** The plugin hook needs a probe first. Nobody has shown that plugin hooks fire under the Agent SDK in QMX's launch path.

**Open clash:** Theo wants the hook as a Must because it is the feel he described; Murat wants it a Should behind the probe, with the row and the Library door as the Must. Vex wants the scan's deny list widened (importlib, eval, exec) for agent-written blocks; Sam says honest agents never hit it and it only adds noise.

## P3. The dictionary: its new form, and who grows it

**The operator:** "if someone from a source mentions anything, we already know what it is, okay? Or if it's new, we can append it" (T2:788) "239 is very small" (T2:1000) "you tell them to ground themselves first. Don't limit them, okay?" (T3:1264)

**Mary:** Two things share one word. A vocabulary for agents to cite, and a catalogue of blocks that run. Research 43 merged them: "a dictionary entry that runs is a catalogue block".

**Dana:** Then tell me what "volume" means. On CME it's contracts traded. On a cTrader CFD it's a count of price changes. If one entry says "volume", my order-flow unit is reading tick counts and thinks it's reading the tape.

**Mary:** One entry per word, with a per-class meaning table, and every block declares its data level with the three splits from research 45: volume kind, depth grade, the clock of a derivatives field.

**Priya:** And the checker refuses a block needing "exchange volume" on a market whose instrument record says "tick count". Or it runs the declared fallback and labels it.

**Kenji:** Funding, open interest, mark against last. None of that exists in the 239. Perps need their own pack.

**Lena:** And an FX swing trader needs swap and the rollover hour. That's not a strategy word, that's a fact about the market. Keep facts on the market and words in the dictionary.

**Winston:** Three homes per class, as research 43 said: facts on the instrument record, class-only readings in the catalogue, a transfer status per entry per class.

**John:** Who writes the entries? He asked that twice.

**Winston:** STATE's lead answer to ruling 13 stands: builders build the form, a packet ports the 239 and adds families with no cap, and after that growth runs through the same authoring door the copilot uses. One checker for all of them.

**Haiku:** I'm the one adding entries at three in the morning. What stops me inventing a "liquidity sweep" that's really a stop hunt with a new name?

**Mary:** The match script. A source sentence maps to an existing id or "unmatched". Unmatched becomes an append request with a family, a data class and either code or a stated gap. Aliases are checked for clashes.

**Grumbal:** And the status? Who says an entry is "tested"?

**Murat:** A script, from what exists: a spec, code, a golden test, a no-future test, a unit that binds it. Status is computed, never typed.

**Open clash:** Dana wants one entry per meaning for the twelve multi-meaning words (no ambiguity possible); Mary wants one entry with a per-class meaning table (one place for agents to look). Research 45 §8 item 2 left it to the lead.

## P4. The unit: slots, and the two speeds of tuning

**The operator:** "Unit is literally a replacement of a trading bot. It's just a self-configuring trading bot. Simple as that." (T2:788) "how do we make sure that those if-else statements can self-tune?" (T2:788)

**Rafa:** I'll tell you what tunes on a real scalper. The stop is a multiple of the current range, so it widens when the market wakes up. The entry threshold follows where price has been. Those move every bar. Nobody waits for trades to move them.

**Priya:** And then the numbers that only your own record can tell you, like which hours your entries actually work. Those need hundreds of trades. Research 24: a real 0.1R edge passes a 270-trade test half the time.

**Lena:** On a swing unit I get twenty trades a quarter. If my "self-tuning" needs 200 trades, it never tunes.

**Winston:** So every number declares its motion. Source: price, own journal, a reading, or fixed. Cadence: per bar, per session, nightly, after N closed trades. Range. Who may widen the range: only him.

**Priya:** And journal motion shrinks. With five trades, the number barely moves; with five hundred, it can reach its estimate. n over n plus k, a minimum count before the first move, at most one step per update.

**Grumbal:** You've just described an optimiser running live. Every move is a try. Your try ledger explodes.

**Priya:** No. Here's the trick. The motion rule runs inside the backtest too. The replay feeds the calibrator only trades closed before the instant. So what QMB tested is the unit with its self-tuning switched on. The live motion is the same rule doing the same thing. It's not a new search.

**Murat:** That's testable: run the unit twice in QMB, motion on and motion off, and keep both results. The difference is what the tuning is worth, measured honestly.

**The operator:** "A unit, it is self-optimizing, it's relying on very few things" (T3:1145)

**Sam:** What never moves: which blocks, which branches, which exits, the combiner. Those change as a new version, by his click.

**Lena:** Then say so on the card. I want to see which numbers moved, when and why, and nothing else.

**Open clash:** Rafa wants fast numbers allowed to move inside the session; Priya wants even price-driven motion frozen while a position is open, so an open trade's exits never shift under it. Both are honest; it touches exits, so the risk session decides the "open position" rule and the unit file leaves a flag.

## P5. The dummy unit: which strategy, which number

**The operator:** "you are smart enough to conjure up any strategy you want" (T3:1264) "All we want to make sure is that our unit template or our unit thing works." (T3:1264)

**Sam:** Build it only from blocks that already run, so the proof tests the unit and not new indicators. Wrapped today: SMA, EMA, WMA, RSI, MOM, ROC, plus swing points. ATR, VWAP and session range are named but not wrapped.

**Rafa:** Then a trend pullback. EMA 100 for direction, RSI for the pullback, swing low for the stop. Every FX trader knows it, it trades a few times a day on M15, it makes enough trades in two years to move a slow number.

**Priya:** Two speeds, two numbers. Fast: the RSI threshold as a percentile of RSI's own last 500 bars, so it moves every bar from price. Slow: a minimum trend-strength filter, moved nightly from the unit's own closed trades, shrunk, one step at a time.

**Grumbal:** A filter tuned on results is the textbook overfit.

**Priya:** Not if the tuning runs inside walk-forward and the result counts. Then the question "is this motion rule worth it" has a number, motion on against motion off, on months the rule never saw.

**John:** Why not move the stop or the size? That's where self-configuring lives in his head.

**Winston:** Because exits and sizing are the risk session's. The dummy's exits and sizer are placeholders, labelled. It moves a logic number so the mechanism is shown without stepping on that session.

**Rafa:** Markets: EURUSD and gold. Dukascopy history for both, cTrader demo for both, bid and ask so QMB can replay them.

**Noor:** And it ships installed, so my first node start trades something on demo.

**Murat:** And it's QMB's conformance golden and the node's self-test unit. One unit, three jobs.

**Open clash:** Kenji wants a perps dummy beside it (funding as a cost, a 24/7 calendar), to prove the class seams early; Winston wants one dummy until the first slice runs, then a perps twin.

## P6. QMB: core or mini app, variants, and the runner that trades

**The operator:** "So if one day I decide to build a new version of QMB, I should be able to." (T3:1383) "Or improve it, or give multiple variants, because it can be a mini app, for God's sake." (T3:1383) "It runs the same way you run your tests." (T2:135)

**Theo:** The mini-app core already answers most of this. `app_op` runs an app's operation in its supervised process. It takes a `pin = {pack, version}`, so a workflow can name the QMB version it means. An instance has a home machine and the node asks that home through `remote`. On Windows the app runs under a Job object.

**Amelia:** And today `app_op {app: qmb, job: backtest}` fails because no app named `qmb` runs (`qmx_engine/nodes/app_op.py`). Make QMB that app and the route works with no engine change.

**Ines:** PR 204 broke QMB's house rules by spawning a child process and a thread inside `qmb/host`. And its memory limit worked on POSIX only. If QMB runs as a mini app, the runtime gives the process, the Job object's memory limit on Windows, and health logs. QMB itself spawns nothing.

**Grumbal:** And when the breaker trips after three errors, every backtest in the queue dies.

**Ines:** It logs `breaker_open` with the reason, by design. For a research process that's right: a tester that throws three times in a row is broken. He said the limits exist for logging and monitoring.

**The operator:** "So the reason why mini apps are like that is because of the logging and monitoring." (T3:1562)

**Priya:** Variants scare me. A new QMB that "forgets" to count tries, or counts differently, and suddenly everything passes.

**Winston:** So the count lives in the core, not in QMB. PR 204 already proved one landing function, `backtest_and_land`, for the copilot and the workflow. That function is host code. It writes the try ledger, issues the run id, lands the `backtest-result`. A QMB variant only computes.

**Murat:** And before any variant becomes the default tester, it reproduces a conformance pack: the dummy unit, fixed data, fixed seed, the same trade list. A variant that disagrees shows a parity diff, not a silent change.

**Sam:** What it has to compute that it doesn't today: a runner that trades a unit, the typed-partition entry into the trading replay, execution inputs as data, a windowed reader, R beside money.

**Dana:** And it replays quotes only. My futures tape and Kenji's crypto prints don't fit.

**Kenji:** And no funding cost. Every perps backtest comes out too good.

**The operator:** "your whole goal is building something that agents can use, but at the same time at a professional quantitative trader level" (T1:1574)

**Open clash:** Ines wants the copilot to reach QMB through `app:qmb` in the default home preset (no forwarding code); Theo wants the existing `backtest` catalog rows kept as the copilot's door, forwarding to the app (they already exist and land through one function). Both work; the row keeps the copilot's reach without a settings line.

## P7. Judging: the luckiest-market trap and the count of tries

**The operator:** "Agents should judge best of results from performance." (T1:1574) "we don't want to be too strict" (T1:1574) "judging and improvement should come from historical and paper trading" (T1:1574)

**Priya:** Research 24's simulation: twenty markets, a hundred trades each, the best one looked like +0.23R and was really +0.06R. Picking the best-looking market is luck dressed as skill.

**Rafa:** Every desk I sat on did that. "EURJPY loves this setup." Six months later EURJPY didn't love it.

**Priya:** One rule for every market, written into the study before anyone reads a result. Every market that reaches the record is judged the same way. Each one counts as a try. Each result is pulled toward the unit's overall result by how few trades it has. Correlated markets, EURUSD and GBPUSD on one dollar move, count as one.

**Grumbal:** And the agent reruns the study with a different rule until something passes.

**Murat:** The rule lives in the study spec, which lands before the run. Changing it after reading results is itself a counted try. The core issues the run id; the judge refuses any result without one.

**John:** Is this machinery? He hates machinery.

**Winston:** It's one line in the judge and one count in the landing function. No new part.

**Lena:** Paper is my favourite judge. Nobody fits a unit to trades that haven't happened.

**Priya:** And it only counts for the frozen version that took them. Edit after reading a paper result and the paper record restarts.

**Open clash:** Murat wants the shrinkage weight k estimated per unit from the spread between its markets; Grumbal wants a fixed k from the study spec so an agent can't tune k itself. The part file names k as a number with a starting rule and leaves the choice of estimator to the judge's card.

## P8. Journals: depth across markets, brokers, accounts, nodes and worlds

**The operator:** "The journals have one simple row shape. I disagree." (T3:903) "there are times whereby a unit will go back to paper trading. That is known." (T3:903) "this is literally the DevOps layer for that unit" (T1:1574)

**Mary:** The fight is "one shape" against "depth". Both are right at different layers. One envelope that carries every key you'd slice by, and a body whose depth depends on the kind of record.

**Ines:** I'd slice by unit, version, market, account, world, platform, machine, run and trace. Two clocks: venue time and receive time. A flag when the machine's clock was not synchronised.

**Amelia:** CT-13 already has seven event types with an int64 UTC instant, a writer id and a gapless sequence per writer (`packages/qmf-data/src/qmf/data/journal.py`). Its decision event has a closed outcome: authorized, refused-by-door, suppressed. "Suppressed" is the signal seen but not taken.

**Rafa:** I want three things in a journal: the trade, the trade I didn't take and why, and what my numbers were at the time.

**Priya:** And what the market looked like, by reference. The context receipt: reading ids, versions and ages, never copies.

**Lena:** And when my unit goes back to paper on one pair but stays live on another?

**Winston:** World is on every row, and the unit's state machine runs per market. Back to paper is a state change row and then rows with world "paper".

**Ines:** One writer per partition: stream, unit, world, machine, month. A practice twin on his PC and the live copy on the server never write one file.

**Grumbal:** And when his laptop is off for a week?

**Ines:** The node keeps writing locally. When the PC is reachable it ships closed partitions one way, idempotent by writer and sequence. Nothing on the trade path waits for the PC.

**The operator:** "we need to separate the journal for the router" (T1:1574)

**Rafa:** Spread and slippage per broker per minute. Don't copy them into every unit's journal. One market journal, written by whoever holds the feed.

**Open clash:** Ines wants per-bar decision logging on by default for the first month of every unit (debuggability); Murat wants events only by default and per-bar logging switched on per unit for a time box (disk, and the row flood research 43 called out).

## P9. The MIS: defaults for every class, room for his models

**The operator:** "Let's make defaults for the MIS. I'll train the models when I can." (T3:1264) "So the MIS itself is incomplete." (T3:1264) "What I wanted was the MIS just reads and outputs." (T1:1951)

**Mary:** What exists: six execution-health labelers, a quantile liquidity fit, an untrained volatility classifier, all inside the node, reaching "never bots" (G1 §6). What he means by market state is trend against range. Two different things wearing one word.

**Winston:** Then the readings move out of the node into the catalogue, as blocks a unit, QMB and the MIS all run. The MIS becomes a process that runs those blocks across many markets on clocks and publishes what it saw. A unit never needs it to trade.

**Rafa:** For a scalper the MIS is "is now normal?". Spread against usual, tick rate against usual, range against usual, for this minute of the session. That's it.

**The operator:** "you are not going to put an HMM inside a scalper's MIS" (T2:219)

**Priya:** Research 22 sharpened that: the rule is lag against holding time. An HMM belongs on the day tier, a scalper can read the day list.

**Kenji:** Perps need funding state and its extreme tail, open interest change, mark against last. Crypto needs sessions measured from activity, because there is no clock session.

**Dana:** Futures need roll state, days to expiry, the session in Chicago time, price-limit state. And order flow if the data exists, behind its data level.

**Lena:** Gold needs the London fix windows. FX needs currency strength across pairs, which only a shared service can compute.

**Theo:** Where it publishes: four homes already exist (G4b Q6). Derived partitions in the market-data store for the history. Library records for events. A mini app's `provides` contract with `stale_after` for the current board. OpenTelemetry into OpenObserve for its own health.

**Ines:** And the real gap is the link from the node back to the PC. Same as journals. Same one-way shipping.

**John:** And his models?

**Winston:** A "model" kind of reading, trained through the Lab's PC training placement that already exists, run in shadow, live only with his yes. The data and the place exist; the defaults ship now.

**Open clash:** Mary wants "regime" renamed in code to "volatility state" and kept for trend against range, his meaning; Grumbal says renaming shipped code for a word is churn. The word is on his screens, so the lead proposes his meaning and logs it as a call he can undo.

## P10. Instruments, futures, and order-flow data that costs nothing

**The operator:** "I don't want to pay for a platform, I'm not gonna lie." (T3:1264) "They need order flow data." (T3:1264) "I think I'll use CME, man." (T3:1562) "When the app is live, I'll be spoiled for choice" (T3:1562)

**Dana:** Facts first, from research 54. No free real-time CME order flow for an algorithm exists. Sierra locks its data inside its desktop app. Databento is 199 a month for the full book. A futures broker feed is the other road. So for futures, you build the seam now and switch a route on later.

**Kenji:** Crypto is free. Hyperliquid's trades carry the taker side, its book is 20 levels, funding and open interest are on a stream. Binance and Bybit through CCXT. And Hyperliquid's HIP-3 perps trade indices, gold and FX, with real prints on their own book.

**Rafa:** And on cTrader I get ticks and depth. No tape. So any "order flow" there is an estimate from quotes. QMX can compute it itself and say "broker-side estimate" on it.

**Sam:** One internal format for prints and book updates. Every route normalises into it. Units read order flow as readings with a data level and fallbacks: tape, then depth imbalance, then tick rule, then range pressure, each with its expected loss written down.

**Mary:** And a futures account is designed now as facts on the instrument record: multiplier, tick size and value, expiry, roll, sessions in the exchange zone, intraday and overnight margin, price limits.

**Lena:** And the CFD on cTrader has no expiry field at all. It turns close-only by event.

**Winston:** The instrument record is the one table the checker, the MIS defaults and the futures seam read. Data levels per instrument per venue.

**Open clash:** Dana wants a Databento route wired as a dormant adapter in the first build (switch on with a key); Winston wants only the port and the data-level declarations, with no adapter until he pays. The part file keeps the adapter as a Could.

## P11. The trading node: fresh start or refactor, and where it lives

**The operator:** "So a trading node needs a fresh refactor." (T3:1562) "97,000 lines is a big number, bro." (T3:1562) "something that should just be setting itself up on a server, setting up the MIS, and what everything the unit needs to trade autonomously" (T3:1562)

**Ines:** G4a counted 98,063 lines. About 11,900 are proof campaigns and readiness packets that only tests reach. Never traded. Its one host profile is offline replay, so it can't compose a live root even with every value set.

**Sam:** But its organs are good. The cTrader client that records wire evidence before interpreting. Command and event laws with UNKNOWN as a real state. The pacer that keeps room for protection. Reconcile with four verdicts. The kill switch that only escalates on its own. The loop that drives QMB's `run_slice`, so backtest and live share code.

**Winston:** Then: keep the organs, replace the shell. A small node package as the shell; the organs imported as libraries; the old host, seats, promotion, Book paper, doors, deploy recipes, bench and Grafana stack deleted in the same wave once the shell trades on demo.

**The operator:** "Literally, a mini app can have a server of its own." (T3:1562)

**Theo:** And the shell is a mini app. A `money` app: it cannot start without his signature, by code. Its operations are the only door, each with an approval. No operation places an order; orders come only from units inside it.

**Vex:** Where's the live key?

**Ines:** Here's the part I like. QMN's three Linux-only pieces are supervision (systemd), the powers door (a Unix socket with peer credentials) and the secret store (systemd-creds). As a mini app on the QMX host, supervision is the apps supervisor, the powers door is the app's operations with approvals, and secrets go where the host already keeps them: Credential Manager on the PC, an owner-only vault file on a server. All three work on Windows and Linux.

**Vex:** Ruling 135 in code refuses any live-trading grant on every QMX host. You're putting the node inside a QMX host.

**Ines:** On the trading server the host runs a trading profile: no chats, no agent steps, just the supervisor, the node app, the MIS instance, a Library cache and telemetry. The node app stores its own trading grant there, and only on a machine he marked "trading server". On his PC the node app takes demo trading grants and the PC's own view-only live grant. Agents never work where a live key lives.

**Grumbal:** And when the host on the server updates and kills the node mid-trade?

**Ines:** Protection is at the broker before anything can fail. cTrader has no cancel-on-disconnect, so that rule is load-bearing anyway. The host updates on his click only, when the node says it's safe, and the node restarts by reconciling with the broker first.

**The operator:** "It's set for Linux because most VPSs that we're going to be using work with Linux." (T3:1096) "I would prefer using Windows than sorting WSL" (T3:903)

**Lena:** So the same node runs on his Windows PC for practice and on a Linux VPS for live. No WSL.

**Open clash:** Vex wants the node as its own process outside the host on the server (a host crash should never touch trading); Theo wants it inside the host's supervisor (one install, one monitoring path, the cross-machine streams and app_op already work). Ines sits between: inside the supervisor, with the node's own inner supervisor restarting its trading loop, and the host as a systemd service that always restarts.

## P12. The trading node: self-healing, the kill switch, and a newcomer starting one

**The operator:** "a trading node should be as simple as how, for example, I can set up a server from a provider" (T2:1148) "is it going to start as server, then show me that the server has started?" (T3:1102) "So that when we click a kill switch, it can automatically work." (T3:1562)

**Noor:** I open QMX for the first time. What do I click?

**Theo:** The connect dialog already has a step runner: his cards first, then checked steps that are safe to rerun, one row written last (PR 232). It has kinds for storage, compute and deep logs. Add "trading node". First card: "Start a trading node on This PC (practice)".

**Noor:** And then?

**Ines:** It installs the node app, asks for a cTrader demo sign-in in your browser, checks the clock, runs a self-test (broker connection, a demo test trade with a stop, kill-switch latency, feed freshness, disk, clock skew), and lands a passport. Your screen shows one word: running.

**Rafa:** Start the cTrader app registration on the first card. Spotware approves each app, about a day by the reports.

**Noor:** Then I want a server.

**Ines:** Same dialog, "Trading server": pick a provider, paste the address and a one-off Tailscale key, type the server password into the terminal QMX opens. The shipped firewall with its five-minute undo and `qmx-recover` come along. The node app installs, signs in to the live account there, and runs the same self-test.

**Grumbal:** Self-healing. You keep saying it. What heals what?

**Ines:** Desired state lives in the node's volume: which units, which markets, which mode. The node converges to it on start: reconcile with the broker, rebuild positions, restore calibration, re-place any missing protection, resume feeds, then trade. Health checks each minute. The inner supervisor restarts the trading loop with back-off; after too many restarts it stands down alive: heartbeat on, no new entries, protection at the broker. An off-server watcher alerts on a missing heartbeat.

**Vex:** The kill switch.

**Sam:** The kill switch has five levels and only escalates on its own. Automatic kills are risk rules inside the node; nothing needs the PC. His kill is a node operation he clicks from any QMX screen that reaches the server. If nothing reaches it, the broker's own app closes positions; that fallback is written on the node's page.

**The operator:** "nothing actually ever enters live without me" (T1:1574)

**John:** Deploying a unit, then?

**Theo:** One button on the unit page: markets, account, practice or live. Live needs his signature. The node pulls the unit version, its calibrated values and the instrument records it uses into its volume, so it never needs the Library to trade.

**Open clash:** Ines wants a week's soak before any live binding, as the old node design had; Lena says a week of demo proves the plumbing only and research 43 put the PC soak at 24 hours. Both numbers are kept, named, and editable.

## P13. External connections: cTrader first, CCXT opened, Hyperliquid designed

**The operator:** "CCTX only reads crypto spot. Change that. Open it up. Hyperliquid, look it up." (T3:1562) "Is it going to place and execute trades via an API?" (T3:1096)

**Sam:** Yes, through APIs. cTrader's Open API is protobuf over TLS. QMX ships Spotware's descriptor and its own transport; no Spotware SDK. Orders already exist in the node's client and have never run.

**Kenji:** CCXT 4.5.85, the version QMX pins, already has Hyperliquid with orders, positions, funding, open interest, the order book, leverage and the testnet (G4a §2.6). QMX's wrapper refuses every contract market. That filter is the whole fix for reads.

**Vex:** Orders through CCXT on the PC?

**Sam:** Never. The PC host has no order code by design. Orders through CCXT run only inside the node, as a `ccxt` venue client behind the same port as cTrader: capability declaration, the five command kinds, events, reconcile.

**Kenji:** Hyperliquid specifics you can't miss. Its trading key is an agent wallet: it trades, it can't withdraw, it expires within 180 days. Nonces must sit inside a time window around block time, so a drifting clock breaks trading. Its dead man's switch cancels all open orders, stops included, so never rely on it. TP and SL trigger on mark price. Actions are rationed per address. Above 1,000 open orders, new reduce-only and trigger orders are rejected.

**Rafa:** And cTrader has no dead man's switch at all. A dead node leaves only the stops at the broker.

**Winston:** So "protection at the broker before anything can fail" is a port rule, per venue: cTrader places it with the order; Hyperliquid places a trigger order and re-places it after any cancel.

**The operator:** "Hyperliquid can't ban me from to be trading. I already have accounts there." (T3:903)

**Dana:** And futures get a venue-client placeholder: Rithmic's R|Protocol is websockets plus protobuf, any language; CQG's WebAPI is protobuf over websocket. Both need a funded account and a conformance test. Design the slot; build nothing until he picks.

**Open clash:** Kenji wants a native Hyperliquid client (agent wallets and trigger orders handled exactly); Sam wants CCXT's class first (already pinned, one client for every exchange) and a native client only if CCXT falls short in a test. The part file picks CCXT first with a probe.

## P14. Contracts and APIs, internal and external

**The operator:** "more like a male and female connector" (T2:135) "Live trading, which I think might have been catered for a bit, not fully, but a bit." (T3:1264)

**Mary:** Count the new shapes. The unit document. The check result. QMB's operations. The node's operations. The journal envelope and its kinds. The reading card. The instrument record. Seven. Everything else exists.

**Winston:** And they all follow rules that already exist: JSON Schema 2020-12, a `schema_version`, addable and never redefined. Mini-app operations carry input and output schemas in the manifest.

**Theo:** API versioning is the gap G2 found. Routes carry no version. The rule: a breaking change is a new schema version plus an upgrade script, the same as store versions.

**Sam:** External: one venue-client port that already exists in shape (CT-18 declaration with a measured profile, CT-19 commands, CT-20 events, reconcile). One data-route port, new, with data-level declarations.

**Vex:** And the risk socket?

**Winston:** A connector shape with placeholders: an exit-set slot, a sizer slot, halts at three scopes, and a list of readable inputs. Its content is the risk session's.

**Grumbal:** You said "fewer contracts". This sounds like a contracts zoo.

**Mary:** Seven shapes, each replacing Python a fixture builds by hand today. That's fewer than what exists.

**Open clash:** none left open in this round.

## P15. The copilot, the agents and the workflows in the slow lane

**The operator:** "anything that an agent under QMA can do, the copilot should already be able to do" (T3:1264) "Be surgical." (T3:1562) "They should be using the logs from the MIS." (T3:903)

**Theo:** One catalog feeds every door; the copilot's default surface is every core toolset. New unit rows land in a core toolset and the copilot has them with no change. A short parity test pins it.

**John:** What changes in the agent system, line by line?

**Theo:** Rows: `unit_check`, `unit_new`, `unit_explain`, `blocks_find`, `journal_query`, `readings_query`, `instrument_get`. A filled `build-unit` skill and a filled `build-mini-app` skill. The `backtest` rows bound to the QMB app. A hook file in the core plugin after a probe. A Library kind validator that returns every problem. Nothing else.

**Mary:** The slow lane he named: unit review, market review into an almanac, a shortlist before each session, tagging units to markets, a check on the MIS, daily data review, and a watcher over trading nodes.

**Priya:** Every one of them scored by something that isn't an agent. Market calls are dated and scored later by a script. Every number an agent states matches a tool call the engine logged.

**Haiku:** And the fast lane?

**Theo:** No agents. The unit, its readings, the kill switches.

**Open clash:** Haiku wants workflow agent steps to write files like the copilot (the dropped AGW design); Theo says units don't need it, since an agent step returns the unit as JSON and a script saves it. Kept as an option behind the undo phrase in the build store.

## P16. DevOps and clocks

**The operator:** "the trading node is perhaps a firm" (T3:903) "We are literally trading 24/7, my days. This is why we need a trading node." (T2:325)

**Ines:** One monitoring stack. OpenObserve, self-hosted, agents read-only, one telemetry switch, already built and pinned for Windows. QMN's Grafana, Loki and Prometheus go.

**Dana:** Clocks. Every stamp in UTC. Every market event with venue time and receive time. cTrader has no server clock, so the receiving machine's clock is the measurement.

**Ines:** And his Windows Time service is stopped today. The doctor checks it and offers to start it. Linux servers run chrony with several sources and no smeared ones.

**Lena:** Sessions in the market's zone. London open is a London rule. The node's own time zone never enters a rule. A node in Singapore and one in London compute the same session from the same instant.

**Kenji:** And the screen shows each node in the zone I choose, with its clock band. A node whose clock is off is marked, not merged.

**Mary:** His "firm" (T3:903) picture fits the display, not the rules: a node shows its office time, but trades on the market's time.

**Open clash:** none.

## P17. Mini apps: the white-label core

**The operator:** "it's like handing someone white label software" (T3:1338) "Most things can actually become mini apps." (T3:1383) "Mini apps came in because of the same pattern." (T3:1264)

**John:** Shopify has a small core (products, orders, checkout) and everything else is an app with stable doors. What's QMX's core?

**Winston:** QML, the dictionary and its catalogue, the unit template and its checker, the judge and the try ledger, the journal records, the instrument record. Everything that would cause silent wrong answers if two versions disagreed.

**Theo:** And the apps: QMB, the trading node, the MIS. Things that run, that he may want two of, that live on a machine.

**Grumbal:** And the unit? You keep dodging.

**Winston:** A unit is never an app. Units are Library items. Two apps run them: QMB on history, the node on practice and live. That's what keeps "only the node sends orders" true.

**The operator:** "Maybe you can have a version or a template of a mini app using what is already there." (T3:1562)

**Theo:** Then QMB's app is that template: a filled `build-mini-app` skill uses it as the worked example.

**Noor:** And for me, out of the box: QMB, the node and the MIS installed and enabled with defaults, the dummy unit in my Library.

**Open clash:** Mary wants the MIS as a third mini app from day one; John wants the MIS readings as catalogue code only, with the publishing process added later, since no unit needs it to trade. The part file weighs both.

## P18. Close: what the room still disagrees on

**Winston:** We agree on more than we fight about. The unit as a declaration plus code blocks. Motion declared per number and tested inside the replay. The checker through three seams. Tries counted in the core. QMB and the node as mini apps. Journals as one envelope with deep kinds.

**Grumbal:** And on all of it, nothing has run. The first slice decides.

**The operator:** "Design for complexity, not a complex system." (T3:1264)

**Mary:** The open clashes, for the convergence:
1. Compiler output: closure with a trace, or generated source (P1).
2. The plugin hook: Must or Should behind a probe (P2).
3. Scan deny list widened for agent blocks (P2).
4. Twelve multi-meaning words: one entry per meaning, or one entry with a per-class table (P3).
5. Fast motion while a position is open (P4, flagged to the risk session).
6. A perps dummy in the first slice (P5).
7. Copilot's door to QMB: rows that forward, or `app:qmb` in the preset (P6).
8. The shrinkage weight k: estimated or fixed per study (P7).
9. Per-bar decision logging by default (P8).
10. The regime word in code (P9).
11. A dormant Databento adapter (P10).
12. The node inside the host's supervisor or beside it (P11).
13. Soak length before live (P12).
14. Native Hyperliquid client or CCXT first (P13).
15. Agent steps writing files (P15).
16. The MIS as a mini app from day one (P17).

**Noor:** And I still want to see the word "running" in the first hour.

*(Natural close. The convergence runs in each part file; the lead's picks are logged in `00-index.md` under "Lead's calls".)*
