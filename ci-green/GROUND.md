# Ground: ci-green

Tip: bef6e80849161614e669b26952c88aeaf2acbed2
Fetch: ok 2026-11-14

Read at a detached checkout of the tip (`D:/QMX-worktrees/ground-ci-green`, removed after the check). Pyright's own output cannot be a fact here (facts run no `uv run`), so the error lists come from the deep run's logs and are kept as notes; every offending line is pinned by a `git grep` fact.

```fact G1
$ git rev-parse HEAD
bef6e80849161614e669b26952c88aeaf2acbed2
```

## Which run speaks for the tip

Deep run 43525887862 (`deep ci/github`, head `ce6df38d`) is the latest full deep run. PR #1 merged its tree as `773952ce`; the tip `bef6e808` changes only the two baseline files the retake wrote, so every product line that run typed is the same at the tip:

```fact G2
$ git diff --name-only ce6df38df54103974caec8f5d3a6b386ecd02023 HEAD
ci/baselines/flaky.txt
ci/baselines/known-reds.txt
```

Its red jobs, read from the job logs (`gh run view -R mubarakhimself-byte/QMX --job <id> --log`):

| Job | Blocks a green deep run at the tip? | Why |
|---|---|---|
| `lint` (job 132231451252) | yes | one failure only: `FAIL qmx-agents/packages/qmx-apps:0: [fmt-check] poe fmt-check failed (rc=1)`. Its types step printed `pyright: 68 findings, 0 not in the baseline, 0 blocking, 0 baseline rows gone`: the Linux typing errors in the five qmx-agents packages are all in the ratchet and block nothing. |
| `qmn-lane` (job 132231451255) | yes | step `uv run pyright --pythonplatform Linux --project pyproject.toml qmn/src qmn/deploy` printed `107 errors, 0 warnings, 0 informations`; this step has no baseline. Its other steps (ci_lane scans, isolated install, switch and rollback proof) passed: the log has one `##[error]`, on the pyright step. |
| `skylos` (job 132231451142) | not at the tip | one BLOCK, `tools/tests/test_mutation_workflow.py:41: [ai_defects:SKY-A104] ... public CLI flag removed in this diff (--all)`, raised by `--diff-base 3ae41ffc` on PR #1's own diff. A deep run scans only the diff since its merge-base with `engine/base` (`skylos_base` in `tools/ci/qci.py`), so at the tip or on `build/ci-green` that diff no longer holds PR #1. Not proven until the build's deep run. |
| `suite-linux 2, 6, 8`, `suite-windows 4, 5, 8` | not at the tip | their reds were retaken into `ci/baselines/known-reds.txt` by `bef6e808` (38 known reds, 1 flaky), and a listed red does not block. Not proven until the build's deep run. |

`deep-verdict` needs every deep job green:

```fact G3
$ git grep -n -e "pythonplatform" -e "needs: \[level, lint" -- .github/workflows/qmx-ci.yml
.github/workflows/qmx-ci.yml:380:        run: uv run pyright --pythonplatform Linux --project pyproject.toml qmn/src qmn/deploy
.github/workflows/qmx-ci.yml:428:    needs: [level, lint, vulture, skylos, suite-linux, suite-windows, mutmut, docker-node, qmn-lane]
.github/workflows/qmx-ci.yml:493:    needs: [level, lint, vulture, skylos, skylos-part, skylos-baseline, fail-at-parent, tests-linux, tests-windows, suite-linux, suite-windows, mutmut, mutmut-walk, smoke-linux, smoke-windows, docker-node, qmn-lane, deep-verdict, gate, release-verdict]
```

So the deep run at the tip has two blockers this program owns, the qmx-apps format check and the qmn Linux lane, and the 68 baselined rows that T-22 names but that block nothing today.

## The area

| Ask | Modules | Notes |
|---|---|---|
| S1, blocker 1 | `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` | format only |
| S1, blocker 2 | `qmn/src/qmn/app/grants.py` (43 errors), `qmn/src/qmn/host/_windows_deployment.py` (64 errors) | the whole qmn lane |
| S1, the ratchet rows | `qma-harness` 12, `qmx-apps` 5, `qmx-engine` 5, `qmx-home` 31, `qmx-host` 15 rows in `ci/baselines/pyright.txt` | 57 come from Windows-only code; 11 in qmx-host do not (Out of scope in `SCOPE.md`) |

### Blocker 1: the qmx-apps format check

The lint log shows `tests/test_shipped_apps.py:799:1` "File would be reformatted": the file ends in eight blank lines after its last statement (line 798). The fix is `ruff format` on that one file, nothing else.

```fact G5
$ python -c "t=open('qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py',encoding='utf-8').read();print(t.count(chr(10)), len(t)-len(t.rstrip(chr(10))))"
806 9
```

806 lines, 9 newline characters at the end where ruff wants 1. The held risk stack already fixes it on its own branch (`build/rc-35` ends the file with one newline; see In flight).

### Blocker 2: the qmn Linux lane (107 errors)

The lane types qmn as Linux on purpose; the root and qmx-agents workspace configs type as Windows, which is why the `lint` job's own pyright over `.` passes:

```fact G4
$ git grep -n "pythonPlatform" -- pyproject.toml qmx-agents/pyproject.toml qmx-agents/packages
pyproject.toml:308:pythonPlatform = "Windows"
qmx-agents/pyproject.toml:117:pythonPlatform = "Windows"
```

Errors per file, from the lane's log: `grants.py` 43, on lines 366 to 401, all inside `CredentialManager`; `_windows_deployment.py` 64, on lines 57 to 193, nearly all inside `_NativeReader.__init__` and its callers. By rule: 71 `reportUnknownMemberType`, 13 `reportAttributeAccessIssue`, 5 `reportUnknownVariableType`, the rest with the rule on a continuation line (`Argument type is unknown`, `Cannot access attribute ... for class "CredentialManager*"`).

**grants.py, the Windows credential store.** `CredentialManager.__init__` raises on any platform but Windows before it sets its attributes. Pyright on Linux treats everything after that `raise` as unreachable, so `target`, `encoding`, `_user` and `_api` are never declared, and every method that reads them fails ("Cannot access attribute target for class CredentialManager*"); `ctypes.get_last_error` does not exist on Linux at all.

```fact G6
$ git grep -n -e "WinDLL" -e "get_last_error" -e "sys.platform" -e "class CredentialManager" -e "def grant_store" -- qmn/src/qmn/app/grants.py
qmn/src/qmn/app/grants.py:348:class CredentialManager:
qmn/src/qmn/app/grants.py:357:        if sys.platform != "win32":
qmn/src/qmn/app/grants.py:362:        self._api = ctypes.WinDLL("advapi32", use_last_error=True)
qmn/src/qmn/app/grants.py:371:            error = ctypes.get_last_error()
qmn/src/qmn/app/grants.py:399:            error = ctypes.get_last_error()
qmn/src/qmn/app/grants.py:428:def grant_store(data: Path, tag: str) -> GrantStore:
qmn/src/qmn/app/grants.py:431:    if sys.platform == "win32":
```

`grant_store` (line 428) already picks `CredentialManager` only on Windows and `GrantFile` everywhere else. The fix kind: declare the attributes with types where pyright sees them on every platform (class-level annotations, or set them before the platform check), and reach `ctypes.WinDLL` and `ctypes.get_last_error` only under a `sys.platform == "win32"` condition pyright can read. The `OSError` on other platforms stays.

**_windows_deployment.py, the Windows deployment reader.** The whole module is Windows-only; its one importer imports it only on Windows, but the lane types every file under `qmn/src`:

```fact G7
$ git grep -n -e "WinDLL" -e "WinError" -e "get_last_error" -- qmn/src/qmn/host/_windows_deployment.py
qmn/src/qmn/host/_windows_deployment.py:57:        native = c.WinDLL("ntdll")
qmn/src/qmn/host/_windows_deployment.py:58:        kernel = c.WinDLL("kernel32", use_last_error=True)
qmn/src/qmn/host/_windows_deployment.py:99:            raise c.WinError(c.get_last_error())
qmn/src/qmn/host/_windows_deployment.py:104:            raise c.WinError(c.get_last_error())
qmn/src/qmn/host/_windows_deployment.py:112:            raise c.WinError(c.get_last_error())
qmn/src/qmn/host/_windows_deployment.py:140:            raise c.WinError(cast("int", self.error(result)))
qmn/src/qmn/host/_windows_deployment.py:159:                raise c.WinError(c.get_last_error())
```

```fact G8
$ git grep -n "_windows_deployment" -- qmn/src qmn/deploy
qmn/src/qmn/host/configured_runtime.py:52:    from qmn.host._windows_deployment import read_deployment
```

The fix kind: tell pyright the module is Windows-only (for example a module-level `sys.platform == "win32"` branch or assertion pyright reads; an assertion must not break any Linux import path, and today nothing imports the module on Linux). Which form is the anneal's and the brief's call.

### The ratchet rows: 68 in five qmx-agents packages

The per-package configs set no `pythonPlatform` (G4), so on the Linux runner they type as Linux; every row is in the baseline, so none blocks today.

```fact G9
$ python -c "import collections;c=collections.Counter(l.split('/')[2] for l in open('ci/baselines/pyright.txt',encoding='utf-8') if l.startswith('qmx-agents/'));print(sorted(c.items()), sum(c.values()))"
[('qma-harness', 12), ('qmx-apps', 5), ('qmx-engine', 5), ('qmx-home', 31), ('qmx-host', 15)] 68
```

```fact G10
$ python -c "import collections;c=collections.Counter(l.split('|')[0] for l in open('ci/baselines/pyright.txt',encoding='utf-8') if l.startswith('qmx-agents/'));print(chr(10).join(f'{v} {k}' for k,v in sorted(c.items())))"
5 qmx-agents/packages/qma-harness/src/qma/harness/procs.py
7 qmx-agents/packages/qma-harness/src/qma/launcher.py
4 qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py
1 qmx-agents/packages/qmx-apps/tests/test_data_reads.py
3 qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/script.py
2 qmx-agents/packages/qmx-engine/tests/test_zones.py
10 qmx-agents/packages/qmx-home/src/qmx_home/backup/restore.py
20 qmx-agents/packages/qmx-home/src/qmx_home/files.py
1 qmx-agents/packages/qmx-home/tests/test_backup_plan.py
1 qmx-agents/packages/qmx-host/src/qmx_host/app_logs.py
6 qmx-agents/packages/qmx-host/src/qmx_host/host.py
1 qmx-agents/packages/qmx-host/tests/test_app_logs.py
3 qmx-agents/packages/qmx-host/tests/test_heartbeats_loop.py
4 qmx-agents/packages/qmx-host/tests/test_vault_acl.py
```

Their Windows-only call sites in source code:

```fact G11
$ git grep -n -e "WinDLL" -e "WinError" -e "get_last_error" -e "CREATE_NO_WINDOW" -e "CREATE_NEW_PROCESS_GROUP" -e "open_osfhandle" -e "O_BINARY" -e "FormatError" -- qmx-agents/packages/qma-harness/src/qma/launcher.py qmx-agents/packages/qma-harness/src/qma/harness/procs.py qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/script.py qmx-agents/packages/qmx-home/src/qmx_home/backup/restore.py qmx-agents/packages/qmx-home/src/qmx_home/files.py
qmx-agents/packages/qma-harness/src/qma/harness/procs.py:274:            error = ctypes.WinError(
qmx-agents/packages/qma-harness/src/qma/harness/procs.py:275:                ctypes.get_last_error(), "watch the parent job; is another holder live?"
qmx-agents/packages/qma-harness/src/qma/launcher.py:130:    k: Any = ctypes.WinDLL("kernel32", use_last_error=True)
qmx-agents/packages/qma-harness/src/qma/launcher.py:163:        raise ctypes.WinError(ctypes.get_last_error(), call)
qmx-agents/packages/qma-harness/src/qma/launcher.py:327:        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
qmx-agents/packages/qma-harness/src/qma/launcher.py:374:        if ctypes.WinDLL("ntdll").NtResumeProcess(wintypes.HANDLE(handle)) != 0:
qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py:606:                    creationflags=subprocess.CREATE_NO_WINDOW | CREATE_SUSPENDED if job else 0,
qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/script.py:166:        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if windows else 0,
qmx-agents/packages/qmx-home/src/qmx_home/backup/restore.py:1017:    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
qmx-agents/packages/qmx-home/src/qmx_home/files.py:149:        error = ctypes.get_last_error()
qmx-agents/packages/qmx-home/src/qmx_home/files.py:150:        raise OSError(None, ctypes.FormatError(error).strip(), str(path), error)
qmx-agents/packages/qmx-home/src/qmx_home/files.py:153:        descriptor = msvcrt.open_osfhandle(handle, access_mode | os.O_BINARY)
qmx-agents/packages/qmx-home/src/qmx_home/files.py:166:    create = ctypes.WinDLL("kernel32", use_last_error=True).CreateFileW
qmx-agents/packages/qmx-home/src/qmx_home/files.py:184:    return cast("Callable[[int], int]", ctypes.WinDLL("kernel32").CloseHandle)
```

Patterns behind the rows, each a fix kind:
- **A condition pyright cannot read.** `script.py` stores the platform test in a variable (`windows = sys.platform == "win32"`, then `... if windows else 0`); `supervisor.py` guards `CREATE_NO_WINDOW` with `if job`, where `job` is set only on Windows, and its `Isolation` import is used only inside the Windows branch, so on Linux it reads as unused. Pyright narrows only a direct `sys.platform` (or `os.name`) comparison in the `if` or the conditional expression itself. Fix: write the comparison in place.
- **A helper with no guard of its own.** `launcher.py`, `procs.py`, `restore.py` and `files.py` call `ctypes.WinDLL`, `ctypes.WinError`, `ctypes.get_last_error`, `ctypes.FormatError`, `msvcrt.open_osfhandle` or `os.O_BINARY` in functions the callers reach only on Windows. Fix: a `sys.platform == "win32"` branch or early return pyright reads, or a small typed shim that holds the Windows calls.
- **Windows-only test helpers.** `_winapi.CreateJunction` in tests, `vault_acl._owner_of` (defined only in the Windows branch of a module-level `if sys.platform != "win32": ... else:`) read by `test_vault_acl.py`, and a `set()` typed by a platform conditional in `test_data_reads.py`. Fix: the same guards, or a typed empty value on the other branch.

```fact G12
$ git grep -n -e "windows = sys.platform" -e "Isolation" -- qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/script.py qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py
qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py:37:from qmx_apps.manifest import Breaker, Definition, Isolation, Trust, image_files, image_hash
qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py:594:            WindowsJob(f"Local\\qmx-install-{uuid.uuid4().hex}", Isolation())
qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/script.py:158:    windows = sys.platform == "win32"
```

```fact G13
$ git grep -n -e "CreateJunction" -- qmx-agents/packages/qmx-engine/tests/test_zones.py qmx-agents/packages/qmx-home/tests/test_backup_plan.py
qmx-agents/packages/qmx-engine/tests/test_zones.py:208:    _winapi.CreateJunction(str(outside), str(overlay.path / "escape"))
qmx-agents/packages/qmx-home/tests/test_backup_plan.py:209:    _winapi.CreateJunction(str(layout.backups), str(door))  # pyright: ignore[reportAttributeAccessIssue]
```

```fact G21
$ git grep -n -e "if sys.platform" -e "def _owner_of" -e "_advapi = ctypes.WinDLL" -- qmx-agents/packages/qmx-host/src/qmx_host/vault_acl.py
qmx-agents/packages/qmx-host/src/qmx_host/vault_acl.py:121:if sys.platform != "win32":
qmx-agents/packages/qmx-host/src/qmx_host/vault_acl.py:165:    _advapi = ctypes.WinDLL("advapi32", use_last_error=True)
qmx-agents/packages/qmx-host/src/qmx_host/vault_acl.py:336:    def _owner_of(path: Path) -> str:
```

```fact G14
$ git grep -n -e "_owner_of" -- qmx-agents/packages/qmx-host/tests/test_vault_acl.py qmx-agents/packages/qmx-host/src/qmx_host/vault_acl.py
qmx-agents/packages/qmx-host/src/qmx_host/vault_acl.py:334:        return _owner_of(path) in {_me(), SYSTEM, ADMINISTRATORS}
qmx-agents/packages/qmx-host/src/qmx_host/vault_acl.py:336:    def _owner_of(path: Path) -> str:
qmx-agents/packages/qmx-host/tests/test_vault_acl.py:137:    owner_of = qmx_host.vault_acl._owner_of  # pyright: ignore[reportPrivateUsage]
qmx-agents/packages/qmx-host/tests/test_vault_acl.py:142:    monkeypatch.setattr(qmx_host.vault_acl, "_owner_of", planter_owns_the_key)
```

```fact G23
$ git grep -n -e "WINDOWS = " -- qmx-agents/packages/qmx-apps/tests/test_data_reads.py
qmx-agents/packages/qmx-apps/tests/test_data_reads.py:70:WINDOWS = {"COMSPEC", "SYSTEMROOT", "WINDIR"} if sys.platform == "win32" else set()
```

The 11 rows that are not platform rows (out of scope) include this one:

```fact G22
$ git grep -n -e "profiles, funding = " -- qmx-agents/packages/qmx-host/src/qmx_host/host.py
qmx-agents/packages/qmx-host/src/qmx_host/host.py:2195:        profiles, funding = stated.get("costs") or {}, stated.get("funding") or {}
```

### No suppressions

The gate's guard counts a new suppression marker, or a pyright or ruff setting turned down in a pyproject, as baseline growth; so the fix is code, not markers. (`pythonPlatform` itself is not in the guard's list, which is why turning Linux typing off is named Out of scope in `SCOPE.md`.)

```fact G15
$ git grep -n -e "type-ignore" -e "pyright-ignore" -e "(\"tool\", \"pyright\")" -- tools/ci/guard.py
tools/ci/guard.py:11:- **Suppressions.** More type-ignore, pyright-ignore, noqa or skylos markers in Python files than
tools/ci/guard.py:42:    "type-ignore": re.compile("#" + r"\s*type:\s*ignore"),
tools/ci/guard.py:43:    "pyright-ignore": re.compile("#" + r"\s*pyright:\s*ignore"),
tools/ci/guard.py:59:    ("tool", "pyright"): ("exclude", "ignore"),
tools/ci/guard.py:199:    return _table(tomllib.loads(text), ("tool", "pyright"))
```

## Open items

Open items: complete. `gh pr list -R mubarakhimself-byte/QMX --state merged --limit 1000 --json number,title,body,files,mergedAt` lists one merged PR, #1 (`ci: GitHub Actions is the primary CI host`, merged 2026-11-13 as `773952ce`). Its `OPEN:` lines that touch the area:
- PR #1: "Fix the Windows-only code that fails Linux typing (qmx-agents lint and the qmn lane), or type-check on Windows too?" This program is the answer: fix it.
- PR #1: "Refresh `known-reds.txt` from the GitHub deep run ...". Done by `bef6e808`.
- PR #1: "The gate does not rerun by itself when the deep run turns green; you rerun the gate job." Touches the merge of this program, not its code.

Older PR bodies live on the old repo `MubarakHimself/QMX`, which returns 404 to everyone; on the new repo no commit since the move touched the area other than PR #1's merge and the baseline retake.

## In flight

Branches checked: every `origin/build/*`, `origin/slice/*` and `origin/ci/*`, with `git diff --name-only bef6e808...<branch> -- <the area>`.
- `origin/build/rc-04` to `origin/build/rc-35` (the held risk stack; it lands only at stops A, B, C on the coordinator's list) touch the area in `qmx-host` (`promote.py`, `lifecycle.py`, `practice_start.py`, `venue_records.py`, `host.py`, `app_logs.py`, `pyproject.toml`, and tests including `test_app_logs.py` and `test_heartbeats_loop.py`) and, at `rc-35`, `qmx-apps/tests/test_shipped_apps.py` (it already ends that file with one newline). None touches qmn's `grants.py` or `_windows_deployment.py`, nor the Windows-only files of the other four packages. Note for the anneal: a slice that edits `test_shipped_apps.py`, `host.py` or `app_logs.py` conflicts with the stack when it lands; the program's Windows-only files do not overlap it.
- `ci/c2` (open PR #2, CI tooling): no file in the area.

No ask depends on code that exists only on a branch.

## Doc drift

- `tracker/ci/ISSUES-2026-11-12.md` row T-22: says qmx-apps has "a format error and an unused import" in lint; code at `bef6e808` does: ruff lint passes, the format error is real (G5), and the unused import is a pyright row (`reportUnusedImport`, `Isolation`, used only in the Windows branch, G12) sitting in the baseline.
- T-22 and the lead's U19 brief: say lint is red on pyright for Windows-only code in five qmx-agents packages; the deep run's lint shows those 68 rows all baselined and non-blocking (`0 blocking`); lint is red on the format check alone.
- `tracker/shipping-method/FACTORY-DESIGN-2026-11-13.md` U19: says "A sweep program (`kind: sweep`)", the mechanical door; this program is kind `feature`, the contained door, because `grants.py` is credential code (fixed line 5).
- `docs/` was not read (`PROJECT-RULES.md`: never read `docs/`).

## Fixed lines touched

- **5. Keys are never read, printed or copied.** `qmn/src/qmn/app/grants.py` `CredentialManager` reads, writes and deletes the cTrader grant (the broker's access document) in Windows Credential Manager (G6). The fix changes only how the class is typed: no new read, no print, no copy, no new log line of the blob; the error messages keep naming the target, never the blob. Its Windows test uses a throwaway entry it deletes (G16), and must keep doing so.
- **5. Keys (the vault).** `qmx-host/src/qmx_host/vault_acl.py` guards the ACLs of the key vault; the row to fix is in its test (`test_vault_acl.py`, which stubs the owner of a planted fake key, G14). The fix is the test's typing of `_owner_of`; the vault code does not change.
- **His guarded parts (ruling, `PROJECT-RULES.md` "The parts he guards").** `qmx-engine` is the workflow engine and `qmx-apps/src/qmx_apps/supervisor.py` is the mini-app core: an engine change is a new template only, and a mini-app core change is a surgical fix with a one-line reason. The fixes there (`nodes/script.py` lines 158 and 166; `supervisor.py` lines 37 and 594 to 606) are a typing-only rewrite of a platform condition; the brief must say so with its one-line reason, or the challenge leaves those rows in the ratchet.
- Fixed lines 1 to 4 (money, promotion, exits, the kill switch), stdlib blocks, and the rulings on brakes, demo accounts and the unit journey: none. No file in the area submits, changes or cancels an order, promotes, lowers a kill level or touches the floor.

**The safety fact (Windows behaviour unchanged).** Every Windows path in the area stays as it is; only what the type checker sees on Linux changes. The Windows tests that drive this code run in the Windows suite shards and are neither known red nor flaky, so a behaviour change shows as a new red that blocks:

```fact G16
$ git grep -n -e "skipif" -e "CredentialManager(" -- qmn/tests/test_app_grants.py
qmn/tests/test_app_grants.py:253:@pytest.mark.skipif(sys.platform != "win32", reason="Credential Manager is Windows only")
qmn/tests/test_app_grants.py:256:    store = CredentialManager(target)
```

```fact G17
$ git grep -c "skipif(os.name != \"nt\"" -- qmn/tests/test_qmn_deployment_reader.py
qmn/tests/test_qmn_deployment_reader.py:5
```

```fact G18 exit=1
$ git grep -n -e "test_app_grants" -e "test_qmn_deployment_reader" -- ci/baselines/known-reds.txt ci/baselines/flaky.txt
```

## Removed

None. `tracker/REMOVED.md` (main checkout, header only; it is not on `engine/base`), `D:/QMX-worktrees/plans/_records/REMOVED.md` (header only) and `D:/QMX-worktrees/funnel-dry-run/pod-scalping/REMOVED.md` (no row names a file or package in the area).

## UI surface today

Contracts: none at bef6e808 (`contracts/` does not exist there):

```fact G20
$ git ls-tree --name-only HEAD contracts/
```

The area's Windows-only files define no route:

```fact G19 exit=1
$ git grep -c -e "rest=(" -e "@router." -- qmn/src/qmn/app/grants.py qmn/src/qmn/host/_windows_deployment.py qmx-agents/packages/qma-harness/src/qma/launcher.py qmx-agents/packages/qma-harness/src/qma/harness/procs.py qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/script.py qmx-agents/packages/qmx-home/src/qmx_home/backup/restore.py qmx-agents/packages/qmx-home/src/qmx_home/files.py
```

`D:/QMX-worktrees/plans/_records/BACKLOG.tsv` has no rows (header only), so no `ui-ask` row names the area. No operation, stream or open UI ask touches this area.
