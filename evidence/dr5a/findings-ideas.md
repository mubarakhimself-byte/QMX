# DR5A findings: ideas

- DR5A: `registry.health(provider, connection, *, fetch=..., secret=...)` would remove the secret-resolution closure from every caller. Today the template script assembles the probe closure; the walk owns the words. One registry function would keep the secret plumbing in the package that already reads it. Evidence: `E/templates/connections-health/scripts/health.py` `resolve`.
- DR5A: persist `slowed_until` beside the heartbeat (one small JSON next to `connections-health.json`) so a host restart does not forget a provider's pacing window. Evidence: `BR/registry.py` `Slowdowns` keeps the map in memory.
- DR5A: the health walk could take the egress IP from the host heartbeat instead of a caller argument, which would make the `(provider, egress IP)` key correct when the machine changes network. Evidence: `BR/registry.py` `walk(egress_ip=...)` defaults to an empty string.
- DR5A: `qmx-broker` could publish its own entry point (`qmx.connections`) for the six data providers, so the packaged wheel declares them the same way a third-party adapter does. Today `registry._builtins()` imports the modules by name.
