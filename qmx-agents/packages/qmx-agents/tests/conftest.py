from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pytest
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel, LanguageModelInput
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from pydantic import Field

from qmx_agents.router import RouterConfig, load_config
from qmx_agents.spec import AgentSpec, BuildContext, build_agent

QMX_HOME = Path.home() / ".qmx"


def snapshot() -> dict[str, tuple[int, int]]:
    return {
        str(path.relative_to(QMX_HOME)): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in QMX_HOME.rglob("*")
        if path.is_file()
    }


@pytest.fixture(autouse=True)
def isolated_home(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    before = snapshot()
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    for name in ("QMX_HOME", "QMX_TOOLS_ROOT", "QMX_TOOLS_FACTORY"):
        monkeypatch.delenv(name, raising=False)
    yield
    after = snapshot()
    changed = sorted(
        name for name in before.keys() | after.keys() if before.get(name) != after.get(name)
    )
    assert not changed, f"the user's real {QMX_HOME} changed during this test: {changed}"


class BoundFakeChatModel(GenericFakeChatModel):
    model_name: str = "qmx:test"
    bound_names: list[list[str]] = Field(default_factory=list[list[str]])
    failures: int = 0
    calls: int = 0

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable[..., Any] | BaseTool],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        self.bound_names.append(
            [item.name if isinstance(item, BaseTool) else str(item) for item in tools]
        )
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.calls += 1
        if self.failures:
            self.failures -= 1
            raise RuntimeError("fake provider failure")
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


@pytest.fixture
def config() -> RouterConfig:
    config = load_config()
    config.max_retries = 0
    return config


def fake(
    *messages: str | AIMessage, name: str = "qmx:test", failures: int = 0
) -> BoundFakeChatModel:
    return BoundFakeChatModel(messages=iter(messages), model_name=name, failures=failures)


def fake_models(model: BaseChatModel) -> dict[str, BaseChatModel]:
    return {"cliproxy:gpt-6.1-sol": model}


def compiled(spec: AgentSpec, ctx: BuildContext) -> Runnable[Any, dict[str, Any]]:
    return cast("Runnable[Any, dict[str, Any]]", asyncio.run(build_agent(spec, ctx)))


def no_secret(service: str, username: str) -> None:
    return None


def fake_secret(service: str, username: str) -> str:
    return "fake-secret"


def stored_secret(service: str, username: str) -> str:
    return "credential-manager"


def named_secret(service: str, username: str) -> str:
    return username
