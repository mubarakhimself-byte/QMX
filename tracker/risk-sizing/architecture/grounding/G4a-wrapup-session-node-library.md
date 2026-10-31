# G4a: the wrap-up session, the trading node and the Library, checked against the code

Grounding agent G4a, 2026-10-31, after his midday rulings 24 to 30. Read and record only. Nothing here is a design. No repo, branch, worktree or PR was changed.

## How to read this

**Code truth.** The read-only checkout of `origin/engine/base` at `c93407ca` (`D:\QMX-worktrees\engine-base-read\`). `git ls-remote` today shows `engine/base` still at `c93407ca` and PR 204's branch `build/wu4` at `aabb813b` (CHECKED). Paths without a prefix are under that checkout.

**Status tags.** BUILT = merged on `engine/base`. STACKED = on a branch or an open PR. DESIGNED = in a plan, design file or chat only. DROPPED = decided against, in his words or a ruling.

**Labels.** CHECKED = read at the cited path and line, seen in the cited command output, or read in the cited message today. INFERRED = my reading of checked facts.

**The session.** "QMX wrap-up coordination", 24 to 29 Oct, extracted at `operator/session-wrapup-coordination-2026-10-24-to-29.md`. Session citations name the message by its timestamp header, for example "session 10-27T17:51". His words are quoted from it as dictated.

**What I read, honestly.** Every operator message in the session, in full. Every lead reply up to 26 Oct 06:17 in full, and after that every lead reply longer than a few lines (the short ones are progress lines such as "Reading the diff"). The 178 builder and reviewer reports (about 920 KB) I read by topic: every report that touches QMB, the node, cTrader, CCXT, the Library, the local-first walk and the first start, found by search. Every claim below that rests on a report says so. The planning files I read by their section lists, then the sections the questions needed. I did not copy the server address or any key path from the session's pasted prompts.

---

## 0. The short answer

1. **The wrap-up session did no trading-node work at all.** Every builder report says "No QMB, QMF or QMN edit" except the backtest door's, and `git diff --stat f05fc64b c93407ca -- qmn` is empty (CHECKED). The node was explicitly scheduled for "a fresh session" with the question "how to cut today's QMN (about 98,000 lines, never deployed) to the basics" (`tracker/qma-v2/HANDOFF-2026-10-24.md:295-301`, CHECKED). That session never happened. His belief that the wrap-up "should have shipped stuff containing that trading node" is wrong, and one likely cause is a word clash: the wrap-up built `qmx node setup`, which sets up a QMX server (workflows, Library, Hub), not the trading node (`qmx-agents/packages/qmx-control/src/qmx_control/node.py:1-30`, no `qmn` reference, CHECKED).
2. **The node is 98,063 lines, built 31 Aug to 4 Oct by the old factory, untouched since 7 Oct except one caller move on 22 Oct** (`git log` per date, CHECKED). About 11,200 of its lines are proof campaigns and readiness packets that only tests and a QA matrix reach (§2.3). Its real trading parts (cTrader client, orders, reconcile, kill switch, kill line, clock bands, secrets) are worth keeping. It cannot run live today because its only host profile is offline replay (`qmn/src/qmn/host/configured_live_resources.py:24-57`, CHECKED).
3. **"Nothing merged has run on his PC" is misleading.** The code ran on this PC many times: `just ci` on Windows for every PR, and throwaway starts, including a 77-check end-to-end first-start run on a blank profile (session 10-27T17:51). What never happened is the first real start on his own data with his logins, which his own brief asked for (item 4) and the session never reached (session 10-28T15:48). No new-layout QMX folder or pointer exists; his old `~/.qmx` was last written 21 Oct (CHECKED, `ls`).
4. **QMB as a tool for agents was designed and half built, then parked on his word.** He said "agents control QMB as a tool" on 21 Oct (QMA v2 design session, 10-21T15:21). The wrap-up built it as PR 204: a backtest from a chat or a workflow runs in its own process and lands one result the copilot can read back. Its only runner makes no trades. On 24 Oct he said to "leave it alone completely" for the unit session (session 10-24T19:04). It is open, conflicts with trunk in two files, and every conflict is two sides adding lines (§4.3).
5. **The cTrader sign-in is a view-only sign-in on his PC.** It asks cTrader for the `accounts` scope only and refuses any grant that could trade a live account (`qmx_broker/oauth.py:31-32`, `adapters.py:137-146`, CHECKED). It has never been done for real. His cTrader app "QMX-NODE" already has QMX's return address registered and is allowed to trade (session 10-24T18:59).
6. **CCXT 4.5.85, the pinned version, already contains Hyperliquid with order placement, positions, funding, open interest, order book, leverage and testnet** (`ccxt/hyperliquid.py:59-129`, `:158-160` in an installed copy, CHECKED). QMX's own CCXT adapter refuses every contract market and has no order code (`adapters.py:330-339`, CHECKED).

---

## 1. What the session designed and decided, and where each item stands in code

### 1.1 The programs it ran (28 PRs on trunk, one left open)

| Program | PRs | What it gave | Status | Evidence |
| --- | --- | --- | --- | --- |
| Wrap-up must-fixes | 198 to 203, 205, 206 | Mini-app tools reach chats; provider tests; keys; template installs into the real Library and the PC writer fix; `just ci` green; real copy counts; cTrader demo sign-in (server version); the server ready to be home with a firewall and `qmx-recover` | BUILT (landed 26 Oct, `d82be318`) | `RESUME.md` "Update 2026-10-26 morning" (`D:\QMX-worktrees\qma-ship\wrapup\RESUME.md`), CHECKED |
| Backtest door (WU4) | 204 | One function lands every backtest from a chat or a workflow, replay in a child process | STACKED, open, parked for the unit session | `gh pr view 204`: OPEN, base `build/wu2`, head `aabb813b`, CHECKED |
| cTrader reads through the server, broker history (WU10) | none | Reads forwarded to the server, a `download-broker` template | DESIGNED, gated on his sign-in | `tracker/qma-v2/WRAPUP-PLAN.md` section WU10, CHECKED |
| Local first | 207 to 214 | Price door open by default; monitoring off by default; one folder resolver; the folder tree; cTrader signed in on This PC; places he names; store versions; bringing old data in | BUILT (landed 31 Oct, `c93407ca`) | `LOCAL-FIRST-PLAN.md` sections; G2 §11, CHECKED |
| Mock data | 215 to 217 | Templates use the real Library; every broker read says demo or live; old imported runs land nothing | BUILT | session 10-27T04:52; PR titles in G2 §11 |
| Loose strings | 218 to 224 | Bring-in as a job; resumed runs land; run inputs from REST and triggers; cTrader out of the box; template install as a job; the host names what did not open; CCXT demo rows refused on 54 exchanges | BUILT | `LOOSE-STRINGS-PLAN.md` sections, CHECKED |
| Backup and restore | 225 to 229 | Copies on This PC and a second drive, restore, automatic copies, restore from the card and Settings | BUILT | session 10-28T13:10, 10-28T18:58 |
| Sync and connect | 230 to 234 | What is saved, by class; connect a storage; packed copies through rclone; connect a server, Modal, E2B and deep logs from one dialog; install, first start, sync before update | BUILT | session 10-29T11:22, 10-29T13:23 |
| Library attach on his click, file upload | none | Five PRs planned | DESIGNED, parked (plan review found 10 serious problems) | session 10-28T15:42, 10-28T15:48; `ATTACH-PLAN.md` |
| Seeing and controlling other machines from the PC | none | A queue item, then left to the UI agent | DESIGNED | session 10-27T04:11; `qma-ship\wrapup\evidence\machines-design-vs-backend-2026-10-27.md` |
| First real start with him, the five journeys, cTrader sign-in with him, one trunk on `main`, docs, backlog triage | none | His brief items 3 to 8 | Not done | session 10-28T15:48 ("Not done from your original brief") and nothing after it, CHECKED |

### 1.2 Decisions and rulings it recorded, by the area the unit work cares about

| Item | His words or the decision | Status in code | Evidence |
| --- | --- | --- | --- |
| The PC is home; servers stand in or expand, never replace (rulings 136, 140 to 143) | "The whole point of having servers in this entire system is not to replace the PC" (session 10-25T14:57) | BUILT for defaults and places: no server in defaults (208), places with This PC built in (212), folder and bring-in (209, 210, 214) | PR titles; `qmx_home/classes.py`, CHECKED |
| No lock that refuses by default (ruling 137); a holdout is his choice per study | "why are you refusing me?" (10-25T14:57) | BUILT: the price door opens by default (207). One template still hard-codes a family holdout (G2 §4, `b-build-and-prove/scripts/spec.py`) | G2 §4, CHECKED there |
| Units, not bots (ruling 138) | "we are no longer using bots. We are using units" (10-25T14:57) | Vocabulary only. Code still says bot everywhere (QML, QMB, QMN) | INFERRED |
| A way back into the server by hand (ruling 139) | "some sort of script ... that allows me to patch in" (10-25T14:57) | BUILT: `qmx-recover` on the server and a PowerShell twin on the PC | G2 §10 row "server recovery script", CHECKED there |
| External compute is an optional extra, designed with the UI in mind (144); the copilot walks him through adding a server, wizard pattern (145) | 10-26T04:40 | 144 DESIGNED into UI notes; 145 DESIGNED, backlog for the methodology session | session 10-26T04:41 |
| The Library "move to the server" card | Cancelled with ruling 136 (10-25T14:58) | DROPPED as a card, but the flip code is still in the host (`qmx_host/host.py:58`, `:635-682`) | CHECKED |
| Save the recipe, not the cake: copy by class; units are lean JSON | "Units are going to be lean, I believe, by design" (10-28T17:03) | BUILT: one class table decides what travels (231). Results include `data/backtests/**` and `backtest-result`; a reserved row `data/node/**` is "a trading node's state on this PC" (`qmx_home/classes.py:120`, `:130`, `:162`) | CHECKED |
| His strategy workflows and QMX's own upkeep workflows are two kinds | "please don't confuse agentic workflows and external workflows" (10-28T17:10) | DESIGNED in the sync design; I found no marker in the template catalog (`git grep -i maintenance` on `templates/catalog.py`: none) | CHECKED |
| One step-by-step connect dialog for storage, compute, a GPU and deep logs | "it can be one question, then another question" (10-28T17:10) | BUILT for storage, compute and deep logs (230, 232). No trading-server kind (`qmx_host/connect.py:389`, G3 §1.4) | CHECKED in G3 |
| OpenObserve self-hosted, one program; agents read-only | 10-28T17:10; lead 10-28T17:58 item 8 | BUILT: Windows build v1.1.2 downloaded, checksum checked and pinned (session 10-29T13:57). Never run against real telemetry | session; G2 §8 |
| No passphrase lock on copies | "I don't think it makes sense for us to lock" (10-28T18:26) | DROPPED (backup PR 7, the sealed key copy). Secrets never travel | session 10-28T18:27 |
| QMB belongs to the unit session; leave the backtest PR alone | "I would argue that you leave it alone completely" (10-24T19:04) | PR 204 STACKED; handoff `tracker/qma-v2/QMB-BACKTEST-DOOR-HANDOFF.md` | CHECKED |
| The trading node in its own fresh session | written by the lead before the session (`HANDOFF-2026-10-24.md:295-301`) | Not started. No node code changed | CHECKED |
| Mock data must not reach live use | "I hope overall in the entire system of QMX you haven't left any mock data" (10-26T15:45) | BUILT in the backend (215 to 217). The desktop app's default demo account ("IC Markets live", $31,560) is the UI session's | session 10-26T16:05 |
| The Library is a graph | his question 10-27T04:34 | BUILT: a unit kind's pages are walks along links ("Logic" follows `uses`, "Results" follows `produced by`, "Family tree" follows `variant of`); storage is a versioned object store with an edge table | session 10-27T04:35; G3 §3.2 row "Library unit kind" |

### 1.3 What it never touched

QML, QMB (except PR 204's two files), QMF, QMN, the MIS and journals. CHECKED: the phrase "No QMB, QMF or QMN edit" ends nearly every builder report; the backup reader found one QMF file touched by the backup work (the price store waits up to about 1.3 s when a backup reads its file) and said "The backup work changed nothing in the trading node" (session report before 10-28T16:33).

---

## 2. Answers to the questions

### 2.1 "Nothing merged has run on his PC yet; no QMX folder exists in the new layout"

**What the first grounding meant.** G2 checked for the folder the new host uses (CHECKED today, the same result):
- No pointer file `%APPDATA%\QMX\home.toml`, which PR 209 adds so QMX can find his folder.
- No folder at `~\QMX`, `C:\QMX`, `D:\QMX`, `E:\QMX` or `F:\QMX`. The design named `D:\QMX` (session 10-26T05:23); the code's default is the roomiest drive that is not the system drive, else his profile (`qmx_home/__init__.py:734-741`, G2).
- Only the old flat folder `C:\Users\Mubarak\.qmx` exists: `control.db`, `library.db` and `runs.db`, last written 21 Oct, plus `artifacts/`.

**Who creates the new folder.** The first-start card, the first time the new host starts: new folder, open one, restore, or bring in the old data (PRs 214, 219, 234). Bringing in copies the old folder, checks every file's fingerprint, converts the copy only and never writes the old one (session 10-26T17:41).

**Why a QMX folder at all.** It is his own ask from 26 Oct: "my data is still local ... data and QMX shouldn't be very, very, very related", with his Whisperflow and mobile-game examples (session 10-26T04:36). Rulings 140 to 143 put his data in one folder the program never owns, so an uninstall or a broken release never touches it. So the folder is the local-first design he asked for, not an extra.

**What "run" means here.** He is right that everything is coded on this laptop, pushed and merged. Merging moves a branch on GitHub. It does not install QMX or start it on his data. In this session's sense, "run" means QMX started as his app on his own folder, with his logins. That has never happened for the new host. The code did run on this PC in other ways (CHECKED in the session):
- `just ci` on Windows for every PR, which includes the node's and QMB's tests (`tools/test_all.py:61-62`).
- Lanes on throwaway homes, for example the 77-check first-start run on a blank profile: first-start card, bring-in, workflows, template installs, a cTrader demo read against a fixture, and a one-hour EURUSD download into the test folder (session 10-27T17:51).
- Server checks on his real server, which was restored to empty after each check (session 10-25T16:35, 10-25T17:48).

**Does it matter.** Yes, in three plain ways (INFERRED from the facts above):
1. His Library today lives in the old store, which the new host does not read until a bring-in runs. Any design that expects his items or price months in the Library on his PC finds an empty Library.
2. No broker sign-in exists yet, so no cTrader read on his account has happened.
3. Never-started code hides bugs. The session found "on your PC, QMX cannot save anything to the Library" by reading code, not by a run (session 10-24T12:36). The dummy unit's proof run will also be the first real start, so the plan should treat the first start, the bring-in and the price downloads as named steps.

### 2.2 The trading node: what the wrap-up shipped, why it is 98,000 lines, and what ruling 27 needs

**What the wrap-up shipped or stacked for it.** Nothing (§0 item 1). The one later commit touching `qmn` is `76f5b205` (22 Oct, the deletion program, moving callers off `qma-core`), before the wrap-up started (CHECKED, `git log --since=2026-10-08 -- qmn`).

**Where the 98,000 lines came from.** The node spine TN-1 to TN-25 (28 Aug), built as factory stories 24.x to 28.x and epics 59.x between 31 Aug and 4 Oct; 7 Oct only formatting and the test baseline (CHECKED, `git log` dates, module docstrings naming "Story 25.16", "Story 28.3" and so on).

**What is in it, by area** (CHECKED: `git ls-files` line counts; the code, docstring, comment and blank split by a scratch script using Python's `ast` and `tokenize`):

| Area | Lines (code) | What it does (from its docstring) | For ruling 27 (INFERRED) |
| --- | --- | --- | --- |
| `host` | 26,602 (23,767) | Composition root, boot ceremony, supervision, configured runtime, risk population, fencing, plus proof campaigns and readiness packets (below) | Split: the root and supervision are needed in some form; about 11,200 lines are proof machinery |
| `mis` | 12,654 (11,145) | Execution-health labelers (identity, spread, gaps, feed, SQS, degraded sensors), a quantile liquidity fit, an untrained regime classifier; publishes only to the Book door and the kill switch, "never bots" | Rethink: units must be able to read it, and it is not market condition yet (G1 §6) |
| `venue` | 7,478 (6,433) | The live cTrader client, reconnect and gap replay, capability check at connect, spot paper | Keep |
| `data` | 7,160 (6,240) | Live observation intake, history bootstrap, news calendar, sealed sync to the workstation | Keep intake; news is out for now (his 31 Oct ruling 13) |
| `ledger` | 5,516 (4,896) | Exact virtual ledger and virtual positions per Book binding | Keep the ledger; "per Book binding" is the Book premise |
| `order` | 5,178 (4,383) | Command identity, protection-priority pacer, UNKNOWN per stream; the Book door freezes R and sizes | Keep, except the sizing seam |
| `seats` | 3,872 (3,450) | Where a bot runs: admission, quarantine on a containment breach, "bot never sizes" | Rethink for units |
| `config` | 3,605 (3,155) | Configuration registry and boot values | Keep the shape; seven boot values are blank (G3 §1.1) |
| `replay` | 3,521 (3,090) | A recorded day replayed as a credential-free decision diff | Useful for debugging; not needed to trade |
| `protection` | 3,150 (2,557) | Kill switch (five levels, escalate-only), effect matrix with blank values, news windows and dead zones | Keep |
| `promotion` | 3,122 (2,684) | Human-only promotion running a silent battery, activation as a second click at the next day boundary | Keep his click; the battery is the old Book flow |
| `paper` | 2,788 (2,375) | Book-level paper only, "never a per-bot warm-up ... or paper lane" | Clashes with per-unit paper (G3 §5) |
| `observability` | 2,488 (2,076) | Health states, liveness heartbeat, a QA failures gate | Keep the heartbeat; logs belong in OpenObserve |
| `bench` | 2,291 (1,950) | Hot-path benchmark harness | Not needed to trade |
| `doors` | 2,014 (1,632) | In-process API, localhost HTTP evidence, Unix-socket powers under `SO_PEERCRED` | The powers door is the Linux-only piece |
| `loop` | 1,349 (1,109) | One loop per (venue, account) stream driving QMB's `run_slice` unforked | Keep: this is the same code in backtest and live |
| `reconcile` | 1,207 (959) | Four verdicts, two exact residuals | Keep |
| `time` | 1,181 (927) | Clock bands, three calendar kinds | Keep |
| `capital` | 1,168 (940) | Kill line on virtual equity, breakeven ratchet | Keep |
| `secrets` | 921 (731) | Two-layer store under `systemd-creds`, one refresher per credential | Keep the rule; the store is Linux-only |
| top level, `testing` | 798 | Package glue, test support | |
| **Total** | **98,063 (85,136 code, 4,011 docstrings, 375 comments, 8,541 blank)** | | |

Beside it: tests 115 files, 42,219 lines; deploy 48 files, 6,353 lines, of which the Grafana, Loki, Prometheus and promtail stack is 13 files and 831 lines. It also leans on two shared packages: `packages/qmf-venue` 10,963 lines (the cTrader wire and the command and event laws) and `packages/qmf-risk` 17,704 lines (the Book door and R faces). CHECKED.

**Dead weight, by the import graph** (CHECKED for who references each module; the label "dead weight" is INFERRED). These `host` modules are reached only by `qmn/host/__init__.py`, the QA matrix `host/qa_debt_matrix.py` and the QA gate `observability/failures_gate.py`, and each has its own test file:

| Module | Lines | Docstring |
| --- | --- | --- |
| `golden_scenarios.py` | 1,984 | "Wire and prove SCN-0006/0008/0010/0011 ... (Story 28.5)" |
| `failure_campaign.py` | 1,671 | "Paper-milestone injected money-path failure campaign (Story 28.3)" |
| `seat_concurrency.py` | 1,428 | "Seat concurrency and end-to-end backpressure proof" |
| `verdict.py` | 1,163 | "TN-23 live-readiness verdict packet and checklist fold" |
| `lifecycle_campaign.py` | 1,018 | "Paper-milestone lifecycle campaign" |
| `concurrency.py` | 961 | "Host concurrency and backpressure proof" |
| `readiness.py` | 941 | "Paper-milestone readiness packet" |
| `qa_debt_matrix.py` | 856 | "machine-readable closure matrix for named node QA debt" |
| `shakedown.py` | 685 | "Layer-2 technical demo shakedown" |
| `security_probes.py` | 505 | "Paper-milestone powers and secret probes" |
| plus `observability/failures_gate.py` | 685 | the QA gate over them |

That is about 11,900 lines of "every part must prove itself" machinery, which he rejected (STATE correction 1), plus `bench/` (2,291) and the second monitoring stack (831 deploy lines). `runtime_risk_gate.py` (1,969), `fencing.py` (1,403), `lineage_persist.py` and `registry_mint.py` are also referenced only from `host/__init__.py` and the QA matrix; whether they are dead or merely re-exported needs a build agent's blast-radius run, not a grep (INFERRED).

**What tests cover it.** 115 test files run in `just ci` on Windows, because `tools/test_all.py:61-62` runs `pytest packages extensions qml qmb qmn` (CHECKED). Five tests are Windows-only (`skipif(os.name != "nt")`, CHECKED). Live-venue tests are marked `live` and excluded (G3 §1.1). Mutation testing covers `order`, `ledger`, `reconcile` and `capital` in `battery.yml:233-292`, but that workflow only runs on pushes and PRs to `main`, `integration` and `rebuild/**` (`battery.yml:4-8`, CHECKED). So the node's logic is well tested against fixtures and has never met a broker.

**What ruling 27 asks, and how much of today's code serves it.**

| His need | What exists | Status | Evidence |
| --- | --- | --- | --- |
| Set itself up on a server | QMN's own installer and recipes, check mode only, never reaching a server; and, separately, the QMX server setup (`qmx node setup`, firewall with a 5-minute undo, `qmx-recover`, Tailscale-only), tested on his real server and restored after | QMN's: BUILT, never run. QMX server setup: BUILT, works, installs `qmx-host`, not QMN. No trading-server kind in the connect dialog | G3 §1.1 "Deploy", §1.4; `qmx_control/node.py:1-30`; session 10-25T17:48 |
| Set up the MIS | `qmn/mis` inside the node; consumers closed to the Book door and the kill switch | BUILT, never run; no unit can read it | G1 §6.1 |
| Everything units need to trade alone | cTrader client, order path, reconcile, ledger, loop over QMB's `run_slice`, clock bands, secrets rotation, heartbeat | BUILT, never run; no live host profile | §0 item 2; G3 §1.1 |
| Kill switches | Kill switch with five levels, kill line, news windows, stand-down on crash loops | BUILT; the effect-matrix values are blank, which blocks live | G3 §1.1 rows "Kill switch", "Kill line" |
| Risk and sizing so money is not lost | The Book door sizes and freezes R; the bot "never sizes" | BUILT, and the opposite of the unit sizing itself | `packages/qmf-risk/src/qmf/risk/door.py:559-571`, G3 §5 |
| Only the node sends orders | The QMX host has no order code; agents only stage proposals awaiting his signature | BUILT, by design | G3 §1.6 |

**Facts a "fresh start or refactor" decision needs** (INFERRED from the tables):
- Keep as working parts: the venue-neutral command and event laws, the cTrader client, reconcile, the order pacer and venue-resident stop, the kill switch and kill line, clock bands, the one-refresher-per-credential rule, the heartbeat, and the loop that reuses QMB's slice runner.
- Cut first: the proof campaigns, readiness packets and QA matrix (about 11,900 lines), the benchmark harness, and the Grafana stack.
- Must be rebuilt whatever is kept: the live host profile, the sizing seam, per-unit paper, the MIS's consumer list, a placement without `systemd` for his PC (DEC-0262, owed), and the connection to the PC's connect dialog.
- The node's logic is not Linux-bound. Only its supervision (`sd_notify`, systemd unit), its powers door (`SO_PEERCRED`) and its secret store (`systemd-creds`) are.

### 2.3 The cTrader sign-in the session built

**What it is.** A sign-in on his PC through cTrader's own page. His browser opens cTrader's consent page; a receiver on `127.0.0.1:47613` takes the one-time code; the host exchanges it with the app's ID and secret from Credential Manager, checks the grant, and stores the token pair in Credential Manager as `qmx/token/ctrader-app` (`qmx_broker/oauth.py:1-35`; `qmx_host/venue_session.py:1-16`, CHECKED in G3 §1.6). The first version kept the token on the server (PR 205); LF7 moved it to This PC when no server exists (PR 211); LS3 made it work out of the box (PR 221).

**Is it read-only.** Yes, twice over (CHECKED):
- It asks only for scope `accounts`: "View only: the read app never asks for `trading`" (`oauth.py:31-32`).
- Any grant that could trade a live account is refused before it is stored, on every QMX host, PC or server (`adapters.py:103-146`, `can_trade_live`). A demo account with trading scope is allowed.

He saw this himself on 31 Oct: "That's just for the local sign-in, not trading node sign-in" (transcript-2026-10-30-to-31, 09:58).

**Has it run.** Not for real. On 24 Oct the lead read his app's settings in his browser, added QMX's return address to his "QMX-NODE" app on his yes and saved it; the app is "allowed to 'Access your accounts and trade'" (session 10-24T18:59). The sign-in day itself never happened (§1.1).

**What the node would need to trade** (G3 §1.6 and §6, plus INFERRED):
1. A grant with trading scope on the live account, stored only on the trading machine. One cTrader app per trading machine, because a token refresh logs out other copies of the same grant (G3 trap 4).
2. A place to keep that token on the node: today `qmn/secrets` under `systemd-creds` (Linux). The PC sign-in code is "the parts that do not depend on where they run" (`oauth.py:1`), so the same flow can serve the node with the `trading` scope.
3. A live host profile, the seven boot values, and the kill-switch matrix values (G3 §1.1).
4. The "QMX-NODE" app may already fit, since it has trade permission; whether it becomes the node's app or the PC's read app is a node-pass decision (INFERRED).

### 2.4 QMB as a tool for agents

**What was designed.**
- His words: "agents control QMB as a tool" (QMA v2 design session, 10-21T15:21) and, later, "It runs the same way you run your tests" (ledger B-02).
- The launch map: "Each algo library publishes one deep door ... QMB: register a sealed strategy, backtest, walk-forward, robustness, compare", one catalog row per door function, "Workflows never shell into the algo half" (`tracker/qma-v2/LAUNCH-AND-CLEANUP-MAP.md:185-191`, CHECKED). DESIGNED.
- The contract: engine AD-31 (`qmb_backtest` door on the QMB placement) and Library AD-29 (one result shape), amended 24 Oct (`QMB-BACKTEST-DOOR-HANDOFF.md:7-9`, CHECKED).

**What shipped on trunk.** The catalog rows `run_backtest`, `backtest_status`, `backtest_results` and `compare_runs` exist and refuse (`qmx_control/catalog.py:285-311`, CHECKED). Seven workflow templates declare `qmb-door` as a need and install as drafts (`templates/catalog.py:63`, G2 §4).

**How an agent runs a backtest today, step by step** (CHECKED):
1. The copilot calls `run_backtest` with a `config_ref`.
2. `DomainContext.run_backtest` looks the reference up. No host registers any configuration, so it answers "Unknown config_ref; ask the host to register a recorded QMB run configuration" (`qmx_tools/service.py:302-306`).
3. If one were registered, it would answer "This host binds no qmb_backtest door" (`:309-313`).
4. A workflow cannot reach QMB at all: trunk's `app_op` node has no QMB route (`git grep -i qmb` on `nodes/app_op.py`: none). PR 204 adds `{app: qmb, job: backtest}` (`origin/build/wu4:.../nodes/app_op.py:23`, `:116`).
5. The only other way is Python in a chat's shell, building QMB's inputs by hand as the tests do. A bare `qmb backtest run` refuses with five missing inputs (G1 header). That is the hand-rolled backtest code he wants agents never to write.

**PR 204's real state** (CHECKED: `gh pr view 204`, the builder reports at session 10-24T14:04 and 14:11, the handoff file):
- Open, mergeable into its old base `build/wu2`, last updated 24 Oct, head `aabb813b`.
- Works: one function `backtest_and_land` lands a backtest from the copilot and from a workflow as one object; the replay runs in a child process; the door answers only on a clean exit with a complete report; `close()` kills children; the copilot reads back what it ran.
- Does not trade: its only runner is `silent`. A real runner needs a typed-partition entry into `execute_recorded_replay_request` (`qmb/src/qmb/host/replay_execution.py:68`, `:120`, `:762-806`), execution inputs a configuration can name, and a unit that can be named by reference.
- Breaks QMB's house rules: `subprocess` and `threading` outside `qmb/orchestrator/`, and the word "engine" in a docstring (`qmb/tests/test_qmb_scaffold.py`).
- The child's memory limit applies only on POSIX.
- Its run configurations live at `<home>/backtests/<ref>.json`, while the new folder layout files backtest results under `data/backtests/**` (`qmx_home/classes.py:130`). A rebase must reconcile the two (INFERRED).

**Its conflicts with trunk** (CHECKED: `git merge-tree --write-tree origin/engine/base origin/build/wu4`): two files.
- `qmx_engine/control_door.py`: one hunk, a docstring.
- `qmx_host/host.py`: seven hunks. Trunk added imports, the backup and connect-dialog wiring at startup, and the shut-price-door router; PR 204 added its imports, the backtest binding at startup and shutdown, and the `qmb_backtests` helper. Every hunk is both sides adding lines, so keeping both resolves each one (INFERRED from the hunks).

### 2.5 The Library and the local-first stack: what shipped, and how units, QMB and journals reach historical data today

**What shipped.** The data round (PRs 171 to 197, merged 24 Oct) built typed monthly price partitions, one market-data door per machine, the downloaders and the `trade` kind (G2 §11). The wrap-up then built everything in §1.1. The Library on any machine is the host's one store; This PC is the primary by default (G2 §7).

**How each consumer reaches historical data today** (CHECKED unless marked):

| Consumer | Path | Works today? | Evidence |
| --- | --- | --- | --- |
| An agent in a chat | `market_*` tools (instruments, bars, features, calendar) through the market-data door; open by default since PR 207; a tool call cannot pass a holdout or run id | Yes, once data exists in the Library | G2 §3 |
| A workflow script | Reads and writes the real Library through the host (PR 216); downloaders are templates (`download-dukascopy`, `download-binance`, `download-ccxt`) | Yes | G1 §5; G2 §4 |
| QMB | Only through PR 204's door, which checks the door, then copies the partitions into an attempt folder; QMB's typed reader `read_typed_replay_source` exists, but the trading replay refuses typed partitions | No backtest that trades can read Library data | G1 §4.3; `replay.py:608-625` |
| A unit's journal | The `trade` kind (29 fields, including `world` and account); no journal kind; nothing writes unit journals | Schema only | G2 §3; G3 §3.2 |
| The trading node | Its own live intake and history bootstrap; no link to the PC's Library beyond the designed one-way pull | Not connected | G3 §1.3 |

**What data is on his PC now.** None in the new layout (§2.1). The old 10 GB of ticks sit on C:, never imported; he chose to keep them there (session 10-24T11:59). The Dukascopy downloader is QMX's own fetcher, because dukascopy-node fetched nothing in a probe (G1 §0 item 12).

### 2.6 CCXT and Hyperliquid

**What exists** (CHECKED):
- CCXT 4.5.85 pinned (`qmx-broker/pyproject.toml:6`).
- `CCXTAdapter` reads spot only: balances, spot balances as positions, quotes, bars, symbol specs. `_market` refuses any symbol that is not active, spot and non-contract with "Select an explicitly active, non-contract spot symbol" (`adapters.py:330-339`). The module calls itself "Read-only CCXT spot and cTrader Open API adapters" (`adapters.py:1`).
- Every read is stamped demo or live; demo proof is CCXT's own sandbox flag, plus Bitget's option flag (`adapters.py:308-318`; PR 215).
- A demo row on any of the 54 exchanges with no sandbox in 4.5.85 is refused when Settings saves it (PR 224; builder report before session 10-27T15:37).
- The public-data downloader `download-ccxt` and probe `ccxt_public` (G3 §2.2).
- In the shared packages, `qmf.venue.spot.SpotMarket`, and in the node, `qmn/venue/spot_paper.py`.

**Hyperliquid.** No QMX code. The pinned CCXT already has it: `ccxt/hyperliquid.py` declares `createOrder`, `fetchFundingRate(s)`, `fetchOpenInterest`, `fetchOrderBook`, `fetchPositions`, `sandbox` and `setLeverage` (`:59-129`), testnet endpoints (`:158-160`), and a streaming twin `ccxt/pro/hyperliquid.py`. CHECKED in the installed copy at `D:\QMX-worktrees\bld-br1\qmx-agents\.venv\Lib\site-packages\ccxt\` (`__version__ = '4.5.85'`).

**What was planned.** The wrap-up planned nothing beyond the demo or live labels and the demo-row refusal. Hyperliquid facts live in research 38 §3.8 (G3 §2.3).

**What opening CCXT beyond spot reads would touch** (paths CHECKED; the list is INFERRED):
- On the PC, reads only: the `_market` filter and positions in `CCXTAdapter`; the CCXT declaration in `qmx_broker/registry.py`; the broker read tools; a per-broker instrument record for contract size, margin, funding and expiry, which is missing today (G1 §5); Library kinds for funding, open interest and trade prints, since QMB replays quotes only (G1 §4.3).
- On the node, orders: `VenueClientKind` is a closed set of `ctrader`, `replay` and `conformance` (`qmn/venue/port.py:40-45`, G3 §3.2); a new client behind the same port; a capability declaration; mapping the five command kinds; its key in the node's secret store; reconcile.
- Ruling 135's wall stays: the QMX host keeps no order code and no trading key, so CCXT orders belong on the node only.
- QMB: perps funding as a carry cost is missing (G1 §4.4).

### 2.7 The old backtesting engine he described

His words point at the old QMX system's backtester ("look at how the old QMX system ... was handling backtesting ... the old one had some things that are partially better", transcript-2026-10-20-to-28 line 1177; "Back then, we didn't have QMB in the old system", line 513). Its design file is `C:\Users\Mubarak\Documents\Claude\QMX-discussion\02-Components\11-backtest-engine.md` (Canonical v1.0, 17 Jul; CHECKED, header and section names). Research 08 recovered it in full (`research/08-old-qmx-testing-and-decay.md` §1.1, §1.4, CHECKED there against the vault).

**What it did** (from research 08 §1.1): a parity replay that ran the same sizing, stops and kill switch as live, with only the data and the fill simulator swapped; a fill simulator per symbol; walk-forward with a minimum trade count per window; a 1,000-shuffle Monte Carlo; PBO by CSCV; pass numbers in R; and WF3 "pool cleaning", which read the trade journals and chose keep, reduce, demote, retire or rehab.

**What QMB should keep from it** (research 08 §1.4, plus INFERRED links to today's code):
1. Parity between backtest and live. Today's node loop already drives QMB's `run_slice` unforked (`qmn/loop/__init__.py` docstring), so the same code path exists in shape.
2. Results in R. QMB results are money only (G1 §4.4).
3. PBO in the battery, and a minimum trade count per window.
4. Report slices by session and regime, and MAE and MFE.
5. A stress stage.
6. A paper window and journal per unit before live. The node has Book-level paper only.

Keep from today's QMB what research 08 §1.5 lists: every try counted, honesty labels on shuffled or synthetic runs, raw measures judged later, fingerprinted runs, costs from real fills (calibration still empty).

---

## 3. Corrections to the first grounding

| # | Claim (where) | What is true | Evidence |
| --- | --- | --- | --- |
| 1 | "Nothing merged has run on his PC yet ... every BUILT row is also NEVER RUN on his real home" (G2 header fact 1; G2 trap 1; G3 trap 1) | Misleading. The code ran on this PC in `just ci` and on throwaway homes for every PR. What never ran is the first real start on his own folder with his logins, one owed step from his 24 Oct brief | §2.1; session 10-27T17:51, 10-28T15:48 |
| 2 | "QMN runs only on Linux with systemd" (G3 §0 item 2) | Partly true. Its supervision, powers door and secret store are Linux-only. Its logic and 115 test files run on Windows in `just ci`; five tests are Windows-only | `tools/test_all.py:61-62`; `qmn/tests` `skipif(os.name != "nt")` |
| 3 | "QMN's CI lane does not run on engine/base PRs" (G3 §1.1, §5) | True, and the same holds for the whole GitHub battery (`battery.yml:4-8`). The wrap-up ran `just ci` locally instead, which includes the node's tests | `.github/workflows/battery.yml:4-8`; `tools/test_all.py:61` |
| 4 | Silence on where the 97,000 lines came from, and on whether the wrap-up touched the node (G3) | The wrap-up changed no node code; the node was planned for a fresh session that never ran; `qmx node setup` is the QMX server, not the node | §0 item 1; `HANDOFF-2026-10-24.md:295-301`; `node.py:1-30` |
| 5 | "About 97,000 lines" (G3 §0 item 1) | 98,063 lines: 85,136 code, 4,011 docstrings, 8,541 blank. Plus 42,219 lines of tests, 6,353 lines of deploy files, and 28,667 lines in `qmf-venue` and `qmf-risk` | §2.2 table |
| 6 | "Whether CCXT 4.5.85 carries the Hyperliquid class was not checked" (G3 §2.3, §7) | It does, with orders, positions, funding, open interest, order book, leverage and testnet | §2.6 |
| 7 | "No working way for agents to run a backtest" (G2 §3; G1 §4.2; lead's 09:43 summary) | True for trunk, but it reads as "missing". It was designed (21 Oct), built as PR 204 for a silent runner, and parked on his word for the unit session | §2.4 |
| 8 | "PR 204 conflicts with engine/base in control_door.py and host.py" (G2 §3) | True, and the conflicts are small: one docstring hunk and seven both-sides-added hunks. Its config folder `<home>/backtests` also predates the new layout's `data/backtests/**` | §2.4 |
| 9 | "Library primary is This PC by default; the server can become primary on his card" (G2 §7) | The card was cancelled with ruling 136 on 25 Oct. The flip code is still in the host, so it is leftover against his ruling, not a feature to design around | `qmx_host/host.py:58`, `:635-682`; session 10-25T14:58 |
| 10 | OpenObserve on This PC "BUILT; NEVER RUN" (G2 §8) | The Windows build is now downloaded, checksum-checked and pinned, so QMX can fetch and start it; it has not run against real telemetry | session 10-29T13:57 |
| 11 | "Sign-in BUILT, NEVER RUN on his real folder" (G3 §2.1) | True. Add that his app's return address is already registered and the app may trade, so the node can reuse the app or the flow | session 10-24T18:59; `oauth.py:1`, `:31-34` |
| 12 | G3's "keep as is" list includes the connect dialog's step runner, but not the QMX server hardening | The server setup's firewall with its 5-minute undo, Tailscale-only bind and `qmx-recover` passed on his real server; a trading server can reuse them | session 10-25T16:35, 10-25T17:48 |

G1's QMB and Library sections and G2 §9 and §10 held up where I checked them.

---

## 4. What the unit design must use as it is, and the few places a change is unavoidable

### 4.1 Use as it is (surgical)

| Part | Why it fits | Where |
| --- | --- | --- |
| The one catalog | A QMB or unit door added as rows reaches the copilot, workflow agents, REST and the engine at once | `qmx_control/catalog.py` |
| The backtest rows and PR 204's design | One function lands a backtest from a chat and from a workflow; child process; read-back. Rebase it rather than redesign it | `qmx_control/catalog.py:285-311`; `origin/build/wu4` |
| Library kinds and landing | Governed kinds land as drafts and wait for his yes, which is "only he promotes" with no new gate; the unit kind already has pages as link walks | `qmx_library/landing.py`; `kinds/unit.schema.json` |
| The market-data door, typed partitions, downloaders | Historical data is the Library's job (his 31 Oct ruling 8) | `qmx_host/market_data.py`; `templates/download-*` |
| The folder layout and save classes | Backtest results and a node's state on This PC already have rows; units fall under content and travel with his work | `qmx_home/classes.py:120`, `:130`, `:162` |
| Places and the attempt record | QMB and a unit run on This PC by default and record where they ran | PR 212 |
| The connect dialog's step runner, the server setup's firewall, undo and `qmx-recover` | The shape a trading-server setup can take, already proven on his server | `qmx_host/connect.py`, `connect_compute.py`; `qmx_control/node.py` |
| The cTrader sign-in flow and the live-grant refusal on QMX hosts | Keys that can trade stay off the PC by construction | `qmx_broker/oauth.py`; `adapters.py:103-146` |
| Demo or live on every broker read | Journals can carry the world of every figure | PR 215 |
| The node's laws and safety parts | Command and event laws, cTrader client, reconcile, pacer and venue-resident stop, kill switch, kill line, clock bands, one refresher per credential, heartbeat | `packages/qmf-venue`; `qmn/venue`, `order`, `reconcile`, `protection`, `capital`, `time`, `secrets`, `observability/liveness.py` |
| The node loop over QMB's slice runner | The parity the old backtester demanded already exists in shape | `qmn/loop/` |
| One telemetry switch and OpenObserve | One home for unit logs | `qma/telemetry.py`; `qmx_host/connect_logs.py` |

### 4.2 Changes that cannot be avoided, and why

1. **QMB's trading path must accept Library data and a named unit.** Add a typed-partition entry into the execution path, express the execution inputs as data, and make a unit nameable by reference; add R to results. Why: without them no agent backtest can trade (§2.4; G1 §4.5).
2. **Rebase PR 204** onto trunk (two files, additive hunks), move its child launch under `qmb/orchestrator/`, drop the thread lock, reword the docstring, and move its run configurations into the new layout. Why: it is the agent door, and QMB's own house-rule test refuses it as it stands.
3. **The sizing seam.** The entry intent carries no size and the Book door sizes. Why: a unit sizes itself (STATE correction 2). It touches `qmf-risk`, QML's intents, QMB's run configuration and the node's seat door (G1 §0 item 4).
4. **A live composition for whatever stays of the node.** Its only registered profile is offline replay. Why: nothing can trade live otherwise (§0 item 2).
5. **Subtract before building on the node.** Cut the proof campaigns, readiness packets and QA matrix (about 11,900 lines), the benchmark harness and the second monitoring stack first. Why: his "97,000 lines is far too much" (ruling 27) and his rejection of prove-itself machinery (STATE correction 1). Which of the four ambiguous `host` modules go needs a blast-radius run (§2.2).
6. **A trading-server kind in the connect dialog.** Why: "set itself up on a server" (ruling 27) and "as simple as how ... I can set up a server from a provider" (ledger N-07).
7. **The MIS must publish to units.** Its consumer set is closed to the Book door and the kill switch. Why: the MIS reads and publishes, units pick, and none needs it to trade (STATE Q6).
8. **CCXT beyond spot.** Lift the spot-only filter for reads on the PC; add a node client for Hyperliquid or CCXT orders. Why: his ruling 28 (§2.6).
9. **Remove the Library flip code.** Why: ruling 136 cancelled the move card; leaving it invites a design to lean on it (§3 row 9).

Everything else in QMA v2, the copilot and mini apps stays as built, per his ruling 24.

---

## Not verified

- No QMX, QMB or node code was run. Behaviour is read from code, docstrings, `git` output and the session's reports.
- Whether `runtime_risk_gate`, `fencing`, `lineage_persist` and `registry_mint` are dead or only re-exported.
- Whether Hyperliquid's trigger orders can carry the venue-resident stop the node requires on every placement.
- That PR 204's conflict hunks resolve cleanly by keeping both sides was judged from the hunks, not by running its tests after a merge.
- The builder and reviewer reports were read by topic, not line by line (see "How to read this").
