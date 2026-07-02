"""Read-only MCP server over the HighLowTicker algo feed.

Consumes the broadcast into a rolling buffer and exposes query tools. It enables
market_summary for itself and NEVER issues ALGO_WEB_WATCH, so it cannot alter the
shared feed subscription state of any other client on the same socket.
"""
from __future__ import annotations

import asyncio
import importlib.resources
from typing import Optional

from mcp.server.fastmcp import FastMCP
from hlt_algo_feed import AlgoFeed

from .buffer import TapeBuffer

mcp = FastMCP("highlowticker-algo-feed")
BUFFER = TapeBuffer()


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


async def _reader(url: str = "ws://127.0.0.1:7412") -> None:
    """Background task: fold the live feed into BUFFER. Read-only (summary only)."""
    async with AlgoFeed(url) as feed:
        await feed.subscribe_summary()  # read-only: never watch()
        async for ev in feed:
            BUFFER.add(ev)


def main() -> None:
    async def runner():
        task = asyncio.create_task(_reader())
        try:
            await mcp.run_stdio_async()
        finally:
            task.cancel()

    asyncio.run(runner())


if __name__ == "__main__":
    main()
