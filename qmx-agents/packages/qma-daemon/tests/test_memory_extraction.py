"""Released LangMem executes a fake supplied chat model; no model-name lookup."""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field
from qma.core.ports.memory import MemoryCandidate
from qma.daemon.request_runtime.durable_memory import JournalMemoryProvider
from qma.daemon.request_runtime.memory_extraction import LangMemExtractor
from qma.daemon.request_runtime.providers import ProviderError
from test_durable_memory import Bound, value

pytest_plugins = ["test_durable_memory"]


class FakeExtractionModel(BaseChatModel):
    calls: int = 0
    texts: list[str] = Field(default_factory=lambda: ["Synthetic alpha fact"])

    @property
    def _llm_type(self) -> str:
        return "offline-extraction-fake"

    def bind_tools(self, tools: Any, **kwargs: Any) -> FakeExtractionModel:
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.calls += 1
        response = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "ExtractedFact",
                    "args": {"memory_type": "semantic", "text": text},
                    "id": f"extract-{i}",
                    "type": "tool_call",
                }
                for i, text in enumerate(self.texts)
            ],
        )
        return ChatResult(generations=[ChatGeneration(message=response)])


def proposals(
    extractor: LangMemExtractor, provider: JournalMemoryProvider
) -> tuple[MemoryCandidate, ...]:
    return extractor.propose(
        [HumanMessage(content="Synthetic alpha fact")],
        provider=provider,
        request_id="request:fake",
        proposer="agent:one",
        occurrence_time=10,
        supporting_artifacts=("artifact:synthetic",),
    )


def test_released_langmem_extracts_only_proposals_then_existing_gate_admits(bound: Bound) -> None:
    memory, provider, _, journal = bound
    model = FakeExtractionModel()
    extractor = LangMemExtractor(model)
    before = len(value(journal.read_events()))
    first = proposals(extractor, provider)
    second = proposals(extractor, provider)
    assert model.calls == 2
    assert first == second and first[0].admission_confidence is None
    assert len(value(journal.read_events())) == before
    assert value(provider.list(provider.scope)) == ()
    memory.admit(first[0])
    assert value(provider.get(first[0].id)).content["text"] == "Synthetic alpha fact"


def test_no_model_name_no_implicit_calls_and_bounded_inputs(bound: Bound) -> None:
    _, provider, _, _ = bound
    with pytest.raises(ValueError, match="injected model"):
        LangMemExtractor("openai:anything")  # pyright: ignore[reportArgumentType] - refusal fixture
    model = FakeExtractionModel()
    extractor = LangMemExtractor(model, max_input_bytes=10)
    assert model.calls == 0
    with pytest.raises(ProviderError, match="input exceeds"):
        proposals(extractor, provider)
    assert model.calls == 0


def test_output_capacity_refuses_without_journal_write(bound: Bound) -> None:
    _, provider, _, journal = bound
    model = FakeExtractionModel(texts=["one", "two"])
    extractor = LangMemExtractor(model, max_candidates=1)
    before = len(value(journal.read_events()))
    with pytest.raises(ProviderError, match="candidate budget"):
        proposals(extractor, provider)
    assert len(value(journal.read_events())) == before


def test_stale_grant_prevents_extraction_call(bound: Bound) -> None:
    _, provider, host, _ = bound
    model = FakeExtractionModel()
    extractor = LangMemExtractor(model)
    host.active = False
    with pytest.raises(ProviderError, match="revoked"):
        proposals(extractor, provider)
    assert model.calls == 0
