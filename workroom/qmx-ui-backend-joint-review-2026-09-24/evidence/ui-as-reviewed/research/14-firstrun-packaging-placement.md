# 14 — First-run, packaging, and placement

Sitting: `architecture-QMX-UI-2026-09-23`. Covers UX-01 (launch / first-run / reconnect), UX-12 (settings / files / terminal / previews), UX-11 consumption of existing health axes, and 03-EXPERIENCE-SCOPE §6 (command identity, local≠VPS, close-window vs stop-work, desktop packaging).

This is research for the UI sitting. It is not a spine, not an installer spec, and not an implementation grant. **PROPOSAL** rows are assistant defaults to evaluate. **U** rows are current user direction from `02-CURRENT-DIRECTION.md`. Class/test existence at inspect SHA is not end-to-end proof.

## Pins

| Pin | Value |
|---|---|
| Inspect SHA | `integration@34c148be404a375cbfd79fd4ce6997452e4f1d20` (2026-09-20, story 59.5) |
| Inspect tree | `C:\Users\Mubarak\Desktop\QMX\.worktrees\integration-inspect` |
| Docs snapshot | Workspace `docs/` (stack.md `verified: 2026-09-23`); do not treat docs as proof the inspect process is live |
| Parent freeze | `270e992` for original ADR-0024 Decision text; this report does not reopen pack-and-grant kit ADs |
| UI branch | `af6628888fb8901bf9e877cbd07e438dbb0f39b4` is **not** a UI implementation base |
| Law numbering | Secrets-as-refs is **L34** (DEC-0136), not L33. L33 is the plain-Python graduation hatch (DEC-0133). |
| Epic 045 | QMA **Epic 45** = environments / Compute Router / JobHandle / RLM / QMB door (FEAT-0044). Story **45.9** is workstation deployment + computer-use exclusion + remote dial-out. FEAT-0045 is the later ledgers epic. |

Legend: **reuse** = already specified or coded, host it; **adapt** = exists, UI must wrap without inventing a second store; **add** = UI/host work this sitting must name; **hole** = contract missing or unwired; **unverified** = user mention or docs without inspect proof.

---

## 1. First-run sequence — **PROPOSAL**

**U:** A deliberate splash/loading then practical configuration. Inspirations are PyCharm and DaVinci Resolve, not Electron-style instant chrome. Include provider credentials / API keys, the mentioned CLI proxy, target connections, and terminal access. Exact provider mechanism is unverified. Brand polish is not a blocker. Do not block all work behind one unavailable provider (UX-01).

### What already exists to hang this on

- QMA daemon default host is the operator workstation; workers are declared Docker-per-worker on that host (`DeploymentEnvelope.host = "operator_workstation"`; Story 45.9 / FR-Q56).
- Wire listener default is loopback `127.0.0.1:8765`. Non-loopback requires `wss://` + HTTPS **and** an explicit operator-recorded config. Unauthenticated bind is a hard startup refusal (`qma-wire/src/qma/wire/listener.py`).
- Listing health is five independent axes: published / configured / granted / reachable / healthy (`listing.py`). First-run must not collapse these into one lamp (UX-11; AD-15; G-34).
- QMN is a **separate** always-on VPS product. The desktop reaches its three doors later over an **SSH tunnel**. The node has no operator CLI. Workstation `qmn` install is provisioning-only; `SecretStore` refuses to construct a venue-session holder off the roster VPS machine tuple.
- Computer-use / Windows VPS is **GAP-0070 deferred**: every `desktop` tool fails `check_fn`; Compute Router returns `NoEnvironment`. First-run must not offer a computer-use setup wizard as if the host existed.
- `qma-ui-contract` is a stub. There is no splash, no installer page, no settings chrome at inspect SHA.

### Proposed sequence (not a wizard that owns the product)

Treat first-run as a **readiness walk**, not a compulsory research→backtest→paper funnel (that funnel is already refused in `qma-core` procedures). Each step is skippable except “a daemon the UI can talk to” if the user wants local work. Remote-only reconnect is a first-class path (UX-01).

| Step | Surface | What it does | Blocks? | Owner |
|---|---|---|---|---|
| 0 | Native splash (small, logo + status line) | Show while the host process starts and probes. Inspired by Resolve/PyCharm splash, **not** a full window. No brand system required. | No work yet; splash is the wait, not a gate | UI host (**add**) |
| 1 | Discover runtime | Probe loopback `127.0.0.1:8765` (or last-known bind). States: **none / starting / loopback-live / remote-recorded / refused**. If none, offer **Start local daemon** (host-supervised) **or** **Connect to recorded remote** (SSH tunnel / non-loopback WSS). Never silently retarget remote failure onto local (03 §6). | Local work needs a daemon. Headless CLI (`qmb`) stays available without the UI. | Host starts `python -m qma.daemon`; does not invent a QMA CLI (DEC-0336) |
| 2 | First usable window | Platform rail + Home + copilot shell with **partial readiness**. Home shows running/attention items independently of opened apps (UX-02). Missing provider ≠ empty product. | Never | Shell (**add**) over listing axes (**reuse**) |
| 3 | Provider / proxy checklist | Cards, not a modal wall: (a) local CLI proxy loopback, (b) QMA-owned model/inference refs in OS store, (c) optional QMN target, (d) optional compute/GPU env. Each card is available / configured / authorized / reachable / healthy. Connection tests **must not mutate accounts** (G-24). | Only the capability that needs that provider. Copilot without a model is “no eligible deployment”, not a frozen app. | See §2 |
| 4 | Target connections | Optional QMN SSH tunnel (powers + evidence). Optional remote ExecutionEnvironment that **dials out** to the daemon (Story 45.9). Trading-node host identity is refuse-at-register. | Trading/risk ops need QMN. Research/ML/library do not. | QMN doors **reuse**; tunnel UI **add**; GAP-0058 single-machine node is **not** this walk |
| 5 | Files / terminal / previews | Pick a workspace data root. Show local vs remote availability. Terminal is a **preview/work tab**, not a general privileged shell (AD-21). | No | UX-12 **add**; see §3 |
| 6 | Reconnect | After splash or crash: attach with `producer_id` + `since_seq`; restore `product_session` durable fields; **do not** cancel jobs; **do not** replay intent (AD-17; 03 §6). Reconcile authoritative status before offering retry. | No | Wire **reuse**; chrome **add** |

Splash copy (PROPOSAL, no brand lock): product name + one status string (`Starting local runtime…` / `Looking for daemon on 127.0.0.1:8765` / `Connecting to recorded target…` / `Ready — 2 of 5 providers healthy`). Keep it small. Closing splash without a daemon still opens the shell in **disconnected** state with retry.

### Partial readiness (required)

Do not invent a global green light.

| Capability family | Ready when | Degraded when | Hard-unavailable |
|---|---|---|---|
| Shell / Home / Library browse | Daemon loopback or recorded remote answers initialize | Reconnecting; stale snapshot | No daemon and user declined start |
| Copilot / model work | ≥1 ModelClass has an eligible Deployment | Proxy down; `NoEligibleDeployment` | All classes empty |
| Governed backtest | `qmb` CLI reachable in an eligible env | Recording/unwired transport | No env / no `qmb` on PATH |
| Trading / risk ops | QMN doors reachable **and** paper/live Book binding identity known | Evidence channel only | No tunnel; node stand-down; missing venue refs |
| Computer-use | `desktop` env registered (GAP-0070) | — | Default: fail-closed, hide or disable with named gap |
| Remote GPU | `remote_host` / `remote_container` registered, dial-out healthy | Queued / unknown job | `NoEnvironment` |

**Actionable retry:** each card retries **its** probe (daemon ping, proxy loopback TCP, QMN evidence GET, env `check_fn`). Retry must not duplicate side-effecting commands (03 §6). A cancelled display is not proof computation stopped.

### What this sequence must not do

- Require a brand DESIGN.md or PyCharm/Resolve proprietary assets.
- Install or configure `~/.opencodex` plaintext files as a QMA secret source (DEC-0371 cut).
- Offer venue/broker API-key fields in QMA settings (allowlist refuses `cred://venue|broker|exchange|trading-node|platform-registry/`).
- Start a second daemon, an HTTP experiment service, or a QMA/QMN operator CLI.
- Treat “browser tab open” as job lifetime.
- Walk the user through GAP-0070 Windows VPS purchase, GAP-0058 single-machine node installer, or GAP-0062 always-on host selection as if those designs existed.

---

## 2. Secrets and providers — reuse vs add

Two **namespaces**. Mixing them in one “API keys” form is a law break.

### A. Trading-node / venue secrets (QMN) — **reuse**, UI later fronts them

| Piece | Status at inspect | First-run implication |
|---|---|---|
| L34 / CT-21 `SecretRef` + `SecretValue` + `SecretStore` | Coded in `qmf-core` (`packages/qmf-core/src/qmf/core/secret.py`). Values never render. Opaque minted ids only. | Settings show **is_set** + ref id, never plaintext. |
| VPS two-layer store | systemd-creds `LoadCredentialEncrypted --with-key=host` (KEK + bootstrap) + AEAD rotated material under `/var/lib/qmx/state`. Backup payload key escrowed on workstation, never VPS-minted. | First-run on Windows does **not** seal venue secrets into the laptop. |
| Workstation wizard | `just node-secrets-provision` (`qmn/deploy/secrets_provision.py`). Human-only. Reads named `qmx/*` slots, streams over SSH stdin into `systemd-creds encrypt`. Check mode plans without reading the OS store. Live `--apply` refused off-VPS. | **Reuse** the recipe. UI may later wrap it; do not reimplement as a form that posts values to the daemon. |
| Slot list | `venue-client-id/secret`, access/refresh tokens, cTID accounts, `backup-payload-key`, object-storage, notification, grafana-admin, log-shipper. | Trading target card lists these as refs. |
| Off-host refusal | `try_create_secret_store` refuses `machine != roster_vps_machine` (`qmn/src/qmn/secrets/store.py`). | A local-only first-run cannot honestly “save broker keys into QMX” for live use. |
| `keyring==25.7.0` WinVault | **Documented** in `docs/architecture/stack.md` for the wizard. **Not imported** by `qmn/deploy` at inspect (tests ban `keyring` on the node path). Wizard uses a `CredentialSource` protocol; live CredRead wiring is composition-root work. | **Hole:** OS-store read for the wizard is specified, not proven as a packaged CredRead. |

`.env` files as a product secret source are **cut** (DEC-0371; runbook: repo/chat/config/`.env`/CLI refuse). Factory `.env` (SSSF lanes) is DevOps, not first-run.

### B. QMA Credential Broker (models / compute / corpus / telemetry) — **reuse** types, **add** host write path

| Piece | Status | Reuse / add |
|---|---|---|
| Allowlist prefixes | `cred://models/`, `inference/`, `compute/`, `sandbox/`, `corpus/`, `knowledge/`, `telemetry/`. Source in `qma-core`, never UI-editable, never a plugin. Out of scope: venue/broker/exchange/trading-node/platform-registry → `CredentialOutOfScope`. | **Reuse.** First-run form must not offer out-of-scope prefixes. |
| Broker | `qma/daemon/proxy/broker.py`. Exact-ref read only. No enumerate/search/list/glob. Adapter-layer caller only. | **Reuse** resolve. **Add** a host “store this ref” path: UI collects plaintext once, writes to Windows Credential Manager under the ref, daemon only ever sees the ref. |
| Windows backend | `WindowsCredentialManagerBackend` takes an injected `_reader: Mapping[str, str]`. If `_reader is None`, resolve returns unavailable: *“Windows Credential Manager reader is not wired at the composition root”*. `DaemonProcess.compose` does **not** inject CredRead. | **Hole.** Types exist; composition root does not wire OS CredRead. First-run cannot claim “keys are in Credential Manager” until that inject exists. |
| Wire auth | `authenticate_before_protocol` requires a `credential_ref` + principal `operator|machine`. Wire surfaces refuse `api_key` / `token` / `secret` keys. The function does **not** call the broker; it validates shape. | **Adapt.** Host presents operator credential **ref**, not a pasted key, on initialize. |
| `registry:proxy.allow_unauthenticated_loopback` | Default `true`, documented ui-editable, operator-overridable. Unauthenticated loopback proxy refused with `UnauthenticatedProxy` when false. Startup evidence names each proxy Deployment + this setting. | **Reuse** as a settings row (L38). Not a first-run blocker. |

### C. Local CLI proxy (OpenCodex as first ModelDeployment) — **reuse** contract, **do not** ingest its files

See §7. QMA registers a local-proxy Deployment with `auth_mode: none`, loopback-only (`NonLoopbackProxy` otherwise). **No QMA-resolved secret crosses into the proxy.** Provider credentials stay the proxy’s custody. First-run “API keys” for ChatGPT/Claude/xAI belong **in the proxy’s own UI/CLI**, not in a QMA form — unless the operator later wants QMA-owned `cred://inference/*` for non-proxy deployments.

### D. What to add in this sitting (UI/host only)

1. Settings scopes (UX-12): **global / app / session / instance**. Map onto existing objects: registry-homed variables (L38), pack config revision, `product_session`, plugin-install `instance_id`. Do not mint a sixth settings store.
2. A **write-once** host helper: “save this value into Windows Credential Manager at `cred://…`”. Daemon never receives the value. Connection test = broker resolve in an adapter-layer probe that discards the egress frame, or a loopback TCP probe for the proxy.
3. Health cards bound to listing axes + `NoEligibleDeployment` / `unavailable-dependency` refusals (ref id, never value).
4. Do **not** add a QMA secret sqlite, a `.env` importer, or a UI that lists every Credential Manager entry (enumerate is forbidden).

---

## 3. Local file vs VPS path resolution — contracts vs holes

**U / 03 §6:** A local path does not establish VPS access. Define resource resolution, explicit staging or refusal, partial-transfer recovery, and version identity. Remote failure must not silently retarget a job locally.

### Existing contracts (**reuse**)

| Contract | What it already says | Evidence |
|---|---|---|
| Durable identity is content, not a path | Machine-local paths are not portable ids. Artifacts carry schema, content identity, provenance, completeness, authorized resolution. | 09-18 AD-3 Prevents; `.memlog`; J08/J22; OP-NEW-14 |
| QMA daemon data root | `QMA_DAEMON_ROOT` env, default **cwd-relative** `"qma-daemon-data"`. Substrate opens `root/qmf-data` + `root/daemon` with a sole-writer lock. Machine env `QMA_DAEMON_MACHINE` default `"workstation"`. | `__main__.py`, `persistence/substrate.py` |
| QMN VPS trees | Code `/opt/qmx` (immutable per-commit + `current` symlink). State `/var/lib/qmx/{rooms,evidence,hub-inbox,hub-published,archive,state,staging}`. Powers `/run/qmn/powers.sock`. | `docs/architecture/overview.md`, runbook |
| QMN workstation plane | Provisioning-only. No live venue credential. Composition root refuses to compose off the roster VPS machine tuple. | stack.md; `qmn/src/qmn/secrets/store.py` |
| Remote dial-out | Remote Quant/Mission/Worker **dials out**; daemon never dials in; deployed side opens no inbound port. Trading-node host identity refused at registration. | Story 45.9; `envs/boundary.py`; `qma-wire` reachability |
| QMB door | Production transport is `CliQmbDoorTransport` (subprocess `qmb`). Default in `BacktestingService` at inspect is `CliQmbDoorTransport()`, not the recording double. Occupancy: one run per ExecutionEnvironment. | `backtest/service.py:374-376` |
| Listing vs grant | published ≠ configured ≠ granted ≠ reachable ≠ healthy. Hit is not a grant. | `listing.py` |
| UI must not kill work | Mount/dispose must not start/kill durable backend work. Tab-close cancels nothing. | 09-18 AD-17; Workbench AD-10 |

### Holes (still true after 09-18 desk-fix intent)

| Hole | Why it bites first-run / UX-12 | Disposition |
|---|---|---|
| **G-11 staging preflight** | AD-3 bans path-as-id; AD-15 bans laptop-coordinator durability. Neither states: when a job is placed remotely, **stage as portable artifact or refuse before execution**. J07/J22 name the journey; inspect has no stager module. | **PROPOSAL:** host preflight — if `execution placement` is not `local` and the input is a machine path, either (1) hash+upload to daemon artifact store and pass the artifact ref, or (2) typed refusal `LocalPathNotPortable` naming the path **class** (not the absolute path in logs if it encodes a home directory — prefer a user-visible path and a content hash). Partial transfer = job `unknown` until operator resolve; no silent local fallback. |
| **Cwd-relative daemon root** | Default `qma-daemon-data` follows the process cwd. Two launches from different folders = two daemons’ worth of sqlite/journals, plus the in-process/on-disk sole-writer lock fighting. | **PROPOSAL:** packaged host sets `QMA_DAEMON_ROOT` to a stable per-user directory (`%LOCALAPPDATA%\QMX\qma-daemon` on Windows; `$XDG_STATE_HOME/qmx/qma-daemon` on Linux). Document the env. Do not keep the cwd default in a shipped product. |
| **QMN path ≠ QMA path** | Staging into `/var/lib/qmx/staging` is node-owned. QMA artifact store is under the daemon root. There is no “copy this laptop file onto the trading VPS” operation, and QMA must not reach the node host. | First-run must not imply Library files are on the VPS. Trading data bootstrap is `just node-data-bootstrap` (Dukascopy), not a UI file picker. |
| **SSH tunnel is specified, not a product** | Desktop UI over SSH to localhost/socket doors is Phase-3 prose. No tunnel supervisor in inspect. | **Add** a host “QMN target” card: recorded host, identity file (provisioning identity is **not** the operator identity), tunnel up/down, evidence GET health. Do not open a public port. |
| **GAP-0058** | Single-machine node (node + agentic system on one box, out-of-the-box installer) is **open, design owed**. VPS epics are not blocked. Supervision without systemd, secret store without systemd-creds, powers without AF_UNIX — unnamed. | First-run must **not** ship a “install trading node on this PC” path until that increment. Colleague-try-this is a later placement profile (G-33), not a SKU. |
| **Preview ≠ permission** | UX-12: browser/video/code/diff/terminal/model/result previews. 03 §4: preview rendering must not imply installation or execution permission. | **PROPOSAL:** preview adapters are host-local. Opening a terminal tab does not grant `CLI` tools to a Mission. Opening a local file in the work area does not stage it remotely. |

### UX-12 settings / files / terminal — **PROPOSAL** mapping

| UX-12 item | Reuse | Add |
|---|---|---|
| Global settings | Registry variables (L38); `proxy.allow_unauthenticated_loopback`; listener bind (operator-recorded) | Settings tree chrome; never widen credential allowlist |
| App / instance settings | Plugin-install instance + config revision; GrantRecords | Scoped editor; connection tests without account mutation |
| Session settings | `product_session` durable fields (profile, app_instance_id, selected_refs, grants). **Not** layout JSON (daemon rejects widget/layout blobs) | Persist layout/session **chrome** in the host (GAP-0081), not in daemon selected_refs |
| File location + remote availability | Artifact refs; KnowledgeSource snapshot; QMB run-dir | File picker that records “upload vs pointer” as distinct (03 §4); remote badge from placement, not from path shape |
| Terminal preview | User asked for terminal access; LSE clip shows a lower Terminal pane (reference only; LSE **layout** is rejected for ML Studio, the clip is still evidence that a terminal pane exists in the inspiration set) | Host PTY or task-output panel. AD-21: useful log/progress ≠ general shell. QMB remains the only operator CLI. |
| Unsupported preview fallback | — | Typed “cannot preview this kind here”; offer Open in OS / show hash / show path |

LSE `terminal-preview.mp4` is an 11s **reference**, not QMX behavior. Do not copy LSE Markets/ticket chrome into first-run.

---

## 4. Desktop packaging — browser + local daemon vs Tauri sidecar vs both

**U:** Svelte + TypeScript is the working frontend. Qt is out. Tauri/Rust remain of interest for desktop/native responsibilities. No whole Python-core rewrite. **P:** evaluate host and process boundaries against workloads, install, and lifecycle. 03 §6: plan bundled vs external Python/models/runtimes, provider/proxy dependencies, process supervision, data directories, updates/rollback, clean-machine install, launch outside the checkout, network loss, local/VPS recovery.

Inspect has **no** Tauri, Electron, NSIS, MSI, or UI package. `qma-ui-contract/STUB.md` defers UI SDK, contribution points, and **UI plugin packaging**. 09-18 AD-17: the host is a **client** of `qma-wire`, QMB API/CLI, and QMN three doors. Daemon-stack study (2026-08-28): UI is a detachable client; a Rust UI attaches over the wire; the daemon stays Python 3.14.

### Option A — Browser + independently supervised local daemon

How: packaged or dev Svelte app in a browser; operator (or a tiny host script) starts `python -m qma.daemon`. Loopback only by default.

| Close-window | Stop-work |
|---|---|
| Closing the tab/window **must not** cancel jobs, stop the daemon, or flatten anything (AD-17, Workbench AD-10, Constitution detachable UI). | Stopping work is an explicit command (`stop_run`, `JobHandle.cancel`, QMN powers). Closing chrome is observation loss, not authority. |
| Reopen = reconnect (`producer_id`, `since_seq`, product_session). | Daemon death on a laptop **does** stop local workers and makes JobHandles `unknown`. That is GAP-0062, not a UI close handler. |

Consequences: matches parent law with the least new machinery. Weak splash (browser cannot do a Resolve-class native splash before the document). Weak OS integration (file dialogs, PTY, Credential Manager, autostart). User can “launch the app” and see a disconnected shell if the daemon was never started — first-run step 1 must be loud. Distribution is “install Python 3.14 + uv + Docker + this wheel + a URL”, which fails the clean-machine bar unless wrapped.

### Option B — Tauri sidecar that **owns** the Python child

How: Tauri webview loads the same Svelte UI; a sidecar process is `qma-daemon` (venv or embedded). Window close kills the job object → kills the daemon → kills Docker workers the daemon spawned.

| Close-window | Stop-work |
|---|---|
| Close ≈ SIGTERM to the daemon. Local jobs go `unknown` or die. QMN on the VPS is **unaffected** (correct). | Accidental close becomes an incident on the workstation plane. Conflicts with “UI is detachable”. |

Consequences: good splash, file dialogs, PTY, keychain. **Bad** lifetime. Only acceptable if the sidecar is a **separate** Windows service / scheduled task, and the window is a client of it — at which point this option has become Option C. Do not ship “close QMX = stop research jobs” unless the operator explicitly wants a supervised-session SKU (G-33 local-attended profile). That profile is unnamed; GAP-0099 (QMN supervision taxonomy) is out of scope until the platform is live.

### Option C — **PROPOSAL default:** both, with split lifetime

Same Svelte UI. Dev: browser + `python -m qma.daemon`. Packaged: Tauri webview **client** + a daemon that is **not** the window’s child.

| Process | Lifetime | Close window | Sleep/lid | Explicit Stop |
|---|---|---|---|---|
| Tauri / browser UI | Session | Disposes views only | UI gone; reconnect later | Exit UI |
| `qma-daemon` | User-session or always-on (operator choice) | Continues | Dies if only on the laptop (GAP-0062 — do not promise laptop-off) | Host “Stop local runtime” |
| Docker workers | Daemon-supervised, ephemeral | Continue while daemon lives | Die with host | Cancel job / daemon stop |
| `qmb` CLI children | Job-scoped | Continue while parent env lives | Die with host | `JobHandle.cancel` → QMB abort |
| Local CLI proxy (OpenCodex etc.) | **Outside** QMA | Continues | Independent | Proxy’s own stop |
| `qmn` on VPS | systemd | Unaffected | Unaffected | Node drain / powers, never window close |

Tauri earns its keep for: native splash (UX-01), OS file pickers, PTY terminal preview, Credential Manager write helper, recorded SSH tunnel, autostart of the **client**, optional autostart of the daemon with an explicit “keep running when I close the window” preference (default **keep running** to match AD-17). Rust is not a second daemon and does not reimplement `fp1`.

### Consequences the sitting should freeze

1. **Close window ≠ stop work** for QMA jobs and QMN trading. State it on the close dialog the first time: “Runs keep going on the local runtime / trading node.” Offer “Stop local runtime” as a separate settings action.
2. **Stop local runtime** is drain + sole-writer release. In-flight JobHandles become `unknown` if the env dies with the host; operator resolves. Do not invent terminal success.
3. **Do not** autostart the daemon on Windows boot in v1 unless GAP-0062 names a host. Default: start with the UI (or on first-run Start), keep running after close, stop on user command or logoff.
4. Bundled Python: **unresolved** (see §5). Prefer external uv-managed 3.14 over embedding until clean-machine is measured. Docker Engine is a **declared** worker isolation, not started by `DaemonProcess.compose` today.
5. Updates: QMN already has `just node-switch` / `node-rollback`. QMA/UI have **no** update channel. Do not pretend the node symlink flip updates the desktop app.

---

## 5. Clean-machine install unknowns

`02-CURRENT-DIRECTION.md`: passing static/unit checks is not evidence of clean-machine installation. `poe check-release` is the **ratified** tier-3 gate (build + clean-install smoke on Windows 11 x86-64 and Ubuntu LTS). That gate is for **library wheels**, not a desktop product. Ubuntu node CI (`ubuntu-24.04` check-mode boot + unit-file scan) is not a Windows UI installer.

Unknowns to record rather than invent:

| Unknown | Why it matters | What would close it |
|---|---|---|
| Does `python -m qma.daemon` run on a machine with only uv + CPython 3.14 + the lockfile, **outside this checkout**? | `__main__.py` exists; `qma-daemon` pyproject has **no** `[project.scripts]` console entry (intentional: not an operator CLI). Compose opens sqlite/journal, activates desk packs, binds a **raw TCP** server that **reads and discards bytes**. It does not speak WebSocket, does not run `negotiate_initialize`, does not start `DeploymentBoundary`, does not inject CredRead. | An installed-product smoke: create venv from wheels, set `QMA_DAEMON_ROOT`, run module, HTTP/WS initialize from a client, assert refusal shapes. **Not done.** |
| Docker Engine 29.7.2 | Stack pin for default worker isolation. `DeploymentBoundary.start()` **registers** `ordinary_docker_worker` in-memory. `DaemonProcess.compose` never calls it. No `docker run` in daemon `src/`. | First-run must treat Docker as **configured/unreachable** until a real placer exists. Do not block the shell on Docker missing. |
| TA-Lib C library, tzdata, protobuf | Library pins. A UI installer that omits them breaks indicators/venue later, not first paint. | Document as runtime deps of QMF/QMN, not of the Svelte bundle. |
| OpenCodex / `ocx` on PATH | Architecture’s first ModelDeployment. Not a QMA dependency in `qma-daemon` pyproject. Research (2026-08-28) observed a **local** install on the operator machine (`127.0.0.1:10100`). Code default bind port for the adapter is **3921**. | Clean machine has **no** proxy. Copilot degrades to `NoEligibleDeployment`. Do not bundle OCX without an operator choice (third-party npm, plaintext home files). |
| Windows Credential Manager entries | Empty on a clean machine. Broker resolve → unavailable-dependency (retryable after condition). | First-run checklist, not a crash. |
| QMN VPS | Operator-procured. Soak gated on VPS existence. Workstation without a VPS still does research/ML. | Target card = “not recorded”. |
| Data directory ACL / AV / App Control | Factory notes `python -m` because a `pyright` console script can be blocked by host App Control. A packaged `.exe` may hit the same. | Measure on a clean Windows 11 VM; do not assume the development laptop. |
| Autostart, firewall, loopback-only | Default bind is loopback; no public port. Windows Firewall usually ignores loopback. Non-loopback WSS is operator-recorded. | Keep v1 loopback-only for the daemon. QMN tunnel is outbound SSH. |
| GPU / CUDA / remote research node | No cloud/Colab assumed (AD-15). | `NoEnvironment` until registered. |
| Single-machine node (GAP-0058) | “Set up out of the box without technical knowledge” is **design owed**. | Out of this first-run. |
| Always-on host (GAP-0062) | Laptop-off continuation unnamed. | Do not promise it in splash copy. |
| Browser stack (GAP-0078) | Fail-closed until registered. | Same as computer-use: not a first-run card. |
| UI bundle + core version skew | Separate UI integration vs backend integration (U). Combined candidate before main. | First-run should show daemon protocol version (`1.0.0`) vs UI expected version and refuse with a named incompatibility, not a blank window (03 §7 “backend incompatibility” scenario). |

**PROPOSAL distribution target for v1 UI:** Windows 11 x86-64 (operator workstation) as the only packaged desktop; Ubuntu LTS as the QMN/VPS OS, not a second desktop SKU yet. Launch-outside-checkout is a required acceptance, not implied by `poe check`.

---

## 6. Paper-trading — only where trading/risk ops exist

**U (D-053):** Paper trading is not a universal mini-app gate. Use it where a capability executes trades or materially affects trading/risk. Non-trading ML, data tools, and headless utilities get functional/operational evaluation instead. No week-or-two paper gate for everything.

### Existing trinity (**reuse**, do not invent QMA-paper)

| Noun | What it is | Where first-run may mention it |
|---|---|---|
| **research-paper** | QMB governed replay (`world=replay`) outside the node. Book/BMS fragments in run-config. | Backtest / research apps. Not a splash checkbox. |
| **node-paper** | Book-level **demo** routing + soak on QMN (`role=demo`, `world=live`). Paper is an **account role on a real venue**, never a sandbox. CONNECT FX paper uses vendor demo host. Soak = one unattended week on demo; paper evidence never authorizes live money. | QMN target / trading app readiness. Soak is ops, not UI first-run. |
| **QMA-paper** | **Does not exist** (DEC-0275, DEC-0341). No execution tool at any account role, “paper only” included. Act-level deny-list at registration. | Never offer “paper trade from copilot”. |

QMA may **read** paper market data / positions / account state and change none of it. Dev-zone candidate artifacts are the only QMA write exception. Promotion is human, outside QMA.

### Where paper **does** belong in this sitting’s UX

- UX-10 trading/risk/position-sizing: environment identity, readiness/transition evidence, operations with financial effects distinct from analysis.
- Book mode / binding screens, QMN powers (paper flip, paper-epoch reset) — operator principal, SSH tunnel, not first-run.
- Alternative Trading Composition still uses sequential paper-then-live + L17 human promote (DEC-0436) when that composition **is** the trading system.

### Where paper **does not** belong

- Splash, provider/proxy setup, Library, graph/code ML, headless utilities, terminal preview, json-render inspectors.
- A compulsory research→backtest→paper wizard (already refused in procedures).

---

## 7. CLI proxy — what the user mentioned vs what is unverified

### What the user said (verbatim steer, not a vendor pick)

Visible dictation (handoff `session-visible-messages.md` / D-050):

> “the first time I set it up obviously we need credentials API keys I'm certain we use a CLI proxy for the providers the terminal dude there's so many things to consider”

`02-CURRENT-DIRECTION.md` **U:** include provider credentials/API keys, the mentioned CLI proxy, target connections, terminal access. **Exact provider mechanism is unverified.** D-050: PyCharm/DaVinci are experience inspirations; **no particular proxy implementation is selected**.

### What architecture already mapped (**reuse** as the default hypothesis)

| Claim | Status |
|---|---|
| Model call names a **ModelClass**, not a vendor | Ratified AD-15 / DEC-0314. Four classes: `REASONING_HIGH`, `WORKHORSE_GENERAL`, `CODING_HIGH`, `FAST_CHEAP`. |
| OpenCodex is the first `ModelDeployment`, **behind the Deployment contract, not the Credential Broker** | Docs + inspect: `qma/daemon/proxy/opencodex.py`, `auth_mode: none`, loopback only. |
| Proxy’s own provider credentials stay **outside QMA** | DEC-0344, DEC-0371. QMA must not read `~/.opencodex` plaintext. |
| Unauthenticated loopback allowed by default | `registry:proxy.allow_unauthenticated_loopback` default true. |
| QMA never pools accounts; records true deployment on the routing decision | Docs; harness tests assert chain `ModelClass → Deployment → OpenCodex`. |

2026-08-28 OpenCodex study (QMA sitting research, not this UI sitting): operator machine had `ocx`/`opencodex` on PATH, proxy on **`127.0.0.1:10100`**, combos, account pool, plaintext `~/.opencodex`. That study recommended OCX **behind** the Deployment contract as the first implementation for OAuth/subscription-pool providers, and rejected making `~/.opencodex/config.json` the QMX registry.

### What inspect code actually does (honesty)

| Observation | Implication |
|---|---|
| `OpenCodexDeployment.call` refuses any `resolved_secret`, then either calls an injected `_handler` or returns the string `opencodex:{id}:{prompt}`. **No HTTP client to the proxy.** | Types/tests, not a live proxy session. First-run “detect OpenCodex” cannot use this call as proof. |
| Default bind in `build_opencodex_deployment_record` is `127.0.0.1:3921`, not 10100. | **Unverified** which port a product first-run should probe. Do not hardcode 10100 or 3921 without a recorded Deployment. |
| `websockets` is pinned in **docs** stack (17.1) and **absent** from `qma-wire` / `qma-daemon` pyproject. `DaemonProcess.serve` is `asyncio.start_server` + read-and-discard. | A browser UI cannot “just connect” to a real CT-40 WebSocket on today’s compose entry. Wire **schemas** and `initialize.py` exist as libraries. |
| `authenticate_before_protocol` does not consult the broker. | Auth is a shape gate until the listener is actually composed onto it. |
| `DeploymentBoundary` (Story 45.9) is tested as a module. `DaemonProcess.compose` does not start it. | Workstation/Docker envelope is a default dataclass, not a boot side effect of `__main__`. |

### Unverified (do not freeze as product law)

- That the product **is** OpenCodex / `ocx` / `@bitkyc08/opencodex` (user did not name it; architecture seated it as first implementation).
- That first-run should **install** a proxy.
- That QMX UI should open the proxy’s dashboard or edit its `config.json`.
- That “CLI proxy” means the QMB CLI (it does not: `qmb` is the platform’s single **operator** CLI; the proxy is a **model** plane).
- That API keys entered in QMX should be forwarded to the proxy (forbidden for local-proxy Deployments).
- Live port, auth mode, and whether a clean machine has any proxy.

### **PROPOSAL** first-run behavior for the mentioned proxy

1. Label the card **“Model proxy (local)”**, not a vendor name, until a Deployment record exists.
2. Probe **registered** loopback binds from the daemon catalog; if the catalog is empty, probe is “not configured”, not a failure of the whole app.
3. If a loopback proxy is healthy: copilot can run. QMA still stores **no** provider keys.
4. If the operator wants QMA-owned keys for a **non-proxy** Deployment: Credential Manager write helper under `cred://inference/…` only.
5. Terminal access is a **separate** UX-12 preview (user listed it in the same breath). It is not the model proxy.

---

## Epic 45 workstation deployment (inspect)

Story 45.9 + `qma-daemon/src/qma/daemon/envs/boundary.py` + `qma-core` `DeploymentEnvelope`:

- Default: daemon on **operator workstation**, Docker workers on that host.
- Remote Quant/Mission/Worker: ExecutionEnvironment contract; **remote dials out**; daemon never dials in; no inbound port on the deployed side.
- Trading-node VPS and any host carrying a trading credential or running node: **refused by host identity**. No QMA workload there.
- Computer-use: excluded until a `desktop` env is registered. `GAP_0070_DESKTOP_EXCLUSION.provisioned = "false"`.
- Paper is not a sandbox; QMA mints no promotion command.

First-run and packaging must describe **this** envelope, not a merged “QMX server” that is both QMA and QMN.

---

## Close-window vs stop-work (03 §6) — freeze candidates

| Actor | Close UI window | Stop work | Sleep laptop |
|---|---|---|---|
| QMN (VPS) | No effect (SSH tunnel drops; node continues; evidence reconnects) | Powers channel / drain / stand-down | No effect |
| QMA daemon (workstation) | No effect if not a child of the window (**PROPOSAL C**) | Host “Stop local runtime”; jobs → `unknown` if env dies | Daemon dies; GAP-0062 unnamed; do not promise continuation |
| QMB run | No effect (process-per-run in an env) | `JobHandle.cancel` only | Dies with host/env |
| Copilot conversation | Session durable in daemon; tabs are chrome | Does not cancel the Mission | Reconnect restores product_session, not widget layout |
| Local proxy | No effect | Proxy’s own tool | Independent |
| Preview terminal | PTY dies with the view (**PROPOSAL:** view-owned, not job-owned) | Killing the PTY is not `JobHandle.cancel` | — |

Cancelled display ≠ computation stopped. Not acknowledged / outcome unknown ≠ failed. After reconnect, reconcile then offer retry.

---

## Sources

- `workroom/qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md`, `03-EXPERIENCE-SCOPE.md` (UX-01, UX-11, UX-12, §6)
- `architecture-QMX-2026-09-18/STACK-AND-EVALUATION.md`, `ARCHITECTURE-SPINE.md` AD-15/AD-17/AD-21, `reviews/reconcile-inputs.md` G-11/G-24/G-33/G-34, `inputs/opportunities-journeys.md` J07/J22
- `architecture-QMA-2026-08-28/research/daemon-stack-options.md`, `opencodex-model-proxy.md`
- `docs/architecture/stack.md`, `docs/lenses/ops/runbook.md`, `docs/lenses/ops/incident-playbook.md`, `docs/constitution.md` L33/L34, `docs/gap-report.md` GAP-0058/0062/0070/0078, `docs/components/qma-daemon.md`, `docs/components/qmb.md` paper trinity
- Inspect `34c148b`: `qma-daemon` `__main__.py`, `process.py`, `proxy/broker.py`, `proxy/opencodex.py`, `proxy/local_proxy.py`, `envs/boundary.py`, `discovery/listing.py`, `persistence/substrate.py`, `backtest/service.py`; `qma-wire` `listener.py`, `auth.py`, `initialize.py`; `qma-core` `ports/deployment.py`, `barriers/credential_allowlist.py`, `barriers/reachability.py`; `qmf-core` `secret.py`; `qmn/deploy/secrets_provision.py`, `qmn/src/qmn/secrets/store.py`; `qma-ui-contract/STUB.md`
- Epic 45 stories in `_bmad-output/planning-artifacts/epics-QMA-2026-08-29.md` (Story 45.9)
- Terminal reference: `evidence/session/video-reference.md` (LSE clip; not QMX)

---

## Sitting questions (only if evidence cannot default)

The defaults above are **PROPOSAL**. Ask the operator only if a default is unacceptable:

1. Keep local runtime running after the window closes? **Default yes.**
2. Name OpenCodex as the first-run proxy, or keep the card vendor-neutral until a Deployment is recorded? **Default vendor-neutral, architecture still uses OpenCodex as first adapter.**
3. GAP-0062 always-on host: leave unnamed (current law) or require an operator-named machine before promising unattended local work? **Default leave unnamed; splash must not promise lid-closed continuation.**
