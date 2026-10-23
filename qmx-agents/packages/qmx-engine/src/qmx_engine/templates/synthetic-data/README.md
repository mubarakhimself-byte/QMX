# Synthetic data from a month of prices

Lib AD-28's synthetic-data generator as one engine run. It draws a series of the same length and clock as a month the market-data door served, and writes the dataset card the Library keeps: `world: synthetic`, the generator, its settings and the seed, so the same seed draws the same series again.

The whole point is the purpose. A synthetic series is a stand-in for data he is allowed to train on, so a run may only draw from `purpose: train`. The door serves the validation, test and final-look segments under a split, and a synthetic series drawn from one of those would put held-out rows back into training under another name.

## Steps

1. `Draw the synthetic month` reads the door's `rows` for the month and draws the generator's output. With any `purpose` other than `train` it writes the refusal to stderr and exits non-zero before it draws anything; the run parks on that step with the reason in its log. `moving-block-bootstrap` walks the source in blocks of `settings.block_rows` rows, each block starting at a seeded position, and keeps the source's own timestamps, so the synthetic month is the same minutes with resampled prices.
2. `Render and grade` checks the card against `schemas/output.json`: `world` is `synthetic`, and the generator, its settings, the seed, the source card version, the months, the row count and the values are all there.
3. `Deliver` hands on the card alone. A failed check stops the run on `Stop on a failed check` and writes nothing.

## What the card carries

`source_card` is the dataset card version the month was read from, so the card names what it was drawn from. That is the `derived-from` edge the door's rule asks for; the relation itself is written where the run's objects land, which is the engine's landing step and not this template's script.

## Test runs

A run with `{"purpose": "test"}` exercises the refusal, and a run with `{"purpose": "train"}` and a few rows of a month draws a card. No model call is involved, so the row carries no recorded fixture.

## Left out, and why

- A generator that invents a calendar: the source month's own timestamps are kept, so a card never claims minutes the door did not serve.
- A second generator: the plan asks for one seeded generator and its settings. Another is a row in `scripts/generate.py`, not a template.
