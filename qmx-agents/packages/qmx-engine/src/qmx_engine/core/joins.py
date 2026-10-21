"""Join closing (SOLUTION-DESIGN 3.5): a `join` node waits on the partitions of the node that feeds
it and fires by its `mode`. `all` needs every partition, `any` the first to arrive and
`quorum` the first `n`. The expected count is the source's partition count.

The `watermark` says when the join stops waiting if its mode is not met: `all-expected` once every
partition has settled, `failed-aggregation` as soon as failures leave too few partitions to meet
it, and `timeout` also once its `timeout_seconds` hold comes due. A join that stops waiting
unmet fails. A join fires with the partitions it counted, merged in partition order; every other
partition is late: named on the join's `node_scheduled` plan and never merged when it arrives.
A join that fired keeps that decision on every later pass (`State.joins`).

A failed partition walks the failure ladder on its own (AD-16, B-35), so `failed` holds only the
partitions that parked: one with ladder steps left is neither arrived nor failed, and the
watermark waits for it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, NamedTuple, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JoinSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["all", "any", "quorum"] = "all"
    n: int | None = Field(default=None, gt=0)
    watermark: Literal["all-expected", "timeout", "failed-aggregation"] = "all-expected"
    timeout_seconds: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _complete(self) -> Self:
        if (self.mode == "quorum") != (self.n is not None):
            raise ValueError("n is given with mode quorum and only then")
        if (self.watermark == "timeout") != (self.timeout_seconds is not None):
            raise ValueError("timeout_seconds is given with watermark timeout and only then")
        return self

    def needed(self, expected: int) -> int:
        return {"all": expected, "any": 1, "quorum": self.n or 0}[self.mode]


class Fired(NamedTuple):
    merged: tuple[int, ...]
    late: tuple[int, ...]


class Unmet(NamedTuple):
    code: str
    message: str


def close(
    spec: JoinSpec,
    expected: Sequence[int],
    arrived: Sequence[int],
    failed: Sequence[int],
    *,
    timed_out: bool = False,
) -> Fired | Unmet | None:
    """`expected` holds the partition ids the source ran and `arrived` the finished ones in arrival
    order. None means keep waiting."""
    need = spec.needed(len(expected))
    if len(arrived) >= need:
        merged = tuple(sorted(arrived[:need]))
        return Fired(merged, tuple(p for p in expected if p not in merged))
    reachable = len(expected) - len(failed) >= need
    settled = len(arrived) + len(failed) == len(expected)
    what = f"{spec.mode} join has {len(arrived)} of {need} needed partitions"
    if not reachable and (settled or spec.watermark == "failed-aggregation"):
        return Unmet("join_failed", f"{what}; {len(failed)} of {len(expected)} failed")
    if timed_out:
        return Unmet("join_timeout", f"{what} at its timeout")
    return None
