# Sub-area 1: QML's door, the compiler, the unit runtime door, CT-23 format 3 and the block loader

Part A, 31 Oct 2026. Decisions: AD-101, AD-104 to AD-109, AD-120 in `ARCHITECTURE-SPINE.md`. Shapes: `CONTRACTS.md` §4 and §6. Paths are relative to the read-only checkout `D:\QMX-worktrees\engine-base-read\` (`origin/engine/base` `c93407ca`).

His words that set the bar: "QML is very important, please." (T3:1264) and "because you are building a bloody library, okay? Like React, JS. You can't assume anything here." (T3:904).

**Verdict: core.** Two copies of QML would give two meanings of one unit; nothing here becomes a mini app.

## 1. What exists (CHECKED)

| Piece | Where | State |
| --- | --- | --- |
| The runtime seam: `BotFactory.construct(declaration, assignment, read_surfaces)`, `BotCallback.on_instant(evidence)` | `qml/src/qml/protocol/__init__.py:108-139` | built; QMB (`qmb/src/qmb/host/adapter.py:59`) and QMN's seat host drive it |
| `construct_bot` validates a CT-33 `BotDefinition`, resolves the assignment, builds `HostedBot` | `qml/src/qml/protocol/factory.py:212-271` | built |
| `HostedBot.on_instant` collects evidence and sends every intent through `accept_intents` | `factory.py:472-512`; `intents.py:76-106` | built; refuses `requested_r`, Book fields, venue commands, unknown CT-23 versions |
| QML protocol format ladder, version 1 only | `qml/src/qml/protocol/contract.py:25-27` | built; version 2 pinned as unsupported by `qml/tests/test_protocol.py:203-213`, `:243-252` |
| Evidence with `knowable_at` and the look-ahead refusal; exact values only, floats refused | `protocol/evidence.py:73-140`, `:588-596` | built |
| State snapshot and restore on an exact scope tuple | `protocol/factory.py:274-314`; `protocol/state.py` | built |
| Footprint and `derive_horizon` | `footprint/horizon.py:50-94` | built; QMB does not yet consume it |
| Logic identity over a source tree; content kept byte-exact (no line-ending normalisation) | `logic/__init__.py:41-95`, `:331-339` | built |
| QML's dependency law: exactly `qmf-core`, `qmf-registry`, `qmf-risk`; no console script; banned imports; no `open()` in `qml/src` | `qml/tests/test_scaffold.py:54-100` | built, pinned by test |
| CT-23 at format 2 with formats 1 and 2 known | `packages/qmf-risk/src/qmf/risk/door.py:145-151` | built |
| Six TA-Lib wrappers and swing points | `packages/qmf-indicators/src/qmf/indicators/wrappers.py:146-193`; `packages/qmf-structure/src/qmf/structure/families.py` | built; the streaming mode recomputes all history per update (`streaming.py:17-23`) |

## 2. What is added

| Addition | Module | Notes |
| --- | --- | --- |
| The door: `new`, `check`, `compile`, `find`, `explain` | `qml/src/qml/door.py` | pure; re-exported at the top level |
| The compiler | `qml/src/qml/compile/` | `compile(document, context) -> CompiledUnit` or the check result |
| The unit door | `qml/src/qml/protocol/unit.py` | `construct_unit`, `restore_unit`, `HostedUnit`, `accept_unit_intents`, `UnitStep` |
| The motion engine | `qml/src/qml/motion/` | inside the compiled closure; emits calibration rows |
| The block API and loader | `qml/src/qml/blocks/api.py`, `qml/src/qml/catalogue/loader.py` | AD-109 |
| QML's own blocks as source files | `qml/src/qml/blocks/stdlib/<entry>/<version>/block.py` | read as bytes by hosts and published as Library entries with origin `qml` |
| CT-23 format 3 | `packages/qmf-risk/src/qmf/risk/unit_intent.py` | `door.py` not edited |
| `environment_check()` | `qml/src/qml/environment.py` | QML-25 |
| Surface trim | `qml/src/qml/__init__.py` | 23 old-law names off the top level (AD-120) |

## 3. The compiled closure, step by step (one instant)

1. Collect declared evidence from the injected surfaces (kept `collect_evidence`), closed bars only unless the stream declares ticks or quotes.
2. Update every bound block instance in dependency order; outputs quantised to the port quantum.
3. If any stream is short of its derived warm-up, record `warming` and stop before entries; exits still run.
4. Run the exit set for each position this compiled fingerprint opened (`own_position`), then the position and unit halts; emit `UnitExitIntent`s.
5. Run the logic slots per side; each combiner yields `signal` or `no_signal` with its reason.
6. Drop opposite entries from one instant with a `dropped_opposite` row; suppress entries at the position limit.
7. For a signal: the entry-order block shapes the order; the sizer block sizes it (or skips with a reason); the exit set attaches the first protection; the account halts may veto; stamp `not_before` and the placeholder labels; emit a `UnitEntryIntent`.
8. Motion: derived numbers were refreshed in step 2; calibrated numbers move only at their cadence instants, only when flat on that instrument, by their rule over `own_journal` rows up to the watermark; each move is a calibration row.
9. Return the `UnitStep`: intents, decision rows (taken, skipped, near misses), calibration rows, state events.

Every step is pure; the host journals the rows and turns intents into orders (node) or fills (QMB). QMB and the node do this through one run-slice handler, `qmb/src/qmb/host/unit_handler.py`, which Part B builds (L0 AD-5, R1-L0-02), so the two worlds cannot drift on warm-up, own-position exits or `not_before`.

## 4. Fork: how a hosted unit admits its sized intent (principle-exhaust-the-design-space)

| Option | What | Verdict |
| --- | --- | --- |
| **A. A separate unit door (picked)** | `construct_unit` and `HostedUnit` beside `construct_bot`; `accept_unit_intents` admits only format 3 | Picked. No shipped line changes; a unit hosted the old way fails closed (BR-A4); QMB and the node share one door through Part B's one handler, and layer G's collector calls it too |
| B. QML protocol format version 2 | add 2 to the ladder; `HostedBot` switches its door on the version | Rejected: two shipped tests pin version 2 as unsupported and fail when it is added (BR-A6); skipping to 3 would leave a hole in an ordinal ladder |
| C. A flag in the CT-33 declaration | `HostedBot` reads a `unit` field | Rejected: CT-33's six body fields and its forbidden list define bot identity (`declaration/bot.py:54-93`); a new field changes every bot fingerprint |
| D. A flag on the factory object | `HostedBot` checks an attribute | Rejected: a hidden switch any plain-Python factory could set; the door would branch on an attribute nobody declares |

## 5. The one block loader (R0-07, L0 AD-47)

- **Interface.** `load(lock, sources, weights) -> Loaded or problems`. `lock` is the sorted pin list; `sources` maps a pin to bytes; `weights` maps a pin to bytes. Pure apart from Python's `compile` and `exec` into a fresh namespace.
- **Fingerprint before compile.** LF-normalise, fp1 over `{"block.py": text}`, compare with the pin. A Windows checkout with CRLF and a Linux one with LF give the same fingerprint (A-NEW-1).
- **Error shape.** Every problem at once, each `{kind, pin, message, hint}`; kinds in `CONTRACTS.md` §6.
- **Folder layout.** `CONTRACTS.md` §6; the lock's fingerprint enters the compiled fingerprint.
- **Callers.** `compile` (from bytes the shell gathered), QMB's sandbox child (from Library blobs), the node and the MIS app (from the deployment's block folder). Package data holds only QML's own blocks, which the host reads as bytes; QML itself never reads a file.
- **What the scan bans and why the loader is allowed.** Agent blocks may not use `importlib`, `__import__`, `eval` or `exec`; only the loader does, and it runs only fingerprint-matched source that passed the checker.

## 6. Must not break

| Shipped behaviour | Kept by | Check |
| --- | --- | --- |
| Every bot path through `construct_bot` and `HostedBot` | the unit door is a sibling, not an edit | QML's 385 tests (BR-A3 run) |
| The Book door refusing format 3 | `door.py` untouched; format 3 lives in its own module | Level 0 `blast-radius.md` item 1's cases D and F, kept as tests |
| QML's three dependencies and no console script | blocks import QMF at run time in hosts; the check entry point lives in `qmx-tools` | `qml/tests/test_scaffold.py` |
| Bot fingerprints | `normalize_source_manifest` unchanged; LF normalisation only for blocks | QML's identity tests |
| Callers of the old-law names | none import them from the top level (BR-A3 scan) | the scan rerun in the subtraction slice |

## 7. The language question (Q-10)

QML stays Python 3.14. Every venue QMX reaches from a server speaks a wire protocol any language can use; only strategies that run inside a charting app force C#, MQL5 or C++ (research 54 §2, CHECKED there). The measured floor at 1-minute speed is the network: about 160 ms to cTrader from his PC against about 0.5 ms for in-process fan-out (research 31, CHECKED there). A compiled hot path is parked until a server sits close enough to a venue for Python to become the floor.

## 8. Edge cases handled here

QML-04, QML-13, QML-17 to QML-23, QML-25, QML-26, UT-04, UT-09, UT-16, UT-20, A-NEW-1 (handling lines in the spine's case table).

## 9. Ledger rows that bind it

Q-01, Q-02, Q-03, Q-04, Q-07, Q-10, Q-15, CC-03, CC-08, CC-12, U-01, R-04.

## 10. Seam for growth

A new block kind, motion mode, combiner or measure is catalogue data plus a block, or one row in a vocabulary table; the compiler's dispatch is a registry keyed by those vocabularies, so none needs a new branch in host code. A new runtime behaviour that changes decisions bumps the compiler format version, so existing deployments keep their tested fingerprint.
