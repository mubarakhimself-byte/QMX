# DevOps and clocks

Part C, area 5 (Level 0 P15). How QMX watches itself on every machine, how it reaches him when his PC is off, and how time works across regions. Rules: spine AD-318 to AD-321 under Level 0 AD-10, AD-42, AD-43.

His words: "the trading node is perhaps a firm" (T3:903); "this is literally the DevOps layer for that unit" (T1:1574); "Is it called, there is this thing they use in DevOps whereby when something goes down, it can set itself back up before the dev comes in" (log 2026-10-31T10:25).

**Verdict: core.** One telemetry switch and OpenObserve exist; QMF's time types exist. The work is to wire them on every machine and delete the second stack.

## 1. What exists

| Piece | State | Where (CHECKED) |
| --- | --- | --- |
| `[telemetry] send_to` (off, This PC, or a place) | BUILT | `qma-harness/src/qma/telemetry.py:25-29` |
| OpenObserve v1.1.2 on This PC on `127.0.0.1:5080` | BUILT, never run on real telemetry | `qmx_host/connect_logs.py:186-188` |
| OpenObserve and a collector on a server, no listen address set | BUILT | `qmx-host/deploy/openobserve.service`; OpenObserve binds 0.0.0.0 when `ZO_HTTP_ADDR` is empty (openobserve `src/main.rs` `init_http_server`) |
| Server firewall lets the tailnet in | BUILT | `qmx_control/qmx-recover.sh:542` (`ufw allow in on tailscale0`) |
| Heartbeat rows per host and app; strict model | BUILT | `qmx_engine/heartbeat.py:120-160`; `BLAST-RADIUS.md` C7 |
| QMN's Grafana, Loki, Prometheus stack | BUILT, never run | `qmn/deploy/observability/` |
| Alert publisher with a closed push list; liveness ping | BUILT organs | `qmn/src/qmn/observability/alerts.py:45-49`, `:174-179`; `liveness.py:1-8` |
| QMN clock bands (ok 10, warn 25, no new entries 100, halt 250 ms) | BUILT | `qmn/src/qmn/time/discipline.py:1-7` |
| No clock check on the host | MISSING | G3 §0 item 6 |
| Windows Time stopped on his PC | measured 31 Oct | research 54 §4.1 |
| Forex-only calendar; forex-shaped `market_open` precheck | BUILT | `extensions/qmf-calendar-forex/`; `qmx_engine/triggers/preflight.py:14-16` |

## 2. Each machine proves its clock

One clock probe module, `qmx_host/clock_probe.py`, is used by the host and by the node: an SNTP query (standard library, UDP 123) to each source, returning offset, delay, stratum and the source kind. Default sources are `0.pool.ntp.org` to `3.pool.ntp.org`; Google's and AWS's smeared servers are never mixed with them (CK-06). Every `clock_probe_s` (60) the host writes the facts into its heartbeat's optional `clock` field (`CONTRACTS.md` §5):

| Machine | Time service | Checked by | If unproven or off |
| --- | --- | --- | --- |
| His Windows PC | Windows Time with a good source; turning it on is his click from the doctor line | the probe; the doctor | rows flagged `clock_ok = false`; the practice node stops new entries past the halt band |
| A Linux server | chrony with four or more sources, one kind (no mixing smeared and unsmeared), installed by setup | the probe; `chronyc tracking` in the doctor | the node's bands |
| WSL, only if he picks it | a time service installed in the distribution, both idle timeouts set | the same | as a server |

The node keeps QMN's bands and checks the band before it signs a Hyperliquid action. A clock step or pause (wall and monotonic disagree) opens a suspect window with no entries until a resync (TN-33).

## 3. Zones, calendars and one view of every node

- Storage in UTC; market-tied jobs in the market's zone; his own routines in This PC's zone; a machine's zone never enters a rule. The host paths that used the machine's zone (`qmx_host/host.py:788`, `first_start.py:1512`, `__main__.py:195`) stamp UTC and display his zone (CK-07).
- Calendars beyond forex ship as data packages (`extensions/qmf-calendar-cme`, `-indices`, `-crypto247`), each with a version and a maximum age; the engine's `market_open` precheck becomes a per-market calendar check that takes a `market_id` (spine AD-320).
- DST: a test runs every session rule across 8 to 29 March 2026 and 25 October to 1 November 2026 (the London and New York mismatch weeks, research 54 §4.1). The doctor announces each mismatch week 7 days ahead.
- One view: every time on his screens is in the zone he picks; each node tile also shows the node's local time beside it (his "firm" picture belongs to the display, not the rules) and its clock band.

## 4. Telemetry

- Apps keep their JSONL logs in their volume; the host tails them (supervisor log and the app's own `logs/*.jsonl`) and exports them with heartbeats and spans through the engine's exporter when `send_to` is on, dropping and counting under pressure (spine AD-321).
- This PC's OpenObserve stays on loopback. A server's unit gains `ZO_HTTP_ADDR` set to its Tailscale address, so it is reachable from This PC over the tailnet and nowhere else even if the firewall is off. This PC opens it in the browser and through the agents' read-only OpenObserve door (X4).
- QMN's `qmn/deploy/observability/` is deleted in the shell cut.
- A test stops OpenObserve and the collector and shows units still trading and journals still written (TN-28).

## 5. Known gaps and CI

| Gap (DO-04, G2 §8) | Closed by |
| --- | --- |
| Incidents not exported | the host's log shipping exports incident rows as OTLP logs (slice C-04) |
| The bucket copy age is always empty | listed for the backup owner (backlog, unchanged) |
| `logs/feeds.json` and `logs/collector.json` absent | the feed keeper writes its own feed log in the node volume, shipped by the host; the collector file stays a backlog row |
| An outside agent's note stored unredacted | the note row passes the redaction seam (slice C-04) |
| The node's Linux lane runs only on `main`, `integration`, `rebuild/**` (DO-08) | the lane's triggers add `engine/base` and `build/**`; `just ci` on Windows already runs the node's tests (`tools/test_all.py:61-62`) |

## 6. The doctor and alarms

New doctor lines on every host: clock (offset, source, sync, band); `tzdata` age (flag past 180 days); next mismatch week; disk per drive with the node volume's drive and WSL's disk location (OP-06); telemetry off shown as off (DO-02); the observer token's expiry 7 days ahead (CA-10); trading profile on or off.

Alarms (spine AD-318): ntfy for push (an HTTPS POST to his topic; the topic name is a secret in `NODE_KEYS`) and Healthchecks.io for the liveness watcher (a ping URL every 60 s; the free plan monitors 20 checks, healthchecks.io/pricing, CHECKED; it can notify through ntfy, healthchecks.io integrations list, CHECKED). The short list that wakes him: node down (the watcher), a risk stop with open trades, protection escalation, a broker link down with open trades, the clock in the halt band for 5 minutes, healing that keeps failing. Everything else goes to the morning digest. Inside open calendars only, except node down, protection escalation and clock halt.

## 7. Settings

| Setting | Default | Origin |
| --- | --- | --- |
| `clock_probe_s` | 60 | INFERRED |
| `clock_drift_warn`, `no_new_entry`, `halt` | 25, 100, 250 ms | QMN TN-14 |
| `clock_skew_warn_ms` | 100 | research 33 §2 |
| `calendar_max_age_days` | 31 | research 54 §4.3 |
| `tzdata_max_age_days` | 180 | research 54 §4.3 |
| `dst_mismatch_notice_days` | 7 | research 54 §4.3 |
| `heartbeat_interval_s` per node | 60 | research 54 §4.3 |
| `liveness_interval_s` | 60 | INFERRED; the watcher's period is set to 3 minutes with 2 minutes grace |
| `halt_band_alarm_after_s` | 300 | `ui-needs.md` §10 |

## 8. Checks

| Must not break | Check |
| --- | --- |
| Heartbeats stay readable across builds | a test parses a row with an unknown field through the cross-machine reader and keeps the known fields |
| A machine zone never enters a rule | a test runs a London-open rule on hosts in UTC+8 and UTC+3 and asserts the same instants |
| Telemetry never on the trading path | the stop-OpenObserve test above |

## 9. Ledger rows, growth seam

- Binds: T-01, T-02, O-01, O-02, CC-14.
- Growth seam: a new source sends OTLP through the switch; a new calendar is a data package; a new alarm destination is a `NotificationChannel` adapter.
