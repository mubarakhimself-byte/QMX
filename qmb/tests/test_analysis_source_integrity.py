"""Independent public projection source substitution regression.

The existing artifact helper is a local recorded-result fixture, not provider evidence.
"""

from qmb.analysis import project
from qmf.core import is_ok, is_refusal
from test_analysis_project import _at, _result, _trade


def test_projection_refuses_unverified_rows_under_existing_ct29_binding_cite() -> None:
    as_of = _at(hour=0)
    original = (_trade(hour=10),)
    artifact = _result(registry_as_of=as_of, trades=original)
    predicate = {"hours": {"start": 8, "end": 16}}
    positive = project(source_ct32=artifact, source_ct29=original, predicate=predicate, as_of=as_of)
    assert is_ok(positive), positive
    assert positive.value.matched_count == 1
    substituted = project(
        source_ct32=artifact,
        source_ct29=(_trade(hour=18, pnl=999999),),
        predicate=predicate,
        as_of=as_of,
    )
    assert is_refusal(substituted), (
        "unverified substituted CT29 rows must not inherit the artifact's binding cite",
        substituted,
    )
