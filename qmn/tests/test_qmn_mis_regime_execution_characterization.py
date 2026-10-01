"""Held-out execution and restart characterization for offline MIS studies."""

from __future__ import annotations

from pathlib import Path

from qmf.core.refusal import is_ok
from qmn.mis import (
    EVALUATION_BACKEND_DETERMINISTIC,
    TRAINING_BACKEND_DETERMINISTIC,
    TrainingArtifact,
    TrainingRecord,
    TrainingTerminalStatus,
    build_evaluation_matrix,
    resume_offline_training,
    run_offline_evaluation,
    run_offline_training,
)
from test_qmn_mis_regime_eval import fixture_trained_regime_evaluation
from test_qmn_mis_regime_train import fixture_prepared_regime_training


def test_training_restart_reproduces_uninterrupted_trials(tmp_path: Path) -> None:
    cleaned, labeled = fixture_prepared_regime_training()
    completed = run_offline_training(
        labeled=labeled,
        cleaned=cleaned,
        output_dir=str(tmp_path / "uninterrupted"),
        seed=73,
        backend=TRAINING_BACKEND_DETERMINISTIC,
        max_trials=4,
    )
    assert is_ok(completed), completed
    assert isinstance(completed.value, TrainingArtifact)

    interrupted = run_offline_training(
        labeled=labeled,
        cleaned=cleaned,
        output_dir=str(tmp_path / "resumed"),
        seed=73,
        backend=TRAINING_BACKEND_DETERMINISTIC,
        max_trials=4,
        abort_after_trials=2,
    )
    assert is_ok(interrupted), interrupted
    assert isinstance(interrupted.value, TrainingRecord)
    assert interrupted.value.status is TrainingTerminalStatus.ABORTED
    assert interrupted.value.registerable is False

    resumed = resume_offline_training(
        labeled=labeled,
        cleaned=cleaned,
        output_dir=str(tmp_path / "resumed"),
        seed=73,
        backend=TRAINING_BACKEND_DETERMINISTIC,
        max_trials=4,
    )
    assert is_ok(resumed), resumed
    assert isinstance(resumed.value, TrainingArtifact)
    assert resumed.value.record.status is TrainingTerminalStatus.COMPLETED
    assert resumed.value.record.registerable is True
    assert resumed.value.model_fp == completed.value.model_fp
    assert resumed.value.matrix_fp == completed.value.matrix_fp
    assert [trial.fp1_identity() for trial in resumed.value.record.trials] == [
        trial.fp1_identity() for trial in completed.value.record.trials
    ]
    assert resumed.value.record.best_trial_index == completed.value.record.best_trial_index


def test_evaluation_metrics_cover_exact_disjoint_split_rows(tmp_path: Path) -> None:
    cleaned, labeled, artifact = fixture_trained_regime_evaluation(tmp_path)
    matrix = build_evaluation_matrix(cleaned, labeled)
    assert is_ok(matrix), matrix
    report = run_offline_evaluation(
        artifact=artifact,
        labeled=labeled,
        cleaned=cleaned,
        output_dir=str(tmp_path / "eval"),
        backend=EVALUATION_BACKEND_DETERMINISTIC,
    )
    assert is_ok(report), report

    expected_counts = {
        "train": len(matrix.value.train_rows),
        "validation": len(matrix.value.validation_rows),
        "sealed-test": len(matrix.value.holdout_rows),
    }
    seen_ids: set[str] = set()
    for scores in (
        report.value.train_scores,
        report.value.validation_scores,
        report.value.holdout_scores,
    ):
        assert scores.row_count == expected_counts[scores.split_role]
        assert scores.excluded_from_scoring == 0
        assert 0 <= scores.brier_ppb <= 1_000_000_000
        assert sum(row.support for row in scores.per_class) == scores.row_count
        assert scores.min_per_class_recall_den > 0
        if scores.split_role == "sealed-test":
            assert scores.row_count == len(matrix.value.holdout_rows)
    for group in (matrix.value.train_rows, matrix.value.validation_rows, matrix.value.holdout_rows):
        ids = {row[0] for row in group}
        assert ids.isdisjoint(seen_ids)
        seen_ids.update(ids)
