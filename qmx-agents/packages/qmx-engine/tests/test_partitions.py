"""The resolved model's window, in both places AD-34 uses it (RTR5): a `by: tokens` chunk plan
fills to 0.30 of the row's window and counts an item with the row's `chars_per_token`, and an agent
chat compacts at 0.40 at 512k and above and 0.75 below."""

from __future__ import annotations

from collections.abc import Sequence

from qmx_engine.core.partitions import chunks, estimate
from qmx_engine.definition.model import Chunk
from qmx_engine.nodes.agent import compact_at
from qmx_engine.ports.router import Reply, Row, adopt
from qmx_engine.settings import DEFAULTS

BIG = Row("kimi/k3", "kimi", "k3", "strong", 1_000_000)
SMALL = Row("deepseek/deepseek-v4", "deepseek", "deepseek-v4", "strong", 200_000)
COUNTED = Row("claude/opus", "claude", "opus", "strong", 1_000_000, 3.0, True)
ABSTRACTS = [{"id": i, "text": "w" * 20_000} for i in range(50)]
SPEC = Chunk(by="tokens", fill=0.3)


class Port:
    """A port that is only there to say a registry answered: `compact_at` reads its presence."""

    def rows(self) -> tuple[Row, ...]:
        return ()

    async def complete(self, *_args: object, **_kwargs: object) -> Reply:
        raise AssertionError("this port never completes")

    def hold(self, *, provider: str, model: str, affinity: str) -> str:
        raise AssertionError("this port never leases")

    def let_go(self, affinity: str) -> None:
        raise AssertionError("this port never leases")


def test_50_abstracts_make_2_chunks_on_a_1m_row_and_7_on_a_200k_row() -> None:
    two = chunks(ABSTRACTS, SPEC, {}, BIG)
    seven = chunks(ABSTRACTS, SPEC, {}, SMALL)

    assert (len(two), len(seven)) == (2, 7)
    assert [(s.start, s.end) for s in two] == [(0, 40), (40, 50)]
    assert [(s.start, s.end) for s in seven] == [
        (0, 8),
        (8, 16),
        (16, 24),
        (24, 32),
        (32, 40),
        (40, 48),
        (48, 50),
    ]


def test_a_row_without_count_tokens_counts_bytes_over_three_with_ten_percent_headroom() -> None:
    item = ABSTRACTS[0]

    assert estimate(item, BIG) == 7_340
    assert estimate(item, SMALL) == 7_340
    assert estimate(item) == 5_005


def test_a_row_that_counts_its_own_tokens_takes_no_headroom() -> None:
    assert estimate(ABSTRACTS[0], COUNTED) == 6_673


def test_an_agent_compacts_at_0_40_from_512k_and_0_75_below() -> None:
    adopt(Port())
    try:
        points = [compact_at(DEFAULTS, window) for window in (1_000_000, 512_000, 200_000)]
    finally:
        adopt(None)

    assert points == [0.4, 0.4, 0.75]


def test_without_a_registry_the_configured_point_stands() -> None:
    adopt(None)

    assert compact_at(DEFAULTS, 200_000) == 0.4
