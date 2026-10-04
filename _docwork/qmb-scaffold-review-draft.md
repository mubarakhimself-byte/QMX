# QMB scaffold root-cause review (draft)

The clean combined run failed three scaffold contracts. Native ctypes argtypes
were module-global lists; use supported immutable tuples. The empty occurrence
mapping sentinel is now a MappingProxyType. Neither changes runtime semantics.

The import guard allows builtin open only for the existing CLI verification
claim read inside backtest_run with exactly claim_path as its argument. It does
not exempt the CLI module from other forbidden calls. The receipt vocabulary
guard recognizes an exact StoreReceipt nominal check with a refusing branch,
then tracks its field proof through a local alias. Assignment, attribute writes,
and rebinding type/StoreReceipt invalidate the proof. The engine diagnostic key
is permitted only when its value compares the proven receipt engine. Added
adversarial scanner tests exercise stale proof, wrong type and non-exiting guard.

Self-review: no public CT47 flow changed; no global whitelist or suppression.
Evidence: structural-reviewed/pytest.txt: 74 passed, four preexisting Windows
chmod skips; qmb-types-example/output.txt: zero strict typing errors. Candidate
and subprocess provenance is retained in task-16/evidence.
