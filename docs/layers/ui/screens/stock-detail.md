# 종목 상세 화면

## Route

- Parent: `stocks`
- Route 후보: `/stocks/:symbol`
- 현재 API 예시: `005930.KS`, `NVDA`. 현재가/등락률/거래량은 `GET /api/quotes`, 메인 차트는 `GET /api/market/chart-candles`, 국내 거래일별 수급은 `GET /api/market/investor-flows/history`를 사용한다.
- Child screens:
  - `stock-news-detail`: 뉴스/공시/리포트 링크 상세 또는 drawer
  - `stock-community-post`: 커뮤니티 원문 snippet/출처 상세
  - `stock-indicator-detail`: 기술/재무 지표 개별 설명 panel

## 화면 목적

사용자가 종목 랭킹에서 특정 종목을 눌렀을 때 가격 흐름, 커뮤니티 반응, 근거 링크, 데이터 신뢰도를 한 화면에서 빠르게 확인하게 한다. 상단 팩트폭격 카피는 `docs/domains/agent/STOCK_DETAIL_HEADLINE.md` 기준의 시황 요약이며, 검은 배너 표현은 `docs/layers/ui/STOCK_DETAIL_BANNER.md`를 따른다. 투자 행동을 지시하는 문구가 아니라 공개 데이터 기반 상태 표현으로 유지한다.

## 현재 섹션

- 팩트폭격 상단 패널: 종목명, 티커, 한줄평, 보조 시황 문장, 근거 keyword chips
- 종목 헤더: 종목명, 시장, quote snapshot 기반 현재가/등락률/거래량/asOf/stale 상태
- 메인 가격 차트: `StockPriceChart` 기반 자체 UI shell. `GET /api/market/chart-candles`를 사용하고, 기본 화면 범위는 3M, 선택지는 `1M`, `3M`, `6M`, `1Y`, `3Y`, `5Y`로 둔다.
- quote snapshot 영역: `GET /api/quotes` 응답을 가격 근처에 표시한다. 현재가/등락률/거래량은 차트에서 긁지 않는다.
- 거래일별 수급 영역: 국내 종목/ETF만 `GET /api/market/investor-flows/history` 응답으로 표시한다. 미국 종목은 숨긴다.
- 데이터 상태: quote/chart/수급 각각 provider, delayLabel, asOf, stale, dataStatus를 노출한다. 실패나 빈 배열을 0값처럼 보이게 만들지 않는다.
- 요약 지표 strip: 반응 점수, 언급 변화, 긍정/부정, 출처 수, 원문 링크 수
- 반응 키워드와 시간대별 변화: 30분 키워드 pulse, 09:00~09:45 snapshot
- 커뮤니티 반응 추이: 30분/1일/1주 언급량과 긍정/부정/중립 비율
- 어제와 달라진 점: 매일 들어왔을 때 바로 볼 변화 요약
- 소스별 반응: 네이버 종토방, 디시, 뽐뿌, 에펨코리아별 언급/반응/메모
- 이벤트 타임라인: 뉴스, 커뮤니티, 가격, 인기글, 리포트를 시간순으로 묶음
- 근거 링크: 뉴스, 리포트, 영상, 블로그, 커뮤니티 제목 링크
- 신호 신뢰도: 표본 수, 커뮤니티 편중, 출처 다양성, 가격 지연, 원문 확인 필요

## 상태와 빈 화면

- loading: 팩트폭격 패널, quote snapshot, chart candle shell fallback을 먼저 보여준다.
- empty: 근거가 부족하면 `headlineTone`을 `normal`로 낮추고 표본/원문 부족을 신뢰도 영역에 표시한다.
- error: chart candle 실패와 quote snapshot 실패를 분리해서 표시한다.
- stale/mock: 가격, 차트, 수급 영역마다 해당 `dataStatus`, `asOf`, `stale`을 분리 표시한다.
- investor flow stale/error: 수급은 장중 실시간처럼 보이게 표시하지 않는다. 국내 종목의 배열이 비면 표를 숨기고 빈 상태 패널만 보여준다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `symbol`, `name`, `market` | stock/backend | 종목 식별과 표시명 |
| `quoteSnapshot` | market | `GET /api/quotes` 응답. 가격 근처에 provider/asOf/delayLabel/stale/dataStatus를 함께 표시한다. |
| `chartCandles` | market | `GET /api/market/chart-candles` 응답. 빈 bars 또는 실패 상태면 차트를 숨긴다. 거래일 key와 표시 정책은 `docs/domains/market/CHART_CANDLES.md`를 따른다. |
| `investorFlowHistory` | market | `GET /api/market/investor-flows/history` 응답. 국내 종목/ETF의 거래일별 수급만 표시한다. `derived=true` 값은 직접 관찰값처럼 보이지 않게 라벨링한다. |
| `headlineTone`, `headline`, `subtitle`, `scoreLine`, `riskNote` | agent/backend | 상단 팩트폭격 카피와 보조 문구 |
| `headlineEvidence` | market/indicator/agent | 한줄평 근거 chip 배열 |
| `quickStats` | indicator | 반응 점수, 언급 변화, 출처 수, 링크 수 |
| `keywordPulse` | indicator | 30분 반응 키워드 증감 |
| `intradaySnapshots` | indicator/market | 시간대별 언급, 반응, 가격 변화 |
| `reactionTrend` | indicator | 30분/1일/1주 언급량과 반응 비율 |
| `sourceReaction` | indicator/community | 커뮤니티별 언급, 긍정/부정, 메모 |
| `events` | backend/indicator/market | 뉴스, 공시, 가격, 커뮤니티 이벤트 타임라인 |
| `evidenceLinks` | community/indicator | 제목 링크와 출처, 원문 URL |
| `reliability` | backend/indicator | 표본 수, 편중, 출처 다양성, 가격 지연, 원문 확인 |
| `dataQuality` | backend | `complete`, `stale`, `partial`, `mock`, `insufficient` |

## 확인 필요

- 외인보유/보유율 컬럼은 현재 API에 없으므로 표시하지 않는다. 필요하면 market API 후보로 `foreignHolding`, `foreignHoldingPct`를 별도 논의한다.
- Lightweight Charts용 chartCandles와 quoteSnapshot의 기준 시각 차이를 어떻게 표시할지.
- quote snapshot만으로 차트를 만들지 않는다.
- 이평선과 zoom/scroll 축 요약은 API가 내려준 전체 bars를 기준으로 계산하고, 화면 범위만 1M/3M/6M/1Y/3Y/5Y로 조절한다. 단기 이평은 5/10/20, 장기 이평은 60/120/200을 쓰고 색상 범례를 함께 표시한다. 날짜 축은 확대/축소에 따라 일/월/년 단위 tick이 여러 개 보이게 유지한다.
- 차트 로드 실패 시 quote snapshot과 커뮤니티 반응을 그대로 보여줄지.
- 뉴스/공시/커뮤니티 글 상세를 별도 route로 둘지 drawer/panel로 둘지.

## 변경 로그

- 2026-05-21: quote snapshot은 `GET /api/quotes`, 메인 가격 차트는 `GET /api/market/chart-candles`로 분리했다. 차트가 숨겨지는 상태와 차트 shell metadata 표시 기준을 최신 API 계약에 맞췄다.
- 2026-05-22: chart-candles 요청 범위를 5Y로 두고 기본 화면 범위만 3M으로 제한해 장기 이평선과 확대/축소 축을 실제 bars 기준으로 계산한다. 축 라벨은 zoom/scroll과 봉 단위에 맞춰 여러 날짜 tick이 일/월/년 단위로 바뀌도록 보정했다.
- 2026-05-22: 국내 종목/ETF 수급은 `GET /api/market/investor-flows/history` 단일 public API로 정리했다. 최신 1건 public API는 두지 않고, 가격/차트 API에는 개인/외국인/기관 수급을 넣지 않는다.
- 2026-05-22: 수급 provider는 `naver-finance` 기본값으로 바꿨다. 외국인/기관은 순매수 수량 관찰값, 개인은 잔차 추정값(`derived=true`)이며, 금액이 없으면 `netAmount=null`이다.
