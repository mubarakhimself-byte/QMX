"""Mount minimum discovery reads on the live roster, without a new store.

No filesystem scan, grant mint, readiness inference or executable payload is
returned. Contribution pin validation uses the existing owner at read time.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

from qma.daemon.discovery.federated import FederatedDiscoveryService
from qma.daemon.plugins.loader import PluginLoader
from qma.daemon.plugins.pins import ContributionPinService
from qma.wire.contribution_pin import ContributionPin
from qma.wire.discovery_queries import DISCOVERY_SCHEMA, parse_discovery_args
from qma.wire.federated_discovery import ContributionHit, parse_federated_hit
from qma.wire.list_mailbox import query_unavailable
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import policy_rejection


@dataclass(frozen=True)
class DiscoveryQueryService:
    """A read-only adapter to existing roster/federation/pin owners."""

    loader: PluginLoader
    session_scope: Callable[[object], Result[str | None]]

    def query(self, name: str, args: object) -> Result[Mapping[str, object]]:
        parsed = parse_discovery_args(name, args)
        if is_refusal(parsed):
            return parsed
        params = parsed.value
        scoped = self.session_scope(params.get("product_session_ref"))
        if is_refusal(scoped):
            return scoped
        scope = scoped.value
        if name == "list_installed_plugins":
            plugins: list[dict[str, object]] = []
            for plugin_id in self.loader.loaded_ids():
                loaded = self.loader.get(plugin_id)
                if loaded is None or (scope is not None and loaded.instance_id != scope):
                    continue
                plugins.append(
                    {
                        "plugin_id": loaded.manifest.id,
                        "package_id": loaded.manifest.id,
                        "package_version": loaded.manifest.version,
                        "instance_id": loaded.instance_id,
                        "availability_revision": loaded.availability_revision,
                        "availability": "enabled",
                    }
                )
            return Ok(
                {
                    "schema": DISCOVERY_SCHEMA,
                    "plugins": plugins,
                    "roster_revision": self.loader.availability_revision(),
                    "authorizes_invoke": False,
                }
            )
        if name == "facade_search":
            if params["hit_class"] != "contribution":
                return query_unavailable(name + ":" + str(params["hit_class"]))
            searched = FederatedDiscoveryService.search_contributions(
                self.loader, cast(str, params["query"])
            )
            if is_refusal(searched):
                return searched
            hits = [
                dict(hit.to_payload())
                for hit in searched.value
                if scope is None
                or (
                    (loaded := self.loader.get(hit.plugin_id)) is not None
                    and loaded.instance_id == scope
                )
            ]
            return Ok(
                {
                    "schema": DISCOVERY_SCHEMA,
                    "hits": hits,
                    "query": params["query"],
                    "hit_class": "contribution",
                    "roster_revision": self.loader.availability_revision(),
                    "authorizes_invoke": False,
                }
            )
        parsed_hit = parse_federated_hit(params["hit"])
        if is_refusal(parsed_hit):
            return parsed_hit
        hit = parsed_hit.value
        if not isinstance(hit, ContributionHit):
            return query_unavailable(name + ":" + hit.hit_class)
        loaded = self.loader.get(hit.plugin_id)
        if loaded is not None and scope is not None and loaded.instance_id != scope:
            return policy_rejection("instance_id", "contribution is outside product session scope")
        pin = ContributionPin.from_hit(hit)
        if is_refusal(pin):
            return pin
        admitted = ContributionPinService(self.loader).revalidate(pin.value)
        if is_refusal(admitted):
            return admitted
        if loaded is None or admitted.value.live != hit:
            return policy_rejection("hit", "exact live contribution identity must match")
        return Ok(
            {
                "schema": DISCOVERY_SCHEMA,
                "hit": dict(hit.to_payload()),
                "instance_id": loaded.instance_id,
                "availability_revision": loaded.availability_revision,
                "authorizes_invoke": False,
            }
        )
