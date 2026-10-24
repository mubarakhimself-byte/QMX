# 60. Wrap-up seams: backtest door and landing, the cTrader sign-in, the run-pass secret

Written 2026-10-24 for the wrap-up program (`WRAPUP-PLAN.md`, WU4, WU8, WU9, WU10). Code truth is `engine/base` at `f05fc64b`, read in the detached checkout `D:/Temp/wrapup-read`. Rulings 105 to 135 of file 26 bind, the latest winning. The spines were amended in place with the `bmad-architecture` skill in amend mode; every amendment is marked *Wrap-up seams (60)*, and no AD id changed.

## Plain words first

- **Backtests.** One piece of QMB code runs a backtest on whichever machine you are on, by default your PC. Your copilot and your workflows both call it through one function, so a result always lands as the same kind of Library card, linked to its data and its bot. The copilot's result shows at once. A workflow's result shows when the workflow finishes and passes.
- **cTrader sign-in.** You click sign in on the PC. cTrader's own page opens and you agree. Your browser brings back a one-minute code. A small receiver on the PC hands it straight to the server and keeps nothing. The server swaps the code for the sign-in and keeps it. Your app's id and secret reach the server once, sealed so only the server can open it. Until the server runs, the sign-in button says it is waiting for the server.
- **Run passes.** A run pass is the short ticket a remote step carries. Today each program makes up its own signing key when it starts, so a ticket made on the PC is refused at the server, and a restart voids every ticket. From now on the key is worked out from the pairing key your PC and server already share. Every machine of your home then checks any ticket itself, before and after a restart, with nothing new to copy.

## Seam A. Where the backtest door and the Library landing live (WU4)

### Code check

| Piece | State | Where |
|---|---|---|
| `BacktestDoor` port and `run_backtest` | PARTIAL: port and tool exist, no implementation, every host builds the context without it | `TL/service.py:175-192`, `:280-316`; call sites `H/harness.py:405`, `TL/servers.py:44`, `SL/qma/cat_lanes.py:274`, `SL/qma/s28_effects.py:88` |
| QMB's landing step and `LandingPort` | EXISTS | `qmb/src/qmb/host/library_landing.py` |
| Store `put` and `relate` | EXISTS | `LB/store.py:927`, `:956` |
| `StoreLanding` adapter | NEW | `LB/adapter.py` |
| QMB door implementation | NEW | `qmb/src/qmb/host/backtest_door.py` |
| `qmb_backtest` operation | NEW; the `app_op` executor exists | `E/control_door.py:294`, `E/nodes/app_op.py` |
| Run-end landing from `refs/runs` to `main` | EXISTS | `LB/landing.py:35` |
| Typed-partition replay reader | EXISTS | `qmb/host/replay.py:608` `read_typed_replay_source` |

Three facts the plan's Files block did not have:

1. **`qmb:backtest` is not a principal.** `land()` defaults to `principal="qmb:backtest"` (`library_landing.py:33,102`), and `Principal.parse` accepts only `operator | agent | run | engine | hub | migrator` (`LB/principal.py:32-39`). And `run:<id>` may not put onto `main` (`LB/principal.py:71-74`). The plan's "a Draft on `main`" works only as `operator`.
2. **The PC host's store refuses every write.** `HO/host.py:550` opens the store as `replica` on every role but `server`, and `_check_writer` refuses any put on a replica (`LB/store.py:860-863`). Nothing appends to the outbox (`Outbox.append` has no caller). So at `f05fc64b` a landing, a copilot save or a session record on a PC host is refused `read_only_replica`.
3. **A month in one go is too big for the reader.** P-QMBREAD measured about 1 GB at 744 frontiers, and a full month of one-minute frontiers would need about 16 GB (data BACKLOG DR4). A backtest in the host process could take the host down (engine AD-30, F39).

### Decision

- **The door is QMB's own**, `qmb/host/backtest_door.py`, satisfying `BacktestDoor`. It materialises the partitions through the host's market-data door and runs the replay in **one child process**. The `qmb` placement defaults to the local host (ruling 117). A dedicated QMB machine is a later placement behind the same door (Deferred).
- **One function lands every backtest**: `qmx_tools.service.backtest_and_land(door, landing, arguments, principal)`, lifted out of `DomainContext.run_backtest`.
  - The copilot's `run_backtest` calls it as `operator`. The record lands on `main` at once, as every copilot save does today (`qmx_control/library.py:330-338`).
  - The workflow node is `app_op` with `parameters {app: qmb, job: backtest, config_ref, tests?}`. `AppOp` routes `app: qmb` to the host's door instead of the mini-app supervisor and calls the function as `run:<run_id>`. The result sits on `refs/runs/<run_id>` until the run-end landing (Library AD-18). A test-mode run lands nothing.
- **`StoreLanding(store)`** in `LB/adapter.py`. `put` becomes one `Draft` under QMB's run id, and `link` becomes `store.relate`. The principal the caller passes picks the ref: `operator` puts onto `main` and `run:<id>` onto `refs/runs/<id>`. Any other principal is refused by name. `land()` loses its `qmb:backtest` default, so every caller names a principal.
- **The PC host opens its store as the writer while `[library] primary` is `pc`.** The server host stays the writer of its own store, as built. Before the flip, the PC needs a write path as a replica, which is put to the primary, or append to the outbox when the primary is away. That path is Deferred in the Library spine and blocks G-FLIP.
- The host builds one door, one `StoreLanding` and the recorded run configurations after `control.attach_library(store)` (`HO/host.py:553`). It hands them to `RecordedHarness.open`, as it already does with `market`, and to `EngineDoor.open`.
- The stdio `qmx-mcp-backtest` process (`TL/servers.py:44`) holds no Store, because each store has one writer. It keeps its named refusal and is not edited.
- A template drops `needs: qmb-door` only when every script it runs needs nothing but `qmb_backtest`. `b-build-and-prove` and `d3-iterate-against-qmb` also wait for QMB's robustness, holdout and report doors (their scripts say so), so they keep the need.

### ADs amended

Engine AD-31, and Library AD-29 with one Deferred row.

### Blast radius

- Callers: `H/harness.py:405`; `SL/qma/cat_lanes.py:274`; `SL/qma/s28_effects.py:88`; `E/control_door.py:294`; `HO/host.py:540-555`.
- Every PC-host write: changing the PC host's store role touches the session recorder (`HO/sessions.py:520-524`), `library_save` and the WU5 install. Each was refused before and now succeeds. WU5's "visible through the Store" lane may have run against a server-role home; recheck it on a PC role.
- Tests: `qmb/tests/test_library_landing.py` (the default principal goes), `QA/qmx-tools/tests/test_tools.py:162-293` (the fake door, plus a landing test and the tamper step), and `QA/qma-harness/tests/test_tools.py:170,359,536` (the context builds). Add one test to the engine's `app_op` tests and one to `HOT/test_host.py` (a PC-role store accepts a put while the primary is `pc`).
- Cleared: `StoreLanding` imports nothing from QMB. The port is structural, so the dependency direction holds (`qmx-library` sits below `qmx-tools`).

### Scenarios

1. The copilot runs a backtest. One card shows on `main` with `consumed` and `uses`.
2. A workflow node runs the same spec. Its result waits on the run branch, then lands when the run passes. Because it has the same object id, it adds no second card.
3. A test-mode run lands nothing.
4. A sealed month is refused by the door's seal, by name.
5. A tampered report blob is refused `corrupt_blob` by name.
6. A replay too big for memory fails the child process, not the host.

### The one fact, proven (step 4, run)

Both paths put the same manifest under QMB's run id, so they land one object. `C:/Users/Mubarak/AppData/Local/Temp/claude/C--Users-Mubarak-Desktop-QMX/3f47fe69-159a-4e17-936c-1c9f3d5c366c/scratchpad/probe/seams.py` (not kept in the repo) against `f05fc64b`'s `qmx_library`: `A same object id across paths: True` (operator on `main` and `run:wf1` on `refs/runs/wf1`). The same run also showed `read_only_replica` for a put on a replica, and `ref_not_owned: run:r1 may not put onto main`.

### Probe for the PR

The plan's three unit tests stand. Add one: the same spec through the tool and through a `qmb_backtest` node gives one object id. For WU4's live lanes, use a bounded month (hourly frontiers, or at most 1,000 frontiers as P-QMBREAD does), not a full month of one-minute data.

## Seam B. The cTrader sign-in, the home's token store, the one venue session (WU8, WU10)

### Code check

| Piece | State | Where |
|---|---|---|
| Vault allow-list (`qmx/read/*`, `qmx/data/*`, model rows; any name containing `token` refused) | EXISTS (DR2C) | `R/vault.py:89-107` |
| Per-machine vault key, server opens its copy alone | EXISTS | `R/vault.py:194-222` |
| Host pass over the pairing key (mint, verify) | EXISTS | `E/service/forward.py:89-140` |
| Long-running venue connection with an injected `SecretStore` and store-before-discard rotation | EXISTS | `packages/qmf-venue/src/qmf/venue/connection.py:454` |
| Credential filing and re-filing | PARTIAL: one JSON bundle per entry `{clientId, clientSecret, accessToken}`, read with the user name `reference` minus `qmx/` | `BR/credentials.py:46-117`, `BR/adapters.py:111-133` |
| Short TLS read session per call | EXISTS, to be replaced by the home session | `BR/ctrader_transport.py:39-47`, `BR/service.py:83` |
| Loopback receiver, begin and code routes, home key store, venue route | NEW | `BR/oauth.py`, `HO/venue_session.py` |

From the operator: the app id and secret are in the PC's vault as `qmx/ctrader-client-id` and `qmx/ctrader-client-secret`, the home is the server, and the sign-in is demo with the read-only scope. cTrader's flow sends no `state` and carries the client secret in the token request's query string [retrieved: help.ctrader.com/open-api/account-authentication]. On Windows, `keyring.get_password` matches the saved user name [remembered: keyring's WinVault backend], so the copy step looks each entry up by its target name.

### Decision

The sign-in in four steps (engine AD-67, *Wrap-up seams (60)*):

1. The PC asks the home host to begin, with a host pass. The home answers with the consent URL and keeps one pending sign-in per app for 10 minutes. A home that is not running, not reachable or has no app credential refuses by name, so no browser opens.
2. The PC starts the loopback receiver on the registered port (a Settings value) and opens the URL. He agrees on cTrader's page.
3. The receiver forwards the one code at once with a host pass, answers the browser, keeps nothing and stops.
4. The home matches the code to its pending sign-in, which is good for one use. It exchanges the code and writes the tokens as `qmx/token/ctrader-app` in its own key store. On the server that store is an owner-only file under `<home>/vault/` for `qmx`. The vault refuses any name containing `token`. The home never logs request URLs.

**How the home gets the client secret.** A one-time copy on the PC writes the two entries as one static entry, `qmx/read/ctrader-app` = `{clientId, clientSecret}`, and keeps the originals. The built allow-list seals it to the server's key, and the server opens it from its own vault copy with the PC asleep. No new vault rule is needed. The copy moves from WU10 to WU8, because WU8's exchange needs it.

**Before the server host runs**, there is no sign-in. The PC never stands in as the home, because a second home refreshing the same grant logs the first out. G-CT waits for four things: WU9's real setup, `qmx node vault install` carrying the new entry, his app's approval, and the redirect address he confirms (question posted).

**The one venue session (WU10).** The home host keeps one `qmf.venue` `ConnectionManager` per app and environment, with the home key store as its `SecretStore`. Broker reads on the home call it in process. A read on any other machine forwards with a host pass and waits `placement` while the home is unreachable. The begin, code and read routes accept a host pass only. A chat, a run pass or an observer token reaches none of them.

### ADs amended

Engine AD-67, which cites AD-28's existing "handed once" rule. No new AD.

### Blast radius

- `BR/service.py:29-90` (`open_adapter` builds a transport per call) and `BR/adapters.py:111-133` (`authenticate` reads the bundle). Both now read the app half and the tokens from different places.
- `BR/tests/test_broker.py` and `test_transport.py` use the bundle.
- `HO/host.py` mounts the venue routes beside `forward_router` (`HO/host.py:811-818`). That puts `HO/host.py` into WU8, so WU8 cannot run beside WU4.
- `HO/door.py` keeps the routes off chats and run passes.
- Cleared: the allow-list needs no change. The proof run gave `qmx/read/ctrader-app True`, `qmx/token/ctrader-app False`, `qmx/ctrader-client-id False`, `qmx/ctrader-client-secret False`.

### Scenarios

1. A full sign-in on scratch homes against a fake token endpoint. The server holds the tokens, and the PC's keyring has no `qmx/token/*`.
2. The server is down. Begin is refused by name, and no browser opens.
3. A code replayed, or arriving after 10 minutes, is refused.
4. A second home for the same app is refused on save.
5. A refresh on the home, then a forwarded PC read, succeeds.
6. Removing the connection on the PC asks the home to delete its tokens, with no tombstone.

### The one fact, proven (step 4, run)

The client secret can reach the server only through the static name. The allow-list run above shows the two typed names stay put, the copy replicates, and the token name never does.

### Probe for the PR

WU8 lane 2 (the full flow on two scratch homes) plus lane 6 (no home reachable). In lane 6, begin is refused before any receiver listens.

## Seam C. The run-pass secret (WU9)

### Code check

| Piece | State | Where |
|---|---|---|
| Pass format, checks, revocation file | EXISTS | `R/passes.py` |
| Secret | PARTIAL: `os.urandom(32)` per `PassAuthority` | `R/passes.py:234` |
| Authorities per host process | THREE, each with its own secret: the door's, the node sidecar's and the harness helpers' | `HO/host.py:476`, `HO/host.py:536`, `qma/harness/delegate.py:405` (built at `harness.py:336`) |
| Pairing key held by both ends, already keying host passes | EXISTS | `QX/node.py:263-280`, `:604-607`; `HO/host.py:771-818` |
| Spine wording "signed with the pairing key" | designed, not built | engine AD-28, Library AD-12 |

So today a pass from the door's authority fails even at the same host's sidecar, besides failing across machines and after a restart.

### Decision

The smallest design that works:

- `secret = HMAC-SHA256(pairing key, "qmx run pass v1")`, read from `<home>/vault/pairing-key`. This is durable per home, shared by every paired machine, and needs no new file to copy. Re-pairing rotates it.
- An unpaired home (the PC alone) uses `<home>/vault/run-pass-key`, 32 random bytes created once, owner-only. Pairing replaces it, which stops passes in flight once.
- One `PassAuthority` per host process, built in `serve` and passed to `node_sidecar`, `compose` and `RecordedHarness.open` and on to `Helpers`.
- `PassAuthority()`'s random default stays for tests and the old lanes.
- Rejected: federation, where a host checks a pass by asking the host that minted it. It needs the PC awake, and AD-28 says signature, no lookup.
- Rejected: a separate shared pass-key file. That is one more secret to copy and to rotate.

### ADs amended

Engine AD-28 and Library AD-12. One Deferred row (revocations across machines).

### Blast radius

- `HO/host.py:476,536`; `qma/harness/delegate.py:405` and `harness.py:336`. That puts `H/harness.py` into WU9, after WU4, which also edits it.
- `QX/node.py` setup and pair must write the key at `<home>/vault/pairing-key` on the server, the file the host and the Hub read (`HB/server.py:957`). Today `pair` writes `/etc/qmx/vault/pairing-key` (`QX/node.py:564`).
- A second finding for WU9: `setup` calls `flip_primary(home, url)` (`QX/node.py:608`). That writes `primary = "server"` on the PC at setup, before his flip click. It should write `hub_url` only and leave `primary` to G-FLIP. With seam A's role rule, an early `primary = server` would also make the PC a replica that refuses every write.
- Tests: `R/tests/test_passes.py`, `test_data_scope.py` and `HOT/test_run_pass_door.py` build authorities with explicit secrets and are unaffected.
- Lanes `SL/server/e13_remote.py:40` and `e57_remote.py:182` mint with a random secret, so at a real door they 401 as before. Note this in their logs; no change is needed.

### Scenarios

1. A pass minted on the scratch PC host is used at the scratch server door after the server restarts, and the read succeeds.
2. A pass from another home is refused `bad_mac`.
3. A `cli` helper's pass verifies at its own host's door.
4. An unpaired PC restarts, and its passes still verify.

### The one fact, proven (step 4, run)

`C:/Users/Mubarak/AppData/Local/Temp/claude/C--Users-Mubarak-Desktop-QMX/3f47fe69-159a-4e17-936c-1c9f3d5c366c/scratchpad/probe/seams.py` (not kept in the repo): `C same home, fresh authority: None` (accepted), `C other home: bad_mac`, `C today (urandom per process): bad_mac`.

### Probe for the PR

WU9's unit test "a pass minted before a host restart verifies after it", and lane 4.

## WRAPUP-PLAN Files blocks: exact changes

WU4.
- Added `QB/host/backtest_door.py`, as the named file for "Add the door in `QB/host/`".
- Added `QB/host/library_landing.py` (the `qmb:backtest` default goes; the principal is required).
- Added `TL/service.py` (`backtest_and_land`, and the named refusal for a corrupt blob in `DomainContext.artifact`).
- Added `E/nodes/app_op.py` (route `app: qmb`).
- Widened `HO/host.py`: the PC host opens its store as the writer while `[library] primary` is `pc`.
- Removed `TL/servers.py:44`.
- Narrowed `T/catalog.py`: `needs: qmb-door` goes only from templates that need nothing else.
- Tests added in `qmb/tests/` and `QA/qma-harness/tests/test_tools.py`.

WU8.
- Added `HO/host.py` (mount the venue routes beside `forward_router`).
- Widened `BR/credentials.py`: the one-time copy into `qmx/read/ctrader-app`, reading by target name and keeping the originals. This moved here from WU10.
- `HO/door.py` keeps the routes off chats and run passes.

WU10.
- Added `BR/service.py` and `BR/adapters.py` (open the adapter on the home session, read the app half and the tokens separately).
- Narrowed `BR/credentials.py` to re-filing old token-bearing bundles, with tokens left on no PC and no tombstone.

WU9.
- Added `H/harness.py` (pass one authority to `Helpers`).
- Widened `QX/node.py`: `setup` writes `hub_url` and not `primary`, and the pairing key lands in `<home>/vault/pairing-key`.
- `R/passes.py` gains the derivation from the pairing key and the create-once fallback.
- `HO/host.py` builds one authority per process.

Appendix C.
- Add a WU4 and WU8 row for `HO/host.py`, order WU4 first. WU4 and WU8 no longer run in parallel, which the appendix already allowed for.
- Add a WU4 and WU9 row for `H/harness.py`, order WU4 first (WU9 already waits for WU4).
- Add a WU8 and WU10 row for `HO/host.py`, order WU8 first.

## Reviewer gate

`lint_spine.py` gives 0 findings on both spines. The brief bars sub-agents, so the reviewer lenses did not run as separate agents. An inline check against the good-spine list found no new AD weakening an inherited one. Rulings 116 to 118 hold: no money gate and no sandbox, and the sign-in key rule only says where a token is kept. The one item for him (the redirect address) is in `QUESTIONS-FOR-OPERATOR.md`.
