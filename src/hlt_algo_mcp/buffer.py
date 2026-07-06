"""In-memory rolling view of the feed. Read-only source for the MCP tools."""
from __future__ import annotations

import os
import time
from collections import deque
from datetime import datetime
from typing import Optional

from hlt_algo_feed.models import TapeEvent

INDEX_SYMBOLS = [
    s.strip().upper()
    for s in os.environ.get("HLT_INDEX_SYMBOLS", "SPY,QQQ,IWM").split(",")
    if s.strip()
]

WINDOW_RETENTION_SECS = 1200  # matches the wire's longest market_high_rate_20m window


def _parse_ts(ts: str) -> Optional[float]:
    """Best-effort ISO-8601 -> Unix timestamp. Returns None (never raises) for
    anything unparseable, e.g. test fixtures using a placeholder ts."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None


class TapeBuffer:
    """Bounded recent-event buffer plus latest summary, per-symbol counts,
    an always-on cache of last-known quotes for index symbols, and
    per-symbol windowed crossing timestamps for 'hottest right now' queries."""

    def __init__(self, maxlen: int = 200, index_symbols: Optional[list[str]] = None):
        self._events: deque[TapeEvent] = deque(maxlen=maxlen)
        self._summary: Optional[TapeEvent] = None
        self._high: dict[str, int] = {}
        self._low: dict[str, int] = {}
        self._index_symbols: set[str] = set(index_symbols or INDEX_SYMBOLS)
        self._index_quotes: dict[str, TapeEvent] = {}
        self._high_timestamps: dict[str, list[float]] = {}
        self._low_timestamps: dict[str, list[float]] = {}
        self._connected_at: float = time.monotonic()

    def add(self, ev: TapeEvent) -> None:
        if ev.event == "market_summary":
            self._summary = ev
            return
        self._events.append(ev)
        if ev.high_count:
            self._high[ev.symbol] = max(self._high.get(ev.symbol, 0), ev.high_count)
            t = _parse_ts(ev.ts)
            if t is not None:
                lst = self._high_timestamps.setdefault(ev.symbol, [])
                lst.append(t)
                lst[:] = [x for x in lst if x > t - WINDOW_RETENTION_SECS]
        if ev.low_count:
            self._low[ev.symbol] = max(self._low.get(ev.symbol, 0), ev.low_count)
            t = _parse_ts(ev.ts)
            if t is not None:
                lst = self._low_timestamps.setdefault(ev.symbol, [])
                lst.append(t)
                lst[:] = [x for x in lst if x > t - WINDOW_RETENTION_SECS]
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

    def windowed_top_movers(
        self,
        by: str = "high",
        k: int = 10,
        window_seconds: int = 300,
        *,
        now: Optional[float] = None,
    ) -> list[tuple[str, int]]:
        """Symbols ranked by crossing count within the trailing
        window_seconds — NOT cumulative like top_movers(). Only counts
        crossings this process has actually observed; see coverage_seconds()
        to judge whether window_seconds is fully covered yet."""
        now = now if now is not None else time.time()
        cutoff = now - window_seconds
        src = self._high_timestamps if by == "high" else self._low_timestamps
        counts = {
            sym: sum(1 for t in ts_list if t > cutoff)
            for sym, ts_list in src.items()
        }
        counts = {s: c for s, c in counts.items() if c > 0}
        return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:k]

    def coverage_seconds(self) -> float:
        """Wall-clock time this buffer has actually been collecting, for
        callers to judge whether a requested window is fully covered."""
        return time.monotonic() - self._connected_at
