"""Closed resolver for installed QMN hosted resources.

The currently registered host profile is replay-only. Resolving it verifies
its pinned source and callback identities, then refuses promotion to a LIVE
seat until the separately governed live observation, MIS, and KSA resources
are available. This module never imports profile-selected code.
"""

from __future__ import annotations

from qmf.core import Result, is_refusal

from qmn.host._refuse import invalid, unavailable
from qmn.host.configured_composition import (
    OFFLINE_CONFORMANCE_PROFILE_ID,
    resolve_host_resource_profile,
)
from qmn.host.configured_hosted import ConfiguredHostedResources
from qmn.host.configured_runtime import ConfiguredRuntimeAssessment

__all__ = ["resolve_configured_live_resources"]


def resolve_configured_live_resources(
    assessment: object,
) -> Result[ConfiguredHostedResources]:
    """Resolve only installed LIVE resources; replay-only profiles stand down.

    Resolution first verifies the independently pinned application profile
    against the checked configured-runtime assessment. No descriptor field is
    interpreted as an import path or callable. The current closed registry
    contains only the offline conformance profile, whose QMB replay source
    cannot supply LIVE observations or node-owned KSA state.
    """
    if not isinstance(assessment, ConfiguredRuntimeAssessment):
        return invalid(
            "assessment",
            "configured hosted resources require a checked runtime assessment",
        )
    profile = resolve_host_resource_profile(assessment)
    if is_refusal(profile):
        return profile
    if profile.value.profile_id != OFFLINE_CONFORMANCE_PROFILE_ID:
        return unavailable(
            "host_resource_profile",
            "the resolved application profile has no registered LIVE resource composition",
            failure_id="configured_runtime.hosted_resources_missing",
        )
    return unavailable(
        "hosted_resources",
        "the pinned profile reads QMB replay evidence and has no LIVE observation, "
        "current MIS, or KSA resource producer",
        failure_id="configured_runtime.hosted_resources_missing",
        profile_id=profile.value.profile_id,
        profile_fp1=profile.value.profile_fp1.value,
        source_fp1=profile.value.source_fp1.value,
    )
