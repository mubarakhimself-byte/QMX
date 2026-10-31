# Party: the versions of the architecture and the foundation set

Agent A0, 31 Oct 2026. Skill `bmad-party-mode`, run `--non-interactive --mode session` (one mind voices every persona; the skill's own fallback for an agent that may not spawn). The cast is named inline, so it is the roster and the party keeps no memory file (the skill: "ad-hoc inline casts have none"). Activation ran: `resolve_customization.py` (party mode `session`, no prepend or append steps) and `resolve_party.py` (`installed_agents_resolved: false`, so the cast was conjured from the brief). The stale factory facts and `on_complete` endings in `_bmad/custom/` were ignored. Nothing was written to `_bmad-output`.

**Cast.**
- 🏗️ **Winston**, the architect (the installed persona: Fowler's pragmatism, Vogels's realism, rule of three, boring technology).
- 💻 **Amelia**, the developer. Terse, talks in file paths and tests.
- 🧪 **Murat**, the test architect. "Show me the check that fails."
- 📟 **Ines**, the on-call engineer for the node and its monitoring. Thinks in pages at 3 a.m.
- 📈 **Kofi**, a cTrader FX and gold scalper.
- 📊 **Dara**, a futures order-flow trader.
- 🧭 **Sam**, a newcomer who installs QMX out of the box.
- 📏 **Level**, the claim checker.
- 🎙️ **The operator**, in his own words only. Every line in his voice is a quote with its transcript line (T1 = `operator/transcript-2026-10-20-to-28.md`, T2 = `-29-to-30.md`, T3 = `-30-to-31.md`), checked by script at the end.

**Inputs on the table.** The frame (`architecture/00-frame-after-grounding.md`), STATE midday rulings 1 to 55, the ledger, the six grounding files and research 54, the funnel (solutions, experience, the edge-case catalogue) and the lead's review of the funnel, which binds.

---

## Round 1. What we are choosing between

🏗️ **Winston:** Three versions, and I want them different enough to argue about. A is the frame with the funnel's refinements: a small kernel of QML, the dictionary, the unit template, the checker, the judge, journals and market facts, on the core that already exists, with QMB, the trading node and the MIS publisher as mini apps. B takes his seed all the way: almost everything is a mini app, the kernel shrinks to the Library, the engine, the catalog and the mini-app core. C is the boring one: no new apps, QMB stays a door in the host, the node becomes a built-in trading role of the host.

🎙️ **The operator:** "Most things can actually become mini apps." (T3:1383)

🎙️ **The operator:** "it's like handing someone white label software" (T3:1338)

📏 **Level:** Before anyone falls in love: all three sit on the same built base. One catalog, one Library, one engine, one host per QMX folder, the mini-app core with its manifest, operations, `provides` and `feeds`. G2 §5.4 and G4b Q5 checked it. Nobody is proposing to replace those.

💻 **Amelia:** And nobody gets to pretend the unit exists. `unit.schema.json` has `"properties": {}`. I ran it: the Library accepts `{"anything": 1, "goes": [1, 2]}` as a unit.

🧭 **Sam:** So whatever you pick, my first hour is: install, open, and there is a unit I can backtest. Is that true in all three?

🏗️ **Winston:** It's the yardstick. That, the 267 cases in the catalogue, and his three tests: hard cases handled, maintainable, explainable in a few sentences.

## Round 2. Version B: mini apps all the way down

📊 **Dara:** I like B on first read. Want a better QMB? Install one. A better MIS? Install one. That's how I'd want a platform.

🧪 **Murat:** Then show me where the judge lives in B.

📊 **Dara:** In a judge app.

🧪 **Murat:** So a new QMB variant arrives with a friendlier judge app and the same unit passes. The score follows the tester. That's the failure the judging file was written to stop.

🎙️ **The operator:** "So if one day I decide to build a new version of QMB, I should be able to." (T3:1383)

🏗️ **Winston:** A new QMB, yes. A new judge of QMB, no. He asked for variants of the tester, not variants of the referee.

💻 **Amelia:** Worse for QML. B makes the checker an app. The Library's save is the one door no path skips, scripts and shells included (G4b Q2 backstop). If the checker is an app that might be off, the backstop is gone. And the copilot's default home lists core toolsets only (`HAR/surface.py:484-489`), so an app's unit tools vanish from the copilot unless a setting names them.

🎙️ **The operator:** "QML is very important, please." (T3:1264)

📈 **Kofi:** And two QML apps means two meanings of "RSI crossed back above 30" on the same day. I've seen that kill a desk. One backtest engine, one live engine, different rounding, three weeks to find it.

📏 **Level:** B keeps one real gain: QMB, the node and the MIS as apps. A already has those three. What B adds beyond A is the checker, the judge, the catalogue and the market facts as apps, and each of those is where two versions must never disagree.

🧭 **Sam:** And I install eight things before anything works?

🏗️ **Winston:** Rule of three. We extract an app when a second version is real. For QMB he named it. For the judge nobody did, and a second judge is a bug.

## Round 3. Version C: the boring core

🏗️ **Winston:** My job is to make C sound good, so here goes. One host process already runs chats, the engine, the Library writer and the apps supervisor (`HO/host.py:1-20`). PR 204 already lands a backtest through one function. Rebase it, bind the door, done. The node becomes a trading role inside the same host. No manifests, no app signatures, fewer moving parts.

📟 **Ines:** I get paged when that host runs out of memory because a chat read a 2 GB file. On the trading server that's the process holding my open positions. A chat should never share a process with an order.

💻 **Amelia:** On a trading host there are no chats. Lead's review, settlement 4: no chats and no agent steps where a live key lives.

📟 **Ines:** Fine, then think updates. In C a QMX update restarts the host, so it restarts trading. In A the node app has its own inner supervisor and the host updates only on his click when the node says it is safe.

🎙️ **The operator:** "Or improve it, or give multiple variants, because it can be a mini app, for God's sake." (T3:1383)

📏 **Level:** That one is a ruling, not a seed: STATE midday ruling 22. C cannot run two QMB versions side by side without a switch in the host. C fails a ruled requirement.

🏗️ **Winston:** Agreed, C loses on QMB. But keep its instinct: no new machinery where the built core already does the job. The node's organs stay libraries. The trading profile is a host setting, not a new program.

🎙️ **The operator:** "Literally, a mini app can have a server of its own." (T3:1562)

🎙️ **The operator:** "So the reason why mini apps are like that is because of the logging and monitoring." (T3:1562)

📟 **Ines:** That's my vote for A on the node. The app's health log and breaker are the monitoring I want, for free.

## Round 4. The node inside A

📈 **Kofi:** The node is the only thing that can lose me money. What's in it?

💻 **Amelia:** The organs that are right, kept as libraries: the cTrader client, reconnect and gap replay, the order pacer, UNKNOWN per stream, reconcile, the kill switch, the kill line, clock bands, one refresher per credential, the heartbeat, the loop over QMB's `run_slice` (G4a §2.2). The shell gets replaced: host, seats, promotion, Book paper, doors, deploy recipes, bench, the Grafana stack, about 11,900 lines of proof campaigns.

🎙️ **The operator:** "We might delete a lot of code, in fact, a fresh start." (T3:1562)

🧪 **Murat:** Deleting needs a census, not a feeling. Who outside the node imports the shell?

💻 **Amelia:** I ran an import scan over the exported checkout. `qmn.seats`, `qmn.promotion`, `qmn.paper`, `qmn.host`, `qmn.bench`: nobody outside `qmn/`. Three callers to move in the same wave: `qmx_tools` imports `qmn.doors.api` for the agent's node-state tool, `qmn.capital.kill_line` imports `qmn.paper.demotion`, and `qmn.mis.regime_register` imports `qmn.promotion.hub`. That's the whole list.

📟 **Ines:** Inside the host's supervisor or its own systemd service?

🏗️ **Winston:** Inside, with its own inner supervisor, and the server's host as a systemd service that always restarts. One install, one monitoring path.

📟 **Ines:** I still want it outside. A host crash should never touch trading.

🏗️ **Winston:** Then the undo is cheap: the node app's process becomes its own service the host adopts. I'm not closing that.

🎙️ **The operator:** "It's set for Linux because most VPSs that we're going to be using work with Linux." (T3:1096)

🎙️ **The operator:** "I would prefer using Windows than sorting WSL" (T3:903)

💻 **Amelia:** The app shape answers both. QMN's Linux-only pieces are supervision, the Unix-socket powers door and `systemd-creds`. The app replaces all three: the apps supervisor with a Job object on Windows, operations instead of the socket, the host's key stores. So practice runs native on his PC, live runs on a Linux VPS, and WSL is only the fallback.

🎙️ **The operator:** "we can go with WSL, okay? If all goes south." (T3:1096)

📈 **Kofi:** Two machines on one cTrader account?

📟 **Ines:** That's my nightmare case. A restored server image wakes up beside the new one. QMN already pins the machine identity in its runtime config (`configured_runtime.py:278-280`). Keep that: a deployment names one machine, and a node refuses a deployment naming another. Then tag every client order id with the node's id, so a start-up reconcile sees a foreign claimant and refuses to trade that account.

🧪 **Murat:** No lease service on a third machine?

📟 **Ines:** No. Units stand alone. The broker is the only thing both nodes can see, so the broker is the arbiter.

## Round 5. Where the MIS lives

🎙️ **The operator:** "What I wanted was the MIS just reads and outputs." (T1:1951)

📊 **Dara:** The funnel said readings are core blocks and the MIS publisher is an app with a node instance and a PC instance. Here's my problem. The node's feed keeper holds the only live connection on that machine (one connection per venue per machine). How does a separate MIS app on the node get ticks?

💻 **Amelia:** Apps talk two ways: an operation, or a landed artifact (engine AD-64). Neither is a tick stream.

📈 **Kofi:** Then split it the way a desk splits it. Spread against usual, quote gaps, feed state, spread quality: those are the node's own guards. They protect me. They run inside the node, on the feed, and the node stamps them into reading history. Volatility state, trend against range, efficiency ratio, funding state: those are market state. They run on bars and sessions. The MIS instance on the node reads the node's local market-data store and publishes those.

🏗️ **Winston:** And a unit that needs a reading at tick speed computes it itself from its own feed. Same code, from the catalogue. The MIS never sits on the trade path.

🎙️ **The operator:** "why should the unit stop trading?" (T1:1574)

📊 **Dara:** And order flow. I need data, not charts.

🎙️ **The operator:** "They need order flow data." (T3:1264)

📊 **Dara:** cTrader gives broker depth and ticks, no tape. Hyperliquid gives a real tape with the taker side, free. CME needs a paid feed. So every order-flow block declares its data level and a fallback chain, and the checker refuses one on a market that can't feed it.

🎙️ **The operator:** "I think I'll use CME, man." (T3:1562)

📏 **Level:** Futures as data are a port with a placeholder. Nothing in the core assumes which feed he buys (lead's review, LC-27 confirmed).

## Round 6. The judge stays home

🧪 **Murat:** Version A puts the judge, the study spec, the try ledger and the baseline cards in the core, outside every QMB version. Results without a core-issued run id are refused. I want that tattooed somewhere.

🎙️ **The operator:** "Favor determinism over non-determinism. That's the whole point of QML" (T3:903)

📈 **Kofi:** And when twenty markets run, the best-looking one is luck until proven otherwise.

🧪 **Murat:** One rule for every market, written before the run. Every judged market a try. Each pulled toward the unit's whole result. Correlated markets count once. Scripts decide; the agent explains.

💻 **Amelia:** Where does the code sit? Not in `qmb/`, or a new QMB version ships without it. A small core package beside the host, called by the landing function and the `judge` subworkflow.

## Round 7. Machines and the wire

📟 **Ines:** The lead just sent a note in: networking gets designed, not assumed. So, every link that crosses machines.

🏗️ **Winston:** Start with the rule: no cross-machine link is on the order path. Feed in, unit decides, guards check, order out, protection at the broker, journal written. All on one machine.

📈 **Kofi:** Then what's the network for?

📟 **Ines:** Control, results and watching. His click to deploy or kill, from the PC to the node over Tailscale on the host's one port. Heartbeats and node state back on the held stream per node (`HO/streams.py`). Journals and the node's MIS history back to the PC. Telemetry to OpenObserve.

📊 **Dara:** And the broker link is the one that matters. Research 31 measured about 160 ms just for a TCP handshake from his PC to cTrader, against half a millisecond for fan-out inside a process. So the node sits near the broker's servers, and the PC is never between the unit and the broker.

💻 **Amelia:** Journals: push from the node, or pull from the PC?

📟 **Ines:** Pull. The PC is home, it writes its own store, and the node never needs a key to the PC. The node keeps every partition until the PC confirms a verified copy. A week offline loses nothing.

💻 **Amelia:** Then we hit a known bug. A run pass minted on the PC fails at the server's door (G2 §6, backlog "Cross-machine run passes"). The pull job must use a host pass, and the run-pass bug gets fixed before any PC-minted run relies on a server.

🎙️ **The operator:** "the trading node is perhaps a firm" (T3:903)

📟 **Ines:** For the screen, yes: each node's tile shows its own office time. For the rules, no: a London-open rule lives in London's zone, on every node.

🧭 **Sam:** And the kill switch, if the node is unreachable?

📟 **Ines:** Every order already carries its stop at the broker. The kill reaches the node by more than one path. And the last resort is written on the node's page: the broker's own app.

## Round 8. The size, and a bug we found by running it

💻 **Amelia:** I ran something that changes a design call. The plan said: lift "the bot may not size" so a unit's entry carries its size. The obvious move is a new field on the entry intent. I built an entry with a `requested_quantity` key and fed it to the Book door and to QML's door. Both accepted it and silently dropped the size. Only `requested_r` is refused. The CT-23 reader ignores unknown keys under a known format version, by design (`door.py` docstring, AC6).

🧪 **Murat:** So a unit's size could vanish, and the Book would size the trade instead. Quietly.

💻 **Amelia:** Then I stamped the same intent `contract_format_version: 3`. Both doors refused it as an unsupported capability. Fail closed.

🏗️ **Winston:** So the unit's sized intent is a new CT-23 format version, never a new key. Any Book-path reader that meets it refuses instead of guessing. Write that down as a rule.

📈 **Kofi:** And the Book path stays, for the risk session to keep or kill.

🎙️ **The operator:** "a small mistake in there is very costly" (T3:1264)

## Round 9. Scoring against the catalogue

📏 **Level:** I scored all three against the 267 cases and the 18 risk rows, property by property, with a script so it can be rerun. Out of 570: A 567, C 442, B 382. A falls short on three cases: units run inside the node's process, so code that evades the scan is walled only by the sandbox run before deploy plus his click; nothing enforces live priority over research on a shared PC by default; and a Hyperliquid trigger order as the broker-side stop is unproven until the testnet probe.

🧪 **Murat:** A scoring itself near perfect is suspicious.

📏 **Level:** It is, and I'll say why in the file. A was drawn against the catalogue, so it should score high. The honest part is the three misses and the fact that these are judgements, not measurements. The scores separate the versions; they don't prove A works. The dummy unit's pass marks do that.

🎙️ **The operator:** "edge cases build a very solid and core foundation" (T3:1338)

🧭 **Sam:** Can someone say A in a few sentences?

🏗️ **Winston:** QMX has a small core that must always agree with itself: the library units are written in, the checker, the referee, the records and the market facts. Everything that runs on a machine and might need a second version is an app on that core: the backtester, the trading node, the market reader. Only the node sends orders, and it trades on its own machine with nothing else up.

🎙️ **The operator:** "design for complexity and don't design a complex system" (T2:1208)

## Round 10. Deep modules, and the words

🏗️ **Winston:** Deletion test on A's kernel. Delete QML's compiler: every host would build factories by hand, which is the fixture code G1 found. Earns its keep. Delete the judge: every template re-copies gate scripts, as `b` and `d3` do today. Earns its keep. Delete the instrument record: every sizer and QMB reads raw venue documents live. Earns its keep. Delete the MIS app: units still trade, templates lose their history. It's an app, so that's the right shape.

💻 **Amelia:** Seams with two real adapters: the venue-client port (cTrader now, CCXT next), the data-route port (cTrader, CCXT, two downloaders), the QMB contract (today's QMB and any variant, plus the conformance pack as the test adapter). Seams with one adapter are hypothetical: the futures client port. Keep it a declared placeholder, not code.

🎙️ **The operator:** "you know how wrong wording has messed us up so far" (T2:1208)

📏 **Level:** Then the words, once. "Regime" is his trend-against-range, and the shipped volatility buckets become "volatility state". "Trading node" is the app; "server" is a machine; "node setup" in today's code sets up a QMX server, not a trading node, so that phrase stays off his screens. "Market settings" and "market version" stay working words he may rename.

🎙️ **The operator:** "A server can be a server." (T3:1102)

---

## Clashes left open

| Clash | Where it landed |
| --- | --- |
| The node app inside the host's supervisor (Winston) or its own systemd service the host adopts (Ines) | Lead's call: inside, with its own inner supervisor; the undo is named (`level-0/LEAD-CALLS.md`) |
| B's appeal of a second judge "for fairness" (Dara, early) | Rejected: a second judge is a bug; variants are for the tester only |
| C's simplicity for QMB (Winston, playing C) | Rejected: ruling 22 needs variants side by side; C's instinct kept as "no new machinery where the core already does it" |
| Where tick-speed readings run | Execution-health readings inside the node as its guards; market-state readings in the MIS app; tick-speed rule inputs computed by the unit itself |
| Whether A's high score means anything | Kept open by Level: the scores rank designs; the dummy unit's pass marks prove the one picked |

## Where the room landed (carried into `versions.md`)

1. Version A wins, with the refinements found in this room: the MIS split by job (guards in the node, market state in the app); sized unit intents as CT-23 format version 3; the PC pulls journals with a host pass; deployments pinned to one machine with node-tagged client order ids; the shell census of three callers.
2. B's gain kept: the three mini apps, and a unit-holding app template for research and paper (lead's review, settlement 2).
3. C's instinct kept: the node's organs stay libraries, the trading profile is a host setting, and no new app where the core already does the job.
