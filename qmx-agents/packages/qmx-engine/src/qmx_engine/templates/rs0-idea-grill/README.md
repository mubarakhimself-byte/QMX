# Question a rough idea until it is a clear test plan

Built from card R0 in `research/methodology/15-templates-researcher.md`. It turns a one-line idea, such as "funding spikes predict reversals", into a term sheet that can die: a mechanism, a universe and timeframe, the data it needs, an entry, an exit or `unresolved`, at least one kill criterion, a capacity guess, and what could fake the result.

## Steps

1. `Idea and what is known` takes the idea and the known dead ends from the run input, so known facts are shown and never asked.
2. `Grill` (role `planner`) asks at most five numbered questions, each with a recommended answer.
3. `Draft the term sheet` (role `writer`) adopts every recommended answer, records each one under `assumptions`, and warns on top when a known dead end shares the mechanism.
4. `Render and grade` (the shared `render-and-grade` block) checks the term sheet against `schemas/output.json`, which demands a mechanism and a kill criterion, and checks that every number in the dead-end warning, mechanism, universe, timeframe, data, entry, exit, kill criteria, capacity guess and "what would fake this" lines comes from the idea or a recorded assumption. A failed check stops the run as failed.

## Test runs

A run started with `{"fixture": true}` reads `fixtures/idea.json`, a synthetic idea and dead end. The answers in `fixtures/recorded/` serve the `--fake` switch and the unit tests.

## Left out, and why

- His answers to the questions and the second round: nothing in a run waits for him (rulings 57 and 77), so each recommended answer becomes a recorded assumption he can overrule by editing the card and running again.
- Searching the Library for prior term sheets, dead ends and rejected ideas: it needs the real Library. Dead ends come with the run input; without them the step says the Library was not searched.
- His correction of the card and the operator-scope memory of rejected ideas: a human step and operator memory are later packets.
- Saving the card to the Library: the real Library is held (ruling 91); the term sheet is the run's result.
