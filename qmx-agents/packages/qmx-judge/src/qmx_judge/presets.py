"""The judge's presets: the pass numbers a study spec names, each with where it came from
(Part B `judge.md` §3 and §6). A preset is data. Nothing overrides a shipped default silently: a
study spec names its preset, and the verdict records which one judged it.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

__all__ = ["DEFAULT_PRESET", "PRESETS", "Preset", "preset"]


@dataclass(frozen=True, slots=True)
class Preset:
    name: str
    origin: str
    min_trades: int
    """The record a market needs before it is judged; below it the market is too thin."""
    walk_forward_efficiency: Decimal
    """Validation Sharpe over in-sample Sharpe, at least this."""
    monte_carlo_p5_above: Decimal
    """The 5th percentile of total R over bootstrapped trade orders is above this."""
    cost_stress: Decimal
    """The cost multiplier the edge must survive."""
    deflated_sharpe: Decimal
    """The deflated Sharpe confidence, with the family's effective tries."""
    min_expectancy_r: Decimal
    """The shrunk expectancy per trade, in R after costs, is above this."""
    signal_p: Decimal = Decimal("0.05")
    """The signal against random entries is significant at this level."""
    entry_edge_ratio_min: Decimal = Decimal("1.0")
    pbo_pass: Decimal | None = None
    """When set, the family's probability of backtest overfitting is below this to pass."""
    pbo_dead: Decimal | None = None


PRESETS: Final[dict[str, Preset]] = {
    preset.name: preset
    for preset in (
        Preset(
            name="shipped",
            origin="the shipped b-build-and-prove template (scripts/gates.py)",
            min_trades=100,
            walk_forward_efficiency=Decimal("0.5"),
            monte_carlo_p5_above=Decimal(0),
            cost_stress=Decimal("1.5"),
            deflated_sharpe=Decimal("0.95"),
            min_expectancy_r=Decimal(0),
        ),
        Preset(
            name="old-qmx",
            origin="old QMX's pass numbers (research 08 section 1.1)",
            min_trades=200,
            walk_forward_efficiency=Decimal("0.5"),
            monte_carlo_p5_above=Decimal(0),
            cost_stress=Decimal(2),
            deflated_sharpe=Decimal("0.95"),
            min_expectancy_r=Decimal("0.15"),
            pbo_pass=Decimal("0.25"),
            pbo_dead=Decimal("0.50"),
        ),
    )
}

DEFAULT_PRESET: Final = "shipped"


def preset(name: str) -> Preset:
    found = PRESETS.get(name)
    if found is None:
        raise ValueError(f"no preset {name!r}; the presets are {', '.join(sorted(PRESETS))}")
    return found
