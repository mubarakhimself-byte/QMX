"""kalman-local-level@1: the Kalman filter's level of a price that wanders as a random walk
under noise.

The local level model: the price is a level plus noise, and the level moves by its own noise.
``signal_to_noise`` is the level's noise variance over the price's, the one number the filtered
level depends on. The first price sets the level, as the exact diffuse start of statsmodels'
UnobservedComponents does; each later price moves it by the Kalman gain. A small ratio smooths
hard and lags; a large one follows the price. The first value comes at update 1.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _LocalLevel:
    __slots__ = ("_level", "_q", "_variance")

    def __init__(self, signal_to_noise: float) -> None:
        self._q = signal_to_noise
        self._level: float | None = None
        self._variance = 0.0

    @property
    def warm_up_bars(self) -> int:
        return 1

    @property
    def state_bound(self) -> int:
        return 1

    def retained(self) -> int:
        return 0 if self._level is None else 1

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        price = evidence.get("series")
        if not isinstance(price, Decimal):
            return None
        new = float(price)
        if self._level is None:
            self._level, self._variance = new, 1.0
        else:
            predicted = self._variance + self._q
            gain = predicted / (predicted + 1.0)
            self._level += gain * (new - self._level)
            self._variance = (1.0 - gain) * predicted
        return quantise(self._level)

    def export_state(self) -> Mapping[str, object]:
        level = None if self._level is None else self._level.hex()
        return {"level": level, "variance": self._variance.hex()}

    def import_state(self, state: Mapping[str, object]) -> None:
        level, variance = state.get("level"), state["variance"]
        if not isinstance(variance, str):
            raise ValueError("kalman-local-level@1 state needs variance")
        self._level = float.fromhex(level) if isinstance(level, str) else None
        self._variance = float.fromhex(variance)


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _LocalLevel:
        ratio = float(params["signal_to_noise"])
        if ratio <= 0:
            raise ValueError("kalman-local-level@1 signal_to_noise must be above 0")
        return _LocalLevel(ratio)


BLOCK = _Block()
