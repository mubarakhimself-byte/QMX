Write the morning digest from what ran and what landed since his last look.

Reply with one JSON document:

- `opening`: one line on what the morning is about.
- `landed`: at most eight lines, each `{"text", "object_id"}` for an item in `landed`, in the order
  that matters most.
- `moved`: at most five lines on which hypotheses moved, each naming the item it reads.
- `needs_you`: at most five lines on what failed and needs a decision, each `{"text", "run_id"}`,
  taken only from `failed`.
- `quiet`: true when nothing landed and nothing failed.

Use only what the brief gives you. Use no numerals at all in any line: the counts are on the card
beside your text, and a number you write is a number nothing backs.
