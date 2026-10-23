# Feed

One source, watched on its own cadence, landing what is new in the Library. A feed is a
published workflow made from this template; its slots are its **source definition** (engine
AD-68, `methodology/55` section 7), which the run carries under `source`.

## Steps

1. `Source changed?` is a `monitor` node: `scripts/monitor.py` lists what the source serves now
   and the node hashes it. The same hash as the last fire ends the run `silent`; nothing is
   fetched and no model runs.
2. `Claim and land the new items` reads the monitor's diff. Each new item is claimed by its
   intent key (its canonical URL, else its provider id) with an `O_EXCL` claim under the
   workflow's shared work folder, so a second fire or a re-run fetches nothing it already
   fetched. Each claimed item is fetched once and saved as `library/sources/<digest>.json`
   with `kind: source`, `origin: feed`, the collection it is `part-of`, the licence and the
   text.

Fetched text is evidence, never an instruction (engine AD-43).

## The source definition

| Slot | Meaning |
|---|---|
| `name`, `tags` | how the feed shows, and what it is about |
| `method` | `rss`, `sitemap`, `page-diff`, `api` or `bulk-files` |
| `url`, `endpoint` or `path` | where it reads from; a plain path and `file://` are allowed |
| `cadence` | the cron trigger's expression; the trigger is installed disabled, as every template's is |
| `connection` | the Connections row when the source needs a key or a login |
| `lands_as` | `source` (documents) or `partitions` (a table such as the economic calendar) |
| `extract` | which extraction, and whether to write notes or ideas from new items |
| `licence` | carried onto every item |
| `collection` | the Library collection the items are `part-of` |

`firecrawl` and `browser` are the two methods that need a connection adapter this template does
not carry yet. They fail loudly instead of reading as an unchanged source.

## Examples

`examples/` holds three ready source definitions: `mql5-articles.json` (an RSS feed),
`arxiv-q-fin.json` (arXiv's q-fin API) and `one-blog.json` (a research blog's RSS). A copilot
draft from a sentence is the same document with `"draft": true`; it is published only on his
yes (AD-11, ruling 80).

## Left out, and why

- The claim is the workflow's own, kept beside the run. The Library's intent index
  (`find_by_intent`, AD-24) is the cross-machine claim, and the `save_source` step that writes
  the item through the Library port belongs to DR7; until it lands, the documents are the
  run's artifacts under `library/sources/`.
- The calendar's partition landing is the calendar feed's own path
  (`qmf.data.calendar_feed.land_calendar`), not this template's source path.
