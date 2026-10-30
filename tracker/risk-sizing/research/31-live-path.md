# 31: The live path: node gaps, feed fan-out, time per step, the first paper unit, and the node on his PC

Ticket: `wayfinder/tickets/research-live-path.md` (covers L14-01, L14-05, L16-04, L16-01, L13-03, Q29). Written 2026-10-30 by research agent 3. Facts and options only; no design, no choice. Ruling 135 is his decision: this file gives facts and options.

## How to read this

- **CHECKED** = read or run today: a file at `origin/engine/base` (d82be318) or `origin/build/sy5` (the stack tip), a command on his PC, or a URL. **INFERRED** = reasoned from checked facts. **MEASURED** = a number from a script run today, with its run count, spread and limiter.
- Venue facts are in research 38, instrument facts in 32, history and disk in 33. This file points to them.
- "Node spine line N" means `_bmad-output/planning-artifacts/architecture/architecture-NODE-2026-08-28/ARCHITECTURE-SPINE.md:N` at `origin/engine/base`; "spine memlog ruling N" means the gate-2 rulings entry at `.memlog.md:51` in the same folder. Code paths without a prefix are under `qmn/src/qmn/`.
- His words this answers (verbatim, `operator/transcript-2026-10-29-to-30.md`, 30 Oct 07:31): "if something is to run on external compute and external storage, it should first run on my machine. This cost us 2 days"; "a trading node should be as simple as how, for example, I can set up a server from a provider"; "Either we can use a wizard or we can just set it up when I click with a click of a button." And (20 Oct, `transcript-2026-10-20-to-28.md` 12:39): "the bot itself also didn't like taking only information from the MIS. No, it took in also live market data."

## 0. The short answer

1. **The node's code is large and mostly built, but has never run anywhere.** QMN is about 98,000 lines of source with a live cTrader client that submits orders, reconnect and gap recovery, reconcile, kill switches (KSA levels), a kill line and ratchet, seats, a recording loop and Book-level paper (CHECKED `git grep -c` and file headers at `origin/engine/base`). It has never been deployed (research 18 §7).
2. **The node already runs its needs on his PC, in principle.** His PC has WSL2 Ubuntu 24.04 with systemd running as process 1, and a Unix-socket peer-credential test (what QMN's powers door uses) passes there (CHECKED `wsl -- ps -p 1`, `systemctl is-system-running` = running, `peercred.py` = ok). So "QMN needs Linux and systemd" does not by itself stop "first run on my PC". Research 43 and the live field treated this as unknown.
3. **But four PC facts differ from a server:** the WSL clock is not synchronised (CHECKED `timedatectl`); WSL shuts a distribution down 15 s after its last process by default and systemd services do not keep it alive (CHECKED Microsoft docs); the WSL disk sits on C:, which has 16 GB free (CHECKED registry and `Get-PSDrive`); and the laptop sleeps and loses power, which is why the node exists at all (his words).
4. **The time per step is dominated by the network, not by Python.** From his PC a TCP handshake to cTrader's live endpoint takes about 160 ms (MEASURED, n=8). In-process fan-out of a quote to the units that want it takes about 0.5 ms at the median under a synthetic burst (MEASURED, 3 runs). For a 1-minute bar (60,000 ms) the whole signal-to-order path from his PC is a fraction of a percent of the bar (INFERRED). QMN's own design records "the operator's roughly 50 ms" as a watched target, never a budget (CHECKED node spine line 628); the network alone exceeds it from his PC to cTrader.
5. **Python is enough for the whole live path at 1-minute speed** (INFERRED from item 4). One Python event loop delivered about 520,000 quote deliveries a second on his CPU (MEASURED). Python's limits matter only for tick-speed units or heavy models on the decision path.
6. **The backtest that trades and the node that runs share one core.** QMN's loop driver calls QMB's `run_slice` unchanged (CHECKED `qmn/src/qmn/loop/driver.py:1-25`, `qmb/src/qmb/runloop/loop.py:780`). So the first paper unit is blocked first by the same missing piece on both sides: a unit that can be named and run by reference (STATE "QMB backtest door", item 3).
7. **QMN carries rules that clash with the unit plan:** "the bot never sizes" at the seat door (CHECKED `qmn/src/qmn/seats/dispatch.py` header); no per-bot paper lane (CHECKED `qmn/src/qmn/paper/lane.py` header, DEC-0261); a long list of values that must be set before the node will boot (CHECKED `qmn/src/qmn/config/registry_catalog.py:37`, spine lines 550-553); and a week-long soak gate with dozens of checks (spine line 629). Facts for the architecture step; nothing here removes shipped work.
8. **New fact for ruling 135:** cTrader issues a view-only live grant, and QMX's stacked code already accepts it on the PC while refusing a grant that can trade live (research 38 §6). So the PC can watch live prices with no trading power at cTrader today. Hyperliquid's trading keys cannot withdraw and expire (research 38 §3.8).

---

## 1. What the node needs beyond the never-deployed QMN code: gaps per part

| Node part | What exists (CHECKED) | Gap (INFERRED unless marked) |
| --- | --- | --- |
| **Venue client, cTrader** | `qmn/venue/live.py`: live client that records wire evidence before interpreting and submits commands; `qmf-venue` `ConnectionManager` (asyncio TLS, port 5035) at `connection.py:454`; 10 s heartbeat bound and token lifecycle at `qmf/venue/ctrader.py:134-161`; reconnect and gap recovery at `qmn/venue/reconnect.py` ("never resubmits a command") | Never run against `demo.ctraderapi.com` from a deployed node (research 18 §7). Whether the node's refresh duty and the PC's sign-in (PR 211) share one grant safely is open (research 14 §9.1) |
| **Venue clients, other** | None for Hyperliquid, MT5 trading, CCXT perps, futures brokers | All new. Research 38 §5 lists what each needs |
| **Feed keeper and pool** | QMN's recording accumulator, one first writer per (venue, account) stream (`qmn/loop/accumulator.py` header) | No shared keeper that serves many units and the router across venues; host-side long-running connection (WU10) waits on gate G-CT (research 42 §4, research 43 §3.6) |
| **Recorder into the Library's price store** | `qmn/venue/spot_recorded.py` records spot ticks into the archive; no live collector created (research 14 §4.6) | A recorder per venue, writing through the market-data door (research 14 §4.6) |
| **Unit runtime** | Seats: admission, containment, dispatch, state (`qmn/seats/*`); the loop driver over QMB `run_slice` | Seat dispatch says the bot never sizes and intents enter the Book door (`seats/dispatch.py` header), the opposite of a unit that sizes itself (STATE correction 2). A unit nameable by reference does not exist (STATE QMB section) |
| **Guards** | KSA with five levels and four trigger classes (`protection/ksa.py`); news windows and dead zones (`protection/windows.py`); kill line and ratchet (`capital/`) | No account guard code, no daily loss limit (research 18 §5). What fires with no PC is open (`live-field.md` F-07) |
| **Reconcile** | Quantity and cash residuals, four verdicts (spine memlog ruling 10; `qmn/reconcile/`) | Exercised only against fixtures |
| **Paper** | Book-level paper routed to one paired demo account; "honest FX paper" = demo host + demo account + world live (`paper/fx_claim.py`, `paper/routing.py` headers) | No per-unit paper (`paper/lane.py`, DEC-0261). Paper per unit is what the judge needs (STATE judging section) |
| **Journals** | CT-13 journals per stream; QMN writes evidence before interpretation | No unit journal or market journal (research 42 §6.1; research 12 §5) |
| **Secrets** | systemd-creds two-layer store, four named holders, one refresher per reference (`qmn/secrets/__init__.py:1-7`) | Credential provisioning never run on a host (research 42 §3) |
| **Deploy** | Install, network, credentials, lifecycle, upgrade, systemd units, observability planners in check mode (`qmn/deploy/` listing; research 42 §3) | Never run against a host; own paths `/opt/qmx`, `/var/lib/qmx`; own Grafana/Loki/Prometheus while QMX moved to OpenObserve (research 42 §3) |
| **Time** | Spine requires chrony (`qmn/deploy/DEMO-SHAPE.txt`: `qmn.service After=chrony.service`) | His WSL clock is not synchronised (CHECKED) |
| **Doors** | Python API, localhost HTTP evidence, Unix-socket powers under `SO_PEERCRED` (`qmn/doors/__init__.py:1-7`, `doors/http/powers.py:1-3`) | No connect-back to the PC; agents read "No node configured" (research 18 §7) |
| **Machine identity** | The runtime config requires "the exact operator-pinned machine identity" (`qmn/host/configured_runtime.py:278-280`); the spine says the composition root refuses to compose off the roster's VPS machine and the secret store refuses a venue session off that host (node spine memlog, ruling 18) | Running on the PC means pinning the PC as a machine in the roster: a config and rule question, not a code wall (INFERRED). The refusal text in the spine conflicts with "first run on my PC" as written |
| **Boot values** | `blocks-boot` blanks: `submission_deadline`, `accumulator_bound`, `max_slice_latency`, `local_queue_bound`, crash-loop K and T, `drain_window`, `watchdog_interval` (spine line 550; `registry_catalog.py:37`, `config/compiler.py:234`) | All blank by design until ruled. Starting defaults for some are in §3.3 |
| **Setup wizard** | PR 232's connect-a-server step runner (research 42 §2.2) | No trading-server kind (research 42 §2.1; §7 below) |
| **MIS on the node** | `qmn/mis/` (13 files) | Its role is being redesigned (research 43 §3.3); out of this file's scope |

---

## 2. One feed pool for 200+ units across brokers and machines

### 2.1 Facts per venue that shape the pool

From research 38 §6 and research 12 §4.1 (all CHECKED there):
- **cTrader:** no symbol cap; one connection per app per environment advised; a token refresh logs other holders of the same grant out. One keeper per (app, environment).
- **Hyperliquid:** per IP 10 websockets and 1,000 subscriptions; so about 200 symbols at 5 channels each per machine (research 12 §4.2 arithmetic).
- **Binance:** 1,024 streams per connection; every connection cut at 24 hours.
- **IBKR:** 100 lines, 3 depth books, 5 tick-by-tick streams at the default (research 38 §3.6). The pool is capped by the vendor, not by QMX.
- **Tradovate:** one connection per customer (research 38 §3.4).
- **MT5:** one terminal per account, on Windows.

### 2.2 Measured: in-process fan-out on his PC

`fanout.py` (scratchpad): one producer, 60 symbols, 200 units each following 3 random symbols, 500 rounds, asyncio queues, Python 3.14.6 on the i7-10750H. Three runs:

| Run | Deliveries | Deliveries a second | Latency p50 / p95 / p99 / max (µs) |
| --- | --- | --- | --- |
| 1 | 300,000 | 557,437 | 521 / 776 / 1,024 / 1,661 |
| 2 | 300,000 | 526,915 | 551 / 814 / 1,012 / 1,595 |
| 3 | 300,000 | 513,755 | 558 / 840 / 1,286 / 2,041 |

**What the numbers mean (explained):** the limiter is one CPU core running one Python event loop; nothing else is in the path. The latency is mostly queueing, because the producer pushes a whole round (about 600 deliveries) before any unit runs; one delivery alone costs about 2 µs (1 ÷ 520,000 a second). Not measured: cross-process buses, real indicator work, a real broker's message rate. INFERRED real load: 60 cTrader symbols at a busy few hundred quotes a second in total, times about 10 readers each, is a few thousand deliveries a second, under 1% of the measured capacity.

### 2.3 Options for the pool across machines (not a choice)

Research 14 §4.3 already lists three bus options (in-process, a local PUB/SUB, a feed service per machine) and §4.5 three ways for the PC and the node to share a cTrader connection (lease, two apps, split by environment). What today's facts add:

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| F1. **One pool per machine, each machine connects itself** | Fine for Hyperliquid and Binance (per-IP limits). For cTrader, two machines on one grant knock each other off at refresh | Simple | "Each machine gets its own prices" |
| F2. **The node's pool is the source; the PC reads it over the private network** | Needs the network up; a unit on the PC goes stale when the link drops | One network reader | "Your PC watches the server's prices" |
| F3. **Split by grant: the node holds the trading grant; the PC holds its own view-only live grant** (new, from research 38 §6) | Two grants, two refresh duties, no knock-off; the PC sees live prices with no trading power; matches ruling 135's "read-only keys" wording | Two sign-ins to keep alive | "Your PC has a watch-only key; the server has the trading key" |

INFERRED: F3 is possible only at venues with a view-only grant (cTrader yes; Hyperliquid needs no key to read; others not checked).

---

## 3. Time per step for a 1-minute scalper

### 3.1 The steps and their numbers

QMN already names six latency points ("rungs"): tick received, evidence write, indicator update, decision, risk evaluation, order submitted, "with no budgets until baselines exist" (CHECKED node spine line 479). The numbers below are what exists today.

| Step | Number | Kind | Source |
| --- | --- | --- | --- |
| Bar close at the broker → quote at the node | about half a round trip; from his PC to cTrader, about 80 ms | INFERRED from the MEASURED TCP handshake (median 156-167 ms, n=8 each to demo and live) | research 38 §3.1 |
| Keeper → unit (in process) | p50 about 0.5 ms, p99 about 1-1.3 ms under burst | MEASURED §2.2 | |
| Evidence write (journal before acting) | local synchronous write; QMN "never awaits I/O: sinks are synchronous local writes" | CHECKED design (spine line 237); time not measured | |
| Indicator update and decision | unit-specific; simple indicators over a few hundred 1-minute bars: well under 1 ms in Python | INFERRED, not measured | |
| Risk evaluation | same order as the decision | INFERRED | |
| Order submitted → broker acknowledgement | at least one round trip: about 160 ms from his PC to cTrader's proxy, plus the broker's own handling | MEASURED handshake + INFERRED | research 38 §3.1 |
| Hyperliquid, for comparison | handshake to the edge about 31 ms; a fresh HTTPS request 306-801 ms | MEASURED (n=8, n=6) | research 38 §3.8 |
| A 1-minute bar | 60,000 ms | fact | |

**Total from his PC, bar close to broker acknowledgement, cTrader (INFERRED):** roughly 250 to 400 ms, almost all network. That is under 1% of a 1-minute bar. On a server near the broker's proxy the network part shrinks (not measured; region of IC's servers and Spotware's proxies not checked).

**Why not twice as fast (explained):** the round trip to the broker is the floor; no code change on the node removes it. Only moving the node closer to the broker's proxy does.

### 3.2 What is fast enough (INFERRED)

- A unit that acts on closed 1-minute bars (QMN's rule: "Forming bars stay never visible or actionable", CHECKED `loop/driver.py:6`) has seconds of slack, not milliseconds.
- A unit that reacts to individual ticks or depth changes (order-flow scalps) is where network and Python start to matter. That is a different style and belongs on a venue whose data supports it (research 38 §4).
- His roughly 50 ms watched target (spine) is not reachable from his PC to cTrader by network alone (the handshake is 156 ms). It is a target for a server near the venue.

### 3.3 Numbers to name (starting defaults, editable)

| Number | Starting default | Why that start |
| --- | --- | --- |
| `signal_to_send_budget_ms` for a 1-minute unit (bar close at the node → order handed to the venue client) | 1,000 ms | About 1.7% of a bar; 10× the measured in-process path plus generous model time (INFERRED) |
| `max_slice_latency` (QMN's blocks-boot value) | 500 ms | Half the budget above, so a breach marks "no new entry" before the bar's value is spent (INFERRED) |
| `venue_ack_warn_ms` | 3 × the measured median round trip per venue and machine | Ties the warning to his real network, not a guess (INFERRED) |
| `clock_skew_warn_ms` | 100 ms | research 33 §2 |

---

## 4. Is Python right for the whole live path, or only parts?

Facts:
- The whole shipped stack is Python (QMN, qmf-venue, QMB, QMX host) (CHECKED listings).
- One Python event loop delivered about 520,000 quote deliveries a second here (MEASURED §2.2), far above a 200-unit, 60-symbol load (INFERRED).
- QMN keeps the trading path free of awaited I/O and pushes heavy work off the path ("shadow lane", never counted toward `max_slice_latency`) (CHECKED spine line 574).
- Python's limits: one core per process for pure-Python work (the GIL in the default build); heavy models on the decision path; garbage-collection pauses (INFERRED, general knowledge).

Options (not a choice):

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| P1. **Python everywhere, units split across a few worker processes** | 1-minute units: yes. Tick-speed order-flow units on depth: likely yes at retail rates; unmeasured | One language, matches all shipped code | "It's all Python, like the rest of QMX" |
| P2. **Python, with heavy models served off the trading path** | A model that misses its deadline makes the unit skip, not stall (QMN's shadow-lane pattern) | Same as P1 plus a deadline rule | "Slow thinking happens beside the trading, never in its way" |
| P3. **A compiled core for the feed keeper and order path only** | Wins only when the network is no longer the floor (a co-located server) | Two languages | "A fast engine room under the Python" |

INFERRED: nothing measured today shows Python is the limiter at 1-minute speed; the network is (§3.1).

---

## 5. What blocks the first paper unit first?

"Paper" in QMN means a demo account on `demo.ctraderapi.com`, role demo, world live (CHECKED `qmn/src/qmn/paper/fx_claim.py` header). The question (contradiction C13): a QMB runner that trades, or a node that runs?

| Blocker | Backtest side (QMB runner) | Live side (node on demo) | Source |
| --- | --- | --- | --- |
| A unit nameable by reference and runnable as data | **Missing.** Only test fixtures trade | **Missing.** Seats need a declared bot | STATE QMB section item 3; research 42 |
| The shared core | `run_slice` exists | QMN calls the same `run_slice` | CHECKED `loop/driver.py`, `runloop/loop.py:780` |
| A runner that places trades | PR 204's only runner is silent; execution inputs are built in Python, not data | QMN's live client submits commands | STATE; `venue/live.py` header |
| Data in | Replay reader copies all history per step (≈1,000 steps cap until windowed) | Live connection; never run | research 12 §1; research 18 §7 |
| Sizing | none | Seat door: "bot never sizes" | `seats/dispatch.py` header |
| Paper per unit | none | Not on the node (DEC-0261) | `paper/lane.py` header |
| Machine | His PC | Linux with systemd: **present in his WSL** | CHECKED §6 |
| Values that block boot | none | Seven blanks must be set (§1) | spine line 550 |
| Gate before live | none | Week-long soak checklist | spine line 629 |

INFERRED: the first blocker on both sides is the same: **the unit as a runnable, named thing** (research 43's "unit written down as data", F3). After it, the backtest side needs a trading runner and a windowed reader; the live side needs boot values, the seat door to let a unit size itself, and per-unit paper.

Shortest-path options (not a choice):

| Option | Order | Hard cases | Maintain | Explain |
| --- | --- | --- | --- | --- |
| S1. Backtest first | Unit as data → QMB trading runner → windowed reader → then the node | Judging works before any live code; live surprises come late | Follows the planned foundations (research 43) | "Prove it on history, then on practice money" |
| S2. Live demo first | QMN on WSL with a fixture bot on the cTrader demo → then the unit | Finds connection, token and clock problems early; no judging yet | Exercises 98k lines that never ran | "Get the trading machine running on practice money first" |
| S3. Through the shared core | The reference unit as one declaration run by `run_slice` in QMB replay and in QMN on demo, in the same step | Both worlds see the same unit; the twin-run diff idea becomes possible (`live-field.md` B017-B018) | One seam, two hosts | "One unit, tested on history and on practice money from the same file" |

---

## 6. Running the same node stack on his Windows PC

### 6.1 What his PC has (CHECKED 30 Oct)

| Fact | Value | Command |
| --- | --- | --- |
| Windows | Windows 11 Home 10.0.26200 | environment |
| CPU, RAM | Intel i7-10750H, 16 GB | `Get-CimInstance` |
| WSL distributions | Ubuntu-24.04 (WSL 2, default), docker-desktop (WSL 2) | `wsl -l -v` |
| WSL kernel | 6.18.33.2-microsoft-standard-WSL2 | `uname -r` |
| systemd | enabled in `/etc/wsl.conf` (`[boot] systemd=true`), PID 1 is systemd, state "running" | `cat /etc/wsl.conf`; `ps -p 1`; `systemctl is-system-running` |
| Unix-socket peer credentials (`SO_PEERCRED`) | works: pid and uid match | `peercred.py` run with WSL's Python 3.12.3 |
| WSL memory | 7 GB of 16 (default half) | `free -g` |
| Clock | Africa/Nairobi; "System clock synchronized: no" | `timedatectl` |
| `.wslconfig` | none found | `cat /mnt/c/Users/Mubarak/.wslconfig` |
| WSL disk location | C:\Users\Mubarak\AppData\Local\wsl\… (C: has 16.0 GB free; D: 58.1 GB) | registry `Lxss`; `Get-PSDrive` |
| Docker | Docker Desktop installed (WSL 2 backend) | `Get-Command docker` |

### 6.2 WSL behaviour that matters (CHECKED https://learn.microsoft.com/en-us/windows/wsl/wsl-config , https://learn.microsoft.com/en-us/windows/wsl/systemd)

- `instanceIdleTimeout` default 15,000 ms: a distribution idle that long is shut down; `-1` disables.
- `vmIdleTimeout` default 60,000 ms for the whole VM.
- "systemd services will NOT keep your WSL instance alive" (Microsoft, systemd page).
- Users report both timeouts must be set to keep services running (SECONDARY https://github.com/microsoft/WSL/discussions/9245 , https://github.com/microsoft/WSL/issues/13033).
- `networkingMode` NAT by default; `mirrored` mirrors Windows' interfaces into Linux.
- `memory` default 50% of Windows memory.

### 6.3 Ways to run the node on the PC (not a choice)

| Option | How close to a server | Hard cases | Maintain | Explain |
| --- | --- | --- | --- | --- |
| W1. **WSL2 Ubuntu 24.04 with systemd (already there)** | Same distribution family as a typical Ubuntu server (PR 232 asks for Ubuntu, research 42 §2.2); different kernel build | Idle shutdown (set both timeouts); clock sync (install and check a time service); disk on C:; laptop sleep pauses everything | One extra config file | "The same Linux runs inside your PC" |
| W2. **A container (Docker Desktop, WSL 2 backend)** | Image identical on PC and server (`live-field.md` "one Linux image the PC also runs") | systemd inside a container is awkward; QMN's units expect systemd (`qmn.service.in`), so either run systemd in the container or replace units with a process supervisor (INFERRED) | Image build and registry | "The same box runs here and there" |
| W3. **A full VM (VirtualBox or VMware)** | Closest to a server | Windows 11 Home has no Hyper-V Manager (INFERRED, not read today); heavier; another OS to patch | Highest | "A small server inside your PC" |
| W4. **Port QMN to native Windows** | Furthest | `SO_PEERCRED` and systemd are Linux-only (research 42 §3); QMN already has a Windows deployment reader (`qmn/host/_windows_deployment.py`), so some Windows paths exist | A second platform forever | "Rewrite the trading program for Windows" |

**The PC-versus-server difference list (INFERRED from §6.1-6.2; feeds `live-field.md` N-10):** kernel build; NAT networking and the PC's home internet path (about 160 ms to cTrader, MEASURED); clock sync state; idle shutdown and laptop sleep; disk on C:; memory share; no static IP; power cuts. A rehearsal on the PC proves the code and the setup, not the server's network or uptime.

---

## 7. "Set up a node as simply as renting a server"

What the shipped path does (research 42 §2.2, CHECKED there): his cards (choose and pay for a server, its address, a Tailscale key, the server password typed into a QMX-opened terminal, the firewall approval), then checked, rerun-safe steps, then one place row written last, then a smoke run. It installs the QMX host as a workflow worker and Library store. It has no trading-server kind and never installs QMN.

What a trading-server wizard would need on top (INFERRED; a list of facts, not a design):

| Step | Why | Fact behind it |
| --- | --- | --- |
| Start the broker app registration on the first card | Spotware reviews each app; "usually around 24 hours" | research 38 §3.1 |
| Choose a trading role for the place, not a worker role | `connect.py:389` has storage, compute and deep logs only | research 42 §2.1 |
| Install either QMN beside the host or the host in a trading role | Two stacks today: different paths, credential store and observability | research 42 §3; research 43 §3.6 |
| Install and check a time service | QMN expects chrony; Hyperliquid's nonce window | `DEMO-SHAPE.txt`; research 38 §3.8 |
| Provision credentials onto the server only | systemd-creds; ruling 135 in code refuses live trading grants elsewhere | `qmn/secrets`; research 42 §3 |
| Pin the machine identity | The runtime config requires it | `configured_runtime.py:278-280` |
| Set the boot values | Seven blanks block boot | spine line 550 |
| Demo smoke trade and passport | A test trade on demo, kill-switch latency, clock skew, feed freshness, image digest | research 43 §3.6 |
| Same wizard, run first against his PC's WSL | His rule: run first on his machine | his words, 30 Oct |

Provider facts (which providers create servers by API, allow trading use, and have regions near the brokers; `live-field.md` N-05) were not researched today. Not verified.

---

## 8. Ruling 135 against "first run on my PC": facts and options

Ruling 135 (research 42 §3): live-money keys only on a trading server; the PC and any machine an agent can reach hold read-only or demo keys. His rule: anything that runs on external compute must first run on his machine. The choice is his. Facts found today that move the options in `live-field.md` §3:

| Fact | What it changes | Source |
| --- | --- | --- |
| The node's Linux needs are met on his PC by WSL2 with systemd | "QMN cannot run on the PC" no longer holds; O2 (demo rehearsal plus twin and shadow runs) needs no new platform | §6.1 CHECKED |
| cTrader view-only live grant exists; stacked code accepts it on the PC and refuses trading grants | Shadow runs on live prices on the PC are possible without breaking ruling 135 | research 38 §6 CHECKED |
| cTrader's protocol has no withdrawal request | A leaked trading token can trade money away but not move it out | research 38 §3.1 (absence) |
| Hyperliquid API wallets cannot withdraw, expire in at most 180 days, and can be revoked | A walled or short-lived trading key is possible at that venue (O4, O7 weaker risk) | research 38 §3.8 |
| Hyperliquid's `scheduleCancel` cancels all open orders, stops included | A venue-side dead man's switch protects against a dead node but strips protection | research 38 §7 |
| cTrader has no dead man's switch | A dead node leaves only the stops already at the broker | research 38 §3.1 |
| Windows 11 Home | A separate Windows account is possible; Hyper-V is not (INFERRED) | environment |
| WSL distributions are registered per Windows user (registry under `HKCU`) | A second Windows account would have its own distributions an agent running as him does not see by default (INFERRED from the per-user registry location) | registry CHECKED |
| The node spine refuses a venue session off the pinned VPS host | Any option that trades from the PC (O3, O4, O7) also needs that rule changed | §1 |

The eight options (keep 135; demo rehearsal plus twin and shadow; overrule for the PC; walled key on the PC; brain and arm; home appliance; live canary on the PC; per venue) stand as written in `live-field.md` §3. None is chosen here.

---

## 9. Questions

| Id | Question | Tag |
| --- | --- | --- |
| P-01 | Does a WSL2 distribution on his PC count as "first run on my machine"? (`live-field.md` N-02) | operator |
| P-02 | Which shortest path to the first paper unit: backtest first, live demo first, or through the shared core? (§5; C13) | operator |
| P-03 | Should the PC hold a view-only live cTrader grant for shadow runs? (§2.3 F3, §8) | operator (money-adjacent) |
| P-04 | Does the seat door's "bot never sizes" stay for units, given the unit sizes itself? | lead (risk session owns the socket) |
| P-05 | Does DEC-0261 (no per-bot paper on the node) stay, given per-unit paper is what judging needs? | operator |
| P-06 | QMN beside the host, or the host in a trading role? (research 43 decision area) | lead, then party mode |
| P-07 | Which provider and region for the trading server, by network distance to IC's and Spotware's servers? | research (not done today) |
| P-08 | Is the week-long soak checklist kept, shrunk, or replaced by a short passport? (spine line 629 vs standing order 6) | operator |
| P-09 | Measure the real round trip from a candidate server region to `live.ctraderapi.com` before choosing a provider | research (a script, once a server exists) |

## 10. Not verified

- Real cTrader message rates, depth update rates and order acknowledgement times (no sign-in).
- Indicator and decision times for a real unit.
- Whether Windows 11 Home blocks Hyper-V (general knowledge, not read today).
- Provider APIs, terms on trading use, and regions.
- Whether QMN boots under WSL2 at all (not attempted: its boot values are blank and it would need credentials).
