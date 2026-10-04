# QMB sandbox structural assertion review (draft)

The test scanned every host file for ctypes, including the filesystem-only
Windows research store. The bot execution boundary is runner.py and worker.py;
the structural assertion now checks those two files. Both retain bans on
ctypes, win32api, exec and eval. This does not add Windows bot confinement or
claim that filesystem handle security confines bot code. Existing runtime
sandbox tests are retained. Evidence: structural-reviewed/pytest.txt: 74 passed
with four preexisting POSIX chmod skips. Self-review: scoped test correction,
no production sandbox code or security setting changes.
