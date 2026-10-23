# Save the old ticks, then import them

Two scripts, in the order they run. `save_old_ticks.py` copies the old ticks to the server,
checks the copy, and writes the manifest the import compares against. `import_old_ticks.py`
reads that copy and lands it as price partitions. Both are scripts, not product code.

# Save the old ticks

`save_old_ticks.py` copies the old ticks to the server, checks the copy, and writes the
record that DR3C's import reads. It is a script, not product code. rclone does the moving
and the comparing; the script picks what gets compared, writes the manifest and the
record, and refuses to guess when rclone reports a difference.

## What it writes

- `MANIFEST.sha256` beside each copy, one line per file, `<sha256>  <bytes>  <path>`, LF
  endings, paths relative to the source and in sorted order.
- A JSON record at the path you pass, with the file count, total bytes, the manifest's own
  sha256 and one entry per destination. Nothing in it changes between two runs over an
  unchanged source, so a rerun writes the same bytes.
- Nothing else. The script reads the source and never deletes or moves a file, and it
  never reads an rclone config: it passes `--config <path>` to rclone and takes remote
  names only. It prints `no bucket remote configured` and exits 0 when `--bucket` is
  absent, which is the state until G-R2 opens.

## Run it

Copy the old 10 GB to the server, with the coordinator's rclone config:

    uv run --no-sync python scripts/data/save_old_ticks.py `
      --source C:/Users/Mubarak/Documents/QMX/data/raw/external-deep-history `
      --target qmxserver:/srv/qmx/data/raw-backup/external-deep-history `
      --config D:/Tools/rclone/rclone-qmx.conf `
      --record D:/QMX-worktrees/qma-ship/data/evidence/dr0/copy-record.json

The risk-lab CSVs are the same run with `--source C:/Users/Mubarak/Desktop/QMX/workroom/risk-lab-2026-10-05/data`
and its own `--target` and `--record`.

## Which comparison, and why

`--check-mode size` is the default. It runs `rclone check --size-only --one-way`, which
asks that every source file exists on the target with the same size, and then compares the
manifest it wrote with the manifest the target returns, byte for byte. The hashes in the
manifest are the source's own, so a file that changed size is caught, and the manifest
identity proves the hash list the importer will read is the hash list that landed.

`--check-mode checksum` runs a full `rclone check --checksum`. It costs one remote md5sum
per file. Measured on this tree, 257,628 small files over SFTP, the hashing leg runs at 0.2
to 0.9 MB/s, so hours. Keep it for small folders such as the risk-lab CSVs, where it was
used for the copy run of 2026-10-22.

`--copy-mode checksum` is the default and is the plan's `rclone copy --checksum`. It also
costs one remote hash per file on a rerun, so a reported rerun that must be quick uses
`--copy-mode size`, which is `rclone copy --size-only`. The first real copy uses the
checksum default.

## Tests

    uv run --no-sync python -m pytest scripts/data -q -n 2

Two tests. Both write an rclone config with one `local` remote under pytest's temp folder,
never in the repo and never with a credential. The first asserts the record's count and
bytes equal the source's and the manifest holds one line per file. The second asserts a
rerun copies zero files, writes the same record bytes, and leaves the source alone. They
skip when rclone is absent, and look for it at `QMX_RCLONE`, then `PATH`, then
`D:/Tools/rclone/rclone.exe`.

# Import the old ticks

`import_old_ticks.py` walks `/srv/qmx/data/raw-backup/` and lands both copies as typed
partitions: the 10.7 GB of old Dukascopy hour files as `dukascopy/<symbol>/ticks` and the
risk-lab one-minute CSVs as `risk-lab/<symbol>/bar-m1/<bid|ask>`. Every month goes in through
the server door's `commit`, so the door stays the only writer, and each series gets one
`dataset` card from `qmx_library.cards`.

    cd qmx-agents
    uv run --no-sync python ../scripts/data/import_old_ticks.py `
      --raw-backup-root /srv/qmx/data/raw-backup `
      --store /srv/qmx/home/market `
      --library /srv/qmx/library `
      --seal-boundary-ns <the host's [data] seal_boundary_ns> `
      --report /srv/qmx/data/dr3c-import.log

Run it as the ordinary user `qmx`, and stop the server's host for the card pass (below). The
import itself needs no host: it opens the same door the host opens, from the same root and the
same `[data]` seal boundary. It reads the raw copy and writes nothing there.

## How a month lands

DR3A's importers do the reading. `RawTicks` picks a month's hour files, `raw_tick_rows` decodes
them, `CsvBars` reads a risk-lab file, and the rows are staged as one typed Parquet file whose
path names its key, `<source>/<subject>/<kind>/<variant>/<YYYY-MM>.parquet`. The door's `commit`
then re-streams that staged file through the typed writer, so the fingerprint the store records
is computed by the door and never taken from the staged file's own claim. The run compares the
staged fingerprint with the stored one and fails the month when they differ: that is the one way
a row could change on the way in.

A risk-lab file holds a whole year, so the driver slices it by the month's window, one partition
per month. A month the source holds no row for is not committed: the report records it as an
empty month, which is how a file that stops early looks.

## Resume

A month already in the store is not read again. Its row, row count and fingerprint come from the
store's state, and the run moves on to the next month. Stopping anywhere leaves the store as the
record of what landed, so a rerun adds only the missing months and never a file twice. The JSON
report is rewritten after every month, so even a stopped run leaves the counts it reached.

## What it writes

The report at `--report` holds `months` (one row per month: series, files, rows, fingerprint,
frozen, gaps, action, seconds and the manifest verdict), `series` (one row per series: months,
source files and rows), `manifest` (the comparison) and `cards` (the item each card claimed).
It also records `months_per_minute` and, on Linux, `peak_self_mb` and `peak_child_mb`: the
driver's own peak resident memory and the largest writer child's, from `/proc/self/status`
and `RUSAGE_CHILDREN`. A platform that exposes neither records nothing rather than a guess.

## The manifest comparison

`MANIFEST.sha256` and `MANIFEST.risk-lab.sha256` sit at the raw-backup root, one
`<sha256>  <bytes>  <path>` line per copied file, with paths relative to the copied root. The
driver compares every month's hour files with the manifest's tick files for that month and fails
the run when a file is missing from the copy or is not in the manifest. For the risk-lab files
it compares each file's size with the manifest's byte count. A month that is skipped on a resume
is compared too, because the file list comes from the copy rather than from the import.

## The card pass needs the Library

The cards are written through `qmx_library.cards`, which opens the Library store as its writer.
That lock is exclusive, so the card pass cannot run while the server's host holds the Library:
stop the host for it, or rerun the same command with the same `--report` after stopping it, and
the partitions are not imported again. The run says so in its report and exits non-zero when the
Library is held.

## Tests

    cd qmx-agents
    uv run --no-sync python -m pytest ../scripts/data/test_import_old_ticks.py -q -n 2

One test. It builds two months of hour files as real LZMA `bi5` payloads with their manifest,
runs the driver on a scratch store with a scratch Library, and asserts two partitions, one card
with both months, and a second run that adds nothing and moves no fingerprint. It runs from
`qmx-agents/` because the driver imports `qmx_host` and `qmx_library`.
