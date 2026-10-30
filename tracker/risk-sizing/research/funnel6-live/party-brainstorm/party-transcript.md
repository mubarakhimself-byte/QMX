# Party mode: the live side (node, live markets, data, journals)

Run 2026-10-30. `bmad-party-mode`, session mode, explicit `--non-interactive` run on one intent, clashes left open. Inline cast, so no party memory (party-memory.md: "ad-hoc inline casts have none"). No human in the room. The operator speaks only through quotes, each script-checked against `operator/*.md` (checker: 30 of 30 found).

**Intent.** Expand the field for the live side of the unit system: the trading node, live market access and outside connections, the data units and agents read, and the journals. Ideas, options and questions. No design. Ruling 135 against "first run on my machine" stays open.

**Labels inside speech.** `[C: source]` = checked this run at that source. `[I]` = inferred or from memory, needs research. Sources: `R42` = `research/42-grounding-shipped-code.md`, `R12` = `research/12-data-feeds-lookback.md`, `R14` = `research/14-design-idea-studies.md`, `R21` = `research/21-old-system-loose-ends.md`, `R02` = `research/02-instruments-and-traders.md`, `R135` = `tracker/qma-v2/research/methodology/26-operator-rulings-and-alignment.md:250-257`, `SEEDS` = `seeds.md:107-117`.

## The room

| Icon | Name | Who |
| --- | --- | --- |
| 🖥️ | **Kofi** | Runs trading servers for a living. Talks in uptime, regions and reboots. Hates snowflake servers. |
| 🔌 | **Ines** | Broker-API integrator. cTrader Open API and MT5 scars. Pedantic about tokens and hosts. |
| 📈 | **Walt** | Futures day trader on Rithmic, used CQG before. Reads DOM and tape. Thinks CFDs are toys. |
| 🌊 | **Mei** | Hyperliquid perps trader. 24/7, funding, API wallets. Talks fast. |
| 📡 | **Dara** | Market-data vendor person, Databento and Tardis style. Licences, schemas, fees. |
| 🔭 | **Priya** | Observability engineer. Journals are telemetry to her. Loves one event shape. |
| 🤖 | **Ana** | A QMX analyst agent that reads journals. Wants handles, ids and small tables. |
| 🏗️ | **Hollis** | Designer of the shipped QMX host. Speaks only from what research 42 found in code. |
| 🔐 | **Sable** | Wrote ruling 135. Thinks about agent shells and keys. Not a money-gate person. |
| 🙋 | **Sam** | Non-technical. Must set this up himself, alone, at night. |
| 🪓 | **Grit** | Skeptic of extra servers. "Buy a UPS." |
| 🎙️ | **The operator** | Quotes only. |

---

## Round 1. Why a node at all

🎙️ **The operator:** "The only reason we're having a trading node is obvious." ... "power goes on, comes back off, Wi-Fi drops when power goes off" ... "We are literally trading 24/7, my days. This is why we need a trading node."

🪓 **Grit:** So the problem is electricity and a router. That's a UPS and a 4G failover box. Forty quid of hardware against a second machine, a second OS, a second key store and a second set of failures.

🖥️ **Kofi:** A UPS buys you minutes. Your ISP's cabinet down the road has no UPS. And "laptop off" isn't a failure, it's Tuesday. He *wants* to close the lid.

🪓 **Grit:** Then the node exists for one state: lid closed. Design for that state, not for a data centre.

🙋 **Sam:** I like that. "When my laptop is closed, these keep trading." That's a sentence I understand.

🏗️ **Hollis:** For the record, what's built. The connect dialog has kinds for storage, compute and deep logs. No kind for a trading server [C: R42 §2.1, `connect.py:389`]. The server it builds is the same QMX host in a `server` role: a worker and a Library store, not a trading server [C: R42 §2.2 table]. QMN is separate, never deployed, Linux and systemd only [C: R42 §3].

🖥️ **Kofi:** Linux-only is fine for a server. It's a problem for "first run on my machine" if the PC is Windows.

🎙️ **The operator:** "if something is to run on external compute and external storage, it should first run on my machine. This cost us 2 days of re-auditing and coding"

🪓 **Grit:** There it is. The node code can't run on his machine today. So rule one already fails before we've written a line.

🔌 **Ines:** Unless "his machine" includes a Linux inside it. WSL2, a VM, Docker [I].

🪓 **Grit:** "Runs in a VM on my PC" is a lawyer's reading of his rule.

🖥️ **Kofi:** It's how every ops shop tests. Same image on the laptop and the box.

*(Grit and Kofi stop talking to each other for a round.)*

## Round 2. The 135 knot

🔐 **Sable:** I'll say why 135 exists. An agent on his PC has a shell. Anything stored there is readable by an agent. A key that can trade live money doesn't belong where a shell can read it [C: R135]. No money gate. Just where the key lives.

🎙️ **The operator:** "before we even buy a trading node and a server"

🔐 **Sable:** And his rule says the node's stack must run on his PC first. Those two only collide if "run" means "run with the live key".

🙋 **Sam:** Does it?

🔐 **Sable:** That's the question. The lead's candidate: the whole stack on the PC against demo, the live key only on the server [C: STATE.md:154]. I named the tension myself in the ruling [C: R135, "The tension with ruling 117"].

🔌 **Ines:** Careful. On cTrader, demo and live go to different hosts and the grant says which accounts it covers [I: hosts from memory; grant scope C: R135]. So "demo on the PC" exercises the code, not the live path. The first live order is still a first.

🪓 **Grit:** So the two-day lesson repeats on the live host.

🔐 **Sable:** Smaller, though. Only the key and the host change.

🌊 **Mei:** On Hyperliquid you'd make an API wallet. It can trade, it can't withdraw [I]. Is that "a key that can trade live money"?

🔐 **Sable:** Yes. Trading is the harm. An agent that places a hundred trades does damage without withdrawing a cent.

🌊 **Mei:** Then you're saying the PC can never trade live. Ever.

🔐 **Sable:** Today. He can overrule it. I wrote the paragraph telling him where.

🤖 **Ana:** I'm an agent. I'd like to point out I never need a live key. I need journals.

📈 **Walt:** Split the thing. A brain that decides and an arm that sends orders. The arm holds the key. The brain can live anywhere.

🔐 **Sable:** ...that's interesting. Then the PC runs the brain against live prices and the arm is a tiny process on the server.

🪓 **Grit:** And now a trade depends on two machines and the link between them. You just broke "units stand alone".

📈 **Walt:** Not if the brain also runs on the server and the PC copy is a shadow.

*(Left open. Five shapes are on the table by the end of the round; they go to the options section.)*

## Round 3. Setting it up

🎙️ **The operator:** "a trading node should be as simple as how, for example, I can set up a server from a provider" ... "Either we can use a wizard or we can just set it up when I click with a click of a button." ... "But who's providing us with our trading servers?"

🙋 **Sam:** One button. I'll pay a provider. I will not type commands.

🏗️ **Hollis:** Today's server path: his cards first (choose and pay, the address, a one-off Tailscale key, the server password in a terminal QMX opens, approve the firewall), then QMX's checked steps, rerun-safe, one place row written last, then a smoke run [C: R42 §2.2]. The shape fits. QMN's paths, credential sealing and observability stack don't match the host's [C: R42 §3].

🖥️ **Kofi:** Two ways to get to one button. One: he gives QMX a provider API token, QMX creates the server itself. Two: QMX gives him a cloud-init text to paste into the provider's "user data" box, and the server builds itself and calls home [I].

🔐 **Sable:** A provider token can create servers and bill him. It's not broker money, but it's money. Short-lived, deleted after setup.

🙋 **Sam:** The paste one scares me less. I paste, I wait, it shows up.

🔌 **Ines:** Whatever you pick, he still registers a cTrader app for each trading server, and Spotware approves it with no timeline [C: R135; R42 §3]. That's not a button. That's a wait.

🙋 **Sam:** How long?

🔌 **Ines:** Nobody publishes it [C: R135].

🖥️ **Kofi:** Then start the app request on day one of the wizard, before he even rents the server.

🏗️ **Hollis:** And the self-test he asked for: kill-switch speed, test trades, broker connections [C: SEEDS]. The smoke run is the slot for it.

🪓 **Grit:** Self-test with a test trade on a live account?

🖥️ **Kofi:** Demo account on the same server. Live gets a read, not a trade.

🎙️ **The operator:** "For now, we might have one for starters, but as we grow, okay, we might have more than one."

🖥️ **Kofi:** Then the second node is "clone this node, other provider". No new wizard.

## Round 4. Failure

🖥️ **Kofi:** Name the failures and their owners. Node reboots. Provider has an outage. Broker weekend maintenance. Token refresh logs another machine out. Disk full. Clock drift.

🔌 **Ines:** The token one is real. A cTrader refresh invalidates the old token's accounts [C: R12 §4.1]. One home per sign-in is already the rule [C: R135].

📈 **Walt:** Every order goes out with its stop at the broker. Then a dead node is an annoyance, not a catastrophe.

🌊 **Mei:** On Hyperliquid there's a scheduled-cancel, a dead man's switch: stop heartbeating and resting orders cancel [I]. Ask whether cTrader has anything like it.

🔭 **Priya:** And who notices? The node can't report its own death. Something outside has to watch the heartbeat. The PC, when it's on. A free outside pinger when it isn't [I].

🙋 **Sam:** I want my phone to buzz once. Not forty times.

🔭 **Priya:** One alert per incident, with a word: unreachable, paused, needs you.

🖥️ **Kofi:** After a crash, the broker's positions win. The node re-reads them, reconciles the unit journals, flags orphans [C: question L14-08 in funnel3].

🪓 **Grit:** And if the node dies for a day, does the PC take over?

🔐 **Sable:** Not with 135 as written. The PC has no live key.

🪓 **Grit:** So the stand-in rule, "servers stand in, never replace", runs backwards here. The server is the only one allowed to trade, and nothing stands in for it.

*(Sable doesn't answer. Hollis writes it on the board: "who stands in for the trading server?")*

## Round 5. Live feeds

🎙️ **The operator:** "live markets, in other words, not just market data, live markets" ... "How am I trading futures? Can I trade futures on CTrader? With order flow and stuff?"

📈 **Walt:** Real futures order flow means exchange data: depth and time-and-sales. Rithmic or CQG through a futures broker, or Interactive Brokers, or Tradovate [I]. CQG depth for CME is a few dollars to forty-odd a month for non-pros [C: R02 §7.2].

🔌 **Ines:** cTrader gives quotes and depth, no public trade tape [C: R21 §3]. Depth quotes carry size, so displayed liquidity yes, executed volume no [C: R21 §3].

📈 **Walt:** So on cTrader you can't see a single real print. Footprint, delta, absorption: gone.

🔌 **Ines:** Best-quote imbalance still works on depth [C: R02 short answer 5].

📡 **Dara:** Data and execution are two different shopping trips. Databento for CME history and live; Tardis for crypto history including Hyperliquid since Oct 2024 [C: R12 §0 point 7]. And watch licences: exchanges often charge more for "non-display" use, which is what an algorithm is [I].

🌊 **Mei:** Hyperliquid's public websocket gives trades, book, funding, open interest, no key needed [C: R12 §4.1]. But the API only keeps about three and a half days of 1-minute candles [C: R02], so if you don't record, you don't have history.

🎙️ **The operator:** "for raw data, we are going to first see, because this 44 minute thing is huge."

🤖 **Ana:** Context: research 05 said a 50% volatility jump takes about 44 minutes to spot from 1-minute closes [C: `transcript-2026-10-29-to-30.md`, lead's message]. Ticks spot it faster.

📡 **Dara:** So the MIS wants ticks, the backtester wants bars, and the disk wants mercy. 150 to 300 MB per FX instrument-year of ticks [C: R12 §5.2].

🙋 **Sam:** I have 12 GB free.

📡 **Dara:** Then record on the server, cache on the PC.

🪓 **Grit:** Which is a server holding the main copy. You just undid the local-first ruling for data.

📡 **Dara:** Rulings say servers extend. A tick archive is the textbook extension.

## Round 6. Data route, execution route

📡 **Dara:** Every connection has two possible jobs: data and execution. Same company, different job.

📈 **Walt:** And a unit could read one and trade the other. Read ES futures tape, trade the US500 CFD on cTrader.

🔌 **Ines:** Different sessions, different prices, a basis that moves. The CFD follows the future, roughly.

📈 **Walt:** Roughly is my whole career.

🤖 **Ana:** If you do that, the journal must say so on every trade: signal venue, execution venue. Otherwise I'll judge the unit on a market it never traded.

🎙️ **The operator:** "is it the broker? Is it the time?"

📡 **Dara:** The market journal answers both if it's keyed by broker, account type, instrument and minute [C: R12 §5.1].

🌊 **Mei:** Add funding and open interest for perps in the same rows. Hourly funding is a cost [C: R02].

🏗️ **Hollis:** CCXT today is spot only; it refuses contract markets [C: R02 short answer 6]. Hyperliquid has zero code [C: R42 §4].

📈 **Walt:** So the futures and perps half of "expanded the domain" is a blank page.

🎙️ **The operator:** "I'm starting with Ctrader. We are going to use Open API." ... "I might also start with Hyperliquid, with perpetual features." ... "I'm not certain on what I'm going to trade fully yet"

🪓 **Grit:** Two venues, one undecided. Build the shape for many, wire two.

## Round 7. Journals, the schema fight

🎙️ **The operator:** "it's anything that can record data" ... "this is literally the DevOps layer for that unit" ... "I would prefer most simple data schemas."

🔭 **Priya:** Then one event shape for everything. Id, time, stream, subject, kind, world, links, body. Traces for trades, spans for each step.

🤖 **Ana:** Please don't make me read OpenTelemetry. I want a table I can filter by unit and month.

🏗️ **Hollis:** What exists: a `trade` kind with `world` (backtest to live) and `initial_risk`, journals per account, tags and notes that never make a new version [C: R42 §6.1]. No unit journal, no router journal, no catalog row that lets an agent read a journal [C: R42 §6.1].

🔭 **Priya:** The node already ships Grafana, Loki, Prometheus. And QMX moved to OpenObserve [C: R42 §3].

🪓 **Grit:** Two observability stacks and no journal. Classic.

🔭 **Priya:** Store of record in Parquet. Dashboards read from the same writer. One fact, one place.

🎙️ **The operator:** "we need to look at the amount of data we are collecting"

🤖 **Ana:** Events only by default. Every bar on request. Missed trades computed afterwards by replay, never written live [C: R14 §5.1-5.2].

📈 **Walt:** "Seen but not taken" needs a reason I can count. Spread too wide. Guard said no. Already in a trade. Session closed. Not "other".

🎙️ **The operator:** "I think the router should give us the journal for that"

🔭 **Priya:** He means market facts. Spread, fees, sessions. The feed keeper writes them, not a router, so they survive with the router down [C: R12 §5.1; R14 §5.2].

🤖 **Ana:** Fine by me, as long as the trade row carries the key into it.

## Round 8. What agents read

🎙️ **The operator:** "this is what the agents will be looking at"

🤖 **Ana:** My wish list. A journal door with handles, like the price door. A preview card before rows. A "trades with context" table already joined. An event when an alarm row lands so a workflow wakes [C: R42 §1.2 for event triggers].

🔐 **Sable:** No account numbers in what agents read. Account id mapped to a label.

🤖 **Ana:** I'll take labels.

🔭 **Priya:** And when you claim something, cite the row ids. A script recomputes it. That's your proof.

🤖 **Ana:** That's what I'd want anyway. My claims are cheap. Rows aren't.

🙋 **Sam:** Can the agent tell me "why didn't my unit trade gold today?"

🤖 **Ana:** From the seen-not-taken rows, yes. Ten words and a link.

🪓 **Grit:** Small models will drown in journals.

🤖 **Ana:** Then a script writes a one-page digest first. The model reads the digest and opens rows only when needed.

## Round 9. The UI, judged by design

🎙️ **The operator:** "don't look at the UI in terms of code, because the code is not right. Look at it in design."

🙋 **Sam:** I want one card for the trading server. A word: trading, paused, unreachable, needs you. Last heartbeat. How many units. What's at risk.

🏗️ **Hollis:** The design's Settings already lists Connections with reading words (ok, slowed, maintenance, needs you, down) and names the place "trading server" [C: `tracker/qma-v2/UI-HANDOFF.md` §17 items 8 and 14]. The UI branch has no unit shelves [C: R42 §6.2].

🙋 **Sam:** And before I close my laptop: a panel that says what keeps running and what stops.

🎙️ **The operator:** "We're not trying to vibe trade or vibe code here."

🤖 **Ana:** Every trade view: the spread when it was taken, the session, the broker. One click to the market journal minute.

📡 **Dara:** A heat map: instrument by hour, per broker, of spread plus fees. He'll see "is it the broker or the time" without asking.

🙋 **Sam:** Preview and detail. He's said it before.

## Round 10. Wildcards

🌊 **Mei:** Wildcard one: no node. Run the units at the venue. cTrader has cloud-hosted cBots [I]. Do they take Python? Find out.

🔌 **Ines:** That hands the unit to Spotware's runtime. Our feed pool, guards and journals don't come along.

🪓 **Grit:** Wildcard two: brokers give free VPSs to active clients [I]. Free node.

🖥️ **Kofi:** Usually Windows with MT5 on it. Fine for MT5, odd for everything else.

📈 **Walt:** Wildcard three: put the node next to the broker's matching engine. London LD4, New York NY4 [I]. Not for speed games. For fewer hops.

🔐 **Sable:** Wildcard four: the live key on a little box at his house that agents can't reach. His hardware, local first, no shell from the agent PC.

🪓 **Grit:** So a second computer at home. That's a node with a worse internet line.

🔐 **Sable:** It's a node that satisfies both rules. Power cuts still kill it.

🔭 **Priya:** Wildcard five: the node keeps a hash-chained flight recorder. He comes back after a week and knows nothing was rewritten.

🤖 **Ana:** Wildcard six: make "first run on my machine" a button. "Rehearse on this PC" next to "Send to trading server" on every unit.

🎙️ **The operator:** "We need to move slowly."

## Round 11. Natural close (no bow)

**Clashes left standing.**
1. Grit vs Kofi: is a VM or WSL2 on the PC a fair reading of "first run on my machine"?
2. Sable vs Mei: is a trade-only, no-withdraw key still "a key that can trade live money"?
3. Walt vs Grit: brain/arm split, or a second machine on the trade path?
4. Grit vs the stand-in rule: who stands in when the only machine allowed to trade is down?
5. Priya vs Ana: telemetry stack or plain tables as the journal's store of record?
6. Dara vs Grit: is a server-held tick archive an extension or a quiet reversal of local first?
7. Ines vs everyone: demo rehearsal proves the code, not the live host.

The room broke up with Sam still asking how long Spotware takes.
