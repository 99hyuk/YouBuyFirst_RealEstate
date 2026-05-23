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
- 메인 가격 차트: TradingView embed가 아니라 `StockPriceChart` 기반의 자체 UI shell이다. 종목 헤더 아래에 두고, 차트 메타 정보는 그래프보다 뒤로 보내 실제 캔버스가 빨리 보이게 한다. `GET /api/market/chart-candles?range=5Y&interval=1d`를 호출해 실제 display-only OHLC bars가 오면 렌더링하고, 화면 기본 범위는 3M으로 둔다. 화면 선택지는 `1M`, `3M`, `6M`, `1Y`, `3Y`, `5Y`이며, `bars`가 비었거나 `dataStatus`가 `INSUFFICIENT`, `PROVIDER_ERROR`, `MOCK`이면 차트를 숨기고 상태 안내를 보여준다. 국내 종목 차트에 비거래일 bar가 있거나 수급 날짜와 차트 날짜가 맞지 않으면 날짜 정합성 경고를 표시한다.
- quote snapshot 영역: `GET /api/quotes?symbols=005930.KS,AAPL,NVDA` 응답을 우선 사용한다. 현재가, 등락률, 거래량, asOf, provider, delayLabel, stale, dataStatus는 가격 근처에 함께 보여주며 차트에서 긁지 않는다.
- 거래일별 수급 영역: 국내 종목/ETF는 `GET /api/market/investor-flows/history?symbol=005930.KS&limit=20` 응답으로 최근 거래일별 개인/외국인/기관 순매수 표를 보여준다. 화면 제목과 안내문에는 수급이 공개 표 기반 추정치이며 실제 확정값과 다를 수 있음을 명시한다. `naver-finance` row는 외국인/기관 순매수 수량만 직접 관찰값이고 개인은 잔차 추정값이므로, `individual.derived=true`이면 `개인(잔차)`처럼 표시한다. `netAmount`가 `null`이면 금액은 `-`로 처리하고 0원처럼 보이지 않게 한다. `tradeDate`, `provider`, `sourceLabel`, `delayLabel`, `asOf`, `stale`, `dataStatus`를 함께 표시한다. public API는 `OK`, `STALE` row만 반환하며, 국내 종목에서 응답 배열이 비면 가짜 0값 표 대신 빈 상태 문구만 보여준다. 미국 종목은 수급 영역을 숨긴다. 표는 5줄 높이 스크롤 목록으로 둔다. 수급 row와 같은 날짜의 `chart-candles` bar가 없으면 종가/전일비/등락률/거래량 칸은 `-`로 표시한다.
- 차트 데이터 상태: `bars`가 비었거나 `dataStatus`가 `INSUFFICIENT`, `PROVIDER_ERROR`, `MOCK`이면 메인 차트를 숨기고 차트 영역에 API 상태 안내를 표시한다. 렌더링 가능한 경우에도 asOf, provider, delayLabel, stale, dataStatus를 차트 shell 안에 함께 보여준다.
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
- stale/mock: `quoteSnapshot.dataStatus`, `quoteSnapshot.asOf`, `quoteSnapshot.stale`, `chartCandles.dataStatus`, `chartCandles.asOf`, `chartCandles.stale`을 각각 가격/차트 영역에 함께 표시한다.
- investor flow stale/error: 수급은 거래일별 확정 관찰 데이터라 장중 실시간처럼 보이게 표시하지 않는다. `investorFlow.delayLabel`, `investorFlow.tradeDate`, `investorFlow.provider`, `investorFlow.stale`, `investorFlow.dataStatus`를 수급 영역에 함께 표시한다. public history 응답은 `OK`, `STALE`만 표에 표시하고, 국내 종목의 배열이 비면 0 수급처럼 보이지 않게 표를 숨기되 빈 상태 패널로 위치를 알려준다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `symbol`, `name`, `market` | stock/backend | 종목 식별과 표시명 |
| `chartCandles.symbol`, `name`, `market`, `currency`, `range`, `interval`, `provider`, `delayLabel`, `asOf`, `stale`, `dataStatus`, `bars`, `displayPolicy` | market | `GET /api/market/chart-candles` 응답 shape. `bars`가 비었거나 `dataStatus`가 `INSUFFICIENT`, `PROVIDER_ERROR`, `MOCK`이면 메인 차트를 숨긴다. |
| `chartCandles.bars[].date`, `open`, `high`, `low`, `close`, `volume` | market | display-only OHLC bars. `date`는 UTC 날짜가 아니라 거래소 현지 거래일이며, 수급 `tradeDate`와 같은 키로 매칭한다. 원시 분봉, 다운로드, 개인/외국인/기관 수급은 포함하지 않는다. |
| `investorFlowHistory[].symbol`, `name`, `market`, `currency`, `tradeDate`, `provider`, `sourceLabel`, `delayLabel`, `asOf`, `stale`, `dataStatus`, `individual`, `foreign`, `institution` | market | `GET /api/market/investor-flows/history` 응답 shape. 국내 종목/ETF의 거래일별 개인/외국인/기관 수급만 다루며, public API는 `OK`, `STALE` row만 반환한다. |
| `investorFlow.individual.netAmount`, `netVolume`, `derived`, `foreign.netAmount`, `netVolume`, `derived`, `institution.netAmount`, `netVolume`, `derived` | market | 순매수 금액과 순매수 수량. `netAmount`는 `null`일 수 있고, `derived=true`는 직접 관찰값이 아니라 잔차/계산값이라는 뜻이다. 음수는 순매도 방향이며 투자 판단 문구로 쓰지 않는다. |
| `quoteSnapshot.symbol`, `name`, `market`, `currency`, `price`, `change`, `changePct`, `volume`, `asOf`, `provider`, `delayLabel`, `stale`, `dataStatus` | market | `GET /api/quotes?symbols=005930.KS,AAPL,NVDA` 응답 shape. 공개 화면은 provider/asOf/delayLabel/stale/dataStatus를 가격 근처에 함께 표시한다. |
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

- investor flow 거래일별 slice는 `GET /api/market/investor-flows/history`를 사용한다. 현재 provider adapter는 `naver-finance`이며, 네이버 표 구조 변경이나 provider 실패 때는 빈 배열이 올 수 있다.
- 외인보유/보유율 컬럼은 현재 API에 없으므로 표시하지 않는다. 필요하면 market API 후보로 `foreignHolding`, `foreignHoldingPct`를 별도 논의한다.
- Lightweight Charts용 chartCandles와 quoteSnapshot의 기준 시각 차이를 어떻게 표시할지.
- chartCandles API는 `docs/domains/market/CHART_CANDLES.md` shape를 따른다. raw minute, order book, bulk OHLC가 아닌 공개 표시 가능한 일/주/월 display bars만 사용한다.
- quote snapshot만으로 차트를 만들지 않는다.
- 이평선과 zoom/scroll 축 요약은 API가 내려준 전체 bars를 기준으로 계산하고, 화면 범위만 1M/3M/6M/1Y/3Y/5Y로 조절한다. 단기 이평은 5/10/20, 장기 이평은 60/120/200을 쓰고 색상 범례를 함께 표시한다. 날짜 축은 확대/축소에 따라 일/월/년 단위 tick이 여러 개 보이게 유지한다.
- 차트 로드 실패 시 quote snapshot과 커뮤니티 반응을 그대로 보여줄지.
- 뉴스/공시/커뮤니티 글 상세를 별도 route로 둘지 drawer/panel로 둘지.

## 변경 로그

- 2026-05-21: quote snapshot은 `GET /api/quotes`, 메인 가격 차트는 `GET /api/market/chart-candles`로 분리했다. 차트가 숨겨지는 상태와 차트 shell metadata 표시 기준을 최신 API 계약에 맞췄다.
- 2026-05-22: chart-candles 요청 범위를 5Y로 두고 기본 화면 범위만 3M으로 제한해 장기 이평선과 확대/축소 축을 실제 bars 기준으로 계산한다. 축 라벨은 zoom/scroll과 봉 단위에 맞춰 여러 날짜 tick이 일/월/년 단위로 바뀌도록 보정했다.
- 2026-05-22: 국내 종목/ETF 수급은 `GET /api/market/investor-flows/history` 단일 public API로 정리했다. 최신 1건 public API는 두지 않고, 가격/차트 API에는 개인/외국인/기관 수급을 넣지 않는다.
- 2026-05-22: 수급 provider는 `naver-finance` 기본값으로 바꿨다. 외국인/기관은 순매수 수량 관찰값, 개인은 잔차 추정값(`derived=true`)이며, 금액이 없으면 `netAmount=null`이다.
