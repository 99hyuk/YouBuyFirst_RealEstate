# 종목 상세 화면

## Route

- Parent: `stocks`
- Route 후보: `/stocks/:symbol`
- 현재 API 예시: `005930.KS`, `NVDA`. 현재가/등락률/거래량은 `GET /api/quotes`, 메인 차트는 `GET /api/market/chart-candles`를 사용한다.
- Child screens:
  - `stock-news-detail`: 뉴스/공시/리포트 링크 상세 또는 drawer
  - `stock-community-post`: 커뮤니티 원문 snippet/출처 상세
  - `stock-indicator-detail`: 기술/재무 지표 개별 설명 panel

## 화면 목적

사용자가 종목 랭킹에서 특정 종목을 눌렀을 때 가격 흐름, 커뮤니티 반응, 근거 링크, 데이터 신뢰도를 한 화면에서 빠르게 확인하게 한다. 상단 팩트폭격 카피는 `STOCK_DETAIL_COPY_GUIDE.md` 기준의 시황 요약이며, 투자 행동을 지시하는 문구가 아니라 공개 데이터 기반 상태 표현으로 유지한다.

## 현재 섹션

- 팩트폭격 상단 패널: 종목명, 티커, 한줄평, 보조 시황 문장, 근거 keyword chips
- 종목 헤더: 종목명, 시장, quote snapshot 기반 현재가/등락률/거래량/asOf/stale 상태
- 메인 가격 차트: `GET /api/market/chart-candles?symbol=005930.KS&range=3M&interval=1d`의 display-only OHLC bars가 있을 때만 렌더링한다.
- quote snapshot 영역: 현재가, 등락률, 거래량, asOf, stale은 차트 라이브러리에서 읽지 않고 `GET /api/quotes` 값으로 관리한다.
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

## API 후보

| 필드 | 소유 트랙 | 설명 |
| --- | --- | --- |
| `symbol`, `name`, `market` | backend/data | 종목 식별과 표시명 |
| `chartCandles.symbol`, `name`, `market`, `currency`, `range`, `interval`, `provider`, `delayLabel`, `asOf`, `stale`, `dataStatus`, `bars`, `displayPolicy` | market | `GET /api/market/chart-candles` 응답 shape. `bars`가 비었거나 `dataStatus`가 `INSUFFICIENT`, `PROVIDER_ERROR`, `MOCK`이면 메인 차트를 숨긴다. |
| `chartCandles.bars[].date`, `open`, `high`, `low`, `close`, `volume` | market | display-only OHLC bars. 원시 분봉, 다운로드, 개인/외국인/기관 수급은 포함하지 않는다. |
| `investorFlow` | market/data | 개인, 외국인, 기관 순매수/순매도는 전 거래일 기준 별도 slice로 분리한다. |
| `quoteSnapshot.symbol`, `name`, `market`, `currency`, `price`, `change`, `changePct`, `volume`, `asOf`, `provider`, `delayLabel`, `stale`, `dataStatus` | market | 차트와 분리된 quote snapshot 응답 shape. 공개 화면은 provider/asOf/stale/dataStatus를 가격 근처에 함께 표시한다. |
| `headlineTone`, `headline`, `subtitle`, `scoreLine`, `riskNote` | agent/backend | 상단 팩트폭격 카피와 보조 문구 |
| `headlineEvidence` | market/data/agent | 한줄평 근거 chip 배열 |
| `quickStats` | data | 반응 점수, 언급 변화, 출처 수, 링크 수 |
| `keywordPulse` | data | 30분 반응 키워드 증감 |
| `intradaySnapshots` | data/market | 시간대별 언급, 반응, 가격 변화 |
| `reactionTrend` | data | 30분/1일/1주 언급량과 반응 비율 |
| `sourceReaction` | data/crawl | 커뮤니티별 언급, 긍정/부정, 메모 |
| `events` | backend/data/market | 뉴스, 공시, 가격, 커뮤니티 이벤트 타임라인 |
| `evidenceLinks` | crawl/data | 제목 링크와 출처, 원문 URL |
| `reliability` | backend/data | 표본 수, 편중, 출처 다양성, 가격 지연, 원문 확인 |
| `dataQuality` | backend | `complete`, `stale`, `partial`, `mock`, `insufficient` |

## 확인 필요

- investor flow 전 거래일 slice를 어느 market/data API에서 가져올지.
- Lightweight Charts용 chartCandles와 quoteSnapshot의 기준 시각 차이를 어떻게 표시할지.
- 차트 로드 실패 시 quote snapshot과 커뮤니티 반응을 그대로 보여줄지.
- 뉴스/공시/커뮤니티 글 상세를 별도 route로 둘지 drawer/panel로 둘지.

## 변경 로그

- 2026-05-19: 종목 상세 메인 차트를 공개 TradingView embed 비교 영역으로 되돌림. `KRX:005930`과 `NASDAQ:NVDA`를 동시에 띄워 국내/해외 심볼 지원 여부를 브라우저에서 확인한다.
- 2026-05-21: 실제 chart candle API가 구현되어 메인 가격 차트는 `GET /api/market/chart-candles`, 현재가 snapshot은 `GET /api/quotes`로 분리한다.
