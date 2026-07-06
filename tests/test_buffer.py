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


def test_index_quote_survives_buffer_eviction():
    buf = TapeBuffer(maxlen=5)
    buf.add(ev("SPY", "new_high", last_price=550.0, pct_change=0.8))
    for i in range(10):
        buf.add(ev("AAPL", "new_high", high_count=i))
    assert buf.recent(symbol="SPY") == []  # evicted from the FIFO
    assert buf.index_quotes()["SPY"].last_price == 550.0  # but retained here


def test_index_quotes_only_tracks_configured_symbols():
    buf = TapeBuffer(index_symbols=["SPY"])
    buf.add(ev("QQQ", "new_high", last_price=480.0))
    assert buf.index_quotes() == {}


def test_index_quotes_env_var_override(monkeypatch):
    monkeypatch.setenv("HLT_INDEX_SYMBOLS", "DIA,VTI")
    import importlib
    import hlt_algo_mcp.buffer as buffer_module
    importlib.reload(buffer_module)
    buf = buffer_module.TapeBuffer()
    buf.add(ev("DIA", "new_high", last_price=400.0))
    buf.add(ev("SPY", "new_high", last_price=550.0))
    assert list(buf.index_quotes().keys()) == ["DIA"]
    importlib.reload(buffer_module)  # restore default for later tests
