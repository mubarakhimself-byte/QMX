# The trading node: a server that sets itself up and lets units trade alone

**What this part is.** The one place orders are sent from. With one click it sets itself up on his PC or on a rented server, installs the MIS instance, checks that everything works, keeps the units he admitted trading on their own (feeds, protection at the broker, kill switches, reconcile, journals), heals itself when something goes down, and sends its results back to his PC. It is the second priority (ledger N-01) and comes late in the build order: QML, the MIS and the contracts first, then assembled into the node (STATE mid r35).

**Verdict: the second mini app.** A `money` mini app (`trading-node`) on the existing mini-app core, homed on This PC for practice or on a trading server for live. A money app cannot start without his signature, by code (G2 §5.1).

## His words

- "So a trading node needs a fresh refactor." (T3:1562) "We might delete a lot of code, in fact, a fresh start." (T3:1562) "97,000 lines is a big number, bro." (T3:1562)
- "something that should just be setting itself up on a server, setting up the MIS, and what everything the unit needs to trade autonomously" (T3:1562)
- "So that when we click a kill switch, it can automatically work." (T3:1562) "Literally, a mini app can have a server of its own." (T3:1562)
- "It's set for Linux because most VPSs that we're going to be using work with Linux." (T3:1096) "we can go with WSL, okay? If all goes south." (T3:1096) "I would prefer using Windows than sorting WSL" (T3:903)
- "a trading node should be as simple as how, for example, I can set up a server from a provider" (T2:1148) "is it going to start as server, then show me that the server has started?" (T3:1102)
- "if something is to run on external compute and external storage, it should first run on my machine" (T2:1148) "How are we going to be able to deploy units from my machine?" (T3:903)
- "We are literally trading 24/7, my days. This is why we need a trading node." (T2:325) "The trading node is a second tier." (T3:1264)

## 1. What exists today

| Part | State | Where checked |
| --- | --- | --- |
| QMN: 98,063 lines (85,136 code), built 31 Aug to 4 Oct by the old factory, untouched since except one caller move; never traded | BUILT, NEVER RUN | G4a §2.2 |
| Its only registered host profile is offline replay, so even a configured QMN refuses to compose a live root | BUILT (blocks live) | G3 §1.1 |
| Organs worth keeping: cTrader live client (records wire evidence before interpreting; never retries after hand-off), reconnect and gap replay, capability check at connect, venue-resident stop on every order, order pacer with a protection reserve, UNKNOWN per stream, reconcile with four verdicts, kill switch (five levels, escalate-only automatic, operator-only resume), kill line and breakeven ratchet, clock bands, one refresher per credential, liveness heartbeat, the loop driving QMB's `run_slice` unforked | BUILT, never run against a venue | G3 §1.1; G4a §2.2 |
| About 11,900 lines of proof campaigns, readiness packets and a QA matrix reached only by tests; a bench harness (2,291); its own Grafana, Loki, Prometheus stack (831 deploy lines) | BUILT | G4a §2.2 |
| Clashes with units: "bot never sizes" at the seat door; Book-level paper only (no per-unit paper, DEC-0261); seven boot values blank; a week-long soak gate; the machine pin; the MIS's consumers closed to the Book door and the kill switch | BUILT | G3 §5; G4a §2.2 |
| Linux-only pieces: supervision (`sd_notify`, systemd), the powers door (a Unix socket under `SO_PEERCRED`), the secret store (`systemd-creds`); its logic and 115 test files run on Windows in `just ci` | BUILT | G4a §2.2, §3 row 2 |
| The QMX host has no order code; an agent's order is a proposal "awaiting_operator_signature"; any cTrader grant that can trade a live account is refused on every QMX host | BUILT (ruling 135 in code) | G3 §1.6 |
| The connect dialog's step runner (his cards, then rerun-safe checked steps, one row last) with kinds storage, compute and deep logs; the server setup's firewall with a five-minute undo, Tailscale-only bind, `qmx-recover`, proven on his real server | BUILT; no trading-server kind | G3 §1.4; G4a §3 row 12 |
| His cTrader app "QMX-NODE" has QMX's return address registered and may trade | venue fact | G4a §2.3 |
| His PC: WSL2 Ubuntu 24.04 with systemd; its clock not synchronised; it shuts down when idle; its disk on C: | measured 30 Oct | research 31 §6 (via G3 §1.2) |
| Mini-app core: operations are the only way in; an instance has one home machine; `app_op` asks a remote home; Job object on Windows, Docker elsewhere; the breaker logs and stops after `max_errors`; a `money` app needs his signature to start; the supervisor has a `restart` operation but no automatic back-off | BUILT | G4b Q5; read this session: `qmx-apps/src/qmx_apps/supervisor.py` (`restart` at :863, `breaker_open` at :828) |

## 2. Fresh start or refactor, weighed on the facts (his ruling 27)

| Area of QMN | Lines (code) | Verdict | Reason |
| --- | --- | --- | --- |
| `venue` (cTrader client, reconnect, capability check) | 7,478 | **keep as an organ** | the hard part of trading with cTrader, already written to the right laws |
| `order` (command identity, pacer, UNKNOWN) | 5,178 | **keep**, except the sizing seam | the size now comes from the unit's sizer |
| `reconcile` | 1,207 | **keep** | broker wins after a crash |
| `protection` (kill switch, windows, dead zones) | 3,150 | **keep**; effect-matrix values are placeholders for the risk session | the guards that work without the PC |
| `capital` (kill line, ratchet) | 1,168 | **keep the code; its use is the risk session's** | the kill line flattens, while standing order 7 says a risk rule "stops"; a line for the risk socket (G3 trap 11) |
| `time` (clock bands, calendars) | 1,181 | **keep**; calendars extend beyond forex | |
| `loop` (one loop per venue and account, over QMB's `run_slice`) | 1,349 | **keep** | the same code in backtest and live |
| `ledger` (virtual ledger per Book binding) | 5,516 | **keep the ledger, rekey it per unit** | one virtual position per unit on a netting account |
| `secrets` | 921 | **keep the one-refresher rule; replace the store** | the store is `systemd-creds`; the host's own stores work on both systems |
| `observability` | 2,488 | **keep the liveness heartbeat; drop the rest** | logs go to OpenObserve |
| `data` (live intake, history bootstrap, news calendar, sealed sync) | 7,160 | **keep the intake and bootstrap; replace the sync with the journal shipping job; park the news calendar** | news is out for now |
| `host` (composition root, boot ceremony, supervision, proof machinery) | 26,602 | **replace** with the new shell; delete the ~11,900 lines of proof campaigns | the shell is the mini app |
| `seats`, `promotion`, `paper` (Book level) | 9,782 | **replace** with deploy, his click and per-unit paper | built around "the bot never sizes" and the Book |
| `mis` | 12,654 | **move** the labelers into the catalogue (`mis.md`) | units, QMB and the MIS must run the same code |
| `doors` | 2,014 | **replace** with the app's operations | the Unix-socket powers door is Linux-only |
| `replay` (a recorded day as a decision diff) | 3,521 | **keep for debugging, off the trade path** | useful, not needed to trade |
| `bench` | 2,291 | **delete** | not needed to trade |
| `config` (registry, boot values) | 3,605 | **keep the shape; give the seven boot values starting defaults** (§10) | blank values block boot |
| deploy recipes and the Grafana stack | 6,353 deploy lines | **delete** | the connect dialog and OpenObserve replace them |

**Recommendation: keep the organs, replace the shell** (S102, S103). A small new node package is the shell; the kept organs are imported as libraries (`qmf-venue` laws, the venue client, pacer, reconcile, kill switch, clock bands, the loop). The old host, seats, promotion, Book paper, doors, deploy recipes, bench and Grafana stack are deleted in the same wave once the new shell trades on demo (poteto-mode's migrate-callers-then-delete principle: no compatibility layer, since nothing outside tests calls them). Which four `host` modules are dead and which are only re-exported (`runtime_risk_gate`, `fencing`, `lineage_persist`, `registry_mint`) needs a builder's blast-radius run (G4a §2.2). This is the fresh start he asked for, without rewriting the parts that are already right.

## 3. Where it lives: the shapes

### Shape A. A money mini app on the QMX host, homed on This PC or a trading server (recommended)

- **What.** The node shell is a mini app with risk `money`. On This PC it runs under the host's apps supervisor with a Job object (Windows native, no WSL). On a trading server the same app runs under the server's QMX host in a **trading profile**: the apps supervisor, the node app, the MIS instance, a Library cache and telemetry, and no chats and no agent workflow steps.
- **What it removes** (insight I2): QMN's three Linux-only pieces. Supervision becomes the apps supervisor plus the node's own inner supervisor; the powers door becomes the app's operations with approvals; the secret store becomes the host's own (Windows Credential Manager on the PC, an owner-only vault file on a server).
- **Reuses.** The mini-app core (operations, homes, `app_op` with `remote`, health logs, the signature gate for money apps); the connect dialog's step runner and the proven server hardening; the host's cross-machine streams and heartbeat ("server unreachable since ..."); OpenObserve; the cTrader sign-in flow (its code "does not depend on where it runs").
- **Hard cases.** PC off for a week (the server trades alone); the host on the server restarts (protection is at the broker, the node reconciles first, the host updates only on his click when the node says it is safe, §7); a crash loop (the inner supervisor stands down alive); two machines on one grant (each trading machine gets its own cTrader app).
- **Explain.** "The trading node is an app inside QMX. On your PC it trades practice accounts; on a rented server it trades live. It is the only thing in QMX that can send an order, and it cannot start without your signature."

### Shape B. QMN refactored as its own Linux program (systemd, Unix-socket door), the PC through WSL

- **What.** Today's design plus the owed single-machine variant (DEC-0262).
- **Hard cases.** Strong isolation from the host.
- **Maintain.** Two stacks: QMN's own paths, credential store, supervision and monitoring beside the host's; the PC-side halves (SSH tunnel, pull, hub push, provisioning wizard) do not exist (G3 §1.3).
- **Why not.** It keeps the three Linux-only pieces he would rather not manage on his PC ("I would prefer using Windows than sorting WSL") and builds a second install, a second monitoring path and a second secret store.

### Shape C. A built-in trading role inside the QMX host, not packaged as a mini app

- **What.** Research 43's "one image, two places": QMN's organs move into the host as packages behind a role switch.
- **Why not.** It is Shape A without the mini-app core's signature gate, operations and health logging, and it ignores his preference for the node as a mini app (STATE mid r43).

**Pick: Shape A.** Party P11 left one clash open: Vex wants the node outside the host on the server so a host crash never touches trading. The pick answers it inside Shape A: the node's inner supervisor owns the trading loop, the host on the server is a systemd service that always restarts, and updates are his click when the node is safe. Lead's call; how to undo: run the node app's process as its own systemd service that the host adopts instead of starts.

## 4. The node app

**Operations** (the only way in; JSON Schema inputs and outputs in `app.toml`):

| Operation | Does | Who may call |
| --- | --- | --- |
| `status`, `units`, `positions`, `journal_tail`, `passport` | read state | anyone, agents included (read) |
| `self_test` | runs the self-test (§6) on demo | anyone (reversible) |
| `deploy` | installs a unit version on markets and an account, practice or live | his click; live needs his signature |
| `pause`, `resume` (per unit, per market) | stop new entries; resume | his click (resume only his, like the kill switch's resume) |
| `kill` (level, scope) | escalate the kill switch | his click; automatic escalation happens inside by risk rules |
| `flatten` (scope) | close positions | his click |
| `mode` (per account: practice or live) | switch | his signature |

**No operation places an order** (S109). Orders come only from units running inside the node.

**Provides:** `node_state` (one word plus reasons, `stale_after` 120 s), `unit_states`, `heartbeat`. **Feeds:** the MIS board (optional, with `stale_after`), instrument-record updates, deployments.

**Its volume holds the desired state** (S107): the deployed units (compiled documents, calibrated values), their markets and accounts, the mode, the instrument snapshots, the journals waiting to ship. On start it converges to that state.

## 5. Placements and keys (ruling 135, handled technically)

| Placement | What it trades | Which grant it holds | Notes |
| --- | --- | --- | --- |
| This PC, practice (the default, first) | demo accounts | a cTrader grant that lists only demo accounts (allowed on the PC today, G3 §1.6 item 3), plus the PC's own view-only live grant for shadow runs on live prices | Windows native; recordings and journals on D: |
| Trading server (a rented Linux VPS), live | the accounts he switched to live | the live trading grant, stored by the node app in the server's vault, only on a machine whose place he marked "trading server" | the server's host runs the trading profile: no chats, no agent steps, so agents never work where a live key lives |
| WSL on his PC | demo | as This PC | the fallback "if all goes south" (N-03); not needed under Shape A |

Every other QMX host keeps refusing live-capable grants exactly as today. One cTrader app per trading machine, because a token refresh logs out every other holder of the same grant (G3 trap 4). Hyperliquid's trading key is an agent wallet per trading process: trade only, cannot withdraw, expires within 180 days (`external.md` §4).

## 6. Setup, and a newcomer starting a node (weak spot 9)

**The connect dialog gains one kind, "Trading node"**, on the shipped step runner (S081, S082):

1. **Card 1, "Start a trading node on This PC (practice)".** It starts the cTrader app registration at once (Spotware approves each app, reported at about a day, research 38 §3.1) and opens the cTrader demo sign-in in his browser.
2. **Checked steps, safe to rerun:** install and enable the node app (his signature as the money gate); install the MIS instance; check the clock (Windows Time running, offset reported); pull instrument records for the demo account's markets; deploy the dummy unit to the demo account (it ships installed, S088).
3. **Self-test, landing a passport** (research 43 §3.6): broker connection, feed freshness, a demo test trade with a protective stop placed and closed (S089), kill-switch latency, clock skew, disk, the image digest. One row written last.
4. **His screen shows one word: running** (S083), with the reason one click away.

**"Trading server" later, in the same dialog:** his cards (pick a provider, the address, a one-off Tailscale key, the server password typed into the terminal QMX opens, the firewall approval), then the same checked steps on the server, including the shipped firewall with its five-minute undo and `qmx-recover`, the trading profile, chrony with several sources, the live sign-in on that machine, the same self-test, and the passport.

**Deploying a unit** (S084): one button on the unit page; pick markets, account, practice or live; live needs his signature. The node pulls the compiled unit, its calibrated values and the instrument snapshots into its volume, so it never needs the Library to trade.

## 7. Self-healing: what heals what

| Situation | What happens | Logged as |
| --- | --- | --- |
| Start or restart | reconcile with the broker first (broker wins), rebuild positions, restore calibration from calibration rows, re-place any missing protection, resume feeds, then allow entries | node journal |
| Trading loop crashes | the inner supervisor restarts it with back-off; after `crash_loop_k` restarts in `crash_loop_t` it stands down alive: heartbeat on, no new entries, protection at the broker (S099) | node journal, alert |
| App process dies | the apps supervisor's breaker logs it; on the server the host is a systemd service that always restarts and re-enables the node app on boot | supervisor log, alert |
| Host update on the server | only on his click, and only when the node reports safe-to-restart (no pending orders, every position protected at the broker); the restart gap is a named budget (S092) | node journal |
| Feed stale | no new entries; existing protection stays; a guard row (S093) | unit and node journals |
| Clock past the halt band | no new entries; past warn, rows flagged (S094) | node journal |
| Disk filling | tick recording stops first; journals last (S098) | node journal |
| PC unreachable | nothing changes on the trade path; journals queue locally (S095) | node journal |
| Server dead | an off-server liveness watcher alerts on the missing heartbeat; the broker's own app is his fallback for flattening, written on the node's page (S100) | watcher alert |

"Desired state it keeps returning to" (STATE mid r35) is the volume's deployment list; health checks run every minute; restarts back off; the watchdog is the heartbeat.

## 8. The order path and the kill switch

**Path:** unit intent (entry with a size from the unit's sizer slot, or an exit) → local guards (kill-switch level, clock band, feed freshness, spread against the unit's cost target, windows) → CT-19 command with the client order id as the trade's trace id → venue client → CT-20 events recorded verbatim → reconcile → unit journal. Protection is placed with the order where the venue allows it, because cTrader has no cancel-on-disconnect (G3 trap 3); on Hyperliquid protection is a trigger order re-placed after any cancel (S097). Before any resend, the node reads open orders and positions by the client id and resends only if absent (research 43 §3.6).

**Per-unit paper** (S110): a paper lane per unit per market on demo accounts replaces Book-level paper (DEC-0261 is lifted for units; a named conflict, research 43 §4).

**The kill switch** (STATE mid r27): five levels, escalate-only by itself. Automatic escalation is a risk rule inside the node, logged; nothing needs the PC. His kill is a node operation he can click from any QMX screen that reaches the server. Resume is only his. The effect-matrix values (what each level does) are blank in code and are the risk session's; placeholders now (`00-index.md`, "For the risk session").

## 9. Results back to his PC, and monitoring

- Journals and the node's MIS partitions ship one way to the PC's Library when it is reachable (`journals.md` §5).
- Heartbeats, node state and guard events reach the PC's merged inbox through the host's held stream per reachable node ("server unreachable since ..." with the last values, G2 §6).
- Operational logs go to OpenObserve through the one telemetry switch (`devops-and-clocks.md`).
- A watcher workflow reads heartbeats, journals and guard rows over time and proposes; it never presses anything (S138; `workflows.md`).

## 10. Numbers (starting defaults, all editable)

| Number | Default | Why |
| --- | --- | --- |
| `max_slice_latency` | 500 ms | research 43 §5 (half the 1,000 ms signal-to-send budget for a 1-minute unit) |
| signal-to-send budget for a 1-minute unit | 1,000 ms | research 43 §5 |
| `crash_loop_k`, `crash_loop_t` | 5 restarts in 10 minutes | INFERRED; enough to ride out a flapping feed |
| `drain_window` | 30 s | INFERRED; time to finish in-flight commands before a planned stop |
| `watchdog_interval` | 10 s | the mini-app heartbeat default (G2 §5.1) |
| `submission_deadline` | 2 s | INFERRED; above the measured ~160 ms handshake to cTrader (research 31 §3) |
| `local_queue_bound` | 10,000 events | INFERRED; minutes of a busy feed |
| `accumulator_bound` | one session of bars per stream | INFERRED |
| restart gap budget for a host update | 60 s | INFERRED |
| venue acknowledgement warning | 3 times the measured median round trip per venue and machine | research 43 §5 |
| twin run before first live | 5 trading days for session markets; 5 calendar days or 50 closed trades, whichever is later, for 24/7 markets | research 43 §5 |
| PC soak before a node release; soak before any live binding | 24 hours; 1 week on demo | both kept as named numbers (party P12 clash): research 43 §5 and the node spine |
| drills (power cut, token refresh, resend) | monthly, on demo | research 43 §5 |
| heartbeat interval per node | 60 s | research 54 §4.3 |

## 11. Connection points

| From | To | What crosses | Door |
| --- | --- | --- | --- |
| His unit page | node app | a deployment (unit version, markets, account, mode) | `deploy` |
| Node | Library (QML catalogue snapshot, instrument records) | compiled unit, calibrated values, snapshots | pulled into the volume on deploy |
| Node | venue | CT-19 commands; CT-20 events | venue-client port (`external.md`) |
| Node | feed keeper | quotes, depth, prints for its markets | inside the node |
| Node | journals | unit, node and market journal rows | the writer library |
| Node | PC | journals and MIS partitions, one way; heartbeats and state | shipping job; the host's held stream |
| Agents | node | reads only; proposals | read operations; the proposal card |
| Risk session | node | kill-switch effect values, the sizer and exits behind the socket | placeholders now |

## 12. UI needs (notes for the UI agent, no UI code)

- The node page: one word (running, paused, stopped, unreachable) with the reason; its machine and zone; the clock band; the passport; units with their state per market; positions with protection shown; the kill switch levels and a resume that only he can press; the broker fallback written plainly.
- The deploy dialog on the unit page: markets, account, practice or live, the placeholders still in the unit, his signature for live.
- The connect dialog's "Trading node" kind: the cards and the checked steps as a list that ticks.

## 13. Open for the architecture step

1. Whether the inner supervisor reuses QMN's `_supervision` crash-loop fold as is.
2. The safe-to-restart rule's exact test.
3. Which `host` modules are dead (blast-radius run).
4. A provider and region study for the trading server by network distance to IC's and Spotware's servers (research 43 §3.6, not researched).

## 14. Parked

- A passive second trading server (not yet, research 43 decision 1's smaller question).
- Brain and arm split beyond Hyperliquid's agent wallets.
- MT5 as a live venue (needs a Windows trading host).
