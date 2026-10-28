# Sync to my account: what the primary sources say

Read on 2026-10-28. Every fact below names the saved copy it comes from, under `sources/`. Each saved copy starts with its URL and the fetch date. Copies are verbatim files from the projects' own repositories where those exist (rclone, restic, borg, kopia, CPython, n8n, Obsidian, VS Code, OpenObserve, OpenTelemetry, Grafana, Prometheus, Docker, Ollama, Hermes, Cloudflare), the documentation JSON for Apple, and text taken from the HTML page for Google, Steam, Tailscale and OpenObserve's pricing. Nothing here comes from memory.

One measurement is my own, not a source: zstd, tar and zip run over QMX's 51 shipped workflow templates (section 3.1). The script used only Python 3.14's standard library on this PC.

Read `01-his-words-2026-10-28.txt` for what he asked and `02-inventory.md` for what QMX has. This file does not repeat either.

---

## The findings that change the design

1. **Every product saves the recipe and fetches the rest again.** Chrome saves an extension as its id, version and update address, not the extension itself. VS Code saves the list of extensions and leaves out settings marked "machine". Steam tells game makers not to sync "machine-specific configurations such as video quality". n8n saves a credential as its id, name and type, never the secret. QMX should do the same: recipes plus pointers, secrets as named stubs, and per-machine settings left out. (1.1 to 1.9)
2. **Nobody quietly merges a whole save.** Steam, VS Code and Google Play Games show both copies and let the person pick. n8n says to edit in one direction only. Only Chrome (one item at a time, the server wins by default) and Obsidian (text notes merged, everything else "last modified wins") merge on their own. QMX's pool, where each file is stored once under its sha256, already cannot conflict. Only the "latest copy" pointer can conflict, so on restore QMX should show the two latest copies with their machine and time, the way Steam does. (1.10)
3. **Pack many small files into one compressed file.** Over QMX's own templates, compressing each file alone gives 2.4 times smaller, zip gives 2.0 times, and one stream over all files gives 5.9 times. Google Drive moves "about 2 files per second", so 700 loose files take about 6 minutes, while one pack takes seconds. restic and kopia both pack, and both keep an index of hash, pack, offset and length. (3.1, 3.3)
4. **Do not build the pool on rclone `union`.** If any member fails to open, the whole union fails to open. If a member fails while listing, its files silently drop out of the list. The "most free space" rule needs a free-space report, which S3 and R2 do not give. Nothing is copied twice unless every write goes to every member. QMX already has "places": it should treat each account as its own place and decide placement itself. (2.1)
5. **rclone's shared Google sign-in stops working during 2026.** rclone says its shared Google Drive client "will stop working during 2026" and that your own client is "now required". So QMX needs its own Google sign-in client. On Google's side, a client left in "Testing" gets sign-ins that expire after 7 days, and the `drive.file` permission does not need Google's review. (2.4)
6. **rclone can already run the step-by-step dialog.** `rclone config create --non-interactive` answers with the next question as JSON (name, help text, default, choices, whether it is a password). QMX shows that question, sends the answer back, and gets the next one. The same works through `rclone rc`, which also reports the Google sign-in address to open in his browser. (2.3)
7. **`bisync` is not needed.** A file stored by its own hash never changes, so `copy` is enough. `sync` deletes files on the far side, so it must not point at the pool. QMX does its own clean-up and re-pack. (2.2)
8. **A full Google account breaks more than backups.** When over quota, he cannot upload to Drive, Gmail "can be impacted", and after 2 years everything in the account "may be removed". QMX must keep a floor of free space on any Google account it writes to. (2.5)
9. **OpenObserve runs on Windows but needs three settings changed.** A Windows build exists: a 150 MB zip for v1.1.2. Out of the box it keeps data 10 years, sends anonymous telemetry, and lets its disk cache grow to 50% of free disk. That last one matters on his nearly full laptop. QMX should set all three. (4.1)
10. **Agents can read OpenObserve through its own MCP server**, and the free edition has one at `/api/{org}/mcp`. The catch: in the free edition every tool runs with full rights, including delete. The self-hosted Enterprise edition is free up to 50 GB a day and adds role-based access, which allows a read-only user for agents. (4.2)
11. **The way to back up the logs layer is OpenObserve's own setting.** A single node can keep its data files in S3-compatible storage instead of on local disk. On several machines, each machine runs an OpenTelemetry Collector with an on-disk queue that sends to one OpenObserve. (4.1, 4.3)
12. **Before an update, take a quick snapshot by default, a full backup on request, then check and roll back.** Hermes does this in that order. If the snapshot fails, the update prints a warning and goes on. It also warns when a restore replaces newer work with older work. Android puts app data back after install and before the first launch. (5.2)

---

## 1. How products make "your stuff follow your account"

### 1.1 Chrome sync

Facts:
- Signed-in Chrome saves bookmarks, reading list, passwords, payment info, addresses, extensions, web apps, settings, and optionally history and tabs. Each kind can be switched on or off. When he signs out, the info "is kept safe in your Google Account and removed from the device". An optional passphrase encrypts it so Google cannot read it. (`sources/chrome-sync-help.md`)
- The full list of synced data types is an enum in Chromium's source: about 70 types, such as BOOKMARKS, PREFERENCES, PASSWORDS, EXTENSIONS, SESSIONS and HISTORY. Cookies are a sync type on ChromeOS only. (`sources/chromium-sync-data-types.md`)
- **What is saved for an extension:** its id, the installed version, its update URL, and whether it is enabled. The extension's code is not saved. It is downloaded again from its update URL. (`sources/chromium-sync-extension-specifics.md`)
- **Conflicts:** sync works one item at a time. "A default implementation chooses the server data unless it is a deletion." Each data type can override that rule. (`sources/chromium-sync-bridge-resolveconflict.md`)
- There are two modes. "Sync-the-feature" merges local and account data. "Sync-the-transport" keeps local and account data strictly separate. (`sources/chromium-components-sync-README.md`)
- **Reinstall:** he signs in, the account data comes down, and extensions are installed again from their update addresses. Cache, downloads and site data are not in the list of types. (`sources/chromium-sync-data-types.md`)

### 1.2 Mobile games: Google Play Games saved games and Android Auto Backup

Facts:
- A Play Games saved game is one binary blob of up to 3 MB, plus metadata (cover image up to 800 KB, description, time played, last change). A game may keep several saves. Google does not charge for this storage. (`sources/play-games-saved-games.md`)
- Conflicts happen when a copy of the game cannot reach the service. Google's advice: load the latest data at start and save often. For Guest accounts, "your game shouldn't automatically overwrite any data" and should "explicitly ask the player to choose". The Android code sample uses the policy `RESOLUTION_POLICY_MOST_RECENTLY_MODIFIED`. (`sources/play-games-saved-games.md`, `sources/play-games-saved-games-android.md`)
- Offline: the game still reads and writes, and Google uploads after the device reconnects. (`sources/play-games-saved-games.md`)
- **Android Auto Backup** is the most likely way a game like DLS comes back after a reinstall. It backs up shared preferences, databases and files, but not the cache or "no backup" folders. The limit is 25 MB per app, stored in a private Drive folder that "does not count toward the user's personal Google Drive quota". Only the latest backup is kept. A backup runs when 24 hours have passed, the device is idle and on Wi-Fi, and "only if the app data has changed". **Restore runs at install, "after the APK is installed but before the app is available to be launched by the user".** (`sources/android-auto-backup.md`)

### 1.3 Apple iCloud key-value store and CloudKit

Facts:
- The key-value store holds settings and small app data: at most 1024 keys and 1 MB in all. It is kept on disk unencrypted, so Apple says to put no secrets in it. Writes go to memory first, then disk, then iCloud. Without an Apple account, changes stay on the device until he signs in, then "reconciles the values there with the local ones". Other devices get a change notice. (`sources/apple-nsubiquitouskeyvaluestore.md`)
- CloudKit stores records (key-value dictionaries) and needs the network. It "provides minimal offline caching support". (`sources/apple-cloudkit.md`)
- **Conflicts in CloudKit:** the server refuses a save when its own copy is newer (`serverRecordChanged`). It hands the app three copies: the client's, the server's and the common ancestor. The app must merge onto the server's copy and save again. (`sources/apple-cloudkit-serverrecordchanged.md`)

### 1.4 Steam Cloud

Facts:
- Files are copied to Steam "after the game exits". With Auto-Cloud, files sync at launch and at exit with no code in the game. Valve says: "Avoid machine-specific configurations such as video quality." Each game sets a byte quota and a file-count quota per user. (`sources/steam-cloud.md`)
- Steam client settings (collections, nicknames, the Settings menu) "are pulled from the cloud upon login". (`sources/steam-cloud-help-faq.md`)
- **Conflicts:** when local files differ from the cloud at launch, Steam shows a window with both copies and their dates, and the player picks. Steam "cannot automatically pick". Offline play "is very likely to cause a conflict". (`sources/steam-cloud-help-faq.md`)
- There is a per-game switch and a global switch. With it off, progress stays on that machine only. Every cloud read and write is logged in `cloud_log.txt`. (`sources/steam-cloud-help-faq.md`)
- **Lost progress after a move:** either the old machine did not finish syncing, or it uploaded an older copy. Steam's advice is to start Steam on the old machine so it syncs. (`sources/steam-cloud-help-faq.md`)

### 1.5 VS Code Settings Sync

Facts:
- It syncs settings, keyboard shortcuts (per operating system by default), snippets, user tasks, MCP servers, UI state, **the extension list** (installed and enabled), profiles (up to 20), and prompt files. Settings with the `machine` or `machine-overridable` scope are not synced, and he can exclude any setting. (`sources/vscode-settings-sync.md`)
- On first sign-in it merges local and cloud data. If it cannot merge, sync "pauses until you resolve the conflicts" with these choices: Accept Local / Replace Remote, Accept Remote / Replace Local, or a side-by-side diff with Complete Merge. (`sources/vscode-settings-sync.md`)
- **Backups:** local backups for 30 days, and the latest 20 versions of each kind in the cloud, all restorable. It keeps a list of synced machines; each can be renamed or switched off remotely. Settings, shortcuts and tasks are limited to 100 KB each. Turning sync off can also clear the cloud copy. (`sources/vscode-settings-sync.md`)

### 1.6 Claude Code, and Claude's account memory

Facts:
- Claude Code reads settings from files: user (`~/.claude/settings.json`), shared project (`.claude/settings.json`, committed to git), local project (`.claude/settings.local.json`, kept out of git), and managed (pushed by an organisation, including from the claude.ai console). (`sources/claude-code-settings.md`)
- CLAUDE.md instructions come at four levels: managed, user, project and local. **Auto memory is "machine-local"**: each repository has a folder `~/.claude/projects/<project>/memory/`, and "files are not shared across machines or cloud environments". Its switch is the setting `autoMemoryEnabled` in user settings. (`sources/claude-code-memory.md`)
- Plugins are named in settings (`enabledPlugins`, `extraKnownMarketplaces`) and fetched from their marketplace. (`sources/claude-code-settings.md`)
- Claude's account memory, which is what he showed, is a switch in Settings > Your Claude ("Memory from chats"). It can also be switched off for one chat before the first message. It is shared between Chat and Cowork in the cloud, but local Cowork sessions do not use it. It can be exported as text. (`sources/claude-ai-memory-help.md`)

So Claude Code itself travels between machines only through git (project files) and managed settings. The account-level memory lives on Anthropic's servers.

### 1.7 Obsidian Sync

Facts:
- Images, audio, video and PDFs sync by default. "Sync all other types" is a switch. Vault configuration sync covers main settings, appearance, themes, hotkeys, and the core plugin list and settings. The community plugin list and the installed community plugins must be switched on by hand. Hidden files are never synced, except `.obsidian`. File-recovery snapshots are never synced. (`sources/obsidian-sync-settings-selective.md`)
- **Conflicts:** Markdown is merged with Google's diff-match-patch. Every other file uses "last modified wins". Settings JSON is merged key by key, local over remote. Since 1.9.7 he can choose "Create conflict file" instead. That choice, the device name and selective sync are set per device. (`sources/obsidian-sync-troubleshoot.md`, `sources/obsidian-sync-settings-selective.md`)
- Plans: 1 GB with a 5 MB file limit, or 10 to 100 GB with 200 MB files. Version history is kept 1 or 12 months. A file added to the excluded list stays in the remote vault. (`sources/obsidian-sync-plans-limits.md`, `sources/obsidian-sync-settings-selective.md`)
- Obsidian advises against running another sync service alongside it: "can lead to conflicts, resulting in duplicate or corrupted files". (`sources/obsidian-sync-faq.md`)

### 1.8 n8n: workflow JSON, export and source control

Facts:
- "n8n saves workflows in JSON format." A workflow can be downloaded, imported from a file or a URL, or copied and pasted as JSON. (`sources/n8n-export-import.md`)
- `n8n export:workflow --backup` writes one pretty JSON file per workflow. Credentials export encrypted, or in plain text with `--decrypted`. **A CLI backup leaves out users, run history, variables, and the instance settings "including the encryption key"**, so it can move workflows but cannot rebuild a whole instance. A full restore needs the `.n8n` folder (SQLite database plus encryption key). Imported workflows start switched off. (`sources/n8n-backup-and-restore.md`, `sources/n8n-cli-commands.md`)
- **Source control commits:** workflows (with tags and owner email), **credential stubs (id, name and type only)**, variable stubs, data table schemas without rows, projects and folders. (`sources/n8n-push-pull.md`)
- **Conflicts:** "n8n can't detect conflicts on workflows." Git is the source of truth. Pull overwrites local and push overwrites Git. The advice: "Design your source control setup so that workflows flow in one direction." When a pulled workflow needs a credential stub that is not there, n8n tells the person to fill in the value. (`sources/n8n-push-pull.md`)
- Licence: n8n's main code is under the Sustainable Use License, a fair-code licence, not open source. (`sources/github-licenses.md`)

### 1.9 OpenCode config

Facts:
- OpenCode is configured by one JSON or JSONC file with a `$schema`. Config files are "merged together, not replaced", in this order: remote organisation default (`.well-known/opencode`), global, the `OPENCODE_CONFIG` file, project, `.opencode` folders, inline, then managed files. Later sources win only on keys that clash. (`sources/opencode-config.md`)
- Plugins are listed by npm package name (`"plugin": [...]`) or placed in a plugins folder. **Secrets are references, not values:** `{env:NAME}` and `{file:~/.secrets/key}`. (`sources/opencode-config.md`)

### 1.10 Hermes agent (backup before update)

Covered in 5.2. In short: before every update it saves a quick snapshot of the state files (config, `.env`, auth, cron jobs, pairing). A full zip is optional, and so is turning it off. `hermes backup` makes a zip of config, skills, sessions and data. The zip leaves out the code, `models/`, `runtimes/`, browser profiles and regenerable cache. (`sources/hermes-docs-updating.md`, `sources/hermes-cli-backup-import-excerpt.md`)

### 1.11 The products side by side

| Product | What is saved | What is fetched or rebuilt | Two machines disagree | Reinstall |
|---|---|---|---|---|
| Chrome | Per-type items: bookmarks, passwords, settings, extension ids and versions | Extension code, from its update URL | One item at a time; the server wins by default | Sign in, data comes down |
| Play Games | Blobs up to 3 MB plus metadata | The game | Game's choice; Google says ask the player | Load the latest save at start |
| Android Auto Backup | App files up to 25 MB, latest only | Cache and no-backup folders | One latest copy | **Restored before first launch** |
| iCloud key-value / CloudKit | Up to 1 MB of keys / records | - | Key-value: reconciled by the system; CloudKit: app merges with 3 copies | Data comes down |
| Steam Cloud | Listed save folders; client settings | Game files | **Window with both copies; the player picks** | Pulled at login and launch |
| VS Code | Settings (minus `machine` scope), keys, snippets, the **extension list** | Extensions, from the Marketplace | Pause; Local / Remote / Diff | Sign in, merge |
| Claude Code | Nothing by itself; project files through git | - | git | Copy `~/.claude` by hand |
| Obsidian Sync | Notes, chosen file types, chosen config | Community plugins only if switched on | Merge Markdown; last-modified for the rest; or a conflict file | Connect the vault |
| n8n | Workflow JSON, credential **stubs**, schemas | Credential values, typed in again; run history not kept | No detection; one direction | Import, then fill in credentials |
| OpenCode | One JSON config, secrets as `{env:}` / `{file:}` | Plugins, from npm | Layered merge by key | Copy the file |
| Hermes | Zip of config, skills, sessions | Code, models, runtimes, browser profiles | Import overwrites, with a warning when older | `hermes import` |

### What fits QMX

- **Save recipes, fetch the rest.** This matches his "save that instead of saving everything verbatim". A mini app should travel as its `app.toml` plus its source hash, and be rebuilt on the new PC like a Chrome extension. A workflow travels as its `definition.json` and scripts. Price series that can be downloaded again travel as a note of what to fetch. This is what 02-inventory section 1 calls "Recipes".
- **Secrets travel as names only.** n8n's stubs and OpenCode's `{env:}` references are the pattern: the copy says "this workflow needs the key named `bybit-main`", and on the new PC the first start asks him to fill it in. That fits his "sign in again" ruling and keeps `keys/` and `vault/` out of every copy.
- **Mark per-machine settings and leave them out.** VS Code's `machine` scope and Steam's "video quality" warning say the same thing. In `settings.toml`, the place list entry for "this PC", disk floors, the telemetry target and GPU choices are per machine.
- **One switch, with a list underneath.** Chrome, VS Code, Steam and Obsidian all have one main switch plus a few per-kind switches. For QMX: "Sync to my account" on or off, then Recipes (always), My content (on), Run results (off by default), Prices I cannot download again (on).
- **When to sync:** on change, at least daily, and before every update. Android's rule fits a desktop well: after 24 hours, when idle, only if something changed. Steam's rule (at start and at exit) fits the "before update" step.
- **Conflicts:** pool files cannot conflict, because a file's name is its own hash. What can conflict is "which copy is the latest". Do what Steam does: on a restore or a first start, show the two newest copies with machine name, time and counts, and let him pick. Never pick quietly. Keep a list of synced machines like VS Code.
- **Restore before first use.** Android restores before the app can open. PR 228's first-start restore is that hook. The account just needs to be one of the places it can restore from.

---

## 2. rclone

### 2.1 union, combine, crypt, compress, chunker, hasher

Facts:
- **union** shows several remotes as one. Members can be tagged `:ro` (read only), `:nc` (no new files) or `:writeback`. Rules come in three groups: action (default `epall`), create (default `epmfs`, "existing path, most free space") and search (default `ff`). `create_policy = all` writes every new file to every member. `min_free_space` (default 1 GiB) only applies to the `lfs`/`eplfs` rules. (`sources/rclone-union.md`)
- **When a member disappears:** at open, `NewFs` returns an error if any member fails to open (other than "is a file"), so the whole union fails. In `List`, an error from one member is kept, and the merged entries of the others are returned unless *every* member failed. So the dead member's files are missing from the list with no error raised. This comes from reading the source; I did not test it. (`sources/rclone-union-go-excerpt.md`)
- **When a member fills up:** the free-space rules need the member to report quota. "Backends without about capability cannot ... use policy `mfs` (most free space) as a member of an rclone union remote." Drive and SFTP report it; the S3 backend, which covers R2, does not. (`sources/rclone-overview.md`, `sources/rclone-about-support-from-source.md`)
- **combine** maps fixed top folders to different remotes, for example `images=s3:bucket files=drive:dir`. (`sources/rclone-combine.md`)
- **crypt** encrypts file contents and names. File length and modification time are not hidden. It stores no hashes but has an authenticator. The obscured password in the config uses a static key shared by all rclone versions, so it is not real protection. (`sources/rclone-crypt.md`)
- **compress** is "**experimental**. Things may break and data may be lost". It offers gzip, and zstd since v1.72.0 (2025-11-21). Files are named `*.###########.gz`, where the `#` part encodes the original size, and must not be renamed by hand. (`sources/rclone-compress.md`, `sources/rclone-changelog-excerpt.md`)
- **chunker** splits big files to get past a provider's size limit. **hasher** adds checksums for remotes that lack them. (`sources/rclone-chunker.md`, `sources/rclone-hasher.md`)

### 2.2 copy, sync, bisync

Facts:
- `sync` makes the destination match the source, "including deleting files if necessary". It deletes nothing if any error happened, and it has `--max-delete` and `--backup-dir`. `copy` never deletes. (`sources/rclone-cmd-rclone_sync.md`, `sources/rclone-cmd-rclone_copy.md`)
- `bisync` is "an **advanced command**, so use with care ... data loss can result". It keeps listings from the last run and needs `--resync` the first time. A conflict is a file changed on both sides. By default both copies are kept and renamed `.conflict1` and `.conflict2`. It has a lock file, `--max-delete` and `--check-access` safety files. It works between two paths only. (`sources/rclone-cmd-rclone_bisync.md`, `sources/rclone-bisync.md`)
- `check` compares source and destination by size and hash. (`sources/rclone-cmd-rclone_check.md`)

### 2.3 Creating a remote without the interactive prompt

Facts:
- `rclone config create <name> <type> key=value ...` creates a remote in one command. **`--non-interactive` "is for use by applications that wish to configure rclone themselves"**: when rclone needs to ask something, it returns JSON with `State` and `Option` (Name, Help, Default, Examples, Required, IsPassword, Type, Exclusive). The app asks the person and calls again with `--state` and `--result`. Passwords are obscured automatically. (`sources/rclone-cmd-rclone_config_create.md`)
- The same through the API server: `config/create` with `opt.nonInteractive`, `opt.continue`, `opt.state` and `opt.result`. `config/oauthstatus` returns `authUrl` (`http://127.0.0.1:53682/auth?state=...`), and `config/oauthstop` stops a broken sign-in. Long jobs run with `_async=true` and are read through `job/status`. The API server has one all-or-nothing login, so it must stay on loopback with a password. (`sources/rclone-rc.md`)
- On a desktop, Google sign-in opens the browser at `127.0.0.1:53682`. For a server without a browser, `rclone authorize` runs on a machine with one and the token is pasted back. (`sources/rclone-drive.md`, `sources/rclone-remote_setup.md`, `sources/rclone-cmd-rclone_authorize.md`)
- The config file holds the sign-in tokens. It can be encrypted with a password, which can come from `RCLONE_PASSWORD_COMMAND`. On Windows, that command could read the password from Credential Manager. (`sources/rclone-docs-config-encryption-excerpt.md`)
- R2 is set up as `type = s3, provider = Cloudflare`, with an access key, a secret, `region = auto` and the endpoint `https://ACCOUNT_ID.r2.cloudflarestorage.com`. A token with only "Object Read & Write" may need `no_check_bucket = true`. (`sources/rclone-s3-r2-excerpt.md`, `sources/r2-rclone.md`)

### 2.4 Google Drive's own limits

Facts:
- **rclone's shared client id is "being retired and will stop working during 2026 ... creating one is now required"**. rclone's guide: create a Google Cloud project, turn on the Drive API, create a "Desktop app" OAuth client, and publish it, because "Testing" sign-ins "expire after a week". Personal apps under 100 users can stay unverified, at the cost of a warning screen. (`sources/rclone-drive.md`)
- Google's side: an external app in "Testing" gets a refresh token that expires in 7 days. There is a limit of 100 refresh tokens per Google account per client; the oldest is dropped. A desktop app "cannot keep secrets" and should use PKCE. (`sources/google-oauth2-overview.md`, `sources/google-oauth-installed-apps.md`)
- Permissions: `drive.file` (only files the app made) and `drive.appdata` (a hidden app folder) are **non-sensitive**. Full `drive` is restricted and needs a security assessment if data is stored on servers. (`sources/gdrive-api-scopes.md`)
- The hidden app folder "is deleted when a user uninstalls your app from their My Drive", and the person cannot see it in Drive. rclone calls this scope `drive.appfolder`. (`sources/gdrive-appdata.md`, `sources/rclone-drive.md`)
- Limits: 750 GB upload per user per 24 hours, 5 TB largest file. API quota: 1,000,000 units a minute per project and 325,000 per user. rclone says Drive limits it to "about 2 files per second ... lots of small files can take a long time". (`sources/gdrive-api-limits.md`, `sources/google-workspace-drive-upload-limits.md`, `sources/rclone-drive.md`)

### 2.5 Cloudflare R2 limits, and what happens when an account fills or goes

Facts:
- R2 free tier each month: 10 GB-month of storage, 1 million writes (Class A), 10 million reads (Class B), and free egress. After that, $0.015 per GB-month. Infrequent Access is cheaper but has a 30-day minimum. Objects can be up to 5 TiB, and storage per bucket is unlimited. (`sources/r2-pricing.md`, `sources/r2-limits.md`)
- R2 decompresses files uploaded with `Content-Encoding: gzip` by default. (`sources/rclone-s3-r2-excerpt.md`)
- **Google over quota:** no new Drive uploads, no Photos backup, "Your ability to send and receive email in Gmail can be impacted", and no new Docs. **"If you're over your quota for 2 years or longer ... all of your content ... may be removed."** (`sources/google-one-storage-terms.md`)
- The Drive programme policy says Google "may reject new uploads, compress content that exists, or delete content" over quota. Under "Circumvention", it bans "Creating or using multiple accounts ... intended to engage in a behavior that was previously prohibited". (`sources/google-drive-program-policies.md`)
- **Correction to 02-inventory, section 4:** neither Google's Terms of Service nor the Drive policy says outright that spreading storage over several free accounts is abuse. The circumvention rule covers behaviour that was "previously prohibited". The risk is real but not written as a rule. His one paid account remains the safe choice. (`sources/google-tos.md`, `sources/google-drive-program-policies.md`)

### 2.6 Licensing

Facts: rclone is MIT. restic is BSD-2-Clause. borg is a BSD-style licence (text in the file). kopia is Apache-2.0. The OpenTelemetry Collector and Prometheus are Apache-2.0. OpenObserve, Grafana and Loki are AGPL-3.0. (`sources/github-licenses.md`, `sources/rclone-COPYING.md`)

The AGPL matters only if QMX changes their code and serves it to others. Running the unchanged binaries next to QMX is not that. (This is my reading of the licence names, not legal advice.)

### What fits QMX

- **One rclone helper, one remote per account, QMX decides where files go.** Do not use `union` for the pool: one dead account would stop the whole union from opening, and R2 cannot join a free-space rule. QMX already keeps a place list with a keep rule. Each Google account, R2 bucket or server becomes one place, and QMX writes each new pack to the place with the most free space after its floor, which Drive and SFTP report through `about`. A second copy is a choice per place ("keep a copy here too"), not union's all-or-nothing. If he wants a fixed split, `combine` (packs on account A, manifests on account B) is safe because nothing in it is automatic.
- **Only `copy` toward the pool.** QMX deletes from a place only through its own prune, after the index no longer names the pack (section 3.2). No `sync` and no `bisync`.
- **The dialog is rclone's own question loop.** The screen calls `config create --non-interactive` (or `config/create` with `nonInteractive`), shows each `Option` as one question with its help text, default and choices, and for Google opens `authUrl` in his browser. Then it runs "test it" (`about` plus a small write and read) and adds the place row. This is the storage half of 02-inventory section 6, item 2.
- **QMX needs its own Google client.** Register a "Desktop app" OAuth client for QMX, ask only for `drive.file` (non-sensitive, files visible in his Drive, no review needed), publish it so sign-ins do not expire weekly, and use PKCE. `drive.appdata` is closer to a game save but is wiped if he removes QMX's access in Drive, and he cannot see it. `drive.file` is the better fit for "my stuff, visible to me".
- **A floor on any Google account that holds his email.** Default: stop writing when free space would fall under, for example, 2 GB or 10% of the account, whichever is larger. Show it in the screen and let him change it. When an account fills, QMX moves on to the next place and raises one incident; it never fills his Gmail account.
- **Keep the rclone config secret and encrypted.** `data/rclone.conf` is already on the secret list. Add a config password read from Credential Manager through `RCLONE_PASSWORD_COMMAND`, so the token file is useless if copied.
- **R2 for the "servers stand in" case.** R2 has 10 GB free and free egress. That holds the recipes-plus-content set (02-inventory estimate: tens to a couple hundred MB after compression) many times over.
- **Do not use rclone `compress`.** It is experimental and its file names encode sizes. Compression belongs in QMX's packs, where QMX checks every byte.

---

## 3. Compression and packing for mostly-text data

### 3.1 Python 3.14 zstd, tar and zip

Facts:
- Python 3.14 adds `compression.zstd`, which binds Meta's zstd library. zstd support is also added to `tarfile` (`'w:zst'`, `'r:zst'`), `zipfile` (`ZIP_ZSTANDARD`, written as method id 93) and `shutil`. (`sources/python314-whatsnew-zstd-excerpt.md`, `sources/python314-tarfile.md`, `sources/python314-zipfile.md`)
- `compression.zstd` is an "optional module": a Python build may lack it. On this PC, Python 3.14.6 has it, with zstd 1.5.7 (checked by import). (`sources/python314-compression-zstd.md`)
- It can train a dictionary (`train_dict`, `ZstdDict`), which improves "compression of smaller amounts of data". `checksum_flag` adds an XXHash64 checksum to each frame, which decompression verifies. `content_size_flag` writes the original size into the frame. (`sources/python314-compression-zstd.md`, `sources/python314-tarfile.md`)

**My measurement** on `D:/QMX-worktrees/bld-br4/qmx-agents/packages/qmx-engine/src/qmx_engine/templates/` (701 files, 1,352,023 bytes, no `__pycache__`), standard library only:

| Method | Bytes | Smaller by |
|---|---|---|
| Each file alone, zstd level 3 | 556,326 | 2.43 times (18 ms in all) |
| Each file alone, zstd level 19 | 531,205 | 2.55 times (392 ms) |
| zip with `ZIP_DEFLATED` | 633,987 | 2.13 times |
| zip with `ZIP_ZSTANDARD` | 668,535 | 2.02 times |
| Each file alone, zstd level 3 with a 64 KiB trained dictionary | 280,622 + 65,536 dictionary | 4.82 times |
| tar plus zstd, default level | 249,520 | 5.42 times |
| All files as one zstd stream, level 3 | 229,440 | 5.89 times |
| All files as one zstd stream, level 19 | 181,316 | 7.46 times |

His idea that zip is the way to go needs one change. zip compresses each file alone, so it barely beats single-file zstd. The large gain comes from compressing many similar files together, which is what tar plus zstd and packs do.

### 3.2 restic, borg and kopia: packs, index, prune and check

Facts:
- **restic:** a blob is data plus its SHA-256. A pack holds many blobs, then a header listing each blob's type, length and hash, so "the index can be rebuilt" from packs alone. Index files map blob to pack, offset and length, are kept under 8 MiB each, and may overlap. Write order: "pack files ... Then the indexes ... And finally the corresponding snapshots"; read in the opposite order. Removing data "must acquire an exclusive lock first", and "a pack must be removed from the referencing index before it is deleted". Rewriting a pack means: new pack, then new index, then delete the old pack. (`sources/restic-design.md`)
- restic chunks content with Rabin fingerprints: files under 512 KiB are not split, and blobs are 512 KiB to 8 MiB, about 1 MiB on average. Repository format 2 compresses blobs with zstd (`--compression off|fastest|auto|better|max`). Packs default to 16 MiB. (`sources/restic-design.md`, `sources/restic-tuning.md`)
- **restic prune:** it marks each pack as fully used, partly used or unused. Unused packs are deleted. Partly used packs are repacked only past `--max-unused` (default 5%), because repacking means "download the file ... and re-upload". `--max-repack-size` limits the work per run. (`sources/restic-forget-prune.md`)
- **restic check:** by default it checks structure. `--read-data` downloads everything. **`--read-data-subset=n/t` checks a different slice each run** (for example 1/5, then 2/5). (`sources/restic-working-with-repos.md`)
- restic can use any rclone remote as `rclone:<remote>:<path>` and starts and stops rclone itself. (`sources/restic-preparing-new-repo.md`)
- **borg 1.4:** about 500 MB segments in a log. It compacts by writing new segments and never edits old ones. Content-defined chunks use buzhash with a 512 KiB minimum by default. `check --verify-data` reads everything; `--repair` is marked "POTENTIALLY DANGEROUS". It needs borg on the far side over SSH; borg 2 (which adds SFTP) is still a beta (2.0.0b25, 2026-09-27). (`sources/borg-internals-data-structures.md`, `sources/borg-usage-check.md`, `sources/borg2-repository-urls.md`, `sources/borg-releases.md`)
- **kopia:** blocks are named by their hash, so equal blocks dedupe themselves. Small blocks are put into packs of 20 to 40 MB. The index maps block to pack, offset and length, and "a local index is also stored at the end of each pack" for recovery. Packs are prefixed `p` (data) and `q` (metadata), indexes `x`. (`sources/kopia-architecture.md`)
- **kopia maintenance:** quick maintenance runs about hourly and full maintenance (garbage collection and pack compaction) every 24 hours. **Exactly one `user@host` is the "Maintenance Owner"; other machines do not run maintenance.** (`sources/kopia-maintenance.md`)
- kopia lets a policy skip compression for file types that are already compressed. Its benchmark shows zstd at about half the size of s2. (`sources/kopia-compression.md`)

### 3.3 Which ideas fit QMX's pool

QMX today: each file is stored once, named by its sha256, with one manifest per copy. The hash is checked when writing and again on restore (02-inventory section 3).

| Idea | Take it? | Why |
|---|---|---|
| **Packs with an index (hash, pack, offset, length)** | **Yes** | Drive's 2 files a second makes loose files slow, and packing gives 5 to 6 times more compression on QMX's own data (3.1). |
| **Index rebuildable from a header in each pack** | **Yes** | If the index is lost or damaged, a check rebuilds it from the packs, as restic and kopia do. |
| **Write packs, then index, then manifest; delete in reverse** | **Yes** | This is the same "safe copy order" PR 225 already uses, carried over to packs. |
| **Compress inside the pack, one zstd frame per file with a trained dictionary, or one frame per group of files** | **Yes** | One frame per file keeps "fetch one file" cheap. A dictionary trained on QMX's own JSON gets most of the gain of one long stream (4.8 times against 5.9 times). Skip Parquet, PDF and images, as kopia does by type. Turn on `checksum_flag`, and keep the sha256 of the original bytes as the name. |
| **Prune that repacks only past an unused threshold, with a size cap per run** | **Yes** | This is his "re-pack periodically" without re-uploading everything every month. Start with restic's 5% unused. |
| **Check one slice at a time (`n/t`)** | **Yes** | A monthly maintenance workflow can download and verify one twelfth of the packs each month, plus the full index and all manifests. PR 226's drill becomes the step that proves a real restore. |
| **One maintenance owner** | **Yes** | With several machines writing to one account, only one machine prunes and repacks, under a lock file in the place. The others only add. This is kopia's rule. |
| **Content-defined chunking** | **Not now** | QMX's files are small JSON, TOML and scripts, mostly under restic's 512 KiB "do not split" line. Whole-file sha256 already dedupes them. Chunking matters only for big files that change in place (SQLite stores, long chat logs). Those are run results or are better saved as appended records. |
| **Encryption inside the pack** | **Optional** | Only if he keeps copies on a service he does not trust. rclone `crypt` over the place can be added later without changing the pack format. |
| **Use restic or kopia instead of building packs** | **Possible, weigh it** | restic (BSD-2) talks to every rclone remote and already has packs, zstd, prune and partial checks. The cost is that QMX's own manifest, keep rule and "recipes only" selection would sit on top of restic's snapshot model, and QMX's sha256 pool would no longer be the store. QMX's pool is small and its rules are QMX-specific, so a small pack layer in QMX is likely simpler. This choice belongs in the design round. |

---

## 4. OpenObserve self-hosted, and how agents read it

### 4.1 One node, several machines, data folder, retention, desktop use

Facts:
- **Single node** (SQLite plus local disk) is the default, for "light usage and testing or if you don't require HA". It handles about 31 MB a second (2.6 TB a day) on an Apple M2. Single node can instead keep its Parquet files **in S3-compatible object storage** "so data survives the loss of the node's local volume". **HA mode** needs Kubernetes, object storage, PostgreSQL and NATS, with no local disk. (`sources/openobserve-architecture.md`)
- **Windows:** the quickstart lists a Windows download. Set `ZO_ROOT_USER_EMAIL` and `ZO_ROOT_USER_PASSWORD` on the first start only, then run `openobserve.exe`. The doc says to use an Administrator prompt. The v1.1.2 Windows zips exist: 150 MB for the free edition and 175 MB for Enterprise (checked by HEAD request, nothing downloaded). (`sources/openobserve-getting-started.md`, `sources/openobserve-windows-binaries-head.md`)
- **Settings that matter on his laptop:** `ZO_DATA_DIR` (default `./data/openobserve/`), `ZO_LOCAL_MODE=true`, `ZO_LOCAL_MODE_STORAGE` (disk or s3), `ZO_HTTP_PORT` 5080. **`ZO_COMPACT_DATA_RETENTION_DAYS` defaults to 3650 (10 years), minimum 3.** **`ZO_TELEMETRY` defaults to true** (anonymous telemetry to OpenObserve). **`ZO_DISK_CACHE_MAX_SIZE` defaults to "50% of the total free disk".** Data older than 5 hours is refused at ingest (`ZO_INGEST_ALLOWED_UPTO`). (`sources/openobserve-administration-configuration-environment-variables.md`)
- OpenObserve's docs do not say anything specific about running it on a desktop. The only guidance is the single-node quickstart and its Windows steps.
- **Windows machine data** (event logs and performance counters) is collected by the OpenObserve Collector (one command, needs Administrator) or by a plain OpenTelemetry Collector. (`sources/openobserve-integration-system-windows.md`)
- **Price:** Cloud costs $0.50 per GB ingested. Self-hosted, the free edition is "free forever", and **self-hosted Enterprise "is free for up to 50 GB of ingestion per day"**, including SSO, RBAC, federated search and audit trail. (`sources/openobserve-pricing.md`)

### 4.2 How agents read it

Facts:
- **MCP is built in**, "available in Open Source, Enterprise Edition, and Cloud", at `https://your-instance/api/{org_id}/mcp`, with basic auth in every edition. It has about 150 tools in groups (Search 17, PromQL 7, Traces 5, Streams 5, Alerts 28 ...). Tools are found on demand: `tools/list` shows `tool_search`, `tools_call` and six pinned tools. (`sources/openobserve-integration-ai-mcp-index.md`)
- **"On an Open Source instance, every MCP tool call runs with the connected account's full privileges. This includes the destructive tools"** such as deleting streams and users. Scoped users need RBAC, which comes with Enterprise or Cloud. (`sources/openobserve-integration-ai-mcp-index.md`)
- A plain HTTP API also exists: `POST /api/{org}/_search` with SQL and a time range in microseconds. (`sources/openobserve-reference-api-search-search.md`)

### 4.3 The OpenTelemetry Collector's role

Facts:
- The Collector receives, processes and exports telemetry, vendor-neutral, and "removes the need to run, operate, and maintain multiple agents/collectors". (`sources/otel-collector-index.md`)
- In the **agent** pattern, a Collector runs on the same host as the app. In the **gateway** pattern, apps or other Collectors send to one shared OTLP endpoint. (`sources/otel-collector-deploy-agent.md`, `sources/otel-collector-deploy-gateway.md`)
- **Persistent queue:** with `sending_queue.storage` pointing at `file_storage`, batches wait on disk. "If the collector instance is killed while having some items in the persistent queue, on restart the items will be picked and the exporting is continued." Data is dropped when the queue or its storage is full. (`sources/otel-exporterhelper-readme.md`)
- OpenObserve's migration guide: going from the Grafana stack to OpenObserve changes "Collector + Loki + Mimir + Tempo + Grafana + object storage" (6 or more parts) into "Collector + OpenObserve" (2), and the Collector needs only an endpoint change. (`sources/openobserve-migration-migrate-from-grafana-to-openobserve-architecture.md`)

### 4.4 One table: OpenObserve against Grafana, Prometheus and Loki, for one person

| | OpenObserve (single node) | Grafana + Prometheus + Loki (+ Tempo for traces) |
|---|---|---|
| Programs to run | 1 (plus a Collector per machine) | 3 to 4 (plus a Collector or agent) (`sources/openobserve-migration-...-architecture.md`) |
| Logs, metrics, traces | All three in one store (SQL and PromQL) | Loki logs (LogQL), Prometheus metrics (PromQL), traces need Tempo |
| Windows binary | Yes, 150 MB zip (`sources/openobserve-windows-binaries-head.md`) | Grafana: Windows installer (`sources/grafana-install-windows.md`); Loki: `loki-windows-amd64.exe` (`sources/loki-install-local.md`) |
| Default retention | 3650 days (`sources/openobserve-...-environment-variables.md`) | Prometheus 15 days (`sources/prometheus-storage.md`); Loki keeps forever unless the compactor's retention is on (`sources/loki-retention.md`) |
| Long-term or off-machine storage | Single node can write Parquet to S3 or R2 | Prometheus local storage "is not clustered or replicated" and uses remote-write for that; Loki uses object storage (`sources/prometheus-storage.md`) |
| Agent access | Built-in MCP; free edition gives full rights including delete; Enterprise (free to 50 GB a day) has RBAC | Grafana's MCP server (Apache-2.0) queries Prometheus and Loki, and has `--disable-write` (`sources/grafana-mcp-readme.md`) |
| Licence | AGPL-3.0 (Enterprise binary under its own terms) | Grafana and Loki AGPL-3.0; Prometheus Apache-2.0 (`sources/github-licenses.md`) |
| Cost if hosted | $0.50 per GB ingested (Cloud) | Not researched (Grafana Cloud) |

### What fits QMX

- **Keep OpenObserve, one per person, on the machine he picks.** The design already points `[telemetry] send_to` at "this PC" or a place. On every other machine, the step "install telemetry" (02-inventory section 6, item 5) installs an OpenTelemetry Collector with a `file_storage` queue that sends to that one OpenObserve. A PC that is offline keeps its logs on disk and sends them later.
- **When QMX starts OpenObserve on the PC, set:** `ZO_TELEMETRY=false`, `ZO_DISK_CACHE_MAX_SIZE` to a small fixed size (for example 1024 MB), a retention he can see and change in the screen (for example 30 days), `ZO_DATA_DIR` under `cache/openobserve/`, and `ZO_HTTP_ADDR=127.0.0.1` with port 5080 (gRPC on 5081). When a server sends to the PC, bind the Tailscale address instead. The docs' quickstart uses an Administrator prompt. Whether a per-user `openobserve.exe` runs without one is not stated and was not tested here. Test that first, because a per-user, no-admin run is what Docker and Ollama manage (5.1).
- **Does the logs layer need a backup?** Mostly no. Logs are the "rebuilt or not needed" class. If he wants to keep them, OpenObserve's own single-node S3 mode can store its Parquet in an R2 bucket. That is OpenObserve's own feature, so it should not go through QMX's sync. Its alert rules and dashboards are recipes; export those through its API into the sync set.
- **For agents, read-only first.** Either run the self-hosted Enterprise build (free to 50 GB a day, his volume is far below) and give agents a read-only role over MCP, or keep the free build and give agents only QMX's own read tool, which calls `POST /_search`. Do not give an agent the free build's MCP endpoint with the root login.
- **Grafana is not needed.** For one person, one program with built-in logs, metrics, traces and UI beats running 3 to 4 programs.

---

## 5. Installers, first-run steps, and update flows that back up first

### 5.1 Installers and first-run sequences

Facts:
- **Docker Desktop on Windows:** "per-user" install is the default and recommended. It goes to `%LOCALAPPDATA%\Programs\DockerDesktop` and needs no admin to install or update. An "all users" mode needs admin. Interactive steps: pick the install mode, pick the backend on a Configuration page (with only one choice shown when only one works), authorize, then Close. **Docker Desktop does not start by itself after install.** On first start it shows the subscription terms and runs only after Accept. Command-line flags give a silent install (`--quiet`, `--accept-license`, data-folder paths). WSL setup is a separate step that may ask to restart. (`sources/docker-desktop-windows-install.md`)
- **Docker's backup page** says to back up before a different version or a reset: commit containers to images, push or `docker image save` the images, and back up volumes separately. "If you use volumes or bind-mounts ... backing up your containers may not be needed", if you keep the Compose file that recreates them. That is the recipe idea again. (`sources/docker-desktop-backup-restore.md`)
- **Ollama on Windows:** a native app that runs in the background with its API on `localhost:11434`. The installer needs no Administrator and installs into the home folder, with about 4 GB for the program. `OllamaSetup.exe /DIR="d:\..."` moves the program and `OLLAMA_MODELS` moves the models. (`sources/ollama-windows.md`)
- **Tailscale (adding a machine without a browser):** auth keys "let you register new nodes without needing to sign in using a web browser". They come as one-off or reusable ("Be very careful with reusable keys") and expire after 1 to 90 days. An OAuth client can create keys through the API. The Windows install and the Linux one-line script are in `sources/tailscale-install-windows.md` and `sources/tailscale-install-linux-script.md`. (`sources/tailscale-auth-keys.md`)
- **Steam:** I did not find a primary page that lists the client's first-run steps. Its cloud behaviour (pull settings at login, sync at launch and exit, conflict window) is in 1.4.

### 5.2 Update flows that back up first

Facts:
- **Hermes `hermes update`**, in order: (1) **pre-update snapshot** of each profile's state files (pairing, cron jobs, `config.yaml`, `.env`, `auth.json`), skipping files over 1 GiB. The setting `updates.pre_update_backup` is `quick` (default), `full` (adds a zip) or `off`. **If the snapshot fails, the update prints "⚠ Pre-update snapshot FAILED" and goes on.** (2) code update, pausing the gateways. (3) **syntax check of the critical files, with automatic rollback** to the commit from before the pull. (4) dependencies; a plugin that no longer fits is switched off, not fatal. (5) config migration that asks about new options. (6) desktop rebuild with **stage-and-swap**, so a failed build leaves the old app launchable. (7) restart. "A code checkout alone is not a data rollback." (`sources/hermes-docs-updating.md`)
- `hermes backup` copies SQLite with SQLite's own `backup()` and leaves out WAL files, checkpoints, models, runtimes, browser profiles and regenerable cache. It exits 1 if anything was missing, so a timer never reports a partial backup as success. `--keep 3` prunes older zips only after a complete backup. `hermes import` checks every member's CRC before writing anything. **When the imported database has fewer messages than the current one, it says so**: "Session data replaced by older backup contents ... Anything recorded after the backup was taken is not in it." (`sources/hermes-cli-backup-import-excerpt.md`)
- **n8n:** the update page links to "Back up and restore". The backup page itself says a CLI export is not a full instance backup (1.8). (`sources/n8n-update.md`, `sources/n8n-backup-and-restore.md`)
- **Android:** restore happens at install time, before first launch (1.2). (`sources/android-auto-backup.md`)

### What fits QMX

- **The update sequence for QMX:** (1) sync to his account, if the switch is on, with a time limit; if it fails, show one line and ask "update anyway?" instead of going on silently. (2) The quick local copy before upgrade that PR 228 already makes. (3) Update code and environment. (4) Check: start the new version against a copy, or run its store checks. (5) Roll back the code if the check fails. This is Hermes's order, with the off-site step added and the silent "continue on failure" turned into a question.
- **The install should look like Docker's and Ollama's:** per-user, no admin, nothing in Program Files, folder choice up front (his C: drive is nearly full, so ask for the data folder before anything else). The first start is a short card sequence: choose or make the QMX folder → "Restore from my account?" (Android's restore before first use) → sign in to his storage → optional extras (OpenObserve, Ollama, servers) each as its own step.
- **Each "connect" step is a job with steps.** The host's job runner already reports step, done of total, and one stop line (02-inventory section 6). Server connect can use a one-off Tailscale auth key created for that machine, so the new machine joins without a browser. Storage connect uses rclone's question loop (2.3). OpenObserve on a new machine means installing a Collector pointing at his one OpenObserve.
- **Warn when a restore goes backwards.** Copy Hermes: if the copy he restores has fewer chats or runs than what is on the PC, say so in numbers before the swap.

---

## Not covered or not verified

- I did not run union, bisync or `config create` against a real account. The union behaviour in 2.1 comes from the source code.
- iCloud key-value conflict rules are not spelled out on Apple's current page; only "reconciles" is stated.
- I found no primary page for Steam's installer or first-run steps.
- The OpenObserve Enterprise free tier (50 GB a day) is from its pricing page. I did not check the licence file of the Enterprise binary.
- Grafana Cloud pricing was not researched.
