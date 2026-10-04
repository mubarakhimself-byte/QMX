# QMB native research-store review — DRAFT

Base: `33165e84146b2a6da32c7e536b698c4fa609be3f`; isolated branch
`fix/qmb-native-runtime`. Only QMB host adapter and tests changed.

## Cause and repair

Candidate-only parent/child imports and pinned Click 8.4.2, DuckDB 1.5.5,
Cryptography 50.0.1 are recorded in task-16/evidence/baseline-clusters.
That clean bounded run reproduced 13 failures; the old Click failure passed.
The five Windows store failures were reproduced separately before repair.

Native evidence `native-cause.txt`, `native-open-existing.txt` and
`native-access.txt` captures NtCreateFile at the existing `Mubarak` ancestor.
NTSTATUS `0xc0000022` maps to WinError 5 / errno 13. READ_ATTRIBUTES succeeds;
adding SYNCHRONIZE fails, independently of sharing flags. Removing OPEN_IF alone
did not cure the failure. No App Control cause is inferred and no ACL/settings
were changed.

Directory anchors now request READ_ATTRIBUTES without synchronous data-I/O
rights, open existing components first, and create only missing components.
All anchors remain no-follow and deny write/delete sharing; new NTFS directories
and temporary files use write-through. File descriptors retain synchronous I/O.
Publication remains handle-relative, atomic and no-clobber. Named published
identity and bytes are checked while the original writable handle stays open.
Readers deny external mutation during read. Leaf traversal and ADS names refuse
before root creation. Native errno/winerror survive in the typed refusal.

A red-first retry test exposed acknowledgement without a flush on existing
bytes. Existing and race-winner blobs now compare and flush under one held
writable handle that denies concurrent mutation. Sharing conflicts refuse and
can be retried; they never imply success. Post-publication failure retains the
final blob; pre-publication failure removes only the owned temporary handle.

## Review and evidence

Self-review checked native masks/layout, no path-based fallback, no replacement
rename, handle ownership transfer/closure, cleanup on failure, concurrent
winner identity, immutable final bytes, and scope. No security guard was relaxed.

`run-qmb.ps1 -Label store-reviewed -TestArgs` with
`qmb/tests/test_research_windows.py`, `test_research_host_store.py`, and
`test_ql7_graduation_recovery.py`: **26 passed, 5 existing POSIX-only skips**.
Native tests actually executed: fresh-process reopen, junction refusal, ancestor
and temporary replacement attempts, read mutation denial, equal/conflicting
concurrent publication, flush-before-publish cleanup, post-publish retention,
idempotent retry flush refusal and ambiguous/escaping paths.
The red-first retry log is `evidence/store-adversarial-red/pytest.txt`.
Scoped Ruff passed. Full QMB strict Pyright passed with explicit source/test and
dependency paths (`types-qmb.json`); the earlier missing-interpreter/missing-test-
path invocation is retained as setup-red evidence, not a source defect.

This proves native process restart and the OS-level write-through/flush contract.
It does not claim a physical power-cut/hardware-cache fault experiment.

## Primary references

- [NtCreateFile masks/options and handle-relative names](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile)
- [FILE_RENAME_INFORMATION no-clobber and relative target](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information)
- [CreateFileW NTFS write-through rename metadata](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
- [FlushFileBuffers write access and failures](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)
- Context7 `/python/cpython`: ctypes native argument declarations and
  `msvcrt.open_osfhandle` transfers handle ownership to the CRT descriptor.

Canonical documentation remains unapplied; this file is evidence and a draft.
