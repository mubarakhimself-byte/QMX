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
