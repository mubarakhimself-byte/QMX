"""The MIS's own tests, the suite the road's tests stage runs before the app may start.

The road runs `unittest discover` over this folder in the app's own locked environment, with no
network and writes only inside the proof volume. That environment has no pytest, so the
supervised suites are `mis_app_test.py` and `mis_road_test.py`: discovery's `test*.py` pattern
leaves them out and pytest's `*_test.py` still collects them.
"""

from __future__ import annotations

import itertools
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from mis_fixtures import BLOCKS, configure_both, pin, records, write_facts, write_markets

from mis_core import Mis

type Json = dict[str, object]

MARCH_NS = int(datetime(2025, 3, 1, tzinfo=UTC).timestamp()) * 1_000_000_000
LAST_MINUTE_NS = int(datetime(2025, 3, 31, 23, 59, tzinfo=UTC).timestamp()) * 1_000_000_000
LAST_FEBRUARY_MINUTE_NS = MARCH_NS - 60_000_000_000
GOLD_QUOTE_NS = MARCH_NS + 4_000_000_000
OFF: Json = {"on": False}


def _value(answer: Json) -> Json:
    assert answer["ok"] is True, answer
    return cast(Json, answer["value"])


class Rounds(unittest.TestCase):
    market_root: Path

    @classmethod
    def setUpClass(cls) -> None:
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.addClassCleanup(folder.cleanup)
        cls.market_root = Path(folder.name) / "market"
        write_markets(cls.market_root)

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(folder.cleanup)
        self.volume = Path(folder.name) / "mis"
        (self.volume / "data").mkdir(parents=True)

    def mis(self, holdout: Json | None = OFF) -> Mis:
        write_facts(self.volume, holdout)
        ticks = itertools.count(1_762_000_000_000_000_000, 1_000_000)
        made = Mis(self.volume, self.market_root, clock=lambda: next(ticks), boot="own")
        self.addCleanup(made.close)
        return made

    def test_each_market_gets_a_record_for_each_reading_its_levels_allow_and_none_for_the_rest(
        self,
    ) -> None:
        mis = self.mis()
        configured = _value(mis.call("configure", configure_both()))
        first = _value(mis.call("round", {}))
        second = _value(mis.call("round", {}))

        bodies = records(self.volume)
        self.assertEqual(configured, {"configured": 2, "refused": []})
        self.assertEqual(
            sorted((str(body["market_id"]), pin(body), body.get("word")) for body in bodies),
            [
                ("eurusd", "cusum-change-point@1", "no_change"),
                ("eurusd", "efficiency-ratio@1", "choppy"),
                ("eurusd", "hurst-exponent@1", "random"),
                ("eurusd", "variance-ratio@1", "random"),
                ("gold", "cusum-change-point@1", "no_change"),
                ("gold", "efficiency-ratio@1", "choppy"),
                ("gold", "hurst-exponent@1", "random"),
                ("gold", "spread_state@v1", "normal"),
                ("gold", "variance-ratio@1", "random"),
            ],
        )
        self.assertEqual(
            {(body["source"], body["machine"], body["health"]) for body in bodies},
            {("mis", "this-pc", "fresh")},
        )
        hurst = next(b for b in bodies if b["market_id"] == "gold" and pin(b) == BLOCKS[3])
        self.assertEqual(
            (hurst["value"], hurst["tier"], hurst["data_level"], hurst["inputs_received_at"]),
            (
                {"num": 538271125283, "den": 1000000000000, "unit_kind": "dimensionless-ratio"},
                "day",
                1,
                LAST_MINUTE_NS,
            ),
        )
        spread = next(b for b in bodies if pin(b) == "spread_state@v1")
        self.assertEqual(
            (spread["tier"], spread["data_level"], spread["inputs_received_at"]),
            ("tick", 2, GOLD_QUOTE_NS),
        )
        self.assertEqual((len(cast(list[Json], first["published"])), second["published"]), (9, []))

    def test_with_the_holdout_on_from_march_no_record_lands_for_march(self) -> None:
        mis = self.mis({"on": True, "boundary": "2025-03", "months": 1})
        _value(mis.call("configure", configure_both()))
        done = _value(mis.call("round", {}))

        bodies = records(self.volume)
        self.assertEqual(done["sealed_months"], ["2025-03"])
        self.assertEqual(
            sorted((str(body["market_id"]), pin(body)) for body in bodies),
            sorted((market, block) for market in ("eurusd", "gold") for block in BLOCKS),
        )
        self.assertEqual({body["inputs_received_at"] for body in bodies}, {LAST_FEBRUARY_MINUTE_NS})
        self.assertEqual({body["health"] for body in bodies}, {"fresh"})

    def test_with_no_host_facts_every_month_is_sealed_and_nothing_lands(self) -> None:
        mis = self.mis(holdout=None)
        _value(mis.call("configure", configure_both()))
        done = _value(mis.call("round", {}))

        self.assertEqual(
            (done["published"], done["sealed_months"], records(self.volume)),
            ([], ["2025-01", "2025-02", "2025-03"], []),
        )
        self.assertEqual(
            _value(mis.call("status", {}))["holdout"], {"on": True, "seals": "every month"}
        )

    def test_a_restarted_mis_reads_its_journal_and_publishes_nothing_twice(self) -> None:
        first = self.mis()
        _value(first.call("configure", configure_both()))
        _value(first.call("round", {}))
        first.close()

        again = self.mis()
        done = _value(again.call("round", {}))

        self.assertEqual((done["published"], len(records(self.volume))), ([], 9))
        self.assertEqual(
            again.plan.answer() if again.plan else None, {"configured": 2, "refused": []}
        )

    def test_a_shadow_reading_is_stamped_shadow_and_stays_off_the_board(self) -> None:
        mis = self.mis()
        shadow = [{"id": "z-score", "version": "1"}]
        _value(mis.call("configure", configure_both(shadow=shadow)))
        _value(mis.call("round", {}))

        bodies = [body for body in records(self.volume) if pin(body) == "z-score@1"]
        board = _value(mis.call("board", {}))
        on_board = {
            reading
            for tier in cast(list[Json], board["boards"])
            for market in cast(list[Json], tier["markets"])
            for reading in cast(Json, market["freshness"])
        }
        self.assertEqual(
            sorted((str(body["market_id"]), body["health"]) for body in bodies),
            [("eurusd", "shadow"), ("gold", "shadow")],
        )
        self.assertEqual(
            on_board,
            {
                "cusum-change-point",
                "efficiency-ratio",
                "variance-ratio",
                "hurst-exponent",
                "spread_state",
            },
        )

    def test_status_answers_before_and_after_a_round(self) -> None:
        mis = self.mis()
        before = _value(mis.call("status", {}))
        _value(mis.call("configure", configure_both()))
        _value(mis.call("round", {}))
        after = _value(mis.call("status", {}))

        self.assertEqual(
            before,
            {
                "state": "not configured",
                "machine": "this-pc",
                "holdout": {"on": False},
                "markets": [],
                "last_round": None,
            },
        )
        self.assertEqual(
            [
                (market["market_id"], market["readings"])
                for market in cast(list[Json], after["markets"])
            ],
            [
                ("eurusd", dict.fromkeys(BLOCKS, "fresh")),
                ("gold", {**dict.fromkeys(BLOCKS, "fresh"), "spread_state@v1": "fresh"}),
            ],
        )

    def test_bad_arguments_are_answered_and_never_raise(self) -> None:
        mis = self.mis()

        self.assertEqual(
            [
                mis.call("status", {"surprise": True}),
                mis.call("configure", {"markets": "eurusd"}),
                mis.call("round", {}),
                mis.call("board", ["not", "an", "object"]),
            ],
            [
                {
                    "ok": False,
                    "code": "bad_argument",
                    "message": "status: unknown argument surprise",
                },
                {
                    "ok": False,
                    "code": "bad_argument",
                    "message": "configure: markets is a list of objects",
                },
                {"ok": False, "code": "bad_argument", "message": "round: configure the MIS first"},
                {"ok": False, "code": "bad_argument", "message": "board: arguments are an object"},
            ],
        )
        self.assertEqual(
            _value(mis.call("configure", configure_both(packs=[{"id": "fx", "version": 1}]))),
            {"configured": 1, "refused": [{"market_id": "gold", "reason": "no pack for metal"}]},
        )
