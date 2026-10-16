# Currency lens — was every committed decision reality-checked rather than asserted?

Verdict: **pass; nothing out of date was found, one [remembered] item is labelled.**

| Decision | Source | Status |
| --- | --- | --- |
| Python 3.14, pydantic 2.13.4, fastapi 0.142.2 | engine spine Stack table, ratified from `qma/hp17` pyproject [retrieved] | current for this workspace |
| @xyflow/svelte 1.6.6, codemirror 6.0.2, @codemirror/lang-python 6.2.1, svelte 5.57.1 | `QMX-worktrees/ui-review-repair/apps/qmx-ui/package.json` [retrieved this run] | the UI's own pins |
| QMB door today = `run_backtest(config_ref)` only; `qmb.doors.mcp` refuses to serve | `qmx_tools/service.py`, `qmb/doors/mcp/__init__.py` on `qma/hp17` [retrieved] | confirmed |
| `qmb.config.compile_run_config` layer order and dummy refusal | `qmb/config/compiler.py` [retrieved] | confirmed |
| `qmx_remote` providers ssh / amp / modal / e2b; RunBundle shape | `qmx_remote/models.py`, `providers.py` [retrieved] | confirmed; Colab absent, hence deferred |
| CT-46 environment kinds, CT-47 occupancy, CT-12 split roles, CT-22/CT-27 sections, CT-28 binding states | `docs/contracts/*.yaml` [retrieved] | confirmed |
| TN-9 node-paper, TN-19 MIS seam, TN-20 two-click promotion | `docs/components/trading-node.md` [retrieved] | confirmed |
| Deflated Sharpe over all trials | [remembered] (Bailey and López de Prado); the spine binds only that it is computed over every trial in the family, not a formula | labelled; the template's script owns the formula |
| Screens and their fields | shots 01-35 (previous run) and 36-58 (this run) [retrieved] | the requirement source after the operator's correction; UI code and demo arrays were read only for which kinds of things exist |

No web check was needed because the spine binds no technology the parents had not already verified. The one external name mentioned in text (Colab) is a placement the design defers, not a dependency.
