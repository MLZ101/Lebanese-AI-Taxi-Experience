"""Phase 2: every byte from a model provider is untrusted."""

import asyncio

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
from app.ai.gemini import GeminiProvider

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
    # And the indirect questions he works from are actually listed for him.
    for clue in ("day3a", "esm el 3ayleh", "madrase", "sayf"):
        assert clue in text.lower()


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
