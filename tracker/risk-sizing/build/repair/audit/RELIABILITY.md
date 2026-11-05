# How far to trust this audit

The auditors found 4 of 12 known defects.

| # | The defect | Found by | Notes |
| --- | --- | --- | --- |
| K1 | A stop moved past entry goes out as an unsigned distance, and the node reports the stop asked for | Missed as a finding | The venue auditor saw it and wrote it under "Ruled, not graded" in `reports/p5b.md`, because his ruling gives the signed distance to the risk session. No row, so it counts as missed. Its second half, the node reporting the wrong stop, is a mechanism defect |
| K2 | The app install runs `uv sync` with no time limit, so it can wait for ever | Missed | |
| K3 | One test line restates its own parameter | Missed | p5a-30 names another line in the same file |
| K4 | One app failing at host start leaves the apps after it down | p5c-3 | Same failure, should |
| K5 | `import qmx_host.connect_logs` first fails with a circular import | Missed | The trial auditor missed it too |
| K6 | A guard reason with no listed phrase writes no row | seams-3, p0b-4 | They went further: it stops the whole unit journal |
| K7 | qmx-control imports `qml` without declaring it | Missed | |
| K8 | The MIS board never reaches a running node | p5d-7, seams-14 | Both `leave`, because his triage calls it safe today (TR:49). I keep that call |
| K9 | Server setup stops on a card asking him to install two Linux programs | p5c-5 | Graded should, known list says must. It belongs with the one-click repair |
| K10 | One deeply nested log line stops deep logs for every app | Missed | |
| K11 | A brief OpenObserve outage leaves the doctor row red and loses waiting lines | Missed | |
| K12 | Every supervisor event reads `app_log` at info level | Missed | |

## What this means

- **At the top, the score is better than 4 of 12 sounds.** Three known defects were graded must. All three were seen, and two were filed.
- **Below that, the score is poor.** Of the nine known defects below must, the auditors filed two. So "this is fine" on small things is weak evidence. There are more small defects than this audit lists.
- **One "this is fine" was wrong.** `reports/p5d.md` calls the log shipper sound and praises its test file. A focused trial read of the same code found three defects there (K10, K11, K12). That part had 86 files. A thin read of a wide part misses things a narrow read catches.
- **Where they did look, they were right.** Two verifiers tried to knock down 34 must rows, reran the proofs and refuted none. They did lower 6 to should and corrected overstatements in several others, so they were not simply agreeing.
- **I found one must they all missed** (chief-2, phone alarms off on an installed node), by following a side effect of a long run. So must-level blind spots exist too.

Plainly: trust the must list as real. Do not treat it as complete. "Sound" means nothing serious turned up, not that nothing is there.

## Skills and coverage per part

| Part | Skills and files check | Tool calls | Hours |
| --- | --- | --- | --- |
| p0a | PASS, 47 of 47 files | 96 | 0.29 |
| p0b | PASS, 67 of 67 | 155 | 0.40 |
| p1a | PASS, 107 of 107 | 206 | 0.42 |
| p1b | PASS, 35 of 35 | 115 | 0.42 |
| p2 | PASS, 53 of 53 | 125 | 0.52 |
| p34 | PASS, 103 of 103 | 112 | 0.43 |
| p5a | PASS, 41 of 41 | 91 | 0.43 |
| p5b | PASS, 31 of 31 | 87 | 0.34 |
| p5c | PASS, 21 of 21 | 79 | 0.27 |
| p5d | PASS, 86 of 86 | 111 | 0.30 |
| p6 | PASS, 142 of 142 | 218 | 0.37 |
| Plan check, seams, verifiers | PASS | | |
| Deletion | One false FAIL: `uv run` was text inside a grep pattern, the hook refused the command, nothing ran. Marked partial | 81 | 0.58 |

The verifier refuted 0 of 34 must findings.
