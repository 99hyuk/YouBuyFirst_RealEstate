# Quote Snapshot Contract

## Scope

This slice gives the frontend a limited quote snapshot for public display. It does not expose raw minute candles, order book levels, bulk OHLC history, or a downloadable market-data API.

The MVP provider path is:

- `yfinance`: first source for exchange-delayed quote price, previous-close change, percent change, and cumulative volume for KR/US symbols.
- FinanceDataReader: domestic metadata and previous-trading-day domestic flow candidates.
- backend `quote_snapshots`: latest snapshot cache consumed by `/api/quotes`.

For quote snapshots, `Close` means the close of the latest intraday bar from Yahoo data, not the final end-of-day close. The adapter combines that timestamp with `fast_info.lastPrice`, `fast_info.regularMarketPreviousClose`, and `fast_info.lastVolume` so the visible `change`/`changePct` are previous-close based.

## Provider Symbols

Initial verification symbols:

| Symbol | Market | Currency | Note |
| --- | --- | --- | --- |
| `005930.KS` | `KR` | `KRW` | Samsung Electronics |
| `000660.KS` | `KR` | `KRW` | SK hynix |
| `069500.KS` | `KR` | `KRW` | KODEX 200 ETF |
| `AAPL` | `US` | `USD` | Apple |
| `NVDA` | `US` | `USD` | NVIDIA |

## API Shape

`GET /api/quotes?symbols=005930.KS,AAPL,NVDA`

```json
[
  {
    "symbol": "005930.KS",
    "name": "Samsung Electronics",
    "market": "KR",
    "currency": "KRW",
    "price": 78200,
    "change": 600,
    "changePct": 0.77,
    "volume": 18400000,
    "asOf": "2026-05-20T06:00:00Z",
    "provider": "yfinance+FinanceDataReader",
    "delayLabel": "Yahoo Finance delayed up to 30 min",
    "stale": false,
    "dataStatus": "OK"
  },
  {
    "symbol": "AAPL",
    "name": "Apple",
    "market": "US",
    "currency": "USD",
    "price": 198.12,
    "change": 1.25,
    "changePct": 0.64,
    "volume": 42123456,
    "asOf": "2026-05-20T20:00:00Z",
    "provider": "yfinance",
    "delayLabel": "Yahoo Finance 10 min refresh snapshot",
    "stale": false,
    "dataStatus": "OK"
  }
]
```

Required frontend fields are exactly:

`symbol`, `name`, `market`, `currency`, `price`, `change`, `changePct`, `volume`, `asOf`, `provider`, `delayLabel`, `stale`, `dataStatus`.

## Collection Flow

1. Pipeline command:
   `python -m youbuyfirst_pipeline.main quote-snapshot --symbols 005930.KS 000660.KS 069500.KS AAPL NVDA`
2. Pipeline push:
   `python -m youbuyfirst_pipeline.main quote-push --symbols 005930.KS 000660.KS 069500.KS AAPL NVDA`
3. Backend receives snapshots at:
   `POST /internal/market/quote-snapshots`
4. Frontend reads:
   `GET /api/quotes?symbols=005930.KS,000660.KS,069500.KS,AAPL,NVDA`

## Cache And Stale Rules

- Yahoo Finance lists `.KS` and `.KQ` Korea data as 20 minutes delayed. The pipeline refreshes every 10 minutes by default, so Korea quotes are displayed as "up to 30 min delayed" rather than real-time.
- US exchange timing differs by exchange, so US quotes are labeled as a 10-minute refresh snapshot, not as a guaranteed 10-minute delayed feed.
- Pipeline provider cache TTL: `MARKET_QUOTE_CACHE_TTL_SECONDS`, default `600` seconds. This is the app refresh cadence, not proof that the upstream data is exactly 10 minutes old for every exchange.
- Backend latest-snapshot cache: one row per `symbol` in `quote_snapshots`; upsert replaces the public snapshot.
- Backend stale threshold: `QUOTE_STALE_MINUTES`, default `2160` minutes (36 hours), so after-hours and holiday snapshots do not immediately look broken. A later market-calendar slice can tighten this during open market hours.
- If `asOf + threshold < now`, backend returns `stale: true` and `dataStatus: "STALE"` even if the collected payload said `OK`.
- Public UI must show `delayLabel`, `provider`, `asOf`, `stale`, and `dataStatus` near displayed prices.

## Public Display Guardrail

This API is intentionally snapshot-only:

- allowed: current/latest price, change, change percent, latest volume, provider, `asOf`, stale/data status.
- not allowed in this slice: raw minute bars, order-book levels, bulk OHLC history, provider download endpoints, or signals that look like investment advice.

## Previous-Day Investor Flow Candidate

Domestic investor flow is separate from the quote snapshot response. It should be added as a previous-trading-day data slice, not intraday real-time flow.

- Base instrument: KODEX 200 ETF, `069500.KS`.
- Reference timing: previous trading day, not intraday real-time.
- Candidate fields: personal/foreign/institution net buy/sell amount, volume, amount, reference date, provider, source URL/label.
- Candidate providers/sources:
  - FinanceDataReader `SnapDataReader("NAVER/INVESTORS/{code}")` for the Naver investor-flow path where it works. In the current package this path exposes institution/foreign net trading volume, but it must be compatibility-checked because Naver table shape can change.
  - KRX public pages or data endpoints for personal/foreign/institution previous-day flow after confirming display and redistribution conditions.
  - pykrx only as a fallback verification candidate, not the default MVP provider.
