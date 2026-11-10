# Stop point A: one unit trades on paper

This is the release note for stop point A. It says what now works, what is still a placeholder, what your signature covers, and which red tests are not part of this slice.

## The line to sign

Sign the trading node at version 0.1.15. That signature records stop point A. One unit trades on paper from zero, with no broker and no judge, sizes itself, and brakes bind on any unit that declares them.

QMB, the tester app, moves to 1.0.10 in the same PR because test files inside its app folder changed three times. QMB never touches money and is not part of what you sign.

Only your hand signs. The control service's signing route is operator-only and is not an agent tool. The signatures besides yours belong to tests, each made with its own key in its own home.

## What now works

- A new person starts from nothing. The practice month of bars ships with QMX, the `canary` template ships with it, and a first backtest runs with no broker and no sign-in.
- One click takes a draft to paper after the safety half of G, with no judge run. The walk from an empty folder ends with one filled paper trade and a decision row written before the send.
- The unit sizes itself. The sizer answers a money amount, converts it with the account's own rate, refuses an absurd size by name, and every trade answers "why this size?" from one row.
- A broken block costs its unit its new entries, not its exits. One bad unit out of two hundred stays one card, and the other units keep trading.
- Every exit runs on every bar, side-correct, and says why it closed. Brakes are rows read from one fold, and a brake can flatten, stop, or send a unit back to paper. Only the rows that say they wait for a hand wait for you.
- No agent tool reaches promote, the kill level, the floor, or the plan hash.

## What is still a placeholder

- Every number is a labelled placeholder with a range and a reason, owned by "numbers talk". This slice does not tune one.
- The `canary` template carries no brakes, and its title and claim card say so. It is the shape a new person starts from, not a unit to trade live.
- Size and exit numbers stay fixed in this slice. The filter number `min_trend_strength` is the one number this slice proves can move. After 20 closed trades it reads 0.0001, from 0, by the built engine. Sizing and exit numbers first move in stop B.
- Nothing here is live. No broker is bound, no venue sign-in happens, and no order leaves the machine.

## The two shortfalls this slice carries

- The practice account cannot land in the Library. The Library's account kind allows a world of `demo` or `live`, and a practice account is neither. Claiming a world it is not would put a false real-tick share on the card. So K7, the walk from an empty folder to one filled paper trade, ends on the fake broker. Every practice row and card still says `world: paper` and `venue_kind: practice`, so nothing claims to be real ticks.
- A production binding path for the practice venue belongs to the release owner. The node's composition root binds a venue only through the cTrader door. Until that path exists, the practice venue is a rehearsal lane, not a shipped door.

## What your signature covers

Your signature binds the trading node's app folder at 0.1.15. The signature is a keyed hash over four things: the app's id, the hash of that folder, the active revision it replaces, and the action, publish or rollback. The folder hash covers the node's own files, including its `app.toml`, `pyproject.toml` and `uv.lock`. It does not bind the QML. The lock names QML as an editable path with no hash, so a change to the QML alone does not change the signature. The QML this slice changes is this release's subject, not something your signature pins. It does not approve live trading, does not turn a placeholder into a number, and does not make the practice venue a production binding.

Publishing enforces this signature. The publish step computes the expected signature from those four values. It refuses a publish without that signature when the app is money or replaces a money app. The supervisor refuses to start a money app with no active revision or to rebuild a signed version whose sources changed, QML included. The trading node will not go live without your signature. The publish record's `operator_signed` reads `true` whenever the signature was required. There is no separate gate in the release tooling that checks stop point A, so this note and the 0.1.15 version row are the record for the stop point.

## Known reds that are not this slice

The sweep fixed every red this section used to list, and each passes at this head: the derived-pairs test, the six R and money literal tests in the QMB app, the lifecycle refusal text test, and the three dictionary port tests. Its runs are in `evidence/rc-20/sweep.log`.

Two baseline reds remain, and both fail at this head:

- `qmx-agents/packages/qmx-host/tests/test_maintenance.py::test_the_upkeep_switched_off_never_runs_while_rounds_and_the_drill_still_do`. It fails with `drilled is None`. With upkeep switched off, the third sweep lands no drill.
- `qa/tests/epic_13/test_l0_static_build.py::test_t13_006_tier1_static_gate_ruff_and_pyright`. It fails on an over-long line (E501) in `qmb/tests/test_risk_event_rows.py` on line 362.

Neither red belongs to this slice.
