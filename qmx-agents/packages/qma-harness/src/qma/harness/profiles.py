"""Moved to `qmx_router.profiles` (RTR0). DEL2 deletes this shim."""

import sys

from qmx_router import profiles
from qmx_router.profiles import *  # noqa: F403

# One module object under both paths, so a patch through either reaches the code.
sys.modules[__name__] = profiles
