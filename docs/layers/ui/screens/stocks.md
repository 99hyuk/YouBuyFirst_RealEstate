# 종목 랭킹 화면

## Route

- Parent: root
- Route 후보: `/stocks`
- Child screens:
  - `stock-detail`: `/stocks/:symbol`

## 화면 목적

국장과 해외 종목을 나눠 거래량 기준으로 비교하고, 관심 종목을 눌러 종목 상세로 들어갑니다. 종목 상세가 첫 화면을 전부 차지하지 않도록 랭킹/검색 화면을 분리합니다.

## 현재 섹션

- 상단 screener hero: 종목명, 티커, 키워드 검색 안내와 상세 이동 목적
- 핵심 신호 strip: 거래량 급증, 긍정 우세, 부정 증가, 라이징 종목
- 필터 strip: 거래량 급증, 언급 증가, 가격 괴리, 부정 증가, 원문 링크 있음, stale 제외
- 랭킹 요약 strip: 정렬 기준, 국장 표시, 해외 표시, 보조 지표
- 국장 거래량 TOP 10: 순위, 종목, 거래량, 반응, 이벤트
- 해외 거래량 TOP 10: 순위, 종목, 거래량, 반응, 이벤트
- 보조 console: 급증 테마, 데이터 기준

## 상태와 빈 화면

- loading: 검색/필터와 table skeleton을 먼저 보여줍니다.
- empty: 필터 조건에 맞는 종목이 없다고 표시하고 필터 초기화를 제공합니다.
- error: quote, reaction, source 상태를 행 단위 badge로 분리합니다.
- stale/mock: `freshness`, 데이터 기준 console, 행별 상태에 표시합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `rankingGroups[].id` | layers/ui/backend | `domestic`, `overseas` 같은 시장 그룹 |
| `rankingGroups[].rows[].rank` | market/indicator | 거래량 기준 현재 정렬 순위 |
| `rankingGroups[].rows[].symbol`, `name`, `market` | stock/backend | 종목 식별 |
| `rankingGroups[].rows[].price`, `change` | market | 현재가와 등락률 |
| `rankingGroups[].rows[].volume`, `volumeDelta` | market | 거래량과 거래량 변화 |
| `rankingGroups[].rows[].positive`, `negative` | indicator | 반응 방향 비율 |
| `rankingGroups[].rows[].event` | backend/indicator | 반응을 움직인 대표 이벤트 |
| `rankingGroups[].rows[].freshness` | backend/market | 지연, mock, stale 상태 |
| `filters` | layers/ui/backend | 서버 필터 후보 |
| `hotThemes` | indicator | 급증 테마와 종목 수 |

## 기획자 확인 필요

- 검색 결과를 같은 table에서 필터링할지, 별도 autocomplete를 둘지.
- 거래량 순위를 거래량 기준으로 둘지, 거래대금 기준도 함께 제공할지.
- 해외 거래량은 원주 기준과 원화 환산 거래대금 중 무엇을 우선할지.
