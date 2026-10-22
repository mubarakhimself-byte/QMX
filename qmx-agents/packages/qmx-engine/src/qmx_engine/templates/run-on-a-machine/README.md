# Run one job on his server

A one-node workflow for a job whose node is placed away from the PC. The `script` node names
`runs_on: contabo`, so the engine's remote `WorkerPort` adapter ships the attempt to that machine,
the run sidecar executes it there, and its outputs come back by hash.

It is the shape AD-57 gives a placed CPU or GPU job: a `script` or `agent` node with `runs_on` and
`resources`, started as a test or live run, landing as a `workflow-run` beside every other run.

## Steps

1. `On request` is the manual trigger, so nothing fires until he asks.
2. `Run the job on its placement` (`scripts/run.py`) runs the argv in `inputs.command` on the placed
   machine and answers with the exit code and the tails of stdout and stderr.

## Left out, and why

- A GPU placement: no paid GPU machine exists (E57 records `not run, no paid GPU placement`).
- The job's own definition, data and credentials: they travel in the same bundle as the attempt,
  so the template carries none of them.
- A provider row for a machine he has not added: the template names `contabo`, the one placement
  the server phase has.
