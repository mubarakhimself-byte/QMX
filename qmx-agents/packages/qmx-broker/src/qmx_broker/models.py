"""Node settings contain identities and vault references, never credentials."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from qmf.venue.spot import exact


class Account(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(min_length=1, max_length=128)
    currency: str = Field(min_length=1, max_length=16)
    leverage: str = "1"
    permissions: list[Literal["read", "propose"]] = Field(default_factory=lambda: ["read"])
    # CCXT has no universal subaccount selector. Separate key pairs are explicit.
    credential_ref: str = ""
    label: str = ""
    broker: str = ""
    enabled: bool = True

    @field_validator("leverage")
    @classmethod
    def positive_leverage(cls, value: str) -> str:
        exact(value)
        return value

    @field_validator("credential_ref")
    @classmethod
    def vault_ref(cls, value: str) -> str:
        if value and not value.startswith("qmx/"):
            raise ValueError("Credentials must reference Windows Credential Manager qmx/*")
        return value


class Connection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(min_length=1, max_length=128)
    credential_ref: str = Field(pattern=r"^qmx/.+")
    environment: Literal["demo", "live"] = "demo"
    accounts: list[Account] = Field(default_factory=list[Account])
    # A credential is `read` only when its probe proves it cannot trade (AD-67).
    scope: Literal["read", "trade"] = "read"
    # The one machine that holds the secret and opens its sessions. Never `any`.
    home: str = Field(default="pc", pattern=r"^[a-z0-9][a-z0-9._-]*$")
    capabilities: list[str] = Field(default_factory=list[str])
    """What the connection's test found, such as `accounts`, `balances` or `bars`."""
    reported_limits: dict[str, str] = Field(default_factory=dict[str, str])
    """The provider's own published or reported limits, never a QMX number."""
    licence: str = ""
    # Existing QMF consumes pinned protobuf definitions as data, not the Twisted SDK.
    protocol_path: str = ""
    protocol_tag: int | None = Field(default=None, gt=0)

    @field_validator("home", mode="before")
    @classmethod
    def one_home(cls, value: object) -> object:
        if isinstance(value, str) and value.strip().casefold() == "any":
            raise ValueError("A connection has one home machine, never any")
        return value

    @model_validator(mode="after")
    def unique_accounts(self) -> Connection:
        if len({account.id for account in self.accounts}) != len(self.accounts):
            raise ValueError("Account ids must be unique within a connection")
        return self


class Broker(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    # A name from the open adapter registry (`qmx_broker.registry`), not a closed list.
    adapter: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    exchange: str = ""
    kind: Literal["broker", "platform", "data"] = "broker"
    connections: list[Connection] = Field(default_factory=list[Connection])

    @model_validator(mode="after")
    def valid_connections(self) -> Broker:
        if self.adapter == "ccxt" and not self.exchange:
            raise ValueError("CCXT brokers require an exchange id")
        if len({connection.id for connection in self.connections}) != len(self.connections):
            raise ValueError("Connection ids must be unique within a broker")
        for connection in self.connections:
            if self.adapter == "ctrader" and any(
                not account.id.isdecimal() or int(account.id) <= 0
                for account in connection.accounts
            ):
                raise ValueError("cTrader accounts require positive ctidTraderAccountId values")
            if (
                self.adapter == "ccxt"
                and len(connection.accounts) > 1
                and any(not account.credential_ref for account in connection.accounts)
            ):
                raise ValueError("Multiple CCXT accounts require distinct account vault references")
            refs = [
                account.credential_ref for account in connection.accounts if account.credential_ref
            ]
            if self.adapter == "ccxt" and len(set(refs)) != len(refs):
                raise ValueError("CCXT account vault references must be distinct")
        return self


class BrokerSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    brokers: list[Broker] = Field(default_factory=list[Broker])
    """The pre-DR5A section, read once into `connections` and kept only for that read."""
    connections: list[Broker] = Field(default_factory=list[Broker])

    @model_validator(mode="after")
    def migrate_and_check(self) -> BrokerSettings:
        if self.brokers and self.connections:
            raise ValueError("Name the connections list or the legacy brokers list, not both")
        if len({broker.id for broker in self.providers}) != len(self.providers):
            raise ValueError("Broker ids must be unique on a node")
        homes: dict[str, str] = {}
        for broker in self.providers:
            for connection in broker.connections:
                if len({account.id for account in connection.accounts}) != len(connection.accounts):
                    raise ValueError("Account ids must be unique within a connection")
                earlier = homes.setdefault(connection.credential_ref, connection.home)
                if earlier != connection.home:
                    raise ValueError(
                        f"Credential {connection.credential_ref} has two homes;"
                        " the home belongs to the credential"
                    )
        return self

    @property
    def providers(self) -> list[Broker]:
        return self.connections or self.brokers

    def resolve(
        self, broker_id: str, connection_id: str, account_id: str
    ) -> tuple[Broker, Connection, Account]:
        for broker in self.providers:
            if broker.id == broker_id:
                for connection in broker.connections:
                    if connection.id == connection_id:
                        for account in connection.accounts:
                            if account.id == account_id:
                                return broker, connection, account
        raise ValueError("Unknown broker/connection/account; use list_accounts to select one")


class OrderProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    broker_id: str = Field(min_length=1, max_length=128)
    connection_id: str = Field(min_length=1, max_length=128)
    account_id: str = Field(min_length=1, max_length=128)
    symbol: str = Field(min_length=1, max_length=128)
    side: Literal["buy", "sell"]
    quantity: str
    order_type: Literal["market", "limit"] = "market"
    limit_price: str = ""

    @field_validator("quantity", "limit_price")
    @classmethod
    def decimal_text(cls, value: str) -> str:
        if value:
            exact(value)
        return value

    @model_validator(mode="after")
    def valid_order(self) -> OrderProposal:
        if not self.quantity or Decimal(self.quantity) <= 0:
            raise ValueError("Quantity must be positive decimal text")
        if (self.order_type == "limit") != bool(self.limit_price):
            raise ValueError("Only limit proposals require limit_price")
        return self
