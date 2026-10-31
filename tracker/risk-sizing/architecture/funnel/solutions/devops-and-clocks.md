# DevOps and clocks

**What this part is.** How QMX watches itself across his PC and any servers (logging, observability, monitoring, health), and how time works when nodes sit in different regions: one time scale for every stamp, sessions in each market's own zone, each machine proving its own clock, and one screen that shows a Singapore node and a London node together (weak spot 8).

**Verdict: core.** One telemetry switch and OpenObserve are already built; QMF's time types are built. The work is to make every machine report its clock, move every session rule to market calendars, and delete the second monitoring stack.

## His words

- "the trading node is perhaps a firm" (T3:903)
- "We are literally trading 24/7, my days. This is why we need a trading node." (T2:325)
- "this is literally the DevOps layer for that unit" (T1:1574)

## 1. What exists today

| Piece | State | Where checked |
| --- | --- | --- |
| One setting for all monitoring, `[telemetry] send_to` (off by default, This PC, or a place) | BUILT | G2 §8 |
| OpenObserve v1.1.2 for Windows, fetched and checked against its sha256; a server variant with a collector and an on-disk queue; agents read-only through its MCP door | BUILT, never run on real telemetry | G2 §8; G4a §3 row 10 |
| The engine's exporter: spans, heartbeats as gauges, ledger events and log lines to OTLP; the four records stay the source of truth | BUILT | G2 §8 |
| A heartbeat per host and per running app; doctor lines; `ops_health`, `ops_spans`, `ops_heartbeats` | BUILT | G2 §8 |
| QMN's own Grafana, Loki, Prometheus and promtail stack | BUILT, never run (a second stack) | G2 §8; G3 §1.1 |
| QMF time: every stored time an `Instant` (int64 UTC nanoseconds); `TradingDate` carries its calendar identity and tzdata version; an injected clock; `SessionWindow`; local time only for display, always labelled | BUILT | G2 §9 |
| Market calendars: only forex (`forex-17NY`) | BUILT (forex only) | G2 §9 |
| Triggers in an IANA zone with cron's DST rules; scripts read the run clock from `QMX_NOW` | BUILT | G2 §9 |
| The `market_open` precheck: shut on Saturdays, Sundays and listed holidays, forex-shaped | BUILT, wrong for crypto and futures | G2 §9 |
| Machine-local time in three host paths (backups, first start, the command line) | BUILT | G2 §9 |
| Per-machine zone and clock offset on attempts, heartbeats or monitoring rows | MISSING | G2 §9 |
| QMN's clock discipline: host clock the only stamper, chrony with four or more sources, no trade before sync, four bands (ok at 10 ms or less, warn 25 ms, no-new-entry 100 ms, halt 250 ms), broker skew kept apart from latency | BUILT inside QMN only | G3 §0 item 6; research 54 §4.1 |
| His PC: Windows Time service stopped (start type Manual); WSL clock not synchronised; Windows zone E. Africa Standard Time (UTC+3) | measured 31 and 30 Oct | research 54 §4.1 |
| `tzdata` pinned at 2025.2; the latest is 2026.6; Windows has no system tz database, so Python on Windows reads the `tzdata` package | BUILT | research 54 §4.1 |
| Zone defaults disagree: templates use Europe/London, the build skill suggests Europe/Berlin, three host paths use the machine's zone | BUILT | G2 trap 11 |

## 2. Harvest

| Solution | Where | Fits now? |
| --- | --- | --- |
| One time scale (UTC) for every stamp; local time only for display and session rules; a synchronised clock on every machine; calendars from the exchange, versioned, with a maximum age; sessions in the market's zone; the trading day at the venue's day boundary; monitoring several nodes in the viewer's zone, with a node whose clock is off marked | research 54 §4.2 | Yes |
| Two stamps on every market event (venue time and receive time); skew watched, never corrected | research 54 §4.2 item 2 | Yes |
| Clock sync checked before any recording and on the passport; rows recorded unsynchronised flagged | research 43 §4 L14-09 (research 31, 33) | Yes |
| Both WSL idle timeouts set if WSL is used | research 43 §4 (research 31 §6.2) | Only for the WSL fallback |
| One stack must win; QMX moved to OpenObserve | research 53 §2 item 8; ledger O-01 | Yes |
| Review timing in 24/7 markets runs on a clock table of session closes plus a rolling crypto clock | research 43 §4 L11-07 | Yes (`workflows.md`) |
| One clock per reading tier instead of "5 trading days" | research 43 "Subtract first" item 5 | Yes (`mis.md`) |

## 3. DevOps: the shapes

### Shape A. OpenObserve only, behind the one telemetry switch; QMN's Grafana stack deleted (recommended)

- **What.** Every process (host, engine, apps, the node, the MIS, QMB) sends OTLP through the one switch. On his PC, OpenObserve on This PC; on a server, OpenObserve or the collector shipping to his PC's instance. The journals stay the record of truth for units; OpenObserve holds operational logs (research 43 F4).
- **Reuses.** Everything in §1's first five rows.
- **Explain.** "One place to look at how every part of QMX is running, on every machine."

### Shape B. Keep both stacks (QMN's Grafana for the node, OpenObserve for the rest)

- **Why not.** Two places to look, two sets of alerts, two deploys; a unit's logs would have two homes (G2 trap 10).

### Shape C. Journals as the only monitoring, no telemetry

- **Why not.** Journals record trading; they do not show a process's memory, a stuck queue or a failing disk.

**Pick: Shape A.**

## 4. Clocks: the shapes (weak spot 8)

### Shape A. UTC stamps, market-zone rules, every machine proving its clock (recommended)

1. **Every stamp is UTC** (QMF's `Instant`), on every journal row, order, fill and log line (S121).
2. **Market events carry two stamps**, venue time where the venue gives one and receive time always (S122). cTrader gives no server time (G3 §2.1), so the receiving machine's clock is the measurement; its skew against a time server is watched, never "corrected".
3. **Every machine reports its own clock** (S123): zone, offset against a time server, sync state, tzdata version, on its heartbeat and on its passport. A machine that cannot prove its offset writes rows with `clock_ok = false` (`journals.md` §3.1).
4. **Sessions live in the market's zone** (S124): London open is a London-zone rule, CME's close a Chicago-zone rule, the gold fix a London-zone rule. A node in Singapore and a node in London compute the same session from the same instant. The node's own local time never enters a rule.
5. **Calendars are versioned data on the instrument record** (S125), with a maximum age; the forex calendar is joined by futures (exchange sessions, daily break, holidays, expiries), index (per-index breaks) and 24/7 calendars (crypto, perps, with sessions measured from activity and the funding clock).
6. **The trading day is the venue's day boundary** (for example 17:00 New York for FX at many brokers), measured per broker.
7. **Clock bands on every trading machine** (QMN's, kept): warn, no new entries, halt. Hyperliquid also rejects actions whose nonce falls outside its time window, so a drifting clock blocks trading there (research 38 §3.8).
8. **Display** shows each node in the zone he chooses, with its own office time beside it (his "firm" (T3:903) picture, which fits the display, not the rules), and marks a node whose clock is off (S126).

### Shape B. Each node runs on its own local time ("the node is a firm"), converted at the PC

- **Why not for rules.** A London-open rule written in a Singapore node's time breaks twice a year at DST and every week a mismatch window opens (London and New York are 4 hours apart, not 5, between their changes: this week, 25 Oct to 1 Nov 2026, research 54 §4.1). It is kept for display only.

### Shape C. Correct every stamp by the measured skew

- **Why not.** A corrected stamp hides the fact that the clock was off; the flag is honest, the correction is not (research 54 §4.2).

**Pick: Shape A.**

## 5. What each machine does about its clock

| Machine | Time service | Checked by | If it fails |
| --- | --- | --- | --- |
| His Windows PC | the Windows Time service, running with a good source | the doctor (a new doctor line) and the node's passport; QMX proposes starting the service and he clicks (a system setting is his act) | rows flagged; the practice node blocks new entries past the halt band |
| A Linux trading server | chrony with four or more sources, no smeared sources mixed (Google and AWS smear leap seconds) | installed and checked by the connect dialog's steps; the node's clock bands | the node's bands: warn, no new entries, halt |
| WSL (fallback only) | a time service installed inside; both idle timeouts set | the same checks | as the server |

## 6. The small fixes

| Fix | Reason, one line |
| --- | --- |
| Record zone, offset and sync state beside each attempt, heartbeat and monitoring row (`ENG/runner.py:206-212` records place and machine only) | his Singapore and London case |
| Replace the forex-shaped `market_open` precheck with a per-market calendar check | wrong for crypto and futures |
| One zone default: storage in UTC; market-tied jobs (session closes) in the market's zone; his own routines (the morning card) in his PC's zone | three defaults disagree today |
| An age check on the `tzdata` pin, and a notice before each DST mismatch week | the pin is two IANA years old |

## 7. Monitoring several nodes together

The PC's merged inbox already holds one stream per reachable owned node and shows "server unreachable since ..." with the last values (G2 §6). Each node's tile shows its one word, its machine, its zone and office time, its clock band, its heartbeat age and its kill-switch level. Every time on the screen is shown in the zone he picks, labelled. A watcher workflow reads heartbeats and node journals over time (`workflows.md`).

## 8. Numbers (starting defaults, all editable; from research 54 §4.3 unless marked)

| Number | Default |
| --- | --- |
| `clock_drift_warn` | 25 ms |
| `clock_drift_no_new_entry` | 100 ms |
| `clock_drift_halt` | 250 ms |
| `clock_skew_warn_ms` (receive clock against a time server) | 100 ms |
| `calendar_max_age_days` | 31 |
| `tzdata_max_age_days` before the pin is flagged | 180 |
| `dst_mismatch_notice_days` | 7 |
| `heartbeat_interval_s` per node | 60 |
| missing-heartbeat alert | 3 intervals (INFERRED) |

## 9. Connection points

| From | To | What crosses |
| --- | --- | --- |
| Every process | OpenObserve | OTLP traces, gauges, logs, through the one switch |
| Every machine | PC inbox | heartbeat with zone, offset, sync state, tzdata version |
| Instrument records | QMB, node, MIS | calendars in each market's zone, versioned |
| Node | journals | `clock_ok` on every row |

## 10. Open for the architecture step

1. Whether a server's OpenObserve is its own instance or ships to his PC's (local first says the PC holds everything; a server stands in when the PC is off).
2. The doctor's exact clock checks on Windows (the support boundary for 1 s, 50 ms or 1 ms accuracy, research 54 §4.1).

## 11. Parked

- A compiled time path for co-located servers (only when the network stops being the floor).
