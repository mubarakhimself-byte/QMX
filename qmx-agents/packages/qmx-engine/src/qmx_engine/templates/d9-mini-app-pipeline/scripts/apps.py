"""The pre-check read (card D9 pre-check): both apps exist and are enabled, the producer's
`provides` schema for the output it emits with its version, the consumer's `feeds` schema for the
input it accepts with its version, and a recorded producer artifact for the contract test.

Its output is `producer` and `consumer` (each `id`, `enabled`, `version`), `provides` and `feeds`
(JSON schemas) and `fixture` (a recorded artifact). The apps door is the host's (`apps.get`,
`pipelines.validate_schemas`). Until it exists this template stays a draft (`needs: app-op`) and
this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the host's apps and pipelines doors (needs: app-op)")
raise SystemExit(1)
