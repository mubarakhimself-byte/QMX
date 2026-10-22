# Server probe findings, PRB-DS

Premise and measure probes 13, 27 and 30 of the final probe table in
`research/methodology/55-data-round-architecture.md` "Fix-check applied (58)": P-HS, P-DOCLING and
P-OO. The sections they gate are DR2E, DR7 and DR10.

Every probe runs on `qmx-server` (Ubuntu 24.04, 6 cores, 11,960 MB as `free -m` reads it, 160 GB
free) as the ordinary user `qmx`, from the checkout at `/srv/qmx/check/prb-ds/checkout`, under
`/srv/qmx/check/prb-ds/`. Root installed PostgreSQL 16 with pgvector and `useradd` made nothing.
The probe folders and services are removed when the probes finish; the PostgreSQL package stays
for DR2E.

Owner runs are the builder's. Lane runs are the coordinator's, and every row names its command so
they run the same thing. A row that says `not run` carries the reason it was not measured; it is
never dressed as a pass.

| Probe | Verdict | Numbers | Fallback it triggers |
| --- | --- | --- | --- |
| P-HS | not run (owner: out of the session's probe budget) | Hindsight 1.1.0 is installed and PostgreSQL 16.15 with pgvector is up. The memory legs need the corpus and the recall leg needs the PC's answers to the same corpus, and the retain burst PRB-S timed at 1,032 s on this box is over the builder's 15-minute probe budget. The rerun writes all of it | the plan's: Hindsight stays on the PC and server workflows recall through FTS5 over the same rows, as PRB-S measured. DR2E is skipped as OBSOLETE and the reading goes to `QUESTIONS-FOR-OPERATOR.md` |
| P-DOCLING | not run (owner: Docling install and the two extractions are over the session's probe budget) | The PDF leg downloads a public GNU Emacs manual and slices it to 400 pages with `pypdf`; the audio leg downloads one 63-minute public LibriVox chapter. Both run in a child process each and print time and peak memory | the plan's: the `extract-source` template's default home becomes `pc` for the class that was killed, and DR7 ships with that default |
| P-OO | not run (owner: OpenObserve's release asset is not on GitHub, see the departure below) | One day of telemetry (57,600 heartbeat rows, 20,000 spans, 5,000 log rows) is replayed into the 1.0.4 binary and the row takes its peak memory and its data-folder size. The binary comes from `downloads.openobserve.ai`, because the `v1.0.4` GitHub tag has an empty asset list | the plan's: DR10 ships the internal layer and the exporters, with the collector keeping its disk queue and OpenObserve not installed |

## How each probe decides

- **P-HS** (`scripts/probes/data/p_hs.py`). Hindsight 1.1.0 starts against a system PostgreSQL 16
  cluster with pgvector, on a unix socket, as `qmx`, with `llm_provider=none` and the local
  embedding and rerank models, so no key is read and no model turn runs. The child keeps the row
  count in `chunks` mode with observations off, exactly PRB-S's shape. PASS needs the service to
  start, the child not to be killed, the memory to be recorded, the live free RAM after the burst
  to still hold the probe's own admission bound of 2,560 MB (AD-30's 1,536 MB session plus 1,024
  MB for the host and the collector; a probe bound, not a QMX cap), and recall parity with the
  PC over the fixed query set. FAIL is the process killed, the service not starting, or recall
  differing. `--emit-recall` on the PC and `--pc-recall` on the server make parity two runs of
  the same script over the same rows.
- **P-DOCLING** (`scripts/probes/data/p_docling.py`). Docling 2.134.0 extracts a 400-page public
  PDF and one hour of public audio, one child process per leg, and the row takes each leg's wall
  time and peak resident memory. PASS is both legs finishing. FAIL is a process killed or a leg
  that does not start. A build with no audio pipeline prints the audio leg as `not run` with that
  reason, because that is a finding about the version, not a memory number.
- **P-OO** (`scripts/probes/data/p_oo.py`). The 1.0.4 service runs on the server's own disk, the
  day's records go to its own `_json` ingest in batches of 1,000, and the row takes the group's
  peak resident memory, the data folder's size and the replay time. A `--scale` below 1 reports
  the day it would reach. PASS is the service starting and the ingest completing. FAIL is the
  process killed or the service that does not start.

## Departures from the plan's Build block

- **P-OO's download.** The plan says OpenObserve 1.0.4 "from its GitHub release". That release
  has no assets: `https://api.github.com/repos/openobserve/openobserve/releases/tags/v1.0.4`
  answers with an empty asset list, and the pinned URL here is the published
  `downloads.openobserve.ai` archive for the same tag.
- **P-DOCLING's sample.** The plan names "a 400-page public PDF and one hour of public audio"
  without naming the files. The probe pins the GNU Emacs manual sliced to 400 pages and one
  63-minute LibriVox chapter, both public, and reuses the downloads on a rerun so Docling is what
  is measured.
- **P-HS's corpus.** The fixed query set is `scripts/probes/library/questions.json`, as the plan
  says, and the corpus is the rows file the PC builds once (`--corpus-root` over the plan record)
  and the server reuses, so both sides rank the same bytes.
