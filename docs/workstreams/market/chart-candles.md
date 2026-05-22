# Chart Candles API Contract

## Scope

This slice answers the stock-detail frontend request for a real price chart source. `GET /api/quotes` remains a quote snapshot API and must not be used to synthesize candles.

The chart-candles API is display-only OHLC data for stock-detail charts. It is not a raw market-data download API, not an order-book API, and not a minute-bar API.

## Frontend Request Summary

The frontend branch `codex/front-retail-sentiment-widget` blocks the stock-detail main chart because the current quote snapshot only has current/latest price, change, volume, provider, and freshness metadata. Rendering fixture candles or stretching them to the latest quote would make fake data look like a real Samsung Electronics/NVIDIA chart.

Public endpoint:

```http
GET /api/market/chart-candles?symbol=005930.KS&range=5Y&interval=1d
```

## Public Endpoint

`GET /api/market/chart-candles`

### Query

| Name | Required | Values | Default | Notes |
| --- | --- | --- | --- | --- |
| `symbol` | yes | `005930.KS`, `AAPL`, `NVDA` | none | Same provider symbol format as `GET /api/quotes`. |
| `range` | no | `1M`, `3M`, `6M`, `1Y`, `3Y`, `5Y` | `3M` | Bounded display ranges only. `5Y` is the longest public stock-detail chart window; do not add `MAX` or arbitrary `from/to` download behavior without another review. |
| `interval` | no | `1d`, `1wk`, `1mo` | `1d` | Public display candles only. No minute interval in this slice. |

Unsupported values return `400` with a small error body. If no cached candle set exists, the API returns `dataStatus: "INSUFFICIENT"` with empty `bars` so the frontend can keep the chart hidden.

### Response

```json
{
  "symbol": "005930.KS",
  "name": "Samsung Electronics",
  "market": "KR",
  "currency": "KRW",
  "range": "3M",
  "interval": "1d",
  "provider": "yfinance+FinanceDataReader",
  "delayLabel": "Yahoo Finance delayed up to 30 min",
  "asOf": "2026-05-21T04:30:00Z",
  "stale": false,
  "dataStatus": "OK",
  "bars": [
    {
      "date": "2026-05-21",
      "open": 280000,
      "high": 301000,
      "low": 279000,
      "close": 295500,
      "volume": 24688716
    }
  ],
  "displayPolicy": {
    "displayOnly": true,
    "rawMinute": false,
    "downloadable": false,
    "maxBars": 1260
  }
}
```

Required top-level fields:

`symbol`, `name`, `market`, `currency`, `range`, `interval`, `provider`, `delayLabel`, `asOf`, `stale`, `dataStatus`, `bars`, `displayPolicy`.

Required bar fields:

`date`, `open`, `high`, `low`, `close`, `volume`.

## Data Status

| Status | Front behavior | Meaning |
| --- | --- | --- |
| `OK` | Render chart. | Cached chart bars are fresh enough for display. |
| `PARTIAL` | Render with caution label. | Provider returned bars, but latest expected trading date may be missing. |
| `STALE` | Hide or show stale warning depending on product decision. | Cached bars are older than the stale threshold. |
| `INSUFFICIENT` | Hide chart and show API-needed/insufficient state. | Too few bars to draw a useful chart. |
| `PROVIDER_ERROR` | Hide chart unless stale cached bars are intentionally displayed. | Provider call failed. |

Do not use `MOCK` for this public API unless the whole environment is explicitly marked demo-only. If `MOCK` appears, stock-detail main chart should not render it as real market data.

## Provider And Collection Path

MVP provider split:

- `yfinance`: first source for public display OHLC bars for KR/US symbols.
- FinanceDataReader: domestic metadata and possible daily fallback/enrichment after compatibility checks.
- `pykrx`: fallback verification candidate only, not the default provider.

The implemented architecture follows the quote snapshot pattern:

1. Pipeline fetches candles from the provider.
2. Pipeline pushes a bounded display payload to an internal Spring endpoint.
3. Spring stores the latest bounded candle set.
4. Frontend reads the public `GET /api/market/chart-candles` endpoint.

Internal endpoint:

```http
POST /internal/market/chart-candles
```

This keeps provider calls out of the frontend request path and lets Spring apply a stable public contract, stale rules, and display guardrails.

## Storage

MySQL is the first display cache because the project already has it and the MVP range is small.

Storage model:

- `chart_candle_sets`: `symbol`, `range`, `interval`, `provider`, `delay_label`, `as_of`, `data_status`, `collected_at`.
- `chart_candles`: `set_id`, `trade_date`, `open`, `high`, `low`, `close`, `volume`.

Uniqueness:

- one latest set per `symbol + range + interval`.
- one candle per `set_id + trade_date`.

Redis can be added later if chart requests become hot or if WebSocket/STOMP market refresh is introduced. It is not required for this first display contract.

## Cache And Stale Rules

- Pipeline refresh cadence: every 10 minutes by default through the market refresh job registered by `python -m youbuyfirst_pipeline.main serve`.
- Public response max bars: `1260` daily bars, roughly five trading years.
- `1M`, `3M`, `6M`, `1Y`, `3Y`, `5Y` should stay bounded and should not expose arbitrary `from`/`to` download behavior.
- Backend stale threshold candidate: 36 hours until a market-calendar slice exists. During holidays/weekends this prevents normal closed-market data from looking broken too quickly.
- `asOf` should be the latest provider bar timestamp converted to UTC.
- `date` should be the exchange-local trading date for the candle, formatted as `YYYY-MM-DD`. Do not derive `bars[].date` from the UTC-converted timestamp. For Korean daily bars, a provider index such as `2026-05-15 00:00:00+09:00` must stay `2026-05-15`, even though the UTC instant is `2026-05-14T15:00:00Z`.
- `asOf` may be UTC, but `bars[].date` is a trading-day key used to match investor-flow `tradeDate`.

## Public Display Guardrails

Allowed:

- display-only daily/weekly/monthly OHLC bars.
- bounded ranges: `1M`, `3M`, `6M`, `1Y`, `3Y`, `5Y`.
- latest source metadata: `provider`, `delayLabel`, `asOf`, `stale`, `dataStatus`.

Not allowed in this slice:

- raw minute bars such as `1m`, `5m`, `15m`, `30m`, `60m`.
- order book levels or bid/ask depth.
- arbitrary date range downloads.
- CSV/export/download endpoints.
- bulk OHLC history.
- investment-advice wording or buy/sell CTA.

## Front Integration Rules

- Keep quote cards/header prices on `GET /api/quotes`.
- Use `GET /api/market/chart-candles` only for the main price chart.
- Do not derive chart bars from quote snapshots.
- Hide the chart when `bars` is empty or `dataStatus` is `INSUFFICIENT`, `PROVIDER_ERROR`, or `MOCK`.
- Show `asOf`, `provider`, `delayLabel`, `stale`, and `dataStatus` in the chart shell.
- The existing fixture fields `individual`, `foreign`, and `institution` should not be added to this candle response. Investor flow belongs to a separate previous-trading-day flow slice.

## Commands

Print provider candles:

```bash
python -m youbuyfirst_pipeline.main chart-candles --symbols 005930.KS AAPL NVDA --chart-range 5Y --interval 1d
```

Push provider candles to Spring:

```bash
python -m youbuyfirst_pipeline.main chart-candles-push --symbols 005930.KS AAPL NVDA --chart-range 5Y --interval 1d
```

Run scheduled quote and chart refresh:

```bash
python -m youbuyfirst_pipeline.main serve --market-refresh-interval-minutes 10
```

Frontend read:

```http
GET /api/market/chart-candles?symbol=005930.KS&range=3M&interval=1d
```

## Implemented Flow

1. Pipeline chart candle provider adapter wraps yfinance historical bars.
2. Spring internal upsert endpoint stores bounded candle sets.
3. Public `GET /api/market/chart-candles` reads the latest bounded set.
4. Tests cover the frontend response contract, unsupported minute intervals, display policy, and absence of investor-flow fields.
5. Front should replace the chart blocker only when this endpoint returns `bars` with `dataStatus: "OK"` or an explicitly accepted `PARTIAL`.
