"""First-party desk plugin pack roster (FR-Q71; FEAT-0046; CT-42).

Loads the five packs from ``qmx-agents/plugins/`` and activates them through
the core ``PluginManifest`` / ``PluginContext`` surface. Authors import
contribution types from ``qma-core``; this module never offers a daemon-private
registration path. ``analysis-backtest`` is the existing Backtesting Service
adapter: one ``qmb`` job per environment through the QMB door.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

from qma.core.ontology.records import Agent, Subagent
from qma.core.plugins.context import PluginContext
from qma.core.plugins.manifest import PluginManifest, parse_plugin_manifest
from qma.core.plugins.packs import (
    ANALYSIS_BACKTEST_PLUGIN_ID,
    DESK_PLUGIN_PACK_DESKS,
    DESK_PLUGIN_PACK_IDS,
    MEMORY_CANDIDATES_ARE_ADMITTED,
    PACK_ENTRYPOINT,
    PROMOTE_IS_HUMAN_OUTSIDE_QMA,
    REFINEMENT_PROPOSALS_ARE_APPLIED,
    require_desk_plugin_pack_id,
)
from qma.core.ports.cardinality import Cardinality
from qma.core.ports.knowledge import KnowledgeSource
from qma.core.ports.memory import MemoryProvider, refuse_memory_promote
from qma.core.ports.qmb import QMB_BACKTEST_TOOL_ID, QMB_OWNED_CONCERNS
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.capabilities.spawn import SpawnRequest, spawn_agent
from qma.daemon.knowledge import KnowledgeSourceRegistry
from qma.daemon.memory import MemoryAdmissionGate
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.daemon.plugins.lifecycle import AtomicRoster
from qma.daemon.plugins.loader import (
    LoadCommand,
    LoadedPlugin,
    PluginActivator,
    PluginLoader,
    PluginLoadError,
)
from qma.daemon.staging.proposal import ProposalGate
from qma.daemon.taskgraph.compiler import GraphTemplateCatalog, MissionCompiler
from qma.daemon.taskgraph.records import GraphTemplate
from qmf.core import Ok, Result, is_ok, is_refusal
from qmf.core.fingerprint import fingerprint_bytes

if TYPE_CHECKING:
    from qma.daemon.backtest.service import BacktestingService
    from qma.daemon.journal.authoritative import AuthoritativeJournal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "ANALYSIS_BACKTEST_PLUGIN_ID",
    "DESK_PLUGIN_PACK_DESKS",
    "DESK_PLUGIN_PACK_IDS",
    "MEMORY_CANDIDATES_ARE_ADMITTED",
    "PACK_ENTRYPOINT",
    "PROMOTE_IS_HUMAN_OUTSIDE_QMA",
    "QMB_OWNED_CONCERNS",
    "REFINEMENT_PROPOSALS_ARE_APPLIED",
    "DeskPluginRoster",
    "default_plugins_root",
    "load_pack_activator",
    "load_pack_manifest_raw",
    "research_corpus_plugin_load_config",
]


def research_corpus_plugin_load_config(
    root_path: Path | str,
) -> dict[str, dict[str, object]]:
    """Operator-principal load config binding seed-corpus ``root_path``.

    ``root_path`` is a filesystem path, not an env var, git path, venue secret,
    or qmb setting (NFR-RES-06).
    """
    return {"research-corpus": {"root_path": str(Path(root_path))}}


def default_plugins_root() -> Path:
    """Resolve ``qmx-agents/plugins`` from this module or a parent walk."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "plugins"
        if (candidate / "research-corpus" / "manifest.json").is_file():
            return candidate
    return here.parents[6] / "plugins"


def load_pack_manifest_raw(plugin_root: Path) -> dict[str, object]:
    """Read one pack ``manifest.json`` as a mapping."""
    path = plugin_root / "manifest.json"
    if not path.is_file():
        raise PluginLoadError(
            f"desk pack manifest missing at {path}",
            plugin_id=plugin_root.name,
            field="manifest",
        )
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise PluginLoadError(
            f"manifest must be a JSON object; got {type(loaded).__name__}",
            plugin_id=plugin_root.name,
            field="manifest",
        )
    return cast(dict[str, object], loaded)


def load_pack_activator(plugin_root: Path, entrypoint: str) -> PluginActivator:
    """Import ``activate`` from the pack tree without a ``qma.daemon`` edge."""
    if ":" not in entrypoint:
        raise PluginLoadError(
            f"entrypoint must be module:function; got {entrypoint!r}",
            plugin_id=plugin_root.name,
            field="entrypoint",
        )
    module_rel, func_name = entrypoint.split(":", 1)
    if not module_rel or not func_name:
        raise PluginLoadError(
            f"entrypoint must be module:function; got {entrypoint!r}",
            plugin_id=plugin_root.name,
            field="entrypoint",
        )
    path = plugin_root.joinpath(*module_rel.split(".")).with_suffix(".py")
    if not path.is_file():
        raise PluginLoadError(
            f"entrypoint module not found at {path}",
            plugin_id=plugin_root.name,
            field="entrypoint",
        )
    module_name = f"qma_desk_pack_{plugin_root.name}_{module_rel.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise PluginLoadError(
            f"cannot load entrypoint {entrypoint!r}",
            plugin_id=plugin_root.name,
            field="entrypoint",
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    activator = getattr(module, func_name, None)
    if not callable(activator):
        raise PluginLoadError(
            f"entrypoint {entrypoint!r} is not callable",
            plugin_id=plugin_root.name,
            field="entrypoint",
        )
    return cast(PluginActivator, activator)


def _graph_template_from_mapping(payload: Mapping[str, object]) -> GraphTemplate:
    nodes_raw = payload.get("nodes", ())
    edges_raw = payload.get("edges", ())
    nodes: tuple[Mapping[str, object], ...]
    edges: tuple[Mapping[str, object], ...]
    if isinstance(nodes_raw, Sequence) and not isinstance(nodes_raw, (str, bytes)):
        built_nodes: list[Mapping[str, object]] = []
        for item in cast(Sequence[object], nodes_raw):
            if not isinstance(item, Mapping):
                msg = "graph_template nodes must be mappings; refusing silent drop (AD-5; FR-WF-42)"
                raise PluginLoadError(msg, field="graph_template.nodes")
            built_nodes.append(dict(cast(Mapping[str, object], item)))
        nodes = tuple(built_nodes)
    else:
        nodes = ()
    if isinstance(edges_raw, Sequence) and not isinstance(edges_raw, (str, bytes)):
        built_edges: list[Mapping[str, object]] = []
        for item in cast(Sequence[object], edges_raw):
            if not isinstance(item, Mapping):
                # Do not silently drop malformed edges (AD-5; Story 56.3).
                msg = "graph_template edges must be mappings; refusing silent drop (AD-5; FR-WF-42)"
                raise PluginLoadError(msg, field="graph_template.edges")
            built_edges.append(dict(cast(Mapping[str, object], item)))
        edges = tuple(built_edges)
    else:
        edges = ()
    qualified = payload.get("qualified_id")
    version = payload.get("version")
    if not isinstance(qualified, str) or not isinstance(version, str):
        msg = "graph_template requires qualified_id and version"
        raise PluginLoadError(msg, field="graph_template")
    return GraphTemplate(qualified_id=qualified, version=version, nodes=nodes, edges=edges)


class DeskPluginRoster:
    """Five first-party desk packs registered through the core contribution surface."""

    def __init__(
        self,
        *,
        plugins_root: Path | None = None,
        loader: PluginLoader | None = None,
        backtesting: BacktestingService | None = None,
        plugin_load_configs: Mapping[str, Mapping[str, object]] | None = None,
        authoring_roster_root: Path | None = None,
        authoring_journal: AuthoritativeJournal | None = None,
        sqlite: SingleSqliteWriter | None = None,
    ) -> None:
        self.plugins_root = plugins_root if plugins_root is not None else default_plugins_root()
        configs: dict[str, Mapping[str, object]] = {
            key: dict(value) for key, value in dict(plugin_load_configs or {}).items()
        }
        if loader is not None:
            self.loader = loader
            if sqlite is not None:
                self.loader.pack_ui_sqlite = sqlite
            if configs:
                merged = dict(loader.plugin_load_configs)
                merged.update(configs)
                self.loader.plugin_load_configs = merged
        else:
            self.loader = PluginLoader(plugin_load_configs=configs, pack_ui_sqlite=sqlite)
        if backtesting is not None:
            self.backtesting = backtesting
        else:
            service_mod = importlib.import_module("qma.daemon.backtest.service")
            self.backtesting = service_mod.BacktestingService()
        self.templates = GraphTemplateCatalog()
        self.compiler = MissionCompiler(templates=self.templates)
        self.memory = MemoryAdmissionGate()
        self.knowledge = KnowledgeSourceRegistry()
        self.proposals = ProposalGate()
        self.authoring_roster_root = authoring_roster_root
        self.authoring_journal = authoring_journal

    @property
    def pack_ids(self) -> tuple[str, ...]:
        return DESK_PLUGIN_PACK_IDS

    def raw_manifests(self) -> tuple[dict[str, object], ...]:
        """Load the five pack manifests in roster order."""
        rows: list[dict[str, object]] = []
        present = sorted(path.name for path in self.plugins_root.iterdir() if path.is_dir())
        expected = sorted(DESK_PLUGIN_PACK_IDS)
        if present != expected:
            raise PluginLoadError(
                f"desk-pack roster must be {expected}; found {present}",
                field="id",
            )
        for plugin_id in DESK_PLUGIN_PACK_IDS:
            require_desk_plugin_pack_id(plugin_id)
            raw = load_pack_manifest_raw(self.plugins_root / plugin_id)
            if raw.get("id") != plugin_id:
                raise PluginLoadError(
                    f"manifest id {raw.get('id')!r} does not match directory {plugin_id!r}",
                    plugin_id=plugin_id,
                    field="id",
                )
            desk = DESK_PLUGIN_PACK_DESKS[plugin_id]
            if raw.get("desk") != desk:
                raise PluginLoadError(
                    f"manifest desk {raw.get('desk')!r} must be {desk!r}",
                    plugin_id=plugin_id,
                    field="desk",
                )
            rows.append(raw)
        return tuple(rows)

    def parsed_manifests(self) -> tuple[PluginManifest, ...]:
        return tuple(parse_plugin_manifest(raw) for raw in self.raw_manifests())

    def activators(self) -> dict[str, PluginActivator]:
        loaded: dict[str, PluginActivator] = {}
        for manifest in self.parsed_manifests():
            loaded[manifest.id] = load_pack_activator(
                self.plugins_root / manifest.id,
                manifest.entrypoint,
            )
        return loaded

    def activate(
        self,
        *,
        principal: object = PrincipalClass.OPERATOR,
        correlation_id: object = "desk-pack-roster",
    ) -> Result[tuple[LoadedPlugin, ...]]:
        """Activate every pack through ``PluginLoader`` (core contribution surface)."""
        try:
            raw = self.raw_manifests()
            acts = self.activators()
        except (PluginLoadError, OSError, json.JSONDecodeError, ValueError) as exc:
            plugin_id = getattr(exc, "plugin_id", None)
            field = getattr(exc, "field", "manifest")
            return invalid_input(
                str(field) if isinstance(field, str) else "manifest",
                str(exc),
                plugin_id=plugin_id,
            )
        activated = self.loader.activate_roster(
            raw,
            activators=acts,
            principal=principal,
            correlation_id=correlation_id,
        )
        if not is_ok(activated):
            return activated
        ingested = self._ingest_activated(activated.value)
        if is_refusal(ingested):
            for row in reversed(activated.value):
                self.loader.unload(row.manifest.id)
            return ingested
        restored_authoring = self._rehydrate_enabled_authoring_contributions(
            principal=principal,
            correlation_id=correlation_id,
        )
        if is_refusal(restored_authoring):
            for row in reversed(activated.value):
                self.loader.unload(row.manifest.id)
            return restored_authoring
        return Ok(activated.value)

    def enable_published_authoring_contribution(
        self,
        contribution_id: str,
        *,
        principal: object = PrincipalClass.OPERATOR,
        correlation_id: object = "authoring-pack-enable",
    ) -> Result[LoadedPlugin]:
        if self.authoring_roster_root is None:
            return invalid_input(
                "authoring_roster_root",
                "local authoring roster is not configured for this daemon",
            )
        roster = AtomicRoster(self.authoring_roster_root)
        with roster.synchronized():
            return self._enable_published_authoring_contribution_locked(
                contribution_id,
                principal=principal,
                correlation_id=correlation_id,
                roster=roster,
                rehydrating=False,
            )

    def _require_authoring_operator(
        self,
        principal: object,
        *,
        command: str = "plugin.enable",
    ) -> Result[PrincipalClass]:
        return self.loader.require_operator(cast(LoadCommand, command), principal)

    def _authoring_uninstall_tombstoned(self, contribution_id: str) -> Result[bool]:
        if self.authoring_journal is None:
            return Ok(False)
        events = self.authoring_journal.read_events()
        if is_refusal(events):
            return events
        for event in events.value:
            payload = getattr(event, "payload", None)
            if (
                getattr(event, "event", None) == "editor_draft.uninstalled"
                and isinstance(payload, Mapping)
                and cast(Mapping[str, object], payload).get("contribution_id") == contribution_id
            ):
                return Ok(True)
        return Ok(False)

    @staticmethod
    def _authoring_plugin_id(contribution_id: str) -> str:
        digest = hashlib.sha256(contribution_id.encode("utf-8")).hexdigest()[:16]
        return f"research-authoring-{digest}"

    @staticmethod
    def _validated_authoring_identity(row: Mapping[str, object]) -> Result[tuple[str, str]]:
        contribution_id = row.get("contribution_id")
        qualified_id = row.get("qualified_id")
        version = row.get("version")
        revision = row.get("editor_revision")
        editor_draft_id = row.get("editor_draft_id")
        body = row.get("bytes")
        if (
            not isinstance(contribution_id, str)
            or not contribution_id.startswith("authoring-contribution:")
            or not isinstance(revision, str)
            or not isinstance(qualified_id, str)
            or not isinstance(version, str)
            or row.get("point") != "graph_template"
            or row.get("published") is not True
            or not isinstance(body, str)
            or not isinstance(row.get("enabled"), bool)
            or fingerprint_bytes(body.encode("utf-8")).value != revision
        ):
            return invalid_input(
                "authoring_roster", "generated authoring contribution is malformed"
            )
        prefix = "authoring-contribution:"
        suffix = f":{revision}"
        if not contribution_id.endswith(suffix):
            return invalid_input(
                "authoring_roster", "generated authoring contribution id is malformed"
            )
        derived_draft_id = contribution_id[len(prefix) : -len(suffix)]
        if (
            not derived_draft_id
            or (isinstance(editor_draft_id, str) and editor_draft_id != derived_draft_id)
            or (editor_draft_id is not None and not isinstance(editor_draft_id, str))
        ):
            return invalid_input(
                "authoring_roster", "generated authoring contribution id is malformed"
            )
        try:
            decoded = json.loads(body)
            if not isinstance(decoded, dict):
                raise ValueError("generated graph template bytes must encode an object")
            parsed = _graph_template_from_mapping(cast(Mapping[str, object], decoded))
        except (TypeError, ValueError, json.JSONDecodeError, PluginLoadError) as exc:
            return invalid_input("authoring_roster", str(exc))
        if parsed.qualified_id != qualified_id or parsed.version != version:
            return invalid_input(
                "authoring_roster", "generated authoring contribution bytes do not match identity"
            )
        return Ok((qualified_id, version))

    def _authoring_plugin_matches(
        self,
        contribution_id: str,
        qualified_id: str,
        version: str,
    ) -> bool:
        loaded = self.loader.get(self._authoring_plugin_id(contribution_id))
        if loaded is None:
            return False
        multis = cast(Mapping[object, object], loaded.context.snapshot()["multis"])
        return any(
            isinstance(value, Mapping)
            and cast(Mapping[str, object], value).get("qualified_id") == qualified_id
            and cast(Mapping[str, object], value).get("version") == version
            for value in multis.values()
        )

    def _remove_authoring_runtime(
        self,
        contribution_id: str,
        qualified_id: str,
        version: str,
    ) -> Result[None]:
        loaded = self.loader.get(self._authoring_plugin_id(contribution_id))
        if loaded is None:
            # The exact catalog tuple may have been claimed by another provider
            # after this generated plugin was removed. Without a live generated
            # owner, an idempotent retry must not unregister that provider.
            return Ok(None)
        if not self._authoring_plugin_matches(contribution_id, qualified_id, version):
            return policy_rejection(
                "contribution_id",
                "generated plugin identity does not match the targeted authoring contribution",
                contribution_id=contribution_id,
            )
        self.loader.unload(self._authoring_plugin_id(contribution_id))
        self.templates.unregister_version(qualified_id, version)
        return Ok(None)

    def disable_published_authoring_contribution(
        self,
        contribution_id: str,
        *,
        principal: object,
    ) -> Result[None]:
        """Durably disable one generated authoring contribution as an operator."""
        authorized = self._require_authoring_operator(principal)
        if is_refusal(authorized):
            return authorized
        if self.authoring_roster_root is None:
            return invalid_input(
                "authoring_roster_root",
                "local authoring roster is not configured for this daemon",
            )
        roster = AtomicRoster(self.authoring_roster_root)
        with roster.synchronized():
            loaded = roster.load()
            if is_refusal(loaded):
                return loaded
            rows = loaded.value.get("published", [])
            if not isinstance(rows, list):
                return invalid_input("authoring_roster", "published roster must be a list")
            selected = next(
                (
                    cast(Mapping[str, object], item)
                    for item in cast(list[object], rows)
                    if isinstance(item, Mapping)
                    and cast(Mapping[str, object], item).get("contribution_id") == contribution_id
                ),
                None,
            )
            if selected is None:
                return invalid_input(
                    "contribution_id", "published authoring contribution is not present"
                )
            identity = self._validated_authoring_identity(selected)
            if is_refusal(identity):
                return identity
            if selected.get("enabled") is True:
                replacement = dict(loaded.value)
                replacement["published"] = [
                    {**dict(cast(Mapping[str, object], item)), "enabled": False}
                    if isinstance(item, Mapping)
                    and cast(Mapping[str, object], item).get("contribution_id") == contribution_id
                    else item
                    for item in cast(list[object], rows)
                ]
                saved = roster.publish(replacement)
                if is_refusal(saved):
                    return saved
            removed = self._remove_authoring_runtime(
                contribution_id,
                identity.value[0],
                identity.value[1],
            )
            if is_refusal(removed):
                return removed
        return Ok(None)

    def retire_replaced_authoring_contribution(
        self,
        contribution_id: str,
        qualified_id: str,
        version: str,
        *,
        principal: object,
    ) -> Result[None]:
        """Remove one exact predecessor from the live publication domain."""
        authorized = self._require_authoring_operator(principal)
        if is_refusal(authorized):
            return authorized
        if self.authoring_roster_root is None:
            return invalid_input(
                "authoring_roster_root",
                "local authoring roster is not configured for this daemon",
            )
        with AtomicRoster(self.authoring_roster_root).synchronized():
            return self._remove_authoring_runtime(contribution_id, qualified_id, version)

    def uninstall_published_authoring_contribution(
        self,
        contribution_id: str,
        *,
        principal: object,
    ) -> Result[None]:
        """Remove one disabled contribution, journal its tombstone, and clean exact runtime."""
        authorized = self._require_authoring_operator(principal, command="plugin.install")
        if is_refusal(authorized):
            return authorized
        if self.authoring_roster_root is None:
            return invalid_input(
                "authoring_roster_root",
                "local authoring roster is not configured for this daemon",
            )
        if self.authoring_journal is None:
            return invalid_input(
                "authoring_journal",
                "authoring uninstall requires the authoritative journal",
            )
        roster = AtomicRoster(self.authoring_roster_root)
        with roster.synchronized():
            loaded = roster.load()
            if is_refusal(loaded):
                return loaded
            rows = loaded.value.get("published", [])
            if not isinstance(rows, list):
                return invalid_input("authoring_roster", "published roster must be a list")
            typed_rows = cast(list[object], rows)
            matching = next(
                (
                    cast(Mapping[str, object], item)
                    for item in typed_rows
                    if isinstance(item, Mapping)
                    and cast(Mapping[str, object], item).get("contribution_id") == contribution_id
                ),
                None,
            )
            if matching is None:
                return invalid_input(
                    "contribution_id", "published authoring contribution is not present"
                )
            identity = self._validated_authoring_identity(matching)
            if is_refusal(identity):
                return identity
            if matching.get("enabled") is True:
                return policy_rejection(
                    "contribution_id",
                    "disable an authoring contribution before uninstall",
                    contribution_id=contribution_id,
                )
            remainder = contribution_id[len("authoring-contribution:") :]
            revision = matching.get("editor_revision")
            suffix = f":{revision}" if isinstance(revision, str) else ""
            if not suffix or not remainder.endswith(suffix):
                return invalid_input(
                    "contribution_id", "published editor draft identity is malformed"
                )
            draft_id = remainder[: -len(suffix)]
            if not draft_id:
                return invalid_input(
                    "contribution_id", "published editor draft identity is malformed"
                )
            # The tombstone is authoritative; a subsequent roster write can be
            # repaired from it if the process stops between these operations.
            tombstone = self.authoring_journal.append_event(
                "editor_draft.uninstalled",
                payload={
                    "contribution_id": contribution_id,
                    "editor_draft_id": draft_id,
                    "qualified_id": identity.value[0],
                    "version": identity.value[1],
                    "editor_revision": revision,
                },
            )
            if is_refusal(tombstone):
                return tombstone
            replacement = dict(loaded.value)
            replacement["published"] = [
                dict(cast(Mapping[str, object], item))
                for item in typed_rows
                if not (
                    isinstance(item, Mapping)
                    and cast(Mapping[str, object], item).get("contribution_id") == contribution_id
                )
            ]
            saved = roster.publish(replacement)
            if is_refusal(saved):
                return saved
            removed = self._remove_authoring_runtime(
                contribution_id,
                identity.value[0],
                identity.value[1],
            )
            if is_refusal(removed):
                return removed
        return Ok(None)

    def _enable_published_authoring_contribution_locked(
        self,
        contribution_id: str,
        *,
        principal: object,
        correlation_id: object,
        roster: AtomicRoster,
        rehydrating: bool,
    ) -> Result[LoadedPlugin]:
        """Enable one daemon-published draft through the production PluginLoader.

        Publishing a draft only stages it in the local authoring roster. This
        explicit operator path is the existing plugin enable flow: the
        contribution becomes live only after ``PluginLoader.enable`` accepts
        its generated manifest and scoped registration.
        """
        if self.authoring_roster_root is None:
            return invalid_input(
                "authoring_roster_root",
                "local authoring roster is not configured for this daemon",
            )
        tombstoned = self._authoring_uninstall_tombstoned(contribution_id)
        if is_refusal(tombstoned):
            return tombstoned
        if tombstoned.value:
            return policy_rejection(
                "contribution_id",
                "uninstalled authoring contributions cannot be re-enabled",
                contribution_id=contribution_id,
            )
        loaded_roster = roster.load()
        if is_refusal(loaded_roster):
            return loaded_roster
        published = loaded_roster.value.get("published", [])
        if not isinstance(published, list):
            return invalid_input("authoring_roster", "published roster must be a list")
        record: Mapping[str, object] | None = None
        for candidate in cast(list[object], published):
            if not isinstance(candidate, Mapping):
                continue
            mapping = cast(Mapping[str, object], candidate)
            if mapping.get("contribution_id") == contribution_id:
                record = mapping
                break
        if record is None:
            return invalid_input(
                "contribution_id",
                "published authoring contribution is not present in the local roster",
            )
        enabled_flag = record.get("enabled") is True
        if record.get("point") != "graph_template":
            return invalid_input("point", "authoring enable supports graph_template only")
        try:
            body = record.get("bytes")
            if not isinstance(body, str):
                raise ValueError("published graph template bytes must be text")
            decoded = json.loads(body)
            if not isinstance(decoded, dict):
                raise ValueError("published graph template must be a JSON object")
            template = cast(dict[str, object], decoded)
            qualified_id = record.get("qualified_id")
            version = record.get("version")
            if not isinstance(qualified_id, str) or not isinstance(version, str):
                raise ValueError("published graph template identity is malformed")
            if template.get("qualified_id") != qualified_id or template.get("version") != version:
                raise ValueError("published graph template identity does not match its roster row")
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            return invalid_input("authoring_roster", str(exc))

        digest = hashlib.sha256(contribution_id.encode("utf-8")).hexdigest()[:16]
        plugin_id = f"research-authoring-{digest}"
        already_loaded = self.loader.get(plugin_id)
        if already_loaded is not None:
            if enabled_flag:
                return Ok(already_loaded)
            return invalid_input(
                "contribution_id",
                "authoring contribution is already live in the PluginLoader",
                contribution_id=contribution_id,
            )
        if enabled_flag and not rehydrating:
            # An enabled roster row may be replayed after process restart. The
            # ordinary enable request is idempotent and reuses that live path.
            rehydrating = True
        local_id = "draft-template"
        contribution = dict(template)
        contribution.update(
            {
                "qualified_id": qualified_id,
                "version": version,
                "stateless": True,
                "runtime_state": None,
            }
        )

        def activate(context: PluginContext) -> None:
            context.register_graph_template(local_id, contribution)

        raw_manifest: dict[str, object] = {
            "id": plugin_id,
            "version": version,
            "qma_api": ">=0.1.0,<1.0.0",
            "desk": "research",
            "entrypoint": "daemon.plugin:activate",
            "dependencies": [],
            "contributions": [
                {
                    "point": "graph_template",
                    "local_id": local_id,
                    "qualified_id": qualified_id,
                }
            ],
            "permissions": [],
            "migrations": [],
            "peer_integration": "qma_wire_only",
            "daemon_renders": False,
        }
        loader_snapshot = self.loader.snapshot_published_roster()
        loaded_before = set(self.loader.loaded_ids())
        template_snapshot = self.templates.snapshot()

        def rollback() -> None:
            for loaded_id in reversed(self.loader.loaded_ids()):
                if loaded_id not in loaded_before:
                    self.loader.unload(loaded_id)
            self.loader.restore_published_roster(loader_snapshot)
            self.templates.restore(template_snapshot)

        enabled = self.loader.enable(
            raw_manifest,
            activator=cast(PluginActivator, activate),
            principal=principal,
            correlation_id=correlation_id,
        )
        if is_refusal(enabled):
            return enabled
        ingested = self._ingest_graph_templates(enabled.value)
        if is_refusal(ingested):
            rollback()
            return ingested

        if rehydrating and enabled_flag:
            return enabled

        replacement = dict(loaded_roster.value)
        replacement_published: list[object] = []
        for item in cast(list[object], published):
            if isinstance(item, Mapping):
                replacement_published.append(dict(cast(Mapping[str, object], item)))
            else:
                replacement_published.append(item)
        for item in replacement_published:
            if isinstance(item, dict):
                row = cast(dict[str, object], item)
                if row.get("contribution_id") == contribution_id:
                    row["enabled"] = True
        replacement["published"] = replacement_published
        saved = roster.publish(replacement)
        if is_refusal(saved):
            rollback()
            return saved
        return enabled

    def _rehydrate_enabled_authoring_contributions(
        self,
        *,
        principal: object,
        correlation_id: object,
    ) -> Result[None]:
        if self.authoring_roster_root is None:
            return Ok(None)
        roster = AtomicRoster(self.authoring_roster_root)
        with roster.synchronized():
            loaded = roster.load()
            if is_refusal(loaded):
                return loaded
            rows = loaded.value.get("published", [])
            if not isinstance(rows, list):
                return invalid_input("authoring_roster", "published roster must be a list")
            initial_plugins = set(self.loader.loaded_ids())
            initial_roster = self.loader.snapshot_published_roster()
            initial_templates = self.templates.snapshot()

            def rollback_rehydration() -> None:
                for loaded_id in reversed(self.loader.loaded_ids()):
                    if loaded_id not in initial_plugins:
                        self.loader.unload(loaded_id)
                self.loader.restore_published_roster(initial_roster)
                self.templates.restore(initial_templates)

            for candidate in cast(list[object], rows):
                if not isinstance(candidate, Mapping):
                    continue
                entry = cast(Mapping[str, object], candidate)
                if entry.get("enabled") is not True:
                    continue
                contribution_id = entry.get("contribution_id")
                if not isinstance(contribution_id, str) or not contribution_id:
                    rollback_rehydration()
                    return invalid_input(
                        "authoring_roster",
                        "enabled contribution requires a stable contribution_id",
                    )
                restored = self._enable_published_authoring_contribution_locked(
                    contribution_id,
                    principal=principal,
                    correlation_id=correlation_id,
                    roster=roster,
                    rehydrating=True,
                )
                if is_refusal(restored):
                    rollback_rehydration()
                    return restored
        return Ok(None)

    def _ingest_activated(self, loaded: Sequence[LoadedPlugin]) -> Result[None]:
        for row in loaded:
            declared = self._assert_declared_registered(row)
            if is_refusal(declared):
                return declared
            templates = self._ingest_graph_templates(row)
            if is_refusal(templates):
                return templates
            bound = self._bind_singletons(row)
            if is_refusal(bound):
                return bound
        analysis = self.loader.get(ANALYSIS_BACKTEST_PLUGIN_ID)
        if analysis is None:
            return invalid_input(
                "analysis-backtest",
                "analysis-backtest must be activated as the Backtesting Service adapter",
            )
        installed = self.backtesting.install(context=analysis.context)
        if is_refusal(installed):
            return installed
        if installed.value.tool_id != QMB_BACKTEST_TOOL_ID:
            return invalid_input("tool_id", "analysis-backtest exposes one qmb tool")
        return Ok(None)

    def _assert_declared_registered(self, loaded: LoadedPlugin) -> Result[None]:
        snap = loaded.context.snapshot()
        singletons = cast(Mapping[object, object], snap["singletons"])
        multis = cast(Mapping[object, object], snap["multis"])
        for decl in loaded.manifest.contributions:
            if decl.cardinality is Cardinality.SINGLETON:
                found = any(
                    isinstance(key, tuple)
                    and len(cast(tuple[object, ...], key)) == 2
                    and cast(tuple[object, ...], key)[0] == decl.point
                    for key in singletons
                )
                if not found:
                    return invalid_input(
                        decl.point,
                        "declared singleton was not registered through PluginContext",
                        plugin_id=loaded.manifest.id,
                    )
            elif decl.local_id is not None:
                key = (decl.point, f"{loaded.manifest.id}:{decl.local_id}")
                if key not in multis:
                    return invalid_input(
                        decl.point,
                        "declared multi contribution was not registered through PluginContext",
                        plugin_id=loaded.manifest.id,
                        local_id=decl.local_id,
                    )
        return Ok(None)

    def _ingest_graph_templates(self, loaded: LoadedPlugin) -> Result[None]:
        snap = loaded.context.snapshot()
        multis = cast(Mapping[object, object], snap["multis"])
        for key, value in multis.items():
            if not isinstance(key, tuple):
                continue
            pair = cast(tuple[object, ...], key)
            if len(pair) != 2 or pair[0] != "graph_template":
                continue
            if not isinstance(value, Mapping):
                return invalid_input(
                    "graph_template",
                    "graph_template contribution must be a mapping",
                    plugin_id=loaded.manifest.id,
                )
            mapping = cast(Mapping[str, object], value)
            if mapping.get("stateless") is not True or mapping.get("runtime_state") is not None:
                return policy_rejection(
                    "graph_template",
                    "Graph Template remains an authored, versioned, stateless definition "
                    "(FR-Q71; AD-13)",
                    plugin_id=loaded.manifest.id,
                    qualified_id=mapping.get("qualified_id"),
                )
            try:
                template = _graph_template_from_mapping(mapping)
            except (PluginLoadError, ValueError, TypeError) as exc:
                return invalid_input("graph_template", str(exc), plugin_id=loaded.manifest.id)
            registered = self.templates.register(template)
            if is_refusal(registered):
                return registered
        return Ok(None)

    def _bind_singletons(self, loaded: LoadedPlugin) -> Result[None]:
        snap = loaded.context.snapshot()
        singletons = cast(Mapping[object, object], snap["singletons"])
        for key, value in singletons.items():
            if not isinstance(key, tuple):
                continue
            pair = cast(tuple[object, ...], key)
            if len(pair) != 2:
                continue
            port, scope_value = pair
            if port == "MemoryProvider" and isinstance(scope_value, str):
                bound = self.memory.bind(
                    scope_value,
                    cast(MemoryProvider, value),
                    plugin_id=loaded.manifest.id,
                )
                if is_refusal(bound):
                    return bound
            if port == "KnowledgeSource" and isinstance(scope_value, str):
                bound_k = self.knowledge.bind(
                    scope_value,
                    cast(KnowledgeSource, value),
                    plugin_id=loaded.manifest.id,
                )
                if is_refusal(bound_k):
                    return bound_k
        return Ok(None)

    def published_tool_ids(self) -> frozenset[str]:
        return frozenset(
            row.qualified_id
            for row in self.loader.published_contributions()
            if row.point == "tool" and row.qualified_id is not None
        )

    def spawn_constrained(
        self,
        request: SpawnRequest,
    ) -> Result[Agent | Subagent]:
        """Spawn with the pack contribution set as the Agent-spawn ceiling."""
        published = self.published_tool_ids()
        requested_pack = {
            tool_id
            for tool_id in request.role_base.tool_ids
            if tool_id.split(":", 1)[0] in DESK_PLUGIN_PACK_IDS
        }
        extras = sorted(requested_pack - published)
        if extras:
            return policy_rejection(
                "effective_capabilities",
                "Agent spawn may not grant a desk-pack tool that was not published "
                "through PluginContext (FR-Q71; AD-16)",
                extras=extras,
            )
        return spawn_agent(request)

    def refuse_promote(self, *, surface: str = "artifact") -> Result[None]:
        """Promote is a human live-zone act outside QMA (DEC-0345)."""
        if surface == "memory":
            return refuse_memory_promote()
        return self.proposals.promote_refused("outside-qma")

    def snapshot(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "pack_ids": list(DESK_PLUGIN_PACK_IDS),
                "desks": dict(DESK_PLUGIN_PACK_DESKS),
                "loaded": list(self.loader.loaded_ids()),
                "published": [
                    dict(row.to_payload()) for row in self.loader.published_contributions()
                ],
                "qmb_tool_id": QMB_BACKTEST_TOOL_ID,
                "scheduling_authority": self.backtesting.scheduling_authority,
                "parallelism": self.backtesting.parallelism,
                "backtest_state": self.backtesting.backtest_state,
                "qmb_owned": sorted(QMB_OWNED_CONCERNS),
                "memory_candidates_admitted": MEMORY_CANDIDATES_ARE_ADMITTED,
                "refinement_proposals_applied": REFINEMENT_PROPOSALS_ARE_APPLIED,
                "promote_is_human_outside_qma": PROMOTE_IS_HUMAN_OUTSIDE_QMA,
            }
        )
