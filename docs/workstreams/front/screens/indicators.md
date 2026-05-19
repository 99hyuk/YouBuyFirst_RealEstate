# 주요 지표 화면

## Route

- Parent: root
- Route 후보: `/indicators`
- Child screens: 지표 개별 설명 panel은 `stock-indicator-detail` 후보와 공유 가능

## 화면 목적

시장 지표와 커뮤니티 반응을 같이 보여주고, 가격과 반응이 엇갈리는 종목이나 테마를 찾아냅니다. 일반 금융 대시보드가 아니라 커뮤니티 반응과 시장 지표의 괴리를 보여주는 화면입니다.

## 현재 섹션

- 시장 지표 tape: KOSPI, KOSDAQ, NASDAQ, 환율, VIX, 금리, SOX 등
- 가격과 반응이 엇갈린 종목
- 섹터/테마별 반응 히트맵
- 국장/미장 섹터 방향 보드: 정사각형에 가까운 타일로 각 섹터의 상승/하락 방향과 강도를 표시
- 주요 일정: CPI, FOMC, 실적, 공시
- 지표별 데이터 신선도

## 상태와 빈 화면

- loading: market tape skeleton을 먼저 보여줍니다.
- empty: 시장 지표는 유지하고 커뮤니티 괴리 섹션만 빈 상태로 둡니다.
- error: market, data, schedule 실패를 분리합니다.
- stale/mock: 지표별 `state`와 신선도 표에 표시합니다.

## API 후보

| 필드 | 소유 트랙 | 설명 |
| --- | --- | --- |
| `marketIndicators` | market | 지수, 환율, VIX, 금리, 원자재 |
| `marketIndicators[].reaction` | data | 해당 지표와 연결된 커뮤니티 반응 변화 |
| `anomalyRows` | market/data | 가격 상승·부정 증가, 가격 하락·관심 증가 등 |
| `themeHeatmap` | data | 섹터/테마별 언급과 반응 점수 |
| `sectorBreadthGroups` | market/data | 국장, 미장 섹터별 상승/하락 방향, 변화율, 강도와 기준 시각 |
| `schedules` | market/backend | 주요 일정과 영향 후보 |
| `freshnessRows` | backend | 데이터 신선도와 사용처 |

## 기획자 확인 필요

- 지표와 커뮤니티 반응의 연결 산식을 어떤 수준까지 노출할지.
- CPI/FOMC 같은 일정은 수동 mock, 공개 API, 크롤링 중 무엇으로 시작할지.
- 가격/반응 괴리 종목을 투자 시그널처럼 보이지 않게 하는 문구 기준.

## 변경 로그

- 2026-05-18: Screen Brief 신규 작성. 시장 지표와 커뮤니티 괴리 중심으로 기준화.
