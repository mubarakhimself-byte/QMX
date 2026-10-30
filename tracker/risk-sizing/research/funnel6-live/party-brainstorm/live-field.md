# The live field: node, live markets, data and journals

Written 2026-10-30 by a funnel agent. Expansion only. Nothing here is a design, a choice or a ruling. Ruling 135 is not decided here.

## How to read this

**Inputs.** His words in `operator/transcript-2026-10-29-to-30.md`, `operator/transcript-2026-10-20-to-28.md` and `operator/2026-10-27-review-dictation.md` (all quotes script-checked, 30 of 30 found). Findings in `STATE.md`, `research/42` (in full), `12` §0, §4, §5, `14` §3.3, §3.6, §5, `18` §7-8, `21` §3, `02` short answer and §7, `09` §2.6, `19` (grep for the old node), `funnel3/party-brainstorm/playing-field.md` L05, L09, L14, `seeds.md:107-117`, and `tracker/qma-v2/UI-HANDOFF.md` §17, `UI-NOTES.md`, `LOCAL-FIRST-PLAN.md`, `SYNC-PLAN.md` (grepped for the node and journals).

**Runs behind it.** `party-transcript.md` (11 rounds, 12 voices, 7 clashes left open). `.memlog.md` (headless brainstorm, 10 techniques, 120 ideas, status complete).

**Marks.**
- `seed-expanded (Sx)` = grows one of the seeds in the seed table. `new` = not in any seed or finding read.
- Question tags: `research` (vendor or tool facts; the number names which queued run would settle it: 31 live path, 32 terrain and venues, 33 data depth and terms, 38 venue connectivity), `operator` (only he can answer: money, irreversible scope, words he cares about), `lead` (settle at architecture), `fog` (not yet askable).
- Claims: CHECKED (source given) or INFERRED. Anything from memory about a vendor is INFERRED and tagged `research`.

## 0. Seeds this round grows

| Id | Seed | Where (CHECKED) |
| --- | --- | --- |
| S1 | PC first: "if something is to run on external compute and external storage, it should first run on my machine. This cost us 2 days of re-auditing and coding" | transcript 10-29/30 |
| S2 | Why a node: "power goes on, comes back off, Wi-Fi drops when power goes off"; "We are literally trading 24/7, my days. This is why we need a trading node." | transcript 10-29/30 |
| S3 | Setup like renting: "a trading node should be as simple as how, for example, I can set up a server from a provider"; "Either we can use a wizard or we can just set it up when I click with a click of a button." | transcript 10-29/30 |
| S4 | "For now, we might have one for starters, but as we grow, okay, we might have more than one." | transcript 10-29/30 |
| S5 | "in the settings in the UI, we proposed that we have an external compute provider" | transcript 10-29/30 |
| S6 | "live markets, in other words, not just market data, live markets" | transcript 10-29/30 |
| S7 | "How am I trading futures? Can I trade futures on CTrader? With order flow and stuff?" | transcript 10-29/30 |
| S8 | "I'm starting with Ctrader. We are going to use Open API." "I might also start with Hyperliquid, with perpetual features." CCXT for crypto | transcript 10-29/30; `STATE.md:157` |
| S9 | Data versus execution: who provides order flow is separate from who executes | `STATE.md:157` |
| S10 | "I would prefer most simple data schemas." | transcript 10-29/30 |
| S11 | Journals are what agents read: "this is what the agents will be looking at" | transcript 10-29/30 |
| S12 | How the Library stores journals | transcript 10-29/30; `STATE.md:152` |
| S13 | The UI judged by design: "don't look at the UI in terms of code, because the code is not right. Look at it in design." | transcript 10-29/30 |
| S14 | Taken, seen but not taken, missed; "this is literally the DevOps layer for that unit" | 2026-10-27 dictation |
| S15 | Market facts apart: "I think the router should give us the journal for that"; "is it the broker? Is it the time?" | 2026-10-27 dictation |
| S16 | Preview and detailed views; "We're not trying to vibe trade or vibe code here." | 2026-10-27 dictation |
| S17 | One id from source to trade | `STATE.md:183` (research 13 row) |
| S18 | Ruling 135 against his PC-first rule (S1) | `STATE.md:154`; ruling text `tracker/qma-v2/research/methodology/26-operator-rulings-and-alignment.md:250-257` |
| S19 | Raw data: "this 44 minute thing is huge" (a 50% volatility jump takes about 44 minutes to show in 1-minute closes, the lead's message just before it) | transcript 10-29/30 |
| S20 | "we need to look at the amount of data we are collecting" | 2026-10-27 dictation |
| F1 | The connect dialog's runner: his cards, checked rerun-safe steps, one row last; no trading-server kind | `research/42` §2.1-2.2 |
| F2 | QMN is Linux and systemd only and never deployed | `research/42` §3 |
| F3 | Feed pool per machine and a lease per broker app | `research/12` §4.2 |
| F4 | Feed failure table | `research/12` §4.3 |
| F5 | Every hard need of a unit is local to its machine | `research/14` §3.3 |
| F6 | Four journal streams, one writer each | `research/14` §5.2 |
| F7 | cTrader has quotes and depth, no public trade tape | `research/21` §3 |
| F8 | Node self-test on connect (kill-switch speed, test trades, broker connections) | `seeds.md:111` |
| F9 | A `trade` kind with `world`; no unit or router journal; no agent read path for journals | `research/42` §6.1 |
| F10 | Market journal per broker x account type x instrument x minute | `research/12` §5.1 |

## 1. The facts this field stands on (CHECKED unless marked)

1. A trading node cannot be set up through the shipped path. The connect dialog has kinds for storage, compute and deep logs only (`research/42` §2.1, `connect.py:389`). The server it builds is the QMX host as a worker and Library store (`research/42` §2.2).
2. QMN needs Linux and systemd. Its powers door is a Unix socket checked by peer credentials (`research/42` §3). So the node cannot run on his Windows PC as it is. This means the PC-first rule (S1) already fails for the node before any new work (INFERRED from the two checked facts).
3. Ruling 135 is in code. A live-capable cTrader grant is refused on This PC and on any agent-reachable machine (`research/42` §3, `BRK/adapters.py:107-172`).
4. Each trading server needs its own cTrader app, approved by Spotware with no published timeline (ruling text `:254`).
5. cTrader gives bid and ask quotes and depth with sizes, but no market-wide trade tape (`research/21` §3).
6. CCXT in QMX is spot only. Hyperliquid has no code (`research/02` short answer 6; `research/42` §4).
7. Hyperliquid's public websocket carries trades, book, funding and open interest. Its API keeps about 3.5 days of 1-minute candles, so QMX must record its own (`research/12` §4.1; `research/02`).
8. Journals today are the `trade` kind per account, with `world` and `initial_risk`. Agents cannot read journals through any catalog row (`research/42` §6.1).
9. The design names the place "trading server" and shows Connections with reading words: ok, slowed, maintenance, needs you, down (`tracker/qma-v2/UI-HANDOFF.md` §17 items 8, 14).
10. The PC had 12 GB free on C: when last read. Ticks for the whole archive do not fit (`research/12` §5.2).

---

## 2. Ideas by theme

Ids match `.memlog.md`. A few party-only ideas carry a `P` id.

### 2.1 Setting up a node

| Id | Idea | Mark |
| --- | --- | --- |
| B001 | A trading server is one more kind in the connect dialog, on the same runner. | seed-expanded (S3, F1) |
| B002 | Provider-API wizard. He pastes a provider token once; QMX creates the server, installs, deletes the token. Token lifetime is a number (default: one hour). | seed-expanded (S3) |
| B003 | No-token default. He rents by hand, as today's card says; QMX does the rest. | seed-expanded (S3, F1) |
| B004 | Cloud-init paste. QMX prints one text block; he pastes it into the provider's user-data box; the server builds itself and calls home. | new |
| B005 | Region picker by measured round trip to each broker's trade host, before he pays. | new |
| B006 | One image, two roles. The QMX host gains a trading role instead of a separate QMN deploy with its own paths and observability. | seed-expanded (`seeds.md` "simplify QMN", F2) |
| B007 | Places gain a can-trade capability beside can-run. | seed-expanded (F1) |
| B008 | Node passport. The connect self-test lands as a Library item: kill-switch latency, a demo test trade, broker connect, clock skew, disk, feed freshness. | seed-expanded (F8) |
| B009 | Size suggestion from the admitted units and their data kinds. The size table is a number. | new |
| B010 | Retire-a-node wizard. Units go back to paper on the PC, the node's broker app grant is revoked, the server is deleted. | new |
| B011 | Updates only when flat or between sessions, reusing sync-before-update. | seed-expanded (`research/42` §2.1, PR 234) |
| B012 | Second node = clone this node in another provider. | seed-expanded (S4) |
| B013 | Start the cTrader app registration on day one of the wizard, before he rents anything. | new |
| P01 | A one-sentence promise on the node card: "When my laptop is closed, these keep trading." | seed-expanded (S2) |

### 2.2 First run on his PC

| Id | Idea | Mark |
| --- | --- | --- |
| B014 | The Linux node runs on the PC under WSL2, so the PC rehearses the exact node. | new (from F2) |
| B015 | The node is a container image; the PC and the server run the same image. | new (from F2) |
| B016 | Port the Linux-only doors so the node runs natively on Windows too. | new (from F2) |
| B017 | Shadow mode. The full node stack on the PC reads live prices, decides and journals would-have-done rows, placing nothing. | new |
| B018 | Twin run. PC and node run the same units for N days and the journals are diffed. N is a number (default: 5 trading days). | new |
| B019 | The two-day lesson as a release check. A node release ships only after X hours on the PC. X is a number (default: 24). | new |
| B020 | Home-node mode. The PC trades live while on; the server stands in when it goes dark. | seed-expanded (S1, rulings 136-139) |
| B021 | Reverse. The PC never trades live; the node is the PC's always-on half. | seed-expanded (S18, today's code) |
| B022 | A small home box on a UPS, unreachable by agents, holds the live key. | new |
| B023 | The PC-versus-node difference list. Only the key, the host name and the broker app may differ; anything else listed is a bug. | new |
| B024 | A "Rehearse on this PC" button beside "Send to trading server" on every unit. | new |

### 2.3 Failure and recovery

| Id | Idea | Mark |
| --- | --- | --- |
| B025 | Every live order carries its stop at the broker. | seed-expanded (F4) |
| B026 | A venue dead man's switch where one exists (Hyperliquid scheduled cancel, INFERRED); silence cancels resting orders. | new |
| B027 | Reconcile on restart. The broker's positions and deals win; journals rebuild from them; orphans get rows. | seed-expanded (playing-field L14-08) |
| B028 | Power-cut drill on the PC in demo. | new |
| B029 | Outside watcher: the PC when on, a free uptime pinger when off; one alert per incident. | new |
| B030 | Passive second node in another provider, holding no live key until his click. | seed-expanded (S4) |
| B031 | Laptop-off is the normal state; the PC link shows "unreachable since". | seed-expanded (F5) |
| B032 | Node outbox. Journals queue and sync when the PC returns, even after a week. | seed-expanded (F5) |
| B033 | Disk-full order on the node: tick recording gives way before journals. | seed-expanded (playing-field L14-10) |
| B034 | Broker weekend maintenance as scheduled venue-down rows. | seed-expanded (F4) |
| B035 | Token-refresh drill on demo across two machines. | seed-expanded (ruling text "one home per sign-in") |
| B036 | Client order id = the trade's trace id, so a retried send never doubles a position. | new |
| B037 | A five-line provider-outage card: what keeps running at the broker, what he does by hand. | new |
| B038 | Clock drift check in the passport and hourly. | seed-expanded (F4) |
| P02 | Name who stands in for the trading server. Under 135 as written, nothing can. | new (party round 4) |

### 2.4 Live feeds

| Id | Idea | Mark |
| --- | --- | --- |
| B039 | Feed pool per machine, one subscription per symbol, a lease per broker app. | seed-expanded (F3) |
| B040 | Record everything subscribed; live data becomes history. | seed-expanded (S6, fact 7) |
| B041 | Tick-first feeds for sensing market state. | seed-expanded (S19) |
| B042 | Futures routes to compare: Rithmic via a futures broker, CQG, Interactive Brokers, Tradovate; data from a vendor. | seed-expanded (S7) |
| B043 | Ask whether any cTrader broker lists exchange futures, or only futures-based CFDs. | seed-expanded (S7) |
| B044 | Hyperliquid data with no key; trading through an API wallet. | seed-expanded (S8) |
| B045 | Perps feeds through CCXT's websocket layer. | seed-expanded (S8, fact 6) |
| B046 | Feed quality per symbol per hour in the market journal. | new |
| B047 | Venue time and receive time on every message. | seed-expanded (F3) |
| B048 | Trading-hours calendar as data per instrument and venue. | seed-expanded (`research/02` short answer 1) |
| B049 | Units declare data kinds; the pool subscribes only to those, which also bounds data fees. | new |
| B050 | Paid feeds switched on when a unit backtested on that vendor's history passes. | seed-expanded (STATE round-2 Q7) |
| B051 | Last-value cache so a restarted unit sees current state at once. | seed-expanded (F3) |

### 2.5 Data route and execution route

| Id | Idea | Mark |
| --- | --- | --- |
| B052 | A connection has two roles, data and execution. A unit binds one data route per data kind and one execution route. | seed-expanded (S9) |
| B053 | Proxy-data unit. Trade the US500 CFD on cTrader, read CME futures tape from a vendor; every row names both venues. | seed-expanded (S9, F7) |
| B054 | Basis watch: the gap between the proxy and the traded market, per minute. | new |
| B055 | Same-venue data preferred; proxy is a declared, tested fallback. | new |
| B056 | Execution route ranking per instrument from measured spread plus fees by hour. | seed-expanded (S15) |
| B057 | Several brokers per instrument, compared in the market journal; his admission names the broker. | seed-expanded (S15, STATE round-2 Q2) |
| B058 | The grid class x data source x execution venue x machine, readable by agents and by him. | new |
| B059 | Data licence terms on the connection row (personal, display, non-display). | new |
| B060 | A separate data route keeps market sensing alive during a broker outage. | new |
| B061 | Data-only connections with no account are first-class rows. | new |
| B062 | A broker whose data is unused still writes its spread and fill rows. | seed-expanded (F10) |

### 2.6 Journals and schemas

| Id | Idea | Mark |
| --- | --- | --- |
| B063 | One event row shape for every stream: id, at, stream, subject, kind, world, links, body. | seed-expanded (S10, S14) |
| B064 | Four streams with one writer each, plus a fifth node journal (start, stop, update, self-test). | seed-expanded (F6) |
| B065 | No separate guard stream; guard verdicts are rows with stream = guard. | new (contests F6) |
| B066 | Seen-not-taken rows carry one reason from a small closed list plus free text. | seed-expanded (S14) |
| B067 | Missed trades computed afterwards by replay, never written live. | seed-expanded (S14, `research/14` §5.2) |
| B068 | Events by default; every decision per bar only on request, time-boxed. Box length is a number (default: one day). | seed-expanded (S20) |
| B069 | Journal before dispatch, as the node already does. | seed-expanded (`research/14` §3.3) |
| B070 | World on every row, from the trade kind. | seed-expanded (F9) |
| B071 | Calibration receipts as rows: what moved, from what, to what, driven by which rows. | seed-expanded (STATE research 13 row) |
| B072 | Schema version on every row; old rows never migrate. | new |
| B073 | Monthly Parquet partitions per unit journal, one Library card pointing at them. | seed-expanded (S12, `research/12` §5.3) |
| B074 | Broker-says stream: the broker's own deal history beside the unit's rows. | new |
| B075 | Session and hour performance is a derived view, never a stored column. | seed-expanded (S20) |

### 2.7 What agents read

| Id | Idea | Mark |
| --- | --- | --- |
| B076 | A journal door for agents with handles, as a catalog row agent steps can name. | seed-expanded (S11, F9) |
| B077 | Preview card first, rows after. | seed-expanded (S16) |
| B078 | A prebuilt trades-with-context table so agents never write joins. | seed-expanded (playing-field L09-09) |
| B079 | Journal alarm rows fire Library event triggers. | seed-expanded (`research/42` §1.2) |
| B080 | Agents write only notes and proposals, in their own section, linked to what they annotate. | seed-expanded (`research/14` §5.2) |
| B081 | Agent claims cite row ids; a script recomputes the claim before it renders. | seed-expanded (funnel3 agent-proof finding) |
| B082 | Market almanac workflow: weekly plain sentences from the market journal. | seed-expanded (STATE round-2 Q6a) |
| B083 | "Why didn't it trade?" from seen-not-taken rows. | new |
| B084 | Morning brief gains node facts from the node journal. | seed-expanded (`research/42` §1.8, db-desk-brief) |
| B085 | A digest script before the model, one page per unit per day. | new |
| B086 | Labels, not account numbers, in what agents read. | new |

### 2.8 The UI, judged by its design

| Id | Idea | Mark |
| --- | --- | --- |
| B087 | Trading server card: one word, last heartbeat, units on it, open risk. | seed-expanded (S13, fact 9) |
| B088 | "Before you close the laptop" panel: what keeps running, what stops, what waits. | new |
| B089 | Wizard screens are his cards, with progress as checked steps. | seed-expanded (S3, F1) |
| B090 | The compute provider setting splits into workers and trading servers. | seed-expanded (S5, fact 9) |
| B091 | Unit preview: stage, world, markets, last-30-trades sparkline, guard state, where it runs. | seed-expanded (S16, `research/14` §5.6) |
| B092 | Unit detail: journal tabs taken, seen, missed; each trade joins its market minute. | seed-expanded (S14, S16) |
| B093 | Trade view: spread, session and broker at the moment of the trade. | seed-expanded (S15) |
| B094 | Market heat map: instrument x hour, per broker, spread plus fees. | new |
| B095 | Where-it-runs badge on every unit and job. | seed-expanded (`UI-NOTES.md:18` standing rule) |
| B096 | Demo or live stamp on every money figure. | seed-expanded (PR 215, `UI-HANDOFF.md` §18 item 5) |
| B097 | One timeline strip of node events with PC on and off overlaid. | new |

### 2.9 Security and keys

| Id | Idea | Mark |
| --- | --- | --- |
| B098 | Demo-rehearse everything on the PC; the live key lives only on the server. | seed-expanded (S18, `STATE.md:154`) |
| B099 | The harm is placing trades, not withdrawing, so no-withdraw trade keys still count as live keys. | new |
| B100 | A separate Windows account or VM, out of agent reach, holds the live key. | new |
| B101 | Hardware-backed unlock (Windows Hello or TPM) for the trading process only. | new |
| B102 | Live key exists on the PC only while the agent harness is stopped. | new (weak) |
| B103 | Broker-side account limits as the guard that holds even if a key leaks. | new |
| B104 | A tiny live canary sub-account on the PC as the live path's PC-first proof. | new |
| B105 | The trading server must not share the SSH path the PC already holds to the worker server. | new (from `research/42` §2.2 step 4) |
| B106 | Brain and arm. The arm holds the key and sends orders, on the server only. The brain (units, feeds, guards, journals) runs anywhere, the PC included, with a full copy on the server so units still stand alone. | new |
| B107 | The shipped key path: the sign-in code goes to the server, the PC reads the account from the server's reports. | seed-expanded (ruling text) |

### 2.10 Wildcards

| Id | Idea | Mark |
| --- | --- | --- |
| B108 | No node: units as cloud-hosted cTrader cBots, if those exist and take Python. | new |
| B109 | A broker's free VPS for active clients as the node. | new |
| B110 | Node in the broker's data centre region for fewer hops. | new |
| B111 | UPS plus 4G failover so the PC rarely goes dark; the node only for long absences. | new |
| B112 | A small ARM board as the home node. | new |
| B113 | The journal is the PC-node protocol: admissions go as rows, answers come as rows. | new |
| B114 | Hash-chained flight recorder on the node. | new |
| B115 | Rent the node by the hour, only for the sessions units trade. | new |
| B116 | Nodes by venue, each near its venue's servers. | seed-expanded (S4) |
| B117 | Node cost readout beside what the node's units earned. | new |
| B118 | The node never holds the Library; it holds journals and an outbox. | seed-expanded (`research/42` "must not break": one Library writer) |
| B119 | Phone panic button: stop new entries everywhere, logged by the guard. | new |
| B120 | Each unit carries a data-needs card; a new node is checked against it before anything moves. | new |

---

## 3. Ruling 135 against "first run on my machine": the options

Not decided. Each option is judged on the three tests from standing order 6: the hard cases, maintenance and debugging, and explaining it in a few sentences. "Live path" means the live host, the live broker app and a live account.

| # | Option | What runs on the PC | Hard cases | Maintain and debug | Explain to him | Main cost |
| --- | --- | --- | --- | --- | --- | --- |
| O1 | **Keep 135 as written** (B021, B107) | Everything on demo. Never live. | Weak. The first live order happens on the server, unrehearsed. Nothing stands in when the server is down (P02). | Simplest. Already in code. | "Live money only on the trading server." | His rule is met for code, not for the live path. |
| O2 | **Demo rehearsal plus twin and shadow runs** (B017, B018, B023, B098; lead's candidate grown) | The full node stack, on demo and on live prices with no orders. | Better. Only the live host and live app go untested on the PC, and the difference list names them. Still no stand-in. | One more mode (shadow) and a diff script. QMN must run on the PC first (B014 or B015). | "Your PC runs everything on practice money and watches live prices. Only the real-money key lives on the server." | Needs a Linux layer on the PC. |
| O3 | **Overrule for the PC: home-node mode** (B020) | Everything, live included, while the PC is on. The server stands in. | Strong for local first and the stand-in rule. Weak against an agent shell placing trades. | Two machines can trade the same account, so one home per sign-in and a hand-over are needed. | "Your PC trades when it's on; the server takes over when it's off." | The agent-shell threat comes back. |
| O4 | **A walled key on the PC** (B100, B101) | Everything, with the live key behind a Windows account, a VM or a hardware unlock agents cannot open. | Depends on how strong the wall is (research 31). | A second user or VM to keep alive. | "The real-money key sits in a locked room on your PC that agents can't enter." | The wall's strength is unproven. |
| O5 | **Brain and arm** (B106) | Units, feeds, guards and journals, on live prices. Orders go only through the arm on the server. | Strong if the server also runs a full brain, so a unit never waits on the PC link. Weak if the PC brain is ever the only brain. | A new seam and a small protocol to keep. | "Your PC thinks; the server is the only one allowed to press the button." | A second concept on the trade path. |
| O6 | **A home appliance** (B022) | Nothing live. A second small box at home holds the key. | Fails the reason the node exists: power cuts and Wi-Fi drops still stop it. | Another machine to patch. | "A small locked box at home trades." | Doesn't survive his power cuts. |
| O7 | **A live canary on the PC** (B104) | One tiny live sub-account, live, on the PC. | Proves the live path on his PC. Keeps the agent-shell risk for that account. | One extra account and its key. | "One small real account on your PC proves it works before the server gets the big one." | A money call, and still a live key where agents work. |
| O8 | **Per venue** (B099, B103) | Decided per venue from what the broker offers (account limits, trade-only keys, dead man's switch). | Honest about real differences between venues. | A rule table per venue. | Hard. A different answer per broker. | Fails the few-sentences test. |

**Facts that move these options (all `research`):** whether QMN runs in WSL2 or a container on Windows 11 (research 31); how strong a separate Windows account or VM is against an agent running as him (research 31); which of his venues offer account-level limits, trade-only keys or a dead man's switch (research 38); cTrader live and demo hosts and app approval times (research 38).

**What every option shares (INFERRED):** broker-side stops on every order (B025), one home per sign-in (B035), and the guard working without the PC (`research/14` §3.6).

---

## 4. Questions

### 4.1 Node setup and PC first

| Id | Question | Tag |
| --- | --- | --- |
| N-01 | Does QMN run unchanged in WSL2 or a container on Windows 11, with systemd and peer-checked Unix sockets? | research (31) |
| N-02 | Does a Linux layer inside his PC count as "first run on my machine"? | operator |
| N-03 | Is the trading server the QMX host in a trading role, or QMN beside the host? | lead |
| N-04 | Which wizard is the default: provider token, cloud-init paste, or his manual card? | lead |
| N-05 | Which providers create servers by API, allow trading use, and have regions near the brokers? | research (31) |
| N-06 | How long does Spotware take to approve an app per trading server, and can the request start before the server exists? | research (38) |
| N-07 | Which passport checks touch a live account, and are they read-only? | lead |
| N-08 | Does he want QMX to pick the provider, or pick it himself? | operator |
| N-09 | Is a passive second node worth its monthly cost before the first unit is live? | operator |
| N-10 | What is on the PC-versus-node difference list today? | lead |
| N-11 | MT5 needs Windows: does an MT5 unit force a Windows trading server, Wine, or MT5 on the PC only? | lead |
| N-12 | If a unit runs on the node and its shadow on the PC, which copy is "the unit" in the Library? | lead |

### 4.2 Failure and recovery

| Id | Question | Tag |
| --- | --- | --- |
| F-01 | Who stands in for the trading server when it is down, if the PC may not hold a live key? | operator |
| F-02 | Which venues offer a dead man's switch or scheduled cancel? | research (38) |
| F-03 | After a crash with partial fills, which record wins, and how is the unit journal corrected? | lead |
| F-04 | How does an alert reach his phone with no agent sending messages for him? | lead |
| F-05 | What does the node do after a week without the PC: which advice expires, what keeps trading? | lead |
| F-06 | Does a provider reboot mid-trade matter once stops sit at the broker? | lead |
| F-07 | Which kill-switch levels fire on the node with no PC? | operator |
| F-08 | How often do power-cut and token-refresh drills run? (a number) | lead |
| F-09 | On a full disk, what gives way first on the node and on the PC? | lead |

### 4.3 Live feeds

| Id | Question | Tag |
| --- | --- | --- |
| L-01 | Which futures routes give tape and depth at retail size, and at what monthly cost? | research (38) |
| L-02 | Can any cTrader broker trade exchange futures, or only futures CFDs that expire early? | research (38) |
| L-03 | What are Hyperliquid's limits for about 200 symbols on one machine and one address? | research (38) |
| L-04 | Does CCXT's websocket layer cover Hyperliquid and Binance futures with funding and open interest? | research (38) |
| L-05 | Which instruments record ticks from day one? | operator |
| L-06 | Ticks on the server with a PC cache, given 12 GB free on C:? | lead |
| L-07 | Does tick-first sensing help a unit that trades 1-minute bars, or only market sensing? | fog |
| L-08 | What exactly did "this 44 minute thing is huge" ask for: tick sensors, tick units, or both? | fog |
| L-09 | Do Dukascopy's terms and exchange non-display rules allow recording and agent analysis? | research (33) |
| L-10 | When does a symbol count as stale? (a number per instrument and hour) | lead |

### 4.4 Data route and execution route

| Id | Question | Tag |
| --- | --- | --- |
| D-01 | Is a proxy-data unit allowed, and how is it judged when its signal and execution venues differ? | lead |
| D-02 | How large and how steady is the gap between index futures and index CFDs per minute? | research (32) |
| D-03 | Is the execution venue part of what his click admits? | operator |
| D-04 | Which two venues get wired first: cTrader and Hyperliquid? | operator |
| D-05 | Does a data-only connection get health words and a row in Settings like a broker? | lead |
| D-06 | Does a broker outage stop market sensing when data comes from that broker? | lead |
| D-07 | Who decides to start paying for a data feed, and on what evidence? | operator |

### 4.5 Journals and schemas

| Id | Question | Tag |
| --- | --- | --- |
| J-01 | Store of record: plain Parquet streams, the telemetry stack, or Library items? | lead |
| J-02 | Guard verdicts as their own stream, or rows in the one shape? | lead |
| J-03 | Who keeps the closed list of not-taken reasons, and how does it grow? | lead |
| J-04 | Does every row carry the market key, or only trade rows? | lead |
| J-05 | Which backup class are journals: his content that travels, or rebuildable? | lead |
| J-06 | Which field names come from the shipped `trade` kind unchanged? | lead |
| J-07 | What does each venue's own deal history give for the broker-says stream? | research (38) |
| J-08 | Does the node journal live in the same store as unit journals? | lead |
| J-09 | What does every-decision logging cost per unit per year, against the event-only default? | lead |
| J-10 | What does "anything that can record data" leave out? | fog |

### 4.6 What agents read

| Id | Question | Tag |
| --- | --- | --- |
| A-01 | Is the journal door a catalog row, a mini-app operation, or a script read? | lead |
| A-02 | What goes into the daily digest so small models don't drown? | lead |
| A-03 | May agents read journals of trades still open, or only closed ones? | lead |
| A-04 | How are agent claims scored later against what the market did? | lead |
| A-05 | Which account fields are hidden from agents? | lead |
| A-06 | Which rows wake a workflow: alarms only, or every trade? | lead |

### 4.7 UI

| Id | Question | Tag |
| --- | --- | --- |
| U-01 | Does the trading server live in Connections, Machines, or its own page? | lead |
| U-02 | What does the laptop panel say when nothing runs on a node yet? | lead |
| U-03 | Which few numbers go on a unit's preview? | operator |
| U-04 | Which words do phone alerts use? | lead |
| U-05 | Does he want a market heat map of spread and fees? | operator |

### 4.8 Security and keys

| Id | Question | Tag |
| --- | --- | --- |
| S-01 | Keep, reshape or overrule ruling 135 (options O1 to O8)? | operator |
| S-02 | Is a trade-only, no-withdraw key a live key for this rule? | operator |
| S-03 | How strong is a separate Windows account or VM against an agent shell running as him? | research (31) |
| S-04 | Which of his brokers offer account-level limits (size, daily loss)? | research (32) |
| S-05 | Is a small live canary account on the PC acceptable to him? | operator |
| S-06 | Can any agent-reachable key on the PC reach the trading server by SSH? | lead |
| S-07 | How do Hyperliquid API wallets work, and what can such a key do? | research (38) |

### 4.9 Wildcards

| Id | Question | Tag |
| --- | --- | --- |
| W-01 | Does cTrader run cloud-hosted cBots in Python, and could a unit live there? | research (38) |
| W-02 | What do brokers' free VPS offers require and run? | research (38) |
| W-03 | Can the Python stack and QMN run on a small ARM board? | fog |
| W-04 | Does hourly rental save anything once crypto trades 24/7? | lead |
| W-05 | Do nodes split by venue once there is more than one? | fog |

**Counts:** 71 questions. research 16, operator 14, lead 36, fog 5.

---

## 5. Cross-map: permutations of venue, data, execution and machine

Each row is one way a unit could trade live. Columns name the data route, the execution route, where it can be rehearsed, and where the live key would live under each 135 option. INFERRED rows built from the checked facts in §1; vendor details are `research`.

| Market | Data route | Execution route | Rehearse on PC | Live key: O1, O2 | Live key: O3, O4, O7 | Live key: O5 | Leans on |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FX and gold CFDs | cTrader quotes and depth | cTrader | Yes, demo host | Server | PC (O3, O7) or walled PC (O4) | Arm on server | B039, B052, B098 |
| Index CFDs, own data | cTrader quotes and depth (no tape) | cTrader | Yes, demo | Server | PC or walled PC | Arm | F7, B043 |
| Index CFDs, futures tape as signal | Vendor CME data | cTrader | Data yes; fills demo only | Server | PC or walled PC | Arm | B053, B054, B059 |
| Exchange futures | Futures broker or vendor | Rithmic, CQG, IBKR or Tradovate | Only if the route has a test environment (research 38) | Server | PC or walled PC | Arm | B042, L-01 |
| Hyperliquid perps (crypto and HIP-3 stocks, gold, FX) | Public websocket, no key | API wallet | Data yes; testnet if offered (research 38) | Server | PC or walled PC | Arm | B044, B026, S-07 |
| Crypto spot | Public CCXT and bulk files | Exchange API key | Sandbox where CCXT knows one (PR 224) | Server | PC or walled PC | Arm | B045, B061 |
| Stock CFDs at IC | MT5 terminal | MT5 (Windows only) | Yes, MT5 demo | Windows trading server | PC, against the ruling text's MT5 warning | Arm needs Windows | N-11 |

**Second map: themes against the 135 options.** A mark means the theme's ideas behave differently under that option.

| Theme | O1 | O2 | O3 | O4 | O5 | O6 | O7 | O8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Setup wizard (2.1) | x | x | | | x | x | | |
| PC first (2.2) | | x | x | x | x | | x | |
| Failure, stand-in (2.3) | x | x | x | x | x | x | | |
| Feeds and the lease (2.4) | | x | x | | x | | x | |
| Journals (2.6) | | x | | | x | | | |
| Keys (2.9) | x | x | x | x | x | x | x | x |

## 6. Clashes left open (from the party)

1. Is a VM or WSL2 on the PC a fair reading of "first run on my machine"? (N-02)
2. Is a trade-only key still a live key? (S-02)
3. Brain and arm, or a second machine on the trade path? (O5)
4. Who stands in when the only machine allowed to trade is down? (F-01)
5. Telemetry stack or plain tables as the journal's store of record? (J-01)
6. Is a server-held tick archive an extension of local first or a reversal of it? (L-06)
7. Demo rehearsal proves the code, not the live host. (O2)

## 7. Parked

| Item | Why parked |
| --- | --- |
| B102 live key only while the harness is stopped | Weak; one forgotten restart puts a live key next to an agent. |
| B108 units as cloud cBots | Hands the unit to the venue's runtime; the feed pool, guards and journals don't come along. Kept as a research question (W-01). |
| B109 broker free VPS | Usually Windows with MT5; odd for everything else. W-02 keeps the fact-check. |
| B110 broker data-centre region | Speed games were ruled out; only useful as a region default (B005). |
| B112 ARM home board | Fog until W-03. |
| B115 hourly rental | 24/7 crypto likely kills the saving (W-04). |
| Exit, stop and sizing rules on the node | The risk-and-sizing session owns them (`STATE.md:145`). |
| The book, correlation control, account guard plus pod | Risk-and-sizing session (`STATE.md:152`). |
| How the MIS reads ticks | The MIS expansion round, after research 37. |
| Reading the UI code | His rule: judge the design by running it (S13). |
| A name for the trading router | Vocabulary, his call (`STATE.md:227`). |

## 8. The five new ideas that matter most

1. **B106 brain and arm.** The only shape that runs the whole stack on his PC against live prices without a live key there, if the server also runs a full brain.
2. **B014 and B015, the node as one Linux image the PC also runs.** QMN cannot run on Windows today, so PC first fails for the node before anything else is built.
3. **B013 start the broker app approval on day one.** The one-click wizard has a wait inside it with no published length.
4. **B026 a venue dead man's switch.** Silence from the node cancels resting orders at the venue, where one exists.
5. **B105 the trading server must not share the PC's SSH path.** The shipped connect flow makes an SSH key on the PC; ruling 135 only holds if that key never reaches the trading server.

## 9. Not done

- No vendor fact was looked up. Every vendor claim beyond the cited research files is INFERRED and tagged `research`.
- The UI was not run; UI ideas rest on `UI-HANDOFF.md` and `UI-NOTES.md` text.
- Research 31, 32, 33 and 38 have not run; their answers may move every option in §3.
- `brainstorm.html` was written from the memlog by this agent, not a sub-agent (standing order 1 forbids sub-agents). Not checked visually.
