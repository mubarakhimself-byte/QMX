# G3: The trading node and the external connections, as built

Grounding agent G3, 2026-10-31 midday program. Read and record only. Nothing here is a design. No repo, branch, worktree or PR was changed.

Code truth: the read-only checkout of `origin/engine/base` at `c93407ca` (31 Oct 08:25, "Merge pull request #234"). Paths without a prefix are relative to `D:\QMX-worktrees\engine-base-read\`.

## How to read this

**Status tags.**
- **BUILT**: merged on `origin/engine/base` at `c93407ca`.
- **STACKED**: in an open PR, not merged. Only PR 204 is still open (`gh pr list -R MubarakHimself/QMX --state all --limit 60`, CHECKED: 207 to 234 all MERGED on 2026-10-31, 204 OPEN on `build/wu4 -> build/wu2`).
- **DESIGNED**: in an architecture or docs file, no code.
- **MISSING**: in neither.
- **NEVER RUN**: the code exists, but no file I read shows it ran against a real venue, a real host or his real QMX folder.

**Evidence labels.** CHECKED = read at the cited path and line, or seen in the cited command output today. INFERRED = my reading of checked facts.

**What changed since research 42 (30 Oct).** Research 42 read trunk at `d82be318` and the stack tip `build/sy5` at `074670ac`. The whole stack (PRs 207 to 234) merged on 31 Oct. So every row research 42 tagged STACKED (PR 207 to 234) is now BUILT. CHECKED (`git log --oneline d82be318..HEAD` in the checkout: 193 commits, merges of 207 to 234).

**Earlier work this builds on.** Research 31 (live path), 38 (venues), 42 (shipped code), 18 (today), 12 (feeds), `trading-node-notes.md`, the node spine `_bmad-output/planning-artifacts/architecture/architecture-NODE-2026-08-28/ARCHITECTURE-SPINE.md` (the "node spine"), `docs/components/trading-node.md`, and `workroom/research/05-broker-connectivity.md` (17 Aug). Facts taken from them say so.

---

## 0. The short answer

1. **The node (QMN) is a large, finished-looking Linux program that has never traded.** About 97,000 lines in `qmn/src/qmn/` (CHECKED, line count per package). It has a live cTrader client that submits the five command kinds, reconnect and gap recovery, reconciliation, a kill-switch authority (KSA), clock bands, secrets, deploy planners and a liveness heartbeat. It has never been deployed (research 18 §7, research 42 §3). NEW today: its only registered host profile is an offline replay profile, so even a configured QMN refuses to compose a live trading root (`qmn/src/qmn/host/configured_live_resources.py:1-7`, `:38-58`, CHECKED).
2. **QMN runs only on Linux with systemd.** Its powers door is a Unix socket checked with `SO_PEERCRED`, its service is a systemd `Type=notify` unit that starts after `chrony.service`, and its secrets are sealed with `systemd-creds` (`qmn/deploy/systemd/templates/qmn.service.in:9,15,16,29,33`; research 42 §3, CHECKED). A single-machine variant (node on the same box as the rest of QMX, without systemd) is ruled in scope with its design owed (`docs/gap-report.md:169`, GAP-0058, DEC-0262). His PC already has WSL2 Ubuntu 24.04 with systemd running (research 31 §6.1, CHECKED 30 Oct).
3. **Ruling 135 is in code, in two places.** The QMX host (PC or a QMX server) refuses to store any cTrader sign-in that can trade a live account (`qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:103-146`; `qmx-agents/packages/qmx-host/src/qmx_host/venue_session.py:1-16`). And the QMX host has no order path at all: every broker adapter is read-only, and an agent's order is only a staged proposal "awaiting_operator_signature" (`qmx-agents/packages/qmx-broker/src/qmx_broker/service.py:560-584`). The only order path in QMX is QMN. CHECKED.
4. **cTrader is the only venue that can trade.** BUILT: the cTrader Open API over Protobuf (port 5035), OAuth sign-in on This PC, read adapters, and QMN's live command client. CCXT is BUILT for spot reads only and refuses every contract market. MT5 is a declaration only. Hyperliquid, Rithmic, CQG, Tradovate and IBKR are MISSING. Databento is a key check only. CHECKED (§2).
5. **The live contracts are rich and venue-neutral, but shaped around "the bot never sizes".** Five command kinds under a four-outcome law (`packages/qmf-venue/src/qmf/venue/commands.py:1-50`), record-before-interpret events with four reconciliation verdicts (`events.py:1-50`), and an entry intent that carries no size (`packages/qmf-risk/src/qmf/risk/door.py:559-571`). The unit plan says the unit sizes itself (STATE correction 2). That seam is the biggest "must change" fact for the foundation (INFERRED).
6. **Clock discipline exists only inside QMN.** Four clock bands, chrony checks, broker skew kept apart from latency (`qmn/src/qmn/time/discipline.py:1-7`). The QMX host on his PC has no clock-sync check (`git grep -i -E "\bntp\b|chrony|w32time|timedatectl|clock_skew" -- qmx-agents` = no hits, CHECKED). His Windows Time service is stopped with start type Manual today (`Get-Service w32time`, CHECKED 31 Oct).

---

## 1. The trading node (QMN)

### 1.1 What exists, part by part

| Part | Status | What it is | Evidence |
| --- | --- | --- | --- |
| Package size | BUILT | 21 subpackages, about 97,000 lines (host 26,602; mis 12,654; venue 7,478; data 7,160; ledger 5,516; order 5,178) | `git ls-files qmn/src/qmn/<pkg>` line counts, CHECKED |
| Composition root and boot ceremony | BUILT, NEVER RUN | doors, then boot-attempt record, preflight, compose, fingerprint, seal | `qmn/src/qmn/host/boot_ceremony.py` docstring; node spine TN-2 |
| Live host profile | MISSING | The closed registry holds one profile, `qmn.book.offline-conformance.v1`, which reads QMB replay evidence; live resolution refuses with `configured_runtime.hosted_resources_missing` ("no LIVE observation, current MIS, or KSA resource producer") | `qmn/src/qmn/host/configured_composition.py:40`, `configured_live_resources.py:38-58`, called from `_supervision.py:367`, CHECKED |
| Machine pin | BUILT | The runtime config requires "the exact operator-pinned machine identity" | `qmn/src/qmn/host/configured_runtime.py:278-280`, CHECKED |
| Supervision | BUILT, NEVER RUN | one long-lived process, raw `sd_notify`, watchdog, stand-down-alive, crash-loop fold, exit code 75 for a requested restart | `qmn/src/qmn/host/_supervision.py` docstring; node spine TN-4 |
| Live loop | BUILT, NEVER RUN | one loop per `(VenueId, account)` stream driving QMB's `run_slice` unforked; forming bars never actionable | `qmn/src/qmn/loop/driver.py:1-25`; research 31 §0 item 6 |
| cTrader live client | BUILT, NEVER RUN | records wire evidence before interpreting; submits every CT-19 kind the capability declaration supports; refuses an unprotected `place_order`; never retries after wire hand-off | `qmn/src/qmn/venue/live.py:1-35`, CHECKED |
| Reconnect and gap recovery | BUILT, NEVER RUN | refresh by credential reference, re-verify capabilities, gap-replay fills; never resubmits a command | `qmn/src/qmn/venue/reconnect.py` docstring |
| Capability check at connect | BUILT, NEVER RUN | verify-or-refuse: timestamp unit, daily boundary, bar basis, pip formula, money exponent, netting or hedging | `qmn/src/qmn/venue/verify.py` docstring |
| Venue-resident stop | BUILT | every `place_order` must carry a protective stop at the broker at placement | `qmn/src/qmn/order/protection.py` docstring |
| Order path | BUILT | Book door freezes R before a command is minted; command ordinal; protection-priority pacer; UNKNOWN per stream | `qmn/src/qmn/order/door.py:135-157`, `order/pacer.py`, `order/unknown.py` docstrings |
| Reconcile | BUILT, exercised on fixtures only | four verdicts `reconciled | drift | unknown | out-of-lookback`, two exact residuals | `qmn/src/qmn/reconcile/__init__.py` docstring; research 31 §1 |
| Kill switch (KSA) | BUILT, values blank | five levels GREEN to BLACK, four trigger classes, escalate-only automatic, operator-only `resume`; effect-matrix values are operator-owned and blank, which blocks live | `qmn/src/qmn/protection/ksa.py`, `effect_matrix.py` ("shape only, no values") docstrings; node spine TN-7; GAP-0050 |
| News windows and dead zones | BUILT | instrument-scoped news blackout, daily dead zone, session-handover buffer; exits and protection never blocked | `qmn/src/qmn/protection/windows.py` docstring |
| Kill line and ratchet | BUILT | per-binding capital floor on virtual-ledger equity; breakeven ratchet | `qmn/src/qmn/capital/__init__.py` docstring |
| Seats (where a bot runs) | BUILT | admitted, active, benched, quarantined; a seat needs a registered CT-33 definition, QML conformance, the prediction linter, a declared footprint and a Book/BMS binding; plain Python cannot bypass it | `qmn/src/qmn/seats/admission.py`, `seats/state.py` docstrings |
| "Bot never sizes" | BUILT | seated callbacks emit CT-23 intents only; size is resolved at the Book door | `qmn/src/qmn/seats/dispatch.py` docstring ("bot never sizes") |
| Paper | BUILT | Book-level paper routed to one paired demo account; no per-bot paper lane (DEC-0261) | `qmn/src/qmn/paper/lane.py`, `paper/routing.py`, `paper/fx_claim.py` docstrings |
| Promotion and activation | BUILT, NEVER RUN | human-only promotion click runs a silent battery; activation is a second click effective at the next day boundary | `qmn/src/qmn/promotion/lifecycle.py` docstring |
| How a bot reaches the node | BUILT on the node side; MISSING on the PC side | sandboxes push fragments into a write-only hub inbox; the operator's `hub_publish` act publishes them; the node's only inbound live path is a click-gated pull of the published set; sandbox provenance refused twice | `qmn/src/qmn/promotion/hub.py`, `passive_hub.py` docstrings. PC side: `git grep -i qmn -- qmx-agents/packages/qmx-host/src qmx-agents/packages/qmx-control/src` = no hits, CHECKED |
| How results come back | BUILT on the node side, NEVER RUN; PC pull DESIGNED | one-way watermarked copy of hot rooms into a `sealed-archive` tree, then a one-way SSH pull to the workstation (node spine TN-3) | `qmn/src/qmn/data/sealed_archive.py` docstring; node spine TN-3 diagram |
| Doors | BUILT | in-process Python API, localhost HTTP evidence (publish-never-act), Unix-socket powers under `SO_PEERCRED`; no command line (his 28 Aug ruling) | `qmn/src/qmn/doors/__init__.py`, `doors/http/powers.py` docstrings |
| Agent read of the node | BUILT, answers "No node configured" | the agent tool `node_state` reads lifecycle only; no trading or node-control power is exposed | `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py:232-236`, CHECKED |
| Secrets | BUILT, NEVER RUN on a host | two-layer store under systemd-creds, four named holders, one refresher per credential reference | `qmn/src/qmn/secrets/__init__.py`, `holders.py`, `rotation.py` docstrings |
| Clock | BUILT | the host OS clock is the only stamper; four bands `ok | warn | no-new-entry | halt`; machine-versus-truth and node-versus-broker skew kept apart | `qmn/src/qmn/time/clock.py`, `time/discipline.py:1-7`; node spine TN-14 |
| Calendars | BUILT | three named calendar kinds (market hours, day boundary, news); only one market-hours provider exists, `forex-17NY` | `qmn/src/qmn/time/calendars.py` docstring; `extensions/qmf-calendar-forex/src/qmf/calendar_forex/_provider.py:123`, CHECKED |
| Monitoring | BUILT, NEVER RUN | own Prometheus, Grafana, Loki and promtail stack; JSON-lines logs; seven independent health states; alert allow-list | `qmn/deploy/observability/`; `qmn/src/qmn/observability/` docstrings |
| Liveness heartbeat | BUILT | outbound alive-ping to an off-server watcher that alerts on a missing ping; zero authority (DEC-0261, formerly the dead-man's switch) | `qmn/src/qmn/observability/liveness.py` docstring |
| Deploy | BUILT, check mode only | `just node-install`, `node-switch`, `node-rollback`, `node-secrets-provision`, `node-data-bootstrap` and others; immutable tree per commit under `/opt/qmx` | `qmn/deploy/justfile-recipes/node.just:15-87`; `qmn/deploy/install.py` ("never SSHes to Contabo", research 42 §3) |
| Boot values | DESIGNED, blank | seven values block boot until set: `submission_deadline`, `accumulator_bound`, `max_slice_latency`, `local_queue_bound`, crash-loop K and T, `drain_window`, `watchdog_interval` | research 31 §1 (spine line 550, `registry_catalog.py:37`) |
| Soak gate | DESIGNED | one full week unattended on demo before any live binding; acceptance is machinery proof, never profit | `docs/components/trading-node.md:177`; operator ruling 28 Aug |
| CI | BUILT | a pinned `ubuntu-24.04` lane: Linux typing, unit-file scan, check-mode boot, switch and rollback | `.github/workflows/qmn-ubuntu-24.04.yml:1-60`. It triggers on `main`, `integration` and `rebuild/**` only, so PRs into `engine/base` do not run it (`:9-14`, CHECKED) |
| Live-venue tests | BUILT, excluded | tests marked `live` ("credentialed live-venue smoke; not part of the credential-free gate") | `pyproject.toml:221-224`; `qmn/tests/test_qmn_live.py`, CHECKED |

### 1.2 Operating systems

| Piece | Windows | Linux | Evidence |
| --- | --- | --- | --- |
| QMN node | No. One read-only Windows deployment reader exists, nothing more | Yes, Ubuntu 24.04 with systemd | `qmn/src/qmn/host/_windows_deployment.py:1-6`; `qmn.service.in`; `doors/http/powers.py` (`SO_PEERCRED`) |
| qmf-venue (cTrader transport) | Yes in principle: stdlib asyncio TLS | Yes | `packages/qmf-venue/src/qmf/venue/connection.py:1-17` (INFERRED from stdlib-only) |
| QMX host (agents, workflows, Library, broker reads) | Yes, first-class: Credential Manager, `msvcrt` file locks, Job objects | Yes, as a server role | `venue_session.py:73`, `:113-125`; research 42 §1.4 |
| MT5 | Only Windows (or Wine on Linux) | Through Wine and an RPyC bridge | `adapters.py:59-72` (`runs_on=("windows", "windows_or_wine")`); `workroom/research/05-broker-connectivity.md` §3 |
| WSL fallback | His PC has WSL2 Ubuntu 24.04, systemd as PID 1, `SO_PEERCRED` works | | research 31 §6.1 (CHECKED 30 Oct) |

WSL facts that differ from a server (research 31 §6.2, CHECKED there against Microsoft docs): the WSL clock was "System clock synchronized: no"; a distribution shuts down 15 s after its last process unless `instanceIdleTimeout` and `vmIdleTimeout` are changed; "systemd services will NOT keep your WSL instance alive"; its disk sits on C:, which had 16 GB free; the laptop sleeps and loses power.

His ruling (31 Oct, verbatim in `operator/transcript-2026-10-30-to-31.md`, 04:55): the node is set for Linux "because most VPSs that we're going to be using work with Linux", and "we can go with WSL, okay? If all goes south." His morning ruling 7: Windows is first-class; he prefers plain Windows to WSL.

DEC-0262 (`docs/components/trading-node.md:17`, `:117`; `docs/gap-report.md:169`, CHECKED): the single-machine variant is "ONE product with two placements, never a fork". Its owed design is named: supervision without systemd, the secret store without systemd-creds, the powers channel without a Unix socket, the observability placement, and a self-setup installer. Containers are allowed there. The compose-off-machine refusal is re-scoped from "the VPS" to "the machine the roster names".

### 1.3 How the pieces were meant to connect (DESIGNED, node spine TN-3)

- Three planes, two machines, one bucket. The server plane holds the node, the live connections and the only live credentials. The workstation plane (Windows) holds research, the desktop app, the provisioning wizard and Credential Manager `qmx/*` as the provisioning source. The bucket holds encrypted nightly copies pushed by the server.
- Flows are one-way: node to evidence tier to workstation (SSH pull). Two inbound crossings only: the click-gated promotion pull and the sandbox push into the hub inbox.
- The desktop app reaches the node's doors over an SSH tunnel.
- cTrader allows one demo and one live connection per app, so the node's sensing feed is also the recorder.

None of the PC-side halves (tunnel, pull, hub push, provisioning wizard on the PC) exist in `qmx-agents` (CHECKED, grep above). The PC side today is the QMX host, which knows nothing about QMN beyond the `read_status` import in the agent tools.

### 1.4 Setting up a server today (BUILT, PR 232)

The connect dialog's step runner: his cards (choose and pay for a server "such as Hetzner or Contabo, with Ubuntu on it", the address, a one-off Tailscale key, the server password typed into a terminal QMX opens, the firewall approval), then checked rerun-safe steps, one place row written last, then a smoke run (`qmx-agents/packages/qmx-host/src/qmx_host/connect_compute.py:229-238`; research 42 §2.2). It installs the QMX host as a workflow worker and Library server. Its kinds are storage, compute and deep logs only: `KINDS: Final[Mapping[str, Kind]] = kinds_of(STORAGE, COMPUTE, DEEP_LOGS)` (`qmx-agents/packages/qmx-host/src/qmx_host/connect.py:389`, CHECKED). There is no trading-server kind and it never installs QMN. **A trading node cannot be set up through any shipped path** (research 42 §2.2, re-checked today).

### 1.5 What is automated, and what is his

| Automatic (in code) | His act only (in code) |
| --- | --- |
| KSA escalation (escalate only) | KSA `resume` (de-escalation), per scope |
| Kill-line breach flattens that Book's scope | `resurrect` out of node stand-down |
| Stand-down on a crash loop, a `halt` clock band or a preflight failure | Promotion click, then a separate activation click |
| Reconnect, gap replay, token refresh, heartbeat, verification monitors | `hub_publish` of sandbox fragments |
| Nightly backup, sample restore, monthly full restore (timers) | Setting the KSA matrix values and the seven boot values |
| Liveness ping | Flatten at any scope, any time |

Sources: node spine TN-4, TN-7, TN-20; `trading-node-notes.md` (risk sitting, 20 Aug); module docstrings in §1.1. This matches his rule that "the only automatic transition is a risk rule stopping a unit, logged" (standing order 7) in shape, with one difference to note: the kill line flattens, it does not only stop (INFERRED from TN-8 wording in `trading-node-notes.md`).

### 1.6 Ruling 135, technically

Ruling 135 is a planning lead's decision derived from his rulings 116-118, recorded "so he sees it and can overrule it" (`D:\QMX-worktrees\unit-plan\tracker\qma-v2\research\methodology\26-operator-rulings-and-alignment.md:248-257`, CHECKED). His 31 Oct ruling 9 dropped the "real-money key" question for him and asked for the technical handling. What the code does:

1. **The refusal test.** `can_trade_live(listing)` returns true when the grant's `permissionScope` is not `SCOPE_VIEW` and the grant lists any account with `isLive` true. An unreported scope counts as able to trade (`adapters.py:137-146`, CHECKED).
2. **Where it fires.** At sign-in, before the token pair is stored (`venue_session.py:1-16`, `:288`), and on every read (`service.py:247`, `:345`, `:548`). The message says the sign-in "belongs on a trading server" (`adapters.py:103-115`). It fires on every QMX host, PC or server, because the QMX host is never a trading server (CHECKED).
3. **What is allowed on the PC.** A view-only grant that lists live accounts (live prices, balances, positions, no trading). A trading-scope grant that lists only demo accounts. QMX's own read app only ever asks for scope `accounts` (`oauth.py:31`), so a trading grant can only arrive from outside QMX's own sign-in (INFERRED).
4. **Where the pair lives.** Credential Manager as `qmx/token/ctrader-app` on This PC, or an owner-only file under `<home>/vault/` on a server. The vault refuses any name holding `token`, so the pair never replicates (`venue_session.py:7-10`, CHECKED).
5. **Second wall: there is no order code in the QMX host.** The CCXT and cTrader adapters are read-only (`adapters.py:1`, "Read-only CCXT spot and cTrader Open API adapters"). `propose_order` writes a row to `portfolio.db` with status `awaiting_operator_signature` and `executed: False`; "signing and execution belong to QMN" (`service.py:560-584`). The agent tool says "saving cannot submit or authorize an order" (`functions.py:238-241`). CHECKED.
6. **Third wall: QMN pins its machine.** The runtime config requires the operator-pinned machine identity (`configured_runtime.py:278-280`), and the spine refuses to compose off the roster's server (research 31 §1, spine memlog ruling 18). DEC-0262 re-scopes this to "the machine the roster names".
7. **One app per trading server.** Each trading server registers its own cTrader app, because a refresh on one machine logs out every other copy of the same grant (`26-operator-rulings-and-alignment.md:254`; research 38 §3.1, ProtoOAAccountsTokenInvalidatedEvent). Spotware reviews each app, "usually around 24 hours" (research 38 §3.1).

**What it means in plain words:** his PC can watch live cTrader prices and trade demo accounts, but QMX code on his PC can never place a live order, because the PC holds no live trading key and the PC side has no order code. Live orders can only come from QMN on a machine pinned in its roster. With QMN on the PC (WSL or the single-machine variant), the PC would become that machine, and the refusal in step 2 would still stop the QMX host from keeping the key; QMN would need its own key store there (INFERRED from steps 2, 4 and 6).

---

## 2. Broker and exchange links

### 2.1 cTrader Open API

| Capability | Status | Evidence |
| --- | --- | --- |
| Wire format | BUILT: Protobuf over TLS on port 5035, length-prefixed frames, Spotware's pinned descriptor `openapi-91.pb` shipped in QMX; no Spotware SDK, no Twisted. JSON (port 5036) is not used | `packages/qmf-venue/src/qmf/venue/connection.py:13-17`; `qmx-agents/packages/qmx-broker/src/qmx_broker/protocol/openapi-91.pb`; research 38 §3.1 |
| Sign-in | BUILT, NEVER RUN on his real folder: his browser opens cTrader's consent page (`id.ctrader.com`), a loopback receiver on `127.0.0.1:47613` takes the one code, the host exchanges it at `openapi.ctrader.com/apps/token`, refuses a live trading grant, stores the pair | `oauth.py:1-35`; `venue_session.py:1-16` |
| Token lifecycle | BUILT: access token about 30 days, refresh token never expires; refresh before a read; one refresher per credential reference in QMN | `packages/qmf-venue/src/qmf/venue/ctrader.py:24-29`; `qmn/src/qmn/secrets/rotation.py` docstring; PR 221 |
| Reads on the PC | BUILT: accounts, balance (with `moneyDigits`), positions (`ProtoOAReconcileReq`), one spot quote, trendbars by period, symbol specs; each read stamped `{environment, is_live, connection_id, account_id, result}`; a session that proves the other kind fails as `environment_mismatch` | `adapters.py:155-301`; `ctrader_transport.py:13-26`; `service.py:522-556` |
| Read session shape | BUILT: one short TLS session per read on the PC; the long-running connection manager lives in qmf-venue and QMN | research 42 Q11; `ctrader_transport.py:1` |
| Order placement | BUILT in QMN, NEVER RUN: `ProtoOANewOrderReq` (2106), `CancelOrderReq` (2108), `AmendPositionSLTPReq` (2110), `ClosePositionReq` (2111) | `packages/qmf-venue/src/qmf/venue/encode.py:50-69`; `qmn/src/qmn/venue/live.py:24-35` |
| Live market data in QMN | BUILT: spot, trendbar-in-spot and depth wire kinds; depth sizes in cents | `qmn/src/qmn/venue/live.py:142-206` |
| Market-wide trades tape, real volume, open interest | Not offered by cTrader | research 38 §3.1 (protocol file), research 21 §3 |
| Rate limits and heartbeat | BUILT: 50 requests/s, 5/s history, 10 s heartbeat bound, one-week tick span | `ctrader.py:123-145` |
| Money scales | BUILT: prices in 1/100000; execution prices raw doubles crossed at a named boundary; `moneyDigits` on nine messages | `ctrader.py:12-22`, `:147-160` |
| No server clock | Fact encoded: "no server clock exists on the Open API", receive time recorded on every message | `ctrader.py:14-17` |
| Reconnect | BUILT in QMN, NEVER RUN | `qmn/src/qmn/venue/reconnect.py` |
| Dead man's switch | None at cTrader | research 38 §3.1 |
| Exchange futures | Not available through cTrader | research 38 §0 item 1; Spotware calls cTrader a "Premium FX/CFD trading platform" (https://www.spotware.com/ctrader/, CHECKED today) |

### 2.2 CCXT (crypto)

| Capability | Status | Evidence |
| --- | --- | --- |
| Version | BUILT: `ccxt==4.5.85` pinned | `qmx-agents/packages/qmx-broker/pyproject.toml:6`; `qmx-agents/uv.lock:412-413` |
| Reads | BUILT: balances, positions (spot balances), quotes, bars, symbol specs | `adapters.py:304-412` |
| Contract markets (perps, futures) | Refused: a symbol must be `spot` true, `contract` false, `active` true | `adapters.py:330-338` |
| Orders | MISSING (no `create_order` outside a test fake) | `git grep -n -E "create_order|createOrder" -- '*.py'`, CHECKED |
| Demo rows | BUILT: a demo row on an exchange with no demo mode is refused (asks CCXT) | PR 224; `qmx-agents/packages/qmx-broker/src/qmx_broker/sandbox.py` |
| WebSocket streams | MISSING in QMX. CCXT's own `watch*` methods are free and MIT-licensed inside the `ccxt` package | context7 `/websites/ccxt` FAQ ("CCXT Pro is included in the ccxt package"), CHECKED |
| Public data downloader | BUILT: `download-ccxt` and `download-binance` workflow templates; `ccxt_public` and `binance_vision` provider probes | research 42 §1.8; `providers/__init__.py:1-19` |

### 2.3 Hyperliquid

MISSING. No code anywhere: `git grep -l -i hyperliquid` finds only four old `workroom/` notes (CHECKED). CCXT documents a `ccxt.pro.hyperliquid` exchange (context7 CCXT FAQ, CHECKED), so the pinned CCXT may reach Hyperliquid, but QMX's CCXT adapter refuses its perps as contract markets (`adapters.py:330-338`). Whether 4.5.85 carries the Hyperliquid class was not checked locally (no installed venv found, INFERRED likely). Venue facts: research 38 §3.8.

### 2.4 MetaTrader 5

DESIGNED as a declaration only: auth `terminal_session`, reads listed, `runs_on=("windows", "windows_or_wine")` (`adapters.py:59-72`, CHECKED). No adapter class. One probe script imports `MetaTrader5` to test an investor (read-only) login (`scripts/probes/data/p_ctscope.py:188-200`, CHECKED). Earlier research: the Python package is Windows-only, talks to a running terminal over local IPC, has no push events, and one terminal serves one account (`workroom/research/05-broker-connectivity.md` §3, 17 Aug).

### 2.5 Data providers

| Provider | Status | Evidence |
| --- | --- | --- |
| Databento | BUILT as a key check only: one metadata call "proves the key and the plan, without a data charge"; reads declared `bars, trades, instrument_specs`, none implemented | `providers/databento.py:1-59` |
| Dukascopy | BUILT: provider probe plus the `download-dukascopy` template; old 10 GB ticks import script not run on the PC | `providers/dukascopy.py`; research 42 §4 |
| Binance Vision | BUILT: probe plus `download-binance` | `providers/binance_vision.py` |
| Rithmic, CQG, Tradovate, IBKR, Tardis, dxFeed | MISSING | `git grep -i -E "rithmic|tradovate|ibapi"` beyond research 18's search, INFERRED none; research 38 §10 |

### 2.6 Summary per link

| Link | Orders | Positions | Fills | Account state | Market data | Reconnect | Tag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cTrader in QMN | yes (5 kinds) | read-back | yes, deal id is the fill key | yes | spot, depth, bars | yes | BUILT, NEVER RUN |
| cTrader on the PC host | no (by design) | yes | no | yes | one quote, bars | per read | BUILT, NEVER RUN on his folder |
| CCXT | no | spot balances | no | balances | ticker, bars (REST) | per call | BUILT (spot reads) |
| Hyperliquid | no | no | no | no | no | no | MISSING |
| MT5 | no | no | no | no | no | no | DESIGNED (declaration) |
| Rithmic, CQG, Tradovate, IBKR | no | no | no | no | no | no | MISSING |
| Databento | n/a | n/a | n/a | n/a | key check | n/a | BUILT (probe only) |

---

## 3. Live-trading contracts that exist

### 3.1 The chain, as built

```
unit or bot (QML CT-33 declaration, in a QMN seat)
  -> CT-23 intent: EntryIntent or ExitIntent (no size)            packages/qmf-risk/src/qmf/risk/door.py:163-175, 559-580
  -> Book door: size resolved, R frozen -> AuthorizedIntent        qmn/src/qmn/order/door.py:135-157
  -> BMS binding, KSA, windows, clock band, protection gate         qmn/src/qmn/seats/dispatch.py, protection/*
  -> CT-19 Command (five kinds) on one (VenueId, account) stream   packages/qmf-venue/src/qmf/venue/commands.py:127-181, 735-754
  -> VenueClientPort.submit -> SubmissionResult (four outcomes)    qmn/src/qmn/venue/port.py:49-101
  -> CT-20 events: recorded verbatim, then folded into order state packages/qmf-venue/src/qmf/venue/events.py:127-209
  -> reconcile(): reconciled | drift | unknown | out-of-lookback   events.py:181-193
  -> CT-29 exit record per virtual-position close                  docs/contracts/ct-29-exit-record.yaml
  -> CT-13 journal                                                 docs/contracts/ct-13-journal.yaml
```

### 3.2 The shapes

| Shape | Fields and law | Evidence |
| --- | --- | --- |
| `EntryIntent` (CT-23) | `instrument`, `direction`, `reason_code`, `execution_target`, optional advisory `proposed_r`, `cited_evidence`, `advisory_stop_proposal`. No `requested_r`: "the bot may not size" | `door.py:559-580`, CHECKED |
| Intent families | exactly two, `entry` and `exit`; exit kinds `close_full` and `tighten_protective_stop`; no partial close | `door.py:163-186`, CHECKED |
| `AuthorizedIntent` | `admitted`, `faces` (R faces), `requested_r`, `admitted_quantity`, `r_unit_price`, `original_risk_amount` | `qmn/src/qmn/order/door.py:135-157`, CHECKED |
| `Command` (CT-19) | `kind`, `venue_id`, `account`, `session_epoch`, `ordering_ordinal`, `order_parameters` (order type, time in force, quantity, limit, stop, protective stop distance, native ids), `close_scope`, `subject_reference`, `protection_amendment` | `commands.py:345-366`, `:735-754`, CHECKED |
| Command kinds | `place_order`, `cancel_order`, `close_position`, `close_all`, `amend_protection`; "addable, never redefined" | `commands.py:127-140` |
| Outcomes | `accepted-by-venue`, `rejected-by-venue`, `denied-locally`, `UNKNOWN`; `partially-executed` for a compound parent only; a timeout is never a rejection; nothing retries on UNKNOWN | `commands.py:184-240` |
| `amend_protection` | risk-non-increasing on the stop side against the frozen original risk distance | `commands.py:600-616` |
| CT-20 events | observation kinds: submission acknowledgement, fill, cancel acknowledgement, expiry, close-by-venue, out-of-sequence; order states fold at read time and are never stored | `events.py:127-163` |
| Reconciliation | on demand, over a mandatory declared lookback (do-not-default) | `events.py:36-43`, `:181-193` |
| Capability declaration (CT-18) | static declaration plus a measured venue-observation profile; an error map where an unmapped code means `UNKNOWN` plus an alarm; daily boundary and bar basis measured per broker, never hardcoded | `packages/qmf-venue/src/qmf/venue/capabilities.py:1-40`; `ctrader.py:30-35` |
| `VenueClientPort` | `kind`, `venue_id`, `world`, `open_session`, `close_session`, `verify_capabilities`, `submit`, `observations`, `reconcile`. Kinds are a closed enum: `ctrader`, `replay`, `conformance`; live selection refuses anything else | `qmn/src/qmn/venue/port.py:40-101`, `:107-190` (live branch at `:171-190`), CHECKED |
| Broker read result (PC) | `{environment, is_live, connection_id, account_id, result}` | `service.py:522-556`; PR 215 |
| `OrderProposal` (agent) | `account`, `symbol`, `side`, `quantity` (decimal string, never a float), `reason`; stored with status `awaiting_operator_signature`, `executed: False` | `qmx-agents/packages/qmx-tools/src/qmx_tools/service.py:126-139`; `qmx-broker/.../service.py:560-580` |
| CT-29 exit record | one per virtual-position close; frozen R faces; fill references; cost components; one typed close reason from a closed, addable taxonomy | `docs/contracts/ct-29-exit-record.yaml:1-30` |
| Library `trade` kind | account, instrument, side, `world` (backtest, paper, demo, live, synthetic), `initial_risk` | research 42 §6.1 (`LIB/kinds/trade.schema.json`) |
| Library `unit` kind | page exists (Logic, Results, Family tree, Markets, Versions); no fields; nothing writes one | research 42 §6.1 (`LIB/kinds/unit.schema.json:7-10`) |

---

## 4. What the foundation can reuse as is

| What | Why it fits | Where |
| --- | --- | --- |
| The CT-19 command law and CT-20 event law | Venue-neutral, already cover every hard order case (UNKNOWN as a state, idempotent ids, compound commands, record before interpret) | `packages/qmf-venue/src/qmf/venue/commands.py`, `events.py` |
| CT-18 capability declaration plus measured profile | A new venue (Hyperliquid, a futures FCM) is declaration data plus measurements, not new law | `capabilities.py`, `observation.py` |
| The cTrader transport and token lifecycle | Ready for the first live venue; never run | `connection.py`, `ctrader.py` |
| QMN's protection set, reconcile, pacer with a protective reserve, clock bands | The live-side safety code the unit needs regardless of who sizes | `qmn/src/qmn/protection/`, `reconcile/`, `order/pacer.py`, `time/` |
| The one-refresher-per-credential rule and per-machine app | The cTrader knock-off trap is already solved in design | `qmn/src/qmn/secrets/rotation.py`; ruling 135 text |
| Read adapters with declared published limits and error maps | A registry shape every new venue can fill | `qmx-agents/packages/qmx-broker/src/qmx_broker/registry.py`; `adapters.py:20-72` |
| Demo/live stamp on every read, and the live-grant refusal | Journals can carry the world of every figure; keys stay off agent machines | PR 215; `adapters.py:103-146` |
| The connect dialog's step runner | The shape a trading-server setup could take: his cards, checked steps, rerun-safe, one row last | `connect.py:374-389`, `connect_compute.py` |
| The liveness heartbeat | Watches a node that cannot speak | `qmn/src/qmn/observability/liveness.py` |
| Staged order proposals | Agents can propose; only the node executes | `service.py:560-584` |

## 5. What must change (facts that clash with rulings; no design here)

| Fact in code | Clashes with | Evidence |
| --- | --- | --- |
| The entry intent carries no size; the seat door says "bot never sizes" | STATE correction 2: the unit owns its risk and sizing | `door.py:559-571`; `seats/dispatch.py` docstring |
| No per-bot paper on the node (DEC-0261) | Judging needs per-unit paper (STATE judging section) | `qmn/src/qmn/paper/lane.py` docstring |
| QMN's only host profile is offline replay | A unit running live on the node | `configured_live_resources.py:38-58` |
| `VenueClientKind` is closed to `ctrader`, `replay`, `conformance` | Hyperliquid second, futures later (morning ruling 10) | `port.py:40-45`, `:171-190` |
| QMN is Linux and systemd only | Windows first-class (morning ruling 7); local first (rulings 136-139); DEC-0262 owes the single-machine design | §1.2 |
| QMN has its own Grafana, Loki, Prometheus stack | QMX moved to OpenObserve (DR10, PR 232) | research 42 §3; `qmn/deploy/observability/` |
| No trading-server kind in the connect dialog | "a trading node should be as simple as how, for example, I can set up a server from a provider" (his words, `operator/transcript-2026-10-29-to-30.md`, 30 Oct 07:31) | `connect.py:389` |
| CCXT adapter is spot reads only | Perps and Hyperliquid; crypto "through CCXT (already built)" (morning ruling 10) | `adapters.py:330-338` |
| Only the `forex-17NY` market-hours calendar exists | Futures, indices, metals, perps sessions | `extensions/qmf-calendar-forex/`; research 02 short answer 6 |
| `tzdata` pinned at 2025.2; PyPI's latest is 2026.6 | Correct clocks across regions (morning ruling 15) | root `uv.lock:2002-2003`, `qmx-agents/uv.lock:5296-5297`, `extensions/qmf-calendar-forex/pyproject.toml:11`; https://pypi.org/project/tzdata/ (CHECKED today) |
| No clock check on the QMX host side | Monitoring nodes in several regions together | grep in §0 item 6 |
| QMN's CI lane does not run on `engine/base` PRs | Any change to QMN in this build | `.github/workflows/qmn-ubuntu-24.04.yml:9-14` |
| Docs say VPS only, no per-bot paper, bot never sizes | His newer rulings | `docs/components/trading-node.md:17-23` |

## 6. Traps

1. **Never-run code reads as finished.** About 97,000 lines of QMN plus the cTrader sign-in have no recorded real run. "Coded is not built until run" (his direction, STATE). Plan the first real run early.
2. **A live QMN root cannot compose today**, even with every value set, because no live host profile is registered (§1.1).
3. **cTrader has no dead man's switch.** A dead node leaves only the stops already at the broker, so the venue-resident stop rule (`order/protection.py`) is load-bearing (research 38 §7).
4. **A token refresh logs out other machines on the same grant.** Two machines must never share one cTrader grant (research 38 §3.1).
5. **cTrader has no server clock.** Every cTrader time is the receive time on the local machine, so a drifting PC clock corrupts every latency, staleness and session number (`ctrader.py:14-17`).
6. **His PC's clocks are not disciplined.** Windows Time is stopped, start type Manual, `SpecialPollInterval` 16384 s (CHECKED today, `Get-Service w32time`, registry). The WSL clock was unsynchronised (research 31). chrony, which QMN expects, does not run on Windows (chrony FAQ §8.1 heading, https://chrony-project.org/faq.html; answer INFERRED).
7. **WSL shuts itself down when idle** unless both timeouts are changed, and systemd does not keep it alive (research 31 §6.2).
8. **The CCXT "already built" link cannot trade or read perps.** He believes crypto is covered; reads of spot are, trading is not (§2.2).
9. **MT5 forces Windows and a running terminal per account.** An MT5 unit makes the trading machine a Windows machine (§2.4).
10. **Ruling 135 and the single-machine variant pull in opposite directions.** The QMX host refuses live grants everywhere; QMN on the PC would need its own key store on the PC. The foundation should name which process owns a live key on each placement (INFERRED; §1.6).
11. **The kill line flattens; standing order 7 says a risk rule "stopping" a unit is the only automatic transition.** Same spirit, different verb; worth a line in the unit's risk socket (INFERRED).
12. **The calendar and tz database lag.** One FX calendar and a tzdata pin two IANA years old (§5).

## 7. Not verified

- No QMN, broker or sign-in code was run. Behaviour is read from code, docstrings and PR bodies.
- Whether CCXT 4.5.85 contains the Hyperliquid exchange class (no installed copy found).
- Whether any real cTrader sign-in has happened since PRs 211 and 221 merged on 31 Oct (no file I read records one).
- WSL's clock state today (not re-run; research 31 read it on 30 Oct).
