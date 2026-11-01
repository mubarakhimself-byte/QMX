# qmf-calendar-indices

Index sessions and their per-index breaks as versioned data. An instrument record names one of
these by its `calendar_ref`, and the workflow engine's `market_open:<market_id>` precheck reads it
in the market's own zone.

| Calendar | Zone | Week |
| --- | --- | --- |
| `nyse@1` | America/New_York | weekdays 09:30 to 16:00, shut on the NYSE holidays |
| `us-index-cfd@1` | America/Chicago | CME's equity futures week, 17:00 to 16:00 with a daily break |
| `uk-index-cfd@1` | Europe/London | ICE's FTSE 100 futures, weekdays 01:00 to 21:00 |
| `de-index-cfd@1` | Europe/Berlin | Eurex's DAX futures, weekdays 01:10 to 22:00 |
| `jp-index-cfd@1` | Asia/Tokyo | Osaka's Nikkei 225 futures, 08:45 to 15:45 and 17:00 to 06:00 |

Holidays are full closures through 2026 and the first quarter of 2027. Early closes are not
modelled in version 1.

## The data

Each file in `src/qmf/calendar_indices/calendars/` is one `qmx.calendar/1` document named
`<calendar_ref>.json`, in the shape `qmf-calendar-cme`'s README describes: weekly `sessions` in
`zone`, local `closures`, and `issued` with `max_age_days` (31). A changed rule is a new version
file, so a record that pins the old one keeps it.
