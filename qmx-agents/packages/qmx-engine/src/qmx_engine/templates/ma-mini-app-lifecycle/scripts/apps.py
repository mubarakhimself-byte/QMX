"""The pre-check read (card D7 pre-check, card D8 step 9's blast radius): the installed apps and
templates that already do what he asks, whether the Lab objects the app would read exist, and for
a named app its lifecycle state, its versions and its consumers (the apps and workflows that read
its outputs). It echoes the request and its `build` flag.

Its output is `request`, `build`, `similar`, `data_reads_missing`, and for a named app `app`
(`lifecycle`, `versions`) and `consumers` (each `id`, `kind`, `rewired`). The apps door is the
host's (`apps.list`, `apps.consumers`). Until it exists this template stays a draft
(`needs: sandbox, app-op`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the host's apps door: list and consumers (needs: sandbox, app-op)")
raise SystemExit(1)
