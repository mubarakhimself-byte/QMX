# Blast radius of the shipped files Part A changes

Part A, 31 Oct 2026, skill `blast-radius`. For each shipped seam this part changes: what changes, the one fact it is safe because of, how far that fact was proven (1 said, 2 pointed at the line, 3 walked the failure, 4 ran it, 5 reproduced in the running app), the risks found, what was cleared and the cheapest check before merge.

**How the code was run.** Against scratch exports of `origin/engine/base` `c93407ca` made with `git archive` from the read-only checkout into this agent's scratchpad (`...\scratchpad\l1a\root\`), with the existing environments of the earlier export (`...\scratchpad\eb\.venv`, `eb\qmx-agents\.venv`, Python 3.14.6). Patched modules were put first on `PYTHONPATH`; the read-only checkout was never written. Scripts: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\l1a\br\`.

## Summary

| # | Seam | The one fact | Step |
| --- | --- | --- | --- |
| BR-A1 | The Library's kind check returns every problem; kind files list checks; `unit` gets a shape schema; `component` gets an entry face | kinds without an applying check behave exactly as today, and the shipped every-kind test's minimal items pass a shape-only unit schema and a marker-conditioned entry check | 4 |
| BR-A2 | Two new core toolsets with domain-function rows | the harness's in-process servers come from its own roster `DOMAIN_GROUPS`; derived from the catalog rows, every shipped harness, tools and control result is unchanged | 4 |
| BR-A3 | 23 old-law names leave QML's top-level surface | nothing in the repository imports them from the top level | 4 |
| BR-A4 | Units hosted through a new unit door | today's `HostedBot` refuses a format-3 intent, so a unit hosted the old way fails closed | 4 |
| BR-A5 | Block source stored in the Library | the write redaction leaves ordinary strategy-library Python unchanged and rewrites only key-shaped text | 4 |
| BR-A6 | (the rejected option) a QML protocol version 2 | adding it fails exactly two shipped tests | 4 |
| BR-A7 | The host lands the dummy unit as a draft on first start (R1 fix round, R1-A-05) | the find-then-put landing keyed by a field writes nothing on a rerun, so a second start adds no second dummy | 4 (the shipped pattern's tests), 2 (no host test asserts a fresh store's contents) |
| BR-A8 | The dummy's slow rule shrinks its edge toward the default (A-NEW-6) | the first rule's shrink toward zero kept every sign, so it never changed a decision | 4 |

## BR-A1. The Library's kind check and kind-file checks

**What changes.** `Kind.check` collects every JSON Schema problem (message and pointer), keeps the first message as the refusal text, and runs any `checks` entry the kind file lists for the event when its `applies_when` holds; an applying check with no registered checker refuses `checker_unavailable`. `unit.schema.json` moves to schema version 2 with a shape-only schema and a publish check; `component.schema.json` gains new `component_type` values, an optional `entry` object and a put check that applies only when `/entry/schema` is `qmx.entry/1`.

**Where grep stops.** `qmx-library/tests/test_view.py:110-128` saves, for every live kind, the smallest fields its own schema allows (`filled_from`, `:45-63`). The first version of this design ran a deep unit check on every save; running it refused that test's minimal unit:

```text
E   qmx_library.port.LibraryRefused: checker_unavailable: unit: no checker 'qml.unit/1' is registered on this host
FAILED tests/test_view.py::test_every_kind_answers_a_card_of_at_most_five_facts_and_a_page
1 failed, 100 passed in 60.20s
```

**Proof (step 4), the refined design** (`bra1_patch_library.py`: shape-only unit schema with a publish check, marker-conditioned component check, no checker registered):

```text
qmx-library: 101 passed in 26.65s
qmx-control: 3 failed, 173 passed, 2 skipped   (patched)
qmx-control: the same backup tests fail unpatched in this environment (rclone is not installed); no other test differs
```

**Risks confirmed.** (1) A save-time deep check of `unit` breaks a shipped test (cost: CI red; odds: certain). Closed by AD-111. (2) A dictionary check keyed on `component_type` would refuse mini apps' provides components and migrated confluences, which carry no entry faces (`qmx_control/library.py:312-330`, `migrate/from_apps.py:66-70`, `migrate/from_registry.py:34`). Closed by the explicit marker.

**Cleared.** The refusal text for kinds without checks is the same first message as today (`kinds/__init__.py:46-55`), so the 28 text-comparing test lines stay green (Level 0 `blast-radius.md` item 6 and this run). `ingest` from a peer does not run checks (`store.py:2259-2268`), so replicas never refuse an object checked at its origin.

**Before merge.** The Library and control suites; a test that a store with no registered checker refuses an entry save and accepts a provides component.

## BR-A2. Two new core toolsets

**What changes.** `CORE_TOOLSETS` gains `unit` and `blocks`; seven `domain_fn` rows; `qmx_tools.functions` gains the two groups.

**Where grep stops.** The harness builds one in-process server per name in its own tuple `DOMAIN_GROUPS = ("data", "backtest", "research", "node")` (`qma-harness/src/qma/harness/tools.py:668`, used at `:641`). With rows and functions added but the tuple unchanged, the tool list refuses:

```text
qma.harness.tools.ToolSurfaceError: catalog rows are missing on their server: blocks_check, blocks_find, blocks_get, blocks_match, unit_check, unit_explain, unit_new
```

A second trap: FastMCP refuses functions with `**kwargs` ("Functions with **kwargs are not supported as tools"), so the row functions need explicit parameters.

**Proof (step 4)** (`bra2_patch_toolsets.py`: rows, functions with explicit parameters, `DOMAIN_GROUPS` derived as `tuple(dict.fromkeys(row.toolset for row in DOMAIN_ROWS))`):

```text
DOMAIN_GROUPS -> ('data', 'backtest', 'research', 'node', 'unit', 'blocks')
qma-harness: 131 failed, 659 passed (patched) | 131 failed, 659 passed (unpatched): same failure set
qmx-tools:   12 passed (patched) | 12 passed (unpatched)
qmx-control: no test differs apart from the backup tests, which fail in this environment with and without the patch
```

The 131 harness failures exist unpatched in this scratch environment (provider and chat tests that need a real home and sign-ins); the patched set is identical by name.

**Risks confirmed.** Adding the rows to `research` instead would change the research server's tool count pinned at `qmx-tools/tests/test_tools.py:374-375`.

**Before merge.** Rerun the harness suite on a real checkout and compare with the base branch's result; the parity test that every agent-visible core row is on the default copilot surface.

## BR-A3. Old-law names off QML's top-level surface

**Proof (step 4)** (`bra3_surface.py`: an AST scan of every `.py` in the export for `from qml import <name>`, `from qml import *` and `qml.<name>`, then a trimmed `__init__.py`):

```text
old-law names on the top-level surface: 23
callers using them from top-level qml: 0 []
trimmed __init__ written, lines removed: 46
qml: 385 passed in 103.78s
```

**Cleared.** Tests import these names from `qml.generation` and `qml.research`, which keep them (`qml/tests/test_research_stage0.py:22`, `test_research_collapse.py:22`). Stage 0's behaviour is unchanged, which keeps `test_research_stage0.py:100` and `test_research_collapse.py:82` green.

## BR-A4. The wrong door fails closed

**Proof (step 4)** (`bra4_wrong_door.py`: the shipped example's declaration, a factory whose callback returns a format-3 entry, hosted through today's `construct_bot`):

```text
A unit entry stamped CT-23 format 3 -> REFUSED unsupported capability field=contract_format_version
B nothing emitted (silent instant) -> ACCEPTED 0 intent(s)
```

**Fact.** A compiled unit hosted by mistake through the bot door cannot be sized by the Book path; its first sized intent is refused. The unit door is a sibling module, so no shipped line of `factory.py` or `intents.py` changes.

## BR-A5. Block source and the Library's write redaction

**Proof (step 4)** (`bra5_redaction.py`: `qmx_engine.ledger.redact.redact` over every `.py` under `qml/src`, `qml/examples`, `qmb/src` and `packages/*/src`):

```text
files scanned: 325 lines: 179592
files the redactor would change: 0 []
key-shaped literal in a block rewritten: True
```

**Fact and risk.** Ordinary strategy-library code survives the Library's blob redaction byte for byte (`qmx-library/src/qmx_library/store.py:843-855`), so a block's stored source equals its checked source; a key-shaped literal is rewritten, which would change the fingerprint (A-NEW-2). Closed by the entry checker refusing source the redaction would change, and by the loader fingerprinting the bytes it receives.

## BR-A6. The rejected option: QML protocol version 2

**Proof (step 4)** (protocol known versions set to `{1, 2}` in a scratch copy):

```text
FAILED tests/test_protocol.py::test_unknown_protocol_format_version_is_unsupported_capability
FAILED tests/test_protocol.py::test_construct_bot_refuses_unknown_protocol_version
2 failed, 39 passed in 3.41s
```

This is the evidence behind fork F1 (`1-qml-door-compiler-runtime.md` §4).

## BR-A7. The dummy lands in his Library on first start (X1-0A)

**What changes.** At composition, beside registering the two checkers, the host puts the dummy unit document on its item's draft ref when no item carries the same document fingerprint (A7, AD-118). It never merges onto main; his yes publishes it.

**The one fact.** The Library's own migration lands app items the same way: `once(store, key, value, draft)` returns the existing object when an item's `fields.<key>` already holds the value, and puts the draft only otherwise (`qmx_library/migrate/from_apps.py:52-57`, with `with_legacy` at `qmx_library/migrate/__init__.py:87-94`). A rerun therefore writes nothing. The find also sees an item that exists only on a draft ref, because the catalog indexes every ref's move, drafts included (`qmx_library/fts.py:42-45`, `:187-200`, read), and `with_legacy` joins on those moves.

**Proof (step 4).** The shipped tests that pin that behaviour, run in the scratch export's agents environment (the export's `from_apps.py`, `migrate/__init__.py` and `test_migrate.py` compared with the read-only checkout ignoring line endings: identical):

```text
$ python -m pytest packages/qmx-library/tests/test_migrate.py -q -p no:cacheprovider -k "rerun_writes_nothing or app_artifacts"
2 passed in 56.74s
```

**Risks.** (1) A shipped test that opens a host on a fresh folder and counts drafts or units would see one more. A grep over `qmx-host/tests` for assertions on Library contents found none (step 2); A7's Verify runs the host, control and library suites, and if one counts, the landing moves behind the first-start card's `make_new` plus a one-time host step for existing folders. (2) The `place` helper beside `once` merges a governed draft onto main; the landing must not use it, or the dummy would be published without his yes. A7's test asserts the dummy is a draft.

**Before merge.** A7's fresh-folder test: one draft after the first start, still one after the second.

## BR-A8. The dummy's slow rule and its shrink (X1-0A)

**What changes.** `trend-floor-from-record@1` finds the lowest bucket edge above which every bucket with trades has a mean R of at least zero, then shrinks that edge toward the number's default by n/(n+k) before moving one step (`2-unit-template-numbers-lifecycle.md` §6).

**The one fact.** The first rule shrank each bucket's mean toward zero and then tested its sign. Multiplying by n/(n+k), which is positive, never changes a sign, so `shrink_k` had no effect on any decision.

**Proof (step 4).** `scratchpad\x1-0a\shrink_sign.py`, exact fractions, 10,000 random bucket sets:

```text
cases where k changes the old rule's edge: 0 of 10000
amended target at n=20, k=100, edge 0.12, default 0.00: 0.02
amended target at n=400, k=100, same edge: 0.096
```

**Before merge.** A5's test feeds a hand-made `own_journal`, asserts no calibration row before the 20th closed trade and one step toward the shrunk edge after it.

## R1-A-04, checked and rejected

R1 said `DOMAIN_GROUPS` sits at `qma-harness/src/qma/harness/tools.py:664`. At `c93407ca` it is defined at line 668 and used at line 641 (`git show c93407ca:qmx-agents/packages/qma-harness/src/qma/harness/tools.py | grep -n DOMAIN_GROUPS`, run in the read-only checkout; the file has CRLF endings and Python's `splitlines` gives the same two lines). BR-A2's citation stands.

## Not proven here

- Plugin hooks firing under the Agent SDK from the core plugin (needs a running chat; slice A14's probe).
- Layer G inside QMB's sandbox child on Library data (Part B's runner; slice A6 proves the functions in process).
- The node loading a deployment's block folder (Part C).
- The CT-23 format 3 module (new code; its safety rests on `door.py` being untouched, which Level 0 `blast-radius.md` item 1's cases pin).
