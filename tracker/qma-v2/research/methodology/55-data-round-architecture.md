# 55 — Data round: the architecture

Date: 2026-10-22. Architecture pass (BMad architecture skill, headless, amend mode) over the data round. Nothing was committed. Writes: this file, the three architecture folders under `tracker/qma-v2/architecture/`, `26-operator-rulings-and-alignment.md` (rulings 120-134) and `UI-HANDOFF.md` (§17).

**Inputs read in full:** `51-data-round-seeds.md` (with §8 and §9, his answers), `54-data-round-funnel.md` (30 scenarios, 16 defaults), `52-data-round-inventory.md`, `53-data-stack-research.md`, `50-backend-packages-and-data-today.md`, rulings in `26`, `33` §0, the three spines, `UI-HANDOFF.md`, `D:\QMX-worktrees\qma-ship\build\RESUME.md`. Code truth: `origin/engine/base` `8af1a1cd` and the deletion branches `build/del1`, `build/del2`, `build/del4`, `build/run1b`, read with `git show` and `git grep`, no checkout.

---

## 0. Plain words first

**What this pass decided, in one paragraph.** Most of the data machinery already exists and is switched off. This design switches it on in a fixed order, adds the two missing doors (data in, data out), and adds three things he asked for that had no design: feeds, external connections (brokers, platforms, data providers) and the two monitoring layers. No new database is added. The Library stays the one place every piece of data is named, found, linked and versioned; big price files sit beside it on the server, with a copy in the cloud bucket, each set listed in the Library by a card.

**The biggest decisions.**
1. **One Library, switched on this week.** Every save goes to the new Library. The old Library file and the four other stores that hold Library-like data are imported and retired; nothing is lost, the old files are kept read-only. The server holds the main copy; the PC keeps a working copy, works offline and catches up.
2. **Price history: one card per series, one file per month.** A downloader writes one unchangeable file per source, instrument (or account), kind, price side and month, once that month is complete; the current month is one file replaced as it grows. The same month always gets the same name, so two downloads never make two copies. Each series has one card in the Library that says what it is, where the files are, how complete it is and how good.
3. **One door for price history, with the lock in the door.** Every reader (the copilot, a workflow, the Lab, the backtester, a remote machine) asks the same door. The door refuses the sealed months and keeps a gap between training and testing months. Nothing can skip it by accident.
4. **The backtester is the tool that matters now.** It reads prices through the door by fingerprint and leaves one kind of result in the Library, linked to the card, the bot version and the idea it tests. The copilot's data and backtest tools are filled from this at start-up.
5. **Anything can come in.** One upload door takes any file of any size, streamed and fingerprinted. Books, papers, pages, videos, screenshots and recordings all become one kind of Library item, a "source", with their text pulled out by a server workflow, page and minute numbers kept.
6. **Feeds and downloaders are scheduled workflows.** A feed is a workflow plus a source definition (an academic site, a blog, MQL5 articles, a news site, a calendar). It runs on the server on a schedule, pulls only what changed, and lands items in the Library. News comes through this one path; the three old calendar fetchers retire. Downloaders (Dukascopy through dukascopy-node, Binance bulk files, CCXT, broker history, paid futures later) are feeds that write price files instead of documents.
7. **External connections are one thing in QMX.** Brokers, trading platforms and data providers are rows in one Connections list in Settings. Each is added once, tested with a real probe, watched by a health check, and shown with its accounts. Keys stay in each machine's own key store. A broker key that can trade live money is never kept on his PC or his server: he enters it on a trading server when he sets one up (ruling 135). His PC and server hold read-only keys and keys that can trade only demo accounts, and each sign-in lives on one machine, which alone keeps and refreshes it. Agents read; they never trade.
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

- **Decision.** Every piece of data has a Library item. Price history (ticks, bars, trades, order books, calendars, fills) is stored as Parquet partitions keyed `source / subject / kind / variant / year / month` (subject: the instrument, the account or `-`; variant: the price side, the parameter fingerprint of a derived series, or `-`), one immutable file per frozen month named by its streamed fingerprint, written by a new typed-column writer in `qmf-data` (57 F1: the existing engine cannot read back a month of ticks). One `dataset` card per series `(source, subject, kind, variant)` lists its frozen partitions; a newly frozen month or a corrected month mints a new card version (a correction is listed in the card's `replaced`). Where the bytes are, `complete_up_to` and freshness are computed at read (Library AD-33); the card carries a quality report (gaps against the market calendar, spikes, duplicates, drift against the broker's own prices), `licence`, `world`, `redownloadable`. Small tables (a pasted CSV, a journal export) may live inside a Library item; the rule is by shape, not by a size number: anything read by time range is partitions, anything read as a document is an item.
- **Blast radius.** `qmf-data` gains a second columnar writer for price partitions (typed columns, compressed, rows streamed in row groups, no copy of the rows in the file metadata) beside the existing engine, which embeds canonical JSON in the metadata and keeps serving small evidence artifacts; downloaders and importers write calendar-month windows only. The `dataset` schema (`qmx_library/kinds/dataset.schema.json`) gains fields; nothing stores cards today, so nothing migrates. The agent tools' `datasets.json` (`qmx_tools/service.py:242-265`) retires; cards are the only list.
- **Safe because:** a partition's fingerprint is sha256 over a pinned logical encoding of its key and its time-ordered rows, so a fixed month is deterministic and a re-download of an unchanged month is a no-op; probe P-MDREAD proves write, read-back and the no-op on one real month of ticks before anything is imported (57 F1 ran the old engine and it failed to read back 1.1 million rows).
- **Scenarios:** S-01, S-03, S-05, S-21, S-23, S-25, S-29. **Edges:** a provider replaces an archived file (Binance says it may): new fingerprint, new card version, the old fingerprint listed in `replaced`, and only results that read that month show "corrected" (Library AD-22). The current month is one file under a fixed open key, replaced as it grows and never archived; it freezes by its kind's rule (prices by the gap check, provider files by their checksums, fills and calendars at month end plus the provider's settlement delay), and a month whose gaps one re-fetch cannot fill freezes with them recorded, with no click from him (fix-check 58, N6, N7). Weekends and holidays come from the market calendar (crypto uses a 24/7 calendar) and are never gaps.

### D-2. The switch-on: the new Library is the only Library, the server holds the main copy (Library AD-26; rulings 120, 121)

- **Decision.** One switch-over, run on his real home: import `library.db` (filtering the known test junk), compare once, flip every `library_*` row to the new store, keep `library.db` read-only in `migration/retired/`. The other four stores retire the same way: the mini-app `artifacts.db` (imported, then the running app attaches the Library sink so outputs land directly), the engine's stand-alone fake (tests only), QMB's registry projection (reads go through the Library), and the QMF registry room (replaced, not mirrored: the Library is the governed store, and a trading server keeps only a read-only copy of the bot versions he admits; OPEN-2 closed). Then the server becomes the main copy (the procedure of Library AD-19, run this week): on the server the Library service runs inside the one QMX host process, so the server store has one writer; the PC host runs a selective sync loop (ref moves, manifests, edges and text slots since its last seen sequence; other blobs only when opened, as cache copies; fix-check 58, N1, N3) and a write outbox, whose replays are idempotent, for the time the server cannot be reached.
- **Blast radius.** `qmx_control/service.py:643-659` (`library_*` rows), `qmx_host/host.py:489-490` (the dual write becomes the only write; on the server the host opens the store and serves the Library routes from the same object), `qmx_hub/server.py` (runs inside the host process on the server instead of alone), `qmx_control/backup.py:18-21` (`library.db` leaves the weekly list; the new store is covered by replication, D-11), `qmx_control/service.py:1243-1270` (`app_runtime()` attaches `LibrarySink`), the harness's `domain.library = control.library` (`qma/harness/harness.py:404`).
- **Safe because:** the importer and the dual write already exist and are proven in tests (LIBM PR 135, LIB1 PR 131). His real home has no new-store folder (the mirror never ran there, 52 §3), so the switch-over first runs on a copy of his real home in a scratch root, counts and hashes compared (probe P-REHEARSE; 57 F19).
- **Scenarios:** S-01, S-02, S-11, S-25. **Edges:** a save arrives during the flip (the flip quiesces writes for its duration, MIGRATION step 8); the PC is offline for days (the outbox replays on reconnect; a replay of a save the server already applied is a success, and only a replay that meets someone else's move becomes a `merge-conflict`, never a silent pick); the server disk fills (the host refuses the write with an incident before writing, D-11); his real home has no new-store folder today (the import creates it).

### D-3. Ways in: one upload door, one kind for every outside document (Library AD-27)

- **Decision.** One streaming upload route on the PC host and on the server (`POST /api/library/upload`, chunked, hashed while written, resumable by offset; no size limit of QMX's own, the provider's limits only; the bucket's 5 GiB single-part limit is met by multipart). Every document that enters from outside is one kind, `source`, with `origin: upload | agent | feed | capture | import`, blob slots `original`, `text`, `pages/*`, `transcript`, `frames/*`, and `canonical_url` when it has one. Extraction is a server workflow on Docling alone (books, PDFs, slides, spreadsheets and e-books with page numbers; OCR for images; speech recognition for audio and video without captions); MarkItDown, which file 53 offered as a quick path, is dropped because Docling covers the same formats and YouTube captions already come through `yt-dlp` in the video template; writing `text` and per-page or per-second `derived-from` edges with locators. Search indexes the whole extracted text in chunks (the first-1-MB limit goes). Dedupe: same bytes, same blob; same page, same `canonical_url` as intent key; same book with different bytes, same extracted-text hash.
- **Blast radius.** New routes in `qmx_control/server.py` and on the server host; `qmx_library/store.py` `TEXT_LIMIT` (line 78) and `_index_object` (chunked indexing); `qmx_hub/server.py` `BODY_LIMIT` (line 66, 64 MB) goes and blob moves stream; `source.schema.json` fields; one extraction template. `upload` is not a new kind.
- **Safe because:** blobs are already addressed by sha256 and written once (`store.py` `_write_once`; pointed at), so streaming changes how bytes arrive, not how they are named.
- **Scenarios:** S-06, S-07, S-20, S-26, S-27. **Edges:** a 3 GB recording (streams; never held in memory; probe P-UPL); a scanned PDF (OCR); extraction fails (the source stays, the incident names the step); a key pasted into a document (redaction at put refuses it, Library AD-6); a private book (kept on his server and in the bucket; bucket encryption is OPEN-3, recommendation unchanged); an account number visible in a screenshot (the extracted text is redacted against the account ids in Connections; the pixels are kept, they are his own data on his own machines).

### D-4. Feeds, downloaders and news: scheduled workflows over a source definition (engine AD-68; ruling 131)

- **Decision.** A **feed** is a published workflow made from the `feed` template; its slots are the source definition: `url` or `endpoint`, `method` (`rss | sitemap | page-diff | firecrawl | browser | api | bulk-files`), cadence (a cron trigger on the server by default), `connection` (when the source needs a key or a login), selectors, tags, licence, `lands_as` (`source` items or `partitions`). Its first node is a `monitor` (a cheap check with a hash diff); an unchanged source ends the fire `silent`. New items are claimed by intent key (canonical URL or provider id), so two feeds never fetch one item twice (a card update also claims its series key, so one writer at a time moves a series card); they are saved as `source` items with `origin: feed`, `part-of` the feed's collection, and handed to the extraction workflow. A **downloader** is the same thing with `lands_as: partitions`: it claims each partition key, writes partitions and updates the card. **News is one path:** the economic calendar is a feed landing partitions (`source=forexfactory, kind=calendar`, every revision kept, parsed by `qmf/data/calendar_feed.py`), and headlines are feeds landing sources; the PC scheduled task, the node's recorder and the template's private fetch retire. MQL5 articles, academic sites (arXiv, SSRN and the like), blogs and central-bank pages are feeds. Agent browsers and Firecrawl are methods, chosen per source.
- **Market-data downloaders.** Dukascopy through **dukascopy-node** (MIT, Node 20+, pinned 1.50.0 of 2026-07-24; 1.51.0 is a day old) as the default fetcher, a script node on the server run with `--retries` and `--retry-on-empty` (both off by default, 56 §7) and its batch pauses, one price side per run; its output enters partitions through the existing `qmf.data.dukascopy` adapter seam (DEC-0013 forbids vendoring its code, not calling it). QMX's own bi5 fetch through the existing stdlib decoder serves only probe P-DUKA's cross-check; once the probe passes, dukascopy-node is the one fetcher. Probe P-DUKA compares both against the old 10 GB of raw bi5 files for one month before the first big download. Binance public bulk files (spot and USD-M futures: klines, trades, aggTrades, bookDepth, bookTicker, metrics; each file with a checksum) for crypto history; CCXT tops up recent days; broker history from cTrader (5 requests a second, one week of ticks per request, paged, through the home host's long-running `qmf-venue` session) and MT5 (PC only) as `source=<broker>` series to compare with the free data; Databento for real futures only when a strategy needs it (ruling 122). **Order flow:** true traded volume and order books exist for crypto exchanges (Binance trades, aggTrades and bookDepth, free) and for exchange-traded futures (Databento, paid); spot FX has no consolidated volume, and Dukascopy's volume is its own liquidity, labelled so on the card. Order-flow series are partition kinds (`trades`, `book`), so nothing new is needed to store them.
- **Blast radius.** One new template (`feed`) and four downloader templates; `t3-news-calendar-watch` switches to the proper parser; the `recorder/` scheduled task is removed on his PC (a step on his machine he approves); the node's `news_calendar_recorder.py` and `data/bootstrap.py` are the trading-server session's to drop.
- **Safe because:** the engine already has the `monitor` node kind (hash diff, `silent`), cron triggers with one catch-up run after downtime, and claims in the store (pointed at: `qmx_engine/definition/registry.py` `monitor`, `store.py` `claim`); a feed adds no engine machinery.
- **Scenarios:** S-05, S-07, S-24, S-29. **Edges:** the provider throttles (its own signal sets the connection's shared `slowed_until`, which every run on that machine waits on; never a limit of ours); the server is down through a cadence (one catch-up run); a site changes its layout (extraction yields nothing, the feed's incident names it); a paywalled page (kept as read, marked); the disk fills mid-download (refused before writing, no half partition); two agents start the same month (one claim wins, the other links).

### D-5. One door to price history, with the lock where data is served (Library AD-28; engine AD-31)

- **Decision.** The **market-data door** is a module of the one host process on each machine (no new service) and the only writer of the price store on that machine: downloaders and importers stage finished partition files and call `commit(files)`, which verifies and records them. Reads: `instruments()`, `card(series)`, `read(series or partition fingerprints, from, to, purpose)` and `materialise(fingerprints) -> local paths`. It opens the `qmf-data` store **with** the holdout seal and the split definitions; a read that names no split is exploration and gets every unsealed month; a read that names a split states its `purpose` (`train | validation | test | final_look`) and gets only that segment; the door refuses sealed months unless the purpose is the one journaled final look; split definitions gain a `gap` (bars or a duration) between training and testing, which becomes part of the split fingerprint. A missing partition is fetched by fingerprint: PC cache, then server, then bucket, hash verified. On the server the door also answers remote callers over the tailnet and checks the run pass's new `data_scope` (dataset card ids). QMB reads through it: the door materialises the exact partitions into its cache and hands QMB their paths and fingerprints. *Fix-check (58), N2:* this is a real change to QMB, not a small one. QMB's replay reader today reads CT-10 archive receipts from a QMF EvidenceStore and pairs bid and ask inside them; it gains a second entry point that reads the typed partitions (verifying fingerprints, world, seal and split as before) and builds quote pairs from tick rows or from a bid and an ask bar series that `materialise` returns as a pair. The door never materialises sealed partitions into a shared cache; a final look reads into the run's own attempt folder and leaves nothing behind. The agent data tools (`data.instruments`, `data.bars`, `data.features`, `data.calendar`) are filled from the door at start-up.
- **Blast radius.** `qma/harness/harness.py:403` (`DomainContext` gets the door and the backtest binding), `qmx_tools/service.py:242-265` (`from_environment` and `datasets.json` go), `qmf/data/splits.py` (`gap`), `qmx_router/passes.py` (a `data_scope` field; the pass is signed, so an old pass simply lacks it and the door refuses it), `qmb/src/qmb/host/replay.py:143-195` (a second entry point for typed partitions beside `read_recorded_replay_source`, in DR4's blast radius; fix-check 58, N2).
- **Safe because:** `seal.py` already refuses a sealed read with a typed refusal at every read boundary when the seal is passed in (pointed at), so the door's whole job is to always pass it in.
- **Scenarios:** S-04, S-09, S-15, S-16, S-18, S-22, S-23. **Edges:** an agent asks for sealed months (refused with the reason, never an empty answer); a feature window crosses the seal (computed only inside allowed months plus the gap); a remote worker with no `data_scope` (refused before start); DuckDB 2.0 files cannot be read by 1.x (stay on the pinned 1.5.5 until 2.0 is two weeks old and probe P-MDREAD passes, then bump everywhere at once); an agent with a shell reading files directly on the server (possible; sealed partitions sit in no cache the agents' working folders see, and research honesty, not money, is at stake; accepted).

### D-6. Backtests: QMB by fingerprint, one result shape, results in the Library (Library AD-29; engine AD-31; Lab AD-5; ruling 125)

- **Decision.** The backtest tools reach QMB through the engine's `qmb_backtest` operation (on the `qmb` placement, the PC as fallback). The result lands as one `backtest-result` item through one landing step, with `consumed` to the dataset card version, `uses` to the bot version, `tests` to the hypothesis when one is given, and big trade tables as Parquet blobs inside it. QMB's own result files (CT-32) import into this shape; the old Library's `backtest` items map to it (MIGRATION table). This is the agent tool that matters now; the rest of the backend reaches agents through the Lab and mini apps, without a long tool list.
- **Blast radius.** `qmx_tools/service.py:191-230` (agent backtests stop writing the old Library); QMB's run gets a landing step (a script after the run, shaped like `qmx_engine/trace_export.py`); the `backtest` rows in `catalog.py` are rebound.
- **Safe because:** QMB already never fetches and reads only by fingerprint (`qmb/src/qmb/data/policy.py`; pointed at), so the door decides exactly which bytes it reads. *Fix-check (58), N2:* the input is not byte-identical to today's CT-10 receipts; DR4's acceptance probe P-QMBREAD replays one month from the new files and from the same rows admitted the old way and requires the same trades.
- **Scenarios:** S-09, S-10, S-21, S-29. **Edges:** the card's data is corrected later (the result shows "corrected"); the run touches sealed months (only through `qmb.holdout_touch`, journaled, one per family per window); three old result shapes (one survives, the others import).

### D-7. Version control for concurrent agents (Library AD-30)

- **Decision.** Keep what LIB1-LIB4 built (agent branches, drafts, three-way merge, conflict objects, history, as-of reads, claims). Add: (1) **line-by-line text merge**: in the three-way merge, a `text/*` blob slot both sides changed is merged with `git merge-file -p --diff3`; exit 0 lands the merged text, a positive exit (the number of conflicts) mints a `merge-conflict` carrying the marked text; (2) **structural JSON merge** for `application/json` slots, key by key, one conflict entry per clashing key; (3) **history and blame reads**: `history(item)` (who moved which ref when, from the ref log) and `blame(item, slot)` (for text, the version and principal that last changed each line, computed at read from parents and line diffs); (4) chats reach it: the `library` toolset gains `branch`, `merge`, `conflicts`, `resolve`, `history` and `blame` rows over the new store; (5) the engine takes a claim at node start for any node with an intent key, released when its output lands.
- **Blast radius.** `qmx_library/store.py` `_three_way` (the blob branch of `pick`, lines 645-655), the catalog's `library` rows, engine node start (claims). Files agents edit on disk keep engine AD-49 (a git worktree per writer for real repositories).
- **Safe because:** `git merge-file -p --diff3` returns 0 with both edits on a clean merge and the conflict count with diff3 markers otherwise (ran: scratch base, ours and theirs files, git 2.55.0; output in section 11).
- **Scenarios:** S-08, S-14, S-17. **Edges:** both agents change the same line (a conflict, never a silent pick); binary blobs (pick-one, as built); a claim held by a dead run (expires within one heartbeat ttl, Library AD-24); he edits while an agent edits (he is one writer among others); a merged workflow fails validation (it becomes a conflict, Library AD-7).

### D-8. External connections: one registry, one health ladder (engine AD-67; rulings 129, 133)

Section 4 has the full design. In short: one Connections list in Settings, rows of kind `broker | platform | data`, each with an adapter from an open registry (today `ctrader | mt5 | ccxt | dukascopy | binance-vision | databento | firecrawl | http`) that declares how it signs in, where it runs, whether the home host holds its session, how its provider signals limits and errors, and its health check (56 §8.2), plus environment, accounts (several per connection, several connections per broker, as `qmx-broker` already models), a credential reference with a **scope** (`read | trade`), one home machine that alone holds and refreshes it, its capabilities and its provider limits. Setup uses the five states the engine already uses for machines (`available | configured | authorized | reachable | healthy`); while running, each connection reads `ok | slowed | maintenance | needs_you | down` (56 §8.4); a test is a real probe (for cTrader the existing QMF capability probe); a script workflow on the home keeps them healthy. Agents read through the existing read-only broker tools; nothing in this design submits an order.

- **Blast radius.** `qmx_broker/models.py` (the `Broker` row becomes one connection kind; the adapter list gains `mt5`; `Connection` gains `scope`), `qmx_control/service.py:466-474` (the `brokers` settings section is read once into `connections`), `qmx_router/vault.py` (replication by allow-list: model-provider rows, `qmx/read/*` and `qmx/data/*` static keys only; each receiving machine opens its copies with its own key; OAuth tokens and trade keys never enter it, fix-check 58, N5), `qmx_broker/ctrader_transport.py` (its short read sessions become calls to the home host's session, fix-check 58, N16), one health template.
- **Safe because:** the broker → connection → account model with keyring references and no credential in any read result already exists and is tested (`qmx_broker/models.py`, `credentials.py`, README; pointed at), so this widens a working shape instead of inventing one.

### D-9. Two monitoring layers from one source of events (engine AD-69; rulings 123, 126)

Section 6. Internal: the inbox, incidents, heartbeats, run cards, the doctor and the `ops` toolset keep reading spans, heartbeat rows, incidents and logs as they do, and gain a data health view (card freshness, failed downloads, connection health, disk). External: the same records are handed, at the point they are written, to an OpenTelemetry exporter; one collector on the server buffers on disk and forwards to OpenObserve. Claude Code chats and Hindsight send their own telemetry to the same collector. An outside agent gets a read-only observer token for QMX's MCP door, OpenObserve's own MCP door, and a runbook skill.

### D-10. Remote work reaches data the same way (engine AD-70)

Section 5. A remote worker gets the Library through the Library server (built), price data through the server's data door (`data_scope` on its pass), model keys through the relay (built), no non-model key (a step that needs a connection runs on that connection's home), and sends telemetry to the server's collector. The runner sets each node's placement and prefers the machine that already holds the data. Burst machines read through the server's door; direct bucket reads wait until the read-speed probe shows the extra hop matters.

### D-11. Storage, backups and real numbers (Library AD-10 and AD-16 amended; engine AD-30 amended)

- **Decision.** The server holds the main Library copy and the price files it has room for; the bucket holds everything, pushed nightly by the server; the PC holds the catalog, manifests, hot blobs and a price cache sized from its live free space. A durable Library blob born on the PC leaves it only after two verified remote copies, and a blob the PC fetched is a cache copy it may drop at any time (fix-check 58, N3); a price partition may leave the PC cache at any time (it is always re-fetchable by fingerprint) and leaves the server only after the bucket copy is verified and only if its card says `redownloadable`. One backup plan: PC to server through the Library server on commit, server to bucket after each commit batch (price files nightly), with the drills of Library AD-16. Every limit is a provider's own or a default measured on the machines, editable in Settings: server capacity comes from the live readings in the heartbeat (free RAM, measured session size), not from reserved constants. The 6,144 MB overhead, 12,288 MB budget, 2,048 MB attempt, 64 MB body, 1 MB search text, 1,000-bar read and 2 GiB sync-back figures are removed.
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
| Provider | `id`, `name`, `kind: trading | data`, `adapter` from the open registry (today `ctrader | mt5 | ccxt | dukascopy | binance-vision | databento | firecrawl | http`), `exchange` (CCXT) | "IC Markets via cTrader", "Binance", "Dukascopy" |
| Connection (one login or key) | `id`, `environment: demo | live`, `scope: read | trade`, `credential_ref: qmx/<...>` in the OS keyring, and the credential's `home: pc | contabo | <trading server>`, one machine that alone holds, refreshes and opens it, shared by every row naming that credential (for cTrader, by every grant under one app registration; fix-check 58, N9) (MT5 needs his Windows terminal, so `pc`), capabilities found by the test, the provider's own limits as reported, `licence` | "cTrader ID, live, read-only token", "MT5 investor login" |
| Account | `id`, `label`, `broker` (on platforms that reach several brokers), currency, leverage, `enabled`, `permissions: read | propose` | "IC Markets 1234567, USD, live" |

Several brokers and several accounts per broker are the existing model (several connections per provider, several accounts per connection). A data provider has no accounts.

**Added.** Settings, Connections, Add: pick the provider; enter the key through the keyring's secure prompt, or, for cTrader, sign in once on cTrader's own consent page that QMX opens and receives back on a local address, choosing read-only for his PC and server (a grant that can trade live money is made on a trading server, ruling 135). *Fix-check (58), N5:* his browser carries only the one-minute code; the PC's loopback receiver forwards it to the connection's home and keeps nothing; the home holds the app's client secret, exchanges the code and keeps the tokens in its own key store, never in the vault. QMX then runs the test and lists the accounts it found; he labels and enables them. Nothing about a key is ever written to a settings file, a log, the Library or a model's context.

**Tested.** Each adapter has one `probe()`: for cTrader the existing first-connection probe in `qmf/venue/probe.py` (timestamp unit, daily boundary, bar basis, pip formula, money exponent) plus sign-in and the account list; for MT5 terminal reachable, signed in, symbol info, and `trade_allowed` false for an investor login; for CCXT the server time, balances and the key's own permission flags where the exchange reports them; for a data provider one small fetch. **A credential is labelled `read` only when the probe confirms it cannot trade** (cTrader token scope, MT5 investor login, exchange key permissions); otherwise it is `trade`. Each test result is a `test-report` record in the Library naming the connection.

**Kept healthy.** A `connections-health` script workflow runs on a schedule on each connection's home machine: it walks the five states (`available | configured | authorized | reachable | healthy`), renews OAuth tokens before they expire on the home only (the grant's one refresh owner: a cTrader refresh kills the old pair everywhere, 56 §2), and writes a short reading per connection into the host heartbeat (`ok | slowed | maintenance | needs_you | down`, last good, latency, token expiry, `slowed_until`). Only `down` is an incident per masked signature (`connection:<id>:<code>`) at provider-failure severity (engine AD-17), shown once and resolved by the next passing check; `needs_you` (a new grant, an app not yet approved, a weekly login) is an inbox task; a cTrader outage while the market is closed reads `maintenance` (56 §2).

**Shown.** The Connections list (state chip, accounts with balance and equity read when opened, token expiry, last test, capabilities, which feeds and workflows use it, where it runs); the data health view; Portfolio reads the same accounts.

**Used.**
- *Workflows and feeds* name `connection: <id>` in their inputs or slots. Preflight checks that the connection is `healthy` and that the node runs where the credential may be read; otherwise the fire is `blocked_config` with one item, and no model call.
- *Credentials by scope and home.* Data-provider keys and confirmed read-only trading credentials replicate (by allow-list) only to make the server their home, where the server opens them with its own vault key, so server downloaders and health checks run while the PC sleeps (engine AD-28). A CCXT key is used on one machine only (a shared key raises `InvalidNonce`, 56 §5); a machine that needs the same exchange gets its own key. A cTrader read grant has one home, which alone opens its demo and live connections (cTrader advises at most one of each per app, 56 §2), and the other machine's reads go through it. A credential that can trade a live account is never on the PC or the server (ruling 135).
- *The copilot* uses the existing read-only broker tools (accounts, positions, quotes, bars, symbol info) over the accounts he enabled. No catalog row submits, changes or cancels an order. `propose_order` stays as built (an unsigned proposal with no signing path).
- *A trading server (later, designed by that session).* He enters the trading key on the trading server itself when he sets it up, under its own cTrader app registration (one per trading server, each approved by Spotware first; fix-check 58, N10), so its refreshes never touch the read app's connections and QMX on his PC never stores it. Consent follows the same contract as the read app (N11): the trading app's secret is entered only on the trading server, the code reaches it by a redirect to its tailnet address or through the PC's receiver, and the trading server makes the exchange. The Connections list shows the account as "on trading server X" with its health from that server's heartbeat. How the trading server trades is the trading-node and unit sessions' design.

**Why this holds the money rule.** Agents read through tools that cannot trade; a credential that can trade live money lives only on a trading server, never on a machine where agents have a shell (ruling 135); withdrawals are impossible through cTrader and MT5 and happen only in his own browser (ruling 116).

---

## 5. Remote work and split runs (engine AD-70)

| Who | Library | Price data | Keys | Connections | Telemetry |
|---|---|---|---|---|---|
| The PC (server is the main copy) | its own replica and cache; writes go to the server; outbox when the server is unreachable | its cache; misses fetched from the server, then the bucket, by fingerprint | its keyring: model keys, read-only and data keys | the connections whose home is the PC; reads of server-homed connections go to the server | OTLP to the server's collector; a gap while the server is unreachable |
| A workflow step on the server | the server store, in the same process | the server's door, with the seal | the server's relay; keys opened with the server's own vault key | the connections whose home is the server | the server's collector |
| A remote worker or burst machine | the Library server over the tailnet with its run pass (built) | the server's door over the tailnet, checked against the pass's `data_scope` | none; model calls through the central relay | none; a step that needs a connection is placed where the connection lives | OTLP to the server's collector; logs and trace saved as run blobs at the end |
| A split run (data prep on the server, GPU training on the PC, report on the server) | each step on its machine as above | the PC step's partitions are materialised into the PC cache before it starts | as above | as above | one trace across machines (`trace_id = run_id`) |
| An outside agent (Claude Code) | read-only observer token on QMX's MCP door (on the server, so the PC may sleep) | a card's sample through the door, sealed months refused | none | read the Connections list without credentials | OpenObserve's MCP door |
| A trading server (contract only; its design belongs to that session) | fetches admitted bot versions by id; sends journals, fills, decisions, heartbeats and kill events to the Library server within seconds | its own live stream; history through the server's door | none from QMX's vault; its trading keys entered on it | its own connections, shown in the PC's list | OTLP to the server's collector |

**Placement.** The runner sets each node's placement from its `runs_on` list and the data locality the heartbeat reports (the blob-cache summary seam of engine AD-65), so a data-heavy step runs next to its partitions; today it reads `runs_on` only through an adapter workaround (REM verdict). A placement that lacks the partitions and cannot reach the door waits `placement`, never fails.

---

## 6. Two monitoring layers from one source of events (engine AD-69)

**One source.** Every level already writes four things: spans (the engine ledger and the router journal, engine AD-15), heartbeat rows (engine AD-65), incidents per masked signature (engine AD-10), and JSONL logs. These are the source of truth for both layers; nothing writes twice by hand.

**Internal layer (in the app).** The inbox, incidents, heartbeats, run cards, the doctor, the Machines list and the `ops` toolset keep reading those rows. New: Library heartbeat facts (writer alive, sync lag, outbox length, disk), Lab facts (open projects, kernels, runs), a **data health** view (card freshness and quality, downloads and feeds with their last run and incidents, connections with their states, free disk on the PC and the server, bucket copy age), and PC disk alerts read from live free space.

**External layer (deep, on the server).** At each write point the record is also handed to an OpenTelemetry exporter (spans as traces with GenAI names pinned to one version of the conventions, heartbeat facts as metrics, logs as logs). One OpenTelemetry Collector, on the server, receives them over the tailnet with a disk-backed queue and forwards to OpenObserve; the PC runs none, so while the server is unreachable the deep view has a gap, and the Library still keeps every run's trace and logs. Every exporter is fed the record after redaction (engine AD-37). Each Claude Code chat the harness starts gets the telemetry environment (`CLAUDE_CODE_ENABLE_TELEMETRY=1`, OTLP to the server's collector; prompt text stays redacted, the CLI's default). Hindsight turns on its own traces. A trading server later sends to the same collector instead of its planned Prometheus, Loki and Grafana. OpenObserve keeps a short window (a Settings value); the Library keeps every run's trace and logs as the permanent record, so the viewer can be rebuilt or swapped.

**The outside agent's door.** Three read-only things: an observer token on QMX's MCP door that lists only the `ops` and doctor rows, run traces and logs and the data health read (no broker or Library content rows) plus one row that saves a diagnosis note on the observer's own ref (shown in the inbox as "an outside agent left a diagnosis"); OpenObserve's MCP door (its free tier, ruling 123); and a runbook skill, `inspect-qmx`, kept as a Library skill and exportable, that names each door, the doctor, the data health view and how to read a run's trace. The token is revocable, expires, and is created by him in Settings.

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
| S-09 | Backtests by fingerprint, one result shape | Library AD-29, AD-28, engine AD-31 | QMB through the door with a second replay-reader entry point for typed partitions, bid and ask bar series materialised as a pair; same trades as the old reader (P-QMBREAD); one landing step; old shapes import (fix-check 58) | DR4 |
| S-10 | Tuesday's run in today's | engine AD-5, AD-63; Lab AD-19 | `library` node available; `@run` and `@library` in workflow inputs | DR9 |
| S-11 | Mini apps in the Library, run as plugins | engine AD-55, AD-64 | four switches (publish writes the item, materialise at start, bind `app:` rows, attach the sink) | DR1, DR9 |
| S-12 | One health view at every level | engine AD-69, AD-65 | internal views over the same rows; OTel exporters, collectors, OpenObserve | DR10 |
| S-13 | Outside agent looks in, can only look | engine AD-69 | observer token (read rows plus a diagnosis note), OpenObserve MCP, runbook skill | DR10 |
| S-14 | Lab as a workspace | Lab AD-19 | project collection, New… by level, workspace annotations, panels over existing reads; pods left out | DR13 |
| S-15 | Quick copilot idea that cites its data | Library AD-28, AD-25 | data tools over the door; `consumed` edge to the card version when saved | DR3 |
| S-16 | ML on his PC with the data there | Lab AD-20 | PC placement with a GPU slot; free-space check; partitions materialised by fingerprint; model lineage | DR13 |
| S-17 | Family trees for strategies, indicators, units, models | Library AD-32 | templates write `variant-of` with `what_changed`; `component_type`; one family read | DR12 |
| S-18 | Remote step that needs market data | engine AD-70, Library AD-28 | `data_scope` on the pass; the server's door over the tailnet; placement by locality | DR3, DR14 |
| S-19 | Trade journals in one shape | Library AD-31, AD-25, AD-16 | fills as partitions ordered by observation time, so a late fill is an append; a fill month freezes at month end plus the broker's settlement delay with no gap check, and a fill arriving later lands as an automatic correction; the open fill month is pushed to the bucket after each commit batch; `trade` items, journal collections, imports per broker (fix-check 58) | DR12 |
| S-20 | Computer and browser outputs as evidence | Library AD-27 | captures land as `source` with `origin: capture`, linked to the run or session; text redacted against account ids | DR7 |
| S-21 | Bad data found later | Library AD-25, AD-22 | a corrected partition mints a card version listing it in `replaced`; only results that read it show "corrected" | DR3 |
| S-22 | Synthetic data as its own world | Library AD-28 | generator template reads through the door with `purpose: train` only; card `world: synthetic` with generator, settings, seed | DR4 |
| S-23 | Features and labels as datasets | Library AD-25, AD-32 | derived partitions with `derived-from` the source card and `uses` the component version; computed inside allowed months plus the gap | DR12 |
| S-24 | News and calendar from one fetcher | engine AD-68, Library AD-25, AD-16 | the calendar is a feed landing partitions; each revision is a new row by observation time (an append while the month is open, an automatic correction after it froze at month end plus the settlement delay); the open calendar month is pushed to the bucket after each commit batch because revisions cannot be fetched again; headlines are feeds; three old fetchers retire (fix-check 58) | DR6 |
| S-25 | Disks: where bytes live, when the PC lets go | Library AD-10, AD-25 | a blob born on the PC leaves it after two verified remote copies; a fetched blob is a cache copy, evictable; cache sized from live free space; "where are my bytes" from cards and status, saying plainly what has one copy without the bucket (fix-check 58) | DR2, DR3 |
| S-26 | Real numbers replace invented ones | engine AD-30, Library AD-27 | capacity from live heartbeat readings; body, search and bar limits removed | DR2, DR7 |
| S-27 | New kinds as schema files | Library AD-3, AD-31, AD-33 | one new kind (`trade`); `source` and `component` extended; card and page declared per kind | DR7, DR12 |
| S-28 | Trading servers connect back (data side) | engine AD-67, AD-70 | the data contract in section 5; no credential hand-over (ruling 135): each trading server has its own cTrader app, he enters its trading key there, and the sign-in code goes to that server, which keeps the tokens; design owned by the trading-node session (fix-check 58, N10, N11, N22) | after the unit work |
| S-29 | Strategy funnel at data scale | Library AD-25, AD-32 | many cards from the downloaders; registry entries as items; trial counts from edges; the QMB redesign belongs to the risk session | DR6, DR12 |
| S-30 | Search and answers at real volume | Library AD-8, AD-27, AD-10 | text slots sync to the PC with the manifests and a blob's arrival re-indexes its objects, so the PC's search finds the words of server-born items (P-SYNC-DISK); probes P-TAINT and P-SRCH on 100,000 items, then page and summarise answers (fix-check 58, N1) | DR2, DR7 |

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
| 14 | One backup plan: PC to server on commit, server to bucket after each commit batch (frozen price files nightly; the open month of a non-redownloadable series after each batch), price files included | Library AD-16 |
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
| 2 | **DR1, the Library switch-on on the PC** | after the rehearsal on a copy of his home (P-REHEARSE), import `library.db` (junk filtered) and `artifacts.db`; flip the `library_*` rows; retire the old file read-only; the harness's `domain.library` and the copilot's search use the new store; `app_runtime()` attaches the sink; backup list updated; QMB's registry projection reads through the port | step 0 (DEL3a touches the same files) |
| 3 | **DR2, the server is home** | the Library service inside the server's host process; the selective PC sync, the idempotent outbox and the primary epoch; the server-loss drill; flip `primary = server` by the MIGRATION step 8 procedure; Hindsight moved to the server with a system Postgres (rebuild from Library rows); capacity from live readings (D-11) | DR1 |
| 4 | **DR3, the price store and the door** | the typed-column partition writer and the key with subject and variant (P-MDREAD, P-KEY, P-MARKS pass first); the open month and the freeze rule; card writer and `dataset` fields; the door in each host (seal, splits with a gap, `purpose`); `data_scope` on passes; agent data tools filled at start-up; `datasets.json` retired; the old ticks imported from the server copy as partitions with cards | DR2, DR0 |
| 5 | **DR4, backtests through the door** | QMB reads through the door; one landing step for `backtest-result`; old shapes imported; backtest tools bound; synthetic-data template | DR3 |
| 6 | **DR5, Connections** | the `connections` registry (brokers and data providers), scopes, tests (cTrader probe, CCXT, MT5 adapter on the PC), the health workflow, readings in the heartbeat; the `brokers` section read once into it | DR2 |
| 7 | **DR6, downloaders and feeds** | the `feed` template; Dukascopy (dukascopy-node, after probe P-DUKA), Binance bulk, CCXT top-up, broker history; the calendar feed; old fetchers retired | DR3, DR5 |
| 8 | **DR7, ways in** | upload door, `source` fields, Docling extraction workflow, chunked whole-text search, body and text limits removed, `save_source` step, captures | DR2 |
| 9 | **DR8, version control reaches agents** | line and JSON merge, history and blame, chat rows, engine claims at node start | DR1 |
| 10 | **DR9, workflows read the Library** | the `library` node switched on; `@` references in workflow inputs; the mini-app switches | DR1 |
| 11 | **DR10, monitoring** | OTel at the write points after redaction, one collector on the server (none on the PC), OpenObserve on the server, CLI and Hindsight telemetry, Library and Lab heartbeat facts, the data health rows, observer token and runbook skill | DR2 |
| 12 | **DR11, real numbers sweep** | any invented constant left after DR2 and DR7 | DR2, DR7 |
| 13 | **DR12, kinds and lineage** | `trade` kind and journal imports; `component_type`; funnel templates write edges; card and page declarations for every kind | DR1 |
| 14 | **DR13, the Lab workspace and ML on the PC** | projects, New… by level, workspace state, Tuesday's run, data panel, GPU placement and the training template | DR3, DR9, DR12 |
| 15 | **DR14, placement by data locality** | the runner sets placement from `runs_on` and locality; remote reads through the server's door | DR3, DR10 |

Steps 6 to 11 may run in any order once their dependency lands; the table order is the recommendation. *Fix-check (58), N4:* the work items the planner turns into PRs, in build order, with the packet that builds each fix and the probes that gate each, are in "Fix-check applied (58)" at the end of this file; they supersede this table where they differ. Migration safety (MIGRATION.md, unchanged law): back up first, import into a distinct destination, verify counts and hashes, then flip; old stores are retired read-only, never deleted.

---

## 11. Probes (each measures; none sets a limit)

The final list, its order and the exact pass and fail lines are in "Fix-check applied (58)" at the end of this file (which supersedes the list in "Edge-case review applied (57)"); it supersedes this table where they differ.

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

1. **A cloud copy for his data.** QMX should keep a second copy of everything off the server, in a storage bucket. Recommended: a Cloudflare R2 bucket (the first 10 GB are free; about $2-3 a month at today's sizes; downloads are free). This needs his own Cloudflare account. If he says no, the switch-on still works, but (fix-check 58, N3, said plainly) **every file made on the server has one copy, on the server**: uploads the server receives, the pages and text Docling pulls out (the text also reaches his PC), recordings, run logs, trained models, and price months that cannot be downloaded again (his fills, calendar revisions). Files made on his PC keep two copies (the PC and the server) and stay on the PC, and the old 10 GB stays on C:. A file he opens on the PC is only a cache copy. *Recommended: yes, R2, opened before the server becomes the main copy (DR2's flip).*
2. **Free his C: drive.** May QMX remove the old 10 GB of price history from his C: drive once two checked copies exist (one on the server, one in the bucket)? Nothing is removed before both copies are checked by fingerprint. *Recommended: yes.* (He did not answer this one in the funnel.)

Steps that are his to do, not decisions: sign up for OpenObserve's free tier when monitoring is installed (he said the free tier is fine); sign in once on cTrader's own page when he adds his cTrader connection; approve removing the old calendar task on his PC.

---

## 13. Reviewer gate and lint

The skill's gate was run inline (the brief allows no sub-agents): the deterministic lint, a rubric walk against the good-spine checklist, the currency lens and the adversary lens. Lint, run with `python -I C:/Users/Mubarak/Desktop/QMX/.claude/skills/bmad-architecture/scripts/lint_spine.py --workspace <dir>` after every edit: **0 findings on all three spines** (library-and-data, workflow-engine, lab-and-pods). The review is in `architecture/library-and-data/reviews/review-2026-10-22-data-round.md`; its fixes are applied:

- **Adversary, applied.** (1) Two downloaders, or a downloader and an importer, could each obey AD-25 and both move one series card: a card update now claims the series key. (2) A script process and the host could both write the price store's metadata: the door is now the store's only writer, through `commit(files)`. (3) A copilot read with no split and a Lab read with a split could disagree on what "purpose" means: a read without a split is exploration over every unsealed month; a read with a split gets only that segment. (4) A workflow output typed `source` could land as an `artifact` in one template and as a `source` in another: it always lands as a `source`. (5) Derived series had no key rule: `source = derived`, `kind = <component>-v<version>`. (6) A feed's server home could read as breaking "local by default": the template only suggests the server because the data lives there; he can move it. (7) The Lab's workspace annotation needed the `collection` schema to accept it: stated.
- **Currency, applied.** Every new pin was read from its registry on 2026-10-22: dukascopy-node 1.50.0 (npm; 1.51.0 published 2026-10-21), DuckDB 2.0.0 (PyPI, 2026-10-21; the code pins 1.5.5), Docling 2.134.0 (PyPI), MetaTrader5 5.0.6231 (PyPI), OpenTelemetry Collector 0.162.0 and OpenObserve 1.0.4 (GitHub releases), Hindsight 1.1.0 (PyPI `hindsight-api`), Node.js 24.21.0 LTS (nodejs.org), the Binance public-data folders (bookDepth, bookTicker, trades, aggTrades listed live), and dukascopy-node's CLI options (its config page). Two facts stay **remembered, not verified**, and each has a probe before anything relies on it: cTrader's read-only OAuth scope and the MT5 investor login's `trade_allowed` (P-CTSCOPE). (Since then 56 §2 retrieved cTrader's two scopes, `accounts` view-only and `trading`; P-CTSCOPE keeps the demo order test.)
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

---

## Edge-case review applied (57)

Date: 2026-10-22, evening. The one fix round for `57-data-round-edge-case-review.md` (4 critical, 16 high, 20 medium, 7 low). BMad architecture skill, headless, amend mode; no sub-agents, so the reviewer gate is the deterministic lint plus this table. AD ids are stable: amendments sit in place, marked *Edge-case review (57)*. Nothing committed.

**Code claims checked before acting** (`origin/engine/base` `8af1a1cd`, `git show`, no checkout): `qmf/data/store/engines/parquet.py` stores each row as a JSON string and the whole canonical JSON in the schema metadata, reads it back with `pq.read_schema`, and renames without an fsync (F1, F13); `SeriesPartition` holds only `source, instrument, window` (F2); `qmx_hub/replicate.py` `_copy` pulls every object the PC lacks with every blob it names, and `plan` pushes an owned ref whenever the heads differ (F10, F12); `Store.put` checks `stale_head` before its idempotent return, and `_lines` calls `json.loads` on every line with no recovery (F11, F13); `qmx_router/vault.py` `is_replicable` refuses only names with a `broker` segment, and its header says the PC is the vault and nodes ask it (F29, F30); `qma/harness/surface.py` `CLI_BUILTINS` gives every chat `Bash` (F28); `seal.py` keeps the boundary frozen and never re-derived (F7); `passes.py` checks `expires_at` with no leeway (F38); the heartbeat already carries `qmx_version` (F16). All held. **cTrader, read on the web today** (help.ctrader.com/open-api/connection, "Best practices"): "At most, you should create two connections: one for demo accounts and one for live accounts." It is advice, and the error `CONNECTIONS_LIMIT_EXCEEDED` (67) exists, so the design keeps one holder per app and environment and lets probe P-CT2CONN widen that.

### What changed, in plain words

- **The four criticals.** (1) Price months get their own writer that stores real columns and fingerprints the rows as they stream, so a month of ticks reads back; the read probe now runs before the old ticks are imported. (2) The PC copies only the list of what exists and the small records; a file comes to the PC only when he opens it, so syncing cannot fill his C: drive. (3) Each broker sign-in has one home machine, which alone refreshes it; trading servers use their own cTrader app registration, so a routine refresh can never log out a live bot. (4) A key that can trade live money never sits on his PC or server, where agents have shells: he enters it on a trading server at setup (ruling 135, the lead's decision, recorded for him to see).
- **Storage and sync.** Which copy is the main one is a single record with a number only his flip raises, so an old backup cannot quietly take over; a resent save is not a conflict; a power cut cannot stop the Library opening; the server pushes to the bucket after each batch of saves; losing the server has a written, drilled procedure; when a disk fills, re-fetchable data gives way first and a save is refused whole, never half-written; without the bucket everything works except freeing his C: drive.
- **Connections.** One home per connection; read and data keys can live on the server and open there while the PC sleeps; a provider's slow-down signal is shared by every run on that machine; health shows "slowed", "maintenance" and "needs you" instead of errors.
- **Price data.** Bid and ask, and different indicator settings, are separate series; only complete months are frozen, and the current month is one file replaced as it grows; a backtest is marked only when data it actually read is corrected; gaps stay open until filled or accepted; the holdout boundary moves only by his click.

### Finding → outcome

A = applied. Where = the AD (L = Library, E = engine, Lab) or the file amended.

| # | Sev | Outcome | Where | What was done |
|---|---|---|---|---|
| F1 | Critical | A | L AD-25; Stack; D-1 | A typed-column partition writer in `qmf-data` (int64 time and scaled prices, compressed row groups, no rows in the metadata); fingerprint over a pinned logical encoding, streamed; the old engine keeps small evidence only; P-MDREAD before the DR3 import |
| F2 | High | A | L AD-25; conventions | Key `source / subject / kind / variant / year / month`; `commit` refuses a different file for a frozen key unless marked a correction |
| F3 | High | A | L AD-25; D-1 | Only frozen months are immutable; the open month is one file under a fixed key, replaced, never archived or bucketed, minting no card version |
| F4 | High | A | L AD-22, AD-25 | `where`, `complete_up_to` and freshness computed at read; data marks from partition fingerprints; `superseded` never through a card; `corrected` from the card's `replaced` |
| F5 | High | A | L AD-25; E AD-68; D-4 | `--retries` and `--retry-on-empty`; a month freezes only on a passing gap check or his acceptance; gaps re-fetched |
| F6 | Medium | A | L AD-28 | PC partitions stream to the server door's staging route; the server's `commit` verifies them |
| F7 | Medium | A | L AD-28; SOLUTION-DESIGN §30.1 | The seal moves only by his click, journaled; `seal-roll` withdrawn; a door that cannot confirm the current seal serves only months before its last confirmed boundary |
| F8 | Medium | A | L AD-28 | A final look takes the claim `final_look:<family>/<window>` and waits while the server is unreachable |
| F9 | Medium | A | L AD-28 | A big read returns a handle (path, rows, summary, chart spec); heavy reads run in a child process |
| F10 | Critical | A | L AD-10, AD-26; D-2 | Selective sync: ref moves since the last sequence, with their manifests and edges; blobs only when opened; one sync at a time, coalesced |
| F11 | High | A | L AD-14 | Outbox entries carry item id, expected head, intended object and version; `put` succeeds when the head already is the intended object |
| F12 | High | A | L AD-14, AD-19; MIGRATION | `refs/primary` with an epoch only his flip raises; fast-forward-only pushes of owned refs; the server refuses `mirror` of refs it owns |
| F13 | High | A | L AD-16 | A torn last line is quarantined with an alarm and the store opens; a bad middle line opens read-only with an incident; fsync before rename |
| F14 | High | A | L AD-16; MIGRATION "When the server is lost" | A written procedure, drilled on scratch roots before DR2 (P-SERVERLOST) |
| F15 | Medium | A | L AD-14; UI-HANDOFF §17.6 | Pending outbox entries show in PC reads, marked "waiting for the server" |
| F16 | Medium | A | L AD-14; E AD-65 | Version and kind-digest check on every sync; `server_needs_update`; the server updates first; outbox entries carry their version |
| F17 | Medium | A | L AD-16 | With `primary = server` the PC reaches the server store only through the Library server's API; rclone only server to bucket |
| F18 | Medium | A | L AD-10 | Same fix as F10; existence checks read ids, never bytes |
| F19 | Medium | A | L AD-26; MIGRATION; D-2 | A rehearsal on a copy of his real home first (P-REHEARSE); D-2's "safe because" corrected |
| F20 | Low | A in part | L AD-16 | The rename retries WinError 5 or 32. Not adopted: excluding the Library from Windows indexing and Defender, a security setting that is his to change |
| F21 | High | A | L AD-10; OPEN-DECISIONS; §12 | Not a precondition: without the bucket nothing durable leaves the PC, partitions stay on the server, "one copy off this PC" is shown; everything else works |
| F22 | High | A | L AD-10; Lab AD-20 | One live rule per machine: the price cache, transient blobs, the telemetry queue, then doubly-copied hot blobs give way; writers refuse whole with `disk_full`; Library writes are refused last against a measured floor he may raise |
| F23 | Medium | Logged | L Deferred | Server eviction of durable blobs deferred: partitions, the bulk, already leave the server; revisit when the fill reading shows durable blobs need the room |
| F24 | Medium | A | L AD-16 | Objects, refs, edges and durable blobs pushed to the bucket after each commit batch; partitions nightly |
| F25 | Medium | A | L AD-16 | The monthly drill rebuilds the catalog only, plus a rolling hash-checked sample |
| F26 | Medium | A | L AD-27 | A resume re-hashes the partial; abandoned partials are deleted; PC uploads stream through to the server, the staging copy kept until two remote copies exist |
| F27 | Critical | A | E AD-67; ruling 135; §4 | One home per connection, its only refresh owner; other machines forward reads; trading servers on their own cTrader app; P-CTREFRESH |
| F28 | Critical | A | E AD-28, AD-67; L AD-12; ruling 135 | Keys that can trade live money only on trading servers, entered there; a live-trade key added on the PC is not stored (`needs_you`); demo-only trade keys allowed. Not adopted: the review's fallback of a trade key on the PC sealed behind Windows Hello (no trade key on the PC at all is simpler) |
| F29 | High | A | E AD-28; L AD-12 | Replication by allow-list: model-provider rows, `qmx/read/*`, `qmx/data/*`; P-NOTRADE tests `qmx-broker`'s own names |
| F30 | High | A | E AD-28 | Each receiving machine has its own vault key pair; the server's private key sits in a file only the QMX service user reads; the path where the server asks the PC goes; `vault:unavailable:<machine>` |
| F31 | High | A, other form | E AD-28, AD-67, AD-70 | Not one gateway for everything: `host` adapters (cTrader, MT5, CCXT) keep one session in the home host that local steps call; `step` adapters get the key on the home; no non-model key on remote workers |
| F32 | High | A | E AD-67 | One holder per (cTrader app, environment); a separate app for trading servers; P-CT2CONN records the real behaviour |
| F33 | High | A | E AD-67, AD-68 | A shared `slowed_until` per connection on its home, set from the provider's own signal; one CCXT key per machine |
| F34 | Medium | A | E AD-67; UI-HANDOFF §17.8 | Readings ok, slowed, maintenance, needs_you, down; only `down` is an incident |
| F35 | Medium | A | E AD-67 | Adapter declarations (`auth`, `runs_on`, `session`, `limit_signals`, `error_map`, `health_check`, `published_limits`); an entry-point registry; `http` checks the body |
| F36 | Medium | A | E AD-67, AD-68 | cTrader history through the home host's long-running `qmf-venue` session |
| F37 | Low | A | E AD-67 | One fixed loopback port registered on the read app; "app not approved yet" is `needs_you` |
| F38 | Low | A | E AD-28, AD-65, AD-67 | Heartbeat clock offset; CCXT `adjustForTimeDifference`; pass checks tolerate the measured offset |
| F39 | High | A | E AD-30 | Admission reserves declared memory until measured; heavy work in child processes; the host's out-of-memory score lowered; P-OOM |
| F40 | Medium | A | E AD-68; L AD-28 | One node per partition; heartbeat on its own thread; `commit` refused while another run holds the key's claim |
| F41 | Low | A | L AD-27 | Canonical URLs normalised; text hashes compared within one `extractor_version` |
| F42 | Medium | A | E AD-69 | "Keeps what the queue holds"; the collector's drop and queue metrics in data health; the queue is expendable |
| F43 | Medium | A | E AD-69 | Exporters fed after redaction; P-REDACT |
| F44 | Medium | A | E AD-69; HARNESS-REQUESTS H61 | The observer gets the `ops` and doctor rows, traces, logs and data health; no broker or Library content rows |
| F45 | Low | A | E AD-65 | Masked signatures for sync, torn logs, epoch, vault, stale seal, telemetry drops and disk |
| F46 | Low | A | E AD-69; HARNESS-REQUESTS H60 | No collector on the PC; OTLP straight to the server's collector |
| F47 | Low | A | E AD-68; D-4 | dukascopy-node is the one fetcher after P-DUKA; QMX's bi5 path only as the probe's cross-check |

**Counts.** Applied 46 (F20 and F31 in part or in another form), logged 1 (F23, Deferred with a revisit condition), rejected 0. Parts not adopted, with reasons above: the indexing and Defender exclusion (F20), the bucket as a precondition (F21), a Windows Hello-sealed trade key (F28), one gateway for every provider (F31).

### 55 against 56: contradictions resolved

| # | Was in 55 | Now | Where |
|---|---|---|---|
| C1 | every home renews OAuth; read tokens replicate; the PC's trade token is copied to a trading server | one home per connection, its only refresh owner; live-trade keys entered on the trading server; a separate cTrader app for trading servers | §0 item 7, D-8, §4 "Kept healthy", "Used", the money rule; E AD-67 |
| C2 | dukascopy-node "with its own retries" | `--retries` and `--retry-on-empty`; one side per run, as the series `variant` | D-4; E AD-68; L AD-25 |
| C3 | keys in "the operating system's keyring"; the vault's private key on Contabo, while the code makes the PC the vault | each receiving machine has its own vault key, the server's in a service-user file; no PC dependency | §0 item 7, D-8, §5; E AD-28 |
| C4 | the five machine states only | five states for setup, plus ok, slowed, maintenance, needs_you, down while running | D-8, §4; E AD-67; UI-HANDOFF §17.8 |
| C5 | a closed adapter list; "its own limit cools the run" | an open registry with 56 §8.2's declaration fields; a shared `slowed_until` from each provider's own signal | D-4, D-8, §4; E AD-67, AD-68 |
| C6 | a cTrader connection per machine and per use | one holder per (app, environment); other machines forward | §4; E AD-67 |
| C7 | one CCXT key replicated while the PC also uses it | one CCXT key per machine | §4 "Used"; E AD-67 |
| C8 | `qmx-broker`'s short sessions for downloads and health | the home host's long-running `qmf-venue` session | D-4; E AD-67, AD-68 |
| C9 | cTrader's read scope "remembered" | the scopes `accounts` and `trading` are retrieved (56 §2); P-CTSCOPE keeps the demo order test | §13 |
| C10 | Hyperliquid absent | the open registry admits it later with its own declaration | E AD-67 |

The contradictions with the code and with 55's own text (57 §8) are closed by F1, F4, F7, F10, F12, F17, F19 and F29 above.

### Pre-build probes: final list, in order

*Superseded by the probe list in "Fix-check applied (58)" below (N4: as written here, most of these gate the packet that builds the code they test).* Each runs the real code on scratch roots or demo accounts. A failure is a finding to fix, never a reason to add a limit. "Before" is the packet of §10 that may not start until the probe passes.

| Order | Probe | Before | PASS when | FAIL when | Covers |
|---|---|---|---|---|---|
| 1 | P-REHEARSE | DR1 | the switch-over run on a copy of his real `~/.qmx` in a scratch root ends with item counts per kind, version chains, links, memo rows and blob hashes equal to MIGRATION step 0's numbers, and his real home is untouched | any count or hash differs, the importer stops, or his real home changed | F19 |
| 2 | P-TORN | DR1 (store logs); DR2 adds the outbox log | with the last line of the ref, edge and annotation logs cut mid-line, and separately NUL-filled, the store opens, the line sits in `quarantine/`, `library:torn:<log>` is raised, and every other record reads back | the store refuses to open, a torn line is read as a record, or no alarm is raised | F13 |
| 3 | P-SYNC-DISK | DR2 | with `primary = server` and 5 GB of blobs on the scratch server, one PC sync copies no blob file; opening one item fetches exactly its blobs; the sync asks for ref moves since a sequence, not for every object id | any blob is copied without being opened, or a sync lists every object id on either side | F10, F18 |
| 4 | P-REPLAY | DR2 | after the connection is killed between the server's commit and its reply, the outbox replay returns success, the ref's head is the intended object, and there is no `merge-conflict` and no second item | a conflict, a `stale_head` refusal, or a duplicate item | F11 |
| 5 | P-SPLIT | DR2 | after a flip to epoch E, a PC restored with `primary = pc` and epoch E-1 refuses to act as primary, raises `library:epoch:<store>`, and the server's `main` heads are unchanged after a sync | the server's `main` moves to an older head, or the stale PC moves `main` anywhere | F12 |
| 6 | P-VERSION | DR2 | with the PC one `qmx_version` ahead, a sync refuses with `server_needs_update`, the save stays in the outbox, and it lands after the server updates | the server takes the write, or the save is lost | F16 |
| 7 | P-SERVERLOST | DR2 | on two scratch roots and a scratch bucket folder: the server root is wiped; MIGRATION's procedure promotes the PC (epoch raised), lists the stale server-owned refs, restores a new server from the bucket and re-pairs; every object the bucket held reads back by hash and the two ref logs agree | a step needs an action the procedure does not name, or an object the bucket held does not come back | F14, F21, F24 |
| 8 | P-DISKFULL | DR2 (Library, cache, telemetry); DR7 (uploads) | on a scratch volume filled to the floor, the price cache, transient blobs and the telemetry queue give way first, in that order in the log; a Library save past the floor is refused with `disk_full` and a plain message, and no half-written file exists; an upload stops whole and resumes later | any half-written file, a lost outbox entry, or a Library write refused while expendable data remained | F22, F26 |
| 9 | P-OOM | DR2; again at DR7 | on the server, Docling on a 400-page PDF, a big door read and two agent nodes started together: if the kernel kills anything it is a child process; `qmx_host` stays up and the Library and the door keep answering | `qmx_host` is killed, or the Library stops answering | F39, F9 |
| 10 | P-VAULT-AWAY | DR2 (model keys); DR5 (connection keys) | with the PC switched off, a restarted server opens its own keys: the relay serves a model call and a server-homed health check runs; with the server's key file removed, `vault:unavailable:contabo` is raised | a server job waits for the PC, or fails without the incident | F30 |
| 11 | P-HS, P-LAT (exist) | DR2 | as §11 states | as §11 states | — |
| 12 | P-MDREAD (moved up) | the DR3 import | one real month of EURUSD ticks written by the new writer reads back row for row through the door; a second write of the same rows gives the same fingerprint and no new file; file size and peak RAM for one week and for one month are recorded; read times for 23 years of m1 from the PC cache, the server disk and over the tailnet are recorded; DuckDB 1.5.5 reads the files | the read-back fails or differs, the fingerprint changes between two writes of the same rows, or peak RAM rises in step with the rows (a month near four times a week: the month is held whole) | F1, F3 |
| 13 | P-KEY | DR3 | bid and ask m1 for one month land as two series with two cards; RSI(14) and RSI(21) of one component version land as two series; a different file for an existing frozen key is refused unless marked a correction with a reason | any two of these share a key, or the different file is accepted silently | F2 |
| 14 | P-MARKS | DR3 | a result that read 2019 stays unmarked after a month freezes, after an open-month update and after a correction to March 2024; a result that read March 2024 shows "corrected" | a data append marks any result "superseded", or a correction marks a result that did not read that month | F4 |
| 15 | P-CTSCOPE (exists) | DR5 | as §11 states | as §11 states | — |
| 16 | P-NOTRADE | DR5 | the allow-list `is_replicable` returns false for `qmx/ctrader-demo`, `qmx/ctrader-live`, `qmx/crypto` and `qmx/backup-payload-key`, and true only for `qmx/read/*`, `qmx/data/*` and model-provider rows; adding a key whose probe finds a live account it can trade stores nothing on the PC and shows `needs_you` | any of those names replicates, or a live-trade key is stored on the PC | F28, F29 |
| 17 | P-CTREFRESH | DR5 | on demo, the server refreshes the read app's grant and the PC's next forwarded read succeeds; a grant under a second app registration still works after that refresh; whether a second grant for the same cTrader ID under one app revokes the first is recorded | the refresh breaks the PC's forwarded read, or breaks the other app's grant (then trading servers need his decision on a separate cTrader ID) | F27 |
| 18 | P-CT2CONN | DR5 | on demo, with the read app's demo connection held on the server, a second demo connection with the same app is opened from the PC and what happens to the first is recorded; every read in the design still works with one holder | a read path in the design turns out to need two connections under one app | F32 |
| 19 | P-DUKA (extended) | DR6 | dukascopy-node 1.50.0, QMX's own bi5 fetch and the old raw bi5 agree for one month of EURUSD ticks (row count, first and last tick, prices, gaps); with one hour forced empty, the run retries it and the month does not freeze while that gap is unexplained | rows differ with no explanation, or the month freezes with the injected gap | F5, F47 |
| 20 | P-BAN | DR6 | two Binance runs on the server and a faked 429 with `Retry-After`: both wait until `slowed_until`, no request goes out before it, and no 418 comes back | any request inside the wait, or a 418 | F33 |
| 21 | P-UPL (extended) | DR7 | a 3 GB file through the PC door streams to the server with flat peak memory; after a cut the resume re-hashes the partial and the final hash matches; the PC staging copy is dropped only after two verified remote copies (kept while there is no bucket) | memory grows with the file, a resumed hash differs, or the PC copy is dropped early | F26 |
| 22 | P-DOCLING (exists) | DR7 | as §11 states | as §11 states | — |
| 23 | P-REDACT | DR10 | a token-shaped value written into a log line, a span attribute and a heartbeat field never reaches the server's collector | it appears in any exported record | F43 |
| 24 | P-OO (exists) | DR10 | as §11 states | as §11 states | — |
| 25 | P-GPU (exists) | DR13 | as §11 states | as §11 states | — |
| 26 | P-TAINT, P-SRCH (exist) | S-30 paging work | as §11 states | as §11 states | — |

P-MERGE ran in the first pass and passed.

### What still needs him (plain words, minimal)

1. **The cloud bucket** (§12 item 1, corrected by the fix-check 58). Nothing waits for it, but until it exists every file made on the server has one copy, and the old 10 GB cannot leave his C: drive. *Recommended: yes, R2.*
2. **Freeing the old 10 GB** (unchanged, §12 item 2), once the server and the bucket each hold a checked copy. *Recommended: yes.*
3. **Ruling 135 is the lead's decision**, written in file 26 for him to read. If he disagrees, the key rules change and nothing else does.

His steps, not decisions: sign in once on cTrader with the read-only ("accounts") scope for the read connection on the server; if a cTrader key already on his PC turns out to trade a live account, replace it with a read-only one (QMX says so on the row); when a trading server is set up, register a cTrader app for that server alone and enter its trading key there. (Accepting a month's gaps is no longer his step: fix-check 58, N7.)

### Lint and files

`python -I C:/Users/Mubarak/Desktop/QMX/.claude/skills/bmad-architecture/scripts/lint_spine.py --workspace <dir>`: 0 findings on all three spines after this round. Files changed: this file (in place where 57 named a contradiction, plus this section); `26-operator-rulings-and-alignment.md` (ruling 135); `architecture/library-and-data/` (ARCHITECTURE-SPINE: AD-10, AD-12, AD-14, AD-16, AD-19, AD-22, AD-25 to AD-28, conventions, Stack, Deferred; MIGRATION: rehearsal, epoch, "When the server is lost"; OPEN-DECISIONS: what works without the bucket; `.memlog.md`); `architecture/workflow-engine/` (ARCHITECTURE-SPINE: AD-28, AD-30, AD-65, AD-67 to AD-70; SOLUTION-DESIGN §30.1 and §30.2; HARNESS-REQUESTS H60 and H61; `.memlog.md`); `architecture/lab-and-pods/` (AD-20; `.memlog.md`); `UI-HANDOFF.md` §17 items 2, 6, 7, 8, 12 and 13.

---

## Fix-check applied (58)

Date: 2026-10-22, night. The last design round before planning: the fixes of `58-data-round-fix-check.md` (47 verdicts on review 57: 35 fixed, 10 partial, 1 regressed, 1 deferred; 22 new findings: 7 high, 10 medium, 5 low; N9 and N10 on ruling 135; five scenario lines). BMad architecture skill, headless, amend mode, with `principle-subtract-before-you-add`; no sub-agents, so the reviewer gate is the deterministic lint plus this table. AD ids are stable: amendments sit in place, marked *Fix-check (58)*. Nothing committed.

**Code claims checked before acting** (`origin/engine/base` `8af1a1cd`, `git show`, no checkout). All held:

- `qmx_library/store.py` `_index_object` (L329-337) indexes text only from blobs present on that store (`if path.exists()`). `read_blob` (L851-870) fetches a missing durable blob from `upstream` and caches it, but does not re-index (N1).
- `_placed_by` (L788) asks "was this object ever a head at or before sequence n" over **all** refs. The F11 fix needs it filtered to the one ref (one line). `claim` (L1149) expires and is released, so it stops two looks at once, not one after another (F8).
- `qmb/src/qmb/host/replay.py` `read_recorded_replay_source` (L143-160) takes CT-10 archive receipt fingerprints from a QMF EvidenceStore and "builds quote pairs only from matching bid/ask observations" (N2).
- `qmx_router/vault.py` (L1-14): "This module never moves" keys; the original stays in the PC's Credential Manager; "Deletion publishes a tombstone"; the node copy keeps the newest `updated_at` (N5).
- `qmx_broker/ctrader_transport.py` (L1): "Short read sessions" (F32, N16).
- `qmf/data/seal.py` (L2-6): the seal is "the newest sealed window (`registry:historical_holdout_months`, approximately twelve months)", and `authorize_final_look` journals the one look in that store's journal (F8, N15).

### What changed, in plain words

- **Search on the PC finds everything again.** The PC now also pulls the small text that QMX pulls out of books, pages and recordings on the server. Any file that arrives later is indexed again, so a search on the PC finds the words of something made on the server.
- **Honest copies.** A file he opens on the PC is only a cache copy. QMX may drop it to free space and fetch it again later, so opening files never fills C:. Without the cloud bucket, the screens say plainly: files made on the server have one copy, on the server. Files made on his PC have two.
- **QMB really changes.** QMB's backtest reader gets a second way in that reads the new price files. Bid and ask one-minute bars are handed over as a pair. A check proves that one month gives the same trades as the old reader.
- **Sign-ins live on one machine.** The cTrader sign-in page opens in his browser, but only the one-minute code passes through the PC. The home machine turns the code into the key and keeps it. The key copy QMX sends between his machines carries plain keys only, never a sign-in. So no stale copy sits on the PC, and deleting on one machine cannot delete on another. Each trading server gets its own cTrader app.
- **Months close by themselves.** Each kind of data has its own rule for when a month is complete. A month whose gaps one re-fetch cannot fill closes with those gaps written down. His click is needed only to re-open a month. A fill or calendar change that arrives late lands as an automatic correction. The open month of data that cannot be downloaded again (his fills, calendar revisions) is backed up after each batch of saves.
- **Checks gate the right step.** Each check now runs where it can pass. A check on an outside fact runs before the work starts. A check on new code must pass before that work merges and before the real step on his machines. Every check has a pass line and a fail line. Every fix sits in a named work item.

### Finding → outcome

A = applied. L = Library spine, E = engine spine, Lab = Lab spine.

| # | Verdict in 58 | Outcome | Where | What was done |
|---|---|---|---|---|
| F6 | Partial | A | L AD-28 | A PC-born partition is pinned in the PC cache, never evicted, until the server door's `commit` verifies it |
| F8 | Partial | A | L AD-28, Lab AD-5 | The claim is withdrawn (subtraction). Only the primary's door serves `final_look`, so `seal.py`'s one journal decides every look; other doors forward and wait. P-FINALLOOK |
| F10 | Regressed | A | L AD-10, AD-27; D-2 | Closed by N1 and N3 below: text slots sync, fetched blobs are cache copies, the no-bucket state is stated truthfully |
| F11 | Partial | A | L AD-14; P-REPLAY | A replay succeeds when the intended object was ever placed on that ref (`_placed_by`, filtered to the ref). P-REPLAY gains the "head moved past" case |
| F14 | Partial | A | L AD-16; MIGRATION "When the server is lost" | The no-bucket branch names exactly what is lost (server-born blobs never opened on the PC, minus text slots). P-SERVERLOST drills both branches. Fencing as in N13 |
| F16 | Partial | A | L AD-14, E AD-65; UI-HANDOFF §17.6 | Refuse only an entry whose kind or schema version the reader lacks, with `needs_update` naming the side behind. Mixed versions keep syncing |
| F19 | Partial | A | MIGRATION data-round paragraph and fix-check (1) | The false premise ("the mirror has written every save since LIB1") is withdrawn. P-REHEARSE compares to step 0 minus the filtered junk (N18) |
| F21 | Partial | A | L AD-10; OPEN-DECISIONS; §12; MIGRATION | The no-bucket mode is described truthfully (N3), and fetched blobs no longer pin C: |
| F23 | Not fixed (deferred) | Logged, unchanged | L Deferred | Still deferred with its revisit condition |
| F27 | Partial | A | E AD-28, AD-67; L AD-12; ruling 135 reworded | Closed by N5 and N9 |
| F32 | Partial | A | E AD-67; D-8 | `qmx-broker`'s short read sessions are rewired to the home host's session (N16). One app per trading server (N10) |
| F33 | Partial | A | E AD-67, AD-68 | Adapters declare `limit_scope: connection \| egress`. For an `egress` provider (Binance), `slowed_until` is kept per (provider, egress IP) on that machine. P-BAN covers two connections on one address |
| N1 | High | A | L AD-10, AD-27; S-30 | Text slots (`text`, `transcript`, and any slot marked `index: true`) sync with the manifests. A blob arriving by sync or fetch re-indexes the objects that name it. P-SYNC-DISK proves a PC search finds server-extracted words |
| N2 | High | A | L AD-25, AD-28; E AD-31; Lab AD-5; D-5, D-6; S-09 | QMB's replay reader gains a typed-partition entry point (fingerprint, world, seal and split checks kept). `materialise` returns bid and ask bar series as a monthly pair; ticks keep both sides in one row. D-5's "barely changes" and D-6's "byte-identical" are corrected. P-QMBREAD in DR4 |
| N3 | High | A | L AD-10, conventions; OPEN-DECISIONS; MIGRATION; §12; UI-HANDOFF §17.13 | A fetched blob is a cache copy, evictable. The two-copy rule binds only blobs born on that store. Without the bucket, files made on the server have one copy, and the screens say so. The bucket stays his call, recommended before the flip |
| N4 | High | A | probe list and work items below; §10, §11 pointers | Probes are split into premise probes (before a work item starts) and acceptance probes (before it merges and before the real-home step they protect). Torn logs, fsync and rename retry are in W2. The full-disk rule and memory guard are in W4. The version check is in W5 |
| N5 | High | A | E AD-28, AD-67; L AD-12; MIGRATION fix-check (2); ruling 135 | The home exchanges the code. The PC's loopback receiver forwards the code and keeps nothing. OAuth tokens and trade keys are never vault entries: no seal, no copy, no tombstone, no re-seal overwrite. The allow-list moves static keys only. Existing `qmx/ctrader-*` entries are re-filed or removed locally |
| N6 | High | A | L AD-16, AD-25; E AD-68; S-19, S-24 | Each kind declares its freeze rule (gap check; provider files with checksums; month end plus the provider's settlement delay for fills and calendars). Rows are ordered by observation time for bitemporal kinds, so a late fill or revision is an append. Late rows for a frozen month become an automatic correction. The open file of a non-redownloadable series is pushed to the bucket after each commit batch |
| N7 | High | A | L AD-25; E AD-68; UI-HANDOFF §17.2; SOLUTION-DESIGN §30.1 | A month freezes with its gaps recorded once one re-fetch returns the same gaps. Data health lists such months as information. His click is needed only to re-open a month or hold a series open (his override). His "accept the gaps" step is withdrawn |
| N8 | Medium | A | ruling 135 in 26 | The tension with ruling 117 is named in one bullet |
| N9 | Medium | A | E AD-67; §4 table | The home belongs to the credential. For cTrader, it belongs to the app registration. A save that gives one credential two homes is refused |
| N10 | Medium | A | E AD-67; ruling 135; §4; S-28 | One cTrader app registration per trading server, approved by Spotware first, listed among his steps for each server |
| N11 | Medium | A | E AD-67; §4 | The trading server's consent follows the N5 contract under its own app. Its secret is entered only there. The code reaches it by a redirect to its tailnet address or through the PC's receiver. The trading-node session builds on this |
| N12 | Medium | A | probe list | P-CTREFRESH is split: the same-app half runs before W13; the cross-app half runs before the first trading server |
| N13 | Medium | A | L AD-14, AD-16; MIGRATION step 1 | Server loss first asks him to stop the old host when it is reachable. A store that learns a higher epoch parks its moves as `merge-conflict` items |
| N14 | Medium | A | probe list | Every probe has a decision line. P-MDREAD is split: read-back before the import; read times measured after W11 and W14 |
| N15 | Medium | A | L AD-28; UI-HANDOFF §17.12 | When the sealed span exceeds `historical_holdout_months`, an inbox task offers the move (his click) |
| N16 | Medium | A | E AD-67; D-8; SOLUTION-DESIGN §30.2; W13 | `qmx_broker/ctrader_transport.py` reads go through the home host's `host` adapter session |
| N17 | Medium | A | as F16 | |
| N18 | Low | A | MIGRATION fix-check (1); P-REHEARSE | The baseline excludes the filtered rows, listed by id. A hash of `~/.qmx` before and after proves his real home untouched |
| N19 | Low | A | probe list | P-OOM runs under a memory limit on a scratch cgroup. P-BAN uses a 418-answering stub. P-NOTRADE uses a stub adapter that returns a live trade account. P-SERVERLOST drills the no-bucket branch. P-SPLIT covers an offline restored PC (moves parked as conflicts) |
| N20 | Low | A | E AD-67; UI-HANDOFF §17.8 | One reading word per connection. `needs_you` covers a connection not yet set up or signed in. The five setup words stay on Machines |
| N21 | Low | A | L AD-22, AD-25; P-MARKS | Open-month reads are recorded as (key, range) and corrections as (key, range, reason); `corrected` is computed on overlap |
| N22 | Low | A | §9.1 S-28; §9.2 default 14; MIGRATION; §0 item 7; L AD-16 opening; H61; E AD-67 | All stale text fixed. H61's check now proves `broker_read` and Library content rows are refused. Read keys are re-filed under `qmx/read/*` at W13. The host session relays one history page at a time; the partition is written in the step's child process |

**Ruling 135 (N9, N10; F27, F28).** Its substance is unchanged: no key that can trade live money is kept where agents work, and each sign-in has one home that alone refreshes it. Its wording in file 26 now says four things. The sign-in code goes to the home, which alone keeps the tokens. The home belongs to the sign-in, not to a row. Each trading server has its own cTrader app. The tension with ruling 117 is named.

**Scenario lines corrected (§9.1):** S-09 (N2), S-19 and S-24 (N6), S-28 (N10, N11, N22) and S-30 (N1). S-25 also changed (N3). The other 24 lines hold.

**Counts.** Highs applied 7 of 7. F10, the regressed fix, is closed. Partials applied 10 of 10. Mediums applied 10 of 10. Lows applied 5 of 5. Rejected 0. Deferred 1 (F23, unchanged).

### Probes: final list, in order

Each probe runs the real code on scratch roots, scratch cgroups, stubs or demo accounts. A failure is a finding to fix, never a reason to add a limit. There are three kinds:

- **Premise** probes test an outside fact. They run before the work item that relies on it starts.
- **Acceptance** probes test new code. They must pass before that work item merges *and* before the real-home step in the "Gates" column.
- **Measure** probes record a number. PASS means the value is recorded as the Settings default and live readings show it fits. FAIL means a process is killed or a service does not start.

| Order | Probe | Kind | Built in | Gates | PASS when | FAIL when |
|---|---|---|---|---|---|---|
| 1 | P-TORN | acceptance | W2 | W2's merge; W3's real import | With the last line of the ref, edge and annotation logs cut mid-line, and separately NUL-filled, the store opens. The line is in `quarantine/` and `library:torn:<log>` is raised. A bad middle line opens the store read-only with an incident. Every other record reads back. A rename under a held Windows handle retries and lands | the store refuses to open, a torn line is read as a record, no alarm, or a rename is lost |
| 2 | P-REHEARSE | acceptance | W3 | the switch-over on his real home | The switch-over is run on a copy of his `~/.qmx` in a scratch root. Item counts per kind, version chains, links, memo rows and blob hashes equal MIGRATION step 0's numbers minus the filtered test junk, which is listed by id. A hash of his real `~/.qmx` is the same before and after | any count or hash differs beyond the listed ids, the importer stops, or the real home's hash changed |
| 3 | P-DISKFULL | acceptance | W4 (uploads part in W15) | the flip (W7); uploads switched on (W15) | On a scratch volume filled to the floor, the price cache, transient blobs, the telemetry queue and then fetched cache copies give way first, in that order in the log. A Library save past the floor is refused with `disk_full` and a plain message. No half-written file exists. An upload stops whole and resumes later | a half-written file, a lost outbox entry, or a Library write refused while expendable data remained |
| 4 | P-OOM | acceptance | W4 (again with Docling in W15) | the flip (W7); extraction switched on (W15) | A scratch cgroup's memory limit is set below the combined need of Docling on a 400-page PDF, a big door read and two agent nodes started together. The kernel kills a child process, never `qmx_host`. The Library and the door keep answering. The killed node fails with a memory reason and is retried. The run counts only if the limit forced a kill | `qmx_host` is killed, or the Library or the door stops answering |
| 5 | P-SYNC-DISK | acceptance | W5 | the flip (W7) | Set `primary = server` with 5 GB of originals plus their text slots on the scratch server. One PC sync copies only text-slot blobs. A PC search for a phrase found only in a server-extracted text finds the item. Opening one item fetches exactly its other blobs. Under disk pressure a fetched blob is evicted and comes back on the next open. A PC-born blob with fewer than two remote copies is never evicted. The sync asks for ref moves since a sequence | a non-text blob is copied without being opened, the phrase is not found, a PC-born blob is evicted early, a fetched blob cannot be evicted, or a sync lists every object id |
| 6 | P-REPLAY | acceptance | W5 | the flip (W7) | The connection is killed between the server's commit and its reply. (a) The outbox replay succeeds. (b) In a second run, a server workflow moves the same ref on before the replay. The replay still succeeds and leaves the newer head in place. There is no `merge-conflict` and no second item | a conflict, a `stale_head`, a duplicate, or the newer head rewound |
| 7 | P-SPLIT | acceptance | W5 | the flip (W7) | After a flip to epoch E, a PC is restored with `primary = pc` and epoch E-1 and works offline, moving its own `main`. At its first sync it learns E. It stops acting as primary, raises `library:epoch:<store>`, and its offline moves appear as `merge-conflict` items. The server's `main` heads are unchanged. A scratch old server cut off while running its cron behaves the same on reconnect | the server's `main` moves to an older head, or an offline move is lost or applied silently |
| 8 | P-VERSION | acceptance | W5 | the flip (W7) | When the PC runs a newer `qmx_version` with the same kinds, sync and forwards work. When the PC writes a kind schema version the server lacks, that entry is refused with `needs_update` naming the server: it stays in the outbox, other entries land, and it lands after the server updates. The reverse case names the PC | a mixed version with the same kinds is refused, a host takes an entry it cannot read, the message names the wrong side, or a save is lost |
| 9 | P-LAT (exists) | acceptance | W5 | the flip (W7) | With the PC as replica and cache over the tailnet, list, search and card reads are served from the PC replica, and the measured screen times are recorded | a list or search screen waits on a tailnet round trip (a latency bug fixed on the PC side, never a reason to keep the PC primary) |
| 10 | P-VAULT-AWAY | acceptance | W6 (connection keys again in W13) | the flip (W7); server-homed connections (W13) | With the PC switched off, a restarted server opens its own model keys from its own key file and the relay serves a model call. After W13, a server-homed health check also runs. With the server's key file removed, `vault:unavailable:contabo` is raised | a server job waits for the PC, or fails without the incident |
| 11 | P-NOTRADE | acceptance | W6 (allow-list); W13 (add time, tokens) | the flip (W7); the first real connection added (W13) | (W6) `is_replicable` is false for `qmx/ctrader-demo`, `qmx/ctrader-live`, `qmx/crypto`, `qmx/backup-payload-key` and any token entry, and true only for `qmx/read/*`, `qmx/data/*` and model-provider rows. (W13) A stub adapter returns a live account with trade scope: adding that key stores nothing on the PC and shows `needs_you`. A cTrader demo grant for a server-homed connection leaves no token in the PC's keyring or in the vault document. Deleting that connection from the PC publishes no tombstone and removes the token on the server | any of those names replicates, a live-trade key or any token is kept on the PC or in the vault, or a deletion spreads by tombstone |
| 12 | P-SERVERLOST | acceptance | W7 | the flip (W7) | Two scratch roots, run twice: once with a scratch bucket folder, once without. The server root is wiped, or a scratch old server is cut off while still running. MIGRATION's procedure asks to stop the old host if it is reachable, promotes the PC (epoch raised), lists the stale server-owned refs, and restores a new server and re-pairs it. With the bucket, every object the bucket held reads back by hash. Without it, the objects named lost are exactly those born on the server and never opened on the PC (text slots excluded), and everything else reads back. An old server that comes back parks its moves as conflicts | a step needs an action the procedure does not name, an object the bucket held does not come back, or the lost list is wrong |
| 13 | P-HS (exists) | premise and measure | — | Hindsight moved to the server (W8) | Hindsight 1.1 with a system Postgres on the server: memory at idle and in a retain burst at the default worker slots is recorded as the admission reading, and the host, the collector and at least one measured agent session still fit the live free RAM. Recall parity with the PC holds on a fixed query set | the process is killed, the service does not start, or recall differs |
| 14 | P-MDREAD-DUCK | premise | — | W9 starts | A scratch file in the planned typed schema (int64 `t`, int64 scaled prices, the kind's columns), written by pyarrow 25.0.1 in row groups, is read row for row by DuckDB 1.5.5 | any column reads differently or the read fails (then the schema changes before W9) |
| 15 | P-MDREAD (read-back) | acceptance | W9 | W9's merge; the old-ticks import (W11) | One real month of EURUSD ticks written by the new writer reads back row for row. A second write of the same rows gives the same fingerprint and no new file. File size and peak RAM for one week and for one month are recorded | the read-back fails or differs, the fingerprint changes between two writes, or peak RAM rises in step with the rows (a month near four times a week) |
| 16 | P-KEY | acceptance | W9 | the old-ticks import (W11) | Bid and ask m1 for one month land as two series with two cards. Ticks land as one series with both sides. RSI(14) and RSI(21) of one component version land as two series. A different file for an existing frozen key is refused unless marked a correction with a reason | any two of these share a key, or the different file is accepted silently |
| 17 | P-FREEZE | acceptance | W9 | the old-ticks import (W11); downloaders and feeds (W14) | (a) A ticks month with one hour forced empty stays open after its first fetch. It is re-fetched once and freezes with the gap in `quality` when the re-fetch returns the same gap, with no click. (b) A fills month freezes at month end plus the declared settlement delay, with no gap check. A fill for that month arriving after the freeze lands as a correction listing the old and new fingerprints with its reason. A calendar revision in an open month is an append. (c) After a commit batch, the open file of a non-redownloadable series is in the scratch bucket under its fixed name, and the next batch overwrites it. (d) A re-opened month is re-fetched | a month waits for a click, a late row is refused, a fill month waits on a gap check, or the open file is missing from the bucket |
| 18 | P-MARKS | acceptance | W9 | the old-ticks import (W11) | A result that read 2019 stays unmarked after a month freezes, after an open-month update and after a correction to March 2024. A result that read March 2024 shows "corrected". A result that read an open-month range shows "corrected" only when a recorded open-month correction overlaps that range | a data append marks any result "superseded", or a correction marks a result that did not read the corrected rows |
| 19 | P-FINALLOOK | acceptance | W10 | the door switched on (W10's merge) | A final look requested on the PC is forwarded to the primary's door and journaled there with its `touched` edge. A second final look for the same family and window, from either machine, at once or later, is refused. With the primary unreachable, the PC's request waits and serves nothing | two looks are journaled, or a door off the primary serves a look |
| 20 | P-MDREAD-TIMES | measure | — | the DuckDB 2.0 bump; direct bucket reads (Library Deferred) | Read times for one month of ticks and for every year of m1 the store then holds are recorded from the PC cache, the server disk, the server's door over the tailnet and a bucket fetch. Run after W11, then again after W14 | the read is killed or does not finish |
| 21 | P-QMBREAD | acceptance | W12 | W12's merge; backtest tools bound for agents | QMB replays one month from the typed partitions twice: from ticks, and from bid and ask m1 materialised as a pair. Both give the same trades as the same rows admitted through the CT-10 boundary into a scratch EvidenceStore and read the old way. A missing ask partition is refused, never used as half a pair | any trade differs, or a one-sided pair is accepted |
| 22 | P-CTSCOPE (exists) | premise | — | W13 starts | Each refuses to trade: a cTrader `accounts`-scope token cannot place an order on a demo account; an MT5 investor login reports `trade_allowed` false; a read-only exchange key reports no trade permission | any of them can trade (then that credential type is never labelled `read`, and W13 labels it `trade`) |
| 23 | P-CTREFRESH (same app) | premise | — | W13 starts | On demo, with a scratch script under the read app: a refresh returns a new pair that reopens the session, and the old pair is dead. Whether a second grant for the same cTrader ID under the same app revokes the first is recorded in the adapter declaration | the new pair cannot reopen the session (then the health workflow is redesigned before W13) |
| 24 | P-CT2CONN | premise | — | W13 starts | On demo, the read app's demo connection is held on one machine and a second demo connection under the same app is opened from another. The second is refused (error 67) or drops the first with an event, and which one is recorded in the adapter declaration | the first connection dies with no event (then the health walk must detect it before W13 merges) |
| 25 | P-DUKA | premise | — | the Dukascopy downloader (W14) starts | dukascopy-node 1.50.0, QMX's own bi5 fetch and the old raw bi5 agree for one month of EURUSD ticks: row count, first and last tick, prices and gaps | rows differ with no explanation |
| 26 | P-BAN | acceptance | W14 | the first real Binance download | Two Binance connections on one server (spot and futures) talk to a local stub that answers 429 with `Retry-After`, then 418 to any request inside the wait. Both connections wait until the shared `slowed_until` for that egress address, and the stub records no request inside the wait | any request lands inside the wait |
| 27 | P-DOCLING (exists) | premise and measure | — | extraction switched on (W15) | Time and peak memory for a 400-page PDF and one hour of audio on the server's CPU, each in a child process, are recorded as the step's declared memory default, and both finish | the process is killed or does not start |
| 28 | P-UPL | acceptance | W15 | uploads switched on | A 3 GB file goes through the PC door and streams to the server with flat peak memory. After a cut, the resume re-hashes the partial and the final hash matches. The PC staging copy is dropped only after two verified remote copies; it is kept while there is no bucket | memory grows with the file, a resumed hash differs, or the PC copy is dropped early |
| 29 | P-TAINT, P-SRCH (exist) | measure | — | search paging on (W15) | On 100,000 items, the marks walk for one shown object and the search answer sizes are recorded, and the grounder's precision against items' own tags is recorded as the baseline. The walk runs per shown object, never as a batch | a walk or a search is killed or does not finish |
| 30 | P-OO (exists) | premise and measure | — | OpenObserve installed (W18) | OpenObserve's memory and disk per day under a day of QMX telemetry are recorded as the Settings defaults and fit the server's live readings | the process is killed or does not start |
| 31 | P-REDACT | acceptance | W18 | exporters switched on | A token-shaped value written into a log line, a span attribute and a heartbeat field never reaches the server's collector | it appears in any exported record |
| 32 | P-GPU (exists) | premise and measure | — | the training template ships (W21) | A small model trained on the PC's Quadro T1000 from cached partitions: time, GPU memory and disk used are recorded as the template's defaults | the process is killed or does not start |
| 33 | P-CTREFRESH (cross app) | premise | — | the first trading server's setup (trading-node session) | On demo, a grant under a second app registration for the same cTrader ID still works after the read app's grant is refreshed. Which redirect cTrader accepts for that app (its tailnet address, or the PC's receiver) is recorded | the refresh breaks the other app's grant (then trading servers need a separate cTrader ID: his decision then) |

P-MERGE ran in the first pass and passed.

### Work items, in build order

Each item is one PR, built by one Opus builder, with one build and one check. Its acceptance probes pass before it merges. Premise probes pass before it starts. **Real step** names the act on his real home or the real server that waits for the item's acceptance probes. "Fixes" names the review findings whose code the item builds.

| # | Work item | Builds (fixes) | Premise first | Acceptance | Real step | After |
|---|---|---|---|---|---|---|
| — | His merges of the stacked PRs 164, 166, 167 (chain B) and 165 | — | — | — | — | — |
| W0.1 | **DEL3a**: remove the three money-word call sites and their two tests; drop `qma-core` from three `pyproject.toml` files; delete `test_qma_callers.py` with its script (§8 item 1) | — | — | each touched package's tests and type check | — | his merges |
| W0.2 | **DEL3 with the rest of DEL4**: the old core, wire and daemon with their importers; `langchain`, `langgraph`, `deepagents`, `openai-codex`; relock (§8 items 2-3) | — | — | suites and type check | — | W0.1 |
| W0.3 | **The rest of DEL2**: `qma/serve.py`, the RTR0 shims, `s21c_egress.py` (§8 item 4) | — | — | suites | — | W0.2 |
| W0.4 | **RUN1c**: the maintenance loop off `runs_list` and `jobs`; weekly backup as a cron script workflow (§8 item 5) | — | — | suites; the two live lanes repointed | — | W0.3 |
| W0.5 | **DEL3b**: the harness's `money_words.py` and its three users (§8 item 6) | — | — | suites | — | W0.2 (does not block data work) |
| W1 | **DR0, save the old ticks** (script, no product code): rclone with checksums of the old 10 GB and the risk-lab CSVs to the server (and the bucket once it exists); counts and hashes recorded | — | — | `rclone check` clean; counts and hashes recorded | — | nothing; most urgent |
| W2 | **DR1a, store durability**: torn-tail quarantine, read-only open on a bad middle line, fsync before rename, Windows rename retry | F13, F20 | — | P-TORN | W3's real import | W0.1 |
| W3 | **DR1b, the Library switch-on on the PC**: import `library.db` (junk filtered) and `artifacts.db`; flip the `library_*` rows; retire the old file read-only; `domain.library` and copilot search on the new store; `app_runtime()` attaches the sink; backup list; QMB's registry projection through the port | F19, N18 | — | P-REHEARSE | the switch-over on his real home | W2 |
| W4 | **DR2a, host guards**: the per-machine full-disk rule (order of giving way, refuse whole, measured floor); admission reserving declared memory until measured, heavy work in child processes, the host's lower out-of-memory score; capacity from live readings with the invented constants removed | F22, F39, D-11 | — | P-DISKFULL, P-OOM | the flip (W7) | W3 |
| W5 | **DR2b, sync and outbox**: the Library service inside the server's `qmx_host`; selective sync with text slots and re-index on blob arrival; cache copies versus born blobs; the idempotent outbox (ever placed on the ref); `refs/primary` with its epoch, fast-forward-only pushes, mirror refusal, stale-epoch moves parked as conflicts; the version check by kinds and schema versions with `needs_update`; pending writes shown | F10, F11, F12, F15, F16, F18, N1, N3, N13, N17, N19 | — | P-SYNC-DISK, P-REPLAY, P-SPLIT, P-VERSION, P-LAT | the flip (W7) | W4 |
| W6 | **DR2c, vault and keys**: each machine's own vault key pair and the server's service-user key file; replication by allow-list of static keys; the ask-the-PC path removed; tokens and trade keys never vault entries; the host route that hands a secret once to its home | F29, F30, N5 | — | P-VAULT-AWAY (model keys), P-NOTRADE (allow-list) | the flip (W7) | W4 |
| W7 | **DR2d, the flip and the server-loss procedure**: tooling for MIGRATION step 8 (quiesce, push until equal, his click raises the epoch); the server-loss procedure (stop the old host, promote, list stale refs, rebuild, re-pair); server-to-bucket push of Library objects after each commit batch | F14, F24, N13 | — | P-SERVERLOST | **the flip to `primary = server` (his click)**, after every acceptance probe of W4 to W7 passed | W5, W6 |
| W8 | **DR2e, Hindsight on the server** with a system Postgres; banks rebuilt from Library rows | — | P-HS | recall parity on the fixed query set | Hindsight switched on the server | W7 |
| W9 | **DR3a, price partitions and series rules**: the typed-column writer with its streamed fingerprint; the key with subject and variant; the open-month file; freeze rules per kind with the one-re-fetch freeze; late rows as automatic corrections; (key, range) reads and corrections; the card writer and `dataset` fields; the series claim; the bucket push of non-redownloadable open files | F1-F5, N6, N7, N21 | P-MDREAD-DUCK | P-MDREAD (read-back), P-KEY, P-FREEZE, P-MARKS | the old-ticks import (W11) | W7 |
| W10 | **DR3b, the market-data door**: a module in each host and the only writer, through `commit`; seal, splits with a gap, `purpose`; `data_scope` on passes; `final_look` served only by the primary; the seal's inbox task; PC-born partitions staged and pinned; handles and child-process reads; agent data tools filled at start-up (H59); `datasets.json` retired | F6, F7, F8, F9, F40, N15 | — | P-FINALLOOK; a sealed read refused with its reason | door switched on for agents | W9 |
| W11 | **DR3c, import the old ticks** from the server copy as partitions with cards (a run of W9's importer on real data, not new code) | — | — | the import's counts match W1's record; P-MDREAD-TIMES afterwards | **the import on the real server** | W1, W10 |
| W12 | **DR4, backtests through the door**: QMB's typed-partition entry point and the bid/ask pair; one landing step for `backtest-result`; old shapes imported; backtest tools bound; the synthetic-data template | N2 | — | P-QMBREAD | backtest tools bound for agents | W10 (W11 for real data) |
| W13 | **DR5, Connections**: the registry; scopes and probes per adapter; the health workflow; one reading word; the credential's home (per app for cTrader), refused on save when split; code exchange on the home with the PC's receiver forwarding; tokens in the home's key store; `qmx_broker` reads through the home's session; `limit_scope` with `slowed_until` per (provider, egress IP); the `brokers` section read once; existing `qmx/ctrader-*` entries re-filed or removed locally | F27, F28, F31-F38, N5, N9, N16, N20, N22 | P-CTSCOPE, P-CTREFRESH (same app), P-CT2CONN | P-NOTRADE (add time, tokens), P-VAULT-AWAY (connections) | his first real connection added | W6, W7 |
| W14 | **DR6, downloaders and feeds**: the `feed` template; Dukascopy through dukascopy-node; Binance bulk; CCXT top-up; broker history; the calendar feed (bitemporal); old fetchers retired (removing the PC task is his approval) | F5, F33, F36, F47, N6, N7 | P-DUKA | P-BAN; P-FREEZE (b) on a real feed; P-MDREAD-TIMES afterwards | the first big downloads | W10, W13 |
| W15 | **DR7, ways in**: the upload door; `source` fields; the Docling extraction workflow; chunked whole-text search; body and text limits removed; the `save_source` step; captures | F26, F41 | P-DOCLING | P-UPL, P-DISKFULL (uploads), P-OOM (with Docling), P-TAINT and P-SRCH measured | uploads and extraction switched on | W5 |
| W16 | **DR8, version control reaches agents**: line and JSON merge; history and blame; chat rows; engine claims at node start | — | — | P-MERGE (ran) plus the merge tests | — | W3 |
| W17 | **DR9, workflows read the Library**: the `library` node switched on; `@` references in workflow inputs; the mini-app switches | — | — | its journeys | — | W3 |
| W18 | **DR10, monitoring**: OTel at the write points after redaction; one collector and OpenObserve on the server; CLI and Hindsight telemetry; Library and Lab heartbeat facts; the data health rows; the observer token and runbook skill | F42-F46, N22 (H61) | P-OO | P-REDACT; H61's check | exporters switched on | W7 |
| W19 | **DR11, real-numbers sweep**: any invented constant left after W4 and W15 | — | — | a grep finds none of the removed figures | — | W4, W15 |
| W20 | **DR12, kinds and lineage**: the `trade` kind and journal imports over fill partitions; `component_type`; funnel templates write edges; card and page declarations for every kind | — | — | its journeys | — | W3, W9 |
| W21 | **DR13, the Lab workspace and ML on the PC**: projects, New… by level, workspace state, Tuesday's run, the data panel, the GPU placement and the training template | — | P-GPU | its journeys | — | W10, W17, W20 |
| W22 | **DR14, placement by data locality**: the runner sets placement from `runs_on` and locality; remote reads through the server's door | — | — | its journeys | — | W10, W18 |

Every data item's journeys also pass on his real home and the real server (file 54 default 16). Once their dependencies land, W13 to W19 may run in any order. W8 and W18 need only W7.

### Genuine operator calls (minimal)

1. **The cloud bucket** (§12 item 1, now with its real consequence). Without it, every file made on the server has one copy, and so does every price month that cannot be downloaded again. *Recommended: yes, R2 (about $2-3 a month), opened before his flip in W7.* Nothing else waits on it.
2. **Freeing the old 10 GB** (§12 item 2, unchanged): once the server and the bucket each hold a checked copy. *Recommended: yes.*
3. **Ruling 135** stays the lead's decision. Its new wording names the tension with ruling 117, so an overrule is informed. If he overrules it, only the key rules change.

These are his steps, not decisions. He clicks the flip in W7. He signs in once on cTrader in his browser; the key is kept on the server. He approves removing the old calendar task on his PC. He signs up for OpenObserve's free tier at W18. For each trading server, later, he registers that server's own cTrader app and enters its trading key there.

### Lint and files

`python -I C:/Users/Mubarak/Desktop/QMX/.claude/skills/bmad-architecture/scripts/lint_spine.py --workspace <dir>`: 0 findings on all three spines after this round. Files changed:

- This file: in place where 58 named stale or wrong text (§0 item 7, D-1, D-2, D-5, D-6, D-8, D-11, §4, §9.1, §9.2, §10, §11, §12, and two lines of the 57 section), plus this section.
- `26-operator-rulings-and-alignment.md`: ruling 135 reworded, substance kept.
- `architecture/library-and-data/`: ARCHITECTURE-SPINE (AD-10, AD-12, AD-14, AD-16, AD-22, AD-25, AD-27, AD-28, conventions, the container diagram), MIGRATION, OPEN-DECISIONS and `.memlog.md`.
- `architecture/workflow-engine/`: ARCHITECTURE-SPINE (AD-28, AD-31, AD-65, AD-67, AD-68), SOLUTION-DESIGN (the replicable-set row, §30.1 and §30.2), HARNESS-REQUESTS H61 and `.memlog.md`.
- `architecture/lab-and-pods/`: ARCHITECTURE-SPINE (AD-5) and `.memlog.md`.
- `UI-HANDOFF.md`: §17 items 2, 6, 8, 12 and 13.
