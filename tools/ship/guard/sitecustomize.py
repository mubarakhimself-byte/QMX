"""Refuse direct Windows Credential Manager calls in any Python process the timed wrapper starts.

The wrapper puts this folder first on PYTHONPATH, so Python imports it at start. The fake keyring
backend covers the keyring library; this covers code that reaches Cred* through ctypes.
A process started with `python -I` skips it.
"""

import sys


def _refuse_credential_calls(event, args):
    if event.startswith("ctypes.dlsym") and len(args) >= 2 and str(args[1]).startswith("Cred"):
        raise RuntimeError(f"ship guard: {args[1]} refused, tests may not reach the real Credential Manager")


sys.addaudithook(_refuse_credential_calls)
