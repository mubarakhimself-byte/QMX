# The interview

Three things, three questions at most, each with the answer you recommend. He answers "yes" and
you have all of them. Never send this list whole; pick the two or three that his line leaves
open, and leave out anything it already answers.

## Trigger

Ask only when his line names no time and no event.

- "Does this run on a clock, or when you click run?" Recommended: the clock he implied, plus
  manual, so he can try it once.
- "Which days, and at what hour, in your timezone?" Recommended: weekdays at the hour he named,
  else 07:00 Europe/Berlin.
- "What should wake it when it is not a clock?" Recommended: the source's change, as a `monitor`.

A cron goes in the trigger node's name and in your message. The row that arms it is his enable
card, never your act.

## Checkpoints, pushed as late as possible

The default is none: a run does not stop for him (ruling 57). Ask only when the workflow touches
something that cannot be undone, and then push the checkpoint to the last node before it.

- "Should it stop and show you the draft before it sends anything?" Recommended: no, unless the
  last node is an external send, a post or a trade.
- "If it fails halfway, should it park or retry?" Recommended: park, and tell him in one line
  where it stopped.

A checkpoint is a `wait` node or a `grader` with `fail` wired to a `wait`. It costs his attention,
so it is never a default.

## Brief

Write the brief yourself from his line and show it in one sentence at the end. Ask only when the
result is ambiguous.

- "Where does the result go: the Library, a file, or a message to you?" Recommended: the Library,
  as the run's output, unless he named a channel.
- "Is one paragraph the answer, or a table?" Recommended: the shape his sentence implies.

## Writing the questions

Numbered, each with the recommended answer first, each in his vocabulary rather than the graph's.
"Should the digest be saved in the Library with the rest of your notes?" beats "confirm the
outputs block". If he says "yes", take every recommendation and build. If he corrects one, build
with his correction and leave the rest.
