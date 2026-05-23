# 대시보드 화면

## Route

- Parent: root
- Route 후보: `/dashboard`
- Child screens:
  - 오른쪽 빠른 패널: 반응, 지표, 관심, 최근 본, 실시간 drawer 상태

## 화면 목적

첫 화면에서 커뮤니티 반응, 종목 반응, 주요 지표, 뉴스/리포트/영상/블로그 링크를 빠르게 훑고 상세 route로 이동합니다. 화면 문구는 투자 자문이 아니라 관찰 데이터와 mock 상태를 명확히 보여줍니다.

## 현재 섹션

- 상단 속보 티커
- 중앙 검색창과 반응 필터
- 검색 영역 왼쪽 보조 카드: 가로형 개미 심리 지수 게이지, 수치, 어제 대비 변화율, 대표 반응 키워드
- 데이터 기준 strip: 언급 합계, 지연 시세, 관찰 종목, 투자 자문 아님
- 커뮤니티 지표 비교 그래프와 기간 버튼
- 종목 반응 한눈에: 언급+긍정, 언급+부정 상위 묶음
- 오른쪽 라이브 패널: 급상승 종목의 이유 키워드, 라이징 스타
- 실시간 주요 지표 row
- 뉴스, 애널리스트 리포트, 증권 영상 새 글, 블로그/커뮤니티 링크
- 사이트 소개 footer

## 상태와 빈 화면

- loading: 검색, 지표 strip, 그래프 skeleton 순서로 보여줍니다.
- empty: 뉴스/지표 영역은 유지하고 반응 섹션만 빈 상태로 둡니다.
- error: feed, quote, reaction 실패를 섹션별로 분리합니다.
- stale/mock: 상단과 각 카드 badge에 표시합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `dashboardSummary` | backend/indicator | 대시보드 요약, rising star, feed 묶음 |
| `retailSentimentIndex` | indicator | 개미 심리 지수, 전일 대비 변화율, 키워드, 게이지 구간, 과거 비교값 |
| `reactionRanking` | indicator/community | 종목 반응 순위와 기간별 반응 |
| `communityPerformance` | agent/indicator | 커뮤니티 지표 비교 그래프 |
| `quoteSnapshots` | market | 가격 상태와 stale quote |
| `marketIndicators` | market | 주요 지표, 수익률, VIX, 금리 등 |
| `contentFeeds` | community/indicator | 뉴스, 리포트, 영상, 블로그/커뮤니티 링크 |
| `drawerTabs` | layers/ui/backend | 오른쪽 빠른 패널 탭 데이터 |

## 기획상 확인 필요

- 개미 심리 지수 산식은 `indicator` 도메인에서 확정해야 합니다. 현재 프론트는 mock fixture와 시각 구조만 둡니다.
- 검색창은 중앙 위치를 유지합니다. 넓은 화면에서는 보조 지표를 왼쪽 독립 카드로 두고, 1439px 이하 태블릿/반폭 화면에서는 검색창 위의 얇은 정보 바로 전환합니다.
- 자료 모음집에는 재현 이미지보다 사용자가 준 원본 이미지 파일을 우선 연결합니다.
- 커뮤니티 지표 비교의 실제 성과 산식은 `agent`와 `indicator` 중 어느 도메인이 정본을 소유할지 정해야 합니다.

## 변경 로그

- 2026-05-20: 검색창 위치와 아래 간격은 유지하면서 왼쪽에 가로형 개미 심리 지수 게이지를 추가. SVG 안의 글씨/숫자를 제거해 겹침을 방지하고, 자료 모음집은 실제 원본 이미지 파일 중심으로 정리.
- 2026-05-18: Screen Brief 신규 작성. 현재 대시보드 섹션과 오른쪽 빠른 패널 기준 정리.
