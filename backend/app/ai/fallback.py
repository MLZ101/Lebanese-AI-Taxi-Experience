"""Scripted Abu Fadi. Used when the real provider fails, and for offline UI work.

Never raises. Whatever happens upstream, the ride keeps moving.
"""

from __future__ import annotations

from ..models import AISuggestion, GameState

#: Ordered so the ride still escalates if the API dies on turn one. Confidence
#: creeps up each turn so a fallback-only ride still reaches a real ending.
SCRIPT: list[dict] = [
    {
        "question": "Ahlan. Min wein enta ya zalameh, mesh min hon sa7?",
        "thinking": "New face...",
        "mood": "curious",
        "driver_action": "mirror",
        "radar_changes": {"money": 0, "status": 0, "suspicion": 2, "tip": 0},
        "money_confidence_change": 4,
        "religion_confidence_change": 6,
    },
    {
        "question": "Tayyeb w shu bta3mel? Shighel maktab wella shighel jedde?",
        "thinking": "Hmmm.",
        "mood": "curious",
        "driver_action": "normal",
        "radar_changes": {"money": 4, "status": 3, "suspicion": 0, "tip": 2},
        "money_confidence_change": 8,
        "religion_confidence_change": 5,
    },
    {
        "question": "W sakin wein hallaq? El ijar sar 7arb, wallah.",
        "thinking": "Ba3ref shu 2elak.",
        "mood": "suspicious",
        "driver_action": "mirror",
        "radar_changes": {"money": 5, "status": 4, "suspicion": 3, "tip": 1},
        "money_confidence_change": 9,
        "religion_confidence_change": 8,
    },
    {
        "question": "3andak sayyara? Ya3ne shu bteshtghel fiya, la tkhabbe.",
        "thinking": "KACHING",
        "mood": "excited",
        "driver_action": "money",
        "radar_changes": {"money": 7, "status": 5, "suspicion": 0, "tip": 5},
        "money_confidence_change": 10,
        "religion_confidence_change": 6,
    },
    {
        "question": "W mtajawwez? La2? Ya zalameh, 3ammak 3endo bent mnee7a.",
        "thinking": "Aha.",
        "mood": "curious",
        "driver_action": "nod",
        "radar_changes": {"money": 2, "status": 3, "suspicion": 2, "tip": 3},
        "money_confidence_change": 7,
        "religion_confidence_change": 10,
    },
    {
        "question": "Ahlak min ayya day3a aslan? Kel wa7ad elo day3a.",
        "thinking": "Now we're talking.",
        "mood": "suspicious",
        "driver_action": "mirror",
        "radar_changes": {"money": 3, "status": 4, "suspicion": 4, "tip": 2},
        "money_confidence_change": 8,
        "religion_confidence_change": 10,
    },
    {
        "question": "W bel 3id, bterja3o 3al day3a wella bteb2o hon?",
        "thinking": "Last piece.",
        "mood": "excited",
        "driver_action": "nod",
        "radar_changes": {"money": 3, "status": 3, "suspicion": -2, "tip": 6},
        "money_confidence_change": 9,
        "religion_confidence_change": 10,
    },
]

#: Used once the script runs out.
FILLER = {
    "question": "Eh... w ba3den? 7kine kamen shway, el tari2 tawile.",
    "thinking": "Traffic.",
    "mood": "neutral",
    "driver_action": "normal",
    "radar_changes": {"money": 1, "status": 1, "suspicion": 1, "tip": 1},
    "money_confidence_change": 6,
    "religion_confidence_change": 6,
}


def canned_suggestion(state: GameState) -> AISuggestion:
    """Pick the next unused scripted line. Always succeeds."""
    asked = {t.text for t in state.conversation_history if t.role == "abu_fadi"}
    line = next((s for s in SCRIPT if s["question"] not in asked), FILLER)
    return AISuggestion.model_validate({**line, "end_conversation": False})


class FallbackProvider:
    name = "fallback"

    async def suggest(self, state: GameState) -> AISuggestion:
        return canned_suggestion(state)
