"""Runs the built component in the sandbox (card D1 steps 4 to 7, card D5 steps 4 to 7): the unit
tests, the component computed on data truncated at sampled bars t and on the full data, its first
values after a cold start, lint and type check, a speed check in bars per second on a fixed
dataset, the Graph view produced from the code's declared steps and rebuilt into code and back,
and the picture on a fixed chart week. The order the builder wrote its files in comes from the
sandbox's file log.

Its output is `tests` (name and passed), `truncated` and `full` (the values at each sampled t),
`first_values`, `warm_up`, `lint`, `types`, `bars_per_second`, `graph_round_trip`
(`graph`, `rebuilt`), `written` (each file with the order it was first written in) and `picture`.
Until the sandbox exists, agent nodes cannot write and nothing can run, so this template stays a
draft (`needs: sandbox`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the Lab sandbox that runs built code (needs: sandbox)")
raise SystemExit(1)
