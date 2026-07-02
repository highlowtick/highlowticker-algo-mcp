# highlowticker-algo-mcp

A read-only MCP server that lets an AI agent (Claude Desktop, Cursor) explore
the live HighLowTicker algo feed conversationally. It consumes the feed into a
rolling in-memory buffer and exposes a few query tools plus the wire-protocol
schema as a resource.

**Read-only by design.** The server subscribes to the periodic market summary
for itself, but it never sends a watch list, so it can never change the feed
subscription state of any other program connected to the same socket. The
capability to drive subscriptions belongs to your own strategy via the
`highlowticker-algo-feed` client, not to this shared agent lens.

## Install

```bash
pip install highlowticker-algo-mcp
```

## Requirements

- HighLowTicker running with the algo feed enabled (Settings, Algo feed :7412).
- Python 3.10 or newer.

## Tools

- `get_market_summary()` — latest market push/pull and breadth summary.
- `recent_tape(symbol=None, kind=None, n=20)` — recent new-high / new-low / price-update frames.
- `top_movers(by="high", k=10)` — symbols ranked by cumulative new-high or new-low count.

## Resources

- `schema://algo-feed` — the wire-protocol JSON Schema.
- `doc://field-reference` — a condensed field reference.

## Claude Desktop config

Add to your MCP servers config:

```json
{
  "mcpServers": {
    "highlowticker-algo-feed": {
      "command": "hlt-algo-mcp"
    }
  }
}
```
