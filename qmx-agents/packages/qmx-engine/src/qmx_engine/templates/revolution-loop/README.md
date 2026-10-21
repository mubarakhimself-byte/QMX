# Loop a subworkflow until the idea plateaus

The revolution loop of DC-11. The parent workflow holds one loop; its body calls a child workflow
that holds its own loop. The child runs generate, a deterministic gate and a record of the negative
results; the parent checks the plateau and reframes while a revolution still keeps a candidate.

This nesting is the one AD-5 sanctions: a loop over a `subworkflow` whose child holds a loop. A loop
inside another loop's body in one graph is still refused at validation, because the child runs in
its own ledger namespace and its prompts never read the parent's files.

## What one revolution does

1. `Brief the drafter` carries the idea, the refused candidates and the score forward on the loop's
   `next` value.
2. `Draft a candidate` asks the `builder` role for one JSON candidate.
3. `Test it against the gates` is a script, never a model: an operator word in the entry or exit, a
   stop, and an evidence line naming a source the brief was given.
4. `Record the result` keeps a refused candidate as a negative result and hands the value back to
   the attempt loop; the attempt loop stops as soon as one candidate passes.

## What the parent does

`Plateau?` stops the outer loop when a revolution kept nothing. `Assemble the loop card` writes the
card: every revolution, the kept candidate, every negative result and the plateau line.

The card carries no number in its prose that the run did not record, so the shared `Render and
grade` check passes on the evidence the scripts produced.

## Run it

Manual trigger, no schedule. Install it, then start a run with `{"idea": "..."}`. A test run with
`{"fixture": "first-pass"}` or `{"fixture": "plateau"}` replays the recorded answers.
