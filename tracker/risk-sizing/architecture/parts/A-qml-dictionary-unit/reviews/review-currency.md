# Review: currency lens (configured reviewer 1)

Part A, 31 Oct 2026. The `bmad-architecture` configured lens: was every committed technology reality-checked rather than asserted from memory? Run in sequence by the part's author; the reviewer gate's sub-agent dispatch is barred by the brief.

**Verdict.** Every pinned version was read from the running environment and the lockfile this session; no version is asserted from memory. This part adds no dependency.

| Name | Version | How it was checked |
| --- | --- | --- |
| Python | 3.14.6 | `sys.version` in the export's environments (`scratchpad\eb\.venv`, `eb\qmx-agents\.venv`); QML requires `>=3.14,<3.15` (`qml/pyproject.toml`, G1 §1.1) |
| TA-Lib | 0.7.1 | `importlib.metadata.version("ta-lib")` in the QMF environment; pinned in `packages/qmf-indicators/pyproject.toml` |
| jsonschema | 4.26.0 | the agents environment and `qmx-agents/uv.lock:1876-1877`; used only by the Library |
| pyarrow | 25.0.1 | the agents environment and `qmx-agents/uv.lock:3238-3239` |
| fastmcp | 4.0.11 | the agents environment and `qmx-agents/uv.lock:1113-1114`; the BR-A2 run found its rule that tools may not take `**kwargs` |
| claude-agent-sdk | 0.2.166 | the agents environment; the hook's behaviour under it is unproven and gets a probe (slice A14) |

**Facts that could age.** Plugin hooks under the Agent SDK (probe first, AD-117). The `additionalContext` behaviour of PostToolUse hooks was checked by the grounding (G2 §2.1 against the SDK's hooks page); the probe rechecks it on QMX's launch path.
