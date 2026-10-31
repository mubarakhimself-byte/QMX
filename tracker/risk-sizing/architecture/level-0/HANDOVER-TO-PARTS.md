# Handover to the Level 1 parts

Agent X0, 31 Oct 2026 (evening), after applying review R0 (`architecture/review/R0-level-0.md`) to Level 0. Read this first. Each line is one thing your spine must settle by name, with its source id: a review finding (R0-nn) or a catalogue case (`funnel/edge-cases/catalogue.md`). Where Level 0 already fixed the rule, the line names the AD or connection row that holds it, and your job is the design and the build slices under it. Where a line says "consumes", another part owns the shape and you match it.

Parts: **A** is QML, the dictionary, the unit template and its checker. **B** is QMB as a mini app, journals, workflow templates (and the judge, the Library's data, the slow-lane agent templates). **C** is the trading node as a mini app, the MIS, external connections, DevOps, clocks and networking (and the host's roles, the host route, the instrument, venue and account records).

**For every part (R0-11).** Your spine carries a table of every catalogue case your part owns: id, the handling in one line, the AD or section that holds it. R1 checks by script that every owned id is there with a non-empty handling. Ownership is in the Level 0 spine's part sections; the score in `versions.md` proves properties, not cases.

## A. QML, the dictionary, the unit template and its checker

| Source | Settle in your spine |
| --- | --- |
| R0-03 | Design layer G's behaviour report beside the unchanged `evaluate_layer2` verdict (AD-17): trade count or the unit's declared "may not trade on this slice", each exit kind fired or unfired, signal constant or not, a shuffled-day control; all warnings; its shape in the check result. B runs it in QMB's sandbox. Test: the dummy unit and three broken twins (always long, an exit that cannot fire, a constant signal); the verdict passes all four and the report names each fault (`blast-radius.md` item 3). |
| R0-07 | Design the one block loader (AD-47): its interface, the fingerprint check before compile, its error shape, the deployment's block folder layout, and how QMB, the node and the MIS app call it. Package data holds only QML's own blocks. |
| R0-12 | Build AD-17's door table: the catalog row, the template step and the hook run A to F; the Library save runs A to F; a QMB run and a node deploy look up a recorded G verdict by the exact compiled fingerprint. Say where the verdict is stored with the unit. |
| R0-14 | In the lifecycle machine, moving a unit from tested to paper is his click by default (AD-23). |
| R0-18 | Define the identity table as a core setting (AD-23): its name, its rows (Lab AD-16's designed rows plus the unit edit labels), and how each host hands it to QML as data. |
| R0-19 | QML's compiler refuses a read of another unit's live output (AD-2, QML-22). The socket's slot contracts take local inputs plus AD-2's optional read surfaces with a fallback (AD-24). |
| QML-04 | A streaming indicator updates in flat time; a test replays a week of ticks and shows no growth in time per update. |
| QML-13 | A learned block's weights arrive as a pinned file with a fingerprint through a declared read surface; a retrain inside declared bounds is a calibration (AD-47). |
| QML-17 | The unit document states each side; the checker refuses an implicit long and short mirror. |
| QML-18 | The entry price is the first price after the last required input became knowable; define it on `knowable_at` so QMB's fill model and the node use one rule (B consumes). |
| QML-19 | The runtime hands a unit closed bars only unless it declares tick input (AD-5); the same rule in QMB and the node. |
| QML-20 | A higher-timeframe value is knowable only at its bar's close in the venue's day boundary (AD-5). |
| QML-21 | Every combiner has an explicit "no signal" result; the checker refuses a combiner without one. |
| QML-22 | As R0-19: no live unit-to-unit read; composition at build time into one unit. |
| QML-25 | QML's first-run check names a wrong interpreter; each app bundle pins Python 3.14. |
| UT-01 | As R0-03. |
| UT-09 | Unit state carries the unit version and a state schema version; a mismatch starts from a declared cold state, logged. |
| UT-11 | The deployment records its warm-up source; a cross-source jump above a named setting is flagged at the seam. |
| OP-03 | The promotion card shows what changed against what is live (a diff of the unit documents and pinned blocks); UI note only. |
| AG-11 | The same problem set returned twice in a row counts as no progress, so the agent's checker loop stops and reports. |
| AG-15 | The check result leads with the counts and the refusals, so a spilled answer still shows the failing problems first. |

## B. QMB, journals, workflow templates, the judge and the Library's data

| Source | Settle in your spine |
| --- | --- |
| R0-01 | QMB homed on a server (capacity he adds) is asked through `app_op`'s `remote` path and AD-46's `apps.job`; declare each QMB operation's `state` and approval so that path works. |
| R0-06 | The writer library maps the node's in-process append store onto the Library's partition key and commits only closed partitions through the machine's market-data door, after the fact (AD-27); the host is never a step before a send. |
| R0-17 | Extend the existing `note` kind (agents' notes) and `paper-run` kind (a unit's paper lane per market) additively; add the test that the unit path never writes `bot` or `strategy`. Retirement of those two kinds waits for the PR that moves the registry migration and the tests that save them (`blast-radius.md` item 13). |
| R0-19 | Stamp world from the account the venue reader proved and the deployment's lane: `paper` for a unit's paper lane, `demo` for other demo-account work (AD-27); define both in the journal kinds. |
| QB-05 | The data card records stitching and roll dates; QMB replays futures contract by contract with the roll as an event. |
| QB-11 | A run records the model that built the unit and its training cutoff; QMB offers a window after the cutoff. |
| QB-15 | A result with zero trades is labelled as such, never a pass. |
| QB-16 | The synthetic generator takes the instrument record's class, not a forex-CFD default. |
| QB-17 | On a shared machine live paths have priority over research: QMB's Job object or container runs below the node's. |
| QB-21 | Bars are built from ticks in the venue's day boundary (AD-5). |
| QB-22 | What-if filters that can only worsen results stay views; ones that can improve results become counted reruns in the try ledger. |
| QB-23 | The nightly replay of each live day reads the quotes and bars the node recorded, pulled home by X3 (AD-5, AD-28); it compares decisions per unit. |
| MIS-10 | Every decision row carries the value, source and version of every reading the unit computed or read (AD-27); the unit journal kind holds them. |
| MIS-11 | Each judge proof states what it can and cannot fail on (for example the shuffled-readings proof cannot fail when units compute their own inputs). |
| JR-08 | The envelope's `backfilled` mark (AD-27); live statistics exclude backfilled rows unless asked. |
| JR-14 | Every artifact a tool writes lands in the Library as a draft or published item, never orphaned in a tool folder. |
| JR-15 | Trades without initial risk are flagged and never averaged in as zero R. |
| LD-03 | A per-file timestamp-unit check at import; the seam is written on the data card. |
| LD-04 | Cadence seams are recorded on the data card and named in any result that crosses one. |
| LD-11 | A backup never blocks a live writer; reads for backup go through a snapshot or a lower-priority reader. |
| LD-12 | A cross-source offset check keyed by the market id (AD-26); the market journal measures the gap. |
| AG-07 | Outside sources enter an agent step as marked data; numbers come only from tools. |
| AG-12 | Every number in an agent's output cites a tool receipt, checked by the receipts grader (AD-32). |
| WF-07 | Long work runs as a script step or a background job with a handle, never as an agent step waiting on a tool. |
| MA-03 | The mini-app examples and the first-party apps are built and tested in CI. |
| RS-13 | QMB and the journals record a gap through the stop as the loss it was, in R, never capped at 1R; the sizing answer is the risk session's. |

## C. The trading node, the MIS, external connections, DevOps, clocks and networking

| Source | Settle in your spine |
| --- | --- |
| R0-01 | Design AD-46's route first: `POST /api/host/forward`, the verbs `apps.ask`, `apps.job`, `heartbeats`, `data.list`, `data.fetch` field by field with `schema_version`; the one entry in the door's set (`qmx_host/door.py:166-179`); composing `AppOp` with its `Placements` at `qmx_engine/control_door.py:308`; the principal rule (`manage` answers only to `user`). The node's read operations keep instance state, which the manifest refuses as `read` (`qmx_apps/manifest.py:324-327`): declare them `domain_write`, or fix the core rule under ruling 46 with its reason. Recheck the X6 run-pass failure in the same packet. Tests: `blast-radius.md` items 10 and 11. |
| R0-02 | Confirm that This PC can open a server's OpenObserve over the tailnet (its bind and the firewall's `tailscale0` rule, engine AD-71) for X4; nothing connects into This PC (AD-44). |
| R0-04 | Build the node's own trading sign-in (AD-37): This PC's loopback receiver relays only the one-time code to the node app (over AD-46 for a server); the node exchanges it with its machine's trading registration (client id and secret named only in the `trading-node` manifest) and keeps and refreshes the pair in its own store (Credential Manager entries only the node writes on Windows; QMN's node secret store on Linux), under names no `connections` row references. The node accepts a live-capable grant only on a host in the trading profile. The host's refusal and its tests stay; reword the `LiveGrant` docstring, keep its message (tests compare it). This PC's two grants: the host's view-only grant under the read app, and the practice node's demo-only trade grant under the PC's own trading app. |
| R0-05 | Build per-order attribution in the start-up reconcile (new code; the kept organ compares quantities per account): the node's tag in the client order id, in cTrader's `label` (positions keep it) and in Hyperliquid's `cloid`; one node per account or subaccount on the account record; the install id and his same-node confirmation; his take-over click (AD-8, AD-38). Prove on demo that `label` survives onto the position and its length, and what cTrader does with a repeated client order id. |
| R0-06 | Keep the journal-before-dispatch write in the node's own append store, in process (AD-12, AD-27); B's writer library ships closed partitions. |
| R0-08 | Design X10 (updates): host builds through the step runner; app versions and models through the Library hub, installed on the server by his signed publish (node) or his enable (MIS); prove the INFERRED install-from-replica path or replace it. The Hyperliquid agent wallet step in setup from the venue's own documents (E8). |
| R0-09 | Wire the kept alert publisher (E11) and liveness ping (E12) on every trading machine; pick the default push service and watcher; the short named list; the setup cards that name the destinations. |
| R0-10 | Move every caller the scan found in the shell-cut wave (AD-36): the agent's node-state tool; the kill line's and the bench fold's calls into `qmn.paper.demotion`; the MIS register's call into `qmn.promotion.hub`. Give the kill line its labelled placeholder action (no new entries for that binding, a risk stop); run the stop-on-every-order test (TN-34) before and after. Keep `liveness.py` and `alerts.py` out of the deletion. |
| R0-13 | Build the install check: only the `trading-node` manifest may name the venue trading-grant secrets; on the Docker tier, an app's network allow-list names only its venues (AD-33). Replace the evidence word `proposal_only` for the node (LC-A0-18). |
| R0-14 | Build AD-38's stand-down table as settings with their starting defaults, and the two soak settings shown on the release and binding cards. |
| R0-15 | X2 reads latest values every heartbeat interval (`heartbeats` and `status`); guard events reach This PC by the pull (X3). |
| R0-16 | Build the trading profile as one derived check, not a role: a host that is home to a node holding a live-capable grant refuses chats and agent workflow steps; the setup step turns them off before a live binding (AD-45). |
| R0-19 | State the host process and its apps supervisor on the trading path (on This PC the Job object kills the node app when the host dies; on a server the host is a systemd service that always restarts; AD-2, LC-A0-06). Apply AD-6's overlap window to the cross-machine handshake and AD-46's verbs. Add the market id to the instrument record (AD-26, EX-06). |
| TN-04 | As R0-05: a copied disk or restored image refuses on its install id. |
| MA-02 | As R0-05: his take-over click adopts the dead node's tagged positions under protection. |
| TN-07 | An exchange halt or price limit is a market event every unit sees: no entries during it; the journal records it. |
| TN-15 | A sleep or power loss of This PC during practice is logged as a gap; the node reconciles on wake before entries (AD-38). |
| TN-23 | Protection follows the filled quantity on a partial fill; the unit sees the real position (AD-39). |
| TN-25 | A broker spec change is an event and a new record version; units on that symbol pause until his click on the change card (AD-26, AD-38). |
| TN-26 | A close-only switch is a market event: no entries, exits allowed (AD-26, AD-38). |
| TN-31 | Setup starts the cTrader trading-app request on day one and shows it as a waiting step (X8). |
| TN-32 | Setup measures the round trip to the broker and shows it on the passport (X8). |
| LD-13 | Dividend events per index CFD live on the instrument record and reach QMB's replay as cash events. |
| EX-01 | A spot event with one side keeps the last value of the other side. |
| EX-02 | The depth book is rebuilt after every reconnect before any unit reads it. |
| EX-06 | One market named across venues by the market id on each instrument record (AD-26). |
| EX-15 | A CFD and its future are recorded on one clock; the price gap is measured and stored. |
| EX-16 | The capability record states a venue's manual weekly login or its server ban; setup refuses an unattended node there. |
| CA-10 | The outside agent's observer token shows its expiry; renewals are his. |
| DO-03 | An early packet starts OpenObserve on real events from QMX, on This PC and on a server. |
| DO-04 | Each known monitoring gap (incidents not exported, the copy age, two absent log files, an unredacted outside note) is closed or listed. |
| CK-10 | Same-minute-of-week baselines run in venue session time; a short history after a DST change shows as thin. |
| CK-13 | Durations for 24/7 markets are in calendar time or closed trades, never "trading days". |
| OP-02 | The first real start on his own folder, with his sign-ins, is a named early step in the build plan. |
| OP-09 | The node and MIS screens say a market is shut and until when (from the calendars); UI note only. |
| RS-18 | Leverage and margin are versioned record fields; a change pauses that symbol's units like any spec change (AD-26, AD-38). |
