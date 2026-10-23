# Server probe findings, PRB-DS

Premise and measure probes 13, 27 and 30 of the final probe table in
`research/methodology/55-data-round-architecture.md` "Fix-check applied (58)": P-HS, P-DOCLING and
P-OO. The sections they gate are DR2E, DR7 and DR10.

Every row below is a run that happened, and the numbers are quoted from the log the row names.
`evidence/prb-ds/owner-lanes.md` holds the exact command that reproduces each one. The box is
`qmx-server`: Ubuntu 24.04, 6 cores, 11,960 MB as `/proc/meminfo` reads it, 153 GB free. Every
probe runs as the ordinary user `qmx` under `/srv/qmx/check/prb-ds/`; root installed packages and
nothing else. The probe folder and every service in it are removed when the probes finish. The
PostgreSQL package and the `ffmpeg` binary stay on the box, because apt installed them and DR2E
reuses PostgreSQL.

Owner runs are the builder's, named `owner-` in the probe root's `logs/`. A lane run writes
`check-` beside them. A leg that did not run says so in words and is never dressed as a pass.

| Probe | Verdict | Numbers | Fallback it triggers |
| --- | --- | --- | --- |
| P-HS | PASS on the service and memory legs, recall parity `not run` (see the parity note) | Hindsight 1.1.0 (the `hindsight-api` console script; the package's module is `hindsight_api`) on Ubuntu's PostgreSQL 16.15 with pgvector 0.6.0, `HINDSIGHT_API_LLM_PROVIDER=none`, no worker or slot variable set, so the package's own `DEFAULT_WORKERS = 1` applies. Service healthy in 43.1 s. Idle: 1,342 MB resident, 10,261 MB free. Retain burst of 500 rows in `chunks` mode with observations off: 94.8 s, 1,584 MB service at the end of the burst and 29 MB of PostgreSQL high-water mark, 9,868 MB free after. The whole run's peak, reached during recall, was 2,030 MB of service, so the admission reading is 2,059 MB with PostgreSQL. Against the row's 2,560 MB reserve (AD-30's 1,536 MB session plus 1,024 MB for the host and the collector: a probe bound, not a QMX cap) the box holds with 501 MB to spare on that peak and 947 MB on the burst reading. PRB-S's PC reading was 2,687 MB, 657 MB above this one. 5 of the 40 fixed queries recalled in 171.4 s. Logs: `/srv/qmx/check/prb-ds/logs/owner-prb-ds-hs.log` and the second run's stdout, kept as `evidence/prb-ds/owner-prb-ds-hs.log` | none: the plan's fallback (Hindsight stays on the PC, DR2E skipped as OBSOLETE) is not triggered |
| P-DOCLING | PASS, in two runs of the same probe | Docling 2.134.0, one child process per leg. PDF leg: the GNU Emacs manual cut to its first 400 pages, 1,182.0 s, 7,334 MB peak, 1,278,411 characters of markdown out (2.96 s and 18.3 MB a page). Audio leg: one 3,797 s (63.3 minute) LibriVox chapter, 50,560,458 bytes of mp3, 1,104.1 s, 2,666 MB peak, 58,034 characters out (0.29 of realtime). Both exit 0. Logs: `/srv/qmx/check/prb-ds/logs/docling-run2.out` for the PDF leg (the first full run, whose audio leg failed first) and `docling-run3.out` for the audio leg, kept as `evidence/prb-ds/owner-prb-ds-docling-full.log` and `evidence/prb-ds/owner-prb-ds-docling-audio.log` | none: the plan's fallback (the `extract-source` template defaults that file class to `pc`) is not triggered |
| P-OO | PASS | OpenObserve 1.0.4 on the server's own disk. A synthetic day of QMX telemetry (57,600 heartbeat rows, 20,000 spans, 5,000 log lines: 82,600 records, 15,533,475 bytes of JSON) replayed in batches of 1,000: 7.9 s in total. Service healthy in 5.2 s, 207 MB idle, 340 MB peak across the service's process group. Data folder after the day: 64 MB, so 64 MB a day. Free RAM 11,271 MB before, 10,990 MB after. Log: `/srv/qmx/check/prb-ds/logs/owner-prb-ds-oo.log`, kept as `evidence/prb-ds/owner-prb-ds-oo.log` | none: the plan's fallback (DR10 ships the internal layer and the exporters, OpenObserve not installed) is not triggered |

## The Settings default each row feeds

- P-HS feeds DR2E's admission reserve: 2,030 MB for the Hindsight service over a whole run plus
  29 MB of PostgreSQL, which the row rounds up to its 2,560 MB bound so the host, the collector and
  one agent session fit beside it. The idle reading is the service's floor: 1,342 MB before any row
  is retained.
- P-DOCLING feeds DR7's `extract-source` declared memory default: 7,334 MB for 400 pages, about
  18 MB a page, and 2,666 MB for an hour of audio. The times matter as much: 400 pages took 1,182 s
  and an hour of audio took 1,104 s on this CPU, so an extraction is a background job and never a
  request.
- P-OO feeds DR10's Settings: 340 MB of memory and 64 MB of data folder per day of this shape, so
  the plan's 14-day retention is about 0.9 GB per ingest source before any replication.

## How each probe decides

- **P-HS** (`scripts/probes/data/p_hs.py`). PASS needs the service to start and answer healthy, the
  process not to be killed, the memory to be recorded, and the live free RAM after the burst to
  still hold the probe's own 2,560 MB bound. FAIL is the process killed, the service not starting,
  or recall differing from a named second run. The parity leg compares the same fixed questions
  against another run's answers, written with `--emit-recall` and named with `--pc-recall`.
- **P-DOCLING** (`scripts/probes/data/p_docling.py`). PASS is both legs finishing in their child
  processes with their time and peak memory recorded. FAIL is a process killed or a leg that does
  not start. The peak is the kernel's high-water mark for the child's own process group, so a short
  spike between samples is not lost.
- **P-OO** (`scripts/probes/data/p_oo.py`). PASS is the 1.0.4 service starting and the day's records
  being accepted. FAIL is the process killed or a service that does not start. It stops the whole
  service group before it exits, so no probe service outlives the run, and it wipes its data folder
  first so the disk figure is its own day.

## The parity leg, in plain words

Recall parity with the PC is **not measured**, and the row says so rather than calling it a pass.
Two things are missing, and neither is a number this builder can produce honestly:

- The fixed query set `scripts/probes/library/questions.json` was written over his real library
  rows (its own `note` says the 40 questions were written over `~/.qmx/library.db` as of
  2026-10-18). Reading his real home is outside this builder's boundary, so the run above ranks the
  plan record's markdown instead. It proves the recall path works end to end on this box; it does
  not prove those 40 questions come back the way the PC answers them.
- Parity is defined by this probe as a second run of the same script with `--emit-recall`. No such
  run exists, and the PC cannot make one today: it has no PostgreSQL 16 binaries at
  `/usr/lib/postgresql/16/bin` and no Hindsight install.

The coordinator can close it with one `--emit-recall` run on a box that has both, then one
`--pc-recall` run here. The flag, the comparison and the top-5 rule are already in the probe.

## Departures from the plan's Build block

- **Docling's audio backend.** A plain `docling==2.134.0` install ships the audio pipeline class but
  not its backend: the audio leg ended `ImportError: whisper is not installed. Please install it via
  'pip install openai-whisper' or do 'uv sync --extra asr'.` (`logs/docling-run2.out`). The plan says
  "Docling 2.134.0", which is what was installed, so this is a real finding about the package, not a
  slip in the install. `openai-whisper==20250625` and `ffmpeg 6.1.1` were added and the audio leg
  rerun alone (`logs/docling-run3.out`); the PDF numbers are from the run before it, which is why
  the row names two logs. Every command is in `evidence/prb-ds/owner-installs.md`.
- **P-DOCLING's page library.** Docling does not depend on `pypdf`, which the probe uses to cut the
  source PDF to 400 pages. Without it the probe logged "no pypdf in this venv: the whole document is
  the PDF leg" and started converting 700-odd pages; that attempt was stopped. `pypdf==6.21.2` is in
  the venv and in the install record now.
- **P-OO's download.** The plan says OpenObserve 1.0.4 "from its GitHub release". That release has
  no assets: `https://api.github.com/repos/openobserve/openobserve/releases/tags/v1.0.4` answers
  with an empty asset list, so the pinned URL is the published `downloads.openobserve.ai` archive
  for the same tag, and the probe fetches it itself.
- **P-DOCLING's sample.** The plan names "a 400-page public PDF and one hour of public audio"
  without naming files. The probe pins the GNU Emacs manual cut to 400 pages and one 63-minute
  LibriVox chapter, both public, and reuses the downloads on a rerun so Docling is what is measured.
- **P-HS's corpus and transport.** The plan does not name the corpus; the probe builds rows from the
  plan record's markdown. PostgreSQL listens on a loopback port picked at run time rather than a
  unix socket, because the service's own URL parsing is happiest with a TCP DSN, and no fixed port
  is held either way.
- **P-HS's worker slots.** The row records "default": no `HINDSIGHT_API_*WORKERS` or `*SLOTS`
  variable is set, so the package's `DEFAULT_WORKERS = 1` applies. That is what the plan's "at the
  default worker slots" is.
