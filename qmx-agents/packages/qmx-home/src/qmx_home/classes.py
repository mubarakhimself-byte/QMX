"""What every path of a QMX folder is, for the copies, the guards and the sweeps (design 06
section 2). Standard library only.

`class_of(path, kind)` answers for a path relative to the QMX folder, `/` between names, so
`data/vault/` and `keys/` are told apart. The first rule that matches answers; a path no rule
names is `content`, the safe side, and `rule_of` says whether a rule named it. A Library object
answers by its kind, and a blob by the kinds of the objects that name it.

Four classes are sent: `recipe`, `content`, `result` and `prices`. `rebuildable`, `secret` and
`scratch` never leave the PC. The Library's logs travel whole with any Library class (`sent`).

`secret_values(settings)` finds every value in `settings.toml` stored under a key named like a
secret or shaped like one; a copy leaves each out by its key path.
"""

from __future__ import annotations

import functools
import glob
import os
import re
from collections.abc import Collection, Iterator, Mapping
from dataclasses import dataclass
from typing import Final, Literal, cast

type Class = Literal["recipe", "content", "result", "prices", "rebuildable", "secret", "scratch"]
type Answer = Class | Literal["kind"]

SENT: Final[tuple[Class, ...]] = ("recipe", "content", "result", "prices")
"""The saved set: what a storage keeps, each with its own switch."""
NEVER: Final[frozenset[Class]] = frozenset({"rebuildable", "secret", "scratch"})
"""Never leaves the PC."""
LIBRARY: Final[frozenset[Class]] = frozenset({"recipe", "content", "result"})
"""The classes Library objects fall into, by kind."""


@dataclass(frozen=True, slots=True)
class Rule:
    glob: str
    """Relative to the QMX folder, `/` between names; `**` crosses folders."""
    answer: Answer
    """The class, or `kind` for a Library object or blob, which answers by its kind."""
    why: str


_TEMPORARY: Final = "?" * 32
RULES: Final[tuple[Rule, ...]] = (
    Rule("keys/**", "secret", "the folder's keys"),
    Rule("data/vault/**", "secret", "the vault's keys"),
    Rule("data/vault-store.json", "secret", "sealed key copies for servers"),
    Rule("data/passes/**", "secret", "the run passes' revocation list"),
    Rule("data/rclone.conf", "secret", "the storages' sign-ins"),
    Rule("data/rclone.conf.unreadable-*", "secret", "storage sign-ins set aside"),
    Rule("data/claude/.credentials.json", "secret", "the plan login"),
    Rule("data/claude/.claude.json", "secret", "the plan login's account file"),
    Rule("data/claude-relayed/.credentials.json", "secret", "a login in the relayed home"),
    Rule("data/claude-relayed/.claude.json", "secret", "the relayed home's account file"),
    Rule("cache/**", "rebuildable", "fetched or made again"),
    Rule("logs/**", "rebuildable", "logs"),
    Rule("backups/**", "scratch", "the copies themselves"),
    Rule("qmx-home.toml", "scratch", "the folder's label, which a restore writes again"),
    Rule("data/**/*.lock", "scratch", "a lock"),
    Rule("data/**/*-wal", "scratch", "SQLite's own file; the store is copied whole"),
    Rule("data/**/*-shm", "scratch", "SQLite's own file; the store is copied whole"),
    Rule("data/**/*-journal", "scratch", "SQLite's own file; the store is copied whole"),
    Rule("data/**/*.qmx-copying", "scratch", "a copy still being written"),
    Rule("data/**/*.part", "scratch", "a file still being written"),
    Rule(f"data/library/**/.*.{_TEMPORARY}", "scratch", "a file the Library is still writing"),
    Rule("data/settings.tmp", "scratch", "settings still being written"),
    Rule("data/control-process.json", "scratch", "the record of a running process"),
    Rule("data/router.port", "scratch", "a running process's port"),
    Rule("data/node.port", "scratch", "a running process's port"),
    Rule("data/hub.port", "scratch", "a running process's port"),
    Rule("data/locks/**", "scratch", "each mini app's lease, kept by the machine"),
    Rule("data/road-locks/**", "scratch", "each mini app's road lease"),
    Rule("data/migration/restore-unfinished.txt", "scratch", "a restore's own marker"),
    Rule("data/market/.staging/**", "scratch", "price commits still being written"),
    Rule("data/market/**/.state.tmp", "scratch", "a price state still being written"),
    Rule("data/market/**/.incoming.parquet", "scratch", "a price file still being written"),
    Rule("data/market/**/.verify-*", "scratch", "a price check's scratch"),
    Rule("data/chats/*/**", "scratch", "a chat's launch files, made again at each launch"),
    Rule("data/apps/*/data/heartbeat-*", "scratch", "a mini app's heartbeat"),
    Rule("data/apps/*/data/tmp/**", "scratch", "a mini app's scratch"),
    Rule("data/apps/*/backup.json.tmp", "scratch", "a mini app's scratch"),
    Rule("data/claude-relayed/projects", "scratch", "a link to the plan home's chats"),
    Rule("data/claude-relayed/**", "scratch", "the relayed home, made again at each launch"),
    Rule("data/claude/projects/**", "content", "his chats"),
    Rule("data/claude/**", "scratch", "the plan home, made again at each launch"),
    Rule("data/library/catalog.db", "rebuildable", "the Library's index, made from its files"),
    Rule("data/library/catalog.db.*", "rebuildable", "an index the Library set aside"),
    Rule("data/library/blobs/fetched/**", "rebuildable", "copies fetched again from their store"),
    Rule("data/library/blobs/transient/**", "rebuildable", "checkpoints the host deletes"),
    Rule("data/memory/fts.db", "rebuildable", "the recall index, made from the Library"),
    Rule("data/memory/hindsight/**", "rebuildable", "Hindsight's database, made from Library rows"),
    Rule("data/queue/telemetry/**", "rebuildable", "telemetry the host deletes"),
    Rule("data/cache/**", "rebuildable", "prices and files fetched again"),
    Rule("data/logs/**", "rebuildable", "logs"),
    Rule("data/apps/*/logs/**", "rebuildable", "a mini app's logs"),
    Rule("data/settings.toml", "recipe", "his settings, with any key left out"),
    Rule("data/observers.json", "recipe", "observer tokens by hash, kept per machine"),
    Rule("data/profiles/**", "recipe", "his model rows"),
    Rule("data/slots/**", "recipe", "his prompt texts"),
    Rule("data/definitions/**", "recipe", "mini-app images"),
    Rule("data/apps.db", "recipe", "the mini-app catalogue"),
    Rule("data/library/kinds/**", "recipe", "the kinds the Library was written with"),
    Rule("data/library/objects/**", "kind", "a Library object, by its kind"),
    Rule("data/library/blobs/tombstones/**", "content", "a Library purge, with its logs"),
    Rule("data/library/blobs/**", "kind", "a Library blob, by the kinds that name it"),
    Rule("data/library/refs/**", "content", "the Library's ref log"),
    Rule("data/library/edges/**", "content", "the Library's edges"),
    Rule("data/library/annotations/**", "content", "the Library's annotations"),
    Rule("data/library/checkout/**", "content", "his working copies"),
    Rule("data/library/uploads/**", "content", "his uploads"),
    Rule("data/chats/*.json", "content", "his chats"),
    Rule("data/runs/**", "content", "each chat's usage journal"),
    Rule("data/agent-memory/**", "content", "the CLI's memory per working folder"),
    Rule("data/exports/**", "content", "his chat exports"),
    Rule("data/workspaces/**", "content", "his working folders"),
    Rule("data/apps/**", "content", "each mini app's own volume"),
    Rule("data/node/**", "content", "a trading node's state on this PC"),
    Rule("data/migration/pre/**", "content", "a store as it was before a switch"),
    Rule("data/migration/retired/**", "content", "an old store, kept read only"),
    Rule("data/migration/**", "content", "switch reports"),
    Rule("data/engine/engine.sqlite", "result", "the run ledger"),
    Rule("data/engine/inbox.sqlite", "result", "the inbox and incidents"),
    Rule("data/engine/runs/**", "result", "each run's frozen workflow and traces"),
    Rule("data/runs.db", "result", "the run index"),
    Rule("data/control.db", "result", "the control store"),
    Rule("data/portfolio.db", "result", "broker portfolio reads"),
    Rule("data/backtests/**", "result", "recorded backtest runs"),
    Rule("data/market/**", "prices", "prices that can't be downloaded again"),
)
"""Every path the code writes, first match first. Built from `STORES`, `Layout`, the snapshot's
old lists, `Volume.create` and both Claude homes."""

LIBRARY_LOGS: Final[tuple[str, ...]] = (
    "data/library/refs/**",
    "data/library/edges/**",
    "data/library/annotations/**",
    "data/library/blobs/tombstones/**",
)
"""Small, and every object needs them: they travel whole with any Library class."""

KINDS: Final[Mapping[str, Class]] = {
    **dict.fromkeys(
        (
            "workflow",
            "mini-app",
            "unit",
            "skill",
            "methodology",
            "template",
            "agent",
            "persona",
            "strategy",
            "component",
            "logic",
        ),
        cast("Class", "recipe"),
    ),
    **dict.fromkeys(
        ("workflow-run", "test-report", "artifact", "backtest-result"), cast("Class", "result")
    ),
}
"""The Library kinds that are not `content`; an unknown kind is `content`."""

PER_MACHINE: Final[tuple[str, ...]] = ("data/observers.json",)
"""Files kept from the new machine when a copy is restored onto it: observer token hashes belong
to the PC that minted them."""
PER_MACHINE_KEYS: Final[tuple[str, ...]] = (
    "engine.disk.floor_gb",
    "engine.placement.pc",
    "telemetry.send_to",
    "backup.rclone_path",
)
"""`settings.toml` keys kept from the new machine when a copy is restored onto it."""

SECRET_NAMES: Final = frozenset({"key", "apikey", "token", "password", "secret", "clientkey"})
"""Key names, lower case with `_` and `-` dropped, whose values are never stored or sent."""
SECRET_SHAPES: Final = re.compile(
    r"(?:sk-ant-|sk-or-|sk-proj-|sk-|ghp_|gho_|github_pat_|xox[abp]-|AKIA|AIza|hf_|GOCSPX-)"
    r"[A-Za-z0-9_\-]{16,}"
)
"""The published prefixes of provider keys and tokens: a value that is one of these whole."""
PUBLIC: Final = re.compile(r"engine\.placement\.[^.]+\.client_secret")
"""A Drive place row's client secret: a Desktop client's is public, so it travels."""

_CASE: Final = os.name != "nt"


def rule_of(path: str) -> Rule | None:
    """The rule that names `path`, or None when none does."""
    found = _pattern().match(path)
    if found is None:
        return None
    return RULES[int(next(name for name, hit in found.groupdict().items() if hit)[1:])]


def class_of(path: str, kind: str | Collection[str] | None = None) -> Class:
    """The class of `path`, relative to the QMX folder. `kind` is a Library object's kind, or
    the kinds of the objects that name a blob: the blob is the class of any of them that is
    sent, so a recipe's blob travels with the recipe."""
    found = rule_of(path)
    if found is None:
        return "content"
    if found.answer != "kind":
        return found.answer
    kinds = (kind,) if isinstance(kind, str) else tuple(kind or ())
    classes: set[Class] = {KINDS.get(one, "content") for one in kinds}
    for sent_class in SENT:
        if sent_class in classes:
            return sent_class
    return "content"


def is_library_log(path: str) -> bool:
    return _logs().match(path) is not None


def sent(path: str, save: Collection[Class], kind: str | Collection[str] | None = None) -> bool:
    """Whether a copy with the switches `save` holds `path`: its class is switched on, or it is
    a Library log and some Library class is."""
    if is_library_log(path):
        return any(one in LIBRARY for one in save)
    return class_of(path, kind) in save


def pruned(folder: str) -> bool:
    """Whether nothing under `folder` (relative to the QMX folder) is ever sent, so a walk need
    not enter it."""
    return _pruned().match(folder) is not None


def secret_paths() -> tuple[str, ...]:
    """The fixed paths of the `secret` rules, relative to the QMX folder, a folder for each
    `**` rule: what the harness guard refuses and a restore keeps from the machine."""
    return tuple(
        rule.glob.removesuffix("/**")
        for rule in RULES
        if rule.answer == "secret" and "*" not in rule.glob.removesuffix("/**")
    )


def secret_values(settings: Mapping[str, object]) -> dict[str, str]:
    """Each value of `settings` (as `settings.toml` reads) under a key named like a secret, or
    shaped like a key, by its key path: `providers.kimi.api_key`, an array's entry by index
    (`providers[2].api_key`). A Drive place row's `client_secret` is public and never named."""
    return {path: value for path, value in _strings(settings, "") if not PUBLIC.fullmatch(path)}


def without(settings: Mapping[str, object], paths: Collection[str]) -> dict[str, object]:
    """`settings` less the values at `paths`, as `secret_values` names them."""
    return cast("dict[str, object]", _drop(settings, "", frozenset(paths)))


def secret_name(key: str) -> bool:
    return key.lower().replace("_", "").replace("-", "") in SECRET_NAMES


def _strings(value: object, at: str, named: bool = False) -> Iterator[tuple[str, str]]:
    if isinstance(value, Mapping):
        for key, item in cast("Mapping[str, object]", value).items():
            yield from _strings(item, f"{at}.{key}" if at else key, named or secret_name(key))
    elif isinstance(value, list):
        for index, item in enumerate(cast("list[object]", value)):
            yield from _strings(item, f"{at}[{index}]", named)
    elif isinstance(value, str) and (named or SECRET_SHAPES.fullmatch(value)):
        yield at, value


def _drop(value: object, at: str, paths: frozenset[str]) -> object:
    if isinstance(value, Mapping):
        kept: dict[str, object] = {}
        for key, item in cast("Mapping[str, object]", value).items():
            inner = f"{at}.{key}" if at else key
            if inner not in paths:
                kept[key] = _drop(item, inner, paths)
        return kept
    if isinstance(value, list):
        return [
            _drop(item, f"{at}[{index}]", paths)
            for index, item in enumerate(cast("list[object]", value))
            if f"{at}[{index}]" not in paths
        ]
    return value


@functools.cache
def _pattern() -> re.Pattern[str]:
    parts = (f"(?P<r{number}>{_translated(rule.glob)})" for number, rule in enumerate(RULES))
    return re.compile("|".join(parts), 0 if _CASE else re.IGNORECASE)


@functools.cache
def _pruned() -> re.Pattern[str]:
    """Every never-sent `<folder>/**` rule no earlier sent rule reaches inside."""
    folders: list[str] = []
    for number, rule in enumerate(RULES):
        if rule.answer not in NEVER or not rule.glob.endswith("/**"):
            continue
        folder = rule.glob.removesuffix("/**")
        reached = any(
            earlier.glob.startswith(f"{folder}/") and earlier.answer not in NEVER
            for earlier in RULES[:number]
        )
        if not reached:
            folders.append(folder)
    return re.compile(
        "|".join(f"(?:{_translated(f)})" for f in folders), 0 if _CASE else re.IGNORECASE
    )


@functools.cache
def _logs() -> re.Pattern[str]:
    return re.compile(
        "|".join(f"(?:{_translated(g)})" for g in LIBRARY_LOGS), 0 if _CASE else re.IGNORECASE
    )


def _translated(pattern: str) -> str:
    return (
        glob.translate(pattern, recursive=True, include_hidden=True, seps="/").removesuffix(r"\Z")
        + r"\Z"
    )
