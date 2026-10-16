# Docs and DECs that must change

Source of each conflict: research file 24 §E and this run's reads of `_docwork/ledger.yaml` and `docs/`. "Change" means a new DEC that supersedes, never an edit of a ratified line.

| Doc / DEC | Today says **[retrieved]** | Must become | Driven by |
| --- | --- | --- | --- |
| DEC-0271 (Workbench AD-3) | Library is a projection over ten kinds; Graph Templates, Skills, Routines, saved views, derived datasets are not Library objects | Superseded: the Library is one store of every kind (AD-1, AD-3); the ten kinds map by name; `COMP-QMX-LIBRARY` is a new component | ruling 28 |
| UI0923 `LIBRARY-AND-ATTACHMENTS.md:16` | forbids "a generic Library database, `COMP-LIB`, a copied-row sqlite, a sixth store class" | Retire the forbidden list; the Library is a content-addressed object store with a rebuildable catalog; keep "do not collapse identities" as AD-3 typed kinds | ruling 28 |
| DEC-0476 (UI AD-10) | "one chrome over typed hits … must not collapse kinds" | Keep typed kinds; drop "hits from three rails"; the Library is the store the chrome reads | ruling 28 |
| DEC-0415 (Workflows AD-2) | four discovery rails, Library kinds unchanged, hits are never a store | Discovery reads `LibraryPort.search`; `ContributionHit` becomes a `mini-app` / `workflow` object; pins store object ids | ruling 28 |
| glossary 699-701 (mini-app) | "not a registry kind" | a Library kind (`mini-app`, `mini-app-instance`) | rulings 9, 28 |
| DEC-0443 (Workflows AD-30) | pack states end in `uninstalled` | `… ⇄ disabled → archived` with reason and `replaced_by`; no uninstall | ruling 9, AD-6 |
| Lab spine AD-11 / its DOC-CHANGES row on the Library mapping | `book-definition → pod`, `bms-definition → pod-block` collide with the UI's pod shape | resolved here: governed kinds `book` and `bms` added; `pod` and `pod-block` are ungoverned design kinds; `compiles-to` and `touched` relations added; a "draft" is `fields.stage = draft` on an object, never a kind; the family ledger is a fold over edges, never a stored counter | Lab AD-10, AD-11 |
| Engine spine AD-26 ("`main` moves only by his click") | applies to every workflow output | applies to challengers only; every other passed-run output fast-forwards under the workflow's `publish` rule (AD-18) | ruling 57 |
| Engine spine AD-14 (kinds `workflow_version`, `test_report`) | separate kinds | `workflow_version` is an object of the `workflow` item, not a kind; `test-report` kept | AD-2, AD-3 |
| DEC-0188 wording "nothing in either area is a service"; the word "hub" | the passive file-sync hub is the only hub | `qmx_hub` (the Library Hub) is a service on the same server; rename the passive hub "the node inbox" in docs and code comments | ruling 43, file 30 §3.12 |
| `docs/lenses/data/data-layer.md`, TN-13 | market data on the PC and the node only; runs never fetch | the server holds the primary market-data store; `dataset` cards in the Library; `data_scope` on run tokens; the market-data service is file 30's design | file 30, AD-3, AD-12 |
| DEC-0417 (Workflows AD-4) | board layout is client-only and writes nothing; "do not fingerprint templates onto the Artifact rail" | `board` is a Library kind (ruling 31); templates and workflow versions are objects with fp1 ids; selected-subgraph runs are kept | rulings 28, 31 |
| DEC-0420, DEC-0439 | reuse the QMA daemon as the procedure runtime; Mission Compiler; Task Graph in daemon sqlite | The daemon is deleted (D3). The new engine (designed elsewhere) keeps live state in its own SQLite and definitions and runs in the Library (AD-15) | rulings 22-24 |
| docs workflow life `draft → validate → publish → enable → invoke` | no test step | add `tested` as a `tested-by` relation to a passing run (AD-15) | ruling 23 |
| DEC-0488, DEC-0497 (artifact ingest) | PUT `/artifacts/stage` on the daemon; `transfer_artifact` tickets; daemon never dials in | Keep the PUT shape as `POST /v1/blobs/<sha>` on the control door and the hub; transfer = replication by hash (AD-10); "never dials in" kept (AD-11) | ruling 43 |
| DEC-0118 (backup AD-20), `object-storage.md` | bucket catches nightly encrypted copies pushed by the VPS; QMF primitives | Extend: the Library replicates PC→server continuously and server→bucket nightly (AD-16); drills on the server; the Library catalog is rebuilt, never restored as a DB | ruling 42 |
| DEC-0188 (TN-3 topology) | workstation holds the working archive; bucket pushed by the VPS; passive file-sync hub | Add the Hub as a service on the same server (AD-11); it is a Library writer, so "nothing in either area is a service" needs a carve-out for `qmx_hub`; the registry room stays as is (OPEN-2) | ruling 43 |
| DEC-0278 (continuation) | continuation is a daemon property; GAP-0062 names no always-on host | The always-on host is his server running the Hub; close GAP-0062 | ruling 43 |
| DEC-0428 (placement) | placement is preflight through ExecutionEnvironment ports | Keep; the Hub is the data plane every placement reaches; `ran-on` records the placement | ruling 43 |
| CT-07 | fourteen edge types, addable never redefined | Unchanged. The Library relation vocabulary is a new contract (CT-Library-Relations) that includes CT-07 verbatim (AD-4) | — |
| CT-09 | registry room per world | Unchanged under OPEN-2 (mirror) | — |
| DEC-0380 | STRATS is seed corpus; `source_id=strats` is an adapter key | Unchanged; Strats is out (ruling 28) | — |
| `qmf-registry.md:88-91`, `library.md` screen lens | Library search returns typed hits over registry kinds; uploads via daemon PUT | Rewrite the Library screen lens on AD-17 (previews/detail from kind schemas) and AD-9 (verbs) | ruling 28 |
| `rebuild/DESIGN.md §7.6b` (hp17) | Library = `artifacts/<sha256>` + `library.db`; GitHub weekly | Replace the Library row with the object store and AD-16 | ruling 42 |
| `rebuild/packets/P22` | Library service in `qmx_control`, JSON catalog | Superseded by `qmx_library`; memo kept | — |
| `rebuild/packets/P21`, `qmx-remote/README.md` | bucket on VPS over SFTP; CLIProxy on the server | Keep the provider interface and bucket layout as degraded mode; add the Hub and tokens; drop the CLIProxy section (ruling 38) | rulings 38, 43 |
| harness `tools.py AGENT_OPERATIONS` | `library_search/save/get/versions/links/link` | the rows in LLD §7 (additive; `library_link`/`library_links` retire after migration) | ruling 24 kept: table rows only |
| `UI-BACKLOG`, `BACKEND-REQUIREMENTS.md:80` | "models, workflows, pods, scenarios, reports have no backend kind" | closed by the roster (AD-3) | ruling 28 |
| research files 05 §4, 10 §2, 12, 19 | Library named "Strats"; only `article`/`backtest` written | already corrected by file 24; mark superseded by this folder | — |

New documents to mint after ratification: `docs/components/qmx-library.md` (COMP-QMX-LIBRARY), `docs/components/qmx-hub.md`, `docs/contracts/ct-library-object.yaml`, `docs/contracts/ct-library-relations.yaml`, a Library screen lens rewrite, and a glossary entry for `object`, `ref`, `edge`, `hub`, `run token`, `sidecar`.
