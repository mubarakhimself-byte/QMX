# Architecture: ci-green (element index)

Light depth: the element index alone, with Operations and Interfaces. The plan adds no module.

- **A1** (S1.a) Linux-runnable pins of `CredentialManager.read` and `CredentialManager.delete`, in a new test file `qmn/tests/test_app_grants_windows_calls.py`: a recording fake of advapi32's `CredReadW`, `CredFree` and `CredDeleteW` that keeps the Windows contract (nonzero for success, zero for failure with the reason in the last-error code, a real `_Credential` structure behind the returned pointer), and the last-error read patched to the fake's code (`ctypes.get_last_error`, added with `raising=False` where ctypes has none). The store is built without its Windows-only constructor (`object.__new__`, then its four attributes). Who: the cg-01 builder. Covers: E1, E2, E3, E4, E6. Spine: none.
- **A2** (S1.b, S1.d) `qmn/src/qmn/app/grants.py` typed for every platform: class-level annotations on `CredentialManager` (`target: str`, `encoding: str`, `_user: str`, `_api: Any`, with `Any` added to the `typing` import), and the two last-error reads written so pyright knows the call on any platform while it still resolves `ctypes.get_last_error` at call time (proven form: a module-level `Protocol` holding `get_last_error: Callable[[], int]` and `cast("<that protocol>", ctypes).get_last_error()`; no new function). Who: the cg-02 builder. Covers: E1, E6, E7. Spine: none.
- **A3** (S1.b, S1.d) `qmn/src/qmn/host/_windows_deployment.py` declared Windows-only: `import sys` and a module-level `if sys.platform != "win32": raise ImportError(...)` after the imports, so pyright reads the rest as Windows code; no function changes. Who: the cg-02 builder. Covers: E5, E7. Spine: none.
- **A4** (S1.c) `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` formatted by ruff (the eight trailing blank lines go). Who: the cg-02 builder. Covers: E8, E7. Spine: none.
- **A5** (S2.a, S2.b, S2.c) Platform conditions pyright reads, in place, in the later packages' Windows-only code and tests, outside his guarded parts; the kit's merge prune drops the gone rows. Who: stop B's builders, briefed after stop A merges. Covers: none yet. Spine: none.

## Operations

- **Logging:** none added. The credential store's error messages stay as they are, naming the target and the code, never the blob (E1).
- **Observability:** the deep run's job results are the signal: `lint`, `qmn-lane`, `mutmut` and `deep-verdict` in `qmx-ci.yml`.
- **Monitoring:** the gate refuses any pull request into `engine/base` without a green deep run of its head; the ratchet blocks any new type row, and the nightly walk keeps running.
- **Self-recovery:** none needed: no running process changes. A red deep run is rerun once; a red from outside the two blockers goes to the lead as a budget call (`CHALLENGE.md` call-outs).
- **Backend operations:** none. No route, store, schedule or deployment step changes; Windows behaviour is unchanged (S1.d).

## Interfaces

Interfaces: none, because the program changes only type annotations, an import guard, a test file and its formatting; no operation, route or stream is added, changed or removed (`GROUND.md`, UI surface today).
