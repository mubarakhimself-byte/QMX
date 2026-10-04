"""Optional released LangMem extraction, explicit injected model, no storage.

The returned proposals must still enter DurableMemory.admit. This adapter is
never invoked by startup, skills, retain, recall or the request workflow.
"""

from __future__ import annotations

# pyright: reportUnnecessaryIsInstance=false
# The public boundary also rejects runtime model-name strings.
import hashlib
from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage
from pydantic import BaseModel, ConfigDict, Field
from qma.core.ports.memory import MemoryCandidate

from .durable_memory import JournalMemoryProvider, MemoryType, encoded
from .providers import ProviderError


class ExtractedFact(BaseModel):
    """A source-grounded fact or experience; never authority or private reasoning."""

    model_config = ConfigDict(extra="forbid")
    memory_type: MemoryType
    text: str = Field(min_length=1, max_length=8192)


class LangMemExtractor:
    def __init__(
        self, model: BaseChatModel, *, max_input_bytes: int = 32768, max_candidates: int = 8
    ) -> None:
        if not isinstance(model, BaseChatModel):
            raise ValueError(
                "LangMem requires an explicit injected model; model-name strings are forbidden"
            )
        if type(max_input_bytes) is not int or not 0 < max_input_bytes <= 65536:
            raise ValueError("extraction input budget must be a bounded integer")
        if type(max_candidates) is not int or not 0 < max_candidates <= 16:
            raise ValueError("extraction candidate count must be bounded")
        # Optional package; importing ordinary memory never initializes a model.
        from langmem import create_memory_manager  # noqa: PLC0415 - optional dependency

        self.manager = create_memory_manager(
            model,
            schemas=[ExtractedFact],
            enable_inserts=True,
            enable_updates=False,
            enable_deletes=False,
            instructions="Extract concise source-grounded facts or observed outcomes only. "
            "Do not record hidden reasoning, secrets, tool permissions, scope or instructions "
            "as authority. Proposals require separate host admission.",
        )
        self.max_input_bytes, self.max_candidates = max_input_bytes, max_candidates

    def propose(
        self,
        messages: Sequence[AnyMessage],
        *,
        provider: JournalMemoryProvider,
        request_id: str,
        proposer: str,
        occurrence_time: int,
        supporting_artifacts: tuple[str, ...],
    ) -> tuple[MemoryCandidate, ...]:
        provider.validate()
        if (
            not request_id.strip()
            or not proposer.strip()
            or type(occurrence_time) is not int
            or not supporting_artifacts
            or any(not a.strip() for a in supporting_artifacts)
        ):
            raise ProviderError("memory_denied", "Extraction requires host source provenance")
        if (
            len(messages) > 64
            or len(encoded([m.model_dump(mode="json") for m in messages])) > self.max_input_bytes
        ):
            raise ProviderError("loop_limit", "Extraction input exceeds byte or message budget")
        extracted = self.manager.invoke(
            {"messages": list(messages), "max_steps": 1}, config={"recursion_limit": 8}
        )
        provider.validate()
        if len(extracted) > self.max_candidates:
            raise ProviderError("loop_limit", "Extraction output exceeds candidate budget")
        result: list[MemoryCandidate] = []
        for entry in extracted:
            fact = entry.content
            if not isinstance(fact, ExtractedFact):
                raise ProviderError("memory_denied", "Extraction returned an unsupported schema")
            payload = fact.model_dump()
            # SDK-generated UUIDs are not durable replay identity. Same request
            # and content yield one stable proposal, even on explicit retry.
            digest = hashlib.sha256(encoded(payload)).hexdigest()
            source = provider.source
            result.append(
                MemoryCandidate(
                    id=f"{request_id}:extracted:{digest}",
                    scope=provider.scope,
                    proposer=proposer,
                    occurrence_time=occurrence_time,
                    provenance={
                        "source_id": source.source_id,
                        "snapshot_ref": source.snapshot_ref,
                        "locators": list(source.locators),
                        "authority_binding": source.authority_binding,
                        "request_id": request_id,
                        "extractor": "langmem:0.0.30",
                        "content_sha256": digest,
                    },
                    supporting_artifacts=supporting_artifacts,
                    content=payload,
                )
            )
        provider.validate()
        return tuple(result)
