# Turn new clippings into linked research

The clippings intake of K-31. A watched folder is read hourly, every clipping gets a content hash and
an intent key computed with no model, and the Library's own `find_by_intent` decides what is new.
The same clipping fed twice runs once: the second run links to what already holds it.

## What it does

1. `Read the clippings` hashes each clipping's bytes and fingerprints `clipping | hash | source` into
   its intent key (AD-27).
2. `Dedupe by hash and intent key` asks the Library which keys it already holds.
3. `Summarise the new ones` asks the `reader` role for a note and a testable hypothesis per new
   clipping.
4. `Land and link them` stores each new clipping once under its intent key, and links a clipping
   already held to the object that holds it (`consumed`), so nothing is stored twice and nothing is
   deleted.

## Run it

Interval trigger, one hour. Set the `folder` input to the clippings folder, or a test run with
`{"fixture": true}` replays `fixtures/clippings.json`.

Installing the template only suggests the schedule; enabling it is yours.
