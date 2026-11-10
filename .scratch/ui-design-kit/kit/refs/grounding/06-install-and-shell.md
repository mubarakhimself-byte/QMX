# 06: Install, first start, handover and the desktop shell

Grounding for the release UI, read through an installation lens. Read-only.

- Code: `D:/QMX-worktrees/engine-base-read` at `3ae41ffc` (= `origin/engine/base`). Paths below are relative to it unless named.
- Short names: `HOST/` = `qmx-agents/packages/qmx-host/src/qmx_host/`, `SRV` = `qmx-agents/packages/qmx-control/src/qmx_control/server.py`.
- Notes read: `tracker/release-inventory/SHIPPED.md` §1-2 and `JOURNEYS.md` (J1, loose strings, backup, sync), memory `installer-lessons-first-start-2026-11-09`, `release-roadmap-2026-11-09`, `ui-notes-held-for-ui-session`, `D:/QMX-worktrees/unit-plan/tracker/qma-v2/UI-HANDOFF.md` §19, §23, §26, and the wizard he ran on 11-09 (`D:/QMX-worktrees/first-start/wizard.sh`, `start-host.ps1`).
- Complements `01-backend-wiring-map.md` (route map). This file covers getting from nothing to a running, wired app.

---

## 1. What exists today, step by step

### 1.1 The bottom line

QMX has no Windows installer, no desktop shell, no updater and no auto-start. The host also does not serve the UI. The only path that has ever run on his PC is a source checkout plus `uv`, driven by a terminal wizard. The older release bundle in `release/` targets the October-era daemon and would not run the current host from an installed environment.

| Piece | Exists? | Where |
|---|---|---|
| Host program with exit codes meant for a desktop app | Yes | `HOST/__main__.py:1-48` |
| First-start card (backend + routes) | Yes | `HOST/first_start.py:1432-1900` |
| Handover card -> host | Yes (contract only) | `HOST/__main__.py:349-363`, `HOST/first_start.py:1711-1742` |
| Something that chains card -> handover -> `serve` | **No** | the docstring says "the desktop app ... then starts the host" (`HOST/first_start.py:22-25`) |
| Desktop shell (Tauri, Electron, pywebview, WebView2) | **No** | no match in code (also `SHIPPED.md:12,37`) |
| Windows installer (Inno, NSIS, MSI, MSIX, winget, PyInstaller) | **No** | no match in code |
| Host serving the built UI | **No** | no `StaticFiles` mount anywhere in the host or control packages |
| Release bundle builder + installer | Yes, stale | `tools/build_release.py`, `release/install.py`, `release/launcher.py` |
| Auto-start, updater, tray | **No** | no match in code; duties only in plan AD-48 |
| "Getting started" list | **No backend** | `JOURNEYS.md:30,171` |

### 1.2 Path A: the release bundle (old era, does not fit the new host)

1. **Build.** `python3.14 tools/build_release.py <dest>` refuses a dirty tree, makes a detached worktree, runs `uv build --all-packages` for the root and `qmx-agents` workspaces, and exports both locks into `requirements.lock` (`tools/build_release.py:182-252`). It builds the UI with pinned Node 22.12.0 and pnpm 10.18.3 into `ui.tar.gz` (`:70-93`). It also archives `qmn/deploy` and copies `launcher.py`, `install.py` and `README.md`. An optional offline wheel closure is **Linux x86_64 only** (`release/README.md:22-36`).
2. **Install.** `py -3.14 <bundle>/install.py <new dest>` needs CPython 3.14 (`release/install.py:392`) and a new destination (`:394`). It verifies checksums, wheels, the lock and the UI archive, creates `<dest>/venv`, and runs pip with `--require-hashes`, then `--no-deps` for the product wheels, then `pip check` (`:438-450`). It extracts the UI to `<dest>/ui` (`:451-452`), **which nothing serves**, and prints the launcher command (`:463-465`).
3. **Start.** `launcher.py` runs `qmb host start` (`release/launcher.py:22`), which runs `python -m qmx_host start --port ...` (`qmb/src/qmb/doors/cli/host.py:1,46-61`).
4. **Why it would fail today:**
   - The README describes the retired daemon: `operator-config.json`, a `qma-daemon` data root and a pairing listener on port 8765 (`release/README.md:79-101`, `release/UI_INTERFACE.md:16`).
   - Runtime code finds its resources by walking up from its own source file, so it assumes a checkout. Inside a venv's `site-packages` these paths point at nothing:
     - first-party apps (`HOST/first_start.py:603-606`, `HOST/connect_node.py:95`)
     - the plugin folder (`qmx-agents/packages/qma-harness/src/qma/harness/home.py:82`)
     - plugin skills and extensions (`qmx-agents/packages/qmx-engine/src/qmx_engine/triggers/preflight.py:68,73`)
     - catalogue seeds (`HOST/first_start.py:173,176`)
     - the repo root (`qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py:78`)
     - the server unit file (`qmx-agents/packages/qmx-control/src/qmx_control/node.py:501`)
   - Installing a mini app runs `uv sync --project <app source> --locked`. That needs `uv` on PATH and the app's path sources on disk (`qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py:505-508,532-536,172-189`). A new folder enables QMB and the MIS at once (`HOST/first_start.py:599,608`), so a host without `uv` and the source tree cannot finish a first start.
   - `SHIPPED.md:36` agrees: "Not checked against the new host". Native Windows is "NOT RUN" (`release/README.md:59,73-75`).

### 1.3 Path B: what he actually ran on 2026-11-09 (the only proven path)

From `D:/QMX-worktrees/first-start/wizard.sh` (stages 1-6) and `start-host.ps1`:

1. `git worktree add --detach D:/QMX-worktrees/engine-live origin/engine/base`.
2. `uv sync --frozen` at the root, then `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`. Takes minutes; the wizard sets `UV_CACHE_DIR=D:\Caches\uv`.
3. He typed a data-folder path (an empty folder, or one holding `qmx-home.toml`).
4. He opened his cTrader Open API app page by hand and checked that the redirect `http://127.0.0.1:47613/ctrader/callback` was set.
5. A **second PowerShell window** ran `uv run --no-sync python -m qmx_host serve --home <folder> --port 8766 [--create]`, and he had to leave it open. He missed this step once (installer lesson 4).
6. `uv run python tools/first_real_start.py --home <folder> [--account N]` set up the node, asked for the secret through `getpass` with no echo (`tools/first_real_start.py:678`), opened cTrader's consent page, made one demo trade, and printed PASS or FAIL lines. With two demo accounts it stopped with "name one demo account with --account" (`:348-352,383-385`), and the wizard re-asked and reran.

The wizard skipped the first-start card. `serve --create` made the folder directly (`HOST/__main__.py:119`).

### 1.4 The designed flow: download to running app, with file:line

This is the contract the backend already honours. The **shell steps** are the missing pieces.

| # | Step | Who | Backend fact |
|---|---|---|---|
| 0 | Prerequisites | installer (missing) | Python `>=3.14,<3.15` (`qmx-agents/packages/qmx-host/pyproject.toml`), `uv` on PATH at runtime (supervisor `:505-508`), git (only for checkout installs), Docker (Linux apps only), rclone (only for rclone storage) |
| 1 | Is a first start due? | shell (missing) | `serve`/`start`/`status`/`stop` exit **3** when no folder, only old data, or an unfinished bring-in or restore (`HOST/__main__.py:38-43,118-139`). The folder is found by `--home`, `QMX_HOME`, the pointer `%APPDATA%\QMX\home.toml`, the default, then each fixed drive's `QMX\qmx-home.toml` (UI-HANDOFF §19.14) |
| 2 | Start the card | shell (missing) | `python -m qmx_host first-start --serve --port 8766 --ui-origin <origin>` binds `127.0.0.1:<port>` before serving (exit **4** if taken, `HOST/__main__.py:453-466`), prints the offer as text (`:344`) and serves the card app (`HOST/first_start.py:1880-1900`): **no bearer**, CORS for one origin, GET/POST/PUT |
| 3 | He picks a choice | UI | `GET /api/first-start` returns the offer (`HOST/first_start.py:1493-1509`, `offer()` `:422-499`). `new`/`open` answer at once (`:1511-1520`). `bring-in`, `restore`, `connect` (restore from his storage) and `keep` are 202 jobs read by id, one at a time (`:1536-1665`, `_one_job` `:1871-1877`) |
| 3a | A new folder | backend | `make_new` checks the folder against the "never" places, writes the pointer and `first-party.json` enabling `qmb` and `mis` (`HOST/first_start.py:590-600`) |
| 3b | A key the card waits for | UI | `PUT /api/first-start/keys/{name}` writes only the key named by the waiting `secret` card (`HOST/first_start.py:1667-1686`) |
| 4 | Handover | UI then shell | `POST /api/first-start/handover` returns `{folder, port}`, or 409 while a job runs or before any finished choice (`HOST/first_start.py:1711-1727`). The card exits 0 within 3 s, with `{"handover":{"folder","port"}}` as the last stdout line (`HOST/__main__.py:349-363`, `HANDOVER_GRACE_S=3` `:75`). Exit 1 means it stopped with no handover |
| 5 | Start the host | shell (missing) | `serve --home <folder> --port <port> --ui-origin <origin>` first finishes a staged restore, refuses an old Library or unfinished bring-in, checks each store's version, and copies before an upgrade (`HOST/__main__.py:126-147`). It then takes the folder lock and binds loopback (`HOST/host.py:346`). Exit codes: 0, 1 (already running, bad place), 2 `QMX did not start: <why>`, 3, 4 (`HOST/host.py:330-364`). Or `start` runs `serve` in the background with `CREATE_NO_WINDOW`, logs to `<folder>/logs/host.log` and waits up to 30 s for `/api/health` (`HOST/host.py:2914-2972`, `START_S` `:227`) |
| 6 | The bearer | shell (missing) | `serve` mints the token on first run into Windows Credential Manager `qmx/control-token` / `control-token` (`HOST/host.py:1193`, `SRV:55-74`). Every route, `/api/health` included, needs `Authorization: Bearer <token>` (`SRV:336-361,472`). The host never hands it out. CORS allows one origin with GET/POST/PUT (`SRV:487-503`), and only on the `pc` role (`HOST/host.py:1320`) |
| 7 | Ready | shell + UI | `GET /api/health` returns `{status, pid, read_only:[{store,line}]}` (`SRV:472-477`). First-party apps install into `<folder>/cache/envs/<hash>` with `uv` (`supervisor.py:367,505+`). Dummy unit and dictionary seeds land (`HOST/first_start.py:749-900`) |
| 8 | Keys | UI | `PUT /api/keys/{name}` is write-only and limited to `qmx/` names, refusing names QMX makes or files itself. `GET /api/keys` lists which are set (`HOST/keys.py:1-88`, mounted `HOST/host.py:1581-1588`). This closes UI-HANDOFF §26 gap 3 (cTrader app id and secret) |
| 9 | Trading node on This PC | UI | Connect kind `trading-node-pc` (`HOST/connect_node.py:794-797`). Steps in order: `ctrader-app` (his), `keys`, `clock`, `install`, `signature` (his), `enable`, `sign-in` (his), `round-trip`, `self-test`, `passport`, `row` (`:778-790`). Started with `POST /api/connect/jobs {kind, place, answer}` and read with `GET /api/connect/jobs/{id}`. A job ends `needs: {card, line, fields?, key?, link?, job?}`, and the same POST with his answer resumes it (`HOST/connect.py:1-13,307-331`). Signature: `GET /api/apps/trading-node` then `POST /api/apps/trading-node/sign` (`tools/first_real_start.py:246-257`). Node operations: `POST /api/apps/trading-node/tools/{op}` (`sign_in_begin`, `sign_in_code`, `bind`, `status`; `:204-206,330-398`) |
| 10 | cTrader read sign-in on This PC (no node) | UI | `POST`/`GET /api/venue/ctrader/sign-in`, listening on `127.0.0.1:47613` for 10 min (UI-HANDOFF §23.4) |
| 11 | Next launch | shell (missing) | the same `serve` on the pointer folder. Nothing starts QMX at login, restarts a crashed host or updates it |

**Data vs code.** The QMX folder (`qmx-home.toml` plus `data`, `keys`, `backups`, `cache`, `logs`) holds everything mutable. App envs live under `cache/envs` (`supervisor.py:367`). The card refuses a QMX folder inside the program folder or checkout, Windows app folders, network drives, a drive root, or a live-synced folder (`HOST/first_start.py:12-16`; lines in UI-HANDOFF §19.8). Plan AD-48 says the install tree is immutable and an update replaces only it (`D:/QMX-worktrees/unit-plan/tracker/qma-v2/architecture/workflow-engine/ARCHITECTURE-SPINE.md:376-380`). Installer lesson 5 says "QMX folder" means this data folder, never the code.

---

## 2. What the UI must provide in this flow

The UI states the flow needs, the host route behind each one, and its errors. Refusal shapes differ by router: `{"detail": "<line>"}` for the card, backups and templates; `{"error": {code, message}}` for control routes; `{"detail": {code, message}}` for the cTrader sign-in; FastAPI's 422 for a bad body; 401 for a missing or wrong bearer (UI-HANDOFF §19.15).

| Screen / state | What it shows | Route(s) | Errors and edge states |
|---|---|---|---|
| **Startup card** (AD-48: stages) | Starting, checking the folder, opening stores, starting apps, ready | shell exit codes; `GET /api/first-start` 200 without a bearer means the card is up; `GET /api/health` with the bearer means the host is up | Exit 1: already running (offer "open the running one") or host not ready in 30 s (show the `logs/host.log` path). Exit 2: show the `QMX did not start: …` line and each store line above it, then offer the card's open or restore. Exit 3: go to the first-start card. Exit 4: port taken (another port, or stop the holder). `read_only` in health: a banner, since writes will refuse |
| **First-start card** | `found`, `default` and free space per drive, `old` (bring-in chosen first), `choices` in order, `warning` (removable drive), `second_drive.line` | `GET /api/first-start` | Five card states: fresh with old data, fresh without, `refused` (only open or restore, **never new**), `unfinished` bring-in (bring in again into the same folder), `restore_unfinished`. While a job runs it shows the offer as it stood when the job started, plus `running` and `job` |
| **Folder picker** | Default path, change folder | `POST /api/first-start/new` and `/open` `{folder}` | 409 with a named place line ("`X` is inside `Y`, where a QMX folder never goes…"); warning for a removable drive. **A browser cannot return a filesystem path**: a native picker needs the shell, or the user types a path |
| **Bring-in progress** | Step line, `done` of `total`, bytes, then the report | `POST /api/first-start/bring-in` 202, `GET /api/first-start/jobs/{id}` | Steps per UI-HANDOFF §19.10. `stopped` with one line (a file changed while copied). 409 for one job at a time, or bringing the same old folder in twice |
| **Restore from a folder** | Copy list (date, why, size, machine, partial), what the copy replaces, confirm | `/copies`, `/restore/check`, `/restore` (`confirmed: true` only) | 400 when not confirmed, 409 for another folder's copy without `replace`, "QMX is running on X (PID n)", several `home_id`s in one place. After the restore, the keys-to-fill list |
| **Restore from my storage** | The connect dialog's storage cards, then the copy list | `POST /api/first-start/connect` 202, job read, `POST /jobs/{id}/cancel` | Cards: `fields`, `secret`, `question`, `sign-in` (`link`), `password`, `folder`. A Drive restore stops at the client card |
| **Keep your work** (optional, after "new") | `kept.line` plus storage kinds | `POST /api/first-start/keep` | 409 when the folder was not made new by this card |
| **Secret entry** (any card) | A masked input. He asked for asterisks (lesson 3) | card: `PUT /api/first-start/keys/{name}`; host: `PUT /api/keys/{name}`, `GET /api/keys` | 400 for a name outside `qmx/`, made by QMX, or filed by a probe. 409 when no card waits for that key. Never read back |
| **Handover -> "Starting QMX"** | The chosen folder, then the startup card | `POST /api/first-start/handover`, then health polling with the bearer | 409 while a job runs, before a choice, or after an unfinished bring-in |
| **Trading node on This PC** | One step list with ticks (QMX steps tick themselves; his steps open a card), ending in "Ready" | `GET /api/connect/kinds`, `POST /api/connect/jobs`, `GET /api/connect/jobs/{id}`, `/cancel` | Cards: `ctrader-app` (client id field; secret through the key route to `qmx/node-ctrader-app-secret`), `signature` (sign via `/api/apps/trading-node/sign`), `sign-in` (open cTrader's consent page; redirect `127.0.0.1:47613`). A stuck step shows the step name |
| **Account picker** | Each account: **the number cTrader's app shows (`login`)**, broker, demo or live. Pick one demo account (lessons 1-2) | node `sign_in_code`, then `bind` | Live accounts must not be selectable. The grant is not kept for a live-trading grant (`LIVE_GRANT_MESSAGE`). See gap G8 |
| **cTrader read sign-in** (no node) | Sign in, waiting, ok, refused | `POST`/`GET /api/venue/ctrader/sign-in` | Codes `app_credential_missing`, `sign_in_expired`, `no_pending_sign_in`, `live_trading_grant` and others (UI-HANDOFF §23.4) |
| **Getting started list** | First steps after the folder exists | none | no backend (`JOURNEYS.md:30,171`) |

---

## 3. Gaps blocking an installable release with a UI

| # | Gap | Evidence | Size |
|---|---|---|---|
| G1 | **Nothing runs the flow.** No process starts the card, reads the handover line, starts `serve`, reads the bearer, restarts a crashed host or stops it on exit. AD-48's duties (startup card, restart-loop breaker, keep-awake, start at login, dead-man task) are unbuilt | `HOST/first_start.py:22-25`; spine AD-48 | L |
| G2 | **The UI is not served.** The host mounts no static files. The card app does not either. The release installer extracts `ui/`, which nothing serves | `SRV:487-503`, `release/install.py:451-452` | S (a static mount on host + card) or part of a shell |
| G3 | **Token handoff.** The bearer is header-only (no cookie, no query), and the host never serves it. Browser `EventSource` cannot send headers, so streams must use `fetch()`. The token exists only after the first `serve`. The card has none | `SRV:55-74,336-361`; `HOST/host.py:1193` | S-M |
| G4 | **Packaging assumes a source checkout.** Nine source-relative `parents[N]` lookups in `qmx-agents` (§1.2; more in `qmn`), and mini-app installs need `uv` plus app sources at runtime. A plain venv or frozen exe breaks first start (QMB and the MIS are enabled at once) | §1.2 list; `supervisor.py:505-536` | M (ship a source snapshot + uv) to L (refactor for wheels) |
| G5 | **The release bundle is stale.** Old-era README, launcher through `qmb`, offline closure Linux only, Windows "NOT RUN" | `release/README.md`, `release/launcher.py` | M |
| G6 | **Runtime prerequisites on a clean PC.** Python 3.14 and `uv` must be shipped or installed. `UV_CACHE_DIR` and the temp dir must stay off a nearly full C: (the wizard set D:). WebView2 (present on Win 11) or a bundled browser engine, depending on the shell | `pyproject.toml`; `wizard.sh` | M |
| G7 | **No updates or rollback.** Nothing swaps the install tree. Parts exist: the before-update copy in `serve` (`HOST/__main__.py:146-147,242-314`) and host drain `POST /api/node/drain` (`HOST/host.py:2715-2719`). AD-48 wants the previous release kept for a one-step rollback | spine AD-48 | M |
| G8 | **The account picker lacks the data.** `sign_in_code` lists only `{account, is_live}`, though the grant holds `login` and `broker` (`qmn/src/qmn/app/server.py:491-493` vs `qmn/src/qmn/app/grants.py:176-190`). Lesson 1 needs the app's number, the broker and demo or live | code | XS backend |
| G9 | **Native folder picker.** A web page cannot return a path. Needs a shell dialog or a typed path with the card's checks | browser platform | S with a shell |
| G10 | **Port and origin coupling.** Card and host share one port (8766), and CORS allows exactly one origin given at start. A taken port (exit 4) or a different shell origin (dev `127.0.0.1:5173` vs packaged) means both restart with matching values, and the UI must learn the port from whatever started it | `HOST/__main__.py:99,105`; `SRV:491` | S |
| G11 | **Start-failure text reaches no screen.** The exit-2 line goes to stderr or `logs/host.log`. A shell must capture and show it | `HOST/host.py:2953-2966` | S |
| G12 | **Getting-started list** has no backend | `JOURNEYS.md:171` | S-M |
| G13 | **Card security.** The card has no bearer, so any local process can drive it, including writing the waiting key. It binds loopback and refuses keys no card asks for; low risk, but worth recording | `HOST/first_start.py:1667-1686,1896-1899` | note |
| G14 | **Ruling tension (not decided here).** Rulings 32 and 40 say QMX is a desktop app with never a web version (`research/methodology/26-operator-rulings-and-alignment.md:43,112`). AD-48 says the UI renders in the app's own windows, "never as a web site". The 11-09 roadmap lists "A web version first" after release (memory `release-roadmap-2026-11-09`). The 2026-08-17 accord said "Rust UI later, no Electron" (`tracker/map.md:50`). DEC-0478 / GAP-0112: "Tauri shell optional, installer deferred". AD-48 leaves the framework to a probe that must check: hosts the Svelte UI, supervises Python, always-on-top HUD, global hotkey, Windows auto-start; not MSIX; not package id `QMX`; keeps the previous release (spine `:796`) | rulings | his call |

---

## 4. Options for the desktop shell and serving the UI

Laid out, not decided. Two questions are independent: **(a) what window the UI runs in and who supervises the host**, and **(b) how Python and the code reach his PC**.

### 4a. Shell and serving

**Option 1: built into the host as static files, opened in his normal browser by a small launcher.**
- How: mount the built UI (`adapter-static`, `fallback: 200.html`, already the build output) on the host and on the card app, at the same origin, so CORS is not needed. A launcher (a `.cmd`, a `pythonw` script or a tiny exe) runs card or host and then opens the browser.
- Token: same origin still needs the bearer. Either the launcher opens `http://127.0.0.1:8766/#t=<token>` (a URL fragment is never sent to the server or logged; the page moves it into memory), or the host swaps a one-time code for an HttpOnly cookie (backend change). A cookie also lets plain `EventSource` work.
- Good: the smallest build, no new language, works the same on a Linux server, and it is the road to the "web version first" roadmap item.
- Costs: it is a browser tab. That conflicts with rulings 32/40 and AD-48 ("never as a web site"). There is no native folder picker, no HUD or global hotkey, no tray. Closing the tab does not stop the host. Something still has to supervise restarts and auto-start (G1). On a shared PC another local user could open the same port.

**Option 2: plain browser via a pairing link (the T3 Code style).**
- How: the host (or launcher) prints or opens a URL holding a one-time pairing code. The browser trades it for a session, and further devices can be paired the same way.
- Needs: a pairing route, sessions and revoke, and a bind wider than loopback for other devices. Today the `pc` role binds `127.0.0.1` only (`HOST/host.py:346`). There is a precedent for minted tokens: observer tokens (`HOST/door.py:16-24`), but they are limited to ops reads and cannot be the UI's token.
- Good: the same thing becomes the phone and web path later. No shell to build.
- Costs: everything in Option 1, plus the security work for a token that travels, and a wider attack surface if the bind opens. For a non-technical user, pairing is one more step he must understand. His remote coding tool works this way and he pairs it himself (`HANDOFF-2026-11-10.md:61`).

**Option 3: Tauri 2 (Rust main process, system WebView2).**
- How: the shell starts card or host as a sidecar process and reads `qmx/control-token` from Credential Manager natively. It hands the token and port to the page through an IPC command, so the token is never in a URL. Its page origin is passed as `--ui-origin`; on Windows that is Tauri's own localhost origin, to be checked on the web when probed. It could also load from the host's URL under Option 1's static mount.
- Good: small download for the shell itself (the Python runtime is still separate). Plugins for tray, global shortcut, autostart, updater, single instance and native dialogs (the folder picker). Multiple windows, so a HUD is possible. Installer through its NSIS or MSI bundler. Matches the "Rust later, no Electron" note and DEC-0478's "Tauri optional".
- Costs: a Rust toolchain in the build and a codebase with no Rust today. WebView2 differences from Chrome are small but real. Plugin versions must be verified on the web (AD-48 requires that).

**Option 4: Electron (bundled Chromium, Node main process).**
- How: the main process spawns the host, reads the keyring through a Node keyring library, and passes the token by preload IPC. It loads the UI from a custom protocol or from the host.
- Good: the most mature desktop stack (electron-builder NSIS installer, auto-update, tray, global shortcut, always-on-top). The same Chromium everywhere, and it matches the Playwright tests' engine.
- Costs: a large download (Chromium) and memory use on top of a heavy Python host. The 2026-08-17 accord says "no Electron". Node tooling is in the build already for the UI, so less new than Rust.

**Option 5: pywebview (Python shell on WebView2).**
- How: a separate small Python process (never inside the host, which holds the folder lock and must be restartable). It starts card or host, reads the token with the `keyring` library QMX already uses, and injects token and port through `js_api`. It has a native folder dialog.
- Good: one language for the whole team. The fewest new tools. The shell could share the installer's Python runtime.
- Costs: weaker multi-window and HUD support. Global hotkey, tray and auto-start need extra Python libraries or a Scheduled Task. Packaging through PyInstaller, Nuitka or Briefcase adds its own Windows issues. A smaller community than Tauri or Electron for desktop polish.

Common to every shell option: the shell owns the exit-code branching (§1.4), the handover line, the token, the port and origin pair, capturing stderr, restarts with a breaker, auto-start (or a Scheduled Task) and, later, updates (AD-48).

### 4b. Getting Python and the code onto the PC

| Way | Fits today's runtime? | Notes |
|---|---|---|
| **Source snapshot + bundled `uv`**: install a git-free copy of the tree at the candidate commit, plus `uv.exe`; `uv python install 3.14`; `uv sync --frozen` both workspaces at install time | **Yes**: `parents[N]` lookups and `uv sync --project <app>` keep working | Closest to the proven 11-09 path. A first install needs network for wheels, unless a Windows wheelhouse is shipped (today's offline closure is Linux only). The tree must sit outside the QMX folder (the card refuses that mix) |
| **Embeddable Python + venv + wheels** (the `release/install.py` model) | **No**, not without fixing the `parents[N]` lookups and the app-source paths | Cleaner immutable install tree, which AD-48 wants |
| **Frozen exe (PyInstaller, Nuitka)** | **No**: mini apps install with `uv sync` from source, and the harness launches the Claude CLI | Largest refactor |

Installer wrapper (any of the above): a per-user install under `%LOCALAPPDATA%\Programs\…` avoids admin prompts. Inno Setup, NSIS (also what Tauri and Electron emit) or a WiX MSI can each keep the previous release beside the new one. AD-48 bars a virtualized MSIX and the package id `QMX`. winget can come later as a distribution channel.

---

## 5. Lessons from his first start that bind any choice

From memory `installer-lessons-first-start-2026-11-09` and `ui-notes-held-for-ui-session`:

1. Show cTrader's own account number (`login`), the broker and demo or live, and pick from a list (needs G8).
2. Ask when several demo accounts exist; never stop with a command-line hint.
3. Mask secrets with asterisks.
4. The host starts by itself, with no second window and no pasted command (G1).
5. "QMX folder" is the data folder, never the code. `--create` needs an empty folder.
6. The cTrader app's redirect must be `http://127.0.0.1:47613/ctrader/callback`. Sign-in happens on cTrader's consent page.
7. Remember answers and skip finished steps. The connect dialog already reruns and skips steps whose check passes (`HOST/connect.py:1-13`); the UI keeps that rather than re-asking.
