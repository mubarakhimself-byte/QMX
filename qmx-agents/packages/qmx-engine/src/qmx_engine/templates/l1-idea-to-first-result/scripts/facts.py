"""The pre-check, run before the first question (card L1 step 1): Library search for prior boards,
term sheets, components and dead ends on the same mechanism; Toolbox search for the indicators and
components he named; and data availability for the market and timeframe his words imply. Facts found
are shown, never asked. Its output is the `idea`, `prior` (boards, term sheets, components),
`dead_ends` (same mechanism and market), `toolbox` hits, and `data` (`available` and any proxy
options).

The Toolbox and the data check are the Lab's backend, read from the Library. Until a workflow can
read those rows this template stays a draft (`needs: real-library`) and this script refuses to
guess.
"""

import sys

sys.stderr.write(
    "waits for a workflow read of the Library's Toolbox and data facts (needs: real-library)"
)
raise SystemExit(1)
