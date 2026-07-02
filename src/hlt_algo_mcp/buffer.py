"""In-memory rolling view of the feed. Read-only source for the MCP tools."""
from __future__ import annotations

from collections import deque
from typing import Optional

from hlt_algo_feed.models import TapeEvent


class TapeBuffer:
    """Bounded recent-event buffer plus latest summary and per-symbol counts."""

    def __init__(self, maxlen: int = 200):
        self._events: deque[TapeEvent] = deque(maxlen=maxlen)
        self._summary: Optional[TapeEvent] = None
        self._high: dict[str, int] = {}
        self._low: dict[str, int] = {}

    def add(self, ev: TapeEvent) -> None:
        if ev.event == "market_summary":
            self._summary = ev
            return
        self._events.append(ev)
        if ev.high_count:
            self._high[ev.symbol] = max(self._high.get(ev.symbol, 0), ev.high_count)
        if ev.low_count:
            self._low[ev.symbol] = max(self._low.get(ev.symbol, 0), ev.low_count)

    def latest_summary(self) -> Optional[TapeEvent]:
        return self._summary

    def recent(
        self, symbol: Optional[str] = None, kind: Optional[str] = None, n: int = 20
    ) -> list[TapeEvent]:
        out = [
            e
            for e in self._events
            if (symbol is None or e.symbol == symbol)
            and (kind is None or e.event == kind)
        ]
        return out[-n:]

    def top_movers(self, by: str = "high", k: int = 10) -> list[tuple[str, int]]:
        src = self._high if by == "high" else self._low
        return sorted(src.items(), key=lambda kv: kv[1], reverse=True)[:k]
