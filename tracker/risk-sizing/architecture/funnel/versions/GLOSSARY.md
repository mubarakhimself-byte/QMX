# QMX unit system: glossary

The words the unit-system architecture uses, one meaning each, fixed once before Level 0 (skill `domain-modeling`, glossary format). Every Level 1 file and every build packet uses these words. Where his own words differ, his win on his screens; the lead's choices that he may rename are marked "working word". It holds no design.

## Units and how they are written

**Unit**:
One complete trading algorithm: its entries, exits, its own sizing, its condition needs, its session profile and its journal, tested as one. It replaces the trading bot.
_Avoid_: bot (fine in chat, not in QMX's words), strategy (that is an idea before it is a unit), system 1, system 2

**Unit document**:
The written form of a unit: its named slots, the blocks that fill them, its numbers and its markets, stored as one Library item.
_Avoid_: spec, JSON unit, declaration (the older bot word)

**Unit template**:
A unit document with defaults that a new unit starts from; the dummy unit is the first.
_Avoid_: preset, skeleton

**Slot**:
A named place in a unit document that one or more blocks fill: context, trigger, confirmation, entry order, exit set, sizer, halts, and roles such as veto or timeout.
_Avoid_: pillar (the old checklist view), port (that word is for connections)

**Block**:
A piece of tested code from the catalogue that fills a slot.
_Avoid_: component (the Library kind's name, not the trader's word), module

**Catalogue**:
Every block QMX can run, with its version and tests.
_Avoid_: parts bin, registry

**Dictionary entry**:
One page of trader vocabulary: what a trader means by a word, what data it needs, and whether it has working code yet. An entry with working code is also a catalogue block.
_Avoid_: STRATS entry, primitive

**Plain-Python unit**:
A unit whose logic is ordinary Python beside QML, with the same journal, lineage and tries as any other unit.
_Avoid_: ungoverned bot, tunnel

## Numbers and how they move

**Fixed number**:
A number that changes only when he approves a new version.
_Avoid_: constant, hyperparameter

**Calibrated number**:
A number that follows the unit's own record, slowly, inside a range he approved, by a rule written down in advance.
_Avoid_: self-tuned setting, adaptive parameter

**Derived value**:
A number the unit's logic works out every bar from the market, such as a stop measured in multiples of recent range.
_Avoid_: dynamic parameter

**Motion**:
How a number may move: never, with the market, with its own record, with a reading, or as a learned value.
_Avoid_: tuning mode

**Calibration row**:
The journal's record of one move of a calibrated number: old value, new value, the rule and the trades it read.
_Avoid_: tuning log

**Placeholder**:
A block that stands in for exits, sizing or halts until the risk and sizing session replaces it, labelled so on the unit's card and every trade.
_Avoid_: stub, dummy block, default sizing

## Markets and facts

**Market**:
One instrument at one venue, such as EURUSD at IC Markets on cTrader.
_Avoid_: pair (only for currencies), symbol (the venue's code), terrain

**Instrument record**:
The one page of facts about a market: what a point is worth, the smallest size, hours in the market's own zone, carry, expiry and roll, margin, the data it offers.
_Avoid_: symbol info, contract spec

**Account record**:
The facts about one trading account: broker, demo or live, netting or hedging.
_Avoid_: connection (that is the login)

**Data level**:
How rich a market's data is, from calendar only, through bars, quote ticks and depth, to a tape with the aggressor side and derivatives fields.
_Avoid_: data tier, feed quality

**Session**:
A window of trading time defined in the market's own zone, such as the London open.
_Avoid_: timeframe (a bar size is a bar spec), hours

**Bar spec**:
The size of a bar a unit reads, such as 15 minutes.
_Avoid_: timeframe (bare)

**Market settings** (working word):
A unit's own values for one market, earned from its record there and pulled toward its values on all its markets.
_Avoid_: specialist, sibling settings

**Market version** (working word):
A unit whose logic was changed for one market, earned from the record there; a new unit in the same family.
_Avoid_: system 2, specialist unit

## Reading the market

**The MIS**:
QMX's market reader: it reads every market and writes down what it saw, with the time it saw it. No unit needs it to trade.
_Avoid_: router, regime engine

**Reading**:
One measure of market state or execution health, such as volatility against usual or the spread against usual, with its time, version and freshness.
_Avoid_: signal (that is a unit's), label, sensor (the code behind it)

**Board**:
The MIS's latest readings across markets, used only to point a unit at the markets he admitted.
_Avoid_: routing table, offers

**Regime**:
Whether a market is trending or ranging, in his meaning.
_Avoid_: regime for volatility (that is volatility state)

**Volatility state**:
How quiet or stressed a market is now against its usual: quiet, normal, elevated, stressed.
_Avoid_: regime

## Judging

**Try**:
One test anyone ran of a unit, a variant or a market, counted by QMX whoever ran it.
_Avoid_: trial (QMB's code word), attempt

**Study spec**:
The rules of a test written down before any result is read: markets, windows, the record needed, his holdout choice.
_Avoid_: test plan, config

**Verdict**:
The judge's answer on a unit's results, made by scripts and explained by an agent.
_Avoid_: score, grade

**Baseline card**:
The frozen record of how a unit tested, which later live results are compared against.
_Avoid_: exam baseline (QMB's code may not use "exam")

**R**:
A trade's result measured in multiples of what it risked at entry.
_Avoid_: risk unit

## Records

**Unit journal**:
Everything a unit did and decided, in every world: trades, signals taken and skipped with the reason, number moves, state changes, guard verdicts.
_Avoid_: logbook, trade log

**Market journal**:
Costs and conditions per market, broker, account type and minute: spread, fees, slippage, gaps.
_Avoid_: router journal (his older word for it)

**Node journal**:
What a trading node did: starts, stops, self-tests, reconcile results, kill-switch levels, clock bands.
_Avoid_: node log

**Reading history**:
Every reading as it was published, never rewritten.
_Avoid_: MIS log (the same thing, said loosely), MIS output

**Notes**:
What agents write: analysis and proposals, each linked to the rows it explains.
_Avoid_: agent journal

**World**:
Where a record came from: backtest, stress, paper, demo, live, shadow or synthetic.
_Avoid_: mode, environment

**Signal row**:
One decision a unit made on one instant: taken, skipped with its reason, or blocked by a guard.
_Avoid_: missed trade (that is computed afterwards by replay)

## Life of a unit

**Lifecycle state**:
Where a unit stands on one market: draft, tested, parked, paper, live, stopped or retired.
_Avoid_: stage, status

**His click**:
The only way a unit or a market moves toward live; nothing else promotes.
_Avoid_: approval gate, sign-off flow

**Risk stop**:
A unit stopped by its own risk rule, the one automatic move; it waits for his resume.
_Avoid_: kill (that is the kill switch), halt (a slot name)

**Health stop**:
A process stopped for a technical fault; healing may restart it by itself.
_Avoid_: breaker trip (the code word)

**Deployment**:
A unit version installed on a trading node for chosen markets, an account and practice or live.
_Avoid_: seat, admission

## Machines

**This PC**:
His own computer, where everything runs first.
_Avoid_: workstation, local box

**Server**:
A rented machine that stands in for or extends This PC.
_Avoid_: trading server (as a kind), VPS (fine in chat), QMX node

**Trading node**:
The QMX app that sends orders. It runs on This PC for practice and on a server for live.
_Avoid_: node setup (today's code uses that for a QMX server), QMN (the code package)

**Trading profile**:
How a server runs once he binds a live account to its trading node: no chats and no agent steps there.
_Avoid_: trading server kind

**Practice**:
Trading demo accounts only.
_Avoid_: rehearsal, paper (paper is a lifecycle state)

**Feed keeper**:
The one live market connection per venue on a machine, shared by every unit and reader there.
_Avoid_: data pump, subscriber

**Kill switch**:
The node's five levels of stopping, raised by risk rules on their own, lowered only by him.
_Avoid_: emergency stop button

**Heal**:
The node putting itself back to what he asked for after a technical fault.
_Avoid_: auto-recovery

**Office time**:
A node's local time, shown on screens beside his own zone; never used by a rule.
_Avoid_: node time (in rules)

## Software

**Core**:
The parts that must always agree with themselves, of which QMX keeps exactly one copy.
_Avoid_: kernel (used only in the architecture's paradigm name), platform

**Mini app**:
A program on QMX's app core that can be replaced, improved or run as several versions: QMB, the trading node, the MIS.
_Avoid_: plugin, pack (a related but different word)

**QMB version** and **QMB variant**:
A build of the backtester; several may be installed side by side, and one is the default.
_Avoid_: engine (QMB's code may not use it)

**Agent** and **the copilot**:
A model working through QMX's tools; the copilot is the one he talks to. Neither ever trades.
_Avoid_: bot (that word is retired for units)
