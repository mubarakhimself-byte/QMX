"""Pinned V1 execution adapters bound by adapter-id (B-6, Story 17.1).

Fill, slippage, and cost are SEPARATE adapters. Calibration *content* (spread
tables, slip parameters, commission rates, swap points) stays deferred to
GAP-0048 — these adapters invent no numbers. The ``zero`` slippage and cost
shapes are the named catalog entries from SLIP-2 / FEE-2, never a silent default.
The financing scheduler is bound from a schedule reference plus an optional
swap-table calibration (FEE-4).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from qmf.core.chrono import Duration
from qmf.core.exact import ExactRational, Money, UnitKind
from qmf.core.refusal import Ok, Result, is_refusal

from qmb._refuse import invalid
from qmb.execution.cost import (
    COST_ADAPTER_CATALOG,
    COST_ADAPTER_NOTIONAL_MINIMUM,
    COST_ADAPTER_PER_LOT,
    COST_ADAPTER_PERCENT_OF_NOTIONAL,
    COST_ADAPTER_ZERO,
    COST_CALIBRATION_KEY,
    COST_MODELS,
    CommissionCalibration,
    NotionalProportionalMinimumCostAdapter,
    PercentOfNotionalCostAdapter,
    PerLotCostAdapter,
    ZeroCostAdapter,
)
from qmb.execution.fidelity import FidelityIdentity, stamp_fidelity
from qmb.execution.fill import (
    FILL_BASES,
    FILL_BASIS_WORST_CASE,
    cross_declared_path,
)
from qmb.execution.financing import (
    FINANCING_ADAPTER_SCHEDULED,
    FINANCING_CALIBRATION_KEY,
    FinancingScheduler,
)
from qmb.execution.ports import (
    COMPOSITION_VERSION,
    TAINT_OPTIMISTIC,
    AuthorizedIntent,
    Fill,
    FillPort,
    NoFill,
    PartialFill,
    SlicePath,
    SlippagePort,
    require_authorized_intent,
)
from qmb.execution.slippage import (
    SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
    SLIPPAGE_ADAPTER_GAP_VOLATILITY,
    SLIPPAGE_ADAPTER_SIZE_TIERED,
    SLIPPAGE_ADAPTER_SPREAD_CROSSING,
    SLIPPAGE_ADAPTER_ZERO,
    ConstantPercentSlippageAdapter,
    GapVolatilitySlippageAdapter,
    SizeTieredSlippageAdapter,
    SlippageCalibration,
    SpreadCrossingSlippageAdapter,
    ZeroSlippageAdapter,
)

__all__ = [
    "AMBIENT_DISCOVERY",
    "COST_ADAPTER_CATALOG",
    "COST_ADAPTER_NOTIONAL_MINIMUM",
    "COST_ADAPTER_PERCENT_OF_NOTIONAL",
    "COST_ADAPTER_PER_LOT",
    "COST_ADAPTER_ZERO",
    "COST_CALIBRATION_KEY",
    "COST_MODELS",
    "FILL_ADAPTER_CATALOG",
    "FILL_ADAPTER_DECLARED_PATH",
    "FINANCING_ADAPTER_SCHEDULED",
    "FINANCING_CALIBRATION_KEY",
    "SLIPPAGE_ADAPTER_CATALOG",
    "SLIPPAGE_ADAPTER_CONSTANT_PERCENT",
    "SLIPPAGE_ADAPTER_GAP_VOLATILITY",
    "SLIPPAGE_ADAPTER_SIZE_TIERED",
    "SLIPPAGE_ADAPTER_SPREAD_CROSSING",
    "SLIPPAGE_ADAPTER_ZERO",
    "CommissionCalibration",
    "ConstantPercentSlippageAdapter",
    "DeclaredPathFillAdapter",
    "FinancingScheduler",
    "GapVolatilitySlippageAdapter",
    "NotionalProportionalMinimumCostAdapter",
    "PerLotCostAdapter",
    "PercentOfNotionalCostAdapter",
    "SizeTieredSlippageAdapter",
    "SpreadCrossingSlippageAdapter",
    "ZeroCostAdapter",
    "ZeroSlippageAdapter",
    "decode_commission_calibration",
    "decode_slippage_calibration",
    "parse_adapter_ref",
]

AMBIENT_DISCOVERY: Final[bool] = False
FILL_ADAPTER_DECLARED_PATH: Final[str] = "declared-path"


@dataclass(frozen=True, slots=True)
class DeclaredPathFillAdapter:
    """Fill adapter: declared-path crossing dispatched per order type (FILL-2).

    Default pricing is bar-worst-case. Optimistic-exact is a labeled fill-basis.
    Both stay ``optimistic``-tainted until GAP-0048.
    """

    adapter_id: str = FILL_ADAPTER_DECLARED_PATH
    composition_version: int = COMPOSITION_VERSION
    taint: str = TAINT_OPTIMISTIC
    fill_basis: str = FILL_BASIS_WORST_CASE
    stale_price_span: Duration | None = None

    def fidelity(self) -> Result[FidelityIdentity]:
        """Stamp adapter-id + composition-version + fill-basis + optimistic taint."""
        return stamp_fidelity(
            self.adapter_id,
            composition_version=self.composition_version,
            fill_basis=self.fill_basis,
        )

    def decide(
        self,
        intent: AuthorizedIntent,
        path: SlicePath,
        *,
        requested_quantity: object,
        order: object = None,
        fill_basis: object = None,
        stale_price_span: object = None,
    ) -> Result[Fill | NoFill | PartialFill]:
        """Fill the authorized intent by crossing the declared path."""
        authorized = require_authorized_intent(intent)
        if is_refusal(authorized):
            return authorized
        if not path.prints and path.open is None and path.bid is None and path.ask is None:
            none = NoFill.try_create("empty-path")
            if is_refusal(none):
                return none
            return Ok(none.value)
        basis = self.fill_basis if fill_basis is None else fill_basis
        span = self.stale_price_span if stale_price_span is None else stale_price_span
        if basis not in FILL_BASES:
            basis = self.fill_basis
        return cross_declared_path(
            authorized.value,
            path,
            requested_quantity=requested_quantity,
            order=order,
            fill_basis=basis,
            stale_price_span=span,
        )


FILL_ADAPTER_CATALOG: Final[MappingProxyType[str, type[FillPort]]] = MappingProxyType(
    {FILL_ADAPTER_DECLARED_PATH: DeclaredPathFillAdapter}
)
SLIPPAGE_ADAPTER_CATALOG: Final[MappingProxyType[str, type[SlippagePort]]] = MappingProxyType(
    {
        SLIPPAGE_ADAPTER_ZERO: ZeroSlippageAdapter,
        SLIPPAGE_ADAPTER_CONSTANT_PERCENT: ConstantPercentSlippageAdapter,
        SLIPPAGE_ADAPTER_SPREAD_CROSSING: SpreadCrossingSlippageAdapter,
        SLIPPAGE_ADAPTER_GAP_VOLATILITY: GapVolatilitySlippageAdapter,
        SLIPPAGE_ADAPTER_SIZE_TIERED: SizeTieredSlippageAdapter,
    }
)


def parse_adapter_ref(field: str, raw: object, catalog: Mapping[str, object]) -> Result[str]:
    """Read a request's ``name@version`` adapter pin and return the catalog adapter-id.

    The version is the composition version every catalog adapter stamps, so a request
    pinned to another version is refused rather than bound to adapters it did not name.
    """
    if not isinstance(raw, str) or "@" not in raw:
        return invalid(field, "an adapter is named as name@version", given=repr(raw))
    name, version = raw.rsplit("@", 1)
    if name not in catalog:
        return invalid(field, "unknown adapter name", given=name, known=sorted(catalog))
    if version != str(COMPOSITION_VERSION):
        return invalid(
            field,
            "this QMB binds only the adapter version it ships",
            given=version,
            known=[str(COMPOSITION_VERSION)],
        )
    return Ok(name)


def decode_commission_calibration(
    adapter_id: str, raw: Mapping[str, object]
) -> Result[CommissionCalibration | None]:
    """Build a cost profile's commission calibration from its request data."""
    if adapter_id == COST_ADAPTER_ZERO:
        return Ok(None)
    percent = _optional_ratio(raw.get("percent"), "cost_profile.percent")
    if is_refusal(percent):
        return percent
    per_lot = _optional_money(raw.get("per_lot"), "cost_profile.per_lot")
    if is_refusal(per_lot):
        return per_lot
    per_1k = _optional_money(raw.get("per_1k_units"), "cost_profile.per_1k_units")
    if is_refusal(per_1k):
        return per_1k
    minimum = _optional_money(raw.get("minimum"), "cost_profile.minimum")
    if is_refusal(minimum):
        return minimum
    built = CommissionCalibration.try_create(
        adapter_id,
        raw.get("broker"),
        currency=raw.get("currency"),
        percent=percent.value,
        per_lot=per_lot.value,
        per_1k_units=per_1k.value,
        minimum=minimum.value,
    )
    if is_refusal(built):
        return built
    return Ok(built.value)


def decode_slippage_calibration(
    adapter_id: str, raw: Mapping[str, object]
) -> Result[SlippageCalibration | None]:
    """Build a slippage calibration from its request data; ``zero`` takes none."""
    if adapter_id == SLIPPAGE_ADAPTER_ZERO:
        return Ok(None)
    percent = _optional_ratio(raw.get("percent"), "slippage.percent")
    if is_refusal(percent):
        return percent
    built = SlippageCalibration.try_create(adapter_id, raw.get("broker"), percent=percent.value)
    if is_refusal(built):
        return built
    return Ok(built.value)


def _optional_money(raw: object, field: str) -> Result[Money | None]:
    if raw is None:
        return Ok(None)
    if not isinstance(raw, Mapping):
        return invalid(field, "money is {amount, currency, scale} with whole numbers")
    body = cast("Mapping[str, object]", raw)
    built = Money.try_create(body.get("amount"), body.get("currency"), body.get("scale"))
    if is_refusal(built):
        return built
    return Ok(built.value)


def _optional_ratio(raw: object, field: str) -> Result[ExactRational | None]:
    if raw is None:
        return Ok(None)
    if not isinstance(raw, Mapping):
        return invalid(field, "a ratio is {numerator, denominator} with whole numbers")
    body = cast("Mapping[str, object]", raw)
    built = ExactRational.try_create(
        body.get("numerator"), body.get("denominator"), UnitKind.DIMENSIONLESS_RATIO
    )
    if is_refusal(built):
        return built
    return Ok(built.value)
