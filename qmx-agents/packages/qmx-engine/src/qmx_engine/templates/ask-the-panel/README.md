# Ask several model families and show the spread

The panel of K-11. Three seats answer one open question, each from its own angle and its own model
family; a script builds the spread from what the seats really said; a judge reads the spread and
names the disagreement that matters.

The card never collapses the panel into one confident answer. A seat that never answered stays on
the card as absent. A judge that shares a family with a seat is labelled beside it, because
agreement inside one family is weaker evidence than agreement across families (AD-13).

## Seats

Each seat is an `llm` node with its own role, so the three families come from the settings:

- `member_macro` on the `triage` role.
- `member_positioning` on the `searcher` role.
- `member_sentiment` on the `reviewer` role.

The spread reads each seat's dispatch row from the run's own ledger, so the family on the card is the
family that really served the answer, not the one a lane meant to use.

## Claims discipline

Every claim a seat writes carries a `basis`: `retrieved`, `remembered` or `inferred`. Candidates come
before the pick, and a range comes with its coverage.

## Run it

Manual trigger. Start it with `{"question": "..."}`. A test run with a `fixture` replays the
recorded panel. Point the three roles at three different provider rows to see a spread across
families; on one family the card says so.
