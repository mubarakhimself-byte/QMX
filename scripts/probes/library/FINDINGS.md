# PRB-L findings

Probes from HARDENING-PLAN PRB-L, run on the PC (Windows 11, 16 GB RAM) on 2026-10-18 and 2026-10-19 at `engine/base` 132169c7. Logs are in `D:/QMX-worktrees/qma-ship/build/evidence/prb-l/` as `owner-<slug>.log`. The P-SRCH question set (`questions.json`) and the P-MEM questions are Claude's default (Appendix H): no labelled set exists, and the operator may replace them.

## Read this first: what the probes disproved

1. His `~/.qmx/library.db` holds 11 items, all one `workflow-result` titled `remote-flow` with byte-identical content, no tags and no links. The ship home's `library.db` is empty. P-SRCH cannot measure a grounder on it, because no grounding can be wrong.
2. P-MEM does not fit the PC lines with the stock embedded Hindsight. Its peak resident memory was 2,223 MB against the 2,048 MB line, and one digest retain took 42.0 s against the 30 s line.
3. The P-MEM corpus is his plan record, not his session transcripts. The brief forbids touching `~/.claude`, so P-MEM ran on the 224 Markdown files under `tracker/qma-v2/` on `plan/agent-system` plus his `library.db` items, 3,591 rows.

## Rows

| Probe | Verdict | Numbers | Fallback it triggers |
| --- | --- | --- | --- |
| P-TAINT | PASS | p95 13.73 ms (lane 2) and 13.81 ms (lane 5), 0.6 % apart; p50 10.94 ms; 200 samples; ancestry 500, depth 20; 100,000 items with 29,438 memory rows | none |
| P-MEM (PC) | FAIL on RAM, quality and retain time | peak resident 2,223 MB (line 2,048); digest retain 42.0 s with `deepseek/deepseek-v4-flash` on OpenRouter, reasoning off (line 30 s); mean relevant hits in the top 5, Hindsight against FTS5: already-built 1.0 / 0.4, dead-end 1.4 / 0.8, lab-to-hub 2.2 / 2.4, decided 1.2 / 0.6 | RAM: Hindsight stays on the PC and the server's runs recall through FTS5 over the same rows until the server grows. Quality: recorded and tuned, the choice of Hindsight stands (ruling 119). Retain time: the plan names no fallback; the coordinator reports it |
| P-SRCH | FAIL | precision 1.0, coverage 0.75 (9 of 12 answerable), truncation keeps every top 5, noise keeps his item first; 1 distinct item, so the numbers measure nothing | LIB3 tunes the constants and reruns P-SRCH before it is appended, on a store with real items |
| P-NEST | PASS | parent 0 problems, child 0 problems. The validator has no nesting check at all, so a loop directly in a loop body also validates (BACKLOG) | none |
| P-OPS (PC) | PASS | 20 agents, every 30 s, 1,800 s, 1,260 rows; largest row 810 bytes (line 4 KB); work 0.0408 % of one core (line 1 %) | none |

## How to read the P-MEM numbers

- Memory is the peak, sampled every 2 s, of the probe's Python process plus pg0's Postgres for the probe instance. Each process's unique working set is summed, and the largest shared part is added once, so Postgres's shared buffers count once. The plain RSS sum was 9,117 MB, because each of the pool's Postgres backends maps the same shared buffers. Resident memory was 1,835 MB after the bulk retain and peaked at 2,223 MB later, during recall and the digest retain. The earlier, cut run read about 1,690 MB at mid-run: Python 1,278 MB (the local embedder and reranker) and Postgres 409 MB over 54 processes.
- Free RAM was 2.7 GB of 16 GB when the run began, and no test suite was running. Windows trims working sets under pressure, so 2,223 MB is a lower bound, not an overstatement.
- The retain time is one extraction of 8,000 characters of his rulings file through the OpenRouter DeepSeek row. On the same text, `deepseek/deepseek-v4.1-flash` took 103 s with reasoning off and 406 s with reasoning on. 42.0 s is the fastest DeepSeek row measured. Most of it is likely the provider's generation time rather than Hindsight's own work (inferred from the spread between DeepSeek rows on the same text, not measured inside Hindsight).
- A hit is relevant when its text holds the question's answer phrase. That oracle favours lexical matches and so favours FTS5. Hindsight still led on three of the four types and was behind by 0.2 hits on lab-to-hub (2.2 against 2.4, decided by one question: 2 hits against 4).
- The run's own verdict line reported only the RAM failure. `judge` now reports every failed line with its fallback, and the logged numbers were judged again with it (last line of `owner-prb-l-mem.log`).

## Machine load beside the timing numbers

P-TAINT's quiet runs (2026-10-19 09:36) had CPU at 16 to 33 % and no test-suite process. An earlier pair at 09:14 ran while another builder's pytest suites were running (10 test processes, 356 MB free RAM) and read 15.88 ms and 20.67 ms, 30 % apart. Both still pass the 50 ms line. They stay in the logs and are not used for the verdict.
