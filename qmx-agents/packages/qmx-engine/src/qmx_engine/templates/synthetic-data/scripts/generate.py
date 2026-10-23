"""Turns the month the door served into a synthetic series, and refuses any purpose but `train`.

Library AD-28: a synthetic generator reads through the market-data door with `purpose: train` only,
so a run may never draw from the validation, test or final-look segment, and the card it writes says
`world: synthetic` with the generator, its settings and the seed, so the same seed gives the same
series again.

`in` carries what the door served: `rows` are the month's `[t_ms, bid, ask]` rows, `months` names
them and `source_card` is the dataset card version the read is pinned to. The generator walks the
source in blocks of `settings.block_rows` rows, each block starting at a seeded position, and keeps
the source's own timestamps, so the synthetic month is the same minutes with resampled prices.
"""

import json
import random
import sys

PURPOSES = frozenset({"train"})
GENERATORS = frozenset({"moving-block-bootstrap"})

given = json.load(sys.stdin).get("in") or {}
purpose = given.get("purpose")
if purpose not in PURPOSES:
    sys.stderr.write(
        "a synthetic series reads through the door with purpose train only (Lib AD-28); "
        f"purpose {purpose!r} is refused"
    )
    raise SystemExit(2)
generator = given.get("generator") or "moving-block-bootstrap"
if generator not in GENERATORS:
    sys.stderr.write(f"unknown generator {generator!r}; this template ships {sorted(GENERATORS)}")
    raise SystemExit(2)
source_card = given.get("source_card")
rows = given.get("rows")
seed = given.get("seed")
if not isinstance(source_card, str) or not source_card.strip():
    sys.stderr.write("a synthetic series names the dataset card version it derives from")
    raise SystemExit(2)
if not isinstance(rows, list) or not rows:
    sys.stderr.write("a synthetic series needs the rows the door served for its month")
    raise SystemExit(2)
if isinstance(seed, bool) or not isinstance(seed, int):
    sys.stderr.write("a synthetic series names an integer seed, so it can be drawn again")
    raise SystemExit(2)
settings = dict(given.get("settings") or {})
block = settings.setdefault("block_rows", 7)
if isinstance(block, bool) or not isinstance(block, int) or not 1 <= block <= len(rows):
    sys.stderr.write(f"settings.block_rows is a whole number of rows from 1 to {len(rows)}")
    raise SystemExit(2)

rng = random.Random(seed)  # noqa: S311 - a seeded bootstrap, not a secret
drawn = []
while len(drawn) < len(rows):
    start = rng.randrange(len(rows))
    drawn.extend(rows[start : start + block][: len(rows) - len(drawn)])

values = [[row[0], picked[1], picked[2]] for row, picked in zip(rows, drawn, strict=True)]
print(
    json.dumps(
        {
            "world": "synthetic",
            "generator": generator,
            "settings": settings,
            "seed": seed,
            "source_card": source_card,
            "months": list(given.get("months") or []),
            "rows": len(values),
            "values": values,
        }
    )
)
