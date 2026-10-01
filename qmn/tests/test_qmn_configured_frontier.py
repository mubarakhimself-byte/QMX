"""Two recorded QMB frontiers reach the actual Book/KSA hosted root."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from hosted_root_fixture_support import drive_two_recorded_frontiers
from qmf.core import Instant, World, is_ok
from qmf.data.journal_producer import JournalReader
from qmf.data.store import JournalStore
from qmn.host.decision_root import HostedDecisionRoot
from qmn.mis import SignalSnapshot
from test_qmn_seat_tunnel import fixture_exercise_configured_decision_root


def test_two_accumulated_qmb_frontiers_call_persisted_hosted_book_ksa_root(
    tmp_path: Path,
) -> None:
    def drive(
        root: HostedDecisionRoot,
        snapshot_value: object,
        journal: JournalStore,
        intent_state: dict[str, object],
    ) -> None:
        assert isinstance(snapshot_value, SignalSnapshot)
        second = Instant.try_create(snapshot_value.frontier_instant.value_ns + 1_000_000_000)
        assert is_ok(second)
        outcomes, transcripts = drive_two_recorded_frontiers(
            root=root,
            snapshot=snapshot_value,
            journal=journal,
            intent_state=intent_state,
            frontier_instants=(snapshot_value.frontier_instant, second.value),
        )
        assert len(outcomes) == 2
        assert all(outcome is not None for outcome in outcomes)
        assert len(transcripts) == 2
        first = transcripts[0]
        second_transcript = transcripts[1]
        assert first.dispatch.commands
        assert not second_transcript.dispatch.commands
        assert first.snapshot_fingerprint != second_transcript.snapshot_fingerprint
        events = JournalReader(journal).read_checked(
            "hosted-decisions", for_world=World.LIVE
        )
        recorded_frontiers = JournalReader(journal).read_checked(
            "frontier-observations", for_world=World.LIVE
        )
        committed_frontiers = JournalReader(journal).read_checked(
            "frontier-cursor", for_world=World.LIVE
        )
        assert is_ok(events)
        assert is_ok(recorded_frontiers)
        assert is_ok(committed_frontiers)
        assert len(recorded_frontiers.value) == 2
        cursor_commits = [
            event for event in committed_frontiers.value
            if event.payload.get("kind") == "interpretation-cursor-commit"
        ]
        assert len(cursor_commits) == 2
        receive_stamps: list[object] = []
        for event in recorded_frontiers.value:
            observation = event.payload.get("observation")
            assert isinstance(observation, Mapping)
            receive_stamps.append(
                cast(Mapping[str, object], observation).get("receive_wall_time_ns")
            )
        assert receive_stamps == [
            snapshot_value.frontier_instant.value_ns,
            second.value.value_ns,
        ]
        decision_rows = [
            event.payload
            for event in events.value
            if event.payload.get("class") == "qmn-hosted-decision-transcript"
        ]
        # The first frontier dispatches the admitted entry. The harness then
        # supplies no intent on the second call; no production duplicate-action
        # property is inferred from this fixture.
        assert len(decision_rows) >= 4

    fixture_exercise_configured_decision_root(tmp_path, after_root_ready=drive)
