"""Moved to `qmx_router.relay` (RTR0). DEL2 deletes this shim."""

import sys

from qmx_router import relay
from qmx_router.relay import *  # noqa: F403

# One module object under both paths, so a patch through either reaches the code.
sys.modules[__name__] = relay
