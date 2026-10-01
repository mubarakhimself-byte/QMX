# Independent ATC runtime semantics exploration

Reviewer: GPT 6.1 Sol. Read-only product exploration against full governing
architecture aligned by `a14c121351bff8b379b6bb068fca2f05c976010d`. No product
source writes or provider/credential access. Local `origin/main` still points
at the earlier `c3e8ec5e` ref; the corpus alignment commit is the evidence pin.

## Finding

ATC is an adopted complete trading composition, not an optional/deferred class.
The restored September 18 architecture supplies its identity, ownership,
admission, accounting/risk obligations and end-to-end adoption requirements.
It does **not** supply executable semantics for the example opaque policy tokens
`fixed-fraction`, `max_gross`, `fifo`, `last-mark` and their complete numeric
inputs. A descriptor handoff cannot itself earn actual ATC runtime acceptance.
The unresolved portion is token interpretation and concrete policy parameters,
not authority to build the ATC lifecycle or a reason to narrow ATC/optimization
scope.

Precise authority:

- `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md:222`
  adopts AD-23. Line 226 requires accounting cash/position identity, fill
  application, valuation/currency/residual meaning; risk limits/halt/sizing/
  UNKNOWN handling/override principal; immutable PolicyPair identity; actual
  QML/QMB optimization/QMN adoption; CT-07 lineage; sequential paper/live.
- Same directory `CONTRACTS.md:654` starts AlternativeRunConfig. Lines 665–679
  show example policy snapshots: `fifo` at 669, `last-mark` at 670,
  `max_gross: "100000"` at 675, `halt: "on-unknown-or-limit"` at 676 and
  `sizing: "fixed-fraction"` at 677. Line 705 specifies the canonical hash
  preimage; line 707 specifies authoritative admission. It does not define a
  fraction, its capital/risk basis, exposure unit/marking convention, lot
  rounding, signed financing treatment or transition functions for those tokens.
- `docs/decisions/ADR-0024-workflows-construction-kit.md:124` says A1 PolicyPair
  field catalogue proceeds: the ATC class is operator-direct and the field list
  is sitting machinery. This permits implementation of the adopted shape; it
  does not choose an unspecified financial fraction.
- `docs/components/qmb.md:272` requires evaluation **and optimization** to adopt
  the selected ATC; line 275 refuses dummy/no-op/unlimited/pass-through policies;
  line 279 requires ATC JSONL and CT-07 lineage, comparing only conserved measures.
- `docs/scenarios/SCN-0020-two-trading-compositions.md:37` requires selected ATC
  adoption; line 45 requires actual validate/simulate evidence. An internal
  simulate token is part of that journey, not evidence that accounting/sizing
  executed against recorded market data.

Targeted searches covered full September 18 architecture Markdown, restored
`_docwork` rider/extractions, docs component/contracts/registry, and the current
ATC parser/runtime source. Other `max_gross`/`fixed-fraction` occurrences are
copies of the same illustrative contract example, not a numerical execution
grammar. The registry supplies no ATC fixed-fraction parameter in the searched
entries.

## Current source boundary

`qmb/src/qmb/config/alternative.py:122` and 130 declare accounting/risk field
catalogues. `_require_section` at 941 admits token/integer values and required
keys; it does not interpret policy behavior. `simulate_alternative_run` at 645
validates and mints an internal token/lineage/journal identity (680–729), without
market input, cash/position transitions or sizing execution. A structurally
complete PolicyPair remains distinct from a demonstrated complete runtime.

A generic policy runtime interface can honestly be implemented using the adopted
roles, exact QMF value types, pinned policy identity, actual selected-policy
execution and refusal for unsupported interpretations. Actual financial runs
must use an explicitly specified executable policy with its fraction/basis,
limits/valuation/rounding and state-transition rules. Those facts must not be
silently guessed from the JSON illustration. No new ratification or formal
GAP-* identifier is invented by this evidence.

## Next independently reviewable default-path seams

Coordinated directly with execution/data implementers:

1. Execution owns the new CT-12 SourceObservation partition/admission adapter
   in `qmb.host.replay`. Review its immutable split identity, actual source refs,
   window/evidence ownership and as-of horizon first. Current CT-10 materializer
   is already independently reviewed; CT-12 source is not yet a stable candidate.
2. Data owns `qmb.host.book_handler` next. It must consume selected typed
   proposals, explicit sizing/full-loss inputs and existing Book admission,
   preserve original authorization/position identity, and persist CT-13/CT-29
   evidence. The implementer reports the QMB/QMF virtual-position mint/identity
   seam still unresolved; importing QMN or duplicating its runtime mint is not
   authorized by a descriptor.
3. Then independently exercise the actual installed request/child transport,
   selected source, Book veto/partial fills/close, economic collector and one
   terminal record. CLIchild/Book composition currently remains in progress.

These seams continue the full objective; they do not substitute Book work for
ATC or optimization acceptance.
