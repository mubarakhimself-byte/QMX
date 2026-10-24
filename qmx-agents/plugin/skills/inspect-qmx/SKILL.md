---
name: inspect-qmx
description: Look into a running QMX from outside with an observer token. Use when asked to inspect QMX, read its data health, read a run's trace, or leave the operator a diagnosis note.
allowed-tools: Bash(curl:*)
---

# Inspect QMX

You are outside QMX, looking in. The operator gave you an observer token: four reads and one
write. Nothing else on the door answers you, and a refusal is final.

## The door

- `$QMX_DOOR` is the operator's control door, such as `http://100.64.0.2:8766` over the tailnet.
- Every call carries the token, and the token never prints. Not in a command you show, not in a
  file, not in a URL, not in your answer. The shell expands it:

```bash
curl -s -H "Authorization: Bearer $QMX_OBSERVER_TOKEN" "$QMX_DOOR/api/doctor"
```

- The token reaches the `ops` rows and the doctor. A broker row, a Library content row, a
  workflow, a settings write and everything else answer 403 with
  `{"error": {"code": "observer_refused", ...}}`. Do not retry a refusal and do not look for a
  second way in.

## Read 1: the doctor

`GET $QMX_DOOR/api/doctor` lists setup checks, one line per fact, each with its state and what to
do when it is refused. Read this first: it says whether the door, the vault, the Library and the
providers are as the machine thinks.

## Read 2: the data health

`GET $QMX_DOOR/api/ops/health` is one document of facts, and an absent file is reported absent,
never as a zero:

- `hosts`: each machine's newest heartbeat row. `free_disk_bytes` and `disk_floor_bytes` say how
  much room is left and what the machine keeps for itself; `library` carries the outbox length and
  sync lag; `lab` carries open projects, kernels and runs when a Lab backend writes them.
- `cards`: one row per price-series card on the Library's main line, with its coverage
  (`months`, `last_month`), its `quality` note and `age_s` since the card was written. A card
  whose coverage stops before the month you expect is the freshness problem.
- `feeds`: each feed and downloader with its last run, when DR6's feed file exists.
  `present: false` means no feed has written one yet.
- `connections`: the health walk's newest reading per external connection: `word` (`ok`, `slowed`,
  `maintenance`, `needs_you`, `down`), `latency_ms`, `clock_offset_ms` and when it was read.
- `telemetry`: the QMX exporter's counters. `sent`, `dropped`, `failed`, `last_error` and
  `held` say whether records reached the server's collector; `dropped` above zero is the answer.
- `bucket`: the bucket remote the server names, how many copies the Library has, and `said`. The
  collector's own queue and drop counters are on the server's `127.0.0.1:8888/metrics` and are not
  in this file.

## Read 3: a run's trace

The door serves one run at a time: `GET $QMX_DOOR/api/ops/spans/{run_id}`. The run id comes from
the operator or from OpenObserve. QMX's trace id is derived from it, `sha256(run_id)[:32]`, so the
same run is one trace in both places.

Each span carries `qmx.node_id`, `qmx.attempt`, `qmx.status`, `qmx.duration_ms`, the model and
usage under the pinned GenAI names (`gen_ai.system`, `gen_ai.request.model`,
`gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`), and `qmx.redactions` for the values the
redaction seam masked. A failed attempt carries `qmx.error_signature`, which is what the inbox item
is keyed by.

Logs are not on this door. The same collector sends them to OpenObserve, the operator's viewer
(`http://<server>:5080`, a 14-day window), where a run's trace and its log lines are one search by
`run_id` or `trace_id`.

## Read 4: what is running

`GET $QMX_DOOR/api/aggregates`, `GET $QMX_DOOR/api/sessions` and
`GET $QMX_DOOR/api/ops/spans/{run_id}` are the `ops` rows' reads. Every other route refuses.

## The one write: a diagnosis note

`POST $QMX_DOOR/api/ops/notes` with `{"body": "<what you checked and what you found>"}`. The door
writes it on your own observer ref, `refs/agents/<your observer id>/diagnosis`, and the operator's
inbox shows one `info` item: "an outside agent left a diagnosis". It is the only write the token
has, and one note per inspection is enough. A note is not a place for a credential, a path or a
copy of a record: write what you observed and where you saw it.

## If the door says no

- `401 unauthorized`: the token is missing, expired or revoked. Ask the operator to mint one in
  Settings, and never reuse an old one.
- `403 observer_refused`: the row is outside the token's list. Say what you wanted and stop; do
  not retry, guess a path, or ask for the full-control token.

## What you never do

- Never read, copy or print a provider key, a broker credential, a vault value or a Library item's
  content. None of them is on your door.
- Never look at an account, a position or an order. No observer row reads one.
- Never write anything but the note, and never change a setting.
