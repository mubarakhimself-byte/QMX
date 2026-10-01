"""CT-10 source-observation admission against a CT-12 split.

Raw source facts have their own bitemporal law (event time / knowledge time); they
are not indicator or structure ``KnowledgeRecord`` values. This adapter applies the
same CT-12 instant partition, straddle, purge, and producer-width rules directly to
the source-observation contract without relabeling the fact.
"""

from __future__ import annotations

from qmf.core import Ok, Result, fingerprint, is_refusal
from qmf.data.observation import SourceObservation
from qmf.data.splits import SegmentRole, SplitManifest
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = ["partition_source_observation"]


def partition_source_observation(manifest: object, observation: object) -> Result[SegmentRole]:
    """Return the CT-12 segment for one CT-10 source fact or refuse it.

    Placement uses ``known_at``; ``event_time`` is the observation horizon used
    for the same cross-boundary embargo check that CT-12 applies to derived rows.
    The caller must separately apply a configured :class:`HoldoutSeal` at the raw
    archive read boundary before making admitted rows available to a run.
    """
    if not isinstance(manifest, SplitManifest):
        return invalid_input("manifest", "source admission requires a CT-12 SplitManifest")
    if not isinstance(observation, SourceObservation):
        return invalid_input(
            "observation", "source admission accepts an immutable CT-10 SourceObservation"
        )
    stamped = fingerprint(manifest.fp1_identity())
    if is_refusal(stamped):
        return stamped
    if stamped.value != manifest.fingerprint:
        return policy_rejection(
            "manifest", "CT-12 fields recompute to the cited manifest fingerprint",
            expected=manifest.fingerprint.value,
            actual=stamped.value.value,
        )
    if manifest.world is not observation.world:
        return policy_rejection(
            "world",
            "CT-10 source world matches its CT-12 split",
            split=manifest.world.value,
            observation=observation.world.value,
        )
    if manifest.boundary_kind != "instant":
        return invalid_input(
            "segments", "CT-10 event and knowledge Instants require instant-form CT-12 boundaries"
        )
    event_ns = observation.event_time.value_ns
    known_ns = observation.known_at.value_ns
    if known_ns < event_ns:
        return invalid_input(
            "known_at",
            "a source fact cannot become knowable before its event time",
            event_time_ns=event_ns,
            known_at_ns=known_ns,
        )
    knowledge_index = manifest.instant_segment_index(observation.known_at)
    if knowledge_index is None:
        return invalid_input(
            "known_at",
            "source knowledge time falls beyond the CT-12 split",
            known_at_ns=known_ns,
        )
    event_index = manifest.instant_segment_index(observation.event_time)
    if event_index != knowledge_index:
        gap_ns = known_ns - event_ns
        if manifest.embargo_width.value_ns < gap_ns:
            return policy_rejection(
                "observation",
                "source event/knowledge straddle exceeds the CT-12 embargo",
                event_time_ns=event_ns,
                known_at_ns=known_ns,
                gap_ns=gap_ns,
                embargo_ns=manifest.embargo_width.value_ns,
            )
        return Ok(manifest.segments[knowledge_index].role)
    purged = manifest.purge_zone_refusal(observation.known_at, knowledge_index)
    if purged is not None:
        return purged
    return Ok(manifest.segments[knowledge_index].role)
