"""The RLM step (card R8 steps 1 and 2): mount the data handles read-only in a fresh research
sandbox, then the `rlm-root` model writes Python against the data as variables and fans sub-calls
out to the cheap `rlm-sub` role through QMX's provider layer. The kernel snapshots after each cell
and caches sub-call results by (model, prompt hash); its budget (children, tokens, dollars, wall
clock) is read by the kernel. No network except the data store; no live or Portfolio path.

Its output is `findings` (each `id`, `claim`, `value`, and the `cells` that produced it), `cells`,
`snapshot`, `sub_call_log` and `cost_usd`. Until the `rlm` node kind and its kernel exist this
template stays a draft (`needs: rlm`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the rlm node kind and its research kernel (needs: rlm)")
raise SystemExit(1)
