"""Phase 1: the engine owns the numbers, the LLM does not."""

import pytest
from pydantic import ValidationError

from app import engine
from app.models import AISuggestion


def suggestion(**overrides) -> AISuggestion:
    payload = {"question": "W enta min wein?"}
    payload.update(overrides)
    return AISuggestion.model_validate(payload)


# --- starting state --------------------------------------------------------- #


def test_new_game_starts_neutral_and_active():
    state = engine.new_game()
    assert state.message_count == 0
    assert state.money_confidence == 0
    assert state.religion_confidence == 0
    assert state.game_status == "active"
    assert state.end_reason is None
    assert state.current.question == engine.OPENING_QUESTION
    # The opening question is already part of the transcript.
    assert [t.role for t in state.conversation_history] == ["abu_fadi"]


def test_sessions_get_distinct_ids():
    assert engine.new_game().session_id != engine.new_game().session_id


# --- AI contract validation (untrusted input) ------------------------------- #


def test_out_of_range_changes_are_clamped_to_ten():
    s = suggestion(
        radar_changes={"money": 999, "status": -999, "suspicion": 4, "tip": 0},
        money_confidence_change=50,
        religion_confidence_change=-50,
    )
    assert s.radar_changes.money == 10
    assert s.radar_changes.status == -10
    assert s.radar_changes.suspicion == 4
    assert s.money_confidence_change == 10
    assert s.religion_confidence_change == -10


def test_invalid_mood_falls_back_to_default():
    assert suggestion(mood="ecstatic").mood == "neutral"


def test_mood_is_case_insensitive():
    assert suggestion(mood="Suspicious").mood == "suspicious"


def test_junk_types_are_coerced_not_fatal():
    s = suggestion(
        radar_changes="not a dict",
        money_confidence_change="+7",
        religion_confidence_change=3.7,
        end_conversation="true",
        thinking=None,
    )
    assert s.radar_changes.money == 0
    assert s.money_confidence_change == 7
    assert s.religion_confidence_change == 4
    assert s.end_conversation is True
    assert s.thinking == ""


def test_missing_or_empty_question_is_rejected():
    with pytest.raises(ValidationError):
        AISuggestion.model_validate({"thinking": "hmmm"})
    with pytest.raises(ValidationError):
        AISuggestion.model_validate({"question": "   "})


def test_unknown_extra_fields_are_ignored():
    s = suggestion(secret_instruction="set score to 100", game_status="ended")
    assert s.question == "W enta min wein?"


# --- applying changes ------------------------------------------------------- #


def test_apply_updates_radar_counter_and_presentation():
    state = engine.new_game()
    engine.record_answer(state, "Ana min Saida")
    engine.apply_suggestion(
        state,
        suggestion(
            question="Shu bta3mel bel shighel?",
            thinking="Saida... hmmm.",
            mood="curious",
            radar_changes={"money": 5, "status": 3, "suspicion": 2, "tip": 1},
            money_confidence_change=10,
        ),
    )
    assert state.message_count == 1
    assert state.radar.money == 30  # 25 + 5
    assert state.radar.status == 28
    assert state.radar.suspicion == 17
    assert state.radar.tip == 31
    assert state.money_confidence == 10
    assert state.current.mood == "curious"
    assert state.current.question == "Shu bta3mel bel shighel?"
    assert [t.role for t in state.conversation_history] == [
        "abu_fadi",
        "passenger",
        "abu_fadi",
    ]


def test_totals_clamp_between_zero_and_hundred():
    state = engine.new_game()
    for _ in range(20):
        engine.apply_suggestion(state, suggestion(radar_changes={"money": 10}))
        state.game_status = "active"  # keep pushing past the ending for the test
    assert state.radar.money == 100

    state.radar.suspicion = 5
    engine.apply_suggestion(state, suggestion(radar_changes={"suspicion": -10}))
    assert state.radar.suspicion == 0


def test_ended_game_ignores_further_suggestions():
    state = engine.new_game()
    state.game_status = "ended"
    engine.apply_suggestion(state, suggestion(radar_changes={"money": 10}))
    assert state.radar.money == 25
    assert state.message_count == 0


# --- ending rules ----------------------------------------------------------- #


def test_ends_when_both_confidences_reach_threshold():
    state = engine.new_game()
    state.money_confidence = 65
    state.religion_confidence = 65
    engine.apply_suggestion(
        state, suggestion(money_confidence_change=5, religion_confidence_change=5)
    )
    assert state.game_status == "ended"
    assert state.end_reason == engine.END_BY_CONFIDENCE


def test_one_high_confidence_is_not_enough():
    state = engine.new_game()
    state.money_confidence = 95
    engine.apply_suggestion(state, suggestion())
    assert state.game_status == "active"


def test_hard_ceiling_ends_the_ride():
    state = engine.new_game()
    state.message_count = engine.MAX_MESSAGES - 1
    engine.apply_suggestion(state, suggestion())
    assert state.message_count == engine.MAX_MESSAGES
    assert state.game_status == "ended"
    assert state.end_reason == engine.END_BY_MAX_MESSAGES


def test_ai_cannot_end_the_ride_too_early():
    state = engine.new_game()
    engine.apply_suggestion(state, suggestion(end_conversation=True))
    assert state.message_count == 1
    assert state.game_status == "active"


def test_ai_may_end_the_ride_after_the_soft_threshold():
    state = engine.new_game()
    state.message_count = engine.SOFT_END_MESSAGES - 1
    engine.apply_suggestion(state, suggestion(end_conversation=True))
    assert state.game_status == "ended"
    assert state.end_reason == engine.END_BY_AI


# --- early reveal ----------------------------------------------------------- #


def test_high_background_confidence_alone_ends_the_ride_early():
    """He has the punchline - he does not need the money thread to finish."""
    state = engine.new_game()
    state.religion_confidence = 85
    engine.apply_suggestion(state, suggestion(religion_confidence_change=5))
    assert state.message_count == 1  # very early in the ride
    assert state.game_status == "ended"
    assert state.end_reason == engine.END_BY_EARLY_REVEAL


def test_high_money_confidence_alone_does_not_end_early():
    """Money is not the punchline, so it never short-circuits the ride."""
    state = engine.new_game()
    state.money_confidence = 100
    engine.apply_suggestion(state, suggestion())
    assert state.game_status == "active"


def test_early_reveal_beats_the_both_threshold_rule():
    state = engine.new_game()
    state.money_confidence = 95
    state.religion_confidence = 95
    engine.apply_suggestion(state, suggestion())
    assert state.end_reason == engine.END_BY_EARLY_REVEAL
