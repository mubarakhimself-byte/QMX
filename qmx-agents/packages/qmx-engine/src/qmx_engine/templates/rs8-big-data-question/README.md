# Answer a question over a large table

Waits for the `rlm` node kind and its research kernel (`needs: rlm`).

Built from card R8 (big-data question, RLM kernel) in `research/methodology/15-templates-researcher.md`. It answers questions like "across 3 years of ticks on 40 symbols, where does strategy X break?" without pasting data into a model's context: a root model writes code against the data in a sandboxed kernel, and only findings a script reproduces from the kernel's snapshot are reported.

## Steps

1. `Estimate sub-calls and cost` (zero tokens) sizes every data handle and estimates sub-calls and dollars before any model call.
2. `Within his ask-above number?` ends the run with a cost card, and no spend, above his number or when a handle does not resolve.
3. `Root model in the research kernel` (`scripts/kernel.py`) is the `rlm` step: data mounted read-only, the root writes code and fans out cheap sub-calls, the kernel snapshots each cell and caches sub-calls.
4. `Reproduce from the snapshot` (`scripts/reproduce.py`) re-runs, by script and with no model, the cells behind each finding.
5. `Keep reproduced findings` reports a finding only when the re-run gives the same number, and checks the evidence pack holds the cells, the sub-call log and the cost.
6. `Write the explainer` (role `writer`) answers from the reproduced findings only; `Render and grade` checks its numbers against the estimate, the kernel run and the re-run.

## Left out, and why

- The `rlm` node itself: the kind is unavailable until its packet, so the root and the re-run are the two kernel calls named above. When it lands, step 3 becomes an `rlm` node with the `rlm-root` and `rlm-sub` roles.
- R7 calibrate over the kernel's reruns: it joins when the kernel exists.
- Writing regime breaks as Library knowledge rows linked to the strategy: it needs the real Library.
- The heat map or regime map: drawing is UI-side; the result carries the numbers.
- The approve-spend step: it ends as the cost card, because `human_gate` is unavailable.
