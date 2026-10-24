"""Binance's bulk files: the checksum decides whether a month may be read (W14).

The bucket publishes a digest beside every file. A file that does not hash to it is refused
before a row is decoded, because the alternative is a month that quietly holds the days that
worked and looks complete.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import date

from qmf.core import Ok, RefusalCategory, Result, is_ok, is_refusal
from qmf.data.binance_vision import (
    COLUMNS,
    bucket_path,
    decode_rows,
    kind_for,
    month_files,
    parse_checksum,
    variant_for,
    verify_checksum,
)
from qmf.data.series import FreezeKind, SeriesKey
from qmf.data.store.refusals import storage_failure

TRADES_CSV = (
    b"trade_id,price,qty,quote_qty,time,is_buyer_maker,is_best_match\n"
    b"1,19000.50,0.25,4750.125,1756684800000,false,true\n"
    b"2,19001.00,0.75,14250.75,1756684801000,true,true\n"
)


def value[T](result: Result[T]) -> T:
    """The successful value, with the refusal assertion spelled once."""
    assert is_ok(result)
    return result.value


def zipped(csv_bytes: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("BTCUSDT-trades-2026-08-01.csv", csv_bytes)
    return buffer.getvalue()


def test_a_file_that_does_not_hash_to_its_published_checksum_is_refused() -> None:
    payload = zipped(TRADES_CSV)
    published = "sha256:" + hashlib.sha256(b"a different file").hexdigest()

    refused = verify_checksum(payload, published, name="BTCUSDT-trades-2026-08-01.zip")

    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "checksum"
    assert refused.context["published"] == published.removeprefix("sha256:")


def test_the_two_trade_datasets_land_as_one_kind_under_two_variants() -> None:
    assert (value(kind_for("trades")), value(variant_for("trades"))) == ("trades", "")
    assert (value(kind_for("aggTrades")), value(variant_for("aggTrades"))) == (
        "trades",
        "aggTrades",
    )
    assert (value(kind_for("bookDepth")), value(variant_for("bookDepth"))) == ("book", "depth")
    assert value(decode_rows("trades", TRADES_CSV))[0] == (
        1_756_684_800_000,
        1_900_050_000_000,
        0.25,
    )


def test_a_month_whose_second_day_the_bucket_does_not_serve_is_refused() -> None:
    payload = zipped(TRADES_CSV)
    checksum = "sha256:" + hashlib.sha256(payload).hexdigest()
    first = bucket_path("trades", "BTCUSDT", date(2026, 8, 1))
    served = {first.path: payload, first.checksum_path: checksum.encode()}

    def reader(url: str):
        if url in served:
            return Ok(served[url])
        return storage_failure("the bucket has no such file", context={"url": url})

    refused = month_files(reader, "trades", "BTCUSDT", 2026, 8)

    assert is_refusal(refused)
    assert refused.category is RefusalCategory.STORAGE_FAILURE


def test_a_trades_and_a_book_month_freeze_on_a_checksum_with_the_decoder_columns() -> None:
    for dataset, kind, variant in (
        ("trades", "trades", ""),
        ("aggTrades", "trades", "aggTrades"),
        ("bookDepth", "book", "depth"),
    ):
        built = SeriesKey.try_create("binance", "BTCUSDT", kind, 2026, 8, variant)
        assert is_ok(built)
        rule = built.value.rule

        assert rule.columns == COLUMNS[value(kind_for(dataset))]
        assert rule.freeze is FreezeKind.CHECKSUM


def test_a_checksum_file_is_read_in_the_shapes_the_bucket_publishes() -> None:
    digest = "ab" * 32

    assert value(parse_checksum(f"sha256:{digest}  BTCUSDT-trades-2026-08-01.zip\n")) == digest
    assert value(parse_checksum(f"SHA256 (BTCUSDT-trades-2026-08-01.zip) = {digest}")) == digest
    assert value(parse_checksum(digest.encode())) == digest
