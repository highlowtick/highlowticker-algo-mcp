import pytest
from datetime import datetime, timezone

from hlt_algo_mcp.buffer import TapeBuffer
from hlt_algo_mcp import server as srv
from tests_helpers import ev


@pytest.fixture(autouse=True)
def fresh_buffer():
    srv.BUFFER = TapeBuffer()
    yield


def test_recent_tape_tool_returns_dicts():
    srv.BUFFER.add(ev("AAPL", "new_high", high_count=2))
    out = srv.recent_tape(symbol="AAPL")
    assert out and out[0]["symbol"] == "AAPL" and out[0]["high_count"] == 2


def test_recent_tape_filters_by_kind():
    srv.BUFFER.add(ev("AAPL", "new_high"))
    srv.BUFFER.add(ev("NVDA", "new_low"))
    out = srv.recent_tape(kind="new_low")
    assert [o["symbol"] for o in out] == ["NVDA"]


def test_get_market_summary_none_when_empty():
    assert srv.get_market_summary() is None


def test_get_market_summary_returns_latest():
    srv.BUFFER.add(ev("-", "market_summary", buy_pct_5m=61.0))
    assert srv.get_market_summary()["buy_pct_5m"] == 61.0


def test_top_movers_tool():
    srv.BUFFER.add(ev("NVDA", "new_low", low_count=4))
    assert srv.top_movers(by="low", k=5) == [{"symbol": "NVDA", "count": 4}]


def test_index_quotes_empty_before_any_index_event():
    assert srv.index_quotes() == {}


def test_index_quotes_returns_last_known_per_symbol():
    srv.BUFFER.add(ev("SPY", "new_high", last_price=550.0, pct_change=0.8))
    result = srv.index_quotes()
    assert result["SPY"]["last_price"] == 550.0
    assert result["SPY"]["pct_change"] == 0.8


def test_python_client_quickstart_resource_is_readable():
    text = srv.python_client_quickstart()
    assert "AlgoFeed" in text
    assert "pip install highlowticker-algo-feed" in text


def test_hottest_recent_empty_before_any_event():
    result = srv.hottest_recent()
    assert result["movers"] == []
    assert result["window_seconds"] == 300
    assert result["coverage_seconds"] >= 0


def test_hottest_recent_returns_ranked_movers():
    now_ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    srv.BUFFER.add(ev("AAPL", "new_high", high_count=1, ts=now_ts))
    result = srv.hottest_recent(window_seconds=300)
    assert result["movers"] == [{"symbol": "AAPL", "count": 1}]
    assert result["window_seconds"] == 300
