# Weekly backup

The backup plan of D-11 as one engine run. Every Monday the workflow snapshots the small stores in the home to the private Git repository in Settings, verifies each copied database, and commits it. The control plane's maintenance loop used to call this function and record a `jobs` row; the loop and the `jobs` kind are gone.

## Steps

1. `Snapshot the small stores` reads `backup.repository` from the home's Settings. A home without one records `not_configured` and ends; nothing else runs. It clones the repository, copies the databases, the settings and the definitions the backup plan names, and checks each database with `PRAGMA integrity_check` before committing and pushing. A file over 95 MB fails the step rather than publishing a partial snapshot.

A failed snapshot files one incident with the signature `maintenance:backup` in the home's inbox and fails the step, so the run's failure and the incident name the same step. A passing one resolves nothing it did not open.

## Cadence

Mondays at 06:00 UTC (Claude's default). The catalogue row installs the cron trigger disabled, as every row does, and it stays editable in Settings. The seven-day gate the loop's function held is still there: a manual fire inside the week returns `not_due` and publishes nothing.

## Test runs

A run started with `{"dry_run": true}` exercises the whole job against a local bare Git repository and pushes nothing. Pointing `backup.repository` at a local bare repository takes the same path, because that is the only local form `weekly_backup` accepts; the private GitHub form `owner/private-repo` publishes.

## Left out, and why

- A recorded fixture and an `--fake` switch: no model call is involved, so there is nothing to record.
- Restore: a snapshot is only half the plan, but restoring a home is DR2D's flip and procedure, not this row's.
