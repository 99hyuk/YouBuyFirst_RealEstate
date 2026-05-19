# 대시보드 화면

## Route

- Parent: root
- Route 후보: `/dashboard`
- Child screens:
  - 오른쪽 빠른 패널: 반응, 지표, 관심 탭. 현재는 route 없는 drawer 상태입니다.

## 화면 목적

사용자가 첫 화면에서 커뮤니티 반응, 종목 반응, 주요 지표, 뉴스/리포트/영상/블로그 링크를 빠르게 훑고 상세 route로 이동합니다.

## 현재 섹션

- 독립 검색 영역과 반응 필터
- 데이터 기준 strip: 수집 시각, 가격 기준, mock/stale 상태
- 커뮤니티 지표 비교 그래프와 기간 버튼
- 종목 반응 한눈에: 긍정/부정 상위 종목 묶음
- 실시간 주요 지표 row
- 실시간 뉴스, 애널리스트 리포트, 증권 영상 새 글, 블로그/커뮤니티 링크
- 가격 상태와 확인 필요
- 오른쪽 빠른 패널: 급상승 종목 이유, 라이징 스타, 지표/관심 미리보기

## 상태와 빈 화면

- loading: 검색, 지표 strip, 핵심 그래프 skeleton 순서로 보여줍니다.
- empty: 반응 데이터가 없으면 뉴스/지표 영역은 유지하고 반응 섹션만 빈 상태로 둡니다.
- error: feed, quote, reaction 실패를 섹션별로 분리합니다.
- stale/mock: 상단과 각 카드 badge에 표시합니다.

## API 후보

| 필드 | 소유 트랙 | 설명 |
| --- | --- | --- |
| `dashboardSummary` | backend/data | 대시보드 요약, rising star, feed 묶음 |
| `reactionRanking` | data | 종목 반응 순위와 기간별 반응 |
| `communityPerformance` | agent/data | 커뮤니티 지표 비교 그래프 |
| `quoteSnapshots` | market | 가격 상태와 stale quote |
| `marketIndicators` | market | 주요 지수, 환율, VIX, 금리 등 |
| `contentFeeds` | crawl/data | 뉴스, 리포트, 영상, 블로그/커뮤니티 링크 |
| `drawerTabs` | front/backend | 오른쪽 빠른 패널 탭 데이터 |

## 기획자 확인 필요

- 오른쪽 빠른 패널을 route 없는 drawer로 유지할지, 별도 상세 route를 둘지.
- 검색창이 실제 통합 검색으로 연결될 때 결과 route를 `/stocks` 중심으로 둘지.
- 커뮤니티 지표 비교의 실제 성과 산식을 agent/data 중 어느 트랙이 소유할지.

## 변경 로그

- 2026-05-18: Screen Brief 신규 작성. 현재 대시보드 섹션과 오른쪽 빠른 패널을 기준화.
