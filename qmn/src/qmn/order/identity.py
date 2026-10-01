"""Command-fingerprint-to-venue-id binding before wire handoff (TN-6; CT-19).

V1 maps into the venue client-id field through a durable command-id-binding
record persisted **before** submission — ``(venue client id, command fp1,
account, session epoch)`` — because a short venue client id cannot be a total
injection over an fp1 digest space plus stream qualification. Unpersistable
identity blocks submission (DEC-0191, DEC-0224).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, cast

from qmf.core import (
    Fingerprint,
    Instrument,
    Ok,
    RecordSink,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
    fingerprint,
    is_refusal,
)
from qmf.risk.paper import ExecutionTarget

from qmn.venue import BindingOutcome, Command, CommandIdBindingRegistry

__all__ = [
    "VENUE_CLIENT_ID_PREFIX",
    "CommandIdentityBinder",
    "NativeExecutionMap",
    "NativeExecutionMapping",
    "mint_venue_client_id",
]


VENUE_CLIENT_ID_PREFIX: Final[str] = "qmn"


@dataclass(frozen=True, slots=True)
class NativeExecutionMapping:
    """One immutable native-id row tied to a Book execution target."""

    target: ExecutionTarget
    instrument: Instrument
    native_account_id: int
    native_symbol_id: int

    @classmethod
    def try_create(
        cls,
        target: object,
        instrument: object,
        *,
        native_account_id: object,
        native_symbol_id: object,
    ) -> Result[NativeExecutionMapping]:
        if not isinstance(target, ExecutionTarget):
            return _invalid("target", "a native row binds a typed ExecutionTarget")
        if not isinstance(instrument, Instrument) or instrument.venue != target.venue_id:
            return _invalid("instrument", "mapped instrument belongs to the target venue")
        if (
            isinstance(native_account_id, bool)
            or not isinstance(native_account_id, int)
            or native_account_id < 1
        ):
            return _invalid("native_account_id", "native account id is a positive integer")
        if (
            isinstance(native_symbol_id, bool)
            or not isinstance(native_symbol_id, int)
            or native_symbol_id < 1
        ):
            return _invalid("native_symbol_id", "native symbol id is a positive integer")
        return Ok(
            cls(
                target=target,
                instrument=instrument,
                native_account_id=native_account_id,
                native_symbol_id=native_symbol_id,
            )
        )

    def identity(self) -> dict[str, object]:
        return {
            "account_id": self.target.account_id,
            "instrument": {
                "venue": self.instrument.venue.value,
                "symbol": self.instrument.symbol,
            },
            "native_account_id": self.native_account_id,
            "native_symbol_id": self.native_symbol_id,
            "role": self.target.role.value,
            "venue_id": self.target.venue_id.value,
        }


@dataclass(frozen=True, slots=True)
class NativeExecutionMap:
    """Frozen native mapping from one registry snapshot and optional binding epoch."""

    registry_as_of_fingerprint: Fingerprint
    binding_epoch: Fingerprint | None
    mappings: tuple[NativeExecutionMapping, ...]
    fingerprint: Fingerprint

    @classmethod
    def try_create(
        cls,
        mappings: object,
        *,
        registry_as_of_fingerprint: object,
        binding_epoch: object = None,
    ) -> Result[NativeExecutionMap]:
        if not isinstance(registry_as_of_fingerprint, Fingerprint):
            return _invalid(
                "registry_as_of_fingerprint",
                "native mappings cite the pinned registry as-of set",
            )
        if binding_epoch is not None and not isinstance(binding_epoch, Fingerprint):
            return _invalid("binding_epoch", "native mappings cite a typed CT-28 binding epoch")
        if isinstance(mappings, (str, bytes)) or not isinstance(mappings, Iterable):
            return _invalid("mappings", "native execution mappings are an ordered collection")
        rows: list[NativeExecutionMapping] = []
        keys: set[tuple[str, str, str, str, str]] = set()
        for item in cast("Iterable[object]", mappings):
            if not isinstance(item, NativeExecutionMapping):
                return _invalid(
                    "mappings", "each native execution row is a NativeExecutionMapping"
                )
            if item.instrument.venue != item.target.venue_id:
                return _invalid(
                    "instrument", "mapped instrument venue matches its execution target"
                )
            if (
                type(item.native_account_id) is not int
                or item.native_account_id < 1
                or type(item.native_symbol_id) is not int
                or item.native_symbol_id < 1
            ):
                return _invalid("native_ids", "native account and symbol ids are positive integers")
            key = (
                item.target.role.value,
                item.target.venue_id.value,
                item.target.account_id,
                item.instrument.venue.value,
                item.instrument.symbol,
            )
            if key in keys:
                return _invalid(
                    "mappings", "native execution target/instrument mappings are unique"
                )
            keys.add(key)
            rows.append(item)
        if not rows:
            return _invalid(
                "mappings", "native execution map contains at least one resolved target"
            )
        content = {
            "class": "qmn-native-execution-map",
            "registry_as_of_fingerprint": registry_as_of_fingerprint.value,
            "mappings": [
                row.identity()
                for row in sorted(
                    rows,
                    key=lambda row: (
                        row.target.role.value,
                        row.target.venue_id.value,
                        row.target.account_id,
                        row.instrument.venue.value,
                        row.instrument.symbol,
                    ),
                )
            ],
            "format_version": 1,
        }
        if binding_epoch is not None:
            content["binding_epoch"] = binding_epoch.value
        fp = fingerprint(content)
        if is_refusal(fp):
            return fp
        return Ok(
            cls(
                registry_as_of_fingerprint=registry_as_of_fingerprint,
                binding_epoch=binding_epoch,
                mappings=tuple(rows),
                fingerprint=fp.value,
            )
        )

    def resolve(
        self, target: object, instrument: object
    ) -> Result[NativeExecutionMapping]:
        if not isinstance(target, ExecutionTarget) or not isinstance(instrument, Instrument):
            return _invalid(
                "target", "native mapping lookup uses an ExecutionTarget and Instrument"
            )
        for row in self.mappings:
            if row.target == target and row.instrument == instrument:
                return Ok(row)
        return _invalid(
            "native_execution_mapping",
            "the pinned native map has no row for the exact admitted account, role, venue, "
            "and instrument",
            target=target.fp1_identity(),
            instrument={"venue": instrument.venue.value, "symbol": instrument.symbol},
        )


def _invalid(field: str, reason: str, **extra: object) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context={"field": field, "reason": reason, **extra},
    )


def mint_venue_client_id(*, ordering_ordinal: object, session_epoch: object) -> Result[str]:
    """Mint a short venue client id for the non-injective cTrader clientMsgId map."""
    if (
        not isinstance(ordering_ordinal, int)
        or isinstance(ordering_ordinal, bool)
        or ordering_ordinal < 0
    ):
        return TypedRefusal(
            category=RefusalCategory.INVALID_INPUT,
            retryability=Retryability.NO,
            context={
                "field": "ordering_ordinal",
                "reason": "venue client id derivation requires the command ordinal",
                "given": repr(ordering_ordinal),
            },
        )
    if not isinstance(session_epoch, str) or session_epoch.strip() == "":
        return TypedRefusal(
            category=RefusalCategory.INVALID_INPUT,
            retryability=Retryability.NO,
            context={
                "field": "session_epoch",
                "reason": "venue client id derivation requires the session epoch",
                "given": repr(session_epoch),
            },
        )
    # Keep well under cTrader's 100-character clientMsgId bound.
    epoch_token = session_epoch.strip().replace(" ", "")[-24:]
    return Ok(f"{VENUE_CLIENT_ID_PREFIX}-{ordering_ordinal}-{epoch_token}")


@dataclass
class CommandIdentityBinder:
    """Persist command-fingerprint-to-venue-id binding before wire handoff.

    Wraps :class:`CommandIdBindingRegistry`. When the CT-18 mapping is not
    injective-and-total (V1 cTrader path), binding must succeed before handoff;
    storage failure blocks submission.
    """

    registry: CommandIdBindingRegistry
    injective_total: bool = False

    @classmethod
    def try_create(
        cls,
        record_sink: object,
        *,
        injective_total: object = False,
    ) -> Result[CommandIdentityBinder]:
        if not isinstance(injective_total, bool):
            return TypedRefusal(
                category=RefusalCategory.INVALID_INPUT,
                retryability=Retryability.NO,
                context={
                    "field": "injective_total",
                    "reason": "CT-18 command_id_mapping.injective_total is a boolean",
                    "given": repr(injective_total),
                },
            )
        if not isinstance(record_sink, RecordSink):
            return TypedRefusal(
                category=RefusalCategory.INVALID_INPUT,
                retryability=Retryability.NO,
                context={
                    "field": "record_sink",
                    "reason": "command-id binding persists through an injected RecordSink",
                    "given": repr(record_sink),
                },
            )
        registry = CommandIdBindingRegistry.try_create(cast("RecordSink[object]", record_sink))
        if is_refusal(registry):
            return registry
        return Ok(cls(registry=registry.value, injective_total=injective_total))

    def bind_before_wire_handoff(
        self,
        command: object,
        *,
        venue_client_id: object | None = None,
    ) -> Result[BindingOutcome]:
        """Persist the fp1↔venue-id binding before wire handoff.

        Unpersistable identity is surfaced and blocks submission. Ordinal-bearing
        venue client ids are minted when the caller does not supply one.
        """
        if not isinstance(command, Command):
            return TypedRefusal(
                category=RefusalCategory.INVALID_INPUT,
                retryability=Retryability.NO,
                context={
                    "field": "command",
                    "reason": "identity binding requires a typed CT-19 Command",
                    "given": type(command).__name__,
                },
            )
        client_id = venue_client_id
        if client_id is None:
            minted = mint_venue_client_id(
                ordering_ordinal=command.ordering_ordinal,
                session_epoch=command.session_epoch,
            )
            if is_refusal(minted):
                return minted
            client_id = minted.value
        if not isinstance(client_id, str) or client_id.strip() == "":
            return TypedRefusal(
                category=RefusalCategory.INVALID_INPUT,
                retryability=Retryability.NO,
                context={
                    "field": "venue_client_id",
                    "reason": "command-fingerprint-to-venue-id binding needs a venue client id",
                    "given": repr(client_id),
                },
            )
        bound = self.registry.bind_before_submission(
            command,
            venue_client_id=client_id.strip(),
            injective_total=self.injective_total,
        )
        if is_refusal(bound):
            # Unpersistable identity blocks submission — never hand off.
            return bound
        return bound
