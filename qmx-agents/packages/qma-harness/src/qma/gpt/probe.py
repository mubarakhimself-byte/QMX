"""Moved to `qmx_router.gpt.probe` (RTR0). DEL2 deletes this shim."""

import sys

from qmx_router.gpt import probe
from qmx_router.gpt.probe import *  # noqa: F403

# One module object under both paths, so a patch through either reaches the code.
sys.modules[__name__] = probe
