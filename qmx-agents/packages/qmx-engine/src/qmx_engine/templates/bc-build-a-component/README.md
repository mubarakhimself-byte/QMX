# Build a component or indicator

Waits for the Lab sandbox where agents write and built code runs (`needs: sandbox`).

Built from cards D1 (component card to Lab build with tests) and D5 (indicator authoring) in `research/methodology/17-templates-dev-pm-lab.md`. It turns a component or indicator card into a Lab piece in Graph and Code, with tests written first that prove it does what the card says, and a no-future test that catches lookahead without a model.

## Steps

1. `Check the card and scaffold` (zero tokens) refuses a card whose parameters lack a value or `unresolved`, or that names no formula, warm-up or output type. A Pine source with `lookahead_on` or a repaint flag is rebuilt without it and labelled a child. It hashes the formula and lists the folder to fill.
2. `Card complete?` stops an incomplete card with its problems.
3. `Write the tests, then the code` (role `builder`, 30 turns) writes the worked example, the edge cases and the no-future test, then the code. An `unresolved` parameter stays a parameter.
4. `Run the checks in the sandbox` (`scripts/checks.py`) runs the tests, the cut-at-t and full-data computations, the cold start, lint, types, speed, the Graph round trip and the file log.
5. `No-future, warm-up and test-first verdict` decides by script: every sampled value matches on cut and full data, the warm-up values are missing and not zero, every test file was written before the code, the Graph round-trips, tests, lint and types are clean.
6. `Review the code against the card` (role `reviewer`, the card's validator) answers whether the code matches the card and whether any value is invented.
7. `Publish or keep as a draft` offers a version only when everything is green; otherwise the draft names each failing check, and a test still failing after one repair saves a `fragment`. `Render and grade` checks every number in the review against the card and the checks.

## Left out, and why

- The Library dedupe on the formula hash and publishing to the Toolbox: they need the real Library and L3's promote step; the result carries the hash and "ready to publish a version".
- Two readings of a formula that change the meaning: they end as a note in the review, because `human_gate` is unavailable.
- The picture on a fixed chart week and the distribution plot: the sandbox makes them; drawing them is UI-side.
- The reviewer on another model family: Settings maps the `reviewer` role; until a second family is set, it is a fresh context with the same family.
- Test fixtures: they come with the sandbox, whose real check output they must match.
