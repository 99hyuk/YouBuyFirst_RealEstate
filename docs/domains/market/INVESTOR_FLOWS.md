# Investor Flow History

## 한눈에 보기

종목별 개인/외국인/기관 수급은 가격 snapshot이나 차트 candle에 섞지 않고 별도 history slice로 제공한다. 프론트는 종목 상세에서 가격은 `GET /api/quotes`, 차트는 `GET /api/market/chart-candles`, 수급은 `GET /api/market/investor-flows/history`로 분리 호출한다.

이 API는 국내 종목/ETF의 거래일별 확정 관찰 데이터만 다룬다. 장중 실시간 수급, 외인 보유율, 원시 market feed, 다운로드용 OHLC는 이 화면 API에 포함하지 않는다.

## Provider 역할

- `naver-finance`: 현재 1차 수급 provider. 네이버 금융 `item/frgn.nhn` 공개 표에서 거래일별 기관 순매수 수량과 외국인 순매수 수량을 읽는다. 네이버 표에는 개인 값이 직접 없으므로 `개인 = -(외국인 + 기관)` 잔차로 계산하고 `derived=true`로 표시한다.
- `pykrx`: KRX 투자자별 거래대금/거래량을 조회하는 후보 adapter. KRX 응답이 세션/권한 문제로 비어 있거나 실패할 수 있어 기본 provider에서 제외하고, 필요할 때 `MARKET_INVESTOR_FLOW_PROVIDER=pykrx`로 검증한다.
- FinanceDataReader: 종목명, 시장, 통화 같은 국내 종목 메타데이터 보강에 사용한다. 현재 FinanceDataReader의 네이버 수급 snapshot wrapper는 네이버 표 구조와 맞지 않아 1차 수급 provider로 쓰지 않는다.
- KRX OpenAPI 또는 상용 vendor: 서비스 트래픽, 상용화, 재배포 권한이 중요해지면 다음 안정화 후보로 검토한다.

## 공개 API

`GET /api/market/investor-flows/history?symbol=005930.KS&limit=20`

공개 응답은 단일 국내 종목의 거래일별 수급 배열이며 `tradeDate` 최신순이다. `limit` 기본값은 20이고 서버에서 상한을 둔다. 표시 가능한 상태는 `OK`, `STALE`뿐이며 `INSUFFICIENT`, `PROVIDER_ERROR`, `MOCK` row는 공개 history 응답에 넣지 않는다.

단일 최신 수급 public endpoint는 두지 않는다. 최신 1건이 필요하면 history 응답의 첫 번째 row를 사용한다.

```json
[
  {
    "symbol": "005930.KS",
    "name": "Samsung Electronics",
    "market": "KR",
    "currency": "KRW",
    "tradeDate": "2026-05-21",
    "provider": "naver-finance",
    "sourceLabel": "Naver Finance investor trend; individual is residual from foreign and institution",
    "delayLabel": "Previous trading day investor trend",
    "asOf": "2026-05-21T00:00:00Z",
    "stale": false,
    "dataStatus": "OK",
    "individual": {
      "netAmount": null,
      "netVolume": -6280909,
      "derived": true
    },
    "foreign": {
      "netAmount": null,
      "netVolume": 3672423,
      "derived": false
    },
    "institution": {
      "netAmount": null,
      "netVolume": 2608486,
      "derived": false
    }
  }
]
```

### 필드 의미

| 필드 | 의미 |
| --- | --- |
| `symbol`, `name`, `market`, `currency` | 프론트 표시용 종목 메타데이터 |
| `tradeDate` | 수급 기준 거래일. 장중 시각이 아니라 거래일별 관찰 row 기준 |
| `provider` | 데이터를 만든 provider. 기본값은 `naver-finance`, 선택 검증값은 `pykrx` |
| `sourceLabel` | 사용자에게 보여줄 수 있는 출처 설명 |
| `delayLabel` | 지연/확정 기준 설명. 수급은 장중 실시간처럼 표시하지 않는다 |
| `asOf` | 해당 snapshot이 대표하는 기준 시각 |
| `stale` | stale 기준을 넘겼는지 여부 |
| `dataStatus` | 공개 history에서는 `OK`, `STALE`만 반환한다 |
| `individual`, `foreign`, `institution` | 개인/외국인/기관별 순매수 관찰값 또는 잔차값 |
| `netAmount` | 순매수 금액. provider가 금액을 제공하지 않으면 `null` |
| `netVolume` | 순매수 수량. 음수는 순매도 방향 |
| `derived` | 직접 관찰값이 아니라 다른 관찰값으로 계산한 값인지 여부 |

`naver-finance` provider에서는 외국인/기관 `netVolume`만 직접 관찰값이고 `netAmount`는 `null`이다. 개인 `netVolume`은 외국인과 기관의 합이 0으로 맞는다는 표 구조를 이용한 잔차라서 `derived=true`로 내려간다. 프론트는 이 값을 `개인(잔차)` 또는 `개인 추정`처럼 표시하고, 실제 개인 원천값처럼 단정하지 않는다.

## 내부 적재 API

pipeline은 provider 결과를 backend display cache로 batch 적재한다.

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
      "provider": "naver-finance",
      "sourceLabel": "Naver Finance investor trend; individual is residual from foreign and institution",
      "delayLabel": "Previous trading day investor trend",
      "asOf": "2026-05-21T00:00:00Z",
      "dataStatus": "OK",
      "individual": {"netAmount": null, "netVolume": -6280909, "derived": true},
      "foreign": {"netAmount": null, "netVolume": 3672423, "derived": false},
      "institution": {"netAmount": null, "netVolume": 2608486, "derived": false}
    }
  ]
}
```

내부 적재 API는 `OK`, `STALE` row만 저장한다. `PROVIDER_ERROR`, `INSUFFICIENT`, `MOCK` row는 저장하지 않는다. provider 실패 때 0값을 넣어서 "실제 수급 0"처럼 보이게 만들지 않는다.

## Pipeline 사용법

조회만 확인:

```powershell
.\pipeline\.venv\Scripts\python -m youbuyfirst_pipeline.main investor-flows --investor-flow-symbols 005930.KS --trade-date 2026-05-21 --investor-flow-limit 20
```

backend cache에 적재:

```powershell
.\pipeline\.venv\Scripts\python -m youbuyfirst_pipeline.main investor-flows-push --investor-flow-symbols 005930.KS --trade-date 2026-05-21 --investor-flow-limit 20
```

provider를 명시해 검증할 때:

```powershell
.\pipeline\.venv\Scripts\python -m youbuyfirst_pipeline.main investor-flows --investor-flow-symbols 005930.KS --investor-flow-provider pykrx
```

`serve` runtime에서는 quote/chart 10분 refresh와 별개로 수급 refresh job을 등록한다. 기본값은 한국시간 평일 18:30이다.

```env
MARKET_INVESTOR_FLOW_PROVIDER=naver-finance
MARKET_INVESTOR_FLOW_REFRESH_ENABLED=true
MARKET_INVESTOR_FLOW_SYMBOLS=005930.KS,000660.KS,069500.KS
MARKET_INVESTOR_FLOW_HISTORY_LIMIT=20
MARKET_INVESTOR_FLOW_REFRESH_HOUR_LOCAL=18
MARKET_INVESTOR_FLOW_REFRESH_MINUTE_LOCAL=30
MARKET_INVESTOR_FLOW_REFRESH_TIMEZONE=Asia/Seoul
MARKET_INVESTOR_FLOW_STALE_AFTER_HOURS=96
```

## 캐시와 stale 기준

backend는 `investor_flow_snapshots` display cache를 가진다. 같은 `symbol + tradeDate`는 마지막 snapshot으로 upsert한다.

기본 stale 기준은 96시간이다. 거래일별 확정 관찰 데이터라 quote/chart보다 길게 둔다. 장중 실시간처럼 보이지 않게 `tradeDate`, `delayLabel`, `provider`, `asOf`, `stale`을 함께 표시한다.

```env
INVESTOR_FLOW_STALE_MINUTES=5760
```

## 현재 검증 상태

- `naver-finance` provider는 `item/frgn.nhn` 공개 HTML 표를 parsing해 여러 거래일 row를 생성한다.
- backend는 `netAmount=null`과 `derived` flag를 저장/응답할 수 있다.
- public history API는 `OK`, `STALE` row만 반환하고 실패 row나 mock row를 공개하지 않는다.
- pykrx 직접 provider는 KRX 응답/세션 문제로 실패할 수 있어 선택 검증용으로만 둔다.

참고:

- Naver Finance item investor trend: `https://finance.naver.com/item/frgn.nhn?code=005930`
- pykrx PyPI: https://pypi.org/project/pykrx/
- pykrx GitHub: https://github.com/sharebook-kr/pykrx
