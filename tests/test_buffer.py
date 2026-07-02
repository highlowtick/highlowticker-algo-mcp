from hlt_algo_mcp.buffer import TapeBuffer
from tests_helpers import ev


def test_recent_filters_by_symbol_and_kind():
    buf = TapeBuffer()
    buf.add(ev("AAPL", "new_high"))
    buf.add(ev("NVDA", "new_low"))
    buf.add(ev("AAPL", "new_low"))
    assert [e.symbol for e in buf.recent(symbol="AAPL")] == ["AAPL", "AAPL"]
    assert [e.event for e in buf.recent(kind="new_low")] == ["new_low", "new_low"]


def test_latest_summary_returns_last_summary_only():
    buf = TapeBuffer()
    buf.add(ev("-", "market_summary", buy_pct_5m=61.0))
    buf.add(ev("AAPL", "new_high"))
    buf.add(ev("-", "market_summary", buy_pct_5m=55.0))
    assert buf.latest_summary().buy_pct_5m == 55.0


def test_summary_not_in_recent():
    buf = TapeBuffer()
    buf.add(ev("-", "market_summary", buy_pct_5m=61.0))
    buf.add(ev("AAPL", "new_high"))
    assert [e.symbol for e in buf.recent()] == ["AAPL"]


def test_top_movers_ranks_by_high_count():
    buf = TapeBuffer()
    buf.add(ev("AAPL", "new_high", high_count=3))
    buf.add(ev("NVDA", "new_high", high_count=7))
    assert buf.top_movers(by="high", k=1) == [("NVDA", 7)]


def test_top_movers_by_low():
    buf = TapeBuffer()
    buf.add(ev("PWR", "new_low", low_count=4))
    buf.add(ev("ENPH", "new_low", low_count=2))
    assert buf.top_movers(by="low", k=5) == [("PWR", 4), ("ENPH", 2)]
