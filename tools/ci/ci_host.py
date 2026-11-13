"""Where a CI job runs, and the facts about its run that qci needs.

GitHub Actions is the primary host, GitLab the fallback, and a laptop the default. Every other
module reads these facts from `read()` and never from a host's own variables, so a new host is one
more branch here.

On GitHub the workflow passes what the runner does not put in the environment by itself:
`QMX_HEAD_SHA` (the pull request's head; GITHUB_SHA is the merge commit there), `QMX_BEFORE_SHA`
(github.event.before) and the matrix shard as `QMX_SHARD` of `QMX_SHARDS`.
"""

from __future__ import annotations

import dataclasses
import enum
from collections.abc import Mapping


class Host(enum.StrEnum):
    GITHUB = "github"
    GITLAB = "gitlab"
    LAPTOP = "laptop"


@dataclasses.dataclass(frozen=True)
class RunFacts:
    host: Host
    head: str | None  # the commit under test; None means `git rev-parse HEAD`
    before: str | None  # the branch tip before this push, when the host knows it
    shard: int  # 1-based
    shards: int
    number: int  # counts up per run of this pipeline or workflow; picks the walk part
    ref: str  # branch or tag name
    run_id: str  # the host's id for this run, as its API names it


# Variables that belong to the host, not to the code under test. Tests run without them: they hold
# job tokens and proxy settings that the code under test rightly refuses to run beside (the agent
# harness refuses any name holding PROXY). `CI` itself stays.
HOST_PREFIXES = ("CI_", "GITLAB_", "GITHUB_", "ACTIONS_", "RUNNER_")


def _int(value: str | None, default: int) -> int:
    return int(value) if value else default


def _sha(value: str | None) -> str | None:
    return value if value and value.strip("0") else None


def read(env: Mapping[str, str]) -> RunFacts:
    if env.get("GITHUB_ACTIONS") == "true":
        return RunFacts(
            host=Host.GITHUB,
            head=env.get("QMX_HEAD_SHA") or env.get("GITHUB_SHA") or None,
            before=_sha(env.get("QMX_BEFORE_SHA")),
            shard=_int(env.get("QMX_SHARD"), 1),
            shards=_int(env.get("QMX_SHARDS"), 1),
            number=_int(env.get("GITHUB_RUN_NUMBER"), 0),
            ref=env.get("GITHUB_HEAD_REF") or env.get("GITHUB_REF_NAME", ""),
            run_id=env.get("GITHUB_RUN_ID", ""),
        )
    if env.get("GITLAB_CI") == "true":
        return RunFacts(
            host=Host.GITLAB,
            head=env.get("CI_MERGE_REQUEST_SOURCE_BRANCH_SHA") or env.get("CI_COMMIT_SHA") or None,
            before=_sha(env.get("CI_COMMIT_BEFORE_SHA")),
            shard=_int(env.get("CI_NODE_INDEX"), 1),
            shards=_int(env.get("CI_NODE_TOTAL"), 1),
            number=_int(env.get("CI_PIPELINE_IID"), 0),
            ref=env.get("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME") or env.get("CI_COMMIT_REF_NAME", ""),
            run_id=env.get("CI_PIPELINE_ID", ""),
        )
    return RunFacts(
        host=Host.LAPTOP,
        head=None,
        before=_sha(env.get("QMX_BEFORE_SHA")),
        shard=_int(env.get("QMX_SHARD"), 1),
        shards=_int(env.get("QMX_SHARDS"), 1),
        number=0,
        ref="",
        run_id="",
    )


def test_env(env: Mapping[str, str]) -> dict[str, str]:
    """The job's environment without the host's own variables."""
    return {k: v for k, v in env.items() if not k.startswith(HOST_PREFIXES)}
