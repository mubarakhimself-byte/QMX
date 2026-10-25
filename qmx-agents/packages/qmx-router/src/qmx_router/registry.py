"""The model registry (engine AD-39): providers are data, and each model is its own row.

A provider is a bundled `profiles/<name>.toml`. A user file of the same name in the user's
profile folder overrides it key by key: top-level keys replace, the `[defaults]` table merges
one key at a time, and a `[[models]]` entry merges into the bundled row with the same `qmx_id`
(or joins as a new row). A model row holds its wire, window, output limit, capabilities and the
normaliser fields of AD-50. Every default below is Claude's, and every one is UI-editable
(Appendix H).

`one_token_test` is the Test: it spends one output token on one row, only through a key that
exists, and says plainly when it spent nothing.
"""

from __future__ import annotations

import asyncio
import functools
import json
import os
import re
import time
import tomllib
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass, field, fields, replace
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Literal, NewType, cast, get_args
from urllib.parse import urlsplit

import httpx

from qmx_router import chat_lane
from qmx_router.profiles import (
    ROW_NAME,
    SECRET_REF,
    TIERS,
    AuthHeader,
    CacheMarkers,
    KeyProvider,
    ModelId,
    ProfileName,
    Quirks,
    SecretRef,
    WireQuirks,
    family_refusal,
    gpt_refusal,
    normalize,
    parse_profiles,
)

QmxId = NewType("QmxId", str)
"""`<provider>/<name>`, stable across regions and native id changes."""

type Kind = Literal["plan", "gpt", "key"]
type Use = Literal["any", "interactive", "test_only"]
type Wire = Literal["anthropic", "openai_chat", "responses"]
type Thinking = Literal["none", "optional", "forced"]
type ToolSearch = Literal["native", "bridge", "none"]
type PromptCache = Literal["explicit", "automatic", "top_level_only", "none"]
type CacheTtl = Literal["5m", "1h", "none"]
type ModelClass = Literal["strong", "mid", "cheap"]
type PlanMainNative = Literal["proven", "delegate_only"]

TOKENS_STEP: Final = 100_000


@dataclass(frozen=True)
class ModelRow:
    qmx_id: QmxId
    provider: ProfileName
    native: ModelId
    """The id the provider's API takes."""
    wire: Wire = "anthropic"
    window: int = 200_000
    max_output: int = 32_000
    tools: bool = True
    vision: bool = False
    pdf: bool = False
    audio: bool = False
    video: bool = False
    thinking: Thinking = "optional"
    tool_search: ToolSearch = "none"
    """Direct rows keep `none` until probe P3 sets it."""
    accepts_betas: frozenset[str] = frozenset()
    cache_ttl: CacheTtl = "5m"
    prompt_cache: PromptCache = "explicit"
    strip_fields: frozenset[str] = frozenset()
    """Top-level body fields the vendor answers 400 for."""
    forward_headers: frozenset[str] = frozenset()
    first_token_timeout_s: int = 120
    first_token_per_100k_s: int = 60
    keepalive: bool = False
    class_: ModelClass = "mid"
    count_tokens: bool = False
    chars_per_token: float = 3.0
    plan_main_native: PlanMainNative = "delegate_only"
    """`proven` only once probe P4 shows the plan main runs this row as a native sub-agent."""

    def first_token_timeout(self, prompt_tokens: int) -> float:
        """The no-progress bound on the first upstream event for a prompt this long."""
        return self.first_token_timeout_s + self.first_token_per_100k_s * (
            prompt_tokens / TOKENS_STEP
        )


@dataclass(frozen=True)
class Provider:
    name: ProfileName
    kind: Kind
    base_url: Mapping[str, str] = field(default_factory=dict[str, str])
    """Region to base URL. Empty for the plan and GPT, whose lanes own the route."""
    region: str = ""
    """The region `base_url` is read at. Empty means the first one listed."""
    aliases: tuple[str, ...] = ()
    auth: AuthHeader = "bearer"
    credentials: tuple[SecretRef, ...] = ()
    models_url: str = ""
    use: Use = "any"
    terms_note: str = ""
    cheap_aux: QmxId | None = None
    cli_env: Mapping[str, str] = field(default_factory=dict[str, str])
    """CLI knobs for a process whose main is this provider, beside the tool-search flag the rows
    decide."""
    models: tuple[ModelRow, ...] = ()
    source: Literal["bundled", "user", "both"] = "bundled"

    @property
    def url(self) -> str:
        if not self.base_url:
            return ""
        return self.base_url.get(self.region) or next(iter(self.base_url.values()))

    def quirks(self) -> Quirks:
        """The per-process quirks of a chat whose main is this provider, read from its rows.
        Tool search is on only when every row takes it natively."""
        native = bool(self.models) and all(row.tool_search == "native" for row in self.models)
        top_level = any(row.prompt_cache == "top_level_only" for row in self.models)
        strip = frozenset(name for row in self.models for name in row.strip_fields)
        markers: CacheMarkers = "top_level_only" if top_level else "as_sent"
        return Quirks(
            env={"ENABLE_TOOL_SEARCH": "true" if native else "false", **self.cli_env},
            wire=WireQuirks(strip_fields=strip, cache_markers=markers, auth_header=self.auth),
        )


class RegistryError(ValueError):
    """A profile file or row that cannot load; the message names the file and the key."""


class UnknownModel(KeyError):
    """No row has this `qmx_id`. Never guessed."""


@dataclass(frozen=True)
class Registry:
    providers: Mapping[ProfileName, Provider]
    errors: Mapping[str, str] = field(default_factory=dict[str, str])
    """A profile that does not load, by name. It refuses only itself."""

    def rows(self) -> tuple[ModelRow, ...]:
        return tuple(row for provider in self.providers.values() for row in provider.models)

    def model(self, qmx_id: str) -> ModelRow:
        found = next((row for row in self.rows() if row.qmx_id == qmx_id), None)
        if found is None:
            raise UnknownModel(f"no model row is {qmx_id!r}")
        return found

    def provider(self, name: str) -> Provider:
        found = self.providers.get(ProfileName(name))
        if found is None:
            raise UnknownModel(self.errors.get(name, f"no provider profile is {name!r}"))
        return found

    def for_host(self, host: str) -> Provider | None:
        """The key provider whose base URL, in any region, is on `host`."""
        return next(
            (
                provider
                for provider in self.providers.values()
                if provider.kind == "key"
                and any(urlsplit(url).hostname == host for url in provider.base_url.values())
            ),
            None,
        )


def describe(registry: Registry) -> dict[str, object]:
    """Every provider and its rows as plain JSON values, with credentials as references only."""

    def plain(value: object) -> object:
        if isinstance(value, frozenset):
            return sorted(cast("frozenset[str]", value))
        return value

    providers = [
        {
            "name": provider.name,
            "kind": provider.kind,
            "base_url": provider.url,
            "regions": dict(provider.base_url),
            "auth": provider.auth,
            "credentials": list(provider.credentials),
            "use": provider.use,
            "terms_note": provider.terms_note,
            "cheap_aux": provider.cheap_aux,
            "source": provider.source,
            "models": [
                {
                    ("class" if item.name == "class_" else item.name): plain(
                        getattr(row, item.name)
                    )
                    for item in fields(row)
                    if item.name != "provider"
                }
                for row in provider.models
            ],
        }
        for provider in registry.providers.values()
    ]
    return {"providers": providers, "errors": dict(registry.errors)}


PROVIDER_KEYS: Final = frozenset(
    {
        "name",
        "kind",
        "base_url",
        "region",
        "aliases",
        "auth",
        "credentials",
        "models_url",
        "use",
        "terms_note",
        "cheap_aux",
        "cli_env",
        "defaults",
        "models",
    }
)
MODEL_FIELDS: Final = {item.name: item for item in fields(ModelRow)}
TOML_NAME: Final = {"class": "class_"}
"""TOML keys that are Python keywords."""
CHOICES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "wire": get_args(Wire.__value__),
        "thinking": get_args(Thinking.__value__),
        "tool_search": get_args(ToolSearch.__value__),
        "cache_ttl": get_args(CacheTtl.__value__),
        "prompt_cache": get_args(PromptCache.__value__),
        "class_": get_args(ModelClass.__value__),
        "plan_main_native": get_args(PlanMainNative.__value__),
    }
)
SETS: Final = frozenset({"accepts_betas", "strip_fields", "forward_headers"})
BUNDLED: Final = resources.files("qmx_router") / "profiles"


def merge(base: Mapping[str, Any], user: Mapping[str, Any]) -> dict[str, Any]:
    """A user profile over a bundled one, key by key. A user row that is not a table is kept as
    it is, so the parse refuses it by name."""
    merged = {**base, **{k: v for k, v in user.items() if k not in ("defaults", "models")}}
    merged["defaults"] = {**base.get("defaults", {}), **user.get("defaults", {})}
    rows: dict[object, Any] = {}
    for index, row in enumerate([*base.get("models", []), *user.get("models", [])]):
        if not isinstance(row, dict):
            rows[index] = row
            continue
        key = str(cast("dict[str, Any]", row).get("qmx_id", ""))
        rows[key] = {**rows.get(key, {}), **row}
    merged["models"] = list(rows.values())
    return merged


def load(user_dir: Path | None = None) -> Registry:
    """The bundled profiles, each overridden by `user_dir/<name>.toml` when present. A user file
    with no bundled twin adds a provider."""
    documents: dict[str, tuple[dict[str, Any], Literal["bundled", "user", "both"]]] = {}
    errors: dict[str, str] = {}
    for entry in BUNDLED.iterdir():
        if entry.name.endswith(".toml"):
            documents[entry.name.removesuffix(".toml")] = (
                tomllib.loads(entry.read_text(encoding="utf-8")),
                "bundled",
            )
    for path in sorted(user_dir.glob("*.toml")) if user_dir and user_dir.is_dir() else ():
        name = path.stem
        try:
            user = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as error:
            errors[name] = f"{path.name}: {error}"
            documents.pop(name, None)
            continue
        found = documents.get(name)
        documents[name] = (merge(found[0], user), "both") if found else (user, "user")
    providers: dict[ProfileName, Provider] = {}
    for name, (document, source) in sorted(documents.items()):
        try:
            providers[ProfileName(name)] = replace(parse_provider(name, document), source=source)
        except RegistryError as error:
            errors[name] = f"{name}.toml {error}"
    return Registry(MappingProxyType(providers), MappingProxyType(errors))


@functools.cache
def bundled() -> Registry:
    """The bundled profiles alone, loaded once."""
    return load(None)


type KeyCheck = Callable[[SecretRef], bool]


def key_stored(reference: SecretRef) -> bool:
    """Whether the keyring holds `reference`. The value is only tested against None and dropped
    here; it is never returned, logged or kept."""
    import keyring  # noqa: PLC0415  (a registry read never needs the keyring)

    try:
        return keyring.get_password(reference, reference.removeprefix("qmx/")) is not None
    except Exception:  # keyring backends raise their own types
        return False


def usable(rows: Mapping[str, object], *, stored: KeyCheck | None = None) -> frozenset[ProfileName]:
    """The providers a role or a sub-agent may use, from `settings.toml [providers]`: the plan,
    and every row that parses, less a key row whose keyring entry is missing. A row he removed
    or left invalid is not one. `stored` is the keyring check, `key_stored` when None."""
    check = stored or key_stored
    found = parse_profiles(rows).by_name
    return frozenset(
        name
        for name, profile in found.items()
        if not isinstance(profile, KeyProvider) or check(profile.credential)
    )


def home_registry(
    profiles: Path, rows: Mapping[str, object], *, stored: KeyCheck | None = None
) -> Registry:
    """The registry one home's chats and helpers see: `load(profiles)`, cut to the providers
    `usable(rows)` keeps."""
    return configured(load(profiles), usable(rows, stored=stored))


def configured(registry: Registry, names: Iterable[str]) -> Registry:
    """`registry` cut to the providers in `names` (from `usable`), so a provider that is not
    configured, not valid or has no key offers no row and no sub-agent."""
    keep = frozenset(names)
    return replace(
        registry,
        providers={name: found for name, found in registry.providers.items() if name in keep},
    )


def parse_provider(name: str, document: Mapping[str, Any]) -> Provider:
    if not ROW_NAME.fullmatch(name) or document.get("name", name) != name:
        raise RegistryError("needs a lowercase name equal to its file name")
    _no_unknown(document, PROVIDER_KEYS, "the profile")
    kind = _choice(document.get("kind", "key"), get_args(Kind.__value__), "kind")
    base_url = _str_map(document.get("base_url", {}), "base_url")
    if kind == "key" and not base_url:
        raise RegistryError("base_url needs at least one region")
    for url in base_url.values():
        if urlsplit(url).scheme != "https" or not urlsplit(url).hostname:
            raise RegistryError(f"base_url {url!r} must be an https URL")
    credentials = _str_list(document.get("credentials", []), "credentials")
    if not all(SECRET_REF.fullmatch(ref) for ref in credentials):
        raise RegistryError("credentials must be qmx/<name> keyring references")
    defaults = document.get("defaults", {})
    if not isinstance(defaults, dict):
        raise RegistryError("defaults must be a table")
    raw_rows = document.get("models", [])
    if not isinstance(raw_rows, list) or not raw_rows:
        raise RegistryError("needs at least one [[models]] row")
    models = tuple(
        _model(name, kind, {**cast("dict[str, Any]", defaults), **_table(row, "a model row")})
        for row in cast("list[object]", raw_rows)
    )
    ids = [row.qmx_id for row in models]
    if len(set(ids)) != len(ids):
        raise RegistryError("lists a qmx_id twice")
    cheap_aux = document.get("cheap_aux")
    if cheap_aux is not None and cheap_aux not in ids:
        raise RegistryError(f"cheap_aux {cheap_aux!r} is not one of its rows")
    region = str(document.get("region", ""))
    if region and region not in base_url:
        raise RegistryError(f"region {region!r} is not a base_url key")
    return Provider(
        name=ProfileName(name),
        kind=kind,
        base_url=MappingProxyType(base_url),
        region=region,
        aliases=tuple(_str_list(document.get("aliases", []), "aliases")),
        auth=_choice(document.get("auth", "bearer"), get_args(AuthHeader.__value__), "auth"),
        credentials=tuple(SecretRef(ref) for ref in credentials),
        models_url=str(document.get("models_url", "")),
        use=_choice(document.get("use", "any"), get_args(Use.__value__), "use"),
        terms_note=str(document.get("terms_note", "")),
        cheap_aux=QmxId(cheap_aux) if isinstance(cheap_aux, str) else None,
        cli_env=MappingProxyType(_str_map(document.get("cli_env", {}), "cli_env")),
        models=models,
    )


def _model(provider: str, kind: str, table: Mapping[str, Any]) -> ModelRow:
    values: dict[str, Any] = {TOML_NAME.get(key, key): value for key, value in table.items()}
    _no_unknown(values, set(MODEL_FIELDS) - {"provider"}, "a model row")
    qmx_id, native = values.get("qmx_id"), values.get("native")
    if not isinstance(qmx_id, str) or not qmx_id.startswith(f"{provider}/"):
        raise RegistryError(f"qmx_id {qmx_id!r} must start with {provider}/")
    if not isinstance(native, str) or not native:
        raise RegistryError(f"{qmx_id}: native must name the provider's model id")
    refusal = _native_refusal(kind, native)
    if refusal:
        raise RegistryError(f"{qmx_id}: {refusal}")
    for key, value in values.items():
        if key in ("qmx_id", "native"):
            continue
        values[key] = _field(qmx_id, key, value)
    return ModelRow(provider=ProfileName(provider), **values)


def _native_refusal(kind: str, native: str) -> str | None:
    match kind:
        case "plan":
            return None if normalize(native) in TIERS else f"{native} is not a plan tier"
        case "gpt":
            return gpt_refusal(native)
        case _:
            return family_refusal(native)


def _field(qmx_id: str, key: str, value: object) -> object:
    default = MODEL_FIELDS[key].default
    where = f"{qmx_id}: {'class' if key == 'class_' else key}"
    if key in SETS:
        return frozenset(_str_list(value, where))
    if key in CHOICES:
        return _choice(value, CHOICES[key], where)
    if isinstance(default, bool):
        if not isinstance(value, bool):
            raise RegistryError(f"{where} must be true or false")
        return value
    if isinstance(default, int):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise RegistryError(f"{where} must be a positive whole number")
        return value
    if isinstance(default, float):
        if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
            raise RegistryError(f"{where} must be a positive number")
        return float(value)
    raise RegistryError(f"{where} is not a model field")


def _no_unknown(table: Mapping[str, Any], allowed: Iterable[str], what: str) -> None:
    unknown = sorted(set(table) - set(allowed))
    if unknown:
        shown = ["class" if key == "class_" else key for key in unknown]
        raise RegistryError(f"{what} has unknown keys {', '.join(shown)}")


def _table(value: object, what: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RegistryError(f"{what} must be a table")
    return cast("dict[str, Any]", value)


def _str_map(value: object, what: str) -> dict[str, str]:
    table = _table(value, what)
    if not all(isinstance(item, str) for item in table.values()):
        raise RegistryError(f"{what} values must be strings")
    return cast("dict[str, str]", table)


def _str_list(value: object, what: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in cast("list[object]", value)
    ):
        raise RegistryError(f"{what} must be a list of strings")
    return cast("list[str]", value)


def _choice[T: str](value: object, choices: tuple[T, ...], what: str) -> T:
    if value not in choices:
        raise RegistryError(f"{what} must be one of {', '.join(choices)}")
    return cast("T", value)


type TestStatus = Literal["ok", "no_key", "failed", "not_run"]


@dataclass(frozen=True)
class RowTestResult:
    qmx_id: str
    status: TestStatus
    detail: str
    output_tokens: int | None = None
    ms: int | None = None
    spent: bool = False
    """True once a request reached the provider."""


type SecretLookup = Callable[[str], str]
type PlanTurn = Callable[[ModelRow], Awaitable[RowTestResult]]
"""Runs the plan row's one-turn Test through a plan login. The hosting process supplies it."""

TEST_PROMPT: Final = "Reply with the single word OK."
ANTHROPIC_VERSION: Final = "2023-06-01"
HTTP_OK: Final = 200
CHAT_PATH: Final = "/v1/chat/completions"


async def one_token_test(
    registry: Registry,
    qmx_id: str,
    *,
    secrets: SecretLookup | None = None,
    plan_turn: PlanTurn | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> RowTestResult:
    """One request with `max_tokens` 1 on one row. A key row with no stored key, a lane that
    has not landed, or a plan row with no plan turn spends nothing and says why."""
    row = registry.model(qmx_id)
    provider = registry.provider(row.provider)
    match provider.kind:
        case "plan":
            if plan_turn is None:
                return RowTestResult(qmx_id, "not_run", "the plan row tests through a plan login")
            return await plan_turn(row)
        case "gpt":
            return RowTestResult(qmx_id, "not_run", "GPT rows test through the GPT lane (RTR4)")
        case "key":
            if row.wire == "responses":
                return RowTestResult(
                    qmx_id, "not_run", "a key row on the responses wire has no lane"
                )
            return await _key_test(provider, row, secrets or _keyring, transport)


ROUTING_ENV: Final = re.compile(r"^(ANTHROPIC_\w+|CLAUDE_CODE_OAUTH_TOKEN|CLAUDE_CONFIG_DIR)$")
"""Names that would route the plan CLI away from the plan login."""


def plan_test(plan_dir: Path, cwd: Path) -> PlanTurn:
    """A one-turn Test of a plan row through the plan login in `plan_dir`, with no tools and no
    settings file. Refuses to start while this process carries a routing name, because the SDK
    hands its own environment to the CLI."""

    async def turn(row: ModelRow) -> RowTestResult:
        inherited = sorted(name for name in os.environ if ROUTING_ENV.match(name))
        if inherited:
            return RowTestResult(row.qmx_id, "not_run", f"unset {', '.join(inherited)} first")
        from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query  # noqa: PLC0415

        options = ClaudeAgentOptions(
            model=row.native,
            tools=[],
            setting_sources=[],
            max_turns=1,
            cwd=str(cwd),
            env={"CLAUDE_CONFIG_DIR": str(plan_dir)},
        )
        started = time.perf_counter()
        result: ResultMessage | None = None
        async for message in query(prompt=TEST_PROMPT, options=options):
            if isinstance(message, ResultMessage):
                result = message
        ms = round((time.perf_counter() - started) * 1000)
        if result is None or result.is_error:
            detail = "no result" if result is None else f"error: {(result.result or '')[:200]}"
            return RowTestResult(row.qmx_id, "failed", detail, ms=ms, spent=result is not None)
        tokens = (result.usage or {}).get("output_tokens")
        return RowTestResult(
            row.qmx_id,
            "ok",
            f"answered {(result.result or '').strip()[:40]!r} on "
            f"{', '.join(sorted(result.model_usage or {})) or 'an unreported model'}",
            output_tokens=tokens if isinstance(tokens, int) else None,
            ms=ms,
            spent=True,
        )

    return turn


def _served(row: ModelRow, answer: httpx.Response) -> tuple[str, object]:
    """The served model and the output tokens: a chat-wire row's stream read through the chat
    lane's own state machine, an Anthropic-wire row's one JSON document."""
    if row.wire == "openai_chat":
        from qmx_router.complete import sse_blocks  # noqa: PLC0415  (complete imports this)

        state = chat_lane.StreamState(chat_lane.Translation({}, {}), row.native)
        for block in sse_blocks(answer.text.splitlines()):
            for chunk in chat_lane.parse_sse(block):
                state.feed(chunk)
        state.finish()
        if state.error is not None:
            raise ValueError(state.error[2])
        return state.served or "", state.usage.get("output_tokens")
    document = cast("dict[str, Any]", answer.json())
    usage = cast("dict[str, Any]", document.get("usage") or {})
    return str(document.get("model", "")), usage.get("output_tokens")


def _keyring(reference: str) -> str:
    from qmx_router.relay import keyring_secret  # noqa: PLC0415  (relay imports profiles)

    return keyring_secret(reference)


async def _key_test(
    provider: Provider,
    row: ModelRow,
    secrets: SecretLookup,
    transport: httpx.AsyncBaseTransport | None,
) -> RowTestResult:
    if not provider.credentials:
        return RowTestResult(row.qmx_id, "no_key", f"{provider.name} names no credential")
    reference = provider.credentials[0]
    try:
        key = await asyncio.to_thread(secrets, reference)
    except Exception:  # keyring backends raise their own types
        return RowTestResult(row.qmx_id, "no_key", f"the key {reference} is missing; nothing spent")
    auth = (
        {"x-api-key": key} if provider.auth == "x-api-key" else {"authorization": f"Bearer {key}"}
    )
    message = [{"role": "user", "content": TEST_PROMPT}]
    if row.wire == "openai_chat":
        from qmx_router.complete import Ask, chat_request  # noqa: PLC0415  (complete imports this)

        url = f"{provider.url}{CHAT_PATH}"
        headers = {"content-type": "application/json", "accept": "text/event-stream", **auth}
        content = chat_request(row, Ask(message, max_tokens=1), row.native)
    else:
        url = f"{provider.url}/v1/messages"
        headers = {
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
            **auth,
        }
        body = {"model": row.native, "max_tokens": 1, "messages": message}
        content = json.dumps(body).encode()
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(transport=transport, timeout=60.0) as client:
            answer = await client.post(url, headers=headers, content=content)
    except httpx.HTTPError as error:
        return RowTestResult(row.qmx_id, "failed", f"transport: {type(error).__name__}", spent=True)
    ms = round((time.perf_counter() - started) * 1000)
    text = answer.text.replace(key, "[key]")
    if answer.status_code != HTTP_OK:
        return RowTestResult(
            row.qmx_id, "failed", f"HTTP {answer.status_code}: {text[:200]}", ms=ms, spent=True
        )
    try:
        served, tokens = _served(row, answer)
    except ValueError as error:
        detail = f"unreadable answer: {str(error).replace(key, '[key]')[:200]}"
        return RowTestResult(row.qmx_id, "failed", detail, ms=ms, spent=True)
    refusal = family_refusal(served) if served else None
    if refusal:
        return RowTestResult(row.qmx_id, "failed", f"served {refusal}", ms=ms, spent=True)
    return RowTestResult(
        row.qmx_id,
        "ok",
        f"served {served or row.native}",
        output_tokens=tokens if isinstance(tokens, int) else None,
        ms=ms,
        spent=True,
    )
