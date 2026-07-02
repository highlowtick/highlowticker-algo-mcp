"""Shared test helper: build a TapeEvent from minimal kwargs."""
from hlt_algo_feed.models import TapeEvent


def ev(symbol, event, **kw):
    base = dict(
        type="TAPE_EVENT", ts="t", symbol=symbol, event=event,
        session_high=None, session_low=None, last_price=None, close_price=None,
        volume=None, pct_change=None, high_count=0, low_count=0,
        is_week52_high=False, is_week52_low=False, volume_spike=False,
        market_high_rate_30s=0, market_high_rate_1m=0, market_low_rate_30s=0,
        market_low_rate_1m=0, market_high_rate_5m=0, market_low_rate_5m=0,
        market_high_rate_20m=0, market_low_rate_20m=0,
    )
    base.update(kw)
    return TapeEvent.model_validate(base)
