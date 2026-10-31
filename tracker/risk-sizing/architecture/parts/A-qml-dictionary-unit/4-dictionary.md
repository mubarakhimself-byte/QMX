# Sub-area 4: the dictionary, its new form, the port of the 239, the first content wave and growth

Part A, 31 Oct 2026. Decisions: AD-104, AD-113, AD-114 in `ARCHITECTURE-SPINE.md`. Shapes: `CONTRACTS.md` §5.

His words: "if someone from a source mentions anything, we already know what it is, okay? Or if it's new, we can append it" (T2:788), "239 is very small" (T2:1000), "you tell them to ground themselves first. Don't limit them, okay?" (T3:1264).

**Verdict: core.** The vocabulary is what every agent and every unit must agree on. Entries are Library items; deployments carry the blocks they pin, so the node never needs the Library.

## 1. The rebuild in plain words (the page he is owed, ledger D-02)

The dictionary keeps every one of the 239 ideas. Each becomes a page QMX itself stores, not a note in an old folder. A page says what a trader means by the word, what data it needs, how it differs between forex, futures, metals, indices and crypto, and whether it has working code yet. A script, not a person, says how far along each page is. Pages for futures, metals, indices and crypto perps are written now, before QMX can trade those markets, so a unit for them can be written and checked today. When an agent reads a new source, every sentence is matched to a page or flagged as new; new pages pass the same checks and wait for his yes, like everything else in the Library. Pages with code are the building blocks units are made of.

## 2. What exists (CHECKED)

| Piece | Where | State |
| --- | --- | --- |
| 239 entries in four Markdown files: context 66, exits 57, locations 56, triggers 60 | `C:\Users\Mubarak\Desktop\Stats\dictionary\` (outside the repo; four files, about 371 KB, listed this session) | prose; six family folders empty |
| Twelve fields per entry; QML's parser reads all 239 with zero refusals; 154 free-text role strings | `qml/src/qml/research/vocab.py:28-60`; G1 §2.2 (run there) | built |
| The `component` kind (`component_type`: indicator, combination, feature, filter, labeler; inputs; parameters; logic fingerprint; a `code` blob) | `qmx-library/src/qmx_library/kinds/component.schema.json` | built; **already written** by mini apps' provides schemas and migrated confluences (`qmx_control/library.py:312-330`, `migrate/from_apps.py:66-70`, `migrate/from_registry.py:34`) |
| Six TA-Lib wrappers, swing points | `packages/qmf-indicators/src/qmf/indicators/wrappers.py:146-193`; `packages/qmf-structure` | built |
| The no-future and warm-up gates as a verdict script | `qmx-engine/src/qmx_engine/templates/bc-build-a-component/scripts/verdict.py:1-40` | designed; its runner waits for a sandbox |
| Coverage: 112 of 252 MQL5 concepts (44%); about 150 concepts beyond FX missing; twelve words with class-dependent meanings | research 36 §0, research 45 §0, §4 | research |

## 3. The new form, `qmx.entry/1`

Fields: `CONTRACTS.md` §5.1. The checks the entry checker runs (pure, every problem, the corpus gate as for units):

| Check | Error when |
| --- | --- |
| Shape | a face is malformed |
| Identity | an alias collides with another entry's id or alias; an id is reused with another meaning |
| Roles | an eligible role is outside the vocabulary |
| Data level | an input has no data level or a fallback has no expected-loss label |
| Transfer | a class is claimed `native` or `direct` with no source |
| Sources | a non-standard entry cites no source with a quote and a date |
| Implementation (only when code is present) | golden values mismatch beyond the tolerance; the cut-against-full test fails (QML-01, QML-02); warm-up values are zero instead of missing; the recursive-settle length exceeds the declared warm-up (QML-03); the block fails the loader's protocol; the source would change under the Library's redaction (A-NEW-2) |

**Status is computed** (`tools/dictionary/status.py`, run by CI and after every entry save): `named` (trader face passes), `specified` (machine face passes), `implemented` (implementation checks pass), `tested_on_data` (run on a recorded slice of each class it claims), `used_in_unit` (a published unit pins it). Written as an annotation with its evidence fingerprint; an author never types it.

**Typed roles.** One vocabulary (AD-104) replaces the 154 strings. A mapping table in `qml/src/qml/catalogue/roles.py` maps each string seen in the 239 to a role, for example "pre-trigger filter" to filter, "arming condition" to arming, "exit prompt" to exit, "location interaction" to location, "management observation" to management; a string the table does not map is logged in the port's report for review, never guessed.

**Data levels** (`CONTRACTS.md` §5.2) with research 45's three splits: volume kind, depth grade, derivatives clock and history. Order-flow entries (delta, cumulative delta, imbalance, absorption) declare level 4 with the fallback chain depth imbalance (3), tick-rule imbalance (2), range pressure (1), each with its expected loss; native iceberg detection needs order-by-order depth and is `not_transferable` to cTrader data.

**Words that change meaning by class** (volume, open interest, session, rollover, basis, settlement, gap, spread, liquidation, funding against swap, the open, the close): one entry with a meaning per class; two entries linked `same-word-as` when the code differs (exchange volume against a tick count; the daily swap against perp funding).

### Fork: where entries live (principle-exhaust-the-design-space)

| Option | Verdict |
| --- | --- |
| **A. The `component` kind with an explicit `entry.schema` marker (picked)** | honours L0 AD-19; the existing writers' items carry no marker and are never checked as entries (BR-A1 run with the extended schema: Library and control suites unchanged) |
| B. A new `entry` kind | cleaner name, but contradicts L0 AD-19 and duplicates a kind that already holds blocks' code; would need a spine amendment |
| C. Dispatch on `component_type` values | rejected: existing writers may use `indicator` or `filter` without entry faces, so the type cannot tell an entry from a legacy item |
| D. Keep the Markdown files and add a machine index | rejected: prose cannot be checked or run, and "never in limbo" means inside QMX's own store (research 41) |

## 4. The port of the 239 (the first content packet)

| Step | Mechanism | Proof |
| --- | --- | --- |
| Freeze the source | copy the four files into `qml/catalogue-seed/stats-2026-08-26/` with a `SOURCES.json` of their fingerprints; the secret scan runs on the commit | the fingerprints match the Desktop files |
| Parse | QML's parser (`resolve_dictionary_entry`) over every `##` record | 239 parsed, 0 refused |
| Map the faces | the twelve fields to the three faces; parameter names to `NumberSpec`s with their origin labels (`source_stated`, `published_convention` as written; `unresolved` where no value is given); inputs to data levels by a mapping table | each entry passes the entry checker at `named` or `specified` |
| Map roles | the roles table above | an unmapped-role report |
| Rewrite market lines | "crypto spot only" and FX-only lines become per-class transfer status; classes without evidence are `not_assessed` | no entry claims `native` without a source |
| Collisions | the nine kept slug collisions become family-scoped ids (`context/<slug>`, `exits/<slug>`) linked `same-word-as` where the meaning is shared | ids unique |
| Land | every entry as a draft in one collection on a port ref; one card asks for one publish of the whole collection | 239 in, 239 drafts out, counted by the script |

The port is a script (`tools/dictionary/port_stats.py`), rerunnable and idempotent: entries are keyed by their source fingerprint, so a rerun changes nothing.

## 5. The first content wave (a build packet, no cap)

**What it covers.** Every concept research 45 §3 lists (market profile, the futures calendar, stock and index clocks, perps fields, metals and energy clocks, statistics and models used as readings: Hurst, variance ratio, efficiency ratio, half-life, HMM, GARCH, change points), the census gaps of research 36 §3 (MetaTrader's built-ins: CCI, Parabolic SAR, Williams %R, Awesome and Accelerator, Alligator, DeMarker, MFI, OBV, A/D, RVI, Force, Bulls and Bears, TRIX; ATR, MACD, Bollinger, ADX, Stochastic, VWAP and session range), the exit families research 35 found missing (time-varying targets, unrealised-profit caps, give-back from peak, account-level halts as `halt` entries, probability exits as `specified`), and the blocks the dummy needs. Futures entries are written as `specified` now. Every concept computable from bars and quotes gets code with golden tests against TA-Lib or a published table. MetaTrader's grid, martingale and averaging families are written as entries with an honest trader face; whether units may use them is the risk session's.

**Directions every builder gets, written into the packet and the skill:**
- Ground first: read the entry's sources, research 45's row, the census row and what QML already runs. Never guess a definition.
- No cap: write every concept the sources use. "Too many" is not a reason to stop.
- Cite: every non-standard entry names its source with an exact quote and a date.
- Role-neutral: never write the job into the entry; the unit's binding assigns it.
- Data honest: declare the data level with its splits and the fallback chain; mark proxies.
- Pass the checker; never type a status.
- Unmatched words become append requests, never silent new entries.

## 6. Growth after the build

Later growth goes through the same door the copilot and QMA agents use: `blocks_find`, `blocks_get`, `blocks_check`, `blocks_match` and `library_save`, inside Part B's dictionary-expansion template (source in, match report, append requests, entries written, the checker run, governed drafts waiting for his yes) and its librarian template (proposes blocks from repeated custom code in plain-Python blocks). A block fix is a new entry version; `tools/dictionary/upgrade_pins.py` lists every unit pinning the old version and makes successor drafts with re-tests queued; live units keep their pins until he promotes (QML-11, QML-12).

## 7. Must not break

Every existing `component` writer and its tests (the marker decides, BR-A1); the vocab parser's tests (`qml/tests/test_research_vocab.py`); the Stats folder itself (read, never written; the frozen copy is the port's input).

## 8. Edge cases handled here

QML-01 to QML-03, QML-07 to QML-12, A-NEW-2, A-NEW-3.

## 9. Ledger rows that bind it

D-01 to D-10, Q-08, CC-07, CC-19.

## 10. Seam for growth

A new class is a pack of entries plus the records Part C refreshes; a new data source is a data-level declaration; a new kind of entry is a `component_type` value plus its output type in the block protocol. None changes QML's code.
