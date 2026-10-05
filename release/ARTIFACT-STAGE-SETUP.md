# Local artifact upload setup (draft)

A fresh daemon keeps `registry:artifact.stage_max_bytes` unset and refuses
`PUT /artifacts/stage` without writing an object. There is no adopted production
byte limit. After installing and starting the daemon with an existing corpus
configuration, the local operator selects a non-negative integer byte count:

```powershell
$env:QMA_DAEMON_ROOT = '<existing private daemon root>'
$maxUploadBytes = '<operator-selected integer byte count>'
qmb host configure artifact-stage-max-bytes $maxUploadBytes
```

The command uses the existing loopback host-control channel and current local
token. It returns the selected `max_bytes`, registry key, writer and
`journal_seq`. It records `variable.set` through the sole daemon writer.
Changes require another explicit command. Stop/start on the same root restores
the latest journaled cap without another configuration receipt. Local setup
files cannot override it. No cap field is added to `operator-config.json`.
Invalid journaled cap values cause startup refusal; they do not select a default
or silently reuse an older value. Zero permits only complete empty uploads.

Boolean, negative, fractional and string values refuse at the host-control/API
boundary. CLI arguments are parsed as integer text. Unknown targets and extra
cap fields refuse without mutation. Generic `variable.set`, pairing proofs,
agents and provider tools gain no host-control authority; the existing
pairing-TTL special restriction remains. Browser upload still requires its
paired Origin and Bearer proof and uses raw-byte HTTP PUT, not JSON-RPC stage.
At/below-cap complete bodies retain exact fp1; oversize and interrupted bodies
write no object. The cap limits one upload, not total storage or retention.

Verification uses disposable test-only 16-byte and 8-byte caps, with zero in
regression checks. These values are not deployment guidance. This packet adds
no public CT-40/schema, database schema, provider, UI, remote-access or trading
change. Focused Windows installed/runtime evidence does not certify a release.
Existing coverage, strict-docs, inherited QMB format, historical actor-deadline,
provider, connected UI, native and Linux limitations remain with their owners.
