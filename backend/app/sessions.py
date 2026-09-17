"""In-memory session store. No database, on purpose.

Sessions live until the process restarts or the cap evicts them, which is
exactly the lifetime a demo needs.
"""

from __future__ import annotations

from collections import OrderedDict

from .models import GameState

#: Oldest-used rides are dropped past this. Keeps a long demo from growing
#: without bound; nobody comes back to a ride from an hour ago.
MAX_SESSIONS = 500


class SessionStore:
    def __init__(self, max_sessions: int = MAX_SESSIONS):
        self._sessions: OrderedDict[str, GameState] = OrderedDict()
        self._max = max_sessions

    def add(self, state: GameState) -> GameState:
        self._sessions[state.session_id] = state
        self._sessions.move_to_end(state.session_id)
        while len(self._sessions) > self._max:
            self._sessions.popitem(last=False)
        return state

    def get(self, session_id: str) -> GameState | None:
        state = self._sessions.get(session_id)
        if state is not None:
            self._sessions.move_to_end(session_id)
        return state

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def __len__(self) -> int:
        return len(self._sessions)


#: One store per process. Imported directly - no DI container needed here.
store = SessionStore()
