"""QMB composition-root adapter for stamping QML-authored CT-33/CT-34 content.

QML owns fingerprintable content and conformance verdicts. This QMB host module
owns the CT-06 Registrar boundary and the occurrence facts needed for receipts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, cast

from qmf.core.chrono import Instant, WriterId
from qmf.core.fingerprint import Fingerprint
from qmf.core.refusal import Ok, Result, is_refusal
from qmf.registry import FieldSetKind, KindRegistry, Registrar, RegistrationReceipt
from qml._refuse import invalid, policy
from qml.conformance.registration import ConformanceTicket
from qml.declaration.bot import (
    KIND_BOT_DEFINITION,
    BotDefinition,
    bot_definition_kind_contract,
    mint_bot_definition,
)
from qml.declaration.confluence import (
    KIND_CONFLUENCE,
    Confluence,
    confluence_kind_contract,
    mint_confluence,
)
from qml.families import (
    KIND_STRATEGY_FAMILY,
    StrategyFamilyId,
    StrategyFamilyRecord,
    mint_strategy_family,
    strategy_family_kind_contract,
)
from qml.generation import AuthoredStructure

__all__ = [
    "QMB_AUTHORS_CANDIDATES",
    "QMB_MINTS_CT06_ENVELOPE",
    "RegisteredCandidate",
    "install_bot_domain_kinds",
    "install_strategy_family_kind",
    "mint_ct06_envelope",
    "mint_generation_envelope",
    "register_bot_definition",
    "register_confluence",
    "register_strategy_family",
]

QMB_MINTS_CT06_ENVELOPE: Final[bool] = True
QMB_AUTHORS_CANDIDATES: Final[bool] = False


def install_bot_domain_kinds(registry: object) -> Result[KindRegistry]:
    """Install QML's CT-33 and CT-34 kind contracts at the QMB root."""
    if not isinstance(registry, KindRegistry):
        return invalid("registry", "QMB installs bot-domain kinds on a CT-06 KindRegistry")
    for contract_factory in (
        confluence_kind_contract,
        bot_definition_kind_contract,
        strategy_family_kind_contract,
    ):
        contract = contract_factory()
        if is_refusal(contract):
            return contract
        installed = registry.register(contract.value)
        if is_refusal(installed):
            return installed
    return Ok(registry)


def install_strategy_family_kind(registry: object) -> Result[FieldSetKind]:
    """Install the CT-06 strategy-family kind at the QMB composition root."""
    if not isinstance(registry, KindRegistry):
        return invalid("registry", "QMB installs strategy-family kind on a KindRegistry")
    contract = strategy_family_kind_contract()
    if is_refusal(contract):
        return contract
    installed = registry.register(contract.value)
    if is_refusal(installed):
        return installed
    return Ok(contract.value)


def register_strategy_family(
    family_id: object,
    *,
    registrar: object,
    writer: object,
    sequence: object,
    created_at: object,
) -> Result[RegistrationReceipt]:
    """Stamp QML-authored strategy-family identity through QMB's Registrar."""
    if not isinstance(registrar, Registrar):
        return invalid("registrar", "QMB composition root requires a CT-06 Registrar")
    if not isinstance(family_id, StrategyFamilyId):
        content = mint_strategy_family(family_id)
        if is_refusal(content):
            return content
        family: StrategyFamilyRecord = content.value
    else:
        content = mint_strategy_family(family_id.value)
        if is_refusal(content):
            return content
        family = content.value
    return registrar.register(
        kind=KIND_STRATEGY_FAMILY,
        body=family.body(),
        writer=writer,
        sequence=sequence,
        created_at=created_at,
    )


def register_bot_definition(
    declaration: object,
    *,
    registrar: object,
    writer: object,
    sequence: object,
    created_at: object,
    ticket: object,
    at_birth_parent_refs: object = (),
) -> Result[RegistrationReceipt]:
    """Stamp Bot content only after QML supplied a passing two-layer ticket."""
    if not isinstance(registrar, Registrar):
        return invalid("registrar", "QMB composition root requires a CT-06 Registrar")
    if not isinstance(ticket, ConformanceTicket) or not (
        ticket.layer1_passed and ticket.layer2_passed
    ):
        return policy(
            "ticket",
            "the QMB root stamps a Bot-kind record only after both QML conformance layers pass",
        )
    if isinstance(declaration, BotDefinition):
        content = declaration
    else:
        parsed = mint_bot_definition(declaration)
        if is_refusal(parsed):
            return parsed
        content = parsed.value
    parents: object = at_birth_parent_refs
    if parents in ((), None) and content.at_birth_parent_refs:
        parents = content.at_birth_parent_refs
    return registrar.register(
        kind=KIND_BOT_DEFINITION,
        body=content.body(),
        writer=writer,
        sequence=sequence,
        created_at=created_at,
        at_birth_parent_refs=parents,
    )


def register_confluence(
    legs: object,
    *,
    registrar: object,
    writer: object,
    sequence: object,
    created_at: object,
    order_significance: object = None,
    at_birth_parent_refs: object = (),
) -> Result[RegistrationReceipt]:
    """Stamp fingerprintable CT-34 content at the QMB composition root."""
    if not isinstance(registrar, Registrar):
        return invalid("registrar", "QMB composition root requires a CT-06 Registrar")
    content = mint_confluence(legs, order_significance=order_significance)
    if is_refusal(content):
        return content
    return registrar.register(
        kind=KIND_CONFLUENCE,
        body=content.value.body(),
        writer=writer,
        sequence=sequence,
        created_at=created_at,
        at_birth_parent_refs=at_birth_parent_refs,
    )


def mint_ct06_envelope(
    *,
    kind: object,
    body: object,
    registrar: object,
    writer: object,
    sequence: object,
    created_at: object,
    ticket: object = None,
    at_birth_parent_refs: object = (),
) -> Result[RegistrationReceipt]:
    """Dispatch the two QML domain kinds through the QMB-owned Registrar."""
    token = kind if isinstance(kind, str) else getattr(kind, "value", None)
    if not isinstance(token, str):
        return invalid("kind", "a CT-06 envelope names a bot-domain kind")
    if token == KIND_BOT_DEFINITION:
        return register_bot_definition(
            body,
            registrar=registrar,
            writer=writer,
            sequence=sequence,
            created_at=created_at,
            ticket=ticket,
            at_birth_parent_refs=at_birth_parent_refs,
        )
    if token == KIND_CONFLUENCE:
        if isinstance(body, Confluence):
            legs: object = body.legs
            order = body.ordering.value if body.order_significant else None
        elif isinstance(body, Mapping):
            mapping = cast("Mapping[str, object]", body)
            legs = mapping.get("legs", cast("object", body))
            order = mapping.get("order_significance")
        else:
            legs, order = body, None
        return register_confluence(
            legs,
            registrar=registrar,
            writer=writer,
            sequence=sequence,
            created_at=created_at,
            order_significance=order,
            at_birth_parent_refs=at_birth_parent_refs,
        )
    return invalid("kind", "QMB root stamps only bot-definition and confluence kinds")


@dataclass(frozen=True, slots=True)
class RegisteredCandidate:
    """QMB-stamped CT-06 receipts for QML-authored generation content."""

    confluence: RegistrationReceipt | None
    bot: RegistrationReceipt | None
    logic_fp1: Fingerprint | None
    qmb_authors: bool = QMB_AUTHORS_CANDIDATES
    qmb_mints_envelope: bool = QMB_MINTS_CT06_ENVELOPE

    def bot_fp1(self) -> Fingerprint | None:
        return None if self.bot is None else self.bot.record.stable_id


def mint_generation_envelope(
    authored: object,
    *,
    registrar: object,
    created_at: object,
    ticket: object = None,
    bot_writer: object = None,
    confluence_writer: object = None,
    sequence: object = 0,
) -> Result[RegisteredCandidate]:
    """Stamp QML-authored generation content at QMB's composition root."""
    if not isinstance(authored, AuthoredStructure):
        return invalid("authored", "QMB root requires QML AuthoredStructure content")
    if not isinstance(registrar, Registrar):
        return invalid("registrar", "QMB composition root requires a CT-06 Registrar")
    if authored.bot is not None and (
        not isinstance(ticket, ConformanceTicket)
        or not (ticket.layer1_passed and ticket.layer2_passed)
    ):
        return policy(
            "ticket",
            "QMB preflights both QML conformance layers before stamping generation receipts",
        )
    if authored.bot is not None and not isinstance(bot_writer, WriterId):
        return invalid("bot_writer", "QMB root supplies a Bot-definition WriterId")
    if authored.confluence is not None and not isinstance(confluence_writer, WriterId):
        return invalid("confluence_writer", "QMB root supplies a confluence WriterId")
    if isinstance(created_at, Instant):
        stamped_at = created_at
    else:
        parsed_at = Instant.try_create(created_at)
        if is_refusal(parsed_at):
            return invalid("created_at", "QMB root supplies a valid CT-06 created-at Instant")
        stamped_at = parsed_at.value

    confluence_receipt: RegistrationReceipt | None = None
    bot_receipt: RegistrationReceipt | None = None
    if authored.confluence is not None:
        if not isinstance(confluence_writer, WriterId):
            return invalid("confluence_writer", "QMB root supplies a confluence WriterId")
        stamped = register_confluence(
            authored.confluence.legs,
            registrar=registrar,
            writer=confluence_writer,
            sequence=sequence,
            created_at=stamped_at,
            order_significance=(
                authored.confluence.ordering.value
                if authored.confluence.order_significant
                else None
            ),
        )
        if is_refusal(stamped):
            return stamped
        confluence_receipt = stamped.value
    if authored.bot is not None:
        if not isinstance(bot_writer, WriterId):
            return invalid("bot_writer", "QMB root supplies a Bot-definition WriterId")
        stamped_bot = register_bot_definition(
            authored.bot,
            registrar=registrar,
            writer=bot_writer,
            sequence=sequence,
            created_at=stamped_at,
            ticket=ticket,
        )
        if is_refusal(stamped_bot):
            return stamped_bot
        bot_receipt = stamped_bot.value
    logic_fp = None if authored.logic is None else authored.logic.source_manifest
    if confluence_receipt is None and bot_receipt is None and logic_fp is None:
        return invalid("authored", "empty generation content cannot mint a CT-06 receipt")
    return Ok(
        RegisteredCandidate(
            confluence=confluence_receipt,
            bot=bot_receipt,
            logic_fp1=logic_fp,
        )
    )
