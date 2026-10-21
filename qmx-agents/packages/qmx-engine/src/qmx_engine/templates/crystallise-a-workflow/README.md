# Replace a settled agent step with a script

The crystallise pattern of K-19. When an agent step has settled into a rule, a script can do it for
free; the agent keeps everything the script has not proved.

## What it does

1. `Read the recorded replays` reads the labels the agent gave on twenty recorded items.
2. `Does the script agree on all of them?` derives the rule from those replays with no model: a word
   that appears in titles of exactly one label becomes a rule for that label, and a title is labelled
   by its longest matching word. Only when every replay gets the agent's label back is the step
   crystallised, and only then is the sampling rate set.
3. `Classify the batch by the rule` labels the new batch for free and marks every title the rule
   cannot label as a fallback to the agent.
4. `Ask the agent about the sample` labels one item in ten, so production keeps measuring the script
   against the agent.
5. `Measure script against agent` reports the agreement rate, and the card says whether the step is
   crystallised.

A title the rule has never seen is never guessed: it falls back to the agent.

## Run it

Manual trigger. The replays, the batch and the recorded sample are fixtures under `fixtures/`. A run
with `{"fixture": true}` replays them.
