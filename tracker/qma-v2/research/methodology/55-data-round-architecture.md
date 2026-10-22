# 55 — Data round: the architecture

Date: 2026-10-22. Architecture pass (BMad architecture skill, headless, amend mode) over the data round. Nothing was committed. Writes: this file, the three architecture folders under `tracker/qma-v2/architecture/`, `26-operator-rulings-and-alignment.md` (rulings 120-134) and `UI-HANDOFF.md` (§17).

**Inputs read in full:** `51-data-round-seeds.md` (with §8 and §9, his answers), `54-data-round-funnel.md` (30 scenarios, 16 defaults), `52-data-round-inventory.md`, `53-data-stack-research.md`, `50-backend-packages-and-data-today.md`, rulings in `26`, `33` §0, the three spines, `UI-HANDOFF.md`, `D:\QMX-worktrees\qma-ship\build\RESUME.md`. Code truth: `origin/engine/base` `8af1a1cd` and the deletion branches `build/del1`, `build/del2`, `build/del4`, `build/run1b`, read with `git show` and `git grep`, no checkout.

---

## 0. Plain words first

**What this pass decided, in one paragraph.** Most of the data machinery already exists and is switched off. This design switches it on in a fixed order, adds the two missing doors (data in, data out), and adds three things he asked for that had no design: feeds, external connections (brokers, platforms, data providers) and the two monitoring layers. No new database is added. The Library stays the one place every piece of data is named, found, linked and versioned; big price files sit beside it on the server, with a copy in the cloud bucket, each set listed in the Library by a card.

**The biggest decisions.**
1. **One Library, switched on this week.** Every save goes to the new Library. The old Library file and the four other stores that hold Library-like data are imported and retired; nothing is lost, the old files are kept read-only. The server holds the main copy; the PC keeps a working copy, works offline and catches up.
2. **Price history: one card per series, one file per month.** A downloader writes one unchangeable file per source, instrument, kind and month. The same month always gets the same name, so two downloads never make two copies. Each series has one card in the Library that says what it is, where the files are, how complete it is and how good.
3. **One door for price history, with the lock in the door.** Every reader (the copilot, a workflow, the Lab, the backtester, a remote machine) asks the same door. The door refuses the sealed months and keeps a gap between training and testing months. Nothing can skip it by accident.
4. **The backtester is the tool that matters now.** It reads prices through the door by fingerprint and leaves one kind of result in the Library, linked to the card, the bot version and the idea it tests. The copilot's data and backtest tools are filled from this at start-up.
5. **Anything can come in.** One upload door takes any file of any size, streamed and fingerprinted. Books, papers, pages, videos, screenshots and recordings all become one kind of Library item, a "source", with their text pulled out by a server workflow, page and minute numbers kept.
6. **Feeds and downloaders are scheduled workflows.** A feed is a workflow plus a source definition (an academic site, a blog, MQL5 articles, a news site, a calendar). It runs on the server on a schedule, pulls only what changed, and lands items in the Library. News comes through this one path; the three old calendar fetchers retire. Downloaders (Dukascopy through dukascopy-node, Binance bulk files, CCXT, broker history, paid futures later) are feeds that write price files instead of documents.
7. **External connections are one thing in QMX.** Brokers, trading platforms and data providers are rows in one Connections list in Settings. Each is added once, tested with a real probe, watched by a health check, and shown with its accounts. Keys stay in the operating system's keyring. A broker key that can trade never leaves his PC except by his own click to a trading server; a read-only key may be used by server workflows. Agents read; they never trade.
8. **Version control reaches the agents.** What was built (branches, merges, history, claims) becomes reachable from chats, and text is merged line by line so two agents editing one note both keep their work. A history view shows who changed what, line by line.
9. **Two monitoring layers, one source of events.** QMX's own health and incident views stay in the app. The same events also go out over the standard OpenTelemetry format to OpenObserve on the server, for deep logs and traces, and an outside agent such as Claude Code can look in through a read-only door and a short "how to inspect QMX" skill.
10. **A Lab backend now, without pods.** Projects, "New…" from templates at four levels (quick idea, experiment, study, campaign), pulling Tuesday's run into today's, a data panel, and machine-learning runs on his PC with the data copied there first.
11. **Every Library item has a card and a full page.** Each kind says what its small card shows and what its full page shows; the Library hands both from one read, including the facts the card needs (marks, freshness, where the bytes are).
12. **Deletion leftovers are unblocked by subtraction.** The old money-word checks are removed (three call sites, not two), so the old core, wire and daemon delete together; the old agent libraries go with them.

**What switches on first.** Back up the 10 GB of old ticks to the server; switch every save to the new Library and make the server the main copy; open the price door; fill the copilot's data and backtest tools; then uploads, feeds and connections; then monitoring; then the Lab workspace. Section 10 has the full order.

**What still needs him (section 12).** Two small calls: open a cloud storage bucket for the off-server copy (about $2-3 a month at today's sizes), and allow QMX to remove the old 10 GB from his C: drive once two checked copies exist. Everything else is decided.

---

## 1. What this pass changed

| File | Change |
|---|---|
| `architecture/library-and-data/ARCHITECTURE-SPINE.md` | AD-25 to AD-33 added; AD-1, AD-3, AD-10, AD-12, AD-13, AD-16, AD-17, AD-19 amended in place; conventions, Stack, kinds table, capability map and Deferred updated |
| `architecture/library-and-data/OPEN-DECISIONS.md`, `MIGRATION.md` | OPEN-2 closed (replace the registry room); migration steps 5-8 re-cut as the switch-on order |
| `architecture/workflow-engine/ARCHITECTURE-SPINE.md` | AD-67 to AD-70 added; AD-5, AD-18, AD-28, AD-30, AD-31, AD-59, AD-63, AD-65 amended in place; Stack and Deferred updated |
| `architecture/workflow-engine/HARNESS-REQUESTS.md`, `OPEN-DECISIONS.md`, `SOLUTION-DESIGN.md` | change rows H59-H62; W4 and W5 recorded; §30 (new templates, code changes, acceptance) appended |
| `architecture/lab-and-pods/ARCHITECTURE-SPINE.md` | AD-19 and AD-20 added; AD-5 amended in place; inherited table extended |
| `.memlog.md` in all three | the decisions of this pass, appended |
| `research/methodology/26-operator-rulings-and-alignment.md` | rulings 120-134 (his funnel answers and seeds §8-9) |
| `UI-HANDOFF.md` | §17, the data round's UI landings |

AD ids are stable. Lint: section 13.

---

## 2. Decisions, with blast radius

Each decision names the AD that binds it, what it touches in code, the one fact it is safe because of (with how far that fact was proven: "pointed at" = a real file and line, "ran" = a script ran the real code), the scenarios it serves (S-nn from file 54) and its edge cases.

### D-1. The Library is the one catalog; big price files sit beside it as monthly partitions listed by cards (Library AD-25; ruling 120)

- **Decision.** Every piece of data has a Library item. Price history (ticks, bars, trades, order books, calendars, fills) is stored as Parquet partitions keyed `source / instrument / kind / year / month`, one immutable file per partition named by its fingerprint, in the existing `qmf-data` store. One `dataset` card per series `(source, instrument, kind)` lists its partitions; a new month or a corrected month mints a new card version (`replaces` edge on a correction). The card carries `where` (server, bucket, PC cache, with sizes), `complete_up_to`, a quality report (gaps against the market calendar, spikes, duplicates, drift against the broker's own prices), `licence`, `world`, `redownloadable`. Small tables (a pasted CSV, a journal export) may live inside a Library item; the rule is by shape, not by a size number: anything read by time range is partitions, anything read as a document is an item.
- **Blast radius.** `qmf-data` keeps its store; the change is a rule on the window: downloaders and importers write calendar-month windows only (`qmf/data/partitions.py` puts the window into the fingerprint, which is exactly why fixed months fix "same days, different fingerprints"; pointed at). The `dataset` schema (`qmx_library/kinds/dataset.schema.json`) gains fields; nothing stores cards today, so nothing migrates. The agent tools' `datasets.json` (`qmx_tools/service.py:242-265`) retires; cards are the only list.
- **Safe because:** a partition's fingerprint is a pure function of `(source, instrument, kind, window, bytes)` (pointed at, `partitions.py` header), so a fixed month window is deterministic and a re-download of an unchanged month is a no-op.
- **Scenarios:** S-01, S-03, S-05, S-21, S-23, S-25, S-29. **Edges:** a provider replaces an archived file (Binance says it may): new fingerprint, new card version, `replaces` edge, every result on the old month shows "corrected" (Library AD-22). The current month is partial: it is written as a partition flagged `open`, rewritten daily, and frozen at month end. Weekends and holidays come from the market calendar (crypto uses a 24/7 calendar) and are never gaps.

### D-2. The switch-on: the new Library is the only Library, the server holds the main copy (Library AD-26; rulings 120, 121)

- **Decision.** One switch-over, run on his real home: import `library.db` (filtering the known test junk), compare once, flip every `library_*` row to the new store, keep `library.db` read-only in `migration/retired/`. The other four stores retire the same way: the mini-app `artifacts.db` (imported, then the running app attaches the Library sink so outputs land directly), the engine's stand-alone fake (tests only), QMB's registry projection (reads go through the Library), and the QMF registry room (replaced, not mirrored: the Library is the governed store, and a trading server keeps only a read-only copy of the bot versions he admits; OPEN-2 closed). Then the server becomes the main copy (the procedure of Library AD-19, run this week): on the server the Library service runs inside the one QMX host process, so the server store has one writer; the PC host runs a sync loop (on commit, on a timer, on wake) and a write outbox for the time the server cannot be reached.
- **Blast radius.** `qmx_control/service.py:643-659` (`library_*` rows), `qmx_host/host.py:489-490` (the dual write becomes the only write; on the server the host opens the store and serves the Library routes from the same object), `qmx_hub/server.py` (runs inside the host process on the server instead of alone), `qmx_control/backup.py:18-21` (`library.db` leaves the weekly list; the new store is covered by replication, D-11), `qmx_control/service.py:1243-1270` (`app_runtime()` attaches `LibrarySink`), the harness's `domain.library = control.library` (`qma/harness/harness.py:404`).
- **Safe because:** the importer and the dual write already exist and are proven (LIBM PR 135, LIB1 PR 131), and every save since the mirror went on is already in the new store; the import covers the rest (pointed at).
- **Scenarios:** S-01, S-02, S-11, S-25. **Edges:** a save arrives during the flip (the flip quiesces writes for its duration, MIGRATION step 8); the PC is offline for days (the outbox replays on reconnect; a replay that meets a moved head becomes a `merge-conflict`, never a silent pick); the server disk fills (the host refuses the write with an incident before writing, D-11); his real home has no new-store folder today (the import creates it).

### D-3. Ways in: one upload door, one kind for every outside document (Library AD-27)

- **Decision.** One streaming upload route on the PC host and on the server (`POST /api/library/upload`, chunked, hashed while written, resumable by offset; no size limit of QMX's own, the provider's limits only; the bucket's 5 GiB single-part limit is met by multipart). Every document that enters from outside is one kind, `source`, with `origin: upload | agent | feed | capture | import`, blob slots `original`, `text`, `pages/*`, `transcript`, `frames/*`, and `canonical_url` when it has one. Extraction is a server workflow on Docling alone (books, PDFs, slides, spreadsheets and e-books with page numbers; OCR for images; speech recognition for audio and video without captions); MarkItDown, which file 53 offered as a quick path, is dropped because Docling covers the same formats and YouTube captions already come through `yt-dlp` in the video template; writing `text` and per-page or per-second `derived-from` edges with locators. Search indexes the whole extracted text in chunks (the first-1-MB limit goes). Dedupe: same bytes, same blob; same page, same `canonical_url` as intent key; same book with different bytes, same extracted-text hash.
- **Blast radius.** New routes in `qmx_control/server.py` and on the server host; `qmx_library/store.py` `TEXT_LIMIT` (line 78) and `_index_object` (chunked indexing); `qmx_hub/server.py` `BODY_LIMIT` (line 66, 64 MB) goes and blob moves stream; `source.schema.json` fields; one extraction template. `upload` is not a new kind.
- **Safe because:** blobs are already addressed by sha256 and written once (`store.py` `_write_once`; pointed at), so streaming changes how bytes arrive, not how they are named.
- **Scenarios:** S-06, S-07, S-20, S-26, S-27. **Edges:** a 3 GB recording (streams; never held in memory; probe P-UPL); a scanned PDF (OCR); extraction fails (the source stays, the incident names the step); a key pasted into a document (redaction at put refuses it, Library AD-6); a private book (kept on his server and in the bucket; bucket encryption is OPEN-3, recommendation unchanged); an account number visible in a screenshot (the extracted text is redacted against the account ids in Connections; the pixels are kept, they are his own data on his own machines).

### D-4. Feeds, downloaders and news: scheduled workflows over a source definition (engine AD-68; ruling 131)

- **Decision.** A **feed** is a published workflow made from the `feed` template; its slots are the source definition: `url` or `endpoint`, `method` (`rss | sitemap | page-diff | firecrawl | browser | api | bulk-files`), cadence (a cron trigger on the server by default), `connection` (when the source needs a key or a login), selectors, tags, licence, `lands_as` (`source` items or `partitions`). Its first node is a `monitor` (a cheap check with a hash diff); an unchanged source ends the fire `silent`. New items are claimed by intent key (canonical URL or provider id), so two feeds never fetch one item twice (a card update also claims its series key, so one writer at a time moves a series card); they are saved as `source` items with `origin: feed`, `part-of` the feed's collection, and handed to the extraction workflow. A **downloader** is the same thing with `lands_as: partitions`: it claims each partition key, writes partitions and updates the card. **News is one path:** the economic calendar is a feed landing partitions (`source=forexfactory, kind=calendar`, every revision kept, parsed by `qmf/data/calendar_feed.py`), and headlines are feeds landing sources; the PC scheduled task, the node's recorder and the template's private fetch retire. MQL5 articles, academic sites (arXiv, SSRN and the like), blogs and central-bank pages are feeds. Agent browsers and Firecrawl are methods, chosen per source.
- **Market-data downloaders.** Dukascopy through **dukascopy-node** (MIT, Node 20+, pinned 1.50.0 of 2026-07-24; 1.51.0 is a day old) as the default fetcher, a script node on the server with its own retries and batch pauses; its output enters partitions through the existing `qmf.data.dukascopy` adapter seam (DEC-0013 forbids vendoring its code, not calling it). QMX's own bi5 fetch through the existing stdlib decoder is the second adapter, kept for cross-checks. Probe P-DUKA compares both against the old 10 GB of raw bi5 files for one month before the first big download. Binance public bulk files (spot and USD-M futures: klines, trades, aggTrades, bookDepth, bookTicker, metrics; each file with a checksum) for crypto history; CCXT tops up recent days; broker history from cTrader (5 requests a second, one week of ticks per request, paged) and MT5 (PC only) as `source=<broker>` series to compare with the free data; Databento for real futures only when a strategy needs it (ruling 122). **Order flow:** true traded volume and order books exist for crypto exchanges (Binance trades, aggTrades and bookDepth, free) and for exchange-traded futures (Databento, paid); spot FX has no consolidated volume, and Dukascopy's volume is its own liquidity, labelled so on the card. Order-flow series are partition kinds (`trades`, `book`), so nothing new is needed to store them.
- **Blast radius.** One new template (`feed`) and four downloader templates; `t3-news-calendar-watch` switches to the proper parser; the `recorder/` scheduled task is removed on his PC (a step on his machine he approves); the node's `news_calendar_recorder.py` and `data/bootstrap.py` are the trading-server session's to drop.
- **Safe because:** the engine already has the `monitor` node kind (hash diff, `silent`), cron triggers with one catch-up run after downtime, and claims in the store (pointed at: `qmx_engine/definition/registry.py` `monitor`, `store.py` `claim`); a feed adds no engine machinery.
- **Scenarios:** S-05, S-07, S-24, S-29. **Edges:** the provider throttles (its own limit cools the run, never ours); the server is down through a cadence (one catch-up run); a site changes its layout (extraction yields nothing, the feed's incident names it); a paywalled page (kept as read, marked); the disk fills mid-download (refused before writing, no half partition); two agents start the same month (one claim wins, the other links).

### D-5. One door to price history, with the lock where data is served (Library AD-28; engine AD-31)

- **Decision.** The **market-data door** is a module of the one host process on each machine (no new service) and the only writer of the price store on that machine: downloaders and importers stage finished partition files and call `commit(files)`, which verifies and records them. Reads: `instruments()`, `card(series)`, `read(series or partition fingerprints, from, to, purpose)` and `materialise(fingerprints) -> local paths`. It opens the `qmf-data` store **with** the holdout seal and the split definitions; a read that names no split is exploration and gets every unsealed month; a read that names a split states its `purpose` (`train | validation | test | final_look`) and gets only that segment; the door refuses sealed months unless the purpose is the one journaled final look; split definitions gain a `gap` (bars or a duration) between training and testing, which becomes part of the split fingerprint. A missing partition is fetched by fingerprint: PC cache, then server, then bucket, hash verified. On the server the door also answers remote callers over the tailnet and checks the run pass's new `data_scope` (dataset card ids). QMB reads through it: the door materialises the exact partitions into its cache and hands QMB the `store_root` and fingerprints QMB takes today, so QMB's reader barely changes. The door never materialises sealed partitions into a shared cache; a final look reads into the run's own attempt folder and leaves nothing behind. The agent data tools (`data.instruments`, `data.bars`, `data.features`, `data.calendar`) are filled from the door at start-up.
- **Blast radius.** `qma/harness/harness.py:403` (`DomainContext` gets the door and the backtest binding), `qmx_tools/service.py:242-265` (`from_environment` and `datasets.json` go), `qmf/data/splits.py` (`gap`), `qmx_router/passes.py` (a `data_scope` field; the pass is signed, so an old pass simply lacks it and the door refuses it), `qmb/src/qmb/host/replay.py:143-195` (same interface; the caller passes the door's cache root).
- **Safe because:** `seal.py` already refuses a sealed read with a typed refusal at every read boundary when the seal is passed in (pointed at), so the door's whole job is to always pass it in.
- **Scenarios:** S-04, S-09, S-15, S-16, S-18, S-22, S-23. **Edges:** an agent asks for sealed months (refused with the reason, never an empty answer); a feature window crosses the seal (computed only inside allowed months plus the gap); a remote worker with no `data_scope` (refused before start); DuckDB 2.0 files cannot be read by 1.x (stay on the pinned 1.5.5 until 2.0 is two weeks old and probe P-MDREAD passes, then bump everywhere at once); an agent with a shell reading files directly on the server (possible; sealed partitions sit in no cache the agents' working folders see, and research honesty, not money, is at stake; accepted).

### D-6. Backtests: QMB by fingerprint, one result shape, results in the Library (Library AD-29; engine AD-31; Lab AD-5; ruling 125)

- **Decision.** The backtest tools reach QMB through the engine's `qmb_backtest` operation (on the `qmb` placement, the PC as fallback). The result lands as one `backtest-result` item through one landing step, with `consumed` to the dataset card version, `uses` to the bot version, `tests` to the hypothesis when one is given, and big trade tables as Parquet blobs inside it. QMB's own result files (CT-32) import into this shape; the old Library's `backtest` items map to it (MIGRATION table). This is the agent tool that matters now; the rest of the backend reaches agents through the Lab and mini apps, without a long tool list.
- **Blast radius.** `qmx_tools/service.py:191-230` (agent backtests stop writing the old Library); QMB's run gets a landing step (a script after the run, shaped like `qmx_engine/trace_export.py`); the `backtest` rows in `catalog.py` are rebound.
- **Safe because:** QMB already never fetches and reads only by fingerprint (`qmb/src/qmb/data/policy.py`; pointed at), so pointing it at the door's partitions gives byte-identical input.
- **Scenarios:** S-09, S-10, S-21, S-29. **Edges:** the card's data is corrected later (the result shows "corrected"); the run touches sealed months (only through `qmb.holdout_touch`, journaled, one per family per window); three old result shapes (one survives, the others import).

### D-7. Version control for concurrent agents (Library AD-30)

- **Decision.** Keep what LIB1-LIB4 built (agent branches, drafts, three-way merge, conflict objects, history, as-of reads, claims). Add: (1) **line-by-line text merge**: in the three-way merge, a `text/*` blob slot both sides changed is merged with `git merge-file -p --diff3`; exit 0 lands the merged text, a positive exit (the number of conflicts) mints a `merge-conflict` carrying the marked text; (2) **structural JSON merge** for `application/json` slots, key by key, one conflict entry per clashing key; (3) **history and blame reads**: `history(item)` (who moved which ref when, from the ref log) and `blame(item, slot)` (for text, the version and principal that last changed each line, computed at read from parents and line diffs); (4) chats reach it: the `library` toolset gains `branch`, `merge`, `conflicts`, `resolve`, `history` and `blame` rows over the new store; (5) the engine takes a claim at node start for any node with an intent key, released when its output lands.
- **Blast radius.** `qmx_library/store.py` `_three_way` (the blob branch of `pick`, lines 645-655), the catalog's `library` rows, engine node start (claims). Files agents edit on disk keep engine AD-49 (a git worktree per writer for real repositories).
- **Safe because:** `git merge-file -p --diff3` returns 0 with both edits on a clean merge and the conflict count with diff3 markers otherwise (ran: scratch base, ours and theirs files, git 2.55.0; output in section 11).
- **Scenarios:** S-08, S-14, S-17. **Edges:** both agents change the same line (a conflict, never a silent pick); binary blobs (pick-one, as built); a claim held by a dead run (expires within one heartbeat ttl, Library AD-24); he edits while an agent edits (he is one writer among others); a merged workflow fails validation (it becomes a conflict, Library AD-7).

### D-8. External connections: one registry, one health ladder (engine AD-67; rulings 129, 133)

Section 4 has the full design. In short: one Connections list in Settings, rows of kind `broker | platform | data`, each with an adapter (`ctrader | mt5 | ccxt | dukascopy | binance-vision | databento | firecrawl | http`), environment, accounts (several per connection, several connections per broker, as `qmx-broker` already models), a credential reference in the keyring with a **scope** (`read | trade`), a home machine where it can run, its capabilities and its provider limits. Health uses the five states the engine already uses for machines (`available | configured | authorized | reachable | healthy`); a test is a real probe (for cTrader the existing QMF capability probe); a script workflow keeps them healthy. Agents read through the existing read-only broker tools; nothing in this design submits an order.

- **Blast radius.** `qmx_broker/models.py` (the `Broker` row becomes one connection kind; the adapter list gains `mt5`; `Connection` gains `scope`), `qmx_control/service.py:466-474` (the `brokers` settings section is read once into `connections`), `qmx_router/vault.py` (read-scope credentials and data-provider keys may replicate; trade-scope never), one health template.
- **Safe because:** the broker → connection → account model with keyring references and no credential in any read result already exists and is tested (`qmx_broker/models.py`, `credentials.py`, README; pointed at), so this widens a working shape instead of inventing one.

### D-9. Two monitoring layers from one source of events (engine AD-69; rulings 123, 126)

Section 6. Internal: the inbox, incidents, heartbeats, run cards, the doctor and the `ops` toolset keep reading spans, heartbeat rows, incidents and logs as they do, and gain a data health view (card freshness, failed downloads, connection health, disk). External: the same records are handed, at the point they are written, to an OpenTelemetry exporter; one collector per machine buffers on disk and forwards over the tailnet to OpenObserve on the server. Claude Code chats and Hindsight send their own telemetry to the same collector. An outside agent gets a read-only observer token for QMX's MCP door, OpenObserve's own MCP door, and a runbook skill.

### D-10. Remote work reaches data the same way (engine AD-70)

Section 5. A remote worker gets the Library through the Library server (built), price data through the server's data door (`data_scope` on its pass), model keys through the relay (built), data-provider keys and read-only broker tokens through the vault, and sends telemetry to the server's collector. The runner sets each node's placement and prefers the machine that already holds the data. Burst machines read through the server's door; direct bucket reads wait until the read-speed probe shows the extra hop matters.

### D-11. Storage, backups and real numbers (Library AD-10 and AD-16 amended; engine AD-30 amended)

- **Decision.** The server holds the main Library copy and the price files it has room for; the bucket holds everything, pushed nightly by the server; the PC holds the catalog, manifests, hot blobs and a price cache sized from its live free space. A durable Library blob leaves the PC only after two verified remote copies; a price partition may leave the PC cache at any time (it is always re-fetchable by fingerprint) and leaves the server only after the bucket copy is verified and only if its card says `redownloadable`. One backup plan: PC to server on commit, server to bucket nightly, price files included, with the drills of Library AD-16. Every limit is a provider's own or a default measured on the machines, editable in Settings: server capacity comes from the live readings in the heartbeat (free RAM, measured session size), not from reserved constants. The 6,144 MB overhead, 12,288 MB budget, 2,048 MB attempt, 64 MB body, 1 MB search text, 1,000-bar read and 2 GiB sync-back figures are removed.
- **Blast radius.** `qmx_engine/settings.py:146-150`, admission (engine AD-58), `qmx_hub/server.py:66`, `qmx_library/store.py:78`, `qmx_broker` bar paging, the sync-back cap in SOLUTION-DESIGN.
- **Scenarios:** S-02, S-03, S-25, S-26.

### D-12. Hindsight on the server now (engine AD-18 amended)

Hindsight runs on the server with a system Postgres and pgvector, banks made from its templates, its model calls through the router. The earlier "does not fit" verdict rested on an invented 2 GB line; the server has about 11.3 GB free at idle and Hindsight peaked at about 2.8 GB (PRB-S PR 156). Memories stay QMX records in the Library, so the move is a rebuild, not a migration.

### D-13. Lineage, indicators, journals (Library AD-31, AD-32)

- **Indicators and combinations** are `component` items with `component_type: indicator | combination | feature | filter | labeler`; a combination `uses` the components it combines; versions are item versions. No new kind.
- **Lineage** is written by the templates, never left to a model's choice: every funnel step (pass branch, fail branch, rewrite, domain-expansion cell) writes `variant-of` with a `what_changed` annotation; composites write `merged-from`; units link `uses` to their bot version and risk settings; models link `consumed` to the card versions and partitions, `derived-from` the code version, and carry the seed. One family read returns parent, children, siblings and history (the built `walk`). "Pairs" means both: two variants compared or combined, and the instruments a variant ran on; both are edges.
- **Trade journals** have three layers: fills as partitions (`source=<broker or backtest>`, `account`, `month`); each round trip a `trade` item (record class; the one new kind of this pass) with world `backtest | paper | demo | live | synthetic`; his tags and notes as annotations that never mint a version. A journal is a `collection` per account. Imports from cTrader, MT5 and CCXT dedupe by broker ids; money keeps exact integers and `moneyDigits`.
- **Scenarios:** S-17, S-19, S-23, S-29.

### D-14. The Lab backend now (Lab AD-19, AD-20)

A project is a `collection`; "New…" installs a template at a level; the workspace (open project, layout, pins) is annotations on the project; Tuesday's run enters today's through the engine's `library` node and `@run` and `@library` references in workflow inputs; the data panel reads the door and the card; problems are marks and conflicts; the timeline is history. ML training on the PC is a placement with a GPU slot: the door pulls only the partitions the run needs into the PC cache after a free-space check, the run trains, and the model item records the data fingerprints, code version and seed. Pods are not part of this backend.

### D-15. Mini apps live in the Library and run as plugins (four switches)

Publishing writes a `mini-app` item; the host materialises published packs at start-up; the harness binds `app:<id>` rows; `app_runtime()` attaches the Library sink. An app's private database is backed up with the app and its outputs land in the Library; moving an app to the server pulls it from the Library. Engine AD-19, AD-55 and AD-64 already decide all of this; this pass orders it into the switch-on.

### D-16. Preview and detail view per kind (Library AD-33; ruling 127)

Section 3.

### D-17. Deletion leftovers (engine AD-59 amended)

Section 8.

---

## 3. Card and full page for every kind (the "FIFA card"; Library AD-33)

**The contract.** One read, `view(object_id, level)` with `level: card | page`, serves both. Every answer carries a common header the Library computes, never stores: title, kind and its icon, version label (semver or `v<n>`), state (active or archived), who made it and when, the worst mark with its path (Library AD-22), how it landed (which run or session, which rule), where its bytes are and their size, and freshness where the kind has one. A kind schema declares, beside its existing `preview` and `detail` (Library AD-17): `card.facts` (at most five, by name), `card.thumbnail` (a blob slot, a computed chart spec, or the kind icon), `card.badge`, and `page.tabs` (each a field set, a blob slot, a relation neighbourhood or a computed read, with a renderer). Facts that are computed (marks, freshness, used-in count, trial count, hypothesis status, card completeness) are named in the schema and filled by the Library at read time.

**When each appears (UI contract).** The card appears wherever an item is one among many: lists and shelves, search answers, chat attachment chips, hover, the "used in" neighbourhood, the landed feed, the Lab's explorer. The page appears when he opens one item: from a card, a chip, a link in an explainer, or the Lab inspector's full view. The generic renderer always works; a kind may register a richer component.

| Kind | Card facts (at most five) | Thumbnail | Page tabs |
|---|---|---|---|
| `dataset` (a price series card) | source, instrument, kind (ticks, m1, trades, book, calendar, fills), months covered and `complete_up_to`, quality grade | a coverage strip by month (computed) | Overview, Partitions (month, rows, size, fingerprint, where), Quality (gaps, spikes, drift against the broker), Sample (first rows through the door, sealed months refused), Used in, History |
| `source` (uploads, pages, papers, videos, feed items, screen captures) | origin, media type, author or site, date, pages or duration | first page, video frame or screenshot | Read (text with page or time anchors), Original, Derived (notes and ideas pointing to a page or minute), Used in, History |
| `note` | first line, author, linked items count | none (icon) | Text, Blame (who wrote each line), Links, History |
| `backtest-result` | bot version, dataset and months, headline measure (net R or Sharpe as the procedure reports it), trades, outcome for its hypothesis | equity curve (computed from the trades blob) | Summary, Equity, Trades, Robustness, Data used, Comparable runs, History |
| `trade` | instrument, side, R, holding time, world | entry and exit on a small chart (computed) | Fills, Chart, Notes and tags, Screenshots, Produced by |
| `hypothesis` | statement, status (supported, refuted, open, mixed), tests, family trial count | status ring by regime (computed) | Evidence, Source (with locator), Family, History |
| `component` (indicators, combinations, features, filters, labelers) | type, inputs, version, used by count | a sample plot over a fixed reference window (computed on publish) | Code, Parameters, Uses, Used by, Versions |
| `strategy`, `bot`, `unit` | family, version, last result, markets proven on, state (draft, published, admitted) | equity of its last result | Logic, Results, Family tree, Markets, Versions |
| `model` | task, data fingerprints, metric, size, trained where | training curve | Card (data, code, seed), Metrics, Used by, Versions |
| `workflow` | trigger, last run status, next run, publish rule | the graph, small | Graph, Code, Runs, Tests, Versions |
| `workflow-run` | workflow, status, duration, machine, spend reading | the timeline, small | Timeline, Outputs, Logs, Trace, Explain |
| `mini-app` | operations count, feeds from and to, health, home machine | its first widget | About, Operations, Outputs, Health, Versions |
| `collection` (projects, journals, feed folders) | members count, last change, owner | member mosaic | Members, Activity, History |
| `session` | title, home, models used, last turn | none (icon) | Transcript export, Attached items, What it saw, Produced |
| `merge-conflict` | item, both authors, number of clashes | none | Diff (both sides with base), Resolve |
| every other kind | its schema's `preview.card` fields | icon | its schema's `detail` tabs |

Edge cases: an archived item still shows its card, greyed, with "archived" and the reason; a blob not cached on this machine shows "not on this PC" and fetches on open; a card whose computed fact fails (a corrupt trades blob) shows the fact as unavailable with the reason, never a stale number.

---

## 4. External connections (engine AD-67)

**What a connection is.** Anything outside QMX that holds accounts or data and needs a login or a key: trading platforms and brokers (cTrader first, MT5, crypto exchanges through CCXT, more later) and data providers (Dukascopy, Binance public files, Databento, Firecrawl, news or research APIs). Model providers keep their own registry (the router's provider rows) and machines keep theirs (placements); both already use the same health states, so the three lists read alike.

**Shape (three levels, as `qmx-broker` already has them).**

| Level | Holds | Example |
|---|---|---|
| Provider | `id`, `name`, `kind: trading | data`, `adapter: ctrader | mt5 | ccxt | dukascopy | binance-vision | databento | firecrawl | http`, `exchange` (CCXT) | "IC Markets via cTrader", "Binance", "Dukascopy" |
| Connection (one login or key) | `id`, `environment: demo | live`, `scope: read | trade`, `credential_ref: qmx/<...>` in the OS keyring, `home: pc | contabo | any` (where it can run: MT5 needs his Windows terminal, so `pc`), capabilities found by the test, the provider's own limits as reported, `licence` | "cTrader ID, live, read-only token", "MT5 investor login" |
| Account | `id`, `label`, `broker` (on platforms that reach several brokers), currency, leverage, `enabled`, `permissions: read | propose` | "IC Markets 1234567, USD, live" |

Several brokers and several accounts per broker are the existing model (several connections per provider, several accounts per connection). A data provider has no accounts.

**Added.** Settings, Connections, Add: pick the provider; enter the key through the keyring's secure prompt, or, for cTrader, sign in once on cTrader's own consent page that QMX opens and receives back on a local address, choosing the read or trade scope; QMX stores the tokens in the keyring. QMX then runs the test and lists the accounts it found; he labels and enables them. Nothing about a key is ever written to a settings file, a log, the Library or a model's context.

**Tested.** Each adapter has one `probe()`: for cTrader the existing first-connection probe in `qmf/venue/probe.py` (timestamp unit, daily boundary, bar basis, pip formula, money exponent) plus sign-in and the account list; for MT5 terminal reachable, signed in, symbol info, and `trade_allowed` false for an investor login; for CCXT the server time, balances and the key's own permission flags where the exchange reports them; for a data provider one small fetch. **A credential is labelled `read` only when the probe confirms it cannot trade** (cTrader token scope, MT5 investor login, exchange key permissions); otherwise it is `trade`. Each test result is a `test-report` record in the Library naming the connection.

**Kept healthy.** A `connections-health` script workflow runs on a schedule on each connection's home machine: it walks the five states (`available | configured | authorized | reachable | healthy`), renews OAuth tokens before they expire, and writes a short reading per connection into the host heartbeat (state, last good, latency, token expiry). A failure is an incident per masked signature (`connection:<id>:<code>`) at provider-failure severity (engine AD-17), shown once and resolved by the next passing check.

**Shown.** The Connections list (state chip, accounts with balance and equity read when opened, token expiry, last test, capabilities, which feeds and workflows use it, where it runs); the data health view; Portfolio reads the same accounts.

**Used.**
- *Workflows and feeds* name `connection: <id>` in their inputs or slots. Preflight checks that the connection is `healthy` and that the node runs where the credential may be read; otherwise the fire is `blocked_config` with one item, and no model call.
- *Credentials by scope.* Data-provider keys and confirmed read-only trading credentials may replicate to the server through the vault (engine AD-28), so server downloaders and health checks can use them. Trade-scope credentials never replicate and never appear in any run pass's key scope; they stay on his PC.
- *The copilot* uses the existing read-only broker tools (accounts, positions, quotes, bars, symbol info) over the accounts he enabled. No catalog row submits, changes or cancels an order. `propose_order` stays as built (an unsigned proposal with no signing path).
- *A trading server (later, designed by that session).* He assigns an account to a trading server with one click; the platform then sends that connection's trade-scope credential sealed to the trading server's own key, directly over the tailnet, never through the Library server or the vault. The Connections list shows the account as "on trading server X" with its health from that server's heartbeat. How the trading server trades is the trading-node and unit sessions' design.

**Why this holds the money rule.** Agents read through tools that cannot trade; a trade-scope credential lives only on his PC and, by his click, on a trading server; withdrawals are impossible through cTrader and MT5 and happen only in his own browser (ruling 116).

---

## 5. Remote work and split runs (engine AD-70)

| Who | Library | Price data | Keys | Connections | Telemetry |
|---|---|---|---|---|---|
| The PC (server is the main copy) | its own replica and cache; writes go to the server; outbox when the server is unreachable | its cache; misses fetched from the server, then the bucket, by fingerprint | its keyring | every row; trade-scope only here | local collector, forwards when the server answers |
| A workflow step on the server | the server store, in the same process | the server's door, with the seal | the server's relay and vault copy | data keys and read-only trading credentials from the vault | the server's collector |
| A remote worker or burst machine | the Library server over the tailnet with its run pass (built) | the server's door over the tailnet, checked against the pass's `data_scope` | none; model calls through the central relay | none; a step that needs a connection is placed where the connection lives | OTLP to the server's collector; logs and trace saved as run blobs at the end |
| A split run (data prep on the server, GPU training on the PC, report on the server) | each step on its machine as above | the PC step's partitions are materialised into the PC cache before it starts | as above | as above | one trace across machines (`trace_id = run_id`) |
| An outside agent (Claude Code) | read-only observer token on QMX's MCP door (on the server, so the PC may sleep) | a card's sample through the door, sealed months refused | none | read the Connections list without credentials | OpenObserve's MCP door |
| A trading server (contract only; its design belongs to that session) | fetches admitted bot versions by id; sends journals, fills, decisions, heartbeats and kill events to the Library server within seconds | its own live stream; history through the server's door | none from QMX's vault | the accounts assigned to it | OTLP to the server's collector |

**Placement.** The runner sets each node's placement from its `runs_on` list and the data locality the heartbeat reports (the blob-cache summary seam of engine AD-65), so a data-heavy step runs next to its partitions; today it reads `runs_on` only through an adapter workaround (REM verdict). A placement that lacks the partitions and cannot reach the door waits `placement`, never fails.

---

## 6. Two monitoring layers from one source of events (engine AD-69)

**One source.** Every level already writes four things: spans (the engine ledger and the router journal, engine AD-15), heartbeat rows (engine AD-65), incidents per masked signature (engine AD-10), and JSONL logs. These are the source of truth for both layers; nothing writes twice by hand.

**Internal layer (in the app).** The inbox, incidents, heartbeats, run cards, the doctor, the Machines list and the `ops` toolset keep reading those rows. New: Library heartbeat facts (writer alive, sync lag, outbox length, disk), Lab facts (open projects, kernels, runs), a **data health** view (card freshness and quality, downloads and feeds with their last run and incidents, connections with their states, free disk on the PC and the server, bucket copy age), and PC disk alerts read from live free space.

**External layer (deep, on the server).** At each write point the record is also handed to an OpenTelemetry exporter (spans as traces with GenAI names pinned to one version of the conventions, heartbeat facts as metrics, logs as logs). One OpenTelemetry Collector per machine receives them with a disk-backed queue and forwards over the tailnet to OpenObserve on the server; a sleeping PC or an unreachable server loses nothing. Each Claude Code chat the harness starts gets the telemetry environment (`CLAUDE_CODE_ENABLE_TELEMETRY=1`, OTLP to the local collector; prompt text stays redacted, the CLI's default). Hindsight turns on its own traces. A trading server later sends to the same collector instead of its planned Prometheus, Loki and Grafana. OpenObserve keeps a short window (a Settings value); the Library keeps every run's trace and logs as the permanent record, so the viewer can be rebuilt or swapped.

**The outside agent's door.** Three read-only things: an observer token on QMX's MCP door that lists only rows whose approval is `read` plus one row that saves a diagnosis note on the observer's own ref (shown in the inbox as "an outside agent left a diagnosis"); OpenObserve's MCP door (its free tier, ruling 123); and a runbook skill, `inspect-qmx`, kept as a Library skill and exportable, that names each door, the doctor, the data health view and how to read a run's trace. The token is revocable, expires, and is created by him in Settings.

---

## 7. Feeds (engine AD-68)

**Source definition (the feed template's slots).**

| Slot | Meaning |
|---|---|
| `name`, `tags` | how it shows and what it is about (`item:` tags reach memory, engine AD-18) |
| `method` | `rss`, `sitemap`, `page-diff`, `firecrawl` (crawl or search through his key), `browser` (an agent browser, isolated profile unless he ticked the site), `api`, `bulk-files` |
| `url` or `endpoint`, `selectors` or `query` | where and what |
| `cadence` | a cron trigger, on the server by default |
| `connection` | when the source needs a key or a login (Connections) |
| `lands_as` | `source` items (documents) or `partitions` (tables such as a calendar) |
| `extract` | which extraction to run (text, transcript, OCR), and whether to make notes or ideas from new items (an agent step) |
| `licence` | carried onto every item |

**Examples he named.** MQL5 articles (the `mql5-articles` mini app's collector becomes a feed; its `app.db` finds are imported once); academic research sites (arXiv listing for q-fin, SSRN); trading blogs; central-bank releases; the economic calendar (partitions, every revision kept); headline news. The copilot can create a feed from a sentence ("watch this blog weekly"), which drafts a feed workflow he publishes with one yes (ruling 80).

**What a run does.** monitor (hash diff; unchanged ends `silent`) → list new items → claim each by intent key → fetch → save `source` (`origin: feed`, `part-of` the feed's collection) → extraction workflow → optional agent step that writes notes or hypotheses linked to the exact page or minute. Every item is data, never instructions (engine AD-43).

---

## 8. Deletion leftovers (engine AD-59 amended)

**Finding.** The brief names two call sites of the old core's money-word matcher. There are three live ones in product code (checked on `8af1a1cd` and `build/del4`):

| Call site | What it does | Change |
|---|---|---|
| `qmx_apps/road/check.py:28` (used at line 146) | `qmx app check` refuses a declared operation named like an order | remove the import and the `order_act` branch; keep the wire-name length check |
| `qmx_control/catalog.py:21` (used at line 528) | an app's operations naming an order act raise `CatalogError` | remove the import and the check |
| `qmx_apps/supervisor.py:30` (used at lines 636 and 845) | `check_descriptor`, the old core's money-path refusal for each tool an app's server lists and calls | remove the import and both calls |

Their tests go with them: `qmx-apps/tests/test_app2a.py:251` (the `order_act` case) and `qmx-control/tests/test_app2a_catalog.py:47` (the order-act case). Money-word matching is retired (rulings 116, 118; engine OPEN-DECISIONS W3), so these are removals, not moves; no equivalence test is needed because nothing replaces them. **Safe because:** a grep of `8af1a1cd` finds no other product caller of `qma.core.barriers` outside the old core, daemon and wire except `qmx_agents/guards/money_path.py`, which DEL1 deletes with the old `qmx-agents` package (pointed at; `build/del4` diff).

**Order of PRs.**
1. **DEL3a, unblock (small).** The three removals and two test edits above; drop `qma-core` from the `pyproject.toml` of `qmx-engine`, `qma-harness` and `qmx-apps` (none imports it after this); delete `tools/tests/test_qma_callers.py` with `scripts/dev/qma_callers.py`. Gate: each touched package's tests and type check.
2. **DEL3, the old core, wire and daemon together** (their tests read each other's files): `qmx-agents/packages/qma-core`, `qma-wire`, `qma-daemon`; the importers that only exist for them: `qa/integration/test_qma_*.py`, `qmn/examples/spot_paper_journey.py`, `qmx-agents/examples/native_*_proof.py`, `scoped_tool_request.py`, `scaffold_overview.py`, the `daemon/` folders of `qmx-agents/plugins/*`, `qmx-agents/tests/test_workspace_scaffold.py`, `scripts/probes/qma/name_barrier_diff.py`; the root and `qmx-agents` `pyproject.toml` paths, coverage targets and the `qma-runtime` extra.
3. **The rest of DEL4 in the same PR as DEL3 or right after:** `langchain`, `langgraph`, `deepagents` (only `qma-daemon/pyproject.toml:16-18` after DEL1) and `openai-codex` (`qmx-agents/pyproject.toml:62`, dev group) with `qmx-agents/examples/native_sdk_offline_check.py`; relock.
4. **The rest of DEL2:** delete `qma/serve.py` and its launcher `serve()` at `qma/console.py:797-799` (the host starts through `qmx_host` now); point `qmx_host/host.py:50` (`ProfileName` from the `qma.harness.profiles` shim) and the harness's own imports at `qmx_router` directly and delete the two nine-line RTR0 shims, `qma/harness/profiles.py` and `qma/harness/relay.py`; fix `scripts/live/qma/s21c_egress.py` to read `qmx_router/relay.py`.
5. **RUN1c:** the maintenance loop in `qmx_control/server.py` stops calling `runs_list` and `record_work("jobs", …)`; the weekly backup becomes a script workflow on a cron trigger (one run system, engine AD-57; it also becomes the "one backup plan" of D-11); a maintenance failure is an incident, not a jobs row; delete `runs_list`, `runs_get`, `runs_cancel`, `jobs_list`, `jobs_cancel`, `record_work` and the `runs` and `jobs` work kinds; move their tests to engine runs; repoint or retire the two live lanes (`scripts/live/engine/e57_app_trigger.py:266`, `x13_doors.py:417`).
6. **DEL3b (follow-on, same reason):** the harness's own copy of the word list, `qma/harness/money_words.py` (`named_money_act`), still serves the MCP-server vetting (`qma/harness/tools.py:958`), the engine definition lint (`qmx_engine/definition/lint.py:165`) and a catalog test (`qmx-control/tests/test_catalog.py:91-97`). It is the same retired machinery (W3). Remove it after DEL3 lands; it does not block DEL3.

Merge order with what is stacked today: 164, 166, 167 (chain B), 165 any time, then DEL3a, DEL3 (with DEL4's rest), DEL2's rest, RUN1c, DEL3b. The data packets (section 10) start on the tree after DEL3a, because D-2 and D-5 touch `qmx_control/service.py` and `catalog.py`, which DEL3a also touches.

---

## 9. Coverage

### 9.1 The 30 kept scenarios of file 54

"Packet" is the switch-on step in section 10. Every scenario has a home; three (S-28, S-29 in part, S-14's pods) are owned by other sessions by ruling and are covered here only on the data side.

| # | Scenario | Decided in | Mechanism in one line | Packet |
|---|---|---|---|---|
| S-01 | Every save goes to the new Library | Library AD-26 | import, flip the `library_*` rows, old file read-only, backup follows | DR1 |
| S-02 | Server is home, PC syncs | Library AD-26, AD-19 | Library service inside the server host; PC sync loop and outbox; flip primary | DR2 |
| S-03 | Save the old 10 GB, then free C: | Library AD-25, AD-10 | rclone with checksums to server and bucket; import as monthly partitions with cards; delete on his yes | DR0, DR3 |
| S-04 | One door, lock on the serving side | Library AD-28 | door in each host opens the store with the seal and splits with a gap; `purpose` on every read | DR3 |
| S-05 | Downloaders as server workflows writing cards | engine AD-68, Library AD-25 | feed template with `lands_as: partitions`; claims per partition key | DR6 |
| S-06 | Hand QMX a file | Library AD-27 | streaming upload; `source` with origin; Docling extraction on the server | DR7 |
| S-07 | Agents keep what they find, once | Library AD-27, engine AD-68 | `save_source` template step; canonical URL as intent key; claims | DR7 |
| S-08 | Version control reaches chat agents | Library AD-30 | chat rows for branch, merge, conflicts, resolve, history, blame; line and JSON merge; engine claims | DR8 |
| S-09 | Backtests by fingerprint, one result shape | Library AD-29, engine AD-31 | QMB through the door; one landing step; old shapes import | DR4 |
| S-10 | Tuesday's run in today's | engine AD-5, AD-63; Lab AD-19 | `library` node available; `@run` and `@library` in workflow inputs | DR9 |
| S-11 | Mini apps in the Library, run as plugins | engine AD-55, AD-64 | four switches (publish writes the item, materialise at start, bind `app:` rows, attach the sink) | DR1, DR9 |
| S-12 | One health view at every level | engine AD-69, AD-65 | internal views over the same rows; OTel exporters, collectors, OpenObserve | DR10 |
| S-13 | Outside agent looks in, can only look | engine AD-69 | observer token (read rows plus a diagnosis note), OpenObserve MCP, runbook skill | DR10 |
| S-14 | Lab as a workspace | Lab AD-19 | project collection, New… by level, workspace annotations, panels over existing reads; pods left out | DR13 |
| S-15 | Quick copilot idea that cites its data | Library AD-28, AD-25 | data tools over the door; `consumed` edge to the card version when saved | DR3 |
| S-16 | ML on his PC with the data there | Lab AD-20 | PC placement with a GPU slot; free-space check; partitions materialised by fingerprint; model lineage | DR13 |
| S-17 | Family trees for strategies, indicators, units, models | Library AD-32 | templates write `variant-of` with `what_changed`; `component_type`; one family read | DR12 |
| S-18 | Remote step that needs market data | engine AD-70, Library AD-28 | `data_scope` on the pass; the server's door over the tailnet; placement by locality | DR3, DR14 |
| S-19 | Trade journals in one shape | Library AD-31 | fills as partitions, `trade` items, journal collections, imports per broker | DR12 |
| S-20 | Computer and browser outputs as evidence | Library AD-27 | captures land as `source` with `origin: capture`, linked to the run or session; text redacted against account ids | DR7 |
| S-21 | Bad data found later | Library AD-25, AD-22 | a corrected partition mints a card version with `replaces`; marks computed at read | DR3 |
| S-22 | Synthetic data as its own world | Library AD-28 | generator template reads through the door with `purpose: train` only; card `world: synthetic` with generator, settings, seed | DR4 |
| S-23 | Features and labels as datasets | Library AD-25, AD-32 | derived partitions with `derived-from` the source card and `uses` the component version; computed inside allowed months plus the gap | DR12 |
| S-24 | News and calendar from one fetcher | engine AD-68 | the calendar is a feed landing partitions with every revision; headlines are feeds; three old fetchers retire | DR6 |
| S-25 | Disks: where bytes live, when the PC lets go | Library AD-10, AD-25 | eviction after two verified copies; cache sized from live free space; "where are my bytes" from cards and status | DR2, DR3 |
| S-26 | Real numbers replace invented ones | engine AD-30, Library AD-27 | capacity from live heartbeat readings; body, search and bar limits removed | DR2, DR7 |
| S-27 | New kinds as schema files | Library AD-3, AD-31, AD-33 | one new kind (`trade`); `source` and `component` extended; card and page declared per kind | DR7, DR12 |
| S-28 | Trading servers connect back (data side) | engine AD-67, AD-70 | the data contract in section 5; credential hand-over by his click; design owned by the trading-node session | after the unit work |
| S-29 | Strategy funnel at data scale | Library AD-25, AD-32 | many cards from the downloaders; registry entries as items; trial counts from edges; the QMB redesign belongs to the risk session | DR6, DR12 |
| S-30 | Search and answers at real volume | Library AD-8, AD-27 | probes P-TAINT and P-SRCH on 100,000 items, then page and summarise answers | DR7 |

### 9.2 The 16 defaults of file 54 §12, recorded

| # | Default | Recorded in |
|---|---|---|
| 1 | The outside agent is read-only and writes only its diagnosis note | engine AD-69 |
| 2 | No graph database now; lineage pictures come from the edge table | Library Deferred (graph projection row) |
| 3 | No outside version-control system; line merge through `git merge-file` | Library AD-30 |
| 4 | Price files in fixed monthly partitions named by fingerprint; one fetcher per source | Library AD-25, engine AD-68 |
| 5 | The holdout lock is applied by the serving door, with a train/test gap | Library AD-28 |
| 6 | Synthetic data is its own world and never comes from sealed months | Library AD-28 |
| 7 | Trade journals in three layers: fills as data, trades as items, notes on top | Library AD-31 |
| 8 | Names: "worker", "trading server", "node" only for a workflow step, "Library server" for the Hub when he reads it | Library and engine Consistency Conventions; UI-HANDOFF §17 |
| 9 | "Pairs" means both: compared or combined variants, and instruments run on | Library AD-32 |
| 10 | ML on the PC pulls only the partitions it needs; the cache size comes from real free space | Lab AD-20, Library AD-10 |
| 11 | Every limit is a provider's own or a measured default, editable in Settings | engine AD-30, Library AD-27 |
| 12 | Hindsight on the server with a system Postgres | engine AD-18 |
| 13 | Uploads stream to disk while hashed; no size limit of our own | Library AD-27 |
| 14 | One backup plan: PC to server on commit, server to bucket nightly, price files included | Library AD-16 |
| 15 | One calendar fetcher on the server; the PC task retires | engine AD-68 |
| 16 | Acceptance for data work: the Tier A journeys pass on his real home and the real server | section 10 |

### 9.3 Paths for what "goes nowhere today" (ruling 132)

Every dead end of file 50 (§7 gaps, §2 journeys) gets a path:

| Goes nowhere today (file 50) | Path | Packet |
|---|---|---|
| No downloader for any history | feeds with `lands_as: partitions` (engine AD-68) | DR6 |
| The old 10 GB and the risk-lab CSVs, unread and unbacked | copied with checksums, imported as partitions with cards | DR0, DR3 |
| The calendar recorder's 126 files on his PC, read by nothing | imported once into the calendar series; the task retires | DR6 |
| No upload | the upload door (Library AD-27) | DR7 |
| Agent data tools return nothing | filled from the door at start-up (HARNESS-REQUESTS H59) | DR3 |
| Backtest tools return nothing; QMB's agent door a placeholder | the backtest rows bound to engine AD-31's door; one result shape | DR4 |
| `research.qml_run` returns nothing (no registered bot) | a bot version is a Library item the Lab compiles into a setup (Lab AD-5); the tool binds when the first bot is published | DR4, DR13 |
| `node.state` returns nothing (no node) | the trading-server session's design; the platform side is engine AD-67 and AD-70 | after the unit work |
| The lock is optional and the agent path skips it | the door always opens the store with the seal (Library AD-28) | DR3 |
| Remote runs cannot read market data | `data_scope` and the server's door (engine AD-70) | DR3, DR14 |
| Mini-app outputs never reach the Library | the four switches; `artifacts.db` imported | DR1, DR9 |
| QMB results never reach the Library | one landing step (Library AD-29) | DR4 |
| No central log view; nothing leaves the PC | the two monitoring layers (engine AD-69) | DR10 |
| The node cannot talk to the PC | the data contract in §5; its design belongs to the trading-node session | after the unit work |
| Three news fetchers, one never run | one path: feeds (engine AD-68) | DR6 |
| Two dataset lists | cards only; `datasets.json` retires | DR3 |
| Chat finds kept only if the agent chooses | the `save_source` step in intake templates; captures land automatically | DR7 |
| The research-corpus plugin reads the out-of-scope Stats database | goes with the old daemon's plugin folders (DEL3); ruling 28 keeps Stats out of scope | step 0 |

---

## 10. Switch-on order and migration

**Acceptance for every data packet:** its journeys pass on his real home and the real server, not only in a test home (default 16). Each packet is one PR, built by one Opus builder, one build and one check (operator memory "light verification per PR").

| Step | Packet | What it does | Depends on |
|---|---|---|---|
| 0 | Deletions | the stacked PRs 164, 166, 167, 165, then DEL3a, DEL3 with the rest of DEL4, the rest of DEL2, RUN1c (section 8) | his merges |
| 1 | **DR0, save the old ticks** (a script, no product code) | copy `C:\Users\Mubarak\Documents\QMX\data\raw\external-deep-history` (about 10 GB) and the risk-lab CSVs (252 MB, flagged "2025 ask file incomplete") to the server, and to the bucket once it exists, with rclone checksums; record counts and hashes | nothing; most urgent |
| 2 | **DR1, the Library switch-on on the PC** | import `library.db` (junk filtered) and `artifacts.db`; flip the `library_*` rows; retire the old file read-only; the harness's `domain.library` and the copilot's search use the new store; `app_runtime()` attaches the sink; backup list updated; QMB's registry projection reads through the port | step 0 (DEL3a touches the same files) |
| 3 | **DR2, the server is home** | the Library service inside the server's host process; the PC sync loop and outbox; flip `primary = server` by the MIGRATION step 8 procedure; Hindsight moved to the server with a system Postgres (rebuild from Library rows); capacity from live readings (D-11) | DR1 |
| 4 | **DR3, the price store and the door** | monthly partition rule; card writer and `dataset` fields; the door in each host (seal, splits with a gap, `purpose`); `data_scope` on passes; agent data tools filled at start-up; `datasets.json` retired; the old ticks imported from the server copy as partitions with cards | DR2, DR0 |
| 5 | **DR4, backtests through the door** | QMB reads through the door; one landing step for `backtest-result`; old shapes imported; backtest tools bound; synthetic-data template | DR3 |
| 6 | **DR5, Connections** | the `connections` registry (brokers and data providers), scopes, tests (cTrader probe, CCXT, MT5 adapter on the PC), the health workflow, readings in the heartbeat; the `brokers` section read once into it | DR2 |
| 7 | **DR6, downloaders and feeds** | the `feed` template; Dukascopy (dukascopy-node, after probe P-DUKA), Binance bulk, CCXT top-up, broker history; the calendar feed; old fetchers retired | DR3, DR5 |
| 8 | **DR7, ways in** | upload door, `source` fields, Docling extraction workflow, chunked whole-text search, body and text limits removed, `save_source` step, captures | DR2 |
| 9 | **DR8, version control reaches agents** | line and JSON merge, history and blame, chat rows, engine claims at node start | DR1 |
| 10 | **DR9, workflows read the Library** | the `library` node switched on; `@` references in workflow inputs; the mini-app switches | DR1 |
| 11 | **DR10, monitoring** | OTel at the write points, a collector per machine, OpenObserve on the server, CLI and Hindsight telemetry, Library and Lab heartbeat facts, the data health rows, observer token and runbook skill | DR2 |
| 12 | **DR11, real numbers sweep** | any invented constant left after DR2 and DR7 | DR2, DR7 |
| 13 | **DR12, kinds and lineage** | `trade` kind and journal imports; `component_type`; funnel templates write edges; card and page declarations for every kind | DR1 |
| 14 | **DR13, the Lab workspace and ML on the PC** | projects, New… by level, workspace state, Tuesday's run, data panel, GPU placement and the training template | DR3, DR9, DR12 |
| 15 | **DR14, placement by data locality** | the runner sets placement from `runs_on` and locality; remote reads through the server's door | DR3, DR10 |

Steps 6 to 11 may run in any order once their dependency lands; the table order is the recommendation. Migration safety (MIGRATION.md, unchanged law): back up first, import into a distinct destination, verify counts and hashes, then flip; old stores are retired read-only, never deleted.

---

## 11. Probes (each measures; none sets a limit)

| Probe | What it measures | Before |
|---|---|---|
| P-DUKA | dukascopy-node 1.50.0 output vs QMX's own bi5 fetch and decoder vs the old raw bi5 files, one month of EURUSD ticks: row count, first and last tick, price equality, gaps | the first big Dukascopy download |
| P-MDREAD | the door's read time for one month of ticks and 23 years of one-minute bars: PC cache, server disk, the server's door from the PC over the tailnet, a partition fetched from the bucket; DuckDB 1.5.5 vs 2.0 | DR4; the DuckDB bump; direct bucket reads for burst machines |
| P-UPL | a 3 GB file through the PC upload door and the server stream: peak memory flat, resume after a cut | DR7 ships |
| P-DOCLING | a 400-page PDF and one hour of audio on the server's CPU: time and peak memory | DR7 ships |
| P-OO | OpenObserve memory and disk per day on the server under a day of QMX telemetry | DR10 ships |
| P-HS | Hindsight 1.1 with a system Postgres on the server: memory at idle and in a retain burst at the default worker slots; recall parity with the PC | DR2's Hindsight move |
| P-CTSCOPE | a cTrader token granted the read scope cannot place an order on a demo account; an MT5 investor login reports `trade_allowed` false; a read-only exchange key reports no trade permission | DR5 labels any credential `read` |
| P-GPU | a small model trained on the PC's Quadro T1000 from cached partitions: time, GPU memory, disk used | DR13 ships |
| P-TAINT, P-SRCH (exist) | marks walk and search answer size on 100,000 items | S-30 paging work |
| P-LAT (exists) | Library screens over the tailnet with the PC as replica and cache | DR2 |
| P-MERGE (ran) | `git merge-file -p --diff3` exit codes on a clean and a clashing edit | done, below |

P-MERGE, run on this PC with git 2.55.0.windows.2 against three scratch files (base `stop: 20 pips / exit: 2R`, ours changed the stop, theirs changed the exit): clean merge printed both changes and exited 0; with theirs changing the same stop line it printed diff3 markers (`<<<<<<< ours`, `||||||| base`, `=======`, `>>>>>>> theirs`) and exited 1. That is the behaviour Library AD-30 relies on.

---

## 12. What still needs him (plain words)

1. **A cloud copy for his data.** QMX should keep a second copy of everything off the server, in a storage bucket. Recommended: a Cloudflare R2 bucket (the first 10 GB are free; about $2-3 a month at today's sizes; downloads are free). This needs his own Cloudflare account. If he says no, the server is the only copy outside his PC. *Recommended: yes, R2.*
2. **Free his C: drive.** May QMX remove the old 10 GB of price history from his C: drive once two checked copies exist (one on the server, one in the bucket)? Nothing is removed before both copies are checked by fingerprint. *Recommended: yes.* (He did not answer this one in the funnel.)

Steps that are his to do, not decisions: sign up for OpenObserve's free tier when monitoring is installed (he said the free tier is fine); sign in once on cTrader's own page when he adds his cTrader connection; approve removing the old calendar task on his PC.

---

## 13. Reviewer gate and lint

The skill's gate was run inline (the brief allows no sub-agents): the deterministic lint, a rubric walk against the good-spine checklist, the currency lens and the adversary lens. Lint, run with `python -I C:/Users/Mubarak/Desktop/QMX/.claude/skills/bmad-architecture/scripts/lint_spine.py --workspace <dir>` after every edit: **0 findings on all three spines** (library-and-data, workflow-engine, lab-and-pods). The review is in `architecture/library-and-data/reviews/review-2026-10-22-data-round.md`; its fixes are applied:

- **Adversary, applied.** (1) Two downloaders, or a downloader and an importer, could each obey AD-25 and both move one series card: a card update now claims the series key. (2) A script process and the host could both write the price store's metadata: the door is now the store's only writer, through `commit(files)`. (3) A copilot read with no split and a Lab read with a split could disagree on what "purpose" means: a read without a split is exploration over every unsealed month; a read with a split gets only that segment. (4) A workflow output typed `source` could land as an `artifact` in one template and as a `source` in another: it always lands as a `source`. (5) Derived series had no key rule: `source = derived`, `kind = <component>-v<version>`. (6) A feed's server home could read as breaking "local by default": the template only suggests the server because the data lives there; he can move it. (7) The Lab's workspace annotation needed the `collection` schema to accept it: stated.
- **Currency, applied.** Every new pin was read from its registry on 2026-10-22: dukascopy-node 1.50.0 (npm; 1.51.0 published 2026-10-21), DuckDB 2.0.0 (PyPI, 2026-10-21; the code pins 1.5.5), Docling 2.134.0 (PyPI), MetaTrader5 5.0.6231 (PyPI), OpenTelemetry Collector 0.162.0 and OpenObserve 1.0.4 (GitHub releases), Hindsight 1.1.0 (PyPI `hindsight-api`), Node.js 24.21.0 LTS (nodejs.org), the Binance public-data folders (bookDepth, bookTicker, trades, aggTrades listed live), and dukascopy-node's CLI options (its config page). Two facts stay **remembered, not verified**, and each has a probe before anything relies on it: cTrader's read-only OAuth scope and the MT5 investor login's `trade_allowed` (P-CTSCOPE).
- **Rubric, applied.** The operational envelope is covered (the server runs the host with the Library service, OpenObserve, the collector, Hindsight with Postgres, and Node for the downloader; the bucket; health and incidents). One engine rule (AD-28's "broker credentials never replicable") was refined in place rather than contradicted, and the Library server's name-based refusal still holds (read credentials live under `qmx/read/*`).

**Conflicts with prior decisions, surfaced:** engine AD-28 and Library AD-12 forbade any broker credential on a server; engine AD-67 allows a credential its probe proves read-only (it cannot move money, ruling 116). Engine AD-30's "4 sessions, then 2 with Hindsight" came from invented constants and no longer binds. Library OPEN-2's recommendation (mirror) is reversed to replace by ruling 120.

---

## 14. Sources

- His words: `51-data-round-seeds.md` (§1-§9), rulings in `26-operator-rulings-and-alignment.md` (1-134), `33-state-of-play.md` §0.
- Studies: `50`, `52`, `53`, `54` (scenarios S-01 to S-30, defaults, tensions, questions).
- Architectures amended: `architecture/library-and-data/`, `architecture/workflow-engine/`, `architecture/lab-and-pods/`.
- Code: `origin/engine/base` `8af1a1cd` (`qmx_library/store.py`, `kinds/dataset.schema.json`, `qmx_hub/server.py`, `qmx_control/service.py`, `catalog.py`, `backup.py`, `qmx_host/host.py`, `qma/harness/harness.py`, `qmx_router/passes.py`, `qmx_remote/models.py`, `qmx_engine/definition/registry.py`, `settings.py`, `qmx_broker/*`, `qmf/data/partitions.py`, `dukascopy.py`, `seal.py`, `ingest.py`, `qmf/venue/probe.py`, `capabilities.py`, `qmx_apps/road/check.py`, `supervisor.py`); deletion branches `build/del1`, `build/del2`, `build/del4`, `build/run1b`; `D:\QMX-worktrees\qma-ship\build\RESUME.md` and `BACKLOG.md` (lines 65-78, 258-267).
- Web, 2026-10-22: dukascopy-node.app/config/cli; registry.npmjs.org/dukascopy-node; the data.binance.vision listing; pypi.org (duckdb, docling, MetaTrader5, hindsight-api, ccxt); GitHub releases (openobserve, opentelemetry-collector-releases); nodejs.org/dist/index.json.
- Skills read: `bmad-architecture` (SKILL, headless, reviewer gate), `codebase-design`, `domain-modeling`, `blast-radius`, `principle-subtract-before-you-add`.
