from __future__ import annotations

from qmx_engine.ledger.signature import normalized, signature


def test_messages_differing_only_in_a_uuid_and_a_path_share_a_signature() -> None:
    first = (
        "run 0192f1c2-7a3b-7c4d-8e5f-0a1b2c3d4e5f could not read "
        "D:\\QMX\\runs\\a1\\out.json after 3 tries"
    )
    second = (
        "run 6f9619ff-8b86-d011-b42d-00c04fc964ff could not read "
        "/home/qmx/runs/b7/out.json after 4 tries"
    )
    assert signature("E_READ", first) == signature("E_READ", second)
    assert normalized(first) == "run <uuid> could not read <path> after <n> tries"


def test_a_hash_is_replaced_and_words_and_codes_still_count() -> None:
    assert normalized("object sha256:9f86d081884c7d65 missing; cafe decade") == (
        "object <hash> missing; cafe decade"
    )
    base = signature("E_READ", "could not read the file")
    assert signature("E_WRITE", "could not read the file") != base
    assert signature("E_READ", "could not parse the file") != base
