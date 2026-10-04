"""Application-mediated recorded spot ticks into the real QMF CT-10 archive.

One self-describing raw tick per receipt; bid is the ForeignMoney value and the
complete original payload, including ask, is retained as provenance. No live
collector or substitute CT-15 key authority is created.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from typing import cast

from qmf.core import Fingerprint, Result, WriterId, is_refusal
from qmf.data.observation import (
    ForeignMoney,
    ForeignTimestamp,
    MarketDataContext,
    SourceObservation,
)
from qmf.data.source_boundary import ObservationReceipt, SourceObservationBoundary
from qmf.venue.spot import SpotMarket, exact, refusal

from qmn.venue.spot_paper import SpotPaperAccount


@dataclass(frozen=True, slots=True)
class RecordedSpotSource:
    boundary: SourceObservationBoundary
    writer: WriterId
    source_id: str
    venue_id: str
    market: SpotMarket

    def ingest(
        self,
        payload: Mapping[str, object],
        *,
        native_id: str,
        revision: str,
        writer_sequence: int,
        correction_of: Fingerprint | None = None,
    ) -> Result[ObservationReceipt]:
        if payload.get("origin") != "synthetic":
            return refusal(
                "this tested intake admits synthetic infrastructure recordings only; "
                "public recordings require the existing CT-15 authority and an explicit license",
                code="POLICY",
            )
        try:
            with localcontext() as context:
                context.prec = 128
                bid, ask = exact(payload.get("bid")), exact(payload.get("ask"))
                if bid > ask:
                    raise ValueError("recorded bid cannot exceed ask")
                price_step = exact(self.market.price_step)
                if bid % price_step or ask % price_step:
                    raise ValueError("recorded prices violate declared precision")
                # A named exact scale boundary; wire payload strings remain unchanged.
                scale = max(0, -int(price_step.as_tuple().exponent))
                scaled = int(bid * Decimal(10) ** scale)
        except (ValueError, TypeError, InvalidOperation) as exc:
            return refusal(str(exc))
        context = MarketDataContext.try_create(
            venue=self.venue_id,
            symbol=self.market.symbol,
            resolution="tick",
            side="bid",
            license_tag="synthetic-infrastructure-only",
            provenance={
                "origin": payload["origin"],
                "raw_tick": dict(payload),
                "adapter_version": 1,
                "market": self.market.symbol,
                "amount_step": self.market.amount_step,
                "price_step": self.market.price_step,
            },
        )
        if is_refusal(context):
            return context
        observation = SourceObservation.try_create(
            event_time=payload.get("event_ns"),
            known_at=payload.get("received_ns"),
            source=self.source_id,
            source_native_id=native_id,
            revision=revision,
            receive_wall_time=payload.get("received_ns"),
            writer=self.writer,
            sequence=writer_sequence,
            world="replay",
            foreign_timestamp=ForeignTimestamp(
                str(payload.get("event_ns")), "UTC", "+00:00", "nanoseconds"
            ),
            foreign_money=ForeignMoney(scaled, scale),
            market_data=context.value,
            correction_of=correction_of,
        )
        if is_refusal(observation):
            return observation
        return self.boundary.admit(observation.value)

    def query(self, archive_ref: object) -> Result[SourceObservation]:
        return self.boundary.read(archive_ref, in_world="replay", for_world="replay")

    def replay_into(
        self, account: SpotPaperAccount, archive_ref: object
    ) -> Result[Mapping[str, object]]:
        """Interpret only a freshly verified same-source/symbol archive receipt."""
        read = self.query(archive_ref)
        if is_refusal(read):
            return read
        observed = read.value
        context = observed.market_data
        if (
            observed.source != self.source_id
            or context is None
            or context.venue != self.venue_id
            or context.symbol != self.market.symbol
            or account.scope.venue_id != self.venue_id
            or account.market != self.market
        ):
            return refusal(
                "replay receipt is outside the pinned source/venue/market scope", code="POLICY"
            )
        raw = context.provenance.get("raw_tick")
        if not isinstance(raw, Mapping):
            return refusal("recorded spot receipt has no complete raw tick")
        tick = cast("Mapping[str, object]", raw)
        if (
            context.license_tag != "synthetic-infrastructure-only"
            or context.resolution != "tick"
            or context.side != "bid"
            or context.provenance.get("origin") != "synthetic"
            or tick.get("origin") != "synthetic"
            or context.provenance.get("adapter_version") != 1
            or context.provenance.get("market") != self.market.symbol
            or context.provenance.get("amount_step") != self.market.amount_step
            or context.provenance.get("price_step") != self.market.price_step
            or tick.get("event_ns") != observed.event_time.value_ns
            or tick.get("received_ns") != observed.known_at.value_ns
            or tick.get("received_ns") != observed.receive_wall_time.value_ns
        ):
            return refusal("raw tick disagrees with retained CT-10 provenance/time", code="POLICY")
        try:
            with localcontext() as arithmetic:
                arithmetic.prec = 128
                scale = max(0, -int(exact(self.market.price_step).as_tuple().exponent))
                foreign = observed.foreign_money
                if (
                    foreign is None
                    or foreign.scale != scale
                    or foreign.verbatim != int(exact(tick.get("bid")) * Decimal(10) ** scale)
                ):
                    return refusal(
                        "raw bid disagrees with retained CT-10 foreign money", code="POLICY"
                    )
        except (ValueError, InvalidOperation) as exc:
            return refusal(str(exc))
        return account.ingest(tick)
