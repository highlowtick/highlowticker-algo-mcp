"""Live smoke for the MCP data path: run the background reader against a live
feed for a few seconds, then call each tool on the populated buffer.

Precondition: HighLowTicker running with Settings, Algo feed :7412 enabled.
Run: python scripts/smoke.py
"""
import asyncio

from hlt_algo_mcp import server as srv


async def smoke():
    reader = asyncio.create_task(srv._reader())
    await asyncio.sleep(6)
    reader.cancel()
    print("market_summary:", srv.get_market_summary() is not None)
    print("recent_tape:", [(r["event"], r["symbol"]) for r in srv.recent_tape(n=5)])
    print("top_movers high:", srv.top_movers(by="high", k=3))
    print("top_movers low:", srv.top_movers(by="low", k=3))


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(smoke(), timeout=15))
