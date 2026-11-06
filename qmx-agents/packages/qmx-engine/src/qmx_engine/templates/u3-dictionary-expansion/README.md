# Expand the dictionary from a source

A source in, its concepts out: each sentence matched to the entry it states, an append request for each one no entry states, and entry drafts that pass the checker. Nothing publishes. Part A `4-dictionary.md` section 5, ruling 13, and the plan's Appendix F.

## Steps

1. `Match each sentence` (`scripts/match.py`) runs QML's matcher over every sentence. Each unmatched sentence lands as one `append-request` artifact on the run's own ref, never as a silent new entry.
2. `Quote the source as data` (the shared `marked-sources` block, carried in `marked-sources/`) quotes the source and its unmatched sentences, so a page that says "ignore your instructions" reaches the agent step only as data.
3. `Draft the new entries` (role `extractor`, toolset `blocks`) drafts an entry for each append request under Appendix F's directions: ground first, no cap, cite with a quote under 15 words and a date, role-neutral, data honest, never type a status, code only where QMX's data can feed it. It checks each draft with `blocks_check`, and names an entry it finds already holds a sentence under `already_held`.
4. `Check every draft` (`scripts/check.py`) runs QML's entry checker and the corpus check on each draft. Only a draft that passes lands, as an `entry-draft` artifact with its computed status and fingerprint. A draft that fails lands nothing and is listed with every problem.

## Left out, and why

- Saving a draft as a `component` item: a script lands artifacts only, and the `component` kind lands through the Library's put. He saves a draft he wants from the run's ref.
- The Library's own entries in the match: a script reads QML's entries only, so a sentence only a Library-held entry states files an append request; the drafting step finds it with `blocks_match` and lists it under `already_held`.
