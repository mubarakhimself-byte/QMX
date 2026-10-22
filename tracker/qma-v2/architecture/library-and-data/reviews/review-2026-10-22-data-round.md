# Review — data round amendment (2026-10-22)

Scope: Library AD-25 to AD-33 and the in-place amendments; engine AD-67 to AD-70 and the in-place amendments (AD-5, AD-18, AD-28, AD-30, AD-31, AD-59, AD-63, AD-65); Lab AD-19, AD-20 and AD-5. Run inline by the architect (the brief allowed no sub-agents); each lens was walked separately against the three spines after they were written.

**Verdict:** the amendment fixes the real divergence points of the data round; seven adversary holes were found and closed in place; lint 0 findings on all three spines after every edit.

## Lint

`python -I C:/Users/Mubarak/Desktop/QMX/.claude/skills/bmad-architecture/scripts/lint_spine.py --workspace <dir>`: library-and-data 0, workflow-engine 0, lab-and-pods 0.

## Adversary lens (two units obeying every AD, still incompatible)

| # | Pair that diverged | Fix (applied) |
|---|---|---|
| A1 | the Dukascopy downloader and the old-ticks importer both write the EURUSD tick card's next version; two `main` moves of one record item, one becomes a conflict every month | Library AD-25: a card update first claims the series key `series:<source>/<instrument>/<kind>` |
| A2 | a downloader script process and the host both write the `qmf-data` store's metadata | Library AD-28: the door is the store's only writer on its machine; writers stage files and call `commit(files)`; engine AD-68 says the same from the feed side |
| A3 | the copilot reads EURUSD with no split; a Lab procedure reads with a split; "purpose" means two things | Library AD-28: no split = exploration over every unsealed month; a named split returns only the segment for its purpose |
| A4 | one template lists a scraped page as an `artifact` of type `source`, another saves a `source` item | Library AD-27: a declared `source` output always lands as a `source` item |
| A5 | two derived-feature steps name their series differently | Library AD-32: derived series key `source = derived`, `kind = <component>-v<version>` |
| A6 | a feed homed on the server by default reads as contradicting ruling 117 (local by default) | engine AD-68: the template suggests the server because the data's main copy lives there (ruling 121); he may move any feed |
| A7 | the Lab writes a `workspace` annotation the `collection` schema does not accept (Library AD-2, AD-3) | Lab AD-19 states the schema accepts it |

Checked and cleared: outbox replay versus ref ownership (a replayed write keeps its principal and expected head; a moved head becomes a conflict, AD-26); observer notes (an `agent:` principal on its own `refs/agents/` ref, inside Library AD-7's closed set); read-only trading credentials versus the Library server's refusal by name (they live under `qmx/read/*`, so the refusal of `qmx/ctrader-*` names still holds; engine AD-28 amended in place).

## Currency lens

Read live on 2026-10-22: dukascopy-node 1.50.0 and 1.51.0 dates (npm), its CLI options (dukascopy-node.app), DuckDB 2.0.0 (PyPI; the code pins 1.5.5), Docling 2.134.0, MetaTrader5 5.0.6231, `hindsight-api` 1.1.0 (PyPI), OpenTelemetry Collector 0.162.0 and OpenObserve 1.0.4 (GitHub releases), Node.js 24.21.0 LTS (nodejs.org), Binance public-data folders (S3 listing). `git merge-file` behaviour was run on git 2.55.0. Remembered and not verified, each behind a probe: cTrader's read-only OAuth scope, the MT5 investor login's `trade_allowed` (P-CTSCOPE).

## Rubric walk (good-spine checklist)

- Real divergence points for the level below: price layout, card writer, store writer, read purpose, result shape, merge behaviour, source kind, connection shape and credential scope, feed shape, telemetry path, remote data path: each has one AD.
- Enforceable rules: each names the code seam it changes (file and line in `55` §2).
- Deferred cannot cause divergence: graph projection, DuckLake, direct bucket reads, pixel redaction are each behind a seam already bound.
- Brownfield ratified: the partition fingerprint, seal, broker model, monitor node, claims and merge seam are extended, not replaced.
- Operational envelope: server processes (host with the Library service, OpenObserve, collector, Hindsight with Postgres, Node for the downloader), the bucket, health, incidents, backups and drills: covered.
- Conflicts surfaced (not silent overrides): engine AD-28 and Library AD-12 on broker credentials; engine AD-30's derived session counts; Library OPEN-2 reversed by ruling 120.
