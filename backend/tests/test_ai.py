"""Phase 2: every byte from a model provider is untrusted."""

import asyncio

import httpx

import pytest

from app import engine
from app.ai.base import (
    AIError,
    parse_suggestion,
    parse_verdict,
    system_text,
    transcript,
    verdict_text,
)
from app.ai.fallback import FallbackProvider, canned_suggestion
from app.ai.azure_openai import AzureOpenAIProvider
from app.ai.gemini import GeminiProvider
from app.ai.openai_api import OpenAIProvider

GOOD = """
{"question": "Min wein ya zalameh?", "thinking": "Hmmm.", "mood": "curious",
 "radar_changes": {"money": 3, "status": 1, "suspicion": 0, "tip": 2},
 "money_confidence_change": 5, "religion_confidence_change": 4,
 "end_conversation": false}
"""


# --- getting JSON out of whatever arrived ----------------------------------- #


def test_parses_plain_json():
    assert parse_suggestion(GOOD).question == "Min wein ya zalameh?"


def test_parses_through_markdown_fence():
    assert parse_suggestion(f"```json\n{GOOD}\n```").mood == "curious"


def test_parses_json_buried_in_prose():
    wrapped = f"Sure! Here is the turn:\n{GOOD}\nHope that helps."
    assert parse_suggestion(wrapped).mood == "curious"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "I'm sorry, I can't do that.",
        "{not json at all}",
        "[1, 2, 3]",
        '"just a string"',
        '{"thinking": "no question here"}',
    ],
)
def test_unusable_responses_raise_ai_error(raw):
    with pytest.raises(AIError):
        parse_suggestion(raw)


# --- prompt assembly -------------------------------------------------------- #


def test_briefing_is_appended_and_tracks_state():
    state = engine.new_game()
    state.money_confidence = 42
    text = system_text(state)
    assert "ABU FADI" in text
    assert "Money theory confidence: 42/100" in text
    assert "Do NOT set end_conversation yet." in text


def test_briefing_unlocks_ending_late_in_the_ride():
    state = engine.new_game()
    state.message_count = engine.SOFT_END_MESSAGES
    assert "You may set end_conversation true" in system_text(state)


def test_transcript_maps_roles_for_providers():
    state = engine.new_game()
    engine.record_answer(state, "Hamra please")
    assert [t["role"] for t in transcript(state)] == ["assistant", "user"]


# --- gemini response shapes ------------------------------------------------- #


def test_missing_api_key_fails_fast():
    with pytest.raises(AIError):
        GeminiProvider(api_key="")


def test_gemini_rejects_empty_and_blocked_responses():
    provider = GeminiProvider(api_key="test-key")
    with pytest.raises(AIError):
        provider._text_from({"candidates": []})
    with pytest.raises(AIError):
        provider._text_from({"promptFeedback": {"blockReason": "SAFETY"}})
    with pytest.raises(AIError):
        provider._text_from(
            {"candidates": [{"content": {"parts": []}, "finishReason": "MAX_TOKENS"}]}
        )


def test_gemini_joins_multipart_text():
    provider = GeminiProvider(api_key="test-key")
    data = {"candidates": [{"content": {"parts": [{"text": '{"que'}, {"text": 'stion": "Eh?"}'}]}}]}
    assert provider._text_from(data) == '{"question": "Eh?"}'


def test_gemini_payload_carries_schema_and_history():
    from app.ai.base import system_text
    from app.ai.gemini import RESPONSE_SCHEMA

    state = engine.new_game()
    engine.record_answer(state, "Hamra please")
    payload = GeminiProvider(api_key="test-key")._payload(
        state, system_text(state), RESPONSE_SCHEMA
    )
    assert payload["generationConfig"]["responseMimeType"] == "application/json"
    assert "question" in payload["generationConfig"]["responseSchema"]["required"]
    assert [c["role"] for c in payload["contents"]] == ["model", "user"]


# --- the fallback must never fail ------------------------------------------- #


def test_fallback_walks_the_script_without_repeating():
    state = engine.new_game()
    seen = []
    for _ in range(6):
        suggestion = canned_suggestion(state)
        seen.append(suggestion.question)
        engine.record_answer(state, "eh")
        engine.apply_suggestion(state, suggestion)
        state.game_status = "active"
    assert len(set(seen)) == len(seen)


def test_fallback_provider_is_awaitable_and_valid():
    suggestion = asyncio.run(FallbackProvider().suggest(engine.new_game()))
    assert suggestion.question
    assert suggestion.mood in {"neutral", "curious", "suspicious", "excited", "upset"}


def test_fallback_survives_running_out_of_script():
    state = engine.new_game()
    for line in range(40):
        suggestion = canned_suggestion(state)
        assert suggestion.question
        engine.apply_suggestion(state, suggestion)
        state.game_status = "active"


def test_rate_limits_get_a_longer_backoff_than_ordinary_errors():
    """A 429 needs real patience; a blip just needs a beat."""
    import httpx

    provider = GeminiProvider(api_key="k")
    assert provider._retry_delay(httpx.Response(429), 0) > provider._retry_delay(
        httpx.Response(500), 0
    )
    assert (
        provider._retry_delay(httpx.Response(429, headers={"retry-after": "3"}), 0)
        == 3.0
    )


# --- the reveal ------------------------------------------------------------- #

GOOD_VERDICT = """
{"money_verdict": "Ma3ak masari bas mkhabbi.",
 "background_verdict": "Min 3ayle mnee7a, ahlak min day3a.",
 "evidence": ["El sayyara 7akit", "Ma sa2alt 3an el ta3rifeh"],
 "fare": "Khalas, 3atine li badak.",
 "closing_line": "Rou7 bi salemeh ya zalameh."}
"""


def test_verdict_parses_and_keeps_the_evidence():
    verdict = parse_verdict(GOOD_VERDICT)
    assert verdict.money_verdict.startswith("Ma3ak")
    assert len(verdict.evidence) == 2


def test_verdict_survives_junk_and_caps_the_evidence():
    verdict = parse_verdict(
        '{"money_verdict": "x", "background_verdict": "y",'
        ' "evidence": ["a","b","c","d","e"], "fare": null, "closing_line": 7}'
    )
    assert len(verdict.evidence) == 4
    assert verdict.fare == ""
    assert verdict.closing_line == "7"


@pytest.mark.parametrize("raw", ["", "not json", '{"money_verdict": ""}'])
def test_unusable_verdicts_raise(raw):
    with pytest.raises(AIError):
        parse_verdict(raw)


def test_he_may_not_ask_outright_during_the_ride():
    """The whole game is working it out sideways - asking would end it."""
    text = system_text(engine.new_game())
    assert "NEVER ask what someone is" in text
    assert "ta7ayol" in text


def test_the_prompt_hands_him_no_ready_made_questions():
    """A list of example questions makes him recite them every single ride."""
    text = system_text(engine.new_game())
    for scripted in (
        "Min ayya day3a ahlak?",
        "Shu esm el 3ayleh?",
        "Ayya madrase rou7t?",
        "Wein bet2addo el sayf?",
    ):
        assert scripted not in text
    assert "do not work" in text  # he is told to invent his own way in


def test_he_names_his_guess_only_at_the_reveal():
    text = verdict_text(engine.new_game())
    assert "NOW YOU SAY IT" in text
    assert '"guess"' in text
    assert "NAMED" in text


def test_the_scripted_driver_always_has_a_verdict():
    verdict = asyncio.run(FallbackProvider().verdict(engine.new_game()))
    assert verdict.money_verdict and verdict.background_verdict


def test_payload_never_ends_on_a_model_turn():
    """Gemini 400s on that, and at verdict time the transcript always does."""
    from app.ai.gemini import RESPONSE_SCHEMA

    provider = GeminiProvider(api_key="k")
    state = engine.new_game()  # opening question only -> ends on a model turn
    contents = provider._payload(state, "sys", RESPONSE_SCHEMA)["contents"]
    assert contents[-1]["role"] == "user"

    engine.record_answer(state, "Hamra")  # now ends on the passenger
    contents = provider._payload(state, "sys", RESPONSE_SCHEMA)["contents"]
    assert contents[-1]["role"] == "user"
    assert contents[-1]["parts"][0]["text"] == "Hamra"


# --- azure openai ----------------------------------------------------------- #


def azure(**kw):
    defaults = dict(
        api_key="k",
        endpoint="https://res.openai.azure.com",
        deployment="gpt-55",
        api_version="2024-10-21",
    )
    return AzureOpenAIProvider(**{**defaults, **kw})


@pytest.mark.parametrize("missing", ["api_key", "endpoint", "deployment"])
def test_azure_needs_all_of_its_settings(missing):
    with pytest.raises(AIError, match="AZURE_OPENAI"):
        azure(**{missing: ""})


def test_azure_url_carries_deployment_and_api_version():
    """The model lives in the URL on Azure, not in the request body."""
    url = azure().url
    assert url == (
        "https://res.openai.azure.com/openai/deployments/gpt-55"
        "/chat/completions?api-version=2024-10-21"
    )


def test_azure_trailing_slash_on_the_endpoint_is_harmless():
    assert "azure.com//openai" not in azure(endpoint="https://res.openai.azure.com/").url


def test_azure_body_has_no_model_field():
    payload = azure()._payload(engine.new_game(), "sys")
    assert "model" not in payload
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["messages"][0]["role"] == "system"


def test_azure_drops_a_parameter_the_deployment_rejects():
    """Newer deployments refuse some older knobs - drop and retry, don't fail."""
    provider = azure()
    payload = provider._payload(engine.new_game(), "sys")
    assert "max_completion_tokens" in payload

    complaint = "Unsupported parameter: 'max_completion_tokens' is not supported"
    trimmed = provider._drop_unsupported(payload, complaint)
    assert trimmed is not None
    assert "max_completion_tokens" not in trimmed
    assert trimmed["messages"] == payload["messages"]  # the turn survives

    # A 400 about something else is a real error, not something to retry blind.
    assert provider._drop_unsupported(payload, "content filter triggered") is None


def test_azure_reads_the_message_content():
    assert parse_suggestion(
        azure()._text_from({"choices": [{"message": {"content": GOOD}}]})
    ).mood == "curious"


def test_azure_rejects_empty_and_errored_responses():
    provider = azure()
    with pytest.raises(AIError):
        provider._text_from({"choices": []})
    with pytest.raises(AIError, match="quota"):
        provider._text_from({"error": {"message": "quota exceeded"}})
    with pytest.raises(AIError):
        provider._text_from(
            {"choices": [{"message": {"content": " "}, "finish_reason": "length"}]}
        )


def test_azure_is_only_offered_when_fully_configured(monkeypatch):
    from app import config as cfg
    from app.ai import catalog

    entry = next(e for e in catalog.MODELS if e["provider"] == "azure")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_API_KEY", "k")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_DEPLOYMENT", "d")
    assert not catalog.is_available(entry)  # a key alone points at nothing

    monkeypatch.setattr(cfg, "AZURE_OPENAI_ENDPOINT", "https://res.openai.azure.com")
    assert catalog.is_available(entry)


def test_target_uri_supplies_all_three_pieces():
    """Azure shows one URL next to a deployment; pasting it should be enough."""
    from app.ai.azure_openai import parse_target_uri

    parts = parse_target_uri(
        "https://my-res.openai.azure.com/openai/deployments/gpt-55-taxi"
        "/chat/completions?api-version=2025-01-01-preview"
    )
    assert parts == {
        "endpoint": "https://my-res.openai.azure.com",
        "deployment": "gpt-55-taxi",
        "api_version": "2025-01-01-preview",
    }


def test_target_uri_shrugs_off_junk():
    from app.ai.azure_openai import parse_target_uri

    assert parse_target_uri("") == {}
    assert parse_target_uri("not a url") == {}
    # A bare resource URL still gives us the endpoint.
    assert parse_target_uri("https://my-res.openai.azure.com") == {
        "endpoint": "https://my-res.openai.azure.com"
    }


def test_provider_builds_from_target_uri_alone(monkeypatch):
    from app import config as cfg
    from app.ai import azure_openai

    monkeypatch.setattr(cfg, "AZURE_OPENAI_API_KEY", "k")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_DEPLOYMENT", "")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_API_VERSION", "")
    monkeypatch.setattr(
        cfg,
        "AZURE_OPENAI_TARGET_URI",
        "https://my-res.openai.azure.com/openai/deployments/gpt-55"
        "/chat/completions?api-version=2025-01-01-preview",
    )
    provider = azure_openai.AzureOpenAIProvider()
    assert provider.deployment == "gpt-55"
    assert provider.api_version == "2025-01-01-preview"
    assert provider.url.startswith("https://my-res.openai.azure.com/openai/deployments/gpt-55")


def test_explicit_settings_beat_the_target_uri(monkeypatch):
    from app import config as cfg
    from app.ai import azure_openai

    monkeypatch.setattr(cfg, "AZURE_OPENAI_API_KEY", "k")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_ENDPOINT", "https://chosen.openai.azure.com")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_DEPLOYMENT", "chosen-deploy")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_API_VERSION", "")
    monkeypatch.setattr(
        cfg,
        "AZURE_OPENAI_TARGET_URI",
        "https://other.openai.azure.com/openai/deployments/other/chat/completions",
    )
    provider = azure_openai.AzureOpenAIProvider()
    assert provider.endpoint == "https://chosen.openai.azure.com"
    assert provider.deployment == "chosen-deploy"
    assert provider.api_version == azure_openai.DEFAULT_API_VERSION


def test_a_key_with_no_address_is_not_offered(monkeypatch):
    from app import config as cfg
    from app.ai import catalog

    entry = next(e for e in catalog.MODELS if e["provider"] == "azure")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_API_KEY", "k")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_DEPLOYMENT", "")
    monkeypatch.setattr(cfg, "AZURE_OPENAI_TARGET_URI", "")
    assert not catalog.is_available(entry)

    monkeypatch.setattr(
        cfg,
        "AZURE_OPENAI_TARGET_URI",
        "https://r.openai.azure.com/openai/deployments/d/chat/completions",
    )
    assert catalog.is_available(entry)


# --- openai (official SDK) -------------------------------------------------- #


class FakeChoice:
    def __init__(self, content, finish_reason="stop"):
        self.message = type("M", (), {"content": content})()
        self.finish_reason = finish_reason


class FakeCompletion:
    def __init__(self, *choices):
        self.choices = list(choices)


def test_openai_needs_a_key():
    with pytest.raises(AIError, match="OPENAI_API_KEY"):
        OpenAIProvider(api_key="")


def test_openai_builds_an_sdk_client_with_our_limits():
    """Timeout and retries are the SDK's job now - make sure it gets them."""
    from app import config as cfg

    provider = OpenAIProvider(api_key="k", model="gpt-5.5")
    assert provider.client.api_key == "k"
    assert provider.client.max_retries == cfg.AI_MAX_RETRIES
    assert provider.model == "gpt-5.5"


def test_openai_names_the_model_in_the_request():
    kwargs = OpenAIProvider(api_key="k", model="gpt-5.5")._kwargs(
        engine.new_game(), "sys"
    )
    assert kwargs["model"] == "gpt-5.5"
    assert kwargs["response_format"] == {"type": "json_object"}
    assert kwargs["messages"][0]["role"] == "system"


def test_openai_base_url_can_point_elsewhere(monkeypatch):
    from app import config as cfg

    monkeypatch.setattr(cfg, "OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
    provider = OpenAIProvider(api_key="k")
    assert "groq.com" in str(provider.client.base_url)


def test_openai_drops_a_parameter_the_model_rejects():
    provider = OpenAIProvider(api_key="k")
    kwargs = provider._kwargs(engine.new_game(), "sys")
    trimmed = provider._drop_unsupported(
        kwargs, "Unsupported parameter: 'max_completion_tokens'"
    )
    assert trimmed is not None and "max_completion_tokens" not in trimmed
    assert trimmed["messages"] == kwargs["messages"]  # the turn survives
    assert provider._drop_unsupported(kwargs, "content filter") is None


def test_openai_reads_the_completion():
    provider = OpenAIProvider(api_key="k")
    assert parse_suggestion(
        provider._text_from(FakeCompletion(FakeChoice(GOOD)))
    ).mood == "curious"


def test_openai_rejects_empty_completions():
    provider = OpenAIProvider(api_key="k")
    with pytest.raises(AIError):
        provider._text_from(FakeCompletion())
    with pytest.raises(AIError, match="length"):
        provider._text_from(FakeCompletion(FakeChoice("  ", "length")))


def test_openai_retries_once_without_the_bad_parameter(monkeypatch):
    """A 400 naming a parameter must cost one retry, not the whole turn."""
    from openai import BadRequestError

    provider = OpenAIProvider(api_key="k")
    seen = []

    async def create(**kwargs):
        seen.append(kwargs)
        if "max_completion_tokens" in kwargs:
            raise BadRequestError(
                "Unsupported parameter: 'max_completion_tokens' is not supported",
                response=httpx.Response(400, request=httpx.Request("POST", "http://x")),
                body=None,
            )
        return FakeCompletion(FakeChoice(GOOD))

    monkeypatch.setattr(provider.client.chat.completions, "create", create)
    suggestion = asyncio.run(provider.suggest(engine.new_game()))
    assert suggestion.question
    assert len(seen) == 2
    assert "max_completion_tokens" not in seen[1]


def test_openai_surfaces_a_real_bad_request(monkeypatch):
    from openai import BadRequestError

    provider = OpenAIProvider(api_key="k")

    async def create(**kwargs):
        raise BadRequestError(
            "The model `nope` does not exist",
            response=httpx.Response(400, request=httpx.Request("POST", "http://x")),
            body=None,
        )

    monkeypatch.setattr(provider.client.chat.completions, "create", create)
    with pytest.raises(AIError, match="does not exist"):
        asyncio.run(provider.suggest(engine.new_game()))


def test_openai_models_are_offered_once_a_key_exists(monkeypatch):
    from app import config as cfg
    from app.ai import catalog

    entries = [e for e in catalog.MODELS if e["provider"] == "openai"]
    assert entries, "no OpenAI models in the catalog"
    monkeypatch.setattr(cfg, "OPENAI_API_KEY", "")
    assert not any(catalog.is_available(e) for e in entries)
    monkeypatch.setattr(cfg, "OPENAI_API_KEY", "sk-test")
    assert all(catalog.is_available(e) for e in entries)


def test_the_prompt_forbids_arabic_script():
    """The pixel font cannot draw it - one slipped word is a hole on screen."""
    text = system_text(engine.new_game())
    assert "LATIN LETTERS ONLY" in text
    # And the prompt must not itself contain any, or it teaches the opposite.
    assert not any("\u0600" <= ch <= "\u06ff" for ch in text)
