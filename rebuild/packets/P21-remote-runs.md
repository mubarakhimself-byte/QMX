# P21: Remote runs (laptop off, Git-style results)

## Goal
From `qmx-control` (later the UI), send a workflow, app or agent run to a remote target. It keeps working with the laptop off, and QMX recovers every result, log and trace afterwards.

## Read first
- `rebuild/DESIGN.md` §11b, §7.5–7.7 and §8
- Amp docs: https://ampcode.com/docs/orbs, https://ampcode.com/docs/sdk, https://ampcode.com/docs/cli/runners
- The Modal, E2B and Daytona Python SDK docs

## Build (package `qmx_remote`)
0. **The own VPS is the default** (DESIGN §11b). The primary bucket is a directory on the VPS reached by rclone over SFTP; S3-compatible stores are optional. GPU: the node advertises its GPU (from P17 bootstrap), jobs declare `resources: {gpu: N}`, and the placement logic picks a GPU node or a configured GPU provider. Agents get `run_job`, `job_status`, `job_logs` and `job_fetch` tools (DESIGN §5.6b).
1. **`ComputeProvider` interface:** `provision`, `start`, `status`, `logs`, `stop`, `teardown`, plus a registry chosen in settings. Implement in this order:
   1. `ssh` (own VPS, using the P17 Docker image)
   2. `amp` (remote agent: Amp Python SDK `execute` with `executor="orb"` or `"runner"`, and `mcpConfig` pointing at QMX's MCP servers)
   3. `modal`
   4. `e2b`
   Add each after the previous one passes.
2. **Run bundle:** the app or workflow definition hash, inputs, model profile, and a credentials scope (references only).
3. **Results store:**
   - `s3://<bucket>/runs/<run_id>/`: `manifest.json` (inputs, versions, status, artifact list with sha256), `artifacts/<sha256>`, `journal.jsonl`, `logs/`, `traces/`, `checkpoints/`.
   - Upload incrementally while running.
   - Use any S3-compatible store; the bucket is set in settings.
4. **`fetch(run_id)`:** download, verify hashes, register artifacts in the Library or app volume, append a journal record.
5. **`resume(run_id, target)`:** restart from the last LangGraph checkpoint in the bucket.
6. **Code changes** from remote agents are pushed to branch `runs/<run_id>`, never to working branches.
7. **CLIProxy on the server:** document the Docker setup and pass the proxy URL to the run. Credentials are injected per run and removed at teardown.
8. **`qmx-control` operations:** `runs.start_remote`, `runs.status`, `runs.logs`, `runs.fetch`, `runs.resume`, `runs.stop`.

## Tests
- A fake provider covers the full lifecycle.
- A manifest and hash mismatch is detected.
- Resume works from a checkpoint.
- Incremental upload survives a killed run (local-folder S3 stand-in, e.g. MinIO or moto).
- The Amp adapter is tested with a stubbed SDK. A real orb or VPS run goes in `scripts/live/` for the operator.

## Depends on
P10 (workflows), P12 (apps), P13 (backup and bucket), P17 (Docker image).
