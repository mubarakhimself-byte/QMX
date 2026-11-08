# qmf-risk modules

One sentence per module, saying which of the two risk worlds it belongs to.

The two worlds are the ones the spine names. The **new risk world** is the risk a unit
decides and runs itself through QML blocks, plus the sized intent and the execution target
that carry that decision out. The **wire and accounting** world is the Book and BMS contract,
admission, identity, records, journals and money that the new path cites and, where the swap
says so, retires. The spine's new qmf-risk modules (`chain.py`, `facts.py`, `controls.py`,
`group.py`) do not exist yet; the slices that build them land beside `unit_intent.py`.

- `__init__.py` belongs to the wire and accounting because it re-exports the Book, BMS,
  admission, binding, paper, door, record and journal types and runs nothing of its own.
- `_bench.py` belongs to the wire and accounting because it is the package's benchmark slot,
  and it measures a placeholder workload without holding a risk rule.
- `_common.py` belongs to the wire and accounting because it holds the refusal builders and
  enum coercion that the contract modules share.
- `admission.py` belongs to the wire and accounting because it runs the three ordered
  admission layers that end in the operator's signature.
- `admission_bar.py` belongs to the wire and accounting because it defines the
  per-requirement bar that refuses a composite score and blocks a blank threshold from live
  money.
- `binding.py` belongs to the wire and accounting because it mints the dated Book and BMS
  binding record, its identity trinity and its bind-time capability check.
- `control_action.py` belongs to the wire and accounting because it types the old CT-30
  control actions and their same-tick arbitration, which the new risk world replaces with
  QML control rows.
- `control_rank.py` belongs to the wire and accounting because it holds the BMS rank table
  that ordered the old arbitration, which the new group caps replace.
- `control_window.py` belongs to the wire and accounting because it types the old CT-31
  no-trade windows, which the new risk world replaces with QML reads and node stickers.
- `dimensional.py` belongs to the wire and accounting because it checks the unit kinds of
  the template formulas and keeps the dead FORM-0006 as a permanent negative test.
- `door.py` belongs to the wire and accounting because it is the Book's risk-evaluation
  door for bot entry and exit intents.
- `exit_policy.py` belongs to the wire and accounting because it resolves the Book's
  per-family exit policy entry, including the format-2 catch-all.
- `exit_record.py` belongs to the wire and accounting because it records one exit per Book
  position close, attributes the whole trade and folds the bench.
- `footprint_requirements.py` belongs to the wire and accounting because it fills the
  reserved footprint requirement slot with typed admission requirements.
- `grammar.py` belongs to the wire and accounting because it defines the four-part template
  variable every Book and BMS number is written as.
- `journal.py` belongs to the wire and accounting because it projects the Book, BMS and bot
  journals from the one writer-scoped stream.
- `migrations.py` belongs to the wire and accounting because it holds the format-1 to
  format-2 migration notes for CT-22 and CT-23.
- `numeraire.py` belongs to the wire and accounting because it fixes USD as the V1 numeraire
  and refuses a Book limit stated in lots.
- `paper.py` belongs to the wire and accounting because it types paper as a dated binding
  change, and the one export the new path cites is `ExecutionTarget`, the per-intent routing
  target.
- `performance.py` belongs to the wire and accounting because it publishes a performance
  result and refuses any score that could gate live money.
- `r_faces.py` belongs to the wire and accounting because it mints the frozen R faces and
  crosses money and R over a named rate.
- `sizing.py` belongs to the wire and accounting because it validates the Book's old money
  ladder unit kinds and refuses a count where an r-multiple belongs.
- `templates.py` belongs to the wire and accounting because it is the Book and BMS
  definition container and its fp1 identity.
- `unit_intent.py` belongs to the new risk world because it is the format-3 wire that
  carries the quantity the unit's own sizer chose, including `none_declared` for a unit
  that declares no stop.
- `versioning.py` belongs to the wire and accounting because it versions Book and BMS
  templates as a branch-and-pointer graph.
