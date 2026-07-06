# hlt_algo_feed Python client — quickstart

Install: `pip install highlowticker-algo-feed`

This is the pypi client for the same wire protocol described in
`doc://field-reference` / `schema://algo-feed`. Use it to write a strategy
script that runs standalone (outside this MCP), against a running
HighLowTicker instance with the algo feed enabled (`ws://127.0.0.1:7412`
by default).

**Read-only / no trading:** there is no order-placement surface anywhere in
this client. A "strategy" here means: watch the tape, decide, print/log —
never submit an order. There is also no historical/backtest data source;
`AlgoFeed` only streams what HighLowTicker sees live, from the moment you
connect.

## Core class: `AlgoFeed`

```python
from hlt_algo_feed import AlgoFeed

async with AlgoFeed("ws://127.0.0.1:7412") as feed:
    await feed.watch(["SPY", "AAPL"])     # subscribe to price_update ticks
                                           # for these symbols (replaces any
                                           # prior watch set — not additive)
    await feed.subscribe_summary(True)    # turn on periodic market_summary
    async for ev in feed:                 # ev is a typed TapeEvent
        print(ev.symbol, ev.event, ev.last_price, ev.pct_change)
```

Other `AlgoFeed` methods:
- `await feed.unwatch()` — clears the watch set (equivalent to `watch([])`).
- `async for ev in feed.new_highs()` — yields only `new_high`/`new_high_and_low` events.
- `async for ev in feed.new_lows()` — yields only `new_low`/`new_high_and_low` events.
- `async for ev in feed.summaries()` — yields only `market_summary` events.

## Easiest path: `run()` (sync-friendly facade)

For a strategy that's "a handler function plus a watch list," skip manual
connect/reconnect entirely:

```python
from hlt_algo_feed import run

def handler(ev):
    if ev.symbol == "SPY" and "high" in ev.event:
        print(f"SPY new high @ {ev.last_price}")

run(handler, watch=["SPY"], summary=False, reconnect=True)
```

`run(handler, *, watch=None, summary=False, reconnect=True)` owns the whole
lifecycle — connect, (re)subscribe, iterate, dispatch, and automatic
reconnect with backoff on a dropped socket. `handler(ev)` may be a plain
function or an `async def` — both are supported.

## Declarative alternative: `notify_when()`

For "fire an action once per condition, don't repeat it":

```python
from hlt_algo_feed import AlgoFeed

async with AlgoFeed() as feed:
    await feed.notify_when(
        condition=lambda ev: ev.symbol == "SPY" and (ev.high_count or 0) >= 5,
        action=lambda ev: print(f"SPY milestone hit @ {ev.last_price}"),
        once=lambda ev: ev.symbol,   # dedup key: only fires once per symbol
        watch=["SPY"],
    )
```

## Minimal complete strategy (paper-trade skeleton)

This mirrors the pattern used throughout this project's own examples —
a plain class holding position/entry/realized state, driven by `run()`:

```python
import os
from hlt_algo_feed import run

SYMBOL = os.environ.get("HLT_SYMBOL", "SPY").strip().upper()
MILESTONE = int(os.environ.get("HLT_MILESTONE", "5"))


class Momentum:
    """Long on the Nth new high, flat on a new low. Local paper account."""

    def __init__(self):
        self.pos, self.entry, self.realized = 0, 0.0, 0.0

    def __call__(self, ev):
        if ev.symbol != SYMBOL or ev.last_price is None:
            return
        if self.pos == 0 and "high" in ev.event and (ev.high_count or 0) >= MILESTONE:
            self.pos, self.entry = 1, ev.last_price
            print(f"ENTER {ev.symbol} @ {self.entry:.2f}", flush=True)
        elif self.pos == 1 and "low" in ev.event:
            self.realized += ev.last_price - self.entry
            print(f"EXIT  {ev.symbol} @ {ev.last_price:.2f}  realized {self.realized:+.2f}", flush=True)
            self.pos = 0


if __name__ == "__main__":
    run(Momentum(), watch=[SYMBOL])
```

Adapt the `__call__` decision logic for a different strategy — the
lifecycle (`run()`, watch list, reconnect) never needs to change.

## Field meanings

See `doc://field-reference` for what each `TapeEvent` field means
(`event` kinds, `pct_change`, `high_count`/`low_count`, `trade_side`, etc.) —
this quickstart only covers the *client*, not the wire format.
