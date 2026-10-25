# 61. The server as a substitute, and the second round of WU9

Written 2026-10-25 by the WU9 second-round architect. Code truth is `build/wu9` at `546d06f1` in `D:/QMX-worktrees/bld-wu9` (read only). Server facts were read over SSH on 2026-10-25 and nothing was changed there. Rulings 105 to 139 of file 26 bind; rulings 136 to 139 are new today and win over everything earlier. The spines were amended in place with the `bmad-architecture` skill in amend mode; every amendment is marked *Server substitute (61)* or *WU9 second round (61)*, one AD was added (engine AD-71), and no AD id changed.

## Plain words first

- **Three things stopped the server from starting.** QMX's server program needs a memory package it never asked for, so the server's install left it out. The server has no password safe like Windows has, so the program could not find its own door key. And the server answers on the public internet, because nothing there blocks the doors, although every door still asks for its key.
- **The fixes.** The program now lists every package it uses. On a machine with no password safe, its door key lives in a locked file in its own folder. The server gets a firewall that lets in only SSH (so you can always log in), your private Tailscale network and QMX's own containers. If the firewall step goes wrong, it switches itself off after five minutes.
- **Your way back in.** Every server gets one script you can run yourself, `sudo qmx-recover`, with no agent. It tells you in plain words what is running and what is wrong, shows logs, restarts or stops things, fixes permissions and program files, goes back to the previous version, makes a fresh pairing code, checks the key copy and opens or closes the firewall. It does not need QMX to be working. Your PC gets a twin that does the same from Windows.
- **No locks.** The price-data door no longer stays shut until you name a holdout month. A holdout is something you switch on for a study if you want one. It is off unless you do, and you can test any idea on any period, 1996 included.
- **Your PC is home.** The plan to move the Library's main copy to the server is withdrawn. The server stays a stand-in for when your PC is off, and extra capacity. The list in section D says what in the earlier design still assumes the server is home and what the right shape is; it is designed in a later round.

## A. The three server blockers

### A1. qmx-host declares what it imports

**Code check (run, not read).** A script walked `uv.lock` from `qmx-host` and parsed every `import` in every first-party package of that closure (`scratchpad/wu9b/imports.py`, not kept).

| Piece | State | Where |
|---|---|---|
| `qmx-host` imports `qmx_memory` | NEW to the closure: not declared, not reachable through any declared dependency, so `uv sync --package qmx-host` leaves it out | `qmx_host/host.py:95-96`, `qmx_host/sessions.py:55-57`; `qmx-host/pyproject.toml:6-16` |
| `qmx-host` imports `qmx_router`, `qmx_remote`, `qmx_broker`, `qmf.core`, `qmf.data` | PARTIAL: in the closure only through other packages, not declared | `door.py:73`, `host.py:51,97-101`, `market_data.py:33,43-46`, `venue_session.py:32-34` |
| Any other first-party import outside the closure | none (the only miss is `qmx_memory`) | run result |
| Third-party imports outside the closure | none on the host's start path; `torch` and `docling` are template child scripts with their own installs, `lightgbm` is a lazy import in `qmn` | `templates/d6-ml-training-run/scripts/train.py:90`, `templates/extract-source/.../extract.py:83`, `qmn/mis/regime_train.py:1765` |
| What `qmx-memory` adds on the server | 80 packages (`hindsight-all`, `pg0-embedded`, `onnxruntime`, `litellm` and others); `pg0-embedded` ships a `manylinux_2_35_x86_64` wheel and the server has glibc 2.39 (Ubuntu 24.04.5) | `uv.lock:1435`, `uv.lock:2988-2994` |
| Hindsight starts on the first memory read or retain whenever it is importable | EXISTS; the host ignores `[memory] hindsight`, which only the bootstrap reads | `host.py:432-453`, `qmx_memory/hindsight.py:92-94`, `node.py:255-257` |

**Decision.** `qmx-host` declares every first-party package it imports: add `qmx-memory`, `qmx-router`, `qmx-remote`, `qmx-broker` (workspace sources) and `qmf-core`, `qmf-data` (the same source form `qmx-tools` uses). Because declaring `qmx-memory` makes Hindsight importable on the server, the host follows `[memory] hindsight` there: on the `node` and `server` roles `compose_memory` passes `index=None` (the built FTS5 engine, `qmx_memory/engine.py:91,104`) unless the setting is true. The PC is unchanged (Hindsight by default, ruling 119). A test guards the rule so the next undeclared import fails on the PC, not on the server.

- **Done when** a fresh `uv sync --frozen --package qmx-host --no-default-groups` imports `qmx_host.host`, `qmx_host.sessions`, `qmx_host.venue_session` and `qmx_host.market_data`, and a server host with `[memory] hindsight` unset recalls through FTS5.
- **The one check.** On the server, in `/srv/qmx/check/wu9b`, from the PR head's source archive: the sync above into a fresh environment, then `python -c "import qmx_host.host, qmx_host.sessions, qmx_host.venue_session, qmx_host.market_data"` exits 0. Save `wu9b-imports.log`.
- **Blast radius.** `qmx-agents/uv.lock` (the `qmx-host` entry only); install size on the server (about 80 more packages, 159 GB free). PC: none, its workspace sync already installs them. Tests: `test_host.py` gains a server-role memory test. Cleared: no cycle, because nothing depends on `qmx-host`.

### A2. The control token on a headless server

**Code check.**

| Piece | State | Where |
|---|---|---|
| `local_token()` reads and creates the token in the OS keyring only | PARTIAL | `qmx_control/server.py:46-52` |
| Callers | `create_app` fallback `server.py:345`; host `host.py:671` and `:1099`; the door's fallback `door.py:197-200`, used because `compose` builds `PrincipalDoor` without `bearer` (`host.py:1057-1063`); the engine CLI `qmx_engine/__main__.py:251` | read |
| Server token file | PARTIAL: `/etc/qmx/vault/control-token` is written only by `qmx node bootstrap` (`node.py:838-850`), never by `setup`; `read_secret` already refuses a file that is not owner-only | `node.py:67-77` |
| The server's own commands read the token from `--vault /etc/qmx/vault` | EXISTS | `node.py:740-748`, `:664`, `:913` |
| The server today | no `/etc/qmx/vault`, no `/opt/qmx`, no gnome-keyring, `qmx` user exists (uid 997) | SSH read |

**Decision.** `local_token(home: Path | None = None, *, create: bool = False) -> str` in `qmx_control/server.py`.

- Where `keyring.get_keyring()` has a real backend, behaviour is today's: read the keyring entry and create it if missing. The PC path does not change, whatever `create` says.
- Where the keyring library has no backend (its `fail` backend, which is what a headless Linux server gets and what raised `NoKeyringError` in the check, or its `null` backend, which silently stores nothing), the token lives in `<home>/vault/control-token`, the same folder as the pairing key. A file with group or world bits is refused by name. A missing file is created only when `create=True`, with `O_CREAT | O_EXCL` and mode 600 inside a 700 folder; otherwise the caller gets a plain error naming the home. The host's `serve` is the only caller with `create=True`.
- `home` defaults to `default_home()`, which is `/srv/qmx/home/.qmx` under the unit's `HOME`.
- The host computes the bearer once in `serve` with `create=True` and passes it to `compose` and to `PrincipalDoor(bearer=...)`, so the door's fallback is no longer used by the host. `health(port)` and the engine CLI pass their home.
- Setup's "move the pairing key" step also moves an old `/etc/qmx/vault/control-token` into `<home>/vault/` once, and the server commands' `--vault` default becomes `SERVER_HOME/vault`, so `verify`'s `node_token` line and `update`'s drain read the file the host uses.
- Rejected: catching `NoKeyringError` around the keyring call (it would also swallow a real failure on the PC), and `keyrings.alt` (a plaintext file under another name, plus a new dependency).

- **Done when** the server host starts under its unit with no workaround and answers `/api/health` with the file's token.
- **The one check.** Unit: `test_local_token_uses_the_home_file_without_a_keyring` sets the `fail` backend, calls `local_token(home, create=True)` twice (same value, file mode 600), refuses a 640 file, refuses to create with `create=False`, and with an in-memory backend never touches the file. Live: lane 2 without the scratch workaround.
- **Blast radius.** The five callers above; `test_control.py:234-241` (patches `keyring.get_password` and `set_password`, still valid on the keyring path); the PC console and `scripts/live/qma/*` read the keyring directly and run only on the PC. The check's lane 2 passed once this and A1 were worked around, so nothing else on the start path needs a keyring.

### A3. Exposure

**Facts on the server (SSH, 2026-10-25).** Public `155.133.27.86/23` and `2a02:c207:2296:3912::1/64` on `eth0`; tailnet `100.105.172.63` on `tailscale0`. `ufw` 0.36.2 installed and inactive; INPUT policy ACCEPT for IPv4 and IPv6; Tailscale's own `ts-input` chain only. `sshd` listens on 22 on every address through `ssh.socket`, with password and root login on. Docker is not installed yet (the bootstrap installs it).

**Code check.**

| Piece | State | Where |
|---|---|---|
| Router, node sidecar and server host bind `0.0.0.0` on the premise that the tailnet is the only network | EXISTS, premise false on Contabo | `qmx_router/server.py:39-41`; `host.py:498`, `:621`, `:686` |
| Collector listens on `0.0.0.0:4317`, `:4318`, `:13133`; its file says "the host firewall admits 4317 and 4318 only over the tailnet" | the firewall it names does not exist | `qmx-host/deploy/otelcol.yaml:20-30,60` |
| Loopback callers of the host | `health()` probes `127.0.0.1` | `host.py:1094-1103` |
| Containers QMX starts | default bridge, no published port | `qmx_remote/providers.py:122-160` |
| The old node service refuses any address that is not `100.*` | EXISTS (precedent) | `node.py:910-912` |

**Decision: a firewall step in setup, binds unchanged.** The firewall closes every door at once, the collector's and future ones included, for IPv4 and IPv6, where a tailnet-only bind would cover only QMX's Python listeners, break the loopback probe and the Docker bridge, and fail to start when the host boots before Tailscale has its address. The rules (engine AD-71):

1. Read the SSH ports from `sshd -T` and `ufw allow <port>/tcp` for each, first.
2. `ufw allow in on tailscale0`, `ufw allow 41641/udp`, `ufw allow in on docker0`.
3. `ufw default deny incoming`, `ufw default allow outgoing`, IPv6 on (Ubuntu's default, checked).
4. Before `ufw --force enable`: `systemd-run --unit qmx-firewall-undo --on-active=300 /usr/sbin/ufw --force disable` (a leftover undo unit is stopped first, so a rerun is safe).
5. Setup, on the PC, opens a fresh SSH connection to the same target; only when it succeeds does it run `qmx-recover firewall keep`, which stops the undo timer. If it fails, ufw turns itself off within five minutes and setup says so in plain words.

Established connections survive `ufw enable` (ufw's own conntrack rule). SSH stays open on the public address. Contabo's VNC console in its customer panel is the last way in [remembered]. `qmx node verify` gains a `firewall` line (active, deny incoming), and the docstring of `TAILNET` names the firewall as what makes its premise true.

- **Done when** every QMX port is unreachable on the public address while SSH works there and the tailnet door answers.
- **The one check.** From the PC after the step: `curl -m 5 http://155.133.27.86:8766/` gets no answer, `ssh -o ConnectTimeout=10 root@155.133.27.86 true` succeeds, and `curl http://100.105.172.63:8766/api/health` answers 401. Save `wu9b-firewall.log`.
- **Blast radius.** Docker containers reaching the host door through the tailnet address (allowed on `docker0`; a custom Docker network would need its own rule, none exists); Tailscale direct connections (41641/udp; without it traffic still flows through relays); the collector over the tailnet (allowed); OpenObserve and Postgres listen on loopback only. Docker's published ports pass around ufw, so AD-71 bars a published port bound to every address. A public listener for providers off the tailnet (Library OPEN-5) is a Deferred row. Password SSH and root login are a separate hardening item (BACKLOG), because changing `sshd` is the one step that could lock him out.

## B. The recovery script (ruling 139)

**Where it lives.** Source `qmx-agents/packages/qmx-control/src/qmx_control/qmx-recover.sh`, beside `node-bootstrap.sh`. Setup copies it to `/usr/local/sbin/qmx-recover` (root, 755), outside `/opt/qmx`, which is a symlink to one version and can be the broken thing. Setup writes `/etc/qmx/recover.conf` (plain `KEY=value`, no secret): `HOST_UNIT=qmx-host`, `QMX_HOME=/srv/qmx/home/.qmx`, `LIBRARY=/srv/qmx/library`, `PORT=8766`, `PROJECT=/opt/qmx/qmx-agents`, `VENV=/opt/qmx/qmx-agents/.venv`, `VERSIONS=/opt/qmx-versions`, `QMX_USER=qmx`. `QMX_RECOVER_CONF` points the script at a scratch conf for lanes.

**What it calls.** Only what the machine has without QMX: bash, systemctl, journalctl, ufw, tailscale, ss, curl, df, free, and `/usr/bin/python3` only to check that the vault copy parses as JSON. It runs QMX's own Python only for `doctor` and `reinstall`, and says so plainly when that Python is broken. It never prints a key, a token or a vault value, and it reads the token file only to test its mode.

**Help text (the shape the builder writes).**

```
qmx-recover: get this server going again, without an agent.
Run it as: sudo qmx-recover <what>

  status            What is running, what is not, and what looks wrong.
  logs [part]       The last 200 lines of a part's log. Add "follow" to keep watching.
  start [part]      Start a part, or all of QMX.
  stop [part]       Stop a part, or all of QMX.
  restart [part]    Stop and start again.
  repair            Fix what can be fixed without a reset, then start QMX and check it answers.
  reinstall         Put QMX's program files back at the version in use.
  rollback          Go back to the version before the last update.
  pair              Make a fresh pairing code here. Then run "qmx-recover pair" on your PC.
  vault             Check the key copy your PC sent (names only, never values).
  firewall status   Say whether the firewall is on.
  firewall close    Turn it on: SSH, Tailscale and QMX's containers only.
  firewall open     Turn it off. Every door then answers the internet, each still behind its key.
  doctor            QMX's own check (needs QMX's program files).

Parts: host, shipping, monitoring, tailscale, docker. Leave it out to mean all of QMX.
Locked out of SSH? Use Contabo's VNC console in its customer panel, log in, and run
"sudo qmx-recover firewall open".
A full reset is "qmx node setup" from your PC, and losing the Library is "qmx node rebuild".
```

**Commands, in detail.**

- `status`: each unit's state and last exit; the host's door on loopback (401 means it answers); the tailnet address and whether the PC shows in `tailscale status`; firewall on or off; free disk and RAM; the store root's owner and size; the vault folder's and token file's modes (not contents); the last five error lines of the host's journal. Each line ends in PASS or FAIL with a plain reason.
- `repair`, in order, each step said as it runs: stop the host; set owners and modes (`QMX_HOME` 750, `vault` 700, files 600, the store root owned by `qmx`); move an old `/etc/qmx/vault` pairing key or token into the home once, as setup does; rewrite the unit from `/var/lib/qmx/recover/qmx-host.service` (setup's saved copy) when it is missing or changed, then `daemon-reload`; check `$VENV/bin/python -c "import qmx_host.host"` and run `reinstall` when it fails; start the host; wait up to 60 seconds for the door to answer. The engine's lock is an OS lock released when a process dies (`host.py:22`, `:152-170`), so there is no stale lock to remove.
- `reinstall`: `uv sync --project $PROJECT --package qmx-host --frozen --no-default-groups`, offline first (`--offline`), then online.
- `rollback`: lists `$VERSIONS`, points `/opt/qmx` at the version before the current one, reinstalls, restarts.
- `pair`: with `--from-stdin`, takes the PC's code and does the rotation `pair_script` does today (`node.py:202-222`: new key in place, the old one kept as `pairing-key.previous`, `run-pass-key` removed, the `/etc` copy removed, `try-restart`); without it, makes a fresh code itself (32 random bytes, URL-safe) and tells him to run the PC twin's `pair`.
- `vault`: `vault-store.json` present, owned by `qmx`, mode 600, parses, with entry and tombstone counts and its age; to send it again, run the PC twin's `vault`.
- `firewall`: the rules of A3. `close` arms the undo and enables; `keep` cancels the undo; `open` disables after a plain warning.

**The PC twin.** Source `qmx-agents/packages/qmx-control/src/qmx_control/qmx-recover.ps1`; setup writes it to `<home>\bin\qmx-recover.ps1` with `<home>\bin\qmx-recover.conf` (the SSH target and key path, no secret). Commands: `status` (the PC host's door, `tailscale ping` to the server, an SSH test), `server <what>` (runs `ssh <target> sudo qmx-recover <what>` with the same words), `pair` (runs `qmx node pair --ssh-host` when QMX's Python works; otherwise asks the server's script for a fresh code and copies the code file into `<home>\vault\pairing-key` over SSH, never on screen, keeping the old one as `pairing-key.previous`), `vault` (runs `qmx node vault install --ssh-host`), `restart` and `logs` for the PC host.

**How it stays usable when QMX is broken.** It lives outside the version folders, depends on no QMX package, and does every check with system tools. `qmx node pair` and `qmx node setup` call it, so it is exercised on every setup rather than only on a bad day.

- **Done when** he can, with only SSH, see what is wrong, stop the host, repair it and see it answer, with no agent and no Python of QMX's.
- **The one check.** `QXT/test_recover.py` runs the script under bash with a stub `PATH` (fake `systemctl`, `ufw`, `sshd`, `systemd-run`, `journalctl` that log their arguments) and asserts the order for `firewall close`: SSH ports allowed, then the undo armed, then `default deny`, then `enable`; and that `status`, `repair` and `pair` print no line from a planted token or key file. It skips where no bash exists. Live lane: on the scratch conf, `status`, then `stop host`, then `repair`, then `status` shows the host answering. Save `wu9b-recover.log`.
- **Blast radius.** `node.py` `setup_steps`, `setup`, the `pair` command (`node.py:793-807`) and `pair_script`'s tests now go through the script; the plan's `--dry-run` output gains three steps.

## C. Ruling 137 in code: the door opens by default

**Every default-closed lock of that kind, found in code.**

| Lock | State | Where |
|---|---|---|
| `MarketDoor.open` refuses without `[data] seal_boundary_ns` | EXISTS, the lock | `market_data.py:212-226` |
| The seal is a required field; "a door without the holdout lock is not a door" | EXISTS | `market_data.py:173-174,184` |
| A missing boundary makes the host's door `None`, so no market route is mounted (the check's lane 4 got 404 for this reason) and every data tool raises | EXISTS | `host.py:893-910`, `:683-684`; `qmx_tools/service.py:249-252` |
| A 12-month holdout whenever a boundary exists | EXISTS | `market_data.py:76,227` |
| Downloaders, the ML dataset step and the old-ticks import cannot even commit without a boundary, because they open the door | EXISTS | `templates/download-dukascopy/scripts/download.py:245`, `download-binance/.../download.py:175`, `download-ccxt/.../download.py:170`, `d6-ml-training-run/scripts/dataset.py:174`; `scripts/data/import_old_ticks.py:788-791` (required flag) |
| `[data]` is not a Settings section, so not even the boundary is editable in the UI | EXISTS | `qmx_control/service.py:51-67` |
| The final look is served only by the door placed on the server ("the server holds the main copy and is the primary") | EXISTS, a ruling 136 contradiction | `market_data.py:103-104,192-195`, `_final_look` |
| QMB's governed replay builds a seal from the split manifest and its `holdout_months` | EXISTS, QMB's own (a later item for the QMB and unit sessions) | `qmb/host/replay_request.py:346`, `qmb/host/replay.py:281-299` |
| Not locks, kept: the run-pass `data_scope` check on remote callers (access control for remote runs, ruling 117); a split read without split definitions is answered by name (nothing to clip) | EXISTS | `market_data.py:622-646`, `:705-715` |

**Decision.** The shape, per study, off by default, editable in the UI:

- `MarketDoor.seal: HoldoutSeal | None = None`. `open` never refuses for a missing boundary; it refuses only a store it cannot read. With no seal, `_sealed` answers false, `card` shows no boundary, `holdout_task` files nothing, and `final_look` and `move_seal` answer by name ("this study has no holdout; read with exploration, which serves every month").
- `read` and `materialise` take an optional `holdout` (`{boundary, months}` or `off`) for the study the read is for, which builds that read's `HoldoutSeal`. The study's own holdout lives in Lab AD-6's holdout registry once the Lab's study record exists; until then the run configuration or the tool call carries it.
- Settings gains a `data` section (added to `SettingsSection`): `holdout` off by default, and when on, the boundary month and `holdout_months` (12) as the default for new studies. A study's `off` beats an `on` default.
- `primary` follows `[library] primary` (today `pc`), not the placement name.
- `import_old_ticks.py --seal-boundary-ns` becomes optional. The four template scripts need no edit, because `commit` never used the seal; only the Dukascopy README line changes.

**Its own PR, WU11, after WU9b.** It touches the door, the tools, the settings schema, a script and tests that WU9b does not, it is proven entirely on the PC, and folding it in would make WU9b's server verdict wait on an unrelated diff. The one shared file is `HO/host.py` (`market_door` only), order WU9b first.

- **Done when** a door opened with an empty `[data]` serves a 1996 partition with `exploration`, and a study holdout seals only that study's reads.
- **The one check.** `HOT/test_market_data.py::test_door_opens_without_a_holdout_and_serves_1996`.
- **Blast radius.** `host.py:893-910` and its mount; `qmx_tools/service.py:241-260`; `HOT/test_market_data.py:56` (opens with a seal, still valid); `QA/qmx-engine/tests/test_lab_lane3.py:84` (passes a seal, still valid); `scripts/probes/data/p_finallook.py:66,134` (passes a seal); `scripts/data/test_import_old_ticks.py`. The Settings row on screen belongs to the UI session (BACKLOG line).

## D. Ruling 136, the gap list (for a later round, not built now)

The right shape in one paragraph: the PC is primary and holds everything first, data included, with a local backup always. A server (Contabo, a burst provider, any borrowed machine) keeps work moving while the PC is off and adds capacity; while it stands in, its work waits on its own refs and its new data waits on its own disk, and when the PC returns the PC takes it home and the server goes back to helping. The PC never waits on a server. The trading node follows the same model: it keeps trading when the laptop closes and sends its records home.

| # | Gap | Where, in the merged design and code | ADs | Recommendation |
|---|---|---|---|---|
| G1 | The flip makes the server primary at setup | Library AD-19 ("made unconditional", "never a reason to keep the PC primary"), AD-26; `qmx_control/primary.py` (`Flip`, the card, `press`); WRAPUP-PLAN G-FLIP and G-LAND | Lib AD-19, AD-26, AD-14 | Superseded now (recorded). `[library] primary` stays `pc`. Keep the server's refusal of `main` (built in WU9). Reuse `Flip`'s quiesce and push-until-equal only if the hand-back needs them; otherwise retire it with a caller scan |
| G2 | Price partitions: the server is the main copy, the PC a cache | Lib AD-10, AD-25 (PC-born partitions pinned until the server verifies them), AD-28 | Lib AD-10, AD-25, AD-28 | The PC store holds every partition as the main copy; a server holds what its work needs. Reverse the pin: a partition born on a server stays pinned there until the PC has verified it |
| G3 | The final look and the door's `primary` belong to the server's placement | `market_data.py:103-104,192-195` | Lib AD-28 | `primary` follows `[library] primary`. A server door forwards a final look to the PC and waits (already built for a non-primary door). Lands in WU11 |
| G4 | Contabo is "the always-on home" with its own scheduler | Engine AD-30, AD-3 | Eng AD-30, AD-10 | One schedule list, homed on the PC. A server fires a PC-homed trigger only while it holds a stand-in lease (no PC heartbeat for a time he sets in Settings), at most once per occurrence through the fire claim, which syncs to the PC so its catch-up skips it; the lease ends at the PC's first heartbeat |
| G5 | Feeds and downloaders default to the server because "the data's main copy lives there" | Engine AD-68 | Eng AD-68 | Default `pc`, the server as stand-in under G4's lease; what it fetches comes home by G2 |
| G6 | The PC as a replica with an outbox; server-run results reach `main` only after the flip | Lib AD-14, AD-26, Deferred row; BACKLOG WU9 lines 31, 32, 35 (`Replicator.for_home` is `None` while the primary is `pc`; nothing pulls a server's `refs/runs` to the PC) | Lib AD-11, AD-14, AD-18, AD-26 | The PC pulls every server-owned run, session and draft ref on wake and lands records by AD-18's class rule as if it had run them. The outbox becomes the server's list of work waiting to come home; the PC needs none for its own writes |
| G7 | Backups start from the server; no local backup on the PC | Lib AD-16 (PC to server, server to bucket, server-loss procedure) | Lib AD-16 | A local backup on the PC always, in its own folder on another drive chosen in Settings (default the largest drive that is not the home's), the server as off-site copy, the bucket optional. Losing a server is routine; losing the PC is the drill |
| G8 | Server-born durable blobs have one copy, on the server | Lib AD-10 ("Until the bucket exists"), AD-27 (extraction is a server workflow) | Lib AD-10, AD-27 | Born-on-server blobs come home to the PC on wake like G6; extraction runs where it is placed, PC by default |
| G9 | The old ticks are planned to live on the server | ruling 130 says they are on the PC; DATA-PLAN DR0 copies them up; `scripts/data/import_old_ticks.py` targets the server home | Lib AD-10, AD-25 | Import into the PC's store first; the server gets a copy only for work placed there |
| G10 | Server-only roles: the vault replica and the central relay | Eng AD-28, AD-30 | Eng AD-28, AD-30 | Holds as capacity: PC work never needs them, and burst work that does waits `placement` while the server is down. Wording only |
| G11 | The trading node and every burst machine | Eng AD-70 (a trading server sends to the Library server within seconds); ruling 136's last sentence | Eng AD-70, AD-30 | The same stand-in model: records go to the PC when it is up and to a server stand-in when not, then home. The design belongs to the trading-node and unit sessions |
| G12 | The bootstrap writes `primary = "server"` into `/var/lib/qmx/hub.toml` | `node-bootstrap.sh` ("the server is primary from this setup on"), read by the standalone Hub (`qmx_hub/server.py:944`, disabled by setup) and the bucket config | Lib AD-19 | Drop the `primary` line with the stand-in round; harmless until then because setup disables the standalone Hub |

Monitoring (engine AD-69) already fits: the PC keeps its own health view, and the outside layer on the server is an addition.

## The WU9 second round (WU9b): Files block

Stacked on `build/wu9` at `546d06f1`, which is not stacked (NOT CLEAN, the one fix round used). This is a new PR that carries WU9's diff plus these changes, with a fresh check.

- [ ] Edit `QA/qmx-host/pyproject.toml` and `qmx-agents/uv.lock` (declare `qmx-memory`, `qmx-router`, `qmx-remote`, `qmx-broker`, `qmf-core`, `qmf-data`).
- [ ] Edit `HO/host.py` (`compose_memory` follows `[memory] hindsight` on the node and server roles; `serve` computes the bearer once with `local_token(home, create=True)` and passes it to `compose` and `PrincipalDoor(bearer=...)`; `health(port)` passes the home).
- [ ] Edit `QX/server.py` (`local_token(home=None, *, create=False)`, the file path where the keyring has no backend).
- [ ] Edit `QX/node.py` (setup steps in this order: bootstrap, install the recovery script and its conf, close the firewall with the fresh-SSH check, install the host, stop the standalone Hub, move the pairing key and the control token, import as `qmx`, start the host; `pair` hands the code to `qmx-recover pair --from-stdin`; the server commands' `--vault` default becomes `SERVER_HOME/vault`; `verify` gains a `firewall` line; the PC side of setup writes the twin and its conf to `<home>/bin/`).
- [ ] Add `QX/qmx-recover.sh` and `QX/qmx-recover.ps1`.
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/__main__.py` (`local_token(home)` at line 251).
- [ ] Edit `R/server.py` and `QA/qmx-host/deploy/otelcol.yaml` (comments only: the firewall of engine AD-71 is what makes the tailnet the only way in).
- [ ] Add tests: `QXT/test_control.py` (the token file), `QXT/test_recover.py` (stub `PATH`), `QXT/test_node*.py` (step order, the move, the `pair` call), `HOT/test_host.py` (server-role memory, the declared-imports guard).

`QX/` is `qmx-agents/packages/qmx-control/src/qmx_control/`, `QXT/` its tests, `HO/` and `HOT/` the host's source and tests, `QA/` `qmx-agents/packages/`, `R/` the router's source. `HO/door.py` is not edited, because the host now passes the bearer.

**Verify, unit.** The four new tests above, plus the control, host, router, engine and remote suites with `-n 2`.

**Verify, live** (on `haiku` where a model is needed, per the boot recipe):

1. The suites at parent `546d06f1` and head. Pass when head fails nothing the parent passes.
2. A1's check on the server. `wu9b-imports.log`.
3. WU9's lane 2 again, with no workaround: setup against `/srv/qmx/check/wu9b` as `qmx`. Pass when the host runs under the unit, answers on loopback with the file token, serves the one root, and no standalone Hub is left. `wu9b-setup.log`.
4. A3's check, run on the real server with the undo armed; lane 9 opens the firewall again (or lets the undo fire), because the real close is the G-LAND setup. `wu9b-firewall.log`.
5. B's live lane on the scratch conf. `wu9b-recover.log`.
6. WU9's lanes 3 and 4 (sync and pass) again on the new head.
7. `tools/secret_scan.py`, and a grep of every lane log for the planted token and key values. Pass when both are clean.
8. Gates in the control, host, router and engine packages. Every exit code 0.
9. Remove `/srv/qmx/check/wu9b`, open the firewall or confirm the undo fired, list processes on both machines. Pass when nothing from the lanes is left and `ufw status` matches what lane 4 found.

**Perf.** Seconds for `qmx node setup` on the server (lane 3), recorded, no fail rule.

## The separate PR (WU11): Files block

- [ ] Edit `HO/market_data.py` (optional seal, the per-read `holdout`, named answers when none, `primary` from `[library] primary`).
- [ ] Edit `HO/host.py` (`market_door` returns `None` only for a store it cannot read; the market router always mounts).
- [ ] Edit `QX/service.py` (`data` in `SettingsSection`, with a parser for the holdout fields).
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/service.py` (passes the optional holdout; narrower message when there is no door).
- [ ] Edit `scripts/data/import_old_ticks.py` (`--seal-boundary-ns` optional) and the `download-dukascopy` README line.
- [ ] Add tests in `HOT/test_market_data.py` (opens with none and serves 1996; a study holdout seals only its reads; a final look with none is answered by name) and `scripts/data/test_import_old_ticks.py`.

Verify: those tests, the host, tools and engine suites, and one live lane on the PC: `read_bars` from a chat for a 1996 window answers rows. Order after WU9b (shared `HO/host.py`).

## Spine amendments made

- Library spine: AD-10, AD-14, AD-16, AD-19 and AD-26 record ruling 136 and mark the flip superseded; AD-28 records ruling 137; the Deferred row on the PC's replica write path is superseded, and one row added for the stand-in round.
- Engine spine: AD-30 and AD-68 record ruling 136; AD-52 records A1 and A2; AD-71 added for the recovery script and the firewall; two Deferred rows (the stand-in round, a public listener).
- Both memlogs carry the decisions; `lint_spine.py` gives 0 findings on both spines.

## Reviewer gate

Sub-agents are barred by the brief, so the lenses ran inline. Rubric walk: AD-71 makes AD-11's "the Hub listens on the tailnet first" true rather than weakening it; AD-52's file token keeps the PC's keyring path as built; the AD-28 amendment removes a default-closed lock without weakening an opted-in holdout; no AD reintroduces a money gate or sandbox (rulings 116 to 118); every new text says "unit", never "bot" (ruling 138). Edge lens: a host that boots before Tailscale has an address still binds (the reason binds stay `0.0.0.0`); a rerun of the firewall step stops a leftover undo first; a wrong home fails plainly instead of minting a second token; the recovery script's own failure cannot block a start, because nothing on the start path calls it.

## For the BACKLOG (not in either PR)

- The server allows password SSH and root login. Hardening it to key-only is a separate step, done with the undo pattern and the VNC console at hand.
- The remote image still installs only `qmx-remote`, while the sidecar imports `qmx_engine` (`RM/sidecar.py:574`; BACKLOG line 27 stands; `qmx-remote` also imports `qmx_engine` undeclared, and declaring it needs a check for a dependency cycle).
- Other undeclared first-party imports (none outside their closures): `qmx-control` imports `qmx-library`, `qmx-hub`, `qmx-engine` and `qmx-router`; `qmx-engine` imports `qmx-apps`, `qmx-library` and `qmx-remote`; `qmx-broker` and `qmx-tools` import `qmf-core`. Several would be cycles, so they wait for a package-layering pass.
- The server has uv 0.13.4 while the bootstrap pins 0.12.23 and reinstalls it on every run.

## What needs him

Nothing. Every question in this round was technical and is settled above. The firewall's real close happens inside the setup he already approved at G-LAND, with SSH kept open and the five-minute undo.
