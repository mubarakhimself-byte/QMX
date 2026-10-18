# RS2 Source to component card

Built from card R2 with R5 (understand and extract) and R7 (calibrate) in `research/methodology/15-templates-researcher.md`. It takes one piece of a paper, such as a signal, a filter, an exit, a sizing rule or a regime classifier, and makes it a card the Lab can test on its own. Every field the paper does not state stays `unresolved`.

## Steps

1. `Source and piece` takes the captured text and the piece to extract.
2. `Sections`, `Read each chunk of sections` (role `reader`) and `Quotes check` are the shared `understand-extract` block: located claims, each tagged source-stated, inferred or unresolved, and each quote checked against its section.
3. `Extract the component` (role `extractor`) writes the card: formula, data frequency, warm-up, claimed effect, inputs, parameters with the paper's defaults, stated failure cases, and an ablation plan (host kinds, and the test host with versus without).
4. `Keep the holes` makes any field, parameter or failure case that rests on no cited claim read `unresolved`, and lists the holes and what it changed.
5. `Items to calibrate` and the shared `calibrate` block give the claimed effect and the formula a confidence: basis labels from the quote check, two `reader` samples and one `reviewer` sample, then the agreement rule.
6. `Render and grade` checks the card against `schemas/output.json` and checks every number in its formula, frequency, warm-up, claimed effect, parameters and ablation plan against the paper. A failed check stops the run as failed.

## Test runs

A run started with `{"fixture": true}` reads `fixtures/source.json`, a synthetic paper that leaves the warm-up and the threshold default unstated. `fixtures/recorded/` holds the answers for the `--fake` switch and the unit tests (`component.json` answers the agent step in tests only).

## Left out, and why

- The duplicate pre-check on formula hash or name: it needs the real Library.
- Reading the PDF with `answer_pdf_queries`: text arrives already captured; the PDF tool is a later packet.
- The code stub, its unit test, the test run and the lookahead lint in the Lab sandbox: they need the sandbox.
- Naming host strategies from the Library: the ablation plan names host kinds instead.
- The rerun spread in calibrate: it needs Lab reruns.
- Asking him to pick between two readings of a formula: the extractor records the reading it took under `assumptions` (rulings 57 and 77).
- The Library write and the paper-to-component lineage edge: the real Library is held (ruling 91).
