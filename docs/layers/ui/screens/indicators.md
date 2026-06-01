# 주요 지표 화면

## Route

- Parent: root
- Overview route: `/indicators`
- Detail routes:
  - `/indicators/price-transaction`
  - `/indicators/supply-demand`
  - `/indicators/sentiment-demand`
  - `/indicators/macro-finance`

## 화면 목적

부동산 시장을 하나의 등락률로 단순화하지 않고, 가격·거래량, 공급·수급, 수요·심리, 거시·금융 지표를 분리해 보여줍니다. 사용자는 어떤 지표가 지역 반응과 함께 움직이는지, 어떤 지표는 반응과 엇갈리는지 확인합니다.

## 현재 섹션

- 지표 hub hero: 데이터 기준 시각, 공개 지연 안내
- 핵심 지표 카테고리 카드: 네 가지 지표 묶음과 대표 수치
- 지역별 지표 방향: 상승/하락 지역군과 핵심 키워드
- 지표 묶음별 관찰 포인트: 가격, 공급, 심리, 금융의 해석 포인트
- 지표와 반응이 엇갈린 지역: 공식 지표와 커뮤니티 반응 괴리 후보
- 지표별 반응 히트맵: 핵심 수치 chip
- 데이터 신선도: 한국부동산원, 국토부, 한국은행, 통계청 기준
- 주요 일정: 가격동향, 실거래, 미분양, 금리 발표 후보

## 상세 route 섹션

- 상세 hero: 지표 묶음명, 요약, 방향성
- 상세 KPI grid: 개별 지표의 값과 해석
- 지표와 지역 반응 동시 변화 chart shell
- 지표별 데이터 신선도
- 연결 키워드 chip
- 지표와 반응이 엇갈린 지역 table

## 지표 정의

- 가격 및 거래량: 매매가격지수, 전세가격지수, 실거래가 지수, 매매·전월세 거래량
- 공급 및 수급: 미분양 주택 현황, 준공 후 미분양, 인허가·착공·준공 실적, 전세가율
- 수요 및 심리: 매매수급지수, 전세수급지수, 부동산시장 소비심리지수
- 거시경제 및 금융: 주택구입부담지수(K-HAI), 기준금리, 통화량(M2), 물가상승률

## 상태와 빈 화면

- loading: 카테고리 카드와 상세 KPI skeleton을 먼저 보여줍니다.
- empty: 지표 값이 없으면 해당 출처와 다음 갱신 예정일을 보여줍니다.
- error: 지표 묶음별로 실패 상태를 분리합니다.
- stale/mock: 지표 공개 주기와 mock 여부를 같은 위치에 표시합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `marketGroups` | market/realestate | 네 가지 핵심 지표 묶음 |
| `detailRows` | market/realestate | 상세 route별 지표 목록 |
| `regionTiles` | market/indicator | 지역군별 방향과 heat |
| `anomalyRows` | indicator/community | 지표와 반응이 엇갈린 지역 |
| `freshnessRows` | backend | 지표 출처별 공개 주기와 stale 상태 |
| `schedules` | backend/content | 주요 발표 일정 |

## 기획 확인 필요

- 실거래가 지수는 전국/시도/시군구 중 어떤 단위까지 1차로 제공할지.
- 수급지수와 소비심리지수의 기준선 100을 카드에서 얼마나 명확히 설명할지.
- K-HAI, M2, 물가상승률은 전국 지표이므로 지역 화면에서 어떻게 가중치를 줄지.

## 변경 로그

- 2026-06-01: 금융시장 지표 묶음을 부동산 핵심 지표 네 그룹으로 교체.
