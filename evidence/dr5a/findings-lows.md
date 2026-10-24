# DR5A findings: lows in this PR

- DR5A: `http.answered` treats every 2xx except 200 and 206 as a failure, so a provider whose health endpoint answers 204 reads `down`. Evidence: `BR/providers/http.py` `OK = frozenset({200, 206})`.
- DR5A: the `home` pattern is lowercase only, so a Windows machine named `Trading-Server` must be typed `trading-server` in Settings or the save is refused. Evidence: `BR/models.py` `Connection.home` pattern.
- DR5A: `registry.describe` imports every built-in and every installed entry point on first use; a broken third-party adapter package raises through it instead of being skipped with a reading. Evidence: `BR/registry.py` `_builtins`.
- DR5A: `databento` and `firecrawl` probes accept `apiKey` or `api_key`, but the declarations name only `apiKey`; a keyring entry written with the other spelling works and is undocumented. Evidence: `BR/providers/databento.py`, `firecrawl.py`.
- DR5A: the template script writes `logs/connections-health.json` on every run even when nothing changed; a home with no connections gets an empty readings file. Evidence: `connections-health/scripts/health.py`.
