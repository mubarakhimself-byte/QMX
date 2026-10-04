# Independent offline Windows storage correctness review

**ACCEPT the bounded two-file containment repair.** It closes the early directory-movement issue B1 identified in `qmb-runtime-independent-review.md`, while preserving successful local publication/read, no-clobber behavior, flush refusals and handle cleanup. No concrete correctness blocker was found in this correction. This is acceptance of the local storage increment, not platform, release, physical power-loss or Study-ingress acceptance.

## Exact reviewed source

Worktree: `C:/Users/Mubarak/Documents/Codex/2026-10-04/task-12/qmb-containment-repair`; branch `backend/qmb-containment-repair-20261004`; base `8d76250280b4566cb4fe61a3528f3d7eccc4de5c`. Review began with exactly two modified files. The integrator then committed their identical reviewed bytes as **`0ccfa7ff9522789f547349c8541481d6903e7611`**; final HEAD was independently verified at that commit with clean status. Acceptance is against this exact committed repair, with final SHA-256 values:

| File | SHA-256 |
|---|---|
| `qmb/src/qmb/host/_windows_research.py` | `C23208132E5694274E0D5C0591DC6E4D0925F0D02D2E05C9C5B5450B3EDCB28C` |
| `qmb/tests/test_research_windows.py` | `C2A849A2DDCF775738B9E462F22158B60D3765D2DDDD8108EE56ADE418F7DB37` |

Runtime hash was stable throughout review and matches the integrator's native/store gate. The test file changed during review from `23BF9E6D9DCAB4B599B9A824E26A4A61AA75EFFB390FA5DE32CF4E181C20D048` to the final hash above. The integrator confirmed, and final diff inspection agrees, that its only semantic-neutral adjustment introduced `seam = "_open"`, then reused that variable for `getattr` and `monkeypatch.setattr` in the component-walk test to satisfy B009. Formatting also changed earlier. No control, assertion or runtime behavior changed. A broad rerun was unnecessary for this test-name indirection.

All Git calls used per-command safe.directory for the exact worktree. Neither source checkout was edited by this reviewer. Only separate workspace fixture/evidence/review files were created. No dependencies, ACLs, protection settings, accounts, credentials or network services were changed or accessed.

## Correctness of the bounded repair

Directory DesiredAccess changes from FILE_READ_ATTRIBUTES (0x80) to FILE_READ_ATTRIBUTES | FILE_LIST_DIRECTORY (0x81). The latter participates in the sharing checks that were absent in the original early-movement gap. Directory sharing includes read and write, while DELETE remains unshared. Sharing writes permits NTFS's target-directory open during actual native publication, resolving the earlier 0x81-only diagnostic's WinError32. It does not grant a directory data-write right to this adapter or change its file-handle modes.

The adapter still acquires and retains each ancestor, verifies ordinary directory/file type and rejects preexisting reparse components, performs relative child opens, and holds all anchors until completion. Root and parent moves now fail both before leaf acquisition and during component walking. The new tests perform those moves from another thread and demonstrate that the same move succeeds after handle release, distinguishing active pinning from an unrelated permission denial.

Leaf modes remain unchanged: readers deny concurrent writes/deletes; temporaries and existing-blob comparisons retain their existing writable exclusive modes. Native rename does not replace an existing destination. Concurrent equal/conflicting publishers can refuse on sharing conflicts, and every acknowledged publisher observes its own winning payload; a loser does not clobber it. Existing or race-winner success requires equal bytes and a successful flush under a held writable leaf handle.

Temporary file bytes are flushed before native publication; published bytes are flushed and checked against the held native file identity and actual payload before acknowledgement. Newly created directories/files retain the existing write-through options. A pre-publication fault deletes only the owned temporary by handle. A post-publication fault leaves the final blob and refuses success. Existing-blob flush failure also refuses. CRT ownership transfer, descriptor closure and reverse ancestor-handle closure are unchanged. The correction does not establish a new hardware-cache or physical power-cut guarantee.

Directory WRITE sharing must be described accurately: it blocks deletion/movement via active read-access sharing checks but does **not** deny all directory mutations. Therefore update the held series' older native handoff/review/ledger draft claim that directory anchors deny write sharing. This is a required documentation reconciliation, not another runtime defect found here.

## Independent consistency control and evidence

The independent run used the integrator's source-first `run-qmb-containment-check.ps1`, existing `evidence/combined-runtime-env/Scripts/python.exe`, bytecode disabled, and new workspace-only cache/temp/evidence directories. Source provenance resolves to this exact repair worktree. The ordinary host token is independently recorded as `desktop-lagn1js\\mubarak` in `evidence/qmb-native-independent/containment-repair-normal-token.txt`. Restricted-token LIST denial at an ancestor remains a legitimate refusal; no metadata-only fallback or ACL adjustment is proposed.

**23 passed in 5.99 seconds, exit 0**: all 21 native Windows tests plus two additional independent disposable directory consistency checks. Evidence:

`evidence/qmb-containment-independent-directory-consistency-f869f7c1632a4cefacf28cde105f0427/{command.json,source-provenance.txt,pytest.txt,pytest.exit}`.

The added check is separate from the owned source/tests, at `evidence/qmb-native-independent/test_reparse_consistency.py`. Its first case turns a disposable empty directory into a local NTFS junction before admission and confirms UnsafePath refusal with an untouched target. This positive setup control demonstrates that the junction operation is actually supported on this host.

Its second case changes the same kind of disposable directory after anchor validation but before the first leaf open. With directory write sharing, this change actually succeeds. The subsequent native write refuses with WinError1921 (`The name of the file cannot be resolved by the system`); it does not acknowledge publication and the outside target remains empty. Thus the actual observed protection is a fail-closed relative open after that directory change, not a claim that WRITE sharing prevents the change itself.

A narrow observation-only rerun of those same two checks, using pytest `-s`, recorded the exact successful directory change and subsequent write refusal: **2 passed in 2.62 seconds, exit 0**. Evidence:

`evidence/qmb-containment-independent-directory-observations-e3dacd79270742309805b86c6f90d57a/{command.json,source-provenance.txt,pytest.txt,pytest.exit}`.

No additional probes are needed for this review. The observations establish this host's bounded ordinary-directory/junction behavior, not universal reparse-tag or hardlink guarantees.

Reproduce the independent bounded suite from task-12 as the ordinary host user:

```powershell
.\run-qmb-containment-check.ps1 -Label independent-directory-consistency -Targets @('C:\Users\Mubarak\Documents\Codex\2026-10-04\task-12\evidence\qmb-native-independent\test_reparse_consistency.py','qmb/tests/test_research_windows.py')
```

Integrator evidence was also read directly: `evidence/qmb-containment-native-store-cd91f05e94bb4161a26f2b6540445284` records **31 passed, 5 existing POSIX-only skips in 4.87 seconds**, with the same runtime SHA and source-first environment. The retained old-source evidence `qmb-containment-red-final-bb3f4306080b40d4bc71ab1380ea0eb9` records **2 failed, 2 passed**, correctly exposing root movement before any leaf handle exists. Early tests covered that prior blind spot; no failure was hidden or coverage floor lowered.

Final checkpoint logs independently read from disk: `evidence/types-qmb-containment-fixed.txt` reports zero errors, warnings or informations for the two Windows files; `evidence/lint-qmb-containment.txt` reports all checks passed. This adds the bounded strict/lint evidence, not a full-component typing claim.

The existing seven-commit QMB series review remains valid for its other bounded changes and remaining Study failure. B1 is closed only when this exact accepted repair is composed and the obsolete deny-write-sharing claims are reconciled. Current evidence does not turn the broader recorded QMB gate, coverage or platform readiness into green claims; the integrator owns those gates and the separate Study/public projection contract work.
