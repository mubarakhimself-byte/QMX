# PRB-S findings

Probes from HARDENING-PLAN PRB-S, run on his Contabo server (Ubuntu 24.04.5, 6 cores, 11,960 MB
RAM as `free -m` reads it, 193 GB disk) on 2026-10-21, at `engine/base` 788b1926. The logs are in
`D:/QMX-worktrees/qma-ship/build/evidence/prb-s/` as `owner-<slug>.log`; the install commands are
in `owner-installs.md` there and the lane commands in `owner-lanes.md`. Both probes ran in
`/srv/qmx/check/prb-s` in the throwaway venv at `homes/prb-s/venv` (Hindsight 1.0.0, the same
version PRB-L measured on the PC), as the unprivileged user `prbs`, because embedded PostgreSQL
refuses to run as root.

## Read this first: what the probes disproved

1. **Hindsight does not fit the 2,048 MB line on the server.** Its peak resident memory on Contabo
   was 2,687 MB, against 2,223 MB on the PC. The server is not the cheaper host for it; it is the
   more expensive one. The plan's named fallback therefore applies: Hindsight stays on the PC and
   the server's runs recall through FTS5 over the same rows until the server grows.
2. **The fallback costs no quality.** The server's Hindsight reproduced the PC's recall numbers
   exactly, question for question: already-built 1.0, dead-end 1.4, lab-to-hub 2.2, decided 1.2.
   FTS5 over the same rows reproduced the PC's FTS5 numbers exactly as well (0.4 / 0.8 / 2.4 /
   0.6), which is also the check that the copied rows are the PC's rows.
3. **The line that fails is an RSS line, and the host-level cost is lower.** Free RAM fell by
   1,601 MB (11,340 to 9,739) while Hindsight held the index at rest, because the model files it
   maps are reclaimable page cache that `MemAvailable` still counts. The plan's P-MEM line is RSS,
   not free RAM, so the row is a FAIL; a placement budget built on the free-RAM delta alone would
   have passed it.
4. **P-OPS passes with room**, but its run shared the box with P-MEM: load rose from 0.70 to 6.52
   and the tick wall to 3,675 ms over 60 ticks, so 0.2042 % of a core is an upper bound on a quiet
   host. The PC read 0.0408 % on a quiet one.

## Rows

| Probe | Verdict | Numbers | Fallback it triggers |
| --- | --- | --- | --- |
| P-OPS (Contabo) | PASS | 20 agents, every 30 s, 1,800 s, 1,260 rows; largest row 814 bytes (line 4,096); work 0.2042 % of one core (line 1 %), the larger of process CPU and tick wall; load 0.70 at the start and 6.52 at the end, beside P-MEM | none |
| P-MEM (Contabo) | FAIL on RAM | peak resident 2,687 MB (line 2,048); resident 1,899 MB after the bulk retain and the 20 recalls; peak RSS sum 8,044 MB (shared buffers counted once per backend); Hindsight against the PC's per-type numbers, all held: already-built 1.0/1.0, dead-end 1.4/1.4, lab-to-hub 2.2/2.2, decided 1.2/1.2; FTS5 on the same rows 0.4/0.8/2.4/0.6, the PC's exactly; bulk chunks retain 1,032 s for 3,591 rows (the PC's 618 s) | the plan's: Hindsight stays on the PC and the server's runs recall through FTS5 over the same rows until the server grows |
| `overhead_mb` (derived) | 8,960 | free RAM 11,340 MB without Hindsight and 9,739 MB with it, 10,075 MB after it stopped; Hindsight's footprint 2,687 MB (the peak, against a 1,601 MB free-RAM delta at rest); 6,144 + 2,687 rounded up to the next 256 MB; `floor((12,288 - 8,960) / 1,536)` = 2 sessions with Hindsight, and `floor((12,288 - 6,144) / 1,536)` = 4 without | none: it is a recorded figure for `[placements] contabo` |

## What the probes measure

- **P-OPS.** `scripts/probes/server/p_ops.py` writes synthetic heartbeat rows for 20 agents at the
  30 s interval for 1,800 s, one real process sampled per agent row, into SQLite in one
  transaction per tick. The row, the insert path, the limits and the verdict are
  `scripts/probes/library/p_ops.py`'s, loaded by path; only the row producer is the server's,
  because the library's labels the host `pc` and reads `D:/` for free disk. `test_probes.py`
  checks that the server row has the library row's fields and that the two differ in the host name
  and the disk root.
- **P-MEM.** `scripts/probes/server/p_mem.py` retains PRB-L's 3,591 rows in Hindsight's `chunks`
  mode with observations off, recalls the same 20 questions, and compares the top-5 hits with
  FTS5 over the same rows. Quality is the PC's question and is held, not re-decided: the server's
  Hindsight must not fall below the PC's per-type means. The row this host decides is memory: peak
  resident at most 2,048 MB.
- **`overhead_mb`.** AD-30 derives `max_sessions = floor((ram_budget_mb - overhead_mb) /
  session_mb)`, with `session_mb` 1,536 and Contabo's colocated services at 6,144, which gives 4
  sessions on 12 GB. The derived figure adds Hindsight's measured footprint and rounds up to the
  next 256 MB. Review 48 M11 said the 6,144 leaves Hindsight out; this is the measurement that puts
  it in.

## How to read the numbers

- Memory is the peak, sampled every 2 s, of the probe's Python process plus pg0's PostgreSQL for
  the probe instance (this host has no other instances): each process's unique working set summed,
  and the largest shared part added once, exactly the PC's measure. The plain RSS sum is in the
  log beside it; it is 8,044 MB because each of the pool's backends maps the same shared buffers.
- The 2,687 MB peak came before the end of the recall: 1,899 MB was resident when the run read
  free RAM. The free-RAM delta (1,601 MB) therefore understates the peak; the overhead uses the
  peak, which is the conservative figure, and the delta's own route (6,144 + 1,601 = 7,745,
  rounded to 7,936) also leaves 2 sessions. Both routes agree on the session count.
- What `[placements] contabo` should take: 8,960 is the figure that counts Hindsight and leaves 2
  sessions, and it is the one this PR records. While the P-MEM FAIL keeps Hindsight on the PC (the
  plan's fallback), Contabo's row keeps 6,144 and its 4 sessions; 8,960 is the value it takes when
  the server grows or Hindsight moves there.
- The bulk chunk retain on the server took 1,032 s for the 3,591 rows against the PC's 618 s: 1.7
  times slower per row on six shared vCPUs than on the PC, with no GPU. MEM's retain worker and the
  session-digest budget should be sized from the server figure, not the PC's.
- Machine load beside the numbers: the box ran both probes at once, so the P-OPS load line rose
  from 0.70 to 6.52 while P-MEM's local embedder used the cores. The P-MEM timings are from that
  same loaded window and are therefore an upper bound too.

## What is different from the PC run

- No key and no model turn: Hindsight starts with `llm_provider=none`, the rows are retained in
  `chunks` mode with observations off, and recall is pure retrieval. The embedding model is the
  local download `BAAI/bge-small-en-v1.5`; the reranker is local too. The PC's digest-retain
  latency line (42.0 s through an extractor) is therefore not re-measured here; it needs an
  extractor through the router and this host holds no provider key.
- The corpus is PRB-L's rows file, copied unchanged
  (`sha256 1b9d9f1d196ab029eca3ce7ff2db5706aba76a9fd5b22d1324ef5a8e7f93688f`), rather than re-cut
  from the plan branch: the same bytes are what "against the same rows as PRB-L" means, and the
  identical FTS5 numbers are the proof they survived the trip.
- Lanes 3 and 4 are two separate full runs of the same script; lane 4 only names its log
  `prb-s-ram` and leads with the RAM record.
