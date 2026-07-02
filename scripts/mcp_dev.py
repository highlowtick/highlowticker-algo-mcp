"""MCP Inspector dev entry point.

``mcp dev`` loads a file as a standalone script, so it cannot import
``server.py`` directly (relative imports fail). This shim re-exports the
installed package's FastMCP instance instead.

Run from the repo root with the project venv active::

    mcp dev -e . scripts/mcp_dev.py:mcp
"""
from hlt_algo_mcp.server import mcp
