# cg-02: Type the Windows-only qmn code for Linux and fix the qmx-apps format

Serves: S1 in `SCOPE.md`. Stop point: A. Lane: L1. Kind: refactor. Depends on: cg-01.
Chain: S1.b, S1.c, S1.d; A2, A3, A4; E1, E5, E6, E7, E8; none

## 1. Goal

The two things that keep CI's deep run red are gone: the qmn Linux type check finds 0 errors (it finds 107 today) and the qmx-apps format check passes, with nothing on Windows behaving differently and no check turned down.

## 2. Files it may touch

- `qmn/src/qmn/app/grants.py`: typing of `CredentialManager` (class-level annotations, the `Any` import, the two last-error reads).
- `qmn/src/qmn/host/_windows_deployment.py`: `import sys` and a module-level Windows-only guard.
- `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`: the eight blank lines at its end go, nothing else.

No forced files: `ci/baselines/` is never a builder's file (the kit's merge step prunes it), and nothing here moves a pin, a count or a lock.

## 3. Facts about the code

The format failure: the file ends in 9 newline characters where ruff wants 1 (806 newlines in all):

```fact F1
$ python -c "t=open('qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py',encoding='utf-8').read();print(t.count(chr(10)), len(t)-len(t.rstrip(chr(10))))"
806 9
```

The credential store as it is: the platform check that raises before the attributes are set (so pyright on Linux never sees them), the Windows DLL load, and the two last-error reads that do not exist on Linux:

```fact F2
$ git grep -n -e "WinDLL" -e "get_last_error" -e "sys.platform" -e "class CredentialManager" -e "def __init__(self, target" -e "^from typing import" -- qmn/src/qmn/app/grants.py
qmn/src/qmn/app/grants.py:37:from typing import Final, Protocol, TypeAlias, cast
qmn/src/qmn/app/grants.py:348:class CredentialManager:
qmn/src/qmn/app/grants.py:356:    def __init__(self, target: str, *, encoding: str = "utf-8") -> None:
qmn/src/qmn/app/grants.py:357:        if sys.platform != "win32":
qmn/src/qmn/app/grants.py:362:        self._api = ctypes.WinDLL("advapi32", use_last_error=True)
qmn/src/qmn/app/grants.py:371:            error = ctypes.get_last_error()
qmn/src/qmn/app/grants.py:399:            error = ctypes.get_last_error()
qmn/src/qmn/app/grants.py:431:    if sys.platform == "win32":
```

The methods and their line ranges; only `read` and `delete` may change inside a function:

```fact F3
$ python -c "import ast;t=ast.parse(open('qmn/src/qmn/app/grants.py',encoding='utf-8').read());c=[n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='CredentialManager'][0];print([(f.name,f.lineno,f.end_lineno) for f in c.body if isinstance(f,ast.FunctionDef)])"
[('__init__', 356, 362), ('name', 365, 366), ('read', 368, 380), ('write', 382, 395), ('delete', 397, 401)]
```

The deployment reader's imports and its Windows DLL loads; nothing imports it off Windows (its importer guards on `os.name == "nt"`, its tests import it inside Windows-only tests):

```fact F4
$ git grep -n -e "^import" -e "^from" -e "WinDLL" -- qmn/src/qmn/host/_windows_deployment.py
qmn/src/qmn/host/_windows_deployment.py:8:from __future__ import annotations
qmn/src/qmn/host/_windows_deployment.py:10:import ctypes as c
qmn/src/qmn/host/_windows_deployment.py:11:from contextlib import ExitStack
qmn/src/qmn/host/_windows_deployment.py:12:from pathlib import Path
qmn/src/qmn/host/_windows_deployment.py:13:from typing import cast
qmn/src/qmn/host/_windows_deployment.py:57:        native = c.WinDLL("ntdll")
qmn/src/qmn/host/_windows_deployment.py:58:        kernel = c.WinDLL("kernel32", use_last_error=True)
```

```fact F5
$ git grep -n "_windows_deployment" -- qmn/src qmn/deploy qmn/tests
qmn/src/qmn/host/configured_runtime.py:52:    from qmn.host._windows_deployment import read_deployment
qmn/tests/test_qmn_deployment_reader.py:144:    from qmn.host import _windows_deployment as native
qmn/tests/test_qmn_deployment_reader.py:185:    from qmn.host import _windows_deployment as native
qmn/tests/test_qmn_deployment_reader.py:238:    from qmn.host import _windows_deployment as native
qmn/tests/test_qmn_deployment_reader.py:263:    from qmn.host import _windows_deployment as native
```

The Linux check this slice must satisfy, and the workspace configs that type as Windows and must stay as they are:

```fact F6
$ git grep -n -e "pythonplatform" -- .github/workflows/qmx-ci.yml
.github/workflows/qmx-ci.yml:380:        run: uv run pyright --pythonplatform Linux --project pyproject.toml qmn/src qmn/deploy
```

```fact F7
$ git grep -n "pythonPlatform" -- pyproject.toml qmx-agents/pyproject.toml qmx-agents/packages
pyproject.toml:308:pythonPlatform = "Windows"
qmx-agents/pyproject.toml:117:pythonPlatform = "Windows"
```

The ignore markers these three files carry today; the count must not grow:

```fact F8
$ git grep -c -e "type: ignore" -e "pyright: ignore" -e "noqa" -- qmn/src/qmn/app/grants.py qmn/src/qmn/host/_windows_deployment.py qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py
qmn/src/qmn/app/grants.py:3
qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py:2
```

## 4. Read first

- `qmn/src/qmn/app/grants.py` lines 345 to 430 (`CredentialManager`, `_ERROR_NOT_FOUND`, `_Credential`, `grant_store`).
- `qmn/src/qmn/host/_windows_deployment.py` lines 1 to 60 (imports, structures, `_NativeReader.__init__`) and `qmn/src/qmn/host/configured_runtime.py` lines 51 to 52 and 921 to 931 (the only importer, Windows-only).
- `qmn/tests/test_app_grants_windows_calls.py` (from cg-01): the pins this slice must keep green. They patch `ctypes.get_last_error` on the `ctypes` module, so the last-error read must still look that name up on `ctypes` at call time.
- `GROUND.md` in the program folder: "Blocker 2" and "Found after the challenge" (the mutation lane, the measured fix).

## 5. What it must do

1. `_windows_deployment.py`: add `import sys` with the other imports, and right after the imports a module-level `if sys.platform != "win32": raise ImportError("qmn.host._windows_deployment reads deployments on Windows only")`. Change no line inside any function or class. Pyright on Linux then reads the rest as Windows code: 64 errors to 0.
2. `grants.py`, class body of `CredentialManager`, between the docstring and `__init__`: annotate `target: str`, `encoding: str`, `_user: str`, `_api: Any`, and add `Any` to the existing `from typing import ...` line. 43 errors to 6.
3. `grants.py`, the two lines `error = ctypes.get_last_error()` in `read` and `delete`: write them so pyright knows the call on every platform and it still resolves `ctypes.get_last_error` when it runs. The proven form: a module-level `class _WindowsErrors(Protocol)` with one annotated attribute, `get_last_error: Callable[[], int]` (an attribute, not a method, so no new function appears), placed before `CredentialManager`, and `error = cast("_WindowsErrors", ctypes).get_last_error()` on both lines. 6 errors to 0. Change no other line inside a function.
4. `test_shipped_apps.py`: run `ruff format --config pyproject.toml tests/test_shipped_apps.py` from the qmx-apps folder (or delete the eight trailing blank lines by hand); the diff is those blank lines only.
5. Prove it: from `qmn/`, `uv run --no-sync pyright --pythonplatform Linux --project ../pyproject.toml src deploy` prints `0 errors`, and the same with `--pythonplatform Windows` prints `0 errors`. The planner applied exactly steps 1 to 3 at the parent tip: both runs printed 0 errors, ruff check and format passed, and the touched functions were `CredentialManager.read` and `CredentialManager.delete` only.

## 6. Tests that prove it

| Test | Door it calls | Fixture | Expected (literal) |
|---|---|---|---|
| `qmn/tests/test_app_grants_windows_calls.py` (all six, from cg-01) | `CredentialManager.read`, `.delete` | the recording fake | unchanged: all pass at the head |
| `qmn/tests/test_app_grants.py` (all, including `test_the_windows_store_writes_reads_and_deletes_one_throwaway_entry` on Windows) | `grant_store`, `GrantFile`, `CredentialManager` | as today | unchanged: all pass at the head |
| `qmn/tests/test_qmn_deployment_reader.py` (all; five run only on Windows) | `read_deployment` | as today | unchanged: all pass at the head |
| `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` | the shipped apps | as today | unchanged: all pass at the head |
| Linux type check (command in 5.5) | pyright | `qmn/src`, `qmn/deploy` | `0 errors, 0 warnings, 0 informations` |

The parent rule for this slice's kind:

- refactor: the pin slices it depends on stay green, and no new mutant survives in a changed function.

This slice adds no test.

## 7. What it must not do

- No behaviour change on any platform: `grant_store` still picks `CredentialManager` on Windows and `GrantFile` elsewhere, and `CredentialManager` still raises `OSError("Credential Manager is a Windows store")` off Windows.
- Fixed line 5, keys are never read, printed or copied: no new read, print, log or copy of a credential blob; the error messages stay exactly as they are, naming the target and the code.
- Change no line inside any function except the two last-error lines in `read` and `delete`, and add no new function or method in these files: the deep run mutates every touched function on Linux, and only those two are pinned.
- No check switched off or silenced: no new `# type: ignore`, `# pyright: ignore` or `# noqa`; no change to any `pyproject.toml`, to `pythonPlatform`, or to `.github/workflows/qmx-ci.yml`; nothing under `ci/baselines/`.
- Keep the names the Skylos baseline already keys on (`read_deployment`, `_NativeReader`, `CredentialManager`): renaming one turns a known row into a new finding.
- Never rebuild: no removed rows touch these files.

## 7a. Edge-case scenarios

- E1 Fixed line 5 holds through the retyping (test: the cg-01 pins and `test_the_windows_store_writes_reads_and_deletes_one_throwaway_entry` pass unchanged; covered by fact SAFETY).
- E5 The reader's import guard changes nothing a Linux node runs (test: `qmn/tests/test_qmn_deployment_reader.py` passes; covered by fact F5).
- E6 The touched functions are exactly `read` and `delete`, and the pins leave no surviving mutant in them (test: the cg-01 pins; the deep run's mutation lane on the build branch).
- E7 No check is turned down (test: the gate's guard on the pull request; covered by fact F8).
- E8 The format fix removes only the trailing blank lines (test: `test_shipped_apps.py` passes; covered by fact F1).

## 8. Safety fact

The choice of grant store, Windows Credential Manager on Windows and the owner-only file elsewhere, is the same before and after this slice.

```fact SAFETY
$ python -c "import ast;s=open('qmn/src/qmn/app/grants.py',encoding='utf-8').read();f=[n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='grant_store'][0];print(ast.get_source_segment(s,f))"
def grant_store(data: Path, tag: str) -> GrantStore:
    """This machine's grant store for the node ``tag``: Credential Manager on Windows, the
    volume's owner-only ``data/grants/`` file elsewhere."""
    if sys.platform == "win32":
        return CredentialManager(f"qmx/node-{tag}-ctrader")
    return GrantFile(data / "grants" / "ctrader.json")
```

## 9. Done when

- [ ] Every item in 5 has a test from 6 that passes at the head.
- [ ] The safety fact gives the same output at the head.
- [ ] The Linux and Windows type checks in 5.5 print 0 errors.
- [ ] `ruff check` and `ruff format --check` pass for qmn (from `qmn/`) and qmx-apps (its `fmt-check` task's arguments).
- [ ] `git diff` touches only the three files in 2, and inside functions only the two last-error lines.

Operations: none, because the slice changes typing, an import guard and blank lines; no running process, log or schedule changes. The deep run on the build branch (lint, qmn-lane, mutmut, deep-verdict) is watched at stop A (test: the deep run's `deep-verdict` job).

## 10. Size guide

S: about 20 changed lines in two source files, plus 8 deleted blank lines.

## 11. Merge request

- Title: cg-02: Type the Windows-only qmn code for Linux and fix the qmx-apps format
- In plain words: CI can pass again: the trading node's Windows-only code now tells the Linux type check that it only runs on Windows, and one test file loses eight extra blank lines. Nothing changes in how QMX behaves.
- TRACE: cg-02 -> S1.b, S1.c, S1.d -> S1
- Door: two-way, because it changes types, an import guard on a Windows-only module and blank lines, and reverts cleanly. Blast radius: the credential store and the deployment reader on Windows, held by the cg-01 pins and the Windows tests, and the grant store choice, proved by fact SAFETY.
- DOC: none
- OPEN known at planning: the `lint` and `qmn-lane` jobs and the mutation lane are proven only by the build branch's deep run | CI | stop A review; the held risk stack (`build/rc-35`) also edits `test_shipped_apps.py` and will meet this change when it lands | the coordinator | stop A merge
- API: none

Skills: how, blast-radius. Principles: principle-subtract-before-you-add, principle-type-system-discipline, principle-prove-it-works.
