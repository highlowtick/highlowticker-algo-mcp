# Algo feed field reference

Every egress frame is `{"type": "TAPE_EVENT", ...}`. The `event` field says which
kind it is. See `schema://algo-feed` for the full machine-readable schema.

## Event kinds (`event`)

| kind | fires when |
|---|---|
| `new_high` | a symbol prints a new session high |
| `new_low` | a symbol prints a new session low |
| `new_high_and_low` | both in the same update |
| `price_update` | a watched symbol ticks (requires a watch subscription; one frame per tick, unthrottled) |
| `market_summary` | periodic breadth push/pull (~1.5 s while subscribed); `symbol` is `-` |

## Fields

| field | meaning |
|---|---|
| `ts` | ISO-8601 UTC timestamp (ms) |
| `symbol` | ticker (or `-` for market_summary) |
| `session_high` / `session_low` | session extremes |
| `last_price` / `close_price` | last trade / prior close |
| `volume` | session volume |
| `pct_change` | percent change vs prior close |
| `high_count` / `low_count` | per-symbol cumulative new-high / new-low counts this session |
| `is_week52_high` / `is_week52_low` | at or beyond the 52-week extreme |
| `volume_spike` | volume-spike flag (hysteresis-latched) |
| `market_high_rate_30s` / `_1m` / `_5m` / `_20m` | market-wide new highs over the window |
| `market_low_rate_30s` / `_1m` / `_5m` / `_20m` | market-wide new lows over the window |
| `trade_side` | aggressor on the print: buy / sell / unknown (optional) |
| `last_size` | size of the classified print (optional) |
| `cvd` | session cumulative volume delta (optional) |
| `top_imbalance` | L1 top-of-book imbalance (optional) |
| `buy_pct_5m` / `sell_pct_5m` | 5-minute aggressive buy / sell share, market_summary only (optional) |
