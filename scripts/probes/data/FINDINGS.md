# Data probes

Probes from the data round (DATA-PLAN; the final probe table in `research/methodology/55-data-round-architecture.md` "Fix-check applied (58)"), run on the PC (Windows 11) and on the server. Logs are in the store's `evidence/<id>/` as `owner-<slug>.log`. The plan rewrote the probe table in 58, so a probe's PASS and FAIL lines are the ones in that table, not in 57.

| Probe | Verdict | Numbers | Fallback it triggers |
| --- | --- | --- | --- |
| P-TORN | PASS (owner run, DR1A) | Four cases on a scratch store under `D:/Temp`: the ref, edge and annotation logs each standing with a cut last line, then with a NUL-filled last line, the store opened `torn` and quarantined the line byte for byte; a bad middle line opened it `read_only` with the incident `refs/log.jsonl line 2 does not parse` and refused `put`; a second process held `refs/claims.json` open and the rename retried 5 times (WinError 5) and landed after the handle closed at about 0.6 s. The coordinator reruns it at the verified head | none |
