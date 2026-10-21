# PRB-S findings

Probes from HARDENING-PLAN PRB-S, run on his Contabo server (Ubuntu 24.04.5, 6 cores, 11,960 MB
RAM as `free -m` reads it, 193 GB disk) on 2026-10-21, at `engine/base` 788b1926. The logs are in
`D:/QMX-worktrees/qma-ship/build/evidence/prb-s/` as `owner-<slug>.log`; the install commands are
in `owner-installs.md` there. Both probes ran in `/srv/qmx/check/prb-s` in the throwaway venv at
`homes/prb-s/venv` (Hindsight 1.0.0, the same version PRB-L measured on the PC).

## Rows

| Probe | Verdict | Numbers | Fallback it triggers |
| --- | --- | --- | --- |
| P-OPS (Contabo) | run pending at this commit | row bytes and CPU share land with the lane 2 log | the plan's: idle hosts send deltas at a longer interval (OPS2) |
| P-MEM (Contabo) | run pending at this commit | peak resident MB and the per-type hold land with the lane 3 log | the plan's: Hindsight stays on the PC and server runs recall through FTS5 over the same rows until the server grows |
| `overhead_mb` | run pending at this commit | the free-RAM pair and the derived figure land with the lane 4 log | none: a recorded number for `[placements] contabo` |

## What the probes measure

- **P-OPS.** `scripts/probes/server/p_ops.py` writes synthetic heartbeat rows for 20 agents at the
  30 s interval for 1,800 s, one real process sampled per agent row, into SQLite in one
  transaction per tick. Pass is a row of at most 4 KB and the work at most 1 % of one core. The
  row, the insert path, the limits and the verdict are `scripts/probes/library/p_ops.py`'s, loaded
  by path; only the row producer is the server's, because the library's labels the host `pc` and
  reads `D:/` for free disk. `test_probes.py` checks that the server row has the library row's
  fields and that the two differ only in the host name and the disk root.
- **P-MEM.** `scripts/probes/server/p_mem.py` retains PRB-L's 3,591 rows in Hindsight's `chunks`
  mode with observations off, recalls the same 20 questions, and compares the top-5 hits with
  FTS5 over the same rows. Quality is the PC's question and is held, not re-decided: the server's
  Hindsight must not fall below the PC's per-type means (already-built 1.0, dead-end 1.4,
  lab-to-hub 2.2, decided 1.2) and its peak resident memory must stay within 2,048 MB. The server
  also re-scores FTS5 on the copied rows as a check that they are the PC's rows.
- **`overhead_mb`.** AD-30 derives `max_sessions = floor((ram_budget_mb - overhead_mb) /
  session_mb)`, with `session_mb` 1,536 and Contabo's colocated services at 6,144, which gives 4
  sessions on 12 GB. The derived figure adds Hindsight's measured footprint to the 6,144, rounded
  up to the next 256 MB, and is reported with the session count it reserves. Review 48 M11 said
  the 6,144 leaves Hindsight out; this is the measurement that puts it in.

## What is different from the PC run

- No key and no model turn: Hindsight starts with `llm_provider=none`, the rows are retained in
  `chunks` mode with observations off, and recall is pure retrieval. The embedding model is the
  local download `BAAI/bge-small-en-v1.5`; the reranker is local too. The PC's digest-retain
  latency line (42.0 s through an extractor) is therefore not re-measured here; it needs an
  extractor through the router and this host holds no provider key.
- The corpus is PRB-L's rows file, copied unchanged, rather than re-cut from the plan branch: the
  same rows are what "against the same rows as PRB-L" means, and it keeps the comparison exact.
- Memory is the peak over this process and pg0's Postgres for the probe instance, the same
  measure as the PC's 2,223 MB (unique working sets summed, the largest shared part counted
  once).

## How to read the numbers

Filled with the run.
