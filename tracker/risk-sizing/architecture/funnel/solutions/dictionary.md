# The dictionary and the block catalogue

**What this part is.** The trader vocabulary agents cite, and the catalogue of blocks that run: what an entry looks like now, how it is checked, how it covers every market in scope (forex, futures, metals, CFDs, indices, crypto perps), who adds entries, and how it grows without a cap. QML's door resolves entries (`qml.md` §5); units bind them (`unit.md` §3).

**Verdict: core.** The vocabulary is what every agent and every unit must agree on, so it stays one source in the core: Library items as the source of truth, a snapshot shipped as QML package data so the trading node never needs the Library up.

## His words

- "if someone from a source mentions anything, we already know what it is, okay? Or if it's new, we can append it" (T2:788)
- "239 is very small" (T2:1000)
- "you tell them to ground themselves first. Don't limit them, okay?" (T3:1264)
- "remember, we are enhancing QML, the dictionary, and most things" (T3:1435)

## 1. What exists today

| Piece | State | Where checked |
| --- | --- | --- |
| 239 entries in four Markdown files outside the repo (`Desktop\Stats\dictionary`): context 66, exits 57, locations 56, triggers 60 | BUILT, prose only, by order ("Do not create Python") | G1 §2.1; research 34 |
| Twelve fields per entry (family, aliases, definition, boundaries, observable inputs, recognition semantics, parameters and profiles, eligible roles, market and data constraints, transfer notes, evidence and status, uncertainty and variants) | BUILT | G1 §2.1 (`qml/src/qml/research/vocab.py:28-41`) |
| QML's parser reads all 239 with zero refusals; 154 distinct free-text role strings against QML's four closed roles | BUILT (run) | G1 §2.2 |
| Six family folders empty: indicators, liquidity and order flow, time and sessions, execution, risk and sizing, market data and venues | BUILT (empty) | G1 §2.1 |
| Scope FX and crypto spot; several entries say "crypto spot only" | BUILT | G1 §2.5; research 45 §4 |
| Running blocks: six TA-Lib wrappers (SMA, EMA, WMA, RSI, MOM, ROC) and swing points; ATR, MACD, Bollinger, ADX, VWAP, session range named but not wrapped | BUILT / MISSING | G1 §2.3 |
| Library `component` kind (`component_type`: indicator, combination, feature, filter, labeler; inputs; parameters; logic fingerprint) | BUILT, nothing writes it | G1 §2.4 |
| `bc-build-a-component` template: card check, tests first, no-future test (value cut at t equals value on full data, to 1e-9), warm-up values missing not zero | DESIGNED, its runner is a stub | G1 §2.4 |
| Coverage: the MQL5 census found 112 of 252 concepts covered (44%); about 150 concepts beyond FX are missing | research | research 36 §0; research 45 §3 |

## 2. Harvest: solutions already on disk

| Solution | Where | Fits now? | Carried as |
| --- | --- | --- | --- |
| Rebuild the form, keep all 239 entries and their ideas as seeds; never lose them, never leave them in limbo | research 43 §3.2; ledger D-01, D-06; research 41 §2.1 | Yes (his 29 and 30 Oct words; lead's answer to ruling 13) | §4, §7 |
| Three faces per entry: trader words, machine spec, implementation | `research/funnel4-qml/party-brainstorm/qml-field.md` B031; research 43 §3.2 | Yes | §4 |
| Status computed by script (named, specified, implemented, tested on data, used in a unit) | research 43 §3.2 (review A26); funnel4 intent item 4 | Yes | §5 |
| Three homes per class: facts on the instrument record, class-only readings in the catalogue, a transfer status per entry per class | `qml-field.md` P-I4; research 43 §3.2 | Yes | §6 |
| Data levels 0 to 6 with three ladder splits (volume kind, depth grade, derivatives field clock); fallbacks with expected loss | research 45 §2; research 43 F6, §3.2 | Yes | §4, §6 |
| About 150 missing concepts with family, data level, classes, settings and a source; twelve words with class-dependent meanings | research 45 §3, §4 | Yes, as the first content waves' worklist | §6, §7 |
| A statistics and models family (Hurst, variance ratio, efficiency ratio, half-life, HMM, GARCH, change point) as readings on session and day clocks, each with a minimum sample and a lag | research 43 §3.2; research 45 §5; research 22 | Yes | §6 |
| Match script: each source sentence maps to an entry id or "unmatched"; unmatched becomes an append request | research 43 §3.2 (B037, B062, B126) | Yes | §7 |
| One-line index for cheap agents; full entries on demand | `qml-field.md` B079 | Yes | §4 |
| Evaluation words in a separate judging glossary | research 43 §3.2 (`qml-field.md` B058; research 36) | Yes | §4 |
| "Builds blocked until an entry is implemented" | funnel4, dropped by the forge | Dropped: 85% of strategy articles use a missing concept; a part with no implemented entry is tagged "outside QML" instead | §5 |
| Every block needs runnable code; fill the empty families; fix duplicate names; ranges for unresolved settings; market tags for CFD, perps, futures, spot | workroom `decisions.md` "QML (13 Oct)" | Yes | §5, §7 |
| Agents search blocks before writing new code; a librarian proposes blocks from repeated custom code | same | Yes | §7; `workflows.md` |
| The gold mine's layers: primitive, role binding, graph; role neutrality; roles beyond four | research 39 via G1 §8.2 | Yes | entries stay role-neutral; roles live on the binding |

## 3. Solution shapes

### Shape A. One kind, three faces: an entry that runs is a block (recommended)

- **What.** Every concept is one Library item. Its trader face says what a trader means; its machine face gives inputs, output type, parameters with kinds and ranges, data level and fallbacks; its implementation face points at code with golden tests. An entry without code is "named" or "specified" and still citable.
- **Reuses.** The Library `component` kind (BUILT, no writer), extended surgically: `component_type` gains trigger, exit, sizer, motion, reading, combiner, calendar, context. QML's parser for the port. The `bc-build-a-component` checks for the implementation face.
- **Hard cases.** A concept with no code yet (tagged, never blocking); a concept whose meaning changes by class (per-class meaning table); multiple implementations of one concept (versions or variants of the entry).
- **Maintain.** One kind, one checker, one snapshot.
- **Explain.** "Every word an agent can use is one page. If it has code, a unit can run it. A script says how far along each page is."

### Shape B. Two kinds: a vocabulary of words and a catalogue of blocks, linked by "implements"

- **What.** Words and blocks are separate; many blocks may implement one word, one block may serve several words.
- **Hard cases.** Strong on many implementations per word.
- **Maintain.** Two kinds, two checkers, link rules to keep consistent; agents must hop twice.
- **Explain.** "A dictionary and a parts bin, cross-referenced."
- **Why not.** It doubles what a cheap agent must traverse, and Shape A covers several implementations as versions of one entry.

### Shape C. Keep the prose files; add a machine index beside them

- **What.** The 239 stay Markdown; a generated index carries ids, aliases and data levels.
- **Why not.** The reason the prose existed ("QMX wasn't ready", research 34) no longer holds; prose cannot be checked or run, and "never in limbo" means inside QMX's own store (research 41).

**Pick: Shape A.** Reason: one concept per page keeps the cheap-agent path short, reuses a BUILT kind, and makes "a dictionary entry that runs is a catalogue block" literal.

**The twelve multi-meaning words** (party P3, open clash). Lead's call: one entry per word with a per-class meaning table and a same-meaning check before any cross-class match; when two class meanings need different code (exchange volume against a tick count), they become two entries linked `same-word-as`, and the checker picks by the market's data level. Why: one place for an agent to look, without ever silently mixing meanings. How to undo: split every multi-meaning word into one entry per meaning.

## 4. The new form of an entry

| Face | Fields |
| --- | --- |
| Identity | `entry_id`, `version`, `family` (folders by family, never by job), `aliases` (unique across the catalogue), `same_word_as` links |
| Trader face | definition in trader words, boundaries (what it is not), recognition semantics, eligible roles (role-neutral: the job is assigned on the unit's binding), per-class meaning table, sources with exact quotes and dates |
| Machine face | inputs (streams and their data level with the three splits), output type (event, level, series, state, probability, intent), parameters as `NumberSpec` with a starting profile and its origin label (RSI 14 and 70/30 as "published convention"), warm-up rule, minimum sample and expected lag for statistics, fallback chain with expected loss, transfer status per class (native, direct, adapted, conceptual only, not transferable, not assessed) |
| Implementation face | code reference and fingerprint; golden test values with their reference (TA-Lib or a published table); no-future test; warm-up test; per-class profile tests |
| Computed | status (§5), used-in count, last check verdict |

Evaluation words (Sharpe, PBO, walk-forward, expectancy) live in a separate judging glossary, not here (S049). A one-line index (id, aliases, family, output type, data level, status) is generated for cheap models; full entries are fetched on demand (S036).

## 5. How each entry is checked

A dictionary checker, the same pattern as the unit checker: pure, every problem at once, no false positives on the known-good corpus.

| Check | Error when |
| --- | --- |
| Schema | a face is malformed |
| Identity | an alias collides with another entry's id or alias; an id is reused with a different meaning |
| Roles | a role is outside the declared role list (the 154 free strings map to it; unmapped ones are logged for review, not guessed) |
| Data level | a machine face has no data level, or a fallback has no expected-loss label |
| Transfer | a class is claimed "native" or "direct" with no evidence or source |
| Implementation (only when status would be "implemented") | golden values mismatch; the no-future test fails; warm-up values are zero instead of missing |
| Sources | no source citation on a non-standard entry |

**Status is computed, never typed** (S041): `named` (trader face only), `specified` (machine face passes), `implemented` (code plus golden, no-future and warm-up tests pass), `tested on data` (run on a recorded slice of each class it claims), `used in a unit` (a unit he admitted binds it). A unit may bind a "named" or "specified" entry only through a Python block tagged "outside QML", shown on the unit card; nothing is blocked (research 43 §3.2 forge note).

## 6. Covering every market in scope

**Three homes per class** (research 43 §3.2):
1. **Facts about the market** on the instrument record (`instruments.md`): contract size, tick, lot step, sessions, swap or funding, expiry and roll, margin.
2. **Class-only readings** in the catalogue: funding state, open interest change, liquidations, basis, mark against last (perps); roll state, days to expiry, settlement, the daily break, price-limit state (futures); cash open, opening drive, initial balance, breadth (indices); fix windows at 10:30 and 15:00 London (gold); currency strength (FX, cross-sectional).
3. **A transfer status per entry per class**, "not assessed" until that class's pack is built.

**Packs and their order.** The form covers every class from the first build, because he asked for futures accounts and every instrument now (STATE mid r29). Content follows the doors: FX, gold and index CFDs on cTrader first; perps second; futures and stocks after their routes exist (research 43 decision 4). Market-profile entries run on bars, so they ship with the first packs as flagged proxies of exchange volume on CFDs (research 45 §6). Futures entries are written in the first content wave as `specified` (their machine faces and data levels), so a futures unit can be written and checked before any futures data route is switched on.

**Order flow entries** (delta, cumulative delta, trade imbalance, absorption, iceberg) declare data level 4 (a tape with aggressor side) with the fallback chain depth imbalance (level 3), tick-rule imbalance (level 2), range pressure (level 1), each with its expected loss (S115; research 43 §3.2). Native iceberg detection needs order-by-order depth and is "not transferable" to cTrader data.

## 7. Who adds entries, and the directions they get (his rulings 13 and D-05)

**The lead's answer stands** (STATE "The lead's answer to ruling 13"):
1. **The form** (kind extension, entry schema, dictionary checker, status script, snapshot script, one-line index) is built by the orchestrator's builders as code.
2. **The first content wave** is a packet in the same build: a script ports the 239 entries (QML's parser already reads them), maps roles, rewrites "crypto spot only" market lines, and then builders add the families beyond forex from research 45's list and the MQL5 census gaps, with no cap.
3. **Later growth** goes through the same authoring door the copilot and QMA agents use: a `dictionary-expansion` workflow template (source in, match report, append requests, entries written, the checker run, governed drafts waiting for his yes) and the librarian workflow that proposes blocks from repeated custom code (`workflows.md`).

**Directions every expander gets, written into the packet and the template:**
- Ground first: read the entry's sources, research 45's row for it, the census row, and what QML already runs. Never guess a definition.
- No cap: write every concept the sources use; "too many" is not a reason to stop.
- Cite: every non-standard entry names its source with an exact quote and a date.
- Role-neutral: never write the job into the entry; the unit's binding assigns it.
- Data honest: declare the data level and the fallback, and mark proxies.
- Pass the checker; never mark status by hand.
- Unmatched words become append requests, never silent new entries.

## 8. The rebuild in plain words (the page he is owed, ledger D-02)

The dictionary keeps every one of the 239 ideas. Each one becomes a page QMX itself stores, not a note in an old folder. A page says what a trader means, what data it needs, and whether it has working code yet. A script, not a person, says how far along each page is. Pages for futures, metals, indices and crypto perps get written now, even before QMX can trade those markets. When an agent reads a new source, every word is matched to a page or flagged as new. New pages wait for his yes, like everything else in the Library.

## 9. Numbers (starting defaults, all editable)

| Number | Default | Why |
| --- | --- | --- |
| golden test tolerance | 1e-9 relative | the shipped `bc-build-a-component` value |
| minimum points for a Hurst value | 1,000, flagged below 4,000 | research 43 §5 (research 22, 37) |
| persistence window at 1m | 240 bars | research 43 §5 |
| same-meaning check across classes | percentile definitions agree within 10 points on a shared window | research 43 §5 (research 23) |
| snapshot refresh into QML package data | on every publish of an entry | the node reads the snapshot |

## 10. Connection points

| From | To | What crosses |
| --- | --- | --- |
| Expanders (builders, agents, copilot) | Library `component` kind | entry drafts; the checker's problems |
| Dictionary | QML | the catalogue snapshot; `find` and resolve by id and version |
| Dictionary | instrument records | data levels a market offers, for the checker and the transfer status |
| Dictionary | MIS | reading entries the MIS runs (`mis.md`) |
| Sources (videos, articles, chats) | match script | sentences in; entry ids or append requests out |

## 11. Open for the architecture step

1. The kind: extend `component` (picked, surgical) or add a new `entry` kind. Extending reuses a BUILT kind with no writer.
2. How entry versions pin: a unit pins `entry_id@version`; a fixed entry makes new versions of the units that use it (identity table).

## 12. Parked

- Options-as-context entries and a stocks pack (after the first doors).
- Vision-model chart readers as entry implementations.
