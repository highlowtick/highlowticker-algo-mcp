"""Read-only MCP server over the HighLowTicker algo feed.

Consumes the broadcast into a rolling buffer and exposes query tools. It enables
market_summary for itself and NEVER issues ALGO_WEB_WATCH, so it cannot alter the
shared feed subscription state of any other client on the same socket.
"""
from __future__ import annotations

import asyncio
import importlib.resources
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from mcp.server.fastmcp import FastMCP
from hlt_algo_feed import AlgoFeed

from .buffer import TapeBuffer

BUFFER = TapeBuffer()


async def _reader(url: str = "ws://127.0.0.1:7412") -> None:
    """Background task: fold the live feed into BUFFER. Read-only (summary only)."""
    async with AlgoFeed(url) as feed:
        await feed.subscribe_summary()  # read-only: never watch()
        async for ev in feed:
            BUFFER.add(ev)


@asynccontextmanager
async def _feed_lifespan(_app: FastMCP) -> AsyncIterator[None]:
    task = asyncio.create_task(_reader())
    try:
        yield
    finally:
        task.cancel()


mcp = FastMCP("highlowticker-algo-feed", lifespan=_feed_lifespan)


@mcp.tool()
def get_market_summary() -> Optional[dict]:
    """Latest market push/pull and breadth summary, or None if not seen yet."""
    s = BUFFER.latest_summary()
    return s.model_dump() if s is not None else None


@mcp.tool()
def recent_tape(
    symbol: Optional[str] = None, kind: Optional[str] = None, n: int = 20
) -> list[dict]:
    """Recent new_high / new_low / price_update frames, optionally filtered.

    kind is one of: new_high, new_low, new_high_and_low, price_update.
    """
    return [e.model_dump() for e in BUFFER.recent(symbol=symbol, kind=kind, n=n)]


@mcp.tool()
def top_movers(by: str = "high", k: int = 10) -> list[dict]:
    """Symbols ranked by cumulative new-high (by='high') or new-low (by='low') count."""
    return [{"symbol": s, "count": c} for s, c in BUFFER.top_movers(by=by, k=k)]


@mcp.tool()
def index_quotes() -> dict[str, dict]:
    """Last-known price/pct_change per configured index symbol (default
    SPY/QQQ/IWM, override via HLT_INDEX_SYMBOLS env var). Each entry
    includes its own `ts` so staleness is visible — this is the last
    session-high/low crossing HighLowTicker actually saw for that symbol,
    not a continuously live tick."""
    return {sym: ev.model_dump() for sym, ev in BUFFER.index_quotes().items()}


@mcp.tool()
def hottest_recent(by: str = "high", k: int = 10, window_seconds: int = 300) -> dict:
    """Symbols ranked by new-high/new-low crossings in the trailing
    window_seconds (default 5 min) — NOT cumulative like top_movers.

    If this MCP process has been running for less than window_seconds, the
    result only reflects the time actually observed (see coverage_seconds
    in the response) — it under-reports on a freshly-started MCP rather
    than silently claiming full-window coverage it doesn't have.
    """
    return {
        "movers": [
            {"symbol": s, "count": c}
            for s, c in BUFFER.windowed_top_movers(by=by, k=k, window_seconds=window_seconds)
        ],
        "window_seconds": window_seconds,
        "coverage_seconds": round(BUFFER.coverage_seconds(), 1),
    }


def _resource_text(name: str) -> str:
    return importlib.resources.files("hlt_algo_mcp").joinpath("resources", name).read_text()


@mcp.resource("schema://algo-feed")
def algo_feed_schema() -> str:
    """The wire-protocol JSON Schema (egress TapeEvent + ingress AlgoEvent)."""
    return _resource_text("algo-feed.schema.json")


@mcp.resource("doc://field-reference")
def field_reference() -> str:
    """Condensed field reference for the tape events."""
    return _resource_text("field-reference.md")


@mcp.resource("doc://python-client-quickstart")
def python_client_quickstart() -> str:
    """How to use the hlt_algo_feed pypi package to write a standalone strategy."""
    return _resource_text("python-client-quickstart.md")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
