# 58 — Data round: fix-check of review 57

Date: 2026-10-22. Independent fix-check. **A fresh Opus checking Opus:** the checker is Claude Opus 5.5, the same model that wrote 55 and 57 and applied the fixes, so shared blind spots remain likely. Treat "FIXED" as "no gap found", not "proven". No sub-agents. Nothing committed. No design file edited. Lenses: BMad `bmad-review` verification-gap and edge-case-hunter, read and applied by hand.

**Inputs.** Commit `eba4a662` (applies 57) against `0a7419c2`. Also read: 55 "Edge-case review applied (57)", 56, 51, 54 (S-01 to S-30) and 26 (rulings 115-135). Code truth comes from `origin/engine/base` `8af1a1cd`, read with git show and git grep, no checkout. Proof levels: *pointed at* (file:line), *walked*. Nothing was run this time.

---

## 0. Plain words first

Most of the 47 fixes are really in the files and close their scenarios. Four fixes opened new holes:

1. **The PC now pulls the list of items but not their files.** That stops sync from filling C:. But the PC's search builds its index only from files on the PC, so on the PC a search misses the text of books, pages and feed items that were made on the server. And until the bucket exists, every file made on the server has exactly **one** copy anywhere, while the screen tells him "one copy off this PC".
2. **The new price-file writer is a format QMB cannot read.** QMB's replay reader reads the old archive receipts and pairs bid and ask inside one file. The design still says QMB "barely changes", but the files and the bid/ask split are both new.
3. **"One machine owns each sign-in" does not fit the vault that is built.** The vault leaves the original key on the PC and spreads a deletion to every copy. A cTrader token that the server refreshes therefore has two holders, and the stale PC copy can kill the live one.
4. **Most probes are scheduled "before" the very packet that builds the code they test,** so as written they cannot pass. Several fixes (torn logs, the full-disk rule, the memory guard) are not in any packet.

Ruling 135 fits cTrader's facts in substance: one live connection per app, and one owner for each refresh. Two details are missing. One owner per *grant* is needed, not per connection row. And each trading server needs its own app.

---

## 1. Verdict per finding of 57

FIXED = the fix is in the named files and closes the scenario. PARTIAL = something is missing (named). REGRESSED = the scenario is closed but the fix breaks something else. NOT-FIXED = not applied.

| # | Verdict | Checked where | Note |
|---|---|---|---|
| F1 | FIXED | L AD-25, Stack, D-1 | Typed writer, streamed pinned fingerprint, P-MDREAD before the import. QMB was not adopted: N2 |
| F2 | FIXED | L AD-25, conventions | `subject` and `variant` in key and card; `commit` refuses a silent replace. The bid/ask split collides with QMB's pairing: N2 |
| F3 | FIXED | L AD-25, D-1 | Open month is one replaced file. New holes in the open month: N6 |
| F4 | FIXED | L AD-22, AD-25, AD-33 | Marks come from partition fingerprints; `where` is computed at read. Open-month corrections: N21 |
| F5 | FIXED | E AD-68, L AD-25, D-4, P-DUKA | Flags set; a month freezes only after a gap check. The freeze rule overloads him: N7 |
| F6 | PARTIAL | L AD-28 | A PC-born partition waits in the PC *cache*, the first thing evicted on a full disk (AD-10), until the server commits it. It can be evicted before it ever reaches the server. Fix: pin it until the server's `commit` verifies it |
| F7 | FIXED | L AD-28, SOLUTION-DESIGN §30.1 | Seal moves only by his click. Side effect: N15 |
| F8 | PARTIAL | L AD-28 | A claim stops two looks *at once*, not one after another. Claims expire and are released on landing (`store.py` `claim`, L1149). The one-look rule lives in `seal.py`'s CT-13 journal (`authorize_final_look`), which is per store. Fix: only the primary's door serves `final_look`, so one journal decides |
| F9 | FIXED | L AD-28 | Handles and a child process |
| F10 | REGRESSED | L AD-10, AD-26, D-2 | The disk-fill scenario is closed, but N1 (search) and N3 (single copy without the bucket) follow from it |
| F11 | PARTIAL | L AD-14 | Success only when head **equals** the intended object. Case left open: the PC sleeps after the lost reply, a server workflow moves the same ref on, and the replay sees head ≠ intended, giving `stale_head` and a false conflict. Fix: success when the intended object was ever placed on that ref. `store.py` `_placed_by` (L788) already answers that. Add the case to P-REPLAY |
| F12 | FIXED | L AD-14, AD-19, MIGRATION | Epoch record, fast-forward-only pushes, `mirror` of owned refs refused. Fencing gap in server loss: N13 |
| F13 | FIXED | L AD-16 | Quarantine, read-only on a middle line, fsync. No packet builds it: N4 |
| F14 | PARTIAL | MIGRATION "When the server is lost" | The procedure exists. Its no-bucket branch (the likely state) loses every server-born blob the PC never opened, and P-SERVERLOST drills only the bucket branch. No fencing (N13) |
| F15 | FIXED | L AD-14, UI-HANDOFF §17.6 | |
| F16 | PARTIAL | L AD-14, E AD-65 | "A mismatch refuses" is strict equality. With "the server updates first", the older PC is then refused with the wrong message (`server_needs_update`), and every forward between hosts stops until every host updates. Fix: refuse only when a writer sends kinds or schema versions the reader lacks; name the side that is behind |
| F17 | FIXED | L AD-16 | AD-16's original rule (rclone PC→server) still opens the paragraph, overridden by the amendment. Tidy it (N22) |
| F18 | FIXED | L AD-10 | |
| F19 | PARTIAL | L AD-26, MIGRATION, D-2 | Rehearsal added. MIGRATION's data-round paragraph (line 13) still carries the false premise ("the mirror has written every save since LIB1"). P-REHEARSE compares against step 0 counts that include the junk the import filters (N18) |
| F20 | FIXED | L AD-16 | Retry on WinError 5/32; leaving the indexing exclusion to him is reasonable |
| F21 | PARTIAL | L AD-10, OPEN-DECISIONS, §12 | The no-bucket mode is stated but mis-described (N3). A PC upload stays on C: for good, and so does every server blob he opens |
| F22 | FIXED | L AD-10, Lab AD-20 | Order of giving way; writes refused whole. No packet builds it (N4) |
| F23 | NOT-FIXED | L Deferred | Logged on purpose, with a revisit condition; acceptable |
| F24 | FIXED | L AD-16 | Stale "nightly" left in 55 §9.2 default 14 (N22) |
| F25 | FIXED | L AD-16 | |
| F26 | FIXED | L AD-27, P-UPL | |
| F27 | PARTIAL | E AD-67, ruling 135 | The rule is right. The hand-over and the built vault contradict it (N5). The owner is keyed to the wrong unit (N9) |
| F28 | FIXED | E AD-28, AD-67, L AD-12, ruling 135 | No live-trade key on the PC; refused at add time. cTrader adds new accounts only by a new grant (56 §2), so a demo-only grant cannot quietly gain a live account |
| F29 | FIXED | E AD-28, L AD-12, P-NOTRADE | Allow-list. Existing read keys under `qmx/ctrader-*` need re-filing under `qmx/read/*` (N22) |
| F30 | FIXED | E AD-28 | Each machine has its own key pair; the server's key sits in a service-user file |
| F31 | FIXED | E AD-28, AD-67, AD-70 | `host` and `step` adapters; no non-model key on remote workers |
| F32 | PARTIAL | E AD-67 | One holder per (app, environment) is stated, but `qmx-broker`'s read tools still open their own **short read sessions** (`qmx_broker/ctrader_transport.py` L1). Rewiring them to the home session is in no blast radius (D-8, SOLUTION-DESIGN §30.2). Several trading servers on one trading app repeat the problem (N10) |
| F33 | PARTIAL | E AD-67, AD-68 | `slowed_until` is per **connection**. Binance limits **per IP** (56 §1). Two connections on one server (spot and futures, or keyless and keyed) still add up to a ban. Fix: key the shared wait by (provider, egress IP) for providers that limit per IP, as 57 proposed |
| F34 | FIXED | E AD-67, UI-HANDOFF §17.8 | |
| F35 | FIXED | E AD-67 | |
| F36 | FIXED | E AD-67, AD-68 | History pages pass through `qmx_host`'s session, while F39 says downloads never run inside the host; low (N22) |
| F37 | FIXED | E AD-67 | Read app only. The trading-server redirect: N11 |
| F38 | FIXED | E AD-28, AD-65, AD-67 | |
| F39 | FIXED | E AD-30 | No packet builds it (N4) |
| F40 | FIXED | E AD-68, L AD-28 | |
| F41 | FIXED | L AD-27 | |
| F42 | FIXED | E AD-69 | |
| F43 | FIXED | E AD-69, P-REDACT | |
| F44 | FIXED | E AD-69, H61 | H61's check column still tests only a manage row; it does not show that `broker_read` is refused (N22) |
| F45 | FIXED | E AD-65 | |
| F46 | FIXED | E AD-69, H60 | |
| F47 | FIXED | E AD-68, D-4 | |

**Counts:** FIXED 35, PARTIAL 10, REGRESSED 1, NOT-FIXED 1 (deferred on purpose).

---

## 2. New findings

### Critical

None.

### High

**N1 — HIGH. On the PC, search misses the text of everything made on the server (from F10).**
- *Path.* With selective sync the PC ingests manifests without blobs. `Store._index_object` (`store.py` L329-337) indexes text only from blobs whose file exists on that store (`if path.exists() ...`). So on the PC, a server-extracted book, a feed item or a Docling page is indexed by title and summary only. A blob fetched later on open does not re-index the item (nothing in the design says so). The PC's searches (served from the replica: AD-19, P-LAT, and when offline) answer "not found" for content that exists. This hits S-06, S-07 and S-30, and the copilot's search.
- *Fix.* Sync pulls the `text` and `transcript` slots with the manifests. They are small next to originals; `original`, `pages/*` and `frames/*` stay on demand. Re-index an item when one of its text blobs arrives. Then P-SYNC-DISK reads "copies no blob except text slots".

**N2 — HIGH. QMB cannot read the new price files, and the bid/ask split breaks its quote pairs (from F1, F2).**
- *Path.* `qmb/src/qmb/host/replay.py` `read_recorded_replay_source` (L143-160) takes CT-10 **archive receipt fingerprints** from a QMF EvidenceStore. It resolves them through the QMF boundary (`SourceObservationBoundary`) and "builds quote pairs only from matching bid/ask observations". The F1 writer makes typed-column files that are not CT-10 receipts. F2 puts bid and ask m1 in **two series**. Yet D-5 ("QMB's reader barely changes"), D-6's "safe because" ("byte-identical input") and L AD-28 ("QMB keeps its `store_root` and fingerprint interface") were left unchanged. DR4, the packet that matters most now (ruling 125), would hit this on its first run.
- *Fix.* In DR4's blast radius: QMB's replay reader gains one reader for the typed partition schema, and `materialise` for a quote series returns the bid and ask partitions as a pair. Ticks keep both sides in one row (`variant = -`). Correct D-5, D-6 and AD-28. Add a DR4 acceptance check: one month replayed from the new files gives the same trades as from a small month written the old way.

**N3 — HIGH. Without the bucket, every file made on the server has one copy anywhere, and the screen says otherwise (from F10 with F21).**
- *Path.* The bucket is not a precondition (F21 outcome). With selective sync, server-born durable blobs (server uploads, Docling pages, recordings, run logs, model weights) no longer reach the PC. MIGRATION's own step 3 admits it: "blobs the PC never opened ... are named in the incident as lost". The server was reset on 2026-10-21 (ruling 130). UI-HANDOFF §17.13, OPEN-DECISIONS and 55 §12 tell him "one copy off this PC", which is false for these files. The other side: a blob he opens is fetched to the PC and is durable, so it may be evicted only after two remote copies (AD-10). Without the bucket it can never leave, and every opened file pins C: (12 GB free).
- *Fix (pick one, his call, one line in §12).* (a) Make the bucket a precondition of DR2's flip. This is the simplest option, at about $2-3 a month. (b) Until the bucket exists, keep `primary = pc` and the full blob pull for durable server-born blobs only. Either way: a blob fetched from upstream is a cache copy, evictable at any time, and the two-copy rule applies only to blobs born on that machine. The no-bucket message says "files made on the server have one copy".

**N4 — HIGH. The probes gate packets that build the very code they test, and several fixes are in no packet.**
- *Path.* 55's final table defines "Before" as "the packet ... that may not start until the probe passes". P-TORN (before DR1) and P-SYNC-DISK, P-REPLAY, P-SPLIT and P-VERSION (before DR2) test code that DR2 itself builds. So do P-KEY and P-MARKS (DR3), P-NOTRADE (DR5) and P-BAN (DR6/DR5). Read literally, none can pass, so either the run stalls or the gate is ignored. Separately, the torn-log quarantine, fsync and rename retry (L AD-16), the full-disk rule (AD-10), the memory reservation and child processes (E AD-30) and the version check appear in **no** packet row of §10, yet P-TORN, P-DISKFULL, P-OOM and P-VERSION gate DR1 and DR2.
- *Fix.* Split the table. **Premise probes** run before the packet starts: P-CTSCOPE, P-CTREFRESH (same-app part), P-CT2CONN, P-DUKA, P-HS, P-OO, P-GPU, P-DOCLING, and P-MDREAD's DuckDB part. **Acceptance probes** must pass before the packet merges *and* before the real-home act they protect: P-REHEARSE before the real import, P-SPLIT, P-SERVERLOST and P-SYNC-DISK before the flip, P-MDREAD's read-back before the old-ticks import. Name the packet that builds each fix: torn logs and fsync in DR1; full disk, memory guard and version check in DR2.

**N5 — HIGH. "Only the home holds the secret" contradicts the built vault, so a server-refreshed cTrader token can be killed from the PC (ruling 135 / F27).**
- *Path.* For the cTrader read grant, consent lands on the PC: "one fixed loopback port" (E AD-67), and his browser is on the PC. The PC therefore receives the tokens, and the home is the server. The built vault (`qmx_router/vault.py` L1-14) "never moves" keys. The original stays in the PC's Credential Manager and only a sealed copy goes out. "Deletion publishes a tombstone. A node that reads a tombstone refuses the name from then on." So: (a) the PC is a second holder of the refresh token; (b) if the PC drops its copy to obey "only the home holds it", the tombstone kills the server's copy; (c) no path lets the server write back the rotated pair, and "newest `updated_at` wins" lets any later PC re-seal overwrite it. MIGRATION's server-loss step 4 already shows the conflict: "the PC seals the replicable entries again" next to "its refresh token lived only there".
- *Fix (simpler than today).* The home exchanges the code. The PC browser carries only the one-minute code, which is useless without the app secret, and forwards it to the home host, which holds the read app's secret. The tokens are written only into the home's local store. OAuth credentials are never on the allow-list; `qmx/read/*` replication is for static keys only. The same pattern answers N11.

**N6 — HIGH. The open month is never backed up, and its freeze and append rules do not fit kinds without a fixed density (from F3).**
- *Path.* L AD-25: the open file is "never archived, never bucketed", and it freezes only on a gap check "against the series' market calendar". For fills (S-19; a trading server sends them within seconds, S-28), calendar revisions (S-24, "every revision kept", not re-downloadable) and trades or book events, there is no expected density. Such a month may never freeze, so it may never be bucketed, so it can stay a single copy on the server indefinitely. That breaks "one backup plan covers everything" (AD-16). The append rule ("only adds rows after its last row, or inside a listed gap") also refuses a late fill after an outage, and a calendar revision of an earlier event, unless it is a "correction run". The rule never says whether order is by event time or by observation time.
- *Fix.* The freeze rule is declared per kind. Continuous price kinds use the gap check. Event kinds (fills, calendar, trades) freeze at month end plus the provider's own settlement delay, with no gap check. Order is by observation time for bitemporal kinds. A non-redownloadable open file is pushed to the bucket after each commit batch under its fixed name, overwritten each time.

**N7 — HIGH. The freeze rule makes his click the bottleneck for thousands of historical months (from F5).**
- *Path.* "A month freezes when its gap check passes or when he accepts the listed gaps" (L AD-25; UI-HANDOFF §17.2 "a button to accept them"). DR3 imports 23 years × many pairs from the old 10 GB, and Dukascopy history has known permanent holes. Every month with one unfilled hour stays "open" and is re-fetched on every downloader run. It mints no card version, so results on it point at open ranges. It is never bucketed (N6), and it waits for a click from a non-technical operator, multiplied by thousands.
- *Fix.* A month freezes with its gaps recorded in `quality` once a re-fetch returns the same gaps, which means the provider has nothing more. His click is needed only to *re-open* a frozen month. Data health lists frozen-with-gaps months as information, not as tasks.

### Medium

**N8 — MEDIUM. Ruling 135 contradicts the letter of ruling 117, and 26 does not say so.** Ruling 117: "Docker, Contabo or a server is never forced as a safety requirement." Ruling 135 forces live keys onto a trading server for safety. Live trading was always the trading node's job, so the substance holds. But 135 says only "derived from rulings 116-118". Fix: one sentence in 135 naming the tension with 117, so his overrule is informed.

**N9 — MEDIUM. The refresh owner is keyed to the connection row, but one cTrader grant spans demo and live.** One token covers every account he ticked, demo and live (56 §2). The model puts `environment` on the Connection row (55 §4 table), so one grant becomes two rows with one `credential_ref`, and "one home per connection" lets them take two homes, which means two refresh owners. E AD-67 says the read app's demo and live connections share one home only for cTrader, as a default. Fix: the home and refresh owner belong to the **credential**. Rows sharing a `credential_ref` must share its home, checked when saved.

**N10 — MEDIUM. Several trading servers on "their own cTrader app" repeat F27 and F32 among themselves.** Ruling 135 and E AD-67 say "trading servers use their own app registration", but it is unclear whether that means one app per server. S-28 expects several trading servers. Two of them on one app give two live connections per app and two refresh owners. Each app needs Spotware approval, with no published timeline (56 §2). Fix: "one cTrader app registration per trading server", listed among his steps for each server.

**N11 — MEDIUM. The trading server's consent flow is not described.** "The redirect lands there" (E AD-28, ruling 135), but a VPS has no browser and the only redirect designed is a loopback port on the read app. Fix: the N5 pattern. The trading app registers a redirect to the trading server's tailnet address; his PC browser carries only the code; the trading server holds the trading app's secret and does the exchange. State it as the contract the trading-node session builds on.

**N12 — MEDIUM. P-CTREFRESH's second-app half needs an approved second app before DR5.** Its PASS line needs "a grant under a second app registration", and approval has no timeline. Fix: keep the same-app half before DR5. Move the cross-app half to "before the first trading server".

**N13 — MEDIUM. Promoting the PC does not stop a server that is unreachable but still running.** MIGRATION "When the server is lost" step 1 raises the epoch on the PC only. An old server cut off by the network keeps running its crons and moving its own `main`. When it comes back, its pushes are refused (good), but its results are stranded with no step to recover them. Fix: step 1 asks him to stop the old server's host when it can be reached. On reconnect, a store with the stale epoch lists its moves since the last common sequence as `merge-conflict` items for him, never silently.

**N14 — MEDIUM. Measure-only probes cannot gate anything.** Rows 11, 15, 22, 24, 25 and 26 say "as §11 states", and §11 gives only what is measured (P-HS, P-OO, P-GPU, P-DOCLING, P-TAINT and P-SRCH have no pass or fail line). P-MDREAD's "23 years of m1 from the PC cache, server, tailnet" cannot run "before the DR3 import", because those years arrive with the import or with DR6. Fix: every probe gets a decision line ("PASS: the measured value is recorded as the Settings default and live readings show it fits; FAIL: the process is killed or the service does not start"). Split P-MDREAD: read-back before the import, read times after DR6.

**N15 — MEDIUM. With the seal frozen, `historical_holdout_months` means nothing and the sealed window keeps growing (from F7).** `seal.py` L2-6 and `docs/components/qmf-data.md` define the seal as "the newest sealed window (`historical_holdout_months`, approximately twelve months)". "Frozen" there means the boundary is stored verbatim, not that it never moves. Without the monthly roll, everything after the boundary stays sealed forever unless he clicks. So a year from now the copilot cannot explore the last two years (S-15). Fix: keep "only by his click", and when the sealed span exceeds the setting, raise an inbox task offering the move (with the dialog of §17.12).

**N16 — MEDIUM. The copilot's broker reads are not rewired to the home's session (F32 adoption).** See F32. `qmx_broker/ctrader_transport.py` opens a short TLS session for each read, so a copilot read on the server opens a second connection beside the home's long session. Fix: add `qmx_broker`'s transport to DR5's blast radius. Its reads call the home host's `host` adapter session (local or forwarded).

**N17 — MEDIUM. A version mismatch blocks every update window (F16).** See F16. Under strict equality, every QMX update stops sync and forwarding until all hosts match, and the PC sees the wrong message. Fix as in F16.

### Low

- **N18.** P-REHEARSE's PASS line compares against MIGRATION step 0 counts, which include the test junk that AD-26 filters, so it fails by construction. Make it "step 0's numbers minus the filtered rows, listed by id". Also confirm the real home is untouched by a hash of the home before and after.
- **N19.** Probes that pass trivially: P-OOM passes if nothing is killed, so run it under a memory limit on a scratch cgroup. P-BAN's "no 418" needs a local stub that answers 418 when called inside the wait. P-NOTRADE's "live account it can trade" needs a stub adapter returning a live, trade-scope account. P-SERVERLOST should also drill the no-bucket branch. P-SPLIT should say what an offline restored PC does before its first sync (it acts locally; those moves go to a side ref).
- **N20.** Two status words on every connection row: a setup chip of five words plus a running reading of five words (UI-HANDOFF §17.8). Under "design for complexity, not a complex system", fold the setup states into the reading (`needs_you` covers unconfigured and unauthorized) and keep the five machine words for Machines only.
- **N21.** A result that read an open-month range is never marked "corrected", because `replaced` lists fingerprints and the open file has none. Record open-month corrections as (key, range, reason).
- **N22.** Stale text the fix round left: 55 §9.1 S-28 still says "credential hand-over by his click" (ruling 135 removed the hand-over); 55 §9.2 default 14 still says "server to bucket nightly"; MIGRATION line 13's premise (F19); 55 §0 item 7 omits demo-only trade keys, which ruling 135 allows; L AD-16's opening rclone sentence; H61's check column does not test the new refusals; existing `qmx/ctrader-*` read keys are not re-filed under `qmx/read/*` in any step; E AD-67's cTrader history pages flow through `qmx_host`, while E AD-30 keeps downloads out of it (say the host session only relays one page at a time).

---

## 3. Ruling 135 against 56's cTrader facts

| 56 fact | 135 / E AD-67 | Coherent? |
|---|---|---|
| At most one demo and one live connection per app; each carries unlimited accounts | The PC and server share the read app; one home holds both; others forward | Yes for the PC and server. Not yet for `qmx-broker`'s short sessions (N16) or for several trading servers on one app (N10) |
| A refresh returns a new pair and kills the old pair | The home is the only refresh owner | The rule is right, but the hand-over and the built vault leave a second holder and a tombstone path (N5). The owner must be the grant, not the row (N9) |
| One token covers the accounts ticked at grant; new accounts need a new grant | A demo-only trade grant may sit on the PC | Yes: a live account cannot appear later without his new grant, and the add-time probe refuses a live-trade grant |
| Whether two grants for one user and one app coexist is not documented | P-CTREFRESH records it | Yes, but the cross-app half has an approval dependency (N12) |
| The app needs Spotware approval first | "App not approved yet" is `needs_you` | Yes for the read app. Each trading server needs its own approval (N10) |

Verdict: **coherent in substance.** Fixing N5 and N9 makes it hold in the built code. Fixing N10 and N11 makes it hold for the trading servers.

---

## 4. The probe list

- **Exact lines.** 20 of 26 rows have a concrete PASS and FAIL. Six defer to §11 ("as §11 states"). Only P-CTSCOPE's §11 entry works as a pass line; the other five measure and never decide (N14).
- **Testable.** Mostly yes. Three need stubs or forced conditions to mean anything (N19). P-REHEARSE fails by construction (N18).
- **Ordered before the step it gates.** No, for the code-behaviour probes. They gate the packet that builds the code they test (N4). P-MDREAD's read-times part needs data from the step it gates (N14). P-CTREFRESH's second half needs an outside approval (N12).
- **Missing probe cases for the fixes as written:** F11's "head moved past" replay (F11); the no-bucket server loss (F14, N3); PC search over server-born text (N1); QMB reading the new files (N2).

---

## 5. The 30 scenarios of 54

Every scenario still has a home in 55 §9.1, and the fix round removed none. Five now have a mechanism line that the fixes contradict, to be corrected with the findings above:

| Scenario | Problem | Finding |
|---|---|---|
| S-09 Backtests by fingerprint | QMB cannot read the new files; the bid/ask pair is split | N2 |
| S-19 Trade journals | Fill months may never freeze and are not backed up while open | N6 |
| S-24 News and calendar | Calendar revisions break the append rule; the open month is not backed up | N6 |
| S-28 Trading servers connect back | Row still says "hand-over by his click"; one app per trading server | N10, N22 |
| S-30 Search at real volume | PC search lacks the text of server-born items | N1 |

S-02, S-03, S-15, S-21 and S-25 hold, with the caveats in N3, N7, N15 and N21.
