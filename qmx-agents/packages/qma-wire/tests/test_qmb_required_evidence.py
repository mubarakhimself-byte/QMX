"""Public backtest inputs agree with the persisted replay-request requirement."""

from qma.core.operations import public_operation_descriptors
from qma.wire.invocation_envelope import compute_input_hash
from qmf.core import is_ok, is_refusal


def test_backtest_requires_evidence_before_authority_or_dispatch() -> None:
    descriptor = next(
        row for row in public_operation_descriptors() if row.op_id == "qmb.backtest.run"
    )
    spec = "fp1:sha256:" + "a" * 64
    missing = compute_input_hash({"run_fp1": spec}, descriptor=descriptor)
    assert is_refusal(missing)
    assert missing.context["missing"] == ("evidence_ref",)
    # CT-40 validates required field presence. Receipt content and persisted
    # replay identity remain QMB/runtime semantic checks, not wire authority.
    complete = compute_input_hash(
        {"run_fp1": spec, "evidence_ref": "fp1:sha256:" + "b" * 64}, descriptor=descriptor
    )
    assert is_ok(complete)
