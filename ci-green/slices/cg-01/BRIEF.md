# cg-01: Pin the Windows credential calls on Linux

Serves: S1 in `SCOPE.md`. Stop point: A. Lane: L1. Kind: pin. Depends on: none.
Chain: S1.a; A1; E1, E2, E3, E4, E6; none

## 1. Goal

The two Windows credential calls that the next slice has to retype, reading and deleting the node's grant entry, are pinned by tests that run on Linux as well as Windows. A later change that alters what they do turns a test red on either system.

## 2. Files it may touch

- `qmn/tests/test_app_grants_windows_calls.py` (new): the pins and their fake.

Nothing else. In particular, no file under `qmn/src` (that is cg-02) and nothing under `ci/baselines/`.

## 3. Facts about the code

The methods of `CredentialManager` and their line ranges. The deep run's mutation lane mutates whichever of these a change touches; cg-02 touches `read` and `delete`:

```fact F1
$ python -c "import ast;t=ast.parse(open('qmn/src/qmn/app/grants.py',encoding='utf-8').read());c=[n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='CredentialManager'][0];print([(f.name,f.lineno,f.end_lineno) for f in c.body if isinstance(f,ast.FunctionDef)])"
[('__init__', 356, 362), ('name', 365, 366), ('read', 368, 380), ('write', 382, 395), ('delete', 397, 401)]
```

What `read` and `delete` do today: the calls, the arguments (type 1, flags 0), the last-error read, the not-found code 1168, the exact refusal messages, the free and the decode:

```fact F2
$ git grep -n -e "def read(self)" -e "def delete(self)" -e "CredReadW" -e "CredFree" -e "CredDeleteW" -e "get_last_error" -e "_ERROR_NOT_FOUND" -e "refused to" -e "blob.decode" -- qmn/src/qmn/app/grants.py
qmn/src/qmn/app/grants.py:310:    def read(self) -> str | None: ...
qmn/src/qmn/app/grants.py:314:    def delete(self) -> None: ...
qmn/src/qmn/app/grants.py:327:    def read(self) -> str | None:
qmn/src/qmn/app/grants.py:344:    def delete(self) -> None:
qmn/src/qmn/app/grants.py:368:    def read(self) -> str | None:
qmn/src/qmn/app/grants.py:370:        if not self._api.CredReadW(ctypes.c_wchar_p(self.target), 1, 0, ctypes.byref(found)):
qmn/src/qmn/app/grants.py:371:            error = ctypes.get_last_error()
qmn/src/qmn/app/grants.py:372:            if error == _ERROR_NOT_FOUND:
qmn/src/qmn/app/grants.py:374:            raise OSError(f"Credential Manager refused to read {self.target} ({error})")
qmn/src/qmn/app/grants.py:379:            self._api.CredFree(found)
qmn/src/qmn/app/grants.py:380:        return blob.decode(self.encoding)
qmn/src/qmn/app/grants.py:395:            raise OSError(f"Credential Manager refused to write {self.target}")
qmn/src/qmn/app/grants.py:397:    def delete(self) -> None:
qmn/src/qmn/app/grants.py:398:        if not self._api.CredDeleteW(ctypes.c_wchar_p(self.target), 1, 0):
qmn/src/qmn/app/grants.py:399:            error = ctypes.get_last_error()
qmn/src/qmn/app/grants.py:400:            if error != _ERROR_NOT_FOUND:
qmn/src/qmn/app/grants.py:401:                raise OSError(f"Credential Manager refused to delete {self.target} ({error})")
qmn/src/qmn/app/grants.py:404:_ERROR_NOT_FOUND: Final = 1168
```

The Windows structure `read` reads the blob from, which a faithful fake builds for real:

```fact F3
$ git grep -n -e "class _Credential(" -e "CredentialBlob" -e "TargetName" -- qmn/src/qmn/app/grants.py
qmn/src/qmn/app/grants.py:377:            blob = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
qmn/src/qmn/app/grants.py:389:        credential.TargetName = self.target
qmn/src/qmn/app/grants.py:390:        credential.CredentialBlobSize = len(blob)
qmn/src/qmn/app/grants.py:391:        credential.CredentialBlob = ctypes.cast(buffer, ctypes.c_void_p)
qmn/src/qmn/app/grants.py:411:class _Credential(ctypes.Structure):
qmn/src/qmn/app/grants.py:415:        ("TargetName", ctypes.c_wchar_p),
qmn/src/qmn/app/grants.py:418:        ("CredentialBlobSize", ctypes.c_uint32),
qmn/src/qmn/app/grants.py:419:        ("CredentialBlob", ctypes.c_void_p),
```

The one existing test of this class runs only on Windows, against a throwaway `qmx-test-` entry:

```fact F4
$ git grep -n -e "skipif" -e "CredentialManager(" -e "qmx-test-" -- qmn/tests/test_app_grants.py
qmn/tests/test_app_grants.py:253:@pytest.mark.skipif(sys.platform != "win32", reason="Credential Manager is Windows only")
qmn/tests/test_app_grants.py:255:    target = f"qmx-test-{uuid.uuid4().hex}/node-abc-ctrader"
qmn/tests/test_app_grants.py:256:    store = CredentialManager(target)
```

qmn's tests run under xdist from the root config (`-n auto`), so a test must not depend on another test's state:

```fact F5
$ git grep -n -e "addopts" -e "testpaths" -- pyproject.toml
pyproject.toml:187:addopts = "-n auto --dist worksteal"
pyproject.toml:191:testpaths = ["tools/tests", "qml/tests", "qmb/tests", "qmn/tests"]
```

## 4. Read first

- `qmn/src/qmn/app/grants.py` lines 300 to 430: the `GrantStore` protocol, `GrantFile`, `CredentialManager`, `_ERROR_NOT_FOUND`, `_Credential`, `grant_store`.
- `qmn/tests/test_app_grants.py`: the house style of these tests, and `test_the_windows_store_writes_reads_and_deletes_one_throwaway_entry` (line 254), the Windows-only test you complement.
- `GROUND.md` in the program folder, "Found after the challenge": why these pins exist (the Linux mutation lane counts an untested mutant as a survivor).
- The Windows API contract you fake: `CredReadW`, `CredDeleteW` and `CredFree` in advapi32 return a nonzero BOOL on success and zero on failure, with the reason in the thread's last-error code (`ERROR_NOT_FOUND` = 1168, `ERROR_ACCESS_DENIED` = 5); `CredReadW` fills its out pointer with a `CREDENTIALW` the caller frees with `CredFree`.

## 5. What it must do

1. Add `qmn/tests/test_app_grants_windows_calls.py` with a recording fake of the three advapi32 calls that keeps the contract above, not a kinder one:
   - `CredReadW(target, type, flags, out)`: records `("CredReadW", target.value, type, flags)`; on a stored blob it builds a real `grants._Credential` with `CredentialBlob` pointing at a buffer holding the bytes and `CredentialBlobSize` set, writes its address through `out` (the `ctypes.byref` argument's `_obj`), keeps both alive, and returns 1; with no entry it sets its last-error code and returns 0.
   - `CredFree(pointer)`: records that it was called and with which pointer.
   - `CredDeleteW(target, type, flags)`: records the call; returns 1, or sets its last-error code and returns 0.
   - The last-error read: patch `ctypes.get_last_error` to return the fake's code, with `monkeypatch.setattr(ctypes, "get_last_error", ..., raising=False)` (ctypes has no such function off Windows). Patch the `ctypes` module itself, never a name inside `qmn.app.grants`, so the same test passes before and after cg-02.
2. Build the store without its Windows-only constructor: `object.__new__(CredentialManager)`, then set `target` (a `qmx-test-` name, for example `qmx-test-pin/node-abc-ctrader`), `encoding` (`"utf-8"`), `_user` and `_api` (the fake).
3. Pin today's behaviour, one test per line of E2 to E4, each asserting the real result and the recorded calls:
   - a stored blob `b'{"grant": 1}'` reads back as the text `{"grant": 1}`; the calls are exactly `CredReadW(target, 1, 0)` then one `CredFree` of the pointer `CredReadW` filled;
   - a missing entry (return 0, last error 1168) reads as `None`, with exactly one `CredReadW(target, 1, 0)` call and no `CredFree`;
   - another refusal (return 0, last error 5) raises `OSError` whose message is exactly `Credential Manager refused to read qmx-test-pin/node-abc-ctrader (5)`;
   - deleting a missing entry (return 0, last error 1168) returns without raising, with exactly one `CredDeleteW(target, 1, 0)` call;
   - deleting with last error 5 raises `OSError` whose message is exactly `Credential Manager refused to delete qmx-test-pin/node-abc-ctrader (5)`;
   - deleting an existing entry (return 1) returns without raising and records exactly one `CredDeleteW(target, 1, 0)`.
4. Each test asserts the subject's own result or the fake's recorded calls, so it fails when its subject returns None (the kit's probe checks this).

## 6. Tests that prove it

| Test | Door it calls | Fixture | Expected (literal) |
|---|---|---|---|
| `qmn/tests/test_app_grants_windows_calls.py::test_a_stored_grant_reads_back_whole_and_its_buffer_is_freed_once` | `CredentialManager.read` | fake holding `b'{"grant": 1}'` | `'{"grant": 1}'`; calls `[("CredReadW", "qmx-test-pin/node-abc-ctrader", 1, 0), ("CredFree", the pointer CredReadW filled)]` |
| `...::test_a_missing_entry_reads_as_nothing` | `CredentialManager.read` | return 0, last error 1168 | `None`; one `CredReadW` call, no `CredFree` |
| `...::test_another_refusal_to_read_names_the_target_and_the_code` | `CredentialManager.read` | return 0, last error 5 | `OSError("Credential Manager refused to read qmx-test-pin/node-abc-ctrader (5)")` |
| `...::test_deleting_a_missing_entry_is_quiet` | `CredentialManager.delete` | return 0, last error 1168 | returns `None`; one `CredDeleteW` call |
| `...::test_another_refusal_to_delete_names_the_target_and_the_code` | `CredentialManager.delete` | return 0, last error 5 | `OSError("Credential Manager refused to delete qmx-test-pin/node-abc-ctrader (5)")` |
| `...::test_deleting_an_existing_entry_asks_once` | `CredentialManager.delete` | return 1 | returns `None`; one `CredDeleteW` call |

The parent rule for this slice's kind:

- pin: each new test passes at the parent and at the head, and the probe shows it fails when its subject returns nothing.

Run them on Windows from `qmn/`: `uv run --no-sync python -m pytest -q -p no:cacheprovider tests/test_app_grants_windows_calls.py`. The planner ran a prototype of these pins on Windows: they passed at the parent tip and with cg-02's proven change applied. On Linux they run in CI's suite.

## 7. What it must not do

- Touch no file but the new test file: no source change (cg-02 owns `grants.py`), no change to `qmn/tests/test_app_grants.py`.
- Fixed line 5, keys are never read, printed or copied: never call the real Credential Manager from these tests, never use a `qmx/node-` target (the node's real entry), never print or log a blob. The fake holds made-up bytes only.
- No `skipif` on these tests: they must run on Linux, which is their reason to exist.
- No ignore marker (`# type: ignore`, `# pyright: ignore`, `# noqa`): the gate counts each as growth. Name the fake's methods as the API names them and, if ruff's naming rule objects, keep the fake's names behind a small mapping rather than a marker.
- Never rebuild: no removed rows touch these files.

## 7a. Edge-case scenarios

- E1 Fixed line 5 holds while pinning: no real entry is touched and no blob is printed (test: every test in the file uses the fake and a `qmx-test-` target; covered by fact SAFETY).
- E2 A missing entry reads as nothing and deletes quietly (test: `test_a_missing_entry_reads_as_nothing`, `test_deleting_a_missing_entry_is_quiet`).
- E3 Another refusal raises an OSError naming the target and the code (test: `test_another_refusal_to_read_names_the_target_and_the_code`, `test_another_refusal_to_delete_names_the_target_and_the_code`).
- E4 A successful read returns the decoded blob, asks for type 1 with flags 0 and frees once (test: `test_a_stored_grant_reads_back_whole_and_its_buffer_is_freed_once`).
- E6 The pins leave no untested mutant in `read` or `delete` on Linux (test: all six tests above; the deep run's mutation lane after cg-02 is the proof).

## 8. Safety fact

No qmn test names the node's real Credential Manager entry, before or after this slice.

```fact SAFETY exit=1
$ git grep -n "qmx/node-" -- qmn/tests
```

## 9. Done when

- [ ] Every item in 5 has a test from 6 that passes at the head.
- [ ] The safety fact gives the same output at the head.
- [ ] The six tests pass at the parent and at the head, on Windows locally; none is skipped.
- [ ] `uv run --no-sync ruff check .` and `uv run --no-sync ruff format --check .` from `qmn/` are clean.

Operations: none, because the slice adds tests only; no running process, log or schedule changes.

## 10. Size guide

S: one new test file of about 100 to 150 lines.

## 11. Merge request

- Title: cg-01: Pin the Windows credential calls on Linux
- In plain words: The part of the trading node that keeps the broker grant in Windows' credential store now has tests that also run on Linux, so the type fix that comes next can be checked to change nothing.
- TRACE: cg-01 -> S1.a -> S1
- Door: two-way, because it adds tests only and changes no product code. Blast radius: none outside the new file; it never touches a real credential entry, proved by fact SAFETY.
- DOC: none
- OPEN known at planning: the deep run's mutation lane is the final proof that these pins leave no untested mutant in `read` and `delete` | CI, after cg-02 | stop A review
- API: none

Skills: tdd, how. Principles: principle-test-behavior-not-implementation, principle-prove-it-works.
