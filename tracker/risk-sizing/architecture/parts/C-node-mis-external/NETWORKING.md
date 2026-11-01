# Networking between machines

Part C, area 6. Every link between his PC, his servers, the node and the venues: transport, what crosses, how often, what happens when it drops, and where a node should sit. Rules: spine AD-303, AD-304, AD-318, AD-321, AD-322 under Level 0 AD-44, AD-46. The master table is `architecture/01-connections.md` §3 and §4; this file adds the settings and the parts Level 0 left to Part C.

His ask (log 2026-10-31T16:20): "I hope you're considering networking, things like latency from one server, in other words, intermachinery or communication between machines". Only the node's own link to its venue is on the order path.

## 1. The host route on every host

- `POST /api/host/forward`, added to the door's host-pass set (`qmx_host/door.py:166-179`, one more entry; Level 0 `blast-radius.md` item 10). The route itself verifies the pass with `verify_host_pass` against this host's place name and the pairing key (`qmx_engine/service/forward.py:114-138`); a wrong target answers `wrong_engine`, an expired pass `expired_pass`.
- Principal: the pass's `principal` claim is the caller's real one: `operator` (his UI bearer), `agent:<id>` or `run:<id>` (`qmx_engine/service/context.py:54-67`). A `manage` operation answers only to `operator`. The PC side mints with the caller's principal, never the forwarders' constant (`qmx_host/host.py:1155`; `BLAST-RADIUS.md` C1).
- Verbs and their budgets: `CONTRACTS.md` §1. Each answers inside 8 s except `data.fetch`, which streams.
- On This PC the route is mounted too but answers nothing useful: no machine connects into This PC (Level 0 AD-44). It exists so one host build serves every role.

## 2. The node link on This PC

`qmx_host/node_link.py` (spine AD-303) is the one place This PC asks a node.

| Need | How |
| --- | --- |
| Which nodes exist and where | place rows written last by the node setup, each listing the apps homed there (`apps = ["trading-node", "mis"]`); This PC's practice node is homed `pc` |
| Ask an operation | local: the supervisor's `call` with the pin; remote: `apps.ask` on the home's route, which hands an ask to the trading node to that host's own node link; before `deploy`, the node link on the home stages the deployment's files from that machine's Library |
| Latest state (X2) | `heartbeats` and `apps.ask status` every `heartbeat_interval_s` (60) per node; kept with "unreachable since" after `unreachable_after` (3) missed reads |
| A change while a node is down (X1) | the per-node outbox in the host's store, keyed by op id and stamped `issued_at`, retried with back-off (5 s doubling to 120 s) until the node answers; his screen shows "waiting for London-1"; the node answers `superseded` to a change older than the newest it applied for that scope, except `kill` and `flatten` |
| Workflows (`app_op`, X7) | the engine's `AppOp` is composed with `Placements` (Level 0 AD-46, `qmx_engine/control_door.py:308`) whose `remote` calls the node link's `apps.job`, with the step's `inputs`; a job on a `money` app answers only his principal |
| Agents (X7) | the core `node` rows call the node link's reads; they cannot reach a `manage` operation |

## 3. Link by link

| Link | Transport | Crosses, how often | Down |
| --- | --- | --- | --- |
| E1 node to cTrader | TLS protobuf on 5035, one long session per environment per machine | commands and events; quotes, depth, bars as they arrive; heartbeat 10 s | no new entries; protection already at the broker; reconnect with back-off (1 s doubling to 60 s), gap replay of fills, capabilities re-verified, book rebuilt before readers see it |
| E3 node to Hyperliquid | CCXT REST (signed actions) and websockets | orders and fills; trades, book, funding as they arrive | as E1; the stop triggers rest at the venue; nothing relies on a venue dead man's switch |
| X1 his click to a node | AD-46 `apps.ask` over the tailnet; a promotion is the promote action on This PC (spine AD-324) | rare; the deployment document is small JSON; its block and weights files, of any size, reach a server through the Library hub (X5) and are staged there before `deploy` | waits in the outbox, also while files are still replicating (`files_missing`); the kill also has the broker's own app (E10), named on the node page |
| X2 node state | AD-46 `heartbeats` and `apps.ask status` | every 60 s, small | "unreachable since" with last values; events arrive by X3 |
| X3 pull | AD-46 `data.list`, `data.fetch`, `apps.ask journal_tail`; Part B's job | live tail every 5 minutes, closed partitions at once; bars and journals always, ticks only where a live unit's data card names them | the node and its machine's store keep everything; a week offline loses nothing |
| X4 a server's deep logs | the server's OpenObserve on its Tailscale address, port 5080 | on demand | the server keeps its window |
| X5 Library hub | replication with the pairing key, as built | as items land | offline is normal |
| X6 remote workflow steps | run passes on `POST /api/data/read` | per step | rechecked in code: a pass minted on This PC verifies at a server holding the same pairing key and fails at an unpaired one (`qmx_router/passes.py:246-286`; `BLAST-RADIUS.md` C9). The handoff's per-process secret note is out of date; what stays unproven is a run between two real hosts (slice C-17) |
| X7 agents reading a node | the core `node` rows through the node link | on demand and on the watcher template's schedule | answered from the last values and the view-only broker read |
| X8 setting up a server | SSH and Tailscale through the shipped step runner | setup time only | every step reruns; the failed one is named |
| X10 updates | step runner for host builds; hub replication plus an install for app versions (§4) | per release | the node keeps trading its version |
| E11, E12 alarms and liveness | HTTPS from the trading machine to ntfy and Healthchecks.io | when an alarm fires; a ping every 60 s | a failed send is counted and retried |

Nothing crosses from This PC's readings to a node.

## 4. Updates to a server (X10, R0-08)

- Host builds: the step runner sends the source and runs the host's install steps on the server over SSH (the X8 pattern), only on his click and only while the node's `status` says `safe_to_restart`; `qmx-recover rollback` is the undo.
- App versions: a node or MIS version he publishes on This PC lands as a Library `mini-app` item; the hub replicates it to the server's Library; on his signed publish naming the server (node) or his enable (MIS), the server's supervisor installs that definition from its replica (`install` with the expected hash, `qmx_apps/supervisor.py:295-319`) and the node restarts on it at a safe point. That the server's supervisor installs from the replica is INFERRED from the install API taking a definition folder and an expected hash; slice C-19 proves it by running both sides on one machine with two homes.
- Models: shadow models from the Lab travel the same way as Library `model` items; only This PC's MIS instance runs them.

## 5. Contract versions on connect

Every node link connection reads the node's `status` contract versions (route verbs, node operations, deployment document, reading record) and compares them with its own. A reader keeps reading an old version for the 90-day overlap window (Level 0 AD-6). On a mismatch past it, the node keeps trading what it has and the deploy dialog refuses new deployments, naming which side to update.

## 6. Where a node should sit

The network, not Python, is the floor: a TCP handshake from his PC to cTrader live is about 160 ms, to Hyperliquid's edge about 31 ms, against about 0.5 ms for in-process fan-out (research 31 §2, §3; research 38 §3.1, §3.8; MEASURED there).

| Venue | Its servers | Default region for a node | Status |
| --- | --- | --- | --- |
| cTrader at IC Markets | Equinix LD5, London (icmarkets.com trading-servers page, CHECKED); the Open API is reached through Spotware's proxies behind AWS Global Accelerator (help.ctrader.com, research 38 §3.1) | London | measure at setup |
| Hyperliquid | an API served from edges; its chain's own location not checked | measure from two candidate regions (London and Tokyo) before choosing | INFERRED, measure |
| A CME futures broker | CME's matching engine near Chicago (INFERRED, not checked) | Chicago | later, with his broker |

The setup measures the round trip from the candidate server to each venue (8 handshakes, median and spread) and puts it on the passport; the soak card shows it. One node per broker region; a second region is a second node, never one node far from one of its venues.

## 7. Checks

| Must not break | Check |
| --- | --- |
| Exactly five host-pass routes | Level 0 `br10_host_pass_routes.py` reruns on the route slice and shows five |
| An agent's pass cannot reach `manage` | a route test with principal `agent:x` on `kill` answers `refused_principal` |
| A pass for another host is refused | a route test with a pass minted for another place answers `wrong_engine` |
| A homed-here app keeps today's path | Level 0 `br11_app_op_remote.py` as an engine test |
| The outbox converges | a test queues `pause` for an unreachable node, brings it back, asserts one `pause` applied and the outbox empty |
| An agent cannot start a money app's job | a route test with principal `agent:x` on `apps.job` of a `money` app answers `refused_principal` (slice C-06) |
