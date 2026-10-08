# Remote runs

The laptop submits a hashed bundle and keeps a durable provider handle. A worker
on the target runs the workflow, app tool, agent or command and flushes its journal,
logs, traces, outputs and SQLite checkpoints every five seconds. It continues
without the laptop. Workflow steps also trigger a flush. A failed upload fails
the run; it never silently drops evidence.

## Settings

Use `settings_put("remote", ...)` through REST or MCP. For an own VPS:

```toml
[remote]
default_target = "vps"
bucket = "vps:/srv/qmx/bucket"

[remote.targets.vps]
provider = "ssh"
host = "qmx-vps"
root = "/srv/qmx/bucket"
image = "qmx-remote:<tested-revision>"
gpu = 0
```

`vps` is a named rclone SFTP remote, configured with SSH key authentication;
`qmx-vps` is an OpenSSH host alias with its host key already trusted. `root` must
be the same directory as the SFTP bucket. The container sees it as `/bucket`.
Configure a named rclone S3 remote instead to use optional S3 storage. Tests use
a local directory with the same layout and atomic file replacements.
For another SSH node (for example a GPU machine) set `bucket_local=false`;
its worker reaches the primary bucket through rclone with scoped access instead
of mounting a directory on that machine as if it were the primary bucket.

The worker image uses the P17 pinned Python/uv base and includes this package and
its frozen dependencies. The package Dockerfile is built from the repository
root. Its Dockerfile-specific ignore file excludes environments, caches and
runtime data. Builds and real node provisioning are operator tasks. No image
build is needed for the fake-provider test suite.

For optional Modal/E2B control clients, install the corresponding `qmx-control`
extra (`remote-modal` or `remote-e2b`). A Modal target's `image` is the prebuilt
worker image; E2B's is a prebuilt template containing the worker and rclone.
Configure the named rclone remote on those targets too, or supply rclone's
documented environment configuration through scoped credentials. Modal reads
`qmx/modal-token-id` and `qmx/modal-token-secret` from the control host's vault on
each operation; E2B reads `qmx/e2b`. These account credentials are separate from
the scoped credentials injected into a job.

Targets advertise `gpu` counts from the P17 node bootstrap. A bundle requests
`resources.gpu`; an explicit CPU target refuses GPU work. Without an explicit
target, placement chooses the first configured node/provider with enough GPUs.
Modal GPU targets also set `gpu_type`, e.g. `A10`. E2B is CPU-only here.

## Bundles and operations

`RunBundle.definition_hash` is SHA256 of canonical JSON
`{"definition": <definition>, "files": <relative-path-to-sha256 map>}` using the
P08 journal encoder. `files` are copied from `definition_path`, verified on both
ends and loaded into the worker's definition directory. Workflows carry a P10
graph in `definition`; agents include `agent.yaml`; apps include their manifest,
code and lockfile. App inputs name a `tool` and its `arguments`. Jobs supply a
command argument list and write additional results under `QMX_REMOTE_OUTPUT`.

`model_profile` is the resolved P06 router configuration, including the server
proxy URL. `credentials_scope` maps environment names to `qmx/*` vault references.
The submitter resolves only those references; SSH sends values on stdin and
Docker receives environment names, never literal credentials in argv. Workers
redact those values from logs and results, clear their environment at exit, and
the provider removes the container/sandbox at teardown. Status observes final
manifests and releases finished resources; stop releases them immediately.

REST and MCP share `runs_start_remote`, `runs_status`, `runs_logs`, `runs_fetch`,
`runs_resume`, `runs_stop`. Job tools are `run_job`, `job_status`, `job_logs`,
`job_fetch`. Submission records placement in the existing run index and emits
platform events. Fetch validates every file before registering output references
in the Library and appending a P08 journal record.

Results live under `runs/<id>/manifest.json` and `artifacts/<sha256>`.
The manifest gives each blob its logical name (`journal.jsonl`, `logs/*`,
`traces/*`, `checkpoints/latest.db`, `outputs/*`), size and hash. Every flush
uploads immutable blobs first and commits the manifest last. An interrupted
flush leaves the previous complete manifest usable. SQLite checkpoints use
the online backup API to include committed WAL content.

Resume verifies the last checkpoint, keeps the workflow thread/run identity,
releases the old target and launches a fresh worker on the selected target.
Running/completed runs and runs without a verified checkpoint cannot resume.
Approval gates require an operator decision and are not automatically approved.

## Amp

An Amp target uses `provider="amp"`, an SSH worker host/image, and
`executor="orb"` with `project`, or `executor="runner"` with `runner_id` and an
optional absolute `runner_dir`. The durable SDK consumer runs on the VPS so
both the task and incremental result capture survive a laptop disconnect.
Install the pinned `qmx-remote[amp]` extra and Amp CLI on that worker image.

Configure QMX MCP endpoints and their auth in the Amp project or runner settings.
The remote SDK ignores `mcp_config`, `skills` and `enabled_tools`; this adapter
does not pass them. The worker records the Amp session ID and SDK event stream.
Stopping QMX stops its consumer; the fetched SDK docs expose no remote-thread
cancel API. Stop the Amp thread in Amp too when cancelling delegated work.

For code tasks, include `code.repository` (HTTPS without embedded credentials)
and an exact 40-character `code.revision`. The worker creates an isolated clone
on `runs/<run_id>`, refuses publication if that branch changed, and pushes only
`HEAD:refs/heads/runs/<run_id>`. Amp code tasks require a runner on the same VPS
with the bucket's `code/<run_id>` directory served and writable by the worker.
Orb code publication is unavailable until its remote Git policy is verified.

## Server model proxy and operator smoke

CLIProxy's Docker config uses `config-version: 8`, `server.port: 8317`,
`access.api-keys`, `oauth.auth-dir` and `management.secret-key`. Keep its config
and auth directory in the node vault, mount them into `eceasy/cli-proxy-api`,
and expose it only on the node's private network. Pass its private URL through
`model_profile.providers.cliproxy.base_url` and its key through a scoped
`qmx/cliproxy` reference. Use `/v1` for OpenAI and the host root for Anthropic;
the P06 router resolves that distinction. Subscription login and prompt-cloak
checks remain operator-only live commands.

On the server, follow the official CLIProxy Docker Compose setup: clone
`https://github.com/router-for-me/CLIProxyAPI.git`, copy `config.example.yaml`
to `config.yaml`, configure the private listener and vault-backed mounts above,
then run `docker compose up -d` using its prebuilt image. Subscription login is
`docker compose exec cli-proxy-api /CLIProxyAPI/CLIProxyAPI -no-browser --codex-login`
(or `--claude-login`). These commands require the operator's server and live
credentials and are not part of the packet tests.

Run `scripts/live/smoke_remote.py` using the `qmx-control` environment. Start with
`--home <configured-home> --bundle <bundle.json> --target vps`; later use
`--action status|logs|fetch|resume|stop --run-id <id>`. This is intentionally not
part of CI. Daytona's SDK docs were read, but the packet's implementation order
ends at E2B; no speculative Daytona adapter is registered.
