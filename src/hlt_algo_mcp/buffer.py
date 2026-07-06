"""In-memory rolling view of the feed. Read-only source for the MCP tools."""
from __future__ import annotations

import os
from collections import deque
from typing import Optional

from hlt_algo_feed.models import TapeEvent

INDEX_SYMBOLS = [
    s.strip().upper()
    for s in os.environ.get("HLT_INDEX_SYMBOLS", "SPY,QQQ,IWM").split(",")
    if s.strip()
]


class TapeBuffer:
    """Bounded recent-event buffer plus latest summary, per-symbol counts,
    and an always-on cache of last-known quotes for index symbols."""

    def __init__(self, maxlen: int = 200, index_symbols: Optional[list[str]] = None):
        self._events: deque[TapeEvent] = deque(maxlen=maxlen)
        self._summary: Optional[TapeEvent] = None
        self._high: dict[str, int] = {}
        self._low: dict[str, int] = {}
        self._index_symbols: set[str] = set(index_symbols or INDEX_SYMBOLS)
        self._index_quotes: dict[str, TapeEvent] = {}

    def add(self, ev: TapeEvent) -> None:
        if ev.event == "market_summary":
            self._summary = ev
            return
        self._events.append(ev)
        if ev.high_count:
            self._high[ev.symbol] = max(self._high.get(ev.symbol, 0), ev.high_count)
        if ev.low_count:
            self._low[ev.symbol] = max(self._low.get(ev.symbol, 0), ev.low_count)
        if ev.symbol in self._index_symbols:
            self._index_quotes[ev.symbol] = ev

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

    def index_quotes(self) -> dict[str, TapeEvent]:
        """Last-known event per configured index symbol (e.g. SPY/QQQ/IWM),
        never evicted by the bounded `_events` deque. Each event carries its
        own `ts`, so callers can judge staleness — this is 'as of last
        session-high/low crossing,' not a continuous live tick."""
        return dict(self._index_quotes)
