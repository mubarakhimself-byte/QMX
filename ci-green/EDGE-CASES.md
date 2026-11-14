# Edge cases: ci-green

- **E1** (S1.a, S1.b, S1.d) Fixed line 5 (keys are never read, printed or copied) still holds when the credential store is pinned and retyped. Must hold: no test or code reads, prints, logs or copies a real Credential Manager entry; the pins use a fake and a `qmx-test-` target, never `qmx/node-`; error messages keep naming the target and the code, never the blob.
- **E2** (S1.a) Reading or deleting an entry that does not exist (the call returns 0 and the last error is 1168, ERROR_NOT_FOUND). Must hold: `read()` returns None; `delete()` returns without raising.
- **E3** (S1.a) Windows refuses for any other reason (for example 5, access denied). Must hold: `read()` raises `OSError("Credential Manager refused to read <target> (5)")` and `delete()` raises `OSError("Credential Manager refused to delete <target> (5)")`, exact text.
- **E4** (S1.a) A read that succeeds. Must hold: it returns the blob decoded with the store's encoding, after asking for type 1 (generic) with flags 0, and frees Windows' buffer exactly once.
- **E5** (S1.b, S1.d) The deployment reader gains a Windows-only import guard. Must hold: nothing off Windows imports it (its one importer imports it only when `os.name == "nt"`, and its tests import it only inside Windows-only tests), and the Windows reader tests pass unchanged.
- **E6** (S1.b) The deep run's mutation lane looks at every function the fix touches. Must hold: the touched functions are exactly `CredentialManager.read` and `CredentialManager.delete`, and the S1.a pins leave no surviving or untested mutant in them on Linux.
- **E7** (S1.b, S1.c) No check is switched off or silenced. Must hold: no new `# type: ignore`, `# pyright: ignore` or `# noqa`, no pyright or ruff setting changed, no `pythonPlatform` added, and `qmn-lane` still types qmn for Linux.
- **E8** (S1.c) The format fix. Must hold: the only change to `test_shipped_apps.py` removes the eight blank lines at its end; no test or pin in it moves.
