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

- [HighLowTicker](https://highlowtick.com) running with the algo feed enabled (Settings, Algo feed :7412).
- Python 3.10 or newer. (The plain `highlowticker-algo-feed` client works on 3.9; the MCP layer needs 3.10.)

Wire-protocol reference and examples: <https://highlowtick.com/algo-feed.html>

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

## Interactive testing (MCP Inspector)

`mcp dev` loads its target as a standalone file, which breaks the package's
relative imports. Use the `scripts/mcp_dev.py` shim (it re-exports the installed
package's FastMCP instance) and keep the editable install active with `-e .`:

```bash
cd highlowticker-algo-mcp
source .venv/bin/activate
pip install "mcp[cli]"
mcp dev -e . scripts/mcp_dev.py:mcp
```

The background feed reader starts via the server's FastMCP lifespan, so the
Inspector's Tools tab returns live data (feed must be running on :7412).
