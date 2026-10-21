"""The one classifier, against the error bodies the providers actually send.

Each fixture is a recorded provider error: Anthropic's own envelope, the OpenAI-compatible one
Kimi, DeepSeek and OpenRouter share, and OpenRouter's credit refusal. The expected class is a
literal, so a mapping change has to change this file.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from qmx_router.classify import CLASSES, classify

NOW = datetime(2026, 10, 20, 18, 0, tzinfo=UTC)

ANTHROPIC_RATE = {
    "type": "error",
    "error": {"type": "rate_limit_error", "message": "Number of requests exceeded your rate limit"},
}
OPENAI_QUOTA = {
    "error": {
        "message": "You exceeded your current quota, please check your plan and billing details.",
        "type": "insufficient_quota",
        "code": "insufficient_quota",
    }
}
OPENROUTER_CREDITS = {
    "error": {"message": "Insufficient credits. Add more credits to continue.", "code": 402}
}
ANTHROPIC_TOO_LONG = {
    "type": "error",
    "error": {
        "type": "invalid_request_error",
        "message": "prompt is too long: 250000 tokens > 200000 maximum",
    },
}
DEEPSEEK_NO_MODEL = {
    "error": {
        "message": "Model Not Exist",
        "type": "invalid_request_error",
        "code": "model_not_found",
    }
}
OPENROUTER_NO_ENDPOINT = {
    "error": {"message": "No endpoints found for deepseek/deepseek-v3", "code": 404}
}


def test_each_provider_error_maps_to_one_class() -> None:
    assert classify(429, ANTHROPIC_RATE).kind == "rate_limit"
    assert classify(429, OPENAI_QUOTA).kind == "billing"
    assert classify(402, OPENROUTER_CREDITS).kind == "billing"
    assert (
        classify(401, {"error": {"message": "Invalid API key", "code": "invalid_api_key"}}).kind
        == "auth"
    )
    assert (
        classify(529, {"type": "error", "error": {"type": "overloaded_error"}}).kind == "transient"
    )
    assert classify(400, ANTHROPIC_TOO_LONG).kind == "content"
    assert classify(400, DEEPSEEK_NO_MODEL).kind == "model_entitlement"
    assert classify(404, OPENROUTER_NO_ENDPOINT).kind == "model_entitlement"
    assert classify(400, {"error": {"message": "messages: field required"}}).kind == "fatal"
    assert classify(0, {"message": "the stream ended mid-answer"}).kind == "transient"


def test_the_class_set_is_closed() -> None:
    assert {
        "rate_limit",
        "billing",
        "auth",
        "model_entitlement",
        "content",
        "transient",
        "fatal",
    } == CLASSES


def test_the_providers_own_words_separate_a_limit_from_traffic() -> None:
    """The two 429s carry the same status. Only the body says which one is the account's limit."""
    traffic = classify(429, ANTHROPIC_RATE)
    limit = classify(
        429,
        {"error": {"message": "You have reached your usage limit for this billing period"}},
    )
    assert (traffic.kind, traffic.usage_limit) == ("rate_limit", False)
    assert (limit.kind, limit.usage_limit) == ("rate_limit", True)


def test_retry_after_is_a_delay_and_a_body_may_name_a_stamp() -> None:
    thirty = classify(429, ANTHROPIC_RATE, {"retry-after": "30"})
    assert (thirty.kind, thirty.reset_in, thirty.reset_at) == ("rate_limit", 30.0, None)
    assert thirty.until(NOW) == NOW + timedelta(seconds=30)

    stamped = classify(
        429,
        {"error": {"message": "slow down", "resets_at": "2026-10-20T19:00:00Z"}},
    )
    assert stamped.until(NOW) == datetime(2026, 10, 20, 19, 0, tzinfo=UTC)

    assert classify(429, ANTHROPIC_RATE).until(NOW) is None


def test_a_raw_body_is_read_without_a_key_ever_reaching_the_message() -> None:
    found = classify(500, b'{"error": {"message": "upstream connect error"}}')
    assert (found.kind, found.message) == ("transient", "upstream connect error")
    assert classify(429, b"<html>rate limited</html>").message == "<html>rate limited</html>"
