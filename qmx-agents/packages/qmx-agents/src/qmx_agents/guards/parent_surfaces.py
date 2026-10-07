"""Closed parent surfaces rules retained from the existing barrier."""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class ParentLibrary(StrEnum):
    QMF_REGISTRY = "qmf-registry"
    QMF_RISK = "qmf-risk"


class ParentSurfaceKind(StrEnum):
    VALUE_TYPE = "value_type"
    TYPED_REFUSAL = "typed_refusal"
    PURE_CALCULATION = "pure_calculation"
    DEV_ZONE_CANDIDATE_WRITE = "dev_zone_candidate_write"


class ProhibitedRecordFamily(StrEnum):
    BINDING = "binding"
    BOOK = "book"
    BMS = "bms"
    SEAT = "seat"
    CONTROL_ACTION = "control_action"
    EXIT = "exit"
    PROTECTION = "protection"
    PRIORITY_RANK = "priority_rank"
    PROMOTION = "promotion"


class ProhibitedMutation(StrEnum):
    CONSTRUCT = "construct"
    WRITE = "write"
    AMEND = "amend"
    DELETE = "delete"


PARENT_SURFACE_LIBRARIES: Final[frozenset[ParentLibrary]] = frozenset(ParentLibrary)


PERMITTED_PARENT_SURFACES: Final[frozenset[tuple[ParentLibrary, ParentSurfaceKind]]] = frozenset(
    {
        (ParentLibrary.QMF_REGISTRY, ParentSurfaceKind.VALUE_TYPE),
        (ParentLibrary.QMF_REGISTRY, ParentSurfaceKind.TYPED_REFUSAL),
        (ParentLibrary.QMF_REGISTRY, ParentSurfaceKind.PURE_CALCULATION),
        (ParentLibrary.QMF_REGISTRY, ParentSurfaceKind.DEV_ZONE_CANDIDATE_WRITE),
        (ParentLibrary.QMF_RISK, ParentSurfaceKind.VALUE_TYPE),
        (ParentLibrary.QMF_RISK, ParentSurfaceKind.TYPED_REFUSAL),
        (ParentLibrary.QMF_RISK, ParentSurfaceKind.PURE_CALCULATION),
    }
)


PROHIBITED_RECORD_FAMILIES: Final[frozenset[ProhibitedRecordFamily]] = frozenset(
    ProhibitedRecordFamily
)


SOLE_PERMITTED_PARENT_WRITE: Final[tuple[ParentLibrary, ParentSurfaceKind]] = (
    ParentLibrary.QMF_REGISTRY,
    ParentSurfaceKind.DEV_ZONE_CANDIDATE_WRITE,
)


class ParentSurfaceError(ValueError):
    """The requested surface is outside the research boundary."""


def _resolve_library(library: ParentLibrary | str) -> ParentLibrary:
    if isinstance(library, ParentLibrary):
        return library
    try:
        return ParentLibrary(library)
    except ValueError as exc:
        raise ParentSurfaceError(f"{library!r} is not a declared parent library") from exc


def _resolve_kind(kind: ParentSurfaceKind | str) -> ParentSurfaceKind:
    if isinstance(kind, ParentSurfaceKind):
        return kind
    try:
        return ParentSurfaceKind(kind)
    except ValueError as exc:
        raise ParentSurfaceError(f"{kind!r} is not a parent surface kind") from exc


def is_parent_surface_permitted(
    library: ParentLibrary | str, kind: ParentSurfaceKind | str
) -> bool:
    try:
        resolved = (_resolve_library(library), _resolve_kind(kind))
    except ParentSurfaceError:
        return False
    return resolved in PERMITTED_PARENT_SURFACES
