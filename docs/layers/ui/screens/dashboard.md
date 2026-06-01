# 대시보드 화면

## Route

- Parent: root
- Route 정보: `/dashboard`
- Child screens: `/realestate/map`, `/realestate/reactions`, `/realestate/targets/:symbol`, `/indicators/:category`, `/newsroom`

## 화면 목적

첫 화면에서 지역·단지 반응, 주요 부동산 지표, 뉴스/리포트/영상/커뮤니티 링크를 빠르게 훑고 상세 화면으로 이동합니다. 화면 문구는 매수·매도 지시가 아니라 공개 데이터와 커뮤니티 반응을 함께 보는 관찰형 정보로 유지합니다.

## 현재 섹션

- 검색/필터: 지역이나 단지 검색, 반응 필터, 데이터 기준 strip
- 부동산 투기 과열 지표: 냉각·주의·과열을 보여주는 gauge
- 핵심 지역별 상승률: 주/월/6개월/년 단위로 지역별 가격 변화율 비교
- 지역·단지 반응 한눈에: 언급+기대, 언급+우려 TOP 묶음
- 주요 부동산 지표: 매매가격지수, 전세가격지수, 실거래가 지수, 거래량, 전세가율, 미분양. 카드 안의 작은 차트는 제거하고 기간 토글로 전환
- 뉴스/리포트/영상/링크 feed: 실제 source icon 기반 외부 링크
- 실거래·지표 상태: 공공데이터 stale/mock 상태
- 오른쪽 빠른 패널: 반응, 지표, 관심 탭

## 주요 지표 기준

- 가격 및 거래량: 매매/전세가격지수, 실거래가 지수, 매매/전월세 거래량
- 공급 및 수급: 미분양 주택, 준공 후 미분양, 인허가·착공·준공, 전세가율
- 수요 및 심리: 매매수급지수, 전세수급지수, 부동산시장 소비심리지수
- 거시경제 및 금융: K-HAI, 기준금리, M2, 물가상승률

## 상태와 빈 화면

- loading: gauge, 반응 순위, 지표 카드, feed skeleton을 먼저 보여줍니다.
- empty: 관찰 지역이 없으면 관심 지역 추가와 지도 화면 이동을 제공합니다.
- error: 뉴스, 공공데이터, 커뮤니티 수집 실패를 영역별 badge로 분리합니다.
- stale/mock: 실거래·공공통계는 공개 지연 가능성을 항상 표시합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `reactionRanking` | indicator/community | 지역·단지별 언급량과 반응 방향 |
| `marketIndicators` | market/realestate | 핵심 부동산 지표 카드 |
| `retailSentimentIndex` | indicator/community | 부동산 투기 과열 지표 gauge |
| `regionalReturnSeries` | market/realestate | 핵심 지역별 상승률 chart |
| `liveNews`, `analystReports` | content/backend | 뉴스와 정책·통계 리포트 |
| `externalContent` | content/backend | 영상, 블로그, 커뮤니티 링크 |
| `quoteSnapshots` | market/realestate | 실거래·지표 snapshot과 stale 상태 |

## 기획 확인 필요

- 실거래가 지수와 거래량의 지역 단위를 어디까지 세분화할지.
- 공공데이터 공개 주기와 커뮤니티 수집 주기가 다를 때 카드에 표시할 기준 시점.
- 상승/하락 색상은 빨강/파랑 관습을 따르고, 서비스 포인트 색은 주황 계열로 유지.

## 변경 로그

- 2026-06-01: 기존 금융 지표 중심 대시보드에서 부동산 지표·지역 반응 중심 대시보드로 전환.
- 2026-06-01: 좌상단 지표를 부동산 투기 과열 지표로 바꾸고, 커뮤니티 비교 chart를 핵심 지역별 상승률 chart로 전환.
- 2026-06-01: 지역/단지와 반응 지표 진입점을 `/realestate/reactions`로 합침.
