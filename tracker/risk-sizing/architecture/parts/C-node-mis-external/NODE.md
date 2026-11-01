# The trading node

Part C, area 1. The node is the `trading-node` mini app (risk `money`): the only place an order is sent from. Rules: spine AD-301 to AD-309, AD-315 to AD-317, AD-323, AD-324, under Level 0 AD-2, AD-3, AD-8, AD-12, AD-13, AD-36 to AD-39, AD-45, AD-46. Shapes: `CONTRACTS.md` §2 to §5.

His words this answers: "So that when we click a kill switch, it can automatically work." (T3:1562); "something that should just be setting itself up on a server, setting up the MIS, and what everything the unit needs to trade autonomously" (T3:1562); "is it going to start as server, then show me that the server has started?" (T3:1102); "We are literally trading 24/7, my days. This is why we need a trading node." (T2:325).

**Verdict: a mini app on the core.** Reason: the core gives it what a trading server needs for free (one supervised process, a home machine, operations as the only door, health logs, his signature per version) and his preference is a node app (STATE midday ruling 43). The organs it runs are core libraries.

## 1. What exists

| Piece | State | Where (CHECKED unless marked) |
| --- | --- | --- |
| QMN, 98,063 lines, never traded | BUILT, NEVER RUN | G4a §2.2 |
| Organs: venue laws, cTrader client, reconnect, capability check, pacer, UNKNOWN, reconcile, protection gate, kill switch (five levels, escalate-only), kill line, clock bands, loop over `run_slice`, ledger, liveness, alerts | BUILT | `packages/qmf-venue`; `qmn/src/qmn/{venue,order,reconcile,protection,capital,time,loop,ledger}`; `observability/liveness.py`, `alerts.py` |
| Live host profile | MISSING (only offline replay is registered) | `qmn/src/qmn/host/configured_live_resources.py:38-58` |
| Mini-app core: manifest, supervisor, breaker, money gate, homes, Job object | BUILT | `qmx_apps/manifest.py`, `supervisor.py` |
| A supervised app may write only inside its volume | BUILT | `qmx_apps/bootstrap.py:93-100`, `:117-145` |
| Tool exceptions count toward the breaker; default trips at 3 and kills the process | BUILT | `supervisor.py:884-934`, `:815-832`; `BLAST-RADIUS.md` C2 |
| A call is cancelled after 20 s inside and the app is stopped after 30 s outside | BUILT | `supervisor.py:897`, `:957-963` |
| An instance operation cannot be declared `read` | BUILT | `manifest.py:324-327`; `BLAST-RADIUS.md` C4 |
| A `state = "none"` operation starts the app on the caller's machine | BUILT | `qmx_engine/nodes/app_op.py:121-145`; `BLAST-RADIUS.md` C3 |
| A declared manifest secret that is missing stops the start | BUILT | `supervisor.py:598-632`; `BLAST-RADIUS.md` C8 |
| The connect dialog's step runner; storage, compute and deep-logs kinds | BUILT, no trading-node kind | `qmx_host/connect.py:374-389` |
| Shipped server unit rewritten to role `server` by setup | BUILT | `qmx_control/node.py:488-509` |

## 2. Refactor, fresh start, or keep the organs (exhausting the design space)

Three real shapes, judged on his three tests (hard cases, maintainable, explainable).

| Shape | Hard cases | Maintain | Explain | Verdict |
| --- | --- | --- | --- | --- |
| A. Refactor QMN in place: keep its host, boot ceremony, seats and doors; port supervision and the powers door to Windows | keeps proven laws; keeps "bot never sizes", Book paper, the systemd-bound supervision and the 11,900 lines of proof machinery he rejected | two stacks forever (QMN's and the mini-app core's) | "the old node, patched" | rejected: carries what blocks units and his PC |
| B. Keep the organs, write a new thin shell inside the mini app | the hard parts (wire, reconcile, UNKNOWN, protection, clock bands) are kept and already tested in `just ci` on Windows | one supervision path, one store, one monitoring path | "the parts that trade stay; the box around them is new" | **picked** (Level 0 AD-36) |
| C. Fully fresh node on `qmf-venue` laws only | rewrites 7,478 lines of cTrader client, reconcile and protection that are already lawful; new bugs where none were | small at first, then the same size | "a new node from scratch" | rejected: rewriting the right parts |

Kept, by line count (G4a §2.2): venue 7,478, order 5,178, ledger 5,516, protection 3,150, reconcile 1,207, capital 1,168, time 1,181, loop 1,349, config shape 3,605, intake and bootstrap from data, liveness and alerts from observability, the rotation rule from secrets: about 40,000 lines. Moved, not deleted: `mis` (12,654) into `packages/qmf-readings`. Deleted in the cut (AD-323): host 26,602, seats, promotion and paper 9,782, doors 2,014, bench 2,291, the rest of observability, deploy recipes and the Grafana stack (6,353 deploy lines): about 47,000 lines. The new shell is INFERRED at 3,000 to 5,000 lines.

**The process inside the app: three shapes.**

| Shape | Stuck loop | Crash | Moving parts | Verdict |
| --- | --- | --- | --- | --- |
| P1. One process: MCP server thread plus runtime thread, joined by a store and a queue | the runtime's watchdog exits the process; the supervisor restarts it | an exception restarts the runtime thread; a hard crash restarts the app | fewest | **picked** (AD-301) |
| P2. The MCP server spawns the runtime as a child process | the server kills and restarts the child | the child dies alone | child management, pipes, signals on Windows | rejected: more code for what P1 gets from the core's restart |
| P3. The runtime as its own mini app, the operations in another | apps cannot stream to each other (engine AD-64) | | two apps to sign and supervise | rejected |

## 3. The manifest

```toml
id = "trading-node"
name = "Trading node"
version = "0.1.0"
risk = "money"
kind = "headless"
startup_timeout_seconds = 90

[entrypoints]
mcp = "server.py"

[capabilities]
secrets = { NODE_KEYS = "qmx/trading-node-keys" }
network = ["live.ctraderapi.com", "demo.ctraderapi.com", "api.hyperliquid.xyz", "api.hyperliquid-testnet.xyz", "ntfy.sh", "hc-ping.com"]

[breaker]
max_errors = 1000
heartbeat_timeout = 30
restart = "backoff"            # the AD-315 core fix; off by default for other apps
# no [entrypoints] jobs: the route refuses agents a money app's job anyway, and a test pins none

[operations.status]            # every operation: state = "instance"
state = "instance"
approval = "domain_write"      # a read; the manifest refuses instance reads
reversibility = "none"
# units, positions, journal_tail, passport, deployments: the same

[operations.deploy]
state = "instance"
approval = "manage"
reversibility = "compensable"
# withdraw, pause, resume, kill, flatten, bind, confirm_same_node, take_over,
# sign_in_begin, sign_in_code, self_test, rotate_keys: manage

[provides.node_state]
stale_after = 120
[provides.unit_states]
stale_after = 120
```

The network list is for the Docker tier's allow-list; on the default tier it is recorded, not enforced (`supervisor.py:695-705`).

## 4. The store, the reconciler and what each operation does

The volume store is `data/node.sqlite`, two owned tables (spine AD-301):

| Table | Writer | Holds |
| --- | --- | --- |
| `desired` | operation handlers only | one row per change: op id, kind, arguments, caller principal, at; never edited |
| `observed` | the runtime only | latest values (state word, reasons, per-unit and per-market states, positions, protection seen, clock band, venue sessions, safe-to-restart) and an append-only event list |
| `identity` | first start only | install id, machine fingerprint, minted at; then his confirmations |

Handlers write `desired` in arrival order. A change whose `issued_at` is older than the newest change applied for the same scope answers `superseded`; `kill` and `flatten` always apply (spine AD-303). The reconciler folds `desired` into the target (deployments, bindings, pauses, kill level, keys version), compares it with `observed`, and acts in a fixed order on every wake and tick: kill and pause first, then protection repair, then bindings, then deployments, then unpauses. Every action is idempotent: it checks what is in place before it acts (principle-make-operations-idempotent).

| Operation | Writes | Answers |
| --- | --- | --- |
| `status` | nothing | node state word, reasons, identity, clock, venue sessions, units summary, `safe_to_restart` with reasons, contract versions |
| `units`, `positions`, `deployments`, `passport` | nothing | the observed rows |
| `journal_tail` | nothing | the newest node and unit journal rows after a sequence, at most `tail_rows` (default 500) per call, read with Part B's committed reader so a line the runtime is still writing is never cut |
| `deploy` | a deployment change | `accepted` and the deployment id; compile happens after (AD-317) |
| `withdraw` | stop new entries for the deployment; remove it when flat | `accepted` |
| `pause`, `resume` | per unit, market, account or all | `accepted`; `resume` first lists the open causes (OP-10) |
| `kill` | escalate the kill switch at a scope; escalate-only | the level now in force |
| `flatten` | close positions at a scope | `accepted`; fills arrive as events |
| `bind` | add or remove an account binding; world comes from the venue's proof | `accepted`, or a refusal naming the missing grant or trading profile |
| `confirm_same_node`, `take_over` | identity decisions (§8) | `accepted` |
| `sign_in_begin`, `sign_in_code` | the grant (§10) | a consent link; then `ok` and the accounts the grant lists |
| `self_test` | a self-test run on a demo binding | `accepted`; the passport lands when done |
| `rotate_keys` | re-read `NODE_KEYS` at the next safe point | `accepted` |

## 5. Market events and stand-downs

The stand-down table is Level 0 AD-38's, inherited as is (stale feed, clock band, disk, venue not ready, repeated fault, spec change, risk stop), each clearing as that table says. Market events every unit sees, from the venue and the calendars: market shut (calendar), exchange halt or price limit (a futures route's status, or a venue error class mapped to it), close-only switch (cTrader trading-mode change), maintenance window (venue record calendar), delisting. During any of them: no new entries, exits allowed, a journal row with the event. The node's `status` names each with "until when" from the calendar when it is known (OP-09). A risk stop is also the unit's `lifecycle` event (Part A's body, `by: {kind: risk_rule}`), written through Part B's writer; the node's own starts and stops are `node_lifecycle` rows (R1-B-06).

## 6. The order path per venue

Level 0 AD-39's chain, with the venue's own protection rule (spine AD-308):

1. Unit intent, CT-23 format 3 (Part A), carrying the size.
2. Local guards: kill level, clock band, feed freshness, spread against the unit's cost target, windows, market events.
3. The cross-unit hook (placeholder: passes every order).
4. The protection gate proves the venue's stop form for the order type, or refuses before submission.
5. A CT-19 command: client order id `q<tag>-<ULID>`; on cTrader also `label` `qmx:<tag>:<unit tag>`; on Hyperliquid the `cloid` built from the tag and the ULID.
6. Journal before dispatch, in process, into the node's append store (`qmn/src/qmn/journal_dispatch.py`, kept); a failed write blocks the order, never a stop or an exit.
7. The venue client; CT-20 events recorded before they are interpreted; reconcile.

**UNKNOWN and resend (TN-01).** An outcome past `submission_deadline` (default 2 s) is UNKNOWN for that stream: no further entry on the stream until it resolves. Before any resend the node reads open orders by client order id and positions by tag; it resends only when both prove absent. The drill loses the answer to a send and proves one position: on the conformance venue in slice C-12b, on demo in slice C-15.

**Typed rejections (TN-24).** A rejection the error map knows (stop too close, market closed, not enough margin) reaches the unit as a typed refusal; the unit's declared back-off applies (default: no new attempt on that market until the next bar). An unmapped code is UNKNOWN plus an alarm.

**cTrader.** Market and limit entries carry `relativeStopLoss` (`encode.py:617-621`); absolute `stopLoss` is refused by cTrader for market orders (help.ctrader.com/open-api/messages, CHECKED). Protection amendments go through `amend_protection` (risk-non-increasing, `commands.py:600-616`).

**Hyperliquid.** The entry first; on each fill event a reduce-only trigger `tpsl = "sl"`, `isMarket = true`, grouping `positionTpsl`, size the whole position, so it follows partial fills (TN-23). Triggers fire on mark price, which the venue record states as the trigger basis. Not confirmed after `protect_retry_max` attempts: a reduce-only close of that position, labelled a placeholder, and a protection-escalation alarm.

## 7. Healing, sleep and disk

| Situation | What happens | Logged as |
| --- | --- | --- |
| Start or restart | identity check, reconcile with the venue (venue wins), rebuild positions, restore calibration, re-place missing protection, warm up, then entries; a slice re-run after a crash writes no double rows, because Part B's record id for decision, calibration and state rows is Part A's row id | node journal |
| Runtime exception | inner supervisor restarts the thread with back-off; the crash-loop fold stands down alive past 5 in 10 minutes | node journal, alarm on stand-down |
| Runtime stuck past `stuck_after_s` | the process exits with `runtime_stuck`; the supervisor's opt-in restart brings it back | supervisor log, node journal |
| Breaker trip or process death | the supervisor restarts the active signed version with back-off (5 s doubling to 300 s) | supervisor log |
| This PC sleeps or loses power (practice) | on wake the node logs the gap from its last observed write and reconciles before any entry (TN-15) | node journal |
| Disk below `journal_guard_bytes` (default 2 GB) plus margin | tick recording stops first, then bar recording; journals last; entries stop only when the journal cannot be written; exits always go (TN-18) | node journal, alarm |
| Host on the server restarts | the node app restarts with it (systemd restarts the host; the supervisor restarts the app) and reconciles first | both logs |
| His PC unreachable | nothing changes on the node; journals queue in the append store | node journal |

## 8. Identity, tags and taking over

- First start mints the install id and records the machine fingerprint (spine AD-305). The tag is its first 8 base-32 characters.
- Every start compares the machine fingerprint. A mismatch means the volume moved or was copied: the node refuses all trading and shows a card with two choices. A Linux grant never travels with the volume (spine AD-306), so after either choice he signs in again. "This is the same node, moved" (`confirm_same_node`) re-binds the identity to this machine; the account records' owner field follows. "Take over a dead node" (`take_over`, with the old tag) first needs his word that the old node is gone and its heartbeat absent for `takeover_quiet_s` (default 600).
- A take-over adopts positions and orders tagged with the old tag, under protection, and the account record names the new owner. This PC then re-issues the dead node's deployments for the new identity, from its own record of them.
- A live twin (same identity, both running) shows as activity tagged with my tag that my journal does not hold. The node stands down entries on that account and raises an alarm; the twin does the same.
- cTrader: positions keep `label` on their trade data (`ProtoOATradeData`, R0's read of `openapi-91.pb`). Whether `label` survives every path (partial close, amend) and what cTrader does with a repeated client order id are proven on demo in slice C-15; until then the design never relies on cTrader refusing a duplicate.
- Hyperliquid: positions carry no tag, so one node per subaccount, recorded on the account record; orders carry `cloid`.

## 9. Settings with their starting defaults

| Setting | Default | Origin |
| --- | --- | --- |
| `reconcile_tick_ms` | 200 | INFERRED: five looks a second, cheap |
| `op_answer_budget_ms` | 2,000 | under the supervisor's 20 s inner call timeout by ten times |
| `stuck_after_s` | 30 | INFERRED: thirty 1-second slices with no progress |
| `inner_backoff_s` | 1, doubling to 60 | INFERRED |
| `crash_loop_k`, `crash_loop_t` | 5 in 10 minutes | `funnel/solutions/node.md` §10 |
| `restart_backoff_s` (supervisor) | 5, doubling to 300 | INFERRED |
| `submission_deadline` | 2 s | above the measured 160 ms handshake (research 31 §3) |
| `max_slice_latency` | 500 ms | research 31 §3.3 |
| `local_queue_bound` | 10,000 events | `node.md` §10 |
| `accumulator_bound` | one session of bars per stream | `node.md` §10 |
| `drain_window` | 30 s | `node.md` §10 |
| `watchdog_interval` | 10 s | the mini-app heartbeat default |
| `protect_confirm_ms`, `protect_retry_max` | 2,000, 3 | INFERRED |
| `open_orders_margin` (Hyperliquid) | 900 | `external.md` §8 |
| `journal_guard_bytes` | 2 GB plus a 1 GB margin | INFERRED from research 12 volumes |
| `takeover_quiet_s` | 600 | INFERRED: ten missed heartbeats |
| `tail_rows` | 500 | INFERRED |
| soak shown before a release, before a live binding | 24 h, 1 week on demo | Level 0 AD-38 (shown, never enforced) |

Seven of these were QMN's blank boot values (`submission_deadline`, `accumulator_bound`, `max_slice_latency`, `local_queue_bound`, the crash-loop pair, `drain_window`, `watchdog_interval`); each now ships its default (TN-10).

## 10. Keys, sign-in, the trading profile and the evidence word

- `NODE_KEYS` (`qmx/trading-node-keys`): JSON, `schema_version`, per venue `{registration | agent_wallets}`, `alarms {ntfy_topic_url, healthchecks_ping_url}`. On This PC it is a Credential Manager entry written through the host's key route (`SECRET_INTAKE`, `qmx_host/door.py:85`, `:228`, user only). On a server it is the owner-only file `<home>/vault/trading-node-keys`, written in the server's own terminal window during setup, never through This PC (Level 0 E8); the supervisor reads it there through the server's secret reader (spine AD-306).
- Size: Credential Manager holds at most 2,560 bytes per entry (INFERRED from the Win32 limit); the document is far under it for one cTrader app and a few agent wallets. Past it, the document splits per venue (`qmx/trading-node-keys-<venue>`), a schema step, not a redesign.
- Sign-in: his click on This PC calls `sign_in_begin` (local or through the host route), opens the consent link in his browser, This PC's loopback receiver takes the one code and relays it to `sign_in_code`. The node exchanges it with its own registration, reads the account list once, and keeps the pair in its grant store. A grant listing a live account is kept only when `road/host/facts.json` says `trading_profile = true`.
- The trading profile: spine AD-307. Entering it is the connect dialog's "bind a live account" steps: turn chats and agent steps off over SSH, write `[host] trading_profile = true`, then `bind`.
- The recorded evidence word `proposal_only` (`qmx_apps/road/__init__.py:360`) is replaced for apps whose manifest names `qmx/trading-node-keys` by `sends_orders`; for every other money app it stays.

## 11. Setup and the passport

Steps of the `trading-node` kind (spine AD-316), each rerun-safe:

1. Card: "Ask cTrader for this machine's trading app" (link to Spotware's app page). A waiting step until he pastes the id and secret (TN-31).
2. Write `NODE_KEYS` (empty is fine).
3. Clock: probe, show offset; on This PC offer to start Windows Time; on a server install chrony with four sources (server steps run before, as PR 232 ships them).
4. Install and enable `trading-node` and `mis`; his signature publishes the node version.
5. Sign in on cTrader's page (demo first); optional Hyperliquid agent wallet in the server's own window.
6. Measure the round trip to each venue (n = 8 handshakes; median and spread) (TN-32).
7. Self-test on a demo binding: broker session ready, feed fresh, a demo test trade with its stop placed, observed and closed, kill-switch latency, clock band, disk, image digest.
8. Land the passport; write the place row last.

On his screen: one word, then the reason one click away.

## 12. Deploying a unit

His click does it (spine AD-324): "Promote to paper" or "Promote to live" on the unit page, then pick a node (Ready only), an account binding and the market. The promote action writes the lifecycle event and builds the deployment document (`CONTRACTS.md` §3) from the Library: the unit, its pinned block files by fingerprint, its G record, the starting numbers (defaults on paper; the paper lane's last calibrated values and watermark on live), record snapshots. The node link on the node's home stages the files into `data/deployments/<deployment_id>/in/` from that machine's Library (a server's arrives by the hub) and asks `deploy`. There is no size limit; a file the home does not hold yet waits in the outbox as `files_missing`. The preflight refusals are spine AD-317's. A live lane on a live-world account needs his signature step and a host in the trading profile.

## 13. What must not break, and how each is checked

| Must not break | Check (deterministic) |
| --- | --- |
| Every order carries its stop at the broker | `qmn/tests/test_protection_every_order.py` (NEW), run before and after the cut, on the replay and conformance venue clients |
| Shipped tests stay green | `just ci` on Windows and the Linux lanes on every slice |
| An operation answers fast and never raises | a test drives every operation with good and bad arguments through the supervisor's real `call`, asserts an answer under 2 s and `instance.errors == 0` |
| `deploy` answers before it compiles | a test whose compile sleeps 40 s asserts the answer under 2 s and the app still running |
| The kill works with the runtime stuck | a test freezes the runtime thread, calls `kill`, asserts the process exits and, after restart, the level is in force |
| Twin and take-over | conformance-venue tests: same tag not in journal stands down; machine mismatch refuses until `confirm_same_node`; `take_over` adopts under protection |
| No importer of a deleted module | `tools/import_scan.py` (NEW, the AST scan of `BLAST-RADIUS.md` C6) on the PR head |
| The venue gets the size the unit chose | slice C-12a: the quantity the conformance venue receives equals the sizer receipt's quantity after lot rounding (CA-03) |
| A lost answer never doubles a position | slice C-12b drill on the conformance venue, slice C-15 on demo (TN-01) |
| No reader sees a half-built book; a silent socket reconnects | slice C-12a tests (EX-02, TN-19) |
| An older change never undoes a newer one | slice C-10: an older `pause` after an applied `resume` answers `superseded`; an older `kill` still applies |
| A deployment of any size | slice C-12a: a staged 32 MB weights file deploys; a missing or mismatched file refuses by name |

## 14. Ledger rows, growth seam

- Binds: N-01 to N-10, CC-06, CC-12, CC-13, CC-14, CC-15, R-11, R-12, MA-01, MA-05, U-04 placeholders.
- Growth seam: a new venue is a capability declaration plus a venue-client adapter; a new placement is another home for the same app; risk content plugs into the unit's socket and the cross-unit hook; a second node is another setup run.
