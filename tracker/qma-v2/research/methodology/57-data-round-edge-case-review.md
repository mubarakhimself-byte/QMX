# 57 — Data round: edge-case review of the design (55 and the amended spines)

Date: 2026-10-22. Independent technical review. **Opus reviewing Opus:** the reviewer is Claude Opus 5.5, the same model that wrote 55, so shared blind spots are likely; treat a clean area here as "not found", not "proven safe". No sub-agents. Nothing committed; no design file edited.

**Method.** BMad review lenses run headless and in sequence: edge-case hunter (primary: every path and boundary walked, only unhandled ones kept), adversarial general, verification gap; plus the blast-radius rule (prove the one fact by running code). The caller asked for severities, so each finding has one (the lens files themselves rank nothing). Inputs: `55-data-round-architecture.md`; the diff `751583ff` (Library AD-25 to AD-33 and amendments, MIGRATION, OPEN-DECISIONS, engine AD-67 to AD-70 and amendments, SOLUTION-DESIGN §30, HARNESS-REQUESTS H59-H62, Lab AD-19/20, UI-HANDOFF §17, rulings 120-134); `56-external-connections-research.md`; `51`, `52`, `53`, `54`. Code truth: `origin/engine/base` `8af1a1cd`, read with `git show` / `git grep`, no checkout.

**Proof levels** (blast-radius): *said* < *pointed at* (file:line) < *walked* < *ran* (a script calling the real library) < *reproduced in the app*.

---

## 0. Plain words first

The design is broad and mostly sound in shape: one Library, one door to prices, everything content-addressed, conflicts never silently picked. The trouble is in the joins between machines and in three built parts the design leans on without testing them at real size:

1. **The price store as built cannot hold a month of ticks.** It writes the file, then cannot read it back (proven by running the same library calls). Importing the old 10 GB would also grow it many times over.
2. **Switching on the built sync loop copies every server file onto the PC**, whose C: drive has 12 GB free.
3. **cTrader's token refresh logs out every other holder of the token.** The design has the PC, the server and later a trading server all holding one grant, with a cron job refreshing it. A live bot would be logged out by the PC's routine refresh.
4. **"Agents never touch money" is not true on the PC as designed.** Every chat there has a shell, and the design stores the trading-capable cTrader token in the same Windows vault the shell can read.

Each has a simple fix. Section 10 lists the probes that would have caught them. Totals: 4 critical, 16 high, 20 medium, 7 low.

---

## 1. Price history: store, partitions, cards, the door

### F1 — CRITICAL. The built price store cannot hold a month of ticks
- **Scenario.** DR3 imports the old ticks (or the first Dukascopy month lands) through the existing `qmf-data` raw archive → the file is written, but every later read fails with `Couldn't deserialize thrift: TProtocolException: Exceeded size limit` → the card says the month exists, and the copilot, QMB and the Lab get "storage failure" for every tick month. A re-download of the same month also fails, because the idempotency check reads the old file first.
- **Evidence (ran).** `qmf/data/store/engines/parquet.py` (`8af1a1cd`) stores each row as a JSON string column **and** embeds the whole artifact's canonical JSON in the Parquet schema metadata; `read_canonical` calls `pq.read_schema`. A script that uses the same pyarrow calls (pyarrow 25.0.1, the `qmf-data` pin) with tick-shaped rows: 1,100,000 rows → 95.7 MB canonical, 234.7 MB file, **read_schema FAILED**; 1,500,000 rows → 130.5 MB canonical, 320 MB file, **FAILED**. One month of EURUSD ticks is several million rows. The file is also about 2.5 times the size of its own JSON, and `admit` holds the whole month as Python dicts in memory. The 10 GB of compressed bi5 would grow to hundreds of GB in this format. The server has 193 GB in total (52 r64).
- **Why the design missed it.** D-1 says "`qmf-data` keeps its store; the change is a rule on the window". Its "safe because" points only at the `partitions.py` header. P-MDREAD, the read probe, is scheduled before DR4, one step **after** the DR3 import.
- **Fix.** Before DR3, give the price archive a real columnar writer: typed columns (`t` int64 ns, prices as scaled int64, volumes), compressed, and no canonical copy in the metadata. Take the fingerprint over a fixed, version-pinned logical encoding of the sorted rows, streamed, so it does not change with the pyarrow version. Move P-MDREAD (with one real month of ticks) ahead of DR3.

### F2 — HIGH. Partition keys collide, and a collision reads as a "correction"
- **Scenario.** Dukascopy candles come as bid *or* ask, one side per run (56 §7). Run 1 writes `dukascopy/EURUSD/m1/2024/03` from bid prices and run 2 writes the same key from ask prices. The second either "corrects" the first (a `replaces` edge, and every result on it now reads "corrected") or is deduped away by the claim, so ask prices never arrive. The same happens with RSI(14) and RSI(21) from one component version (key `derived/<component>-v<n>` has no parameters), with the calendar (no instrument) and with fills (keyed by account, not instrument).
- **Evidence.** 55 D-1 and Library AD-25 key `source / instrument / kind / year / month`, and AD-32 keys derived series as `kind = <component>-v<version>`. In code, `SeriesPartition.identity()` holds only `source, venue, symbol, window` (`partitions.py`); `kind` is not in it.
- **Fix.** Key = `source / subject / kind / variant / year / month`. `subject` is the instrument, the account or `-`. `variant` is the price side, or the parameter fingerprint for derived series. The door's `commit` refuses a second, different file for an existing key unless the caller marks it as a correction with a reason.

### F3 — HIGH. The daily rewrite of the open month piles up on disk for ever
- **Scenario.** The current month is "rewritten daily, frozen at month end" (D-1). Each rewrite is a new immutable file named by its fingerprint, and the raw archive keeps everything (`StoreReceipt(retained_forever=True)` in `append_store.py`). Over a month, the daily copies of one series add up to about 15 months of that series' data. For ticks on 28 pairs, the server (193 GB) and the bucket fill within weeks. Each rewrite also mints a card version (F4).
- **Fix.** Keep the open month out of the immutable archive. Either append it as day files in a mutable staging area served by the door, or rewrite it under one fixed open key. Only a frozen month enters the archive and mints a card version. "Complete up to" is computed at read time.

### F4 — HIGH. Card-level versions turn every mark into noise
- **Scenario.** A result's `consumed` edge points at the **card version** (AD-25). A new month, the daily rewrite, or a change in `where` (a cache eviction, a bucket push) mints a new card version. "Superseded" is computed as "the consumed object is no longer the head" (AD-22), so the next day **every backtest on that series shows "superseded"**. A correction to March 2024 marks every result on the series "corrected", including results that only read 2019. He learns to ignore marks, and then misses a real one.
- **Evidence.** Library AD-22 (computed `superseded` and `corrected`), AD-25 (`where` with bytes per tier as a card field, a new card version per month and per daily rewrite). This contradicts AD-33, which says where the bytes are and their size are "computed at read time and never stored". The calendar feed keeps "every revision", so it mints versions all month.
- **Fix.** For data, compute marks from the partition fingerprints the result lists (AD-25 already records them): "corrected" only when a partition it read has a `replaces`. Appending months never makes a result "superseded". `where`, sizes and freshness are read-time facts (AD-33), not card fields.

### F5 — HIGH. Dukascopy gaps freeze silently into "complete" months
- **Scenario.** dukascopy-node has **retries off by default and does not retry empty responses unless `--retry-on-empty`** (56 §7). Dukascopy returns empty rather than failing (56 §8.4). A flaky night leaves empty hours. The month is frozen at month end as an immutable partition, and the card shows a quality grade, but nothing re-fetches.
- **Evidence.** 55 D-4 says dukascopy-node runs "with its own retries and batch pauses", which contradicts 56 §7.
- **Fix.** Run it with `--retries` and `--retry-on-empty`. Freeze a month only when its gap check against the market calendar passes, or when he accepts the listed gaps. Otherwise it stays `incomplete` and the downloader retries it. P-DUKA must include an injected empty hour.

### F6 — MEDIUM. Partitions made on the PC have no way into the server's door
- **Scenario.** MT5 history (PC only), a feed he moved to the PC (ruling 117), and ML features made on the PC are committed by the PC's door. The server's door is the only writer of the main copy (AD-28), and AD-16's rclone push would be a second writer → the main copy never lists them, or two writers race on its metadata.
- **Fix.** The PC door pushes finished partition files to a server route that stages them and calls the server door's `commit`, with the same verify-by-fingerprint step.

### F7 — MEDIUM. `seal-roll` contradicts the seal law, and a PC door can serve with a stale seal
- **Scenario.** SOLUTION-DESIGN §30.1 adds a monthly `seal-roll` that "moves the holdout boundary". `seal.py` says the boundary is **frozen**, stored verbatim, and "never silently recycled" (DEC-0119). Moving it releases months that were sealed, and possibly looked at in a final look, back into exploration. A PC door that has not synced since the roll serves months the server now treats as sealed. No AD and no ruling covers this policy.
- **Fix.** Put the seal policy in an AD: the seal moves only by his click, journaled. Each door reads the seal as a Library item and fails closed past the last boundary it has confirmed with the server.

### F8 — MEDIUM. "One final look" has no single authority across machines
- **Scenario.** The server is unreachable → the PC door journals a final look in its own store → later the server door allows another. That makes two "one" final looks for the same family and window.
- **Fix.** A final look takes a Hub claim `final_look:<family>/<window>` and is refused while the Hub is unreachable (it waits, it does not fail).

### F9 — MEDIUM. Removing the 1,000-bar cap leaves nothing to shape big reads
- **Scenario.** The copilot calls `data.bars` for 23 years of one-minute bars (about 12 million rows) → the answer floods the model's context, or the door's in-process DuckDB/pyarrow read balloons the one server process (F39).
- **Fix.** This is answer shape, not a cap. A large read returns a handle (the materialised file path, row count, a summary, a chart spec), and the model reads excerpts on demand (engine AD-63 budgets). Heavy reads run in a child process.

---

## 2. The Library across PC and server: sync, outbox, split-brain, power cuts

### F10 — CRITICAL. The built sync loop copies every server file onto the nearly full PC
- **Scenario.** DR2 switches on `replicate.sync()` "on each commit, on a timer, on wake" (AD-26). The server then holds uploads, extracted pages, recordings, model weights and run logs → each sync **pulls every durable blob the PC lacks** → C: (12 GB free, 97 % used) fills → Library writes, the outbox, Hindsight and Windows itself start failing. He sees the desktop app and then the PC break.
- **Evidence (pointed at).** `qmx_hub/replicate.py` `_copy(..., pull=True)`: `wanted = source.object_ids() - target.object_ids()`, and for each wanted object, every blob it names is fetched whole (`source.blob(blob_id)` returns `bytes`) and stored (`target.store_blob`). Every sync also lists the full id sets of both stores. AD-10 says the PC holds "hot blobs" only, and the code does not.
- **Fix.** The PC pulls manifests, edges and refs only; blobs come on demand through the store's `upstream` fetch (`get` already fetches a missing blob). Sync by ref-log sequence ("moves since seq N") instead of full set difference. Blobs move as streams. One sync runs at a time, coalesced when commits burst.

### F11 — HIGH. A replayed save becomes a false conflict (or a duplicate item)
- **Scenario.** The PC sends a save; the server applies it; the reply is lost (a 60 s timeout, Wi-Fi drop, PC sleep) → the outbox replays the same call with the same `expected_head` → the server's head is now the object the PC itself wrote → `stale_head` → per AD-26 a **`merge-conflict` he has to resolve against his own save**. For a new item, if the outbox did not record the item id, the replay mints a second item.
- **Evidence (walked).** `qmx_library/store.py` `put`: the `head != expected_head → stale_head` check runs **before** the `object_id == head` idempotent return. `client.py` uses a 60 s urllib timeout, and a timeout is not a typed refusal, so the outcome is unknown.
- **Fix.** Each outbox record carries the item id and the object id it intends. On replay, "head equals my intended object" is success. Simplest is to swap the two checks in `put`. Add a probe: kill the connection after the server commits, replay, expect no conflict.

### F12 — HIGH. Two "primaries" are possible, and the built sync silently rewinds `main`
- **Scenario.** `primary` lives in two config files (AD-19), so a flip can stop half done: the PC is restored from an old backup, or one side restarts with the old setting. If the PC still says `primary = pc`, it **pushes its older `main` heads onto the server, and the server accepts them**. Server-landed results drop off `main` with no alarm. Nothing is lost (objects are immutable), but `main` regresses, and he sees results "vanish".
- **Evidence (walked).** `replicate.py` `plan()`: for a ref this store owns, `push` happens whenever the heads differ, with no ancestry check. `store.mirror()` "is not an act, so any role takes one" (CAS on the head just read). The hub's `op("mirror")` passes straight to `store.mirror`. AD-14's "stale_head is an alarm" never fires, because the CAS uses the fresh head.
- **Fix.** (1) A primary **epoch** stored as a ref in the server store; both sides check it on every sync, and the stale side refuses to act as primary. (2) Pushing an owned ref is fast-forward only: the other side's head must be an ancestor, otherwise it is an alarm. (3) The hub refuses `mirror` of refs it owns under its own table.

### F13 — HIGH. A power cut mid-append can stop the Library from opening
- **Scenario.** The PC loses power while appending a ref move, edge or annotation, leaving a partial last line (or NUL bytes on NTFS). On restart the size stamp mismatches → `rebuild_indexes()` → `_lines()` calls `json.loads` on the torn line → `Store.open` raises → **the Library will not open**, and every chat, workflow and screen that uses it fails. The new outbox file has the same risk.
- **Evidence (walked).** `store.py` `_append` (write, fsync), `_lines` (`json.loads(line)` for every non-blank line, no recovery), `__init__` (`if self.catalog.stamp() != self._stamp(): self.rebuild_indexes()`). The `qmf-data` Parquet writer replaces the file without an fsync (`parquet.py` `write`), so after a cut on the PC a partition can be present but corrupt.
- **Fix.** The log reader treats a last line with no newline, or one that fails to parse, as torn: it moves it aside to `quarantine/`, raises an alarm and carries on. Every line is written with its own checksum. fsync before the rename in the Parquet writer. Probe: truncate the last line of each log and open the store.

### F14 — HIGH. There is no procedure for "the server is gone"
- **Scenario.** The server was reset on 2026-10-21 (ruling 130). With the server as the main copy and the bucket not yet chosen (F21), a repeat loses every server-born record the PC had not pulled. AD-19's reverse flip ("push until the ref logs are equal") needs both machines alive.
- **Fix.** A written and drilled runbook: the PC promotes its mirror to primary with an epoch bump (F12), lists which refs it holds only as stale mirrors, and the server is rebuilt from the bucket and re-paired. Drill it on scratch roots before DR2.

### F15 — MEDIUM. Offline saves are invisible on the PC that made them
- **Scenario.** With `primary = server` and the server unreachable, a save goes to the outbox, and the PC replica's `main` does not have it. Search, the Library list, a PC workflow and the copilot cannot find the note he just saved. UI-HANDOFF §17 item 6 promises "saved on this PC".
- **Fix.** Reads on the PC overlay pending outbox entries with a "waiting for the server" badge. Or the outbox writes land first on a PC-owned ref (`refs/pending/<item>`) that reads include.

### F16 — MEDIUM. The PC and server can run different versions, and nothing checks
- **Scenario.** The PC updates first and writes a `trade` (a new kind) or a new `source` field → the older server refuses it with `unknown_kind` / `schema_invalid` → the save lands in the outbox or fails, with no clear reason. Outbox records written by one version are replayed by the next.
- **Evidence.** `Store.open` copies the kind schemas from the installed package into the store (`store.py`), so kinds travel with code, not with data.
- **Fix.** The hub handshake compares `qmx_version` and the kind-registry digest (both already in the heartbeat, engine AD-65) and refuses with `server_needs_update`, which the UI shows. Update the server first. Outbox records carry their version.

### F17 — MEDIUM. AD-16's rclone push PC→server becomes a second writer
- **Scenario.** AD-16 still says PC→server pushes "objects, blobs and the ref-log tail" by rclone over SFTP. With `primary = server`, the in-process host is the server store's only writer (AD-26), and an rclone write into its folders (the ref log above all) races it.
- **Fix.** With `primary = server`, the PC talks only through the Hub API, and rclone is used only server→bucket. Amend AD-16.

### F18 — MEDIUM. Syncing "on each commit" with full listings floods the hub
- **Scenario.** An agent writes 500 notes in a minute → 500 syncs, each listing every object id on both sides over the tailnet (`object_ids()`), plus a whole-blob read on the PC just to test existence (`target.blob(blob_id) is not None`).
- **Fix.** The same as F10: sequence-watermark sync, one at a time, coalesced, and an existence check that does not read the bytes.

### F19 — MEDIUM. D-2's "safe because" is false on his real home
- **Scenario.** D-2 rests on "every save since the mirror went on is already in the new store", and MIGRATION cuts the dual run to one comparison for that reason. But 52 §3 item 2 (and 55's own D-2 edges) say his real home has **no** new-store folder: the mirror never ran there. So the switch-over relies on an importer that has never run on his real data.
- **Fix.** Rehearse the import on a copy of his real `~/.qmx` (scratch root), compare counts and hashes, then flip. Keep `library.db` read-only as planned.

### F20 — LOW. Windows file-sharing errors on save
- **Scenario.** Defender or the search indexer briefly opens a new file → `os.replace` raises a sharing violation (WinError 5 or 32) → a save fails at random.
- **Fix.** Retry `os.replace` with short backoff on those two errors, and exclude the Library and cache folders from indexing.

---

## 3. Disks, backups, the bucket

### F21 — HIGH. Without the bucket, the storage rules lock each other
- **Scenario.** The bucket is still his open call (55 §12), but DR2 makes the server the main copy before it. With no bucket: (a) a durable blob may leave the PC only "after two verified remote copies" (AD-10), so **nothing ever leaves the PC**; (b) the old 10 GB can never be freed; (c) the nightly server→bucket push has no target, so the server is the only off-PC copy, the same server that was reset yesterday. A 3 GB upload made on the PC stays on C: for good.
- **Fix.** Make the bucket a precondition of DR2, so he answers it first. If he declines, state a one-remote-copy mode explicitly (the PC may evict after one verified server copy, with his yes) and show "single copy" on the storage view.

### F22 — HIGH. Many writers share one nearly full disk, with no order of who gives way
- **Scenario.** On C: (12 GB free): the Library store with its hot blobs, the outbox, the price cache "sized from live free space", upload staging, the OTel collector's disk queue while the server is unreachable, Claude Code transcripts, and Hindsight's embedded database until it moves. The design protects only partition writes ("free-disk check before each write"). Whichever writer runs last wins. If the outbox or the Library's own log append is the one that hits `ENOSPC`, the save he just made is lost.
- **Fix (no invented number).** One rule per machine, read live. Expendable consumers give way first: the price cache (re-fetchable), the telemetry queue and transient blobs shrink when free space falls below what the pending Library work needs (outbox size plus in-flight uploads). Library writes are refused last, with an incident and a plain message. The floor is a Settings value shown beside the measured need.

### F23 — MEDIUM. The server must keep every durable blob for ever
- **Scenario.** AD-10 says the server "holds everything durable", and AD-6 never purges. Uploads, recordings, model weights, Docling page images and run logs grow without bound beside the price files, OpenObserve and Postgres on a 193 GB disk. Partitions can leave the server; durable blobs cannot.
- **Fix.** Let the server evict a durable blob once its bucket copy is verified (the bucket plus the PC or a second bucket count as the two copies) and fetch it on demand. The storage view shows a fill forecast.

### F24 — MEDIUM. The server is now the main copy, but the off-site copy is up to 24 hours old
- **Scenario.** Overnight server workflows land results, the PC sleeps, and the server disk dies at 23:00 → everything since last night's push is gone.
- **Fix.** Push Library objects and refs (small) to the bucket after each commit batch. Keep the nightly push for partitions only.

### F25 — MEDIUM. The monthly restore drill doubles server disk use
- **Scenario.** AD-16's "monthly full rebuild into a scratch root" copies the whole store → on a full server the drill itself causes disk-full.
- **Fix.** Rebuild only the catalog from the existing evidence into a scratch catalog, plus a rolling sample of blobs and partitions verified by hash.

### F26 — MEDIUM. Uploads: resume, leftovers, and where the bytes land
- **Scenario.** (a) "Resumable by offset" with "hashed while written": after a cut, the running sha256 state is gone (Python's `hashlib` state cannot be saved), so the resume must re-read the partial file, and nothing says so. (b) Abandoned partials pile up on a full disk. (c) An upload on the PC lands on the PC's blob store even when the server is reachable, then waits for two remote copies (F21).
- **Fix.** Resume re-hashes the partial file. Partials older than the session and not resumed are deleted (they are not durable blobs). When the server is reachable, the PC streams the upload straight through to the server and keeps no copy.

---

## 4. External connections (checked against 56)

### F27 — CRITICAL. cTrader's refresh logs out every other holder, so a live bot gets cut off
- **Scenario.** 56 §2: a refresh returns a new access **and** refresh token and kills the old pair, and `ProtoOAAccountsTokenInvalidatedEvent` lists "token refreshed" as a reason. In 55, the `connections-health` cron "renews OAuth tokens before they expire" on the connection's home; a read-scope token is replicated to the server; and at hand-over the trade token is sent to a trading server while the PC keeps its own copy. So the PC's routine refresh **logs out the live bot on the trading server mid-trade**. The vault is one-way (PC → server, "newest `updated_at` wins" by wall clock), so a token refreshed on the server is overwritten by the PC's dead one.
- **Evidence.** 55 §4 "Kept healthy" and "A trading server"; engine AD-67; 56 §2, §9.2, §12 Q1; `vault.py` (`VaultStore`: newest `updated_at` wins). No refresh code exists today (`qmx_broker` has none; `qmf-venue` only labels the class).
- **Fix.** One **refresh owner** per grant, named on the connection row. Only the owner holds the refresh token; other holders ask it for the current access token. At hand-over the trading server becomes the owner and the PC deletes its copy, or each machine gets its own grant once a demo test shows two grants can coexist (56 §12 Q1). Add probe P-CTREFRESH.

### F28 — CRITICAL. "Agents never touch money" does not hold on the PC as designed
- **Scenario.** Every chat on the PC gets `Bash` and `PowerShell` (`qma/harness/surface.py` `CLI_BUILTINS`). 55 §4 makes QMX itself obtain a cTrader token with the **trading** scope and store it in the Windows Credential Manager on the same PC, under the same user. A copilot (or a prompt-injected feed item it reads) can run `python -c "import keyring; …"`, read the token and place an order through the public API. 55 §4's "Why this holds the money rule" says a trade-scope credential "lives only on his PC", and that is exactly where the agents with shells run.
- **Evidence.** `surface.py` (Bash and PowerShell in the tool list); 55 §4 "Added" and "Why this holds the money rule"; engine AD-67. Until now, OAuth grants were "operator/node duties outside QMX" (56 §11), so this design is what puts a trading token where the agents are.
- **Fix (simplest).** Never store a trading-scope credential on the PC. The PC holds read scope only. A trading grant is made on the trading server's own consent flow (the redirect lands there), so "assign to trading server" becomes "authorise on that server". If a trading token must ever sit on the PC, it is sealed under a key that needs his interactive confirmation (Windows Hello). Add a probe: a chat's shell cannot read any trade-scope secret.

### F29 — HIGH. The vault's code guard does not catch the names brokers actually use
- **Scenario.** AD-67 says a trade credential "keeps a name the vault never replicates", and `vault.py` says "Broker credentials are never replicable… held by the code". But the code refuses only names with a `broker` segment. `qmx-broker` uses `qmx/ctrader-demo`, `qmx/ctrader-live` and `qmx/crypto`, so **a trading credential is sealed and published to the server**. `qmx/backup-payload-key`, which AD-28 lists as never replicable, is also published.
- **Evidence (ran).** The real `is_replicable` from `8af1a1cd` on Python 3.14: `qmx/ctrader-demo → True`, `qmx/ctrader-live → True`, `qmx/crypto → True`, `qmx/backup-payload-key → True`, `qmx/broker/ctrader → False`. A search of the repo finds no test that calls `is_replicable` with these names.
- **Fix.** Replicate by allow-list only: `qmx/read/*` plus the router's provider rows. Everything else is local by default. Add a test with `qmx-broker`'s own credential names.

### F30 — HIGH. Server-homed connections still need the PC to be awake
- **Scenario.** The code says "**The PC is the vault**": the private key stays on the PC, and the node holds only ciphertext and asks the PC for values over the tailnet (`vault.py` header; `scripts/live/server/e26_vault.py`). Engine AD-28 and 55 say the private key lives in `qmx-vault`'s keyring on Contabo. A Linux server has no Windows vault, and a headless Secret Service is fragile (56 §9.3). After a server restart while the PC sleeps, server downloaders, health checks and Firecrawl feeds have no keys and stop. That breaks ruling 121's "work on the server lands while the PC sleeps".
- **Fix.** Decide the server-side secret store (for example systemd credentials, or the vault private key in a root-only file on the server for replicable entries only), and make the spine and the code say the same thing. Add an incident "keys unavailable on <machine>".

### F31 — HIGH. The relay cannot carry non-model keys, so either keys reach workers or nothing works
- **Scenario.** AD-12: "no key reaches a worker; the relay injects the key into each model call". A cTrader history downloader (protobuf over TLS), CCXT (HMAC-signed requests) and Firecrawl each need the secret **inside the script process**, and an HTTP model relay cannot inject into those. Either the rule is broken quietly (the key goes into the worker's environment), or server downloaders have no credential path at all.
- **Fix.** One **connection gateway** per connection home, inside the host process. It holds the session, the token, the refresh (F27) and the rate limiter (F33), and it serves read operations to workers that present a pass naming the connection. Workers never hold the secret. This one piece also answers F32 and F34.

### F32 — HIGH. cTrader allows one live connection per app, and the design opens several
- **Scenario.** 56 §2: "At most **two connections per app**: one demo, one live." In 55, the PC's copilot reads (`qmx-broker` opens a short TLS session per read), the server's `download-broker`, the health cron and later a trading server would each open their own live connection under the same app → `CONNECTIONS_LIMIT_EXCEEDED` (67), or one connection drops another, possibly the live bot's.
- **Fix.** The gateway of F31: one connection per (app, environment), owned by one machine, and everyone else reads through it. Probe P-CT2CONN on demo first: open a second connection and record what happens to the first.

### F33 — HIGH. Rate limits are not shared across runs, so Binance can ban the server
- **Scenario.** Several downloader and feed runs on the server are separate script processes. CCXT's limiter is per exchange instance (56 §5), so each process paces only itself. Together they exceed Binance's per-IP weight → 429 → if retries ignore `Retry-After`, **HTTP 418: an IP ban from 2 minutes to 3 days** for every Binance job on the server. Also, when the PC copilot and the server share one CCXT key, the second program raises the nonce and causes `InvalidNonce` (56 §5). 55's "its own limit cools the run" has no shared state behind it.
- **Fix.** The gateway (F31) holds one limiter per (provider, key, egress IP) and records "slowed until" from the provider's own signal (`Retry-After`, 418, cTrader 108) on the connection row, where every run checks it. One CCXT key per machine.

### F34 — MEDIUM. The health words cannot say "slowed", "maintenance" or "needs you"
- **Scenario.** cTrader goes down for maintenance at weekends without notice (56 §2) → `connections-health` raises an incident every weekend. A new broker account needs a fresh grant, a Hyperliquid agent key gets pruned, IBKR needs a weekly login: none fits `available | configured | authorized | reachable | healthy`, so his to-dos look like errors (56 §10 pattern 5).
- **Fix.** Keep the five machine words for setup, and add a reading on each connection: `ok | slowed | maintenance | needs_you | down` (56 §8.4). Raise an incident only for `down`. `needs_you` is an inbox task.

### F35 — MEDIUM. The adapter contract has no notion of how each provider signals failure
- **Scenario.** Hyperliquid returns errors **inside HTTP 200** (56 §4), Dukascopy returns empty instead of failing, cTrader uses error code 108, IBKR disconnects after 3 breaches. A generic `http` adapter that judges by status code shows "healthy" while every call fails, and writes error bodies as data. Also, 55's adapter list is a closed enum (`ctrader | mt5 | ccxt | …`); 56 §8.3 recommends an open registry with entry points.
- **Fix.** Adopt 56 §8.2's declaration fields (`auth`, `runs_on`, `limit_signals`, `error_map`, `health_check`, `published_limits`) in the adapter contract. The `http` adapter validates the body against a schema. Make the adapter list a registry.

### F36 — MEDIUM. cTrader history paging over short sessions
- **Scenario.** `qmx-broker` opens a TLS session per read (56 §9.2), so each one-week tick page also pays application and account auth. 23 years at 5 history requests a second, with each request costing three, triples the time, and every reconnect is another chance of hitting F32.
- **Fix.** The downloader uses `qmf-venue`'s long-running connection (heartbeat, pacer, one-week cap already built), through the gateway.

### F37 — LOW. The OAuth loopback redirect must match the registered app
- **Scenario.** The consent page redirects only to a URI registered on the Spotware-approved app (56 §2: the app needs approval first; the code lives one minute). A random loopback port fails.
- **Fix.** One fixed loopback port registered on the app. Show "app not approved yet" as a `needs_you` state.

### F38 — LOW. Clock skew is not handled anywhere
- **Scenario.** Binance rejects requests more than 1 s ahead of its clock (56 §5). Hyperliquid nonces must fall within a time window (56 §4). Run passes are minted with the owner's clock and checked with the verifier's (`passes.py`: `now >= minted.expires_at`, no leeway). Trade times from several machines are compared (54 I-265, not carried into 55).
- **Fix.** Each heartbeat records the machine's NTP offset (shown in the doctor). Turn on CCXT's `adjustForTimeDifference`. Give pass checks a few seconds of leeway.

---

## 5. The server process, capacity, long jobs

### F39 — HIGH. One out-of-memory kill takes down the whole platform
- **Scenario.** On the server, one `qmx_host` process is the Library's main writer, the Hub, the engine and the price door (AD-26, AD-28). Admission reads live free RAM (engine AD-30 amended), so two nodes admitted from the same reading both start; Docling OCR or speech recognition, a big DuckDB read and a tick-month `admit` (the whole month in RAM, F1) are not counted as agent sessions. The kernel's OOM killer picks the largest process, which can be `qmx_host` → Library, door, engine and Hub go down together, remote runs stall, and the PC falls back to its outbox.
- **Fix.** Admission reserves each admitted node's declared memory until its measured RSS replaces the reservation. Extraction, big door reads and downloads run in child processes or containers sized by their declared memory. Lower the host process's OOM score so the kernel kills a worker first.

### F40 — MEDIUM. Long downloads block updates and can outlive their claims
- **Scenario.** A many-hour download node blocks `qmx node update` (the drain waits for running nodes). If heartbeats stall under CPU-bound pyarrow work, the claim expires and a second runner starts the same partition.
- **Fix.** One node per partition (fan-out), each short. The heartbeat runs on its own thread. The door's `commit` refuses a second, different file for a key whose claim is live (F2).

### F41 — LOW. Dedupe keys drift
- **Scenario.** A Docling upgrade changes the extracted text, so its hash no longer matches and the same book is stored twice. `?utm=`, `http` versus `https` and trailing slashes make one article into two feed items.
- **Fix.** Normalise canonical URLs (scheme, host case, trailing slash, tracking parameters). Store `extractor_version` and compare text hashes only within one version.

---

## 6. Monitoring

### F42 — MEDIUM. "Loses nothing" is overstated, and nothing watches the watcher
- **Scenario.** The OTel Collector's sending queue is bounded and drops when full [remembered: the exporter queue has a default size; not re-read today]. On the PC that queue sits on the nearly full disk (F22). If the collector or OpenObserve is down, the internal layer does not say so.
- **Fix.** Say "keeps what the queue holds". Feed the collector's own drop and queue metrics into the data health view, and count the queue as expendable under F22.

### F43 — MEDIUM. Secrets could reach OpenObserve
- **Scenario.** "At each write point the record is also handed to an OpenTelemetry exporter." The design does not say this happens after redaction (engine AD-37). Claude Code's telemetry can carry tool details such as shell commands [remembered]. A key in a log line then leaves the PC.
- **Fix.** Export only after the redaction step. Add a test: a token-shaped value written to a log never reaches the exporter.

### F44 — MEDIUM. The outside agent sees more than it needs
- **Scenario.** The observer token lists "only rows whose approval is `read`". That includes `broker_read` (accounts, balances, positions) and every Library read (his private books, journals with account numbers). An outside Claude Code (a cloud service) diagnosing a stuck feed does not need his balances.
- **Fix.** The observer gets the `ops` and doctor rows, run traces and logs, and the data health read. No broker or Library content rows.

### F45 — LOW. Several new failure signals have no incident path
- **Scenario.** Sync alarms (`Synced.alarms` in `replicate.py`), "keys unavailable" (F30), a connection `slowed` (F33), a stale seal (F7) and collector drops (F42) are not named as incident classes, so an outside agent would not see them.
- **Fix.** Give each one a masked signature (for example `library:sync:<ref>`, `vault:unavailable:<machine>`) under engine AD-10.

---

## 7. The binding stance (design for complexity, no invented limits, no QMX caps, agents can't touch money)

- **Agents can't touch money:** broken on the PC (F28) and by the vault's name guard (F29). Fixing F28 by never storing trade scope on the PC is *less* machinery, not more.
- **No invented limits / no QMX caps:** respected. 55 removes the old constants and adds none. Two places needed a shape where a number was removed: F9 (big reads return handles) and F22 (who gives way on a full disk). Neither is a cap.
- **Needless complexity, worth a second look:**
  - **F46 — LOW.** A collector daemon on the PC adds a process and a disk queue on a full disk. The PC host and the CLI could send OTLP straight to the server's collector over the tailnet and accept a gap while offline: the Library already keeps each run's trace and logs as blobs (AD-69).
  - **F47 — LOW.** Two Dukascopy fetchers kept for good (dukascopy-node plus QMX's own bi5 path "for cross-checks"). After P-DUKA passes, keep one and run the other only as the probe.
  - The connection gateway (F31) **replaces** three separate mechanisms the design would otherwise need (key delivery to workers, refresh ownership, shared rate limits), so it counts as subtraction.

---

## 8. Where 55 contradicts 56 (or the code)

| # | 55 says | 56 or the code says | Finding |
|---|---|---|---|
| C1 | `connections-health` "renews OAuth tokens before expiry" on each home; read tokens replicate to the server; the trade token is copied to a trading server | A cTrader refresh kills the old pair **everywhere**; one machine must own the refresh, or each needs its own grant (56 §2, §9.2, §12 Q1) | F27 |
| C2 | dukascopy-node runs "with its own retries" | Retries are **off by default**; empty responses are not retried without `--retry-on-empty`; candles are one side (bid or ask) per run (56 §7) | F5, F2 |
| C3 | Keys "stay in the operating system's keyring"; read credentials and data keys "replicate to the server through the vault" so server workflows can use them; engine AD-28 puts the vault's private key on Contabo | A Linux server has no Windows vault; headless Secret Service is fragile (56 §9.3). The code makes **the PC** the vault (`vault.py`, `e26_vault.py`) | F30 |
| C4 | Health uses the five machine states | 56 §8.4 proposes `ok / slowed / maintenance / needs you / down`; cTrader has unscheduled weekend maintenance | F34 |
| C5 | Closed adapter list; no failure-signal fields; "the provider's own limit cools the run" | Four different limit signals, including Hyperliquid's errors inside HTTP 200; an open registry with `limit_signals` and `error_map` (56 §8.2, §8.3, §10) | F35, F33 |
| C6 | One cTrader connection per machine and per use (PC reads, server downloader, health, trading server) | At most two connections per app, one demo and one live (56 §2) | F32 |
| C7 | CCXT read keys replicate to the server while the PC uses the same key | "Do not reuse API keys with different software" → `InvalidNonce`; one key per process (56 §5) | F33 |
| C8 | `qmx-broker`'s read path serves downloads and health | Short TLS session per read; a node needs a long-running connection (56 §9.2) | F36 |
| C9 | "Remembered, not verified": cTrader's read-only scope (P-CTSCOPE) | 56 retrieved the two scopes `accounts` (view only) and `trading`. Not a contradiction: P-CTSCOPE can now focus on the demo order test | — |
| C10 | Hyperliquid is absent from the adapter list | 56 covers it (wallet agent keys, nonce window, HTTP-200 errors). Not wrong for now ("more later"), but the contract must allow it (F35) | F35 |

Agreed between them: cTrader needs no Windows (55 homes only MT5 on the PC); order flow exists only for futures and crypto exchanges, and Dukascopy's volume is its own liquidity (55 D-4 matches 56 §6.1); MT5 needs Windows or Wine.

Contradictions with the code and with the design's own text: F1 (`qmf-data` cannot store a tick month), F10 (the sync pulls every blob, against AD-10), F12 (`mirror` accepts any role, against AD-14's alarm), F19 (D-2's premise against 52 §3.2), F29 (the vault guard against AD-28's list), F4 (AD-25 stores `where`, against AD-33), F7 (`seal-roll` against `seal.py` and DEC-0119), F17 (AD-16 rclone against AD-26's single writer).

---

## 9. What is well covered

- **Content addressing everywhere.** Immutable objects, blobs and (with F1 fixed) partitions copy in any direction without conflict. A re-put is idempotent. Corruption is caught by hash on read.
- **Ref ownership with compare-and-swap.** A conflict never picks a side silently, and `merge-conflict` objects carry both sides. Line merge through `git merge-file` was actually run (P-MERGE).
- **The seal enforced at the serving side,** with typed refusals and never an empty answer (`seal.py`, `rooms.py` derive the seal position from the data itself, so a caller cannot under-state a window).
- **Claims** with expiry on one store's clock (`store.claim` computes both `now` and `expires` on the Hub), renewed by heartbeat, so a dead run frees its work.
- **Runs survive the PC sleeping** (AD-14, engine AD-65's forwarding), passes are verified by signature, and a pass without `data_scope` fails closed at the door.
- **No invented numbers.** The old constants are listed and removed, and every new tool version was read live.
- **Deletion leftovers.** The three call sites of the money-word matcher are named precisely, with their tests.
- **The UI contract** (UI-HANDOFF §17) states the failure states he will see: offline saves, conflicts, sealed months, "not on this PC", a fact that cannot be computed.
- **Scenario coverage.** All 30 scenarios and 16 defaults of file 54 have a home (55 §9).

---

## 10. Probes that must pass before build

Each probe runs the real code on scratch roots or demo accounts. A failure is a finding, not a reason to add a limit.

| Probe | Must show | Before | Covers |
|---|---|---|---|
| **P-MDREAD (moved up)** | One real month of EURUSD ticks written by the new partition writer reads back; file size and peak RAM recorded; the same month re-downloaded is a no-op | DR3 (not DR4) | F1, F3 |
| **P-KEY** | Bid and ask m1 for one month, and two parameter sets of one component, land as separate series; the door refuses a different file for an existing key unless it is marked as a correction | DR3 | F2 |
| **P-MARKS** | Appending a month and a daily open-month write leave old results unmarked; a correction to one month marks only results that read that month | DR3 | F4 |
| **P-DUKA (extended)** | Plus an injected empty hour: retried, and the month is not frozen while the gap is unexplained | DR6 | F5 |
| **P-SYNC-DISK** | With `primary = server` and 5 GB of blobs on the server, one PC sync moves only manifests and refs; PC free space unchanged | DR2 | F10, F18 |
| **P-REPLAY** | Kill the connection after the server commits a put; replay from the outbox; no conflict, no duplicate item | DR2 | F11 |
| **P-SPLIT** | Restore the PC's old settings (`primary = pc`) after the flip; the PC refuses to act as primary, and the server's `main` does not move | DR2 | F12, F14 |
| **P-TORN** | Truncate the last line of the ref, edge, annotation and outbox logs, and NUL-fill one; the store opens, quarantines the line and raises an alarm | DR2 | F13 |
| **P-SERVERLOST** | Wipe the scratch server root; the runbook promotes the PC, restores from the bucket and re-pairs | DR2 | F14, F21 |
| **P-DISKFULL** | Fill a scratch PC volume to the floor; the cache and telemetry give way first; a Library save is refused with a clear message, never half-written | DR2, DR7 | F22, F26 |
| **P-CTREFRESH** | On demo: refresh on machine A, then call on machine B; record the result. Then test two grants for one cTrader ID (56 §12 Q1) | DR5 | F27 |
| **P-CT2CONN** | On demo: open a second connection with the same app; record what happens to the first | DR5 | F32 |
| **P-NOTRADE** | A PC chat's shell cannot read any trade-scope secret; `is_replicable` refuses every `qmx-broker` credential name | DR5 | F28, F29 |
| **P-VAULT-AWAY** | Restart the server with the PC off; server downloaders and health still reach their keys (or raise "keys unavailable") | DR5, DR6 | F30, F31 |
| **P-BAN** | Two concurrent Binance and CCXT runs on the server, plus a faked 429 with `Retry-After`: both runs wait on the shared "slowed until"; no 418 | DR6 | F33 |
| **P-OOM** | On the server, start Docling on a 400-page PDF, a big door read and two agent nodes at once; the kernel kills a worker, never `qmx_host` | DR2, DR7 | F39, F9 |
| **P-REDACT** | A token-shaped value in a log never reaches the exporter | DR10 | F43 |
| P-UPL, P-DOCLING, P-HS, P-GPU, P-OO, P-CTSCOPE (from 55 §11) | As 55 states. Add to P-UPL: resume after a cut re-hashes the partial file | as in 55 | F26 |

---

## Counts

| Severity | Count | Findings |
|---|---|---|
| Critical | 4 | F1, F10, F27, F28 |
| High | 16 | F2, F3, F4, F5, F11, F12, F13, F14, F21, F22, F29, F30, F31, F32, F33, F39 |
| Medium | 20 | F6, F7, F8, F9, F15, F16, F17, F18, F19, F23, F24, F25, F26, F34, F35, F36, F40, F42, F43, F44 |
| Low | 7 | F20, F37, F38, F41, F45, F46, F47 |

**How sure each critical is.** F1 was run (pyarrow 25.0.1, same calls as `parquet.py`). F10 is pointed at (`replicate.py` `_copy`). F27 rests on 56's retrieved cTrader docs and has not been run on demo (P-CTREFRESH). F28 is pointed at (`surface.py` `CLI_BUILTINS`; 55 §4), and the shell actually reading the keyring was not run.

Scratch scripts used for the runs: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\2c4e1647-896c-4990-a5d7-dfae3b2256b5\scratchpad\probe57_meta.py` (F1) and the inline `is_replicable` run over `git show 8af1a1cd:qmx-agents/packages/qmx-router/src/qmx_router/vault.py` (F29).
