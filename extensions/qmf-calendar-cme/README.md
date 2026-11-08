# qmf-calendar-cme

CME Globex calendars as versioned data. An instrument record names one of these by its
`calendar_ref`, and the workflow engine's `market_open:<market_id>` precheck reads it in the
market's own zone.

| Calendar | Zone | Week |
| --- | --- | --- |
| `cme-equity@1`, `cme-metals@1`, `cme-energy@1`, `cme-fx@1`, `cme-rates@1`, `cme-crypto@1` | America/Chicago | Sunday to Friday, 17:00 to 16:00, a daily break 16:00 to 17:00 |
| `cme-grains@1` | America/Chicago | Sunday to Friday, 19:00 to 07:45 and 08:30 to 13:20 |
| `metals-24x5@1` | America/New_York | spot gold and silver CFDs on COMEX's week, 18:00 to 17:00 |

Christmas Day and New Year's Day are full closures. `metals-24x5@1` also lists the early halt on
Martin Luther King Jr. Day and Presidents' Day in 2025 and 2026 (14:30 to 18:00 New York). Other
early closes are not modelled in version 1. Dated closures are data inside a version: they are
added in place, and `issued` dates them.

## The data

Each file in `src/qmf/calendar_cme/calendars/` is one `qmx.calendar/1` document named
`<calendar_ref>.json`:

- `sessions` are weekly spans, `"<day> HH:MM"` in `zone`, a close on a later day running over
  midnight.
- `closures` are local `from` and `to` times that shut the market whatever the sessions say.
- `issued` and `max_age_days` (31) date the data. Past that age the engine still applies it and
  says how stale it is.

Instants stay in UTC. Only the rule reads local time, so a session keeps its local hour across
every daylight-saving change, including the weeks when Chicago, New York and London differ.

A changed rule is a new version: copy the file to `<id>@<n+1>.json` and change that copy. Records
that pin the old version keep it.
