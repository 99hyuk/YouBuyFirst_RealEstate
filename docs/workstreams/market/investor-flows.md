# Investor Flow Snapshot

## 한눈에 보기

종목별 개인/외국인/기관 수급은 가격 snapshot이나 차트 candle에 섞지 않고 별도 slice로 제공한다. 프론트는 종목 상세에서 가격은 `GET /api/quotes`, 차트는 `GET /api/market/chart-candles`, 수급은 `GET /api/market/investor-flows`로 분리 호출한다.

이 API는 국내 종목/ETF의 전 거래일 확정 수급만 대상으로 한다. 장중 실시간 수급, 호가, 분봉, raw market feed, 대량 다운로드용 OHLC는 공개 화면에 제공하지 않는다.

## Provider 역할

- `pykrx`: KRX 투자자별 거래대금/거래량을 조회하는 1차 adapter 후보. 현재 pipeline adapter는 `get_market_trading_value_by_date`, `get_market_trading_volume_by_date`를 사용해 개인/외국인/기관 순매수 금액과 순매수 수량을 만든다.
- FinanceDataReader: 수급 provider가 아니라 국내 종목명, 시장, 통화 같은 메타데이터 보강에 사용한다.
- Naver Finance 직접 HTML crawling: 현재 slice에는 넣지 않는다. 공개 웹 페이지 구조에 기대는 fallback은 provider 안정성과 정책 리스크가 커서 별도 결정 전까지 금지한다.
- KRX OpenAPI 또는 상용 vendor: pykrx 경로가 안정적으로 동작하지 않거나 상용화 전 권한 검토가 필요하면 다음 후보로 검토한다.

pykrx 1.2.8 문서는 일부 KRX 로그인 필요 API에 `KRX_ID`, `KRX_PW` 환경변수가 필요하다고 안내한다. 이 값은 로컬 `.env`나 운영 secret으로만 주입하고 git에는 남기지 않는다.

## 공개 API

`GET /api/market/investor-flows?symbols=005930.KS,000660.KS,069500.KS`

공개 응답은 `GET /api/quotes`처럼 배열이다. 캐시에 없는 종목은 같은 shape로 `dataStatus: "INSUFFICIENT"`를 내려 프론트가 수급 영역만 숨길 수 있게 한다.

```json
[
  {
    "symbol": "005930.KS",
    "name": "Samsung Electronics",
    "market": "KR",
    "currency": "KRW",
    "tradeDate": "2026-05-21",
    "provider": "pykrx",
    "sourceLabel": "KRX investor trading by date via pykrx",
    "delayLabel": "Previous trading day investor flow",
    "asOf": "2026-05-21T00:00:00Z",
    "stale": false,
    "dataStatus": "OK",
    "individual": {
      "netAmount": 125000000000,
      "netVolume": 1700000
    },
    "foreign": {
      "netAmount": -90000000000,
      "netVolume": -1100000
    },
    "institution": {
      "netAmount": -35000000000,
      "netVolume": -600000
    }
  }
]
```

### 필드 의미

| 필드 | 의미 |
| --- | --- |
| `symbol`, `name`, `market`, `currency` | 프론트 표시용 종목 식별 정보 |
| `tradeDate` | 수급 기준 거래일. 전 거래일 확정 데이터 기준 |
| `provider` | 데이터를 만든 provider. 현재 후보는 `pykrx`, 없음은 `none` |
| `sourceLabel` | 사용자가 볼 수 있는 출처 설명 |
| `delayLabel` | 지연/확정 기준 설명. 수급은 장중 실시간이 아니라 전 거래일 기준 |
| `asOf` | 이 snapshot이 대표하는 기준 시각 |
| `stale` | stale 기준을 넘겼는지 여부 |
| `dataStatus` | `OK`, `STALE`, `INSUFFICIENT`, `PROVIDER_ERROR`, `MOCK` |
| `individual`, `foreign`, `institution` | 개인/외국인/기관의 순매수 금액과 순매수 수량 |

`netAmount`는 원화 순매수 금액, `netVolume`은 순매수 수량이다. 음수는 순매도 방향이다. 이 값은 관찰 데이터이지 서비스의 매수/매도 판단이 아니다.

## 내부 적재 API

pipeline은 provider 결과를 backend display cache로 밀어 넣는다.

`POST /internal/market/investor-flows`

```json
{
  "items": [
    {
      "symbol": "005930.KS",
      "name": "Samsung Electronics",
      "market": "KR",
      "currency": "KRW",
      "tradeDate": "2026-05-21",
      "provider": "pykrx",
      "sourceLabel": "KRX investor trading by date via pykrx",
      "delayLabel": "Previous trading day investor flow",
      "asOf": "2026-05-21T00:00:00Z",
      "dataStatus": "OK",
      "individual": {"netAmount": 125000000000, "netVolume": 1700000},
      "foreign": {"netAmount": -90000000000, "netVolume": -1100000},
      "institution": {"netAmount": -35000000000, "netVolume": -600000}
    }
  ]
}
```

## Pipeline 사용법

조회만 확인:

```powershell
.\pipeline\.venv\Scripts\python -m youbuyfirst_pipeline.main investor-flows --investor-flow-symbols 005930.KS 000660.KS 069500.KS --trade-date 2026-05-21
```

CLI 출력은 backend 적재 batch와 맞추기 위해 `{ "items": [...] }`로 감싸지만, 공개 GET API는 배열을 그대로 반환한다.

backend cache에 적재:

```powershell
.\pipeline\.venv\Scripts\python -m youbuyfirst_pipeline.main investor-flows-push --investor-flow-symbols 005930.KS 000660.KS 069500.KS --trade-date 2026-05-21
```

`serve` runtime에서는 quote/chart 10분 refresh와 별개로 수급 refresh job을 등록한다. 기본값은 한국시간 평일 18:30이다.

```env
MARKET_INVESTOR_FLOW_REFRESH_ENABLED=true
MARKET_INVESTOR_FLOW_SYMBOLS=005930.KS,000660.KS,069500.KS
MARKET_INVESTOR_FLOW_REFRESH_HOUR_LOCAL=18
MARKET_INVESTOR_FLOW_REFRESH_MINUTE_LOCAL=30
MARKET_INVESTOR_FLOW_REFRESH_TIMEZONE=Asia/Seoul
MARKET_INVESTOR_FLOW_STALE_AFTER_HOURS=96
# provider access 후보 검증용. git에 커밋하지 않는다.
KRX_ID=
KRX_PW=
```

## 캐시와 stale 기준

backend는 `investor_flow_snapshots` display cache를 가진다. 같은 `symbol`은 마지막 snapshot으로 upsert한다.

기본 stale 기준은 96시간이다. 휴일과 주말을 고려해 전 거래일 데이터가 금요일 장 종료 후 월요일까지 표시될 수 있도록 quote/chart보다 길게 둔다.

```env
INVESTOR_FLOW_STALE_MINUTES=5760
```

## 현재 검증 상태

계약과 adapter 구조는 구현한다. 다만 로컬 검증에서 pykrx 직접 호출은 KRX 응답 문제로 빈 DataFrame/Provider error를 반환했다. 따라서 프론트는 `dataStatus`가 `PROVIDER_ERROR` 또는 `INSUFFICIENT`이면 수급 UI를 숨겨야 한다.

다음 단계는 실제 provider 접근 안정화다. 후보는 pykrx 최신 버전 재검증, KRX OpenAPI, 또는 권한이 명확한 vendor이다.

참고:

- pykrx PyPI: https://pypi.org/project/pykrx/
- pykrx GitHub: https://github.com/sharebook-kr/pykrx
