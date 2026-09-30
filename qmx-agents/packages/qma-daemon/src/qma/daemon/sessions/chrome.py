"""Story 55.4 — a tab/window/view is not a product_session.

Chrome (tab, window, view) does not own grants or occupancy. Occupancy stays
none. ``view:*`` remains an AD-17 wire DTO only — not a plugin contribution
point and not a ContributionHit (GAP-0081; SCN-0018 Branch B). GAP-0081
chrome is not filled.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, cast
from uuid import uuid4

from qma.core.operations import public_operation_descriptors
from qma.core.ports.extensibility import (
    GAP_0081_STATUS,
    QMA_UI_CONTRACT_STATUS,
    UI_VIEW_CONTRIBUTION_POINT,
    register_ui_widget_contribution,
    ui_view_contribution_point_minted,
)
from qma.core.vocabulary.enums import GrantEvaluationMoment
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.plugins.loader import LoadedPlugin, PluginLoader, PublishedContribution
from qma.daemon.sessions.product_session import (
    CHROME_KINDS,
    CHROME_OWNS_GRANTS,
    CHROME_OWNS_OCCUPANCY,
    GAP_0081_CHROME_FILLED,
    PRODUCT_SESSION_NEW_CT_MINTED,
    PRODUCT_SESSION_OCCUPANCY,
    PRODUCT_SESSION_SIXTH_STORE_MINTED,
    PRODUCT_SESSION_TAB_WRITES,
    ProductSession,
    ProductSessionService,
    looks_like_chrome_id,
    refuse_chrome_owns_grants,
    refuse_chrome_owns_occupancy,
    refuse_tab_as_product_session,
    refuse_tab_mints_session,
)
from qma.wire.action_context import ActionContext, validate_action_context_press
from qma.wire.contribution_listing import refuse_hit_as_grant
from qma.wire.federated_discovery import ContributionHit, parse_federated_hit
from qma.wire.grant_record import GrantRecord
from qma.wire.invocation_envelope import OperationDescriptor, format_utc_iso_z
from qma.wire.pack_ui_request import PackUiView
from qma.wire.view_presentation import (
    VIEW_FILLS_GAP_0081_CHROME,
    VIEW_IS_CONTRIBUTION_HIT,
    VIEW_IS_PLUGIN_CONTRIBUTION_POINT,
    VIEW_IS_PRODUCT_SESSION,
    VIEW_OWNS_GRANTS,
    VIEW_PRESENTATION_OCCUPANCY,
    ViewPresentation,
    parse_view_presentation,
    refuse_view_as_contribution_hit,
    refuse_view_durable_work,
)
from qmf.core.chrono import Instant
from qmf.core.refusal import Ok, RefusalCategory, Result, Retryability, TypedRefusal, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "CHROME_KINDS",
    "CHROME_OWNS_GRANTS",
    "CHROME_OWNS_OCCUPANCY",
    "GAP_0081_CHROME_FILLED",
    "VIEW_FILLS_GAP_0081_CHROME",
    "VIEW_IS_CONTRIBUTION_HIT",
    "VIEW_IS_PLUGIN_CONTRIBUTION_POINT",
    "VIEW_IS_PRODUCT_SESSION",
    "VIEW_OWNS_GRANTS",
    "PackUiMount",
    "ProductSessionChrome",
    "looks_like_chrome_id",
    "refuse_chrome_owns_grants",
    "refuse_chrome_owns_occupancy",
    "refuse_tab_as_product_session",
    "refuse_view_as_contribution_hit",
]


CHROME_GAP: Final[str] = "GAP-0081"
CHROME_UI_CONTRACT_STATUS: Final[str] = QMA_UI_CONTRACT_STATUS
CHROME_UI_VIEW_MINTED: Final[bool] = ui_view_contribution_point_minted()
_NATIVE_ADAPTER_AVAILABLE: Final[bool] = True


@dataclass(frozen=True, slots=True)
class PackUiMount:
    """Opaque host mount handle; context and operation binding are host-owned."""

    mount_id: str
    instance_id: str
    view: PackUiView
    renderer: str
    pane: str
    action_context: ActionContext | None
    diagnostics: tuple[str, ...] = ()


def _chrome_token(value: object, field: str) -> Result[str]:
    if not isinstance(value, str) or value.strip() == "":
        return invalid_input(field, f"{field} is a non-empty string", given=repr(value))
    token = value.strip()
    if token.startswith(("psess:", "sess:")):
        return refuse_tab_as_product_session(given=token, field=field)
    return Ok(token)


@dataclass
class ProductSessionChrome:
    """Query-only tab/window/view surface over a journaled product_session."""

    sessions: ProductSessionService = field(default_factory=ProductSessionService)
    journal: AuthoritativeJournal | None = None
    _mounts: dict[str, PackUiMount] = field(default_factory=dict[str, PackUiMount], init=False)

    def mount_pack_ui_view(
        self,
        *,
        product_session_id: object,
        view_id: object,
        loader: PluginLoader,
    ) -> Result[PackUiMount]:
        """Resolve the live view and all invocation bindings from host state."""
        session = self.sessions.get(product_session_id)
        if is_refusal(session):
            return session
        instance = session.value.app_instance_id or session.value.context.instance_id
        if instance is None:
            chosen = tuple(
                item.id for item in session.value.selected_refs if item.kind == "instance_id"
            )
            if len(chosen) != 1:
                return policy_rejection(
                    "instance_id",
                    "mount requires an app instance or exactly one selected instance ref",
                    selected_instance_count=len(chosen),
                )
            instance = chosen[0]
        if not instance.strip():
            return policy_rejection("instance_id", "product session has no enabled instance")
        plugin_id = instance.removeprefix("pack:")
        loaded = loader.get(plugin_id)
        if loaded is None or loaded.instance_id != instance or loaded.pack_ui_request is None:
            return policy_rejection(
                "instance_id",
                "selected pack instance is not currently enabled",
                instance_id=instance,
            )
        if not isinstance(view_id, str):
            return invalid_input("view_id", "view_id must select a recorded view")
        view = next(
            (item for item in loaded.pack_ui_request.request.views if item.view_id == view_id),
            None,
        )
        if view is None:
            return policy_rejection("view_id", "view is not in the recorded PackUiRequest")

        descriptor = next(
            (item for item in public_operation_descriptors() if item.op_id == view.op_id),
            None,
        )
        if descriptor is None or descriptor.input_schema != view.parameter_schema:
            return self._empty_mount(instance, view, "operation_descriptor_unavailable")
        contribution = self._resolve_contribution(loader, loaded, view, descriptor)
        if is_refusal(contribution):
            return contribution

        diagnostic = self._renderer_diagnostic(view)
        if diagnostic is not None:
            return self._empty_mount(instance, view, diagnostic)
        if self.journal is None:
            return self._empty_mount(instance, view, "host_journal_unavailable")
        events = self.journal.read_events()
        if is_refusal(events):
            return events
        snapshot_cursor = events.value[-1].journal_seq if events.value else 0
        timestamp = self.journal.stamp_durable()
        if is_refusal(timestamp):
            return timestamp
        now = format_utc_iso_z(Instant(value_ns=timestamp.value.recorded_at))

        grants = self.sessions.granted_records(session.value.product_session_id)
        if is_refusal(grants):
            return grants
        config_revision = session.value.context.config_revision
        matching: list[GrantRecord] = []
        for grant in grants.value:
            if (
                grant.audience != session.value.product_session_id
                or grant.instance_id != instance
                or grant.config_revision != config_revision
                or grant.op_id != descriptor.op_id
                or grant.op_version != descriptor.version
                or grant.contribution.qualified_id != contribution.value.qualified_id
                or grant.contribution.package_version != loaded.manifest.version
            ):
                continue
            active = self.sessions.ledger.evaluate(
                grant_id=grant.grant_id,
                moment=GrantEvaluationMoment.ACCEPT,
                now=now,
            )
            if not is_refusal(active):
                matching.append(active.value)
            elif active.context.get("code") != "GRANT_INACTIVE":
                return active
        if len(matching) > 1:
            return TypedRefusal(
                category=RefusalCategory.POLICY_REJECTION,
                retryability=Retryability.AFTER_CONDITION,
                context=MappingProxyType(
                    {
                        "field": "grant_id",
                        "reason": "multiple active GrantRecords match this exact mount",
                        "refusal": "GRANT_AMBIGUOUS",
                        "instance_id": instance,
                        "op_id": descriptor.op_id,
                        "product_session_id": session.value.product_session_id,
                    }
                ),
                after_condition_descriptor="the operator leaves exactly one matching GrantRecord",
            )
        selected: GrantRecord | None = matching[0] if matching else None
        built = ActionContext.try_create(
            psess=session.value.product_session_id,
            view_id=view.view_id,
            qualified_id=contribution.value.qualified_id,
            package_version=loaded.manifest.version,
            instance_id=instance,
            config_revision=config_revision,
            grant_id=None if selected is None else selected.grant_id,
            allowed_op_ids=() if selected is None else (descriptor.op_id,),
            account_scope=None if selected is None else selected.account_scope,
            snapshot_cursor=snapshot_cursor,
            operation_descriptor=descriptor,
            parameter_allow_keys=(
                () if selected is None else selected.parameter_ceiling.allow_keys
            ),
        )
        if is_refusal(built):
            return built
        mount = PackUiMount(
            mount_id=f"pack-ui-mount:{uuid4().hex}",
            instance_id=instance,
            view=view,
            renderer=view.renderer,
            pane="native",
            action_context=built.value,
        )
        self._mounts[mount.mount_id] = mount
        return Ok(mount)

    def press_pack_ui_action(
        self, mount_id: object, payload: object
    ) -> Result[Mapping[str, object]]:
        """Validate a renderer press against the immutable server-owned mount."""
        if not isinstance(mount_id, str) or mount_id not in self._mounts:
            return policy_rejection("mount_id", "unknown or disposed Pack UI mount")
        mount = self._mounts[mount_id]
        if mount.action_context is None:
            return policy_rejection("mount_id", "empty renderer mount cannot dispatch actions")
        return validate_action_context_press(payload, context=mount.action_context)

    def unmount_pack_ui_view(self, mount_id: object) -> bool:
        """Invalidate a mount context without cancelling any accepted work."""
        return self._mounts.pop(mount_id, None) is not None if isinstance(mount_id, str) else False

    def _empty_mount(
        self, instance_id: str, view: PackUiView, diagnostic: str
    ) -> Result[PackUiMount]:
        mount = PackUiMount(
            mount_id=f"pack-ui-mount:{uuid4().hex}",
            instance_id=instance_id,
            view=view,
            renderer=view.renderer,
            pane="empty",
            action_context=None,
            diagnostics=(diagnostic,),
        )
        self._mounts[mount.mount_id] = mount
        return Ok(mount)

    @staticmethod
    def _renderer_diagnostic(view: PackUiView) -> str | None:
        if view.renderer == "native" and _NATIVE_ADAPTER_AVAILABLE:
            return None
        if view.renderer == "mcp-app" and not view.ui_resource:
            return "mcp_app_resource_missing"
        if view.renderer == "json-render" and not view.catalog_ref:
            return "json_render_catalog_missing"
        return "renderer_adapter_unavailable"

    @staticmethod
    def _resolve_contribution(
        loader: PluginLoader,
        loaded: LoadedPlugin,
        view: PackUiView,
        descriptor: OperationDescriptor,
    ) -> Result[PublishedContribution]:
        manifest = loaded.manifest
        candidates: list[PublishedContribution] = []
        for declared in manifest.contributes:
            if declared.point != "tool":
                continue
            qualified_id = declared.qualified_id or f"{manifest.id}:{declared.local_id}"
            local_id = declared.local_id
            if view.op_id not in {local_id, qualified_id}:
                continue
            published = next(
                (
                    row
                    for row in loader.published_contributions()
                    if row.plugin_id == manifest.id
                    and row.package_version == manifest.version
                    and row.availability_revision == loaded.availability_revision
                    and row.point == declared.point
                    and row.qualified_id == qualified_id
                ),
                None,
            )
            if published is not None:
                candidates.append(published)
        if len(candidates) != 1 or candidates[0].qualified_id is None:
            return policy_rejection(
                "op_id",
                "view operation does not resolve to one canonical published tool contribution",
                op_id=view.op_id,
            )
        return Ok(candidates[0])

    @property
    def occupancy(self) -> str:
        return PRODUCT_SESSION_OCCUPANCY

    @property
    def tab_writes(self) -> bool:
        return PRODUCT_SESSION_TAB_WRITES

    @property
    def chrome_owns_grants(self) -> bool:
        return CHROME_OWNS_GRANTS

    @property
    def chrome_owns_occupancy(self) -> bool:
        return CHROME_OWNS_OCCUPANCY

    @property
    def gap_0081_chrome_filled(self) -> bool:
        return GAP_0081_CHROME_FILLED

    @property
    def view_is_contribution_hit(self) -> bool:
        return VIEW_IS_CONTRIBUTION_HIT

    @property
    def view_is_plugin_contribution_point(self) -> bool:
        return VIEW_IS_PLUGIN_CONTRIBUTION_POINT

    @property
    def sixth_store_minted(self) -> bool:
        return PRODUCT_SESSION_SIXTH_STORE_MINTED

    @property
    def new_ct_minted(self) -> bool:
        return PRODUCT_SESSION_NEW_CT_MINTED

    def identity(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "chrome_kinds": sorted(CHROME_KINDS),
                "chrome_owns_grants": CHROME_OWNS_GRANTS,
                "chrome_owns_occupancy": CHROME_OWNS_OCCUPANCY,
                "gap": CHROME_GAP,
                "gap_0081_chrome_filled": GAP_0081_CHROME_FILLED,
                "gap_status": GAP_0081_STATUS,
                "occupancy": PRODUCT_SESSION_OCCUPANCY,
                "tab_writes": PRODUCT_SESSION_TAB_WRITES,
                "ui_contract_status": CHROME_UI_CONTRACT_STATUS,
                "ui_view_minted": CHROME_UI_VIEW_MINTED,
                "view_fills_gap_0081_chrome": VIEW_FILLS_GAP_0081_CHROME,
                "view_is_contribution_hit": VIEW_IS_CONTRIBUTION_HIT,
                "view_is_plugin_contribution_point": VIEW_IS_PLUGIN_CONTRIBUTION_POINT,
                "view_is_product_session": VIEW_IS_PRODUCT_SESSION,
                "view_owns_grants": VIEW_OWNS_GRANTS,
            }
        )

    def open_tab(
        self,
        *,
        tab_id: object,
        app_instance_id: object | None = None,
        product_session_id: object | None = None,
    ) -> Result[ProductSession]:
        return self.sessions.open_tab(
            tab_id=tab_id,
            app_instance_id=app_instance_id,
            product_session_id=product_session_id,
        )

    def open_window(
        self,
        *,
        window_id: object,
        app_instance_id: object | None = None,
        product_session_id: object | None = None,
    ) -> Result[ProductSession]:
        token = _chrome_token(window_id, "window_id")
        if is_refusal(token):
            return token
        return self.sessions.open_tab(
            tab_id=token.value,
            app_instance_id=app_instance_id,
            product_session_id=product_session_id,
        )

    def open_view(
        self,
        *,
        view_id: object,
        app_instance_id: object | None = None,
        product_session_id: object | None = None,
    ) -> Result[ProductSession]:
        token = _chrome_token(view_id, "view_id")
        if is_refusal(token):
            return token
        folded = token.value.casefold()
        if folded == UI_VIEW_CONTRIBUTION_POINT or folded.replace("-", "_") == "ui_view":
            return refuse_view_as_contribution_hit(field="view_id", given=token.value)
        if not folded.startswith("view:"):
            return refuse_view_as_contribution_hit(field="view_id", given=token.value)
        return self.sessions.open_tab(
            tab_id=token.value,
            app_instance_id=app_instance_id,
            product_session_id=product_session_id,
        )

    def close(
        self,
        chrome_id: object,
        *,
        product_session_id: object | None = None,
    ) -> Result[ProductSession]:
        return self.sessions.close_tab(chrome_id, product_session_id=product_session_id)

    def mint_from_chrome(self, chrome_id: object, **extra: object) -> TypedRefusal:
        """A new tab/window/view never mints a product_session."""
        return refuse_tab_mints_session(given=chrome_id, extra=sorted(extra))

    def mount_view(
        self,
        *,
        product_session_id: object,
        view: object,
    ) -> Result[ProductSession]:
        """Mount an AD-17 view:* DTO. Writes nothing; occupancy stays none."""
        parsed = parse_view_presentation(view)
        if is_refusal(parsed):
            return parsed
        dto = parsed.value
        if dto.is_contribution_hit or dto.is_plugin_contribution_point:
            return refuse_view_as_contribution_hit(view_id=dto.view_id)
        if dto.occupancy != VIEW_PRESENTATION_OCCUPANCY:
            return refuse_chrome_owns_occupancy(given=dto.occupancy)
        if dto.starts_durable_work or dto.kills_durable_work:
            return refuse_view_durable_work(
                given={"starts": dto.starts_durable_work, "kills": dto.kills_durable_work}
            )
        attached = self.sessions.open_tab(
            tab_id=dto.view_id,
            product_session_id=product_session_id,
        )
        if is_refusal(attached):
            return attached
        payload = attached.value.to_payload()
        if "view_id" in payload or "tab_id" in payload:
            return refuse_tab_as_product_session(fields=("view_id",))
        return Ok(attached.value)

    def grants_for(self, chrome_id: object) -> TypedRefusal:
        """Chrome never owns grants."""
        return refuse_chrome_owns_grants(given=chrome_id)

    def occupancy_for(self, chrome_id: object) -> Result[str]:
        """Chrome occupancy is none; chrome does not own a live occupancy row."""
        token = _chrome_token(chrome_id, "chrome_id")
        if is_refusal(token):
            return token
        return Ok(PRODUCT_SESSION_OCCUPANCY)

    def set_occupancy(self, chrome_id: object, occupancy: object) -> TypedRefusal:
        """Refuse assigning occupancy to a tab/window/view."""
        return refuse_chrome_owns_occupancy(given=occupancy, chrome_id=chrome_id)

    def treat_as_product_session(self, chrome_id: object) -> TypedRefusal:
        return refuse_tab_as_product_session(given=chrome_id)

    def treat_view_as_contribution(self, view: object) -> TypedRefusal:
        """``view:*`` is not a ContributionHit (GAP-0081; SCN-0018 Branch B)."""
        if isinstance(view, ContributionHit):
            return refuse_view_as_contribution_hit(qualified_id=view.qualified_id)
        payload: object = view
        if isinstance(view, Mapping):
            body = dict(cast("Mapping[str, object]", view))
            if body.get("hit_class") == "contribution" or "point" in body:
                parsed_hit = parse_federated_hit(body)
                if is_refusal(parsed_hit):
                    return parsed_hit
                return refuse_view_as_contribution_hit()
            payload = body
        parsed = parse_view_presentation(payload)
        if is_refusal(parsed):
            return parsed
        return refuse_view_as_contribution_hit(view_id=parsed.value.view_id)

    def authorize_invoke(self, source: object) -> TypedRefusal:
        """SCN-0018 Branch B — chrome / view:* / a hit is not a grant."""
        extra: dict[str, object] = {
            "occupancy": PRODUCT_SESSION_OCCUPANCY,
            "chrome_owns_grants": False,
        }
        if isinstance(source, ViewPresentation):
            extra["view_id"] = source.view_id
            extra["field"] = "view"
        elif isinstance(source, ContributionHit):
            extra["qualified_id"] = source.qualified_id
        elif looks_like_chrome_id(source):
            extra["given"] = source
            extra["field"] = "chrome"
        return refuse_hit_as_grant(**extra)

    def fill_gap_0081_chrome(
        self,
        *,
        plugin_id: str = "desk-ui",
        local_id: str = "heatmap",
        point: str = UI_VIEW_CONTRIBUTION_POINT,
    ) -> TypedRefusal:
        """Refused — this story does not fill GAP-0081 chrome."""
        return register_ui_widget_contribution(
            plugin_id=plugin_id,
            local_id=local_id,
            point=point,
        )
