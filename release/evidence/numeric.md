# Causal numeric repair evidence

Scope: NF01–NF06 in release `rc-2026-10-01`, limited to `qmf-core/chrono`,
`qmf-indicators`, and `qmf-structure`. The packet's source-only and synthetic
fixture limits remain in force; this evidence does not establish a deployed
consumer or live trading effect.

## Baseline

Command:

```sh
QMX_REPO=/workspace/QMX-release .venv/bin/python -m pytest -q -p no:cacheprovider -c pyproject.toml /workspace/qmx-audit-inputs/packets/reproductions/test_foundation_numeric_regressions.py
```

Before edits: **8 failed, 7 passed**. Failures were NF01's sparse-scatter and
window-taint cases, NF02's non-monotonic dependency time, NF03's empty interval,
NF04's reversed visible lifecycle times, NF05's mixed cascade horizon, and NF06's
foreign-instrument and reversed-order cases. Passing controls covered ordinary
SMA arithmetic/governed admission, monotonic knowledge time, nonempty interval
boundaries, valid lifecycle order and historical visibility, same-horizon cascade,
and ordered same-instrument confirmation.

## Repairs and compatibility decisions

- **NF01:** Dense provisional flags now follow the compacted input positions, and
  output evidence taint follows the formula's support. SMA/WMA use their finite
  period window; MOM/ROC depend only on the current and period-back endpoints;
  EMA/RSI and unknown kernel formulas conservatively retain the full prior prefix. A finite
  input's provisional status expires after it leaves support. Arithmetic and
  schedule/gap/not-ready output states are unchanged.
- **NF02:** Accepted non-monotonic input knowledge times remain accepted for
  compatibility. Output knowable-at is the maximum over the actual formula
  dependency support, so finite-window times may move earlier after an old
  dependency leaves, while recursive formulas retain prior dependencies. This
  avoids introducing a new admission refusal or a too-late prefix maximum.
- **NF03:** Any valid empty half-open interval now reports no overlap.
- **NF04:** At a requested read horizon, the earliest visible confirmation may
  not follow the earliest visible invalidation. An invalidation without a
  confirmation remains valid lifecycle evidence; facts beyond the horizon remain
  invisible.
- **NF05:** Both folded states must have exactly the requested `as_of` instant;
  mismatches refuse before calling the predicate. Earlier source history cannot
  be reconstructed from a folded state.
- **NF06:** All supplied observations are validated for pivot instrument and
  strictly increasing chronology before any match is returned. Price comparison
  retains exact fractions, and confirmation delay counting and earliest-match
  behavior remain unchanged for valid ordered input.

## Validation

After edits, the external desired-contract reproduction passed **15/15**. The
targeted foundation/indicator/structure command (CT-01, CT-02, CT-05, exact/time/
fingerprint examples, all indicator tests, all structure tests) passed **717/717**
before adding these in-package regressions. The combined run including the new
in-package regressions passed **743/743** after the MOM/ROC support correction. This
count overlaps the other runs and must not be added to them.
An initial combined run found an incorrect expectation in the new finite-window
test; the final passing rerun verifies that taint expires after the provisional
sample leaves the SMA support. Independent review then found that MOM/ROC depend
only on the current and period-back endpoints, not every intervening sample. Support
metadata now uses explicit dense dependency positions, with held-out actual-kernel
regressions for both formulas. The focused MOM/ROC tests passed **2/2**, and the
independent held-out probe confirmed presence [present, provisional, present] and
knowable-at [3, 100, 5] at output indices 2–4. Scoped Ruff check passed for all
modified Python source and test files.

Environment: release checkout's existing `.venv`, CPython from the locked root
environment. System Python does not have pytest installed. The shared environment
was not modified. No full workspace lint/type/release gate, provider path, Windows
run, or deployed consumer validation is claimed. The independent reviewer is updating the evidence verdict for corrective commit review.
