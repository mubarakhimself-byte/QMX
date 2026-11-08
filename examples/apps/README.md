# Example mini apps

Four small apps that show how a mini app is built on QMX's app runtime. Each folder is a whole app
definition: `app.toml`, a server, its `pyproject.toml` and its `uv.lock`. Install one with
`Supervisor(home).install(path, trust="first_party")` and start it with `start("<app id>")`, or
add it from the Apps screen.

`qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` installs every folder here and in
`qmx-agents/apps/`, starts it, calls each tool with the example input it lists, and runs each job
once. `just ci` runs that test, so an example that stops working fails the build.

## exchange-status

Records exchange status observations that you supply, and never contacts an exchange.

- `record(exchange, status, observed_at)` stores one observation in the app's database. The
  status is `operational`, `degraded`, `unavailable` or `unknown`.
- `snapshot()` lands every stored observation as a `snapshot` artifact.
- The panel shows the stored observations as a table.

## weekend-watcher

Summarises an exchange-status snapshot, for example the observations you recorded over a weekend.

- `summarize(snapshot)` takes the reference of a `snapshot` artifact. The supervisor checks the
  artifact against the app's `snapshot` feed and copies it into the app's volume first.
- It lands a `summary` artifact with one line per exchange in the order recorded, such as
  `Recorded-data fixture: binance: operational (2026-10-31T09:00:00Z); kraken: degraded
  (2026-11-01T18:30:00Z)`. The summary also carries the snapshot's `sha256`.
- The summary says it comes from recorded data, because the app never checks an exchange itself.

## macro-daily-bias

Asks one model for the day's market bias and keeps each answer.

- The daily job `daily.py` reads 50 bars with the `read_bars` tool of the MCP server at
  `data_url`, using the `qmx/control-token` credential. It sends those bars and
  `agents/analyst.md` to the OpenAI-compatible `chat/completions` endpoint at `model_url`, using
  the `qmx/cliproxy` credential, and stores the `bullish`, `bearish` or `neutral` answer.
- `bias()` lands the latest stored answer as a `bias` artifact. Before the first run it answers
  `{"status": "awaiting_data"}`.
- Settings are `config.json` in the app folder: `data_url`, `model`, `model_url`, `symbol` and
  `timeframe`. To point one installed instance at its services, write the keys you change to
  `apps/macro-daily-bias/data/config.json` in your QMX folder. The installed app folder cannot
  change without a new version.
- Under the road's `tests` and `sandbox` stages the app uses a recorded snapshot and a recorded
  answer and makes no network call.

## mql5-articles

Collects MQL5 articles into the Library on a daily schedule. Its own README explains the archive
seed and the schedule.

- `status()`, `seed_library(limit)` and `article(article_id)` work offline.
- The daily job `jobs/daily.py` fetches from `www.mql5.com` and saves through the control service
  at `127.0.0.1:8766`. The shipped-apps test skips this job for that reason.
