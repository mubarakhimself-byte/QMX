"""Moved to `qmx_router.gpt.siwc` (RTR0). DEL2 deletes this shim."""

import sys

from qmx_router.gpt import siwc
from qmx_router.gpt.siwc import *  # noqa: F403

# One module object under both paths, so a patch through either reaches the code.
sys.modules[__name__] = siwc
