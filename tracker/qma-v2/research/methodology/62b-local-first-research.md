# 62b. Local first: where QMX keeps its data, and how it survives

Written 2026-10-26 by the local-first research agent, against rulings 140-143 (local first in every system; data independent of the app; PC setup before server; no messy files) and rulings 136-139 (the PC is home, servers stand in or add capacity). Primary sources only. Every source used is saved under `../sources/local-first/` with its URL and fetch date; citations below name the saved file. No code was changed.

## Plain words first

- **The idea has a name and a rulebook.** Ink & Switch call it local-first software: the copy on your own machine is the main copy, and servers hold extra copies to help. Servers still have jobs (backup, a bridge to outside services, extra computing power) but they are never the source of truth. That is exactly rulings 136-139.
- **Keep your data in one visible folder of your own, not inside the program's folders.** Microsoft says app data dies with the app and must not hold anything the user values. Firefox, Zotero, Obsidian and Anki all keep the user's data in a folder of its own, and some let you choose where it goes. Uninstalling the program leaves that folder alone.
- **A real trap on Windows.** Common Windows installers (Squirrel, Velopack) install the program into `%LOCALAPPDATA%\<name>` and delete that whole folder on uninstall. Today QMX already writes its daemon data to `%LOCALAPPDATA%\QMX\qma-daemon`. If QMX ever ships with such an installer under the name `QMX`, an uninstall would delete that data. The QMX home must sit elsewhere.
- **Put a label on the folder.** A small file at the top of the folder says "this is a QMX home, format N". A newer QMX upgrades the folder forward after taking a backup. An older QMX that finds a newer format refuses by name and tells you which version you need. It never guesses. Firefox, Anki and Zotero all work this way.
- **Formats that last:** SQLite (its makers plan to support it until 2050, and the US Library of Congress lists it as a preferred format), Parquet, JSON, Markdown and plain folders.
- **The app backs itself up.** Anki and Zotero make automatic backups and thin out the old ones. They also take a backup before an upgrade. Both say that a backup on the same disk is not enough, and Obsidian says that syncing is not a backup. QMX should keep a quick-undo copy in its home folder and a second copy on another drive you choose.
- **Both services run on your PC.** OpenObserve publishes a Windows build (a 167 MiB zip) that runs as one program with a small SQLite database and local disk. Hindsight officially supports Windows with its embedded Postgres (pg0). Neither needs a server or Docker.

## 1. Local-first principles (Ink & Switch, 2019)

Source: `inkandswitch-local-first.md` (Kleppmann, Wiggins, van Hardenberg, McGranaghan, https://www.inkandswitch.com/essay/local-first/).

**Core move.** In cloud apps the server copy is authoritative and the client is a cache. Local-first apps "swap these roles: we treat the copy of the data on your local device ... as the primary copy. Servers still exist, but they hold secondary copies" (section "Seven ideals").

**The seven ideals and what each means for QMX (one user, one strong PC, optional servers):**

| # | Ideal (essay wording) | Applies to QMX? | What it means here |
|---|---|---|---|
| 1 | No spinners: your work at your fingertips | Yes | Library, catalog, Parquet prices and memory are read from local disk; servers never sit on the read path. |
| 2 | Your work is not trapped on one device | Partly | His devices are the PC and stand-in servers. The home folder copies one way to a server or bucket (backup, stand-in), not as a live multi-master. |
| 3 | The network is optional | Yes, except the jobs that need the network by nature | Research, backtests, the Library and memory all work offline. Broker sessions, market data downloads and LLM API calls need a network by definition. |
| 4 | Seamless collaboration | Mostly no | There is one operator. The parts that do apply are proposals and review, which the essay names as a workflow ("suggest changes", pull requests). Agents' proposed changes can follow that shape. |
| 5 | The Long Now | Yes, and central | "Your work should continue to be accessible indefinitely, even after the company that produced the software is gone." The essay cites the Library of Congress recommending "XML, JSON, or SQLite" for datasets. The practitioner advice: make sure you can "easily export to flattened, standard formats like JSON". |
| 6 | Security and privacy by default | Yes | Keys stay in the OS keyring. Servers that hold copies "only hold encrypted data" in the ideal; at least they hold copies, not the master. |
| 7 | You retain ultimate ownership and control | Yes | "With data ownership comes responsibility: maintaining backups." Practitioner test: "Can users easily back up, duplicate, or delete some or all of their documents within your application?" |

**Sync models.** The essay's findings section is the one QMX needs. Under "Cloud servers still have their place for discovery, backup, and burst compute": servers act "not as central authorities, but as 'cloud peers' that support client applications without being on the critical path". It lists three roles: "an archival/backup location", "a bridge to traditional server APIs (such as weather forecasts or a stock tickers)", and "a provider of burst computing resources". And: "The key difference ... is not an absence of servers, but a change in their responsibilities: they are in a supporting role, not the source of truth." CRDTs are the essay's tool for multi-writer merging; a single-writer QMX does not need them. Content-addressed objects are immutable and copy one way without conflicts. Only refs (the mutable pointers) need a single writer, and the PC is that writer.

## 2. Where data goes on each OS, and what an uninstall removes

### Windows

- **Known folders** (`ms-knownfolderid.md`): `FOLDERID_RoamingAppData` = `%APPDATA%` (`%USERPROFILE%\AppData\Roaming`); `FOLDERID_LocalAppData` = `%LOCALAPPDATA%`; `FOLDERID_UserProgramFiles` = `%LOCALAPPDATA%\Programs` (per-user program installs).
- **Microsoft's own rule** (`ms-store-and-retrieve-app-data.md`): "The lifetime of the app data is tied to the lifetime of the app. If the app is removed, all of the app data will be lost ... Don't use app data to store user data or anything that users might perceive as valuable and irreplaceable." User data is data "the user wants to manipulate or transmit as an entity independent of the app itself". The same page says roaming app data is "no longer supported as of Windows 11". The page also describes a version number for app data: "if the version is less than the version the app expects, the app should update the app data to the new format and update the version."
- **MSIX** (`ms-msix-packaged-desktop-apps.md`, `ms-msix-flexible-virtualization.md`): for virtualized packaged apps, new files under `AppData\Local` and `AppData\Roaming` are redirected to a per-package location, and "when a package is uninstalled ... any redirected writes to AppData or the registry" are removed. "Writes to files and folders that aren't part of the package are ... allowed as long as the user has permission." Microsoft's own example of data that must outlive an uninstall: "games write save data to AppData, and that data needs to persist even after the game is uninstalled" (that is why the `unvirtualizedResources` opt-out exists).
- **MSI** (`ms-msi-removefile-table.md`): Windows Installer removes the components it installed, plus any files the package's `RemoveFile` table lists (wildcards allowed, with an "on remove" mode). Files the app creates at runtime survive unless the installer author lists them there.
- **Squirrel / Velopack** (`squirrel-install-process.md`, `velopack-uninstalling.md`, `velopack-windows.md`): both install per user into `%LocalAppData%\<packId>`. Velopack's uninstaller "Removes the entire install directory — the whole `%LocalAppData%\{packId}` folder ... anything you stored inside it — including settings or logs next to your binary — is lost." "Anything stored **outside** the install directory survives an uninstall — for example settings in `%AppData%\{packId}` ... or files under `~/Library/Application Support` on macOS or in the user's home directory on Linux." Updates replace the whole `current` folder.
- **winget** (`ms-winget-uninstall.md`): `winget uninstall` runs the package's own uninstaller. For portable packages, `--purge` "Deletes all files and directories in the package directory" and `--preserve` "Retains all files".

### Linux (XDG Base Directory spec v0.8, `xdg-basedir-spec.md`)

`$XDG_DATA_HOME` (default `~/.local/share`) holds user data files. `$XDG_CONFIG_HOME` (`~/.config`) holds configuration. `$XDG_STATE_HOME` (`~/.local/state`) holds "state data that should persist between (application) restarts, but that is not important or portable enough to the user that it should be stored in `$XDG_DATA_HOME`": logs, history, layout, open files. `$XDG_CACHE_HOME` (`~/.cache`) holds "non-essential (cached) data". `$XDG_RUNTIME_DIR` holds sockets and pipes, and its files "MUST not survive reboot". Package managers remove the files they installed. Per Velopack, files in the home directory survive.

### macOS (`apple-file-system-overview.md`)

- `~/Library/Application Support/<bundle id or company>` is for "all app data files except those associated with the user's documents".
- `~/Library/Caches` is for files "your app can re-create easily".
- Apps "must not write files to" Documents, Desktop or the other user folders "unless explicitly directed to do so by the user". If QMX offers `~/QMX` or a Documents path, it must come from a setup choice the user makes.
- Uninstalling means dragging the `.app` to the Trash, which removes only the bundle (`velopack-uninstalling.md`, `vscode-uninstall.md`).

### Survival table

| Location | MSI | Squirrel/Velopack | MSIX (virtualized) | macOS trash / Linux pkg |
|---|---|---|---|---|
| Install folder | removed | removed | removed | removed |
| `%LOCALAPPDATA%\<same name as packId>` | survives (unless RemoveFile) | **removed** | redirected, removed | n/a |
| `%APPDATA%\<name>` | survives | survives | redirected, removed | n/a |
| A user folder outside AppData (`%USERPROFILE%\QMX`, `D:\QMX`) | survives | survives | survives (write outside package) | survives |
| `~/Library/...`, `~/.local/...`, `~/QMX` | n/a | n/a | n/a | survives |

### Recommendation: the QMX home and its neighbours

| Kind | Windows | Linux | macOS | Holds |
|---|---|---|---|---|
| **QMX home** (data, chosen in setup, default offered) | `%USERPROFILE%\QMX`, or any folder he picks such as `D:\QMX` | `~/QMX`, or `$XDG_DATA_HOME/qmx` if he prefers it hidden | `~/QMX` (user-chosen) or `~/Library/Application Support/QMX` | Everything that matters: Library objects, blobs and refs; the SQLite catalog; price Parquet; the memory database directory; the workflow ledger; units; `settings.toml`; `backups/`; the manifest |
| **Pointer** (config: where the home is) | `%APPDATA%\QMX\home.toml` | `$XDG_CONFIG_HOME/qmx/home.toml` | `~/Library/Application Support/QMX/home.toml` | One path and a list of recent homes (the way Obsidian's global folder lists vaults) |
| **Machine state** (rebuildable, not backed up) | `%LOCALAPPDATA%\QMX-state\...` (never the same name as the installer's packId) | `$XDG_STATE_HOME/qmx` | `~/Library/Logs/QMX`, `~/Library/Application Support/QMX/state` | Window layout, local logs, OpenObserve's working data, pg0's unpacked binaries, PIDs |
| **Cache** (deletable anytime) | `%LOCALAPPDATA%\QMX-cache` | `$XDG_CACHE_HOME/qmx` | `~/Library/Caches/QMX` | Search indexes, thumbnails, downloaded wheels |
| **Runtime** | named pipes | `$XDG_RUNTIME_DIR/qmx` | temp dir | Sockets |
| **Secrets** | Windows Credential Manager | Secret Service, or the locked file from study 61 | Keychain | Keys. The home stores only key names. |
| **Program** | `%LOCALAPPDATA%\Programs\QMX` or a Velopack packId such as `QMX.App` | package or AppImage | `/Applications/QMX.app` | Code only, so deleting it loses nothing |

Rule of thumb: if losing it would cost him work, it goes in the home. If QMX can rebuild it, it goes in state or cache. If it says where the home is, it is config.

**Today's code differs.** `qmx_control/server.py:256` and `qmx_broker/server.py:73` default to `~/.qmx`. `qma/daemon/host_control/root.py:35-57` uses `%LOCALAPPDATA%\QMX\qma-daemon` (Linux `$XDG_STATE_HOME/qmx/qma-daemon`), which is the folder name an installer would claim. Hindsight's pg0 instance is at `C:\Users\Mubarak\.pg0\instances\hindsight`, outside any QMX folder (file 53).

## 3. How well-known apps separate data and survive reinstall

| App | Where the data lives | Chooser | Survives uninstall | Source |
|---|---|---|---|---|
| Firefox | Profile in `%APPDATA%\Mozilla\Firefox\Profiles\` | Profile Manager, `-profile` | "you can uninstall Firefox without losing your personal information" | `firefox-profiles.md` |
| Chrome/Chromium | User Data Dir in `%LOCALAPPDATA%\Google\Chrome\User Data` | `--user-data-dir` | separate folder | `chromium-user-data-dir.md` |
| VS Code | `%APPDATA%\Code` plus `~/.vscode`; portable mode keeps a `data` folder next to the program | `--user-data-dir`, portable `data` | yes; a "clean uninstall" means deleting those folders by hand; portable `data` "can be moved to other ... installations" to upgrade | `vscode-uninstall.md`, `vscode-portable-mode.md` |
| Obsidian | The vault is "a folder on your local file system" of Markdown files; per-vault settings live in `.obsidian/`; global settings in `%APPDATA%\Obsidian` | Pick any folder | yes; "you can use other text editors" | `obsidian-how-obsidian-stores-data.md` |
| Logseq | A graph is created "by connecting Logseq with an existing folder"; graph config in `logseq/config.edn`; global config in `~/.logseq/config` | Pick a folder | yes | `logseq-*.md` |
| Zotero | `C:\Users\<user>\Zotero` (a visible home folder, not AppData); `zotero.sqlite` plus `storage/` | "Data Directory Location" in Advanced settings | yes | `zotero-data-directory.md` |
| Anki | `%APPDATA%\Anki2`; program in `%LOCALAPPDATA%\Programs\Anki`; removing `AnkiProgramFiles` makes the launcher "behave like a fresh install" without touching data | `-b` flag or `ANKI_BASE` | yes | `anki-files.md` |
| Steam games | Save files under AppData etc.; Auto-Cloud copies named roots up after each session and down at launch | Developer-defined roots | yes; cloud restores on a new PC | `steam-cloud.md` |

**Repeating patterns:**
1. **One data folder separate from the program,** often user-chosen (Zotero, Obsidian, Logseq, Anki `-b`, Chrome `--user-data-dir`, VS Code portable).
2. **Small global config that points at the data** (Obsidian's global folder, Logseq's `~/.logseq`, Firefox's `profiles.ini`).
3. **Version marker plus migration on open.** Zotero updates the database on a major upgrade and keeps `zotero.sqlite.[num].bak`. Firefox writes `compatibility.ini` and refuses older versions. Anki has an explicit "Downgrade" step.
4. **Automatic local backups with thinning** (Anki, Zotero, Obsidian File recovery, Firefox `bookmarkbackups`).
5. **Rebuildable indexes are kept out of backups** (Zotero `fulltext.sqlite` "can be recreated"; Obsidian's metadata cache can be rebuilt).
6. **Export to open formats.** Anki `.colpkg`. Zotero warns that export is not a backup.
7. **Do not live-sync the live folder.** Anki: "We do not recommend you sync your Anki folder directly". Obsidian: do not keep the vault inside the backup service.

## 4. Versioning so newer and older QMX can share one folder

- **Manifest at the root** (`qmx-home.toml`): `format = "qmx-home"`, `format_version = "MAJOR.MINOR"`, `created_by`, `last_written_by` (app version), and one version per store (catalog schema, Parquet layout, memory schema, ledger). This is the Firefox `compatibility.ini` idea, made explicit.
- **SQLite files** set `PRAGMA application_id` so tools can recognise the file and `PRAGMA user_version` for the schema number. SQLite "makes no use of the user-version itself" (`sqlite-pragma.md`).
- **Rule on open:**
  1. Same major and same or lower minor: open normally. An older app ignores unknown optional fields and folders. Parquet works the same way: "Additional page types can be added and safely skipped" (`parquet-format-readme.md`).
  2. Lower major: back up first (Zotero's upgrade backup), then run forward-only migrations one step at a time, each in a transaction, then bump the version.
  3. Higher major: refuse by name. Example: "This QMX home was written by QMX 4.1 (format 5). This QMX reads format 4 or older. Install 4.1 or newer." Offer read-only browsing at most. Firefox warns that "using an older version of Firefox can corrupt profile data" and has an explicit override (`--allow-downgrade`), and Anki requires a deliberate "Downgrade your collection" (`firefox-dedicated-profiles-downgrade.md`, `anki-profiles.md`). QMX should have no silent downgrade path.
- **Durable formats:**
  - SQLite: "we plan as if we will be supporting SQLite until 2050", and "Database files created today will be readable and writable by future versions of SQLite decades in the future" (`sqlite-long-term-support.md`). The Library of Congress lists SQLite as a preferred dataset format (`loc-rfs-datasets.md`, `loc-sqlite-fdd.md`).
  - Parquet: an open Apache spec with a "PAR1" magic number, self-describing footer metadata and a file version (`parquet-format-readme.md`). The LoC list does not name it. Its durability comes from the open spec and wide tool support.
  - JSON, Markdown and CSV are character-based formats, which the LoC prefers.
  - Plain folders with hash-named blob files need no software to read.

## 5. Local backups done by the app

- **Anki** (`anki-backups.md`): automatic backups every 30 minutes by default. It forces one before risky operations (a one-way sync download, a `.colpkg` import, Check Database). "After backups are two days old, Anki will start removing some of the older ones", and the number of daily, weekly and monthly backups to keep is set in preferences. Restoring is done from the profile window ("Open Backup"), and "Anki disables automatic syncing and backups when you restore" until restart. Backups "will not protect you if your device breaks or is stolen".
- **Zotero** (`zotero-data-directory.md`): `zotero.sqlite.bak` is taken at most once a day, an upgrade backup is taken before a major-version database change, and `fulltext.sqlite` is excluded as rebuildable. The advice is to copy the whole data directory "preferably on another storage device" and to keep incremental history. Syncing "is not a complete substitute for a proper backup".
- **Obsidian** (`obsidian-back-up-your-files.md`, `obsidian-file-recovery.md`): "Syncing is not a backup." File recovery snapshots are taken at least 5 minutes apart and kept 7 days. They are stored outside the vault, "to account for vault-related data loss".
- **How to copy a live SQLite file:** `VACUUM INTO` writes a compact copy of a live database ("an alternative to the backup API"), and the online backup API copies incrementally (`sqlite-vacuum-into.md`, `sqlite-online-backup.md`).

**QMX backup rule:**
1. Take automatic snapshots of the irreplaceable stores (the catalog via `VACUUM INTO`, the ledger, refs, settings, and a memory dump). Copy blobs incrementally: they are content-addressed and never change, so only new hashes are copied.
2. Thin the history the way Anki does: everything for 2 days, then keep N daily, weekly and monthly copies.
3. Always take a snapshot before a migration, an import, a restore or a version change.
4. Write to two places: `home/backups/` for quick undo, and a second drive he picks during setup. Warn him while no second drive is set.
5. Restore from the launcher even when the home will not open. Server copying stays paused after a restore until he confirms, so a server copy cannot overwrite the restore.
6. Leave caches and indexes out of backups.

## 6. Running the DevOps and memory pieces on the PC

- **OpenObserve.** The docs' Windows tab says to download the binary and run `openobserve.exe` with `ZO_ROOT_USER_EMAIL` and `ZO_ROOT_USER_PASSWORD` set; they ask for an Administrator prompt (`openobserve-getting-started.md`). v1.1.2 ships `openobserve-ee-v1.1.2-windows-amd64.zip` (Enterprise build, 174,741,772 bytes; no published checksum) (`openobserve-downloads.md`). "Single-node mode with SQLite and local disk is the default way to run OpenObserve" (`openobserve-architecture.md`). No minimum RAM is documented. Defaults to override on a desktop (`openobserve-environment-variables.md`):
  - `ZO_DATA_DIR` defaults to the current directory's `./data` (this would scatter files);
  - `ZO_MEM_TABLE_MAX_SIZE` defaults to 50 % of RAM;
  - `ZO_DISK_CACHE_MAX_SIZE` defaults to 50 % of free disk;
  - retention defaults to 10 years;
  - `ZO_TELEMETRY` is on;
  - set `ZO_HTTP_ADDR=127.0.0.1`.
- **OpenTelemetry Collector.** Windows releases come as an MSI, which installs a Windows service, or as a `.tar.gz` holding a plain executable (`otel-collector-install-windows.md`). For a no-admin, tidy setup, QMX should run the tarball's executable itself.
- **Hindsight.** Windows is "Fully supported" with Docker, pip, or the embedded pg0 database. "Hindsight works on Windows with the embedded database (pg0) out of the box" (`hindsight-installation.md`). pg0 is "convenient for development but **not recommended for production**". RAM for the full API: minimum 1.5 GB, recommended 2 GB; Postgres: minimum 512 MB, recommended 1 GB or more. pg0 bundles PostgreSQL 18 and pgvector 0.8.5 and ships `pg0-windows-x86_64.exe` (`pg0-readme.md`). Its data defaults to `~/.pg0/instances/<name>/data`. pg0 accepts `--data-dir`, and its Python SDK accepts `data_dir` (`pg0-python-sdk-source.md`). Hindsight's own wrapper passes only name, user, password, database and port (`hindsight-pg0-wrapper-source.md`). **So to keep memory inside the QMX home, QMX starts pg0 itself with `data_dir=<home>/memory/pg` and gives Hindsight `HINDSIGHT_API_DATABASE_URL=postgresql://...`.** Back up the memory database with a dump, or stop the instance before copying it; whether pg0 bundles `pg_dump` is not verified. The SQLite FTS5 fallback covers a PC where pg0 will not start.

## 7. "Run here or there" in plain terms

- **Docker contexts** (`docker-contexts.md`): a named target holds the endpoint and TLS details. `docker context use` sets the default, and `--context` or `DOCKER_CONTEXT` overrides it for one command.
- **VS Code Remote** (`vscode-remote-overview.md`): opens the same workspace on SSH, WSL, a container or a tunnel. It installs a VS Code Server on the remote side, so "everything feels as it does when you run locally".
- **Jupyter in VS Code** (`vscode-jupyter-kernel-management.md`): a kernel picker on each notebook, with local kernels plus "Existing Jupyter Server" by URL.
- **Ollama** (`ollama-faq.md`): one API either way. The server binds `127.0.0.1:11434` by default, and `OLLAMA_HOST` chooses the address.

**For QMX:** "This PC" is the default target. Each server is a named target. A "Run on" choice appears on each job, with a remembered default. The ledger records where each job ran. Local services bind to loopback.

## Open points

- Whether pg0 bundles `pg_dump` (affects the memory backup step).
- Measured RAM for OpenObserve single-node on the PC (still unmeasured, carried from file 53).
- The installer choice (Velopack or MSI) decides the packId; it must not be `QMX` while anything lives in `%LOCALAPPDATA%\QMX`.
