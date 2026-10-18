# PRB-L findings (work in progress, paused by a hold order)

Probes from HARDENING-PLAN PRB-L, run on the PC on 2026-10-18 at `engine/base` 132169c7. Logs are in `D:/QMX-worktrees/qma-ship/build/evidence/prb-l/` as `owner-<slug>.log`. The P-SRCH question set (`questions.json`) is Claude's default (Appendix H): no labelled set exists, and the operator may replace it.

## Read this first: two design facts the probes disproved

1. His `~/.qmx/library.db` holds 11 items, all one `workflow-result` titled `remote-flow` with byte-identical content, no tags and no links. P-SRCH cannot measure a grounder on it, because no grounding can be wrong.
2. Copying his session transcripts out of `~/.claude` was refused by the session's permission check. P-MEM runs on his plan documents (224 Markdown files under `tracker/qma-v2/`) and his `library.db` items instead.

## Rows

| Probe | Verdict | Numbers | Fallback it triggers |
| --- | --- | --- | --- |
| P-NEST | PASS | parent 0 problems, child 0 problems. The validator has no nesting check at all, so a loop directly in a loop body also validates | none |
| P-OPS (PC) | PASS | 20 agents, 30 s, 1,800 s, 1,260 rows; largest row 810 bytes; work 0.0408 % of one core | none |
| P-SRCH | FAIL | precision 1.0, coverage 0.75 (9 of 12), truncation keeps every top 5, noise keeps his item first; distinct items 1, so the numbers measure nothing | LIB3 tunes and reruns P-SRCH before it is appended, on a store with real items |
| P-TAINT | not settled | dev run under load (Hindsight install running): p95 86.3 ms, p50 18.0 ms, fresh-connection p95 17.5 ms, ancestry 500, depth 20. Needs a quiet owner run (lanes 2 and 5) | pending |
| P-MEM (PC) | not settled | last complete run (memory metric then wrong): Hindsight vs FTS5 mean relevant hits in top 5: already-built 1.0 vs 0.4, dead-end 1.4 vs 0.8, lab-to-hub 2.2 vs 2.4, decided 1.2 vs 0.6. Resident memory sampled mid-run about 1,690 MB unique plus shared buffers once (Python 1,278 MB USS, Postgres 409 MB USS over 54 processes). Digest retain timed out with deepseek-v4.1-flash; deepseek-v4-flash with reasoning off took 35 s on a plain request | pending |
