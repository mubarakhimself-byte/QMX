"""Runs `qmx app check` on the built folder in the sandbox (card D7 steps 5 and 7, card D8 step 6):
manifest, secrets and paths, build and bundle size, unit tests, contract tests, sandbox run, load
check, agent eval, the render check (each widget with sample, empty, error and loading props,
failing on console errors or failed requests, fitting its slot, with screenshots), and the shadow
line for apps that run on a schedule.

Its output is `lines`: each line's `n`, `name`, `status` (`pass`, `fail` or `needs-human`) and
`detail`, plus `screenshots`. The check is the host's (`apps.check`, `apps.render_check`). Until it
and the sandbox exist this template stays a draft (`needs: sandbox, app-op`) and this script
refuses to guess.
"""

import sys

sys.stderr.write("waits for the host's app check and the Lab sandbox (needs: sandbox, app-op)")
raise SystemExit(1)
