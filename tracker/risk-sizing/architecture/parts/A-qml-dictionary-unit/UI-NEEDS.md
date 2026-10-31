# What the UI needs from Part A (notes and design proposals only)

Part A, 31 Oct 2026, for the UI session. No UI code is written or edited here (ruling 45: "You're not going to touch my designs"). Built on the screens and promises already recorded (`architecture/funnel/experience/ui-needs.md` §3, §4, §6, which read the design from screenshots) and on the Library's shipped card and page shapes (`qmx-library/src/qmx_library/kinds/unit.schema.json`: card facts version, state, used in; tabs Logic, Results, Family tree, Markets, Versions). Each section says where it folds into an existing view and which backend shape feeds it.

## 0. Words on the screens

| Thing | Words |
| --- | --- |
| A number's kind | Fixed · Follows the market · Follows its record |
| A number's origin | Source said · Convention · Builder chose · Unresolved · Placeholder |
| A check result | Checks passed · N problems · Warnings only |
| An entry's status | Named · Specified · Has code · Tested on data · Used in a unit |
| A unit's state on one market | Draft · Tested · Parked · Paper · Live · Stopped · Retired |
| Why a unit is not trading (from the unit's own rows) | Warming up · At its position limit · No signal · Skipped: `<reason>` |

## 1. The copilot while it writes a unit

- **Shows.** Beside the chat, the unit draft as a card filling slot by slot; under it the latest check: "N problems" with each problem in one line (where, what, the hint), errors first; when empty, "Checks passed" with the layers named on tap. A "No progress" line when the same problems came back twice, with what the copilot stopped on.
- **Backend.** `unit_check` (`qmx.check/1`, counts first); `unit_explain` for the card.
- **Folds into.** The copilot's right-hand panel.

## 2. The unit page (detail) and card (preview)

The card keeps the shipped facts (version, state, used in) and adds a placeholder stripe when any slot holds a placeholder.

| Tab (proposed additions marked) | Shows | Backend |
| --- | --- | --- |
| Logic (exists) | the slots in trader words, each with its block and status; the combiner in one sentence ("all of these", "2 of these 3") | `unit_explain`; pins |
| Numbers (proposed) | every number: value now, range as a dial, kind, origin, last move with its receipt on tap, an "at its limit" mark | `numbers` in the document; calibration rows (Part B's journal) |
| Checks (proposed) | the latest check per layer, the G safety verdict and the behaviour report (trades on the slice, exits fired and unfired, constant signal), the checker version | `qmx.check/1`; the `test-report` record (`qmx.behaviour/1`) |
| Blocks (proposed) | the lock: every pinned block, its version, status and whether a newer version exists ("a fix is available: making a new version re-tests it") | `pins`; entry status annotations |
| Markets (exists, reads `fields.markets`) | per market: lifecycle state, its own settings if earned, data level offered against needed | the lifecycle fold; layer D |
| Results, Family tree, Versions (exist) | unchanged; Versions labels each change by its edit kind ("range change: new version") | `qml.identity.classify` |

## 3. Publish and promotion cards

- **Publish (his yes on a draft).** One card: what the unit is in two sentences, the checks passed, the placeholders it carries (a stripe naming them), what may move by itself (each derived and calibrated number with its range). The publish button runs the full check; if it fails, the card lists every problem instead.
- **Promotion toward paper or live (OP-03).** The card shows what changes against what is live on that market: the document diff in trader words, the edit labels, the pinned blocks that differ and their versions, and whether the change is a new version or a new unit. "Admitting this version parks version N on EURUSD" when another is live there (UT-23).
- **Backend.** `qml.identity.diff` and `classify`; the lifecycle fold; publish runs `qml.unit/1`.

## 4. The dictionary pages

- **Entry page.** Three faces as three sections: what a trader means (with each class's meaning, and the sources with their quotes and dates), what data it needs (data level with the fallback chain and its expected loss), and the code (status, golden tests, settle length). "Used by" lists the units that pin it.
- **The port card.** "Publish the ported dictionary: 239 pages, all passing" with a list view he can scroll; one click publishes the collection.
- **Append requests.** Words an agent found in a source that match no page, each with its sentence and source, as proposals he can accept into drafts.
- **Backend.** `blocks_get`, `blocks_find`, `blocks_match`; status annotations; the port's collection.
- **Folds into.** The Library's existing item page for the `component` kind (tabs Code, Parameters, Uses, Used by, Versions exist); the entry faces are proposed as the top of that page.

## 5. Gaps the UI will meet

| Gap | Owner |
| --- | --- |
| Calibration rows and decision rows need Part B's journal read path before the Numbers tab can show moves | Part B |
| The lifecycle fold needs the lifecycle journal kind | Part B |
| Layer D's market column needs Part C's instrument records | Part C |
| Publishing a collection in one click needs a small host operation that publishes each item in turn (idempotent) | Part A proposes it in `LEAD-CALLS.md` LC-A1-14; the build plan places it |
